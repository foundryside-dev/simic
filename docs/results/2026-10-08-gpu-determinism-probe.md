# GPU determinism probe — bounded runner on 2× RTX 4060 Ti

2026-10-08. torch 2.13.0+cu130, cuDNN 92000, driver 580.178.04. Flags = `enable_class1()` (deterministic algorithms, cudnn.deterministic, benchmark off, TF32 off, `CUBLAS_WORKSPACE_CONFIG=:4096:8`), 1 thread. Data: `smoke_split` (CIFAR shapes; `runs/` not read). Every run is a fresh process; hashes are the runner's `training_state_sha256`. Scripts and raw JSON sit beside this file (`probe_lib.py`, `probe_ops.py`, `q123/`, `snap/`, `q5/`). Repo untouched.

## Verdicts

**Q1 same seed, same GPU, twice: bitwise identical.** 9 configurations (mild, under_normalized × no_growth/scheduled/static × conv_light/norm; 6 epochs, germination at 2): every epoch hash equal. Where the crippled host went non-finite on smoke data, both runs diverged at the same (epoch, step, reason): mild/no_growth `8f88bdc7d3e8…`; under_normalized `544448466f3b…`, epoch 3 step 3.

**Q2 pairing on GPU: holds.** scheduled == no_growth at every pre-germination epoch, and host-parameter hashes stay equal through the alpha=0 graft epoch, on GPU0, GPU1 and CPU. `verify_pairing` passes unchanged.

**Q3a GPU0 vs GPU1: bitwise identical** in all 9 configurations. **Snapshot branching (rung 4's operation):** a no_growth snapshot at epoch 2, resumed in a new process as no_growth or as scheduled, reproduces the continuous runs' hashes exactly — on GPU1, on GPU0 under multi-process contention, and from a mid-lifecycle (BLENDING) snapshot.

**Q3b CPU vs GPU: not equal, as expected.** Init equal; the first forward differs at ULP level (step-1 |ΔCE| 1.2e-7). Mild host, 256 examples: dev |ΔCE| peaks 3.1e-2 (epoch 2), 1.7e-5 at epoch 5; accuracy identical. Screen config: ≤ 8.9e-3 mid-run, 3.6e-5 final (smoke saturates; not CIFAR magnitudes). **Hazard:** on under_normalized the ULP noise moved the non-finite point from epoch 3 step 3 (GPU) to epoch 5 step 6 (CPU) — a different outcome class.

**Q4 ops refusing deterministic mode: none.** 52 cases (4 hosts × {no seed, 4 seeds} × 3 stages; forward, backward, step, eval): zero errors, zero warnings — GroupNorm, BatchNorm, attention, grouped conv, pooling, reflect-pad, cross-entropy all run.

**Q5 throughput, screen config (4096/5000/10/32), one arm incl. dev scoring:**

| Execution | Wall/arm | Units/hour | Note |
|---|---:|---:|---|
| 1 CPU thread | 105.7 s | ~11 | matches screen-v1 (366–435 s/unit) |
| 1 GPU, det on | 8.0 s | ~150 | 150 MiB peak |
| 1 GPU, det off | 6.3 s | — | deterministic mode costs 1.27× |
| 2 / 4 / 8 procs per GPU | 19.4 / 36.7 / 73.7 s each | ~124 / 131 / 130 | hashes identical to solo |

One GPU ≈ 13× one CPU thread, ≈ 2× the 8-worker CPU screen; both GPUs ≈ 300 units/hour. Sharing a GPU is determinism-safe but aggregate throughput stays below solo: one process per GPU, two GPUs in parallel.

## Recommended profile for rung 4

**"Academy-exact on GPU", scoped exact-per-SKU:** bitwise within a device, across these two identical GPUs, and across snapshot/resume/fan — PDR-0050's "bitwise through deterministic algorithms and a fixed CUBLAS workspace". Never claim CPU equivalence; CPU stays the reference lineage and a run's lineage is its device class. "Measured uncertainty" applies only if CPU and GPU are mixed inside a unit, which rung 4 must not do.

## Minimal runner changes (described only)

1. `configure_cpu` → `configure(spec)` with a `device` field on `RunSpec`: on CUDA call `enable_class1()`, drop `set_default_device("cpu")`, add a CUDA RNG pin.
2. `attach_seed`: `build_seed(...).to(device)` before `tau_init`.
3. `train`: data, host and slot `.to(device)` before `build_optimizer`.
4. `runtime()`/manifest: record device, GPU name, driver, cuDNN, TF32, workspace config; `verify_run` re-derives it rather than hardcoding `"device": "cpu"`; `scaffold_state.execution` gets a GPU value.
5. `training_state_hash`: fold in the CUDA RNG state.
6. A resumable snapshot (host, seed, optimizer, slot lifecycle fields, both RNG states, hash) whose restore asserts hash equality before continuing — `probe_lib._snapshot/_restore` is the shape.

## Hazards

- Exactness is per SKU/driver/torch build: pin and record them, refuse replay on mismatch (`REPLAY_REFUSAL_KEYS`).
- Never mix or bitwise-compare CPU and GPU lineages; ULP noise moved a divergence by two epochs.
- `torch.compile`, AMP, TF32, cudnn.benchmark each void the claim (`FORBIDDEN_RELAXATIONS`).
- Per-step `float()` syncs keep the GPU launch-bound; a larger batch would be faster but changes the pre-registered design.

## Confidence Assessment

High for Q1, Q2, Q3a, Q4 and snapshot branching (hashes in `q123/`, `snap/`); Moderate for Q5 absolutes (smoke data, one seed); Low for CPU–GPU CE magnitudes on CIFAR.

## Risk Assessment

Low to adopt the profile (reversible; CPU path untouched). Medium that an unmeasured CIFAR-scale path differs (same ops and shapes, so not expected).

## Information Gaps

No CIFAR run; no cross-driver/torch-version test; no MPS test; sharing tested to 8 processes.

## Caveats

The probe re-implements `train()`'s loop out-of-tree reusing `train_epoch`, `score`, `training_state_hash`; a runner port must be re-verified with the same hash checks.
