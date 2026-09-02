"""Static contract tests for the AutoHotkey entry point."""

from pathlib import Path


def test_default_hotkeys_route_profile_and_action_to_backend() -> None:
    script = Path("automation/windows/proofread-it.ahk").read_text(encoding="utf-8")

    assert '^!e::Invoke("proofread", "show_full")' in script
    assert '^!+e::Invoke("proofread", "copy_final")' in script
    assert "proofread-it --settings" in script
    assert "PROOFREAD_IT_SOURCE_PROCESS_NAME" in script
    assert "PROOFREAD_IT_SOURCE_WINDOW_TITLE" in script
