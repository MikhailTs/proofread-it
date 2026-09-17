#Requires AutoHotkey v2.0
#SingleInstance Ignore

SplitPath(A_LineFile, , &AutomationDir)
ProjectRoot := AutomationDir "\..\.."
SettingsPath := ProjectRoot "\config\settings.json"
InvokeScriptPath := ProjectRoot "\scripts\invoke.ps1"
SourceCheckCommand := 'powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -Command uv run --project "' ProjectRoot '" --no-sync python -m proofread_it.source_check'

#MaxThreadsPerHotkey 2
^!e::InvokeDefault("show_full")
^!+e::InvokeDefault("copy_final")
#MaxThreadsPerHotkey 1

InvokeDefault(action) {
    Invoke("", action)
}

Invoke(profile, action) {
    static invocationActive := false
    global InvokeScriptPath, SettingsPath, SourceCheckCommand

    if invocationActive {
        NotifyConcurrentInvocation()
        return
    }
    invocationActive := true
    mutexHandle := 0
    try {
        mutexHandle := TryAcquireInvocationMutex()
        if !mutexHandle {
            NotifyConcurrentInvocation()
            return
        }

        activeWindow := WinExist("A")
        processName := activeWindow ? WinGetProcessName("ahk_id " activeWindow) : ""
        windowTitle := activeWindow ? WinGetTitle("ahk_id " activeWindow) : ""

        EnvSet("PROOFREAD_IT_SOURCE_PROCESS_NAME", processName)
        EnvSet("PROOFREAD_IT_SOURCE_WINDOW_TITLE", windowTitle)
        profileOption := profile = "" ? "" : ' --profile "' profile '"'
        policyCommand := Format(
            '{1} --settings "{2}"{3} --action "{4}"',
            SourceCheckCommand,
            SettingsPath,
            profileOption,
            action
        )
        policyExitCode := RunCaptured(policyCommand, &policyOutput, &policyError)
        if (policyExitCode != 0) {
            message := Trim(policyError)
            if (message = "") {
                message := "Proofreading is blocked for the active application or window."
            }
            MsgBox(message, "Proofread It", "Icon!")
            return
        }

        currentWindow := WinExist("A")
        currentProcessName := currentWindow ? WinGetProcessName("ahk_id " currentWindow) : ""
        currentWindowTitle := currentWindow ? WinGetTitle("ahk_id " currentWindow) : ""
        if (
            currentWindow != activeWindow
            || currentProcessName != processName
            || currentWindowTitle != windowTitle
        ) {
            MsgBox("The active window changed. Select the text and try again.", "Proofread It", "Icon!")
            return
        }

        selectedText := CaptureSelectedText()
        if (selectedText = "") {
            MsgBox("No selected text was detected.", "Proofread It", "Icon!")
            return
        }
        EnvSet("PROOFREAD_IT_SOURCE_TEXT", selectedText)

        profileOption := profile = "" ? "" : ' -Profile "' profile '"'
        command := Format(
            'powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "{1}" -SettingsPath "{2}"{3} -Action "{4}"',
            InvokeScriptPath,
            SettingsPath,
            profileOption,
            action
        )
        exitCode := RunCaptured(command, &correctedText, &errorText)
        if (exitCode != 0) {
            message := Trim(errorText)
            if (message = "") {
                message := "Proofreading failed. See the application log for details."
            }
            MsgBox(message, "Proofread It", "Icon!")
            return
        }
        if (action = "copy_final") {
            A_Clipboard := correctedText
        }
    } finally {
        try {
            EnvSet("PROOFREAD_IT_SOURCE_PROCESS_NAME", "")
            EnvSet("PROOFREAD_IT_SOURCE_WINDOW_TITLE", "")
            EnvSet("PROOFREAD_IT_SOURCE_TEXT", "")
        } finally {
            try {
                if mutexHandle {
                    ReleaseInvocationMutex(mutexHandle)
                }
            } finally {
                invocationActive := false
            }
        }
    }
}

TryAcquireInvocationMutex() {
    ; One name covers direct execution and every script that includes this file.
    mutexHandle := DllCall("Kernel32\CreateMutexW", "Ptr", 0, "Int", 0,
        "Str", "Local\ProofreadIt.Invocation", "Ptr")
    if !mutexHandle {
        throw Error("Cannot create the proofreading invocation mutex.")
    }

    waitResult := DllCall("Kernel32\WaitForSingleObject", "Ptr", mutexHandle, "UInt", 0, "UInt")
    if (waitResult = 0 || waitResult = 0x80) {
        return mutexHandle
    }
    DllCall("Kernel32\CloseHandle", "Ptr", mutexHandle)
    if (waitResult = 0x102) {
        return 0
    }
    throw Error("Cannot acquire the proofreading invocation mutex.")
}

ReleaseInvocationMutex(mutexHandle) {
    try {
        if !DllCall("Kernel32\ReleaseMutex", "Ptr", mutexHandle) {
            throw Error("Cannot release the proofreading invocation mutex.")
        }
    } finally {
        DllCall("Kernel32\CloseHandle", "Ptr", mutexHandle)
    }
}

NotifyConcurrentInvocation() {
    ToolTip("Proofreading is already in progress.", , , 20)
    SetTimer(HideConcurrentNotification, -2500)
}

HideConcurrentNotification() {
    ToolTip(, , , 20)
}

RunCaptured(command, &standardOutput, &standardError) {
    token := DllCall("GetCurrentProcessId") "-" A_TickCount "-" Random(100000, 999999)
    outputPath := A_Temp "\proofread-it-" token ".stdout"
    errorPath := A_Temp "\proofread-it-" token ".stderr"
    try {
        target := A_ComSpec ' /D /C ' command ' > "' outputPath '" 2> "' errorPath '"'
        exitCode := RunWait(target, , "Hide")
        standardOutput := FileExist(outputPath) ? FileRead(outputPath) : ""
        standardError := FileExist(errorPath) ? FileRead(errorPath) : ""
        return exitCode
    } finally {
        if FileExist(outputPath) {
            FileDelete(outputPath)
        }
        if FileExist(errorPath) {
            FileDelete(errorPath)
        }
    }
}

CaptureSelectedText() {
    clipboardBackup := ClipboardAll()
    try {
        A_Clipboard := ""
        Send("^c")
        if !ClipWait(1.0) {
            return ""
        }
        return A_Clipboard
    } finally {
        A_Clipboard := clipboardBackup
    }
}
