"""Credential loading at the provider boundary."""

import os
from collections.abc import Mapping


class CredentialError(RuntimeError):
    """Raised when a required provider credential is unavailable."""


def read_api_key_from_environment(
    environment_variable: str,
    *,
    environ: Mapping[str, str] | None = None,
) -> str:
    """Read and normalize an API key from one explicitly named environment variable."""
    source = os.environ if environ is None else environ
    value = source.get(environment_variable)
    if value is None:
        raise CredentialError(
            f"API credential environment variable {environment_variable!r} is not set"
        )

    api_key = value.strip()
    if not api_key:
        raise CredentialError(
            f"API credential environment variable {environment_variable!r} is empty"
        )
    return api_key
