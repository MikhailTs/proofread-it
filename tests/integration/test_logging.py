"""Integration tests for the single append-only application log."""

import json
from pathlib import Path

from proofread_it.app_logging import log_event, log_invocation


def test_invocations_are_appended_to_one_json_lines_file(tmp_path: Path) -> None:
    log_path = tmp_path / "proofread-it.jsonl"

    log_invocation(
        log_path,
        profile="proofread",
        action="show_full",
        source_text="First draft text",
        source_process_name="firefox.exe",
        source_window_title="First draft",
    )
    log_invocation(
        log_path,
        profile="proofread",
        action="copy_final",
        source_text="Second draft text",
        source_process_name="Telegram.exe",
        source_window_title="Second draft",
    )

    events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert [event["action"] for event in events] == ["show_full", "copy_final"]
    assert [event["source_text"] for event in events] == [
        "First draft text",
        "Second draft text",
    ]
    assert [event["source"]["process_name"] for event in events] == [
        "firefox.exe",
        "Telegram.exe",
    ]


def test_nested_credentials_and_authorization_values_are_redacted(tmp_path: Path) -> None:
    log_path = tmp_path / "proofread-it.jsonl"
    sentinel = "logging-sentinel-key"

    log_event(
        log_path,
        {
            "event": "provider_response",
            "raw_response": {
                "api_key": sentinel,
                "headers": {"authorization": f"Bearer {sentinel}"},
                "detail": f"request used {sentinel}",
            },
        },
        sensitive_values=(sentinel,),
    )

    raw_log = log_path.read_text(encoding="utf-8")
    event = json.loads(raw_log)
    assert sentinel not in raw_log
    assert event["raw_response"]["api_key"] == "[REDACTED]"
    assert event["raw_response"]["headers"]["authorization"] == "[REDACTED]"
    assert event["raw_response"]["detail"] == "request used [REDACTED]"
