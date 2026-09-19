Updated: 2026-09-19T21:15:12Z

- WAL-Schema: 1
- Checkpoint-ID: 7ba8b6ff-7445-4298-83ce-7f4e0de82671
- Task: Record early proofreading failures in the configured MVP log without exposing credentials or excluded-source text.
- Active scope: Create one local commit containing the accepted early-failure logging implementation, safe provider diagnostics, focused tests, documentation, and this checkpoint. No semantic spec change, dependency change, push, or live API request is authorized.
- Authority: Project owner request on 2026-09-17 to fix missing early-failure logging, project owner report on 2026-09-19 that both manual scenarios work correctly, and subsequent explicit request to commit these changes.
- Authoritative spec: spec://proofreader/DESKTOP-ASSISTANT#logging, spec://proofreader/DESKTOP-ASSISTANT#errors, spec://proofreader/DESKTOP-ASSISTANT#context-policy, and spec://proofreader/DESKTOP-ASSISTANT#api-access. Observed specification SHA-256 9DB89DFCBC7082EB3D6CE3F4FC9ACCE7B3BD33C7899BD0584965F59551DEB2D3.
- Issue: NONE
- Assignment: NONE
- Phase: IN_PROGRESS

## Constraints

- The single configured log records available invocation diagnostics, while API keys, authorization material, and excluded-source text do not enter it -> addressed spec anchors.
- Preserve the pre-capture exclusion and process-local credential boundaries -> addressed spec anchors.
- Use uv; the local commit is explicitly requested, while push still requires separate authorization -> AGENTS.md.

## Checkpoint and evidence basis

- Repository/worktree/branch: %USERPROFILE%/workspace/proofread-it; main; HEAD 2d2e0d7a66ecf5030bd63ea604a683a34719a1b3; origin/main observed seven commits behind HEAD. Index clean; no merge/rebase observed.
- Expected unstaged task paths excluding ACTIVE_WAL: automation/windows/proofread-it.ahk, docs/development.md, docs/windows-acceptance.md, scripts/invoke.ps1, src/proofread_it/cli.py, src/proofread_it/errors.py, src/proofread_it/providers/openai.py, src/proofread_it/source_check.py, src/proofread_it/workflow.py, tests/component/test_app_invocation_wrapper.py, tests/component/test_cli_contract.py, tests/component/test_source_check.py, tests/component/test_workflow.py, tests/unit/test_openai_provider.py, tests/windows/test_clipboard.py, tests/windows/test_hotkeys.py. Non-ignored untracked task paths: src/proofread_it/invocation_failure.py and tests/integration/test_invocation_failure.py.
- Task fingerprint excluding ACTIVE_WAL: git diff --binary -- . ':(exclude)specs/WAL.md' | git hash-object --stdin -> 883c55f07f971fd65759fbc26623ab736f281425. Untracked SHA-256 values respectively A56C67BCC801C9CD945201B478924C61502CEB6966E84F3B525ADD3709486F03 and A3BDA2748B19C8FC1D555CFE7284A5768AA3DF9D8990BA41E5D818D76A872102. Pre-replacement ACTIVE_WAL SHA-256 BC0AFE2AF85631BB81FF1E7CFA533BA77D805D34052A4CABB30C20B7CE0509D8; that WAL belonged to the completed result-window task, while the current owner message authorizes this logging checkpoint.

## Boundaries

- Specs: Approved logging, error, credential, and privacy requirements are followed; no specification file changed. Documentation now states that recoverable early failures are logged.
- Code: A credential-free helper records known preflight failures when the configured path is recoverable. AutoHotkey logs empty selection and changed-window failures; the wrapper logs invalid settings and missing, unreadable, or empty credential files; CLI/source-check failures are covered; provider logs retain bounded safe identifiers rather than raw SDK messages. Excluded-source text is omitted.
- Verification on unchanged logging content: `uv run --no-sync pytest -q -p no:cacheprovider` -> 149 passed, 2 deselected in 21.72s; `uv run --no-sync ruff check .` -> passed; `uv run --no-sync mypy src` -> passed for 27 source files; `AutoHotkey64.exe /Validate /ErrorStdOut=UTF-8 automation/windows/proofread-it.ahk` -> exit 0; `git diff --check` -> exit 0 with line-ending warnings (all 2026-09-19). The project owner reported on 2026-09-19 that both focused live scenarios (empty selection and credential failure) work correctly.
- Risks / REVIEW: If settings are absent or invalid and no log path can be recovered, no configured destination exists for an event; the user-facing error remains. Human semantic acceptance is complete. No pending REVIEW, known blocking risk, or temporary code/spec divergence remains.

## Next action

- Action: Stage the 19 scoped task paths and create the requested local commit.
- First command: git add -- automation/windows/proofread-it.ahk docs/development.md docs/windows-acceptance.md scripts/invoke.ps1 specs/WAL.md src/proofread_it/cli.py src/proofread_it/errors.py src/proofread_it/invocation_failure.py src/proofread_it/providers/openai.py src/proofread_it/source_check.py src/proofread_it/workflow.py tests/component/test_app_invocation_wrapper.py tests/component/test_cli_contract.py tests/component/test_source_check.py tests/component/test_workflow.py tests/integration/test_invocation_failure.py tests/unit/test_openai_provider.py tests/windows/test_clipboard.py tests/windows/test_hotkeys.py
- Completion criterion: One local commit has subject `fix: log failures before proofreading starts`, includes all four relevant full `spec://` addresses in its message, contains exactly the 19 scoped paths, and no push occurs.

- Blockers: NONE
- Pending decisions: NONE
- Temporary code/spec divergence: NONE
