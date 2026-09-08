Updated: 2026-09-08T18:41:58Z

- WAL-Schema: `1`
- Checkpoint-ID: `35a64d0e-cb61-4663-99e2-aa258bf8f258`
- Task: Record and locally commit the Project owner's approved MVP-boundary decisions for AutoHotkey configuration, profile scope, and `#Include` compatibility.
- Active scope: The approved specification and semantic changelog change is complete; create the explicitly requested local commit containing that change and this checkpoint. Push, implementation and manual acceptance of include-compatible AutoHotkey behavior, exclusions, concurrency, retry-event logging, and broader MVP work remain out of scope.
- Authority: Project owner semantic decisions on 2026-09-05 and explicit local commit request in the current conversation on 2026-09-08.
- Authoritative spec: `spec://proofreader/DESKTOP-ASSISTANT#architecture`, `spec://proofreader/DESKTOP-ASSISTANT#configuration`, `spec://proofreader/DESKTOP-ASSISTANT#proofreading-profile`, `spec://proofreader/DESKTOP-ASSISTANT#interaction`, and `spec://proofreader/DESKTOP-ASSISTANT#mvp-scope`; observed approved post-change file SHA-256 `4f8095733e5e9022ffb93e5407c8a50750d7a9bb3d3ecee501f08456eeb76051`.
- Issue: `NONE`
- Assignment: `NONE`
- Phase: `IN_PROGRESS`

## Constraints

- MVP hotkey customization belongs in the AutoHotkey script rather than `settings.json` -> current Project owner decision.
- Only the generic `proofread` profile is required; separate casual, professional, and similar profiles are post-MVP -> current Project owner decision.
- The shipped AutoHotkey automation must preserve the same workflow when launched directly or loaded through `#Include` -> current Project owner decision.
- Preserve the generic profile's requirement to retain tone/register and English variant across representative inputs; this is behavior of `proofread`, not a requirement for extra profiles -> `spec://proofreader/DESKTOP-ASSISTANT#proofreading-profile` and the current decision's stated profile scope.
- Preserve unrelated changes; do not commit or push without a separate request -> `AGENTS.md`.

## Checkpoint and evidence basis

- Repository/worktree/branch: `%USERPROFILE%/workspace/proofread-it`; `main`; HEAD `4ff6c2afeee8c2d087e3bdcbc20b20e974b4b291`; observed `origin/main` `1c37b1e77f31c4a35ce9faf326339618a8371833`; no merge or rebase observed.
- On 2026-09-08 before this WAL replacement, staged state was clean; unstaged state contained only `specs/WAL.md` and `specs/modules/proofreader/DESKTOP-ASSISTANT.md`; non-ignored untracked state was clean.
- Retained prior WAL SHA-256 before replacement: `52894d99c89bbcf8376a3ddf8bca5d524fa94ae2c33a65497b6760baf8bc8559`.
- Relevant input revision: Project owner message observed in the current conversation on 2026-09-05; pre-change specification SHA-256 `153bdf184c574be97d2f62a9acdfeef84cc3f4c356ca72c64151e83e75383d86`.
- Expected state excluding ACTIVE_WAL after the approved specification edit: modified `specs/modules/proofreader/DESKTOP-ASSISTANT.md` only; its SHA-256 is `4f8095733e5e9022ffb93e5407c8a50750d7a9bb3d3ecee501f08456eeb76051` and the sorted `path=SHA-256` content-manifest SHA-256 is `84bc0615029ac39662f07d1e6f5e9b3f5a152596d8e774993da5a0a41eb28911`.

## Boundaries

- Specs: The five addressed approved anchors and semantic changelog now record AHK-source hotkey customization, the explicit post-MVP status of additional named profiles, and equivalent direct/`#Include` automation behavior with included-file-relative path resolution.
- Code: Existing hard-coded AHK bindings reflect the accepted hotkey-configuration boundary. Current include compatibility is not conforming because `automation/windows/proofread-it.ahk` resolves `ProjectRoot` from `A_ScriptDir`, which refers to the host script when included.
- Tests: At 2026-09-05T18:40Z, `git diff --check` exited `0` with line-ending warnings only; an anchor scan found 22 unique anchors and no duplicates; exact inbound-reference search completed for all five changed anchors. The preceding code audit ran `uv run --no-sync pytest -q` (`81 passed, 2 deselected`), `uv run --no-sync ruff check .` (passed), and `uv run --no-sync mypy src` (passed), but that evidence predates and does not verify the new include requirement.
- Human acceptance: The Project owner directly approved the three semantic decisions in the current conversation.
- Outstanding: Create and verify the explicitly requested local commit.
- Risk / REVIEW: The new include requirement intentionally invalidates AutoHotkey path/bootstrap evidence, automation tests, Windows acceptance documentation, and the MVP release checklist until implementation and acceptance; no unresolved semantic review remains.

## Next action

- Action: Stage only the specification and WAL, then create the proposed local commit `docs(spec): clarify AHK configuration and include support` with all five full spec addresses in its body.
- First command: `git add -- specs/WAL.md specs/modules/proofreader/DESKTOP-ASSISTANT.md`.
- Completion criterion: the commit succeeds, contains exactly the approved specification/WAL changes, and post-commit status and HEAD are recorded; no push occurs.

- Blockers: `NONE`
- Pending decisions: `NONE`
- Temporary code/spec divergence: `spec://proofreader/DESKTOP-ASSISTANT#architecture` and `spec://proofreader/DESKTOP-ASSISTANT#interaction` now require direct/`#Include` equivalence, while `automation/windows/proofread-it.ahk` still uses host-relative `A_ScriptDir`; owner: Project owner; exit condition: implement included-file-relative path resolution and pass direct/include Windows acceptance.
