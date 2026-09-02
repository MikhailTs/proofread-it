# Development

Development uses `uv` with the repository-local `.venv`.

```powershell
uv sync --dev
uv run pytest
uv run ruff check .
uv run mypy src
```

The current source and test modules are placeholders only.

## Development API credential

During MVP development, the API secret source is:

```text
$env:USERPROFILE\.secrets\openai_token.txt
```

Do not commit this file, copy the token into project configuration, pass it on a command line, or persist it in the Windows User or Machine environment. Restrict the file so that only the current Windows user can read it.

The development launcher and explicit live-test wrapper, once implemented, will read the file only when invoked and inject its value into the environment variable selected by settings (`OPENAI_API_KEY` by default) only for the launched application or test process tree. This covers starting the AutoHotkey entry point and its backend without creating a persistent User or Machine variable. A normal `uv run pytest` must remain offline, must not read this file, and must exclude live API tests. Windows Credential Manager integration is the first post-MVP task.
