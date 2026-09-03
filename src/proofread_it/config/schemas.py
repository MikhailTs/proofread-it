"""Typed configuration used by the implemented application slice."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

type ContextField = Literal["application_name", "process_name", "window_title"]


@dataclass(frozen=True, slots=True)
class ContextSettings:
    """Maximum source-context fields that may enter a request."""

    fields: tuple[ContextField, ...]


@dataclass(frozen=True, slots=True)
class LoggingSettings:
    """Local application log settings."""

    path: Path


@dataclass(frozen=True, slots=True)
class Settings:
    """Validated operational settings."""

    schema_version: Literal[1]
    default_profile: str
    context: ContextSettings
    logging: LoggingSettings


@dataclass(frozen=True, slots=True)
class Profile:
    """Validated model-processing profile."""

    name: str
    task: str
    instructions: str
    context_fields: tuple[ContextField, ...]
