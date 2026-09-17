"""Static contract tests for the AutoHotkey entry point."""

from pathlib import Path


def test_default_hotkeys_route_action_and_allow_profile_override() -> None:
    script = Path("automation/windows/proofread-it.ahk").read_text(encoding="utf-8")

    assert '^!e::InvokeDefault("show_full")' in script
    assert '^!+e::InvokeDefault("copy_final")' in script
    assert 'Invoke("", action)' in script
    assert 'profileOption := profile = "" ? ""' in script
    assert "scripts\\invoke.ps1" in script
    assert "powershell.exe -NoProfile -NonInteractive" in script
    assert "PROOFREAD_IT_SOURCE_PROCESS_NAME" in script
    assert "PROOFREAD_IT_SOURCE_WINDOW_TITLE" in script
    assert "python -m proofread_it.source_check" in script


def test_repository_paths_are_relative_to_the_automation_file() -> None:
    script = Path("automation/windows/proofread-it.ahk").read_text(encoding="utf-8")

    assert "SplitPath(A_LineFile, , &AutomationDir)" in script
    assert 'ProjectRoot := AutomationDir "\\..\\.."' in script
    assert 'InvokeScriptPath := ProjectRoot "\\scripts\\invoke.ps1"' in script
    assert "ProjectRoot := A_ScriptDir" not in script


def test_windows_acceptance_documents_credential_free_automation_startup() -> None:
    instructions = Path("docs/windows-acceptance.md").read_text(encoding="utf-8")

    assert instructions.count(r".\scripts\start.ps1") == 2
    assert '-AutomationPath "C:\\path\\to\\temporary-host.ahk"' in instructions
    assert "does not read or inject the API credential" in instructions
    assert "per-invocation wrapper" in instructions
    assert "real, billable OpenAI Responses API requests" in instructions
    assert "placeholder" not in instructions
    assert "clipboard must contain only its normalized `final_text`" in instructions
    assert "Proofreading is already in progress." in instructions
    assert "concurrency.lock_path" in instructions


def test_automation_never_reads_or_receives_the_api_credential() -> None:
    script = Path("automation/windows/proofread-it.ahk").read_text(encoding="utf-8")

    assert "openai_token.txt" not in script
    assert "OPENAI_API_KEY" not in script
    assert "scripts\\invoke.ps1" in script


def test_source_exclusions_are_checked_before_clipboard_capture_and_backend_invocation() -> None:
    script = Path("automation/windows/proofread-it.ahk").read_text(encoding="utf-8")

    policy_run = script.index("RunCaptured(policyCommand")
    blocked_guard = script.index("policyExitCode != 0")
    clipboard_capture = script.index("selectedText := CaptureSelectedText()")
    backend_run = script.index("RunCaptured(command")

    assert policy_run < blocked_guard < clipboard_capture < backend_run


def test_policy_and_backend_processes_cannot_show_a_focus_stealing_console() -> None:
    script = Path("automation/windows/proofread-it.ahk").read_text(encoding="utf-8")

    hidden_prefix = "powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden"

    assert script.count(hidden_prefix) == 2
    assert "-Command uv run --project" in script
    assert "-ExecutionPolicy Bypass -File" in script


def test_child_process_wait_allows_duplicate_hotkey_threads_to_run_immediately() -> None:
    script = Path("automation/windows/proofread-it.ahk").read_text(encoding="utf-8")

    assert script.count("RunCaptured(") == 3
    assert 'RunWait(target, , "Hide")' in script
    assert 'ComObject("WScript.Shell").Exec' not in script
    assert ".StdOut.ReadAll()" not in script
    assert "A_ComSpec" in script
    assert "2>" in script
