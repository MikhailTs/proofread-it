Updated: 2026-09-16T08:47:02Z

- WAL-Schema: `1`
- Checkpoint-ID: `8a856a3f-b178-4af2-b344-27fb4a505a66`
- Task: Protect proofreading invocations from parallel execution.
- Active scope: The approved one-active-request behavior is implemented and accepted at the AutoHotkey and Python backend boundaries, including immediate duplicate-hotkey feedback while child processes run, hidden helper consoles, schema-version-1 operational configuration, documentation, and offline automated verification. The Project owner explicitly requested a local commit of this work. No queueing, multiple simultaneous requests, dependency, unrelated MVP, push, or live-API change is authorized.
- Authority: Project owner requests in the current conversation on 2026-09-15 to implement protection from parallel launches and on 2026-09-16 to prepare its local commit.
- Authoritative spec: `spec://proofreader/DESKTOP-ASSISTANT#concurrency`, with scope dependencies `spec://proofreader/DESKTOP-ASSISTANT#architecture`, `spec://proofreader/DESKTOP-ASSISTANT#configuration`, `spec://proofreader/DESKTOP-ASSISTANT#interaction`, `spec://proofreader/DESKTOP-ASSISTANT#clipboard`, and `spec://proofreader/DESKTOP-ASSISTANT#testability`; observed file SHA-256 `0bd561e289f1f83455b7ce52eb47d898ba9ead7eece172a19fb51cf59c04f98b`.
- Issue: `NONE`
- Assignment: `NONE`
- Phase: `IN_PROGRESS`

## Constraints

- Permit at most one active request and reject later invocations without queueing -> `spec://proofreader/DESKTOP-ASSISTANT#concurrency`.
- Reject a repeated hotkey before selection capture or clipboard mutation and show a concise notification -> `spec://proofreader/DESKTOP-ASSISTANT#concurrency` and `spec://proofreader/DESKTOP-ASSISTANT#clipboard`.
- Preserve direct and `#Include` AutoHotkey operation while keeping Windows behavior in the automation/adapter boundaries -> `spec://proofreader/DESKTOP-ASSISTANT#architecture`.
- Keep default verification offline and credential-free; separately cover the Windows single-request boundary -> `spec://proofreader/DESKTOP-ASSISTANT#testability`.
- Preserve unrelated changes, use `uv`, commit only the scoped paths, and do not push -> `AGENTS.md` and current request boundary.

## Checkpoint and evidence basis

- Repository/worktree/branch: `%USERPROFILE%/workspace/proofread-it`; `main`; HEAD `8520d3820cdcdc9311a38a82caeef1433ebc0aef`; observed `origin/main` `aaac5d52c9cd3b8a5b0303e5a6bf5ce61efe5acd`; branch is ahead by two commits; no merge or rebase observed.
- Index is clean. Expected unstaged paths are `automation/windows/proofread-it.ahk`, `config/settings.json`, `docs/development.md`, `docs/windows-acceptance.md`, `specs/WAL.md`, `src/proofread_it/cli.py`, `src/proofread_it/concurrency.py`, `src/proofread_it/config/loader.py`, `src/proofread_it/config/schemas.py`, `tests/component/test_app_invocation_wrapper.py`, `tests/component/test_cli_contract.py`, `tests/component/test_live_test_wrapper.py`, `tests/component/test_source_check.py`, `tests/component/test_workflow.py`, `tests/integration/test_config_files.py`, `tests/unit/test_config.py`, `tests/unit/test_openai_provider.py`, `tests/unit/test_request_builder.py`, `tests/windows/test_clipboard.py`, `tests/windows/test_hotkeys.py`, and `tests/windows/test_single_request.py`. The sole non-ignored untracked path is the expected `tests/unit/test_concurrency.py`.
- Dirty tracked implementation/docs/test diff fingerprint excluding ACTIVE_WAL: Git patch hash `f10e6e38a2efa8d729e364ee8852f030219ab4c5`. Untracked concurrency-test fingerprint: Git blob `c6a0341098fbf82f8bd5618abd326969d5a7b65a`, SHA-256 `3c5bebcf98f403068e105b7d440cd0767c313444bc1c4f39662deef3291bd9a3`. Retained pre-replacement WAL SHA-256: `006d060c8fbd25042556d1e87fd6c4deb9503a3042d6ccf8dbf7dde58c117615`.
- Relevant installed dependency: locked and installed `openai==3.8.0`; no new dependency is planned.

## Boundaries

- Specs: The approved concurrency behavior is explicit and implementable; no semantic spec edit is planned.
- Code: AutoHotkey permits one duplicate thread so it can show the concise rejection before observing the window or clipboard, resets the local guard in `finally`, and ignores replacement launches. Child commands use interruptible `RunWait(..., "Hide")` instead of blocking COM pipe reads; stdout/stderr are captured through unique temporary files and removed in `finally`. Both helpers also request hidden PowerShell windows. The Python CLI holds a configured non-blocking Windows byte-range lock for the complete invocation and returns distinct exit code `11` when another process owns it. OS process termination releases the lock; the coordination file intentionally remains.
- Tests: Unit coverage proves nested and real cross-process exclusion plus release after failure. Component coverage proves backend rejection before credential read/provider construction. Static Windows boundary coverage proves rejection precedes window/clipboard work, guard release is in `finally`, both helper commands are hidden, and no blocking `StdOut.ReadAll()` remains. AutoHotkey `/Validate` accepts the script.
- Documentation: Development guidance documents `concurrency.lock_path` and persistent-file semantics. Windows acceptance now covers both action hotkeys, clipboard preservation, one-result behavior, duplicate script launch, and release after success/failure.
- Verification on tracked patch `f10e6e38a2efa8d729e364ee8852f030219ab4c5` plus untracked test blob `c6a0341098fbf82f8bd5618abd326969d5a7b65a` at 2026-09-16T08:47Z: `uv run --no-sync pytest -q` -> `128 passed, 2 deselected`; `uv run --no-sync ruff check .` -> passed; `uv run --no-sync mypy src` -> passed for 26 source files; `git diff --check` -> exit `0` with line-ending warnings only. Installed AutoHotkey v2 `/Validate /ErrorStdOut=UTF-8` -> exit `0` on the same implementation patch at 2026-09-15T18:43Z.
- Human acceptance: The Project owner reported `Ручная проверка пройдена` in the current conversation on 2026-09-16 after the requested Windows retest of immediate duplicate notification, unchanged clipboard/API behavior for rejected invocations, and the existing non-ASCII result sample. This is owner-reported acceptance, not an independently recorded screen or API trace.
- Risk / REVIEW: Temporary capture-file decoding relies on the current Windows process output encoding; the owner-reported manual pass covers the existing non-ASCII acceptance sample on this checkout. The lock is Windows-specific by approved MVP scope. No semantic spec REVIEW is open.

## Next action

- Action: Stage only the scoped paths, inspect the staged diff, and create the explicitly requested local commit with the full `spec://proofreader/DESKTOP-ASSISTANT#concurrency` address.
- First command: `git add -- automation/windows/proofread-it.ahk config/settings.json docs/development.md docs/windows-acceptance.md specs/WAL.md src/proofread_it/cli.py src/proofread_it/concurrency.py src/proofread_it/config/loader.py src/proofread_it/config/schemas.py tests/component/test_app_invocation_wrapper.py tests/component/test_cli_contract.py tests/component/test_live_test_wrapper.py tests/component/test_source_check.py tests/component/test_workflow.py tests/integration/test_config_files.py tests/unit/test_concurrency.py tests/unit/test_config.py tests/unit/test_openai_provider.py tests/unit/test_request_builder.py tests/windows/test_clipboard.py tests/windows/test_hotkeys.py tests/windows/test_single_request.py`.
- Completion criterion: One local commit contains only the accepted task paths and the specification reference; no push, live API request, or unrelated MVP change occurs.

- Blockers: `NONE`
- Pending decisions: `NONE`
- Temporary code/spec divergence: `NONE`
