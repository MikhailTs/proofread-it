"""Typed configuration used by the implemented application slice."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass(frozen=True, slots=True)
class LoggingSettings:
    """Local application log settings."""

    path: Path


@dataclass(frozen=True, slots=True)
class Settings:
    """Validated operational settings."""

    schema_version: Literal[1]
    logging: LoggingSettings
