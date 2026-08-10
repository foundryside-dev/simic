# Kernel demo — exploratory analysis register

**Date:** 2026-08-10 · **Status:** registered **pre-data**, before
`--selftest --certify` · **Companion to:** spec rev 6.2
(`2026-08-09-kernel-demo-design.md`)

## Why this file exists

`--eval` is one-shot and enforces it. Everything in the frozen battery — the
lift test, the agreement gate, the money chart, the falsifier, the five verdict
booleans — is pre-registered there and is the **only** thing that may be quoted
as a result of this demo.

The studies below read the *same store* offline and answer different questions.
Registered here, before any data exists, they are **secondary exploratory
analysis**. Discovered afterwards, the identical analysis would be fishing.
That distinction is the entire purpose of this file, and it costs nothing to
buy now.

## Standing rules for everything in this register

1. **No study here may alter, re-word, or re-scope a frozen-battery claim.**
   If an exploratory result contradicts the headline, both are reported; the
   headline stands as pre-registered.
2. **Exploratory results are labelled exploratory** wherever they appear —
   in the report, in the product workspace, and in any external write-up.
3. **No p-value from this register enters a verdict boolean.** Report effect
   sizes and intervals; do not manufacture a pass/fail line after the fact.
4. **Underpowered is a result.** Where a study's resolution depends on a rate
   that is unknown pre-data (divergence rate, germination rate), report the
   realized rate beside the finding so a null reads as "underpowered below X"
   rather than as evidence of absence.
5. Adding a study to this register after data exists is permitted **only** with
   an explicit dated note saying so — which downgrades it to post-hoc, and it
   must be labelled as such.

## Registered studies

### E1 — Tail-risk predictability and the price of a veto
Predict `status == "diverged"` from **pre-decision** telemetry plus seed
identity. Report the ROC, and at each operating point the **foregone benefit**
(mean `R_best − R_noop` over the fans a veto at that point would have blocked).
*Why:* Simic's lexicographic admission invariant says the tail-risk veto is
adjudicated before any utility comparison and that the assurance class owns its
operating point. There is currently no evidence such a point is findable.
*Power:* set by the realized divergence rate; report it beside the ROC (rule 4).

### E2 — Retrieval as a policy conditioner (the MVP's L0 rung)
k-NN over normalized telemetry into the fan store, conditioning the WHICH head
on retrieved precedent; scored on the same tune split as the trained policy.
*Why:* the MVP is specified to start at retrieval over the fixed menu
(`simic-03de2210b6`). This tests the premise before Urborg's retrieval path is
designed around it.

### E3 — The price of provider blindness
Construct the blinded view offline by dropping `name` from arm payloads. Train a
judge on (telemetry, arm curve) → `R` with and without seed identity; the
accuracy delta is the empirical cost of blinding.
*Why:* dual provider blindness is currently a principle with no measured price.

### E4 — Horizon truncation
Rank correlation between `R` at the horizon and `R` truncated at epoch `t`, per
pathology. Needs only `curve_val`.
*Why:* branch QA is the dominant cost in Simic. If arms rank correctly at half
the horizon, the fan cost halves.

### E5 — Fan-width economics
Policy quality as a function of arms actually run (subsample K of the four plus
no-op). Pilot for the successor experiment's menu-scaling question.

### E6 — Post-graft trajectory studies *(enabled by rev 6.2)*
Using per-arm telemetry: (a) does a policy trained on virgin-host decisions
transfer to a host that already carries a graft; (b) what the 20-dim signature
of an arm looks like in the epochs *before* divergence; (c) whether influence
at the horizon (`g_at_horizon`, `rms_ratio_horizon`) predicts end-state `R`.
*Why:* the entire post-commit half of Simic — continued tenancy, retirement,
sequential grafts — decides about already-grafted hosts, and has no empirical
support today.
*Read the trajectory by record kind:* for `kind="fan"` it is the per-arm
`telemetry` field (post-decision); for `kind="policy_run"` it is
`FanRecord.telemetry`, which on a live eval episode is the **whole** run,
pre- and post-germination. Study (a) needs the `policy_run` form.

### E7 — Supervision cost accounting *(enabled by rev 6.2)*
From `wall_s` / `peak_mem_bytes`: cost per counterfactual arm, per fan, and per
unit of realized decision quality. Feeds `docs/design/programme/cost-model.md`
and fleet sizing.

## Explicitly NOT in this register

Menu scaling, a second slot, host families, and a retirement arm are a
**successor experiment**, not analyses of this store. They change what is
collected and breach the spec's scope pins. They are described in
`docs/superpowers/reviews/2026-08-10-kernel-demo-enhancement-analysis.md`
(Tier 3) and require their own design and sign-off.
