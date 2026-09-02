"""Operational configuration loading."""

import json
from pathlib import Path

from proofread_it.config.schemas import LoggingSettings, Settings


class ConfigurationError(ValueError):
    """Raised when operational settings cannot be loaded safely."""


def load_settings(path: Path) -> Settings:
    """Load the currently implemented subset of schema version 1 settings."""
    try:
        payload: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ConfigurationError(f"Cannot load settings from {path}: {error}") from error

    if not isinstance(payload, dict):
        raise ConfigurationError("Settings must be a JSON object")
    schema_version = payload.get("schema_version")
    if type(schema_version) is not int or schema_version != 1:
        raise ConfigurationError("settings.schema_version must be 1")

    logging_payload = payload.get("logging")
    if not isinstance(logging_payload, dict):
        raise ConfigurationError("settings.logging must be an object")

    raw_log_path = logging_payload.get("path")
    if not isinstance(raw_log_path, str) or not raw_log_path.strip():
        raise ConfigurationError("settings.logging.path must be a non-empty string")

    log_path = Path(raw_log_path)
    if not log_path.is_absolute():
        log_path = path.parent / log_path

    return Settings(schema_version=1, logging=LoggingSettings(path=log_path.resolve()))
