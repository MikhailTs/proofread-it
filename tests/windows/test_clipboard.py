"""Static contracts for selected-text capture at the Windows boundary."""

from pathlib import Path


def test_capture_clears_stale_data_waits_and_restores_clipboard() -> None:
    script = Path("automation/windows/proofread-it.ahk").read_text(encoding="utf-8")

    assert "clipboardBackup := ClipboardAll()" in script
    assert 'A_Clipboard := ""' in script
    assert 'Send("^c")' in script
    assert "if !ClipWait(1.0)" in script
    assert "A_Clipboard := clipboardBackup" in script


def test_backend_runs_only_with_non_empty_text_outside_the_command_line() -> None:
    script = Path("automation/windows/proofread-it.ahk").read_text(encoding="utf-8")

    empty_guard = script.index('if (selectedText = "")')
    backend_run = script.index('.Exec(command)')

    assert empty_guard < backend_run
    assert 'EnvSet("PROOFREAD_IT_SOURCE_TEXT", selectedText)' in script
    assert 'EnvSet("PROOFREAD_IT_SOURCE_TEXT", "")' in script
    assert "selectedText" not in script[script.index("command := Format(") : backend_run]


def test_copy_final_uses_only_successful_backend_stdout() -> None:
    script = Path("automation/windows/proofread-it.ahk").read_text(encoding="utf-8")

    exit_check = script.index("process.ExitCode != 0")
    clipboard_write = script.index("A_Clipboard := correctedText")
    assert "process.StdOut.ReadAll()" in script
    assert exit_check < clipboard_write
