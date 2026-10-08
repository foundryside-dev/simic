# Positive control v2 — result, 2026-10-08

**Pre-registered reading: `control_fails_below_floor`.**

On the `under_normalized` host, static `norm`-seed capacity beats no growth
in late-epoch development CE by **0.119 nats**, 95% interval
[0.088, 0.151]. That is a real deficit: the interval excludes zero, and
static helped in 89% of units. It falls short of the pre-registered floor of
δ_pc = 0.10, because the interval's upper end is −0.088.

The plan states that this reading is **not a failed replication**: it means
"a detected deficit under the floor". Its consequence is that a new PDR
decides between a longer horizon or budget and stopping. That decision is
[PDR-0049](../product/decisions/0049-deficit-detected-below-floor-rung-two.md),
status **proposed**, awaiting the owner.

## What ran

| Item | Value |
|---|---|
| Plan | [`positive-control-v2`](../prereg/positive-control-v2.json) (PDR-0048), amended once pre-launch after review |
| Source | `main` at `e398a1e`, clean tree. Analysis module pinned at `8f7516a4…` |
| Units | seeds 2101–2148 (fresh); `under_normalized` + `norm`; 4,096 fit / 5,000 dev; 10 epochs |
| Execution | 48/48 launcher exits clean; 4.5 CPU-hours (sum of unit wall times) |
| Analysis | Run once, after the finish gate. 47 units analysable. 1 failed under `diverged_arm_policy: fail_unit`: seed 2142's **static** (contrast) arm diverged. |
| Sealed | The scheduled arm's values and statuses were not extracted or reported |

## Result

Numbers come from `screen_report.json`.

| Quantity | Value |
|---|---|
| Static − no growth (late dev CE, epochs 7–9) | **−0.1194** |
| 95% t interval / bootstrap | [−0.1507, −0.0881] / [−0.1486, −0.0880] |
| sd over units / half-width | 0.107 / 0.031 (precise: half-width ≤ δ_pc) |
| Units where static helped | 89% |
| Worst decile | −0.002 |
| MDE vs zero / true effect needed for an 80% pass | 0.045 / 0.145 |
| Arm late-CE means | no growth 1.600, static 1.481 |
| Cost (mean optimizer parameter-steps) | no growth 206.09 M, static 206.26 M (+0.08%) |

Per-epoch development CE (mean over units):

| Epoch | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| No growth | 2.105 | 1.988 | 1.895 | 1.858 | 1.813 | 1.746 | 1.710 | 1.651 | 1.585 | 1.565 |
| Static | 2.099 | 1.920 | 1.817 | 1.743 | 1.678 | 1.609 | 1.576 | 1.518 | 1.484 | 1.441 |

Both arms are still descending at epoch 9. The gap has been roughly
stable since epoch 4 (0.10–0.14 per epoch). A longer horizon would
therefore lower both curves, but there is no sign it would push the gap
past the floor.

## Against the plan's predictions

The plan pre-recorded simulated reading probabilities. At the observed
spread (sd 0.107) and the design effect of 0.148, `control_fails_below_floor`
had a 9–21% chance, rising to 34–48% if the true benefit was about 0.134. The
observed effect, 0.119, sits below v1's survivor-subset value. This
reading was one of the plan's named plausible outcomes. The plan's
"would surprise" list (no effect, static worse, instrument failure) did not
occur.

**Shrinkage from the exploratory estimate.** v1's all-unit exploratory
estimate was −0.159. The confirmatory estimate is −0.119, a difference of
0.040 (z ≈ 1.9 on the two standard errors). Selection predicts this: the
configuration was the best of 4 in the probe, and v1's estimate was seen
before v2 was planned. PDR-0046 predicted the shrinkage but did not
quantify it.

## The one new failure

Seed 2142's static arm sat at chance for epochs 0–1 (dev CE 2.309 and
2.307, about ln 10), then diverged at epoch 2, step 18, with a non-finite
training objective. Its gain at birth (0.043) was normal. This is the first
static-arm failure in 96 across v1 and v2. It is consistent with the kernel
sweep's finding that the `under_normalized` host sits near its
learning-rate edge, and it is recorded on `simic-75be93e372`.

Excluding one unit (2%) under the declared policy is a disclosed
post-treatment exclusion. The direction of any bias is unknown and its size
is small.

## Evidence

[`2026-10-08-positive-control-v2/`](2026-10-08-positive-control-v2/)
contains:
- `screen_report.json`, byte-identical to the run's;
- `launch.json` and `launch-finished.json`;
- `training.jsonl` and `complete.json` for every unit (all 48 checksums
  verified).

Manifests, checkpoints and the sealed runner stdout stay local in
`runs/positive-control-v2/`.

## Correction (2026-10-08, independent review)

An independent review reproduced the numbers from the archived evidence:
- 0.1194 nats, 95% interval [0.0881, 0.1507];
- 42 of 47 finite pairs benefiting;
- checksums matching.

It corrected three claims, adopted here:

- **"Below the floor" is about what was established, not the estimate.**
  The point estimate, 0.119, *exceeds* δ_pc = 0.10. What the experiment did
  not do is establish a benefit of at least 0.10: the interval's lower end
  is 0.088. The reading `control_fails_below_floor` stands as frozen. Read it
  as "a benefit ≥ 0.10 not established", never as "the benefit is below
  0.10".
- **More seeds would narrow the uncertainty.** The earlier statement that
  "re-measuring will not change the deficit" overstated things. Prioritising
  the lifecycle fix over more positive-control units is a choice about
  effort, not a claim that more data is uninformative.
- **The v1 → v2 shrinkage is consistent with selection, not proven to come
  from it.** v1's −0.159 used reconstructed controls from all 48 units, not
  only the graft survivors.
- **The benefit is conditional on the 47 finite control pairs.** Seed 2142's
  excluded static failure is disclosed. It is a separate mechanism (the
  static arm bypasses the graft's trust penalty), so lifecycle v2 does not
  address it.
