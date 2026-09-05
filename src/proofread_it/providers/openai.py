"""OpenAI Responses API adapter."""

from collections.abc import Callable
from typing import Protocol, cast

from openai import (
    APIConnectionError,
    APIResponseValidationError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    InternalServerError,
    NotFoundError,
    OpenAI,
    OpenAIError,
    PermissionDeniedError,
    RateLimitError,
    UnprocessableEntityError,
)
from openai.types.responses import ResponseTextConfigParam

from proofread_it.config.schemas import Settings
from proofread_it.errors import (
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderResponseError,
    ProviderServerError,
    ProviderTimeoutError,
    UnsupportedModelError,
)
from proofread_it.models import (
    InputPart,
    InstructionsPart,
    LogicalRequest,
    OutputContractPart,
)
from proofread_it.providers.base import ProviderResponse

_RESPONSE_FORMAT_NAME = "proofreading_result"
type ClientFactory = Callable[..., object]


class _ResponseError(Protocol):
    code: str


class _OpenAIResponse(Protocol):
    id: str
    model: str
    status: str | None
    output_text: str
    error: _ResponseError | None

    def model_dump(self, *, mode: str) -> dict[str, object]: ...


class _ResponsesResource(Protocol):
    def create(
        self,
        *,
        model: str,
        instructions: str,
        input: str,
        max_output_tokens: int,
        store: bool,
        text: ResponseTextConfigParam,
    ) -> _OpenAIResponse: ...


class _OpenAIClient(Protocol):
    responses: _ResponsesResource


class OpenAIProvider:
    """Map provider-neutral requests onto one stateless OpenAI response call."""

    def __init__(
        self,
        settings: Settings,
        api_key: str,
        *,
        client_factory: ClientFactory = OpenAI,
    ) -> None:
        self._settings = settings
        self._client = cast(
            _OpenAIClient,
            client_factory(
                api_key=api_key,
                timeout=float(settings.api.timeout_seconds),
                max_retries=settings.api.retry_count,
            ),
        )

    def send(self, request: LogicalRequest) -> ProviderResponse:
        """Send exactly one logical request, allowing only SDK-managed retries."""
        instructions, output_contract, dynamic_input = _request_parts(request)
        response_format: ResponseTextConfigParam = {
            "format": {
                "type": "json_schema",
                "name": _RESPONSE_FORMAT_NAME,
                "strict": True,
                "schema": output_contract["schema"],
            }
        }

        try:
            response = self._client.responses.create(
                model=self._settings.api.model,
                instructions=instructions["text"],
                input=dynamic_input["text"],
                max_output_tokens=self._settings.api.max_output_tokens,
                store=False,
                text=response_format,
            )
        except OpenAIError as error:
            raise _translate_error(error) from error

        if response.error is not None:
            raise _translate_response_error(response.error.code)

        return ProviderResponse(
            response_id=response.id,
            model=response.model,
            api_status=response.status,
            output_text=response.output_text,
            raw_response=response.model_dump(mode="json"),
        )


def _request_parts(
    request: LogicalRequest,
) -> tuple[InstructionsPart, OutputContractPart, InputPart]:
    parts = request.get("parts")
    if not isinstance(parts, list) or len(parts) != 3 or [
        part.get("kind") for part in parts
    ] != [
        "instructions",
        "output_contract",
        "input",
    ]:
        raise ProviderRequestError("The model request is invalid.")
    return (
        cast(InstructionsPart, parts[0]),
        cast(OutputContractPart, parts[1]),
        cast(InputPart, parts[2]),
    )


def _translate_error(error: OpenAIError) -> ProviderError:
    if isinstance(error, (AuthenticationError, PermissionDeniedError)):
        return ProviderAuthenticationError("API authentication failed.")
    if isinstance(error, APITimeoutError):
        return ProviderTimeoutError("The model request timed out.")
    if isinstance(error, RateLimitError):
        return ProviderRateLimitError("The model service rate limit was reached.")
    if isinstance(error, (ConflictError, InternalServerError)):
        return ProviderServerError("The model service is temporarily unavailable.")
    if isinstance(error, APIConnectionError):
        return ProviderConnectionError("Could not connect to the model service.")
    if isinstance(error, NotFoundError) or (
        isinstance(error, (BadRequestError, UnprocessableEntityError))
        and error.code in {"model_not_found", "model_not_supported", "unsupported_model"}
    ):
        return UnsupportedModelError("The configured model is unavailable.")
    if isinstance(error, (BadRequestError, UnprocessableEntityError)):
        return ProviderRequestError("The model service rejected the request.")
    if isinstance(error, APIResponseValidationError):
        return ProviderResponseError("The model service returned an invalid response.")
    if isinstance(error, APIStatusError) and error.status_code >= 500:
        return ProviderServerError("The model service is temporarily unavailable.")
    if isinstance(error, APIStatusError):
        return ProviderRequestError("The model service rejected the request.")
    return ProviderResponseError("The model service returned an invalid response.")


def _translate_response_error(code: str) -> ProviderError:
    if code == "rate_limit_exceeded":
        return ProviderRateLimitError("The model service rate limit was reached.")
    if code == "server_error":
        return ProviderServerError("The model service is temporarily unavailable.")
    return ProviderRequestError("The model service rejected the request.")
