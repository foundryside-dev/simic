# Kernel Demo — "Simic in 20 minutes"

**Date:** 2026-08-09 · **Status:** approved design, pre-implementation
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

**The claim demonstrated** is the inversion of the old Tamiyo regime.
Esper's controller got "hundreds of random seeds, 3 slots, 6 types, good
luck" — sparse bandit feedback in a huge action space. Here: **1 slot, 4
seed types, full counterfactual labels at every decision.** Dense signal in
a tiny action space is enough for a learned controller to do genuine
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

## System mechanics

### Host and task

- CIFAR-10; deliberately undersized 3-stage CNN (~150k params) that plateaus
  in ~10–15 epochs. Slot site fixed after stage 2.
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
must learn restraint, not enthusiasm. The fan records validate this table
empirically: a pathology that never separates the arms is retuned (the
episode design is fixed, the policy is never patched to compensate).

### Seeds

Four residual modules, one interface (slot features in → same shape out):

| Seed | Content | ~Params |
|---|---|---|
| `norm` | GroupNorm + affine | 0.1k |
| `attn` | single-head spatial self-attention | 5k |
| `conv_light` | depthwise-separable 3×3 block | 10k |
| `conv_heavy` | full residual block | 60k |

### Lifecycle (fixed FSM, esper-lite mechanics)

`DORMANT → GERMINATED → TRAINING → BLENDING → FOSSILIZED`, transitions once
per epoch.

- **Structural isolation:** `seed_input = host_features.detach()` at all
  pre-fossil stages — seed gradients cannot reach the host, by construction.
- **TRAINING** (fixed K≈3 epochs): STE forward
  `host + (seed − seed.detach())`. Forward value bit-identical to the host's;
  seed receives full task gradients. Pretrains in the live signal path while
  provably invisible.
- **BLENDING** (fixed M≈3 epochs): `(1−α)·host + α·seed`, α on one fixed
  cosine ease at one fixed speed.
- **FOSSILIZED:** α=1, detach dropped, seed trains jointly as ordinary host
  tissue.

### Action space

Once per epoch while DORMANT:
`{WAIT, GERMINATE(norm), GERMINATE(attn), GERMINATE(conv_light), GERMINATE(conv_heavy)}`.
At most one germination per episode. After germination the lifecycle is
automatic.

## Telemetry and policy

- **Telemetry record** (per epoch, a dataclass — a missing field is a
  construction error, never a silent 0.0): train/val loss, val accuracy,
  loss deltas, per-stage grad-norm mean/var, activation saturation fraction,
  weight norms, epoch index.
- **Embedded tokens, not hand-packed obs vectors:** a small learned MLP
  embeds each record into a d_model≈64 token.
- **Policy:** tiny causal transformer (2 layers, d_model 64, ~100k params)
  over the tokens so far; at each DORMANT epoch emits 5 logits. One trunk,
  one head.

## The counterfactual fan

When Aurelia germinates at epoch *t*:

1. Snapshot run state (host weights, optimizer, RNG, data order).
2. Branch into **5 matched arms**: chosen seed, the other 3, no-op. Every
   arm sees the identical future batch stream — matched common-future
   branches; grouped statistics in miniature.
3. Each arm runs the automatic lifecycle to the fixed episode horizon.
4. `R_a` = mean val accuracy over the final 2–3 epochs (de-noised
   end-state). The full per-epoch arm curves are kept — spike-then-crash
   arms are a headline plot, not a discard.
5. The **fan record** (telemetry context, germination epoch, 5 outcomes,
   arm curves, pathology id) is appended to a JSONL store. Append-only;
   failures and no-op wins kept.

A never-germinate episode is itself a no-op run and still yields a (weaker)
record.

**Horizon rule:** episode length (~18 epochs; decision window ~3–8,
TRAINING ~3, BLENDING ~3) leaves ≥4 fossilized epochs of runway so a
crash-and-burn seed crashes *before* it is scored.

## Learning: offline-online split

- **WHICH — offline, full-information.** Every stored fan labels all five
  arms. The germination-step logits train GRPO-style with
  `Â_a = R_a − mean(R_fan)` for *every* arm, over the whole accumulated fan
  store, replayed freely. No off-policy correction needed: nothing was left
  unmeasured.
- **WHEN — online.** WAIT/timing decisions train by plain REINFORCE on
  fresh episodes only, reward `R_chosen − R_noop`, small entropy bonus.
- **Stated limitation:** the fan measures "now vs never," not "now vs
  later" — timing gets coarser credit than choice. Accepted for the demo.
- Multiple episode workers across both GPUs fill one fan store; the learner
  updates between episode batches.

## Measurement (all read from the fan store)

1. **Headline:** trained policy's mean lift `R_chosen − R_noop` on fresh
   eval episodes vs. the same number for a random policy.
2. **Fan-winner agreement:** rate her pick equals the fan argmax
   (chance ≈ 25%; choosing restraint in no-op episodes counts).
3. **Money chart:** pathology × chosen-seed confusion matrix — proof she
   reads telemetry rather than schedules.

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
  data order); arms share the base trajectory's RNG snapshot and future
  batches. Same seed ⇒ same episode.
- **Runtime:** both 4060 Tis are dedicated — redline them. Multiple episode
  workers per GPU (the host is tiny; VRAM allows several concurrent
  episodes per card), fan arms dispatched across whichever card is free.
  Rough guess 2–4 min/episode/worker → high hundreds of fan records
  overnight, more than sufficient for a 4-way choice with full-information
  labels.

## Success criteria for the demo itself

- A reader can open the one file and follow the whole loop top-to-bottom.
- The three measurements above, produced by `--eval`/`--report`, show:
  lift > 0 and clearly above random, fan-winner agreement well above 25%,
  and a visibly diagonal money chart.
- At least one recorded spike-then-crash arm plot demonstrating why
  end-state reward is the rule.
