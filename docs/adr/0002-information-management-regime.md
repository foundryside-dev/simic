# ADR-0002 — Information-management regime: named-definition lifecycle with Weft-backed sign/lock

Date: 2026-08-08 · Status: accepted
Deciders: john (approach A selected from three in-session) · Tracker: simic-357c92664c

> **Namespec note (ADR-0008):** this record predates Namespec 2.0 and uses
> Namespec 1.0 names; read it through the concordance in
> [`0008-namespec-2.0.md`](0008-namespec-2.0.md).

## Context

Esper and esper-lite had two systemic failures. Reward shaping is recorded
elsewhere (simic-00351db32e); the second was information management. Named by
the owner: requirements and interfaces drifted without record; telemetry
standards were unevenly defined — some parts precise, others "to be done",
with nothing marking which was which; no sign-or-lock gate existed for a
component. On the runtime side: ad-hoc per-run formats, lost lineage, and
silent mutation of results (kin of the None→0 silent-default class that
motivated the reset).

Simic's HLD specifies *what* Sarpadia retains (`domains/sarpadia.md`) but no
regime governs definitional maturity or storage policy. Phase A is
contracts-first: the Leyline shapes about to be implemented need a lock
mechanism before code binds to them. The project dogfoods the Weft suite, and
plainweave (requirements, immutable baselines, actor registry, append-only
event log) plus legis (graded gates) already provide the needed machinery —
verified live in-session (plainweave 1.2.1, SIMIC store initialized, empty).

## Decision

One regime, two layers.

**Layer 1 — definitional lifecycle (effective immediately).** A *named
definitional unit* is anything the system can drift against: each Leyline
contract, each telemetry standard (`TelemetryEnvelope` field set,
`RegionReport` when it lands), the namespec, and the INV set (one unit
initially; split per-INV only if amendment traffic demands it). Chapters are
containers, never lock units. Each unit is a plainweave requirement whose
acceptance criteria state its obligations in checkable form. Three states,
mapped one-to-one onto plainweave primitives: **draft** (a *recorded* TBD —
absence of definition is itself registered, never implicit), **approved**
(reviewed truth), **locked** (member of an immutable named baseline, e.g.
`constitution-1.0`). A locked unit changes only through an ADR plus a new
baseline. John is the sole approving/baselining actor; agents register drafts
and propose promotions only. Drift control: `plainweave baseline diff` as a
legis-graded CI gate (a PR touching a locked definition without an
accompanying ADR/re-baseline fails; `override_submit` is the recorded
exception path), and trace links binding each requirement to its chapter
anchor now and to Loomweave SEIs once Phase A code exists.

**Telemetry rule.** Every telemetry field set must be a registered unit whose
acceptance criteria include: value/observed/age triple discipline (the
silent-default class unrepresentable by construction), a named
transport-completeness test, and layout/width-invariance where the
conditioning invariant applies (simic-0ec359f7fa). A field not in a locked
standard does not ship.

**Layer 2 — runtime data policy (binding principles now; physical design is a
Phase A LLD gated on the cost model, simic-642c2c1823).**

- P1 Append-only: no record class supports in-place update; corrections are
  new records that supersede.
- P2 Unmeasured ≠ zero: every measured quantity is stored as
  value/observed/age or explicit absence.
- P3 One authority per record class: exactly one producing domain and one
  canonical store; all other copies are views.
- P4 Schema-versioned from day one: every persisted record carries schema id
  + version; no version, no write.
- P5 Identity by canonical hash (per the semantic-identity invariant).
- P6 Retention as declared budgets: every store declares size/age budgets and
  a named degradation action; nothing unbounded, nothing silently dropped.
- P7 Grouping key at write time: any record that can enter statistics carries
  its base-trajectory id.

Every future storage choice must answer the seven-question checklist: writer,
write point (transaction boundary), schema unit + version, identity keys,
blinded views required, retention budget, replay implications.

**Seeding — the regime starts true.** Register actors; register Namespec 1.0
and INV-01..44, approve, and lock as baseline `constitution-1.0` (tool state
matches the docs' declared lock from day one). Register every
`05-leyline-contracts.md` contract as **draft** — deliberately, since the
hld-review backlog is actively amending them — promoting and locking each as
its review tasks close. Policy text lives in
`docs/design/ops/information-management.md`.

## Displaced constraints

The "Namespec 1.0 — locked" doc-header convention stays as human-readable
signage, but lock *authority* moves to plainweave baselines; a header claiming
locked without a backing baseline is itself drift. Nothing in
`domains/sarpadia.md` changes: this ADR adds the governance and policy layer
the data model was missing, not new record classes.

## Options considered

- **A — plainweave as state authority (chosen):** definitions in docs, state
  in plainweave, locks as immutable baselines, attribution via the append-only
  event log, drift via baseline diff. Maximal dogfood; state not visible in a
  raw checkout without the tool.
- **B — repo manifest canonical, plainweave mirror:** `registry.yaml` in-repo
  plus a standing manifest↔store consistency check. Fully legible in git, but
  double bookkeeping — the exact drift class this regime exists to kill,
  reintroduced between our own tools. Rejected.
- **C — convention-only front-matter + CI grep:** no tool dependency, but no
  immutable lock, no attribution, no mechanical diff — the esper honour
  system with tidier headers. Rejected; retained as the designated fallback.

## Consequences

Easier: TBD becomes a recorded state, so uneven definition is visible in one
status view; locked definitions are mechanically defended; sign-off is
structurally the owner's (mirroring simic's own warrant discipline);
plainweave/legis get exercised on real work, and per the dogfooding rule their
defects are surfaced, never worked around. Harder: definitional state is
invisible in a raw checkout without plainweave; the MCP surface is read-only,
so all writes (seeding, promotion, baselining) are deliberate CLI operator
acts; the legis gate is new CI work (coordinate with the doc-lint lane,
simic-4da299ff46). Must: write `ops/information-management.md`, run the
seeding session, wire the gate — tracked as simic-357c92664c. Reversal
trigger: if plainweave bookkeeping measurably slows design work or the tool
proves unreliable, fall back to option C with the same state vocabulary —
the states survive, only the machinery changes.
