# PDR-0001 — Bootstrap the Simic product workspace from observed state

Date: 2026-08-08   Status: accepted   Author: Claude (product-owner session)
Owner sign-off: partial — grant carryover directed by owner in-session; audience
assumption and metric targets awaiting confirmation.
Related: vision.md, roadmap.md (Now), metrics.md, ~/esper-lite/docs/product/

## Context
`/own-product` was invoked on a repo with no product workspace. Simic is
pre-implementation: the HLD (v4.1) is canonical and locked, no source code exists,
and the tracker carries an active design-review reconciliation campaign
(`hld-review`) with a decision gate at the top of the critical path. Ownership is
stateful; the workspace had to be constructed from observed reality, not remembered.

## Options considered
1. **Seed the Now bet as design hardening (chosen)** — pro: 43 open design items
   including a decision gate mean the contract surface is not yet stable; con:
   defers visible engineering progress.
2. **Seed the Now bet as Phase A directly** — pro: §30 names it the first
   milestone; con: implementing contracts while the review may still change them
   (e.g. dropping BootstrapAncestryContext, lexicographic admission) churns every
   downstream package. Rejected.
3. **Do nothing (no workspace)** — rejected: a stateless agent's only memory is
   the workspace; ownership fails without it.

## The call
Bootstrap the five artifacts from the repo, the HLD, filigree, and the Esper-pivot
record. Now = design hardening; Next = Phases A–B; Later = Phases C–K, the
Esper-derived controls, and the rename decision. Authority grant carried over from
esper-lite at the owner's direction ("this is a carry over of that experiment in a
new form"), adapted to Simic; one repo-discipline line restating HLD §30 was
appended and flagged for owner review rather than added silently.

## Rationale
The observed direction (git history, tracker critical path, the peer-review
record) all point the same way: the current work *is* the review reconciliation,
and the HLD itself sequences implementation behind it (§25, §30). The workspace
should record reality, not invent a fresh strategy.

## Reversal trigger
Revisit if the owner corrects the inferred vision, audience, or metric targets; or
if the adjudication of simic-0dd5362f05 redirects the Now bet (e.g. by promoting
the Esper-controls baseline work into Now). In any case, review this PDR at the
first `/product-checkpoint`.
