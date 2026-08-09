# ADR-0012 — Curriculum posture: tight, loose, free

Date: 2026-08-09 · Status: accepted
Deciders: John (owner-directed, session 11; playback confirmed) ·
Tracker: simic-eb0cf50deb

## Context

The design keeps reaching for training wheels — four `ScaffoldState` axes
(ADR-0011 added the fourth), eleven curriculum schools, rule-driven
authorities, a field surrogate — and the owner asked for a single stated
posture: what the wheels are, how we know a rung is working, and what earns
a transition to less restrictive. The survey found that the informal phrase
"training wheels" covers three structurally different kinds, that every
scaffold axis is already a three-rung ladder, and that the design's
strongest habit — withdrawn scaffolds becoming permanent instruments — was
practiced everywhere and stated nowhere.

## Decision

Adopt the **tight / loose / free** posture as the named vocabulary for
every scaffold rung, recorded in Appendix F
(`../design/appendices/scaffold-pattern.md`):

- **TIGHT** — the classroom: the constraint fully active so causal signal
  exceeds nuisance variation; ground truth is manufactured here.
- **LOOSE** — controlled relaxation: the constraint partially lifted
  **with the tight instrument still auditing**; never loose without a
  paired tight-grade check.
- **FREE** — withdrawal: the constraint removed as a production
  dependency and **converted, never deleted** — the tight capability
  survives as escalation, audit and regression instrument.

Every scaffold axis instantiates the ladder:

| Axis | TIGHT | LOOSE | FREE |
|---|---|---|---|
| Execution | `ACADEMY_EXACT` | `CALIBRATED_STOCHASTIC` | `FIELD` |
| Host distribution | `REPEATED_ACQUISITION` | `HELD_OUT_IN_FAMILY` | `OPEN_DISTRIBUTION` |
| Design priors | `REFERENCE_ANCESTRY` | `ANCESTRY_DROPOUT` | `NULL_ANCESTRY` |
| Anchoring | `FULL_DECISION_FANOUT` | `ADMISSION_ANCHORED` | `UNANCHORED` |

**Three kinds of wheels ride the ladder differently:**

1. **Measurement scaffolds** (Academy exactness, repeated trajectories,
   the anchor corpus, the field surrogate) — expected to climb; withdrawal
   means the cheap instrument carries a measured error bar.
2. **Capability curricula** (reference ancestry, the L0–L3 candidate
   ladder, the §16 schools) — expected to climb; withdrawal means
   competence demonstrated without the constraint.
3. **Authority maturity ladders** (Isperia, Emrakul, Ugin) — governed by
   the learnability boundary (`../design/programme/learning.md`): **they
   may correctly stay TIGHT forever, and that is a success state**, not a
   stalled curriculum. Their transition metric is the boundary itself —
   does an external signal of sufficient density exist to grade them?

**The measuring stick** is always decision-aware, never merely numeric:
does the looser rung make the same calls as tight ground truth (rank
correlation, accept/no-op agreement, selection regret, tail-error
detection, uncertainty coverage — the §17.4/INV-44 pattern generalised)?
Every scaffold names its stick at declaration time (F.6).

**The transition metric** is a pre-registered gate on that stick —
agreement within declared limits, counted at the statistical-unit level
(INV-32), sustained over a declared window, tail cases included — owned by
the named gate owner (F.4), one axis per confirmatory transition (INV-41),
never because a different axis passed (INV-40).

**The re-tightening trigger** is explicit and symmetric: the stick
degrading in LOOSE or FREE is a named condition that escalates back a
rung. Transitions are earned in both directions.

**The conversion rule** is the default fate: withdrawal removes a
production dependency and **produces a permanent instrument** (INV-42
generalised) — harmful fixtures, the Ugin null allocator, Academy replay
as metrology lab, reference seeds and the Esper blueprint selector as
blinded controls.

## Displaced constraints

None. INV-39, INV-40, INV-41 and INV-42 already carry the mechanics; this
ADR names the semantics they enforce. The `ScaffoldManifest` fields
(`constrained_regime`, `relaxation_regimes[]`, `withdrawal_gate`,
`gate_owner`, `escalation_path`, `retained_reference_role`) are the
vocabulary's carriers — tight/loose/free is what those fields speak.

## Options considered

- **Leave the posture implicit (status quo).** Rejected: four axes and
  eleven schools with an unstated stance invited exactly the two failure
  modes the kinds-taxonomy prevents — graduating an authority nothing can
  grade, and dismantling a lab someone assumed was temporary.
- **A single global curriculum stage.** Rejected long ago by the design
  itself (§16: independent gates, not one flag); restating for the record.
- **Per-scaffold bespoke vocabularies.** Rejected: the four enum ladders
  are already isomorphic; naming the shared type costs one word per rung
  and buys a uniform review question.

## Consequences

Appendix F carries the posture (F.1 kinds + conversion rule, F.2 rung
table, F.5 re-tightening, F.6 stick question); the curriculum preamble
points at it. Future scaffold proposals declare their kind and their rungs
in F.6 terms. Reversal trigger: if a scaffold appears that genuinely
cannot be expressed as a three-rung ladder (e.g. a continuous relaxation
with no discrete gates), revisit the vocabulary by ADR rather than forcing
the fit.
