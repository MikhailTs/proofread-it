"""Component tests for one provider-neutral application workflow."""

import json
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from proofread_it.config.schemas import (
    ApiSettings,
    ContextSettings,
    LoggingSettings,
    Profile,
    Settings,
)
from proofread_it.errors import MalformedResponseError, ProviderTimeoutError
from proofread_it.models import LogicalRequest
from proofread_it.providers.base import ProviderResponse
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
