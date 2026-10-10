# Static `norm` arm divergence: diagnosis — 2026-10-11

**Result (exploratory throughout; `simic-9c5c3a2acf`).**

- **It is not a sustained curvature instability on the gain.** The issue's
  hypothesis was that the loss's curvature along the static gain exceeds
  the momentum-SGD limit c* = 27.14.
  - That curvature's median is 0.05–3.7 per run.
  - It exceeds c* on 36 of 9,366 steps in the failed runs and 15 of 10,240
    in the healthy ones.
  - Crossings are isolated: one or two consecutive steps, mostly at a
    gradient spike. 3 of the 5 healthy runs have them too and recover, so a crossing
    doesn't separate failure from recovery.
- **What most failures share.** In 6 of 8 replayed failures:
  - the gain sits just above 1 (1.02–1.45);
  - one gradient spike, +9.8 to +44.5 on the gain, knocks it down by
    0.86–4.2 in a single step;
  - the loss goes non-finite 5–50 steps later.

  Three healthy runs take the same kind of kick and recover. Seeds 7074 and
  8346 fail differently.
- **A gain guard looks helpful, but isn't proven.** Both runs below are
  identical to their records until 14–59 steps before each recorded failure:
  - a 0.1% sham perturbation from that point did not avoid 5 of the 8;
  - of those 5, a cap on the gain's step prevented 2 cleanly, and a third
    only to chance;
  - the cap never failed where the sham survived;
  - that is 3 discordant pairs against 0, exact p = 0.25, or 2 against 0,
    p = 0.5, without the one at chance.
- **Rates:**

  | Horizon | Static | 95% interval | No growth |
  |---|---:|---|---:|
  | 10 epochs | 6/984 (0.61%) | 0.22–1.32% | 0 |
  | 20 epochs | 12/768 (1.56%) | 0.81–2.71% | 0 |

This is diagnostic only. No reading changes, and no Fleet C1 or Fleet C1-S
record was opened. The diagnosis's numbers are in
[`tables.md`](2026-10-11-static-norm-divergence/tables.md), which
[`build_tables.py.txt`](2026-10-11-static-norm-divergence/tools/build_tables.py.txt)
generates from the records and the replays.

## How often it fails

Counted once per static trajectory ([tables §2, §10f, §10g](2026-10-11-static-norm-divergence/tables.md)):

| Host × seed | Horizon | Static diverged | 95% interval | No growth diverged |
|---|---|---:|---|---:|
| `under_normalized` × `norm` | 10 epochs (5 studies) | 6/984 | 0.22–1.32% | 0/984 |
| `under_normalized` × `norm` | 20 epochs (rung 4) | 12/768 | 0.81–2.71% | 0/768 |
| `under_normalized` × `conv_heavy` | 10 epochs | 0/120 | | |

Rung 4's T0–T5 directories share one 10-epoch static run per seed. Its
20-epoch (H20) static run equals the 10-epoch one over epochs 0–9 on all
768 seeds. So the 12/768 includes rung 4's three 10-epoch failures, and 9
are new, all at epoch 13 or later. The tracker's earlier 3/168 predates
rung 4.

## Method

- **Replays:** finished units, replayed from each study's immutable snapshot through that snapshot's own `bounded_comparison.train`, with one arm only:
  - `graft-capture-v2` at `37e5a5b`;
  - `lifecycle-v2-validation` at `64b5392`;
  - rung 4 at `991dcdc`.
- **The probe** runs between backward and the optimiser step, on deep copies with their hooks removed. It never touches the global RNG.
- **Bitwise check:** all 15 replays without an intervention reproduce their records bit for bit: the birth record, every epoch's `training_state_sha256` and dev metrics, and the divergence step and witness ([§1](2026-10-11-static-norm-divergence/tables.md)). So the probe does not disturb training.
- **Per step it records:**
  - the exact second derivative of the loss along the gain;
  - the gain and its gradient;
  - the mean square of the host's features at the slot, `h_ms`;
  - per-block gradient and weight norms;
  - for seed 7074, the network's top Hessian eigenvalue, by power iteration.
- **Which runs:**
  - the 10-epoch failures, every one except seed 2142 (positive-control-v2 has no snapshot);
  - three of rung 4's nine late failures (epoch 13 or later), picked by hand from the list (8229, 8195, 8605);
  - healthy runs: the first seeds of graft-capture-v2-norm (7001, 7002) and of rung 4 (8001–8003);
  - seed 7074's no-growth arm.
- **Tools:** in [`tools/`](2026-10-11-static-norm-divergence/tools/).
  - The replay lists are in the `replays-*.txt` files.
  - Seed 7074 has three replays: the first probe version (`static_probe_v1`), then static and no growth at 20 power-iteration steps.
- **Raw data:** on nyx at `runs/static-norm-diagnosis-2026-10-11`, regenerable from the snapshots.
- **Co-tenancy:** the replays ran niced on GPU 1 while Fleet C1 was using both GPUs.
  - By the clock, the fleet sealed 61 seeds from 02:38 to 04:04, about 168 s per seed per GPU. That comes from its progress line count, read at those two times.
  - Its recorded unit wall times averaged 169 s over the 48 seeds before the replays.
  - The batch script read Fleet C1's progress line count, and nothing else of the fleet's.
  - Co-tenancy does not change records: that was tested for the atlas at G0.

## What the replays show

The norm seed's delta is `g·(GN(h) − h)`, so the static slot outputs
`(1−g)·h + g·GN(h)`. GroupNorm's output scale is set by its own affine,
not by `h`.

1. **The gain settles in one of two basins.** In rung 4's 20-epoch runs:
   - **+ basin**, 681 of 768 runs: the gain is +0.71 over epochs 5–9 and +0.83 at the end;
   - **− basin**, 85 runs: −0.91 over epochs 5–9 and −1.11 at the end
     ([§10h](2026-10-11-static-norm-divergence/tables.md)).
2. **In the + basin replays, the host's features grow.** In the five +
   basin 20-epoch replays, median `h_ms` rises from 0.07–0.12 at epoch 0 to
   6.8–11.6 by epoch 18. In the one − basin replay it rises from 0.13 to
   0.42 ([§7](2026-10-11-static-norm-divergence/tables.md)). `h_ms` is not
   in the original records, so this rests on six replays.
3. **The kick** ([§10b](2026-10-11-static-norm-divergence/tables.md)):
   - Seeds 4004, 8207, 8526, 8229, 8195 and 8605 sit at a gain of 1.02–1.45, where `(1−g)` changes sign.
   - One gradient of +9.8 to +44.5 knocks the gain down by 0.86–4.2 in a single step. The curvature along the gain is 47–2,604 at that step, above c*.
   - The loss goes non-finite 5–50 steps later.
   - Healthy 7001, 8001 and 8003 take the same kind of kick and recover: gain 1.07–1.14, gradient +5.4 to +9.1, step −0.42 to −0.80, curvature 36–121.
   - A large gain step is present in all 8 failures, but healthy runs reach 0.80 against a failed minimum of 0.86. On its own it doesn't separate them.
4. **Seed 7074 is different.** Its static arm sat at chance for epochs 0–2:
   median train CE 2.29, 2.25 and 2.31, against no growth's 2.17, 1.95 and
   1.96 ([§4](2026-10-11-static-norm-divergence/tables.md)).
   - Its `h_ms` was already 1,589–4,679 before step 108 of epoch 2.
   - There, one gradient of −23.7 moved the gain from 0.73 to 3.00. Momentum then carried it to 10.67 over the next 15 steps, while the gradient was about zero ([§10c](2026-10-11-static-norm-divergence/tables.md)).
5. **Seed 8346 is different too.** It is a − basin run. Its failure begins
   with a host spike at epoch 9, step 27 (CE 5.71, stage-3 squared gradient
   3,328), with the gain at −0.90 ([§10i](2026-10-11-static-norm-divergence/tables.md)).
   - The gain then moves to about 0 and the arm sits at chance.
   - A second host spike at steps 43–44 ends it.
   - Its largest gain step comes after that spike ([§5](2026-10-11-static-norm-divergence/tables.md)).

## Interventions (exploratory)

**Late-onset cap against a sham** ([§11](2026-10-11-static-norm-divergence/tables.md)).

- **The onset:** for each failure, the first step within the final 60 at which the gain's step exceeds 0.1. That falls 14–59 steps before the recorded divergence. The 60-step window was set after seeing that the kicks fall 5–50 steps before divergence.
- **From the onset:**
  - one run caps the gain's step at 0.1, with its momentum buffer clipped to match;
  - a sham run scales the gain's step by 0.999.
- Both runs match the uncapped replay exactly on every probed step up to the onset.

| Seed | Sham | Cap | Sham final dev CE | Cap final dev CE | No growth |
|---|---|---|---:|---:|---:|
| 8526 | diverged | completed | – | 1.545 | 1.572 |
| 8346 | diverged | completed | – | 2.317 | 2.028 |
| 8605 | diverged | completed | – | 1.231 | 1.287 |
| 7074 | diverged | diverged later (epoch 8, not 3) | – | – | 1.436 |
| 8207 | diverged | diverged | – | – | 1.806 |
| 4004 | completed | completed | 1.628 | 1.699 | 1.569 |
| 8229 | completed | completed | 1.562 | 1.167 | 1.262 |
| 8195 | completed | completed | 1.207 | 1.162 | 1.471 |

- **Not avoided by a 0.1% perturbation:** 5 of the 8 failures. The other three (4004, 8229, 8195) were avoided by the sham too, so their pairs say nothing either way.
- **Of those five:**
  - the cap prevented 2 cleanly (8526, 8605);
  - it prevented one only to chance: 8346 ends at 2.317, against ln 10 = 2.303;
  - it delayed one (7074) and did not change one (8207).
- **Survival:** the cap never failed where the sham survived. That is 3 discordant pairs against 0, exact two-sided p = 0.25, or 2 against 0, p = 0.5, without 8346.
- **Final dev CE, where both completed:** the cap was worse on 4004 (1.699 against 1.628) and better on 8229 and 8195.
- **The sham is not size-matched.** At 8526's kick, the sham moves the gain by about 0.001 and the cap by about 0.8.
  - So the sham rules out "any tiny perturbation avoids the failure".
  - It cannot separate guarding the gain's step from any large change to the gain at the kick. A size-matched control would.
- **Reading:** suggestive, not established. In 2 or 3 of the 5 failures a small perturbation could not avoid, capping the gain's step did avoid it.

**Early-onset cap.** This was the first test: capped from step 0, it let 7
of 8 failed arms finish ([§9](2026-10-11-static-norm-divergence/tables.md)).
That is not evidence about the cause:

- Each capped run departs from its record 18–2,338 steps before the recorded failure ([§10e](2026-10-11-static-norm-divergence/tables.md)).
- With failure rates of 0.6–1.6%, almost any perturbation that early would avoid the recorded failure.
- Capped from step 0, seed 8207 still fails at epoch 1. Its slot features collapse (`h_ms` 0.0016) and its stage-1 weights grow 2.4-fold while the gain stays near zero ([§10d](2026-10-11-static-norm-divergence/tables.md)). That is one counterfactual run, so it is not evidence of a second route.
- On the two healthy seeds, the early cap's final dev CE was 0.051 worse (7001) and 0.148 better (8001). That is inconclusive.

## Rung 4's late static rise goes with the + basin (exploratory, post hoc)

Rung 4 found static runs rising late at 20 epochs (117/756) and left the
cause open. Split by gain basin, here defined by the median gain over epochs
5–9, a cut chosen after seeing the data ([§8, §10h](2026-10-11-static-norm-divergence/tables.md)):

| Basin | Late rise | Diverged at epoch ≥ 13 |
|---|---:|---:|
| + | 115/672 | 9/681 |
| − | 2/84 | 0/85 |

- **Strength:** one-sided Fisher p = 5×10⁻⁵.
- **Robust to the cut:** basins taken from epochs 2–4 give 115/671 against 2/85; from epochs 10–14, 113/670 against 4/86.
- **Not a seed-level tendency:** on the same seeds, no growth rises late in 42/672 and 5/84 runs, about 6% in both. So the seed itself doesn't carry a tendency to rise.
- **Two cautions:**
  - Static fits better in the + basin: median minimum dev CE 1.168, against 1.446 in the − basin. So the basin is confounded with fit.
  - Risers and non-risers have the same gain until epoch 17 (0.82 and 0.82), and part only at epoch 19 (0.65 and 0.84). The risers' lower final gain goes with the rise, or follows it. Mostly, it does not precede it.

## What this means

- **Readings already made:** nothing changes. Each handled static divergences by its pre-registered policy.
- **Fleet C1:**
  - Its static arm is built and trained the same way: the same kernel host, slot, seed, calibration and optimiser. The atlas training step reproduces the frozen runner's records bit for bit ([golden](2026-10-09-atlas-g0-golden/README.md)), on seeds that did not diverge, so the divergence path is CPU-tested only.
  - Its plan matches the replayed studies on every field the static arm reads: data, data seed, sizes, batch, learning rate, τ and 10 epochs. Only the seeds differ.
  - So 6/984 (0.22–1.32%) is a direct prior for C1's `under_normalized` static rate, against its pre-registered 10% cap per host.
  - C1 is analysed once, as planned.
- **Fleet C1-S:**
  - Its BatchNorm hosts use `conv_heavy`, `attn` and `conv_light`. None of these has a `(1−g)·h` path.
  - Nothing here was tested on a BatchNorm host or on any seed but `norm`.
  - Its control host's corrected arm equals the registered `norm` arm by construction. Its 48-seed pairing check has not run yet.
- **Decision for John at the C1 checkpoint, not taken:**
  - (a) keep the static arm and report this failure class as now, with the rates above;
  - (b) for future studies, a guarded static arm, such as a step cap or trust term on the gain, like lifecycle v2's clamp on the graft. The evidence for it is the suggestive late-onset result above, so it would need its own pre-registered validation;
  - (c) a norm seed whose delta does not cancel `h`: `GN(h)` instead of `GN(h) − h`. That is a new seed type, because kernel_demo's semantics are frozen.
  - Static is the ladder's oracle comparator (ADR-0018), so (b) and (c) change what it measures.
