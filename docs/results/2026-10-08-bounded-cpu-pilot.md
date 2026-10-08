# Bounded comparison — CPU development pilot, 2026-10-08

**Answer to the predeclared question:** yes. With eight times the training data
of the October 4 smoke, all three arms reduced development cross-entropy (CE)
by the end of the fixed ten-epoch horizon. The smoke's failure (accuracy up,
CE worse) did not persist.

**What it does not show:** that growth helps. On one paired seed, static extra
capacity finished with the lowest development CE and the scheduled graft with
the highest. All three final values lie within the noise of a single epoch,
which swings by up to 0.47 CE in each arm after epoch 4. There is no
superiority claim. Outer (test) data was not opened.

## Run identity

| Item | Value |
|---|---|
| Authority | [ADR-0018](../adr/0018-bounded-structural-comparison.md); budget approved by John 2026-10-04; cap lifted 2026-10-08 ([PDR-0041](../product/decisions/0041-pilot-cap-lifted-first-cifar-reading.md)) |
| Source | commit `4186a9c` (clean tree; the runner and its data module are identical to `c40972d`) |
| Host | `nyx`, CPU only, one compute thread, CUDA hidden, Python 3.14.3, torch 2.13.0 |
| Data | Local CIFAR-10 training files only, through a directory that contains no `test_batch`; 1,024 fit and 256 disjoint development examples; data seed 20261004 |
| Arms | No growth; static `conv_light` capacity from step zero; scheduled graft germinated before epoch 2, stages K1/M2/F1 |
| Training | Seed 7, ten epochs, batch 32, 320 optimizer steps per arm; no tuning, retry or checkpoint selection |
| Resources | 59 s wall time for all three arms, from the shell's `time`; the arms' own recorded `wall_s` sums to 57.1 s. 1.9 MB total output, including checkpoints: 47.8 KB without them. The withdrawn 64 MiB cap would not have bound |

Command, from the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
PYTHONPATH=.:src .venv/bin/python -B -m experiments.bounded_comparison train \
  --data cifar --data-root runs/cifar-fit-only --output runs/bounded-pilot-2026-10-08 \
  --seed 7 --data-seed 20261004 --train-size 1024 --dev-size 256 --epochs 10 \
  --batch-size 32 --graft-epoch 2 --stage-k 1 --stage-m 2 --stage-f 1 --threads 1
```

## Results

Development set: 256 examples. Every arm starts from the same untrained host,
at CE 2.3064 and 7.4% accuracy.

| Arm | Final dev CE | Final dev accuracy | CE decreased? | Parameters | Optimizer parameter-steps | Wall time |
|---|---:|---:|:---:|---:|---:|---:|
| No growth | 1.6913 | 40.6% | yes | 142,006 | 45.44 M | 18.6 s |
| Static capacity | **1.6048** | **41.0%** | yes | 150,903 | 48.29 M | 19.3 s |
| Scheduled graft | 1.7223 | 39.8% | yes | 150,903 | 47.72 M | 19.2 s |

Development CE by epoch:

| Epoch | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| No growth | 2.785 | 1.920 | 1.986 | 1.867 | 1.672 | 1.628 | 1.926 | 1.456 | 1.565 | 1.691 |
| Static | 4.487 | 2.053 | 1.808 | 1.957 | 1.732 | 1.609 | 1.764 | 1.599 | 1.615 | 1.605 |
| Scheduled | 2.785 | 1.920 | 1.986 | 1.857 | 1.673 | 1.628 | 1.903 | 1.451 | 1.605 | 1.722 |

## What the run verifies about the instrument

- **Pairing holds.** Through the end of epoch 2, the scheduled arm's host
  parameter hashes match the no-growth arm's exactly. Epoch 2 is the graft's
  first epoch, when the seed trains invisibly with alpha = 0. So germination
  and the invisible training stage leave the host's trajectory untouched until
  blending starts in epoch 3.
- **The lifecycle executed.** The seed body and gain changed in both
  added-capacity arms. The scheduled arm ran 128 fully coupled optimizer steps
  and the static arm ran 320.
- **Costs are not equal.** Static capacity used 6.3% more optimizer
  parameter-steps than no growth, and the scheduled graft used 5.0% more. Any
  later comparison has to price this difference rather than ignore it.

## Reading against ADR-0018

ADR-0018 says to reopen the design "if the static control wins at the declared
cost, or if measurement uncertainty prevents a credible comparison". This run
points toward the first condition but cannot establish it. The static arm won
on one seed and at a higher cost, and the arms differ by less than one epoch's
swing. The second condition is what binds here: one trajectory cannot separate
these arms. The synthetic acceptance fixture also ranked static capacity first.
That makes two readings in the same direction, neither of them evidence.

The next question is therefore how wide the run-to-run spread is, not which
controller to build. Answering it needs a predeclared multi-seed development
screen, which ADR-0018 requires to be proposed with a budget before it runs.
That proposal is tracked as `simic-7486bc6929`.

## Evidence

- Archived in this repository:
  [`2026-10-08-bounded-cpu-pilot/`](2026-10-08-bounded-cpu-pilot/) contains
  `manifest.json`, `training.jsonl` and `complete.json`. The first two match
  the SHA256 checksums recorded in `complete.json`. `complete.json` itself
  has SHA256 `2e23014c…a9fdfd2`.
- Kept on `nyx` only, under `runs/bounded-pilot-2026-10-08/`: the three
  inference checkpoints. They are omitted from git by `.gitignore`, and
  `complete.json` pins their checksums.
- **This run can no longer be passed to `evaluate`.** Removing the Weft marker
  dependency changed the runner's source after the run
  ([PDR-0042](../product/decisions/0042-retire-unavailable-weft-tools.md)), and
  evaluation refuses runs whose recorded source has drifted. This loses
  nothing that was authorized: the pilot was development-only, and evaluating
  on outer data was never approved for it.
