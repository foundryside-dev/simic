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
| Static | Initialize the same seed body at step zero; calibrate gain on development features; alpha=beta=1; ordinary cross-entropy and joint training throughout |
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

`manifest.json` pins the specification, executed source/dependency hashes,
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

## Local Wardline contract

The new modules use the official `weft-markers` 0.1.0 no-op decorators. Raw
sources are CLI arguments, persisted JSON/JSONL, checkpoint bytes and local
CIFAR tensors. Returning boundaries validate RunSpec ranges, tensor
dtype/shape/count/labels, run completeness and artifact identities, checkpoint
state, and measured evaluation records. JSON parsing alone is only `GUARDED`;
it does not confer semantic assurance. `publish_evaluation` consumes the
validated record and retains the existing exclusive-write refusal. These
markers declare those specific contracts, not arbitrary metadata or scientific
validity. They do not replace runtime checks.

The Nyx-local dependency declares the absolute official source directory
`/home/john/wardline/packages/weft-markers`, from Wardline commit
`28deffbeb856b0359083b7df3e3f2b1e98e57584`. This checkout is required to reproduce
the local environment. UV normalizes the lock's directory against the project
location, so the lock must be generated and checked for `/home/john/simic`
before installation there; it is not a portable or immutable package pin.
Every run separately verifies and records installed marker-module SHA256,
official source-module SHA256 and package-metadata SHA256 against explicit
pins. Evaluation refuses changed dependency bytes along with source drift.
Installing this marker package does not install the scanner or refresh Torch.

Run the unsuppressed local gate from the repository root:

```bash
/home/john/wardline/.venv/bin/wardline scan . --fail-on ERROR \
  --fail-on-inert --fail-on-unanalyzed --local-only --format jsonl \
  --output /tmp/simic-wardline.jsonl --cache-dir /tmp/simic-wardline-cache

WARDLINE_BIN=/home/john/wardline/.venv/bin/wardline \
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CUDA_VISIBLE_DEVICES='' \
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=.:src \
/home/john/simic/.venv/bin/python -B -m pytest tests/unit/test_bounded_wardline.py \
  -q -p no:cacheprovider -o addopts='' --basetemp=/tmp/simic-wardline-tests
```

The integration tests scan temporary copies of these actual modules, require
the recognized function inventory, remove the actual data-validation rejection
and bypass the actual evaluator verification path with raw persisted text.
The intact path passes; both broken paths must produce specific ERROR findings.
No training or dataset access is needed by those tests. Scanner witness tests
skip when `WARDLINE_BIN` or a PATH scanner is unavailable, so a skipped test is
not a passing gate.

This is coverage of the new bounded seams, not a retrofit of the old kernel or
full HLD. External/native calls (including Torch and torchvision) remain
unresolved static-analysis facts; runtime integrity checks and contract tests
cover behavior that the analyzer cannot prove. No baseline, waiver or blanket
trust declaration is used. Warpline remains unavailable and no passing gate is
claimed for it. The full HLD contract registry is unseeded; this experiment does
not claim HLD conformance.
