> **Design spike, 2026-10-09, input to [PDR-0057](../../decisions/0057-controller-training-pathway.md).** Written by a subagent (Opus) from the repository at main `6d38c81`. Scripts it cites under `scratchpad/` were not committed. Where a number here disagrees with a committed script, the committed script wins. In particular, S1's §0 headroom claim is superseded by `docs/results/2026-10-09-rung4-timing-horizon/exploratory/timing_headroom_null.py.txt`: single-future data cannot separate per-seed headroom from noise.

# S3 — Counterfactual atlas: engineering spike

Date: 2026-10-09. Scope: read-only design spike against `experiments/bounded_comparison.py`,
`experiments/timing_study.py`, `experiments/kernel_demo.py`, `experiments/bounded_data.py` and
`tests/unit/test_bounded_lifecycle_v2.py`. CPU-only measurements; no GPU job was run. Nothing in the
repository was written. Scratch scripts live in `.../scratchpad/prof/`.

**Constraint observed throughout:** `Host`, `Slot`, `build_seed`, `augment`, `build_optimizer`,
`append_seed_group`, `take_snapshot`, `state_hash` and the rest of `kernel_demo.py` are `@semantic`.
This document proposes no edits to them. Everything new goes in new modules (proposed:
`experiments/atlas.py`, `experiments/atlas_hosts.py`, `experiments/atlas_telemetry.py`), which
subclass, wrap or re-implement them and must prove bitwise equality where they replace them.

---

## 0. Headline findings

1. **The kernel already has a fork engine.** `Snapshot`/`take_snapshot`/`run_arm`/`run_fan`
   (`kernel_demo.py:1143-1478`) build each arm fresh from snapshot values and check a no-op twin
   against the base's hashes. The atlas should port that pattern into the bounded harness. It
   should not invent a new one. What the kernel's base-only snapshot leaves out is the slot
   lifecycle and any installed seed, and the atlas needs both.
2. **Rung 4 already holds a free golden reference.** `runs/rung4-timing-horizon/` holds 768 seeds
   × 6 cells of GPU records. Each record carries per-epoch `host_state_sha256` and
   `training_state_sha256`, and its `scheduled` arms are exactly the atlas action
   "germinate `norm` at the stage-2 slot at epoch t ∈ {0,1,2,3,5}". An atlas run in "legacy mode"
   (single stage-2 slot, legacy seed-init derivation, `eval_chunk = 32`, exact-records
   optimizations only) must reproduce those `training.jsonl` records bitwise, minus `wall_s`.
   That gives GPU validation at no new design cost.
3. **The loop is bounded by syncs and kernel count, not by FLOPs.** The CPU-side measurement below
   gives 38 / 58 / 52 host←device syncs per train step (dormant / STE / fossilized), plus 6 per
   dev batch. A step launches roughly 380–540 leaf ATen ops, of which the grad-norm witness alone
   is 36%. At batch 32, the GPU kernels are latency-sized, so cutting launches cuts GPU time as
   well as CPU time.
4. **Redundancy explains most of rung 4's cost.** The fleet ran 17.3 h on 2 GPUs: per seed,
   5 × 23.0 s + 42.5 s = 157.5 s, with each cell in its own subprocess. No-growth and static were
   recomputed in every cell, and CIFAR was reloaded and rehashed six times per seed. A
   fork-from-snapshot unit does the same scientific work in **89 instead of 210 arm-epochs per
   seed (2.4×)**, with one process start-up instead of six.

---

## 1. Fork-from-snapshot

### 1.1 State a snapshot must capture (epoch-boundary forks only)

| Component | Where it lives today | Notes |
|---|---|---|
| Host parameters **and buffers** | `host.state_dict()` | `under_normalized` has no BN buffers, but every other host has `running_mean`, `running_var` and `num_batches_tracked`. Use `{k: v.detach().clone()}`: `state_dict()` returns live references. |
| Optimizer state | `opt.state_dict()`: per-param `momentum_buffer` plus the hyperparameters of each param group | Nesterov SGD keeps no separate Nesterov buffer. The look-ahead is computed from `momentum_buffer` (`build_optimizer`, `kernel_demo.py:876-891`). **`copy.deepcopy`** the state dict, as `take_snapshot` does at `kernel_demo.py:1162`. At epoch 0, before any step, the state is empty, and that is correct. |
| Optimizer group structure | 2 host groups, plus 2 per installed seed (`append_seed_group`, `kernel_demo.py:894-899`) | **Second-decision hazard.** A snapshot taken after a graft has 4 or more groups. The branch must rebuild the seed with `build_seed` (same init derivation), call `append_seed_group` in the original order, and only then call `opt.load_state_dict`. `load_state_dict` matches groups by position and refuses a count mismatch. |
| Seed module | `slot.seed.state_dict()` (gain, body, and any BN buffers, e.g. `conv_heavy`) | Capture it only when `slot.seed is not None`. |
| Slot lifecycle | `stage, alpha, beta, _blend_step, _fossil_step, _epochs_in_stage, alpha_beta_log, rms_ratio_blend_entry` | These are the same fields `training_state_hash` hashes (`bounded_comparison.py:459-469`). `alpha` and `beta` are Python floats, so copy them exactly. |
| Slot transients | `last_delta`, `last_h`, `ScaleAwareSlot.last_witness` | Reset them to `None` on materialization. Every forward sets them before anything reads them in a step, so they never carry across an epoch boundary. |
| CPU and CUDA global RNG | `torch.get_rng_state()`, `torch.cuda.get_rng_state()` | **Training draws nothing from either.** All randomness is precomputed in the common future, and `build_seed`/`build_host` draw inside `rng_scope`, which restores the global stream (`kernel_demo.py:124-136`). Both states are restored anyway, because `training_state_hash` includes them (`bounded_comparison.py:477-479`) and digest equality depends on them. |
| Data cursor | — | `draw_future` derives each epoch's order, crops and flips from `derive(seed, "epoch", epoch)` (`bounded_comparison.py:613-617`). The cursor is therefore just the epoch index: no generator state to save. Decision points sit at epoch boundaries, with the semantics `graft_epoch` already has: "germinate before epoch t trains". |
| Cost counters and history | `costs` dict, `history` list in `train()` | These are Python ints and lists. Copy the counters to the branch. History up to t belongs to the trunk, so the atlas record references the trunk rather than duplicating it. |
| Process configuration | `configure(spec)` (`bounded_comparison.py:394-406`) | Set once per process: deterministic algorithms, `enable_class1`, CUBLAS workspace. Every branch of a unit runs in one process on one device. That keeps the existing invariant "every cell of a seed on one device" (`timing_study.py:462`). |

### 1.2 Minimal implementation in this harness

Add a new `experiments/atlas.py` that imports from `bounded_comparison`. Do not touch the frozen
rung-4 runner.

```text
AtlasSnapshot  = {epoch, host_sd, seed_sd | None, seed_meta (blueprint, site, init_seed) | None,
                  slot_lifecycle(dict), opt_sd(deepcopied), cpu_rng, cuda_rng | None, costs}
take(host, slots, opt, costs, epoch) -> AtlasSnapshot
materialize(snap, spec) -> (host, slots, opt):
    host = build_host(spec.host, derive(seed,"host-init")).to(dev); host.load_state_dict(snap.host_sd)
    opt  = build_optimizer(host, cfg)
    for each installed seed in birth order: seed = build_seed(...); seed.load_state_dict(...);
                                            append_seed_group(opt, seed, cfg)
    opt.load_state_dict(copy.deepcopy(snap.opt_sd))           # AFTER all groups exist
    restore slot lifecycle; transients = None; set CPU/CUDA RNG
run_unit(spec, decision_points, actions):
    trunk = no-op run to horizon E, taking snapshots at each t in decision_points (before epoch t trains)
    for t in decision_points: for a in actions: branch = materialize(snap[t]); apply(a); run t..E-1
    twin  = materialize(snap[t0]); run no-op t0..E-1          # integrity check, see 1.3
```

The trunk loop is `train_epoch` plus `score`, with the same record shape as `train()`'s epoch
records (`bounded_comparison.py:929-943`). The atlas schema then reuses `validate_record`'s field
discipline. Treat `train()` itself as frozen and do not refactor it. Copy its arm body into an
`_run_span`-style function (the kernel's "one loop, two call sites" principle,
`kernel_demo.py:1273-1276`), and prove the copy equal to `train()` with the test in 1.3.

Seed-init derivation:
- **Legacy action** (norm at stage 2): keep `derive(seed, "seed-body-init")` exactly
  (`bounded_comparison.py:546`), so that rung-4 reproduces.
- **New (blueprint, site) pairs:** use `derive(seed, "seed-body-init", blueprint, site)`.
- The derivation is independent of decision time t on purpose. "Now vs later" contrasts then share
  their init draw (common random numbers), and only timing differs.

### 1.3 Verifying bitwise branch replay cheaply

These tests are listed in the order to write them. All but the GPU check run on CPU with smoke
data, following the conventions of `test_bounded_lifecycle_v2.py`: `RunSpec(epochs=7, ...)`, a
module-scoped fixture, and the record comparator that drops `wall_s`.

1. `test_atlas_trunk_reproduces_bounded_no_growth_records`: the trunk's epoch records equal
   `bounded_comparison.train(spec)`'s `no_growth` records, minus `wall_s`. This proves the copied
   loop is the frozen loop.
2. `test_forked_noop_twin_matches_unforked_trunk`: for every decision point t, materialize the
   snapshot, run no-op from t to E, and require per-epoch `training_state_sha256` and
   `host_state_sha256` equal to the trunk's records over epochs ≥ t. This is the comparison
   `verify_pairing` already makes for scheduled vs no_growth (`bounded_comparison.py:1162-1176`).
   It costs no extra compute in production, because the no-op branch is mandatory anyway. The
   choice is whether to recompute it or to reuse the trunk suffix (see the caveat below).
3. `test_forked_germination_matches_bounded_scheduled_arm`: a branch "germinate norm at t = 2"
   equals `train(RunSpec(graft_epoch=2))`'s `scheduled` records, minus `wall_s`. Together with
   tests 1–2, this makes the atlas a strict superset of the rung-4 instrument.
4. `test_post_graft_snapshot_rebuilds_groups_before_load` (second decision point): snapshot a
   branch at epoch t + 1 with a seed installed, materialize it, run to E, and require the
   continuation's digests to equal the unforked branch's. The test must fail if
   `opt.load_state_dict` runs before `append_seed_group`.
5. `test_ste_epoch_host_hash_equals_noop` (free per-branch check, every branch, every run): through
   the STE TRAINING epoch, `h + (delta - delta.detach())` with `beta = 0` leaves the host's forward
   value and gradients unchanged. A grafted branch's `host_state_sha256` at the end of its TRAINING
   epoch must therefore equal the no-op's. The kernel asserts the same thing at
   `kernel_demo.py:1455-1462`.
6. **GPU dry-run checkpoint, not a unit test.** Atlas legacy mode, run on seeds 8001–8008, must
   reproduce `runs/rung4-timing-horizon/units/seed-*/T{0,1,2,3,5}/training.jsonl` and the 20-epoch
   `H20` records bitwise, minus `wall_s`, on the same SKU, driver and build.
   `manifest.runtime` pins all three: RTX 4060 Ti, CUDA 13.0, cuDNN 92000, torch 2.13.0+cu130.

**Caveat (protocol, John's call):** the kernel always recomputes the twin ("twin FIRST",
`kernel_demo.py:1441-1450`), which costs 1/(K+1) of a decision point. Once tests 1–6 pass, reusing
the trunk suffix as the no-op and recomputing the twin on a declared sample (for example one
decision point per unit) is defensible. That relaxation is a pre-registration decision, not an
engineering default.

---

## 2. Cost model and speed-up

### 2.1 Where the time goes today (measured where stated)

**Fleet-level, measured from `runs/rung4-timing-horizon/progress.jsonl` and `launch.json`:**
- Median wall is 23.0 s per 10-epoch three-arm subprocess and 42.5 s per 20-epoch one.
- 768 seeds × 6 cells = 4,608 runs took 17.3 h on 2 workers.

**Per epoch, from the `training.jsonl` of seed 8400, cell T0:**
- `wall_s`: no_growth 0.55–0.57 s; static, fossilized and scheduled 0.66–0.72 s; STE epoch 0.77 s.
- `wall_s` wraps `train_epoch` (128 steps of 32) **and** `score` over 5,000 dev images in 157
  batches, because `eval_chunk = batch_size = 32` (`bounded_data.py:92`).
- The three arms sum to about 20 s. The remaining ~3 s per run is process start-up: importing
  torch, loading CIFAR, hashing all 50k images through `cifar_source_hashes`, writing the
  manifest, and writing and fsyncing checkpoints.

**Per step, CPU proxy.** Measured by `scratchpad/prof/step_profile.py` and `regions.py`, with
`CUDA_VISIBLE_DEVICES=""`, smoke data, and Tensor `__float__`/`__bool__`/`__int__`/`item`
instrumented. Each conversion counted here is a full device sync on CUDA.

| | dormant | STE (v2) | fossilized |
|---|---|---|---|
| host←device syncs per train step | 38 | 58 | 52 |
| syncs per dev batch (`score`) | 6 | 6 | 6 |
| leaf ATen ops per step | 378 | 535 | — |
| of which grad-norm witness (`grad_norm`, `bounded_comparison.py:700-707`) | 136 (36%) | 188 (35%) | — |
| of which augment and index (`kernel_demo.py:334-346`) | 62 (16%) | 62 | — |
| forward / loss and trust / backward / `opt.step`* | 42 / 8+9 / 74 / 47 | 56 / 54+9 / 104 / 62 | — |

\* `opt.step` runs the per-parameter for-loop implementation on CPU. On CUDA, `SGD(foreach=None)`
selects the foreach path, so the GPU op count for the optimizer will be lower. This is unverified
here (Information Gap).

**Sync sources in `train_epoch` (`bounded_comparison.py:737-764`), per step:**
- `grad_norm` makes 2 syncs per parameter: `bool(isfinite(grad).all())` and
  `float(grad.square().sum())`. That is 16 for the 8-tensor host, plus the seed body and gain.
- `bool(isfinite(objective))`, `float(ce)`, `float(objective)`, and `float(gain)` when a seed is
  present.
- In the v2 STE epoch: `float(d_t)` and `float(s_t)` (`bounded_comparison.py:668`), plus a
  `deepcopy(seed)` forward.

`score` adds `float(loss)`, `int(correct)` and `bool(isfinite)` per batch (`:498-504`), plus one
`torch.equal` per state tensor afterwards (`:507-509`). That makes about 5,800 syncs per
no-growth epoch.

**Why this matters.** Every sync drains the GPU queue, so CPU launch time and GPU execution add
instead of overlapping. At batch 32 the CNN is about 0.8 GMAC forward per step, so GPU time is set
by kernel count and launch latency rather than FLOPs. "GPU about 50% busy" is consistent with a
serialized, launch-bound loop. Dispatch overhead on this host is ~1.9 µs per tiny CPU op, measured;
CUDA launch adds several µs on top.

**What is cheap:**
- `draw_future` for 10 epochs: 1.05 ms.
- `training_state_hash`: 1.6 ms. `state_hash(host)`: 0.7 ms.
- Both are once per epoch, so negligible. Witness digests are not the bottleneck.
- Augmentation is already GPU-resident (`tx` lives on the device). Its 62 ops are the gather,
  pad, normalize and per-step uploads of `CIFAR_MEAN`/`CIFAR_STD` and of crops, flips and `idx`.
  It is not a CPU-side PIL pipeline.

### 2.2 Proposals, ordered by risk. Every one is gated on trajectory-digest equality.

Two kinds of output need to be kept apart:
- **Trajectory digests**: `host_state_sha256`, `host_parameter_sha256`, `training_state_sha256`.
  These must stay bitwise equal.
- **Recorded witness fields**: `gradient_norm_max`, `train_ce`, `train_objective`, `dev`, the STE
  table. These do not feed back into training. Under the **exact-records** tier they also stay
  bitwise equal, so rung-4 keeps working as a golden reference. A **declared** tier may change
  their low bits, but only under an atlas schema version and only when the change is declared.

| # | Change | Determinism | Expected gain (estimate) |
|---|---|---|---|
| A | **Fork-from-snapshot unit**, one process per seed: trunk + K branches; CIFAR loaded and hashed once | Exact (tests 1.3/1–6) | Rung-4-shaped work: 210 → 89 arm-epochs per seed (**2.4×**), and 6 → 1 start-ups (saves ~15 s/seed). Structural. |
| B | **P processes per GPU.** `timing_study.launch` enforces `workers <= len(gpus)` (`timing_study.py:414-417`). The real invariant is "every cell of a seed on one device", and multi-process keeps it. | Exact: deterministic kernels do not depend on co-tenancy. Test: one unit run solo and run alongside 3 others gives equal digests. | 1.5–2× at P = 2–4 without MPS (time-sliced contexts fill the idle gaps). Possibly more with CUDA MPS, because tiny kernels from different processes can then overlap. 16 GB per card and a footprint of ~0.5 GB per process are not limits. The shared CPU is the limit: watch load. **Measure first. Hours of work, zero arithmetic risk.** |
| C | **Exact-records sync removal.** Queue each parameter's `isfinite().all()` and `square().sum()` kernels unchanged, `torch.stack` them, and do one `.cpu()` per step. Optionally defer to epoch end: keep per-step `ce`, `objective` and `gain` on device and transfer once, then run the **same Python float64 accumulation in the same order**. Do the same in `score`: per-batch sums on device, one transfer, same accumulation order, and a stacked `torch.equal` for the integrity check. | Exact on recorded values as well: the same kernels and the same host-side arithmetic. Deferred divergence detection still reports the first non-finite step and truncates the witness to it. Steps run after a NaN are never recorded or charged; this must be stated in the schema doc. The v2 `float(d_t)`/`float(s_t)` are **causal**, because `lam_t` multiplies the loss. Keep them (STE epochs only). | Syncs drop from 38–58 per step to 1–3, and from 6 per dev batch to ~0. Launch count is unchanged, but CPU and GPU now overlap. ~1.3–2× per step (unmeasured). |
| D | **Pre-augment each epoch once per unit**: one `augment(tx[order_e], crops_e, flips_e)` call over all 4,096 images (50 MB float32 per epoch), sliced per step, **shared by all K branches**. Use device-resident mean, std and future tensors. | Exact. Every op in `augment` is elementwise or a gather, with no reductions. Test `torch.equal(slice, kd.augment(per-step))` on CPU and GPU. `augment` itself is `@semantic` and is called, not edited. | Removes ~60 of ~380 launches per step per branch, and amortizes them across K + 1 branches. ~1.1–1.2×. |
| E | **Larger eval batch** (declared `eval_chunk`, e.g. 500 or 1,000) | **Changes `dev.ce` low bits.** The Python float summation regroups, and cuDNN may pick a different algorithm per batch shape. Allowed only as a declared atlas config field. Legacy mode keeps 32. | Scoring falls from 157 forward calls per epoch to 5–10. Scoring is plausibly 15–40% of epoch wall (unmeasured), so ~1.2–1.6×. |
| F | Grad-norm witness via `torch._foreach_norm`, with an on-device running max | Changes the low bits of `gradient_norm_max` (different reduction). Trajectory unaffected. Declared tier only. | Cuts ~100 launches per step beyond C. ~1.1–1.3×. |
| ✗ | `vmap`/`torch.func` over K branches | **Not Academy-exact relative to the sequential path.** A batched conv is lowered to a grouped conv, with different kernels and reduction order. It cannot batch heterogeneous blueprints at all. It would create a new semantic identity whose no-op must be validated against a vmapped baseline, not against any existing record. Defer. Revisit only if A–F cannot meet the budget. | — |
| ✗ | `torch.compile`; CUDA graphs | `torch.compile` is in `FORBIDDEN_RELAXATIONS` (D10, `kernel_demo.py:915`). CUDA-graph capture cannot contain the remaining causal syncs (v2 clamp) and would bake in `alpha`/`beta` as Python floats that change every BLENDING and FOSSILIZING step. Using either would need a new decision record. | — |

**Atlas arithmetic.** These are estimates, not measurements. Assume ~0.65 s per arm-epoch at
today's loop, decision points t ∈ {0, 2, 4}, a 10-epoch horizon, and K = 10 germinate actions
(4 blueprints × 2–3 sites, trimmed). Per seed, that is a 10-epoch trunk, K × (10 + 8 + 6) = 240
branch-epochs and one 10-epoch twin: about 260 arm-epochs, or about 170 s. For 768 seeds that is
about 36 GPU-hours, or about 18 h wall on 2 GPUs at today's loop. With A–D and P = 3, a combined
~3–5× brings it to roughly 4–6 h wall, and E (declared) to roughly 3–4 h. A first-week atlas of
256 seeds × 1 host takes about 1.5–2 h. Before quoting any of this, run one GPU profile per
build step: `torch.profiler` with the CUDA activity on one epoch.

**Horizon design flag.** Under a fixed end epoch E, a later decision gets fewer post-graft epochs.
The lifecycle needs k + m + f + 1 = 5 epochs (`RunSpec.validate`, `bounded_data.py:69`), so
t ≤ E − 5. The alternative is a fixed post-decision horizon H with E_t = t + H. The prefix-stable
future makes both options exact. The choice is statistical; route it to the
counterfactual-statistics review.

---

## 3. Multi-slot hosts and new blueprints

### 3.1 What breaks with ≥2 slots, and how to fix it without touching `@semantic` code

| Breakage | Location | Fix in `atlas_hosts.py` / `atlas.py` |
|---|---|---|
| One fixed slot site after stage 2 | `Host.forward_to_slot` / `forward` (`kernel_demo.py:601-612`) | `class MultiSlotHost(kd.Host)` **subclass**. It adds `forward_to_site(x, site)` and `forward(x, slots: dict[site, Slot])` that runs stage1 → s1 → stage2 → s2 → stage3 → s3 → GAP → fc. The slots are **not registered** submodules, matching today's pattern of passing the slot as an argument, so `state_dict` keys and `state_hash(host)` are unchanged. Dormant slots return `h` itself (`Slot.forward`, `kernel_demo.py:811-812`), so with only s2 active the op sequence is identical to the legacy forward. This is the golden-test path. |
| Seed channel count hard-coded to 64 | `attach_seed`: `build_seed(spec.seed_type, 64, ...)` (`bounded_comparison.py:546`). `Host.feat_channels = 64` (`kernel_demo.py:578`). | Atlas `attach_seed(site, blueprint)` reads channels from a site table: s1 = (w1, 16×16), s2 = (w2_out, 8×8), s3 = (w3, 4×4). Calibrate with `forward_to_site` on the same `fit_x[:batch_size]` prefix (recorded `calibration_inputs_sha256`). |
| Single-slot lifecycle in the digest | `training_state_hash(host, slot, opt)` (`bounded_comparison.py:454-480`) | `atlas_training_state_hash(host, slots, opt)` hashes `slots` in fixed site order. With only s2 present, the definition must reduce to the legacy one so the golden test holds: either the legacy hash plus one extra digest per extra slot, or a test asserting the reduction. |
| Trust term and witness for one slot | `train_epoch`: `ce + slot.trust_region_loss(cfg)` (`:742`). Witness lists are per-arm. | Sum `trust_region_loss` only over slots in TRAINING, in site order. Adding the `torch.zeros(())` of dormant slots would add launches; with one active slot this is bitwise-equal to the legacy term. The v2 clamp `kappa ≤ s·c*` is a per-slot curvature bound and stays per slot: `c_star` uses the shared `seed_lr`. Witness tables are keyed by site. |
| `step_tick`/`epoch_tick` | `Slot` (`kernel_demo.py:841-873`) | Call each in site order. Lifecycles are independent. |
| Atlas-wide "one lifetime germination" | `attach_seed` refuses a non-DORMANT slot (`:544`) | Keep the refusal per slot. The atlas's first stage needs at most one active graft per branch; multi-graft branches come later. |
| Record validation hard-coded to 3 arms | `validate_record`, `verify_run`, `ARMS` (`:225-329`, `:1043-1159`) | A new atlas schema and `verify_atlas_unit`, written in the same style: strict JSON, `require_keys`, no silent defaults. Leave the rung-4 validators frozen. |
| `GroupNorm(8, C)` | `NormSeed` (`kernel_demo.py:659`) | It needs C % 8 == 0. Measured: `build_seed("norm", 20, ...)` raises a ValueError, so the post-stage-1 site on `mild` (w1 = 20) cannot host `norm`. Either make the atlas action space site-aware, or add a declared `norm_g4` variant. Every slot site in the new host family uses multiples of 8. |

### 3.2 Squeeze-excite blueprint

Put it in `atlas_hosts.py` as `SqueezeExciteSeed(kd.SeedDelta)`. It subclasses the semantic class
and leaves the base untouched.

Define `f(h) = h ⊙ (σ(W₂ ReLU(W₁ GAP(h)) + b₂) − 1)` with reduction r = 4.

- This follows `NormSeed`'s `gn(h) − h` idiom, so gain = 1 recovers exactly the standard SE output
  `h ⊙ s`. With gain = 0 the slot is the identity, so the null-seed bitwise test applies.
- At initialization σ ≈ 0.5, so `rms(f₀) ≈ 0.5·rms(h)` and `tau_init` gives gain ≈ 0.1. That is
  far from the `tau_eps` floor and has no blow-up risk.
- The alternative `h ⊙ (2σ − 1)` starts near zero and pushes gain up. Not recommended.
- Pure gating `f = h ⊙ s` also honours the delta contract, but gain = 1 would then double the
  activation. Rejected.
- Test: `test_se_seed_gain_one_is_standard_se`, `test_se_tau_init_hits_tau`.

Reductions are deterministic: GAP is a mean and the layers are Linear. No new determinism exposure.

### 3.3 Parameter counts (measured with `scratchpad/prof/params.py`)

| Host (kernel pathologies) | params | Seed | s1 (24 ch) | s2 (64 ch) | s3 (80 ch) |
|---|---|---|---|---|---|
| under_normalized | 161,010 | norm | 49 | 129 (0.08%) | 161 |
| channel_starved | 129,922 | se_r4 | 319 | 2,129 (1.3%) | 3,301 |
| no_spatial_mix | 116,626 | attn | 1,657 | 4,337 (2.7%) | 5,409 |
| mild | 142,006 | conv_light | 3,417 | 8,897 (5.5%) | 11,089 |
| reference (BN, 3×3, 24/64/80) | 161,682 | conv_heavy | 22,617 | 60,137 (37%) | 75,145 |

The percentages are relative to under_normalized. `se_r8` is 1,097 parameters at 64 channels.

---

## 4. Pre-decision telemetry features

**Starting point.** The kernel's 20-dim `TelemetryRecord` (`kernel_demo.py:358-396`, built in
`train_one_epoch`, `:1060-1140`) holds:
- loss, val loss and accuracy, and their deltas;
- per-stage grad-norm mean and variance;
- per-stage activation saturation (forward hooks at `:617-627`, which call `.item()` on every
  forward: 3 more syncs per step if copied as written);
- per-stage weight norm;
- per-class accuracy std and confusion entropy.

The bounded harness records only `train_ce`, `train_objective`, `dev`, the whole-host
`gradient_norm_max`, and witness and lifecycle data.

| Tier | Feature | Cost | Mechanism |
|---|---|---|---|
| a: free | dev CE and accuracy; train CE; train−dev gap; epoch deltas; whole-host grad-norm max | 0 | Already in the trunk's epoch records |
| a′: near-free | per-stage grad-norm mean, variance and max | ~0 extra launches | Group the per-parameter square-sums that C already computes, by stage |
| a′ | per-stage weight norm; update/weight ratio from `momentum_buffer` norms | a few launches per epoch | Epoch end, read-only |
| a′ | per-class dev accuracy, confusion entropy and spread | 1 bincount-style op per epoch | Keep the dev logits that `score` already computes. Use a vectorized confusion matrix; the kernel's `confusion_stats` loops 100 masks. |
| a′ | gradient-noise proxy: ‖mean step-gradient‖² vs mean ‖step-gradient‖² | 1 foreach-add per step | Accumulate on device in a buffer separate from the optimizer. It never feeds training. |
| b: probe forward | per-site activation RMS, dead-ReLU fraction, channel-variance spread, effective rank of slot features, BN running-stat drift (BN hosts) | 1 probe forward per decision point | At decision points only, on a **materialized throwaway copy** of the snapshot. Use eval mode with `no_grad`, or train mode with every buffer restored (the `realised_ratio_at_birth` pattern, `bounded_comparison.py:524-539`). Use forward hooks that accumulate on device, never `.item()`. |
| c: curvature | host: grad-norm variance (a′) and the loss change across consecutive steps. Probe: top Hessian eigenvalue by HVP power iteration (~20 HVPs) and a Hutchinson trace on the probe batch. The existing `kappa_live` is seed-side only. | ~20–40 forward/backward pairs per decision point, about 5–10% of one epoch | On the throwaway copy. The start vector comes from `make_generator(derive(seed, "probe", t))`, never the global stream. **Unverified:** double-backward through conv, maxpool and GAP under `use_deterministic_algorithms(True)` on CUDA may raise or be non-bitwise. Gate it with a GPU test that runs twice and asserts bitwise equality. |

**Determinism and leakage rules**, each with a test:
- **Isolation.** Telemetry reads only tensors the step already produced, or runs on a throwaway
  materialized copy. The trunk's digests with telemetry on and off must be equal:
  `test_telemetry_does_not_change_training`. This is the Tamiyo-isolation analogue.
- **No time travel.** Features come from trunk epochs < t and the snapshot at t only. Branch
  telemetry after the decision is outcome, never a feature. This is the kernel's hard rule at
  `kernel_demo.py:1235-1239`.
- **Probe split.** Probe forwards should use a separate split, not dev, because dev late-window CE
  is the outcome. `load_fit_dev` uses `perm[:train_size]` for fit and `perm[45000:]` for dev
  (`bounded_data.py:210`), so `perm[40000:41000]` is untouched for any `train_size ≤ 40000`.
  Declare it as `derive(data_seed, ...)`-pinned and hash it into the manifest.
- **Grouped splits.** Predictor train and test splits are by unit seed (and later by host). Never
  by branch: branches of one trajectory never cross splits.

---

## 5. Host family for transfer

Three of the requested pathologies already exist in `kernel_demo.PATHOLOGIES` (`:542-545`), so
only "shallow", the un-impaired reference and the width-scaled comparators are new.

| Variant | Status | Definition | Params | Slot sites |
|---|---|---|---|---|
| under_normalized | exists | no BN, ×2 init gain | 161,010 | 24 / 64 / 80 |
| channel_starved (narrow) | exists | stage-2 mid width 24 | 129,922 | 24 / 64 / 80 |
| no_spatial_mix (1×1) | exists | stage-2 1×1 kernels | 116,626 | 24 / 64 / 80 |
| shallow | **new** | one conv + BN per stage (keeps all three sites and shapes) | 61,698 | 24 / 64 / 80 |
| reference | **new** | BN, 3×3, 24/64/80 (what every pathology departs from; `mild` is slightly narrow, not healthy) | 161,682 | 24 / 64 / 80 |
| width-scaled comparator | **new** | the *same pathology*, uniformly widened in multiples of 8 to match host + graft parameters; report the residual | e.g. under_normalized + conv_heavy target 221,147 → widths (32, 72, 96) = 223,594 (+1.1%) | no slot |

Width scaling is only needed for conv_heavy, conv_light and attn. For norm and SE the graft adds
≤ 1.3%, and the existing static arm is the right comparator.

**Changes needed:**
- `RunSpec.validate` rejects any host outside `PATHOLOGIES` (`bounded_data.py:47`). Add an
  `AtlasSpec` with its own host registry.
- `kernel_demo` hosts are built through `kd.build_host`. That keeps rung-4 compatibility for
  under_normalized.
- New hosts get `atlas_hosts.build_host(name, init_seed)`. Use the same `rng_scope` discipline,
  reuse `Host._make_stage` via the subclass so stage shapes and the init gain convention match,
  and keep the slot sites aligned.
- Manifest: `host` names the registry and variant, plus a structural hash of the module tree
  (shapes and dtypes), so one name can never silently cover two shapes.
- **Deficit screen first** (round 2, `simic-f73351380d`). The atlas trunk is a no-growth run, so
  one trunk per host × N seeds measures each host's deficit against `reference` at no extra cost.
  Ship the family together with that screen.

---

## 6. Ordered build list (test-first checkpoints)

| # | Item | Effort | Checkpoint (write first) |
|---|---|---|---|
| 0 | GPU profile baseline: one epoch of one arm under `torch.profiler` (CPU + CUDA), recording kernel count, sync count and the eval share of `wall_s` | 1–2 h | Numbers recorded. Turns the §2 estimates into measurements. |
| 1 | **P processes per GPU** knob, in a new launcher or as an atlas flag. Leave `timing_study` frozen. | 2–4 h | `test_cosolo_digest_equality` as a GPU dry run: one unit run solo and alongside 3 co-tenants gives equal records minus `wall_s`. Measure throughput at P = 1–4. |
| 2 | **Snapshot/fork core** (`atlas.py`: take, materialize, trunk, branches, twin) | 1–1.5 d | §1.3 tests 1–5 on CPU smoke, then test 6 on GPU against rung 4 (seeds 8001–8008, all cells including H20). |
| 3 | **Exact-records speed tier** (C + D): stacked per-step syncs, deferred epoch scalars, batched `score`, epoch pre-augmentation | 1–1.5 d | `test_exact_tier_records_bitwise_equal_legacy` (CPU), the rung-4 golden check again (GPU), `test_preaugment_equals_kernel_augment`, and `test_deferred_divergence_reports_first_nonfinite_step` (a `monkeypatch` NaN at step 3, as in `test_bounded_lifecycle_v2.py:138-156`) |
| 4 | **Atlas record schema and `verify_atlas_unit`**: mandatory no-op per decision point (policy utility exactly 0), per-branch effect = branch − no-op on late-window dev CE, failures kept as rows, costs per branch | 1.5–2 d | `test_atlas_rejects_unit_without_noop`, `test_diverged_branch_is_a_row_not_a_drop`, and duplicate-key, non-finite and missing-key refusal tests mirroring `test_bounded_contracts.py` |
| 5 | **Multi-slot host + per-slot lifecycle + SE blueprint** (`atlas_hosts.py`) | 2–3 d | `test_multislot_with_only_s2_equals_legacy_host` (bitwise records), `test_dormant_slots_add_no_ops`, `test_v2_clamp_bound_holds_per_slot`, `test_norm_refused_at_non_multiple_of_8_site`, and the SE tests from §3.2 |
| 6 | **Telemetry tiers a, a′ and b** (`atlas_telemetry.py`), plus the probe split | 1–2 d | `test_telemetry_does_not_change_training`, `test_features_use_only_pre_decision_epochs`, `test_probe_split_disjoint_from_fit_and_dev` |
| 7 | **Host family + width-scaled comparators + deficit screen** | 1–2 d | `test_host_param_counts` (table in §5), `test_width_comparator_within_declared_residual`, `test_each_host_has_aligned_slot_sites` |
| 8 | Declared speed tier (E + F: eval batch size, foreach norms) under an atlas schema bump | 0.5 d | `test_declared_tier_trajectory_digests_unchanged` (`host_state_sha256` and `training_state_sha256` equal to the exact tier; witness fields may differ) |
| 9 | Curvature tier c (HVP), optional | 1 d | GPU: `test_hvp_power_iteration_bitwise_repeatable` under deterministic mode. If it raises, fall back to tier a′ proxies and record the limitation. |

Items 0–4 deliver a single-host, single-slot atlas that reproduces rung 4 exactly, including all
germinate-now-vs-wait contrasts for `norm`. That is about 4–5 working days. Items 5–7 add the
blueprint, site and host axes in another 4–7 days. Item 2 is the critical path; items 1 and 0 can
run in parallel with it.

---

## Confidence Assessment

**Overall: Moderate–High** for the design, **Moderate** for the speed-up numbers.

| Finding | Confidence | Basis |
|---|---|---|
| The snapshot state list is complete for epoch-boundary forks | High | `training_state_hash` enumerates the trajectory state (`bounded_comparison.py:454-480`). The kernel's `run_arm` materialization is a working precedent (`kernel_demo.py:1329-1340`). No RNG draw happens in a step: all draws are in `draw_future` or under `rng_scope`. |
| Optimizer groups must be rebuilt before `load_state_dict` | High | Positional group matching in torch SGD. The kernel comment at `kernel_demo.py:1334-1336` makes the same point. |
| Rung 4 can serve as a golden reference | High for the logic; to be verified on GPU | The records hold the per-epoch digests. Legacy-mode reproduction depends on identical init derivations and an identical op sequence. |
| Sync counts per step (38 / 58 / 52; 6 per dev batch) | High as counts | Measured by instrumenting Tensor conversions. Each conversion is a sync on CUDA. |
| Op counts and the 36% grad-norm share | Moderate | A CPU-profiler proxy for GPU launches. The optimizer count is inflated on CPU. |
| 2.4× arm-epoch saving from forking (rung-4 shape) | High | Arithmetic over the plan's cells (`docs/prereg/rung4-timing-horizon.json`) |
| Per-optimization speed-ups (1.1–2× each; 3–5× combined) | Low–Moderate | Inferred from sync and launch structure. No GPU measurement was run (forbidden in this spike). |
| `vmap` breaks bitwise equality with the sequential path | Moderate–High | Known lowering of batched conv to grouped conv. Not tested here. |
| Pre-augmentation is bitwise-exact | Moderate–High | The ops are elementwise or gathers with no reductions. Needs the `torch.equal` test on GPU. |
| SE delta form and parameter counts | High | Counts measured. The delta form follows `NormSeed`. |

## Information Gaps

- **No GPU profile.** Kernel counts, the real per-sync cost, the eval share of epoch wall, and
  whether CUDA SGD takes the foreach path are all unmeasured. Item 0 closes this gap. Every
  speed-up figure could move by about 2× once measured.
- **GPU co-tenancy.** The behaviour of P > 1 processes per GPU, with and without MPS, on this
  shared-CPU host is unknown. So is the interaction with other users' CPU load (16 logged-in
  users; load average 2.6–6).
- **Double-backward under deterministic mode** on CUDA for this network: will it raise, and is it
  bitwise?
- Whether a `kd.Host` subclass with a new `forward` stays on any `config_hash` surface the atlas
  must declare. `_SEMANTIC_SURFACE` registers only decorated objects, so a subclass in another
  module is outside it. The atlas therefore needs its own source-identity hashing, as
  `source_identity()` does at `bounded_comparison.py:409-419`.
- The statistical design (fixed end epoch vs fixed post-decision horizon; how the "wait" action is
  represented; twin recomputation policy) belongs to the counterfactual-statistics review and is
  not settled here.

## Caveats & Required Follow-ups

1. Treat every speed-up figure as a hypothesis until item 0 has run. Do not size a fleet from §2
   (memory rule: real-config GPU dry run before any fleet).
2. "Exact-records" is a claim checked against the rung-4 records on the **same SKU, driver and
   build**. A torch or CUDA upgrade voids the golden reference. `REPLAY_REFUSAL_KEYS` and
   `manifest.runtime` already refuse a mismatch, so keep that refusal.
3. Reusing the trunk suffix as the mandatory no-op instead of recomputing it, and the
   decision-point and horizon design, are pre-registration decisions for John (PDR-0053
   sketch-before-launch). They are not engineering defaults.
4. Nothing here edits `@semantic` code, the frozen rung-4 runner, or its validators. If a later
   change seems to need that, it is a new decision, not a refactor.
5. Sequence: do items 0 and 1 (measure, then the cheap win), then item 2 (fork core plus the golden
   test), then items 3 and 4, then items 5–7. Each later item is gated on the trajectory digests
   staying equal to the item before it.
