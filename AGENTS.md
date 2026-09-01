# AGENTS.md — Small Project Template

Install this file at the repository root as `AGENTS.md`. It contains stable repository instructions only. The canonical work loader is `specs/BOOT.md`; do not duplicate its protocols here. The authorized human request defines the current task. `specs/WAL.md` carries validated continuation context but never grants authority.

## Session Contract

- Set `ACTIVE_WAL = specs/WAL.md`, then read `specs/BOOT.md` before acting.
- This variant is valid only while the checkout and WAL have one state-changing writer. If parallel writers are possible, stop and adopt the assignment/worktree variant.
- Validate WAL through `specs/WAL-PROTOCOL.md`; never trust its age, status, or next action by itself.
- If BOOT, a required protocol, WAL, or addressed spec is absent, do not invent state. Report the gap and propose the minimum initialization. State-changing recovery requires human confirmation when authority or scope is unknown.
- Preserve unrelated existing changes. Do not revert, move, overwrite, stage, or commit them.

## Scope and Specifications

- Do not invent a `spec://` address for a mechanical task with no normative spec. If the task changes specified behavior, locate and use its canonical decision anchor.
- Follow `specs/SPEC-PROTOCOL.md` for every spec change or `REVIEW`. Do not replace approved meaning with an unapproved proposal.
- New production dependencies, data migrations, public API changes, security/privacy behavior, and irreversible choices require explicit scope and decision authority.
- For reversible local details not fixed by authority, choose the smallest consistent option, verify it, and report it.

## Implementation and Verification

- Use the repository's existing task runner, lockfile, configuration, and generation paths. Do not introduce a second package manager.
- Keep one semantic intent per diff and add or update relevant tests for behavior changes.
- Passing tests establish only their measured consistency. Required human semantic acceptance remains a separate gate; use `AWAITING_HUMAN_REVIEW` until it occurs.
- For code-first discovery, show the proposed spec diff and record temporary divergence in WAL. Apply a semantic spec change only within explicit edit scope and authority.
- A read-only audit changes neither project files nor WAL.

## Python Environment

- Use `uv` as the only Python project, dependency, and virtual-environment manager.
- Use the repository-local `.venv`; do not commit it or depend on absolute paths inside it.
- Run Python and project tools through `uv run`; synchronize the environment through `uv sync`.
- Treat `pyproject.toml` and `uv.lock` as the canonical dependency state. Update the lockfile through `uv` and include it with dependency changes.
- Do not introduce `pip`, Poetry, Conda, `requirements.txt`, or another environment/package-management workflow unless explicitly authorized.
- Do not edit generated files inside `.venv` manually.

## Handoff and Git

After state-changing work, update only `ACTIVE_WAL` according to its protocol. Report `Specs / Code / Tests / Risks & REVIEW / Next`; include every verification command and result.

Create a commit only on explicit request. First show the proposed message and include the relevant full `spec://` address when one exists. Push requires a separate explicit request. Do not add AI attribution or `Co-authored-by` without permission.
