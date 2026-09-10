#Requires AutoHotkey v2.0
#SingleInstance Force

SplitPath(A_LineFile, , &AutomationDir)
ProjectRoot := AutomationDir "\..\.."
SettingsPath := ProjectRoot "\config\settings.json"
InvokeScriptPath := ProjectRoot "\scripts\invoke.ps1"

^!e::Invoke("proofread", "show_full")
^!+e::Invoke("proofread", "copy_final")

Invoke(profile, action) {
    global InvokeScriptPath, SettingsPath

    activeWindow := WinExist("A")
    processName := activeWindow ? WinGetProcessName("ahk_id " activeWindow) : ""
    windowTitle := activeWindow ? WinGetTitle("ahk_id " activeWindow) : ""
    selectedText := CaptureSelectedText()

    if (selectedText = "") {
        MsgBox("No selected text was detected.", "Proofread It", "Icon!")
        return
    }

    EnvSet("PROOFREAD_IT_SOURCE_PROCESS_NAME", processName)
    EnvSet("PROOFREAD_IT_SOURCE_WINDOW_TITLE", windowTitle)
    EnvSet("PROOFREAD_IT_SOURCE_TEXT", selectedText)

    command := Format(
        'powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "{1}" -SettingsPath "{2}" -Profile "{3}" -Action "{4}"',
        InvokeScriptPath,
        SettingsPath,
        profile,
        action
    )
    try {
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
