"""Component tests for one provider-neutral application workflow."""

import json
from dataclasses import dataclass, field
from pathlib import Path

import httpx2
import pytest
from openai import OpenAI

from proofread_it.config.schemas import (
    ApiSettings,
    ConcurrencySettings,
    ContextSettings,
    LoggingSettings,
    Profile,
    Settings,
)
from proofread_it.errors import (
    MalformedResponseError,
    ProviderServerError,
    ProviderTimeoutError,
)
from proofread_it.models import LogicalRequest
from proofread_it.providers.base import ProviderResponse, RetryEvent
from proofread_it.providers.openai import OpenAIProvider
from proofread_it.workflow import run_workflow

_SENTINEL_KEY = "workflow-sentinel-key-must-not-appear"


@dataclass
class _FakeProvider:
    response: ProviderResponse | None = None
    error: Exception | None = None
    requests: list[LogicalRequest] = field(default_factory=list)

    def send(self, request: LogicalRequest) -> ProviderResponse:
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        assert self.response is not None
        return self.response


def _settings(log_path: Path) -> Settings:
    return Settings(
        schema_version=1,
        api=ApiSettings(
            model="gpt-5.6-luna",
            api_key_env="OPENAI_API_KEY",
            timeout_seconds=30,
            max_output_tokens=2048,
            retry_count=2,
        ),
        default_profile="proofread",
        context=ContextSettings(fields=("application_name", "window_title")),
        concurrency=ConcurrencySettings(lock_path=log_path.with_suffix(".lock")),
        logging=LoggingSettings(path=log_path),
    )


def _profile() -> Profile:
    return Profile(
        name="proofread",
        task="proofread_english",
        instructions="Proofread the input.",
        context_fields=("application_name", "process_name", "window_title"),
    )


def _event(log_path: Path) -> dict[str, object]:
    return json.loads(log_path.read_text(encoding="utf-8"))


def test_sends_once_validates_and_logs_the_complete_response(tmp_path: Path) -> None:
    log_path = tmp_path / "events.jsonl"
    provider = _FakeProvider(
        response=ProviderResponse(
            response_id="resp_test",
            model="gpt-5.6-luna-2026-09-01",
            api_status="completed",
            output_text='{"corrections":["Fix agreement."],"final_text":"She goes."}',
            raw_response={
                "id": "resp_test",
                "output_text": "She goes.",
                "Authorization": f"Bearer {_SENTINEL_KEY}",
                "debug": _SENTINEL_KEY,
            },
        )
    )

    result = run_workflow(
        settings=_settings(log_path),
        profile=_profile(),
        provider=provider,
        action="show_full",
        selected_text="She go.",
        source_process_name="firefox.exe",
        source_window_title="Draft — Mozilla Firefox",
        sensitive_values=(_SENTINEL_KEY,),
    )

    event = _event(log_path)
    assert result.corrections == ("Fix agreement.",)
    assert result.final_text == "She goes."
    assert len(provider.requests) == 1
    assert event["event"] == "invocation_completed"
    assert event["source"] == {
        "application_name": "Firefox",
        "process_name": "firefox.exe",
        "window_title": "Draft — Mozilla Firefox",
    }
    assert event["context_policy"]["transmitted_fields"] == [
        "application_name",
        "window_title",
    ]
    assert event["logical_request"] == provider.requests[0]
    assert event["api"] == {
        "response_id": "resp_test",
        "model": "gpt-5.6-luna-2026-09-01",
        "status": "completed",
    }
    assert event["model_output"] == (
        '{"corrections":["Fix agreement."],"final_text":"She goes."}'
    )
    assert event["raw_response"]["id"] == "resp_test"
    assert event["normalized_result"] == {
        "corrections": ["Fix agreement."],
        "final_text": "She goes.",
    }
    assert event["retry_events"] == []
    assert isinstance(event["request_duration_ms"], float)
    raw_log = log_path.read_text(encoding="utf-8")
    assert _SENTINEL_KEY not in raw_log
    assert '"Authorization":"[REDACTED]"' in raw_log


def test_logs_raw_response_before_rejecting_malformed_model_output(tmp_path: Path) -> None:
    log_path = tmp_path / "events.jsonl"
    provider = _FakeProvider(
        response=ProviderResponse(
            response_id="resp_bad",
            model="gpt-5.6-luna",
            api_status="completed",
            output_text='{"final_text":"partial"}',
            raw_response={"id": "resp_bad", "output_text": '{"final_text":"partial"}'},
        )
    )

    with pytest.raises(MalformedResponseError):
        run_workflow(
            settings=_settings(log_path),
            profile=_profile(),
            provider=provider,
            action="copy_final",
            selected_text="Text",
            source_process_name=None,
            source_window_title=None,
        )

    event = _event(log_path)
    assert event["event"] == "invocation_failed"
    assert event["model_output"] == '{"final_text":"partial"}'
    assert event["raw_response"]["id"] == "resp_bad"
    assert event["normalized_result"] is None
    assert event["error"]["type"] == "MalformedResponseError"


def test_logs_a_credential_safe_provider_failure(tmp_path: Path) -> None:
    log_path = tmp_path / "events.jsonl"
    provider = _FakeProvider(
        error=ProviderTimeoutError(f"Timed out with Bearer {_SENTINEL_KEY}")
    )

    with pytest.raises(ProviderTimeoutError):
        run_workflow(
            settings=_settings(log_path),
            profile=_profile(),
            provider=provider,
            action="show_full",
            selected_text="Text",
            source_process_name="editor.exe",
            source_window_title="Draft",
            sensitive_values=(_SENTINEL_KEY,),
        )

    raw_log = log_path.read_text(encoding="utf-8")
    event = json.loads(raw_log)
    assert event["event"] == "invocation_failed"
    assert event["raw_response"] is None
    assert event["error"]["type"] == "ProviderTimeoutError"
    assert _SENTINEL_KEY not in raw_log
    assert "Bearer [REDACTED]" in raw_log


def test_logs_retry_events_observed_during_the_provider_call(tmp_path: Path) -> None:
    log_path = tmp_path / "events.jsonl"
    retry_events: list[RetryEvent] = []

    @dataclass
    class _RetryingProvider:
        def send(self, request: LogicalRequest) -> ProviderResponse:
            retry_events.append(
                {"retry_number": 1, "trigger": "http_status", "status_code": 500}
            )
            return ProviderResponse(
                response_id="resp_retry",
                model="gpt-5.6-luna",
                api_status="completed",
                output_text='{"corrections":[],"final_text":"Text"}',
                raw_response={"id": "resp_retry"},
            )

    run_workflow(
        settings=_settings(log_path),
        profile=_profile(),
        provider=_RetryingProvider(),
        action="show_full",
        selected_text="Text",
        source_process_name="editor.exe",
        source_window_title="Draft",
        retry_events=retry_events,
    )

    assert _event(log_path)["retry_events"] == [
        {"retry_number": 1, "trigger": "http_status", "status_code": 500}
    ]


def test_logs_retry_events_when_the_provider_exhausts_retries(tmp_path: Path) -> None:
    log_path = tmp_path / "events.jsonl"
    retry_events: list[RetryEvent] = []

    @dataclass
    class _FailingRetryProvider:
        def send(self, request: LogicalRequest) -> ProviderResponse:
            retry_events.append(
                {"retry_number": 1, "trigger": "transport_error", "status_code": None}
            )
            raise ProviderServerError("The model service is temporarily unavailable.")

    with pytest.raises(ProviderServerError):
        run_workflow(
            settings=_settings(log_path),
            profile=_profile(),
            provider=_FailingRetryProvider(),
            action="show_full",
            selected_text="Text",
            source_process_name="editor.exe",
            source_window_title="Draft",
            retry_events=retry_events,
        )

    event = _event(log_path)
    assert event["event"] == "invocation_failed"
    assert event["retry_events"] == [
        {"retry_number": 1, "trigger": "transport_error", "status_code": None}
    ]


def test_real_sdk_retry_is_included_in_the_completed_invocation_log(tmp_path: Path) -> None:
    log_path = tmp_path / "events.jsonl"
    settings = _settings(log_path)
    retry_events: list[RetryEvent] = []
    attempts = 0
    created_clients: list[OpenAI] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx2.Response(
                500,
                request=request,
                headers={"retry-after-ms": "1"},
                json={"error": {"message": "temporary", "type": "server_error"}},
            )
        return httpx2.Response(
            200,
            request=request,
            json={
                "id": "resp_retry",
                "object": "response",
                "created_at": 0,
                "status": "completed",
                "error": None,
                "incomplete_details": None,
                "instructions": None,
                "max_output_tokens": 2048,
                "model": "gpt-5.6-luna",
                "output": [
                    {
                        "id": "msg_retry",
                        "type": "message",
                        "status": "completed",
                        "role": "assistant",
                        "content": [
                            {
                                "type": "output_text",
                                "text": '{"corrections":[],"final_text":"Text"}',
                                "annotations": [],
                                "logprobs": [],
                            }
                        ],
                    }
                ],
                "parallel_tool_calls": True,
                "previous_response_id": None,
                "reasoning": {"effort": None, "summary": None},
                "store": False,
                "temperature": 1.0,
                "text": {"format": {"type": "text"}},
                "tool_choice": "auto",
                "tools": [],
                "top_p": 1.0,
                "truncation": "disabled",
                "usage": None,
                "metadata": {},
            },
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
        settings,
        _SENTINEL_KEY,
        client_factory=client_factory,
        http_client_factory=http_client_factory,
        retry_event_sink=retry_events.append,
    )

    try:
        result = run_workflow(
            settings=settings,
            profile=_profile(),
            provider=provider,
            action="show_full",
            selected_text="Text",
            source_process_name="editor.exe",
            source_window_title="Draft",
            retry_events=retry_events,
            sensitive_values=(_SENTINEL_KEY,),
        )
    finally:
        for client in created_clients:
            client.close()

    assert attempts == 2
    assert result.final_text == "Text"
    assert _event(log_path)["retry_events"] == [
        {"retry_number": 1, "trigger": "http_status", "status_code": 500}
    ]
    assert _SENTINEL_KEY not in log_path.read_text(encoding="utf-8")
