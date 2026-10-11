# Training-regime design review: reconciled recommendation — 2026-10-11

**Design review only (John, relayed by his assistant).** The controller pathway is on a
**reversible DEFER** ([`defer-record.md`](defer-record.md)).
- **Nothing here launches.** No experiment below is authorised, and none follows automatically.
- **Out of scope:** implementation, tests, training, GPU use, spending, access grants, merges and
  deployment.
- **Sultai keeps GPU priority.**
- **Thresholds.** Every existing threshold stays frozen. Every new threshold is marked **NEW**, is
  declared here before any data, and takes effect only if John signs it.

**Panel:**
- **Four specialists**, reviewing independently the [brief](brief.md) and the frozen materials at
  `9733431`:
  - training dynamics (`training-diagnostician`);
  - statistics (`counterfactual-statistician`);
  - intervention and the closed loop (`morphogenesis-reviewer`);
  - systems and compute (`plan-review-systems`).
- **An independent adversarial reviewer** (`product-decision-critic`), who reviewed the first
  reconciliation (`aebd3ad`). It endorsed with changes and found no blockers. Its findings, and how
  this revision takes them, are in §9.

**Provenance:**
- [`evidence/panel-notes/`](evidence/panel-notes/) holds my condensed summary of each reviewer's
  report.
- [`evidence/stats-reanalysis/`](evidence/stats-reanalysis/) holds the statistics reanalysis
  (published summaries only; it imports nothing from the repository).
- [`evidence/convergence.md`](evidence/convergence.md) and
  [`evidence/rung4-gain-quantiles.md`](evidence/rung4-gain-quantiles.md) are descriptive tables.
  Each has its script.

**Status of the evidence.** Nothing was trained. Reviewers read published summaries and finished,
already-analysed records on CPU. Every seed involved is already seen, so everything below is
**exploratory** and changes no registered reading.

## 1. Observed evidence

Numbers come from records; interpretations are in §2.

| # | Observation | Source |
|---|---|---|
| O1 | **No host had converged at 10 epochs.** No-growth dev CE is still falling 0.028–0.040 nats per epoch over epochs 7–9 on all four C1 hosts (CIs exclude 0) | stats reanalysis (`out.txt`); [`convergence.md`](evidence/convergence.md) |
| O2 | **BatchNorm hosts:** at epoch 9, train CE 1.05–1.09, dev CE 1.23–1.29, train–dev gap +0.16 to +0.22 (about +0.10 at epoch 3). 2× uniform lowers train and dev CE alike, and the gap does not change. Train CE is measured on augmented batches in train mode, so the true gap is larger | `convergence.md` |
| O3 | **`under_normalized`:** gap about 0 at epoch 9. Per seed, the gap widens by +0.036 [0.028, 0.043] from epoch 3 to 9 and by +0.066 [0.059, 0.074] from epoch 9 to 19. At epochs 17–19 dev CE is still falling 0.011 nats per epoch | stats reanalysis; `convergence.md` |
| O4 | **Decomposing the paired differences over epochs 7–9:** <br>• on the BatchNorm hosts, the epoch-to-epoch jitter share of single-epoch variance is 0.98–1.03, so the persistent per-seed share is about 0–2%; <br>• on `under_normalized` the jitter share is 0.42–0.78. <br>Pairwise cross-epoch correlations (−0.08 to +0.09 on the BatchNorm hosts) agree. This describes seed persistence only. It makes no claim about independence | `stats-reanalysis/out-extra.txt` lines 11–23 |
| O5 | **λ** = 0.0271 [0.0240, 0.0304] (seed bootstrap). It is not constant inside the regime: 0.019 at epoch 5 against 0.029 at epoch 9 (+0.010 [0.003, 0.017]) | stats reanalysis |
| O6 | **The measured 1.1× uniform arm** changes late CE by −0.011 to +0.003 nats. It is 0.003 *worse* than no growth on `channel_starved`, and every 95% upper bound on the gain is ≤ 0.018. At the uniform price, 0.05 nats ≈ 3.6× [3.1, 4.3] the parameters, extrapolated past the measured 2× | `stats-reanalysis/out.txt` §A |
| O7 | **Targeted function repair is far cheaper than width on one designed host.** On `under_normalized`, the `norm` graft at 1.0008× gains 0.096 [0.091, 0.101], about 3,000× the uniform price per doubling, and static `norm` about 0.14. On the other three hosts, no designed seed at ≤ 1.10× gained > 0.05; `attn` on `no_spatial_mix` gained +0.020 | `out.txt` §A; C1 |
| O8 | **Rung 4, 20-epoch cell, `under_normalized`.** Static's paired gain over no growth: <br>• median 0.149 at epoch 6 and 0.107 at epoch 19; <br>• mean 0.041 at epoch 19, pulled down by a lower tail (p10 −0.162). <br>The scheduled graft's median rises to 0.112 at epoch 19 | [`rung4-gain-quantiles.md`](evidence/rung4-gain-quantiles.md) |
| O9 | **Hypothetical sensitivity check:** the registered screen rule applied to rung 4's 20-epoch cell would not pass static on that host. Mean 0.030 [0.001, 0.058] with failures scored at ln 10, 0.045 completed only. That arm's paired sd triples (0.133 → 0.400), and the lower-bound clause then binds. Nothing registered runs at 20 epochs, so this is sensitivity, not a reading | stats reanalysis |
| O10 | **At matched 2× parameter-steps on `under_normalized`:** no growth for 20 epochs, late CE 1.3665 (rung 4), against `scale_x2` for 10 epochs, 1.5847 (C1). A 0.218-nat difference, unpaired across studies | systems review (`panel-notes/4-systems.md`, F4) |
| O11 | **A one-decision keep-or-cull rule with rollback never beat the best fixed policy** (d = 2–6). It was worse on `under_normalized` (+0.010 to +0.023) and `no_spatial_mix` (+0.005), null elsewhere. Caveats: <br>• the rule was fixed after seeing published aggregates; <br>• decision and score both use dev; <br>• the comparator was chosen afterwards | `out-extra.txt` lines 25+ |
| O12 | **Trigger incidence and detector sensitivity (descriptive).** Esper-lite's germination trigger, replayed on published records, fired in **5/768 `under_normalized` no-growth runs by epoch 9 and 74/768 by epoch 19** (median epoch 16). Reproduced independently by the adversarial reviewer; the possible off-by-one changes neither count. <br>• **The blocking clause** is the accuracy-plateau condition: 142 runs had latched by epoch 9 and 428 by epoch 19. <br>• **C1 latch counts by epoch 9:** 132 (`under_normalized`), 52, 36, 39 (BatchNorm hosts). C1 has no per-epoch accuracy, so latch only. <br>• **The trigger missed a known deficit.** `under_normalized` has a demonstrated, repairable deficit (O7), and the trigger fired on 5/768 by epoch 9. <br>• **Its units were set for a different regime:** 150 epochs at lr 0.01 | rung 4 `tables/per-epoch.jsonl.gz`; C1 `arms-summary.jsonl.gz`; EL `tamiyo/tracker.py:108-160`, `heuristic.py:179-212`, `leyline/__init__.py:482-485,592-610@0807ccf` |
| O13 | **Implementation finding: current Simic has no cull path.** `Stage` has no CULLED state (`kernel_demo.py:772-778`), `epoch_tick` fossilises after fixed counts (`:858-873`), and nothing in `experiments/` culls | intervention review; confirmed by the adversarial reviewer |
| O14 | **The original closed loop has one recorded run.** Tamiyo heuristic 82.16%, fixed schedule 80.16%, 10-epoch baseline 69.31%. That is a single seed, up to 40 against 10 epochs, with test-loader selection. The only loop-against-fixed contrast is +2.0 points | EL `README.md:79-88@0ee3a001` |
| O15 | **"Where" was designed, never demonstrated.** `HeuristicTamiyo`'s only slot logic is `available_slots <= 0` (EL `heuristic.py:193@0807ccf`). Its "which" is round-robin with prune penalties (`_get_next_blueprint`). HLD:367 lists "Models exhibit identifiable bottlenecks through telemetry analysis" as a research **assumption** | intervention and adversarial reviews |
| O16 | **Cost.** Optimizer steps drive cost; width barely matters (the GPU is busy 24% of an epoch). Readouts at 10, 20 and 40 epochs nest in one constant-lr run. Cosine-schedule runs do not nest | `docs/results/2026-10-09-atlas-g0-cotenancy/` (profile); `panel-notes/4-systems.md` |

**Three things kept separate (O12, O13).**
1. **Low trigger incidence, with a detector of limited sensitivity.**
   - In these runs and regimes, the transcribed original trigger rarely fired.
   - It also fired rarely on a host with a demonstrated, repairable *rate* deficit (O7), because it
     looks for plateaus. So its silence on any host is **weak evidence of absence**.
   - Neither point means the original loop "cannot run" here. A loop could run with another
     detector or regime, each a new owner decision.
2. **An untested claim.** Whether unimpaired hosts develop a *useful* emergent bottleneck is
   untested; HLD:367 is an assumption. A trigger replay establishes neither its presence nor its
   absence. A plateau signature is not a bottleneck that an intervention usefully relieves. Only an
   intervention test (R3) can show that.
3. **An implementation gap.** Simic has no cull path. That is missing code, not evidence about
   the loop.

## 2. Hypotheses

Each is an interpretation, with the result that would falsify it.

| # | Hypothesis | Falsified by |
|---|---|---|
| H1 | The BatchNorm hosts are moving into a data/generalisation limit at 4,096 examples (O2) | At equal steps, 16,384 examples giving dev CE and gap equivalent to 4,096's within the study's stated resolution: an interval that excludes a material improvement, not merely a non-significant difference |
| H2 | They were also step-limited at 10 epochs (O1) | More steps at the current lr not lowering no-growth dev CE: a 10→20-epoch change whose 95% interval excludes improvements larger than the study's stated resolution. Flattening that begins only after epoch 10 (e.g. by epoch 20) is consistent with H2, not against it |
| H3 | `under_normalized`'s deficit is an optimisation-rate deficit that normalisation removes as a lasting offset (O7, O8) | The median static gain at 40 epochs with a 95% upper bound ≤ 0.02: the offset does not last. A pre-declared schedule letting no growth match static would bear on whether *structure* is needed, not on H3 |
| H4 | Constant lr 0.05 is too high late in training. Static's divergence tail and its sd increase at 20 epochs fit that (O8, O9) | A pre-declared decayed schedule whose late-failure rate and sd are equivalent to constant lr's within the study's stated precision |
| H5 | Capacity returns (λ) grow with horizon or data (O5's within-regime trend) | A longer or annealed regime whose λ has a 95% upper bound ≤ 0.0271 |
| H6 | On the BatchNorm hosts in this regime, per-seed headroom is noise no per-seed decision can use (O4, O11) | On fresh seeds in this regime, a per-seed decision rule fixed in advance beating the best fixed policy (95% upper bound < 0) |
| H7 | **The tension.** Unimpaired hosts already have the functions the library restores, so the one demonstrated repair route (O7) may never meet an emergent bottleneck | On a natural host, the loop (R3's H) beating never-graft and uniform width |
| H8 | Static's lead over the graft (+0.046; rung 4's best schedule at T0) partly reflects handicaps built in from step 0, not the loop | **Contradicted** by installing still ahead of growing on a natural host, with no authored handicap: R3's (H − S_k) 95% lower bound > 0. **Consistent with H8** (not a falsification): growing shown non-inferior to installing there, (H − S_k) upper bound < +δ |
| H9 | Whether a ≤ 1.10× injection can reach 0.05 depends mainly on the deficit class, not on the seed or the regime (from O6, O7; neither seed nor regime was varied) | A capacity-class deficit repaired by > 0.05 at ≤ 1.10× in another regime |

**An inconclusive or underpowered interval falsifies no hypothesis here.** Only an interval that excludes the hypothesised effect at the stated precision counts against it.

## 3. The five review topics

1. **Convergence and duration.** The 10-epoch endpoint is before convergence on every host (O1).
   The two host families are limited differently: the BatchNorm hosts' gap is widening (H1/H2
   undetermined), and `under_normalized`'s gap is near zero at epoch 9 (O2, O3).
   - **Neither "capacity effects are small" nor "a 0.05 repair is impossible" follows.**
   - **A longer constant-lr horizon cuts both ways.** It may enlarge capacity contrasts (H5). In
     the one static arm measured at 20 epochs, it tripled the paired sd (O9).
2. **Compute-matched comparators.**
   - **Primary: equal steps.** Graft against uniform m× under the same regime, reporting realised
     parameter and parameter-step multiples.
   - **Secondary: matched parameter-steps.** Graft at horizon H against 2× uniform at H/2. Free
     under constant lr, because the readouts nest.
   - **FLOPs** come from analytic counts, as a companion, never the primary match. A stage-2
     graft's FLOPs per parameter differ from width's.
   - **Wall time** is for budgets only.
   - **λ (0.0271)** stays frozen for PDR-0057 and is never carried into another regime. Each new
     regime cell fits its own no-growth and uniform arms first.
3. **Intervention capacity against the frozen 0.05 bar.**
   - At ≤ 1.10×, uniform width does not reach 0.05 in this regime (O6).
   - Targeted function repair did, on one designed host (O7).
   - Anything more general is H9. The bar stays frozen.
4. **How natural the impairments are.** Every Simic host carries an authored handicap from step 0.
   - Designed hosts remain a legitimate training curriculum ([HLD:2222]), but they are not evidence
     for L1.
   - An emergent bottleneck would have to be identified on an unimpaired host by a detector fixed
     before any graft.
   - Whether such a bottleneck exists, and is useful, is untested. The trigger replay does not
     settle it (§1, items 1–2).
5. **The closed loop and keep-or-cull (L7).**
   - Untested in Simic, which has no cull path (O13).
   - In Esper-lite it ran once (O14).
   - The only keep-or-cull evidence here (O11) is post hoc and on designed hosts.

## 4. The smallest discriminating future experiments

**Not authorised.** Each needs John's explicit decision, a GPU grant naming the card, window and
cap, and his signature on its NEW thresholds before its data exist.

**Prerequisites for any GPU experiment** (systems review):
- GPU placement mapped to the granted card;
- an occupancy ledger and a terminal cap marker;
- a co-tenancy check by GPU UUID;
- process-group kill;
- `nice 19`, one worker per card;
- a pinned worktree with a maximum pause;
- a PDR-0056 launch record.

**Discipline:**
- one round per experiment;
- no host, regime or seed added after data;
- dry run twice, byte-identical;
- fresh training seeds from a newly declared range;
- replay seeds declared.

**A cap hit or an abandoned run** gives no reading. It uses up the round, and **it is never read as
a negative result.**

**Budgets** use both bases, per 10-epoch arm: conservative 9.3 s; fitted 11 s per unit plus 5.1 s
per arm. Cost scales with optimizer steps.

### R0 — zero-GPU analysis of finished records (0 GPU-h)

- **Covers:** per-seed time-to-target curves (rung 4, C1); analytic FLOPs per arm; a 40-epoch sd
  prior from rung 4; per-seed BatchNorm-host train CE from the finished C1 records.
- **Reaches:** no L-claim. It sharpens R1 and R2.

### R2 — natural-bottleneck qualification (the founding-loop precondition)

**Question.** On unimpaired hosts, does a detector fixed in advance find a plateau signature, with
train and dev flat together, early enough to leave room for a lifecycle? It tests the
*detectability* precondition of HLD:367, not *usefulness*.

**Hosts.** Reference ×1, ×0.5 and ×0.25 width (N0, S1, S2), all with BatchNorm, fixed by rule now
and before any R2 data. They were conceived after C1 (host-family proposal B14). That bars them
from counting in that screen; R2 is a different question with no library arm. S2 is
capacity-limited by construction. If S2 qualifies, its bottleneck is probably plain capacity, which
a ≤ 1.10× library cannot fix (O6).

**Arms and cells.** No growth only:
- 4,096 examples × 40 epochs: N0, S1, S2;
- 16,384 examples × 20 epochs: S1, S2. Fit sets nest (`bounded_data.py:210`).

**Seeds:** 48 per cell.

**Detector (frozen now):** Esper-lite's rule on its own **epoch clock** (HLD:691), with its own
per-epoch constants: latch band (−5%, +3%), 3 and 5 epochs, 0.5 accuracy points (EL
`leyline/__init__.py:482-485,592-610`, `tamiyo/tracker.py:108-160`, `heuristic.py:179-212`
@0807ccf).

**Departures from the original, all NEW:**
- **"Flat together":** clean train CE, evaluated each epoch on a fixed 4,096-example subset of the
  fit set, also stays within the latch band over the same three epochs.
- **Where-rule, frozen now:** among stages 1–3, the stage whose effective rank on a fixed probe
  batch, normalised by stage width, has fallen most at the firing epoch relative to its own
  epoch-2 value. Descriptive in R2; R3 uses it. Per-stage effective rank is a prerequisite
  (`atlas_telemetry.py:146` has stage 2 only).
- **Qualifying windows:**
  - before epoch 30 on the 4,096 × 40 cells (≥ 10 epochs left for an 8-epoch lifecycle,
    `kernel_demo.py:145-147`);
  - before epoch 12 on the 16,384 × 20 cells (≥ 8 left).

**Stops:**
- a health gate (finite loss, per-epoch slope, active-channel fraction);
- a byte-identical dry run;
- **cap 6 GPU-h**;
- one round.

**Budget:** cells 3 × 48 × 4 + 2 × 48 × 8 = 1,344 ten-epoch arm-equivalents, plus clean-train
evaluation (about +30% on the 4,096 cells, +8% on the 16,384 cells) ≈ 1,578. That is about
**4.1 GPU-h conservative, 2.5 fitted**. Per-step cost on the small hosts is unmeasured.

**Outcomes, per cell.** NEW threshold: 50%.

| Outcome | Reading |
|---|---|
| ≥ 50% of runs fire "flat together" within the window | The cell **qualifies as a candidate substrate** for R3. This is not evidence of a useful bottleneck |
| 1–49% fire "flat together" | **Partial.** Not a candidate. Reported with its rate |
| Fires, but only with the train–dev gap widening (not flat together) | **Data-bound plateau.** Not a candidate. This is not low incidence: the trigger fired |
| Fires in < 1% of runs | **Low incidence under this detector.** Weak evidence of absence (O12) |
| Fails the health gate | **Unreadable.** Not a negative result |

**If no cell qualifies,** I would present John with three options at parity:
- **A, stop:** recorded as "the precondition was not observed under this detector at bounded
  scale", **not a falsification**;
- **B, stay deferred;**
- **a new detector:** a new owner decision, designed before any new data, never a retune of this
  one.

**Reaches:** none of L1–L7. It qualifies a substrate.

### R1 — regime characterisation (designed hosts)

**Question.** Does the regime hide capacity effects? Does annealing change the noise? Is C1's G1
pass consistent with longer horizons?

**Hosts:** all four C1 hosts, with no selection.

**Arms:**
- no growth and 2× uniform, in C40 (constant lr, 40 epochs, readouts at 10, 20 and 40 nest) and
  K20 (cosine to 0 over 20 epochs, equal steps to C20);
- a descriptive graft arm on `under_normalized` in C40 and K20.

**Seeds:**
- 48 fresh;
- optional replay on Fleet C1's seeds 10001–10016: no growth and 2× in C40, where epochs 0–9 must
  equal C1 bit for bit. That departs from `fleet-c1.json`'s seed-range disclosure, so it is John's
  call.

**Stops:**
- **cap 9 GPU-h**;
- a replay mismatch → no reading;
- more than 2 failed units → instrument failure;
- a comparator above 2.5% divergence → unstable;
- one round.

**Budget:** 54 arm-equivalents × 48 = 2,592, about 6.7 GPU-h conservative (3.7 fitted). The replay
adds 32 × 16 = 512, about 1.3 GPU-h, for 8.0 in total.

**Readouts** (descriptive; NEW definitions, applying no frozen threshold):
- **"Reaches":** the 2× contrast's mean ≥ 0.05 with 95% lower bound > 0.
- **"Well below":** a 95% upper bound on K20's paired sd ÷ C20's < 0.7. That is the NEW sd-ratio
  threshold, also used in R1c.
- **"Consistent with C1's pass":** graft − 2× mean < 0 with 95% upper bound < 0 at C20 and at
  C40.

**Readings, each a recommendation to John:**
- **Below threshold:** the 2× contrast's 95% upper bound is < 0.05 at every readout. A 2× capacity
  effect of 0.05 or more is **not supported at these readouts and this precision** (48 seeds).
  - It does not show that capacity effects are absent, nor that the regime "is not hiding
    capacity".
  - A longer horizon, more data or another schedule could still reveal them. H1 is left to R1d.
- **Indeterminate:** at some readout the interval includes 0.05 without "reaching" it. **No
  conclusion** at this precision; R1c is the sized follow-up, John's choice.
- **The 2× contrast reaches 0.05 somewhere** → offer R1c.
- **"Well below"** → recommend annealing as the measurement regime, **including for R3**. Otherwise
  no recommendation about annealing at this precision.
- **"Consistent with C1's pass"** → reported as consistent; confirmation would be R1c's statistical
  check. Not shown → no reading, and not evidence against C1's pass.

**Reaches:** none of L1–L7. The graft arm measures synthetic compensation.

**Conditional follow-ups:**
- **R1c, a confirmatory regime test** (statistics plan v0.1; summary in
  [`panel-notes/2-statistics.md`](evidence/panel-notes/2-statistics.md)):
  - NEW floor Δλ = 0.023 and the sd-ratio threshold 0.7;
  - n 192–384 from a 16-seed pilot;
  - 8.2–27.8 GPU-h.
- **R1d, data against steps:** 16,384 examples × 10 epochs, the same steps as 4,096 × 40. Cap 4
  GPU-h.

### R3 — minimal closed loop

**Only on an R2-qualified cell, after R1 sets the regime, and only if John authorises it.**

**Question.** Does the original heuristic loop improve the final model over never-graft and
uniform width, does its first keep-or-cull decision carry information, and does its where-rule
beat a random site?

**Controller and mechanics:**
- **Controller:** `HeuristicTamiyo` transcribed verbatim, up to 3 seeds. Its "which" is
  round-robin, so **R3 does not test "which" as diagnosis**.
- **Library:** capped at 1.10× cumulative, fixed per host before data.
- **Sites:** two, chosen by R2's frozen where-rule.
- **Keep or cull:**
  - transcribed: fossilise if the alpha-ablation contribution exceeds 0.5 accuracy points,
    otherwise prune;
  - **cull** = prune: the slot returns to DORMANT and its parameters leave the optimizer; host
    weights are not rolled back;
  - decisions are made on a **separate probe split**, chosen by example hash and disjoint from the
    scoring dev set (NEW; precedent: S1 pitfall P5).

**Arms, paired at the same horizon:**
- N: never graft;
- U: uniform 2×, with its own λ fitted and frozen before any loop arm is read;
- H: the loop;
- AK: always keep;
- ONE: one germination only;
- S_k: H's first kept blueprint installed at its site from step 0;
- FORK: identical to H up to its first keep-or-cull decision, then the opposite action;
- RS: H's schedule and blueprints at random sites.

**Anchor:** a forced `norm` germination on `under_normalized`. It is an instrument only, and it is
synthetic compensation.

**Sizing:**
- n from a 16-seed pilot outside the range, fixed before the confirmatory seeds. The planning sd
  is 0.20, reflecting O9 rather than C1's 10-epoch 0.11.
- **δ (NEW)** = R3's own 95% half-width at that n, declared before data. About 0.04 at n = 96 and
  sd 0.20.

**The gate, written out** (all NEW and owner-gated except the frozen 0.05 bar, reused unchanged in
its registered form):

Each comparison is read in one of three ways. The labels in the middle column are **NEW**
interpretation labels: they describe an interval and decide nothing on their own. **An
indeterminate interval is never read as evidence against a claim.**

| Comparison | Shown | Evidence the other way, or equivalence | Indeterminate |
|---|---|---|---|
| H − N (gain; positive = the loop is better) | mean > 0.05 and 95% lower bound > 0 (the registered form, unchanged) | **Below threshold:** 95% upper bound < 0.05. A gain of 0.05 or more is not supported at this precision. If the lower bound is > 0, a positive below-threshold effect is shown; otherwise a zero effect is not excluded | Any other interval |
| H against U (negative = H is better) | (H − U) 95% upper bound < 0 | **U ahead:** lower bound > 0. **Equivalent:** 95% CI within ±δ | Any other interval |
| H against FORK (L7) | (H − FORK) upper bound < 0: the decision carries information | **The opposite choice was better:** lower bound > 0. **Equivalent:** CI within ±δ, so there is nothing to decide at this resolution | Any other interval |
| H against RS ("where") | (H − RS) upper bound < 0 | **The random site was better:** lower bound > 0. **Equivalent:** CI within ±δ | Any other interval |
| H against S_k (grow against install) | **Growing non-inferior:** (H − S_k) upper bound < +δ | **Installing ahead:** lower bound > 0 | Any other interval |

When more than one label applies (for example U ahead by less than δ), all of them are reported.

**Readings:**
1. **No reading:** an instrument failure (anchor, fork-prefix bitwise mismatch, more than 10%
   divergence), a cap hit, or `no_trigger` (fewer than 50% of seeds germinate).
2. **H − N below threshold** → a gain of 0.05 or more from the loop is not supported on this host
   at this precision. That is not "the loop adds nothing": a smaller effect may be shown or not
   excluded. Return to John with options A and B.
3. **H − N indeterminate** → no conclusion about the loop's gain on this host at this precision.
   Return to John with options A and B. Any re-run is a new, separately sized owner decision. I
   would not recommend A on an indeterminate interval alone.
4. **H − N shown; H against U shows U ahead or equivalent** → no advantage over uniform width at
   this resolution, so L2 is not supported on this host. I would recommend A; the choice is John's.
   **H against U indeterminate** → L2 undetermined; reported to John with no recommendation drawn
   from it.
5. **H − N and H against U shown, growing shown non-inferior to installing, and the cell not
   capacity-limited by construction** → the first evidence touching L1 on a natural host.
   - Add **L3, where** if H beats RS.
   - Add **L7** if H beats FORK.
   - Then recommend reopening with L4 (learned against this heuristic) rather than Fleet A/G2′.
6. **H − N and H against U shown, installing ahead, and growing not shown non-inferior** →
   targeted structure helps, but installing beats growing here. That is evidence for targeted
   installation, not L1.
7. **Any comparison with an indeterminate interval** → no reading for that comparison's claim.
   Never read as evidence against it. In particular, if H − N and H against U are shown but the
   S_k comparison is indeterminate, L1 is undetermined: structure helps, but grow-versus-install
   is unresolved.

**Budget** (8 arms × 96 seeds):
- a 4,096 × 40 cell: 3,072 arm-equivalents per host, about 7.9 GPU-h conservative, 4.3 fitted;
- a 16,384 × 20 cell: 6,144, about 15.9 conservative, 8.6 fitted.

**Cap: 15 GPU-h.**
- It fits **one host on a 4,096 × 40 cell**.
- A 16,384 × 20 cell fits only under the fitted basis.
- Anything larger is a new decision.

**Reaches** (each only if the corresponding row is shown):
- **L1** on the qualified natural host, conditional on growing being shown non-inferior to installing
  ((H − S_k) upper bound < +δ) and the cell not being capacity-limited by construction;
- **L3:** "when", only partly, as the trigger's timing; "where" only if RS is beaten;
- **L7**, if FORK is beaten;
- **L2** against U.

**Not reached:** L3's "which", L4, L5 and L6. **This is the only design here that can reach the
founding loop.**

### Which experiments reach the founding loop

| Experiment | L1 emergent bottleneck | L3 diagnosis | L7 keep or cull | Synthetic compensation only? |
|---|---|---|---|---|
| R0 | No | No | No | n/a (no intervention) |
| R1, R1c, R1d | No | No | No | Yes, for the graft arm; the rest is regime characterisation |
| R2 | Precondition only (detectability, not usefulness) | Precondition for "where" | No | No (no intervention) |
| R3 | **Conditionally** (reading 5 above) | "When" partly; "where" if RS beaten; not "which" | **If FORK beaten** | No, except the anchor, which is an instrument |
| The host-family screen (revision 3, option C) | No | No | No | Yes |

## 5. Recommendation (mine; the choice is John's)

**Disclosure.** In host-family revision 3 I recommended option A (stop). John chose B. Three of the
four specialists would characterise the regime first: training dynamics and systems by horizon,
statistics by cosine. Only the intervention reviewer would start with the detector. My ordering
below departs from that majority, for the reason given.

**Keep the DEFER as the default.** If John wants to spend GPU time on the founding loop, the
reconciled order is:
1. **R0.** Zero GPU.
2. **R2.** Cap 6 GPU-h. It is the cheapest step that bears on L1's precondition.
3. **If an R2 cell qualifies:** **R1** (cap 9 GPU-h), so R3's regime is chosen on evidence, then
   **R3** (cap 15 GPU-h).
4. **If no R2 cell qualifies:** A, B, or a new detector, at parity, John's choice. Not a
   falsification.

**R1 alone** is the right first spend if John's interest is option C, or bounding C1's scope by
horizon, rather than the founding loop.

**My reason for putting R2 ahead of R1 against the majority:** R1 cannot reach L1 or L7 whatever
it shows. R2 is cheaper, and it is the gate to the only design that can (R3).

## 6. Panel disagreements

1. **What to resolve first.** Three of four: regime (horizon or cosine). One: the detector. My
   reconciliation is §5's, disclosed as departing from the majority. R1 runs C40 and K20 together,
   so the horizon-vs-cosine order is moot within it.
2. **Sizing.** Systems: descriptive, 48 seeds. Statistics: confirmatory, 192–384 seeds.
   **Reconciled:** R1 is descriptive; R1c is the conditional confirmatory follow-up.
3. **A capped descriptive run.**
   - Systems: report the completed seed prefix, deciding nothing.
   - Revision 3: "no reading".
   - **In this review:** no reading for R2 and R3. A completed-prefix report is acceptable for R1
     and R1d only, and decides nothing. John's choice.
4. **Reusing C1's seeds for replay.** It is an instrument check, against `fleet-c1.json`'s
   seed-range disclosure. John's choice.
5. **H1 against H2** for the BatchNorm hosts. Unresolved by the evidence; R1 and R1d discriminate.
6. **The timing evidence and L1.**
   - The intervention reviewer: the only timing evidence runs against L1's timing.
   - The adversarial reviewer: on hosts handicapped from step 0, "earliest is best" is what L1
     predicts, so the evidence is uninformative about L1's timing.
   - Both are recorded in the defer record. H8 and R3's S_k arm would discriminate.
7. **What O12 tells us.**
   - Intervention: mainly low incidence.
   - Adversarial: mainly the detector's limited sensitivity, because it missed a known deficit.
   - Both readings are kept in §1, items 1–2.

## 7. Corrections to host-family revision 3 raised by this panel

Revision 3 itself is unchanged; this is an addendum.

| Revision 3 | Correction |
|---|---|
| §6: "the lower bound never binds" | True at 10 epochs. In the one static arm measured at 20 epochs the sd tripled and it would bind (O9) |
| D4 and §6 bound a ≤ 1.10× injection with λ | λ prices uniform widening only. Use the measured 1.1× arm (O6). λ does not bound targeted repair (O7) |
| §11 D: horizon is "the cheaper lever"; "about 2×"; "45k" | Contested (§6, item 1). One 40-epoch constant-lr run nests the 10/20/40 readouts. Cosine is engineering work (`kernel_demo.py:877-881`). 45k fails validation (maximum 44,992, `bounded_data.py:71-72`; telemetry caps at 40,000). The 11× is an upper bound |
| §1 and D11: L7 "untested" | Esper-lite ran the loop once, single-seed (O14). Untested in Simic |
| D1, "where" | It drifts from the HLD's design, not from a demonstrated capability (O15) |
| D3, "easier" | Applies to L1 evidence. Designed hosts are a legitimate curriculum ([HLD:2222]) |
| §6: sd range treated as fixed | On the BatchNorm hosts the spread is mostly epoch-to-epoch jitter (O4), consistent with H6, so sds for new classes may depend on the regime |
| The defer record | Both readings of the timing evidence added (§6, item 6) |

## 8. Sources

- **Panel materials:**
  - [`brief.md`](brief.md), [`evidence/convergence.md`](evidence/convergence.md),
    [`evidence/rung4-gain-quantiles.md`](evidence/rung4-gain-quantiles.md) (each with its
    script);
  - [`evidence/stats-reanalysis/`](evidence/stats-reanalysis/);
  - [`evidence/panel-notes/`](evidence/panel-notes/).
- **Simic results:**
  - `docs/results/2026-10-11-fleet-c1*.md` and their evidence folders;
  - `2026-10-09-rung4-timing-horizon.md` and `tables/`;
  - `2026-10-09-atlas-g0-cotenancy/`;
  - `2026-10-11-static-norm-divergence.md`.
- **Configuration and code:**
  - `experiments/kernel_demo.py:145-147,153,319-343,772-778,858-890`;
  - `experiments/atlas_hosts.py:52`;
  - `experiments/atlas_telemetry.py:49-53,146`;
  - `experiments/bounded_data.py:71-72,210`;
  - `experiments/bounded_comparison.py:600-617`;
  - `experiments/bounded_screen.py:198-201`;
  - `experiments/c1_study.py:499-558`;
  - `docs/prereg/fleet-c1.json`.
- **Original sources:**
  - HLD `/mnt/data/archive/esper.old@8d69bec`: lines 175-176, 367, 691, 1359, 2222;
  - Esper-lite at `0807ccf`: `tamiyo/tracker.py:108-160`, `heuristic.py:179-212,193,271-311`,
    `leyline/__init__.py:482-485,592-610`;
  - Esper-lite at `0ee3a001`: `README.md:79-88`, `poc_tamiyo.py:54-62`.
- **Prior reviews:** `docs/product/spikes/2026-10-11-host-family/proposal.md` (revision 3) and
  `panel-review.md`.

## 9. Adversarial review and how this revision takes it

- **Verdict on `aebd3ad`:** endorse with changes, no blockers. It said the R2 and R3 gates could
  not be signed as written.

**Taken in this revision:**

| Finding | Change |
|---|---|
| 1. An R2 null routed to stop, but the detector missed a known deficit | O12 and §1 now record the miss. An R2 null goes to A, B or a new detector at parity. §5's wording now matches §4's. The outcomes are split: data-bound, partial, low-incidence and unreadable |
| 2. The detector was not verbatim; "flat" and the where-rule were undefined | Epoch clock with the original per-epoch constants (now citing `leyline:482-485`). The 16,384 × 20 cell replaces the 40,000 × 10 cell. "Flat together", the where-rule and the qualifying windows are defined and marked NEW |
| 3. R3 overclaimed L1 and L3 | L3: "which" not reached; "when" only partly; "where" only against the new RS arm. L1 is conditional on S_k not being ahead and on the cell not being capacity-limited by construction. S2 is caveated |
| 4. R3's gate was missing and underpowered | The gate is written out. δ comes from R3's own sizing at a planning sd of 0.20. An indeterminate outcome is added. A separate probe split is set for decisions. Cull = prune. "Rate-weighted" is dropped. The point estimate and bound are explicit |
| 5. Budgets and caps | R3's cap is shown to fit one host on a 4,096 × 40 cell. R1's cap is raised to 9 to cover the replay. R2 includes clean-train evaluation. Cap hit → no reading, the round used up, never a negative result |
| 6. The ordering followed 1 of 4 reviewers, undisclosed | §5 discloses it, along with my earlier option-A recommendation. R3 now waits for R1's regime answer |
| Nits | O6 corrected (`channel_starved`); O14 adds the 80.16% fixed-schedule arm; O4 cites the jitter decomposition; O8 has a verified script; O10 re-headlined; H5, H6 and H8's falsifiers fixed; H9 added (from §3); R1 terms defined and "not an artefact" softened; arm "H1" renamed "ONE"; the header no longer pre-claims the review |

**Not taken:** none. **Disagreements kept:** §6, items 6–7.

## 10. Revision note

This commit corrects interpretation and logic only, at the request relayed for John. No threshold
or owner decision gate changes, and no experiment is added.
- **R1:** "doesn't reach 0.05 → the regime is not hiding capacity" now reads either "below
  threshold: not supported at this precision" or "indeterminate: no conclusion".
- **R3:** "H − N not shown → the loop adds nothing" and "H against U not shown → L2 fails" now read
  as below-threshold, equivalence or "U ahead" evidence, kept apart from indeterminate intervals.
  The gate table gives each comparison its three outcomes. L1's condition now requires growing to
  be *shown* non-inferior.
- **The hypothesis table:**
  - H8's direction is corrected: growing matching installing on a natural host is *consistent with*
    H8, and installing still ahead contradicts it.
  - H2 now says flattening after epoch 10 is consistent with being step-limited at 10.
  - H1 and H4 now require equivalence at a stated precision.
  - H3's schedule clause moves to a note.
  - An inconclusive interval falsifies nothing.
