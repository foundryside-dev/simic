# PDR-0007 — Decision gate adjudicated: 23 proposals accepted, Tamiyo rename rejected, fast-landing folded

Date: 2026-08-08   Status: accepted   Author: Claude (product-owner session)
Owner sign-off: yes — every ruling made by john in-session (AskUserQuestion),
2026-08-08; executed same session.
Related: simic-0dd5362f05 (gate, closed), adjudication record in its comment #6,
docs/concept/reviews/2026-08-08-esper-pivot-peer-review.md, PDR-0004, PDR-0006

## Context
The 2026-08-08 peer review left 25 reviewer proposals blocked behind a decision
gate so they could not be written into the HLD as if they were decisions. The
gate sat at the top of the critical path with 27 items blocked behind it.

## The call
1. **Accepted (23, released as ready work):** all four constitutional-guard
   items, all four honest-evidence statements, all six scoreboard/criteria
   items, all six control/stability items, the critic specifications, and the
   keystone — **lexicographic admission** (simic-ae3caf44f1): tail-risk veto
   evaluated before utility comparison, not tradeable against it. The
   metrics.md harm-ceiling guardrail binds to its implementation. Sequencing
   added: Schmitt-trigger hysteresis (ed2698fafd) behind it (both rewrite the
   admission spec).
2. **Rejected (wontfix):** the Tamiyo rename (simic-3a17fe545d). Namespec 1.0
   stands. Owner rationale: Tamiyo-as-strategist was a **deliberate
   promotion** (character preference), not an oversight; under the PDR-0006
   clean seam the legacy tactical meaning is history, not a live constraint.
3. **Folded:** fast-landing implications (simic-eb5573bbb7) became a
   conditionality note under the winning-branch-deployment open decision
   (commit 8ee732e); no standing backlog item for an unpursued path.
4. **Docket additions discharged:** §27.1 closure ADR filed
   (simic-a708c5b1b7, carries the Namespec reaffirmation and the owner's
   "weatherlight" name-shelf note).

## Rationale
The proposals were overwhelmingly consistent with the constitution, the reset
rationale, and the owner's own statements in the review thread; the gate's
purpose was owner ratification, not re-derivation. Presenting every item for
explicit ruling also neutralised the gate's known caveat (five collapsed owner
turns made the original decision/proposal split partly inferred).

## Reversal trigger
Rulings reopen individually and only through the ADR process: if an
implementing task finds a ruling contradicts a §18 invariant (INV-nn) that
cannot be resolved without displacing something unsanctioned, that task stops
and escalates rather than absorbing the conflict. The rename rejection reopens
only on the PDR-0006 class of external constraint. The burn-down date
(2026-08-31, PDR-0005) remains the governing pacing trigger for the bet.
