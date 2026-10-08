# Positive control v1 — result, 2026-10-08

**Pre-registered reading: `instrument_failure`.** 12 of 48 units failed
(limit: 4). Under the plan's launch condition, **`graft-capture-v1` does not
launch.**

The control's own question was **not tested**: static − no growth on the
`under_normalized` host. Every failure came from a *different* arm.

- In all 12 failed units, the **scheduled (graft) arm** diverged to a
  non-finite training objective during epoch 2. That is its germination
  epoch, when the seed trains in pass-through (STE) mode.
- The runner treats any arm's divergence as a fatal error for the whole
  unit. So the static and no-growth arms of those 12 units, which completed
  all ten epochs, were lost to the frozen analysis.

Decision record: [PDR-0047](../product/decisions/0047-positive-control-instrument-failure-graft-divergence.md).

## What ran

| Item | Value |
|---|---|
| Plan | [`docs/prereg/positive-control-v1.json`](../prereg/positive-control-v1.json) (PDR-0046), hash `709049ea…` |
| Source | commit `fe6c7ed`, clean tree. The analysis module is hash-pinned (`89fce23b…`) |
| Linked plan | `graft-capture-v1.json` pinned at `a7362feb…` in the launch record. It was unchanged throughout. |
| Units | seeds 2001–2048; `under_normalized` host with the `norm` seed; 4,096 fit / 5,000 dev; 10 epochs; graft before epoch 2 |
| Execution | 8 workers. 36 units completed, 12 exited non-zero. 4.1 CPU-hours (sum of unit wall times in `launch-finished.json`) |
| Analysis | Run once, with the frozen module, after the launcher exited. Output `screen_report.json`: reading `instrument_failure`, `n_units` 36, 12 failures (`FileNotFoundError` for the missing `complete.json`). |

## Why the units failed (root cause)

Each failed unit's stderr ends `ValueError: non-finite training objective`
(`bounded_comparison.py`, `train_epoch`). Counting epoch records per arm,
without reading any values, gives the same shape in all 12: no growth has 10
epochs, static has 10, scheduled has 2. In every case the scheduled arm died
in its germination epoch.

**Reproduction on fresh exploratory seeds** (6001–6016, outside every plan).
The script is the scheduled arm's own code path, instrumented per step:

- **6 of 16 seeds diverge**, at steps 16–109 of the germination epoch.
- The seed's gain oscillates in sign with growing amplitude, for example seed
  6001: 0.013 → 0.019 → −0.010 → … → 4.1 → −0.76 → 11.7 → −156 →
  1.5×10⁶ → ∞. The trust-region term explodes with it.
- Activations are *small* (rms ≈ 0.14–0.29). That refuted the first
  hypothesis, which was large activations.

**Single-variable tests on the 6 diverging seeds:**

| Change | Result |
|---|---|
| Trust-region term off (λ ≈ 0), same learning rate 0.05 | 6/6 complete |
| Learning rate 0.02, trust region on (λ = 1) | 6/6 complete |

**Mechanism:**
- The kernel's trust-region penalty is `λ·mean(δ²)/mean(h²)`
  (`kernel_demo.py`, `Slot.trust_region_loss`). The curvature it puts on the
  seed's parameters scales with (rms of the seed's raw output ÷ rms of h)².
- The kernel comment "lam = 1.0 sits inside the stability bound
  lam < 1/seed_lr" implicitly assumes that ratio is about 1.
- The `norm` seed's raw output, `GroupNorm(h) − h`, is roughly unit-scale
  whatever h is. On this un-normalised host h is about 0.2, so the bound is
  violated.
- Momentum-SGD at learning rate 0.05 then oscillates and diverges in a
  sizeable fraction of seeds: 12/48 here (25%; Wilson 95% interval 15–39%),
  and 6/16 in the reproduction.

Two separate defects follow from this, with different fix paths
(PDR-0047):

1. **Runner abort semantics (measurement defect).** The kernel demo had
   already learned that "a non-finite arm is measured, not an abort" (test
   `test_nonfinite_arm_is_measured_not_abort`). The bounded runner
   regressed it, so one arm's crash destroyed two other arms' valid
   evidence.
2. **Trust-region scaling (lifecycle defect).** This is `@semantic` kernel
   code. Changing it changes what "the scheduled graft" means, so it belongs
   to a lifecycle redesign, not a quiet fix.

## Exploratory estimate (not the pre-registered answer)

Both control arms completed all ten epochs in every unit, so the
static − no growth difference can be computed on all 48 units from
`training.jsonl`.

Caveats:
- This is post hoc and is **not** the control's reading.
- The 12 failed units have no `complete.json`, so their logs are not
  checksum-sealed.

| Units | Static − no growth, late dev CE (epochs 7–9) | 95% t interval | sd |
|---|---|---|---|
| All 48 | −0.159 | [−0.187, −0.131] | 0.097 |
| 36 completed units (the survivor subset) | −0.134 | [−0.159, −0.110] | 0.072 |
| 12 graft-diverged units | −0.232 | [−0.312, −0.153] | 0.126 |

Readings:

- On all 48 units, the interval lies beyond the pre-registered floor of
  δ_pc = 0.10. Had the evidence been analysable, the control would very
  likely have passed. The deficit on this host appears real.
- **The survivor subset is biased.** The seeds whose graft diverged are the
  ones with the largest deficit. That is consistent with the mechanism:
  smaller activations give the `norm` seed more to repair and also more
  instability. Analysing only completed units would have understated the
  effect by about 16%. This is a measured example of why a post-treatment
  condition on one arm must not select the units for another arm's
  contrast.
- The pre-launch planning spread (0.115) bracketed the observed 0.097 on
  all 48 units.

## Corrections to the frozen plan text

The plan was hash-pinned, so it is not edited. The corrections are
recorded here:

- `sealed_arm`: "the scheduled arm's training logs are not opened" was
  never fully true. The shared reducer parses every arm's records, and
  failures name the failing file. In this study the seal was broken by
  design through the failure records, which revealed that and when the
  graft diverged. No scheduled-arm *value* was read for the analysis. The
  plan's seal lasted "until graft-capture-v1 launches or is abandoned".
  Since that study does not launch as written, the seal is released.
- `fail_readings_report`: "every reading reports the realised sd …" was
  false for `instrument_failure`, whose report carries no contrasts. This
  is fixed in the analyzer (`simic-6cb47b3a06` follow-up).

## Evidence

[`2026-10-08-positive-control-v1/`](2026-10-08-positive-control-v1/)
contains:
- `screen_report.json`, `launch.json` and `launch-finished.json`;
- for every unit, `training.jsonl`;
- for the 36 completed units, `complete.json` (all 36 checksums verified);
- for the 12 failed units, the tail of their stderr.

The per-unit manifests, checkpoints and the sealed runner stdout stay
local in `runs/positive-control-v1/`. The reproduction script and its
outputs are in the session scratchpad and are summarised above.
