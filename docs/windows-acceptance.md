# Windows acceptance

## AutoHotkey invocation logging

1. Synchronize the local environment with `uv sync --dev`.
2. Start `automation/windows/proofread-it.ahk` with AutoHotkey v2.
3. Focus a window whose title and process name are easy to recognize.
4. Press `Ctrl+Alt+E`, then inspect the last JSON line in `logs/proofread-it.jsonl`.
5. Press `Ctrl+Alt+Shift+E`, then inspect the new last JSON line.

The first event must contain profile `proofread`, action `show_full`, and the focused window's
process name and title. The second must contain action `copy_final`. This slice has no other visible
application behavior.
