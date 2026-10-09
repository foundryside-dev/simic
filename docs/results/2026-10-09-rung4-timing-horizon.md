# Rung 4: timing and horizon on `norm` — result, 2026-10-09

**Pre-registered reading: `lever_found`. Rung 4 is met on timing; the
horizon contrast corroborates it (PDR-0054, PDR-0055).**

On the `under_normalized` host with the `norm` seed, two things change the
graft's outcome:
- **Timing.** Grafting earlier is better. Starting at epoch 0 instead of
  epoch 3 lowers the graft's late dev CE by 0.051 nats, which is beyond the
  0.02 margin. This contrast is robust on every measure checked.
- **Horizon.** The graft closes most of its gap to static when training
  runs 20 epochs instead of 10. The pre-registered contrast is −0.101,
  beyond the 0.05 margin. The mean includes a tail of static runs that
  degrade late, which is a real cost of static at 20 epochs. On the median
  seed the shrinkage is −0.067. Excluding late-degrading runs of either
  arm gives −0.058; both still clear the margin.

**What "earlier is better" means here.** T0 grafts the same module at the
same site as static, from step zero, behind the lifecycle's ramp. So the
best schedule is the one most like static. This result does not support
injecting capacity later in training.

The graft never beat static at 10 epochs. At 20 epochs the graft beats
static on the mean (−0.049, descriptive) because static degrades late on
some seeds. On the median seed they tie.

Fleet health: 4,608 of 4,608 runs were verified, with no replay
mismatches. The graft diverged in 6 of 4,608 runs.

## What ran

| Item | Value |
|---|---|
| Plan | [`rung4-timing-horizon`](../prereg/rung4-timing-horizon.json), sha256 `89be9860…`; [PDR-0055](../product/decisions/0055-rung-4-timing-horizon-plan.md). Three pre-launch reviews, amendments before launch |
| Question and stop | Owner-signed in [PDR-0054](../product/decisions/0054-rung-4-decide-timing-and-horizon.md) |
| Source | Snapshot of `991dcdc` (clean). Analysis module `c101a550…` |
| Units | 768 fresh seeds (8001–8768); six cells × three arms (no growth, static, scheduled graft); lifecycle v2; 4,096 fit / 5,000 dev examples |
| Cells | T0, T1, T2, T3, T5: graft starts before epoch 0, 1, 2, 3, 5, at a 10-epoch horizon. H20: graft at epoch 2, 20-epoch horizon, replaying T2 bitwise over its first 10 epochs |
| Execution | Two GPUs, Academy-exact profile, one process per GPU. The 3-seed dry run on `991dcdc` gated the launch. Fleet ran 2026-10-09 04:34–21:53 local; 4,608 exits clean |
| Analysis | Run once, from the snapshot. 4,608 runs verified; 0 failures |
| Evidence | [`2026-10-09-rung4-timing-horizon/`](2026-10-09-rung4-timing-horizon/): launch records, `timing_report.json`, the dry-run and pilot-3 reports, a per-run table (the analysis inputs, without the per-step clamp witness lists) and a per-epoch table. Full `training.jsonl` files stay in `runs/rung4-timing-horizon/` (240 MB) |

## Confirmatory results

Numbers come from `fleet/timing_report.json`. Co-primary intervals are
98.33% paired t, Bonferroni over three. Negative values favour the first
term.

| Contrast | Mean [98.33% CI] | sd | n | Margin | Classification |
|---|---|---:|---:|---:|---|
| **Timing:** graft T0 − graft T3 | **−0.051 [−0.059, −0.043]** | 0.089 | 767 | 0.02 | beyond floor, favourable |
| **Horizon:** gap(H20) − gap(T2), gap = graft − static | **−0.101 [−0.136, −0.067]** | 0.393 | 751 | 0.05 | beyond floor, favourable |
| **Lever cell T0:** graft − static | +0.019 [+0.008, +0.030] | 0.128 | 764 | 0 | graft does not beat static |

Flatness checks against T2, graft late CE, same intervals and 0.02 margin:

| Cell − T2 | Mean [98.33% CI] | Classification |
|---|---|---|
| T0 | −0.034 [−0.041, −0.026] | beyond floor |
| T1 | −0.018 [−0.024, −0.012] | inconclusive |
| T3 | +0.017 [+0.012, +0.022] | inconclusive |
| T5 | +0.046 [+0.040, +0.051] | beyond floor, adverse |

Per cell, descriptive. Late dev CE means over finite runs; capture
fraction is (graft − no growth) / (static − no growth) with a 95% paired
bootstrap:

| Cell | No growth | Static | Graft | Graft − static [98.33%] | Capture [95%] |
|---|---:|---:|---:|---|---|
| T0 | 1.602 | 1.469 | 1.488 | +0.019 [+0.008, +0.030] | 0.86 [0.80, 0.92] |
| T1 | 1.602 | 1.469 | 1.504 | +0.035 [+0.025, +0.046] | 0.73 [0.69, 0.79] |
| T2 | 1.602 | 1.469 | 1.522 | +0.053 [+0.043, +0.063] | 0.60 [0.56, 0.64] |
| T3 | 1.602 | 1.469 | 1.539 | +0.070 [+0.060, +0.081] | 0.47 [0.43, 0.51] |
| T5 | 1.602 | 1.469 | 1.568 | +0.099 [+0.088, +0.110] | 0.25 [0.22, 0.28] |
| H20 | 1.367 | 1.322 | 1.273 | −0.049 [−0.084, −0.014] | not estimable: the denominator reached ≥ 0 in 119 of 20,000 resamples |

The secondary per-seed timing slope is +0.016 nats per epoch of delay,
95% [+0.015, +0.017], n = 767. T2's capture of 0.60 replicates rung 3's
0.60 on fresh seeds.

Failures, from the report:

| Cell | Graft diverged | Static diverged | No growth diverged |
|---|---:|---:|---:|
| T0 | 1/768 | 3/768 | 0/768 |
| T1, T2, T3, T5 | 0/768 each | 3/768 each | 0/768 |
| H20 | 5/768 | 12/768 | 0/768 |

Static failures counted once per seed and horizon: 15, against a cap of
80. No cell exceeded the graft cap of 24. Replay mismatches: 0. Host arms
replayed bitwise across same-horizon cells, and H20 replayed T2's first 10
epochs on every seed.

**Reading precedence.** No instrument failure, no unstable graft cell,
static credible. Both moved contrasts are favourable, so the reading is
`lever_found`. `static_wins_every_cell` is false only because of H20's
mean (see below).

## Exploratory checks (after the reading; nothing here changes it)

Scripts and outputs are committed in
[`exploratory/`](2026-10-09-rung4-timing-horizon/exploratory/). They read
the archived tables.

**1. Timing is robust.** T0 − T3: mean −0.051, median −0.051, 10%-trimmed
−0.053. T0 is better on 79.5% of seeds.

**2. The horizon contrast is heavy-tailed, and holds on robust measures.**
Intervals are 98.33%: t for means, seed bootstrap for medians and trimmed
means.

| gap(H20) − gap(T2) | Mean | Median | Trimmed 10% | Share < 0 | n |
|---|---|---|---|---:|---:|
| All pairs | −0.101 [−0.136, −0.067] | −0.067 [−0.078, −0.056] | −0.069 [−0.078, −0.060] | 0.77 | 751 |
| Excluding late risers (> 0.1) of either arm | −0.058 [−0.066, −0.051] | −0.057 | −0.058 | 0.78 | 590 |
| Excluding static's late risers only (biased) | −0.039 | −0.052 [−0.062, −0.043] | −0.051 [−0.059, −0.043] | 0.74 | 634 |

- The all-pairs median and trimmed mean clear the 0.05 margin. So does
  the symmetric exclusion.
- Excluding only static's risers conditions on an outcome of one arm, the
  arm whose degradation drives the effect. It is biased toward zero. Even
  so, its median and trimmed mean sit at the margin rather than below it.
- Static's late degradation is a real cost, not noise. Static runs that
  rise late finish at 44.0% dev accuracy, against 55.3% for the rest.
- Pairs lost to divergence (12 static, 5 graft at H20) are dropped by the
  per-contrast policy. Imputing them at the worst rank for the failing
  arm leaves the median at −0.068 and the share below zero at 0.77. So
  dropping is conservative for the horizon contrast.

**3. At 20 epochs, the graft catches static up; it does not beat it.**

| At H20 | Mean | Median | Share < 0 |
|---|---:|---:|---:|
| graft − no growth | −0.093 | −0.109 | 0.94 |
| static − no growth | −0.045 | −0.110 | 0.77 |
| graft − static | −0.049 | +0.005 [−0.003, +0.016] | 0.47 |
| graft − static, excluding static late risers | +0.010 | +0.018 | 0.40 |

On the median seed, graft and static gain the same over no growth. The
pre-registered per-cell output, graft − static at H20, is −0.049
[−0.084, −0.014] and classifies as favourable. That is descriptive, not a
co-primary, and it comes from static degrading late on some seeds.

**4. Static degrades late at 20 epochs more often than the other arms.**
Runs whose mean dev CE over the last three epochs sits more than 0.1
above their earlier minimum:

| Arm | Late rise > 0.1 | Diverged |
|---|---:|---:|
| No growth | 47/768 | 0 |
| Graft | 56/763 | 5 |
| Static | 117/756 | 12 |

Static's mean dev CE pulls away from its median from about epoch 11
(epoch 19: mean 1.313, median 1.226). The `norm` gain witness is only
slightly higher on the rising static runs: median peak 1.11 against 1.07.
So this is not obviously the gain explosion of `simic-9c5c3a2acf`. It is
a late-horizon static instability that needs diagnosis, and it is logged
on that issue as new evidence.

**5. Per-seed timing preference: real structure, unknown headroom.**
Runs are deterministic, so there is no replicate noise. The analysis fits
a shared timing curve plus a per-seed linear slope. Its residual is the
non-linear part of the seed × timing interaction.

| | Value |
|---|---:|
| Mean slope | +0.016 per epoch of delay |
| Per-seed slope sd, observed | 0.0166 |
| Slope sd implied by a uniform spread of the interaction | 0.0127 |
| Variance ratio, seed bootstrap 95% | 1.69 [1.42, 1.99] |
| Implied extra slope sd, seed bootstrap 95% | [0.008, 0.013] |
| Interaction sd per cell, total | 0.047 |
| Best-of-5 per seed over always-T0, mean (median) | 0.026 (0.000) |
| corr(T0 − T1, T2 − T3) | 0.09 |
| corr(T0 − T1, T3 − T5) | −0.05 |

- Seeds' linear timing slopes vary more than a uniform spread predicts.
  The slopes are heavy-tailed (excess kurtosis 11), so the parametric F
  p-value is not valid; the bootstrap interval is.
- Most of the interaction is non-linear and weakly consistent across
  cells. A per-seed oracle beats always-T0 by between about 0 and 0.026
  nats. The upper end is inflated by the winner's curse.
- What a controller could realise is untested. It would need a
  held-out-seed test using only pre-decision telemetry, and a T0 decision
  sees only the initialisation.
- The lowest-CE cell per seed was T0 for 53%, T1 27%, T2 12%, T3 7% and
  T5 2%. These shares are inflated by the winner's curse.

**6. Accuracy, descriptive.** Late dev accuracy means:

| Cell | No growth | Static | Graft |
|---|---:|---:|---:|
| T0 | 41.0% | 46.6% | 45.8% |
| T2 | 41.0% | 46.6% | 44.3% |
| T5 | 41.0% | 46.6% | 42.2% |
| H20 | 51.6% | 53.5% | 54.9% |

## Disclosures

- **The horizon sd broke its sizing assumption.** PDR-0055 sized the
  horizon contrast at the pilot-3 upper confidence limit, sd 0.230. The
  observed sd is 0.393, 1.7 times that. Timing came in at 0.089, inside
  its 0.105 limit. The pilot had seen the cause: 7 of 24 pilot-3 static
  runs at H20 also rose late. But 24 seeds underestimated a heavy-tailed
  spread. The contrast classified because the effect matched the
  sizing grid's "gap shrinks 0.10" world. At the observed sd, power there
  was about 0.86, not 1.0.
- **Lesson.** When an arm shows late instability in a pilot, size from a
  tail-aware spread or a robust contrast, not the sd's upper limit.
- **The H20 capture fraction is withheld** by the pre-registered guard.
  The point estimate of 2.13 is not meaningful: static's gain over no
  growth is small on the mean because of its late degradation.
- **The exploratory checks were chosen after seeing the report.** They
  qualify the interpretation only. The reading is the pre-registered one.

## What the reading says, and does not say

- **Rung 4 is met, carried by timing.** Under the reading rule, one
  favourable beyond-floor contrast is enough. Timing is robust on every
  measure. Horizon corroborates it: it holds on the all-pairs median and
  under symmetric exclusion, and its mean includes static's late
  degradation.
- **The best fixed schedule here is "graft immediately."** Each epoch of
  delay costs about 0.016 nats. Even at T0 the graft trails static by
  0.019 at 10 epochs.
- **Earlier means more like static.** T0 is the same module at the same
  site from step zero, behind the lifecycle's ramp. This result favours
  static-like schedules. It does not show that late injection pays.
- **Longer training lets the graft catch up.** At 20 epochs, graft and
  static gain the same over no growth on the median seed. On the mean the
  graft is ahead, because static degrades late on some seeds.
- **It does not show the graft improving on static for the typical
  seed.**
- **The timing headroom for a per-seed controller is unknown and may be
  small.** The oracle bound is between about 0 and 0.026 nats over
  always-T0. Whether telemetry can realise any of it is untested.
- **Consequence under PDR-0055.** `lever_found` means rung 4 is met. What
  follows is a new owner-signed DECIDE.
