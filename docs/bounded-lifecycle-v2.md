# Bounded graft lifecycle v2 — design

Status: **revised after Fable design review** (2026-10-08); validation
study pre-registered (PDR-0051). Tracker:
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

Plan: [`lifecycle-v2-validation`](prereg/lifecycle-v2-validation.json).
Decision: [PDR-0051](product/decisions/0051-lifecycle-v2-validation.md).
Code: `experiments/lifecycle_validation.py` (`evaluate_criteria`).

An exploratory engineering acceptance test on fresh seeds (4001–4024),
after two 3-seed GPU dry runs (9201–9203).
Execution profile: **GPU, Academy-exact per SKU** (2× RTX 4060 Ti; GPU
lineage only, never mixed with CPU). Both variants of one seed run on the
same GPU, so the replay test never crosses devices. Units train, and the
analysis runs, from one immutable source snapshot.

| Cell | Host × seed | Run |
|---|---|---|
| A | `under_normalized` × `norm` | v1 and v2, 24 seeds each, same seeds |
| B | `under_normalized` × `conv_heavy` | v1 and v2, 24 seeds each |
| C | `mild` × `conv_light` | v1 and v2, 24 seeds each (regression guard) |

**Declared before running.** A scheduled arm that diverges before its seed
is germinated is host instability: until germination, it is the no-growth
host. Such divergences count toward C5, not toward C1 or C2.

Acceptance needs C1–C4. C5 and the performance table are reported but
never decide acceptance. The criteria below were amended before launch,
informed by the pilot and two reviews (PDR-0051).

1. **v2 is stable.** Zero germinated scheduled-arm divergences in A and B,
   out of 48. A and B share one host per seed, so the report gives:
   - the pooled bounds: rule of three 6.25%, exact one-sided 6.05%;
   - per-cell bounds: 0/24 gives 12.5% and 11.7%.

   A per-cell paired McNemar on v1-vs-v2 discordant seeds is reported.
2. **The mechanism, in the stable cells.**
   - *(a) Falsification.* Every v1 divergence whose record carries the STE
     table showed κ_live > c*/1.1 before its diverging step. The 10% is
     the cross-entropy bilinear allowance above; the strict-c* rate is
     reported. This can only falsify, because survivors cross c* too.
   - *(b) Intervention.* At least one seed diverges under v1 but not v2,
     and none the other way. v2 changes nothing else, so this is causal
     evidence.

   With no v1 STE divergence the criterion is untestable, and that is not a
   pass. Reported only: a within-cell AUC of the rectified growth score
   `Σ max(0, log ρ(κ_t))`, and realised gain growth against it. The plain
   sum `Σ log ρ` was rejected because κ ≈ 1/lr makes the map nearly
   nilpotent (log ρ ≈ −18) and swamps it.
3. **A free replay test.** The no-growth and static arms do not depend on
   the variant, and no growth does not depend on the seed type. Their
   records (wall time excepted) must hash identically between the v1 and
   v2 runs of a seed, and no growth must hash identically across the cells
   that share a host.
4. **Regression guard, cell C.** Two parts:
   - failure rate: no seed may diverge under v2 and not under v1;
   - finite performance: on the seeds where both finished, a paired TOST
     must show the scheduled arm's late dev CE equivalent within ±0.05 at
     α = 0.05.

   The verdict separates `inconclusive` (the 90% CI contains 0 but exceeds
   the margin) from `different` (the CI excludes 0). The clamp-engagement
   count shows whether the pass is trivial.
5. **Host instability (reported).** Per cell:
   - no-growth and static divergences;
   - pre-germination scheduled divergences;
   - lifecycle divergences coinciding with a host-arm divergence of the
     same seed.

   This is the class of positive-control-v2's seed-2142 static divergence.
   It is a separate problem and is not patched here.

**Failure rate and finite performance are reported apart.** For every
cell × variant × arm, the report gives:
- the divergence count, with exact bounds;
- the late dev CE over the units that finished, with its own n.

Paired contrasts use finite pairs only, and the excluded pairs are counted.
A survivor mean is never presented as an arm's performance.

If criterion 2(a) fails, the derivation is wrong for the listed units.
Return to diagnosis, and do not proceed to a graft study.
