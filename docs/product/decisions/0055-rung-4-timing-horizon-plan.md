# PDR-0055 — Rung 4 per-study plan: timing and horizon on `norm`, 384 seeds

Date: 2026-10-09   Status: proposed (pending pre-launch review)   Author: Claude (session 17)
Owner sign-off: the question and stop condition are owner-signed in
PDR-0054. This per-study plan is Claude's under PDR-0053, and the owner was
sketched the design in session and answered "Proceed as sketched". On
2026-10-09 the owner said *"you don't need to ask for permission to run a
job/batch"* and *"go ahead, proceed autonomously"*. The size grew from the
sketch's guess (~64 seeds, ~1.5 GPU-hours) to 384 seeds, about 8 h on two
GPUs. That trade-off was brought to the owner, who chose "bigger pilot,
then size".
Related: PDR-0050, PDR-0052 (rung 3), PDR-0053 (gate split), PDR-0054 (rung
4 DECIDE); plan [`rung4-timing-horizon`](../../prereg/rung4-timing-horizon.json);
`experiments/timing_study.py`; `simic-9c5c3a2acf`

## The design

**Cells.** All on `under_normalized` × `norm` with lifecycle v2, 384 fresh
seeds (8001–8384), on the GPU profile. Every cell of a seed runs on one
GPU from one snapshot.

| Cell | Graft germinates before epoch | Horizon (epochs) |
|---|---:|---:|
| T0 | 0 | 10 |
| T1 | 1 | 10 |
| T2 | 2 | 10 |
| T3 | 3 | 10 |
| T5 | 5 | 10 |
| H20 | 2 | 20 |

**Endpoint.** Dev cross-entropy, as the mean over the last three epochs of
each cell's horizon.

**Co-primaries.** One family, α = 0.05, with Bonferroni over three
(98.33% paired t intervals):
1. **Timing:** graft late CE in T0 minus T5, paired by seed. The per-seed
   slope over the 10-epoch cells is a reported secondary.
2. **Horizon:** (graft − static) in H20 minus (graft − static) in T2,
   paired by seed.
3. **Lever cell T0:** does the graft beat static (interval upper < 0)?

**Classification.** Timing and horizon are each read from their one
interval against δ = 0.05:
- `beyond_floor` (either sign);
- `flat` (inside ±δ);
- `inconclusive` (neither).

**Readings,** in order of precedence:
1. `instrument_failure`: a replay mismatch, a co-primary under three
   pairs, or more than 4 runs failing verification.
2. `graft_unstable`: more than 12 graft divergences in any one cell (of
   384).
3. `static_not_credible`: more than 40 static divergences, counted once
   per seed and horizon (of 768).
4. **`lever_found`:** timing or horizon `beyond_floor`, or the T0 graft
   beats static.
5. **`flat_stop`:** both co-primaries `flat`, and static wins in every
   cell (an intersection, so no correction is needed). **This is the
   owner's stop condition: the ladder stops at rung 4.**
6. `inconclusive`: otherwise. A new decision is needed (more seeds, or a
   longer horizon); this reading does not stop the ladder.

**Failure rates.** Failure rates are reported per cell, apart from finite
performance. Each cell's capture fraction is reported with a guarded
paired bootstrap.

## Sizing (rule 8: simulated through the committed rule)

**Pilots.** Two pilots (seeds 9301–9324, 24 seeds × 6 cells) were read for
spread and stability only:
- graft divergences: 0/144;
- static divergences: 1;
- replay: clean.

Pooled sd:

| Contrast | sd | 95% UCL |
|---|---:|---:|
| Timing | 0.070 | 0.093 |
| Horizon | 0.206 | 0.276 |

The 20-epoch arm is the noisy one.

**Choice of n.** At n = 384 and the UCL sds:
- a flat world reads `flat_stop` with probability 0.93;
- a timing effect of 0.08 reads `lever_found` with probability 1.0;
- a horizon shrink of 0.10 reads `lever_found` with probability 0.99.

At the point sds every row is at least 0.99. The plan's `predictions`
carry the full table.

## Rationale

Rung 3 left two hypotheses confounded at a single timing and horizon:
- **Timing:** grafting earlier captures more.
- **Head start:** static's lead is a head start.

Endpoints T0 and T5 give the timing question its largest, most
interpretable contrast. H20 separates timing from horizon. Using T0 as
the lever cell tests the most favourable timing directly.

The esper-lite archive (researched 2026-10-09) trained 150-epoch episodes
on the full 50k images and never ran a static control. It gives no prior
for this effect size, but suggests that 10 epochs on 4,096 examples may be
short. The H20 arm is a first look at that, and the next rung-level
decision, on horizon and host, is the owner's.

## Reading consequences

- **`lever_found`:** rung 4 is met. Timing and/or horizon is a lever, so
  rung 5 (can telemetry predict the best choice?) has something to predict.
  A new DECIDE PDR shapes rung 5 or a horizon/host rung, and its question is
  owner-signed.
- **`flat_stop`:** the ladder stops at rung 4 (PDR-0054). The write-up is
  a clean negative for the scheduled graft at this scale. Location or a new
  host proceeds only through a new owner decision.
- **`inconclusive`:** the owner decides between more seeds, a longer
  horizon, or stopping.
- **`graft_unstable`:** diagnose the unstable cell (early grafts spend six
  epochs fully coupled). Make no timing claim.
- **`static_not_credible`:** the comparator needs `simic-9c5c3a2acf`
  first.
- **`instrument_failure`:** investigate, and re-run on fresh seeds.

## Reversal trigger

Any change to the plan or `timing_study.py` after launch is an amendment,
and the analysis refuses it.
