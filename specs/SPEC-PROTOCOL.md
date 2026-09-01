# Specification Protocol {#spec-protocol}

_Canonical location: `specs/SPEC-PROTOCOL.md`. This protocol governs specifications under `specs/common/` and `specs/modules/`._

`MUST`, `MUST NOT`, `SHOULD`, and `MAY` are normative.

## Authority and Status {#authority}

Authority order:

1. system, safety, legal, and repository-enforced rules;
2. a decision by the declared authorized human or role;
3. an `APPROVED` specification;
4. tests;
5. code and generated artifacts;
6. WAL, reports, comments, and historical notes.

A lower source never silently overrides a higher one. Conflicting approved specifications are blocking unless one explicitly supersedes the other.

Every specification MUST declare near its top:

- `Status: DRAFT | APPROVED | SUPERSEDED`;
- `Owner: <person or role>`;
- `Approval authority: <person, role, or canonical source>`;
- `Supersedes: <spec://... | NONE>`;
- `Superseded by: <spec://... | NONE>`.

Missing or unknown status means `DRAFT`. `DRAFT` is reviewable but non-normative. `APPROVED` is normative. `SUPERSEDED` is immutable except for redirects, link repair, and changelog correction; it is not a source for new implementation.

Only the declared authority may approve, supersede, or change an approved decision. Edit permission alone is not decision authority. WAL, code, tests, examples, rationale, and changelog entries do not become normative merely by describing behavior.

## Addresses and Anchors {#addresses}

Persisted references MUST use full addresses:

- `spec://common/<DOC>#<id>` resolves to `specs/common/<DOC>.md`;
- `spec://<module>/<DOC>#<id>` resolves to `specs/modules/<module>/<DOC>.md`.

Paths and anchors are case-sensitive. A fragment resolves only to an explicit literal `{#id}` anchor, which MUST occur exactly once in its file. Do not depend on renderer-generated heading slugs.

A published `spec://` address is a public identifier:

- heading text and numbering MAY change while its anchor remains unchanged;
- an anchor MUST NOT be reused for different semantics;
- moving or renaming an approved anchor requires one coherent change that updates all inbound references;
- when immediate migration is impossible, retain the old anchor as a tombstone pointing to the replacement address;
- a superseded document MUST keep its published addresses resolvable through explicit replacement pointers.

Relative or abbreviated addresses MAY be used in conversation but MUST NOT be persisted as canonical references in specs, code, tests, WAL, or commits.

## Required Decision Structure {#structure}

Put the contract summary, critical constraints, and acceptance criteria near the beginning. Put cross-cutting invariants near the end.

Every normative decision created or semantically changed MUST have a stable anchor and contain:

- **Normative statement** — observable required behavior;
- **Rationale** — why the choice exists;
- **Verification** — automated or manual acceptance criteria;
- **Alternatives** — material rejected options, or `NONE`;
- **Reconsider when** — explicit conditions for reopening the decision;
- **Traceability** — affected specs and known code/tests, or `UNKNOWN`.

Recommended form:

```markdown
## <Decision title> {#stable-id}

**Normative:** <required observable behavior>

**Rationale:** <why>

**Verification:** <testable criteria>

**Alternatives:** <rejected alternatives or NONE>

**Reconsider when:** <explicit trigger>

**Traceability:** <spec://..., code, tests, or UNKNOWN>
```

Do not duplicate one normative value in several places. Choose one canonical anchor and reference it elsewhere.

## Edit Modes {#edit-modes}

### Spec-first {#spec-first}

Use Spec-first for new behavior and intended semantic changes:

1. identify the decision authority and affected canonical anchors;
2. inspect relevant code and tests as evidence, not authority;
3. create a separate `DRAFT` or an explicit `REVIEW` proposal without replacing current approved meaning;
4. obtain approval unless the active assignment already records the authorized decision;
5. atomically install the approved normative change and semantic changelog entry;
6. update derived code, tests, references, and verification evidence.

An unapproved proposal MUST NOT overwrite normative text in an approved specification.

### Sync-from-Code {#sync-from-code}

Use Sync-from-Code only when explicitly requested or when repairing non-semantic drift. Existing code does not become authoritative merely because it runs.

For semantic or ambiguous drift:

1. describe observed behavior and evidence;
2. create a `DRAFT` or `REVIEW` proposal;
3. obtain an authoritative decision;
4. update the spec, derived artifacts, references, and changelog coherently.

A mechanical sync MAY be applied directly when edit scope permits and the writer verifies that normative meaning and addresses do not change. Temporary code/spec divergence MUST be recorded in `ACTIVE_WAL` with owner and exit condition.

## Atomic Changes {#atomicity}

One change set MUST express one semantic intent. It MAY span several specs, code, tests, schemas, and generated artifacts when all are required for that intent.

Before editing, inspect current repository state and existing diffs. Never overwrite or absorb unrelated changes. If a relevant file changed since it was read, stop and reconcile before writing.

A semantic change is complete only when normative text, affected references, changelog, invalidation record, and required verification form one coherent result. If that cannot be completed, keep the proposal `DRAFT` or `REVIEW`, record the exact remainder in `ACTIVE_WAL`, and do not claim completion. Unrelated editorial cleanup belongs in a separate change.

## REVIEW and Conflicts {#review}

Use a stable, searchable record:

```markdown
<!-- REVIEW id=<stable-id> state=OPEN severity=ADVISORY|BLOCKING owner=<role>
At: spec://<module>/<DOC>#<id>
Issue: <conflict, ambiguity, or proposal>
Evidence: <facts and references>
Decision needed: <specific question>
-->
```

`ADVISORY` means the current approved text remains implementable: follow it and report the proposal. `BLOCKING` forbids changing the affected behavior until the authority decides.

A conflict is always blocking when it involves safety, security, privacy, data loss, incompatible approved specifications, an impossible acceptance criterion, ownership ambiguity, or an irreversible choice.

Lifecycle:

1. `OPEN` — issue recorded; no decision is inferred.
2. `DECIDED` — authority and decision are recorded.
3. `CLOSED` — normative text, affected artifacts, links, invalidation, and verification are reconciled.

Only the declared authority may move a review to `DECIDED`. On closure, remove the marker or mark it `CLOSED`, and add a semantic changelog entry with its ID and resolution.

If spec edit scope is unavailable, do not modify the specification. Record the review in `ACTIVE_WAL`, the assignment registry, or the report with the exact `spec://` address.

## Semantic Changelog {#changelog}

Every specification MUST end with `## Semantic changelog {#changelog}`. Append semantic entries oldest-to-newest:

```markdown
- YYYY-MM-DD — <authority> — <affected anchors>:
  <old meaning> -> <new meaning>; reason: <why>;
  invalidates: <artifacts/checks>; review: <id | NONE>.
```

Record approval, supersession, normative changes, invariant changes, and address migrations. Editorial-only changes MAY be omitted. Never silently rewrite semantic history; correct it with a later entry.

## Derived-Artifact Invalidation {#invalidation}

A change to normative meaning, status, invariant, or published address invalidates previous verification evidence for:

- the changed anchor;
- code, tests, fixtures, schemas, configuration, documentation, and generated artifacts that reference or implement it;
- known transitive consumers whose behavior depends on it.

Evidence from an older semantic or repository revision is `STALE`. For every semantic change:

1. search for exact inbound `spec://` references;
2. identify affected consumers and generated outputs;
3. update them or record every unresolved item in `ACTIVE_WAL`;
4. remove the force of affected `[x]`, `PASS`, `READY`, or `COMPLETE` claims;
5. rerun the narrowest sufficient checks, then required consumer or contract checks;
6. record exact commands, results, and revision basis in WAL or the handoff report.

A rationale- or formatting-only edit avoids invalidation only when normative meaning and anchors are explicitly verified unchanged.

## Completion Checks {#completion}

Before declaring a specification change complete, verify that:

- every changed target exists and each anchor is unique;
- moved or superseded addresses resolve or have tombstones;
- status and decision authority are valid;
- the diff contains one semantic intent;
- changed decisions include all required fields and traceability;
- no `BLOCKING` review remains in completed scope;
- affected specifications contain no unresolved contradiction;
- required lint, tests, generation, and consumer checks pass;
- evidence names exact commands and relevant spec/repository revisions;
- the semantic changelog and `ACTIVE_WAL` reflect the result.

Approval establishes normative intent; it does not prove that derived artifacts conform.
