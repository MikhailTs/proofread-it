"""Log an invocation that failed before the proofreading workflow started."""

import argparse
import contextlib
import json
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Final

from proofread_it.app_logging import log_event
from proofread_it.config.loader import ConfigurationError, load_settings
from proofread_it.config.schemas import Settings
from proofread_it.context.normalize import normalize_source_context
from proofread_it.context.policy import find_source_exclusion

_SOURCE_PROCESS_NAME = "PROOFREAD_IT_SOURCE_PROCESS_NAME"
_SOURCE_TEXT = "PROOFREAD_IT_SOURCE_TEXT"
_SOURCE_WINDOW_TITLE = "PROOFREAD_IT_SOURCE_WINDOW_TITLE"

class SelectionError(ValueError):
    """The active application did not provide a usable selection."""


class SourceChangedError(RuntimeError):
    """The active window changed during the pre-capture check."""


_REASONS: Final[dict[str, tuple[str, type[Exception], str, bool]]] = {
    "no_selection": ("selection", SelectionError, "No selected text was detected.", False),
    "source_changed": (
        "source_check",
        SourceChangedError,
        "The active window changed before text capture.",
        False,
    ),
}


def log_preflight_failure(
    settings_path: Path,
    *,
    profile_name: str | None,
    action: str,
    stage: str,
    error: Exception,
    include_source_text: bool,
    settings: Settings | None = None,
    sensitive_values: tuple[str, ...] = (),
) -> bool:
    """Append one safe failure event when the configured log path can be found."""
    loaded_settings = settings
    if loaded_settings is None:
        with contextlib.suppress(ConfigurationError):
            loaded_settings = load_settings(settings_path)

    raw_settings = _read_settings_object(settings_path)
    log_path = (
        loaded_settings.logging.path
        if loaded_settings is not None
        else _recover_log_path(settings_path, raw_settings)
    )
    if log_path is None:
        return False

    source = normalize_source_context(
        os.environ.get(_SOURCE_PROCESS_NAME) or None,
        os.environ.get(_SOURCE_WINDOW_TITLE) or None,
    )
    exclusion = (
        find_source_exclusion(
            source["process_name"],
            source["window_title"],
            loaded_settings.context.exclusions,
        )
        if loaded_settings is not None
        else None
    )
    event: dict[str, object] = {
        "event": "invocation_failed",
        "stage": stage,
        "profile": profile_name
        if profile_name is not None
        else loaded_settings.default_profile if loaded_settings is not None else None,
        "action": action,
        "model": loaded_settings.api.model if loaded_settings is not None else None,
        "source": source,
        "context_policy": {
            "globally_allowed_fields": list(loaded_settings.context.fields),
            "transmitted_fields": [],
            "matched_exclusion": (
                {"kind": exclusion.kind, "value": exclusion.value} if exclusion is not None else None
            ),
        }
        if loaded_settings is not None
        else None,
        "source_text": (
            os.environ.get(_SOURCE_TEXT) or None
            if include_source_text and loaded_settings is not None and exclusion is None
            else None
        ),
        "logical_request": None,
        "request_duration_ms": None,
        "api": None,
        "model_output": None,
        "raw_response": None,
        "normalized_result": None,
        "retry_events": [],
        "error": {"type": type(error).__name__, "detail": str(error)},
    }
    try:
        log_event(log_path, event, sensitive_values=sensitive_values)
    except OSError:
        return False
    return True


def _read_settings_object(path: Path) -> dict[str, object] | None:
    try:
        payload: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _recover_log_path(path: Path, payload: dict[str, object] | None) -> Path | None:
    logging = payload.get("logging") if payload is not None else None
    if not isinstance(logging, dict):
        return None
    value = logging.get("path")
    if not isinstance(value, str) or not value.strip():
        return None
    log_path = Path(value)
    return (log_path if log_path.is_absolute() else path.parent / log_path).resolve()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="proofread-it-invocation-failure")
    parser.add_argument("--settings", required=True, type=Path)
    parser.add_argument("--profile")
    parser.add_argument("--action", required=True, choices=("show_full", "copy_final"))
    parser.add_argument("--reason", required=True, choices=tuple(_REASONS))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Report a known, credential-safe preflight failure from desktop helpers."""
    options = _parser().parse_args(argv)
    stage, error_type, detail, include_source_text = _REASONS[options.reason]
    error = error_type(detail)
    logged = log_preflight_failure(
        options.settings,
        profile_name=options.profile,
        action=options.action,
        stage=stage,
        error=error,
        include_source_text=include_source_text,
    )
    return 0 if logged else 1


if __name__ == "__main__":
    raise SystemExit(main())
