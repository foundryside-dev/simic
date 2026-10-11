# Host-family proposal, measured against Esper's original loop — 2026-10-11

**Design only, for John's review. Nothing here is approved training.** No source change, GPU run
or threshold change follows from this document. Simic's GPU reservation was released at 18:47 AEDT
on 2026-10-11 for Sultai's slot from 19:00. No Simic GPU work is authorised until John
re-authorises it.

It starts from the Fleet C1 checkpoint (PR #44, `70707bb`;
[checkpoint](../../../results/2026-10-11-fleet-c1-checkpoint.md)). Only `under_normalized` passed
the deficit screen, and PDR-0057 registered the consequence: "fewer than two passing hosts means
the host set is rebuilt or the pathway stops (John)" (`0057:212-216`). John's refinement: the
revisit must be mindful of the original Esper-lite loop the project is trying to prove.

**Revision 2.** An adversarial benchmark-shopping review of revision 1 found three blockers, all
taken:
- best-of-four was not stricter than the registered rule;
- the small hosts could pass on added parameters alone;
- one candidate was not impaired.

Its should-fix items were taken too. Where its findings change the design, the text says so.

Contents:
1. The original loop, from primary sources
2. Where the current pathway has drifted
3. What the evidence establishes, and what it does not
4. Proposals that would only make the benchmark easier
5. Diagnostic screening is not proof of the loop
6. The proposed family screen
7. Compute budget
8. Go/no-go and stopping rules
9. How this proposal moves the bar
10. Specialist correctness review panel
11. The clean stop, and the regime question
12. Prerequisites (not to be done now)
13. Pending corrections to published notes
14. Recommendation
15. Sources

Companion files:
- [`generator.py.txt`](generator.py.txt) — the frozen host generator and its draw;
- [`draw.md`](draw.md) — the drawn hosts with their parameter multiples.

**Source keys** (full list in §15):
- **[HLD]** `/mnt/data/archive/esper.old`, `docs/architecture/001-high-level-design.md` at
  `8d69bec` (committed 2025-08-03; header "Version 1.4, 01 July 2025"). It is the earliest design
  document found in the archives, reachable with `git log --all`.
- **[PAPER]** `/mnt/data/archive/esper-lite`,
  `_archive/docs/paper/draft_paper.md@0ee3a001` (v3.0RC1; "Results are placeholders", lines 5-7).
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
- **Lifecycle.** Germinate, train with "zero impact" on the host, graft with an alpha ramp,
  stabilise, evaluate, then fossilise or cull [HLD:1548-1565].
- **Reward.** A shaped reward [HLD:1759-1771]. Training was imitation of a heuristic, then RL
  [HLD:1736,1750-1753].
- **Esper-lite as built.**
  - A factored action space: slot, blueprint (including NOOP), tempo and alpha (EL
    `src/esper/leyline/factored_actions.py:20-34,92-115,425-434@P`).
  - Accuracy-minus-parameter-rent reward modes (EL
    `src/esper/simic/rewards/contribution.py:92-111@P`).
  - "No-Op… The crucial decision to do nothing" is a first-class action [PAPER:474,509].

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

For mapping, I split this into six claims:

| | Original claim | Primary source |
|---|---|---|
| **L1** | In-training repair: a bottleneck that arises while a host trains is repaired by structure grafted during training, improving the final artefact | [HLD:77,93,235,330] |
| **L2** | Parameter efficiency: a given performance for fewer parameters than conventional training | [HLD:240]; target "10 to 100 times fewer parameters… compared to full model fine-tuning" [HLD:160-162] |
| **L3** | Diagnosis: the controller decides if, when, where and how, including doing nothing | [HLD:115,734-738]; [PAPER:474,509] |
| **L4** | Learned beats fixed: a learned policy beats random, heuristic or fixed selection | [HLD:113,2225] |
| **L5** | Generality and transfer: across architectures; policy wisdom that carries across hosts | [HLD:217]; EL `DESIGN_MANIFESTO.md:74,84-102@8517cca5` |
| **L6** | Generated structure: blueprints invented, not picked from a fixed menu | [HLD:116]; Simic `docs/product/vision.md:21-23` |

**The owner's statement** (`0057:32-37`) maps onto L1–L2, L3–L4 and L5: "rather than training a
massive model you start by training a small model and inject extra parameters where you have
issue"; "40->60 with 1.01x parameter increase (proven)… train tamiyo to do (somewhat proven) it in
a target agnostic way (entirely unproven so far)". Two cautions:
- **"Instead of a massive model" has no primary source.** The closest primary text is "without
  wasteful, uniform parameter scaling" [HLD:125] and germination "precisely where the student
  model struggles most" [HLD:129]. That line is about a distillation student, not a model grown
  from small. The HLD's own comparator is fine-tuning or retraining
  [HLD:162,215].
- **"40→60 at 1.01×" is owner recollection with no primary source.** The nearest measured
  analogue is Fleet C1 on `under_normalized`, from the published per-arm summary: mean final dev
  accuracy 42.6% for no growth, 46.7% for the graft, 48.1% for static, at 1.001× parameters. That
  is an exploratory accuracy reading; CE is the registered endpoint.

**What the original record never controlled** (EL):
- no uniformly scaled host;
- no matched-budget static arm; static modes were added in `71ec0b31`, and the proof packet
  reports them missing (`docs/analysis/2026-06-15-reward-efficiency-proof-packet.md:779-790@P`);
- no multi-seed replication (seed 42).

Validation and reward used the official CIFAR test split
(`src/esper/simic/training/vectorized_trainer.py:1140,1182,1366@P`; E26
`docs/architecture/decisions/ADR-003-sealed-test-evaluation.md:19-22@bb9d963`).

The POC table (EL `README.md:79-88@0ee3a001`) compares arms on unmatched training budgets. Its
"from-scratch upper bound" is a static-capacity arm that scored below the bare host
(`src/esper/poc.py:51-55,528,614-617,731,750@0ee3a001`).

## 2. Where the current pathway has drifted

"Direction" says whether the drift makes the original claim easier or harder to support.

| # | Original | Simic now | Direction | Evidence |
|---|---|---|---|---|
| D1 | Tamiyo chooses **where** [HLD:115,1697-1703] | One fixed site after stage 2 (`experiments/kernel_demo.py:603`). Esper-lite had already reduced it to fixed slots (EL `docs/plans/2025-11-26-multi-slot-kasmina-design.md:17-24@0ee3a001`). S1 plans 2 sites for G5 (`spikes/2026-10-09-controller-pathway/S1-learning-and-gates.md:335-341`) | **Easier**: L3 loses its where-diagnosis | — |
| D2 | Tamiyo chooses **when**, during initial training [HLD:734] | One decision after epoch 1 (D5, `0057:103`) | Easier, and the evidence runs against L1's timing | Rung 4: T0 best, "the best schedule is the one most like static" (`results/2026-10-09-rung4-timing-horizon.md:18-21`). Static ahead of the graft by +0.046 on `under_normalized` (`results/2026-10-11-fleet-c1.md`) |
| D3 | Tamiyo identifies "learning bottlenecks" while a host trains [HLD:77]. The first Esper-lite host was unimpaired (EL `poc.py:96-112@0ee3a001`) | Four hosts **designed per blueprint**. "Each episode samples one canned handicap… Fan winner (by design)… a pathology that never separates the arms is retuned" (`git show 25be1da:docs/superpowers/specs/2026-08-09-kernel-demo-design.md`, lines 49-64). "Esper-style crippled hosts, each paired with a designed repair seed" (`0046:19-20`). Esper-lite had the same habit later (`cifar10_blind`, EL `src/esper/runtime/tasks.py:214-218@4de8a0a2`) | **Easier**: designed-winner circularity, named at `0057:242-243` | — |
| D4 | Long training on full CIFAR (Esper-lite; per-host exposure depends on loader mode) | 4,096 fit examples, 10 epochs (D9, `0057:107`) | Harder for capacity claims, possibly to the point of being untestable | Exploratory, mine, from the published per-arm summary: the three BatchNorm hosts' mean dev accuracy is 55.6–56.3% with no growth, and 2× uniform widening adds 1.0–1.1 points; λ = 0.027 nats per doubling. Whether data or epochs bind cannot be separated from C1 |
| D5 | Comparator: fine-tuning or retraining, and random or heuristic selection [HLD:162,215,2225] | Uniform scale-up, with static as an oracle ceiling (`vision.md:59-61`). An owner decision recorded as "made after seeing data" (`adr/0019-reopen-comparison-uniform-scaleup.md:63-65`) | **Harder** than the original, but chosen after the data | — |
| D6 | Karn generates blueprints [HLD:116]. Simic's vision: "generated from the live state" (`vision.md:21-23`) | Four human-authored seeds through G5; generation is "beyond G5" (`0057:299-300`) | Easier: L6 untested | All four seeds contain a normaliser (`kernel_demo.py:637-734`): `norm` GroupNorm, `attn` LayerNorm, `conv_light` and `conv_heavy` BatchNorm. Rung 3: static `conv_heavy` repaired `under_normalized` about as well as `norm` (−0.143 vs −0.144, `results/2026-10-09-graft-capture-v2.md:40`). `conv_heavy`'s bottleneck is fixed at 52 channels (`kernel_demo.py:710`), so on narrow hosts it is a large injection (`draw.md`) |
| D7 | The test split was used for validation and reward (§1) | Dev only; outer and test data owner-gated | **Stricter** | — |
| D8 | Single seed 42 | 768 seeds per host, paired | **Stricter** | — |
| D9 | Shaped reward [HLD:1759-1771]; P `contribution.py:92-111` | Counterfactual branches against a measured no-op | Stricter attribution | — |
| D10 | Generality across MLPs, CNNs and Transformers [HLD:217] | One CNN family; G5 interpolates within one generator (`S1:544`) | Easier: L5 narrowed to one architecture family | — |

**Two Simic-internal drifts that need correcting** (§13):
- **The `mild` label.** PDR-0057 calls `mild` "the honest, non-designed host" (`0057:199`). The
  kernel spec built it as the restraint host, with a designed conditional winner `conv_light` and
  "no-op often wins" (`25be1da` spec lines 54-59; `docs/superpowers/specs/2026-08-09-kernel-demo-design.md:135-148`).
  So `mild`'s `inconclusive` does not test "C1 on a non-designed host" as cleanly as the C1 note
  says.
- **My own checkpoint steer.** "Candidates should vary missing-function pathologies by stage and
  severity" (`results/2026-10-11-fleet-c1-checkpoint.md:87-89`) was written after seeing that the
  one missing-normalisation host passed. It steers toward the hosts most likely to pass.
  - **I withdraw it as a rule for choosing candidates.**
  - The counted candidates below are **drawn** from a generator whose ranges predate C1's
    analysis: S1 and S3, unchanged since `4b70653` on 2026-10-09. The draw uses a seed declared
    here.

## 3. What the evidence establishes, and what it does not

| Evidence | Establishes | Does not establish |
|---|---|---|
| Instrument: screen v1, G0 golden, bitwise pairing (`results/2026-10-08-bounded-screen-v1.md`; `results/2026-10-09-atlas-g0-golden/README.md`; `results/2026-10-11-fleet-c1s.md`) | Paired differences resolve to about ±0.018; replay is bitwise | Anything about the claims |
| A real deficit on `under_normalized` (positive control v2; Fleet C1 static +0.142) | A host with a deficit that targeted structure repairs exists | That such deficits arise without being designed in (D3). Every seed type repairs it (D6), so "which blueprint" does not matter on that host |
| Fleet C1 G1 on `under_normalized`: graft − 2× scale-up = −0.071 | **L2 at bounded scale on one designed host**, at a fixed site, with a designed seed, after epoch 1 | L1's timing: static is ahead by 0.046, and rung 4's best schedule is the most static-like. L3, L4, L5, L6 |
| Fleet C1 `mild` (inconclusive; scale-up ahead by 0.012) and the BatchNorm hosts (C1-S: no deficit; graft ≈ static ≈ uniform widening) | Designed capacity and spatial handicaps at stage 2 of 117k–161k-parameter hosts are not repairable deficits in this regime | That capacity-type deficits don't exist in general: the regime may be what binds (D4) |
| Rung 4: no detectable per-seed timing headroom on one host (`0057:50-59`) | Timing alone offers little to learn on that host | Anything about between-host headroom |
| λ = 0.0271 | The regime's price of uniform scale on these hosts | Its value on much smaller hosts or in any other regime |
| Untested | — | **L3, L4 (C2), L5 (C3), L6** |

## 4. Proposals that would only make the benchmark easier

I reject each of these, including the parts my own checkpoint leaned towards:

- **B1. More variants of the missing-normaliser host** (severity, stage) to reach two passing
  hosts. Every seed carries a normaliser (D6), so these pass almost by construction and add
  nothing on L3–L5.
- **B2. Designing new handicaps paired with the blueprint that fixes them**, or retuning a
  handicap until it separates the arms. This is the kernel spec's rule (D3) and the
  designed-winner problem.
- **B3. Loosening the screen**: below 0.05 nats, a weaker lower bound, accuracy instead of CE, or
  dropping the 10% divergence cap.
- **B4. Choosing the horizon, data size or regime per host after seeing results.**
- **B5. Swapping C1's comparator** from uniform scale-up back to static or no growth.
- **B6. Screening in rounds until two hosts pass**, or leaving failed candidates out of the
  report.
- **B7. Best-of-four seed selection on the same data that is tested.** The registered mean bar is
  a point threshold, so a maximum over seeds inflates it however the lower bound is corrected.
  This is what revision 1 did; PDR-0046 flagged the same for `under_normalized` (`0046:30-33`).
- **B8. Reusing dev or test data for selection** beyond the registered screen.
- **B9. Choosing candidates from Fleet C1 or C1-S outcomes** (§2, my withdrawn steer).
- **B10. Reading a screen pass as evidence for the loop** (§5).
- **B11. Passes carried by added parameters.** A seed that adds 1.4–2.6× the host's parameters
  (`conv_heavy`, or any seed on a very small host) can clear 0.05 by capacity alone. The fix is a
  cap on the counted seed's realised multiple (§6).
- **B12. Hand-picked points inside pre-C1 ranges.** Revision 1 took S1's extreme starvation width
  and widths below S1's range, in the direction C1 suggested. The fix is a seeded draw (§6).
- **B13. A sample size that adapts to outcomes,** including setting n after a dry run. With a mean
  bar, a smaller n raises the pass rate of hosts just below the bar. The fix is n set here.
- **B14. A new counting class invented after the data,** for example "honest-small". The fix:
  such hosts are descriptive only.
- **B15. Training family hosts before G5's generator is frozen,** which lets this screen shape G5.
  The fix: freeze the generator here, and keep every screened host out of G5's report hosts.

## 5. Diagnostic screening is not proof of the loop

The family screen measures hosts. It asks whether a family, generated before any data, contains
hosts whose deficits a small injection of library structure repairs, in this regime. At most, a
pass makes later tests possible:
- G2′: is there headroom between and within hosts?
- G3 and G4: does a learned controller beat the best fixed policy?
- G5: does it transfer?

**A screen pass is not evidence for L1–L6, C2 or C3.**

| Gate | What it tests | Original claim |
|---|---|---|
| G0 instrument and replay (`0057:143-185`) | Measurement validity | Precondition for all |
| G1, C1 against uniform scale-up (`0057:187-211`) | Targeted graft against width at matched or greater cost | **L2**, partly L1 (graft after epoch 1); on designed hosts only |
| Deficit screen (`0057:212-216`) and **this family screen** | Does a host have a deficit library structure repairs? | **Diagnostic.** A precondition for L3–L5 data. Tests no claim |
| G2 / G2′, headroom (`0057:231-243`) | Is there anything for a policy to learn? | Learnability precondition for **L3/L4** |
| G3, offline learning (`0057:245-266`) | A learned controller beats the frozen best fixed policy a\* | **L4**; L3's when and which, not where (D1) |
| G4, live single decision (`0057:268-286`) | The same, live, with the admission chain | **L4** live; L1 for one decision |
| G5, transfer (`0057:288-297`) | Held-out hosts from a frozen family; C1 on held-out hosts | **L5** within one CNN family (D10; interpolation only, `S1:544`); L2 on new hosts |
| Generated structure, Momir L1+ (`0057:299-300`) | Generated, not selected | **L6**; beyond this pathway |

## 6. The proposed family screen

**Question.** In a host family generated before any data, does at least one pathology class
other than normalisation contain a host whose deficit a small library injection repairs, by the
registered bar? "Small" means at most 1.10× the host's parameters. The regime is unchanged:
4,096 fit examples, 10 epochs, the corrected static arm born at τ.

**The generator (G-0), frozen here** ([`generator.py.txt`](generator.py.txt)). It is S1's
generator (`S1:335-341`) plus S3's depth class (`S3:331`), made concrete:
- **Classes:** capacity, spatial, depth.
  - Normalisation is not drawn: `under_normalized` already holds that class, and drawing more of
    it is B1.
- **Stage:** 1 or 2, uniform. The slot stays after stage 2.
- **Base width:** b ~ U[0.75, 1.25], widths rounded to multiples of 8.
  - Multiples of 8 are what `0057:159` and `S3:333` say, and not `atlas_hosts.WIDTH_STEP = 4`.
  - The reason: the norm seed is `GroupNorm(8, w2)` at the slot. A first draw at step 4 gave
    w2 = 60 and failed to build, so the generator was fixed before any host was used.
- **Severity:**
  - capacity: the impaired stage's middle width = round8(r × that stage's output width), with
    r ~ U[12/64, 48/64] (S1's starvation range at stage 2's 64 channels, as a ratio);
  - spatial: the impaired stage's convolutions are 1×1;
  - depth: the impaired stage has one convolution instead of two.
- **Draw:** two hosts per class, class-major, from `numpy.random.default_rng(15000)`. Every host
  draws stage, then b, then r, so the stream never depends on the class.

**The drawn hosts** ([`draw.md`](draw.md)). "Seeds ≤ 1.10×" lists the realised multiples of the
seeds eligible to count, computed with `kernel_demo.build_seed`:

| Host | Class | Stage | w1/w2/w3 | Impaired mid width | Parameters | Seeds ≤ 1.10× | Role |
|---|---|---|---|---|---|---|---|
| F1 | capacity | 1 | 24/64/80 | 16 | 159,722 | `norm` 1.001, `attn` 1.027, `conv_light` 1.056 | counted |
| F2 | capacity | 1 | 24/56/72 | 8 | 126,514 | 1.001, 1.030, 1.062 | counted |
| F3 | spatial | 1 | 24/64/80 | — | 156,498 | 1.001, 1.028, 1.057 | counted |
| F4 | spatial | 2 | 24/56/72 | — | 94,594 | 1.001, 1.040, 1.082 | counted |
| F5 | depth | 2 | 32/80/96 | — | 186,826 | 1.001, 1.029, 1.059 | counted |
| F6 | depth | 1 | 24/64/80 | — | 156,450 | 1.001, 1.028, 1.057 | counted |

`conv_heavy` is over the cap on every host (1.38–1.56×). F4 is close to C1's `no_spatial_mix`,
which failed (+0.020). It is kept because it was drawn.

**What a counted host feeds.** The screen tests none of L1–L6. A confirmed host would add:
- for G2′ and G5: one more class whose deficit library structure repairs;
- for stage-1 hosts (F1, F2, F3, F6): evidence that the fixed stage-2 site repairs an upstream
  deficit. That describes the site; it is not a test of choosing where (D1).

**Descriptive hosts, never counted** (B14). These are honest small hosts: the reference
architecture, unimpaired, at reduced width. They are the closest to the original's "start small"
host. EL `cifar_baseline` is described as "~6K parameters… Host alone: ~45-50%… With seeds:
~65-75%" (EL `tasks.py:105-120@d2c139e9`), docstring expectations that were never measured. They
were chosen after C1 and below S1's range, so they cannot count.

| Host | w1/w2/w3 | Parameters | Realised multiples | λ-predicted gain from parameters alone |
|---|---|---|---|---|
| S1, ×0.5 | 16/32/40 | 43,242 | `norm` 1.002, `attn` 1.051, `conv_light` 1.104, `conv_heavy` 1.697 | 0.000 / 0.002 / 0.004 / 0.021 |
| S2, ×0.25 | 8/16/16 | 9,186 | 1.004, 1.122, 1.253, 2.645 | 0.000 / 0.004 / 0.009 / 0.038 |

The λ-predicted gain is Fleet C1's frozen λ × log2(multiple). It is stated before the data, and
λ was fitted on hosts 4–17× larger, so it may understate. The no-growth arms of S2, S1 and the
full-width reference also give a descriptive width ladder: CE against log2 of parameters across a
16× range of honest hosts. That bears on D4 (§11).

**Controls.**

| Control | Arms | Expected | If the expectation fails |
|---|---|---|---|
| **Negative:** `reference` at full width (N0, unimpaired) | Same split-sample rule as the counted hosts, eligible seeds only | **Does not confirm.** No bottleneck means no-op should win [PAPER:474] | If it confirms, the reading is `screen_invalid`: the screen would be measuring "extra structure helps", not deficit repair. Stop; John decides |
| **Positive anchor:** `under_normalized`, fresh seeds 15001–15096 | No growth + `norm` | Passes (Fleet C1: +0.142) | `instrument_failure`. Stop |
| **Pairing:** `under_normalized` on Fleet C1's seeds 10001–10048 | No growth + `norm` static | Bitwise equal to Fleet C1's records (C1-S showed its corrected arm equals the registered arm on this host) | `instrument_failure`. Stop |
| **Instrument (CPU, no GPU):** a zero-function static seed | — | Bitwise equal to no growth | Nothing launches |

**Screen rule for a counted host.** The registered thresholds are unchanged: mean gain > 0.05
nats, 95% two-sided lower bound > 0, static divergence ≤ 10%. They are applied to **one seed
type per host, chosen on separate data:**

1. **Selection, phase 1:** seeds 15001–15048. Arms: no growth plus every eligible seed. The chosen
   seed is the eligible seed with the largest mean gain; a tie goes to library order.
2. **Confirmation, phase 2:** seeds 15049–15240, 192 seeds. Arms: no growth plus the chosen seed
   only. The host **confirms** if the registered thresholds hold on these seeds.

The choice is mechanical: the analysis module makes it, and nobody reads phase 1 before phase 2
launches.

**How strict this is, and against what:**
- **Compared with pre-naming one seed per host and testing it on 192 seeds:** the same error
  rates, because the confirming data never took part in the choice. That is revision 1's
  checkpoint pilot size, with the designed-winner choice removed.
- **Compared with Fleet C1's 768 seeds:** looser. With a point-threshold mean bar, the chance that
  a host just under the bar passes falls as n grows. A confirmation phase at 768 seeds per host
  would cost 4× more.
- **Under sd 0.11** (Fleet C1's static-gain sd was 0.081–0.124), the chance a confirmation
  passes:

  | True gain of the chosen seed | Per host | All six counted hosts at this gain |
  |---|---:|---:|
  | 0 | ≈ 0 | ≈ 0 |
  | 0.03 | 0.006 | 0.035 |
  | 0.04 | 0.10 | 0.48 |
  | 0.06 | 0.90 | — |
  | 0.08 | ≈ 1.00 | — |

  A gain of 0.04 sits close to the bar, and this rule cannot separate it from 0.05 cheaply.

**Counting.** The reading counts passing **classes**: normalisation (held by `under_normalized`),
capacity, spatial and depth.
- **`family_viable`:** at least one of capacity, spatial or depth has a confirmed host. That makes
  two classes, which meets PDR-0057's two-pass bar on classes rather than hosts.
- **Stricter than host counting.** It could only differ by admitting `under_normalized` plus
  another normalisation host, and none is drawn.

**Descriptive only, decided by nothing:**
- phase 1's gains for every eligible seed;
- realised multiples;
- the gain over completed runs only;
- the honest-small hosts and the width ladder.

**Seeds and data:**
- Seeds 15001–15240, from the reserved host-family range (`0057:340-341`), plus 10001–10048 for
  pairing only.
- The same pinned fit and dev data as Fleet C1. Outer and test data are not read.
- Every screened host, F1–F6, S1–S2 and N0, is "seen". G5's report hosts must be drawn later
  from G-0 with a different declared seed, excluding them (B15).

## 7. Compute budget

**Per-arm cost.** Two measured bases:
- Fleet C1-S: 2,496 runs in 768 × 28 s GPU-seconds, about 8.6 s per run;
- Fleet C1: about 6 s per run.

I use 9.3 s, which is conservative.

**Arm-seeds:**
- counted hosts, 6 × (48 × 4 + 192 × 2) = 3,456;
- negative control, 48 × 4 + 192 × 2 = 576;
- honest-small, 2 × 48 × 5 = 480;
- anchor, 96 × 2 = 192;
- pairing, 48 × 2 = 96;
- **total 4,800.**

**Cost:**
- 4,800 × 9.3 s = 12.4 GPU-hours, about **6.2 hours on two GPUs**;
- a dry run of 3 seeds, twice, adds 0.6 GPU-hours (40 arms per seed).

**Hard cap: 15 GPU-hours, dry runs included.**
- Units run seed-major, so a cut-off never leaves whole hosts unscreened.
- If the projection at 25% complete exceeds the cap, the run stops.
- **A run that stops at the cap has no reading.**

**Why more than the checkpoint's "about 4 hours":**
- no designed winners: up to three eligible seeds per counted host in phase 1;
- a separate 192-seed confirmation phase;
- the controls and the honest-small hosts.

Cutting the honest-small hosts saves about 1.2 GPU-hours.

## 8. Go/no-go and stopping rules

**Before any GPU time:**
- John signs this design or a revision of it, including the §9 bar movements;
- the §10 panel endorses;
- the §12 prerequisites are built and tested on CPU;
- an in-session sketch goes to John (PDR-0053);
- **John re-authorises GPU time.** It is released to Sultai now.

**Instrument:**
- the dry run, twice on GPU, gives byte-identical records;
- pairing is bitwise;
- the anchor passes, and the negative control does not confirm;
- failed units stay at or below 1%.

Any failure gives `instrument_failure` or `screen_invalid`. No reading follows, and John decides.

**Readings:**
- `family_viable`: the registered consequence is a **fresh owner decision**, not Fleet A
  automatically. Fleet A or G2′ would need its own plan, review and sketch.
- `no_family`: the registered consequence is that the pathway stops (§11), unless John decides
  otherwise.

**Single round.** No second screening round, and no new draw, without a new owner decision and
new seeds. This round's report stands in full, failures included (B6).

**Budget.** The §7 cap is absolute, and a capped run has no reading.

## 9. How this proposal moves the bar

PDR-0057 records that "the bar has only ever moved in the direction of continuing"
(`0057:67-77`). This proposal moves it again. Each move is owner-gated (`0053:42-51`), even where
it is stricter.

| Move | When | Direction | Note |
|---|---|---|---|
| Rebuilding the host set after a registered fail | After Fleet C1 | Towards continuing | A registered option (`0057:212-216`), but it is still the continuing branch |
| One seed per host chosen on separate data, instead of a designed seed | After C1 | Neither looser nor stricter than a pre-named seed at n = 192; looser than C1's n = 768 | Removes designed winners (D3) |
| Counting classes instead of hosts | After C1 | Stricter | Excludes normalisation variants (B1) |
| Eligibility cap of 1.10× | After C1 | Stricter | Excludes capacity-carried passes (B11). 1.10× is C1's smallest declared scale-up step |
| Generator G-0, the depth-per-stage definition, width step 8 | Here, before any family data | Neutral | Made before any family host trains |
| Honest-small hosts | After C1 | Descriptive only | Never counted (B14) |

## 10. Specialist correctness review panel

The panel reviews the plan, the analysis module and the dry run **before** any GPU time. Each
reviewer must endorse, or endorse with changes that are all taken. Disagreements go to John.

| Reviewer (installed agent) | Checks | Pass criterion |
|---|---|---|
| Statistics (`yzmir-counterfactual-statistics:experiment-statistics-reviewer`) | The split-sample rule; error rates against the registered rule; the n = 192 choice; control logic; the single-round rule | Every rule is shown no looser than a pre-named seed at n = 192; power is stated |
| PyTorch correctness (`yzmir-pytorch-engineering:pytorch-code-reviewer`) | Builders for G-0's classes at stage 1 and 2: shapes, BatchNorm placement, parameter counts against `draw.md`, slot alignment. `GroupNorm(8, w2)`, `attn` against narrow channels, τ birth on every host | Every host builds, trains on CPU, and is born at a realised ratio of 0.05 |
| Determinism (`axiom-determinism-and-replay:determinism-reviewer`) | The new registry keeps bitwise replay; pairing on 10001–10048; phase 2's mechanical choice is reproducible | The dry run is byte-identical twice, and pairing is bitwise |
| Training regime (`yzmir-training-optimization:training-config-reviewer`) | Whether 4,096 examples and 10 epochs bind data or epochs for these hosts (D4); whether S2 at 9k parameters trains stably at lr 0.05 | A stated, sourced view; no change to the regime without John |
| Morphogenesis (`yzmir-morphogenetic-rl:morphogenesis-reviewer`) | Whether a confirmed host means what §6 says; circularity; site against where-choice | The "What a counted host feeds" text is accepted or corrected |
| Benchmark-shopping audit (`axiom-product-management:product-decision-critic`) | §4 and §9 are complete; nothing traces to C1 outcomes; the stop option is real | Revision 2 clears revision 1's blockers |
| Plan reality (`axiom-planning:plan-review-reality`) | Paths, symbols, the cost basis, prerequisites | Every cited path and line resolves |
| Systems (`axiom-planning:plan-review-systems`) | Two-phase sequencing, the mechanical choice, cap and cut-off handling, seed-major ordering | No path where a human sees phase 1 before phase 2 is pinned |

## 11. The clean stop, and the regime question

**The clean stop** is always available, before or after the screen. It needs no GPU time and no
source change. What it leaves:
- **C1 published**, narrowed to designed pathologies. Correct the `mild` wording first (§13).
- **λ = 0.0271 frozen.**
- **A clean negative** on "several repairable deficits exist at this scale": four hosts, 768
  seeds each.
- **The comparators and λ**, available as a bar for Sultai if John wants that.
- **This document's drift analysis** (§2), which applies to any restart.
- **Recording.** A PDR records the stop and its re-entry conditions.

**The regime question, for John, outside this proposal.**
- **Why it matters.** D4 suggests capacity-type deficits may not be testable at 4,096 examples
  and 10 epochs. The original ran long on full CIFAR.
- **What it would take.** Moving towards that regime changes a rung parameter (`0053:42-51`). It
  would multiply the cost per arm by roughly the data × epoch factor: about 11× for 45k fit
  examples at 10 epochs, an estimate, not measured.
- **What the screen can contribute.** Its honest-small width ladder is a cheap descriptive look.
  It cannot settle the question. This is the main re-entry condition I would record with a stop.

## 12. Prerequisites (not to be done now; no dates)

- **Host builders and registry.** Builders for G-0's classes at stages 1 and 2 in
  `experiments/atlas_hosts.py`. `HostConfig` has no stage-1 middle width or kernel today; stage 1
  is `_make_stage(3, w1, w1, …)`. They also need an `AtlasSpec` host registry (S3 §5).
  `RunSpec.validate` rejects hosts outside `PATHOLOGIES` (`experiments/bounded_data.py:47`).
- **Width step.** Width step 8 for family hosts. Reconcile with `WIDTH_STEP = 4`
  (`atlas_hosts.py:25`), which C1's slot-less scale-up arms used.
- **Study module and plan.** A study module for the screen covering phase 1 and 2 with the
  mechanical choice, class counting, controls and pairing. A frozen plan with source pins. CPU
  tests, including the zero-function static control.
- **Out of scope:**
  - the registered arm's BatchNorm birth fix (`simic-e3803e8200`) is not needed, because the
    screen uses the corrected arm (`experiments/atlas_static.py`);
  - a second slot site (D1) is out of scope; G5 needs it.

## 13. Pending corrections to published notes (not made in this change)

- **`mild`.** Qualify "the honest, non-designed host" in `0057:199` (a PDR edit, so John's),
  `results/2026-10-11-fleet-c1.md:13,178-179` and
  `results/2026-10-11-fleet-c1-checkpoint.md:18`. `mild` was designed as the restraint host, with
  a conditional winner `conv_light`.
- **The checkpoint's steer.** Mark "candidates should vary missing-function pathologies"
  (`results/2026-10-11-fleet-c1-checkpoint.md:87-89`) as withdrawn, and link here.

## 14. Recommendation

My checkpoint note recommended rebuilding. Having recovered the original loop and had this
design reviewed adversarially, **I now recommend the clean stop (§11), with the regime question
recorded as its main re-entry condition.**

1. **No host screen tests the loop.** L3–L6 are what the original set out to prove, and §5
   shows the screen reaches none of them.
2. **The likely reading is `no_family`.** The fixes that make the screen honest (drawn hosts, no
   designed winners, the cap, class counting) remove the routes by which it could pass easily.
   That is a prior, not a result. C1-S found no repairable deficit on stage-2 capacity and
   spatial hosts even with their designed seeds.
3. **What it would add is small.** It would mostly confirm a regime limit (D4) that the
   honest-small ladder only describes.
4. **The GPU is going to Sultai.**

If John wants one more look before stopping, this revision is the version to run: about 6 hours,
capped at 15 GPU-hours, with its reading accepted either way. I would not run the 4-hour pilot
from the checkpoint. It used designed winners and could not separate a repair from added
parameters.

## 15. Sources

**Original (archives on nyx):**
- [HLD]: `/mnt/data/archive/esper.old/docs/architecture/001-high-level-design.md@8d69bec`. Lines
  20, 22, 77, 93, 113, 115, 116, 125, 129, 160-162, 215, 217, 235, 240, 330, 691, 719, 734-738,
  1548-1565, 1697-1715, 1736, 1750-1753, 1759-1771, 2225. The review re-resolved the main
  lines.
- [PAPER]: `/mnt/data/archive/esper-lite/_archive/docs/paper/draft_paper.md@0ee3a001`. Lines
  5-7, 95, 215, 424, 446, 472, 474, 509.
- **Esper-lite:**
  - `README.md:79-88@0ee3a001`;
  - `src/esper/poc.py:51-55,96-112,528,614-617,731,750@0ee3a001`;
  - `src/esper/runtime/tasks.py:105-120@d2c139e9`, `:214-218@4de8a0a2`, `:282-296@c4c70f08`;
  - `src/esper/leyline/factored_actions.py:20-34,92-115,425-434@P`;
  - `src/esper/simic/rewards/contribution.py:92-111@P`;
  - `src/esper/simic/training/vectorized_trainer.py:1140,1182,1366@P`;
  - `docs/plans/2025-11-26-multi-slot-kasmina-design.md:17-24@0ee3a001`;
  - `docs/analysis/2026-06-15-reward-efficiency-proof-packet.md:779-790@P`;
  - `DESIGN_MANIFESTO.md:74,84-102,143-169@8517cca5`.
  - Public mirror at P: <https://github.com/tachyon-beep/esper-lite/tree/0807ccfaa847303d9a65bc4c48ad199f34dd3624>.
  - The proof packet, manifesto, factored-actions and trainer citations were not re-verified by
    the review.
- **Esper (E26):** `docs/architecture/decisions/ADR-003-sealed-test-evaluation.md:19-22@bb9d963`.

**Simic:**
- `docs/product/vision.md:21-23,37-41,59-61`;
- `docs/product/decisions/0057-controller-training-pathway.md:32-43,50-77,98-107,143-300,302-314,333-389`;
- `docs/product/decisions/0046-round-two-positive-control-and-graft-plans.md:19-20,30-33,86-89`;
- `docs/product/decisions/0053-vision-update-acceptance-gates-and-ladder.md:42-51`;
- `docs/adr/0019-reopen-comparison-uniform-scaleup.md:63-65`;
- `docs/product/spikes/2026-10-09-controller-pathway/S1-learning-and-gates.md:335-341,485,542-544`;
- `docs/product/spikes/2026-10-09-controller-pathway/S3-atlas-engineering.md:321-350`;
- `git show 25be1da:docs/superpowers/specs/2026-08-09-kernel-demo-design.md` (lines 49-64), and
  `docs/superpowers/specs/2026-08-09-kernel-demo-design.md:135-148`;
- `experiments/kernel_demo.py:546-554,603,637-734`;
- `experiments/atlas_hosts.py:25,41-88`;
- `experiments/bounded_data.py:47`;
- the results: `docs/results/2026-10-08-bounded-screen-v1.md`, `2026-10-09-graft-capture-v2.md:40`,
  `2026-10-09-rung4-timing-horizon.md:18-21`, `2026-10-11-fleet-c1.md`, `2026-10-11-fleet-c1s.md`,
  `2026-10-11-fleet-c1-checkpoint.md`, and the per-arm summary
  `2026-10-11-fleet-c1/arms-summary.jsonl.gz` (the accuracy figures in §1 and D4).

**Research and review behind this note,** all read-only and all 2026-10-11:
- two subagent maps, one of the original loop and one of Simic;
- one adversarial benchmark-shopping review of revision 1.

The §10 panel should re-resolve every cited line.
