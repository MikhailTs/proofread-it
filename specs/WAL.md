Updated: 2026-09-16T20:38:01Z

- WAL-Schema: `1`
- Checkpoint-ID: `9aa59fc9-643e-4795-89c9-b535c61093ad`
- Task: Protect proofreading invocations from parallel execution.
- Active scope: The Project owner requested a shared AutoHotkey mutex for duplicate invocations across direct and `#Include` hosts. The local implementation, offline checks, Windows mutex process test, and acceptance instructions are complete; the owner reported that manual acceptance passed, the verified temporary #Include host was deleted, and a local commit is explicitly requested. No queueing, simultaneous requests, new dependency, unrelated MVP work, live API call, or push is authorized.
- Authority: Project owner request on 2026-09-16 to add the mutex, following the discussion of separate AutoHotkey host processes, plus the owner requests in the current conversation to create and then delete the temporary AHK host and make a local commit after manual acceptance.
- Authoritative spec: `spec://proofreader/DESKTOP-ASSISTANT#concurrency`, with dependencies `spec://proofreader/DESKTOP-ASSISTANT#architecture`, `spec://proofreader/DESKTOP-ASSISTANT#clipboard`, and `spec://proofreader/DESKTOP-ASSISTANT#testability`; observed spec SHA-256 `0bd561e289f1f83455b7ce52eb47d898ba9ead7eece172a19fb51cf59c04f98b`.
- Issue: `NONE`
- Assignment: `NONE`
- Phase: `IN_PROGRESS`

## Constraints

- Reject a duplicate AHK action before active-window observation, source check, selection capture, or clipboard mutation; do not queue it -> `spec://proofreader/DESKTOP-ASSISTANT#concurrency` and `spec://proofreader/DESKTOP-ASSISTANT#clipboard`.
- Direct execution and every `#Include` host must share the same guard; Python retains its independent backend lock -> `spec://proofreader/DESKTOP-ASSISTANT#architecture` and `spec://proofreader/DESKTOP-ASSISTANT#concurrency`.
- Preserve unrelated changes and use `uv`; commit and push require separate requests -> `AGENTS.md`.

## Checkpoint and evidence basis

- Repository/worktree/branch: `%USERPROFILE%/workspace/proofread-it`; `main`; HEAD `c3124ae33275ae35434e76071cb44d15d5da30b1`; no staged changes or merge/rebase observed. Expected unstaged paths excluding ACTIVE_WAL: `automation/windows/proofread-it.ahk`, `docs/development.md`, `docs/windows-acceptance.md`, `tests/windows/test_single_request.py`. Expected non-ignored untracked path: `tests/windows/test_ahk_invocation_mutex.py`.
- Tracked task patch excluding ACTIVE_WAL: Git patch hash `a4538755c5df3c4223cf39e95a3c487ab8adbf25`; untracked test Git blob `6c08221122876c737f6eafb24160f104c977f0e2`. Pre-replacement ACTIVE_WAL SHA-256: `e037488eec4f8060c07a1a24a443d72ec6c1417ef285620f4684f10b559f8b28`. The prior committed concurrency task and its owner-reported acceptance are historical evidence, not acceptance of this change.
- Relevant toolchain: repository-local `uv` environment, installed AutoHotkey v2 at `%USERPROFILE%/AppData/Local/Programs/AutoHotkey/v2/AutoHotkey64.exe`; no dependency change.
- Temporary acceptance host: `%USERPROFILE%/AppData/Local/Temp/proofread-it-acceptance-371722846a1246df8ffe9fb1be25bac8.ahk`, previously SHA-256 `1f6b2bd79cbfaa2639b10b03cc25fd3bf43af5e3e8984bf7a0916157f891c131`, was deleted at 2026-09-16T20:37Z after confirming its resolved path stayed within the system temp directory and its SHA-256 still matched. `Test-Path -LiteralPath` -> `False`. AutoHotkey v2 `/Validate /ErrorStdOut=UTF-8` had exited `0` before owner acceptance.

## Boundaries

- Specs: Existing approved `#concurrency` behavior covers early duplicate rejection; no semantic spec edit was made.
- Code: AHK obtains `Local\ProofreadIt.Invocation` non-blockingly before observing the window, checking source policy, or capturing text. A busy mutex yields a short tooltip without taking focus. The local guard remains for repeated hotkeys within one AHK process. The mutex is released and its handle closed in `finally`, while the Python backend lock remains unchanged.
- Tests: On the recorded implementation patch, `uv run --no-sync pytest -q` -> `130 passed, 2 deselected` at 2026-09-16T20:27Z. The new executable Windows test proves overlap rejection by a second included host, acquisition after termination of the owner, and acquisition after normal release. `uv run --no-sync ruff check .` -> passed; `uv run --no-sync mypy src` -> passed for 26 source files; AutoHotkey `/Validate /ErrorStdOut=UTF-8` -> exit `0`; `git diff --check` -> exit `0` with line-ending warnings only. The narrow mutex test was repeated after the final ReleaseMutex result check -> `4 passed`.
- Human acceptance: The Project owner reported `Ручная проверка пройдена` in the current conversation on 2026-09-16 for the documented cross-host Windows scenario. This is owner-reported acceptance, not an independently captured screen, clipboard, or API trace; this agent made no live API request.
- Risks / REVIEW: An already-running direct Python invocation, or a backend left running after its AHK host exits, can still reach AHK selection capture before the Python lock rejects it. The shared AHK mutex closes the separate-live-AHK-host gap but does not span those backend-only intervals. No semantic spec REVIEW is opened for the scoped mutex implementation.

## Next action

- Action: Stage only the scoped patch and create the owner-requested local commit with the full concurrency spec address.
- First command: `git add -- automation/windows/proofread-it.ahk docs/development.md docs/windows-acceptance.md specs/WAL.md tests/windows/test_single_request.py tests/windows/test_ahk_invocation_mutex.py`.
- Completion criterion: One local commit contains only the six scoped paths and `spec://proofreader/DESKTOP-ASSISTANT#concurrency` in its message; the temporary file stays absent and no push occurs.

- Blockers: `NONE`
- Pending decisions: `NONE` for the scoped mutex change; broader backend-only early exclusion remains outside this request.
- Temporary code/spec divergence: `spec://proofreader/DESKTOP-ASSISTANT#concurrency` requires any active-request duplicate to avoid capture. Direct backend activity and an orphaned backend after AHK exit are not covered before capture by this AHK-only mutex; owner must authorize a shared frontend/backend coordinator if that full boundary is required.
