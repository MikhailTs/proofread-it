"""Tests for the automation-to-backend CLI contract."""

import json
from dataclasses import dataclass, field
from pathlib import Path

from pytest import CaptureFixture, MonkeyPatch

from proofread_it.cli import main
from proofread_it.models import LogicalRequest
from proofread_it.providers.base import ProviderResponse

_SENTINEL_KEY = "cli-sentinel-key-must-not-appear"


@dataclass
class _FakeProvider:
    requests: list[LogicalRequest] = field(default_factory=list)

    def send(self, request: LogicalRequest) -> ProviderResponse:
        self.requests.append(request)
        return ProviderResponse(
            response_id="resp_cli",
            model="gpt-5.6-luna",
            api_status="completed",
            output_text=(
                '{"corrections":["Fix agreement."],'
                '"final_text":"She goes to the library."}'
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
                "context": {"fields": ["application_name", "window_title"]},
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
        lambda _settings, api_key: provider if api_key == _SENTINEL_KEY else None,
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
    assert _SENTINEL_KEY not in (tmp_path / "events.jsonl").read_text(encoding="utf-8")


def test_copy_final_writes_only_validated_text_to_stdout(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    settings_path = _write_config(tmp_path)
    provider = _FakeProvider()
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

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "She goes to the library."
    assert captured.err == ""
    assert shown_results == []


def test_missing_credential_fails_before_constructing_the_provider(
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
