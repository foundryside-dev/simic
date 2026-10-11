# Training-regime design review: reconciled recommendation — 2026-10-11

**Design review only (John, relayed by his assistant).** The controller pathway is on a
**reversible DEFER** ([`defer-record.md`](defer-record.md)).
- **Nothing here launches.** No experiment below is authorised, and none follows automatically.
- **Out of scope:** implementation, tests, training, GPU use, spending, access grants, merges and
  deployment.
- **Sultai keeps GPU priority.**
- **Thresholds.** Every existing threshold stays frozen. Any new threshold is marked **NEW**, is
  declared here before any data, and takes effect only if John signs it.

**Panel.** Four independent specialists reviewed the [brief](brief.md) and the frozen materials at
`9733431`:
- training dynamics (`training-diagnostician`);
- statistics (`counterfactual-statistician`);
- intervention and the closed loop (`morphogenesis-reviewer`);
- systems and compute (`plan-review-systems`).

A fifth, independent adversarial reviewer reviewed this reconciliation; see the end of this
document. Their working notes are summarised here, and the statistics reanalysis is reproducible
from [`evidence/stats-reanalysis/`](evidence/stats-reanalysis/).

**Method and status of the evidence.** Nothing was trained. Reviewers read published summaries
and finished, already-analysed records on CPU. Every seed involved is already seen, so everything
below is **exploratory** and changes no registered reading.

## 1. Observed evidence

Numbers come from records; the interpretations are in §2.

| # | Observation | Source |
|---|---|---|
| O1 | **No host had converged at 10 epochs.** No-growth dev CE is still falling 0.028–0.040 nats per epoch over epochs 7–9 on all four C1 hosts (CIs exclude 0) | stats O10; [`evidence/convergence.md`](evidence/convergence.md) |
| O2 | **BatchNorm hosts:** at epoch 9, train CE 1.05–1.09, dev CE 1.23–1.29, train–dev gap +0.16 to +0.22 (about +0.10 at epoch 3). 2× uniform lowers train and dev CE alike, and the gap does not change. Train CE is measured on augmented batches in train mode, so the true gap is larger | `convergence.md`; dynamics O1, O5 |
| O3 | **`under_normalized`:** gap about 0 at epoch 9. The gap widens by +0.036 [0.028, 0.043] from epoch 3 to 9, and by +0.066 [0.059, 0.074] from epoch 9 to 19. At epochs 17–19, dev CE is still falling 0.011 nats per epoch | stats O9; dynamics O2 |
| O4 | **On the BatchNorm hosts, per-seed spread is mostly epoch-to-epoch noise.** Cross-epoch correlation of no-growth CE and of the 2× contrast is −0.08 to +0.09, so about 0–2% of the spread persists per seed. `under_normalized`: 0.33–0.52 | stats O11 |
| O5 | **λ** = 0.0271 [0.0240, 0.0304] (seed bootstrap). It is not constant inside the regime: 0.019 at epoch 5 against 0.029 at epoch 9 (+0.010 [0.003, 0.017]) | stats O1–O2 |
| O6 | **The measured 1.1× uniform arm** gains 0.003–0.011 nats; every 95% upper bound is ≤ 0.018. At the uniform price, 0.05 nats ≈ 3.6× [3.1, 4.3] the parameters, extrapolated past the measured 2× | stats O3–O4 |
| O7 | **Targeted function repair is far cheaper than width.** The `norm` graft at 1.0008× gains 0.096 [0.091, 0.101] on `under_normalized`, about 3,000× the uniform price per doubling. Static `norm` gains about 0.14. On the other hosts, no designed seed at ≤ 1.10× has gained > 0.05; `attn` on `no_spatial_mix` gained +0.020 | stats O5; C1 |
| O8 | **Rung 4, 20 epochs, `under_normalized`:** the static gain's median holds (0.146 at epoch 6, 0.107 at epoch 19). The mean falls through a lower tail (p10 −0.163 at epoch 19). The scheduled graft's median grows to 0.112 | dynamics O3 |
| O9 | **Hypothetical sensitivity check:** the registered screen rule applied to rung 4's 20-epoch cell would not pass static on the one passing host. Mean 0.030 [0.001, 0.058] with failures scored at ln 10, 0.045 completed only. The paired sd triples (0.133 → 0.400), and the lower-bound clause then binds. Nothing registered runs at 20 epochs, so this is sensitivity, not a reading | stats O6–O7 |
| O10 | **Time beats width on `under_normalized`** at matched 2× parameter-steps: no growth for 20 epochs, late CE 1.3665 (rung 4), against `scale_x2` for 10 epochs, 1.5847 (C1). A 0.218-nat difference, unpaired across studies | systems F4 |
| O11 | **A one-decision keep-or-cull rule with rollback never beat the best fixed policy** on C1's hosts (d = 2–6). It was worse on `under_normalized` (+0.010 to +0.023) and `no_spatial_mix` (+0.005), null elsewhere. The rule was fixed after seeing the published aggregates, both decision and score use dev, and the comparator was chosen afterwards | stats O12 |
| O12 | **Trigger incidence (descriptive).** Esper-lite's germination trigger, replayed on published records, **fired in 5/768 `under_normalized` no-growth runs by epoch 10, and 74/768 by epoch 20** (median epoch 16). On C1's BatchNorm hosts, 36–52/768 per host met the latch condition by epoch 9 (132 on `under_normalized`). Caveats: <br>• the rule's units were set for Esper-lite's regime (150 epochs, lr 0.01); <br>• epoch indexing may be off by one; <br>• C1 publishes no per-epoch accuracy, so its hosts got the latch check only; <br>• the replay was done by one reviewer with `jq` | intervention finding 1 (EL `tamiyo/tracker.py:108-160`, `heuristic.py:179-212`, `leyline/__init__.py:592-610@0807ccf`) |
| O13 | **Implementation finding: current Simic has no cull path.** `Stage` has no CULLED state (`kernel_demo.py:772-778`), `epoch_tick` fossilises after fixed counts (`:858-873`), and nothing in `experiments/` culls | intervention finding 2 |
| O14 | **The original closed loop has one recorded run**, against a shorter baseline: Tamiyo heuristic 82.16% against a 10-epoch baseline at 69.31%. Single seed, up to 40 against 10 epochs, test-loader selection (EL `README.md:79-88@0ee3a001`) | intervention finding 3 |
| O15 | **"Where" was designed, never demonstrated.** `HeuristicTamiyo`'s only slot logic is `available_slots <= 0` (EL `heuristic.py:193@0807ccf`). HLD:367 lists "Models exhibit identifiable bottlenecks through telemetry analysis" as a research **assumption** | intervention finding 5 |
| O16 | **Cost.** Optimizer steps drive cost; width barely matters (the GPU is busy 24% of an epoch). Readouts at 10, 20 and 40 epochs nest in one constant-lr run. Cosine-schedule runs do not nest | systems F2, cost table |

**On O12, separating three things that must not be merged:**
- **Low trigger incidence, observed in these runs.** In these runs and regimes, the transcribed
  original trigger rarely fired. That is a statement about incidence under one rule, not a claim
  that the original loop cannot run here. A loop could be run with a different detector or
  horizon, each of which would be a new design decision.
- **An untested claim.** Whether unimpaired hosts develop a *useful* emergent bottleneck is
  untested (HLD:367 is an assumption). A trigger replay establishes neither its presence nor its
  absence. A plateau signature is not a bottleneck that an intervention can usefully relieve. Only
  an intervention test (R3 below) can show that.
- **An implementation gap.** Simic has no cull path (O13). That is missing code, not evidence
  about the loop.

## 2. Hypotheses

These are interpretations, each with what would falsify it.

| # | Hypothesis | Falsified by |
|---|---|---|
| H1 | The BatchNorm hosts are moving into a data/generalisation limit at 4,096 examples (O2) | At equal steps, 16,384 examples giving the same dev CE and gap |
| H2 | They are also step-limited (O1) | Dev CE flattening by about 20 epochs at the current lr |
| H3 | `under_normalized`'s deficit is an optimisation-rate deficit that function repair (normalisation) removes as a lasting offset (O7, O8) | The median static gain ≤ 0.02 by 40 epochs, or no growth under a tuned schedule matching static |
| H4 | Constant lr 0.05 is too high late in training. The late dev-CE rise, static's divergence tail and the sd increase fit that (O8, O9) | A decayed schedule with the same late-failure rate and sd |
| H5 | Capacity returns (λ) grow with horizon or data (O5's within-regime trend) | λ in a longer or annealed regime, within its CI of 0.0271 |
| H6 | On the BatchNorm hosts in this regime, per-seed headroom is noise that no per-seed decision can use (O4, O11) | A regime in which the per-seed contrast persists across epochs |
| H7 | **The tension.** Unimpaired hosts already have the functions the library restores, so the one demonstrated repair route (O7) may never meet an emergent bottleneck | A natural host on which an intervention test (R3) shows a ≤ 1.10× injection beating never-graft and uniform width |
| H8 | Static's lead over the graft (+0.046; rung 4's best schedule at T0) partly reflects handicaps built in from step 0, not the loop (the host-family proposal's D2 hypothesis) | The install-at-start arm against the loop on a natural host (R3's S_k arm) |

## 3. The five review topics

1. **Convergence and duration.** The 10-epoch endpoint is before convergence on every host (O1).
   The two host families are limited differently: the BatchNorm hosts' gap is widening (H1/H2
   undetermined); `under_normalized` has a near-zero gap at epoch 9 (O2, O3).
   - **Neither "capacity effects are small" nor "a 0.05 repair is impossible" follows from current
     evidence.**
   - **A longer constant-lr horizon cuts both ways.** It may enlarge capacity contrasts (H5), and it
     makes static-based screens about three times noisier (O9).
2. **Compute-matched comparators.**
   - **Primary: equal steps.** Graft against uniform m× under the same regime, reporting realised
     parameter and parameter-step multiples.
   - **Secondary: matched parameter-steps.** Graft at horizon H against 2× uniform at H/2. Under
     constant lr it costs nothing, because the readouts nest.
   - **FLOPs** are not recorded, and a stage-2 graft's FLOPs per parameter differ from width's.
     Report them from analytic counts, not as the primary match.
   - **Wall time** is a property of this machine, for budgets only.
   - **λ (0.0271)** stays frozen for PDR-0057 and is never carried into another regime. Every new
     regime cell must fit its own no-growth and uniform arms first.
3. **Intervention capacity against the frozen 0.05 bar.**
   - At ≤ 1.10×, uniform width cannot reach 0.05 in this regime (O6).
   - Targeted function repair can (O7).
   - So whether the bar is reachable depends mainly on the **deficit class**, not the seed or the
     regime (a hypothesis for other regimes). The bar stays frozen.
4. **How natural the impairments are.**
   - Every Simic host carries an authored handicap from step 0. Designed hosts remain a legitimate
     training curriculum ([HLD:2222]), but they are not evidence for L1.
   - An emergent bottleneck would have to be identified on an unimpaired host by a detector fixed
     before any graft. Whether such a bottleneck exists, and is useful, is untested (§1, O12
     separation; H7).
5. **The closed loop and keep-or-cull (L7).**
   - Untested in Simic, which also lacks a cull path (O13).
   - In Esper-lite it ran once, single-seed and confounded with horizon (O14).
   - The only keep-or-cull evidence here (O11) is post hoc and on designed hosts.

## 4. The smallest discriminating future experiments

**Not authorised; each needs John's explicit decision and GPU grant.**

**Before any of them:**
- **Prerequisites** (systems review): GPU placement mapped to the granted card; an occupancy ledger
  and a terminal cap marker; a co-tenancy check by GPU UUID; process-group kill; `nice 19`, one
  worker per card; a pinned worktree with a maximum pause; a PDR-0056 launch record.
- **Discipline:** one round; no host, regime or seed added after data; dry run twice and
  byte-identical; fresh training seeds from a newly declared range, with any replay seeds
  declared.

**Budgets** use both measured bases: conservative 9.3 s, and fitted 11 s per unit plus 5.1 s per
arm, both per 10-epoch arm. Per-arm time scales with optimizer steps.

### R0 — zero-GPU analysis of finished records

- **What it covers:**
  - per-seed time-to-target curves (rung 4, C1);
  - analytic FLOPs per arm;
  - a 40-epoch sd prior from rung 4;
  - per-seed BatchNorm-host train CE from the finished C1 records.
- **Cost:** 0 GPU-h.
- **Reaches:** no L-claim. It sharpens R1's design.
- **Stop:** none needed.

### R2 — natural-bottleneck qualification (the founding-loop precondition)

**Question.** On unimpaired hosts, in a regime with room for a lifecycle, does a detector fixed in
advance identify a plateau signature, with train and dev flat together, before any intervention?
This tests the **precondition** of HLD:367 (identifiable bottlenecks). It does not test whether
any bottleneck is useful.

**Hosts.** Fixed by rule now: reference ×1, ×0.5 and ×0.25 width (N0, S1, S2).

**Arms and cells.** No growth only. Two kinds of cell:
- 4,096 examples × 40 epochs, all three hosts;
- 40,000 examples × 10 epochs, S1 and S2. The telemetry module caps fit data at 40,000
  (`atlas_telemetry.py:49-53`).

**Seeds and detector.**
- **Seeds:** 48 per cell.
- **Detector:** frozen now, as Esper-lite's rule transcribed verbatim (O12's sources).
  - Clock: 128-step ticks, a declared departure from the HLD's EndOfEpoch clock (HLD:691).
  - The "train and dev flat" condition needs clean train-set CE.
  - The "where" readout needs per-stage effective rank. Both are prerequisites.

**Stops:**
- a health gate;
- a byte-identical dry run;
- **cap 5 GPU-h**;
- one round.

**Budget:** about 3.9 GPU-h conservative, about 2.4 fitted. Per-step cost on the small hosts is
unmeasured.

**Gate.** NEW threshold: a cell "qualifies" if the detector fires in ≥ 50% of its runs before tick
30 with train and dev flat. Outcomes:
- **A cell qualifies** → it becomes a *candidate substrate* for R3. This is not evidence of a
  useful bottleneck.
- **Only data-bound plateaus,** or no firing → the transcribed trigger shows low incidence on these
  hosts and regimes. Recommend option A, recorded as "precondition not observed under this
  detector at bounded scale". **Not a falsification.**
  - A different detector would be a new owner decision, never a retune after data.

**Reaches:** none of L1–L7. It qualifies a substrate.

### R3 — minimal closed loop

**Only on an R2-qualified cell, and only if John authorises it.**

**Question.** Does the original heuristic loop (observe → when, which and where → graft → evaluate →
keep or cull, up to 3 seeds) improve the final model over never-graft and uniform width? And does
its cull carry information?

**Controller and library:**
- `HeuristicTamiyo` transcribed verbatim;
- library capped at 1.10× cumulative, fixed per host before data;
- two slot sites with R2's where-rule.

**Prerequisites:**
- a cull mechanic;
- a second slot site;
- seed width set by the host's channels;
- fork machinery.

**Arms, paired at the same horizon:**
- N: never graft;
- U: uniform 2×, with its own λ fitted and frozen before any loop arm is read;
- H: the loop;
- AK: always keep;
- H1: one germination only;
- S_k: H's first kept blueprint installed from step 0;
- a fork at H's first keep-or-cull decision, taking the opposite choice.

**Anchor:** a forced `norm` germination on `under_normalized`, for the instrument only. It is
synthetic compensation.

**Seeds:** 96 per host (half-width about 0.022 at sd 0.11).

**Stops:**
- fork-prefix bitwise equality;
- anchor failure → `instrument_failure`;
- `no_trigger` if < 50% of seeds germinate;
- the registered 10% divergence cap;
- **cap 15 GPU-h**;
- one round.

**Budget:** about 12.9 GPU-h conservative, 7.7 fitted, for two hosts. Higher on a 40,000-example
cell.

**Gate.** NEW thresholds and equivalence band, as in the intervention review:
- **H − N > 0.05, H beats U, and H beats the rate-weighted fork mean** → the first evidence that
  touches L1, L3 and L7. Reopen with L4 (learned against this heuristic) rather than Fleet A/G2′.
- **H beats N but not U** → option A.
- **Keep and cull within ±0.018** → L7 has nothing to decide at this scale.
- **H no better than the fork mean** → the in-run signal fails. Replace it with branch QA; never
  tune it after data.
- **S_k against H** decides H8 on a natural host.
- **Nothing beats N** → park the pathway until generated structure exists (L6).

**Reaches: L1, L3 (when, which and where), L7, and L2 against U on the qualified host. Not L4–L6.**
This is the only design in this review that reaches the founding loop.

### R1 — regime characterisation (designed hosts)

**Question.** Does the regime hide capacity effects, and does an annealed schedule change the
noise? Does C1's G1 pass survive a longer horizon?

**Hosts:** all four C1 hosts, with no selection.

**Arms:**
- no growth and 2× uniform;
- regimes C40 (constant lr, 40 epochs, with readouts at 10, 20 and 40 nesting) and K20 (cosine to
  0 over 20 epochs, equal steps to C20);
- plus a descriptive graft arm on `under_normalized` in C40 and K20.

**Seeds:** 48 fresh, descriptive. Optional replay seeds 10001–10016: epochs 0–9 must equal Fleet
C1's records bit for bit. Using C1's seeds departs from `fleet-c1.json`'s seed-range disclosure,
so that is John's call.

**Stops:**
- **cap 8 GPU-h**;
- a replay mismatch → no reading;
- more than 2 failed units → instrument failure;
- a comparator above 2.5% divergence → marked unstable;
- one round.

**Budget:** 54 ten-epoch arm-equivalents per seed × 48 ≈ 6.7 GPU-h conservative, about 3.7
fitted.

**Gate.** Descriptive; it applies none of the frozen thresholds.
- **The 2× contrast's upper bound stays < 0.05 at every horizon and regime** → the regime is not
  hiding capacity at this data size. The data-bound question (H1) is left for R1d.
- **The 2× contrast reaches ≥ 0.05 somewhere** → offer John R1c, the confirmatory regime test.
- **K20's paired sd well below C20's** → recommend annealing as the measurement regime.
- **The graft's lead over 2× holds at C20/C40** (descriptive) → C1's pass is not a 10-epoch
  artefact. A confirmatory check would be R1c's E2.

**Reaches:** none of L1–L7. It characterises the regime. The graft arm measures synthetic
compensation.

**Conditional follow-ups**, each its own decision:
- **R1c, a confirmatory regime test** (statistics plan v0.1):
  - NEW floor Δλ = 0.023 and sd-ratio 0.7, owner-gated, declared now;
  - n 192–384 from a 16-seed pilot;
  - 8.2–27.8 GPU-h.
- **R1d, data against steps:** 16,384 examples × 10 epochs, the same steps as 4,096 × 40. Cap 4
  GPU-h.

### Which experiments reach the founding loop

| Experiment | L1 emergent bottleneck | L3 diagnosis (when, which, where) | L7 keep or cull | Synthetic compensation only? |
|---|---|---|---|---|
| R0 | No | No | No | n/a (no intervention) |
| R1, R1c, R1d | No | No | No | Yes, for the graft arm; the rest is regime characterisation |
| R2 | Precondition only (detectability, not usefulness) | Precondition for "where" | No | No (no intervention) |
| R3 | **Yes**, on the qualified natural host | **Yes** | **Yes** | No, except the anchor, which is an instrument |
| The host-family screen (revision 3, option C) | No | No | No | Yes |

## 5. Recommendation (mine; the choice is John's)

**Keep the DEFER as the default.** If John wants to spend GPU time on this question, the
reconciled order is:
1. **R0.** Zero GPU.
2. **R2.** Cap 5 GPU-h. It is the only cheap step toward the founding loop.
3. **R3,** only if R2 qualifies a cell. Cap 15 GPU-h.

**R1** is worth running only if John wants to keep the designed-host pathway (option C) alive, or
to bound C1's scope by horizon. It does not move the founding loop.

**If R2 finds no qualifying cell,** I would recommend option A. It should be recorded as "the
transcribed trigger shows low incidence, and a useful emergent bottleneck was not identified at
bounded scale". That is not a falsification of the loop at other scales or with other detectors.

**Prerequisites and NEW thresholds.** Every prerequisite in §4 comes first. Every NEW threshold
needs John's signature before its experiment's data exist.

## 6. Panel disagreements

None of these is resolved by averaging.

1. **Which question to resolve first.**
   - Training dynamics and systems: horizon first.
   - Statistics: cosine first. It costs 1×, targets the BatchNorm hosts' noise (O4), and a long
     constant-lr horizon destabilises static (O9).
   - Intervention: the natural-bottleneck detector first.
   - **My reconciliation:** R1 runs both C40 and K20 together, so the horizon-vs-cosine order is
     moot inside it. The founding-loop track (R2 → R3) goes ahead of R1, because only that track
     reaches L1 and L7. This is my judgement, and the statistics and dynamics reviewers would weigh
     R1 more heavily.
2. **Sizing.** Systems: descriptive, 48 seeds. Statistics: confirmatory, 192–384 seeds with new
   floors.
   - **Reconciled:** R1 is descriptive; R1c is the conditional confirmatory follow-up.
3. **A capped descriptive run.**
   - Systems: report the completed seed prefix, deciding nothing.
   - Revision 3 §8: "no reading", the rule for confirmatory screens.
   - **Recommendation:** confirmatory → no reading; descriptive → a prefix report that decides
     nothing. John's choice.
4. **Reusing Fleet C1's seeds for replay checks.** Statistics and systems want it as an instrument
   check. It departs from `fleet-c1.json`'s seed-range disclosure. John's choice.
5. **Data-bound against step-bound** for the BatchNorm hosts (H1 against H2). Unresolved by the
   evidence. R1 (and R1d) would discriminate.

## 7. Corrections to host-family revision 3 raised by this panel

Revision 3 itself is unchanged; this is an addendum.

| Revision 3 | Correction |
|---|---|
| §6: "the lower bound never binds" | True only at 10 epochs. At 20 epochs the sd triples and it binds (O9) |
| D4 and §6 bound a ≤ 1.10× injection with λ | λ prices uniform widening only. Use the measured 1.1× arm (O6). λ does not bound targeted repair (O7) |
| §11 D: horizon is "the cheaper lever"; "about 2×"; "45k" | Contested (dissent 1). One 40-epoch constant-lr run nests the 10/20/40 readouts. Cosine is engineering work, not a configuration switch (`kernel_demo.py:877-881`). 45k fails validation (maximum 44,992, `bounded_data.py:71-72`; telemetry caps at 40,000). The 11× is an upper bound |
| §1 and D11: L7 "untested" | Esper-lite ran the closed loop once, single-seed and confounded (O14). Untested in Simic |
| D1, "where" | It drifts from the HLD's design, not from any demonstrated capability (O15) |
| D3, "easier" | Applies to L1 evidence. Designed hosts are a legitimate curriculum ([HLD:2222]) |
| §6: sd range treated as fixed | On the BatchNorm hosts the spread is regime noise (O4), so sds for new classes depend on the regime |
| The defer record | Add that the only timing evidence runs against L1's timing, subject to H8. This is now added to [`defer-record.md`](defer-record.md) |

## 8. Sources

- **Panel materials:** [`brief.md`](brief.md), [`evidence/convergence.md`](evidence/convergence.md)
  (with its script), and [`evidence/stats-reanalysis/`](evidence/stats-reanalysis/). Its scripts
  read only published summaries and import nothing from the repository.
- **Simic results:**
  - `docs/results/2026-10-11-fleet-c1*.md` and their evidence folders;
  - `2026-10-09-rung4-timing-horizon.md` and `tables/`;
  - `2026-10-11-static-norm-divergence.md`.
- **Configuration and code:**
  - `experiments/kernel_demo.py:145-147,153,319-343,772-778,858-890`;
  - `experiments/atlas_telemetry.py:49-53,146`;
  - `experiments/bounded_data.py:71-72,210`;
  - `experiments/bounded_comparison.py:600-617`;
  - `experiments/bounded_screen.py:198-201`;
  - `experiments/c1_study.py:499-558`.
- **Original sources:**
  - the HLD (`/mnt/data/archive/esper.old@8d69bec`: lines 175-176, 367, 691, 1359, 2222);
  - Esper-lite at `0807ccf`: `tamiyo/tracker.py:108-160`, `heuristic.py:179-212,193,271-311`,
    `leyline/__init__.py:592-610`;
  - Esper-lite at `0ee3a001`: `README.md:79-88`, `poc_tamiyo.py:54-62`.
- **Prior reviews:** `docs/product/spikes/2026-10-11-host-family/proposal.md` (revision 3) and
  `panel-review.md`.
