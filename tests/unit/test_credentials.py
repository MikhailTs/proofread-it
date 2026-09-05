"""Unit tests for process-environment credential loading."""

import pytest
from pytest import MonkeyPatch

from proofread_it.providers.credentials import CredentialError, read_api_key_from_environment


def test_api_key_is_read_from_the_explicitly_named_environment_variable(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("PROOFREAD_IT_TEST_API_KEY", "  sentinel-api-key  ")
    monkeypatch.setenv("OPENAI_API_KEY", "wrong-key")

    api_key = read_api_key_from_environment("PROOFREAD_IT_TEST_API_KEY")

    assert api_key == "sentinel-api-key"


@pytest.mark.parametrize("value", [None, "", " \t\r\n "])
def test_missing_or_blank_api_key_fails_without_exposing_a_credential(
    value: str | None,
) -> None:
    environment_variable = "PROOFREAD_IT_TEST_API_KEY"
    sentinel = "must-not-appear"
    environment = {"UNRELATED_SECRET": sentinel}
    if value is not None:
        environment[environment_variable] = value

    with pytest.raises(CredentialError) as raised:
        read_api_key_from_environment(environment_variable, environ=environment)

    assert environment_variable in str(raised.value)
    assert sentinel not in str(raised.value)
