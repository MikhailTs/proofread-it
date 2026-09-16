"""Static contracts for single-request behavior at the Windows boundary."""

from pathlib import Path


def test_repeated_hotkey_is_rejected_before_observation_or_clipboard_capture() -> None:
    script = Path("automation/windows/proofread-it.ahk").read_text(encoding="utf-8")

    guard = script.index("if invocationActive")
    notification = script.index("NotifyConcurrentInvocation()", guard)
    rejected_return = script.index("return", notification)
    activation = script.index("invocationActive := true", rejected_return)
    mutex_acquisition = script.index("mutexHandle := TryAcquireInvocationMutex()", activation)
    cross_host_rejection = script.index("if !mutexHandle", mutex_acquisition)
    window_observation = script.index('activeWindow := WinExist("A")')
    clipboard_capture = script.index("selectedText := CaptureSelectedText()")

    assert "static invocationActive := false" in script
    assert guard < notification < rejected_return < activation
    assert activation < mutex_acquisition < cross_host_rejection < window_observation
    assert window_observation < clipboard_capture


def test_cross_host_guard_is_nonblocking_and_released_after_every_action() -> None:
    script = Path("automation/windows/proofread-it.ahk").read_text(encoding="utf-8")

    assert '"Str", "Local\\ProofreadIt.Invocation"' in script
    assert '"Kernel32\\WaitForSingleObject", "Ptr", mutexHandle, "UInt", 0' in script
    assert "waitResult = 0x102" in script
    assert "waitResult = 0x80" in script
    assert 'ToolTip("Proofreading is already in progress.", , , 20)' in script

    acquisition = script.index("mutexHandle := TryAcquireInvocationMutex()")
    policy_check = script.index("RunCaptured(policyCommand")
    clipboard_capture = script.index("selectedText := CaptureSelectedText()")
    backend_run = script.index("RunCaptured(command")
    release = script.index("ReleaseInvocationMutex(mutexHandle)")
    local_release = script.index("invocationActive := false", release)

    assert acquisition < policy_check < clipboard_capture < backend_run < release < local_release
    assert 'if !DllCall("Kernel32\\ReleaseMutex", "Ptr", mutexHandle)' in script
    assert script.count('DllCall("Kernel32\\CloseHandle", "Ptr", mutexHandle)') == 2


def test_active_guard_is_released_and_duplicate_script_launch_is_ignored() -> None:
    script = Path("automation/windows/proofread-it.ahk").read_text(encoding="utf-8")

    activation = script.index("invocationActive := true")
    finally_block = script.index("} finally {", activation)
    release = script.index("invocationActive := false", finally_block)

    assert "#SingleInstance Ignore" in script
    assert "#MaxThreadsPerHotkey 2" in script
    assert activation < finally_block < release
