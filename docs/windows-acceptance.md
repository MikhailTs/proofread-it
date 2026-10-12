# Windows acceptance

## Credential sources

The shipped schema-version-2 configuration selects Windows Credential Manager target `ProofreadIt/OpenAIApiKey`. Store or replace the key without placing it in command arguments:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\manage-credential.ps1 `
    -Action Set
```

Confirm the entry appears under **Credential Manager → Windows Credentials → Generic Credentials**. It may alternatively be created there manually with target `ProofreadIt/OpenAIApiKey`, username `OPENAI_API_KEY`, and the API key as its password. Neither method prints the key.

For fallback-boundary acceptance, keep a valid legacy file at `$env:USERPROFILE\.secrets\openai_token.txt`, temporarily remove the generic credential, and leave `credential.source` set to `windows_credential_manager`. Invoke proofreading and confirm it fails at stage `credential`, sends no API request, and does not use the file. Restore the generic credential, then change the settings object to `"credential": {"source": "file"}` and confirm an invocation succeeds from the file without reading Credential Manager. Restore the shipped manager object after the check. No test should copy or delete one source automatically because the other is selected.

## Selected-text capture and invocation logging

Successful hotkey invocations in this procedure make real, billable OpenAI Responses API requests using the model and limits in `config/settings.json`.

1. Synchronize the local environment with `uv sync --dev`.
2. Confirm the API key is available in the source explicitly selected by `credential.source`.
3. From the repository root, start `automation/windows/proofread-it.ahk` with the credential-free convenience launcher:

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\start.ps1
   ```

4. Copy a recognizable clipboard sentinel such as `clipboard-before-capture`.
5. In another application, select non-empty multiline text containing non-ASCII characters, but do not copy it manually.
6. Press `Ctrl+Alt+E`. Confirm a `Proofread It` window opens with corrections under `Explanation` and the complete corrected text under `Result`. No helper terminal should appear, receive focus, or trigger an active-window-changed notification.
7. Before copying from the result window, paste into a scratch editor and confirm the original clipboard sentinel is pasted.
8. Return to the result window, select part of either text field, press `Ctrl+C`, and confirm that exact selection can be pasted. Press `Ctrl+A` in the `Result` field and confirm `Ctrl+C` copies its complete text.
9. Click `Copy result` and confirm the complete corrected text can be pasted, then close the window.
10. Inspect the last JSON line in `logs/proofread-it.jsonl`.
11. Repeat with `Ctrl+Alt+Shift+E`, then inspect the new last JSON line.
12. With no text selected, press either hotkey and confirm the concise error is shown and exactly one `invocation_failed` event is appended with stage `selection`, no source text, and no API data.

The first event must contain profile `proofread` (selected through `settings.default_profile`), action `show_full`, the exact selected text, the focused window's process name and title, successful API diagnostics, and the normalized result. The result window must show both result fields and remain readable when resized. After `show_full`, the clipboard content from before invocation must be restored. The second event must contain action `copy_final`, its exact selection, successful API diagnostics, and the normalized result; after that invocation, the clipboard must contain only its normalized `final_text`.

## Parallel invocation protection

1. Copy a recognizable clipboard sentinel, select non-empty text in another application, and press `Ctrl+Alt+E`.
2. While that request is still running, press `Ctrl+Alt+E` and `Ctrl+Alt+Shift+E` again.
3. Before the original result window appears or closes, confirm each accepted duplicate hotkey thread immediately shows `Proofreading is already in progress.` and does not copy a new selection or change the clipboard sentinel.
4. Confirm the original request produces its one result and appends exactly one completed or failed invocation event; there must be no event or API request for a rejected duplicate.
5. While a request is active, start the same automation entry point again and confirm the existing process and request remain active rather than being replaced.
6. After the original request or result window ends, invoke either action again and confirm it is accepted normally. Repeat after a deliberately failed request to confirm the guard is released.

These checks exercise both action hotkeys and the lifecycle around success and failure. A separate host loaded through `#Include` also shares the AutoHotkey invocation mutex. To verify this boundary, keep the direct script running and start a temporary host with the same `#Include` plus a distinct test binding such as `^!q::Invoke("proofread", "copy_final")` to exercise an explicit profile override. While the direct host handles a request, press `Ctrl+Alt+Q`. Confirm the temporary host shows the in-progress tooltip without changing the active window, copying a selection, changing the clipboard, or sending another API request. After the first action ends, the temporary host must accept a new invocation. The offline test `tests/windows/test_ahk_invocation_mutex.py` separately checks mutex recovery when its owning AutoHotkey process exits. The backend lock at `concurrency.lock_path` remains the final guard for direct backend launches.

## Source exclusions

1. Copy a recognizable clipboard sentinel and note the current end of `logs/proofread-it.jsonl`.
2. Open a scratch editor with `password` as a separate word in its window title, select text, and press either proofreading hotkey.
3. Confirm the blocked-action notification appears, the clipboard sentinel remains unchanged, and exactly one `invocation_blocked` event is appended with a `window_title_word` match and no source text, logical request, API data, or response.
4. If KeePass is installed, repeat in `KeePass.exe` and confirm the event reports a `process_name` match for `KeePass.exe` with the same no-capture and no-API behavior.

These checks do not make a billable API request and do not access either credential source. Changing the lists under `context.exclusions` in `config/settings.json` must change the blocked sources after the file is saved, without an AutoHotkey source change.

## `#Include` compatibility

1. Stop the directly launched automation.
2. Create a temporary host script outside the repository with this content, replacing the include path with the absolute path to this checkout:

   ```ahk
   #Requires AutoHotkey v2.0
   #SingleInstance Force
   #Include "C:\path\to\proofread-it\automation\windows\proofread-it.ahk"
   ```

3. From the repository root, start the temporary host through the same credential-free launcher, replacing the host path as needed:

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\start.ps1 `
       -AutomationPath "C:\path\to\temporary-host.ahk"
   ```

4. Repeat the `Ctrl+Alt+E` and `Ctrl+Alt+Shift+E` checks above.

Both hotkeys must route the same profile and actions as the direct launch. Both invocations must load `config/settings.json` and run the backend from this repository rather than resolving either path relative to the temporary host script.

`scripts/start.ps1`, `scripts/invoke.ps1`, and either `.ahk` host do not read or inject the API credential. The automation startup does not read or inject the API credential. The per-invocation wrapper is credential-free as well. After the preflight gates pass, the short-lived Python backend reads exactly the selected source and passes the key directly to the OpenAI client without using a process environment variable.
