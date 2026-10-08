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
  or B, out of 48 units. The report gives the rule-of-three bound (6.25%)
  and the exact one-sided bound (6.05%).
- **C2, mechanism.** Every germinated v1 divergence showed max κ_live > c*
  during STE (sensitivity 1.0), and the amplification `Σ log ρ(κ_t)` ranks
  divergence with AUC ≥ 0.9. With no v1 divergence the criterion is
  untestable, and that is not a pass.
- **C3, replay.** The no-growth and static records are bitwise identical
  between the v1 and v2 runs of each seed.
- **C4, regression guard (cell C).** No seed diverges under v2 that did not
  diverge under v1, and the finite late dev CE passes a paired TOST within
  ±0.05.

**Reported, never deciding:**
- C5, host instability: no-growth and static divergences, plus scheduled
  divergences before germination, per cell;
- the performance table: failure rate and finite performance per cell ×
  variant × arm, side by side.

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

**Cost.** The determinism probe measured 8.0 s per arm on one GPU at this
configuration. That gives about 24 s per run and 144 runs, or about
30 minutes on two GPUs. Diverged arms stop early.

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
- **C1 fails:** the clamp is insufficient. Diagnose the failing stage from
  the recorded stage and witness before any change.
- **C2 fails or is untestable:** the derivation is wrong or unexercised.
  Return to diagnosis; no graft study.
- **C3 fails:** a replay defect. Treat it as an instrument bug before
  reading anything else.
- **C4 fails:** v2 changes the graft where v1 was safe. Redesign the clamp
  (for example, its safety factor) under a new PDR.
- **instrument_failure:** investigate the failures before any re-run.

## Reversal trigger

Any change to the plan or analysis module after launch is an amendment,
and the analysis refuses a changed plan or module. If C2 fails, this PDR's
premise, the derived mechanism, is withdrawn.
