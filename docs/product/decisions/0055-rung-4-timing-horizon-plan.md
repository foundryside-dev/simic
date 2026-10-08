# PDR-0055 — Rung 4 per-study plan: timing and horizon on `norm`, 768 seeds

Date: 2026-10-09   Status: accepted for launch (after three pre-launch reviews and amendments)   Author: Claude (session 17)
Owner sign-off: the question and stop condition are owner-signed in
PDR-0054. This per-study plan is Claude's under PDR-0053, and a delta note
against the sketch is posted in session before launch.

**Owner touchpoints:**
- the sketch, answered "Proceed as sketched";
- the size trade-off, answered "Bigger pilot, then size";
- the compute direction: *"you don't need to ask for permission to run a
  job/batch"* (PDR-0056);
- *"go ahead, proceed autonomously"*.

Related: PDR-0050, PDR-0052 (rung 3), PDR-0053, PDR-0054, PDR-0056; plan
[`rung4-timing-horizon`](../../prereg/rung4-timing-horizon.json); sizing
script [`rung4-timing-horizon-sizing.py.txt`](../../prereg/rung4-timing-horizon-sizing.py.txt);
`experiments/timing_study.py`; `simic-9c5c3a2acf`

## The sketch shown to the owner, and what changed since

**The sketch.** It covered six cells, `under_normalized` × `norm`,
lifecycle v2, fresh seeds (~64, "sized at review"), GPU:

| Cells | Graft starts before epoch | Horizon (epochs) |
|---|---|---|
| T0, T1, T2, T3, T5 | 0, 1, 2, 3, 5 | 10 |
| H20 | 2 | 20 |

It proposed three comparisons:
1. the timing trend 0→5;
2. the horizon gap, 20 against 10 epochs;
3. whether static still wins in every cell.

Its readings:
- "timing or horizon matters", if an effect is beyond δ = 0.05;
- "flat → stop", if both are within ±0.05 and static wins everywhere;
- "inconclusive → new decision".

Cost: about 1.5 GPU-hours.

**Changes since, all from the reviews and pilots:**

| | Sketch | Now | Why |
|---|---|---|---|
| Seeds | ~64 | **768**, about 16 h on two GPUs | The 20-epoch arm is noisy. Owner: "bigger pilot, then size"; nyx compute needs no permission |
| Timing contrast | trend 0→5 | **T0 − T3**, endpoints. The slope is secondary; T5 enters only the flatness check | T5's late window is in blending (statistics review) |
| Timing margin | 0.05 | **0.02** (about 14% of static's gain) | At 0.05, a real 0.03 effect (~21 capture points) could read "flat" and stop the ladder |
| Horizon margin | 0.05 | 0.05 (about 35% of static's gain) | Unchanged; the arm is noisier |
| "Flat" | the endpoints | **every 10-epoch cell flat against T2**, plus horizon flat, plus static winning everywhere | A mid-range peak must not read as flat (product review) |
| "Matters" | either sign | **Split by sign:** `lever_found` (earlier better, gap shrinks, or T0 beats static) or `changes_adversely` (later better, or gap widens) | An adverse change is not a lever for rung 5 |
| Horizon pairing | as drawn | **H20 continues T2 bitwise for 10 epochs** (runner: `draw_future`) | Augmentations were drawn differently; the pilot correlation was 0.11 |

**What stopping now requires.** Every short-horizon cell's graft late CE
must lie within ±0.02 nats of T2's (98.33% intervals). The 20-epoch gap
must be within ±0.05 of the 10-epoch gap. Static must win in every cell.
This is harder to reach than the sketch's version, in the direction that
protects the owner's stop.

## The design

- **Endpoint:** dev CE, as the mean over the last three epochs of each
  cell's horizon.
- **Co-primaries:** α = 0.05, Bonferroni over three (98.33% paired t):
  1. **timing:** graft T0 − T3;
  2. **horizon:** gap(H20) − gap(T2);
  3. **lever cell T0:** does the graft beat static?
- **Readings**, in order of precedence:
  1. `instrument_failure`: a replay mismatch (host arms across same-horizon
     cells, or H20 against T2's first 10 epochs), any co-primary or
     flatness contrast under three pairs, or more than 8 runs failing
     verification.
  2. `graft_unstable`: more than 24 graft divergences in any one cell of
     768.
  3. `static_not_credible`: more than 80 of 1,536 static seed-horizons
     diverged.
  4. `lever_found`
  5. `changes_adversely`
  6. **`flat_stop`**
  7. `inconclusive`
- **Failure rates** are reported per cell, apart from finite performance.
  Each cell's capture fraction comes with a guarded paired bootstrap.
- **Per-contrast policy:** a seed enters a contrast if and only if both of
  its arms finished. Nothing is re-run.

## Sizing (committed script, through the committed rule)

Pilot 3 was run on the launch runner (seeds 9330–9353, 144 runs), read for
spread and stability only. The earlier pilots predate the prefix-stable
future.
- Spreads:

  | Contrast | sd | 95% UCL |
  |---|---:|---:|
  | Timing (T0 − T3) | 0.079 | 0.105 |
  | Horizon | 0.173 | 0.230 |

- Graft divergences: 2/288 across all pilots.
- H20 replayed T2 bitwise on 24/24 seeds.

Results at n = 768, from `predictions` in the plan:

| World | Reading, at UCL spreads | At point spreads |
|---|---|---|
| Flat | `flat_stop` 0.97 | 1.0 |
| Timing −0.06 | `lever_found` 1.0 | 1.0 |
| Timing −0.03 | `lever_found` 0.585, `inconclusive` 0.415 | `lever_found` 0.855 |
| Mid-range peak at T1 | `inconclusive` 1.0 | 1.0 |
| Horizon −0.10 | `lever_found` 1.0 | 1.0 |
| Horizon −0.05 | `inconclusive` 0.99 | 0.99 |
| Horizon widening +0.10 | `changes_adversely` 1.0 | 1.0 |

A 0.03 timing effect and a mid-range peak never read `flat_stop`.

The caps' operating characteristics, computed, are in the plan's
disclosures.

## Pre-launch order

1. Full suite, then commit.
2. A gating 3-seed dry run on the launch commit, with analysis (seeds
   9354–9356).
3. The delta note to the owner, posted in session.
4. Launch.
5. Record the fleet in `current-state.md` and on `simic-f73351380d`
   (PDR-0056).
6. Analyse once, from the snapshot.

## Reading consequences

- **`lever_found`:** rung 4 is met. Rung 5 (can telemetry predict the best
  choice?) has something to predict. A new owner-signed DECIDE shapes rung 5
  or a horizon/host rung. The esper-lite research (memory, 2026-10-09:
  150-epoch runs on the full data) bears on that choice.
- **`changes_adversely`:** the outcome moves, but the wrong way. Bring it
  to the owner; it is not a lever.
- **`flat_stop`:** the ladder stops at rung 4 (PDR-0054), written up as a
  clean negative for the scheduled graft at this scale.
- **`inconclusive`:** the owner decides between more seeds, a longer
  horizon, or stopping.
- **`graft_unstable`:** diagnose the cell. Make no timing claim.
- **`static_not_credible`:** `simic-9c5c3a2acf` first.
- **`instrument_failure`:** investigate, and re-run on fresh seeds.

## Reversal trigger

Any change to the plan or `timing_study.py` after launch is an amendment,
and the analysis refuses it. An interrupted fleet is resumed with
`--resume` from its own snapshot, never relaunched on new code.
