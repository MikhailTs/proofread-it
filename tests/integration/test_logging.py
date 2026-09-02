"""Integration tests for the single append-only application log."""

import json
from pathlib import Path

from proofread_it.app_logging import log_invocation


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
