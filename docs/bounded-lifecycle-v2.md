# Bounded graft lifecycle v2 — design

Status: **draft for review** (2026-10-08). Tracker: `simic-75be93e372`.
Authority: PDR-0049 (accepted), PDR-0050.

## Why

On the `under_normalized` host, the scheduled graft diverges in its
germination (STE) epoch in about 25% of units (positive-control-v1:
12/48; reproduction: 6/16). A kernel stability sweep derived the
mechanism, and the measurements match it:

- During STE training, the trust-region penalty `λ·mean(δ²)/mean(h²)`,
  with `δ = g·f(h)`, puts this curvature on the gain:
  `κ_tr = 2λ·(rms_f / rms_h)²`.
- Nesterov momentum-SGD at learning rate `lr` and momentum `m` is stable
  along that direction only if `κ_tr < c* = 2(1+m) / (lr·(1+2m))`. At
  lr 0.05 and m 0.9, c* ≈ 27.1. The sweep measured 27.13.
- The kernel's comment ("λ < 1/seed_lr") implicitly assumes
  `rms_f ≈ rms_h`.
- The `norm` seed's raw output (`GroupNorm(h) − h`) is unit-scale. So is
  `conv_heavy`'s (its final BatchNorm pins it to 1). When
  `rms_h ≲ 0.27`, κ_tr exceeds c*. The CIFAR band, 0.14–0.29, straddles
  that edge.
- The denominator `mean(h²)` is the live batch, so the bound can hold at
  birth and fail mid-epoch.

## What v2 changes (only what the mechanism requires)

1. **Frozen denominator.** At birth, record `trust_rms_h` (the slot rms
   on the calibration batch tau_init already uses). The penalty becomes
   `λ_eff·mean(δ²)/trust_rms_h²`.
2. **Scale-aware λ.** At birth, set
   `λ_eff = λ·min(1, s·c*·trust_rms_h² / (2λ·rms_f0²))`. That makes
   `κ_tr(birth) ≤ s·c*`, with safety factor `s = 0.5`. The runner
   **asserts** the bound at birth. The bound is enforced, not just
   commented.

Unchanged: tau_init, STE, the blend and beta ramps, joint training, the
optimiser, the learning rates and the kernel demo's `@semantic` code.
`kernel_demo.py` is not edited, so its configuration hash is unchanged.

**Explicitly out of scope.**
- A separate gain learning rate (sweep finding 5) is a second hypothesis.
  It is adopted only if v2 fails validation.
- The static-arm failure on seed 2142 (host learning-rate edge, sweep
  finding 4) is a different mechanism. v2 does not address it, and
  validation does not claim it.

## Implementation (bounded layer only)

- `RunSpec` gains `lifecycle: "v1" | "v2"` (default `"v1"`, so existing
  runs and plans stay valid) and `trust_safety: float = 0.5`. Neither may
  be set by a v1 plan.
- `experiments/bounded_comparison.py` gains a `ScaleAwareSlot(Slot)`. It
  overrides `trust_region_loss` and stores `trust_rms_h`, `rms_f0`,
  `lam_eff` and `curvature_at_birth` when the seed attaches. The variant
  is chosen from the spec, and the manifest records it.
- **Instrumentation for both variants, additively:**
  - each germination's birth record carries `rms_h_birth`, `rms_f0` and
    `predicted_curvature_birth = 2λ·(rms_f0/rms_h_birth)²`;
  - each epoch record carries the gain's minimum and maximum and the
    maximum observed `2λ_eff·mean(f²)/denominator²` during STE.

  This makes the mechanism testable, not just the outcome.
- `verify_run` requires the variant and validates the new fields.

## Validation study (pre-registered as its own PDR before running)

An exploratory engineering acceptance test on fresh exploratory seeds, run
on CPU in parallel:

| Cell | Host × seed | v1 prediction | v2 requirement |
|---|---|---|---|
| A | `under_normalized` × `norm` | diverges when the birth curvature > c* | 0 divergences |
| B | `under_normalized` × `conv_heavy` | diverges when the birth curvature > c* | 0 divergences |
| C | `mild` × `conv_light` | stable (curvature ≪ c*) | stable, and its late dev CE equivalent to v1 within ±0.05 (regression guard) |

There are 24 seeds per cell, run under both variants: 144 units, about
14 CPU-hours.

**Acceptance criteria, declared before running:**
- v2 has zero non-finite scheduled arms in cells A and B;
- in the v1 cells, divergence agrees with "predicted birth curvature > c*"
  in at least 90% of units (the mechanism test);
- cell C is equivalent within ±0.05.

If the mechanism test fails, the derivation is wrong. Do not proceed to a
graft study; return to diagnosis.
