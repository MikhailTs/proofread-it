"""Small provider-facing API abstraction."""

from dataclasses import dataclass
from typing import Protocol

from proofread_it.models import LogicalRequest


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
