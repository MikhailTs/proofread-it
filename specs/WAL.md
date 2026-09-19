Updated: 2026-09-19T18:51:28Z

- WAL-Schema: 1
- Checkpoint-ID: 66a83e2e-d657-4d41-9782-d3617ebfcb35
- Task: Make text in the proofreading result window copyable.
- Active scope: Create one local commit containing only the accepted result-window copying fix, its focused unit tests, the copy-related Windows acceptance guidance, and this checkpoint. Preserve the unrelated logging work. No specification edit, dependency change, push, or live API request is authorized.
- Authority: Project owner request on 2026-09-19 to fix result-window copying, owner report that manual verification passed, and owner request to prepare a commit with these changes.
- Authoritative spec: spec://proofreader/DESKTOP-ASSISTANT#interaction, spec://proofreader/DESKTOP-ASSISTANT#structured-result, and spec://proofreader/DESKTOP-ASSISTANT#testability. Observed specification SHA-256 9DB89DFCBC7082EB3D6CE3F4FC9ACCE7B3BD33C7899BD0584965F59551DEB2D3.
- Issue: NONE
- Assignment: NONE
- Phase: IN_PROGRESS

## Constraints

- `show_full` exposes both normalized result fields; only validated normalized values reach presentation -> addressed spec anchors.
- Selection/copy support is a defect fix within the permitted minimal Tkinter presentation; the approved product contract remains unchanged -> user request and `#interaction`.
- Use uv and preserve unrelated changes; this local commit is explicitly requested, while push still requires separate authorization -> AGENTS.md.

## Checkpoint and evidence basis

- Repository/worktree/branch: %USERPROFILE%/workspace/proofread-it; main; HEAD 1006c494cd8f47b04fd94ce46a921aa08ba2290a; origin/main observed six commits behind HEAD. Index clean before commit preparation; no merge/rebase observed.
- Pre-existing unstaged paths excluding ACTIVE_WAL: automation/windows/proofread-it.ahk, docs/development.md, docs/windows-acceptance.md, scripts/invoke.ps1, src/proofread_it/cli.py, src/proofread_it/errors.py, src/proofread_it/providers/openai.py, src/proofread_it/source_check.py, src/proofread_it/workflow.py, tests/component/test_app_invocation_wrapper.py, tests/component/test_cli_contract.py, tests/component/test_source_check.py, tests/component/test_workflow.py, tests/unit/test_openai_provider.py, tests/windows/test_clipboard.py, tests/windows/test_hotkeys.py. Non-ignored untracked: src/proofread_it/invocation_failure.py and tests/integration/test_invocation_failure.py. These unrelated changes were preserved.
- Current combined dirty fingerprint excluding ACTIVE_WAL: git diff --binary -- . ':(exclude)specs/WAL.md' | git hash-object --stdin -> 81fdb19d8225c85dc946c46d75422641dddc03be. Untracked SHA-256 values remain A56C67BCC801C9CD945201B478924C61502CEB6966E84F3B525ADD3709486F03 and A3BDA2748B19C8FC1D555CFE7284A5768AA3DF9D8990BA41E5D818D76A872102.
- Task paths and final SHA-256: src/proofread_it/presentation/result_window.py 9D631CF26DBC0FB4A70CA968768FCA7A2A276EB180971268FE18EA39925D5ABC; tests/unit/test_result_window.py 65FDD31E1B5C4F4C5C368D379C83BB4D0531E014F06C9594988AD4F975B36DF3; docs/windows-acceptance.md 4C984BCAADA94721956A42DDB31FE6A13350B5B5CA7ED0A2BD8D6B66422B6BC6. Pre-replacement ACTIVE_WAL SHA-256 BE21B99EA17F84B53154DC24F969E47413582EBF13CA70471C64C453BAF64FB4.

## Boundaries

- Specs: No specification file changed; the approved interaction contract permits the minimal Tkinter presentation and already requires both normalized fields to be exposed.
- Code: Read-only result fields now take focus on click and explicitly support `Ctrl+A` and `Ctrl+C`; a `Copy result` button copies the complete normalized final text. Fields remain disabled against edits. Focused tests cover focus, bindings, selection, and clipboard replacement. Windows acceptance guidance now covers both shortcut and button paths.
- Verification: `uv run --no-sync pytest -q -p no:cacheprovider tests/unit/test_result_window.py` -> 5 passed (2026-09-19); `uv run --no-sync ruff check .` -> passed; `uv run --no-sync mypy src` -> passed for 27 source files; `uv run --no-sync pytest -q -p no:cacheprovider` -> 149 passed, 2 deselected in 21.72s on the final code/test hashes before the documentation-only edit; `uv run --no-sync pytest -q -p no:cacheprovider tests/unit/test_result_window.py tests/windows/test_hotkeys.py` -> 12 passed on the final documented state; `git diff --check` -> exit 0 with line-ending warnings (all 2026-09-19).
- Risks / REVIEW: The project owner reported the focused live Windows manual check passed on 2026-09-19, covering the real visible result window and system clipboard. No pending REVIEW, known task-specific risk, or temporary code/spec divergence remains.

## Next action

- Action: Stage only the result-window implementation, focused unit test, copy-related acceptance-document hunk, and ACTIVE_WAL, then create the requested local commit.
- First command: git add -- src/proofread_it/presentation/result_window.py tests/unit/test_result_window.py specs/WAL.md
- Completion criterion: One local commit has subject `fix: enable copying from the result window`, includes `spec://proofreader/DESKTOP-ASSISTANT#interaction` in its message, contains only the four scoped paths, and leaves unrelated logging changes unstaged; no push occurs.

- Blockers: NONE
- Pending decisions: NONE
- Temporary code/spec divergence: NONE
