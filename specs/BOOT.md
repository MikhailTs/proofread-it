# BOOT {#root}

_Canonical location: `specs/BOOT.md`. No current state lives here._

## Load {#load}

1. Resolve `ACTIVE_WAL` from active instructions/assignment; default: `specs/WAL.md`; `NONE` skips it. Before use or update, follow `specs/WAL-PROTOCOL.md`. Validate identity, authority, and evidence basis. Age alone is a warning. `STALE` is recovery context only; `INVALID`/`CONFLICTED` blocks state changes. Unknown facts are `UNKNOWN`.
2. `spec://common/<DOC>#<id>` resolves to `specs/common/<DOC>.md`; `spec://<module>/<DOC>#<id>` to `specs/modules/<module>/<DOC>.md`; `<id>` is literal `{#id}`. Read only addressed decisions and scope dependencies. For spec creation, change, `REVIEW`, or reconciliation, follow `specs/SPEC-PROTOCOL.md`.
3. Derive scope, constraints, DoD, and first verification from the request, assignment, valid WAL, and approved specs. Expand reading only along scope dependencies.

## Coherence {#coherence}

Priority: system/safety rules > authorized human > approved spec > tests > code. One normative source per decision; derived artifacts link back. Never change a spec silently. Stop on authority ambiguity or material product, architecture, security, privacy, migration, or irreversible conflict. Otherwise follow the approved spec; record `REVIEW` only within edit scope, else report it.

## Cycle {#cycle}

Read-only changes nothing. Keep one intent per diff and verify it. Update only `ACTIVE_WAL` per its protocol before destructive work, context loss/handoff, and after material state changes. Code-first: propose the spec diff; apply it only within explicit scope/authority; keep temporary divergence in WAL. Commit only on request; push requires a separate request.
