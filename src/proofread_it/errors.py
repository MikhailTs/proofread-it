"""Credential-safe application errors."""


class ProviderError(RuntimeError):
    """Base class for model-provider failures safe to show to a user."""


class ProviderAuthenticationError(ProviderError):
    """The provider rejected the configured credential or its permissions."""


class ProviderTimeoutError(ProviderError):
    """The provider request exceeded its configured timeout."""


class ProviderConnectionError(ProviderError):
    """The provider could not be reached."""


class ProviderRateLimitError(ProviderError):
    """The provider rate-limited the request."""


class ProviderServerError(ProviderError):
    """The provider failed after exhausting configured retries."""


class UnsupportedModelError(ProviderError):
    """The configured provider model is unavailable or unsupported."""


class ProviderRequestError(ProviderError):
    """The provider rejected the request as invalid."""


class ProviderResponseError(ProviderError):
    """The provider returned an invalid API response envelope."""


class MalformedResponseError(RuntimeError):
    """The model output did not match the required proofreading-result shape."""
