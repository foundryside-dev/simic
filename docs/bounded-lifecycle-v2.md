# Bounded graft lifecycle v2 — design

Status: **revised after Fable design review** (2026-10-08). Tracker:
`simic-75be93e372`. Authority: PDR-0049 and PDR-0050 (both accepted).

## Why

On the `under_normalized` host, the scheduled graft diverges in its
germination (STE) epoch in about 25% of units (positive-control-v1:
12/48; reproduction: 6/16). The mechanism is derived, and the design review
confirmed the formulas exactly:

- **The optimiser's limit.** Nesterov momentum-SGD as torch implements it
  (dampening 0) is stable along a direction of curvature κ only if
  `κ < c* = 2(1+m) / (lr·(1+2m))`. At the seed group's lr of 0.05 and
  momentum 0.9, c* ≈ 27.1. Measured: the spectral radius crosses 1 between
  κ = 27.14 and 27.30.
- **The trust term's curvature.** In the STE stage, the trust term
  `λ·mean(δ²)/mean(h²)`, with `δ = g·f`, puts curvature
  `κ = 2λ·mean(f²)/mean(h²)` on the gain g. This agrees with the full
  Hessian to four digits.
- **What cross-entropy adds.** Under STE, cross-entropy adds no curvature
  along g. It adds a bilinear gain × body term, which raises the top
  eigenvalue by up to about 10% for `conv_heavy`.
- **Why the kernel's comment fails.** The comment ("λ < 1/seed_lr")
  assumes `mean(f²) ≈ mean(h²)`. The `norm` and `conv_heavy` seeds' raw
  outputs are about unit-scale. When rms(h) ≲ 0.27, κ exceeds c*.

## What v2 changes: a per-step curvature clamp

Each STE step computes, live and detached from the gradient:
- `D_t = mean(h²)`;
- `S_t = mean(f(h)²)`, from one extra seed forward pass under `no_grad`;

and uses

`λ_t = min(λ, s·c*·D_t / (2·S_t))`, with safety factor `s = 0.5`.

The trust term becomes `λ_t·mean(δ²)/D_t`. By construction the
trust-term curvature on the gain is `κ_t = 2λ_t·S_t/D_t ≤ s·c*` at
**every** step. The `s = 0.5` margin covers the ~10% cross-entropy
bilinear term. When v1 is already safe, λ_t = λ and v2 is v1. Nothing is
frozen, so nothing can drift.

**Rejected:** the first draft froze the denominator at birth and set a
birth-only λ_eff. The review showed that is unsound for the `norm` seed.
`S_t` grows with h while a frozen `D_0` does not, so v2 diverged in 5/5
seeds where v1 survived. The draft's "assert at birth" was also
tautological.

Unchanged: tau_init, STE, the blend and beta ramps, joint training, the
optimiser and the learning rates. `kernel_demo.py` is not edited (v2 is a
bounded-layer `Slot` subclass). Note that the parked kernel demo campaign
(`under_normalized` × `norm`) therefore remains exposed to the defect.

**Out of scope, and not claimed:**
- a separate gain lr (sweep finding 5);
- host-edge stability (seed 2142, sweep finding 4);
- `conv_heavy`'s body saddle from the linear STE pseudo-loss, an lr-class
  hazard;
- graft *value*. v2 changes λ in exactly the cells where it matters, so it
  may change what the graft achieves there.

## Implementation (bounded layer)

- **RunSpec.** `RunSpec` gains `lifecycle ∈ {"v1", "v2"}` and
  `trust_safety ∈ (0, 1]` (default 0.5). `SCHEMA` goes to 2.
  `verify_run` requires schema 2. Older runs cannot re-verify at HEAD in
  any case, because `source_identity` changed.
- **The limit.** c* is computed from the seed group's actual
  `cfg.seed_lr` and `cfg.momentum`.
- **ScaleAwareSlot(Slot)** overrides `trust_region_loss` for v2. It is
  identical to the kernel `Slot` for v1.
- **Recorded witnesses** (both variants, so v1 is measured too). These are
  additive fields, and `validate_record` requires them:
  - the STE epoch's record carries a constant-width per-step table of
    `kappa_live` (computed with λ, the uncapped value), `lam_t`, `gain` and
    `clamped`;
  - every epoch record carries per-step gain minimum and maximum, and
    `rms_ratio_blend_entry` when blending starts;
  - the birth record carries the realised `rms(δ)/rms(h)` at birth, the
    witness for tau. This also covers `simic-e3803e8200`.
- **Divergence records the stage** (STE, BLENDING, FOSSILIZING or JOINT),
  so a failure that moves to BLENDING is diagnosed, not just counted.

## Validation study (pre-registered as its own PDR before running)

An exploratory engineering acceptance test on fresh exploratory seeds.
Execution profile: **GPU, Academy-exact per SKU** (2× RTX 4060 Ti; GPU
lineage only, never mixed with CPU).

| Cell | Host × seed | Run |
|---|---|---|
| A | `under_normalized` × `norm` | v1 and v2, 24 seeds each, same seeds |
| B | `under_normalized` × `conv_heavy` | v1 and v2, 24 seeds each |
| C | `mild` × `conv_light` | v1 and v2, 24 seeds each (regression guard) |

**Acceptance criteria, declared before running:**

1. **v2 is stable.** Zero non-finite scheduled arms in A and B, out of 48.
   Stated with its rule-of-three bound: 0/48 means a rate below 6.2% at 95%.
   Paired v1-vs-v2 divergence uses McNemar on discordant seeds.
2. **The mechanism, v1 cells.** "Max κ_live > c* during STE" is a
   *necessary* condition for divergence: 100% sensitivity is required (no
   v1 divergence without it). The cumulative amplification
   `Σ_t log ρ(κ_t)` ranks divergence with AUC ≥ 0.9. Sensitivity and
   specificity are reported separately.
3. **A free replay test.** The no-growth and static arms do not depend on
   the variant, so their records must be bitwise-equal between the v1 and
   v2 runs of the same seed.
4. **Regression guard, cell C.** A paired TOST shows the late dev CE of v1
   and v2 equivalent within ±0.05. In cell C, λ_t = λ almost always, so
   this tests that v2 is v1 where v1 is safe.

If criterion 2 fails, the derivation is wrong. Return to diagnosis, and do
not proceed to a graft study.
