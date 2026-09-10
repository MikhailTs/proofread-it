# Windows acceptance

## Selected-text capture and invocation logging

Successful hotkey invocations in this procedure make real, billable OpenAI Responses API requests
using the model and limits in `config/settings.json`.

1. Synchronize the local environment with `uv sync --dev`.
2. Confirm the development API key is stored in
   `$env:USERPROFILE\.secrets\openai_token.txt`.
3. From the repository root, start `automation/windows/proofread-it.ahk` with the credential-free
   convenience launcher:

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\start.ps1
   ```

4. Copy a recognizable clipboard sentinel such as `clipboard-before-capture`.
5. In another application, select non-empty multiline text containing non-ASCII characters, but do
   not copy it manually.
6. Press `Ctrl+Alt+E`. Confirm a `Proofread It` window opens with corrections under `Explanation`
   and the complete corrected text under `Result`, then close it.
7. Inspect the last JSON line in `logs/proofread-it.jsonl`.
8. Paste into a scratch editor and confirm the original clipboard sentinel is pasted.
9. Repeat with `Ctrl+Alt+Shift+E`, then inspect the new last JSON line.
10. With no text selected, press either hotkey and confirm the concise error is shown and no log event
   is appended.

The first event must contain profile `proofread`, action `show_full`, the exact selected text, the
focused window's process name and title, successful API diagnostics, and the normalized result. The
result window must show both result fields and remain readable when resized. After `show_full`, the
clipboard content from before invocation must be restored. The second event must contain action
`copy_final`, its exact selection, successful API diagnostics, and the normalized result; after that
invocation, the clipboard must contain only its normalized `final_text`.

## Source exclusions

1. Copy a recognizable clipboard sentinel and note the current end of `logs/proofread-it.jsonl`.
2. Open a scratch editor with `password` as a separate word in its window title, select text, and
   press either proofreading hotkey.
3. Confirm the blocked-action notification appears, the clipboard sentinel remains unchanged, and
   exactly one `invocation_blocked` event is appended with a `window_title_word` match and no source
   text, logical request, API data, or response.
4. If KeePass is installed, repeat in `KeePass.exe` and confirm the event reports a `process_name`
   match for `KeePass.exe` with the same no-capture and no-API behavior.

These checks do not make a billable API request and do not require the development credential file.
Changing the lists under `context.exclusions` in `config/settings.json` must change the blocked
sources after the file is saved, without an AutoHotkey source change.

## `#Include` compatibility

1. Stop the directly launched automation.
2. Create a temporary host script outside the repository with this content, replacing the include
   path with the absolute path to this checkout:

   ```ahk
   #Requires AutoHotkey v2.0
   #SingleInstance Force
   #Include "C:\path\to\proofread-it\automation\windows\proofread-it.ahk"
   ```

3. From the repository root, start the temporary host through the same credential-free launcher,
   replacing the host path as needed:

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\start.ps1 `
       -AutomationPath "C:\path\to\temporary-host.ahk"
   ```

4. Repeat the `Ctrl+Alt+E` and `Ctrl+Alt+Shift+E` checks above.

Both hotkeys must route the same profile and actions as the direct launch. Both invocations must load
`config/settings.json` and run the backend from this repository rather than resolving either path
relative to the temporary host script.

`scripts/start.ps1` does not read or inject the API credential; either `.ahk` file may instead be
started normally with AutoHotkey v2. Only the per-invocation wrapper reads the secret, after a hotkey
action has been accepted, and exposes it to that short-lived backend process tree.
