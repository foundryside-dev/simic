# Lifecycle v2 validation — result, 2026-10-08

**Pre-registered reading: `accepted`.** All four gating criteria pass.

On the `under_normalized` host, graft lifecycle v1 diverged in its
germination (STE) epoch in:
- 6/24 units with the `norm` seed (cell A);
- 8/24 units with the `conv_heavy` seed (cell B).

Lifecycle v2, the per-step trust-curvature clamp, diverged in **0/48** of the
same seeds, with the same initialisation and the same minibatches. Every v1
divergence crossed the derived stability limit before it blew up. Where v1
was already safe (cell C, `mild` × `conv_light`), the clamp never engaged,
and v2 reproduced v1 exactly.

This is an exploratory engineering acceptance test. It shows that v2 is
stable, and that it is stable for the derived reason. **It does not measure
graft value.** The descriptive performance table below is the input to the
graft-capture plan, not a result about capture.

## What ran

| Item | Value |
|---|---|
| Plan | [`lifecycle-v2-validation`](../prereg/lifecycle-v2-validation.json) ([PDR-0051](../product/decisions/0051-lifecycle-v2-validation.md)), amended pre-launch after three dry runs and two reviews (pilot-informed, disclosed) |
| Source | Snapshot of `64b5392` (clean). Plan `b8b79e3b…`, analysis module `4d8ede3c…`, both pinned at launch |
| Units | 3 cells × 24 seeds (4001–4024) × {v1, v2} = 144 runs; 4,096 fit / 5,000 dev; 10 epochs |
| Execution | GPU, Academy-exact per SKU, 2× RTX 4060 Ti. Both variants of a seed on one GPU. 144/144 exits clean; 30.9 min wall (1.02 GPU-hours) |
| Analysis | Run once, from the snapshot, after the finish gate. 144/144 units verified; 0 failures |
| Evidence | [`2026-10-08-lifecycle-v2-validation/`](2026-10-08-lifecycle-v2-validation/): launch records, `lifecycle_report.json`, and every unit's `training.jsonl` and `complete.json` |

## Criteria

Numbers come from `lifecycle_report.json`.

| Criterion | Result |
|---|---|
| **C1** v2 stable (A+B) | **Pass.** 0/48 lifecycle divergences. Pooled bounds: rule of three 6.25%, exact one-sided 95% 6.05%. Per cell: 0/24 each, exact one-sided 11.7%. |
| **C2a** falsification | **Pass.** 14/14 v1 STE-epoch divergences showed κ_live > c*/1.1 = 24.68 before the diverging step. The strict c* = 27.14 also held for 14/14. Specificity was 5/34 (0.147): most survivors crossed the limit too, as predicted. |
| **C2b** intervention | **Pass.** 14 seeds diverged under v1 and not v2; none the other way. Per cell: A 6/0 (McNemar p = 0.031), B 8/0 (p = 0.0078); pooled p = 1.2×10⁻⁴. |
| **C3** replay | **Pass.** Host-arm records were bitwise identical across variants on 72/72 seed pairs, and no-growth was bitwise identical across cells A and B. |
| **C4** regression guard (C) | **Pass**, verdict `equivalent`. No v2-only divergence. v2 − v1 late CE was exactly 0 on 24/24 pairs, because the clamp engaged in 0 units, so this pass is trivial. |

**Reported, not gated:**
- **Ranking.** The within-cell AUC of the rectified growth score
  `Σ max(0, log ρ(κ_t))` was **1.0** over 236 positive–negative pairs. The
  realised gain growth tracked the predicted growth (Spearman ρ = 0.91,
  n = 48).
- **The pattern.** Divergers and survivors both crossed c*. Accumulated
  growth above the limit separated them completely.
- **Co-divergence.** Six seeds diverged under v1 in both A and B (4001,
  4002, 4004, 4005, 4007, 4023). A and B share one host per seed.
- **How often the clamp engaged under v2:**

  | Cell | Units clamped | Mean clamped steps (of 128) |
  |---|---:|---:|
  | A | 24/24 | 53.9 |
  | B | 24/24 | 103.8 |
  | C | 0/24 | 0 |

## Host instability (C5, a separate problem)

The no-growth arm never diverged. One static arm diverged: cell A,
seed 4004, at epoch 1, step 41, in joint training at full blend. Its seed
gain reached 281 within the epoch, then −7×10¹³ at that step. The record is bitwise
identical under v1 and v2, as it must be, because static does not use the
lifecycle. The same seed's v1 graft also diverged, so the report flags it
as host-coincident.

The static `conv_heavy` arm (cell B) did not diverge on that seed. This is
the class of positive-control-v2's seed 2142, now 2/72 static `norm` arms
on this host. It is a gain explosion in an arm with **no trust term at
all**: under full blend, the only curvature on the gain is cross-entropy's.
v2 does not address it. Any graft-capture plan on this host must declare
how it treats this class (`simic-9c5c3a2acf`).

## Finite performance and failure rate (descriptive)

Late dev CE (epochs 7–9). Intervals are 95% paired t over finite pairs,
uncorrected and exploratory. Negative values favour the first arm.

| Cell | Variant | Graft diverged | graft − no growth | static − no growth | graft − static |
|---|---|---:|---|---|---|
| A | v1 | 6/24 | −0.092 [−0.112, −0.073] (18 pairs) | −0.154 [−0.203, −0.104] (23) | +0.034 [−0.009, +0.076] (18) |
| A | v2 | **0/24** | −0.068 [−0.093, −0.043] (24) | −0.154 [−0.203, −0.104] (23) | +0.086 [+0.032, +0.139] (23) |
| B | v1 | 8/24 | −0.032 [−0.064, +0.000] (16) | −0.142 [−0.186, −0.098] (24) | +0.098 [+0.050, +0.147] (16) |
| B | v2 | **0/24** | −0.054 [−0.081, −0.027] (24) | −0.142 [−0.186, −0.098] (24) | +0.088 [+0.050, +0.126] (24) |
| C | v1 = v2 | 0/24 | +0.029 [+0.003, +0.054] (24) | +0.009 [−0.029, +0.046] (24) | +0.020 [−0.021, +0.061] (24) |

What the table says, and does not say:

- **v2 survives where v1 did not, and still helps.** Under v2 the graft
  beats no growth in both cells, by 0.068 (A) and 0.054 (B), over all 24
  units. These are full-sample estimates, not survivor means.
- **It recovers about 40% of what static capacity recovers.** The graft's
  gain over no growth is 0.068/0.154 = 44% of static's in A and
  0.054/0.142 = 38% in B. Static beats the v2 graft by 0.086 (A) and
  0.088 (B). In graft-capture-v1's vocabulary
  this is *partial capture*, but here it is a descriptive observation,
  not a reading.
- **v1's survivor contrasts are selected.** The seeds that diverged carried
  the larger deficits:

  | Cell | Static − no growth, seeds that diverged | Seeds that survived |
  |---|---|---|
  | A | −0.253 [−0.435, −0.071] (n = 5) | −0.126 [−0.171, −0.081] (n = 18) |
  | B | −0.167 [−0.258, −0.075] (n = 8) | −0.130 [−0.185, −0.075] (n = 16) |

  This is PDR-0047's survivor pattern. v1's −0.092 in A must not be compared
  with v2's −0.068 as "v2 is worse".
- **Cell C.** In cell C the graft was slightly *worse* than no growth
  (+0.029 [+0.003, +0.054]), identically under both variants. The interval
  is uncorrected and exploratory. It differs in seeds from screen v1, which
  found the graft equivalent to no growth on this configuration (+0.002).
  Do not read it as a finding.

## Consequences (PDR-0051)

- **accepted** → the next plan is graft-capture v2 (rung 3), on lifecycle
  v2, covering `norm` and `conv_heavy`. It must declare:
  - its treatment of static-arm host instability (2/72 on this host with
    `norm`);
  - its analysis of graft value as a full-sample contrast, with failure
    rate reported apart.

  The descriptive gap above (the graft recovers about 40% of static's gain) is the prior that
  plan sizes against. It is not a result.
- The parked kernel demo (`under_normalized` × `norm`) still uses v1 and
  remains exposed to the defect.

## Disclosures

- The plan was amended before launch, informed by three 3-seed dry runs
  (seeds 9201–9206, archived as `2026-10-08-lifecycle-v2-dryrun-1/2/3`) and
  two reviews that read the pilot records (PDR-0051, plan `disclosures`).
- The C4 pass is trivial: the clamp never engaged in cell C. C4 shows that
  v2 is v1 where κ stays below 0.5·c*. It does not show v2 is harmless where
  it engages; the performance table is the evidence there.
- A and B share one host per seed. Their 48 v2 units are 24 host
  trajectories × 2 seed types, so the per-cell bounds are the honest
  per-seed-type claim.
