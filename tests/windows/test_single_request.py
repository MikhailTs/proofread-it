"""Static contracts for single-request behavior at the Windows boundary."""

from pathlib import Path


def test_repeated_hotkey_is_rejected_before_observation_or_clipboard_capture() -> None:
    script = Path("automation/windows/proofread-it.ahk").read_text(encoding="utf-8")

    guard = script.index("if invocationActive")
    notification = script.index("Proofreading is already in progress.", guard)
    rejected_return = script.index("return", notification)
    activation = script.index("invocationActive := true", rejected_return)
    window_observation = script.index('activeWindow := WinExist("A")')
    clipboard_capture = script.index("selectedText := CaptureSelectedText()")

    assert "static invocationActive := false" in script
    assert guard < notification < rejected_return < activation
    assert activation < window_observation < clipboard_capture


def test_active_guard_is_released_and_duplicate_script_launch_is_ignored() -> None:
    script = Path("automation/windows/proofread-it.ahk").read_text(encoding="utf-8")

    activation = script.index("invocationActive := true")
    finally_block = script.index("} finally {", activation)
    release = script.index("invocationActive := false", finally_block)

    assert "#SingleInstance Ignore" in script
    assert "#MaxThreadsPerHotkey 2" in script
    assert activation < finally_block < release
