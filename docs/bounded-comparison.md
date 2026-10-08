# Bounded comparison: one host, one seed, three arms

This runnable experiment tests the training instrument before adding a learned
controller. It reuses the kernel demo's fixed `mild` CNN, residual `conv_light`
seed, SGD, deterministic initialization, common minibatch future and lifecycle.
It does not implement the full Simic authority system, generated topology,
warrants, learned timing or transferable structural taste. The original kernel
demo and its registered campaign remain unchanged. Authority for this new
experiment is recorded in [ADR-0018](adr/0018-bounded-structural-comparison.md).

## Run a small CPU engineering smoke

From the repository root, use the existing installed Python environment; these
commands neither install dependencies nor download data. Each output directory
must be new. Training and evaluation are deliberately separate invocations.

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
PYTHONPATH=.:src /home/john/simic/.venv/bin/python -B \
  -m experiments.bounded_comparison train --output /tmp/simic-smoke --epochs 7

PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
PYTHONPATH=.:src /home/john/simic/.venv/bin/python -B \
  -m experiments.bounded_comparison evaluate --run /tmp/simic-smoke
```

The default smoke has 128 fit, 64 development and 128 outer examples, one
paired training seed, one CPU thread and batch size 32. Images have ten
class-specific colors plus independent pixel jitter. Fit/development/outer
examples use distinct recorded random streams from the same learnable rule.
The outer stream identity and size are committed before it is generated.
This is a learning and persistence fixture. Its accuracy and arm differences
are **engineering smoke only**, never CIFAR or growth-superiority evidence.

To check offline CIFAR ingress within the same small budget:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
PYTHONPATH=.:src /home/john/simic/.venv/bin/python -B \
  -m experiments.bounded_comparison train --output /tmp/simic-cifar-smoke \
  --data cifar --data-root /home/john/simic/runs/data --epochs 7

PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
PYTHONPATH=.:src /home/john/simic/.venv/bin/python -B \
  -m experiments.bounded_comparison evaluate --run /tmp/simic-cifar-smoke \
  --data-root /home/john/simic/runs/data
```

This tiny subset checks the data path; it cannot establish generalization or
growth benefit. Larger runs require a separate budget decision. The defaults
are explicit CLI arguments (`train --help`); there is no hidden campaign
collection, policy fitting, scheduler, checkpoint selection or GPU execution.

## Experiment contract

| Item | Fixed meaning |
|---|---|
| Host/task | `Host("mild")`: CNN widths 20/64/72, BatchNorm in all stages, ten classes, one 64-channel 8×8 insertion site |
| Capacity | 142,006 host parameters; 8,897 seed parameters; final added-capacity topology 150,903 (+6.27%) |
| No growth | Train the host normally for the complete horizon |
| Static | Initialize the same seed body at step zero; calibrate gain on the first batch of fit inputs (development inputs before the 2026-10-08 hardening); alpha=beta=1; ordinary cross-entropy and joint training throughout. Caveat: on BatchNorm hosts the calibration features come from the untrained host in eval mode, so the static gain is born far below tau (screen v1: about 1/25 of intended), see PDR-0045's addendum |
| Scheduled | Germinate once before zero-based epoch 2; one epoch of invisible STE training, two blending epochs, one beta-ramp epoch, then joint training |
| Graft equation | `h + alpha * Delta(h.detach()*(1-beta) + h*beta)`; TRAINING instead returns `h + (Delta - Delta.detach())` and adds the kernel trust-region penalty |
| Fossilized meaning | Alpha=beta=1; the seed remains in SGD and remains trainable. This is the kernel demo's joint-training behavior, distinct from Esper-lite's frozen seed semantics |
| Schedule declaration | K=1/M=2/F=1 is this experiment's declared schedule; it does not alter the old kernel campaign's defaults |
| Optimizer | Constant LR .05, SGD Nesterov momentum .9, decay .0005 on matrix/convolution weights, no decay on scalar gain/norm affines/biases; append seed groups without resetting host momentum |
| Pairing | Identical host initialization, seed body initialization, epoch permutations, crops and flips; named body/init/future/data/process RNG streams |
| Calibration difference | Static and scheduled gains and seed BN birth buffers reflect their own host state at birth. This difference is measured and hashed; trained seed weights are never transplanted |
| Horizon | Default ten epochs; seven is the minimum at default graft/stage settings, leaving one fully coupled training epoch. Shorter settings are refused |
| Samples | Fit size must be divisible by batch size, so no fit examples are dropped; development and outer CE are sample-weighted, including the final partial evaluation batch |
| Selection | All three final-epoch checkpoints scored; no early stopping or outer-based checkpoint/arm/schedule selection |

The static and scheduled arms have the same final block and parameter count,
but different optimization histories and executed work. This comparison
isolates the declared lifecycle as a whole; it does not isolate capacity,
birth calibration, STE training and timing into separate causal components.
Equal example/epoch budgets are not equal compute budgets. Parameter-epochs,
optimizer parameter-steps, actual host/seed fit/development/outer example
passes, calibration work and wall seconds are reported separately. Alpha-zero
STE seed execution is charged. No FLOP or CPU peak-memory estimate is fabricated.

## Data and outer evaluation boundary

CIFAR uses one fixed permutation of the official 50,000 training examples:
45,000 possible fit indices and 5,000 disjoint development indices. Requested
subsets take the first specified indices from each partition. Actual training
file SHA256 hashes, selected indices and selected tensor hashes are recorded.
The training constructor checks only canonical training files and metadata,
with `download=False`; it does not deserialize or integrity-read `test_batch`.

Training records the official outer-file MD5 identity and the first-N test
selection without opening the outer file. The evaluation command validates
completion, source, runtime, log order and every checkpoint checksum first.
It then rechecks actual training-file SHA256, verifies canonical test integrity,
records actual outer file/tensor SHA256, and scores the frozen checkpoints once.
CIFAR is a prospective evaluation split; historical development has already
used CIFAR, so it is not a pristine benchmark.

Each score preserves tensor buffers, every submodule's mode, diagnostic caches
and CPU RNG, with restoration in `finally`. Independent outer learning is
reported against the same untrained host, together with paired differences
against both no-growth and static added capacity. One paired seed is one
independent trajectory, not three independent samples. No confidence interval
or superiority claim follows from it.

## Deliverables and failure semantics

`manifest.json` pins the specification, executed source hashes,
Git commit and dirty status, runtime/host/thread identity, split identities,
RNG streams and common future. `training.jsonl` retains every arm start and
epoch, action, calibration, stage and alpha/beta values actually used, raw
loss/development metrics, costs and full training-state signatures. Those
signatures cover host and seed parameters/buffers, optimizer groups and
momentum, lifecycle counters and pinned CPU RNG. Wall time is excluded from
deterministic identity.

`no_growth.pt`, `static.pt` and `scheduled.pt` contain final inference states;
they are explicitly **not resumable training checkpoints**. `complete.json`
is published last, after files are flushed, fsynced and checksummed. Runs that
raise leave partial evidence and no accepted completion marker. Evaluation
uses `torch.load(..., weights_only=True, map_location="cpu")` only after
checksum verification and refuses source/runtime drift, missing evidence,
non-finite numbers, duplicate JSON keys, checksum mismatch and overwrites.
`outer_evaluation.json` cannot be replaced by a repeat invocation.

CPU contract tests verify no-growth parity with the existing production epoch
loop, lifecycle/gradient isolation and recoupling, CE-only seed gradients and
parameter updates, preserved momentum, calibration/body identity, independent
learnable splits, partial-batch scoring, strict corruption refusal and genuine
heldout learning on the synthetic fixture:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CUDA_VISIBLE_DEVICES='' \
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=.:src \
/home/john/simic/.venv/bin/python -B -m pytest tests/unit/test_bounded_comparison.py \
  -q -p no:cacheprovider -o addopts='' --basetemp=/tmp/simic-contract-tests
```

## Trust seams

The raw inputs are CLI arguments, persisted JSON/JSONL, checkpoint bytes and
local CIFAR tensors. Validation happens at the boundary where each one enters:

- `validated_spec` checks RunSpec ranges and types.
- `validate_data` checks tensor dtype, shape, count and labels.
- `read_json` rejects duplicate keys, non-object roots and non-finite numbers.
  Parsing alone is only syntactic.
- `verify_run` gives semantic assurance: completeness, artifact identities,
  checkpoint state and source/runtime drift.
- `publish_evaluation` consumes only a verified record and refuses to
  overwrite an existing one.

The contract tests exercise these rejection paths directly.

Until 2026-10-08 these seams also carried no-op Wardline marker decorators, so
the Wardline scanner could check them statically. Wardline is being rebuilt,
and the markers were imported from an absolute path into its source checkout
and re-hashed at every run. They were therefore removed (PDR-0042). Commit
`c40972d` shows the full marking and its witness tests; re-applying them is
`simic-2035316005`. Until then, no static analyzer covers these modules, and
runtime checks plus contract tests are the only assurance. This experiment does
not claim HLD conformance, and the full HLD contract registry is unseeded.

## Recorded runs

| Date | Run | Data | Outcome |
|---|---|---|---|
| 2026-10-04 | Synthetic acceptance and tiny CIFAR smoke (128 fit / 64 dev / 128 outer, 7 epochs) | Synthetic fixture; CIFAR-10 | Synthetic data: all arms learn. CIFAR: accuracy rose but CE worsened in every arm (Codex task-7 report) |
| 2026-10-08 | [CPU development pilot](results/2026-10-08-bounded-cpu-pilot.md) (1,024 fit / 256 dev, 10 epochs, seed 7) | CIFAR-10 training files only | Dev CE fell in all three arms. Final dev CE: static 1.605, no growth 1.691, scheduled 1.722, within single-epoch noise. Outer data not opened |
| 2026-10-08 | [Pre-registered screen v1](results/2026-10-08-bounded-screen-v1.md): 48 paired seeds (4,096 fit / 5,000 dev, 10 epochs) | CIFAR-10 training files only | Instrument resolves (±0.018 nats). Graft equivalent to no growth (+0.002) and to static capacity (−0.016) within δ = 0.05. Reading `reopen_no_value` (PDR-0045) |
| 2026-10-08 | [Positive control v1](results/2026-10-08-positive-control-v1.md): 48 seeds, `under_normalized` + `norm` | CIFAR-10 training files only | `instrument_failure`: the graft arm diverged in 12/48 units and the runner then aborted them (since fixed); root cause in PDR-0047 |
| 2026-10-08 | [Positive control v2](results/2026-10-08-positive-control-v2.md): 48 fresh seeds | CIFAR-10 training files only | `control_fails_below_floor`: static − no growth −0.119 [−0.151, −0.088], 42/47 finite pairs; a real deficit, but a benefit ≥ δ_pc = 0.10 is not established (PDR-0049) |

## Multi-seed screens

`experiments/bounded_screen.py` runs a frozen plan from `docs/prereg/`. It
launches one training run per declared seed as parallel single-thread CPU
processes, refusing a dirty tree or a data root that exposes `test_batch`. It
then analyses the completed units once:

```bash
PYTHONPATH=.:src .venv/bin/python -B -m experiments.bounded_screen launch \
  --root runs/<screen> --plan docs/prereg/<plan>.json --data-root runs/cifar-fit-only --workers 8
PYTHONPATH=.:src .venv/bin/python -B -m experiments.bounded_screen analyze \
  --root runs/<screen> --plan docs/prereg/<plan>.json
```

The analysis checks every unit with `verify_run`, refuses a plan whose hash
changed since launch, records any unit failure rather than dropping it, and
refuses to overwrite `screen_report.json`. The unit of inference is one
training seed: the three arms within a seed are matched repeated measures.

A plan declares its contrasts as arm pairs with a role (`co-primary` or
`descriptive`), the late epochs, the floor δ, and a named `reading_rule`.
The rule maps the report onto one pre-committed reading with a stated
precedence. The report also records:
- the plan hash, the analysis commit and a timestamp;
- per-arm mean costs;
- for each contrast, the true effect needed for an 80% chance that the whole
  interval clears −δ.

The screen v1 plan predates this schema and is kept unchanged as its record.

## Hosts and seed types

`--host` selects one of the kernel demo's host pathologies (`mild`,
`under_normalized`, `channel_starved`, `no_spatial_mix`), and `--seed-type`
selects one of its seed blocks (`norm`, `attn`, `conv_light`, `conv_heavy`).
The defaults, `mild` and `conv_light`, reproduce screen v1's configuration.
The seed's gain is calibrated on the first batch of *fit* inputs. Runs from
before 2026-10-08's hardening calibrated on development inputs, a negligible
but asymmetric touch that the screen v1 audit flagged. `verify_run` now also
refuses a run whose arms do not share the host initialization, or whose
scheduled arm diverges from no growth before germination.
