"""Selected-text and clipboard contracts at the Windows boundary."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_TEST_API_KEY_ENV = "PROOFREAD_IT_TEST_API_KEY"


def _autohotkey_executable(repository_root: Path) -> str:
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(repository_root / "scripts" / "start.ps1"),
            "-PrintAutoHotkeyPath",
        ],
        cwd=repository_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip("AutoHotkey v2 is not installed")
    return result.stdout.strip()


def _write_wrapper_settings(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "api": {
                    "model": "gpt-5.6-luna",
                    "timeout_seconds": 30,
                    "max_output_tokens": 2048,
                    "retry_count": 2,
                },
                "credential": {"source": "file"},
                "default_profile": "proofread",
                "context": {
                    "fields": [],
                    "exclusions": {"process_names": [], "window_title_words": []},
                },
                "concurrency": {"lock_path": "request.lock"},
                "logging": {"path": "events.jsonl"},
            }
        ),
        encoding="utf-8",
    )


def _write_unicode_fake_uv(path: Path) -> None:
    path.write_text(
        f"""@echo off
if not \"%{_TEST_API_KEY_ENV}%\"==\"\" exit /b 41
if not \"%PYTHONIOENCODING%\"==\"utf-8\" exit /b 42
\"%PROOFREAD_IT_TEST_PYTHON%\" -c "%PROOFREAD_IT_UNICODE_PROBE%"
exit /b %ERRORLEVEL%
""",
        encoding="utf-8",
    )


def test_capture_clears_stale_data_waits_and_restores_clipboard() -> None:
    script = Path("automation/windows/proofread-it.ahk").read_text(encoding="utf-8")

    assert "clipboardBackup := ClipboardAll()" in script
    assert 'A_Clipboard := ""' in script
    assert 'Send("^c")' in script
    assert "if !ClipWait(1.0)" in script
    assert "A_Clipboard := clipboardBackup" in script


def test_backend_runs_only_with_usable_text_outside_the_command_line() -> None:
    script = Path("automation/windows/proofread-it.ahk").read_text(encoding="utf-8")

    empty_guard = script.index('if RegExMatch(selectedText, "^\\s*$")')
    backend_run = script.index("RunCaptured(command")

    assert empty_guard < backend_run
    assert 'EnvSet("PROOFREAD_IT_SOURCE_TEXT", selectedText)' in script
    assert 'EnvSet("PROOFREAD_IT_SOURCE_TEXT", "")' in script
    assert "selectedText" not in script[script.index("command := Format(") : backend_run]


def test_blocked_source_returns_before_clipboard_capture() -> None:
    script = Path("automation/windows/proofread-it.ahk").read_text(encoding="utf-8")

    blocked_guard = script.index("policyExitCode != 0")
    blocked_return = script.index("return", blocked_guard)
    clipboard_capture = script.index("selectedText := CaptureSelectedText()")

    assert blocked_guard < blocked_return < clipboard_capture


def test_changed_active_window_returns_before_clipboard_capture() -> None:
    script = Path("automation/windows/proofread-it.ahk").read_text(encoding="utf-8")

    stability_guard = script.index("currentWindow != activeWindow")
    retry_message = script.index("The active window changed")
    clipboard_capture = script.index("selectedText := CaptureSelectedText()")

    assert stability_guard < retry_message < clipboard_capture


def test_pre_capture_failures_are_logged_without_selected_text() -> None:
    script = Path("automation/windows/proofread-it.ahk").read_text(encoding="utf-8")

    source_changed = script.index('LogPreflightFailure(profile, action, "source_changed")')
    selection_empty = script.index('LogPreflightFailure(profile, action, "no_selection")')
    backend_run = script.index("RunCaptured(command, &correctedText")
    assert source_changed < selection_empty < backend_run
    assert 'EnvSet("PROOFREAD_IT_SOURCE_TEXT", selectedText)' in script[selection_empty:backend_run]


def test_copy_final_uses_only_successful_backend_stdout() -> None:
    script = Path("automation/windows/proofread-it.ahk").read_text(encoding="utf-8")

    exit_check = script.index("exitCode != 0")
    clipboard_write = script.index("CopyFinalToClipboard(correctedText)")
    assert "RunCaptured(command, &correctedText, &errorText)" in script
    assert exit_check < clipboard_write


def test_captured_backend_output_is_decoded_as_utf8() -> None:
    script = Path("automation/windows/proofread-it.ahk").read_text(encoding="utf-8")

    assert 'FileRead(outputPath, "UTF-8")' in script
    assert 'FileRead(errorPath, "UTF-8")' in script
    assert 'StrReplace(text, "`r`n", "`n")' in script
    assert 'StrReplace(normalizedText, "`r", "`n")' in script
    assert 'StrReplace(normalizedText, "`n", "`r`n")' in script


def test_copy_final_preserves_unicode_and_logical_line_breaks_in_clipboard(
    tmp_path: Path,
) -> None:
    repository_root = Path(__file__).parents[2]
    executable = _autohotkey_executable(repository_root)
    included_script = repository_root / "automation" / "windows" / "proofread-it.ahk"
    host_script = tmp_path / "clipboard-host.ahk"
    marker_path = tmp_path / "clipboard.txt"
    blank_line_marker_path = tmp_path / "clipboard-blank-line.txt"
    host_script.write_text(
        "\n".join(
            (
                "#Requires AutoHotkey v2.0",
                'value := "I received the café menu.`r`nIt looks great — thanks!"',
                "clipboardBackup := ClipboardAll()",
                "try {",
                "    CopyFinalToClipboard(value)",
                "    if !ClipWait(1.0)",
                '        throw Error("Clipboard text was unavailable.")',
                '    FileAppend(ReadRawClipboardText(), A_Args[1], "UTF-8-RAW")',
                '    CopyFinalToClipboard("First line`r`n`r`nThird line")',
                '    FileAppend(ReadRawClipboardText(), A_Args[2], "UTF-8-RAW")',
                "} finally {",
                "    A_Clipboard := clipboardBackup",
                "}",
                "ReadRawClipboardText() {",
                '    if !DllCall("User32\\OpenClipboard", "Ptr", 0, "Int")',
                '        throw Error("Cannot open the clipboard.")',
                "    try {",
                '        handle := DllCall("User32\\GetClipboardData", "UInt", 13, "Ptr")',
                "        if !handle",
                '            throw Error("CF_UNICODETEXT is unavailable.")',
                '        pointer := DllCall("Kernel32\\GlobalLock", "Ptr", handle, "Ptr")',
                "        if !pointer",
                '            throw Error("Cannot lock CF_UNICODETEXT.")',
                "        try",
                '            return StrGet(pointer, "UTF-16")',
                "        finally",
                '            DllCall("Kernel32\\GlobalUnlock", "Ptr", handle)',
                "    } finally {",
                '        DllCall("User32\\CloseClipboard")',
                "    }",
                "}",
                "ExitApp",
                f'#Include "{included_script}"',
            )
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            executable,
            "/ErrorStdOut=UTF-8",
            str(host_script),
            str(marker_path),
            str(blank_line_marker_path),
        ],
        cwd=repository_root,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert marker_path.read_bytes() == (
        "I received the café menu.\r\nIt looks great — thanks!".encode()
    )
    assert blank_line_marker_path.read_bytes() == b"First line\r\n\r\nThird line"


def test_full_wrapper_capture_and_clipboard_path_preserves_d1(tmp_path: Path) -> None:
    repository_root = Path(__file__).parents[2]
    executable = _autohotkey_executable(repository_root)
    included_script = repository_root / "automation" / "windows" / "proofread-it.ahk"
    invoke_script = repository_root / "scripts" / "invoke.ps1"
    settings_path = tmp_path / "settings.json"
    fake_bin = tmp_path / "bin"
    host_script = tmp_path / "full-boundary-host.ahk"
    captured_path = tmp_path / "captured.txt"
    clipboard_path = tmp_path / "clipboard.txt"
    error_path = tmp_path / "error.txt"
    fake_bin.mkdir()
    _write_wrapper_settings(settings_path)
    _write_unicode_fake_uv(fake_bin / "uv.cmd")
    host_script.write_text(
        "\n".join(
            (
                "#Requires AutoHotkey v2.0",
                "command := "
                f"'powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "
                f'"{invoke_script}" -SettingsPath "{settings_path}" '
                "-Profile \"proofread\" -Action \"copy_final\"'",
                "exitCode := RunCaptured(command, &correctedText, &errorText)",
                'FileAppend(correctedText, A_Args[1], "UTF-8-RAW")',
                'FileAppend(errorText, A_Args[3], "UTF-8-RAW")',
                "clipboardBackup := ClipboardAll()",
                "try {",
                "    CopyFinalToClipboard(correctedText)",
                "    if !ClipWait(1.0)",
                '        throw Error("Clipboard text was unavailable.")',
                '    FileAppend(ReadRawClipboardText(), A_Args[2], "UTF-8-RAW")',
                "} finally {",
                "    A_Clipboard := clipboardBackup",
                "}",
                "ReadRawClipboardText() {",
                '    if !DllCall("User32\\OpenClipboard", "Ptr", 0, "Int")',
                '        throw Error("Cannot open the clipboard.")',
                "    try {",
                '        handle := DllCall("User32\\GetClipboardData", "UInt", 13, "Ptr")',
                "        if !handle",
                '            throw Error("CF_UNICODETEXT is unavailable.")',
                '        pointer := DllCall("Kernel32\\GlobalLock", "Ptr", handle, "Ptr")',
                "        if !pointer",
                '            throw Error("Cannot lock CF_UNICODETEXT.")',
                "        try",
                '            return StrGet(pointer, "UTF-16")',
                "        finally",
                '            DllCall("Kernel32\\GlobalUnlock", "Ptr", handle)',
                "    } finally {",
                '        DllCall("User32\\CloseClipboard")',
                "    }",
                "}",
                "ExitApp(exitCode)",
                f'#Include "{included_script}"',
            )
        )
        + "\n",
        encoding="utf-8",
    )
    environment = os.environ.copy()
    environment["USERPROFILE"] = str(tmp_path)
    environment["PROOFREAD_IT_TEST_PYTHON"] = sys.executable
    environment["PROOFREAD_IT_UNICODE_PROBE"] = (
        "import sys; sys.stdout.buffer.write(('I received the caf' + chr(233) + ' menu.' "
        "+ chr(13) + chr(10) + 'It looks great ' + chr(8212) + ' thanks!').encode('utf-8'))"
    )
    environment["PATH"] = f"{fake_bin}{os.pathsep}{environment['PATH']}"
    environment.pop(_TEST_API_KEY_ENV, None)

    result = subprocess.run(
        [
            executable,
            "/ErrorStdOut=UTF-8",
            str(host_script),
            str(captured_path),
            str(clipboard_path),
            str(error_path),
        ],
        cwd=repository_root,
        env=environment,
        capture_output=True,
        timeout=10,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr + error_path.read_bytes()
    assert captured_path.read_bytes() == (
        "I received the café menu.\r\nIt looks great — thanks!".encode()
    )
    assert clipboard_path.read_bytes() == (
        "I received the café menu.\r\nIt looks great — thanks!".encode()
    )


def test_result_window_copy_persists_after_tk_owner_closes(tmp_path: Path) -> None:
    repository_root = Path(__file__).parents[2]
    executable = _autohotkey_executable(repository_root)
    probe_script = tmp_path / "tk-clipboard-probe.py"
    host_script = tmp_path / "tk-clipboard-host.ahk"
    marker_path = tmp_path / "clipboard.txt"
    error_path = tmp_path / "error.txt"
    probe_script.write_text(
        "\n".join(
            (
                "import sys",
                "import tkinter as tk",
                f"sys.path.insert(0, {str(repository_root / 'src')!r})",
                "from proofread_it.presentation.result_window import _copy_text",
                "root = tk.Tk()",
                "root.withdraw()",
                "_copy_text(root, 'I received the caf' + chr(233) + ' menu.' "
                "+ chr(13) + chr(10) + 'It looks great ' + chr(8212) + ' thanks!')",
                "root.after(100, root.destroy)",
                "root.mainloop()",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    host_script.write_text(
        "\n".join(
            (
                "#Requires AutoHotkey v2.0",
                "exitCode := 1",
                "clipboardBackup := ClipboardAll()",
                "try {",
                "    command := "
                f"'\"{sys.executable}\" \"{probe_script}\"'",
                f'    exitCode := RunWait(command, "{repository_root}", "Hide")',
                "    if (exitCode != 0)",
                '        throw Error("Tk clipboard probe failed with exit code " exitCode ".")',
                "    if !ClipWait(1.0)",
                '        throw Error("Clipboard text did not persist after Tk exited.")',
                '    FileAppend(ReadRawClipboardText(), A_Args[1], "UTF-8-RAW")',
                "    exitCode := 0",
                "} catch as caughtError {",
                '    FileAppend(caughtError.Message, A_Args[2], "UTF-8-RAW")',
                "} finally {",
                "    A_Clipboard := clipboardBackup",
                "}",
                "ReadRawClipboardText() {",
                '    if !DllCall("User32\\OpenClipboard", "Ptr", 0, "Int")',
                '        throw Error("Cannot open the clipboard.")',
                "    try {",
                '        handle := DllCall("User32\\GetClipboardData", "UInt", 13, "Ptr")',
                "        if !handle",
                '            throw Error("CF_UNICODETEXT is unavailable.")',
                '        pointer := DllCall("Kernel32\\GlobalLock", "Ptr", handle, "Ptr")',
                "        if !pointer",
                '            throw Error("Cannot lock CF_UNICODETEXT.")',
                "        try",
                '            return StrGet(pointer, "UTF-16")',
                "        finally",
                '            DllCall("Kernel32\\GlobalUnlock", "Ptr", handle)',
                "    } finally {",
                '        DllCall("User32\\CloseClipboard")',
                "    }",
                "}",
                "ExitApp(exitCode)",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            executable,
            "/ErrorStdOut=UTF-8",
            str(host_script),
            str(marker_path),
            str(error_path),
        ],
        cwd=repository_root,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    error_text = error_path.read_text(encoding="utf-8") if error_path.exists() else ""
    assert result.returncode == 0, result.stdout + result.stderr + error_text
    assert marker_path.read_bytes() == (
        "I received the café menu.\r\nIt looks great — thanks!".encode()
    )
