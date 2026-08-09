# Kernel Demo — "Simic in 20 minutes"

**Date:** 2026-08-09 · **Status:** rev 6.1 — **LOCKED** (rev 6 owner-approved; panel round 3 verified; external-review patches folded. Rev 6.1, 2026-08-10, owner-approved **pre-data amendment** — no store exists, so the change is statistically free: the money-chart permutation null and the falsifier CI are computed at the **episode** level, not the grid-point level; see the pre-registered numbers section). Design: APPROVE. Implementation: GO.
**Target:** `experiments/kernel_demo.py` (single file, plus optional plotting sidecar)
**Panel:** five SME reviews, two rounds, under `docs/superpowers/reviews/2026-08-09-kernel-demo-*`.
Round-2 verdicts: morpho 19/20 closed · lifecycle 7/9 + 1 reopened · reward 10/13 ·
stats 13/17 · determinism 15/19, 0 not-closed. Round-3 (verification) verdicts:
morpho 17/18 · lifecycle 6/6 ("design done") · reward 9/9 (+N3 conceded) ·
stats 8/9 (+1 regression, fixed below) · determinism 6/7 (+1 compose defect,
fixed below). Dispositions noted inline as (R2: …) / (R3: …).

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
- **Data partition:** train **45k**; **val = 5k held out of the official
  train split**; **test = the official 10k, untouched** (rev 6, external
  review: val and test no longer share a partition, and the reported
  metrics get the full 10k's noise floor). Val feeds telemetry and all
  training-time rewards. **Unit rule, absolute (rev 6 — the previous
  gate-list form leaked through gates 3/6, whose window/horizon remedies
  are frozen-block constants and can fit the report partition exactly as
  the sampler can): anything whose result is allowed to change the frozen
  block reads val; test is unread until after freeze.** Everything
  reported at eval is computed in test units. The val-noise inflation
  this puts in pre-flight probes is second-order (thresholds are
  majority-null-based) and bounded by `P(val-argmax = test-argmax)`,
  reported beside fan density as the measured cost of the unit wall.
- Dev runs may subset the training set behind a flag; headline runs use
  full data.

### Optimizer contract (constants now in-spec; R2: dynarch ask)

SGD + Nesterov momentum, **constant LR**: host group
`lr=0.05, μ=0.9, wd=5e-4`. Constant LR is load-bearing twice over (R3:
dynarch): no scheduler state in snapshots, and — the bigger half —
`lr_scheduler` captures `base_lrs` positionally at construction, so a param
group appended at germination would raise or silently mismatch LRs; constant
LR removes that positional-state bug class structurally rather than by
discipline. Cost (no annealing → noisier end-state) is gated by gate 3. Seed params join as a
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
| Mild handicap | clean curves | conv-light (WHICH); **no-op often wins (NOW)** |

The mild row carries two targets on purpose (rev 6, external review:
no-op belongs to NOW, not WHICH): its designed *seed* winner,
conditional on acting, is **conv-light** — that is what the money chart's
≥3-of-4 criterion scores — while "no-op frequently beats every seed here"
is the NOW-side property that gate 1 checks and the restraint metrics
measure. The design-intent winner map is verified in pre-flight gate 2b
(val units), not assumed.

**Blindness rule:** every `TelemetryRecord` field is a deterministic
function of host state and logical epoch index; wall-clock, durations,
device/worker identity, and `pathology_id` are absent from the dataclass by
construction. `--selftest` greps the telemetry path.
**Finiteness (R2: morpho F10, now closed):** `TelemetryRecord` construction
asserts all fields finite; a non-finite field marks the run diverged at
that epoch (status recorded) — never a silent `inf` into the normalizer.

**Freeze discipline:** seeds namespaced by construction —
`derive(run_seed, ns, i)`, `ns ∈ {dev, preflight, train, eval}`; `tune` is
an 80/20 partition *within* the train namespace, recorded per record in
`split_role`, not a namespace of its own (R3: morpho — the two readings
previously coexisted and the loader assertion needs exactly one). The
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
rates):** **τ-init** — `g = τ·RMS(h)/RMS(f₀ + ε)` measured on one fixed
batch at germination **under `eval()`/no-grad** (a training-mode pass would
update host BN stats per arm and trip the cross-arm assertion; R3: morpho),
τ one shared harness constant (default 0.05), ε a floor on the denominator
with `g` logged at germination (R3: dynarch R3-1 — a small `RMS(f₀)` would
present as an inflated `norm` failure rate, an init-guard bug wearing a
result's clothes). Every arm enters TRAINING at the same
`RMS(Δ)/RMS(h) = τ` with a live gradient path.
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
  norms) added to the seed's loss. **λ = 1.0**, comfortably inside the
  stability bound λ < 1/lr_seed ≈ 20 at the τ-init operating point (R3:
  dynarch R3-2); gate 5 is the instrument that retunes it if needed. Stationary point
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
   divergence report, prior shards remain valid, and **halts all workers**,
   not just its own: a twin divergence means deterministic mode is not
   holding, so sibling records are equally suspect (R2: determinism N4;
   R3: determinism LOW).
   The twin is **non-optional** (forbidden-relaxations list): it is the
   only thing standing between the base-run-as-no-op optimization and a
   silent code-path asymmetry in the headline.
3. **Null-seed arm on a 1-in-10 subsample + `--selftest`** (R2: dynarch
   R2-F4): a real second param group with the gain frozen at 0, Δ≡0, must
   reproduce the base run bitwise through the whole horizon — exercises
   group-append ordering, seed-group momentum isolation, α/β machinery,
   and per-arm init RNG, which the twin (single-group) cannot.
   **Pre-stated contingency (rev 6, external review): the null-seed
   bitwise claim is empirical** — Δ≡0 still executes kernels the base run
   doesn't, and signed-zero/STE-add edge cases exist. If `--selftest`
   trips the null-seed check *while the twin holds*, the remedy is
   value-exact (zero-normalized-hash) comparison for the null-seed arm
   only; the twin's bitwise requirement is untouched.
4. Arm seed modules init from `derive(episode_seed, arm_name)` via their
   own generators. **`host_init_hash` recorded per episode.** Its
   justification under process workers (R3: determinism): it is the
   **replay localiser** — the one field separating "diverged at seeding"
   from "diverged at kernel selection" — not a threading guard; do not
   delete it as one. **Within a worker, a fan's arms run sequentially**,
   keeping within-fan memory pressure close to the base run's (R3:
   determinism — this underwrites the twin and null-seed assertions).
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
TF32 flags, worker_count, device_index — the latter two are **provenance
only, excluded from the replay refusal key**: R3 determinism caught that
worker_count-in-the-key plus single-worker replay composed into a deadlock
where every real record refuses to replay. Whether memory pressure moves
cuDNN algorithm selection at this model size is *measured*, not assumed:
pre-flight runs the twin at 1 worker vs full count on one episode seed; if
it diverges, Class 1 is re-scoped to "bitwise at fixed worker_count" and
`--replay` runs at the recorded count — the contingency is pre-stated so
the finding cannot force an unrecorded scope change),
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
single-worker by default (at the recorded worker_count if the pressure
test re-scoped Class 1), env-block mismatch refuses. `config_hash` covers
the host architecture definition and `derive()` itself (R3: determinism —
both are plausible mid-development edits sitting outside the frozen
block).

## Learning: fully offline, full information

Collection online under the schedule; learning offline; the trained policy
acts live only at eval, under the stated deployment rule.

- Loader asserts `split_role="train"` on every gradient record; refans and
  eval records never train.
- **Loop ordering (R3: reward N10):** `J_which` trains alone as a warm-up
  before `J_now` is enabled. A diverged arm sits ~60× fan density below
  healthy, so early uniform π gives A ≈ −0.15 and p = σ(−33), whose
  `p(1−p)` gradient factor is machine zero — the NOW head would start
  frozen. Warm-up lets π learn divergence-avoidance first; pure ordering,
  offline, replayable, no new constant.
- **Train/tune split (R2: morpho N2):** the train namespace splits 80/20
  **by episode** into `train`/`tune`. Checkpoint selection on tune
  (`J_which + J_now` on tune fans); the learning curve is reported, so
  "overfit 450 fans" is diagnosable and distinguishable from "the approach
  doesn't work." Collection defaults to 300 episodes (= 600 fans); it may
  be extended on tune-curve evidence, but only before any eval-namespace
  episode runs. **The pre-stated levers for a bad tune curve are both
  directions: extend collection, or shrink the trunk** (rev 6, external
  review — ~480 training fans against a ~100k-param trunk; a smaller
  policy is a legitimate remedy and pre-stating it keeps the choice out
  of post-hoc territory).

## Pre-flight validation (gates → freeze → collection)

~30 preflight-namespace episodes under the schedule. **Unit of analysis:
episode — where an episode has two fans, gate statistics use the first
scheduled fan only** (R2: morpho N8, reward N9 — within-episode fans share
a base run). Gates, each stating its remedy (R2: dynarch R2-F3 — a failed
gate names what may be retuned; gate 5's remedy is never the sampler):

1. **No-op wins where designed — an engineering sanity check, not
   inference** (rev 6, external review: at ~7–8 episodes per pathology a
   binomial test against 20% cannot reject downward at α=0.05 even on
   zero wins; headline-scale statistics are not spent on a sampler
   shakedown). Empirical thresholds, pre-stated: no-op is the fan
   val-argmax in ≥2 mild episodes, and is the *modal* winner in no
   targeted pathology. *Remedy: sampler.*
2. **Signal at the right target** — (a) linear probe telemetry →
   pathology, GroupShuffleSplit by episode; (b) probe telemetry →
   **val-argmax** vs majority-class null, plus realized
   pathology × val-argmax contingency vs the design map (val units per the
   corrected unit rule — this gate's remedy is the sampler). *Remedy:
   sampler.*
3. **Contrast beats noise** — fan density `mean(R_best − R_second)` and
   `mean(R_best − R_noop)` within fans (**val units** — this gate's
   remedies are frozen-block constants, so the absolute unit rule
   applies), vs the refan noise floor. *Remedy: averaging window,
   horizon.*
4. **No degenerate dominance** — no seed is val-argmax in >40% of fans
   overall, nor a majority in every pathology (val units — sampler
   remedy). *Remedy: sampler/menu balance.*
5. **Magnitude sanity** — `RMS(Δ)/RMS(h)` at blend entry within ~2× band
   across arms. *Remedy: τ, λ, seed LR — never the sampler.*
6. **Horizon adequacy** — fan density per scheduled epoch does not
   collapse with t (**val units**, same reason as gate 3). *Remedy:
   horizon, window.*
7. **Now-vs-later materiality (R2: reward N1b):** from the paired ordered
   fans, report `P(A(t_late) > A(t_early))` and the mean gap. This decides
   whether the earliest-profitable deployment rule leaves measurable value
   behind — informing the fixed-epoch-null interpretation, not a
   pass/fail gate.
8. **Worker-pressure test (R3: determinism):** twin arm at 1 worker vs
   full worker count, same episode seed. Pass → worker_count is pure
   provenance. Fail → the pre-stated contingency: Class 1 re-scoped to
   fixed worker_count, `--replay` at recorded count. ~20 minutes; also
   underwrites the twin's and null-seed arm's own assertions.

Then the frozen block locks (hash recorded) and collection starts.

## Evaluation protocol

Frozen battery, fixed before any eval run:

- `N_eval = 100` eval-namespace seeds shared by every policy: **trained,
  random, schedule-only, and fixed-epoch**. **Constitutional definitions
  (rev 6, external review — the comparators are load-bearing and may not
  be inherited from review threads):**
  - **schedule-only** — the strongest boring null: identical
    architecture, training data, objective, and training procedure to the
    trained policy, with input telemetry **masked to the logical epoch
    index only**. It answers: does telemetry add anything beyond learning
    when these canned pathologies tend to pay off?
  - **random** — germinates at one epoch drawn uniformly from the
    decision window (from `derive(episode_seed, "random-null")`), seed
    chosen uniformly over the four; always acts.
  - **fixed-epoch** — the trained WHICH head with germination forced at
    the pre-registered mid-window epoch t*=10, same seeds, no retraining
    (R2: morpho N1).
  - The **exploration schedule** itself is likewise pinned: 2 epochs
    drawn uniformly without replacement from the decision window, ordered.
  **The WHEN contrast `trained_live − fixed_epoch` is reported twice (R3:
  stats, morpho note): unrestricted, and restricted to episodes where
  trained-live germinated.** The unrestricted version confounds timing
  with restraint (fixed-epoch always acts; the confound inflates exactly
  when restraint has value); the timing claim is worded off the
  restricted version, with the germination rate beside it. **One further
  scoping sentence (rev 6, external review): the restricted contrast
  bundles timing with time-conditional seed choice** — germinating at
  epoch 7 may also mean choosing a different seed than the t*=10 query
  would — so the claim it supports is "chooses profitable moments,
  including what to plant at them," not timing in isolation.
- **Lift:** per-episode `R_chosen^test − R_noop^test`, paired by seed.
  Never-germinating scores exactly 0. **Statistic: one-sided sign-flip
  permutation test on the mean per-episode lift** (R2: stats R2-2, morpho
  N7 — Wilcoxon's zero-drop silently converts the estimand to
  conditional-on-acting; the permutation test keeps zeros in and the
  estimand is the unconditional lift actually claimed). Realized
  germination rate printed beside every p-value.
- **Agreement & money chart:** frozen `(episode_seed, fan_epoch)` grid —
  **fan epochs drawn from the same distribution as the exploration
  schedule** (from the eval seeds), so teacher-forced agreement is
  measured on the training state distribution (R3: morpho N16, the one
  open round-2 item). **Grid size pre-registered: 2 points per eval
  episode = 200 points.** Teacher-forced queries, ground truth =
  **test-argmax over the four seed arms** (rev 6, external review — the
  argmax set is pinned: restraint is NOW's job and is measured by the
  restraint metrics, so the WHICH head is never scored against a
  no-op-winning fan it structurally cannot match; this also gives the
  mild row its single designed winner). Nulls: majority-class rate and
  schedule-only. Reported
  next to the money chart: the policy's chosen-seed marginal (R2: stats
  R2-9) and a companion chart with diverged fans excluded (R3: stats —
  shows whether the diagonal is driven by diagnosis or by
  divergence-avoidance).
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
  for ≥3 of 4 pathologies, judged against a **permutation null** (rev 6,
  external review: the exact 13/256 = 5.08% figure assumes a uniform 25%
  per row and dies the moment the policy's seed marginal skews — instead,
  pathology labels are shuffled, row winners recomputed, and the ≥3-of-4
  statistic compared to that empirical null, which preserves whatever
  marginal Aurelia actually has; the uniform figure is kept only as a
  footnote). **Rev 6.1 (pre-data amendment, 2026-08-10):** the shuffle
  unit is the **episode**, not the grid fan — pathology is an
  episode-level attribute and the two grid fans of one episode carry
  correlated picks, so labels move across episodes with both fans
  travelling together; the rev-6 point-level wording built a null with up
  to 2× too little variance (money p biased low, and the gate could pass
  on miscalibration). Falsifier collapses the diagonal to within the
  null's CI; **rev 6.1:** that Wilson CI is computed at the episode count
  (N_eval), not the grid-point count (2·N_eval), for the same clustering
  reason — the point-count CI was too tight and the falsifier could
  honestly fail on miscalibration alone.
- **Power note, written at freeze (rev 6, external review):** using gate
  3's measured fan density, record the minimum detectable effect for the
  lift test at N_eval=100 (≈25% of episodes mild, near-zero lift by
  design) and for the agreement gate at the episode count (rev 6.1: the
  200 grid points cluster 2-per-episode, so N_eval=100 bounds the
  independent information; the SD anchor is gate 3's paired refan noise
  floor, a gate-3 measurement). A miss then
  reads "underpowered below X" or "the approach failed" — not an
  uninterpretable p=0.08. One paragraph, effect-size input free from
  gate 3.
- The WHEN contribution (`live − fixed_epoch`) has **no pass threshold**:
  it is reported, and it gates only the wording of the timing claim.

## Report (`--report`)

Lift table (trained / random / schedule-only / fixed-epoch) with
germination rates; agreement vs nulls (+ ceiling as labeled context);
money chart + falsifier twin + chosen-seed marginal + diverged-excluded
companion; per-pathology arm curves incl. ≥1 spike-then-crash; α/β
trajectories; `RMS(Δ)/RMS(h)` at blend entry + `g` at germination;
fan density + `P(val-argmax = test-argmax)`; per-seed arm failure rates
**with observed end-state accuracy of diverged arms printed beside the
0.10 convention** (R3: reward — the convention is a measurement claim, so
the measurement is shown); restraint regret (last-grid-point + labeled
per-point);
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
