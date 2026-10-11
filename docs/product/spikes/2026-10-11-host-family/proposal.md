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

Contents:
1. The original loop, from primary sources
2. Where the current pathway has drifted
3. What the evidence establishes, and what it does not
4. Proposals that would only make the benchmark easier
5. Diagnostic screening is not proof of the loop
6. The proposed family screen
7. Compute budget
8. Go/no-go and stopping rules
9. Specialist correctness review panel
10. The clean stop
11. Prerequisites (not to be done now)
12. Pending corrections to published notes
13. Recommendation
14. Sources

**Source keys** (full list in §14):
- **[HLD]** `/mnt/data/archive/esper.old`, `docs/architecture/001-high-level-design.md` at
  `8d69bec` (committed 2025-08-03; header "Version 1.4, 01 July 2025"). It is the earliest design
  document in any archive, reachable with `git log --all`.
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
  model struggles most" [HLD:129]. The HLD's own comparator is fine-tuning or retraining
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
| D2 | Tamiyo chooses **when**, during initial training [HLD:734] | One decision after epoch 1 (D5, `0057:103`) | Easier, and the evidence runs against L1's timing | Rung 4: T0 best, "the best schedule is the one most like static" (`results/2026-10-09-rung4-timing-horizon.md:18-21`). Static is ahead of the graft by +0.046 on `under_normalized` (`results/2026-10-11-fleet-c1.md`) |
| D3 | Bottlenecks that arise in a host's training [HLD:77]. The first Esper-lite host was unimpaired (EL `poc.py:96-112@0ee3a001`) | Four hosts **designed per blueprint**. "Each episode samples one canned handicap… Fan winner (by design)… a pathology that never separates the arms is retuned" (`git show 25be1da:docs/superpowers/specs/2026-08-09-kernel-demo-design.md`, lines 49-64). "Esper-style crippled hosts, each paired with a designed repair seed" (`0046:19-20`). Esper-lite had the same habit later (`cifar10_blind`, EL `src/esper/runtime/tasks.py:214-218@4de8a0a2`) | **Easier**: designed-winner circularity, named at `0057:242-243` | — |
| D4 | Long training on full CIFAR (Esper-lite; per-host exposure depends on loader mode) | 4,096 fit examples, 10 epochs (D9, `0057:107`) | Harder for capacity claims, possibly to the point of being untestable | Exploratory, mine: in Fleet C1 the three BatchNorm hosts' mean dev accuracy is 55.6–56.3% for no growth; 2× uniform widening adds 1.0–1.1 points; λ = 0.027 nats per doubling. Whether data or epochs bind cannot be separated from C1 |
| D5 | Comparator: fine-tuning or retraining, and random or heuristic selection [HLD:162,215,2225] | Uniform scale-up, with static as an oracle ceiling (`vision.md:59-61`). An owner decision recorded as "made after seeing data" (`adr/0019:63-65`) | **Harder** than the original, but chosen after the data | — |
| D6 | Karn generates blueprints [HLD:116]; Simic's vision: "generated from the live state" (`vision.md:21-23`) | Four human-authored seeds through G5; generation is "beyond G5" (`0057:299-300`) | Easier: L6 untested | All four seeds contain a normaliser (`kernel_demo.py:637-734`): `norm` GroupNorm, `attn` LayerNorm, `conv_light` and `conv_heavy` BatchNorm. Rung 3: static `conv_heavy` repaired `under_normalized` about as well as `norm` (−0.143 vs −0.144, `results/2026-10-09-graft-capture-v2.md:40`) |
| D7 | The test split was used for validation and reward (§1) | Dev only; outer and test data owner-gated | **Stricter** | — |
| D8 | Single seed 42 | 768 seeds per host, paired | **Stricter** | — |
| D9 | Shaped reward [HLD:1759-1771]; P `contribution.py:92-111` | Counterfactual branches against a measured no-op | Stricter attribution | — |

**Two Simic-internal drifts that need correcting** (§12):
- **The `mild` label.** PDR-0057 calls `mild` "the honest, non-designed host" (`0057:199`). The
  kernel spec built it as the restraint host, with a designed conditional winner `conv_light` and
  "no-op often wins" (`25be1da` spec lines 54-59; `docs/superpowers/specs/2026-08-09-kernel-demo-design.md:135-148`).
  So `mild`'s `inconclusive` does not test "C1 on a non-designed host" as cleanly as the C1 note
  says.
- **My own checkpoint steer.** "Candidates should vary missing-function pathologies by stage and
  severity" (`results/2026-10-11-fleet-c1-checkpoint.md:87-89`) was written after seeing that the
  one missing-normalisation host passed. That steers toward the hosts most likely to pass. **I
  withdraw it as a rule for choosing candidates.** The candidates below come from the pre-C1
  generator (S1 and S3 at `4b70653`, 2026-10-09, two days before C1's analysis) or from the
  original sources.

## 3. What the evidence establishes, and what it does not

| Evidence | Establishes | Does not establish |
|---|---|---|
| Instrument: screen v1, G0 golden, bitwise pairing (`results/2026-10-08-bounded-screen-v1.md`; `results/2026-10-09-atlas-g0-golden/README.md`; `results/2026-10-11-fleet-c1s.md`) | Paired differences resolve to about ±0.018; replay is bitwise | Anything about the claims |
| A real deficit on `under_normalized` (positive control v2; Fleet C1 static +0.142) | A host with a deficit that targeted structure repairs exists | That such deficits arise naturally (D3). Every seed type repairs it (D6), so "which blueprint" does not matter on that host |
| Fleet C1 G1 on `under_normalized`: graft − 2× scale-up = −0.071 | **L2 at bounded scale on one designed host**, at a fixed site, with a designed seed, after epoch 1 | L1's timing: static is ahead by 0.046 and rung 4's best schedule is the most static-like. L3, L4, L5, L6 |
| Fleet C1 `mild` (inconclusive; scale-up ahead by 0.012) and the BatchNorm hosts (C1-S: no deficit; graft ≈ static ≈ uniform widening) | Designed capacity and spatial handicaps on 117k–161k-parameter hosts are not repairable deficits in this regime | That capacity-type deficits don't exist in general: the regime may be what binds (D4) |
| Rung 4: no detectable per-seed timing headroom on one host (`0057:50-59`) | Timing alone offers little to learn on that host | Anything about between-host headroom |
| λ = 0.0271 | The regime's price of uniform scale | Its value in any other regime |
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
- **B7. Best-of-four seed selection without a multiplicity correction.** PDR-0046 already flagged
  an uncorrected best-of-4 (`0046:30-33`).
- **B8. Reusing dev or test data for selection** beyond the registered screen.
- **B9. Choosing candidates from Fleet C1 or C1-S outcomes** (§2, my withdrawn steer).
- **B10. Reading a screen pass as evidence for the loop** (§5).

## 5. Diagnostic screening is not proof of the loop

The family screen measures hosts. It asks whether a declared, pre-generated family contains hosts
whose deficits fixed library structure repairs, in this regime. At most, a pass makes the later
tests possible:
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
| G5, transfer (`0057:288-297`) | Held-out hosts from a frozen family; C1 on held-out hosts | **L5** (interpolation only, `S1:544`); L2 on new hosts |
| Generated structure, Momir L1+ (`0057:299-300`) | Generated, not selected | **L6**; beyond this pathway |

## 6. The proposed family screen

**Question.** In a host family declared before any data, do at least two pathology classes
contain a host whose deficit fixed library structure repairs by more than the registered bar? The
regime is the current one: 4,096 fit examples, 10 epochs, the corrected static arm born at τ.

**Candidates.** All eight are fixed now, before any data. Each traces to a source dated before
C1's analysis, or to the original documents.

| # | Host | Class | Source of the variant | Original claim | A pass would mean | A pass would not mean |
|---|---|---|---|---|---|---|
| H1 | `reference` at base width ×0.75 | Honest small: no impairment, smaller | S1 width range [0.75, 1.25] (`S1:335-341`) | **L1/L2**, the owner's "start small… inject where you have issue" (`0057:32-34`); [HLD:129] | A modestly smaller healthy host has a deficit library structure repairs | That growth beats width (needs G1-style scale-up), or anything about a controller |
| H2 | `reference` at ×0.5 | Honest small | **Beyond S1's range.** Original rationale: EL `cifar_baseline`, "Can seeds AUGMENT…? ~6K parameters… Host alone: ~45-50%… With seeds: ~65-75%" (EL `tasks.py:105-120@d2c139e9`; docstring expectations, never measured) | **L1/L2** | As H1, for a small host | As H1 |
| H3 | `reference` at ×0.25 | Honest small | Beyond S1. Closest to the original's host scale (about 10k parameters nominal; exact counts come from the builder) | **L1/L2** | As H1, near the original host scale | As H1 |
| H4 | `shallow` (one conv + BN per stage) | Depth | S3 variant table (`S3-atlas-engineering.md:331`) | **L1**: a structural bottleneck not designed for one seed | A depth deficit the library repairs | That a controller can tell depth from other deficits (G5) |
| H5 | No normalisation at **stage 1** only, init gain 2.0; slot stays after stage 2 | Normalisation, upstream | S1 stage ∈ {1, 2} (`S1:335-341`) | **L3, where**: does a downstream insertion repair an upstream deficit? | Downstream repair works for this class | A second class (it shares one with `under_normalized`; see the counting rule) |
| H6 | Channel starvation at **stage 1** (width 24) | Capacity, upstream | S1 stage and starvation range | **L3** where; **L1** | As H5, for capacity | As H5 |
| H7 | 1×1 kernels at **stage 1** | Spatial, upstream | S1 kernel ∈ {1, 3}, stage ∈ {1, 2} | **L3** where; **L1** | As H5, for spatial mixing | As H5 |
| H8 | Channel starvation at stage 2, width **12** | Capacity, severe | S1 starvation range [12, 48] | **L1/L2**; graded severity for G2′/G5 | A severe capacity deficit is repairable here | That milder ones are (C1-S: width 24 is not) |

**Controls.**

| Control | Arms | Expected | If it fails |
|---|---|---|---|
| **Negative:** `reference` at full width (unimpaired) | No growth + all four seeds | **Fails** the screen with every seed. No bottleneck means no-op should win [PAPER:474] | Reading `screen_invalid`: the screen would be measuring "extra structure helps", not deficit repair. Stop; John decides |
| **Positive anchor:** `under_normalized`, fresh seeds | No growth + `norm` | Passes (Fleet C1: +0.142) | Reading `instrument_failure`. Stop |
| **Instrument (CPU, no GPU):** a zero-function static seed | — | Bitwise equal to no growth | Nothing launches |

**Arms per candidate.** No growth, plus the corrected static arm (born at τ) with each of the
four library seeds. No candidate has a designed winner, which matches the original loop: the
controller picks the blueprint. Static is used because the screen asks whether a repairable
deficit exists. It is not C1's comparison.

**Screen rule.** The registered thresholds are unchanged: mean gain > 0.05 nats, 95% lower bound
> 0, static divergence ≤ 10%. Two changes of *form* are proposed. Each is strictly stricter than
the registered rule, and each is John's call:

1. **Best of four, corrected.** A host passes if any seed type meets the thresholds with its lower
   bound at the Bonferroni level 1 − 0.05/4, two-sided (B7). If John declines, the fallback is the
   registered single-seed rule. Each host's seed is then named in the plan before data, with the
   circularity disclosed for every named seed.
2. **Count passing classes, not hosts.** The classes are normalisation, honest-small, depth,
   capacity and spatial. `under_normalized` already holds the normalisation class, so the
   two-pass bar needs **at least one passing class other than normalisation**. If John declines,
   the registered per-host count applies. In that case H5 could clear the bar beside
   `under_normalized` on one class (B1).

**Descriptive only, decided by nothing:**
- the gain with each of the four seeds;
- realised parameter multiples;
- the gain over completed runs only;
- each passing host's position relative to C1's λ (whether a size-matched widening would close the
  gap needs a G1-style fleet; it is not in this screen).

**Seeds and data.**
- Seeds 15001–15096 (the reserved host-family range, `0057:340-341`), on every host.
- The same pinned fit and dev data as Fleet C1. Outer and test data are not read.

## 7. Compute budget

**Per-arm cost.** Two measured bases:
- Fleet C1-S: 28 s per seed per GPU for three static arms, about 9.3 s per arm;
- Fleet C1: 168 s per seed for 28 arms, about 6 s per arm.

I use the conservative 9.3 s.

**Arms:**
- 8 candidates × 96 seeds × 5 arms = 3,840;
- negative control: 96 × 5 = 480;
- positive anchor: 96 × 2 = 192;
- total: 4,512 arm-seeds.

**Cost:**
- 4,512 × 9.3 s ≈ 11.7 GPU-hours, about **5.9 hours on two GPUs**;
- a twice-run dry run on 3 seeds adds about 0.7 GPU-hours.

**Hard cap:** 14 GPU-hours, about 7 hours on two GPUs, dry runs included.
- **Projection stop:** if the projection at 25% complete exceeds the cap, stop and report.
- **Absolute stop:** nothing runs past the cap.

**Why more than the checkpoint's "about 4 hours".** That estimate assumed one designed seed and
two arms per host. Dropping designed winners (B2) means four seeds per candidate, and the controls
add about 15%.

**Smaller variant:** 64 seeds per host, about 3.9 hours, at some cost in power.

**Power,** assuming a paired sd of 0.11 (Fleet C1's static-gain sd was 0.081–0.124). The 0.05
mean bar binds before the corrected lower bound. The probability a host clears 0.05:

| True gain | 96 seeds | 64 seeds |
|---|---:|---:|
| 0.06 | ≈ 0.81 | ≈ 0.77 |
| 0.08 | ≈ 0.996 | ≈ 0.985 |
| 0 | negligible | negligible |

The small hosts' spread is unknown. The statistics reviewer checks it from the dry run, and the
seed count is fixed before launch.

## 8. Go/no-go and stopping rules

**Before any GPU time:**
- the §9 panel endorses;
- John signs this design or a revision of it, choosing the rule forms in §6;
- the §11 prerequisites are built and tested;
- an in-session sketch goes to John (PDR-0053);
- **John re-authorises GPU time.** It is released to Sultai now.

**Instrument:**
- the dry run, twice on GPU, gives byte-identical records;
- the positive anchor passes and the negative control fails;
- failed units stay at or below 1%.

Any failure gives `instrument_failure` or `screen_invalid`. No reading follows, and John decides.

**Readings:**
- `family_viable`: at least two classes pass, counting `under_normalized`'s. The registered
  consequence is a **fresh owner decision**, not Fleet A automatically. Fleet A or G2′ would need
  its own plan, review and sketch.
- `no_family`: fewer than two classes pass. The registered consequence is that the pathway stops
  (§10), unless John decides otherwise.

**Single round.** No second screening round with new candidates without a new owner decision and
new seeds. This round's report stands in full, failures included (B6).

**Budget.** The §7 cap is absolute.

## 9. Specialist correctness review panel

The panel reviews the plan, the analysis module and the dry run **before** any GPU time. Each
reviewer must endorse, or endorse with changes that are all taken. Disagreements go to John.

| Reviewer (installed agent) | Checks | Pass criterion |
|---|---|---|
| Statistics (`yzmir-counterfactual-statistics:experiment-statistics-reviewer`) | Multiplicity across seeds and hosts; power from the dry run's spread; that each form change is stricter than the registered rule; control logic; the single-round rule | Every rule is no looser than registered; power is stated for the chosen seed count |
| PyTorch correctness (`yzmir-pytorch-engineering:pytorch-code-reviewer`) | New host builders: shapes, BatchNorm placement, init gain, parameter counts, slot alignment. Small widths: `GroupNorm(8, C)` divisibility at the slot, `attn` d=16 against narrow channels, `conv_heavy`'s bottleneck at narrow C, τ birth at every width | Every candidate builds, trains on CPU, and is born at a realised ratio of 0.05 |
| Determinism (`axiom-determinism-and-replay:determinism-reviewer`) | The new host registry and seeds keep bitwise replay; the anchor equals Fleet C1's `under_normalized` records where the seeds overlap in design | The dry run is byte-identical twice |
| Training regime (`yzmir-training-optimization:training-config-reviewer`) | Whether 4,096 examples and 10 epochs are data-bound or epoch-bound for each candidate (D4); whether small hosts train stably at lr 0.05 | A stated, sourced view; no change to the regime without John |
| Morphogenesis (`yzmir-morphogenetic-rl:morphogenesis-reviewer`) | Whether each candidate tests what §6 claims; designed-winner circularity; pathology against host recognition | The table's "does not mean" column is accepted or corrected |
| Benchmark-shopping audit (`axiom-product-management:product-decision-critic`) | §4 is complete; no candidate was chosen on outcomes; the stop option is real | No candidate or rule traces to C1 or C1-S outcomes |
| Plan reality (`axiom-planning:plan-review-reality`) | Paths, symbols, the cost basis and the prerequisites against the source | Every cited path and line resolves |

## 10. The clean stop

This option is always available, before or after the screen. It needs no GPU time and no source
change. What it leaves:
- **C1 published**, narrowed to designed pathologies. Correct the `mild` wording first (§12).
- **λ = 0.0271 frozen.**
- **A clean negative** on "several repairable deficits exist at this scale": four hosts, 768
  seeds each.
- **The scale-up comparators and λ**, available as a bar for Sultai if John wants that.
- **Recording.** A PDR records the stop and its re-entry conditions: a regime decision (below) or
  new evidence from Sultai.

**A regime option, for John, outside this proposal.** D4 suggests capacity-type deficits may not
be testable at 4,096 examples and 10 epochs. Moving towards Esper-lite's regime (more fit data or
a longer horizon) changes a rung parameter (`0053:42-51`). It would multiply the cost per arm by
roughly the data × epoch factor. For example, about 11× for 45k fit examples at 10 epochs; that is
an estimate, not measured. I don't propose it now. It belongs with a stop or rebuild decision,
because it is the main thing the family screen cannot settle.

## 11. Prerequisites (not to be done now; no dates)

- **Host builders and registry.** Builders for H1–H8 in `experiments/atlas_hosts.py`, with an
  `AtlasSpec` host registry (S3 §5). `RunSpec.validate` rejects hosts outside `PATHOLOGIES`
  (`experiments/bounded_data.py:44`).
- **Width step.** Reconcile `WIDTH_STEP = 4` (`atlas_hosts.py:25`) with the "multiples of 8"
  text in `0057:159` and `S3:333`.
- **Study module and plan.** A study module for the screen: best-of-four with a Bonferroni lower
  bound, class counting, controls, and a frozen plan with source pins. CPU tests.
- **The zero-function static control test.**
- **The registered arm's BatchNorm birth fix** (`simic-e3803e8200`) is not needed. The screen
  uses the corrected arm (`experiments/atlas_static.py`).
- **A second slot site** (for a true "where" test, D1) is out of scope here. G5 needs it.

## 12. Pending corrections to published notes (not made in this change)

- **`mild`.** Qualify "the honest, non-designed host" in `0057:199` (a PDR edit, so John's),
  `results/2026-10-11-fleet-c1.md:13,178-179` and
  `results/2026-10-11-fleet-c1-checkpoint.md:18`. `mild` was designed as the restraint host, with
  a conditional winner `conv_light`.
- **The checkpoint's steer.** Mark "candidates should vary missing-function pathologies"
  (`results/2026-10-11-fleet-c1-checkpoint.md:87-89`) as withdrawn, and link here.

## 13. Recommendation

There are three honest courses: the family screen (§6–§9), the clean stop (§10), or the regime
decision (§10). Mine:

**Run the family screen only with both stricter forms in §6, then accept its reading.** If it
reads `no_family`, take the clean stop. H1–H3 are the most faithful to the original claim: honest
hosts, smaller, with no designed winner. If they show no deficit, that is informative about D4 as
well.

If John would rather spend the GPU on Sultai, the clean stop now loses little. The screen tests
preconditions, not the loop, and §3 is already a coherent negative at this scale.

## 14. Sources

**Original (archives on nyx):**
- [HLD]: `/mnt/data/archive/esper.old/docs/architecture/001-high-level-design.md@8d69bec`. Lines
  20, 22, 77, 93, 113, 115, 116, 125, 129, 160-162, 215, 217, 235, 240, 330, 691, 719, 734-738,
  1548-1565, 1697-1715, 1736, 1750-1753, 1759-1771, 2225.
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
- **Esper (E26):** `docs/architecture/decisions/ADR-003-sealed-test-evaluation.md:19-22@bb9d963`.

**Simic:**
- `docs/product/vision.md:21-23,37-41,59-61`;
- `docs/product/decisions/0057-controller-training-pathway.md:32-43,50-65,98-107,143-300,302-314,333-389`;
- `docs/product/decisions/0046-round-two-positive-control-and-graft-plans.md:19-20,30-33,86-89`;
- `docs/product/decisions/0053-vision-update-acceptance-gates-and-ladder.md:42-51`;
- `docs/adr/0019-reopen-comparison-uniform-scaleup.md:63-65`;
- `docs/product/spikes/2026-10-09-controller-pathway/S1-learning-and-gates.md:335-341,485,542-544`;
- `docs/product/spikes/2026-10-09-controller-pathway/S3-atlas-engineering.md:321-350`;
- `git show 25be1da:docs/superpowers/specs/2026-08-09-kernel-demo-design.md` (lines 49-64), and
  `docs/superpowers/specs/2026-08-09-kernel-demo-design.md:135-148`;
- `experiments/kernel_demo.py:546-554,603,637-734`;
- `experiments/atlas_hosts.py:25,41-55`;
- `experiments/bounded_data.py:44`;
- the results: `docs/results/2026-10-08-bounded-screen-v1.md`, `2026-10-09-graft-capture-v2.md:40`,
  `2026-10-09-rung4-timing-horizon.md:18-21`, `2026-10-11-fleet-c1.md`, `2026-10-11-fleet-c1s.md`,
  `2026-10-11-fleet-c1-checkpoint.md`, and the per-arm summary
  `2026-10-11-fleet-c1/arms-summary.jsonl.gz` (the accuracy figures in §1 and D4).

**Research maps behind this note:** two read-only subagent reports from 2026-10-11, one for the
original loop and one for Simic. Their citations were spot-checked, not all re-verified. The
reviewers in §9 should re-resolve every cited line.
