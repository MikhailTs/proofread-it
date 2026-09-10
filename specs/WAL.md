Updated: 2026-09-09T21:39:32Z

- WAL-Schema: `1`
- Checkpoint-ID: `aa479fd2-b415-43bd-9218-7ba107904d67`
- Task: Narrow API credential scope so the AutoHotkey process never receives the key, then complete `#Include` support.
- Active scope: The specification correction is isolated in commit `0309c60`. Credential-free AHK startup, per-invocation backend credential delivery, include-relative paths, derived tests/docs, and automated verification are complete; create the separate implementation commit. Manual Windows acceptance remains; push is out of scope.
- Authority: Project owner decisions in the current conversation on 2026-09-09, including approval of the per-invocation boundary and instruction to commit specification changes separately.
- Authoritative spec: `spec://proofreader/DESKTOP-ASSISTANT#api-access`, `spec://proofreader/DESKTOP-ASSISTANT#testability`, and `spec://proofreader/DESKTOP-ASSISTANT#mvp-scope`; file SHA-256 `12897ef9d39baa614852d187d71348eebb857ceb84bbcaa918a377a4bf063574` in commit `0309c60cd023e83982e2f52228bc3ef508d4a222`.
- Issue: `NONE`
- Assignment: `NONE`
- Phase: `IN_PROGRESS`

## Constraints

- The long-lived AutoHotkey automation or external host MUST NOT receive the API credential in its environment -> `spec://proofreader/DESKTOP-ASSISTANT#api-access`.
- The short-lived per-invocation wrapper reads `$env:USERPROFILE\.secrets\openai_token.txt` and injects the configured environment variable only into one backend invocation tree -> `spec://proofreader/DESKTOP-ASSISTANT#api-access`.
- Direct AHK launch and `#Include` MUST both work without a credential-bearing automation launcher -> approved architecture and API-access anchors.
- Implementation must be committed separately from `0309c60`; do not push -> current Project owner request.
- Preserve unrelated changes and use `uv` -> `AGENTS.md`.

## Checkpoint and evidence basis

- Repository/worktree/branch: `%USERPROFILE%/workspace/proofread-it`; `main`; HEAD `0309c60cd023e83982e2f52228bc3ef508d4a222`; observed `origin/main` `1c37b1e77f31c4a35ce9faf326339618a8371833`; no merge or rebase observed.
- Staged state is clean. Expected unstaged/untracked implementation paths excluding ACTIVE_WAL: `automation/windows/proofread-it.ahk`, `docs/development.md`, `docs/windows-acceptance.md`, `scripts/invoke.ps1`, `scripts/start.ps1`, `tests/component/test_app_invocation_wrapper.py`, `tests/component/test_app_launcher.py`, and `tests/windows/test_hotkeys.py`.
- Sorted implementation `path=SHA-256` manifest: `eaf01db0599a415cd93036cc119172173ab1e11c49d39f60883713c5690cca55`; retained pre-replacement WAL SHA-256 `c847b2b55e73e5ff29c21de2e38fa3ba781d55b22f6b7981cbaceab1f0ede369`.

## Boundaries

- Specs: Approved correction complete and separately committed as `0309c60 docs(spec): narrow API credential scope` with only the spec and its checkpoint WAL.
- Code: `scripts/start.ps1` starts AutoHotkey without reading or injecting the key; new `scripts/invoke.ps1` reads and injects it only for one short-lived backend invocation; AHK routes through that wrapper and resolves repository paths from `A_LineFile`.
- Tests: Sentinel integration coverage proves the simulated AHK host and unrelated child see no key, the selected fake backend sees it, unusable secret files prevent backend launch, and the sentinel is absent from arguments/output. Static contracts cover wrapper routing and absence of credential handling in AHK/startup.
- Documentation: Development and Windows acceptance instructions describe credential-free direct/include startup, per-invocation delivery, real billable calls, and correct clipboard outcomes.
- Verification on manifest `eaf01db0599a415cd93036cc119172173ab1e11c49d39f60883713c5690cca55`: `uv run --no-sync pytest -q tests/component/test_app_launcher.py tests/component/test_app_invocation_wrapper.py tests/windows/test_hotkeys.py` -> `13 passed`; direct AutoHotkey `/ErrorStdOut /Validate` -> exit `0`; disposable external include host checking settings/wrapper paths -> exit `0` and host removed; `uv run --no-sync pytest -q` -> `90 passed, 2 deselected`; `uv run --no-sync ruff check .` -> passed; `uv run --no-sync mypy src` -> passed for 25 source files; `git diff --check` -> exit `0` with line-ending warnings only.
- Human acceptance: Outstanding direct and external-include hotkey workflow using the real development credential; automated verification did not read it or make a billable request.
- Risk / REVIEW: The wrapper temporarily holds the key only in its short-lived process environment while invoking `uv`/Python and restores the previous value afterward. Interactive Windows behavior remains a human gate; no semantic decision is pending.

## Next action

- Action: Stage only the implementation/docs/tests and WAL, inspect the staged diff, and create the separate implementation commit.
- First command: `git add -- automation/windows/proofread-it.ahk docs/development.md docs/windows-acceptance.md scripts/invoke.ps1 scripts/start.ps1 specs/WAL.md tests/component/test_app_invocation_wrapper.py tests/component/test_app_launcher.py tests/windows/test_hotkeys.py`.
- Completion criterion: commit `fix(windows): isolate API credential from AHK host` contains no specification change, all post-commit paths are recorded, and manual acceptance remains explicitly pending.

- Blockers: `NONE`
- Pending decisions: `NONE`
- Temporary code/spec divergence: `NONE`
