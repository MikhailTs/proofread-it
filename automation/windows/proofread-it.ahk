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

    EnvSet("PROOFREAD_IT_SOURCE_PROCESS_NAME", processName)
    EnvSet("PROOFREAD_IT_SOURCE_WINDOW_TITLE", windowTitle)

    command := Format(
        'uv run --project "{1}" proofread-it --settings "{2}" --profile "{3}" --action "{4}"',
        ProjectRoot,
        SettingsPath,
        profile,
        action
    )
    Run(command, ProjectRoot, "Hide")
}
