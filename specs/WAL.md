Updated: 2026-09-09T17:52:45Z

- WAL-Schema: `1`
- Checkpoint-ID: `15eeedef-a098-4e8b-9b5f-84ec4752d819`
- Task: Narrow API credential scope so the AutoHotkey process never receives the key, then complete `#Include` support.
- Active scope: The approved specification correction is complete and ready for its required isolated commit. Per-invocation wrapper implementation, derived tests/docs, a separate implementation commit, and manual acceptance follow; push is out of scope.
- Authority: Project owner decisions in the current conversation on 2026-09-09, including explicit approval of the per-invocation boundary and instruction to commit specification changes separately.
- Authoritative spec: `spec://proofreader/DESKTOP-ASSISTANT#api-access`, `spec://proofreader/DESKTOP-ASSISTANT#testability`, and `spec://proofreader/DESKTOP-ASSISTANT#mvp-scope`; approved post-change file SHA-256 `12897ef9d39baa614852d187d71348eebb857ceb84bbcaa918a377a4bf063574`.
- Issue: `NONE`
- Assignment: `NONE`
- Phase: `IN_PROGRESS`

## Constraints

- The long-lived AutoHotkey automation or external host MUST NOT receive the API credential in its environment -> current Project owner decision and `spec://proofreader/DESKTOP-ASSISTANT#api-access`.
- A short-lived per-invocation wrapper MAY read `$env:USERPROFILE\.secrets\openai_token.txt` and inject the configured environment variable only into one Python backend process tree -> current Project owner decision and `spec://proofreader/DESKTOP-ASSISTANT#api-access`.
- Direct AHK launch and `#Include` MUST both work without a credential-bearing automation launcher -> approved architecture and API-access anchors.
- Specification changes MUST be committed separately from implementation changes; do not push -> current Project owner request.
- Preserve unrelated changes and use `uv` -> `AGENTS.md`.

## Checkpoint and evidence basis

- Repository/worktree/branch: `%USERPROFILE%/workspace/proofread-it`; `main`; HEAD `cbf9fc929164202fb22499235c446e46df7ebf7c`; observed `origin/main` `1c37b1e77f31c4a35ce9faf326339618a8371833`; no merge or rebase observed.
- Staged and non-ignored untracked state are clean. Expected unstaged paths excluding ACTIVE_WAL: `automation/windows/proofread-it.ahk`, `docs/windows-acceptance.md`, `specs/modules/proofreader/DESKTOP-ASSISTANT.md`, and `tests/windows/test_hotkeys.py`.
- Existing implementation-slice SHA-256 values remain AHK `317c5f00ae5b5c00856a6b1bd05cdd737b0f965d0f547f864097ef8a3ec6d168`, acceptance doc `440beafca2efe7967a20e5e373dc7f89b4b25dcf68d74fa1d4de3769d6bef0cd`, and hotkey test `d442e37bd9fa8382faae5015f908e3a0d09ad0c9b455ce45eb5665e895afa335`; retained pre-replacement WAL SHA-256 `7eba4285b0007a8f10da96b820d9e6b5a0b851b7e428b171e42e0e109b0fa72b`.

## Boundaries

- Specs: The three approved anchors now require backend-only per-invocation credential delivery, forbid key exposure to AutoHotkey/external hosts, and record the Project owner's correction in the semantic changelog.
- Code: `scripts/start.ps1` still injects the key before launching AHK and `automation/windows/proofread-it.ahk` still directly starts `uv`; implementation intentionally follows only after the isolated spec commit.
- Tests/docs: Current launcher tests and development/acceptance docs still encode the invalidated broader scope and must change in the implementation commit.
- Verification at 2026-09-09T17:52Z: `git diff --check -- specs/modules/proofreader/DESKTOP-ASSISTANT.md specs/WAL.md` -> exit `0` with line-ending warnings only; anchor scan -> `22` anchors, `22` unique, no duplicates; exact inbound-reference scan completed for all three changed anchors; spec diff inspection confirmed one semantic intent and an appended changelog entry.
- Risk / REVIEW: Semantic authority is explicit and no unresolved review remains. Credential implementation and previous related manual acceptance are intentionally stale until the next commit and verification.

## Next action

- Action: Stage only the approved specification and WAL, inspect the staged diff, and create the isolated specification commit.
- First command: `git add -- specs/modules/proofreader/DESKTOP-ASSISTANT.md specs/WAL.md`.
- Completion criterion: commit `docs(spec): narrow API credential scope` references all three full spec addresses and contains no implementation artifact.

- Blockers: `NONE`
- Pending decisions: `NONE`
- Temporary code/spec divergence: The approved spec now requires backend-only per-invocation credential delivery, while `scripts/start.ps1`, AHK invocation, credential tests, and docs retain the old credential-bearing AHK behavior; owner: Project owner; exit condition: complete and separately commit the implementation slice.
