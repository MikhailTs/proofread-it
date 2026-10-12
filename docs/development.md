# Development

Development uses `uv` with the repository-local `.venv`.

```powershell
uv sync --dev
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\check.ps1
```

The verification script fails fast and reports per-stage and total durations. It runs the offline
test suite, Ruff, mypy, and `git diff --check`. To run an individual check:

```powershell
uv run pytest
uv run ruff check .
uv run mypy src
```

## Git hooks

Enable the repository-managed hooks once after cloning:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-hooks.ps1
```

The installer sets the checkout-local `core.hooksPath` to `.githooks` and refuses to replace a
different existing value unless `-Force` is supplied. The `pre-commit` hook runs the fast offline
checks: whole-checkout Ruff and mypy followed by `git diff --cached --check` for the staged diff.
The `pre-push` hook runs the complete `scripts/check.ps1`, including the offline pytest suite.
Both hooks can be bypassed with Git's `--no-verify` option and therefore complement rather than
replace continuous integration.

The fast checks can also be run directly:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\check-fast.ps1
```

## Running the desktop application

Install AutoHotkey v2 and configure the API credential. The shipped schema-version-2 settings use
the generic Windows Credential Manager target `ProofreadIt/OpenAIApiKey`. Store or replace it through
the hidden interactive prompt:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\manage-credential.ps1 `
    -Action Set
```

Then launch the application with:

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
API request, including missing credentials and an empty selection, are also recorded
when the configured log path can be read. The event contains
the selected text and source context, complete logical request, request duration, API status, model
output, raw API response, normalized result, SDK retry observations, or safe error detail. Each item
in `retry_events` identifies the one-based retry number and whether it followed an HTTP response
(including its status code) or a transport failure with no response. Request bodies, headers, and
credentials are never copied into retry observations. API keys and authorization fields are redacted,
but the remaining log is intentionally sensitive. Keep it private and delete it according to your
needs. The `logs/` directory is ignored by Git.

## Development API credential

Python reads the configured credential directly after configuration, concurrency, source, profile,
and selection checks pass. The key is passed directly to the OpenAI client; AutoHotkey, PowerShell,
`uv`, command arguments, and process environment variables do not receive it.

To remove the configured generic credential, run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\manage-credential.ps1 `
    -Action Remove
```

The same entry can be managed manually in **Credential Manager → Windows Credentials → Generic
Credentials**. Use `ProofreadIt/OpenAIApiKey` as the Internet or network address,
`OPENAI_API_KEY` as the non-secret username label, and the API key as the password. If a custom
schema-version-2 settings file selects another `credential.target`, use that exact target instead.

The retained plaintext-file mode is explicit:

```json
"credential": {"source": "file"}
```

It reads `$env:USERPROFILE\.secrets\openai_token.txt` directly from Python. Existing schema-version-1
settings also select this file for compatibility; their `api_key_env` field is validated but no
longer used. Protect the file so only the current Windows user can read it, and never commit it.
There is no fallback: manager mode does not read the file when its target is missing, and file mode
does not read Credential Manager. Neither source is imported into or deleted from the other.

Run the live checks with:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\test-live.ps1
```

This command verifies direct credential resolution and makes a real, billable OpenAI Responses
API request using the model and limits in `config/settings.json`. The network test checks the response
envelope and strict proofreading shape without asserting nondeterministic wording. A normal
`uv run pytest` remains offline, reads neither real source, and excludes tests marked `live` or
`credential_store`. The native store round-trip uses only a unique temporary target and can be run
explicitly with:

```powershell
uv run --no-sync pytest -q -p no:cacheprovider -m credential_store `
    tests/windows/test_credential_store.py
```
