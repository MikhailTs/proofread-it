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

- `Ctrl+Alt+E` records a `proofread` / `show_full` invocation and opens the result window.
- `Ctrl+Alt+Shift+E` records a `proofread` / `copy_final` invocation.

Each hotkey preserves the current clipboard, copies the selected text with the active application's
standard copy command, restores the clipboard, and passes non-empty text to the Python backend.
The backend records the text together with the active process name and window title in one JSON
event in `logs/proofread-it.jsonl`. For `show_full`, it then opens a minimal result window with a
placeholder explanation and the original selected text as the temporary result. No API call is made
yet, and `copy_final` does not change the clipboard in this slice. If copying does not produce text
within one second, the backend is not started and a concise error is shown.

The log contains sensitive selected text and window titles now and will also contain model data in
later MVP slices. Keep it private and delete it according to your needs. The `logs/` directory is
ignored by Git.

## Development API credential

During MVP development, the API secret source is:

```text
$env:USERPROFILE\.secrets\openai_token.txt
```

Do not commit this file, copy the token into project configuration, pass it on a command line, or persist it in the Windows User or Machine environment. Restrict the file so that only the current Windows user can read it.

The explicit live-test wrapper reads the file only when invoked and injects its value into the environment variable selected by settings (`OPENAI_API_KEY` by default) only for its test process tree. It never creates a persistent Windows User or Machine variable. Run the live checks with:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\test-live.ps1
```

This command verifies process-local credential delivery and makes a real, billable OpenAI Responses API request using the model and limits in `config/settings.json`. The network test checks the response envelope and strict proofreading shape without asserting nondeterministic wording. A normal `uv run pytest` remains offline, does not read the real secret file, and excludes tests marked `live`. API sending is not connected to the desktop workflow yet; the application launcher will use the same process-local credential mechanism when that integration is implemented. Windows Credential Manager integration is the first post-MVP task.
