"""Explicit live verification of process-local credential delivery."""

import os
from pathlib import Path

import pytest

from proofread_it.config.loader import load_settings
from proofread_it.providers.credentials import read_api_key_from_environment

_LIVE_SETTINGS_ENV = "PROOFREAD_IT_LIVE_SETTINGS_PATH"


@pytest.mark.live
def test_configured_api_key_is_available_in_the_live_process_environment() -> None:
    settings_path = os.environ.get(_LIVE_SETTINGS_ENV)
    assert settings_path is not None, "Run live checks through scripts/test-live.ps1"
    settings = load_settings(Path(settings_path))

    api_key = read_api_key_from_environment(settings.api.api_key_env)

    assert api_key
