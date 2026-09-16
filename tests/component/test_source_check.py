"""Component tests for the credential-free pre-capture source check."""

import json
from pathlib import Path

from pytest import CaptureFixture, MonkeyPatch

from proofread_it.source_check import BLOCKED_EXIT_CODE, main


def _write_settings(path: Path) -> None:
    path.write_text(
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
                    "fields": [],
                    "exclusions": {
                        "process_names": ["KeePass.exe"],
                        "window_title_words": ["password"],
                    },
                },
                "concurrency": {"lock_path": "request.lock"},
                "logging": {"path": "events.jsonl"},
            }
        ),
        encoding="utf-8",
    )


def test_blocked_source_is_logged_without_text_request_response_or_credential(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    settings_path = tmp_path / "settings.json"
    _write_settings(settings_path)
    monkeypatch.setenv("PROOFREAD_IT_SOURCE_PROCESS_NAME", "KEEPASS.EXE")
    monkeypatch.setenv("PROOFREAD_IT_SOURCE_WINDOW_TITLE", "Database")
    monkeypatch.setenv("PROOFREAD_IT_SOURCE_TEXT", "must-not-be-read")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

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
    event = json.loads((tmp_path / "events.jsonl").read_text(encoding="utf-8"))
    assert exit_code == BLOCKED_EXIT_CODE
    assert "KeePass.exe" in captured.err
    assert event == {
        "timestamp": event["timestamp"],
        "event": "invocation_blocked",
        "profile": "proofread",
        "action": "show_full",
        "source": {
            "application_name": "KeePass",
            "process_name": "KEEPASS.EXE",
            "window_title": "Database",
        },
        "context_policy": {
            "matched_exclusion": {"kind": "process_name", "value": "KeePass.exe"}
        },
    }
    raw_log = (tmp_path / "events.jsonl").read_text(encoding="utf-8")
    assert "must-not-be-read" not in raw_log
    assert "source_text" not in event
    assert "logical_request" not in event
    assert "response" not in event


def test_allowed_source_returns_success_without_creating_a_log(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    settings_path = tmp_path / "settings.json"
    _write_settings(settings_path)
    monkeypatch.setenv("PROOFREAD_IT_SOURCE_PROCESS_NAME", "notepad.exe")
    monkeypatch.setenv("PROOFREAD_IT_SOURCE_WINDOW_TITLE", "Notes")

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

    assert exit_code == 0
    assert not (tmp_path / "events.jsonl").exists()
