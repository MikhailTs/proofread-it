# Windows acceptance

## Selected-text capture and invocation logging

1. Synchronize the local environment with `uv sync --dev`.
2. Start `automation/windows/proofread-it.ahk` with AutoHotkey v2.
3. Copy a recognizable clipboard sentinel such as `clipboard-before-capture`.
4. In another application, select non-empty multiline text containing non-ASCII characters, but do
   not copy it manually.
5. Press `Ctrl+Alt+E`. Confirm a `Proofread It` window opens with a placeholder explanation and the
   exact selected text under `Result`, then close it.
6. Inspect the last JSON line in `logs/proofread-it.jsonl`.
7. Paste into a scratch editor and confirm the original clipboard sentinel is pasted.
8. Repeat with `Ctrl+Alt+Shift+E`, then inspect the new last JSON line.
9. With no text selected, press either hotkey and confirm the concise error is shown and no log event
   is appended.

The first event must contain profile `proofread`, action `show_full`, the exact selected text, and the
focused window's process name and title. The result window must show both fields and remain readable
when resized. The second event must contain action `copy_final` and its exact selection. In both
successful cases, the clipboard content from before invocation must be restored. This slice makes no
API request; it deliberately presents the original text and a placeholder explanation.
