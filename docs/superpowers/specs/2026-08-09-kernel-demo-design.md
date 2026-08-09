# Kernel Demo — "Simic in 20 minutes"

**Date:** 2026-08-09 · **Status:** rev 4 (post-panel round 2), awaiting final verification
**Target:** `experiments/kernel_demo.py` (single file, plus optional plotting sidecar)
**Panel:** five SME reviews, two rounds, under `docs/superpowers/reviews/2026-08-09-kernel-demo-*`.
Round-2 verdicts: morpho 19/20 closed · lifecycle 7/9 + 1 reopened · reward 10/13 ·
stats 13/17 · determinism 15/19, 0 not-closed. Rev 4 folds in all accepted round-2
findings; dispositions noted inline as (R2: …).

## What this is — and is not

A single-file tech demo proving the substrate loop that Simic is built on:
telemetry → learned decision → structural injection → isolated pretrain →
automatic blend → end-state counterfactual reward. It is the minimum version
of esper-lite that proves the point, written fresh (zero imports from
`~/esper` or `~/esper-lite`), with esper-lite's proven mechanics inherited
by re-implementation.

It is deliberately **not Simic**: the seed menu is fixed and human-authored.
The demo proves the substrate loop and the counterfactual-fan supervision
economics, not generative morphogenesis. This caveat goes verbatim in the
file header.

**Claim scope.** The headline lift `R_chosen − R_noop` asserts *controller
skill*: a learned policy reading telemetry picks better interventions, **at
profitable moments**, than doing nothing — given this menu, this slot, this
host. (Scoped per R2: reward N1 — `J_now` learns "act now vs never," so the
demo may claim profitable timing; the stronger "*best* moment" claim is made
only if the WHEN-isolation null (below) is beaten.) No result may be quoted
as a growth-in-general claim.

**Intellectual role:** the fan store this demo produces is the
counterfactual atlas and proven substrate early Momir needs; Simic's next
move is replacing the four-way vocabulary with generated candidates.

**Claim demonstrated:** the inversion of the old Tamiyo regime ("hundreds of
random seeds, 3 slots, 6 types, good luck" — sparse bandit feedback in a
huge action space). Here: 1 slot, 4 seed types, full counterfactual labels
at every measured decision point.

## Scope pins (agreed, do not widen)

- One fixed host architecture. One fixed slot site. Exactly four seeds.
- No host families, no held-out-architecture tests, no universality claims.
- Aurelia's only authorities: **which** seed and **when**. Zero lifecycle
  knobs for her. All harness constants (λ, τ, stage durations, entropy
  temperatures, exploration schedule, thresholds) are fixed before
  collection, invisible to and untouchable by the policy.
- Reward is **end-state only**: no intermediate reward, no shaped terms.
  Entropy terms are policy regularizers, not reward.
- Telemetry provenance: `TelemetryRecord` is produced where it is measured
  (host/slot code); no Nissa abstraction in the demo.

## Determinism contract — Class 1, with a forbidden-relaxations list

Single machine, single GPU SKU, pinned environment, bitwise-deterministic
execution:

- `torch.use_deterministic_algorithms(True)`, `cudnn.deterministic=True`,
  `cudnn.benchmark=False`, `CUBLAS_WORKSPACE_CONFIG=:4096:8`; TF32 off
  (both flags), recorded. No AMP, no dropout, no gradient clipping.
- `attn` seed uses explicit-matmul attention (SDPA fused backwards would
  raise under deterministic mode).
- **RNG ownership rule (R2: determinism N1):** every random draw comes from
  an explicit, named `torch.Generator` (episode generator, arm-init
  generators, learner generator, refan generators), derived via
  `derive(...)`. `torch.manual_seed` is banned outside process startup.
  `derive(seed, label, i)` = SHA-256 of the concatenation, truncated to 64
  bits (R2: morpho low — derive() now specified).
- **Worker model: OS processes, one per worker** (R2: determinism trade,
  adopted). The no-loader design already dissolved the GIL argument —
  workers await CUDA either way — and processes remove the shared-RNG and
  shared-allocator risk classes outright. Cost: CIFAR resident per process
  (~180MB × workers), affordable. Each worker writes its own shard.
- **Forbidden relaxations (R2: determinism N7/L2):** disabling the twin
  arm, disabling deterministic algorithms, enabling TF32/benchmark/AMP,
  adding clipping or dropout, or running fans across devices **voids the
  Class 1 claim and the headline**. The list is printed by `--selftest`.
- Eval-time action selection is **deterministic** (threshold rule below);
  there is no sampling slot at eval (R2: determinism N5).
- Deterministic-mode slowdown measured once in pre-flight and recorded.

## System mechanics

### Host and task

- CIFAR-10; deliberately undersized 3-stage CNN (~150k params); checkable
  property: plateaus by epoch ~12–15 under the mild pathology.
- **Data partition:** train 50k; the 10k test set is split once by fixed
  seed into 5k **val** / 5k **test**. Val feeds telemetry and all
  training-time rewards; test is the only accuracy any *reported* metric
  uses. **Unit rule (R2: reward N4, stats R2-6): every reported argmax,
  ceiling, probe target, and agreement number is computed in test units;
  every training label in val units. Each gate and metric states its unit
  where defined.** `P(val-argmax = test-argmax)` is reported beside fan
  density — it is the measured cost of the unit wall.
- Dev runs may subset the training set behind a flag; headline runs use
  full data.

### Optimizer contract (constants now in-spec; R2: dynarch ask)

SGD + Nesterov momentum, **constant LR** (no scheduler → no scheduler state
in snapshots): host group `lr=0.05, μ=0.9, wd=5e-4`. Seed params join as a
second param group at germination: same LR, fresh momentum buffers,
**no-decay list: the scalar gain, all norm affines, all biases** (R2:
dynarch R2-F2 — weight decay on a small gain is a decay-toward-zero trap).
Param-group ordering and state restore byte-identical across arms.

### Pathology sampler

| Pathology | Telemetry signature | Fan winner (by design) |
|---|---|---|
| Under-normalized | spiky grad norms, activation saturation | norm |
| Channel-starved | early plateau, high train-loss floor | conv-heavy |
| No spatial mixing (1×1 stage 2) | class-confusion spread | attn |
| Mild handicap | clean curves | conv-light or **no-op** |

The design-intent winner map is verified in pre-flight gate 2b (test
units), not assumed.

**Blindness rule:** every `TelemetryRecord` field is a deterministic
function of host state and logical epoch index; wall-clock, durations,
device/worker identity, and `pathology_id` are absent from the dataclass by
construction. `--selftest` greps the telemetry path.
**Finiteness (R2: morpho F10, now closed):** `TelemetryRecord` construction
asserts all fields finite; a non-finite field marks the run diverged at
that epoch (status recorded) — never a silent `inf` into the normalizer.

**Freeze discipline:** seeds namespaced by construction —
`derive(run_seed, ns, i)`, `ns ∈ {dev, preflight, train, tune, eval}`. The
**frozen block** is enumerated exhaustively (R2: reward N8): pathology
definitions, telemetry normalizer, entropy temperatures, exploration
schedule, λ, τ, stage durations K/M/F, horizon, decision window, optimizer
constants, diverged-arm convention, all pass thresholds. Its hash is
recorded; `--eval` asserts it. Pre-flight retune iterations are themselves
logged to the store with an iteration counter — the tuning process is a
recorded selection process, not an invisible one (R2: stats R2-7).

### Seeds — the delta contract

```
h' = h + α · Δ( lerp(h.detach(), h, β) )        Δ = g · f(h)
```

**Init contract (R2: dynarch R2-F1 — zero-init `g` reopened F3 as an
architecture-selective bootstrap deadlock: with g=0 the inner module gets
exactly zero gradient, and `norm`'s f₀ is already the right correction
while conv/attn f₀ are random, so arms wake at architecture-dependent
rates):** **τ-init** — `g = τ·RMS(h)/RMS(f₀)` measured on one fixed batch
at germination, τ one shared harness constant (default 0.05), so every arm
enters TRAINING at the same `RMS(Δ)/RMS(h) = τ` with a live gradient path.
Invisibility is already guaranteed by STE for any Δ; zero-init bought
nothing. **Only the gain carries τ-init**: internal projections are
standard-init, final BN γ=1 — no nested zeros (answers dynarch Q2).

| Seed | Δ(h) | Internal norm | ~Params |
|---|---|---|---|
| `norm` | `g · (GroupNorm(h) − h)` | GN is the content | 0.1k |
| `attn` | `g · Attn(h)` (explicit matmuls) | LN on attn input | 5k |
| `conv_light` | `g · DWSepConv(h)` | BN inside | 10k |
| `conv_heavy` | `g · ResBlock(h)` | BN inside | 60k |

### Lifecycle (fixed FSM)

`DORMANT → GERMINATED → TRAINING → BLENDING → FOSSILIZING → FOSSILIZED`,
transitions once per epoch; α gates forward contribution, β gates gradient
coupling; both are harness schedules.

- **TRAINING** (K=3 epochs): α=0 via STE `h + (Δ − Δ.detach())`; Δ receives
  full task gradients; trust-region term `λ·‖Δ‖²/‖h‖².detach()` (output
  norms) added to the seed's loss. Stationary point
  `Δ* = −(∂L/∂Δ)·‖h‖²/(2λ)` (R2: dynarch R2-F5 — formula corrected, and
  the loss-gradient symbol no longer collides with the gain `g`).
- **BLENDING** (M=3 epochs): α cosine, per optimizer step,
  `p=(step+1)/total`. β=0.
- **FOSSILIZING** (F=2 epochs): α=1; **β cosine** 0→1 (R2: dynarch R2-F6 —
  same waveform as α; the ramp is the *sole* fossilization mitigation
  under SGD-without-clipping and is named as such single point of failure;
  the α/β plot makes a ramp failure visible).
- **FOSSILIZED:** α=1, β=1; joint training.

SGD note (R2: dynarch, confirming): the α ramp genuinely gates Δ's
effective learning rate under SGD (no preconditioner to absorb it), and
2 fossilizing epochs are ample (momentum carryover ≈ 10 steps).

### Action space — factored head, deployment rule stated

```
transformer trunk
    ├── NOW logit  p(s_t)      trained "act now vs never" (pointwise)
    └── 4 seed logits π(a|s)   conditional on acting; a ∈ 4 seeds only
```

**Deployment rule (R2: stats R2-1, reward N1, morpho N1 — previously
unstated, and both naive readings fail):** at eval the policy is queried
**only inside the trained decision window (epochs 5–15)** (R2: reward N7 —
outside it p is pure extrapolation) and **germinates at the first epoch
where p > 0.5, deterministically**. This is an earliest-profitable-moment
rule by construction — `J_now` is linear in p, so it learns a per-epoch
threshold on sign(A), not a stopping rule; nothing compares t to t′. That
limitation is stated, measured (below), and the timing claim is scoped to
it. Realized germination rate is printed beside every lift number (R2:
stats R2-1/R2-2 interaction).

## Telemetry and policy

Per-epoch `TelemetryRecord` dataclass (missing field = construction error);
per-feature **median/IQR normalizer** fitted on pre-flight episodes, frozen
in the frozen block. Small MLP embeds each normalized record into a
d_model≈64 token; causal transformer (2 layers, ~100k params); factored
head. One trunk.

**Total training loss, stated (R2: morpho N5, reward N6):**

```
maximize  J_which + J_now + β_which·H(π) + β_now·H(p)
J_which = Σ_{a∈4} π(a|s) · R_a^val
J_now   = p·( Σ_{a∈4} sg[π(a|s)] · R_a^val ) + (1−p)·R_noop^val
```

`sg[·]` = stop-gradient: π inside `J_now` is detached, so WHICH trains at
1× regardless of p and the frozen entropy calibration cannot drift.
**Temperatures** (R2: reward N5): β_now is a temperature on the advantage —
set by target confidence, `β_now = fan_density/2.2` (p≈0.9 at one fan
density); `β_which = 0.2 × fan_density`. Both from measured pre-flight fan
density, both frozen. Report includes realized p split by sign(A) — the
diagnostic that catches entropy manufacturing action, which
restraint-rate-beside-coefficient would miss.

## Episodes, the common future, and the fan

**Common future drawn once per episode** (batch order + augmentation
decisions, from the episode generator, independent of model RNG). The
**base run is the no-op arm**. Fans at different epochs share one
baseline.

**Collection is schedule-driven:** the exploration schedule draws **exactly
2 ordered fan epochs per episode** from the decision window (R2: reward
N1b — every episode now yields a paired now-vs-later comparison; "1–2" is
gone). The policy never gates its own data.

**The fan, at scheduled epoch t:**

1. Snapshot: deep-copied host `state_dict()` (params AND buffers),
   optimizer state, CPU + per-device CUDA RNG, data position.
2. Branch arms, all through the one branch executor (no privileged path):
   **4 seed arms + twin**. The **twin arm** re-runs the no-op continuation
   and must match the base-run tail **bitwise, checked as a per-epoch
   host-state hash** — an abort names the first differing epoch, emits a
   divergence report, and prior shards remain valid (R2: determinism N4).
   The twin is **non-optional** (forbidden-relaxations list): it is the
   only thing standing between the base-run-as-no-op optimization and a
   silent code-path asymmetry in the headline.
3. **Null-seed arm on a 1-in-10 subsample + `--selftest`** (R2: dynarch
   R2-F4): a real second param group with the gain frozen at 0, Δ≡0, must
   reproduce the base run bitwise through the whole horizon — exercises
   group-append ordering, seed-group momentum isolation, α/β machinery,
   and per-arm init RNG, which the twin (single-group) cannot.
4. Arm seed modules init from `derive(episode_seed, arm_name)` via their
   own generators. **`host_init_hash` recorded per episode** (R2:
   determinism N1 — makes a seed/init mismatch loud).
5. All arms of one fan on one device; parallelism across episodes.
6. Host weights asserted bitwise identical across arms at end of TRAINING,
   **conditioned on arm finiteness** — a non-finite Δ makes `Δ − Δ.detach()`
   NaN, which is arm divergence (status), not a harness abort (R2: morpho
   N3).
7. Arms run to the horizon. `R_a^val` (training) and `R_a^test`
   (reporting) = mean accuracy over the final 3 epochs, each on its own
   partition.
8. **Diverged-arm convention, pre-registered (R2: reward N3, stats R2-3):**
   a diverged arm scores **chance accuracy, 0.10**, in both objectives and
   every argmax, with `status="diverged"` and curves kept to failure.
   *Rationale, recorded:* this is measurement, not penalty — the end-state
   accuracy of a destroyed classifier is chance. Rejected: last-finite-
   epoch (scores the spike-then-crash arm at its spike — the exact
   anti-pattern the demo exists to expose); `R_noop` (hides catastrophe —
   a seed that wins big and destroys the host 15% of the time must not be
   scored as noop-neutral on failures); drop-and-renormalize (makes
   divergence invisible to the policy); null→0.0 (the founding
   silent-default defect). Failure rates reported per seed type.

**Fan record:** dataclass-serialized JSONL with `schema_version` (R2:
morpho F7 residual), `kind ∈ {fan, refan, policy_run, preflight_iter}`
(each defined where used; `policy_run` = an eval live episode: telemetry,
decisions, germination epoch, `R^test`, status), `episode_seed`,
`seed_namespace`, `split_role`, `pathology_id`, `fan_epoch`,
`schedule_id`, `policy_checkpoint_id`, `config_hash`, `frozen_block_hash`,
`common_future_hash`, `host_init_hash`, env block (versions, GPU,
TF32 flags, **worker_count, device_index** — R2: determinism N2: cuDNN
algorithm choice is workspace-pressure-dependent within a card; the twin
passes under collection pressure while `--replay` fails without this),
per-arm `{name, init_seed, status, R_val, R_test, curve}`, telemetry
context. Append-only; failures and no-op wins kept. Non-finite → `null` +
status in JSON, never bare NaN.

**Refans (R2: determinism N3, stats R2-4):** `kind="refan"`, future
re-drawn via `derive(episode_seed, "refan", k)` with `k` recorded,
**5 real arms including a fresh no-op continuation under the new future**
(the base-run tail is not a valid comparand under a different future, and
the twin would abort by construction unless re-based). Excluded from
training.

**Store:** per-worker shards, canonical merge sorted by
`(episode_seed, fan_epoch)`; learner input is content-ordered.
**Replay:** `--replay <fan_id>` re-derives under the recorded config,
**single-worker** (R2: determinism N2), env-block mismatch refuses.

## Learning: fully offline, full information

Collection online under the schedule; learning offline; the trained policy
acts live only at eval, under the stated deployment rule.

- Loader asserts `split_role="train"` on every gradient record; refans and
  eval records never train.
- **Train/tune split (R2: morpho N2):** the train namespace splits 80/20
  **by episode** into `train`/`tune`. Checkpoint selection on tune
  (`J_which + J_now` on tune fans); the learning curve is reported, so
  "overfit 450 fans" is diagnosable and distinguishable from "the approach
  doesn't work." Collection defaults to 300 episodes (= 600 fans); it may
  be extended on tune-curve evidence, but only before any eval-namespace
  episode runs.

## Pre-flight validation (gates → freeze → collection)

~30 preflight-namespace episodes under the schedule. **Unit of analysis:
episode — where an episode has two fans, gate statistics use the first
scheduled fan only** (R2: morpho N8, reward N9 — within-episode fans share
a base run). Gates, each stating its remedy (R2: dynarch R2-F3 — a failed
gate names what may be retuned; gate 5's remedy is never the sampler):

1. **No-op wins vs the exact null** — binomial vs 20%: above in mild,
   below in the three targeted pathologies. *Remedy: sampler.*
2. **Signal at the right target** — (a) linear probe telemetry →
   pathology, GroupShuffleSplit by episode; (b) probe telemetry →
   **test-argmax** vs majority-class null, plus realized
   pathology × test-argmax contingency vs the design map. *Remedy:
   sampler.*
3. **Contrast beats noise** — fan density `mean(R_best − R_second)` and
   `mean(R_best − R_noop)` within fans (test units), vs the refan noise
   floor. *Remedy: averaging window, horizon.*
4. **No degenerate dominance** — no seed is test-argmax in >40% of fans
   overall, nor a majority in every pathology. *Remedy: sampler/menu
   balance.*
5. **Magnitude sanity** — `RMS(Δ)/RMS(h)` at blend entry within ~2× band
   across arms. *Remedy: τ, λ, seed LR — never the sampler.*
6. **Horizon adequacy** — fan density per scheduled epoch does not
   collapse with t. *Remedy: horizon, window.*
7. **Now-vs-later materiality (R2: reward N1b):** from the paired ordered
   fans, report `P(A(t_late) > A(t_early))` and the mean gap. This decides
   whether the earliest-profitable deployment rule leaves measurable value
   behind — informing the fixed-epoch-null interpretation, not a
   pass/fail gate.

Then the frozen block locks (hash recorded) and collection starts.

## Evaluation protocol

Frozen battery, fixed before any eval run:

- `N_eval = 100` eval-namespace seeds shared by every policy: **trained,
  random, schedule-only, and fixed-epoch** (R2: morpho N1 — the
  fixed-epoch null is the trained WHICH head with germination forced at
  the pre-registered mid-window epoch t*=10, same seeds, no retraining;
  `trained_live_lift − fixed_epoch_lift` **is** the WHEN contribution, and
  the "better moments" claim is made only if it is positive).
- **Lift:** per-episode `R_chosen^test − R_noop^test`, paired by seed.
  Never-germinating scores exactly 0. **Statistic: one-sided sign-flip
  permutation test on the mean per-episode lift** (R2: stats R2-2, morpho
  N7 — Wilcoxon's zero-drop silently converts the estimand to
  conditional-on-acting; the permutation test keeps zeros in and the
  estimand is the unconditional lift actually claimed). Realized
  germination rate printed beside every p-value.
- **Agreement & money chart:** frozen `(episode_seed, fan_epoch)` grid,
  teacher-forced queries, ground truth = **test-argmax**. Nulls:
  majority-class rate and schedule-only. The policy's chosen-seed marginal
  is reported next to the money chart (R2: stats R2-9).
- **Restraint quality:** regret vs fan-optimal-with-no-op, **reported at
  the last grid point** where "wait" and "never" coincide; per-point
  regret shown separately, labeled as containing option value (R2: reward
  N2).
- **Oracle ceiling — context, not threshold (R2: stats Part 2 + R2-5,
  reward N4):** ~30 eval-grid points refanned, **test units**; two-draw
  self-agreement reported **labeled as the Σp² lower bound of the true
  ceiling (max pᵢ)** with its Wilson interval. It appears in no pass
  threshold: at n=30 its CI is wide enough to flip a verdict, and Σp²
  understates the ceiling by up to ~27% — an anti-conservative
  denominator. The agreement gate stands on the majority-class null alone.
- **Falsifier:** telemetry histories swapped **as a derangement across
  pathology classes** (R2: morpho N6 — unrestricted swaps are
  same-pathology ~25% of the time and preserve the signal). Diagonal
  surviving the falsifier = the demo claim fails honestly.

## Pre-registered numbers (locked at freeze)

- Horizon **40** (window 5–15, K=3, M=3, F=2, ≥15 full-influence epochs);
  200-epoch flag exploratory only.
- Collection 300 train-namespace episodes (extendable pre-eval on tune
  evidence only); `N_eval=100`, evaluated once, no peeking, no augmenting.
- Diverged-arm convention 0.10; sign-flip permutation, 10k resamples,
  one-sided, α=0.05.
- Thresholds: trained lift > 0 (permutation p<0.05) **and** > schedule-only
  (paired, same test); conditional-on-acting agreement ≥ majority-class
  null + 15 points (test units); money chart row-argmax = designed winner
  for ≥3 of 4 pathologies (exact α=5.08% under the uniform null — the
  chosen-seed marginal is reported so a skewed marginal is visible);
  falsifier collapses the diagonal to within the null's CI.
- The WHEN contribution (`live − fixed_epoch`) has **no pass threshold**:
  it is reported, and it gates only the wording of the timing claim.

## Report (`--report`)

Lift table (trained / random / schedule-only / fixed-epoch) with
germination rates; agreement vs nulls (+ ceiling as labeled context);
money chart + falsifier twin + chosen-seed marginal; per-pathology arm
curves incl. ≥1 spike-then-crash; α/β trajectories; `RMS(Δ)/RMS(h)` at
blend entry; fan density + `P(val-argmax = test-argmax)`; per-seed arm
failure rates; restraint regret (last-grid-point + labeled per-point);
realized p split by sign(A); tune learning curve; entropy temperatures in
force; deterministic-mode cost. Refuses mixed namespaces.

## Engineering

- **File:** `experiments/kernel_demo.py`, target ≲1200 lines, torch +
  torchvision only, narrative order. Plotting sidecar optional.
- **Modes:** `--selftest` (twin + null-seed smoke episode, blindness grep,
  split assertions, JSON round-trip incl. non-finite, forbidden-
  relaxations printout), `--preflight`, `--collect`, `--train`, `--eval`,
  `--report`, `--replay <fan_id>`.
- **Data path:** GPU-resident CIFAR-10 per worker process, on-GPU
  augmentation from precomputed decisions; no DataLoader.
- **Runtime:** both 4060 Tis; process workers, several per card; fans
  never span devices. 300 collection episodes (2 fans each: base + 2×5
  branch arms ≈ 11 lifecycle runs/episode) fit overnight with margin.

## Success criteria for the demo itself

- A reader can open the one file and follow the whole loop top-to-bottom.
- `--selftest` passes; pre-flight gates 1–6 pass with gate 7 and the
  refan floor reported.
- The pre-registered thresholds are met on the frozen battery, including
  schedule-only; the falsifier collapses; the WHEN contribution is
  reported with the timing claim worded accordingly.
- At least one spike-then-crash arm plot (and note the diverged-arm
  convention exists precisely because such arms sometimes finish the job).
