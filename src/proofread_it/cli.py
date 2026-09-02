"""Automation-to-backend command-line boundary."""

import argparse
import os
from collections.abc import Sequence
from pathlib import Path

from proofread_it.app_logging import log_invocation
from proofread_it.config.loader import load_settings

_SOURCE_PROCESS_NAME = "PROOFREAD_IT_SOURCE_PROCESS_NAME"
_SOURCE_WINDOW_TITLE = "PROOFREAD_IT_SOURCE_WINDOW_TITLE"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="proofread-it")
    parser.add_argument("--settings", required=True, type=Path)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--action", required=True, choices=("show_full", "copy_final"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Record one invocation received from the automation layer."""
    options = _parser().parse_args(argv)
    settings = load_settings(options.settings)

    log_invocation(
        settings.logging.path,
        profile=options.profile,
        action=options.action,
        source_process_name=os.environ.get(_SOURCE_PROCESS_NAME) or None,
        source_window_title=os.environ.get(_SOURCE_WINDOW_TITLE) or None,
    )
    return 0
