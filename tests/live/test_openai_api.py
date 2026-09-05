"""Explicit paid smoke test for the OpenAI Responses API boundary."""

import json
import os
from pathlib import Path

import pytest

from proofread_it.config.loader import load_default_profile, load_settings
from proofread_it.providers.credentials import read_api_key_from_environment
from proofread_it.providers.openai import OpenAIProvider
from proofread_it.requests.builder import build_request

_LIVE_SETTINGS_ENV = "PROOFREAD_IT_LIVE_SETTINGS_PATH"


@pytest.mark.live
def test_openai_api_returns_the_strict_proofreading_shape() -> None:
    settings_value = os.environ.get(_LIVE_SETTINGS_ENV)
    assert settings_value is not None, "Run live checks through scripts/test-live.ps1"
    settings_path = Path(settings_value)
    settings = load_settings(settings_path)
    profile = load_default_profile(settings_path.with_name("profiles.json"), settings)
    api_key = read_api_key_from_environment(settings.api.api_key_env)
    request = build_request(
        "She go to the library every Tuesday.",
        profile,
        {
            "application_name": "Proofread It live test",
            "process_name": "pytest",
            "window_title": None,
        },
        settings,
    )

    response = OpenAIProvider(settings, api_key).send(request)
    payload: object = json.loads(response.output_text)

    assert response.api_status == "completed"
    assert response.response_id
    assert response.model
    assert isinstance(payload, dict)
    assert set(payload) == {"corrections", "final_text"}
    assert isinstance(payload["corrections"], list)
    assert all(isinstance(item, str) for item in payload["corrections"])
    assert isinstance(payload["final_text"], str)
    assert payload["final_text"]
    assert api_key not in json.dumps(response.raw_response, ensure_ascii=False)
