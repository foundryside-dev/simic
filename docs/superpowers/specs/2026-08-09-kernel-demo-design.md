# Kernel Demo — "Simic in 20 minutes"

**Date:** 2026-08-09 · **Status:** approved design (rev 2, post-review), pre-implementation
**Target:** `experiments/kernel_demo.py` (single file, plus optional plotting sidecar)

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

**Intellectual role:** the demo establishes that a transformer can infer
intervention value from host telemetry when trained with dense matched
counterfactual fans, while keeping the intervention language human-authored.
Its output — the fan store — is exactly the counterfactual atlas and proven
substrate that early Momir needs; Simic's next move is replacing the
four-way seed vocabulary with generated candidates.

**The claim demonstrated** is the inversion of the old Tamiyo regime.
Esper's controller got "hundreds of random seeds, 3 slots, 6 types, good
luck" — sparse bandit feedback in a huge action space. Here: **1 slot, 4
seed types, full counterfactual labels at every germination.** Dense signal
in a tiny action space is enough for a learned controller to do genuine
diagnosis: read telemetry, identify the host's deficiency, inject the right
structure at the right time, and be scored against every alternative
including doing nothing.

## Scope pins (agreed, do not widen)

- One fixed host architecture. One fixed slot site. Exactly four seeds.
- No host families, no held-out-architecture tests, no universality claims.
- Aurelia's only authorities: **which** seed and **when**. The lifecycle has
  zero knobs for her — one blend waveform, one speed, fixed stage durations.
- Reward is **end-state only**. No intermediate reward, no shaping terms, no
  progress bonuses (reward shaping is what killed Esper; the demo carries
  zero shaped terms by constitution).
- Telemetry provenance: measurements originate at the host/slot code (the
  Kasmina role, in esper-lite terms) and the demo builds **no Nissa
  abstraction** — the `TelemetryRecord` is produced where it is measured.
  Whether Simic proper recasts Nissa as publication/provenance layer rather
  than observation author is a constitutional question (Nissa's verb,
  INV-07/09 evidence routing) tracked separately, not decided here.

## System mechanics

### Host and task

- CIFAR-10; deliberately undersized 3-stage CNN (~150k params) that plateaus
  well inside the horizon. Slot site fixed after stage 2.
- Dev runs may subset the training set (~20k) behind a flag; headline runs
  use full data.

### Pathology sampler (why telemetry has a signal)

Each episode samples one canned handicap of the *same* host, so the
best-seed answer varies with observable telemetry:

| Pathology | Telemetry signature | Fan winner (by design) |
|---|---|---|
| Under-normalized | spiky grad norms, activation saturation | norm |
| Channel-starved | early plateau, high train-loss floor | conv-heavy |
| No spatial mixing (1×1 stage 2) | distinctive class-confusion spread | attn |
| Mild handicap | clean curves | conv-light or **no-op** |

No-op must genuinely win some episodes — the mandatory-no-op spirit; she
must learn restraint, not enthusiasm.

**Blindness:** `pathology_id` lives only in the fan record for reporting.
It never enters a telemetry record or the policy's input path.

**Freeze discipline:** pathology definitions are tuned on development seeds
until the intended contrasts exist (each pathology separates the arms as
designed, and no-op wins its share), then **locked before headline
evaluation**. Headline runs use fresh host initialisations. Retuning after
seeing evaluation fans is test-set engineering and is not done.

### Seeds — the delta contract

Every seed is a **delta, not a replacement**. The universal slot equation,
across the entire lifecycle:

```
h' = h + α · Δ(h.detach())
```

Four deltas, one interface (slot features in → same-shape delta out):

| Seed | Δ(h) | ~Params |
|---|---|---|
| `norm` | `GroupNorm(h) − h` (replacement-via-delta) | 0.1k |
| `attn` | single-head spatial self-attention residual | 5k |
| `conv_light` | depthwise-separable 3×3 residual | 10k |
| `conv_heavy` | full residual block | 60k |

This is deliberately tighter than esper-lite, which trained the seed under
additive STE semantics (`∂out/∂seed = 1`) but blended it as a replacement
(`(1−α)·host + α·seed`) — two different meanings of "seed." The delta
contract removes the ambiguity, and it is the envelope Momir's generated
candidates inherit later: old static seeds and future Growth IR agree on
what a seed mathematically is.

### Lifecycle (fixed FSM)

`DORMANT → GERMINATED → TRAINING → BLENDING → FOSSILIZED`, transitions once
per epoch. One equation, three regimes of α:

- **Structural isolation** at all pre-fossil stages: the delta consumes
  `h.detach()` — seed gradients cannot reach the host, by construction.
- **TRAINING** (fixed K≈3 epochs): STE forward `h + (Δ − Δ.detach())`.
  Forward value bit-identical to the host's; Δ receives full task gradients
  at effective α=1. Pretrains in the live signal path, provably invisible —
  and what is trained is *exactly* the additive delta that blending will
  introduce.
- **BLENDING** (fixed M≈3 epochs): `h + α·Δ`, α on one fixed cosine ease at
  one fixed speed, 0 → 1.
- **FOSSILIZED:** `h + Δ`, detach dropped; the delta trains jointly as
  ordinary host tissue.

### Action space — factored head

`WAIT` and `no-op` are different things: WAIT preserves the option to
germinate later; the fan's no-op arm means *never* intervene from this
point. The policy head is factored to keep those semantics separate:

```
transformer trunk
    ├── NOW logit                 (germinate this epoch?)
    └── 4 seed logits             (which, given NOW)
```

Evaluated once per epoch while DORMANT; NOW=false ⇒ WAIT. At most one
germination per episode. After germination the lifecycle is automatic.

## Telemetry and policy

- **Telemetry record** (per epoch, a dataclass — a missing field is a
  construction error, never a silent 0.0): train/val loss, val accuracy,
  loss deltas, per-stage grad-norm mean/var, activation saturation fraction,
  weight norms, epoch index. Produced by the host/slot code directly.
- **Embedded tokens, not hand-packed obs vectors:** a small learned MLP
  embeds each record into a d_model≈64 token.
- **Policy:** tiny causal transformer (2 layers, d_model 64, ~100k params)
  over the tokens so far, with the factored NOW/WHICH head above. One
  trunk.

## The counterfactual fan

When Aurelia germinates at epoch *t*:

1. Snapshot the run state (host weights, optimizer state, data position).
2. **Precompute the common future:** the remaining epochs' batch index
   order *and all augmentation decisions* (crop offsets, flip masks) are
   drawn once, independent of model RNG, and shared by every arm. Cloning
   RNG state alone is insufficient — different arm architectures consume
   RNG differently and would silently diverge the data stream. Every branch
   sees literally identical images.
3. Branch into **5 matched arms**: chosen seed, the other 3, no-op.
4. Each arm runs the automatic lifecycle to the fixed episode horizon.
5. `R_a` = mean val accuracy over the final 2–3 epochs (de-noised
   end-state). Full per-epoch arm curves are kept — spike-then-crash arms
   are a headline plot, not a discard.
6. The **fan record** (telemetry context, germination epoch, 5 outcomes,
   arm curves, pathology id) is appended to a JSONL store (schema = the
   dataclass that serializes it, defined adjacent). Append-only; failures
   and no-op wins kept.

**What the fan does and does not measure:** all five arms are measured *for
acting now*. `max_a R_a − R_noop` says whether acting now was worthwhile;
it does not compare now against waiting until t+1. The full-information
claim is scoped to WHICH-given-NOW; WHEN keeps the stated "now vs never,
not now vs later" limitation.

**Never-germinate episodes** produce no fan and train nothing — and that is
principled, not a gap: with reward defined as `R_chosen − R_noop`, the
never-intervene trajectory has utility exactly zero by construction. The
mandatory-no-op invariant's "policy utility exactly zero" appears here as
the reward's zero point. These episodes still land in the store for
evaluation statistics (restraint rate).

**Horizon:** default ~40 epochs (decision window ~5–15, TRAINING ~3,
BLENDING ~3, leaving ≥15 fossilized epochs of runway — a crash-and-burn
seed crashes *before* it is scored). Horizon is a config; a long-run flag
(up to esper's 200-epoch regime) exists for stress runs but is not the
default.

## Learning: offline-online split

- **WHICH — offline, full-information.** Every fan labels all four seed
  arms plus no-op at a measured decision point. The seed head trains by
  directly maximizing exact expected counterfactual reward,
  `J = Σ_a π(a|s, NOW) · R_a`, over the whole accumulated fan store,
  replayed freely, plus a small entropy term to delay premature
  saturation. (No GRPO machinery needed: with every outcome known this is
  a full-information contextual-bandit objective, not an estimate. A
  mean-fan baseline would not change the gradient since Σπ = 1.)
- **WHEN — online.** The NOW/WAIT decisions train by plain REINFORCE on
  fresh episodes only, reward `R_chosen − R_noop`, small entropy bonus.
- **Interference guard:** offline WHICH updates are dense and low-variance;
  online WHEN updates are sparse and noisy. Run a brief offline-only
  warm-up first, and assert during online training that the NOW head's
  outputs actually move (logged, checked in `--train`).
- Multiple episode workers across both GPUs (redlined — dedicated hardware)
  fill one fan store; the learner updates between episode batches.

## Pre-flight validation (before any policy training)

Run ~30 random-policy episodes and check, in order:

1. **No-op wins its share:** no-op is the fan argmax in a meaningful
   fraction of mild-handicap episodes. If never, retune the pathology
   sampler (this is the construction phase; freeze comes after).
2. **Pathology separability:** a linear probe (logistic regression / k-NN)
   over raw telemetry records predicts `pathology_id` well above chance.
   If a linear model cannot see the signal, the transformer will not
   either.
3. **Fan contrast vs noise:** per (pathology, seed) pair, the spread of
   `R_a` across episodes must be smaller than the typical best-vs-second
   arm separation; report **fan density** `mean(R_best − R_worst)`. If
   contrast drowns in noise, widen the end-state averaging window or
   lengthen the horizon before touching anything else.

Only after these pass are pathologies frozen and policy training started.

## Measurement (all read from the fan store)

1. **Headline:** trained policy's mean lift `R_chosen − R_noop` on fresh
   eval episodes vs. the same number for a random policy.
2. **Fan-winner agreement**, reported at both grains: five-way agreement
   with the fan argmax including restraint (chance ≈ 20%), and
   conditional-on-acting seed agreement (chance ≈ 25%).
3. **Money chart:** pathology × chosen-seed confusion matrix — proof she
   reads telemetry rather than schedules.
4. **Falsifier controls:** (a) a schedule-only baseline policy (epoch
   index in, telemetry ignored); (b) the trained policy re-evaluated with
   telemetry shuffled between episodes, epochs preserved. If the money
   chart's diagonal survives shuffling, she learned the schedule, not
   diagnosis — the demo claim fails honestly.
5. **Report plots:** per-pathology arm curves including at least one
   spike-then-crash arm (why end-state reward is the rule), α(t) blend
   trajectory alongside host/arm loss for one episode per pathology, and
   fan density.

## Engineering

- **File:** `experiments/kernel_demo.py`, ≲800 lines, torch + torchvision
  only. Ordered as a narrative: telemetry record → seeds → host + slot →
  lifecycle → fan/branching → policy → training loop → evaluation → report.
  Optional plotting sidecar if matplotlib clutters the main file.
- **Modes:** `--collect`, `--train`, `--eval`, `--report`.
- **Data path — no loader at all:** CIFAR-10 preloaded to each GPU once as
  uint8 (~180MB), augmentation (pad-crop + flip) as on-GPU tensor ops. No
  DataLoader, no worker processes, no IPC — the GIL problem esper-lite's
  `SharedBatchIterator` managed is dodged entirely (this is the terminal
  form of its `gpu_preload` path). Python is already ≥3.14 repo-wide;
  free-threading is available to episode workers but not load-bearing.
- **Determinism:** every episode fully seeded (host init, pathology draw,
  data order); fan arms consume the precomputed common future, never live
  RNG. Same seed ⇒ same episode.
- **Runtime:** both 4060 Tis dedicated; several concurrent episode workers
  per card (tiny host, resident data). At the 40-epoch default an episode
  with its fan is minutes; overnight yields high hundreds to thousands of
  fan records — ample for a 4-way choice with full-information labels.

## Success criteria for the demo itself

- A reader can open the one file and follow the whole loop top-to-bottom.
- Pre-flight validation passes and is reported (no-op wins exist, linear
  probe separates pathologies, fan contrast exceeds noise).
- `--eval`/`--report` show: lift > 0 and clearly above random,
  fan-winner agreement well above both chance rates, a visibly diagonal
  money chart, **and** the shuffled-telemetry control collapsing the
  diagonal.
- At least one recorded spike-then-crash arm plot demonstrating why
  end-state reward is the rule.
