"""Append-only application event logging."""

import json
from datetime import UTC, datetime
from pathlib import Path


def log_invocation(
    log_path: Path,
    *,
    profile: str,
    action: str,
    source_text: str,
    source_process_name: str | None,
    source_window_title: str | None,
) -> None:
    """Append one hotkey invocation as a JSON Lines event."""
    event = {
        "timestamp": datetime.now(UTC).isoformat(timespec="milliseconds"),
        "event": "invocation_received",
        "profile": profile,
        "action": action,
        "source_text": source_text,
        "source": {
            "process_name": source_process_name,
            "window_title": source_window_title,
        },
    }

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")
