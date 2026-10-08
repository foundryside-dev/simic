# PDR-0051 — Validate graft lifecycle v2 before any graft-capture study

Date: 2026-10-08   Status: proposed (pending pre-launch review)   Author: Claude (session 17)
Owner sign-off: within the grant (run authorisation; PDR-0040 carriage).
The owner directed: "you're authorised to execute the study as soon as its
ready", and approved the GPU window ("you have exclusive use to them for
at least the next week or so").
Related: PDR-0047, PDR-0049, PDR-0050; design
[`bounded-lifecycle-v2.md`](../../bounded-lifecycle-v2.md); plan
[`lifecycle-v2-validation`](../../prereg/lifecycle-v2-validation.json);
`simic-75be93e372` (lifecycle instability), `simic-d9694c789d` (GPU profile)

## Context

Rung 3 of the ladder (PDR-0050) asks whether a graft captures the deficit
that rung 2 measured. On the `under_normalized` host, the graft diverges in
its germination (STE) epoch in about a quarter of units:
- positive-control-v1: 12/48;
- the reproduction: 6/16.

The mechanism is derived in the design doc. The trust term's curvature on
the seed gain exceeds the Nesterov limit c* ≈ 27.1 when the seed's raw
output is large relative to the host activation. Lifecycle v2 clamps that
curvature to 0.5·c* at every STE step, and both variants record the
witness.

An independent review of the repository (2026-10-08) asked the next plan
to do three things:
- enforce the bound;
- distinguish finite performance from failure rate;
- pin immutable execution inputs.

It also asked the plan to cover both `norm` and `conv_heavy`, together
with the separate static-host instability (positive-control-v2, seed 2142),
"rather than patching only the observed graft failure".

## The call

Run `lifecycle-v2-validation` **before** any graft-capture plan is
written. It covers three cells:
- A: `under_normalized` × `norm`;
- B: `under_normalized` × `conv_heavy`;
- C: `mild` × `conv_light`, the regression guard.

Each cell runs v1 and v2 on the same 24 fresh seeds, 4001–4024. Every seed
used by an earlier study is excluded.

**Acceptance needs all of C1–C4.** The criteria are computed by
`experiments/lifecycle_validation.py`, whose hash is pinned at launch:

- **C1, v2 stable.** No germinated scheduled-arm divergence under v2 in A
  or B, out of 48 units. A and B share one host per seed, so the 48 units
  are 24 host trajectories × 2 seed types. The report gives:
  - the pooled bounds: rule of three 6.25%, exact one-sided 6.05%;
  - per-cell bounds, which are the honest per-seed claim: 0/24 gives
    12.5% and 11.7%.

  "v2 fixes `conv_heavy`" needs at least one v1-only divergence in B.
  Without one, B reads "stable", not "fixed".
- **C2, mechanism**, on the stable cells, in two gated parts:
  - **C2a, falsification.** Every v1 divergence whose record carries the
    STE table must have shown κ_live > c*/1.1 *before* its diverging step.
    The 10% is the design's own allowance for the cross-entropy bilinear
    term; the strict-c* rate is reported beside it. The diverging row is
    excluded because it records the blow-up itself (κ ≈ 10²⁴ in the pilot).
    The ramp spans several rows before it (pre-divergence maxima of
    10⁷–10⁸ in the pilot), so the exclusion does not stop a blow-up from
    meeting the threshold.
    This can only falsify: survivors cross c* too.
  - **C2b, intervention.** v2 changes only λ_t, where κ > s·c*, on the same
    initialisation and minibatches. A seed that diverges under v1 and not
    under v2 therefore attributes the divergence to the clamped curvature.
    At least one such seed is required, and none the other way. This is not
    an independent second test. "None the other way" is part of C1, so C2b
    reads C1's result as attribution and adds only the requirement that v1
    did diverge. The McNemar p is reported but does not gate.

  With no v1 STE divergence the criterion is untestable, and that is not a
  pass. **Reported, not gated:** a within-cell AUC of the rectified growth
  score `Σ max(0, log ρ(κ_t))`, and the Spearman correlation of realised
  gain growth against that score.
- **C3, replay.** For each seed, the no-growth and static records are
  bitwise identical between the v1 and v2 runs, and the no-growth records
  are identical across the cells that share a host.
- **C4, regression guard (cell C).** No seed diverges under v2 that did not
  diverge under v1, and the finite late dev CE passes a paired TOST within
  ±0.05. The verdict is one of `equivalent`, `inconclusive` (the 90% CI
  exceeds the margin but contains 0) or `different` (the CI excludes 0).
  The report counts the units whose clamp engaged, so a trivial pass is
  visible.

**Reported, never deciding:**
- C5, host instability: no-growth and static divergences, scheduled
  divergences before germination, and lifecycle divergences that coincide
  with a host-arm divergence of the same seed, per cell;
- the performance table: failure rate and finite performance per cell ×
  variant × arm, side by side. It also gives the static − no-growth deficit
  split by the graft's outcome, which shows what the excluded pairs would
  have contributed. Diverging seeds carried the largest deficit in PDR-0047.

**Enforcing the bound.** The bound is enforced at two layers:
- by construction, in the clamp;
- at verification: `validate_witness` rejects any v2 run whose recorded
  effective curvature exceeds `s·c*`. Such a run becomes a unit failure,
  and with `max_failed_units = 0` the study reads `instrument_failure`.

**Immutable inputs.** The following are pinned:
- code: one `git archive` snapshot of the launch commit. Units train, and
  the analysis runs, from it.
- data: the plan pins the CIFAR source-file hashes and the fit/dev tensor
  hashes, launch refuses a data root that differs, and analysis refuses a
  unit whose manifest differs.
- execution: both variants of a seed run on one GPU, one process per GPU.

**Cost.** Dry run 2 measured 17.7–30.5 s per run (mean 24.7 s; three
arms, including scoring) and 4.2 minutes of wall time for 18 runs on two
GPUs. Scaled to 144 runs, that is about 30–33 minutes.

**Pilot and pre-launch reviews.** Two 3-seed GPU dry runs preceded launch
(seeds 9201–9203, archived under `docs/results/2026-10-08-lifecycle-v2-dryrun-1`
and `-2`):

- **Dry run 1** found a defect. Every clamped v2 run failed verification,
  because κ_live and λ_t were each rounded from float32 and their product
  overshot s·c* by ~8×10⁻⁸ against a 10⁻⁹ tolerance. Fixed in `b28d6f7`.
- **Dry run 2** verified all 18 units, and C3 held on 9/9 pairs.

Two Fable reviews (theory, with PyTorch and training-optimisation skills;
statistics, with counterfactual-statistics skills) then returned
GO-with-amendments. They read the pilot's records. Their findings, which
included pilot numbers, reached the author, so **the C2 restructure above
is pilot-informed**:

- the original C2 was a strict any-stage necessity test plus AUC ≥ 0.9 on
  `Σ log ρ`;
- that statistic is dominated by κ ≈ 1/lr, where the map is nearly
  nilpotent (log ρ ≈ −18). On the pilot it ranked cell C's survivors above
  the A/B divergers;
- the diverging row's κ made the necessity test tautological.

The runner now also records the float32 λ the loss multiplies, rounded
toward zero, and reads `gain_at_birth` back from the parameter (the
float64 value made `seed_gain_changed` vacuous). Seeds 9201–9206 are
excluded. Dry run 3 (seeds 9204–9206, commit `a2d1062`, archived as
`-dryrun-3`) was read for mechanics only:
- 18/18 units verified;
- C3 held on 9/9 pairs and across cells;
- none of the 629 clamped rows exceeded s·c*.

The statistics reviewer's one-pass re-check of `a2d1062` returned GO.

## Rationale

A graft-capture study on an unstable lifecycle would measure divergence,
not capture. Validating the fix separately gives two answers:
- whether v2 is stable;
- whether it is stable for the derived reason.

The second answer matters, because a fix that works for an unknown reason
can fail again at rung 4's other timings and locations. Cell C keeps v2
from silently changing the graft where v1 was already safe.

## Reading consequences

- **accepted:** write graft-capture v2 (rung 3) on lifecycle v2, covering
  both `norm` and `conv_heavy`. That plan must state how it treats host
  instability, which C5 will have measured.
- **C1 fails:** the clamp is insufficient. First diagnose the failing stage
  from the recorded stage and witness: blending entry is the predicted
  residual mode. If the failure is flagged host-coincident, diagnose it as
  host instability first.
- **C2a fails:** the derivation is wrong for the listed units. If a listed
  unit is host-coincident, diagnose it before any claim. Return to
  diagnosis; no graft study.
- **C2b fails (C1 holds):** no seed shows v2 removing a v1 divergence. The
  mechanism is unexercised, which is not a pass.
- **C2 untestable:** no v1 STE divergence; not accepted.
- **Ranking below 0.9 (reported only):** the linear limit is necessary but
  does not rank which over-limit units diverge. Record it as a diagnosis
  note. The premise is **not** withdrawn.
- **C3 fails:** a replay defect. Treat it as an instrument bug before
  reading anything else.
- **C4 `different`:** v2 changes the graft where v1 was safe. Redesign the
  clamp (for example, its safety factor) under a new PDR.
- **C4 `inconclusive`:** under-resolved at n = 24, not evidence of a
  change. A new PDR decides between more units and accepting the risk.
- **instrument_failure:** investigate the failures. Any re-run uses fresh
  seeds and is disclosed as informed by the partial report.

Acceptance is a four-way conjunction, so false-rejection risk accumulates.
Each criterion is read on its own consequence above, never as "the study
failed".

## Reversal trigger

Any change to the plan or analysis module after launch is an amendment,
and the analysis refuses a changed plan or module. If C2a fails, this PDR's
premise, the derived mechanism, is withdrawn for the listed units.
