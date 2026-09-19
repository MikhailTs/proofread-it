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

The startup script does not read or inject the API credential. It only detects standard per-user and
system AutoHotkey v2 installations and starts the automation without the key in its environment. If
AutoHotkey is in a custom location, pass `-AutoHotkeyPath C:\path\to\AutoHotkey64.exe`. The
automation can also be started directly or loaded from an existing AutoHotkey v2 host with
`#Include`; all three modes expose the development bindings:

- `Ctrl+Alt+E` uses `default_profile` from `config/settings.json` with `show_full` and opens the
  validated result window.
- `Ctrl+Alt+Shift+E` uses the same default profile with `copy_final` and places only the
  validated final text on the clipboard.

The shipped default is `proofread`. Changing `default_profile` changes the profile used by both
hotkeys without editing the AutoHotkey script. A custom binding may still select a named profile
explicitly with `Invoke("profile_name", "show_full")`; `InvokeDefault("show_full")` uses the
configured default. The backend and source-check commands also use `default_profile` when
`--profile` is omitted, and `scripts/invoke.ps1` forwards `-Profile` only when supplied.

Each hotkey preserves the current clipboard, copies the selected text with the active application's
standard copy command, restores the clipboard, and passes non-empty text to the Python backend.
Before touching the clipboard, it checks the editable exclusion lists in `config/settings.json`.
`context.exclusions.process_names` contains exact executable basenames, while
`context.exclusions.window_title_words` contains whole words to match in window titles; both checks
ignore case. The shipped lists block `KeePass.exe` and any window title containing the word
`password`. Add, remove, or edit list entries to customize the blocked sources.
A blocked action shows a notification, logs the observed source and matched rule, and does not copy
the selection, read the API credential, or start the API backend.
If the active window, process, or title changes during the check, the action stops and asks the user
to select the text and try again.
Only one invocation may run at a time. A repeated hotkey is rejected immediately, before the active
window or clipboard is read, and shows a short tooltip with `Proofreading is already in progress.`
Direct execution and `#Include` hosts share the session-local Windows mutex
`Local\ProofreadIt.Invocation`, acquired before source checks or clipboard capture and released when
the action ends. The Python backend also holds the non-blocking operating-system lock configured by
`concurrency.lock_path`, so direct backend launches cannot overlap. The lock file is a persistent
coordination file; its presence alone does not mean an invocation is active, and it does not need to
be deleted after a normal or failed run.
The backend loads the selected profile, builds one stateless strict-schema request, calls the OpenAI
Responses API, validates the returned corrections and final text, and performs the selected action.
If copying does not produce text within one second, the backend is not started and a concise error is
shown.

Every completed or failed API invocation is appended to `logs/proofread-it.jsonl`. Failures before an
API request, including missing development credentials and an empty selection, are also recorded
when the configured log path can be read. The event contains
the selected text and source context, complete logical request, request duration, API status, model
output, raw API response, normalized result, SDK retry observations, or safe error detail. Each item
in `retry_events` identifies the one-based retry number and whether it followed an HTTP response
(including its status code) or a transport failure with no response. Request bodies, headers, and
credentials are never copied into retry observations. API keys and authorization fields are redacted,
but the remaining log is intentionally sensitive. Keep it private and delete it according to your
needs. The `logs/` directory is ignored by Git.

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
For each accepted hotkey action, `scripts/invoke.ps1` reads the credential file and injects the key
only into that short-lived backend invocation process tree. The long-lived AutoHotkey automation and
any external host never receive the key. The wrapper restores its previous process environment after
the backend exits. Windows Credential Manager integration is the first post-MVP task.
