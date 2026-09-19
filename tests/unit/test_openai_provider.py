"""Unit tests for the OpenAI Responses API adapter."""

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import httpx2
import pytest
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    NotFoundError,
    OpenAI,
    OpenAIError,
    RateLimitError,
)

from proofread_it.config.schemas import (
    ApiSettings,
    ConcurrencySettings,
    ContextSettings,
    LoggingSettings,
    Settings,
)
from proofread_it.errors import (
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderServerError,
    ProviderTimeoutError,
    UnsupportedModelError,
)
from proofread_it.models import LogicalRequest
from proofread_it.providers.base import RetryEvent
from proofread_it.providers.openai import OpenAIProvider

_SENTINEL_KEY = "provider-sentinel-key-must-not-appear"


def _settings(*, retry_count: int = 2) -> Settings:
    return Settings(
        schema_version=1,
        api=ApiSettings(
            model="gpt-5.6-luna",
            api_key_env="OPENAI_API_KEY",
            timeout_seconds=30,
            max_output_tokens=2048,
            retry_count=retry_count,
        ),
        default_profile="proofread",
        context=ContextSettings(fields=()),
        concurrency=ConcurrencySettings(lock_path=Path("request.lock")),
        logging=LoggingSettings(path=Path("events.jsonl")),
    )


def _request() -> LogicalRequest:
    return {
        "parts": [
            {"kind": "instructions", "text": "Stable proofreading instructions."},
            {
                "kind": "output_contract",
                "schema": {
                    "type": "object",
                    "properties": {"final_text": {"type": "string"}},
                    "required": ["final_text"],
                    "additionalProperties": False,
                },
            },
            {
                "kind": "input",
                "media_type": "application/json",
                "text": '{"source_context":{},"selected_text":"She go."}',
            },
        ]
    }


@dataclass
class _FakeResponseError:
    code: str


@dataclass
class _FakeResponse:
    id: str = "resp_test"
    model: str = "gpt-5.6-luna"
    status: str | None = "completed"
    output_text: str = '{"final_text":"She goes."}'
    error: _FakeResponseError | None = None

    def model_dump(self, *, mode: str) -> dict[str, object]:
        assert mode == "json"
        return {
            "id": self.id,
            "model": self.model,
            "status": self.status,
            "output_text": self.output_text,
        }


@dataclass
class _FakeResponses:
    response: _FakeResponse = field(default_factory=_FakeResponse)
    error: OpenAIError | None = None
    calls: list[dict[str, object]] = field(default_factory=list)

    def create(self, **kwargs: object) -> _FakeResponse:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.response


@dataclass
class _FakeClient:
    responses: _FakeResponses = field(default_factory=_FakeResponses)


def _factory_for(
    client: object,
    constructor_calls: list[dict[str, object]],
) -> Callable[..., object]:
    def factory(**kwargs: object) -> object:
        http_client = kwargs.pop("http_client")
        close = getattr(http_client, "close", None)
        if callable(close):
            close()
        constructor_calls.append(kwargs)
        return client

    return factory


def test_maps_the_logical_request_to_one_stateless_strict_response_call() -> None:
    client = _FakeClient()
    constructor_calls: list[dict[str, object]] = []
    provider = OpenAIProvider(
        _settings(),
        _SENTINEL_KEY,
        client_factory=_factory_for(client, constructor_calls),
    )

    response = provider.send(_request())

    assert constructor_calls == [
        {"api_key": _SENTINEL_KEY, "timeout": 30.0, "max_retries": 2}
    ]
    assert client.responses.calls == [
        {
            "model": "gpt-5.6-luna",
            "instructions": "Stable proofreading instructions.",
            "input": '{"source_context":{},"selected_text":"She go."}',
            "max_output_tokens": 2048,
            "store": False,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "proofreading_result",
                    "strict": True,
                    "schema": _request()["parts"][1]["schema"],
                }
            },
        }
    ]
    sent_arguments = client.responses.calls[0]
    assert "conversation" not in sent_arguments
    assert "previous_response_id" not in sent_arguments
    assert _SENTINEL_KEY not in repr(sent_arguments)
    assert response.response_id == "resp_test"
    assert response.output_text == '{"final_text":"She goes."}'


def _status_error(
    error_type: type[BadRequestError]
    | type[AuthenticationError]
    | type[RateLimitError]
    | type[InternalServerError]
    | type[NotFoundError],
    status_code: int,
    *,
    code: str,
) -> OpenAIError:
    request = httpx2.Request("POST", "https://api.openai.test/v1/responses")
    response = httpx2.Response(status_code, request=request)
    return error_type(
        "provider detail containing provider-sentinel-key-must-not-appear",
        response=response,
        body={"code": code},
    )


@pytest.mark.parametrize(
    ("sdk_error", "expected_error"),
    [
        (
            _status_error(AuthenticationError, 401, code="invalid_api_key"),
            ProviderAuthenticationError,
        ),
        (
            APITimeoutError(httpx2.Request("POST", "https://api.openai.test/v1/responses")),
            ProviderTimeoutError,
        ),
        (
            APIConnectionError(
                request=httpx2.Request("POST", "https://api.openai.test/v1/responses")
            ),
            ProviderConnectionError,
        ),
        (
            _status_error(RateLimitError, 429, code="rate_limit_exceeded"),
            ProviderRateLimitError,
        ),
        (
            _status_error(InternalServerError, 500, code="server_error"),
            ProviderServerError,
        ),
        (
            _status_error(NotFoundError, 404, code="model_not_found"),
            UnsupportedModelError,
        ),
        (
            _status_error(BadRequestError, 400, code="invalid_request_error"),
            ProviderRequestError,
        ),
    ],
)
def test_translates_sdk_errors_without_exposing_provider_details(
    sdk_error: OpenAIError,
    expected_error: type[ProviderError],
) -> None:
    client = _FakeClient(responses=_FakeResponses(error=sdk_error))
    provider = OpenAIProvider(
        _settings(),
        _SENTINEL_KEY,
        client_factory=_factory_for(client, []),
    )

    with pytest.raises(expected_error) as captured:
        provider.send(_request())

    assert _SENTINEL_KEY not in str(captured.value)
    diagnostics = captured.value.diagnostics
    assert diagnostics["provider_error_type"] == type(sdk_error).__name__
    if isinstance(sdk_error, APIStatusError):
        assert diagnostics["http_status"] == sdk_error.status_code
        assert diagnostics["provider_code"] == sdk_error.code
    assert _SENTINEL_KEY not in repr(diagnostics)


def test_rejects_an_invalid_logical_envelope_before_calling_the_sdk() -> None:
    client = _FakeClient()
    provider = OpenAIProvider(
        _settings(),
        _SENTINEL_KEY,
        client_factory=_factory_for(client, []),
    )
    invalid_request: LogicalRequest = {"parts": []}

    with pytest.raises(ProviderRequestError, match="model request is invalid"):
        provider.send(invalid_request)

    assert client.responses.calls == []


def test_configured_sdk_retries_are_reported_with_the_previous_http_status() -> None:
    attempts = 0
    created_clients: list[OpenAI] = []
    retry_events: list[RetryEvent] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal attempts
        attempts += 1
        if attempts <= 2:
            return httpx2.Response(
                500,
                request=request,
                headers={"retry-after-ms": "1"},
                json={"error": {"message": "temporary", "type": "server_error"}},
            )
        return httpx2.Response(
            400,
            request=request,
            json={"error": {"message": "stop", "type": "invalid_request_error"}},
        )

    def client_factory(**kwargs: object) -> object:
        client = OpenAI(
            api_key=str(kwargs["api_key"]),
            timeout=float(kwargs["timeout"]),
            max_retries=int(kwargs["max_retries"]),
            base_url="https://api.openai.test/v1/",
            http_client=kwargs["http_client"],  # type: ignore[arg-type]
        )
        created_clients.append(client)
        return client

    def http_client_factory(**kwargs: object) -> object:
        return httpx2.Client(transport=httpx2.MockTransport(handler), **kwargs)

    provider = OpenAIProvider(
        _settings(retry_count=2),
        _SENTINEL_KEY,
        client_factory=client_factory,
        http_client_factory=http_client_factory,
        retry_event_sink=retry_events.append,
    )

    try:
        with pytest.raises(ProviderRequestError):
            provider.send(_request())
    finally:
        for client in created_clients:
            client.close()

    assert attempts == 3
    assert retry_events == [
        {"retry_number": 1, "trigger": "http_status", "status_code": 500},
        {"retry_number": 2, "trigger": "http_status", "status_code": 500},
    ]


def test_transport_retry_is_reported_without_request_or_header_data() -> None:
    attempts = 0
    created_clients: list[OpenAI] = []
    retry_events: list[RetryEvent] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise httpx2.ConnectError("sentinel transport detail", request=request)
        return httpx2.Response(
            400,
            request=request,
            json={"error": {"message": "stop", "type": "invalid_request_error"}},
        )

    def client_factory(**kwargs: object) -> object:
        client = OpenAI(
            api_key=str(kwargs["api_key"]),
            timeout=float(kwargs["timeout"]),
            max_retries=int(kwargs["max_retries"]),
            base_url="https://api.openai.test/v1/",
            http_client=kwargs["http_client"],  # type: ignore[arg-type]
        )
        created_clients.append(client)
        return client

    def http_client_factory(**kwargs: object) -> object:
        return httpx2.Client(transport=httpx2.MockTransport(handler), **kwargs)

    provider = OpenAIProvider(
        _settings(retry_count=1),
        _SENTINEL_KEY,
        client_factory=client_factory,
        http_client_factory=http_client_factory,
        retry_event_sink=retry_events.append,
    )

    try:
        with pytest.raises(ProviderRequestError):
            provider.send(_request())
    finally:
        for client in created_clients:
            client.close()

    assert attempts == 2
    assert retry_events == [
        {"retry_number": 1, "trigger": "transport_error", "status_code": None}
    ]
    assert _SENTINEL_KEY not in repr(retry_events)
    assert "sentinel transport detail" not in repr(retry_events)
