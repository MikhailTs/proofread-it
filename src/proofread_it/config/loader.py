"""Operational configuration loading."""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import cast

from proofread_it.config.schemas import (
    ApiSettings,
    ContextField,
    ContextSettings,
    LoggingSettings,
    Profile,
    Settings,
)

_CONTEXT_FIELDS = frozenset(("application_name", "process_name", "window_title"))


class ConfigurationError(ValueError):
    """Raised when operational settings cannot be loaded safely."""


def load_settings(path: Path) -> Settings:
    """Load the currently implemented subset of schema version 1 settings."""
    payload = _load_json_object(path, document_name="settings")

    schema_version = payload.get("schema_version")
    if type(schema_version) is not int or schema_version != 1:
        raise ConfigurationError("settings.schema_version must be 1")

    default_profile = payload.get("default_profile")
    if not isinstance(default_profile, str) or not default_profile.strip():
        raise ConfigurationError("settings.default_profile must be a non-empty string")

    api_payload = payload.get("api")
    if not isinstance(api_payload, dict):
        raise ConfigurationError("settings.api must be an object")
    _require_exact_keys(
        api_payload,
        {"model", "api_key_env", "timeout_seconds", "max_output_tokens", "retry_count"},
        "settings.api",
    )

    model = api_payload.get("model")
    if not isinstance(model, str) or not model.strip() or model.strip() != model:
        raise ConfigurationError("settings.api.model must be a non-empty model name")

    api_key_env = api_payload.get("api_key_env")
    if (
        not isinstance(api_key_env, str)
        or not api_key_env
        or api_key_env.strip() != api_key_env
        or "=" in api_key_env
        or "\x00" in api_key_env
    ):
        raise ConfigurationError("settings.api.api_key_env must be a valid environment variable name")

    timeout_seconds = _load_integer(
        api_payload.get("timeout_seconds"),
        "settings.api.timeout_seconds",
        minimum=1,
    )
    max_output_tokens = _load_integer(
        api_payload.get("max_output_tokens"),
        "settings.api.max_output_tokens",
        minimum=1,
    )
    retry_count = _load_integer(
        api_payload.get("retry_count"),
        "settings.api.retry_count",
        minimum=0,
    )

    context_payload = payload.get("context")
    if not isinstance(context_payload, dict):
        raise ConfigurationError("settings.context must be an object")
    context_fields = _load_context_fields(context_payload.get("fields"), "settings.context.fields")

    logging_payload = payload.get("logging")
    if not isinstance(logging_payload, dict):
        raise ConfigurationError("settings.logging must be an object")

    raw_log_path = logging_payload.get("path")
    if not isinstance(raw_log_path, str) or not raw_log_path.strip():
        raise ConfigurationError("settings.logging.path must be a non-empty string")

    log_path = Path(raw_log_path)
    if not log_path.is_absolute():
        log_path = path.parent / log_path

    return Settings(
        schema_version=1,
        api=ApiSettings(
            model=model,
            api_key_env=api_key_env,
            timeout_seconds=timeout_seconds,
            max_output_tokens=max_output_tokens,
            retry_count=retry_count,
        ),
        default_profile=default_profile,
        context=ContextSettings(fields=context_fields),
        logging=LoggingSettings(path=log_path.resolve()),
    )


def load_profile(path: Path, name: str) -> Profile:
    """Load one named profile from a schema-version-1 profiles document."""
    payload = _load_json_object(path, document_name="profiles")
    _require_exact_keys(payload, {"schema_version", "profiles"}, "profiles")

    schema_version = payload.get("schema_version")
    if type(schema_version) is not int or schema_version != 1:
        raise ConfigurationError("profiles.schema_version must be 1")

    profiles = payload.get("profiles")
    if not isinstance(profiles, dict):
        raise ConfigurationError("profiles.profiles must be an object")
    raw_profile = profiles.get(name)
    if not isinstance(raw_profile, dict):
        raise ConfigurationError(f"profiles.profiles.{name} must be an object")

    field_path = f"profiles.profiles.{name}"
    _require_exact_keys(raw_profile, {"task", "instructions", "context_fields"}, field_path)

    task = raw_profile.get("task")
    if not isinstance(task, str) or not task.strip():
        raise ConfigurationError(f"{field_path}.task must be a non-empty string")
    instructions = raw_profile.get("instructions")
    if not isinstance(instructions, str) or not instructions.strip():
        raise ConfigurationError(f"{field_path}.instructions must be a non-empty string")
    context_fields = _load_context_fields(
        raw_profile.get("context_fields"), f"{field_path}.context_fields"
    )

    return Profile(
        name=name,
        task=task,
        instructions=instructions,
        context_fields=context_fields,
    )


def load_default_profile(path: Path, settings: Settings) -> Profile:
    """Load the profile selected by operational settings."""
    return load_profile(path, settings.default_profile)


def _load_json_object(path: Path, *, document_name: str) -> dict[str, object]:
    try:
        payload: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ConfigurationError(f"Cannot load {document_name} from {path}: {error}") from error

    if not isinstance(payload, dict):
        raise ConfigurationError(f"{document_name} must be a JSON object")
    return cast(dict[str, object], payload)


def _require_exact_keys(
    payload: Mapping[str, object], expected: set[str], field_path: str
) -> None:
    actual = set(payload)
    missing = sorted(expected - actual)
    if missing:
        raise ConfigurationError(f"{field_path}.{missing[0]} is required")
    unknown = sorted(actual - expected)
    if unknown:
        raise ConfigurationError(f"{field_path}.{unknown[0]} is not supported")


def _load_context_fields(value: object, field_path: str) -> tuple[ContextField, ...]:
    if not isinstance(value, list):
        raise ConfigurationError(f"{field_path} must be an array")

    fields: list[ContextField] = []
    seen: set[str] = set()
    for index, field in enumerate(value):
        item_path = f"{field_path}[{index}]"
        if not isinstance(field, str) or field not in _CONTEXT_FIELDS:
            raise ConfigurationError(f"{item_path} is not a supported context field")
        if field in seen:
            raise ConfigurationError(f"{item_path} duplicates context field {field!r}")
        seen.add(field)
        fields.append(cast(ContextField, field))
    return tuple(fields)


def _load_integer(value: object, field_path: str, *, minimum: int) -> int:
    if type(value) is not int or value < minimum:
        qualifier = "a positive integer" if minimum == 1 else "a non-negative integer"
        raise ConfigurationError(f"{field_path} must be {qualifier}")
    return value
