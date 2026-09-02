"""Tests for the automation-to-backend CLI contract."""

import json
from pathlib import Path

from pytest import MonkeyPatch

from proofread_it.cli import main


def test_cli_logs_only_the_invocation_contract(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    log_path = tmp_path / "events.jsonl"
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps({"schema_version": 1, "logging": {"path": log_path.name}}),
        encoding="utf-8",
    )

    monkeypatch.setenv("PROOFREAD_IT_SOURCE_PROCESS_NAME", "firefox.exe")
    monkeypatch.setenv("PROOFREAD_IT_SOURCE_WINDOW_TITLE", "Draft — Mozilla Firefox")
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-appear")

    result = main(
        [
            "--settings",
            str(settings_path),
            "--profile",
            "proofread",
            "--action",
            "show_full",
        ]
    )

    raw_log = log_path.read_text(encoding="utf-8")
    event = json.loads(raw_log)
    assert result == 0
    assert event["event"] == "invocation_received"
    assert event["profile"] == "proofread"
    assert event["action"] == "show_full"
    assert event["source"] == {
        "process_name": "firefox.exe",
        "window_title": "Draft — Mozilla Firefox",
    }
    assert event["timestamp"].endswith("+00:00")
    assert "must-not-appear" not in raw_log
