# Development

Development uses `uv` with the repository-local `.venv`.

```powershell
uv sync --dev
uv run pytest
uv run ruff check .
uv run mypy src
```

## Current invocation slice

Install AutoHotkey v2, then run `automation/windows/proofread-it.ahk`. The script stays active
and exposes the initial development bindings:

- `Ctrl+Alt+E` records a `proofread` / `show_full` invocation.
- `Ctrl+Alt+Shift+E` records a `proofread` / `copy_final` invocation.

Each hotkey preserves the current clipboard, copies the selected text with the active application's
standard copy command, restores the clipboard, and passes non-empty text to the Python backend.
The backend records the text together with the active process name and window title in one JSON
event in `logs/proofread-it.jsonl`, then exits. No API call or result display exists yet. If copying
does not produce text within one second, the backend is not started and a concise error is shown.

The log contains sensitive selected text and window titles now and will also contain model data in
later MVP slices. Keep it private and delete it according to your needs. The `logs/` directory is
ignored by Git.

## Development API credential

During MVP development, the API secret source is:

```text
$env:USERPROFILE\.secrets\openai_token.txt
```

Do not commit this file, copy the token into project configuration, pass it on a command line, or persist it in the Windows User or Machine environment. Restrict the file so that only the current Windows user can read it.

The development launcher and explicit live-test wrapper, once implemented, will read the file only when invoked and inject its value into the environment variable selected by settings (`OPENAI_API_KEY` by default) only for the launched application or test process tree. This covers starting the AutoHotkey entry point and its backend without creating a persistent User or Machine variable. A normal `uv run pytest` must remain offline, must not read this file, and must exclude live API tests. Windows Credential Manager integration is the first post-MVP task.
