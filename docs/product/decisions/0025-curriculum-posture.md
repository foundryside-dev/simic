# PDR-0025 — Set the curriculum posture: tight/loose/free (ADR-0012) and scope the bitwise bet (ADR-0013)

Date: 2026-08-09   Status: accepted   Author: Claude (product-owner session 11)
Owner sign-off: RECEIVED 2026-08-09 — owner called for the posture ("worth
taking a moment now to set our 'curriculum posture' across the full
system"), named the three stages tight/loose/free, asked for a playback,
and confirmed it ("yes to all 3").
Related: ADR-0012, ADR-0013, simic-eb0cf50deb, simic-d1bdc7173f,
simic-642c2c1823 (tax measurement feeds the cost model)

## Context

The design had four scaffold axes, eleven curriculum schools, rule-driven
authorities and a field surrogate — training wheels everywhere, posture
stated nowhere. The owner also flagged the design's most load-bearing
wheel directly: bitwise precision "is either inspired or going to footgun
us in 6 months."

## The call

Two artifacts, both landed:

1. **ADR-0012 — tight/loose/free.** The three rungs named as the shared
   type of all four `ScaffoldState` ladders; three kinds of wheels
   distinguished (measurement scaffolds, capability curricula, authority
   ladders — the last may correctly stay TIGHT forever); decision-aware
   measuring stick per scaffold; pre-registered transition gates; explicit
   re-tightening triggers; conversion-as-default-fate. No invariant
   amended — the ADR names the semantics INV-39..42 enforce.
2. **ADR-0013 — the bitwise verdict: both, and scoped.** Inspired as a
   bounded metrology lab; footgun only if it leaked. INV-05 amended to
   bind bitwise identity to a declared, pinned execution-stack identity
   with re-baselining as a recorded event; Phase B measures the exactness
   tax and chooses the operating point (including the CPU-lab option) from
   data; topology-change kernel/RNG discipline named as a Tolaria LLD
   deliverable.

## Rationale

A posture stated once beats a stance re-derived per scaffold: it prevents
the two failure modes the census exposed (graduating an authority nothing
can grade; dismantling a lab assumed temporary) and converts the owner's
6-month footgun intuition into four specific, closed gaps rather than a
lingering unease.

## Reversal trigger

ADR-0012: a scaffold that genuinely cannot express as a three-rung ladder
reopens the vocabulary by ADR. ADR-0013: re-baselining churn dominating
lab maintenance reopens the Academy stack choice (e.g. CPU-only) by ADR.
Both inherit PDR-0021's standing rule: signals fire, they are never
silently drifted past.
