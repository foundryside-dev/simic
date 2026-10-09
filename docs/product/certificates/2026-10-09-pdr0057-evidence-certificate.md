# Evidence certificate — PDR-0057 (controller training pathway) and ADR-0019

Date: 2026-10-09 · Prepared by: Claude (session 17) for John's sign-off ·
Branch `controller-pathway` from main `6d38c81` · Status: **for review**

This certificate lists what John is asked to sign, the evidence behind each
item, where that evidence lives, how it was checked, and what it does not
show. Assumptions are labelled as assumptions, not evidence. Three specialist
reviews follow at the end.

## 1. What is being signed

- **PDR-0057** (proposed): gates G0–G5 for training the growth controller
  ("Tamiyo-shaped": Aurelia's commissioning policy plus a Momir L0 critic),
  and owner decisions D1–D9.
- **ADR-0019** (proposed): reopen the bounded comparison as ADR-0018
  directs. C1 is tested against uniform scale-up; targeted static becomes an
  oracle ceiling.
- **Not being signed:** any result, any fleet launch, any edit to
  `vision.md`. Fleet A needs its own reviewed plan and an in-session sketch.

## 2. Evidence register

Each row is a finding the pathway relies on. "Checked" says how the number
was verified.

| # | Finding | Value | Source | Checked | Does not show |
|---|---|---|---|---|---|
| E1 | The paired instrument resolves small differences | ±0.018 nats at n = 48 | `docs/results/2026-10-08-bounded-screen-v1.md`, PDR-0045 | Pre-registered, analysed once | Anything about grafts on a host with a deficit |
| E2 | `under_normalized` has a repairable deficit | static − no growth −0.144 [−0.169, −0.118], n = 95 (descriptive) | `docs/results/2026-10-09-graft-capture-v2.md` | Archived per-unit records | That it clears the old pre-registered floor: rung 2 read `control_fails_below_floor`, −0.119 |
| E3 | A graft repairs part of that deficit | `norm`: graft − no growth −0.087 [−0.105, −0.069]; capture 0.60 [0.51, 0.72]. `conv_heavy`: −0.045, capture 0.31 | same, PDR-0052 | Pre-registered, two plans | That it beats static: static wins by 0.057 and 0.098 |
| E4 | Grafting earlier is better | T0 − T3 −0.051 [−0.059, −0.043], margin 0.02; robust on median, trimmed mean, sign (79.5% of seeds) | `docs/results/2026-10-09-rung4-timing-horizon.md`, PDR-0055 | Pre-registered, 768 seeds, 4,608 runs, analysed once; statistics and product reviews | That late injection pays: T0 is the schedule most like static |
| E5 | A longer horizon lets the graft catch static | gap shrinks 0.101 [0.067, 0.136]; median 0.067 [0.056, 0.078]; graft ties static on the median seed at 20 epochs | same | Pre-registered contrast; robust measures exploratory | That the graft beats static on a typical seed. The mean advantage comes from static degrading late |
| E6 | C1 holds in direction | `norm` adds 0.06% optimizer parameter-steps (rung 3); late dev accuracy 41.0% → 45.8% at T0, static 46.6% (exploratory) | rung-3 and rung-4 results | Records | Anything against uniform scale-up, which has never been run. The Esper "40→60" figure is unreproduced |
| E7 | One host shows no detectable per-seed timing headroom | after-the-fact oracle 0.026 nats over always-T0; normal noise of the same spread gives 0.035; linear slope component ≈ 0.002 (variance ratio 1.69 [1.42, 1.99]) | `exploratory/timing_headroom_null.py.txt`, `seed_timing_interaction.py.txt` | Committed scripts, re-run | That headroom is absent: single-future data cannot separate heterogeneity from noise; residuals have excess kurtosis 26 |
| E8 | The graft lifecycle is stable; static is not, at 20 epochs | graft diverged 0/192 (rung 3), 6/4,608 (rung 4); static late rise >0.1 in 117/756 and 12/768 diverged at 20 epochs | rung-3 and rung-4 results; `simic-9c5c3a2acf` | Records | The cause of static's late instability (undiagnosed) |
| E9 | `mild` has no deficit to repair | static − no growth +0.009 [−0.029, +0.046]; graft − no growth +0.029 [+0.003, +0.054] (n = 24, exploratory) | `docs/results/2026-10-08-lifecycle-v2-validation.md` cell C | Records | Whether it fails Fleet A's pre-registered deficit screen (likely, see R3) |
| E10 | The atlas fork core reproduces the instrument | bitwise equal to rung 4's GPU records, seeds 8001–8008, all six cells | `docs/results/2026-10-09-atlas-g0-golden/` | GPU run on the rung-4 SKU and build; 35 CPU tests including BN hosts and seeds, mid-lifecycle resumes and RNG isolation; a PyTorch code review's warnings fixed | Multi-slot, new hosts, telemetry: not built yet |

**Not admissible as evidence (priors only):** the Esper-lite results. They
used seed 42 throughout, no static control, the official test set for
validation, and a capacity-starved host unlike Simic's; the remembered
attention+norm run is unidentified (`esper-lite` @ `0807ccf`, relayed by
emmy). They motivate the pathway; they do not support any gate.

## 3. Decision by decision

| D | What it asks | Evidence | Assumption it rests on | Risk if the assumption fails |
|---|---|---|---|---|
| D1 | Adopt G0–G5 as rungs 5–7; waive the parked "learned timing only after a graft earns its cost" condition | E4 (a fixed lever exists), E7 (no per-seed timing headroom on one host) | Decision-relevant variation exists **across hosts** (spike S1's designed-winner hypothesis) | G2 reads `no_headroom` on four hosts, then on the family: the ladder stops at rung 5. Cost: Fleet A (~22 h) plus host engineering |
| D2 | C1 comparator becomes uniform scale-up (ADR-0019) | E3/E5: static won; ADR-0018's own reopen trigger fired | That uniform scale-up is the alternative the principle argues against (owner's statement, 2026-10-09) | A post-data comparator change. Mitigation: static's wins stand, it stays reported as a ceiling, and G1 can refute C1 |
| D3 | The stop conditions | Spike S1 design | Sizing inputs: effective hosts ≈ 2.5, disagreement rate 0.5, sd inflated ×1.5 | Under-sizing: G4 `inconclusive`. Re-sized from Fleet A audit spread before G4 |
| D4 | Accept that G1 can refute C1 | E6 | — | None beyond the result itself |
| D5 | One decision point after epoch 1 | E4: each epoch of delay costs ~0.016 nats, paid by every policy | One epoch of telemetry carries signal | G3 fails for a fixable reason; one revision cycle allowed |
| D6 | Naming: Aurelia + Momir L0, Tamiyo as prose only | `02-constitution.md` (INV-35), ADR-0008, spike S2 | — | — |
| D7 | Cost charge λ from uniform scale-up's slope | none yet | The slope is measurable at small width multiples | λ ≈ 0: expensive seed types ranked too kindly. The uncharged ranking is reported beside it |
| D8 | Host-blind fixed-policy comparator | spike S1 | — | A pass may mean "telemetry identifies the pathology", reported under that weaker name |
| D9 | Fleet A hosts, seed types, horizon | E2, E9 | `channel_starved` and `no_spatial_mix` have deficits; they have never run on the bounded runner | Fewer than two hosts pass the deficit screen: the host set is rebuilt before G2 |

## 4. Open risks the signer should know

- **R1. The pathway may end at G2.** No evidence yet shows that the best
  action varies by context. That is exactly what G2 measures; a stop there
  is a recorded negative, not a failure of the apparatus.
- **R2. C1 may not survive G1.** On `under_normalized` the graft trails
  static at 10 epochs; whether it beats 1.25× uniform scale-up is unknown.
- **R3. `mild` likely drops out of C2.** E9 shows no repairable deficit, so
  the deficit screen will probably remove it. G1 still uses `mild` as its
  honest, non-designed host.
- **R4. Static's late-horizon instability is undiagnosed** (E8). It sets a
  ceiling at 10 epochs only, and it inflated rung 4's horizon spread 1.7×
  over its sizing limit.
- **R5. Bounded scale only.** Ten epochs, 4,096 examples, one CNN family,
  one data sample, hand-authored blueprints. Passing every gate supports
  "a controller selects among reference seeds from telemetry", not
  generated structure.

## 5. Integrity

- Results E1–E5 and E8 come from pre-registered plans with hash-pinned
  analysis modules, run once from immutable source snapshots. Exploratory
  numbers (E5 robust measures, E6 accuracy, E7, E9) are labelled and come
  from committed scripts.
- Rung 4 was merged to main as PR #34 after statistics and product
  reviews. PDR-0057 and ADR-0019 were red-teamed twice by a product critic.
- Full test suite after the review fixes: 490 passed. The atlas code was
  reviewed by a PyTorch reviewer; its warnings W1–W3 and items M1–M3 are
  fixed and tested.

## 6. Apparatus re-check on the fixed code

The GPU golden check was repeated on the fixed source: **pass**, all eight
seeds and six cells bitwise, with the source hashes recorded in
`docs/results/2026-10-09-atlas-g0-golden/README.md`. E10 therefore holds
for the code being merged, not only for the first draft.

## 7. Specialist reviews

*Filled in after review. Each reviewer was asked to challenge the evidence
and the decisions; "nothing meaningful to add" is a valid outcome, but each
must be consulted.*
