"""Automation-to-backend command-line boundary."""

import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from proofread_it.config.loader import ConfigurationError, load_profile, load_settings
from proofread_it.errors import MalformedResponseError, ProviderError
from proofread_it.presentation.result_window import show_result
from proofread_it.providers.credentials import CredentialError, read_api_key_from_environment
from proofread_it.providers.openai import OpenAIProvider
from proofread_it.workflow import run_workflow

_SOURCE_PROCESS_NAME = "PROOFREAD_IT_SOURCE_PROCESS_NAME"
_SOURCE_TEXT = "PROOFREAD_IT_SOURCE_TEXT"
_SOURCE_WINDOW_TITLE = "PROOFREAD_IT_SOURCE_WINDOW_TITLE"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="proofread-it")
    parser.add_argument("--settings", required=True, type=Path)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--action", required=True, choices=("show_full", "copy_final"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Handle one invocation received from the automation layer."""
    options = _parser().parse_args(argv)
    try:
        settings = load_settings(options.settings)
        profile = load_profile(options.settings.with_name("profiles.json"), options.profile)
        api_key = read_api_key_from_environment(settings.api.api_key_env)
        result = run_workflow(
            settings=settings,
            profile=profile,
            provider=OpenAIProvider(settings, api_key),
            action=options.action,
            selected_text=os.environ.get(_SOURCE_TEXT, ""),
            source_process_name=os.environ.get(_SOURCE_PROCESS_NAME) or None,
            source_window_title=os.environ.get(_SOURCE_WINDOW_TITLE) or None,
            sensitive_values=(api_key,),
        )
    except (ConfigurationError, CredentialError, MalformedResponseError, ProviderError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1

    if options.action == "show_full":
        show_result(explanations=result.corrections, final_text=result.final_text)
    else:
        sys.stdout.write(result.final_text)
    return 0
