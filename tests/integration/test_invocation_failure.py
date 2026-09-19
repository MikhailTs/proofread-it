"""Integration coverage for failures before request construction."""

import json
from pathlib import Path

from pytest import MonkeyPatch

from proofread_it.invocation_failure import main


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
                    "fields": ["application_name", "window_title"],
                    "exclusions": {"process_names": [], "window_title_words": []},
                },
                "concurrency": {"lock_path": "request.lock"},
                "logging": {"path": "events.jsonl"},
            }
        ),
        encoding="utf-8",
    )


def test_empty_selection_logs_source_but_never_stale_text(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    settings_path = tmp_path / "settings.json"
    _write_settings(settings_path)
    monkeypatch.setenv("PROOFREAD_IT_SOURCE_PROCESS_NAME", "firefox.exe")
    monkeypatch.setenv("PROOFREAD_IT_SOURCE_WINDOW_TITLE", "Draft")
    monkeypatch.setenv("PROOFREAD_IT_SOURCE_TEXT", "stale clipboard text")

    exit_code = main(
        ["--settings", str(settings_path), "--action", "show_full", "--reason", "no_selection"]
    )

    event = json.loads((tmp_path / "events.jsonl").read_text(encoding="utf-8"))
    assert exit_code == 0
    assert event["event"] == "invocation_failed"
    assert event["stage"] == "selection"
    assert event["profile"] == "proofread"
    assert event["source"]["process_name"] == "firefox.exe"
    assert event["source_text"] is None
    assert event["logical_request"] is None
    assert event["api"] is None
    assert event["error"]["type"] == "SelectionError"
    assert "stale clipboard text" not in (tmp_path / "events.jsonl").read_text(encoding="utf-8")


def test_credential_failure_logs_captured_text_but_redacts_a_known_key(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    settings_path = tmp_path / "settings.json"
    _write_settings(settings_path)
    sentinel = "failure-log-sentinel-key"
    monkeypatch.setenv("OPENAI_API_KEY", sentinel)
    monkeypatch.setenv("PROOFREAD_IT_SOURCE_TEXT", f"Draft {sentinel}")

    exit_code = main(
        [
            "--settings", str(settings_path), "--action", "copy_final",
            "--reason", "credential_unavailable",
        ]
    )

    raw_log = (tmp_path / "events.jsonl").read_text(encoding="utf-8")
    event = json.loads(raw_log)
    assert exit_code == 0
    assert event["stage"] == "credential"
    assert event["source_text"] == "Draft [REDACTED]"
    assert event["error"]["type"] == "CredentialError"
    assert sentinel not in raw_log


def test_invalid_settings_use_recoverable_log_path(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps({"schema_version": 2, "logging": {"path": "events.jsonl"}}),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "--settings", str(settings_path), "--action", "show_full",
            "--reason", "configuration_invalid",
        ]
    )

    event = json.loads((tmp_path / "events.jsonl").read_text(encoding="utf-8"))
    assert exit_code == 0
    assert event["stage"] == "configuration"
    assert event["model"] is None
    assert event["logical_request"] is None


def test_excluded_source_text_is_not_logged_by_credential_failure(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    settings_path = tmp_path / "settings.json"
    _write_settings(settings_path)
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    settings["context"]["exclusions"]["process_names"] = ["KeePass.exe"]
    settings_path.write_text(json.dumps(settings), encoding="utf-8")
    monkeypatch.setenv("PROOFREAD_IT_SOURCE_PROCESS_NAME", "keepass.exe")
    monkeypatch.setenv("PROOFREAD_IT_SOURCE_TEXT", "private selection")

    exit_code = main(
        [
            "--settings", str(settings_path), "--action", "show_full",
            "--reason", "credential_unavailable",
        ]
    )

    raw_log = (tmp_path / "events.jsonl").read_text(encoding="utf-8")
    event = json.loads(raw_log)
    assert exit_code == 0
    assert event["source_text"] is None
    assert event["context_policy"]["matched_exclusion"] == {
        "kind": "process_name", "value": "KeePass.exe"
    }
    assert "private selection" not in raw_log


def test_unreadable_settings_without_log_path_cannot_log(tmp_path: Path) -> None:
    exit_code = main(
        [
            "--settings", str(tmp_path / "missing.json"), "--action", "show_full",
            "--reason", "configuration_invalid",
        ]
    )

    assert exit_code == 1
    assert not (tmp_path / "events.jsonl").exists()
