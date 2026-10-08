# Graft-capture v2 (rung 3) — result, 2026-10-09

**Pre-registered readings: `partial_capture` for both `norm` and
`conv_heavy`. Composed rung-3 verdict (PDR-0052, row 4): partial
capture.**

On the `under_normalized` host, a graft grown mid-training with lifecycle
v2 repairs part of the deficit that static capacity repairs:
- **about 60%** with the `norm` seed;
- **about 31%** with the `conv_heavy` seed.

It beats no growth in both cells. Static capacity present from step zero
beats it in both. Under ADR-0018, this means **static wins at the declared
cost**: a negative on "graft ≥ static" at this horizon, not progress
toward it.

The lifecycle was stable at scale: the graft diverged in **0/192** runs.

## What ran

| Item | Value |
|---|---|
| Plans | [`graft-capture-v2-norm`](../prereg/graft-capture-v2-norm.json), [`graft-capture-v2-conv-heavy`](../prereg/graft-capture-v2-conv-heavy.json) ([PDR-0052](../product/decisions/0052-graft-capture-v2.md)). Three pre-launch Fable reviews, then re-checks; amendments before launch |
| Source | Snapshots of `37e5a5b` (clean). Analysis module `d788cca0…`. Each launch pinned its sibling plan's hash |
| Units | 96 fresh seeds (7001–7096), the same in both plans; lifecycle v2; 4,096 fit / 5,000 dev; 10 epochs |
| Execution | GPU, Academy-exact per SKU, one process per GPU. The final 3-seed dry run on `37e5a5b` gated the launch. Both fleets were launched (17.8 and 21.0 min) before either was analysed. 192/192 exits clean |
| Analysis | Run once per plan, from its snapshot. 96/96 units verified in each; 0 failures |
| Evidence | [`2026-10-09-graft-capture-v2/`](2026-10-09-graft-capture-v2/): launch records, both `screen_report.json`, every unit's `training.jsonl` and `complete.json`, and the dry-run reports |

## Results

Numbers come from each plan's `screen_report.json`. Co-primary intervals
are 98.75% paired t (one family of four co-primaries across both plans).
Negative values favour the first arm.

| | `norm` | `conv_heavy` |
|---|---|---|
| **graft − no growth** (co-primary) | −0.087 [−0.105, −0.069], n = 96, 94% of units: `first_better_beyond_floor` | −0.045 [−0.071, −0.019], n = 96, 69% of units: `first_better_floor_not_cleared` |
| **graft − static** (co-primary) | +0.057 [+0.028, +0.086], n = 95: `first_worse` | +0.098 [+0.074, +0.123], n = 96: `first_worse` |
| static − no growth (descriptive, 95%) | −0.144 [−0.169, −0.118], n = 95 | −0.143 [−0.165, −0.122], n = 96 |
| **Capture fraction** (descriptive, 95% paired bootstrap) | **0.60 [0.51, 0.72]**, n = 95 | **0.31 [0.19, 0.42]**, n = 96 |
| Graft divergences | 0/96 (exact one-sided 95% bound 3.07%) | 0/96 (3.07%) |
| Static divergences | 1/96 (seed 7074) | 0/96 |
| Reading | **`partial_capture`** | **`partial_capture`** |

How robust and selective this is:
- **Sensitivity.** In `norm`, the one lost static pair, imputed at either
  extreme, leaves the reading unchanged (`robust: true`). `conv_heavy` lost
  no pairs.
- **Selection diagnostic.** On the unit that lost static, graft − no
  growth was −0.089, against −0.087 on the other 95. One unit is not
  evidence of selection either way.
- **Replay.** The no-growth arm replayed bitwise across the two plans on
  96/96 seeds.
- **Precision.** Every precision gate passed. The graft − static
  half-widths (0.029 and 0.024) are under δ = 0.05, as sized.

## What the readings say, and do not say

- **Rung 3 is met as a partial capture, and it is seed-type dependent in
  size.** The two capture intervals do not overlap: [0.51, 0.72] against
  [0.19, 0.42]. That comparison is descriptive and was not pre-registered
  as a contrast. Read it as "`norm` captures more", not as a tested
  difference.
- **The `norm` graft clears the old floor.** Its gain over no growth is
  −0.087, and the whole interval lies beyond −δ = −0.05. Static still beats
  it, so the reading is `partial_capture`, not `progress`. That is the
  precedence PDR-0046 F1 chose.
- **Cost separates the seed types.** Mean optimizer parameter-steps
  relative to no growth (206.1 M):

  | Seed | Graft | Static |
  |---|---:|---:|
  | `norm` | +0.06% | +0.08% |
  | `conv_heavy` | +29.9% | +37.4% |

  `norm` captures the larger share for almost no added work.
- **Part of static's advantage may be a head start.** Mean dev CE of
  graft − static by epoch (descriptive; arm means over finished units):

  | Seed | Epoch 6 | Epoch 7 | Epoch 8 | Epoch 9 |
  |---|---:|---:|---:|---:|
  | `norm` | +0.087 | +0.061 | +0.064 | +0.044 |
  | `conv_heavy` | +0.129 | +0.114 | +0.113 | +0.068 |

  The gap is narrowing at the 10-epoch horizon. Whether it closes with a
  longer horizon or an earlier graft is exactly rung 4's question (timing),
  not something this study can answer.
- **Against the predictions.** Both plans predicted `partial_capture` at
  ≥ 0.97. The validation's exploratory capture estimates (0.44 and 0.38)
  lie inside this study's intervals for `conv_heavy` and below its interval
  for `norm`. Replication on 96 fresh seeds moved `norm` up, not down.

## Host instability (`simic-9c5c3a2acf`)

The static `norm` arm diverged once (seed 7074): at epoch 3, step 11, in
joint training, its gain reached about 9,954 and then went to −1.8×10¹⁵.
This is the same class as seeds 2142 and 4004. Across every study on this
host so far:

| Static seed | Divergences | Rate (95% interval) |
|---|---:|---|
| `norm` | 3/168 | 1.8% (0.4%–5.1%) |
| `conv_heavy` | 0/120 | one-sided 95% upper bound 2.5% |

The per-contrast policy kept the graft − no-growth pair for the affected
unit. The static cap (10/96) was nowhere near binding.

## Consequences (PDR-0052)

- **Composed verdict: partial capture** (row 4). The graft repairs part of
  the deficit, and static wins at the declared cost.
- **Next, by the ladder (PDR-0050):** rung 4, whether timing or location
  changes the outcome. PDR-0052 records the next step as a rung-4 DECIDE
  PDR that chooses the apparatus; the default is the bounded runner's
  snapshot fan, not the parked kernel demo. The narrowing gap in the epoch
  table, and the seed-type dependence, are its inputs. Per ADR-0018, the
  response to "static wins" is to reopen the design (timing, location),
  never to enlarge the controller.

## Disclosures

- The validation's descriptive estimates were seen before these plans were
  written. This is a confirmatory replication on fresh seeds. Only the sd
  was borrowed for sizing.
- Three 3-seed dry runs (seeds 9207–9209, on `e63a1e3`, `4c6986c` and
  `37e5a5b`) preceded launch and were read for mechanics only. Their
  reports are archived under `dryruns/`.
- The capture-fraction comparison between seed types, the cost
  comparison and the epoch table are descriptive. Only the four
  co-primaries were pre-registered tests.
