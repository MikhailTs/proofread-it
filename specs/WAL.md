Updated: 2026-09-10T18:31:15Z

- WAL-Schema: `1`
- Checkpoint-ID: `43c7e05c-40ea-4ab9-9dd0-291c4a5b31f9`
- Task: Add configurable source exclusions with initial KeePass and password-title rules.
- Active scope: The authorized exclusion-list contract, implementation, documentation, automated verification, and required manual acceptance are complete. The `KeePass.exe` manual path is explicitly deferred; create the requested local commit. Push is out of scope.
- Authority: Project owner request in the current conversation on 2026-09-10 to initially block `KeePass.exe` and windows whose title contains the word `password`, with both lists editable through settings; Project owner confirmation that the password-title manual test passed, instruction to skip the `KeePass.exe` manual check for now, and explicit request to commit these changes.
- Authoritative spec: `spec://proofreader/DESKTOP-ASSISTANT#configuration`, `spec://proofreader/DESKTOP-ASSISTANT#context-policy`, `spec://proofreader/DESKTOP-ASSISTANT#logging`, and `spec://proofreader/DESKTOP-ASSISTANT#mvp-scope`; authorized post-change file SHA-256 `0bd561e289f1f83455b7ce52eb47d898ba9ead7eece172a19fb51cf59c04f98b`.
- Issue: `NONE`
- Assignment: `NONE`
- Phase: `IN_PROGRESS`

## Constraints

- Exclusion decisions occur before selection capture and cause zero API transmission -> `spec://proofreader/DESKTOP-ASSISTANT#context-policy`.
- Blocked invocations log observed source identity and the matched rule, with no source text, request, or response -> `spec://proofreader/DESKTOP-ASSISTANT#logging`.
- The initial editable configuration blocks exact process basename `KeePass.exe` and the whole word `password` in a window title, both case-insensitively -> current Project owner request; exact matching semantics are the smallest conservative interpretation of "process" and "word".
- Direct AHK execution and `#Include` operation must retain equivalent behavior without exposing the API credential -> `spec://proofreader/DESKTOP-ASSISTANT#architecture` and `spec://proofreader/DESKTOP-ASSISTANT#api-access`.
- Preserve unrelated changes, use `uv`, and do not commit or push -> `AGENTS.md` and current request boundary.

## Checkpoint and evidence basis

- Repository/worktree/branch: `%USERPROFILE%/workspace/proofread-it`; `main`; HEAD and observed `origin/main` `aaac5d52c9cd3b8a5b0303e5a6bf5ce61efe5acd`; no merge or rebase observed.
- Staged and non-ignored untracked state are clean. Before this replacement, the only unstaged path was the completed prior task checkpoint `specs/WAL.md`; retained prior WAL SHA-256 `52f2a2c9cbb8a2b3589938a827ddcc236e966a5b4bd3beac280cf9d8cf52fb71`.
- Expected changed paths excluding ACTIVE_WAL: 20 paths comprising `automation/windows/proofread-it.ahk`, `config/settings.json`, `docs/development.md`, `docs/windows-acceptance.md`, the addressed specification, six source files, and nine test files. Sorted `path=SHA-256` manifest hash: `21cfa1fd62e881c0bf448ade793aecc395a091b58a724255c92d6ccd32c65be1`; authoritative spec hash remains `0bd561e289f1f83455b7ce52eb47d898ba9ead7eece172a19fb51cf59c04f98b`.

## Boundaries

- Specs: The approved configuration and context-policy anchors now define editable process-name and window-title-word lists, deterministic matching and precedence, initial values, pre-capture enforcement, blocked logging, and credential independence. `git diff --check -- specs/modules/proofreader/DESKTOP-ASSISTANT.md` -> exit `0` with line-ending warning only at 2026-09-10T15:22:03Z.
- Code: Shipped settings contain `KeePass.exe` and `password`; typed loading validates both editable lists; the pure matcher implements deterministic case-insensitive basename and whole-word rules; a credential-free source check logs blocked invocations; AHK runs it before capture and aborts if the observed active window changes; the main CLI checks again before credential/provider construction.
- Tests: Unit and component coverage exercises configuration errors, matching/non-matching/precedence, blocked log shape, absence of source text, credential independence, API-provider non-construction, and AHK ordering/window-stability guards. The first full run exposed one legacy live-wrapper fixture missing the now-required exclusions object; that fixture was updated and the repeated full run passed.
- Documentation: Development customization and manual Windows source-exclusion acceptance are documented.
- Verification on manifest `21cfa1fd62e881c0bf448ade793aecc395a091b58a724255c92d6ccd32c65be1`: `uv run --no-sync pytest -q` -> `112 passed, 2 deselected`; `uv run --no-sync ruff check .` -> passed; `uv run --no-sync mypy src` -> passed for 26 source files; AutoHotkey v2 `/ErrorStdOut /Validate automation/windows/proofread-it.ahk` -> exit `0`; `git diff --check` -> exit `0` with line-ending warnings only; exact anchor search found one `#configuration` and one `#context-policy` anchor.
- Human acceptance: Project owner confirmed on 2026-09-10 that the password-title rule passed manual Windows testing and explicitly deferred the `KeePass.exe` process-name manual path. Configurability and process-name behavior remain covered by automated tests.
- Risk / REVIEW: The `KeePass.exe` path is not manually exercised, by explicit Project owner deferral. The separate preflight adds startup latency and an unavoidable narrow focus-change boundary; explicit window/process/title stability checks fail closed before capture, and the backend rechecks the original metadata before credential or provider creation. No semantic REVIEW is open.

## Next action

- Action: Stage exactly the 20 task paths plus ACTIVE_WAL, inspect the staged diff, and create the proposed spec-addressed commit.
- First command: `git add --` with the explicit task path list.
- Completion criterion: One local commit contains only this source-exclusion task, its specification and checkpoint; the post-commit worktree is clean and push remains unperformed.

- Blockers: `NONE`
- Pending decisions: `NONE`
- Temporary code/spec divergence: `NONE`
