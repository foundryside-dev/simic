# PDR-0057 — The controller training pathway ("how to train your Tamiyo"): gates G0–G5

Date: 2026-10-09   Status: **proposed; the gates, comparators and stop conditions await owner signature**   Author: Claude (session 17)
Owner direction: **RECEIVED 2026-10-09**, in session: *"can you produce a
'how to train your tamiyo' plan that lets test and prove what we need to
prove. Do any relevant design spikes and then start training tamiyo to
germinate seeds. - what are the various gates. What's the transition
criteria and what is the work done at each stage."*
Related: PDR-0050 (ladder), PDR-0053 (gate split), PDR-0054/0055 (rung 4),
PDR-0056 (compute), ADR-0011 (anchor corpus), ADR-0018 (bounded
comparison), ADR-0019 (proposed: reopen the comparison); spikes in
[`spikes/2026-10-09-controller-pathway/`](../spikes/2026-10-09-controller-pathway/)
(S1 statistics, S2 HLD mapping, S3 engineering). Reviewed by a product
critic before signature; its findings are folded in.

## What this is for

John's founding principle for Esper and Simic, in session on 2026-10-09:
*"rather than training a massive model you start by training a small model
and inject extra parameters where you have issue."* He framed three claims
the same day: *"we can [take] an undercooked model from 40->60 with 1.01x
parameter increase (proven) and that we can train tamiyo to do (somewhat
proven) it in a target agnostic way (entirely unproven so far)."*

| Claim | Statement | Where it stands in Simic (2026-10-09) |
|---|---|---|
| **C1, efficiency** | A small targeted injection lifts an undercooked model, and is worth a larger uniform scale-up | **Direction only.** The `norm` graft adds 0.06% optimizer parameter-steps (rung 3) and captures 0.86 of static's gain at T0 (rung 4). Uniform scale-up has never been measured. The Esper figure ("40→60") has not been reproduced |
| **C2, learnability** | A controller using pre-decision telemetry chooses interventions better than the best fixed policy | **Untested.** One host offers no detectable per-seed headroom (below) |
| **C3, transfer** | The controller works on hosts it never trained on | **Untested.** Needs a host family |

## Two findings that shape the pathway

1. **One host offers no detectable per-seed timing headroom.** Picking each
   seed's best graft timing after the fact gains 0.026 nats over always-T0
   (rung 4, n = 767). Normal noise with the same spread would give 0.035.
   The residuals are very heavy-tailed, so that comparison is suggestive,
   not proof: single-future data cannot separate heterogeneity from noise
   ([script](../../results/2026-10-09-rung4-timing-horizon/exploratory/timing_headroom_null.py.txt)).
   - **Reconciled with rung 4.** The rung-4 result found that per-seed
     *linear* slopes vary beyond a uniform spread (variance ratio 1.69
     [1.42, 1.99]), worth about 0.002 nats to a linear oracle. PDR-0055's
     consequence said `lever_found` gives rung 5 "something to predict".
     That holds for the fixed timing lever. It does not hold per seed at a
     size a controller could use.
   - The seed-type choice on one host looks the same (spike S1).
   - So the first atlas spans **four hosts** and carries **replicate
     futures**, which measure label reliability directly.
2. **The comparator matters.** The ladder's static arm puts the same module
   at the known site from step zero. It needs the diagnosis in advance, so
   it is an oracle ceiling. The principle's alternative is a bigger model
   with no diagnosis: uniform scale-up.

## Naming

- **Whether, when and where to grow** is Aurelia's commissioning policy.
- **Which seed type** is Momir at its L0 rung: retrieval over the fixed
  library, guided by its own critic.
- **The controller is therefore two predictors** (spike S2 §S1): a
  class-blind one for Aurelia, trained only on "best action versus no-op"
  (ADR-0011, INV-09), and a per-action one for Momir's critic. Seed type
  never enters a `GrowthIntent`.
- **Isperia** judges against no-op and stays a fixed, pre-registered rule at
  every stage. A learned judge would grade itself.
- **"Tamiyo" stays a prose gloss** ("the Tamiyo-shaped controller"). It
  never names a package, contract, test or telemetry field. Tamiyo is the
  witness under Namespec 2.0, and INV-35 would be unsatisfiable if the
  controller carried the name.

## Owner decisions this PDR asks for

| # | Decision | Recommendation |
|---|---|---|
| D1 | Adopt G0–G5 as the ladder's continuation: rung 5 = G2 + G3, rung 6 = G4, rung 7 = G5. **This waives a parked condition:** current-state says learned structural timing comes "only after a round-2 graft earns its cost", and the graft has not beaten static | Adopt, with the waiver stated |
| D2 | **Reopen the comparison (ADR-0019, proposed).** ADR-0018 says to reopen the design if static wins at the declared cost; it did. C1's comparator becomes **uniform scale-up**. Targeted static stays reported as an oracle ceiling, and its recorded win stands. **This is a comparator change made after seeing data**, in the direction that tests the founding principle rather than rescuing the graft | Adopt. Claude does not edit `vision.md`; the scoped clause below is for read-back |
| D3 | The stop conditions and readings in the gate table | Adopt as written |
| D4 | G1 can fail C1 at bounded scale. If the `under_normalized` graft is shown **inferior** to 1.25× uniform scale-up, C1 is refuted here in its most favourable case | Accept that risk; it is the point of G1 |
| D5 | v1 has one decision point, after epoch 1 (d = 1). The controller sees one epoch of telemetry; every policy pays rung 4's ~0.016 nats for not grafting at T0 | Adopt. Sequential decisions only if G2 on the host family finds timing headroom |
| D6 | The naming above, including the two-predictor split | Adopt |
| D7 | **The cost charge λ** (nats per doubling of parameter-steps). Derived from uniform scale-up's slope on support seeds, or an exchange rate John states | Derived, unless John states one |
| D8 | **The C2 comparator a\* is host-blind**: one fixed action for every context. A controller that only recognises the pathology then counts as C2, reported under the weaker name "telemetry identifies the pathology" | Adopt |
| D9 | **Fleet A's rung parameters:** hosts `under_normalized`, `channel_starved`, `no_spatial_mix`, `mild` (plus `reference` and scale-up arms); seed types `norm`, `attn`, `conv_light`, `conv_heavy`; one site (stage 2); horizon 10 epochs; 4,096 fit examples | Adopt |

Claude decides, under review: per-study plans, sizing, seeds, engineering,
and always recomputing the no-op branch in Fleet A (the conservative
default).

**Proposed vision clause (D2), scoped to C1, for read-back only:** "C1's
efficiency comparator is uniform scale-up of the host. Static capacity at
the known site from step zero is reported as an oracle ceiling."

## Rules that apply to every gate

- **Fixed sequence.** C1 (G1) is its own claim family, Bonferroni over two
  hosts. C2/C3 (G2 → G3 → G4 → G5) is a fixed sequence at one-sided
  α = 0.025 per gate; a gate opens only when its predecessor passes.
- **Product dependency.** Statistically the C2 chain does not need G1. But
  if G1 refutes C1 on `under_normalized`, C2 spending pauses until John
  decides.
- **Robust companions.** Every primary must clear on the paired mean *and*
  a robust companion (the rung-4 heavy-tail lesson):
  - G1 and G5: the 10%-trimmed mean;
  - G3 and G4: a Wilcoxon signed-rank test on contexts where the controller
    and a\* disagree. Elsewhere their difference is exactly 0, so a trimmed
    mean could never pass.
- **Failures** score chance-level CE (ln 10) and are never dropped. A
  separate tail gate requires the controller's divergence rate to be
  non-inferior to a\*'s (upper 95% bound ≤ +1.0 point).
- **Unblinding order** (one analyst, so the order is the wall):
  1. Read support and screen seeds only. Fit λ, choose a\*, the model class
     and the abstention threshold. Hash-freeze all four.
  2. Only then read audit seeds and run G1, G2 and G3.
- **Seeds.** Seeds 1001–9356 are already seen: support or shakedown only.
  Fresh ranges: Fleet A 10001–10192; G4 11001–11192; host family 12001+.

## The gates

### G0 — Apparatus (no claim)

**Work, items 1–5 (need no owner decision; started):**
1. GPU profile baseline, then several processes per GPU. Gate: a unit run
   alone and alongside co-tenants gives identical records.
2. **Snapshot/fork core** (`experiments/atlas.py`), ported from the kernel
   demo's fork pattern. The frozen rung-4 runner is not modified.
3. **Rung-4 golden test:** the atlas reproduces rung 4's records bitwise
   (wall time aside) on seeds 8001–8008, all six cells.
4. **Replicate futures:** epochs from the decision point draw from
   `derive(seed, "common-future", r)`; r = 0 is today's future bitwise.
5. **Atlas record schema** with a mandatory no-op per decision point;
   failures are rows; per-branch cost recorded.

**Work, items 6–9 (wait for D2, D7–D9):**

6. Hosts: the four pathologies, an unimpaired `reference`, and
   width-scaled no-op hosts at nominal m ∈ {1.1, 1.25, 1.5, 2.0}. Widths
   move in multiples of 8, so each arm records its realised m.
7. Telemetry (Nissa): free and near-free per-stage features, plus one probe
   forward on a throwaway copy, from a pinned split outside fit and dev
   (`perm[40000:41000]`). Dev stays the 5,000 examples of rungs 1–4.
8. Experiment-grade records keeping HLD field names: `ScaffoldState`, a
   light `TelemetryEnvelope`, a light `BranchResult`, a separate blinded-id
   map.
9. **Pipeline shakedown (no claim):** run the G3 training code end to end
   on already-seen seeds, so the first real fit is not also the first run
   of the code.

**Pass:** golden reproduction; forked no-op equals the trunk bitwise;
telemetry on/off gives identical training digests; co-tenancy gives
identical records; a 3-seed real-config dry run of Fleet A completes with
analysis.
**Kill:** any replay mismatch. Fix it before science runs.
**Effort (spike S3):** items 1–5 about 4–5 days; items 6–8 about 4–7 days.

### Fleet A — the first atlas (data for G1, G2, G3)

- 192 fresh seeds, each on the four hosts. One decision after epoch 1:
  no-op plus the four seed types at the stage-2 site.
- Roles by seed hash: support 50%, screen 25%, audit 25%. Replicate futures
  1, 2 and 4 by role.
- Extra arms: static (ceiling and deficit screen) and the scale-up hosts.
- **Deficit screen (pre-registered):** a host stays in C2 analysis only if
  some static arm beats its no-op by more than 0.05 nats with the 95%
  lower bound above 0. A host whose static arm diverges above 10%
  triggers a host-instability policy before G2 is read.
- About 22 hours of fleet wall time on today's throughput, both GPUs.
- **Launch needs** D1–D5 and D7–D9 signed, a reviewed and dry-run plan,
  and the in-session sketch (PDR-0053).

### G1 — C1 efficiency (from Fleet A)

- **Contrast:** each host's pre-declared blueprint (`DESIGNED_WINNER`:
  `under_normalized`→`norm`, `mild`→`conv_light`), grafted at d = 1, minus
  uniform scale-up at m; late dev CE. Choosing the blueprint from data
  would give the graft about one SE of selection edge.
- **Test:** non-inferiority at margin 0.02, stepping down m = 1.25 → 1.5 →
  2.0. The m = 1.1 arm feeds λ and is descriptive.
- **Co-primaries** (Bonferroni, one-sided α = 0.0125 each):
  `under_normalized` (existence) and `mild` (the honest, non-designed host).
- **Readings per host:**
  - `non_inferior at m`: the upper bound of graft − scale-up is below
    +0.02. Report the largest such m;
  - `inferior`: the lower bound is above +0.02 at m = 1.25. On
    `under_normalized` this refutes C1 at bounded scale. **Back to John.**
  - `inconclusive` otherwise. With a half-width of about 0.021, a graft
    exactly equal to 1.25× scale-up lands here about half the time.
  - On `mild`, anything short of `non_inferior` narrows C1 to designed
    pathologies, the expected result.

### G2 — Headroom: is there anything to learn? (rung 5, part 1)

- **Estimator:** the per-context oracle's gain over a\*, cross-fitted over
  seeds and over replicate futures, seed-cluster bootstrap. Also reported:
  a model-based estimate, label reliability ρ across futures, and the split
  between between-host and within-host headroom.
- **Readings:**
  - `go`: lower bound ≥ 0.025 nats, enough for G4 to detect a controller
    that recovers half of it;
  - `no_headroom`: upper bounds of both estimates < 0.025;
  - `inconclusive`: **owner decision** between more audit replicates and
    the host family. No automatic re-run.
- **Stop:** `no_headroom` on the four hosts sends the pathway to the host
  family (G2′, same rule). `no_headroom` again **stops the ladder at rung
  5**: measured counterfactuals show no decision-relevant variation in this
  action space.

### G3 — Offline learnability (rung 5, part 2: the first real training)

- **Training:** on support seeds, from pre-decision telemetry, regressing
  all K cost-charged effects (never argmin labels). At most three model
  classes (ridge, small GBM, kNN), chosen on screen seeds.
- **Primary (audit seeds):** Δ = a\*'s cost-charged CE minus the
  controller's, averaged over the audit replicates. Co-conditions: beats
  no-op; tail gate.
- **Reported separately:** whether-regret (the part Aurelia may learn),
  false-intervention and miss rates, between/within split.
- **Stop:** if Δ fails with ρ ≥ 0.3, telemetry is insufficient: one revision
  cycle on support/screen data only. With ρ < 0.3 the labels are noise:
  stop.

### G4 — Closed loop (rung 6)

- **Fleet:** fresh report seeds on the four hosts; the frozen controller
  acts live at d = 1.
- **Admission chain** (spike S2 §S2): Aurelia's predictor commissions or
  waits → `GrowthIntent` (no seed type) → resolver stub → Momir-L0 proposes
  **one** candidate → Jin-Gitaxias measures it and the no-op → rule-driven
  Isperia → minimal `Warrant` → Wrenn adopts the branch. The attach path
  refuses a missing or mismatched warrant.
- **No oracle admission.** Isperia judges on a short QA window scored on
  the probe split, disjoint from the endpoint data. a\* passes through the
  same gate.
- **Pulls from the tracker:** `simic-0bf2c40dec` (Warrant and a
  RegionContract stub only) and `simic-38a07fad39` (warrant valid only at
  the evidence host state).
- **Primary:** controller − a\* on cost-charged late CE, paired by seed. The
  live branch must equal its atlas branch bitwise.
- **Readings:** `c2_supported`; `c2_not_supported` (upper bound < 0.0125);
  `inconclusive`. If 80% or more of G2's headroom was between hosts, a pass
  is published as "telemetry identifies the pathology".

### G5 — Transfer (rung 7)

- **Prerequisite:** a parametric host family (pathology class, stage,
  severity, base width), two slot sites, frozen before any family host
  trains.
- **Unit: the host.** 32 report hosts × 16 fresh seeds, disjoint from
  support, screen and audit hosts.
- **Primary:** per-host controller − a\*, tested across hosts, with one
  O'Brien–Fleming interim at 16 hosts.
- **Secondary:** C1 on held-out hosts against 1.25× scale-up.
- **Stop:** failure means C3 is not supported; C2 is published as
  within-distribution only.

Generated structure (Momir L1+, Elesh, Urabrask) is beyond G5 and out of
scope. The fixed library stays as permanent blinded controls.

## Compute (fleet wall time on today's throughput, both GPUs)

| Fleet | Hours |
|---|---:|
| G0 checks and dry runs | ~0.5 |
| Fleet A (G1, G2, G3) | ~22 |
| Fleet A, 20-epoch audit subsample (label stability across horizons) | ~2.7 |
| G4 report fleet | ~7 |
| Host family (G2′, G3, G5) | ~35 |
| **Total** | **~67** |

G0's speed work should cut these. Compute does not bind; host engineering
and review do.

## When training starts

- **G0 is under way now** (items 1–5, no claim). Item 2, the fork core, is
  built and tested. Item 3 passed on 2026-10-09: the atlas reproduces rung
  4's GPU records bitwise on seeds 8001–8008, all six cells
  ([report](../../results/2026-10-09-atlas-g0-golden/README.md)).
- **The first training, G3,** needs Fleet A's atlas. Realistically: G0
  takes about 8–12 working days, Fleet A about one day of nyx, then G3.
- **Earlier, without a claim:** the item-9 shakedown trains the G3 code on
  already-seen seeds as soon as items 2–5 and 7 exist.

## Reversal trigger

- John rejects or amends any of D1–D9.
- G0 cannot reproduce rung 4 bitwise: the pathway pauses until it can.
- Fleet A's deficit screen keeps fewer than two hosts: the host set is
  rebuilt before G2.
