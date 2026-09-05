"""Unit tests for source-context normalization."""

import pytest

from proofread_it.context.normalize import normalize_source_context


@pytest.mark.parametrize(
    ("process_name", "application_name"),
    [
        ("firefox.exe", "Firefox"),
        ("Discord.exe", "Discord"),
        ("Telegram.exe", "Telegram"),
        ("code.exe", "code"),
        (r"C:\\Tools\\editor.exe", "editor"),
        (None, None),
    ],
)
def test_maps_known_and_unknown_processes_deterministically(
    process_name: str | None,
    application_name: str | None,
) -> None:
    context = normalize_source_context(process_name, "Draft" if process_name else "")

    assert context == {
        "application_name": application_name,
        "process_name": process_name,
        "window_title": "Draft" if process_name else None,
    }
