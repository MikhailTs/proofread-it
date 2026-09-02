"""Unit tests for operational settings."""

import json
from pathlib import Path

import pytest

from proofread_it.config.loader import ConfigurationError, load_settings


def test_log_path_is_resolved_relative_to_settings_file(tmp_path: Path) -> None:
    settings_path = tmp_path / "config" / "settings.json"
    settings_path.parent.mkdir()
    settings_path.write_text(
        json.dumps({"schema_version": 1, "logging": {"path": "../logs/events.jsonl"}}),
        encoding="utf-8",
    )

    settings = load_settings(settings_path)

    assert settings.logging.path == tmp_path / "logs" / "events.jsonl"


def test_boolean_schema_version_is_rejected(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps({"schema_version": True, "logging": {"path": "events.jsonl"}}),
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="schema_version"):
        load_settings(settings_path)
