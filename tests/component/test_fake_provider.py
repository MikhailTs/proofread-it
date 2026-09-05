"""Provider abstraction component test."""

from dataclasses import dataclass, field

from proofread_it.models import LogicalRequest
from proofread_it.providers.base import Provider, ProviderResponse


@dataclass
class _FakeProvider:
    requests: list[LogicalRequest] = field(default_factory=list)

    def send(self, request: LogicalRequest) -> ProviderResponse:
        self.requests.append(request)
        return ProviderResponse(
            response_id="fake-response",
            model="fake-model",
            api_status="completed",
            output_text='{"corrections":[],"final_text":"Text"}',
            raw_response={"source": "fake"},
        )


def _send_through_boundary(provider: Provider, request: LogicalRequest) -> ProviderResponse:
    return provider.send(request)


def test_provider_boundary_accepts_a_network_free_fake() -> None:
    provider = _FakeProvider()
    request: LogicalRequest = {"parts": []}

    response = _send_through_boundary(provider, request)

    assert provider.requests == [request]
    assert response.output_text == '{"corrections":[],"final_text":"Text"}'
