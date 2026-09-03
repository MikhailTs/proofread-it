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
        "schema_version": 1,
        "default_profile": "proofread",
        "context": {"fields": ["application_name", "window_title"]},
        "logging": {"path": log_path},
    }


def test_log_path_is_resolved_relative_to_settings_file(tmp_path: Path) -> None:
    settings_path = tmp_path / "config" / "settings.json"
    settings_path.parent.mkdir()
    settings_path.write_text(
        json.dumps(_settings_payload("../logs/events.jsonl")),
        encoding="utf-8",
    )

    settings = load_settings(settings_path)

    assert settings.logging.path == tmp_path / "logs" / "events.jsonl"


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
