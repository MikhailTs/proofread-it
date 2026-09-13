"""Small provider-facing API abstraction."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, Protocol, TypedDict

from proofread_it.models import LogicalRequest


class RetryEvent(TypedDict):
    """Credential-free observation of one SDK-managed retry attempt."""

    retry_number: int
    trigger: Literal["http_status", "transport_error"]
    status_code: int | None


type RetryEventSink = Callable[[RetryEvent], None]


@dataclass(frozen=True, slots=True)
class ProviderResponse:
    """Provider response data retained for later validation and diagnostics."""

    response_id: str
    model: str
    api_status: str | None
    output_text: str
    raw_response: dict[str, object]


class Provider(Protocol):
    """Stateless model-provider operation used by the application workflow."""

    def send(self, request: LogicalRequest) -> ProviderResponse:
        """Send one independent logical request."""
        ...
