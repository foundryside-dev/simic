# PDR-0057 — The controller training pathway ("how to train your Tamiyo"): gates G0–G5

Date: 2026-10-09   Status: **accepted (owner-signed 2026-10-10)**   Author: Claude (session 17)
Owner sign-off: **RECEIVED 2026-10-10**, in session, choosing from Claude's
options after reading the evidence certificate:
- "D1–D2: adopt pathway" (Option 0 not taken);
- D3–D6 and D9: "Adopt as written";
- D7: "Derived from scale-up";
- D8: "Both a\* and a\*_h";
- the D2 vision clause: "Apply verbatim" (applied to `vision.md`).
Owner direction: **RECEIVED 2026-10-09**, in session: *"can you produce a
'how to train your tamiyo' plan that lets test and prove what we need to
prove. Do any relevant design spikes and then start training tamiyo to
germinate seeds. - what are the various gates. What's the transition
criteria and what is the work done at each stage."*
Related: PDR-0050 (ladder), PDR-0053 (gate split), PDR-0054/0055 (rung 4),
PDR-0056 (compute), ADR-0011 (anchor corpus), ADR-0018 (bounded
comparison), ADR-0019 (proposed: reopen the comparison); spikes in
[`spikes/2026-10-09-controller-pathway/`](../spikes/2026-10-09-controller-pathway/)
(S1 statistics, S2 HLD mapping, S3 engineering); evidence certificate
[`certificates/2026-10-09-pdr0057-evidence-certificate.md`](../certificates/2026-10-09-pdr0057-evidence-certificate.md).
Reviewed before signature by a product critic (twice) and by DRL, PyTorch
and systems-thinking specialists; their findings are folded in.

**Signer's note.** G0 apparatus work was built before signature because
it makes no claim and needs no decision. That work is not a reason to
adopt anything here. Stopping (Option 0) costs it nothing: the atlas stays
useful to any later question.

## What this is for

John's founding principle for Esper and Simic, in session on 2026-10-09:
*"rather than training a massive model you start by training a small model
and inject extra parameters where you have issue."* He framed three claims
the same day: *"we can [take] an undercooked model from 40->60 with 1.01x
parameter increase (proven) and that we can train tamiyo to do (somewhat
proven) it in a target agnostic way (entirely unproven so far)."*

| Claim | Statement | Where it stands in Simic (2026-10-09) |
|---|---|---|
| **C1, efficiency** | A small targeted injection lifts an undercooked model, and is worth a larger uniform scale-up | **Partly.** The `norm` graft is cheap (+0.06% optimizer parameter-steps, rung 3) and captures 0.86 of static's gain at T0 (rung 4). Against static it loses; against uniform scale-up it has never been run. The Esper figure ("40→60") is unreproduced |
| **C2, learnability** | A controller using pre-decision telemetry chooses interventions better than the best fixed policy | **Untested.** One host offers no detectable per-seed headroom (below) |
| **C3, transfer** | The controller works on hosts it never trained on | **Untested.** Needs a host family |

## Findings that shape the pathway

1. **The graft has never beaten static on a pre-registered contrast.** It
   beat no growth (rung 3: −0.087 with `norm`); static beat it in rungs 3
   and 4. At 20 epochs it ties static on the median seed.
2. **One host offers no detectable per-seed timing headroom.** Picking each
   seed's best graft timing after the fact gains 0.026 nats over always-T0
   (rung 4, n = 767). Normal noise with the same spread would give 0.035.
   The residuals are very heavy-tailed, so this is suggestive, not proof:
   single-future data cannot separate heterogeneity from noise
   ([script](../../results/2026-10-09-rung4-timing-horizon/exploratory/timing_headroom_null.py.txt)).
   Per-seed *linear* slopes do vary beyond a uniform spread (variance ratio
   1.69 [1.42, 1.99]), worth about 0.002 nats. PDR-0055 said `lever_found`
   gives rung 5 "something to predict": that holds for the fixed lever
   ("graft at T0"), not per seed.
3. **The only measured between-host variation is `mild`,** where static is
   no better than no growth (+0.009 [−0.029, +0.046]) and the graft hurts
   (+0.029 [+0.003, +0.054]), n = 24, exploratory.
4. **The comparator matters.** Targeted static needs the diagnosis in
   advance: an oracle ceiling. The principle's alternative is a bigger
   model with no diagnosis: uniform scale-up.

## How the bar has moved so far

Each step below was disclosed at the time. Read together, the bar has only
ever moved in the direction of continuing (systems review).

| Rung | Original bar | Reading | What happened |
|---|---|---|---|
| 2 | static − no growth beyond −0.10 (PDR-0046/0048) | `control_fails_below_floor` (−0.119, lower bound −0.088) | Continued: PDR-0049 deferred the floor to the graft redesign (post-data, owner-ratified) |
| 3 | graft captures static's gain | `partial_capture` | Recorded as met under PDR-0052's composition table, declared before data |
| 4 | sketch: margin 0.05; flat → stop | `lever_found` (margin set to 0.02 and flatness tightened before launch) | Met. The lever is T0, the schedule most like static |
| Now | learned timing "only after a graft earns its cost" (parked) | not met | D1 would waive it; D2 would change C1's comparator (post-data) |

## Naming

- **Whether, when and where to grow** is Aurelia's commissioning policy.
- **Which seed type** is Momir at its L0 rung: retrieval over the fixed
  library, guided by its own critic.
- **The controller is two predictors** (spike S2): a class-blind one for
  Aurelia, and a per-action one for Momir's critic. Seed type never enters
  a `GrowthIntent` (ADR-0011, INV-09).
- **Isperia** judges against no-op and stays a fixed, pre-registered rule.
- **"Tamiyo" stays a prose gloss** ("the Tamiyo-shaped controller"), never
  a package, contract, test or telemetry name (INV-35).

## Owner decisions

Sign **Option 0 or D1–D2 first, on their own.** D3–D9 only matter if D1–D2
are adopted.

| # | Decision | Recommendation |
|---|---|---|
| **Option 0** | **Stop the ladder at rung 4** and publish the clean negative: a hand-built graft repairs most of a designed deficit cheaply, but never beats the same capacity installed from the start. Cost: none; G0 work stays. What is lost: C1 against scale-up and C2/C3 stay untested | A real option. Claude recommends D1–D2 only because Fleet C1 (below) is a cheap, decisive next read |
| D1 | Adopt G0–G5 as the ladder's continuation: rung 5 = G2 + G3, rung 6 = G4, rung 7 = G5. **Waives** the parked "learned timing only after a graft earns its cost" condition | Adopt, with the waiver stated |
| D2 | **Reopen the comparison (ADR-0019).** ADR-0018's own trigger fired: static won. C1's comparator becomes **uniform scale-up**; targeted static stays reported as a ceiling and its wins stand. **A comparator change made after seeing data** | Adopt. Claude does not edit `vision.md`; the scoped clause below is for read-back |
| D3 | The readings and stop conditions in the gates below, including that **every `inconclusive` comes to John with "stop" on the menu** | Adopt as written |
| D4 | G1 can refute C1 at bounded scale. A G1 pass shows that a targeted graft beats uniform width; it does **not** show that growing during training beats installing at the start (static already shows targeting) | Accept |
| D5 | v1 has one decision point, after epoch 1. Every policy pays ~0.016 nats for not grafting at T0. **No evidence yet** that one epoch of telemetry carries signal. Sequential decisions (v2) need a new spike: states after a graft are off-atlas | Adopt |
| D6 | The naming above | Adopt |
| D7 | **Cost charge** λ = max(0, −slope of no-op CE on log₂ parameter-step multiple), fitted on Fleet C1 over the full scale-up range; or an exchange rate John states | Derived, unless John states one |
| D8 | **Two fixed-policy comparators** for C2: a host-blind a\* and a per-host lookup a\*_h, both frozen before audit data. The full C2 name needs a win over a\*_h; beating only a\* is reported as "telemetry identifies the host" | Adopt |
| D9 | Hosts `under_normalized`, `channel_starved`, `no_spatial_mix`, `mild`, plus `reference` and scale-up arms; seed types `norm`, `attn`, `conv_light`, `conv_heavy`; one site (stage 2); 10 epochs; 4,096 fit examples | Adopt |

Claude decides, under review: per-study plans, sizing, seeds, engineering,
and always recomputing the no-op branch.

**Proposed vision clause (D2), scoped to C1, for read-back only:** "C1's
efficiency comparator is uniform scale-up of the host. Static capacity at
the known site from step zero is reported as an oracle ceiling."

**The binding constraint is John's attention,** not compute. Decisions
come to him at four points only: this PDR, after Fleet C1, after G2, and
after G4. Each comes with its cost and a stop option.

## Rules for every gate

- **Fixed sequence.** C1 (G1) is its own claim family, Bonferroni over two
  hosts. C2/C3 (G2 → G3 → G4 → G5) is a fixed sequence at one-sided
  α = 0.025 per gate.
- **Every reading has a consequence.** No reading leads to an automatic
  re-run. Each `inconclusive` goes to John with stop as an option.
- **Robust companions.** Each primary must clear on the paired mean and a
  companion: the 10%-trimmed mean for G1 and G5; for G3 and G4, a Wilcoxon
  signed-rank test on contexts where the controller and the comparator
  disagree.
- **Failures** score chance CE (ln 10) in evaluation and are never dropped.
  Training targets use a Huber loss or a separate divergence head, so the
  penalty does not dominate the fit. A tail gate requires the controller's
  divergence rate to be non-inferior to a\*'s (+1.0 point).
- **Unblinding order** for Fleet A: read support and screen seeds; fit and
  hash-freeze a\*, a\*_h, the model class, the abstention threshold, and
  Isperia's θ and QA window. Only then read audit seeds.
- **Seeds.** 1001–9356 are seen: shakedown only. Fleet C1 10001–10192;
  Fleet A 10201–10392; G4 11001–11192; host family 12001+.

## The gates

### G0 — Apparatus (no claim)

**Items 1–5 (no decision needed; in progress):**
1. GPU profile and co-tenancy. Done: four processes sharing one GPU
   reproduce rung 4 bitwise, but gain only about 1.04× throughput, because
   a training step launches about 249 kernels and 64 host–device syncs.
   Fleets stay at one process per GPU; speed comes from S3's exact-records
   tier ([report](../../results/2026-10-09-atlas-g0-cotenancy/README.md)).
2. **Fork core** (`experiments/atlas.py`). Done.
3. **Rung-4 golden test.** Passed, and passed again after the code review's
   fixes ([report](../../results/2026-10-09-atlas-g0-golden/README.md)).
4. **Replicate futures.** Done.
5. **Unit records** with a mandatory no-op, failures as rows. Done.

**Item 6 (after D2, D7, D9): what Fleet C1 needs.** The four pathologies,
`reference`, and width-scaled no-op hosts at nominal m ∈ {1.1, 1.25, 1.5,
2.0}, each recording its realised m (widths move in multiples of 8). A
**static arm in the atlas**, with its own golden check against rung 4's
static records.

**Items 7–9 (only after John reads Fleet C1):** telemetry from a pinned
probe split outside fit and dev; experiment-grade records with HLD field
names; a no-claim pipeline shakedown on seen seeds; the pathology
decodability probe and `class_derangement` falsifier ported from the kernel
demo. **Telemetry hazard:** the kernel host's saturation hooks close over
`self`, so a probe on a deep copy writes into the live host's statistics.
Probes clear the copy's hooks or use hooks that read the module argument,
and a gate checks that a probe leaves the trunk's telemetry unchanged.

**Pass:**
- golden reproduction (done for `under_normalized` × `norm`);
- forked no-op equals the trunk;
- **every (host, seed type) cell of a fleet runs twice on GPU with equal
  records**, including one BN seed and one resume mid-BLENDING, before that
  fleet launches. The golden covers one host and one seed type only;
- telemetry on/off leaves training digests and the trunk's telemetry
  unchanged;
- co-tenancy leaves records identical **at the target processes per GPU,
  with snapshots resident and peak memory logged** (a cuDNN workspace
  shortfall silently changes algorithm);
- a real-config dry run of each fleet completes with analysis.

**Kill:** any replay mismatch.

### Fleet C1 → G1 (C1 efficiency) and the deficit screen — the first read

Runs before any telemetry or atlas engineering beyond item 6, on its own
seeds, so reading it cannot leak into Fleet A.

- **Arms per host and seed:** no-op; the host's pre-declared blueprint
  (`DESIGNED_WINNER`) grafted after epoch 1; targeted static; uniform
  scale-up at the four multiples. All four hosts, 192 seeds. About 10 hours
  of fleet wall time.
- **G1 contrast:** designed graft − uniform scale-up at m, late dev CE.
  Non-inferiority at margin 0.02, stepping down m = 1.25 → 1.5 → 2.0.
  Co-primaries (Bonferroni, one-sided 0.0125): `under_normalized`
  (existence) and `mild` (the honest, non-designed host).
- **Named co-reading:** graft − static on every host, so the ceiling
  stays in view.
- **Readings per host:** `non_inferior at m` (report the largest m);
  `inferior` (lower bound above +0.02 at m = 1.25); `inconclusive`.
- **Consequences:**
  - `inferior` on `under_normalized`: C1 refuted at bounded scale. C2
    spending stops; John decides.
  - `inconclusive` on `under_normalized` (about half the time if the graft
    exactly equals 1.25× scale-up): John decides between more seeds, stop,
    or proceeding.
  - Anything short of `non_inferior` on `mild` narrows C1 to designed
    pathologies, the expected result.
- **Deficit screen:** a host enters Fleet A only if static beats its no-op
  by more than 0.05 nats with the 95% lower bound above 0. Static
  divergence above 10% triggers a host-instability policy. `mild` will
  probably fail; fewer than two passing hosts means the host set is rebuilt
  or the pathway stops (John).
- **λ** is fitted here (D7) and frozen for every later gate.
- **Checkpoint:** G1, the screen and λ go to John before items 7–9 are
  built.

### Fleet A → G2 (headroom) and G3 (offline learning)

- Seeds 10201–10392 on the hosts that passed the screen. One decision after
  epoch 1: no-op plus the four seed types. Roles by seed hash: support 50%,
  screen 25%, audit 25%; replicate futures 1, 2 and 4 by role. Each branch
  records probe-split CE over a short window after the decision. About 22
  hours.
- **Launch needs** D1–D9 signed, the Fleet C1 checkpoint passed, a reviewed
  and dry-run plan, and the in-session sketch (PDR-0053).

**G2 — is there anything to learn? (rung 5, part 1)**
- Estimator: the per-context oracle's gain over a\*, cross-fitted over seeds
  and replicate futures; also a model-based estimate, label reliability ρ
  **per host**, and the split between between-host and within-host
  headroom.
- `go`: lower bound ≥ 0.025 nats. `no_headroom`: both upper bounds below
  0.025. Otherwise `inconclusive`.
- **Consequences:** `go` → G3. `no_headroom` → **the ladder stops at rung 5**
  as a clean negative, unless John signs a fresh decision to build the host
  family and re-test (G2′, about 35 hours plus the family engineering).
  `inconclusive` → John: more audit replicates, the host family, or stop.
- Four hosts each built for one blueprint make a `go` weakly informative on
  its own (designed-winner circularity). The real tests are G2′ and G5.

**G3 — offline learning (rung 5, part 2: the first real training)**
- Training on support seeds, by regression, never on argmin labels:
  - **Momir's critic:** each seed type's cost-charged effect;
  - **Aurelia's predictor:** the realised effect of the action a
    cross-fitted critic would pick, never the minimum of K noisy effects.
    Where a seed has two futures, select on one and score on the other. It
    sees no seed type.
- At most three model classes (ridge, small GBM, kNN), chosen on screen
  seeds.
- **The policy under test** is the composition, passed offline through the
  frozen Isperia rule using the recorded probe-window CE, so G3 scores the
  same policy G4 runs. Isperia's veto rate on known-good grafts is reported
  before θ is frozen.
- **Primary (audit seeds):** a\*'s cost-charged CE minus the controller's.
  Co-conditions: beats no-op; tail gate. **Also reported:** the margin over
  a\*_h, whether-regret (Aurelia's part), false-intervention and miss rates.
- **Consequences:**
  - pass → G4.
  - fail with ρ ≥ 0.3 on the passing hosts: telemetry is insufficient. One
    revision on support and screen data only, then **one** evaluation on 48
    fresh audit seeds (10401–10448). A second failure stops.
  - fail with ρ < 0.3: the labels are noise. Stop.

### G4 — Live single-decision test (rung 6)

- Fresh report seeds; the frozen controller acts live after epoch 1.
- **Admission chain** (spike S2): Aurelia's predictor commissions or waits
  → `GrowthIntent` (no seed type) → resolver stub → Momir-L0 proposes one
  candidate → Jin-Gitaxias measures it and the no-op on the probe-split QA
  window → rule-driven Isperia → minimal `Warrant` → Wrenn adopts the
  branch. a\* passes through the same gate.
- **What it tests:** the live telemetry pipeline, admission, and fresh
  seeds. **What it does not test:** compounding over sequential decisions.
  With one decision, the live branch equals its atlas branch bitwise.
- **Primary:** controller − a\*, paired by seed, plus the margin over a\*_h.
  Co-conditions as in G3.
- **Consequences:** `c2_supported` (and, only if it beats a\*_h, the full
  name) → G5. `c2_not_supported` (upper bound < 0.0125) → C2 is not
  supported; stop. `inconclusive` → John: more seeds or stop.
- Pulls from the tracker: `simic-0bf2c40dec` (Warrant and a RegionContract
  stub only) and `simic-38a07fad39` (valid only at the evidence host
  state).

### G5 — Transfer (rung 7)

- A parametric host family (pathology class, stage, severity, base width;
  two slot sites), frozen before any family host trains. This is also the
  first real test of pathology recognition rather than host recognition.
- 32 report hosts × 16 fresh seeds, disjoint from support, screen and audit
  hosts. Primary: per-host controller − a\*, tested across hosts, one
  O'Brien–Fleming interim at 16 hosts. Secondary: C1 on held-out hosts.
- **Consequences:** pass → C3 supported at bounded scale. Fail → C3 not
  supported; C2 published as within-distribution only.

Generated structure (Momir L1+, Elesh, Urabrask) is beyond G5. The fixed
library stays as permanent blinded controls.

## Compute (fleet wall time on today's throughput, both GPUs)

| Fleet | Hours |
|---|---:|
| G0 checks and dry runs | ~0.5 |
| Fleet C1 (G1, deficit screen, λ) | ~10 |
| Fleet A (G2, G3) | ~22 |
| Fleet A, 20-epoch audit subsample | ~2.7 |
| G3 revision audit, if needed | ~1 |
| G4 report fleet | ~7 |
| Host family (G2′, G3, G5), only by a fresh decision | ~35 |

G0's speed work should cut these.

## When training starts

- G0 items 1–5 are done or nearly done (no claim).
- Fleet C1 needs D1–D2, D7 and D9, plus item 6: about 2–4 working days,
  then about 10 hours of nyx.
- The first real training (G3) follows John's Fleet C1 checkpoint, items
  7–9, and Fleet A: realistically two to three weeks of spare-time work.

## Reversal trigger

- John chooses Option 0, or rejects or amends any of D1–D9.
- G0 cannot reproduce rung 4 bitwise: the pathway pauses.
- Fleet C1 refutes C1, or fewer than two hosts pass the deficit screen:
  John decides before anything else is built.

## Amendments

**2026-10-10, Fleet C1 sizing and seed ranges (Claude, under "Claude decides: sizing, seeds";
owner informed by the delta note before launch).**
- Fleet C1 runs **768 seeds (10001–10768)**, not 192. The 24-seed pilot showed 192 seeds gives
  power 0.26–0.41 to show non-inferiority when the graft only equals the scale-up; 768 gives
  0.88–0.95 at the pilot sd's 80% upper limit
  ([sizing script](../../prereg/fleet-c1-sizing.py.txt),
  [pilot](../../results/2026-10-10-fleet-c1-pilot.md)). About 31 hours on two GPUs.
- Seed ranges re-declared: Fleet A 13001–13192; G3 revision audit 13401–13448; G4 14001–14192;
  host family 15001+. Seeds up to 9424 are seen.
- Divergence caps are 2.5% for the graft and for each stepped comparator, below the 10% trim
  (statistics review of the C1 module).
- John chose to hold the launch until nyx is free ("Hold for the full box").

**2026-10-10, telemetry built before the Fleet C1 read (owner direction).** John, in session:
*"You've time for additional hardening, telemetry and building out"* while the launch waits
for the box. This moves G0 item 7 (telemetry) ahead of his Fleet C1 checkpoint. The systems
review's caution stands: work already built is not a reason to adopt anything at that
checkpoint, and items 8–9 still wait for it.

**2026-10-10, Fleet C1-S: the deficit screen with static born at τ (owner decision).** Found
after Fleet C1 launched. Fleet C1's static arm reads τ's host features in eval mode
(`simic-e3803e8200`). On a BatchNorm host at step zero those features come from untrained
running statistics, so the static seed is born far below τ.
- The Fleet C1 pilot's birth witnesses give realised ratios of 0.0013–0.0018 against 0.05 on
  `mild`, `channel_starved` and `no_spatial_mix`, and 0.0500 on `under_normalized`, which has no
  BatchNorm. The graft, born after an epoch, is at 0.052.
- **Unaffected:** G1 and λ, which do not use static.
- **Affected:** the deficit screen and the graft − static co-reading on the three BatchNorm
  hosts. The certificate's E9 rests on the same defect (erratum in the certificate).
- **Process miss:** the issue said "fix before any BN-host study", and the C1 pre-flight did not
  check it.

John chose, in session, from three options (supplement after the fleet; stop and re-seal now;
read as registered): **keep Fleet C1 running untouched, then run Fleet C1-S**
([plan](../../prereg/fleet-c1s.json), `experiments/c1s_study.py`).
- Fleet C1-S trains the corrected arm (`static_calibrated`, τ read in train mode;
  `experiments/atlas_static.py`) on Fleet C1's own 768 seeds for the three BatchNorm hosts. It
  reads it against Fleet C1's sealed no-growth and graft arms.
- On seeds 10001–10048 it re-trains no-growth on those hosts, and the corrected arm on
  `under_normalized`, where the two static arms are the same function. Both must equal Fleet
  C1's records bit for bit, or there is no reading.
- The screen's criteria are unchanged (gain > 0.05 nats, 95% lower bound > 0, static divergence
  ≤ 10%).
- At the checkpoint, the Fleet A host list takes the BatchNorm hosts from Fleet C1-S and
  `under_normalized` from Fleet C1. Fleet C1's registered BatchNorm-host screen is reported
  beside it, as registered.
- About 3 hours on two GPUs. It launches when Fleet C1 finishes, **before** Fleet C1's own
  analysis, and a fresh launch is refused once that analysis has published. Every module the arm
  and the reading run through is pinned by hash in the plan. Nothing in Fleet C1-S can therefore
  be chosen after Fleet C1's results are known (statistics review). Its analysis waits for Fleet
  C1's.
- Pre-registered fallback: if Fleet C1-S makes no reading (Fleet C1's instrument failed, a
  pairing or identity mismatch, or too many failed units), the BatchNorm hosts are unscreened.
  Fleet C1's registered screen on them never enters Fleet A, and John decides.
- The PyTorch and statistics reviews endorsed it with changes, all taken: every seed is tied to
  Fleet C1's starting state, every corrected arm must be born at τ, and the completed-runs-only
  gain is reported beside the divergence rate.
