Updated: 2026-09-17T10:36:50Z

- WAL-Schema: 1
- Checkpoint-ID: afa49789-03c0-49da-9943-ddf15733b371
- Task: Use the configured default proofreading profile when an invocation omits a profile.
- Active scope: Make profile selection optional for shipped AutoHotkey hotkeys, the per-invocation PowerShell wrapper, backend CLI, and pre-capture source-check CLI. Preserve explicit profile overrides. Update approved interaction/configuration anchors, tests, and desktop documentation. The project owner reports manual acceptance passed and has requested a local commit of the scoped diff. No additional profile, dependency, or push is in scope.
- Authority: Project owner request on 2026-09-17 to address mandatory profile selection, the owner report in the current conversation on 2026-09-17 that manual verification passed, and the subsequent owner request to prepare a local commit.
- Authoritative spec: spec://proofreader/DESKTOP-ASSISTANT#proofreading-profile and spec://proofreader/DESKTOP-ASSISTANT#product-workflow; changed anchors spec://proofreader/DESKTOP-ASSISTANT#configuration and spec://proofreader/DESKTOP-ASSISTANT#interaction. Observed edited specification SHA-256 7B9E11367E1FAB62E4E5123F130BE9DEEE427494D8F3197F13ECD1136BF2FFBE.
- Issue: NONE
- Assignment: NONE
- Phase: IN_PROGRESS

## Constraints

- Omitted profile uses settings.default_profile; explicit profile wins. Source-check and backend logging use the resolved name -> addressed spec anchors and owner request.
- Preserve credential isolation, pre-capture source exclusion, and explicit custom AHK bindings -> spec://proofreader/DESKTOP-ASSISTANT#api-access, spec://proofreader/DESKTOP-ASSISTANT#context-policy, spec://proofreader/DESKTOP-ASSISTANT#interaction.
- Use uv; preserve unrelated changes; the owner has requested this local commit, while push still requires a separate request -> AGENTS.md.

## Checkpoint and evidence basis

- Repository/worktree/branch: %USERPROFILE%/workspace/proofread-it; main; HEAD aaa69a0a5527ef0e0e4176bb05824e0ac9b485e5; origin/main aaac5d52c9cd3b8a5b0303e5a6bf5ce61efe5acd, branch ahead four. No staged or non-ignored untracked paths; no merge/rebase observed.
- Expected unstaged paths excluding ACTIVE_WAL: automation/windows/proofread-it.ahk, docs/development.md, docs/windows-acceptance.md, scripts/invoke.ps1, specs/modules/proofreader/DESKTOP-ASSISTANT.md, src/proofread_it/cli.py, src/proofread_it/source_check.py, tests/component/test_app_invocation_wrapper.py, tests/component/test_cli_contract.py, tests/component/test_source_check.py, tests/windows/test_hotkeys.py. Revalidated Git patch fingerprint: git diff --binary -- . ':(exclude)specs/WAL.md' | git hash-object --stdin -> 21ec29d02d0b6598705b9f639245aeb2d6a72853 at 2026-09-17T10:19:50Z. Pre-replacement ACTIVE_WAL SHA-256: 5A12080A5F1D18CD6C64F0EBE8AFFAB775D0E39F971AA050449B8EEFF37DA6A1.
- Relevant toolchain: repository-local uv environment and installed AutoHotkey v2 at %USERPROFILE%/AppData/Local/Programs/AutoHotkey/v2/AutoHotkey64.exe; pyproject.toml and uv.lock unchanged. The agent made no live API request or credential read.

## Boundaries

- Specs: Owner-authorized change applied to approved configuration and interaction anchors, with 2026-09-17 semantic changelog entry. Configured-default resolution was already required by the proofreading-profile and product-workflow anchors.
- Code: Shipped hotkeys use InvokeDefault; existing explicit Invoke(profile, action) bindings remain supported. AHK omits profile flags for default invocations. Wrapper forwards -Profile only when supplied. Backend and source-check CLIs resolve omissions from settings.default_profile.
- Automated verification on unchanged scoped patch: uv run --no-sync pytest -q tests/component/test_cli_contract.py tests/component/test_source_check.py tests/component/test_app_invocation_wrapper.py tests/windows/test_hotkeys.py -> 23 passed (2026-09-17); uv run --no-sync pytest -q -> 134 passed, 2 deselected (2026-09-17); uv run --no-sync ruff check . -> passed; uv run --no-sync mypy src -> passed for 26 source files; AutoHotkey64.exe /Validate /ErrorStdOut=UTF-8 automation/windows/proofread-it.ahk -> exit 0; git diff --check -> exit 0 with line-ending warnings only. Spec anchors were observed unique.
- Human acceptance: Project owner reported "ручная проверка пройдена" in the current conversation on 2026-09-17 for the requested default-profile change. This is owner-reported semantic acceptance; no independent desktop trace or log was captured by the agent.
- Risks / REVIEW: No blocking spec REVIEW or temporary code/spec divergence remains. Manual acceptance details are owner-reported rather than independently captured.

## Next action

- Action: Stage only the 12 scoped paths and create the owner-requested local commit with the proposed message and full spec addresses.
- First command: git add -- automation/windows/proofread-it.ahk docs/development.md docs/windows-acceptance.md scripts/invoke.ps1 specs/WAL.md specs/modules/proofreader/DESKTOP-ASSISTANT.md src/proofread_it/cli.py src/proofread_it/source_check.py tests/component/test_app_invocation_wrapper.py tests/component/test_cli_contract.py tests/component/test_source_check.py tests/windows/test_hotkeys.py
- Completion criterion: One local commit contains exactly the 12 scoped paths and the full spec://proofreader/DESKTOP-ASSISTANT#configuration and spec://proofreader/DESKTOP-ASSISTANT#interaction addresses in its message; no push occurs.

- Blockers: NONE
- Pending decisions: NONE for this scoped change.
- Temporary code/spec divergence: NONE