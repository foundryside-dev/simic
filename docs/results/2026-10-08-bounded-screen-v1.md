# Bounded multi-seed screen v1 — result, 2026-10-08

**Pre-registered reading: `reopen_no_value`.**

- **The paired instrument resolves at bounded scale.** On the matched no-op
  contrast it bounds differences to ±0.018 nats, well inside the declared
  0.05-nat floor.
- **The scheduled graft earns nothing measurable at this scale.** It is
  equivalent to no growth, and equivalent to static capacity, within the
  floor.
- **ADR-0018's reopen trigger does not fire.** Static capacity does not win,
  and both comparisons are precise.

Under the frozen plan, this means:

- the lifecycle design reopens: it does not earn its cost here;
- Phase A may resume, because the instrument itself resolves (PDR-0043).

Decision record: [PDR-0045](../product/decisions/0045-bounded-screen-reading-gate-closed.md).

## What ran

| Item | Value |
|---|---|
| Plan | [`docs/prereg/bounded-screen-v1.json`](../prereg/bounded-screen-v1.json), [PDR-0044](../product/decisions/0044-bounded-screen-preregistered.md); amended once before launch (gate scoped to the no-op contrast) |
| Source | commit `f5aeda2`, clean tree, recorded in `launch.json` |
| Units | 48 training seeds (1001–1048). Each seed is one unit; its three arms share initialization, seed body and every minibatch |
| Data | CIFAR-10 training files only, read through a view with no `test_batch`. 4,096 fit and 5,000 development examples; one fixed data sample (data seed 20261004) |
| Training | 10 epochs, batch 32, graft before epoch 2, stages K1/M2/F1, CPU, one thread per unit |
| Execution | 8 parallel workers, 366–435 s per unit, ~48 min wall time, **5.2 CPU-hours measured** (the plan estimated 4.7). 48/48 completed, 0 failures, no re-runs |
| Analysis | Run once, at 97.5% confidence per co-primary contrast (Bonferroni, family α = 0.05). Every unit passed the runner's `verify_run` |

## Results

Endpoint: mean development CE over epochs 7–9, per arm per unit. Means
across units: no growth **1.2970**, scheduled graft **1.2986**, static
capacity **1.3149**.

| Contrast (negative favours the first arm) | Role | Mean | sd over units | 97.5% t interval | Bootstrap | Verdict |
|---|---|---:|---:|---|---|---|
| Scheduled − no growth | co-primary | +0.0016 | 0.054 | [−0.0166, +0.0198] | [−0.0164, +0.0188] | equivalent within floor |
| Scheduled − static | co-primary | −0.0163 | 0.087 | [−0.0454, +0.0129] | [−0.0441, +0.0113] | equivalent within floor |
| Static − no growth | descriptive | +0.0179 | 0.095 | [−0.0140, +0.0498] | [−0.0128, +0.0481] | (descriptive) |

| Contrast | Units favouring first arm | Worst decile | MDE at 80% power | Wilcoxon p (descriptive) |
|---|---:|---:|---:|---:|
| Scheduled − no growth | 21 / 48 | +0.060 | 0.025 | 0.57 |
| Scheduled − static | 26 / 48 | +0.066 | 0.040 | 0.23 |
| Static − no growth | 21 / 48 | +0.123 | 0.044 | 0.18 |

**Cost** (means per unit):

| Arm | Optimizer parameter-steps | Wall time | Final dev CE | Final dev accuracy |
|---|---:|---:|---:|---:|
| No growth | 181.8 M | 125.7 s | 1.332 | 55.0% |
| Scheduled graft | 190.9 M (+5.0%) | 129.7 s | 1.345 | 54.6% |
| Static capacity | 193.2 M (+6.3%) | 132.6 s | 1.297 | 55.7% |

Development CE fell in every arm of every unit. The final-epoch figures are
descriptive. The endpoint is the late-epoch mean, declared in advance.

The final epoch alone ranks static capacity *best* (1.297), while the
pre-registered late-epoch mean ranks it *worst* (1.315). The per-epoch means
across units for epochs 7, 8 and 9 show why:

| Arm | Epoch 7 | Epoch 8 | Epoch 9 |
|---|---:|---:|---:|
| No growth | 1.306 | 1.253 | 1.332 |
| Scheduled graft | 1.296 | 1.254 | 1.345 |
| Static capacity | 1.331 | 1.316 | 1.297 |

No growth and the graft both rise at epoch 9, while static falls. A
final-epoch endpoint would have picked up that one-epoch swing, which is
exactly the horizon degree of freedom the frozen late-epoch mean removes.

## Reading against the frozen rules

| Criterion | Rule | Observed | Met |
|---|---|---|:---:|
| Gate: instrument resolves (PDR-0043) | scheduled − no growth half-width ≤ 0.05 | 0.018 | yes |
| Static comparison credible | scheduled − static half-width ≤ 0.05 | 0.029 | yes |
| ADR-0018 trigger: static wins | scheduled − static lower > 0 | −0.045 | no |
| Progress | scheduled − no growth upper < −0.05 | +0.020 | no |

The only reading consistent with the table is **`reopen_no_value`**. The
graft pays 5% more optimizer work than no growth. The interval rules out a
benefit larger than 0.017 nats, and an equal-sized harm larger than 0.020.

## Exploratory observations (not pre-registered; not claims)

- **Neither added-capacity arm is distinguishable from no growth.** Static
  capacity's interval against no growth also sits inside the floor. A plain
  reading is that this host is not capacity-limited at 4,096 examples and
  ten epochs. If so, *no* growth intervention could show a benefit in this
  configuration, scheduled or not: the experiment had no deficit to repair.
  This is a hypothesis for the redesign, not a result. It fits the Esper
  record, whose clear wins came on degenerate-architecture fixtures with
  large headroom (~10% → ~40%).
- **The static arm is the noisiest:** its per-unit difference against no
  growth ranges from −0.25 to +0.22 nats. Its birth at step zero, with
  freshly calibrated gain, plausibly adds variance. The scheduled arm, born
  into a trained host, does not show this.
- The two single-seed exploratory units disagreed in direction (the pilot
  ranked static first; the timing unit ranked it last). The fleet resolves
  that disagreement as noise around zero.

## Scope

- One host (`mild` CNN), one seed type (`conv_light`), one data sample, CPU,
  development data only.
- Inference covers training randomness. It does not generalise to other data
  subsets, hosts, scales or schedules.
- No outer/test data was opened.
- No superiority or inferiority claim is made in either direction.

## Evidence

- In this repository, under
  [`2026-10-08-bounded-screen-v1/`](2026-10-08-bounded-screen-v1/):
  - `screen_report.json`, the analysis output, published once, with
    per-unit differences;
  - `launch.json` and `launch-finished.json`;
  - for every unit, `complete.json` and `training.jsonl`. All 48 training
    logs match the checksums in their `complete.json`.
- On `nyx` only, under `runs/bounded-screen-v1/`: the per-unit
  `manifest.json` files (data indices) and the 144 inference checkpoints. They
  are pinned by the checksums in each `complete.json`.
