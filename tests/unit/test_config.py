"""Unit tests for operational settings."""

import json
from pathlib import Path

import pytest

from proofread_it.config.loader import (
    ConfigurationError,
    load_default_profile,
    load_profile,
    load_settings,
)


def _settings_payload(log_path: str) -> dict[str, object]:
    return {
        "schema_version": 2,
        "api": {
            "model": "gpt-5.6-luna",
            "timeout_seconds": 30,
            "max_output_tokens": 2048,
            "retry_count": 2,
        },
        "credential": {
            "source": "windows_credential_manager",
            "target": "ProofreadIt/OpenAIApiKey",
        },
        "default_profile": "proofread",
        "context": {
            "fields": ["application_name", "window_title"],
            "exclusions": {
                "process_names": ["KeePass.exe"],
                "window_title_words": ["password"],
            },
        },
        "concurrency": {"lock_path": "request.lock"},
        "logging": {"path": log_path},
    }


def _legacy_settings_payload(log_path: str) -> dict[str, object]:
    payload = _settings_payload(log_path)
    payload["schema_version"] = 1
    payload.pop("credential")
    api = payload["api"]
    assert isinstance(api, dict)
    api["api_key_env"] = "OPENAI_API_KEY"
    return payload


def test_log_path_is_resolved_relative_to_settings_file(tmp_path: Path) -> None:
    settings_path = tmp_path / "config" / "settings.json"
    settings_path.parent.mkdir()
    settings_path.write_text(
        json.dumps(_settings_payload("../logs/events.jsonl")),
        encoding="utf-8",
    )

    settings = load_settings(settings_path)

    assert settings.logging.path == tmp_path / "logs" / "events.jsonl"


def test_lock_path_is_resolved_relative_to_settings_file(tmp_path: Path) -> None:
    settings_path = tmp_path / "config" / "settings.json"
    settings_path.parent.mkdir()
    payload = _settings_payload("../logs/events.jsonl")
    payload["concurrency"] = {"lock_path": "../runtime/request.lock"}
    settings_path.write_text(json.dumps(payload), encoding="utf-8")

    settings = load_settings(settings_path)

    assert settings.concurrency.lock_path == tmp_path / "runtime" / "request.lock"


@pytest.mark.parametrize("value", [None, "", "   "])
def test_invalid_concurrency_lock_path_is_rejected(tmp_path: Path, value: object) -> None:
    settings_path = tmp_path / "settings.json"
    payload = _settings_payload("events.jsonl")
    payload["concurrency"] = {"lock_path": value}
    settings_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ConfigurationError, match=r"settings\.concurrency\.lock_path"):
        load_settings(settings_path)


def test_boolean_schema_version_is_rejected(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    payload = _settings_payload("events.jsonl")
    payload["schema_version"] = True
    settings_path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="schema_version"):
        load_settings(settings_path)


@pytest.mark.parametrize(
    "api_key_env",
    [None, "", " OPENAI_API_KEY", "OPENAI_API_KEY ", "INVALID=NAME", "INVALID\x00NAME"],
)
def test_invalid_api_key_environment_variable_name_is_rejected(
    tmp_path: Path,
    api_key_env: object,
) -> None:
    settings_path = tmp_path / "settings.json"
    payload = _legacy_settings_payload("events.jsonl")
    api = payload["api"]
    assert isinstance(api, dict)
    api["api_key_env"] = api_key_env
    settings_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ConfigurationError, match="settings.api.api_key_env"):
        load_settings(settings_path)


def test_schema_version_one_maps_to_the_legacy_file_source(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(_legacy_settings_payload("events.jsonl")),
        encoding="utf-8",
    )

    settings = load_settings(settings_path)

    assert settings.schema_version == 1
    assert settings.credential.source == "file"
    assert settings.credential.target is None
    assert settings.api.api_key_env == "OPENAI_API_KEY"


@pytest.mark.parametrize(
    ("credential", "error_path"),
    [
        (None, "settings.credential"),
        ({"source": "automatic"}, "settings.credential.source"),
        ({"source": "file", "target": "unused"}, "settings.credential.target"),
        ({"source": "windows_credential_manager"}, "settings.credential.target"),
        (
            {"source": "windows_credential_manager", "target": " ProofreadIt/Test"},
            "settings.credential.target",
        ),
    ],
)
def test_invalid_schema_version_two_credential_is_rejected(
    tmp_path: Path,
    credential: object,
    error_path: str,
) -> None:
    settings_path = tmp_path / "settings.json"
    payload = _settings_payload("events.jsonl")
    payload["credential"] = credential
    settings_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ConfigurationError, match=error_path):
        load_settings(settings_path)


def test_schema_version_two_accepts_explicit_file_source(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    payload = _settings_payload("events.jsonl")
    payload["credential"] = {"source": "file"}
    settings_path.write_text(json.dumps(payload), encoding="utf-8")

    settings = load_settings(settings_path)

    assert settings.schema_version == 2
    assert settings.credential.source == "file"
    assert settings.api.api_key_env is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("model", ""),
        ("model", " gpt-5.6-luna"),
        ("timeout_seconds", 0),
        ("timeout_seconds", True),
        ("max_output_tokens", -1),
        ("retry_count", -1),
        ("retry_count", False),
    ],
)
def test_invalid_api_settings_identify_the_failing_field(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    settings_path = tmp_path / "settings.json"
    payload = _settings_payload("events.jsonl")
    api = payload["api"]
    assert isinstance(api, dict)
    api[field] = value
    settings_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ConfigurationError, match=rf"settings\.api\.{field}"):
        load_settings(settings_path)


def test_unknown_api_setting_is_rejected(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    payload = _settings_payload("events.jsonl")
    api = payload["api"]
    assert isinstance(api, dict)
    api["temperature"] = 0
    settings_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ConfigurationError, match=r"settings\.api\.temperature"):
        load_settings(settings_path)


def test_loads_configurable_source_exclusions(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(json.dumps(_settings_payload("events.jsonl")), encoding="utf-8")

    settings = load_settings(settings_path)

    assert settings.context.exclusions.process_names == ("KeePass.exe",)
    assert settings.context.exclusions.window_title_words == ("password",)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("process_names", "KeePass.exe"),
        ("process_names", [""]),
        ("process_names", ["KeePass.exe", "keepass.EXE"]),
        ("window_title_words", [" password"]),
        ("window_title_words", ["password", "PASSWORD"]),
    ],
)
def test_invalid_exclusions_identify_the_failing_field(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    settings_path = tmp_path / "settings.json"
    payload = _settings_payload("events.jsonl")
    context = payload["context"]
    assert isinstance(context, dict)
    exclusions = context["exclusions"]
    assert isinstance(exclusions, dict)
    exclusions[field] = value
    settings_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ConfigurationError, match=rf"settings\.context\.exclusions\.{field}"):
        load_settings(settings_path)


def test_default_profile_name_from_settings_selects_profile(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    profiles_path = tmp_path / "profiles.json"
    settings_path.write_text(json.dumps(_settings_payload("events.jsonl")), encoding="utf-8")
    profiles_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "profiles": {
                    "proofread": {
                        "task": "proofread_english",
                        "instructions": "Keep this prompt verbatim.\n",
                        "context_fields": ["window_title"],
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    profile = load_default_profile(profiles_path, load_settings(settings_path))

    assert profile.name == "proofread"
    assert profile.task == "proofread_english"
    assert profile.instructions == "Keep this prompt verbatim.\n"
    assert profile.context_fields == ("window_title",)


@pytest.mark.parametrize(
    ("profile_change", "error_path"),
    [
        ({"schema_version": 2}, "profiles.schema_version"),
        ({"remove": "task"}, "profiles.profiles.proofread.task"),
        ({"extra": {"temperature": 0}}, "profiles.profiles.proofread.temperature"),
        (
            {"context_fields": ["window_title", "window_title"]},
            "profiles.profiles.proofread.context_fields",
        ),
        (
            {"context_fields": ["window_title", "clipboard_text"]},
            "profiles.profiles.proofread.context_fields",
        ),
    ],
)
def test_invalid_profile_documents_identify_the_failing_field(
    tmp_path: Path,
    profile_change: dict[str, object],
    error_path: str,
) -> None:
    profile: dict[str, object] = {
        "task": "proofread_english",
        "instructions": "Proofread the input.",
        "context_fields": ["window_title"],
    }
    payload: dict[str, object] = {"schema_version": 1, "profiles": {"proofread": profile}}
    if "schema_version" in profile_change:
        payload["schema_version"] = profile_change["schema_version"]
    if "remove" in profile_change:
        profile.pop(str(profile_change["remove"]))
    if "extra" in profile_change:
        profile.update(profile_change["extra"])  # type: ignore[arg-type]
    if "context_fields" in profile_change:
        profile["context_fields"] = profile_change["context_fields"]
    profiles_path = tmp_path / "profiles.json"
    profiles_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ConfigurationError, match=error_path):
        load_profile(profiles_path, "proofread")
