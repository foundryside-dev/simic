# Commissioning prompt — axiom-contract-engineering (consolidated, v4.1)

Status: **re-commissioned 2026-08-08** with this consolidated prompt (owner
decision, supersedes the delta-brief approach for this pack) · Tracker:
simic-e84fe6737c (closed) · Roster: PDR-0011 · Provenance: PDR-0012

---

Commission a new skillpack: **axiom-contract-engineering** — the engineering
discipline of typed cross-boundary contracts: schema design, versioning and
evolution, deterministic resolution, fail-closed compatibility, blinding by
construction, canonical identity, and contract testing. Axiom faction
(software-engineering discipline). General-purpose like the other axiom
packs — it teaches the discipline, not one project — but it is commissioned
to serve the Simic project's Leyline contract layer, whose requirements
below are the acceptance reality.

## Driving context (Simic / Leyline)

Simic is a lifecycle-driven neural training system in which every
subsystem boundary is a typed Leyline contract; Phase A binds code to those
contracts first, before any behaviour exists. Ground in the decomposed HLD:
entry point `docs/design/00-INDEX.md`; cite chapters by path#anchor,
invariants as INV-nn, contracts by name — never bare §-numbers. Key
grounding: `docs/design/05-leyline-contracts.md` (the contract inventory;
`Snapshot` at `#911-snapshot`), `docs/design/02-constitution.md` (INV set),
`docs/design/04-architecture.md#105-deterministic-request-resolution`,
`docs/design/programme/evaluation.md#212-leyline-contract-tests`,
`docs/design/appendices/newsroom.md` (assignment-brief boundary).

The predecessor project (Esper) died of a contract-layer defect class:
**silent defaults** — plumbing that quietly taught downstream consumers
"unmeasured means zero." The pack's centre of gravity is making that class,
and its relatives, unrepresentable by construction.

## Discipline the pack must teach (reference-sheet territory)

1. **Contract-first boundaries** — typed cross-boundary records; one
   authority per record class; plain-language role statement per contract;
   illegal states unrepresentable rather than policed.
2. **Silent-default elimination** — explicit nullability and validity
   masks; absent ≠ zero; fail-loud on unmeasured fields; no tolerant
   readers that paper over drift; typed accessors only, with untyped
   defaulting access (`.get()`-with-default) CI-banned on contract paths
   per ADR-0006 — including the named AI-engineering failure mode it
   exists to kill: a model hallucinating an interface and hiding it
   behind permissive access idioms. (The Esper stratum-one killer; give
   it its own sheet.)
3. **Schema versioning and evolution** — any change in meaning, width,
   basis, normalisation or provenance is a new schema version; typed
   compatibility fails closed (INV-24); no legacy shims or
   backwards-compat code paths (the consumer moves or the version gates).
4. **Deterministic resolution** — pure resolvers over recorded inputs;
   equivalent inputs produce one canonical output; no covert channels via
   serialisation, aliases, field ordering or irrelevant variation
   (INV-10, INV-11); resolvers can only narrow authority, never widen it.
5. **Blinding by construction** — provider-blind views where excluded
   fields are *absent from the schema*, not present-and-ignored (INV-37);
   boundary fields that are schema-invalid, not discouraged (INV-09).
6. **Canonical identity** — content-addressed semantic hashing; every
   downstream record (artefact, QA report, decision, embodiment) binds the
   same canonical hash (INV-20); raw-to-canonical traceability (INV-19).
7. **Dependency direction** — contracts import nothing from subsystems
   (INV-02); import-lint as an enforced gate, not a convention.
8. **Versioned policy parameters** — policy records carry explicit
   versions; decisions bind the policy version in force. Simic examples:
   `adjudication_policy_version` carries the tail-veto operating point
   (ADR-0004, INV-45) and the admission/retention hysteresis band
   (ADR-0005, INV-33).
9. **Definition lifecycle** — named definitions move
   draft → approved → locked through recorded events, never silent edits
   (Simic's ADR-0002 regime is the reference implementation of this
   discipline).
10. **Contract testing** — golden fixtures, serialisation round-trips,
    canonicalisation property tests (equivalent-input invariance,
    non-equivalent hash separation), schema-invalid rejection tests, and
    authority tests that prove a forbidden field cannot arrive.

## Failure-mode catalogue (critic territory)

Silent defaults; tolerant readers; covert channels through permitted
fields; dual sources of truth for one schema; blinding by ignoring;
version-in-name-only (schema changed, version didn't); compat shims that
let two meanings coexist; resolver logic that grew preferences; contract
tests that only test the happy serialisation path.

## House conventions

Follow the skillpacks house style: a `using-contract-engineering` router
skill plus focused reference sheets (one discipline area per sheet, ~10
sheets); two SME agents following the SME Agent Protocol
(`docs/sme-agent-protocol.md`) — a producer (**contract-suite-architect**:
given a system's boundaries and record classes, designs the contract suite
with versioning, resolution and test plan) and a critic
(**contract-reviewer**: audits a contract suite or diff against the
failure-mode catalogue, severity-rated findings with evidence, refuses to
rubber-stamp); and 2–3 commands (e.g. `design-contract-suite`,
`review-contracts`, `audit-contract-drift`). Every sheet self-sufficient;
no sheet defers to the Simic HLD for content — the HLD grounds the
commission, the pack must stand alone.

## Acceptance reality

The pack is fit when a Phase-A session, loaded with only this pack and the
Simic design chapters, can design the Leyline contract skeleton — schemas,
versioning rules, resolver shape, blinded views, canonical-hash binding,
and the `tests/contracts/` + `tests/namespec/` suites — without
reinventing discipline or importing any silent-default pattern.
