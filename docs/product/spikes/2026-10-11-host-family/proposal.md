# Host-family proposal, measured against Esper's original loop — 2026-10-11

**Design only, for John's review. Nothing here is approved training, and John has made no choice.**
- No source change, test run, GPU run, spending or threshold change follows from this document.
- Simic released its GPU reservation at 18:47 AEDT on 2026-10-11 for Sultai's slot from 19:00. No
  Simic GPU work is authorised until John re-authorises it.
- Stopping, deferring, screening and reopening the regime question are all John's to choose
  (§11). Where this document gives a recommendation, it is labelled as mine.

It starts from the Fleet C1 checkpoint (PR #44, `70707bb`;
[checkpoint](../../../results/2026-10-11-fleet-c1-checkpoint.md)). Only `under_normalized` passed
the deficit screen. PDR-0057 registered: "fewer than two passing hosts means the host set is
rebuilt or the pathway stops (John)" (`0057:212-216`). John's refinement: the revisit must be
mindful of the original Esper-lite loop the project is trying to prove.

**Revision history:**
- **Revision 1:** an adversarial benchmark-shopping review found three blockers.
- **Revision 2:** those three were fixed, and a re-review found none left.
- **Revision 3 (this one):** follows an independent eight-specialist design panel on revision 2
  (`d4bb6a5`). The panel's findings, the resolution of every blocker and the recorded dissent are
  in [`panel-review.md`](panel-review.md).

**Superseded advice is listed in §13.** In particular, the checkpoint's "Rebuild" recommendation
and its "about 4 hours" screen-only pilot are **superseded advice**. That pilot was a
recommendation, never approved training.

Contents:
1. The original loop, from primary sources
2. Where the current pathway has drifted
3. What the evidence establishes, and what it does not
4. Proposals that would only make the benchmark easier
5. Diagnostic screening is not proof of the loop
6. The screen design, if John chooses it
7. Compute budget
8. Go/no-go and stopping rules
9. How this design moves the bar
10. Review before any launch
11. The options, at parity
12. Prerequisites (not to be done now)
13. Superseded and corrected statements
14. Recommendation (mine; the choice is John's)
15. Sources

Companion files:
- [`panel-review.md`](panel-review.md) — the eight-specialist panel and its reconciliation;
- [`generator.py.txt`](generator.py.txt) — the host generator;
- [`draw.md`](draw.md) — the drawn hosts and the recorded failed first draw.

**Source keys** (full list in §15):
- **[HLD]** `/mnt/data/archive/esper.old`, `docs/architecture/001-high-level-design.md` at
  `8d69bec`, committed 2025-08-03 as that repository's root commit; its header reads "Version
  1.4, 01 July 2025". It is the **earliest-committed** design document in the archives, but it
  is itself v1.4. [PAPER] embeds an older "OUTDATED" v2.0a header dated 14 June 2025
  (PAPER:123-127).
- **[PAPER]** `/mnt/data/archive/esper-lite`, `_archive/docs/paper/draft_paper.md@0ee3a001`
  (v3.0RC1; "Results are placeholders", lines 5-7).
- **EL** `/mnt/data/archive/esper-lite`. **P** is its pinned public commit `0807ccf`
  ([github](https://github.com/tachyon-beep/esper-lite/tree/0807ccfaa847303d9a65bc4c48ad199f34dd3624)).
- **E26** `/mnt/data/archive/esper`.
- Simic paths are relative to the repository root.

## 1. The original loop, from primary sources

**The loop as designed:**
- **Clock.** "Tolaria acts as the master clock, emitting an EndOfEpoch event… Tamiyo [analyses]
  the epoch's telemetry to make a germination decision" [HLD:691].
- **Decision.** Tamiyo decides "*if, when, where,* and *how*" [HLD:734], detects plateaus and
  "Selects the optimal dormant Seed" [HLD:736,738]. A location head picks dormant seeds, then a
  kernel head picks the artefact [HLD:1697-1715].
- **Generation.** Karn invents blueprints [HLD:116]. Kasmina is a "Pure Executor" [HLD:719].
- **Staging.** In the original's first phase, Karn is "Stubbed (No-Op Listener)" and Tamiyo uses
  "a static, human-curated library of 10-20 canonical BlueprintIRs" [HLD:2217-2221]. Generation
  was staged after a fixed library.
- **Lifecycle.** Germinate, train with "zero impact" on the host, graft with an alpha ramp,
  stabilise, evaluate, then **fossilise or cull** [HLD:1548-1565, esp. 1560-1563]. The HLD
  expects repeated adaptation cycles with stability kept, and rollback [HLD:161,215,217].
- **Reward.** A shaped reward [HLD:1759-1771]. Training was imitation of a heuristic, then RL
  [HLD:1736,1750-1753].
- **Esper-lite as built.**
  - A factored action space: slot, blueprint (including NOOP), tempo, alpha, and a lifecycle `op`
    head (`LifecycleOp`: WAIT, GERMINATE, SET_ALPHA_TARGET, PRUNE, FOSSILIZE, ADVANCE; EL
    `src/esper/leyline/factored_actions.py:20-34,92-115,425-434@P`).
  - Accuracy-minus-parameter-rent rewards (EL `src/esper/simic/rewards/contribution.py:92-111@P`).
  - No-Op is a library blueprint [PAPER:474,509].

**The claim it was built to prove.** "Tamiyo… monitors a host model during its initial training,
identifying learning bottlenecks and patching in new capacity to improve the final trained
artifact" [HLD:77]. Supporting text:
- the scope is in-training, not post-training [HLD:93,330];
- research question 1 asks whether the architecture can be "safely and autonomously modified…
  during its initial training process" [HLD:235];
- research question 6 asks for "better parameter efficiency for a given performance level than
  traditional training and transfer learning paradigms" [HLD:240];
- a learned policy "replaces static rules or simple heuristics" [HLD:113] and must beat "a
  baseline random or heuristic-based kernel selection strategy" [HLD:2225].

[PAPER] is a different lineage. It describes evolution "IN FROZEN NEURAL NETWORKS", with a
"Frozen base" that is never retrained [PAPER:95,215], which is the case HLD:93 puts out of
scope. **L1 rests on the HLD alone.**

For mapping, I split this into seven claims:

| | Original claim | Primary source |
|---|---|---|
| **L1** | In-training repair: a learning bottleneck identified while a host trains is repaired by structure grafted during training, improving the final artefact | [HLD:77,93,235,330]; capacity grown "based on demonstrated need" for bottlenecks "as they emerge during the training process" [HLD:175-176] |
| **L2** | Parameter efficiency: a given performance for fewer parameters than conventional training; the foil is uniform over-provisioning | [HLD:22,125,175,227,240]; quantitative target "10 to 100 times fewer parameters… compared to full model fine-tuning" [HLD:160-162] |
| **L3** | Diagnosis: the controller decides if, when, where and how, including doing nothing | [HLD:115,734-738] |
| **L4** | Learned beats fixed: a learned policy beats random, heuristic or fixed selection | [HLD:113,2225] |
| **L5** | Generality and transfer: the platform works across MLPs, CNNs and Transformers [HLD:217, a robustness property]; policy wisdom carries across hosts and projects (EL `DESIGN_MANIFESTO.md:74@8517cca5`) | as cited |
| **L6** | Generated structure: blueprints invented, not picked from a fixed menu. In the original, a later stage after a fixed library | [HLD:116,2217-2221]; Simic `docs/product/vision.md:21-23` |
| **L7** | Closed-loop lifecycle: grafts are evaluated, then kept (fossilised) or culled, over repeated cycles, with rollback | [HLD:161,215,217,1560-1563]; EL `factored_actions.py:108-115,433@P` |

**The owner's statement** (`0057:32-37`): "rather than training a massive model you start by
training a small model and inject extra parameters where you have issue"; "40->60 with 1.01x
parameter increase (proven)… train tamiyo to do (somewhat proven) it in a target agnostic way
(entirely unproven so far)". Three cautions:
- **The over-provisioning foil is in the primary sources**, though not in those words: "grow
  capacity precisely where needed" against over-provisioning [HLD:22]; "rather than allowing
  capacity to grow organically" [HLD:175]; also [HLD:125,227] and PAPER:97 ("evolve
  capacity-constrained models"). HLD:129 seeds a smaller student "at the start of its training"
  and germinates "where the student model struggles most". That is close to "start small, grow
  where needed", set within a distillation scenario.
- **"40→60 at 1.01×" has no primary source.** The only 1.01× in the three archives is PAPER:450,
  a placeholder latency figure. PDR-0046 records the owner's prior as an `attn` + `norm`
  **two-seed** combination with compromised telemetry (`0046:86-89`).
- **The nearest measured analogue** is Fleet C1 on `under_normalized`, from the published per-arm
  summary: mean final dev accuracy 42.6% for no growth, 46.7% for the graft, 48.1% for static, at
  1.001× parameters. That is an exploratory accuracy reading; CE is the registered endpoint.

**What the original record controlled and what it did not** (EL):
- **The POC had an epoch-matched static arm.** Its "from-scratch" arm trained the combined
  architecture for 25 epochs, the same as the morphogenetic arm (10 + 5 + 5 + 5). It scored below
  the 10-epoch bare host, and that is unexplained (`src/esper/poc.py:51-55,528,614-617,731,750@0ee3a001`;
  `README.md:79-88@0ee3a001`). The baseline arm had fewer epochs (10).
- **The RL era had no static baselines.** The modes were added in `71ec0b31`, and the proof
  packet reports them missing (`docs/analysis/2026-06-15-reward-efficiency-proof-packet.md:779-790@P`).
- **No uniformly scaled host was ever compared.**
- **No multi-seed replication** was found.
- **Validation and reward used the official CIFAR test split**
  (`src/esper/simic/training/vectorized_trainer.py:1140,1182,1366@P`; the split is set in
  `vectorized.py:1410-1453` and `utils/data.py:416@P`; E26
  `docs/architecture/decisions/ADR-003-sealed-test-evaluation.md:19-22@bb9d963`).

## 2. Where the current pathway has drifted

"Direction" says whether the drift makes the original claim easier or harder to support, or
leaves it the same.

| # | Original | Simic now | Direction | Evidence |
|---|---|---|---|---|
| D1 | Tamiyo chooses **where** [HLD:115,1697-1703] | One fixed site after stage 2 (`experiments/kernel_demo.py:603`). Esper-lite already used fixed slots (EL `docs/plans/2025-11-26-multi-slot-kasmina-design.md:17-24@0ee3a001`). S1 plans 2 sites for G5 (`spikes/2026-10-09-controller-pathway/S1-learning-and-gates.md:335-341`) | **Easier**: L3 loses its where-diagnosis | — |
| D2 | Tamiyo chooses **when**, during initial training [HLD:734] | One decision after epoch 1 (D5, `0057:103`) | Easier; the evidence so far runs against L1's timing | Rung 4: T0 best, "the best schedule is the one most like static" (`results/2026-10-09-rung4-timing-horizon.md:18-21`). Static is ahead of the graft by +0.046 on `under_normalized` (`results/2026-10-11-fleet-c1.md`). **A hypothesis to state as one:** handicaps built in from step 0 make static from step 0 the natural optimum. Part of this evidence may reflect how the hosts were built, not the loop |
| D3 | Bottlenecks "as they emerge during the training process" [HLD:175-176]; the first Esper-lite host was unimpaired (EL `poc.py:96-112@0ee3a001`) | Hosts with **authored handicaps from step 0**, designed per blueprint. "Each episode samples one canned handicap… Fan winner (by design)… a pathology that never separates the arms is retuned" (`git show 25be1da:docs/superpowers/specs/2026-08-09-kernel-demo-design.md`, lines 49-64); "Esper-style crippled hosts, each paired with a designed repair seed" (`0046:19-20`). Esper-lite did the same later (`cifar10_blind`, EL `src/esper/runtime/tasks.py:214-218@4de8a0a2`) | **Easier**: designed-winner circularity (`0057:242-243`). Synthetic, not emergent | — |
| D4 | Long training (Esper-lite: lr 0.01, 150-epoch episodes, one shuffled CIFAR pass partitioned across environments; hosts about 6k and 77 parameters; EL `leyline/__init__.py:90,622@P`, `utils/data.py:234,505-520@P`) | 4,096 fit examples, 10 epochs, batch 32, lr 0.05 constant with Nesterov 0.9, weight decay 5e-4, random crop and flip (D9, `0057:107`; `kernel_demo.py:153,319-343,877-890`; `docs/prereg/fleet-c1.json:34`) | **Different, and not shown to be capacity-insensitive** | From the published per-arm summary: 2× parameters (about 1.41× widths) lowers late CE by 0.018–0.032 nats and adds about 1.1 accuracy points on the BatchNorm hosts. Mean dev CE is still falling 0.02–0.03 nats per epoch at epoch 10 (e.g. `channel_starved` 1.353 → 1.316 → 1.293). So the 10-epoch endpoint is **before convergence at constant lr**, and these hosts **do respond to capacity**. What it implies for this design: a ≤ 1.10× injection's λ-predicted gain is ≤ 0.004 nats. The 0.05 bar is about two doublings of uniform parameters. Data-bound, step-bound and optimisation-bound cannot be told apart from published records (§11) |
| D5 | Foil: uniform over-provisioning [HLD:22,125,175]. Quantitative criterion: parameters used against full fine-tuning [HLD:162,215] | Uniform scale-up, with static as an oracle ceiling (`vision.md:59-61`), recorded as "made after seeing data" (`adr/0019-reopen-comparison-uniform-scaleup.md:63-65`) | **Matches the HLD's motivating foil.** It differs from its fine-tuning-style quantitative criterion. Chosen after the data | — |
| D6 | First phase: a static, human-curated library, Karn stubbed [HLD:2217-2221]; later, Karn generates [HLD:116] | Four human-authored seeds through G5; generation is "beyond G5" (`0057:299-300`) | **Parity with the original's first phase.** L6 is untested | All four seeds contain a normaliser (`kernel_demo.py:637-734`): `norm` GroupNorm, `attn` LayerNorm, `conv_light` and `conv_heavy` BatchNorm. Rung 3: static `conv_heavy` repaired `under_normalized` about as well as `norm` (−0.143 vs −0.144, `results/2026-10-09-graft-capture-v2.md:40`). `conv_heavy`'s bottleneck is fixed at 52 channels (`kernel_demo.py:710`) |
| D7 | Test split used for validation and reward (§1) | Dev only; outer and test data owner-gated | **Stricter** | — |
| D8 | No multi-seed replication found | 768 seeds per host, paired | **Stricter** | — |
| D9 | Shaped reward [HLD:1759-1771] | Counterfactual branches against a measured no-op | Stricter attribution | — |
| D10 | MLPs, CNNs, Transformers [HLD:217]; transfer across projects (manifesto :74) | One CNN family; G5 interpolates within one generator (`S1:544`) | **Easier**: L5 narrowed | — |
| D11 | Repeated keep-or-cull cycles with rollback (L7) | One decision per run (D5); G4 "does not test compounding" (`0057:278`); retirement untested (`S1:545`) | **Easier**: L7 untested by G0–G5 | — |

**Drift inside Simic itself** is corrected in §13. Two items matter most:
- **`mild` was never a non-designed host.** It is the kernel spec's restraint host, and its G1
  graft was its `DESIGNED_WINNER`, `conv_light` (`kernel_demo.py:552`; `0057:192-193`). So **no
  non-designed host has yet been tested**.
- **The checkpoint's candidate steer is withdrawn.** It came from seeing that the
  missing-normalisation host passed.

## 3. What the evidence establishes, and what it does not

| Evidence | Establishes | Does not establish |
|---|---|---|
| Instrument: screen v1, G0 golden, bitwise pairing (`results/2026-10-08-bounded-screen-v1.md`; `results/2026-10-09-atlas-g0-golden/README.md`; `results/2026-10-11-fleet-c1s.md`) | Paired differences resolve to about ±0.018; replay is bitwise | Anything about the claims |
| Deficit on `under_normalized` (positive control v2; Fleet C1 static +0.142) | One authored handicap that library structure repairs | That such deficits arise during training (D3). Any seed type repairs it (D6) |
| Fleet C1 G1 on `under_normalized`: graft − 2× scale-up = −0.071 | **L2 at bounded scale on one designed host**, at a fixed site, with a designed seed, after epoch 1, against the HLD's own foil (D5) | L1's timing: static is ahead by 0.046 (but see the D2 hypothesis). L3–L7 |
| Fleet C1 and C1-S on `channel_starved`, `no_spatial_mix`, `mild` | With each host's **designed seed only**, static did not improve these three designed hosts by more than 0.05. `no_spatial_mix` gained +0.020 [+0.014, +0.026], real but below the bar. On these hosts graft ≈ static, and uniform 1.25× ≈ graft; uniform 2× is ahead of the graft by 0.018–0.032, about the λ price | That no repairable deficit exists on them: other seed types, sites, horizons and data sizes were not tested |
| Rung 4: no detectable per-seed timing headroom on one host (`0057:50-59`) | Timing alone offers little to learn on that host | Anything about between-host headroom |
| λ = 0.0271 | The price of uniform widening of these 117k–161k hosts in this regime | Its value for much smaller hosts or seed injections; any other regime |
| Untested | — | **L3, L4 (C2), L5 (C3), L6, L7, and any naturally occurring bottleneck** |

## 4. Proposals that would only make the benchmark easier

I reject each of these:

- **B1. More missing-normaliser variants** to reach two passes. Every seed carries a normaliser
  (D6).
- **B2. Designing new handicaps paired with the blueprint that fixes them,** or retuning a
  handicap until it separates the arms (D3).
- **B3. Loosening the screen**: below 0.05 nats, a weaker lower bound, accuracy instead of CE, or
  dropping the 10% divergence cap.
- **B4. Choosing horizon, data size or regime per host after seeing results.**
- **B5. Swapping C1's comparator** back to static or no growth.
- **B6. Screening in rounds until two hosts pass,** or leaving failed candidates out of the
  report.
- **B7. Best-of-several seed types on the same data that is tested.** The registered mean bar is
  a point threshold, so a maximum over seed types inflates it however the lower bound is
  corrected (`0046:30-33` flagged the same).
- **B8. Reusing dev or test data for selection** beyond the registered screen.
- **B9. Choosing candidates from Fleet C1 or C1-S outcomes** (§13, the withdrawn steer).
- **B10. Reading a screen pass as evidence for the loop** (§5).
- **B11. Passes that added parameters could carry.** λ prices uniform widening at 0.012–0.017
  nats for `conv_heavy` on the counted hosts. That is below the bar. But a seed placed at a
  bottleneck may earn more per parameter than widening does, so the cap is a **precaution, chosen
  after C1** (§9).
- **B12. Hand-picked points inside pre-C1 ranges.** The fix is a seeded draw.
- **B13. A sample size that adapts to outcomes.** n is fixed here.
- **B14. A counting class invented after the data** ("honest-small"). Such hosts are descriptive
  only.
- **B15. Training family hosts before G5's host list is fixed.** The fix is the G5 proposal in §6,
  binding only on John's signature.

## 5. Diagnostic screening is not proof of the loop

The family screen measures hosts. It asks whether a randomly drawn set of **authored** handicaps
contains one that a small library injection at the fixed stage-2 site reduces, in this regime. At
most, a pass makes later tests possible.

**A screen pass is not evidence for L1–L7, C2 or C3, nor for naturally occurring bottlenecks.**

| Gate | What it tests | Original claim |
|---|---|---|
| G0 instrument and replay (`0057:143-185`) | Measurement validity | Precondition for all |
| G1, C1 against uniform scale-up (`0057:187-211`) | Targeted graft against width at matched or greater cost | **L2** against the HLD's foil; on designed hosts only. It does not show that growing beats installing (PDR-0057 D4, `0057:102`) |
| Deficit screen (`0057:212-216`) and **this family screen** | Does an authored handicap admit a small library repair? | **Diagnostic.** Tests no claim |
| G2 / G2′, headroom (`0057:231-243`) | Is there anything for a policy to learn? | Learnability precondition for **L3/L4** |
| G3, offline learning (`0057:245-266`) | A learned controller beats the frozen best fixed policy a\* | **L4**; for L3, whether to act at one fixed time (D2) and which seed, not where (D1) |
| G4, live single decision (`0057:268-286`) | The same, live, with the admission chain | **L4** live; L1 for one decision |
| G5, transfer (`0057:288-297`) | Held-out hosts from a frozen family; C1 on held-out hosts | **L5** within one CNN family (D10); **L3** as "the first real test of pathology recognition" (`0057:291-292`); L2 on new hosts |
| Generated structure, Momir L1+ (`0057:299-300`) | Generated, not selected | **L6**; beyond this pathway |
| — | Repeated keep-or-cull cycles | **L7**: **untested by any gate G0–G5** |

## 6. The screen design, if John chooses it

**Question.** In a host family drawn at random from authored handicap classes, does at least one
class other than normalisation contain a host whose deficit a small library injection reduces by
the registered bar? "Small" means at most 1.10× the host's parameters. The regime is unchanged:
4,096 fit examples, 10 epochs, the corrected static arm born at τ.

**The generator (G-0)** ([`generator.py.txt`](generator.py.txt)) is S1's generator (`S1:335-341`)
plus S3's depth class (`S3:331`), made concrete. The concrete choices were made **after C1's
analysis** and are listed as such in §9:
- **Classes:** capacity, spatial, depth.
  - Normalisation is not drawn: it is already represented by `under_normalized`, and drawing it
    again is B1.
- **Stage:** 1 or 2, uniform. The slot stays after stage 2.
- **Base width:** b ~ U[0.75, 1.25], widths rounded to multiples of 8.
  - The norm seed is `GroupNorm(8, w2)`.
  - `0057:159` and `S3:333` already say multiples of 8.
  - `atlas_hosts.WIDTH_STEP = 4` is untouched (§12).
- **Severity:**
  - capacity: the impaired stage's middle width = round8(r × that stage's output width),
    r ~ U[12/64, 48/64];
  - spatial: the impaired stage's convolutions are 1×1;
  - depth: the impaired stage has one convolution instead of two. That is milder than S3's
    all-stage `shallow`.
- **Draw:** numpy `default_rng(15000)` (PCG64, numpy 2.5.1), two hosts per class, class-major,
  stage then b then r for every host.
- **The record is [`draw.md`](draw.md), not a re-derivation.** numpy streams are not guaranteed
  across versions, and Python rounds half to even. The plan pins the hosts as explicit configs.

**The drawn hosts.** "Seeds ≤ 1.10×" lists the realised multiples of the seed types eligible to
count:

| Host | Class | Stage | w1/w2/w3 | Impaired mid width | Parameters | Seeds ≤ 1.10× | Role |
|---|---|---|---|---|---|---|---|
| F1 | capacity | 1 | 24/64/80 | 16 | 159,722 | `norm` 1.001, `attn` 1.027, `conv_light` 1.056 | counted |
| F2 | capacity | 1 | 24/56/72 | 8 | 126,514 | 1.001, 1.030, 1.062 | counted |
| F3 | spatial | 1 | 24/64/80 | — | 156,498 | 1.001, 1.028, 1.057 | counted |
| F4 | spatial | 2 | 24/56/72 | — | 94,594 | 1.001, 1.040, 1.082 | counted |
| F5 | depth | 2 | 32/80/96 | — | 186,826 | 1.001, 1.029, 1.059 | counted |
| F6 | depth | 1 | 24/64/80 | — | 156,450 | 1.001, 1.028, 1.057 | counted |

`conv_heavy` is over the cap on every host (1.372× on N0 up to 1.556× on F4).

**What the draw implies, stated before any data:**
- **Four of six counted hosts are impaired at stage 1** (F1, F2, F3, F6). The slot sits after
  stage 2, so a seed there can at most **compensate downstream** for what stage 1 never computed.
  My prior for stage-1 hosts is lower than for stage-2 hosts. **Results are reported separately
  for each stage.**
- **Stage-1 capacity is mild and quantised.**
  - F1 removes 1.2% of the parameters.
  - At w1 = 24, the middle width can only be 8 or 16. At w1 = 16, rounding can make it equal the
    output width, which is no impairment. An assertion catches that (§12).
  - Capacity at stage 2 was not drawn.
- **F4 is close to C1's `no_spatial_mix`**, which gained +0.020 with `attn`. A confirm through
  `attn` on F4 is a **redrawn designed pair** (`kernel_demo.py:546-551`) and is labelled so.
- **No per-host designed seed, but the classes and the library were designed together.** G-0's
  classes are the kernel-demo pathologies (`S1:338`). The cap removes capacity's designed winner
  (`conv_heavy`) but not spatial's (`attn`). Any confirm made through its class's designed winner
  is labelled.

**What a counted confirm would mean** (morphogenesis reviewer's wording, adopted). A confirm adds,
at most, one authored handicap class, drawn at random severity, whose deficit a ≤ 1.10× library
seed at the fixed stage-2 site reduces in this regime, with its gain reported against N0.
- For stage-1 hosts this is downstream compensation, not repair at the bottleneck and not a test
  of where.
- It is not evidence that such deficits arise naturally during training.
- It is not evidence of the closed loop (decide, graft, evaluate, fossilise or cull), which no gate
  from G0 to G5 tests.
- A spatial confirm via `attn` is a redrawn designed pair.

**Descriptive hosts, never counted** (B14). Two honest small hosts: the reference architecture,
unimpaired, at reduced width. They are the closest in kind to the founding principle and to
Esper-lite's `cifar_baseline` ("~6K parameters", EL `tasks.py:105-120@d2c139e9`; docstring
expectations, never measured). But they were chosen after C1, so **the screen cannot produce
counted evidence on the founding principle.**

| Host | Widths (× reference) | Parameters (× reference) | Realised multiples of `norm` / `attn` / `conv_light` / `conv_heavy` |
|---|---|---|---|
| S1 | ×0.5: 16/32/40 | 43,242 (0.27×) | 1.002 / 1.051 / 1.104 / 1.697 |
| S2 | ×0.25: 8/16/16 | 9,186 (0.057×) | 1.004 / 1.122 / 1.253 / 2.645 |

- **No λ-predicted gain is attached.** λ was fitted on uniform widening of 116.6k–161k hosts,
  2.7–17.5× larger. Applied to these hosts or to seed injections, it is a reference null, not a
  prediction.
- **S2 is capacity-limited by construction**, so its no-growth arm is confounded with
  convergence.
- **No host below 117k parameters has been run under this protocol.** A no-growth health gate
  (§8) and one S2 seed in the dry run come first.
- **The width ladder** (S2, S1 and the full-width reference, no growth) is a descriptive look at
  D4 at one untuned lr. It cannot settle D4.

**Controls:**

| Control | Arms | Role | What it can and cannot show |
|---|---|---|---|
| **Reference at full width** (N0) | Same two-phase rule as counted hosts | **Descriptive, not an instrument check.** Reading: `reference_gain` or `reference_no_gain`, reported to John | "Unimpaired" is relative to a chosen reference. A confirm on N0 is the original's own target case, augmenting a capable host (EL `tasks.py:105-120`), not an invalid screen. A non-confirm licenses only "the best eligible seed's generic benefit is probably below about 0.045": with a generic benefit of 0.04, N0 fails to confirm 90% of the time. It **cannot** show that N0 has no repairable bottleneck |
| **Descriptive contrast** | — | For each confirmed host: its phase-2 gain minus N0's gain for the same seed type, with a CI. N0's estimate is its phase-2 estimate for its own chosen seed type, and its phase-1 estimate (unbiased) for any other | Shows how much of a confirm exceeds generic structure benefit on the reference. It does not decide the reading |
| **Positive anchor:** `under_normalized`, fresh seeds 15001–15096 | No growth + `norm` | Instrument: must pass (C1: +0.142) | Catches gross failure only |
| **Pairing:** `under_normalized` on C1 seeds 10001–10048 via the kernel path (`host_cfg=None`); and `channel_starved` and `no_spatial_mix` on 16 of those seeds via the **new class builders** | No growth + static (`static_calibrated` on the BatchNorm hosts) | Instrument: bitwise equal to the Fleet C1 and C1-S records | Proves the new registry reproduces old hosts. The hold-identical list is in §12 |
| **Zero-function static seed** (CPU, no GPU) | — | Instrument | Predicate named now: per-epoch dev metrics, `host_state_sha256` and `host_parameter_sha256` equal to no growth. Full-record equality cannot hold: slot state, optimizer groups and installed parameters differ by construction |

**Screen rule for a counted host.** The registered thresholds are unchanged: mean gain > 0.05
nats, 95% two-sided lower bound > 0, static divergence ≤ 10%. At these spreads the lower bound
never binds (it would need an sd above about 0.35), so the rule is in effect "mean > 0.05".
1. **Selection (phase 1):** training seeds 15001–15048. Arms: no growth plus every eligible seed
   type. The chosen seed type is the eligible one with the largest mean gain; a tie goes to
   library order. Its phase-1 mean is biased upward by about 0.01 and is never pooled with phase 2.
2. **Confirmation (phase 2):** training seeds 15049–15240 (192). Arms: no growth plus the chosen
   seed type only. The host **confirms** if the registered thresholds hold on these seeds.

The choice is made inside the run and sealed; nobody sees it (§8).

**How strict this is** (statistics reviewer):
- **Per host.** The false-pass rate is the nominal rate for the chosen seed type, and never above
  that of pre-naming the best eligible seed type. It has **less power** than an oracle pre-naming:
  - true gains (0.055, 0.045, 0.04) confirm with probability 0.55, against 0.74 if the best were
    pre-named;
  - true gains (0.06, 0.05, 0.03) confirm with 0.78, against 0.90.
- **Shared data.** The phases use separate training seeds but the same pinned fit and dev sets.
  The estimand is conditional on those sets.
- **Near the bar.** At n = 192 and sd 0.11 the 95% half-width is about 0.016 (0.011–0.018 for sd
  0.08–0.13). The rule cannot tell a true gain of 0.04 from 0.05: the expected confirmed
  estimates are 0.054 and 0.056. Its indifference zone is roughly [0.03, 0.07], against roughly
  [0.04, 0.06] at Fleet C1's 768 seeds.

| True gain of the chosen seed type | Confirms, n = 192 | Confirms, n = 768 |
|---:|---:|---:|
| 0 | ≈ 0 | ≈ 0 |
| 0.03 | 0.006 | ≈ 0 |
| 0.04 | 0.10 | 0.006 |
| 0.05 | 0.50 | 0.50 |
| 0.06 | 0.90 | 0.994 |
| 0.08 | ≈ 1.00 | ≈ 1.00 |

Larger n does not fit the cap: confirmation at n = 384 would need about 19 GPU-hours, and at 768
about 33 (§7).

**"At least one of six confirms": an assumption, a bound, and a calibration.** Suppose every
counted host's chosen seed type had the same true gain. The statistics reviewer's addendum
separates three things:
- **The independence heuristic,** 1 − (1 − p)^6. It assumes the six host-level estimation errors
  are mutually independent, not merely uncorrelated, along with an exact sd and every host at
  exactly that gain. **Independence is an assumption, not an established fact.**
- **Bounds that hold under any dependence:** max p_i ≤ P ≤ min(1, Σp_i).
- **The only joint calibration available.** A seed-level bootstrap of Fleet C1's four hosts, with
  the same seeds resampled across hosts, puts the any-of-four exceedance at **0.97–1.00 times the
  independence prediction** (95% intervals [0.968, 1.004] at the 0.04 threshold and [0.983, 1.009]
  at 0.03). That is consistent with independence or a weak positive dependence, which would lower
  the figure.
  - **Low pairwise correlations are descriptive, not a calibration.** Per-seed gain correlations
    of 0.009–0.054 (Fisher 95% CIs within [−0.062, +0.124]) do not calibrate a joint event.
  - **It cannot cover:**
    - the six drawn hosts, which are different architectures, with F1, F3 and F6 near-identical
      layouts;
    - six hosts rather than four;
    - any component common to all hosts that comes from the shared pinned fit and dev data, which
      is unmeasurable from published summaries;
    - tail dependence, which can differ from linear correlation;
    - the phase-1 choice, which adds a shared ingredient.

| sd | Gain 0.03: lower bound / independence / upper bound | Gain 0.04: lower bound / independence / upper bound |
|---|---|---|
| 0.08 | 0.0003 / 0.002 / 0.002 | 0.04 / 0.22 / 0.25 |
| 0.11 | 0.006 / **0.035** / 0.035 | 0.10 / **0.48** / 0.62 |
| 0.13 | 0.017 / 0.095 / 0.099 | 0.14 / 0.60 / 0.86 |
| 0.16 | 0.04 / 0.22 / 0.25 | 0.19 / 0.72 / 1.00 |

In words, for sd 0.11:
- if every counted host's chosen seed type had a true gain of 0.04, the probability that at
  least one confirms is **between 0.10 and 0.62 whatever the dependence**, and 0.48 if the
  errors are independent;
- at a true gain of 0.03 it is at most 0.035;
- across sd 0.08–0.16 the range at 0.04 is 0.04 to 1.00;
- the sd for the new classes is not known, and phase 1 cannot pin it down (C1's sd within
  48-seed blocks ranged from 0.068 to 0.148).

These are scenario values, not a family-wise error rate. A host with a true gain of 0.04 that
confirms is not a false positive about whether a deficit exists. It is a pass below the bar.

**A label that decides nothing.** For each confirmation, the report states whether its 95% CI
excludes 0.05:
- a `family_viable` reading that rests only on CIs straddling 0.05 goes to John as a
  **boundary reading**;
- a confirm with mean 0.05–0.06, or a fail with mean 0.04–0.05, is reported with its interval as
  near-boundary;
- the binary reading and the thresholds are unchanged.

**Counting.** The reading counts passing **classes**: normalisation (held by `under_normalized`),
capacity, spatial and depth. `family_viable` means at least one of capacity, spatial or depth has
a confirmed host. In general that is stricter than counting hosts; on this draw it is equivalent,
because no normalisation host is drawn. Stage-1 and stage-2 confirms are reported separately.

**Seeds and data:**
- **Training seeds** 15001–15240 for this screen, bounding PDR-0057's open "15001+"
  (`0057:340-341`). The anchor's 15001–15096 overlaps the counted hosts' seeds by design.
- **Pairing seeds:** 10001–10048, already seen.
- **Dry-run seeds:** outside every reserved range, as C1's 9903–9905 were.
- **Draw seeds** 15000 and 16000 are numpy draw seeds, a separate namespace from training seeds.
- **Data:** the same pinned fit and dev data as Fleet C1. Outer and test data are not read.

**G5's report hosts: a proposal, binding only on John's signature.** At plan freeze, before any
screen data:
- draw G5's list from G-0 with draw seed 16000, with the normalisation class added and two slot
  sites (`S1:335-341`);
- define host identity as a config hash over class, stage, widths, middle width, kernel, convs,
  BatchNorm and gain;
- exclude every "seen" host (F1–F6, S1, S2, N0, and C1's four hosts) by reject-and-continue;
- commit the list.

Collisions are likely (about 0.16–0.19 per class by rounding), so the rule matters. PDR-0057 asks
for 32 report hosts (`0057:293`).

## 7. Compute budget

Two bases for the cost of an arm, both from published records:
- **Conservative:** 9.3 s per arm. Fleet C1-S measured 8.59 s per run; Fleet C1 6.0 s per arm.
- **Fitted (systems reviewer):** about 11 s fixed per unit (process) plus about 5.1 s per arm,
  with one unit = one training seed covering every host in that phase.

**Arm-seeds:**
- counted hosts, 6 × (48 × 4 + 192 × 2) = 3,456;
- N0, 48 × 4 + 192 × 2 = 576;
- honest-small, 2 × 48 × 5 = 480;
- anchor, 96 × 2 = 192;
- `under_normalized` pairing, 48 × 2 = 96;
- pairing extension, 16 × 2 × 2 = 64;
- **total 4,864.**

| Basis | Screen | Whole-pipeline dry run, twice | Total | Wall time on two GPUs |
|---|---:|---:|---:|---:|
| Conservative | 12.6 GPU-h | about 0.9 GPU-h | **about 13.5 GPU-h** | about 6.8 h |
| Fitted | about 7.8 GPU-h | about 0.9 GPU-h | about 8.7 GPU-h | about 4.4 h |

**Hard cap: 15 GPU-hours,** measured as summed GPU occupancy across every launch.
- Headroom is thin only under the conservative basis.
- The CPU is shared with Sultai, which stretches wall time.

**Beyond GPU time,** the screen needs:
- the §12 engineering;
- a pre-launch review of the plan, the analysis module and the dry run;
- John's attention, which PDR-0057 calls the binding constraint (`0057:116`).

**Superseded estimate:** the checkpoint's "about 4 hours" is withdrawn advice (§13). It assumed
designed winners and two arms per host.

## 8. Go/no-go and stopping rules

**Before any GPU time:**
- John chooses this option (§11) and signs this design or a revision of it, including the §9 bar
  movements and the G5 proposal;
- the §12 prerequisites are built and tested on CPU;
- the pre-launch review (§10) endorses;
- an in-session sketch goes to John (PDR-0053);
- **John's GPU grant covers the whole pipeline at the cap rate.** It can be split: one grant for
  the dry run, then a mechanical go/no-go, then the screen.

**Instrument checks** (any failure → `instrument_failure`, no reading, back to John):
- the whole-pipeline dry run, twice with the GPU order swapped, is byte-identical;
- pairing is bitwise, with the driver and runtime checked against Fleet C1's before any GPU time;
- the anchor passes;
- the zero-function predicate holds (on CPU);
- failed units stay within integer limits stated per phase, with their denominators.

A failed dry run is fixed and re-run. It does not use up the round.

**Health gate** (descriptive hosts): finite loss, a reported per-epoch slope, and the
active-channel fraction for every no-growth arm. An honest-small host that fails it is reported
as untrainable at this lr. It is not dropped silently.

**Readings, all returned to John:**
- `family_viable`: at least one non-normalisation class confirms, marked as a boundary reading
  where it applies. PDR-0057's consequence is a fresh owner decision, not Fleet A automatically.
- `no_family`: no non-normalisation class confirms. PDR-0057's consequence is "rebuilt or the
  pathway stops (John)". **The choice stays with John.** My recommendation is in §14.
- `reference_gain` or `reference_no_gain` (N0) and the contrasts are reported alongside. They
  decide nothing.

**Interruptions:**
- **Pre-emption pauses the run.** It resumes under the existing identity check (same plan,
  module and commit), with a declared maximum pause, and nothing is opened during the pause.
- **"Abandoned"** means a run that cannot resume within the maximum pause. It **uses up the
  single round** and returns to John as no reading. That removes the exit hatch without making a
  stop automatic.
- **The cap.** If the cost model (fitted on the dry run and re-projected as the run goes)
  projects the cap would be crossed, no new unit starts. A terminal stop marker is written that
  both resume and analysis refuse. A capped run has no reading and also uses up the round.

**Single round.** No second screening round, and no new draw, without a new owner decision and
new seeds. The round's report stands in full, failures included.

## 9. How this design moves the bar

PDR-0057 records that "the bar has only ever moved in the direction of continuing"
(`0057:67-77`). Every move below was made after C1's data was seen, so each is owner-gated
(`0053:47-48`), even where it is stricter.

| Move | When | Direction | Note |
|---|---|---|---|
| Rebuilding after a registered fail | After C1 | Towards continuing | A registered option (`0057:212-216`). It makes six new attempts at the second pass: at a true gain of 0.04 on every counted host, one confirms with probability 0.10–0.62 under any dependence (0.48 assuming independence). C1's design with three more hosts at 768 seeds would give about 0.018 |
| One seed type per host chosen on separate training seeds | After C1 | Per host: never looser than pre-naming the best eligible seed type, with less power. **At family level: far looser than C1** | Removes per-host designed seeds |
| Counting classes instead of hosts | After C1 | Stricter in general; equivalent on this draw | — |
| Eligibility cap of 1.10× | After C1 | Stricter; a precaution (B11) | 1.10× is C1's smallest declared scale-up step |
| G-0 concretisations: depth per stage (milder than S3's all-stage `shallow`), normalisation not drawn, the stage-1 starvation ratio, width step 8 | After C1, before any family data | Depth per stage is milder; the rest neutral | The S1 and S3 ranges predate C1 (`4b70653`, 2026-10-09; C1 analysed 2026-10-11 14:48) |
| Honest-small hosts | After C1 | Descriptive only | Never counted |
| N0 made descriptive | Panel, before any data | Neutral | It was an invalid instrument check |

## 10. Review before any launch

This design was reviewed by an independent eight-specialist panel; see
[`panel-review.md`](panel-review.md).

If John chooses the screen, the same eight remits review the built plan, the analysis module and
the dry-run records before the screen's GPU time:
1. statistics;
2. training regime;
3. morphogenesis;
4. implementation correctness;
5. replay and provenance;
6. systems and compute;
7. citation and original-claim fidelity;
8. adversarial.

Each must endorse, or endorse with changes that are all taken, with **no unresolved blocker**.
Disagreements go to John.

## 11. The options, at parity

All four are John's to choose. None has been chosen.

| Option | What it is | What it would add | What it would cost | What it leaves |
|---|---|---|---|---|
| **A. Stop** | Close the controller pathway now, recorded in a PDR with re-entry conditions | Nothing new | No GPU time, no source change | C1 published, narrowed to designed pathologies (with the §13 errata); λ frozen; the comparators and λ available to Sultai if wanted; this drift analysis |
| **B. Defer** | Make no decision now. The pathway stays open, with no spending, while the GPU is with Sultai | Time, and possibly Sultai evidence | Nothing now. The question returns later | Everything as now. The rebuild branch stays open by default |
| **C. Screen, then decide** | §6–§8, after the §12 prerequisites and the pre-launch review | Whether any of three authored, non-normalisation handicap classes admits a small library repair at the fixed site; descriptive honest-small and N0 readings | §12 engineering, the review, then about 8.7–13.5 GPU-h (cap 15) and John's time | A result from one round. Even `family_viable` feeds Fleet A (about 22 h) and G2′ (about 35 h), which cannot reach L1's emergent bottlenecks or L7 |
| **D. The regime question** | Separate data-bound, step-bound and optimisation-bound before any host family | Whether capacity effects grow with horizon, schedule or data, which is D4 | Options below; a rung-parameter change (`0053:42-51`) | A better-posed host question, or a reason to stop |

**What D could involve,** each a separate owner decision, with rough cost multipliers per arm:
- **Step- or epoch-bound:** 20-epoch no-growth and 2× arms, about 2×. Rung 4 already reports that
  the graft-vs-static gap closes at 20 epochs (`results/2026-10-09-rung4-timing-horizon.md:8-14`;
  `0057:49`), so horizon is the cheaper lever.
- **Optimisation-bound:** cosine-annealed 10-epoch no-growth and 2× arms, about 1×. The current lr
  is constant (`kernel_demo.py:877-880`).
- **Data-bound:** look at the train–dev gap. Per-epoch train CE is in the sealed run directories,
  so the owner would have to check it. Rung 4's 20-epoch arms show a late dev-CE rise in 117/756
  static runs against 47/768 no-growth (rung 4 report :144-160).
- **More fit data:** about 11× more training steps at 45k examples (1,280 → about 14,060). For a
  family-screen-sized study that is on the order of 130 GPU-h, and it would need a re-registered
  cap.
- **Comparisons with Esper-lite** should be made in optimizer updates and per-host examples, not
  epochs (D4).

## 12. Prerequisites for C (not to be done now; no dates)

**Without these the screen cannot run as written.**

**Runner:**
- **Seed width.** Build the seed at `host.feat_channels` instead of the hard-coded 64
  (`atlas_static.py:61`, `atlas.py:191`), and let `_require_slot` accept any w2
  (`atlas.py:254-257`).
  - Behaviour stays bit-identical at 64, so the C1 and C1-S records are unchanged.
  - The frozen `bounded_comparison.py` (`:546,1193`) stays untouched; it is not on the corrected
    static arm's path.
  - A CPU test checks the birth ratio is 0.05 on a w2 = 56 host.
- **Host configs.** `HostConfig` has no stage-1 middle width, stage-1 kernel or per-stage conv
  count, and stage 1 is `_make_stage(3, w1, w1, …)`.
  - Adding fields would change `config_hash` (`atlas_hosts.py:121-122`) and `host_label`
    (`atlas.py:252`) for every existing config.
  - So use a separate `FamilyHostConfig`, or hash-stable defaults, with a test that C1's hashes
    are unchanged.
  - Do not change `atlas_hosts.WIDTH_STEP`: C1's scale-up configs depend on it
    (`atlas_hosts.py:25,93`; `c1_study.py:331`; `tests/unit/test_atlas_hosts.py:49`). The family
    generator owns its own step of 8.
- **Registry.** Choose between an `AtlasSpec` registry and passing a base `spec.host` plus
  `host_cfg`, as C1 did. `RunSpec.validate` rejects hosts outside `PATHOLOGIES`
  (`bounded_data.py:47`). Guard `DESIGNED_WINNER` lookups for family hosts.
- **Depth stages.** These have four layers. `Host.attach_stat_hooks` (`kernel_demo.py:620`) and
  `atlas_telemetry._run_stage` (lines 74-80) assume index 5 is the last ReLU. That is an
  IndexError, or a **silent default** in telemetry. Keep depth stages away from both, or give the
  stage a named last ReLU.
- **Assertions.** Middle width < output width for every capacity host. A generator-parity CPU
  test: for all nine hosts, the generator count = `parameter_count` = Σ `numel` of the built host.
- **Zero-function control.** Inject it as a test-only `SeedDelta`, with an exemption from
  `_check_end_state` (`atlas.py:216-221,507-516`), using the predicate named in §6.

**Pairing — hold identical:**
- the host's state-dict key names and buffer set;
- the `derive` labels and per-seed load order;
- config and data pins;
- the runtime, including torch, CUDA, cuDNN, driver 580.178.04 and GPU model. `runtime()` does
  not record the driver today (`bounded_comparison.py:360-394`), so check it.

Also:
- pair the anchor through the kernel path;
- pin each seed to its C1 GPU, or declare cross-card equality in scope.

**Launch machinery:**
- **One pinned plan, one fleet, two internal phases** under one `launch.json`. The plan is
  committed up front with the choice rule.
  - Phase 1 writes only a sealed `choice.json`: the chosen seed type per host, the sha256 of the
    phase-1 unit records, and the launch sha. Its hash goes into the launch record, and the
    choice step prints nothing.
  - Phase 2 refuses to start if any report exists. The single final analysis recomputes the
    choice and refuses on mismatch.
  - Provenance: no report predates phase 2's units, and timestamps are monotonic.
  - The fallback is C1-S's parent-pin pattern, with phase 2's plan committed before phase 1
    launches (`c1s_study.py:108-131,373-379`).
- **Units.** One unit = one training seed covering every host in its phase. Failed-unit limits
  are integers, per phase.
- **Cap.** A cost model fitted on the dry run and re-projected during the run; a terminal stop
  marker refused by resume and analysis; no unit starts that would cross the cap. Resumed units
  currently log `wall_s = 0` and killed units are never logged (`c1_study.py:546-558`), so
  occupancy needs its own record.
- **GPU placement.** Map worker slots to the parent's `CUDA_VISIBLE_DEVICES`. Today they map to
  `range(device_count())` (`bounded_screen.py:198-201`; `c1_study.py:536,556`), so a one-GPU grant
  could land on Sultai's card. Refuse a GPU that another project is using. Stop by killing the
  whole process group.
- **Dry run.** The whole pipeline (phase 1, the choice, phase 2, pairing), twice, on out-of-range
  seeds, with the GPU order swapped. Include one S2 seed.
- **Records.** The plan pins hosts as explicit configs, plus numpy 2.5.1 and PCG64 for the
  record.

**Not needed:**
- the registered arm's BatchNorm birth fix (`simic-e3803e8200`), because the screen uses the
  corrected arm;
- a second slot site, which G5 needs but this screen does not.

## 13. Superseded and corrected statements

These records stay unchanged; this table is the correction for this design scope:
- the published notes (`docs/results/…`);
- PDR-0057;
- the spikes;
- the evidence certificate.

Additive, dated errata in those records, following the precedent at `fleet-c1.md:6-8`, would be a
separate decision for John.

| Location | Original statement | Correction | Status |
|---|---|---|---|
| `0057:199`; `S1-learning-and-gates.md:271`; `certificates/2026-10-09-pdr0057-evidence-certificate.md:77` | `mild` is "the honest, non-designed host" | `mild` is the kernel spec's **restraint host**, with a designed conditional winner: `conv_light` (`kernel_demo.py:552`; `0046:27`; current spec `:135-148`; at `25be1da` the row reads "conv-light or **no-op**" (:59); "no-op often wins" is at current spec :140). S3 calls it "slightly narrow, not healthy" (:332). Its G1 graft was `conv_light` (`0057:192-193`), so **no non-designed host has been tested** | Wrong. The PDR text is John's to amend |
| `results/2026-10-11-fleet-c1.md:13,19` | Same wording, repeated | As above | Wrong. Published note unchanged |
| `results/2026-10-11-fleet-c1.md:178-179` | "`mild` has no designed pathology, and that is where the graft did not pass" | As above | Wrong. Published note unchanged |
| `results/2026-10-11-fleet-c1-checkpoint.md:18` | G1 row: "the honest, non-designed host" | As above | Wrong. Published note unchanged |
| `results/2026-10-11-fleet-c1-checkpoint.md:25` | "the honest host had nothing to repair" | With its designed seed, `mild`'s static gain was +0.004 [−0.003, +0.011]. Other seed types, sites and horizons were not tested | Overstated. Published note unchanged |
| `results/2026-10-11-fleet-c1-checkpoint.md:53-56` | The screen-only pilot, "roughly 4 hours" | **Withdrawn, superseded advice.** It used designed winners and could not separate repair from added parameters. It was a recommendation, never approved training | Superseded |
| `results/2026-10-11-fleet-c1-checkpoint.md:84` | "**Rebuild, as the host family, starting with the screen-only pilot.**" | **Superseded advice.** The current recommendation is §14, and it is a recommendation only | Superseded |
| `results/2026-10-11-fleet-c1-checkpoint.md:87-89` | "candidates should vary missing-function pathologies by stage and severity" (the note itself hedged: "a hypothesis to screen, not a finding", :89) | **Withdrawn as a rule for choosing candidates.** It was written after seeing that the missing-normalisation host passed (B9) | Withdrawn |
| My message to John, 2026-10-11, during this panel | "The 48% figure assumes independence. That holds empirically" | **Retracted.** Low pairwise correlations are descriptive. Independence is not established (§6) | Retracted |
| Revision 2 of this proposal | Several overstatements | Corrected in revision 3. The list is in [`panel-review.md`](panel-review.md) | Superseded |

## 14. Recommendation (mine; the choice is John's)

**I recommend A, stop, recorded with re-entry conditions.** B, defer, is close behind; it differs
mainly in whether the rebuild branch stays open by default. The panel did not reach consensus on
framing. One reviewer would present A, B and C at parity without a recommendation, so §11 does
that and this section is labelled as my view.

The reasons the panel's evidence supports:
1. **No host screen tests the loop.** C cannot reach L1's emergent bottlenecks (D3), the
   where-diagnosis (D1), or keep-or-cull closure (L7). It cannot produce counted evidence on the
   founding principle either, because the honest-small hosts are descriptive.
2. **Even the best reading leads into a long chain.** `family_viable` feeds Fleet A (about 22 h)
   and G2′ (about 35 h). That chain keeps D1, D2 and D11 and cannot reach L1 or L7.
3. **Static is ahead of the graft** (+0.046) on the one host that passed. Growing-versus-installing
   is unresolved, and possibly confounded with how the hosts were built (D2 hypothesis).
4. **The re-entry conditions would be:**
   - the regime question (D, D4);
   - a test design that reaches L1's emergent bottlenecks and L7;
   - new evidence from Sultai.

**What I am no longer arguing:**
- the regime as a reason to stop (D4 was overstated);
- "the GPU goes to Sultai" (that is John's allocation, and if anything it argues for B).

**If John wants C,** revision 3 is the version to run, with its reading accepted either way and
its boundary label reported. Before deciding, it is the cheapest evidence that bears on the
re-entry conditions.

## 15. Sources

**Original (archives on nyx).** The citation reviewer re-resolved the main lines.
- [HLD] `/mnt/data/archive/esper.old/docs/architecture/001-high-level-design.md@8d69bec`. Lines
  22, 77, 93, 113, 115, 116, 125, 129, 160-162, 175-176, 215, 217, 227, 235, 240, 330, 691, 719,
  734-738, 1548-1565, 1697-1715, 1736, 1750-1753, 1759-1771, 2217-2221, 2225.
- [PAPER] `/mnt/data/archive/esper-lite/_archive/docs/paper/draft_paper.md@0ee3a001`. Lines
  5-7, 95, 97, 123-127, 215, 450, 472, 474, 509.
- **Esper-lite:**
  - `README.md:79-88@0ee3a001`;
  - `src/esper/poc.py:51-55,96-112,528,614-617,731,750@0ee3a001`;
  - `src/esper/runtime/tasks.py:105-120@d2c139e9`, `:214-218@4de8a0a2`, `:282-296@c4c70f08`;
  - `src/esper/leyline/factored_actions.py:20-34,92-115,108-115,425-434@P`;
  - `src/esper/leyline/__init__.py:90,622@P`;
  - `src/esper/utils/data.py:234,416,505-520@P`;
  - `src/esper/simic/rewards/contribution.py:92-111@P`;
  - `src/esper/simic/training/vectorized_trainer.py:1140,1182,1366@P` and
    `vectorized.py:1410-1453@P`;
  - `docs/plans/2025-11-26-multi-slot-kasmina-design.md:17-24@0ee3a001`;
  - `docs/analysis/2026-06-15-reward-efficiency-proof-packet.md:779-790@P`;
  - `DESIGN_MANIFESTO.md:74,84-102,143-169@8517cca5`.
  - Public mirror at P: <https://github.com/tachyon-beep/esper-lite/tree/0807ccfaa847303d9a65bc4c48ad199f34dd3624>.
- **Esper (E26):** `docs/architecture/decisions/ADR-003-sealed-test-evaluation.md:19-22@bb9d963`.

**Simic:**
- `docs/product/vision.md:21-23,59-61`;
- `docs/product/decisions/0057-controller-training-pathway.md:32-43,49-77,98-107,116,143-300,192-193,199,212-216,242-243,278,291-293,333-389,340-341`;
- `docs/product/decisions/0046-round-two-positive-control-and-graft-plans.md:19-20,27,30-33,86-89`;
- `docs/product/decisions/0053-vision-update-acceptance-gates-and-ladder.md:42-51`;
- `docs/adr/0019-reopen-comparison-uniform-scaleup.md:63-65`;
- `docs/product/spikes/2026-10-09-controller-pathway/S1-learning-and-gates.md:271,335-341,485,542-545`;
- `docs/product/spikes/2026-10-09-controller-pathway/S3-atlas-engineering.md:321-350`;
- `docs/product/certificates/2026-10-09-pdr0057-evidence-certificate.md:77`;
- `git show 25be1da:docs/superpowers/specs/2026-08-09-kernel-demo-design.md` (lines 49-64) and
  the current file `:135-148`;
- **experiments:**
  - `kernel_demo.py:153,319-343,546-554,603,620,637-734,877-890`;
  - `atlas.py:191,216-221,252,254-257,507-516`;
  - `atlas_static.py:61`;
  - `atlas_hosts.py:25,41-122`;
  - `atlas_telemetry.py:74-80`;
  - `bounded_data.py:47`;
  - `bounded_comparison.py:360-394,546,1193`;
  - `bounded_screen.py:198-201`;
  - `c1_study.py:331,489-558`;
  - `c1s_study.py:108-131,373-379`;
- `docs/prereg/fleet-c1.json:34`;
- **results:**
  - `docs/results/2026-10-08-bounded-screen-v1.md`;
  - `2026-10-09-graft-capture-v2.md:40`;
  - `2026-10-09-rung4-timing-horizon.md:8-21,144-160`;
  - `2026-10-11-fleet-c1.md`, `2026-10-11-fleet-c1s.md`, `2026-10-11-fleet-c1-checkpoint.md`;
  - the per-arm summaries `2026-10-11-fleet-c1/` and `2026-10-11-fleet-c1s/arms-summary.jsonl.gz`.

**Review behind this note,** all read-only:
- two research maps;
- one adversarial review of revision 1, and its re-review of revision 2;
- the eight-specialist panel on revision 2 ([`panel-review.md`](panel-review.md)).
