#Requires AutoHotkey v2.0
#SingleInstance Force

ProjectRoot := A_ScriptDir "\..\.."
SettingsPath := ProjectRoot "\config\settings.json"

^!e::Invoke("proofread", "show_full")
^!+e::Invoke("proofread", "copy_final")

Invoke(profile, action) {
    global ProjectRoot, SettingsPath

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
        'uv run --project "{1}" proofread-it --settings "{2}" --profile "{3}" --action "{4}"',
        ProjectRoot,
        SettingsPath,
        profile,
        action
    )
    try {
        Run(command, ProjectRoot, "Hide")
    } finally {
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
