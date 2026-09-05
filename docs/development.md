# Development

Development uses `uv` with the repository-local `.venv`.

```powershell
uv sync --dev
uv run pytest
uv run ruff check .
uv run mypy src
```

## Running the desktop application

Install AutoHotkey v2, put the development API key in
`$env:USERPROFILE\.secrets\openai_token.txt`, then launch the application with:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

The launcher reads the key only for startup, injects it into the AutoHotkey/backend child process
tree, and restores the launcher's previous process environment immediately afterward. The script
automatically detects standard per-user and system AutoHotkey v2 installations. If AutoHotkey is in
a custom location, pass `-AutoHotkeyPath C:\path\to\AutoHotkey64.exe`. The script stays active and
exposes the development bindings:

- `Ctrl+Alt+E` sends a `proofread` / `show_full` request and opens the validated result window.
- `Ctrl+Alt+Shift+E` sends a `proofread` / `copy_final` request and places only the validated final
  text on the clipboard.

Each hotkey preserves the current clipboard, copies the selected text with the active application's
standard copy command, restores the clipboard, and passes non-empty text to the Python backend.
The backend loads the selected profile, builds one stateless strict-schema request, calls the OpenAI
Responses API, validates the returned corrections and final text, and performs the selected action.
If copying does not produce text within one second, the backend is not started and a concise error is
shown.

Every completed or failed API invocation is appended to `logs/proofread-it.jsonl`. The event contains
the selected text and source context, complete logical request, request duration, API status, model
output, raw API response, normalized result, or safe error detail. API keys and authorization fields are
redacted, but the remaining log is intentionally sensitive. Keep it private and delete it according
to your needs. The `logs/` directory is ignored by Git.

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

This command verifies process-local credential delivery and makes a real, billable OpenAI Responses
API request using the model and limits in `config/settings.json`. The network test checks the response
envelope and strict proofreading shape without asserting nondeterministic wording. A normal
`uv run pytest` remains offline, does not read the real secret file, and excludes tests marked `live`.
The application launcher uses the same process-local credential mechanism. Windows Credential
Manager integration is the first post-MVP task.
