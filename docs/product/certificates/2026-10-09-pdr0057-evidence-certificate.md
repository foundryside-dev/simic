# Evidence certificate — PDR-0057 (controller training pathway) and ADR-0019

Date: 2026-10-09 · Prepared by: Claude (session 17) for John's sign-off ·
Branch `controller-pathway` from main `6d38c81` · Status: **reviewed;
ready for owner decision**

This certificate lists what John is asked to decide, the evidence behind
each item, where it lives, how it was checked, and what it does not show.
Assumptions are labelled as assumptions, not evidence. Three specialist
reviews (DRL, PyTorch, systems thinking) were consulted; §7 records what
each said and what changed.

## 1. What is being decided

- **Option 0, or D1–D2, first and on their own:** stop the ladder at rung 4,
  or continue under the pathway and reopen the comparison (ADR-0019).
- **D3–D9,** only if D1–D2 are adopted: the gates' readings and stops, the
  decision point, naming, the cost charge, the comparators and the hosts.
- **Not being decided:** any result, any fleet launch, any edit to
  `vision.md`. Each fleet needs its own reviewed plan and an in-session
  sketch.
- **Work already done is not a reason to adopt.** The G0 apparatus was built
  before signature because it makes no claim; stopping costs it nothing.

## 2. Evidence register

| # | Finding | Value | Source | Checked | Does not show |
|---|---|---|---|---|---|
| E1 | The paired instrument resolves small differences | ±0.018 nats at n = 48 | `docs/results/2026-10-08-bounded-screen-v1.md`, PDR-0045 | Pre-registered, analysed once | Anything about grafts on a host with a deficit |
| E2 | `under_normalized` has a repairable deficit | static − no growth −0.144 [−0.169, −0.118], n = 95 (descriptive) | `docs/results/2026-10-09-graft-capture-v2.md` | Archived per-unit records | That it clears the old floor: rung 2 read `control_fails_below_floor`, −0.119 |
| E3 | A graft repairs part of that deficit | `norm`: graft − no growth −0.087 [−0.105, −0.069], capture 0.60 [0.51, 0.72]; `conv_heavy`: −0.045, capture 0.31 | same, PDR-0052 | Pre-registered, two plans | That it beats static: static wins by 0.057 and 0.098 |
| E4 | Grafting earlier is better | T0 − T3 −0.051 [−0.059, −0.043], margin 0.02; robust on median, trimmed mean, sign (79.5% of seeds) | `docs/results/2026-10-09-rung4-timing-horizon.md`, PDR-0055 | Pre-registered, 768 seeds, 4,608 runs, analysed once; statistics and product reviews | That late injection pays: T0 is the schedule most like static |
| E5 | A longer horizon lets the graft catch static | gap shrinks 0.101 [0.067, 0.136]; median 0.067 [0.056, 0.078]; graft ties static on the median seed at 20 epochs | same | Pre-registered contrast; robust measures exploratory | That the graft beats static on a typical seed. The mean advantage comes from static degrading late |
| E6 | The graft is cheap and captures most of static's gain | +0.06% optimizer parameter-steps (rung 3); capture 0.86 at T0 (rung 4); late dev accuracy 41.0% → 45.8% at T0, static 46.6% (exploratory) | rung-3 and rung-4 results | Records | C1 itself. Against static the graft loses; against uniform scale-up it has never been run. The Esper "40→60" figure is unreproduced |
| E7 | One host shows no detectable per-seed timing headroom | after-the-fact oracle 0.026 nats over always-T0; normal noise of the same spread gives 0.035; linear slope component ≈ 0.002 (variance ratio 1.69 [1.42, 1.99]) | `exploratory/timing_headroom_null.py.txt`, `seed_timing_interaction.py.txt` | Committed scripts, re-run | That headroom is absent: single-future data cannot separate heterogeneity from noise; residuals have excess kurtosis 26 |
| E8 | The graft lifecycle is stable; static is not, at 20 epochs | graft diverged 0/192 (rung 3), 6/4,608 (rung 4); static late rise >0.1 in 117/756 and 12/768 diverged at 20 epochs | rung-3 and rung-4 results; `simic-9c5c3a2acf` | Records | Why static degrades late (undiagnosed) |
| E9 | `mild` has no deficit to repair; it is the only measured between-host variation | static − no growth +0.009 [−0.029, +0.046]; graft − no growth +0.029 [+0.003, +0.054] (n = 24, exploratory) | `docs/results/2026-10-08-lifecycle-v2-validation.md` cell C | Records | Whether `mild` fails the pre-registered deficit screen (likely, R3) |
| E10 | The atlas fork core reproduces the instrument for `under_normalized` × `norm` | bitwise equal to rung 4's GPU records, seeds 8001–8008, all six cells, both arms, twice (before and after the code-review fixes) | `docs/results/2026-10-09-atlas-g0-golden/` | GPU on the rung-4 SKU and build; 38 CPU tests covering BN hosts and seeds, mid-lifecycle resumes, RNG isolation, replicate lineage and the runner's end-of-run checks | BN hosts, the `attn`/`conv_light`/`conv_heavy` seeds, `reference` and scaled hosts on GPU; co-tenancy; telemetry; the static arm. The GPU re-run shows the fixes did not break reproduction; the RNG and divergence paths are proven by CPU tests only |

**Not evidence (priors only):** the Esper-lite results. They used seed 42
throughout, no static control, the official test set for validation, and a
capacity-starved host unlike Simic's; the remembered attention+norm run is
unidentified (`esper-lite` @ `0807ccf`, relayed by emmy).

**One sentence the register adds up to:** the graft has beaten no growth,
but it has never beaten static on a pre-registered contrast.

## 3. Decision by decision

| D | What it asks | Evidence | Assumption it rests on | Risk if the assumption fails |
|---|---|---|---|---|
| Option 0 | Stop at rung 4; publish the clean negative | E1–E5, E8 | — | C1 against scale-up, C2 and C3 stay untested |
| D1 | Adopt G0–G5; waive the parked "learned timing only after a graft earns its cost" condition | E4 (a fixed lever: graft at T0), E7, E9 | Decision-relevant variation exists **across hosts**. Four hosts each built for one blueprint make a G2 `go` weakly informative; the real tests are G2′ and G5 | G2 reads `no_headroom`: the ladder stops at rung 5 unless John funds the host family |
| D2 | C1 comparator becomes uniform scale-up (ADR-0019) | E3/E5: static won; ADR-0018's reopen trigger fired | Uniform scale-up is the principle's alternative (owner's statement) | A post-data comparator change. Mitigation: static's wins stand, graft − static is a named co-reading in G1, and G1 can refute C1 |
| D3 | Readings and stops; every `inconclusive` comes to John with stop on the menu | spike S1 | Sizing inputs (effective hosts ≈ 2.5, disagreement rate 0.5, sd ×1.5) | Under-sizing gives `inconclusive`; re-sized from audit spread before G4 |
| D4 | G1 can refute C1 | E6 | — | A G1 pass shows targeting beats uniform width, not that growing during training beats installing at the start |
| D5 | One decision after epoch 1 | E4: ~0.016 nats per epoch of delay, paid by every policy | One epoch of telemetry carries signal. **No evidence yet** | G3 fails for a fixable reason; one revision, scored on fresh audit seeds. Sequential decisions need a new spike |
| D6 | Naming: Aurelia + Momir L0; Tamiyo as prose only | `02-constitution.md` (INV-35), ADR-0008, spike S2 | — | — |
| D7 | λ = max(0, −slope of CE on log₂ parameter-step multiple), fitted on Fleet C1 | none yet | The slope is measurable over the scale-up range | λ ≈ 0: costly seed types ranked too kindly; the uncharged ranking is reported beside it |
| D8 | Host-blind a\* and per-host a\*_h; full C2 name needs a win over a\*_h | spike S1; DRL review | — | A controller that only reads the host is reported as "telemetry identifies the host" |
| D9 | Hosts, seed types, horizon | E2, E9 | `channel_starved` and `no_spatial_mix` have deficits; never run on the bounded runner | Fewer than two hosts pass the screen: John decides before anything else is built |

## 4. Open risks

- **R0. The bar has only ever moved toward continuing.** Rung 2's floor was
  deferred, rung 3 counted a partial capture as met, rung 4's lever is the
  schedule most like static, and D1–D2 waive a condition and change a
  comparator after data. Each step was disclosed; together they are a
  pattern. Option 0 is offered for that reason, and PDR-0057 tabulates the
  history.
- **R1. The pathway may end at G2,** which is a recorded negative, not an
  apparatus failure.
- **R2. C1 may not survive G1.** Fleet C1 reads it first, on its own seeds,
  for about 10 hours, before any telemetry or atlas engineering beyond the
  hosts.
- **R3. `mild` likely drops out of C2** (E9). G1 still uses it as the
  honest, non-designed host.
- **R4. Static's late-horizon instability is undiagnosed** (E8).
- **R5. Bounded scale only:** ten epochs, 4,096 examples, one CNN family,
  one data sample, hand-authored blueprints. Passing every gate supports "a
  controller selects among reference seeds from telemetry", not generated
  structure.
- **R6. The binding constraint is John's attention.** Decisions come to him
  at four points only (this one, after Fleet C1, after G2, after G4), each
  with its cost and a stop option.

## 5. Integrity

- E1–E5 and E8 come from pre-registered plans with hash-pinned analysis
  modules, run once from immutable source snapshots. Exploratory numbers
  (E5 robust measures, E6 accuracy, E7, E9) are labelled and come from
  committed scripts.
- Rung 4 merged to main as PR #34 after statistics and product reviews.
  PDR-0057 and ADR-0019 were red-teamed twice by a product critic, then by
  the three specialists in §7.
- The atlas code was reviewed twice by PyTorch reviewers. All warnings and
  minor items are fixed and tested.

## 6. Apparatus re-check on the final code

The golden check ran three times on GPU, the last on the final code with
a self-describing report (`docs/results/2026-10-09-atlas-g0-golden/final/`):
**pass**, eight seeds, six cells, both arms, bitwise. The report records the
atlas and runner source hashes, the runtime (RTX 4060 Ti, torch
2.13.0+cu130), each reference file's hash and the records compared per
cell (10 per arm, 20 for H20). Full test suite on the final code: 493
passed.

## 7. Specialist reviews

Each specialist was told that "nothing meaningful to add" was acceptable
but that they must answer. All three answered with substance; none
declined to endorse.

| Reviewer | Verdict | Main findings | What changed |
|---|---|---|---|
| **DRL** | Endorse with changes | v1 is a full-information contextual bandit, the right first problem; exact offline evaluation; reward-hacking guards sound. (1) The cost charge as specified had the **wrong sign**: it would have credited expensive seed types, Esper's failure class. (2) "Telemetry identifies the pathology" could be earned by host lookup; hosts are readable from architecture. (3) Aurelia's "best effect" label is an argmin in disguise. (4) G3 scored a different policy from G4. (5) "Closed loop" overstated: one decision tests no compounding | λ = max(0, −slope) (D7); per-host comparator a\*_h and the weaker name "identifies the host" (D8); derangement and decodability controls ported (G0 7–9); Aurelia's label is the realised effect of a cross-fitted critic's pick; G3 applies Isperia offline; G4 renamed "live single-decision test"; D5 says v2 needs a new spike; ρ per host; Huber loss for divergence targets |
| **PyTorch** | Endorse with changes | E10 holds for the merged code: hashes match, the runner is unchanged since rung 4, the comparison is not vacuous. (1) The re-run cannot validate the RNG and divergence fixes; only CPU tests do, and the report lacked provenance. (2) A telemetry probe on a deep copy would write into the live host through the kernel's hooks. (3) M2 only partly ported. (4) The golden skips the static arm. (5) GPU pass criteria too narrow for Fleet A. (6) Co-tenancy: check at target load, log memory | E10 wording; golden report now records source hashes (atlas included), runtime, reference hashes and record counts, and was re-run (§6); telemetry hook gate in G0; remaining end-of-run checks ported and tested; static arm in the atlas with its own golden (item 6); every fleet cell runs twice on GPU with equal records before launch; co-tenancy at target load with peak memory |
| **Systems thinking** | Endorse with changes | (1) Eroding goals: the bar has only moved toward continuing, and the signer was never offered a stop. (2) Shifting the burden: G1's graft also has the diagnosis, so a pass shows targeting, not growth. (3) Stops could be routed around (G2′, revision cycle, unhandled `inconclusive`). (4) Apparatus built before C1 is read. (5) Decision rate outruns the owner's attention | Option 0 and the bar-history table (PDR-0057); D1–D2 signed separately; signer's note; D4 states what a G1 pass does not show; graft − static a named G1 co-reading; every reading has a consequence, every `inconclusive` offers stop, G2′ needs a fresh decision, G3's revision is scored once on fresh seeds; **Fleet C1 reads C1 first** on its own seeds before items 7–9; four decision points only |

**One reviewer proposal not taken as written:** the systems review
suggested the sentence "the graft has not beaten any control in any rung".
It beat no growth in rung 3, so §2 says instead that it has never beaten
static on a pre-registered contrast.
