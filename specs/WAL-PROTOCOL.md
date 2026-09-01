# WAL Protocol {#wal-protocol}

_Canonical location: `specs/WAL-PROTOCOL.md`._

`MUST`, `MUST NOT`, `SHOULD`, and `MAY` are normative. Project-specific automation may strengthen this protocol but must not weaken its authority, validation, or concurrency rules.

## Contract {#contract}

A WAL is a replaceable continuation checkpoint for exactly one authorized writer, active task or assignment, and working context. It is not history, a specification, a lock, an ownership registry, an approval record, or proof of completion.

- Normative facts MUST link to their authoritative source instead of being copied as new truth.
- Unknown facts MUST be written as `UNKNOWN`; absence MUST NOT be interpreted as permission, ownership, completion, or approval.
- The WAL MUST be replaced as a whole and SHOULD remain within one rendered page. Stable decisions belong in specs; history belongs in Git, the tracker, or an audit system.
- Claims such as `[x]`, `READY`, and `LOCAL_CHECKS_PASS` are valid only for their recorded evidence basis.
- A WAL phase never authorizes assignment, merge, commit, push, deployment, or acceptance. A missing or old WAL never releases an assignment.

## Required Record {#required-record}

The first line MUST be `Updated: <RFC3339 UTC timestamp>` and use `Z`. Every WAL MUST include:

- `WAL-Schema`;
- a unique `Checkpoint-ID`, replaced on every rewrite;
- stable task identity and exact active scope;
- authoritative spec, issue, and assignment references with observed revisions when available, or `NONE`;
- current local phase;
- constraints with reason and source;
- checkpoint and evidence basis;
- verified and outstanding boundaries;
- exactly one next action, its first command, and an observable completion criterion;
- blockers, pending decisions, and temporary code/spec divergence, each explicitly `NONE` when empty.

An assignment WAL MUST additionally include `Assignment-ID`, registry URI, observed registry revision and check time, base revision, branch/worktree, current `HEAD`, integration target, and its observed revision.

## Checkpoint and Evidence Basis {#evidence-basis}

The basis MUST identify the repository and checkout, branch/worktree, current `HEAD`, staged, unstaged, and non-ignored untracked state excluding `ACTIVE_WAL` itself, and relevant spec/input revisions.

For a dirty checkout, record the expected changed paths and a project-defined fingerprint of their content. If no canonical fingerprint tool exists, write `UNAVAILABLE`; after a session boundary, verification claims on that dirty state are then `STALE` until the diff is inspected and the checks are repeated.

Every completed item or verification result MUST name the exact command or observation, result, time, and evidence basis. A passing command does not prove facts outside its coverage.

Material toolchain, dependency, generated-state, or external-service revisions MUST be included when they affect reproducibility.

## Local Phase Semantics {#phase-semantics}

Small-project phases:

- `IN_PROGRESS`: safe actionable work remains.
- `BLOCKED`: no safe implementation action remains; the blocker and decision owner are named.
- `AWAITING_HUMAN_REVIEW`: implementation checks may pass, but a named semantic decision or acceptance is pending.
- `READY`: scope and DoD are satisfied on the recorded basis and all required human acceptance has occurred.

Assignment-WAL phases:

- `WORKING`, `BLOCKED_LOCALLY`, `AWAITING_HUMAN_REVIEW`, or `LOCAL_CHECKS_PASS`.
- `LOCAL_CHECKS_PASS` describes only the recorded checkout. It MUST NOT be treated as registry `READY`, `INTEGRATED`, or `CLOSED`.

## Validation States {#validation-states}

Validation is read-only and performed by the reader on every load; a status written by the previous writer is not self-authenticating. Apply the highest-priority applicable state: `CONFLICTED`, then `INVALID`, then `STALE`, otherwise `VALID`.

- `VALID`: schema, identity, authority references, checkout basis, and applicable evidence match current observations.
- `STALE`: the record may orient recovery, but its next action, completion marks, and verification claims MUST NOT be trusted until refreshed.
- `INVALID`: required identity is missing, the WAL belongs to another task/checkout, authority conclusively ended or moved, or a required reference is unusable. Do not use it as continuation context.
- `CONFLICTED`: the WAL changed after read, authoritative sources or writers disagree, integration conflicts are unresolved, or unchanged evidence yields contradictory results. Stop state-changing work and escalate to the named authority.

A project-configured age threshold produces `AGE_WARNING` and mandatory revalidation. Age alone neither invalidates a WAL nor releases an assignment or grants ownership.

## Revalidation and Invalidation {#invalidation}

Revalidate before state-changing work whenever any of these changes or cannot be proven unchanged:

- task identity, scope, constraints, DoD, or decision authority;
- branch, worktree, `HEAD`, staged/unstaged/untracked content, or checkout path;
- an addressed spec, anchor, dependency, configuration, test, lockfile, generated contract, or relevant external fact;
- assignment owner, scope, state, lease, registry revision, dependency, or integration target;
- a required reference that disappears, becomes ambiguous, or is superseded;
- the WAL or a loaded spec after it was read.

Task, assignment, ownership, or checkout mismatch invalidates the WAL as a continuation instruction. A changed implementation, spec, test, dependency, or configuration invalidates the affected `[x]` items and evidence; unrelated orientation may remain usable. Any affected invalidation removes the force of `READY` or `LOCAL_CHECKS_PASS` until reconciliation and repeated checks.

Typical classification outcomes:

- same authorized task but changed `HEAD`, owned diff, input revision, dependency state, or relevant result -> `STALE`;
- different task, repository, branch/worktree, cancelled/closed/reassigned authority, or incompatibly superseded required anchor -> `INVALID`;
- changed WAL bytes/Checkpoint-ID after load, unresolved merge/rebase, competing writer, or unexplained contradictory result on the same basis -> `CONFLICTED`.

A completed merge or rebase in the same authorized assignment normally makes old evidence `STALE`; an unresolved one is `CONFLICTED`.

## Resume and Recovery {#resume}

1. Resolve `ACTIVE_WAL`, read it once, and retain a content digest or exact snapshot.
2. Validate its schema and required fields.
3. Observe the current task, repository, branch/worktree, `HEAD`, worktree state, merge/rebase state, addressed specs, and assignment registry when present.
4. Resolve every authority reference and compare the recorded bases with current observations.
5. Classify the WAL as `VALID`, `STALE`, `INVALID`, or `CONFLICTED`.
6. If `STALE`, reconstruct from the authority hierarchy, registry, Git status/diff/log, approved specs, and repeated narrow checks. Treat the recorded next action only as a hypothesis.
7. Mark unresolved facts `UNKNOWN`. Escalate unresolved semantic, ownership, or concurrent-writer conflicts.

No state-changing action may be resumed from `STALE`, `INVALID`, or `CONFLICTED` until a valid checkpoint is reconstructed or an authorized human explicitly redirects the task.

For `INVALID`, do not overwrite it as current state. Obtain authority for the actual task/assignment and initialize a fresh checkpoint. For `CONFLICTED`, preserve competing snapshots and current Git/registry evidence; do not write until the coordinator establishes one authoritative state. A missing WAL MUST be reconstructed only as a draft from Git and canonical sources, with unknown facts explicit and required authority confirmed.

## Updating the WAL {#update}

Rewrite the WAL:

- before a destructive or broad operation;
- after a material change in phase, scope, constraint, blocker, decision, divergence, or verification evidence;
- before a context switch, handoff, or expected context loss;
- at the end of every state-changing session.

A read-only audit MUST NOT update WAL.

For a safe update:

1. Confirm exclusive write authority and revalidate the task/assignment.
2. Recompute the evidence basis and downgrade claims that no longer match.
3. Immediately reread WAL and compare it with the retained snapshot. If bytes or Checkpoint-ID differ, abort as `CONFLICTED`.
4. Build the complete replacement with a new Checkpoint-ID and UTC timestamp.
5. Replace it atomically when the filesystem supports it, then reread and validate the result.

A read comparison is not an atomic lock. When multiple writers are possible, an external coordinator, lease, or equivalent serialization is mandatory. Never append a chronological work log to the active WAL.

## Normative Boundaries {#normative-boundaries}

Temporary observations, continuation details, failed experiments, and local risks belong in WAL. Durable decisions and accepted behavior belong in specs or decision records. Ownership, leases, assignment lifecycle, and integration state belong in their external registry. When WAL conflicts with a canonical source, the canonical source wins and WAL is reclassified. A `REVIEW` item in WAL is a pointer to an unresolved proposal, not an accepted requirement.
