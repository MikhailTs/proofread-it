"""Append-only application event logging."""

import json
import re
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

_REDACTED = "[REDACTED]"
_SENSITIVE_KEYS = frozenset(
    ("apikey", "authorization", "authorizationheader", "openaiapikey")
)
_BEARER_PATTERN = re.compile(r"(?i)\bbearer\s+[^\s\"']+")


def log_event(
    log_path: Path,
    event: Mapping[str, object],
    *,
    sensitive_values: Sequence[str] = (),
) -> None:
    """Append a sanitized JSON Lines application event."""
    payload = {
        "timestamp": datetime.now(UTC).isoformat(timespec="milliseconds"),
        **event,
    }
    sanitized = _sanitize(payload, tuple(value for value in sensitive_values if value))

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(sanitized, ensure_ascii=False, separators=(",", ":")) + "\n")


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
    event: dict[str, object] = {
        "event": "invocation_received",
        "profile": profile,
        "action": action,
        "source_text": source_text,
        "source": {
            "process_name": source_process_name,
            "window_title": source_window_title,
        },
    }

    log_event(log_path, event)


def _sanitize(value: object, sensitive_values: tuple[str, ...]) -> object:
    if isinstance(value, Mapping):
        result: dict[str, object] = {}
        for key, item in value.items():
            normalized_key = "".join(character for character in str(key).casefold() if character.isalnum())
            if normalized_key in _SENSITIVE_KEYS:
                result[str(key)] = _REDACTED
            else:
                result[str(key)] = _sanitize(item, sensitive_values)
        return result
    if isinstance(value, (list, tuple)):
        return [_sanitize(item, sensitive_values) for item in value]
    if isinstance(value, str):
        sanitized = _BEARER_PATTERN.sub(f"Bearer {_REDACTED}", value)
        for sensitive_value in sensitive_values:
            sanitized = sanitized.replace(sensitive_value, _REDACTED)
        return sanitized
    return value
