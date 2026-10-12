Updated: 2026-10-12T12:49:20Z

- WAL-Schema: 1
- Checkpoint-ID: 57764537-9c68-4f90-b240-b163df261dd2
- Task: Make Python read the OpenAI API key directly from Windows Credential Manager while retaining the legacy key-file source.
- Active scope: Approved credential contract, schema version 2 and legacy version 1, direct Python resolution and management, credential-free launchers, tests, and current documentation. No new dependency, commit, push, release, or unrelated feature is authorized.
- Authority: Project owner request on 2026-10-10 to implement the approved direct-Python Credential Manager plan, including schema-version-1 file compatibility and no automatic fallback.
- Authoritative spec: spec://proofreader/DESKTOP-ASSISTANT#constraints, spec://proofreader/DESKTOP-ASSISTANT#configuration, spec://proofreader/DESKTOP-ASSISTANT#api-access, spec://proofreader/DESKTOP-ASSISTANT#credential-storage, spec://proofreader/DESKTOP-ASSISTANT#testability, and spec://proofreader/DESKTOP-ASSISTANT#mvp-scope. Current specification SHA-256 9D57BA1E0D93C228A871666849C886677A910205DF680B24E597151B0BD28132.
- Issue: NONE
- Assignment: NONE
- Phase: READY

## Constraints

- Preserve pre-capture exclusions, direct and #Include automation behavior, credential-safe logging, and one-request semantics -> addressed spec anchors.
- Credential Manager is the shipped schema-version-2 default; schema version 1 and explicit file mode use the fixed user-profile file; never fall back between sources -> approved specification.
- The API key must not pass through PowerShell, uv arguments, process environment, configuration, stdout, or JSONL -> approved specification.
- Use uv and existing dependencies; do not commit or push -> AGENTS.md and Project owner request.

## Checkpoint and evidence basis

- Repository/worktree/branch: C:/Users/tsare/workspace/proofread-it; main; HEAD a26fdfe22b5dd22460375bc60ed9a86e51287395; origin/main matched HEAD at 2026-10-12T12:49:20Z. No staged changes or merge/rebase state.
- Expected modified paths excluding this WAL: config/settings.json; docs/development.md, docs/release-checklist.md, docs/windows-acceptance.md; pyproject.toml; scripts/invoke.ps1, scripts/test-live.ps1, scripts/manage-credential.ps1; specs/modules/proofreader/DESKTOP-ASSISTANT.md; src/proofread_it/cli.py, config/loader.py, config/schemas.py, credential_cli.py, invocation_failure.py, providers/credentials.py; affected component/integration/live/unit/windows tests.
- Dirty-state fingerprint: SHA-256 73F282EB361976333E7AC884B255EA85D850519F1C37768F54E683E4EEAAC7DE over `git diff --binary -- . ':(exclude)specs/WAL.md'` followed by the labeled bytes of the four new task files in sorted order. Untracked `.codex/config.toml` is unrelated and explicitly excluded/preserved.
- Toolchain/dependencies: uv with the existing pyproject.toml and uv.lock; no production dependency or lockfile change.

## Boundaries and verification

- Specs: Contract and semantic changelog define schema v2, direct Python WCM/file resolution, schema-v1 file compatibility, no fallback, credential-free launchers, management operations, and verification. Node repository anchor scan at 2026-10-11T20:53:00Z found 23 unique anchors, 144 references, and no unresolved references.
- Code: Python resolves the selected source only after configuration/concurrency/source/profile/selection checks; Win32 access is isolated behind a mockable adapter, frees successful reads in `finally`, and management prompts with `getpass`. PowerShell handles no credential material.
- Tests: `uv run --no-sync pytest -q -p no:cacheprovider` -> 171 passed, 3 deselected; `uv run --no-sync pytest -q -p no:cacheprovider -m credential_store tests/windows/test_credential_store.py` -> 1 passed and the unique temporary credential was deleted; `uv run --no-sync ruff check .` -> passed; `uv run --no-sync mypy src` -> passed for 28 source files; PowerShell parser for the three credential-related scripts -> passed; `git diff --check` -> passed. Results observed on this fingerprint at 2026-10-11T20:53:00Z.
- Human acceptance: Project owner reported on 2026-10-12 that the documented manual Windows acceptance passed, closing the WCM mode, file mode, live-request, hotkey, and no-fallback acceptance boundary.
- Risks / REVIEW: Generic credentials remain accessible to applications under the same user, and the API key necessarily exists in Python/SDK managed memory during a request. The native test's workspace-local Windows cache artifacts were inspected and removed; no credential remained. REVIEW: NONE.

## Next action

- Action: Preserve the verified READY checkout until the Project owner separately requests a commit or another task.
- First command: NONE — no further command is authorized by the current request.
- Completion criterion: The READY checkpoint remains unchanged and is handed off without committing or pushing.

- Blockers: NONE
- Pending decisions: NONE
- Temporary code/spec divergence: NONE
