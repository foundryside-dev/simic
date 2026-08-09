# Kernel Demo — "Simic in 20 minutes"

**Date:** 2026-08-09 · **Status:** rev 3 (post-panel), awaiting panel re-review
**Target:** `experiments/kernel_demo.py` (single file, plus optional plotting sidecar)
**Panel round 1:** five SME reviews under `docs/superpowers/reviews/2026-08-09-kernel-demo-*`
(morphogenesis, lifecycle, reward, statistics, determinism). Rev 3 incorporates
their accepted findings; the disposition of each is noted inline as (closes: …).

## What this is — and is not

A single-file tech demo proving the substrate loop that Simic is built on:
telemetry → learned decision → structural injection → isolated pretrain →
automatic blend → end-state counterfactual reward. It is the minimum version
of esper-lite that proves the point, written fresh (zero imports from
`~/esper` or `~/esper-lite` — those are the incarnations being rebooted),
with esper-lite's *proven mechanics* inherited by re-implementation.

It is deliberately **not Simic**: the seed menu is fixed and human-authored,
which is exactly what Simic proper rejects (generation from live host state).
The demo proves the substrate loop and the counterfactual-fan supervision
economics, not generative morphogenesis. This caveat goes verbatim in the
file header.

**Claim scope (closes: morpho Part 4).** The headline lift `R_chosen − R_noop`
asserts *controller skill*: that a learned policy reading telemetry picks
better interventions, at better moments, than doing nothing — **given this
menu, this slot, this host**. It does not assert that structural growth in
general is worthwhile, and no result from this demo may be quoted as a
growth-value claim.

**Intellectual role:** the demo establishes that a transformer can infer
intervention value from host telemetry when trained with dense matched
counterfactual fans, while keeping the intervention language human-authored.
Its output — the fan store — is exactly the counterfactual atlas and proven
substrate that early Momir needs; Simic's next move is replacing the
four-way seed vocabulary with generated candidates.

**The claim demonstrated** is the inversion of the old Tamiyo regime.
Esper's controller got "hundreds of random seeds, 3 slots, 6 types, good
luck" — sparse bandit feedback in a huge action space. Here: **1 slot, 4
seed types, full counterfactual labels at every measured decision point.**
Dense signal in a tiny action space is enough for a learned controller to do
genuine diagnosis: read telemetry, identify the host's deficiency, inject
the right structure at the right time, and be scored against every
alternative including doing nothing.

## Scope pins (agreed, do not widen)

- One fixed host architecture. One fixed slot site. Exactly four seeds.
- No host families, no held-out-architecture tests, no universality claims.
- Aurelia's only authorities: **which** seed and **when**. The lifecycle has
  zero knobs for her — one blend waveform, one speed, fixed stage durations.
  All harness constants introduced by this rev (λ trust-region, β-ramp
  length, entropy coefficients, exploration schedule) are **harness
  properties fixed before collection**, invisible to and untouchable by the
  policy — the pin holds.
- Reward is **end-state only**. No intermediate reward, no shaping terms, no
  progress bonuses (reward shaping is what killed Esper; the demo carries
  zero shaped terms by constitution). Entropy regularization is a policy
  regularizer, not a reward term (closes: morpho F14 wording).
- Telemetry provenance: measurements originate at the host/slot code and the
  demo builds no Nissa abstraction — the `TelemetryRecord` is produced where
  it is measured. (In Simic proper, Nissa authors the observation; the demo
  does not model that layer.)

## Determinism contract (closes: determinism CRITICAL-1, MEDIUMs)

The demo declares **Class 1: single machine, single GPU SKU, pinned
environment, bitwise-deterministic execution.**

- `torch.use_deterministic_algorithms(True)`, `cudnn.deterministic=True`,
  `cudnn.benchmark=False`, `CUBLAS_WORKSPACE_CONFIG=:4096:8`.
- TF32 **off** for both matmul and cuDNN, set explicitly and recorded in the
  env block. No AMP anywhere.
- The `attn` seed implements attention as explicit matmuls (QKᵀ softmax V by
  hand — it is a tiny single-head block), because SDPA's fused backwards are
  nondeterministic and would raise under deterministic mode on exactly the
  most interesting arm.
- No dropout anywhere in host, seeds, or policy. No gradient clipping
  anywhere (closes: reward F3's clipping channel by absence, stated).
- Learner RNG (policy init, minibatch order) is seeded; given the same
  merged store, `--train` is bit-reproducible.
- Deterministic-mode slowdown is measured once in pre-flight and recorded.
- "Same seed ⇒ same episode" is claimed **only under this contract**, and is
  continuously verified by the twin arm (below), not asserted.

## System mechanics

### Host and task

- CIFAR-10; deliberately undersized 3-stage CNN (~150k params). Checkable
  host property: under the mild pathology it plateaus by epoch ~12–15
  (restored as a testable statement; closes: stats F12 note).
- **Data partition (closes: stats F7):** train 50k for training; the 10k
  test set is split 5k **val** / 5k **test** once, by fixed seed. Val
  accuracy feeds telemetry and the training-time reward `R_a`. Test accuracy
  is computed for the same arms and stored, and is the **only** accuracy any
  reported metric uses. Loaders assert the partition.
- Dev runs may subset the training set (~20k) behind a flag; headline runs
  use full data.

### Pathology sampler (why telemetry has a signal)

Each episode samples one canned handicap of the *same* host:

| Pathology | Telemetry signature | Fan winner (by design) |
|---|---|---|
| Under-normalized | spiky grad norms, activation saturation | norm |
| Channel-starved | early plateau, high train-loss floor | conv-heavy |
| No spatial mixing (1×1 stage 2) | distinctive class-confusion spread | attn |
| Mild handicap | clean curves | conv-light or **no-op** |

The design-intent winner map is verified in pre-flight (gate 2b), not
assumed (closes: reward F11).

**Blindness rule, generalized (closes: determinism MEDIUM-blindness):**
every `TelemetryRecord` field must be a deterministic function of host state
and the logical epoch index. Wall-clock, durations, device identity, worker
identity, and `pathology_id` are excluded **by construction** — absent from
the dataclass, not filtered downstream. `--selftest` greps the telemetry
path for wall-clock/env/filesystem calls.

**Freeze discipline, enforceable (closes: determinism MEDIUM-freeze, stats
F12, morpho F15):** seeds are namespaced by construction —
`derive(run_seed, ns, i)` for `ns ∈ {dev, preflight, train, eval}` — so dev
and eval seeds cannot collide. Pathology definitions, the telemetry
normalizer, entropy coefficients, and the exploration schedule are tuned on
`dev`/`preflight` namespaces only, then **frozen together**; the git rev and
a hash of the frozen block are recorded, and `--eval` asserts the hash.
Retuning anything in the frozen block after any eval-namespace episode has
run voids the headline.

### Seeds — the delta contract

Every seed is a **delta, not a replacement**. The universal slot equation,
across the entire lifecycle (β defined under Lifecycle):

```
h' = h + α · Δ( lerp(h.detach(), h, β) )
```

**Init and normalization contract (closes: dynarch F3, answers its Q2):**
every seed terminates in a **scalar gain `g`, initialized to 0**, so
Δ ≡ 0 at germination for all four seeds — no accidental-scale confound at
entry. Internal normalization is stated per seed:

| Seed | Δ(h) | Internal norm | ~Params |
|---|---|---|---|
| `norm` | `g · (GroupNorm(h) − h)` | GN is the content | 0.1k |
| `attn` | `g · Attn(h)` (explicit-matmul single head) | LN on the attn input | 5k |
| `conv_light` | `g · DWSepConv(h)` | BN inside the block | 10k |
| `conv_heavy` | `g · ResBlock(h)` | BN inside the block | 60k |

This is deliberately tighter than esper-lite, which trained the seed under
additive STE semantics but blended it interpolatively — two different
meanings of "seed" (verified against `blend_ops.py`/`isolation.py` by the
lifecycle reviewer). The delta contract removes the ambiguity, and it is the
envelope Momir's generated candidates inherit later.

### Lifecycle (fixed FSM)

`DORMANT → GERMINATED → TRAINING → BLENDING → FOSSILIZED`, transitions once
per epoch. One equation; α gates forward contribution, β gates gradient
coupling to the host. Both are harness schedules, never policy knobs.

- **Structural isolation** pre-fossil: β = 0, so Δ consumes `h.detach()` —
  seed gradients cannot reach host parameters through the Jacobian path.
  (Stated precisely: this is Jacobian-path isolation; after blending begins
  the host naturally adapts to its shifted operating point — that is
  embodiment, not a leak. Closes: dynarch F9 wording.)
- **TRAINING** (fixed K≈3 epochs): α = 0 via STE — forward is
  `h + (Δ − Δ.detach())`, value bit-identical to the host's, Δ receives
  full task gradients. **The TRAINING loss for the seed adds a trust-region
  term `λ · ‖Δ‖² / ‖h‖².detach()`** (output-tensor norms, not parameter
  norms), making the objective quadratic with minimizer `Δ* = −g/(2λ)`
  instead of linear-and-unbounded (closes: dynarch F1 — STE alone fixes
  direction but not magnitude). The term contributes nothing to the forward
  value or the host gradient; invisibility is preserved. λ is a fixed
  harness constant.
- **BLENDING** (fixed M≈3 epochs): α ramps on one fixed cosine ease,
  **per optimizer step**, `p = (step+1)/total_steps` (no dead first epoch;
  closes: dynarch F8). β stays 0.
- **FOSSILIZING** (fixed F≈2 epochs, a harness sub-stage, not a policy
  state): α = 1; β ramps 0 → 1 linearly. `lerp(h.detach(), h, β)` is
  value-identical to `h` for every β, so this is a pure gradient-coupling
  ramp — it opens the host's new Jacobian path gradually instead of as a
  step discontinuity (closes: dynarch F2, reward F12).
- **FOSSILIZED:** α = 1, β = 1; the delta trains jointly as ordinary host
  tissue.

**Optimizer contract (closes: dynarch F5, answers its Q1):** SGD + Nesterov
momentum (fixed LR and weight decay, stated in code). Choosing SGD over Adam
dissolves the α-ramp/Adam gradient-absorption finding (dynarch F4) and the
stale-second-moment half of the fossilization shock. Seed parameters join as
a **second param group** created at germination (fixed seed LR, fresh
momentum buffers); host param-group ordering and state restore are
byte-identical across fan arms.

### Action space — factored head

`WAIT` and `no-op` are different things: WAIT preserves the option to act
later; the no-op arm means *never* intervene from this point. The policy
head is factored accordingly:

```
transformer trunk
    ├── NOW logit  p           (germinate at this decision point?)
    └── 4 seed logits π(a|s)   (which, conditional on acting — a ranges
                                over the four seeds ONLY; no-op is never
                                a fifth softmax class)  (closes: reward F9)
```

At most one germination per run. After germination the lifecycle is
automatic.

## Telemetry and policy

- **Telemetry record** (per epoch, a dataclass — a missing field is a
  construction error, never a silent 0.0): train/val loss, val accuracy,
  loss deltas, per-stage grad-norm mean/var, activation saturation fraction,
  weight norms, epoch index. All fields obey the generalized blindness rule.
- **Observation normalization at the boundary (closes: morpho F5):** a
  per-feature normalizer (median/IQR) is fitted on the pre-flight episodes
  and **frozen with the pathologies**. Raw grad-norm variance spans orders
  of magnitude next to [0,1] fractions; unnormalized input would swamp the
  embedding regardless of what a scale-tolerant linear probe says.
- **Embedded tokens:** a small learned MLP embeds each normalized record
  into a d_model≈64 token.
- **Policy:** tiny causal transformer (2 layers, d_model 64, ~100k params)
  over the tokens so far, with the factored head. One trunk.

## Episodes, the common future, and the fan

**The common future is drawn once per episode (closes: reward F5).** At
episode start, the full horizon's batch index order and augmentation
decisions (crop offsets, flip masks) are precomputed from the episode seed,
independent of model RNG. Consequences, all load-bearing:

- The **base run** — the episode trained with no intervention to the
  horizon — **is the no-op arm.** No separate no-op branch is trained
  (~20% compute saved).
- Fans at different epochs of one episode share one baseline, so the store
  natively contains **now-vs-later** evidence within an episode.
- Every branch consumes the precomputed future; different arm architectures
  cannot desynchronize the data stream (cloning RNG state alone would not
  guarantee this).

**Collection is schedule-driven (closes: reward F1/F1b/F7/F10, morpho
F2/F8/F16).** During `--collect`, germination points come from a **fixed
randomized exploration schedule** (per episode: 1–2 fan epochs drawn
uniformly from the decision window, from the episode seed) — never from the
policy. The policy therefore never gates its own data supply: no absorbing
state, no WAIT-prefix credit smearing, no behavior-policy drift in the
corpus, no covariate shift from a changing germination distribution. The
schedule is a harness property, invisible to the policy's action space.

**The fan, at scheduled epoch t:**

1. Snapshot: full host `state_dict()` **deep-copied** (parameters AND
   buffers — BN statistics exist and matter here), optimizer state
   deep-copied, CPU and per-device CUDA RNG states, data-stream position
   (closes: determinism HIGH-snapshot; `state_dict()` returns live
   references — the copy is explicit).
2. Branch into **4 seed arms + 1 twin arm**, all executed by the same
   branch executor — there is no privileged "chosen" path; during
   collection the episode *is* the fan (closes: determinism HIGH-arm-path).
3. **The twin arm** re-runs the no-op continuation from the snapshot and
   must reproduce the base run's tail **bitwise**; any divergence aborts
   collection. One arm continuously verifies snapshot completeness,
   branch-executor equivalence, optimizer restore, and that deterministic
   mode is actually in force (closes: determinism headline fix, its
   divergence-test-vector MEDIUM, and reward F3's integrity concern).
4. Each seed arm's module is initialized from `derive(episode_seed,
   arm_name)` — order-independent, identical whichever arm runs first
   (closes: determinism HIGH-arm-init).
5. **All arms of one fan run on one device** (cuDNN algorithm selection is
   workspace-dependent; two cards under different memory pressure can pick
   different algorithms). Parallelism is across episodes, not within fans
   (closes: determinism HIGH-device).
6. **Assertion:** host weights are bitwise identical across all arms at the
   end of TRAINING (STE forward is value-exact and the host backward is
   unaffected by Δ, so divergence = harness bug: RNG desync, optimizer
   contamination, or STE error) (closes: reward F3).
7. Arms run the automatic lifecycle to the horizon. `R_a^val` = mean val
   accuracy over the final 3 epochs (training-time reward); `R_a^test` =
   same on the test 5k (reporting only). Per-arm curves kept — a
   spike-then-crash arm is a headline plot, not a discard.
8. A **diverged arm** (non-finite loss) is recorded with
   `status="diverged"`, `R_a = null`, curves retained up to failure. The
   fan is kept; arm failure rates are reported per seed type — failure is
   asymmetric by construction and dropping such fans would flatter exactly
   the riskiest arms (closes: stats F15, determinism NaN-JSON MEDIUM — the
   encoder maps non-finite to `null` + status, never bare `NaN`).

**Fan record schema (closes: morpho F7 root cause, determinism CRITICAL-2,
stats F6/F8 fields).** The JSONL record is the serialization of a dataclass
defined adjacent to it, with at minimum: `kind ∈ {fan, policy_run}`,
`episode_seed`, `seed_namespace`, `split_role ∈ {preflight, train, eval}`,
`pathology_id`, `fan_epoch`, `schedule_id` (hash of the exploration
schedule), `policy_checkpoint_id` (for policy_run records), `config_hash`,
`frozen_block_hash`, `common_future_hash`, an `env` block (torch/CUDA/cuDNN
/python versions, GPU name, TF32 flags), per-arm `{name, init_seed, status,
R_val, R_test, curve}`, and the telemetry context. Append-only; failures
and no-op-wins kept.

**Store concurrency (closes: determinism HIGH-store ×2):** each worker
writes its own shard file; `--train` reads a canonical merge sorted by
`(episode_seed, fan_epoch)`. Learner input order is therefore a function of
content, not arrival — the trained policy is reproducible from the shards.

**Replay (closes: determinism CRITICAL-2):** `--replay <fan_id>` re-derives
the episode from `episode_seed` under the recorded config, forces the fan at
the recorded `fan_epoch`, and asserts the recorded outcomes. Env-block
mismatch **refuses** (no warn-and-continue). Replay is re-derivation under
the Class 1 contract; persisted weight snapshots are not required.

## Learning: fully offline, full information

Both heads train offline on the fan store — collection is online under the
exploration schedule; learning is offline with every arm labeled; the
trained policy acts online only at evaluation. (This is the rev 2
"offline-online split" completed: REINFORCE exits the design entirely, and
with it the variance-mismatch, entropy-coupling, and trunk-interference
findings. Closes: reward F1/F2-part/F7/F10, morpho F16.)

- **WHICH:** maximize `J_which = Σ_{a∈4 seeds} π(a|s) · R_a^val` over all
  train-split fans (exact expected counterfactual reward; with every
  outcome known this is full-information — no GRPO, no baseline needed,
  Σπ = 1 makes any baseline a no-op on the gradient).
- **NOW:** the same records, two-arm full-information:
  `J_now = p·(Σ_a π(a|s)·R_a^val) + (1−p)·R_noop^val`. The no-op label
  lands where it belongs — dense supervision for restraint (closes: reward
  F9's core observation).
- **Entropy** terms on both heads, coefficients expressed as a fixed
  fraction of the measured pre-flight **fan density** (the natural reward
  unit; closes: reward F2), frozen with the frozen block, and reported
  alongside the restraint rate so a reader can see the regularizer is not
  manufacturing restraint (closes: morpho F14).
- Loader asserts `split_role == "train"` on every record entering a
  gradient step; eval records never train (closes: stats F6, morpho F4).

## Pre-flight validation (gates before freezing, freeze before collection)

Run ~30 `preflight`-namespace episodes under the exploration schedule, then:

1. **No-op wins, against the exact null (closes: stats F2):** under
   exchangeability P(no-op is fan argmax) = 20% exactly. Gate: no-op win
   rate in mild-handicap fans is significantly **above** 20% (binomial
   test), and significantly **below** 20% in the three targeted
   pathologies. "Not never" is not a gate.
2. **Signal exists, at the right target:** (a) linear probe telemetry →
   `pathology_id` with **GroupShuffleSplit by episode** (closes: stats F1 —
   row-level splits pass on episode-identity leakage); (b) a second probe
   telemetry → **fan argmax**, scored against the majority-class null, plus
   the realized pathology × fan-argmax contingency table compared to the
   design-intent winner map — the ground-truth money chart (closes: reward
   F11, morpho F1 pre-check).
3. **Contrast beats noise, on paired quantities (closes: stats F3, morpho
   F12):** fan density is `mean(R_best − R_second)` and
   `mean(R_best − R_noop)` **within fans** (common-mode episode variance
   cancels in the pair). The twin arm's spread must be exactly zero under
   Class 1 (a bitwise re-execution); the meaningful noise floor is measured
   from ~10 **refanned** episodes — same snapshot, same epoch, a *re-drawn
   common future* — which asks the right question: how much does `R_a` move
   under a different draw of irrelevant conditions (closes: stats F10's
   floor half, corrected for the determinism contract: naive re-execution
   would measure a trivial zero).
4. **No degenerate dominance (closes: dynarch F7, morpho F1, reward F8):**
   no single seed is fan argmax in > ~40% of fans overall, nor a majority
   within every pathology. A capacity-dominant conv_heavy fails this gate
   before a night of collection is spent.
5. **Magnitude sanity (closes: dynarch verification ask):** log
   `RMS(Δ)/RMS(h)` at blend entry per arm; arms should enter within ~2× of
   one another — the empirical check that the trust-region term did its
   job.
6. **Horizon adequacy (closes: reward F6):** fan density reported per
   scheduled fan epoch; the gate is that density does not collapse with t
   (the mechanical facts about runway-vs-plateau are measured, not
   asserted in either direction).

Then the frozen block (pathologies, normalizer, entropy coefficients,
schedule) locks, its hash is recorded, and collection starts. Failing gates
retunes the sampler and re-runs pre-flight — never the policy, never after
eval-namespace episodes exist.

## Evaluation protocol (closes: stats F4/F9, morpho F13)

All comparisons run on a **frozen eval battery** fixed before any eval run:

- `N_eval = 100` `eval`-namespace episode seeds, shared by every policy
  under comparison (trained, random, schedule-only). Paired by seed.
- **Lift:** each policy plays its episode live (its own germination
  choices). Lift per episode = `R_chosen^test − R_noop^test` (the base run
  is the no-op). Never-germinating scores exactly 0 by construction.
  Statistic: Wilcoxon signed-rank on per-episode paired lift, episode as
  the unit.
- **Agreement and the money chart:** computed on a frozen grid of
  `(episode_seed, fan_epoch)` pairs — fans forced at pre-registered epochs,
  the policy queried teacher-forced on the same telemetry prefix. Every
  policy is scored against the *same* fans; a policy's own decisions never
  select the ground-truth set (a fan triggered by the evaluated policy
  makes the label a function of the policy — not comparable across
  policies).
- **Restraint quality:** regret vs fan-optimal *with no-op eligible* on the
  frozen grid (closes: reward F4 — a 0 from correct restraint and a 0 from
  leaving +0.05 unclaimed are now distinguishable).
- **Oracle ceiling (closes: stats F10):** ~30 eval-grid points **refanned**
  (same snapshot and epoch, re-drawn common future — under the bitwise
  contract a plain re-execution would trivially self-agree); the argmax's
  agreement rate across the two draws is the ceiling. Agreement numbers are
  reported as a fraction of that ceiling, not of 100%.
- **Nulls:** uniform-chance rates are not reported. The nulls are the
  **majority-class rate** (marginal best-seed frequency, measured) and the
  **schedule-only policy** (same architecture and training, input reduced
  to epoch index — isolates "diagnosis" from "scheduling").
- **Falsifier (closes: morpho F11 wording):** the trained policy is
  re-scored on the frozen grid with telemetry *histories swapped between
  eval episodes of the same horizon* (epoch alignment preserved
  positionally; the epoch-index field is position-consistent by
  construction). If the money-chart diagonal survives, the policy learned
  the schedule and the demo claim fails honestly.

## Pre-registered numbers (locked at freeze time; closes: morpho F15, stats F11/F12)

- Headline horizon: **40 epochs** (decision window 5–15, TRAINING 3,
  BLENDING 3, FOSSILIZING 2, ≥15 full-influence epochs of runway). The
  200-epoch flag is exploratory and may not be quoted as the headline.
- Collection: 300 train-namespace episodes. Eval: `N_eval = 100`, evaluated
  once, no peeking before collection completes, no augmenting after.
- Pass thresholds, committed now: trained lift > 0 (Wilcoxon p < 0.05,
  one-sided) **and** trained lift > schedule-only lift (paired, same test);
  conditional-on-acting agreement ≥ majority-class null + 15 points **and**
  ≥ 60% of the oracle ceiling; money chart row-argmax matches the designed
  winner for ≥ 3 of 4 pathologies; shuffled-telemetry agreement collapses
  to within the null's CI.

## Report (`--report`)

Fan-winner agreement at both grains (vs measured nulls and ceiling), lift
table (trained / random / schedule-only), money chart + its shuffled
falsifier twin, per-pathology arm curves including at least one
spike-then-crash arm, α(t)/β(t) trajectory for one episode per pathology,
`RMS(Δ)/RMS(h)` at blend entry per seed, fan density, per-seed-type arm
failure rates, restraint-regret, and the entropy coefficients in force.
`--report` refuses to mix seed namespaces in one number.

## Engineering

- **File:** `experiments/kernel_demo.py`, target ≲1000 lines, torch +
  torchvision only, ordered as a narrative: telemetry record → seeds →
  host + slot → lifecycle → fan/branching → policy → learning → pre-flight
  → eval → report. Plotting may live in a sidecar if matplotlib clutters
  the narrative.
- **Modes:** `--selftest`, `--preflight`, `--collect`, `--train`, `--eval`,
  `--report`, `--replay <fan_id>`.
- **Data path — no loader at all:** CIFAR-10 preloaded to each GPU once as
  uint8 (~180MB), augmentation as on-GPU tensor ops consuming the
  precomputed decisions. No DataLoader, no worker processes, no IPC — the
  GIL problem esper-lite's `SharedBatchIterator` managed is dodged
  entirely. Python ≥3.14 repo-wide; worker model: free-threaded episode
  workers, one shard file each.
- **Runtime:** both 4060 Tis dedicated; several episode workers per card;
  fans never span devices. At horizon 40 an episode with one fan is
  minutes; 300 collection episodes fit overnight with margin.

## Success criteria for the demo itself

- A reader can open the one file and follow the whole loop top-to-bottom.
- `--selftest` passes: twin-arm bitwise check on a smoke episode, blindness
  grep, loader split assertions, JSON round-trip of non-finite arm records.
- Pre-flight gates 1–6 pass and are reported.
- The pre-registered thresholds above are met on the frozen eval battery —
  including the schedule-only comparison (the strongest null is required,
  not optional; closes: morpho F6) — and the shuffled-telemetry falsifier
  collapses.
- At least one recorded spike-then-crash arm plot demonstrating why
  end-state reward is the rule.
