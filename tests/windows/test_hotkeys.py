"""Static contract tests for the AutoHotkey entry point."""

from pathlib import Path


def test_default_hotkeys_route_profile_and_action_to_backend() -> None:
    script = Path("automation/windows/proofread-it.ahk").read_text(encoding="utf-8")

    assert '^!e::Invoke("proofread", "show_full")' in script
    assert '^!+e::Invoke("proofread", "copy_final")' in script
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


def test_automation_never_reads_or_receives_the_api_credential() -> None:
    script = Path("automation/windows/proofread-it.ahk").read_text(encoding="utf-8")

    assert "openai_token.txt" not in script
    assert "OPENAI_API_KEY" not in script
    assert "scripts\\invoke.ps1" in script


def test_source_exclusions_are_checked_before_clipboard_capture_and_backend_invocation() -> None:
    script = Path("automation/windows/proofread-it.ahk").read_text(encoding="utf-8")

    policy_run = script.index('.Exec(policyCommand)')
    blocked_guard = script.index("policyProcess.ExitCode != 0")
    clipboard_capture = script.index("selectedText := CaptureSelectedText()")
    backend_run = script.index('.Exec(command)')

    assert policy_run < blocked_guard < clipboard_capture < backend_run
