"""Tests for the automation-to-backend CLI contract."""

import json
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from pytest import CaptureFixture, MonkeyPatch

from proofread_it.cli import main
from proofread_it.concurrency import (
    CONCURRENT_EXIT_CODE,
    CONCURRENT_MESSAGE,
    SingleRequestLock,
)
from proofread_it.models import LogicalRequest
from proofread_it.providers.base import ProviderResponse
from proofread_it.source_check import BLOCKED_EXIT_CODE

_SENTINEL_KEY = "cli-sentinel-key-must-not-appear"


@dataclass
class _FakeProvider:
    final_text: str = "She goes to the library."
    requests: list[LogicalRequest] = field(default_factory=list)

    def send(self, request: LogicalRequest) -> ProviderResponse:
        self.requests.append(request)
        return ProviderResponse(
            response_id="resp_cli",
            model="gpt-5.6-luna",
            api_status="completed",
            output_text=json.dumps(
                {"corrections": ["Fix agreement."], "final_text": self.final_text},
                ensure_ascii=False,
            ),
            raw_response={"id": "resp_cli", "status": "completed"},
        )


def _write_config(tmp_path: Path) -> Path:
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "api": {
                    "model": "gpt-5.6-luna",
                    "api_key_env": "OPENAI_API_KEY",
                    "timeout_seconds": 30,
                    "max_output_tokens": 2048,
                    "retry_count": 2,
                },
                "default_profile": "proofread",
                "context": {
                    "fields": ["application_name", "window_title"],
                    "exclusions": {"process_names": [], "window_title_words": []},
                },
                "concurrency": {"lock_path": "request.lock"},
                "logging": {"path": "events.jsonl"},
            }
        ),
        encoding="utf-8",
    )
    settings_path.with_name("profiles.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "profiles": {
                    "proofread": {
                        "task": "proofread_english",
                        "instructions": "Proofread the selected text.",
                        "context_fields": ["application_name", "window_title"],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    return settings_path


def _connect_fake_provider(monkeypatch: MonkeyPatch, provider: _FakeProvider) -> None:
    monkeypatch.setattr(
        "proofread_it.cli.OpenAIProvider",
        lambda _settings, api_key, **_kwargs: provider if api_key == _SENTINEL_KEY else None,
    )


def test_cli_sends_captured_text_and_shows_the_validated_result(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    settings_path = _write_config(tmp_path)
    provider = _FakeProvider()
    _connect_fake_provider(monkeypatch, provider)
    monkeypatch.setenv("PROOFREAD_IT_SOURCE_PROCESS_NAME", "firefox.exe")
    monkeypatch.setenv("PROOFREAD_IT_SOURCE_WINDOW_TITLE", "Draft — Mozilla Firefox")
    monkeypatch.setenv("PROOFREAD_IT_SOURCE_TEXT", "She go to the library.")
    monkeypatch.setenv("OPENAI_API_KEY", _SENTINEL_KEY)
    shown_results: list[dict[str, object]] = []
    monkeypatch.setattr("proofread_it.cli.show_result", lambda **result: shown_results.append(result))

    exit_code = main(
        [
            "--settings",
            str(settings_path),
            "--profile",
            "proofread",
            "--action",
            "show_full",
        ]
    )

    event = json.loads((tmp_path / "events.jsonl").read_text(encoding="utf-8"))
    assert exit_code == 0
    assert len(provider.requests) == 1
    assert json.loads(provider.requests[0]["parts"][2]["text"]) == {
        "source_context": {
            "application_name": "Firefox",
            "window_title": "Draft — Mozilla Firefox",
        },
        "selected_text": "She go to the library.",
    }
    assert shown_results == [
        {
            "explanations": ("Fix agreement.",),
            "final_text": "She goes to the library.",
        }
    ]
    assert event["event"] == "invocation_completed"
    assert event["raw_response"] == {"id": "resp_cli", "status": "completed"}
    assert event["retry_events"] == []
    assert _SENTINEL_KEY not in (tmp_path / "events.jsonl").read_text(encoding="utf-8")


def test_copy_final_writes_only_validated_text_to_stdout(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capfdbinary: CaptureFixture[bytes],
) -> None:
    settings_path = _write_config(tmp_path)
    final_text = "I received the café menu.\r\nIt looks great — thanks!"
    provider = _FakeProvider(final_text=final_text)
    _connect_fake_provider(monkeypatch, provider)
    monkeypatch.setenv("PROOFREAD_IT_SOURCE_TEXT", "She go to the library.")
    monkeypatch.setenv("OPENAI_API_KEY", _SENTINEL_KEY)
    shown_results: list[dict[str, object]] = []
    monkeypatch.setattr("proofread_it.cli.show_result", lambda **result: shown_results.append(result))

    exit_code = main(
        [
            "--settings",
            str(settings_path),
            "--profile",
            "proofread",
            "--action",
            "copy_final",
        ]
    )

    captured = capfdbinary.readouterr()
    assert exit_code == 0
    assert captured.out == final_text.encode("utf-8")
    assert captured.err == b""
    assert shown_results == []


@pytest.mark.parametrize(
    ("requested_profile", "expected_profile"),
    [(None, "alternate"), ("proofread", "proofread")],
)
def test_cli_uses_configured_default_unless_profile_is_explicit(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    requested_profile: str | None,
    expected_profile: str,
) -> None:
    settings_path = _write_config(tmp_path)
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    settings["default_profile"] = "alternate"
    settings_path.write_text(json.dumps(settings), encoding="utf-8")
    profiles_path = settings_path.with_name("profiles.json")
    profiles = json.loads(profiles_path.read_text(encoding="utf-8"))
    profiles["profiles"]["alternate"] = {
        "task": "proofread_english",
        "instructions": "Alternate profile instructions.",
        "context_fields": [],
    }
    profiles_path.write_text(json.dumps(profiles), encoding="utf-8")
    provider = _FakeProvider()
    _connect_fake_provider(monkeypatch, provider)
    monkeypatch.setenv("PROOFREAD_IT_SOURCE_TEXT", "She go to the library.")
    monkeypatch.setenv("OPENAI_API_KEY", _SENTINEL_KEY)

    arguments = ["--settings", str(settings_path), "--action", "copy_final"]
    if requested_profile is not None:
        arguments += ["--profile", requested_profile]
    exit_code = main(arguments)

    event = json.loads((tmp_path / "events.jsonl").read_text(encoding="utf-8"))
    assert exit_code == 0
    assert len(provider.requests) == 1
    assert event["profile"] == expected_profile
    assert provider.requests[0]["parts"][0]["text"] == (
        "Alternate profile instructions."
        if expected_profile == "alternate"
        else "Proofread the selected text."
    )


def test_missing_credential_fails_before_constructing_the_provider(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    settings_path = _write_config(tmp_path)
    monkeypatch.setenv("PROOFREAD_IT_SOURCE_TEXT", "She go to the library.")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    constructed = False

    def provider_factory(*_args: object) -> _FakeProvider:
        nonlocal constructed
        constructed = True
        return _FakeProvider()

    monkeypatch.setattr("proofread_it.cli.OpenAIProvider", provider_factory)

    exit_code = main(
        [
            "--settings",
            str(settings_path),
            "--profile",
            "proofread",
            "--action",
            "show_full",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert not constructed
    assert "OPENAI_API_KEY" in captured.err
    assert _SENTINEL_KEY not in captured.err
    event = json.loads((tmp_path / "events.jsonl").read_text(encoding="utf-8"))
    assert event["event"] == "invocation_failed"
    assert event["stage"] == "credential"
    assert event["source_text"] == "She go to the library."
    assert event["logical_request"] is None
    assert event["error"]["type"] == "CredentialError"


def test_empty_selection_is_logged_without_reading_the_credential(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    settings_path = _write_config(tmp_path)
    monkeypatch.delenv("PROOFREAD_IT_SOURCE_TEXT", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    exit_code = main(["--settings", str(settings_path), "--action", "copy_final"])

    captured = capsys.readouterr()
    event = json.loads((tmp_path / "events.jsonl").read_text(encoding="utf-8"))
    assert exit_code == 1
    assert "No selected text" in captured.err
    assert event["stage"] == "selection"
    assert event["profile"] == "proofread"
    assert event["source_text"] is None
    assert event["api"] is None


def test_invalid_profile_is_logged_before_credential_access(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    settings_path = _write_config(tmp_path)
    monkeypatch.setenv("PROOFREAD_IT_SOURCE_TEXT", "Draft text")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    exit_code = main(
        ["--settings", str(settings_path), "--profile", "missing", "--action", "show_full"]
    )

    event = json.loads((tmp_path / "events.jsonl").read_text(encoding="utf-8"))
    assert exit_code == 1
    assert event["stage"] == "profile"
    assert event["profile"] == "missing"
    assert event["source_text"] == "Draft text"
    assert event["error"]["type"] == "ConfigurationError"


def test_excluded_source_fails_before_reading_credentials_or_constructing_provider(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    settings_path = _write_config(tmp_path)
    payload = json.loads(settings_path.read_text(encoding="utf-8"))
    payload["context"]["exclusions"]["process_names"] = ["KeePass.exe"]
    settings_path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("PROOFREAD_IT_SOURCE_PROCESS_NAME", "keepass.exe")
    monkeypatch.setenv("PROOFREAD_IT_SOURCE_TEXT", "must-not-be-sent")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    constructed = False

    def provider_factory(*_args: object) -> _FakeProvider:
        nonlocal constructed
        constructed = True
        return _FakeProvider()

    monkeypatch.setattr("proofread_it.cli.OpenAIProvider", provider_factory)

    exit_code = main(
        [
            "--settings",
            str(settings_path),
            "--profile",
            "proofread",
            "--action",
            "show_full",
        ]
    )

    captured = capsys.readouterr()
    raw_log = (tmp_path / "events.jsonl").read_text(encoding="utf-8")
    assert exit_code == BLOCKED_EXIT_CODE
    assert not constructed
    assert "KeePass.exe" in captured.err
    assert "must-not-be-sent" not in raw_log


def test_parallel_invocation_is_rejected_before_credentials_or_provider(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    settings_path = _write_config(tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    constructed = False

    def provider_factory(*_args: object) -> _FakeProvider:
        nonlocal constructed
        constructed = True
        return _FakeProvider()

    monkeypatch.setattr("proofread_it.cli.OpenAIProvider", provider_factory)

    with SingleRequestLock(tmp_path / "request.lock"):
        exit_code = main(
            [
                "--settings",
                str(settings_path),
                "--profile",
                "proofread",
                "--action",
                "copy_final",
            ]
        )

    captured = capsys.readouterr()
    assert exit_code == CONCURRENT_EXIT_CODE
    assert captured.out == ""
    assert captured.err.strip() == CONCURRENT_MESSAGE
    assert not constructed
    assert not (tmp_path / "events.jsonl").exists()
