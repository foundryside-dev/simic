# PDR-0005 — Set the scoreboard: dates as pacing signals, adjudication-bound numbers, audience confirmed

Date: 2026-08-08   Status: accepted   Author: Claude (product-owner session)
Owner sign-off: yes — recommendations accepted verbatim in-session 2026-08-08.
Related: metrics.md, vision.md (Who it serves), simic-642c2c1823 (cost model),
simic-ae3caf44f1 (lexicographic admission), simic-0dd5362f05 (decision gate)

## Context
The bootstrap seeded metrics.md with TBD placeholders. A talk-through with the
owner settled each. Owner framing that governs interpretation: **this is a
spare-time moonshot; the dates are for the owner's own use** — pacing signals,
not delivery commitments.

## Options considered
Per item, discussed in-session: invent numbers now (rejected where the honest
number is the output of a pending adjudication or cost model — prejudging the
gate); leave TBD (rejected where a real date was settable — unfalsifiable
targets never fire); bind to the producing event (chosen where applicable).

## The call
1. **North-star:** shape pre-committed — admission-worthy pool rate ≥ K× the
   random-search control over the first N adjudicated pools after Phase G; K and
   N are outputs of the §22.11 cost model (simic-642c2c1823), due before
   Phase A.
2. **Design-debt burn-down:** 0 open `hld-review` items by **2026-08-31**.
3. **Phase A complete by 2026-09-30**, provisional; revise by PDR if the gate
   reshapes §9 materially.
4. **Harmful-intervention ceiling:** deliberately unnumbered until the
   simic-ae3caf44f1 adjudication defines the tail-risk veto's operating point.
5. **Secondary audience (vision.md):** both, ordered — implementation agents
   (operational), the morphogenetic-AI research community on publication
   (eventual; negative results publishable per §28).

## Rationale
Falsifiability without theatre: real dates where the work is estimable, explicit
event-bindings where the number belongs to a pending decision, and a recorded
interpretation rule so a fired date triggers re-planning rather than reading as
a broken promise.

## Reversal trigger
The dates are the triggers: if 2026-08-31 or 2026-09-30 passes unmet, the next
session's DECIDE must explicitly re-plan (re-date by PDR, re-scope the bet, or
kill it) — silent drift past a fired date is the failure mode this PDR exists to
prevent. The K/N and ceiling bindings fire when their producing tasks close
without delivering the number.
