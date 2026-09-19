"""Credential-free pre-capture source-policy check."""

import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from proofread_it.app_logging import log_event
from proofread_it.config.loader import ConfigurationError, load_settings
from proofread_it.config.schemas import Settings
from proofread_it.context.normalize import normalize_source_context
from proofread_it.context.policy import ExclusionMatch, find_source_exclusion
from proofread_it.invocation_failure import log_preflight_failure

BLOCKED_EXIT_CODE = 10
_SOURCE_PROCESS_NAME = "PROOFREAD_IT_SOURCE_PROCESS_NAME"
_SOURCE_WINDOW_TITLE = "PROOFREAD_IT_SOURCE_WINDOW_TITLE"


def check_current_source(
    settings: Settings,
    *,
    profile: str,
    action: str,
) -> ExclusionMatch | None:
    """Check environment-supplied metadata and log a blocked invocation."""
    process_name = os.environ.get(_SOURCE_PROCESS_NAME) or None
    window_title = os.environ.get(_SOURCE_WINDOW_TITLE) or None
    match = find_source_exclusion(process_name, window_title, settings.context.exclusions)
    if match is None:
        return None

    log_event(
        settings.logging.path,
        {
            "event": "invocation_blocked",
            "profile": profile,
            "action": action,
            "source": normalize_source_context(process_name, window_title),
            "context_policy": {
                "matched_exclusion": {"kind": match.kind, "value": match.value}
            },
        },
    )
    return match


def blocked_message(match: ExclusionMatch) -> str:
    """Build the concise user-facing blocked-action notification."""
    return f"Proofreading is blocked by source exclusion: {match.kind}={match.value}."


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="proofread-it-source-check")
    parser.add_argument("--settings", required=True, type=Path)
    parser.add_argument("--profile")
    parser.add_argument("--action", required=True, choices=("show_full", "copy_final"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Return success for an allowed source and a distinct code for a blocked source."""
    options = _parser().parse_args(argv)
    try:
        settings = load_settings(options.settings)
        match = check_current_source(
            settings,
            profile=options.profile if options.profile is not None else settings.default_profile,
            action=options.action,
        )
    except ConfigurationError as error:
        log_preflight_failure(
            options.settings,
            profile_name=options.profile,
            action=options.action,
            stage="configuration",
            error=error,
            include_source_text=False,
        )
        print(str(error), file=sys.stderr)
        return 1
    except OSError as error:
        print(str(error), file=sys.stderr)
        return 1

    if match is not None:
        print(blocked_message(match), file=sys.stderr)
        return BLOCKED_EXIT_CODE
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
