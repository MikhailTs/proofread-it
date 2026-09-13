"""Provider-neutral orchestration for one proofreading invocation."""

from collections.abc import Sequence
from time import perf_counter

from proofread_it.app_logging import log_event
from proofread_it.config.schemas import Profile, Settings
from proofread_it.context.normalize import normalize_source_context
from proofread_it.providers.base import Provider, ProviderResponse, RetryEvent
from proofread_it.requests.builder import build_request
from proofread_it.responses.parser import ProofreadingResult, parse_response


def run_workflow(
    *,
    settings: Settings,
    profile: Profile,
    provider: Provider,
    action: str,
    selected_text: str,
    source_process_name: str | None,
    source_window_title: str | None,
    retry_events: Sequence[RetryEvent] = (),
    sensitive_values: Sequence[str] = (),
) -> ProofreadingResult:
    """Build, send, validate, and log one independent proofreading request."""
    source_context = normalize_source_context(source_process_name, source_window_title)
    request = build_request(selected_text, profile, source_context, settings)
    transmitted_fields = [
        field for field in profile.context_fields if field in settings.context.fields
    ]
    event: dict[str, object] = {
        "event": "invocation_failed",
        "profile": profile.name,
        "action": action,
        "model": settings.api.model,
        "source": source_context,
        "context_policy": {
            "globally_allowed_fields": list(settings.context.fields),
            "profile_fields": list(profile.context_fields),
            "transmitted_fields": transmitted_fields,
        },
        "source_text": selected_text,
        "logical_request": request,
        "request_duration_ms": None,
        "api": None,
        "model_output": None,
        "raw_response": None,
        "normalized_result": None,
        "retry_events": retry_events,
        "error": None,
    }

    started = perf_counter()
    response: ProviderResponse | None = None
    try:
        response = provider.send(request)
        event["request_duration_ms"] = round((perf_counter() - started) * 1000, 3)
        event["api"] = _api_diagnostics(response)
        event["model_output"] = response.output_text
        event["raw_response"] = response.raw_response
        result = parse_response(response.output_text)
    except Exception as error:
        if event["request_duration_ms"] is None:
            event["request_duration_ms"] = round((perf_counter() - started) * 1000, 3)
        if response is not None:
            event["api"] = _api_diagnostics(response)
            event["model_output"] = response.output_text
            event["raw_response"] = response.raw_response
        event["error"] = {"type": type(error).__name__, "detail": str(error)}
        log_event(settings.logging.path, event, sensitive_values=sensitive_values)
        raise

    event["event"] = "invocation_completed"
    event["normalized_result"] = {
        "corrections": list(result.corrections),
        "final_text": result.final_text,
    }
    log_event(settings.logging.path, event, sensitive_values=sensitive_values)
    return result


def _api_diagnostics(response: ProviderResponse) -> dict[str, object]:
    return {
        "response_id": response.response_id,
        "model": response.model,
        "status": response.api_status,
    }
