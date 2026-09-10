#Requires AutoHotkey v2.0
#SingleInstance Force

SplitPath(A_LineFile, , &AutomationDir)
ProjectRoot := AutomationDir "\..\.."
SettingsPath := ProjectRoot "\config\settings.json"
InvokeScriptPath := ProjectRoot "\scripts\invoke.ps1"
SourceCheckCommand := 'uv run --project "' ProjectRoot '" --no-sync python -m proofread_it.source_check'

^!e::Invoke("proofread", "show_full")
^!+e::Invoke("proofread", "copy_final")

Invoke(profile, action) {
    global InvokeScriptPath, SettingsPath, SourceCheckCommand

    activeWindow := WinExist("A")
    processName := activeWindow ? WinGetProcessName("ahk_id " activeWindow) : ""
    windowTitle := activeWindow ? WinGetTitle("ahk_id " activeWindow) : ""

    EnvSet("PROOFREAD_IT_SOURCE_PROCESS_NAME", processName)
    EnvSet("PROOFREAD_IT_SOURCE_WINDOW_TITLE", windowTitle)
    try {
        policyCommand := Format(
            '{1} --settings "{2}" --profile "{3}" --action "{4}"',
            SourceCheckCommand,
            SettingsPath,
            profile,
            action
        )
        policyProcess := ComObject("WScript.Shell").Exec(policyCommand)
        policyOutput := policyProcess.StdOut.ReadAll()
        policyError := policyProcess.StdErr.ReadAll()
        if (policyProcess.ExitCode != 0) {
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

        command := Format(
            'powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "{1}" -SettingsPath "{2}" -Profile "{3}" -Action "{4}"',
            InvokeScriptPath,
            SettingsPath,
            profile,
            action
        )
        process := ComObject("WScript.Shell").Exec(command)
        correctedText := process.StdOut.ReadAll()
        errorText := process.StdErr.ReadAll()
        if (process.ExitCode != 0) {
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
        EnvSet("PROOFREAD_IT_SOURCE_PROCESS_NAME", "")
        EnvSet("PROOFREAD_IT_SOURCE_WINDOW_TITLE", "")
        EnvSet("PROOFREAD_IT_SOURCE_TEXT", "")
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
