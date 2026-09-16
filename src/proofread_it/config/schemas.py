"""Typed configuration used by the implemented application slice."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

type ContextField = Literal["application_name", "process_name", "window_title"]


@dataclass(frozen=True, slots=True)
class ApiSettings:
    """Validated provider API settings."""

    model: str
    api_key_env: str
    timeout_seconds: int
    max_output_tokens: int
    retry_count: int


@dataclass(frozen=True, slots=True)
class ExclusionSettings:
    """Configured source rules that prevent capture and transmission."""

    process_names: tuple[str, ...] = ()
    window_title_words: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ContextSettings:
    """Maximum source-context fields that may enter a request."""

    fields: tuple[ContextField, ...]
    exclusions: ExclusionSettings = ExclusionSettings()


@dataclass(frozen=True, slots=True)
class LoggingSettings:
    """Local application log settings."""

    path: Path


@dataclass(frozen=True, slots=True)
class ConcurrencySettings:
    """Filesystem location used to serialize backend invocations."""

    lock_path: Path


@dataclass(frozen=True, slots=True)
class Settings:
    """Validated operational settings."""

    schema_version: Literal[1]
    api: ApiSettings
    default_profile: str
    context: ContextSettings
    concurrency: ConcurrencySettings
    logging: LoggingSettings


@dataclass(frozen=True, slots=True)
class Profile:
    """Validated model-processing profile."""

    name: str
    task: str
    instructions: str
    context_fields: tuple[ContextField, ...]
