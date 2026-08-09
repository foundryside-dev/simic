# PDR-0026 — Pull the cost model forward out of wave order and adopt it (ADR-0014); fix K/N; owner decides negative-result scope and endpoint family

Date: 2026-08-09   Status: accepted   Author: Claude (product-owner session 12)
Owner sign-off: RECEIVED 2026-08-09 — the pull-forward was proposed in the
resume brief and the owner said "lets kick off that decision"; the two
claim-scope calls inside it (D1, D2) were put to the owner explicitly
in-session and answered.
Related: ADR-0014, simic-642c2c1823 (closed), PDR-0024 (anchor corpus —
comment-20 formula corrected ~2×), PDR-0025 (ADR-0013 exactness tax is a
model parameter), metrics.md north-star

## Context

simic-642c2c1823 (§22.11 worked cost model, wave:5-scoreboard) had become
the load-bearing unstarted item: three decisions consumed its missing
numbers — the north-star's K and N (metrics.md delegates them to this
model), the anchor-corpus pricing (PDR-0024, issue comment 20), and the
Phase B exactness-tax measurement (ADR-0013). Session 11's checkpoint
already recommended considering the pull-forward. The
axiom-experiment-formalisation pack landed the same day; its own boundary
routes fleet-size/pre-registration work to counterfactual-statistics,
which shaped the dispatch.

## Options

1. Hold wave order (wave:2-momir next) and let three consumers keep
   accumulating against an unpriced budget.
2. **Pull simic-642c2c1823 forward, dispatch under the
   counterfactual-statistics discipline, land as ADR + chapter.** (chosen)

## The call

Pulled forward, dispatched to the counterfactual-statistician agent,
accepted after review (arithmetic spot-checked; the measured esper-lite
inputs — 13-entry catalogue, compute multipliers 1.02–1.35, thousands of
germinations per log — verified against source). Landed as ADR-0014 + new
chapter `docs/design/programme/cost-model.md` + committed pre-registration
`prereg-cost-model-campaign-1.md`; §22.11 and §27.15 now point at the
model; issue closed. Headlines: programme ≈ 10³ HER; per-admitted-growth
1.0–5.2 HER at placeholders; the 40-HER restructure threshold is armed
with the tiered Field QA cascade as the pre-named lever, and it is live,
not hypothetical.

Two claim-scope decisions inside the model were escalated to the owner
in-session and decided:

- **D1 (negative-result scope):** pre-register the inferiority margin the
  budget buys — at n = 32 the fleet can conclude "Momir is not ≥ 1.5×
  random search" at 80% power; §28's negative-result clause holds at that
  stated strength. Symmetric refutation (n = 185, ~6× the confirmatory
  fleet) priced and declined; exploratory-only downgrade declined.
- **D2 (endpoint family):** the rate clause is the single primary
  confirmatory endpoint; the online-cost clause is descriptive (no α
  spent, n stays 32). Family-of-2 at n = 39 priced and declined.

**K and N are fixed:** K = 1.5, N = 256 adjudicated pools = 32 base
trajectories × 8 pools — always stated in that order (INV-32). Recorded in
metrics.md this checkpoint.

## Rationale

The model gates three recorded decisions' numbers; every week it stayed
open, more design text cited an unpriced budget. K = 1.5 is the knee of
the derived power table (a 2.0 floor doubles the fleet for one notch of
claim strength). D1's option 2 and D2's primary/descriptive split are the
only choices that keep §28 defensible without growing the fleet.

## Reversal trigger

ADR-0014 carries the design-level triggers (QA-horizon optimum h ≥ 0.10;
measured ρ > 0.45; non-nested horizons). Product-level: if campaign 1's
M2/M3 measurements move the derived n above ~48 trajectories (≈ +50%
programme fleet cost), the K/N choice returns to DECIDE with the owner —
that is a budget re-plan, not a mechanical re-derivation.
