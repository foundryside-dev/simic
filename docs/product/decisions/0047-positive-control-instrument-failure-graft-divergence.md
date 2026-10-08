# PDR-0047 — Positive control reads `instrument_failure`: the graft lifecycle diverges on an un-normalised host, and the runner let it destroy the control

Date: 2026-10-08   Status: accepted   Author: Claude (session 17)
Owner sign-off: within the grant. This applies the pre-committed reading
of PDR-0046. The owner directed on 2026-10-08: "continue working through
the bugs, use systematic debugging and systems thinking".
Related: PDR-0046, ADR-0018, result
[`docs/results/2026-10-08-positive-control-v1.md`](../../results/2026-10-08-positive-control-v1.md),
`simic-f73351380d`, `simic-6cb47b3a06`

## Context

`positive-control-v1` ran 48 units. 12 failed, against a limit of 4, so the
frozen analysis published **`instrument_failure`**. Under PDR-0046's launch
condition, **`graft-capture-v1` does not launch as written.**

Systematic debugging (result note) located the cause:

- in every failed unit, the *scheduled* arm diverged in its germination
  (STE) epoch;
- the trust-region penalty's curvature violates the kernel's stated
  stability bound when the seed's raw output scale far exceeds the
  activation scale, as with the `norm` seed on the un-normalised host;
- the instability reproduced in 6 of 16 fresh seeds;
- in single-variable tests, turning off the trust-region term, or lowering
  the learning rate, removed it in 6/6.

## The call

1. **The reading stands as published.** It is `instrument_failure`, not a
   reinterpretation. The control's own question was not tested, because a
   different arm's crash took the units down.
2. **Two defects, two separate fix paths.**
   - **Runner abort semantics, fixed now (measurement defect).** A diverged
     arm becomes a recorded per-arm outcome, and the unit completes.
     `verify_run` accepts it, and analysis applies a pre-declared rule for
     diverged arms. This restores the kernel demo's lesson ("a non-finite arm
     is measured, not aborted"), which the bounded runner had regressed.
   - **Trust-region scaling, not fixed now (lifecycle defect).** It is
     `@semantic` kernel code and changes what "the scheduled graft" means.
     Candidate fixes are normalising the penalty by the seed's output scale,
     a lower seed learning rate, or bounding the gain. A pre-registered graft
     redesign chooses among them, with review, under `simic-f73351380d`.
     Per ADR-0018: do not enlarge the controller.
3. **The graft's divergence rate on this host is itself a result:** 12/48 =
   25%, Wilson 95% interval 15–39%. Any future graft study on a host with
   small activations has to pre-declare how a diverged graft arm is
   scored.
4. **Next:**
   - fix the runner and the latent analyzer defects from the 2026-10-08
     code sweep, in one reviewed change;
   - sweep the kernel for other stability claims stated only in comments;
   - write `positive-control-v2` (fresh seeds, arm-level divergence
     recorded, the scheduled arm's divergence a recorded boolean) and review
     it before launch.

## Exploratory, explicitly not the reading

Both control arms completed in all 48 units. Static − no growth computed
from the logs is −0.159 [−0.187, −0.131] across all 48. That is beyond the
floor, so the deficit appears real. The survivor-only subset (−0.134)
understates it, because the graft diverges most where the deficit is
largest. This supports running v2. It does not substitute for it.

## Rationale

The pre-commitment did its job. Under it, a failure in one arm could not
be quietly worked around, and it surfaced a real lifecycle instability that
a reading taken from survivors alone would have hidden. Re-reading the
control from the 48 logs would be a post-hoc reading under a different
rule, the exact move pre-registration exists to prevent.

## Reversal trigger

If the runner fix shows that the 12 failures had a cause other than
germination-epoch divergence, this record's root cause is wrong and returns
to investigation. That would mean a diverged no-growth or static arm, or a
divergence outside epoch 2, in a re-run on fresh seeds.
