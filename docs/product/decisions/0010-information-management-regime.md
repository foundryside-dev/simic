# PDR-0010 — Adopt the information-management regime (ADR-0002) as pre-Phase-A foundation work

Date: 2026-08-08   Status: accepted   Author: Claude (product-owner session)
Owner sign-off: yes — owner initiated ("codify what and when and how I store
information now — data management was the other bugbear of esper and its lite
variant"), selected approach A and every design fork in-session, and directed
"approved as an ADR".
Related: ADR-0002 (docs/adr/0002-information-management-regime.md),
simic-357c92664c (implementation), simic-4da299ff46 (CI gate coordination),
simic-642c2c1823 (cost model gates the physical-storage LLD)

## Context
Esper/esper-lite's second systemic failure, owner-named this session:
requirements and interfaces drifted without record; telemetry standards were
unevenly defined with no marker separating locked from TBD; no sign-or-lock
gate existed for a component. Runtime side: ad-hoc formats, lost lineage,
silent mutation. The HLD specifies what Sarpadia retains but no regime
governed definitional maturity or storage policy — and Phase A
(contracts-first) is the next Now→Next transition.

## The call
Adopt ADR-0002's two-layer regime, effective immediately: (1) named
definitional units (each Leyline contract, each telemetry standard, the
namespec, the INV set) carry draft/approved/locked state in plainweave —
locks are immutable baselines, the owner is the sole signing actor, drift is
mechanically detected via baseline diff behind a legis-graded gate; a
telemetry field not in a locked standard does not ship. (2) Runtime data
policy P1–P7 (append-only, unmeasured ≠ zero, one authority per record class,
schema-versioned, hash identity, declared retention budgets, grouping key at
write) binds all future storage work; physical design deferred to a Phase A
LLD behind the cost model. Implementation (ops chapter, plainweave seeding,
gate wiring) is simic-357c92664c, P1, inside the Now bet alongside the wave
programme — it does not displace wave:1 on the critical path.

## Rationale
Same counter-design pattern as PDR-0009: make the esper failure class
unrepresentable rather than policed by vigilance. TBD becomes a recorded
state instead of an ambient condition; lock authority moves from doc headers
(honour system) to immutable baselines with attribution. Chosen over a repo
manifest (double bookkeeping — a self-inflicted drift channel) and over
convention-only front-matter (the esper honour system with tidier headers).
Maximal Weft dogfood, per the owner's standing instruction that tool defects
be surfaced, never worked around.

## Reversal trigger
ADR-0002's: if plainweave bookkeeping measurably slows design work or the
tool proves unreliable, fall back to convention-only front-matter carrying
the same state vocabulary — states survive, machinery changes. Watch: the
design-debt burn-down (metrics.md) must not stall on regime overhead; a
second consecutive flat session with regime work as the cause fires this
trigger for review.
