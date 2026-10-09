> **Design spike, 2026-10-09, input to [PDR-0057](../../decisions/0057-controller-training-pathway.md).** Written by a subagent (Opus) from the repository at main `6d38c81`. Scripts it cites under `scratchpad/` were not committed. Where a number here disagrees with a committed script, the committed script wins. In particular, S1's §0 headroom claim is superseded by `docs/results/2026-10-09-rung4-timing-horizon/exploratory/timing_headroom_null.py.txt`: single-future data cannot separate per-seed headroom from noise.

# S1: Statistical backbone for the controller pathway (atlas, gates, splits, sizing)

Design spike, 2026-10-09. Forward design only: no code and no repository changes. Author: counterfactual-statistician (spike S1).

**Status: draft.** The gate criteria below are programme-level. Under PDR-0053 they become binding only through an owner-signed DECIDE PDR. Per-study plans then operationalise them.

---

## 0. Headline: no *detectable* within-host headroom on the existing data

I re-read the archived per-run tables. On `under_normalized`, the per-seed choice of timing or blueprint shows **no headroom that can be told apart from noise**. Scripts are in the scratchpad (`s1_headroom.py`, `s1_debias.py`, `s1_what.py`).

**What these numbers can and cannot say.** No replicate-future data exists, so each per-seed residual mixes two things:
- (a) sensitivity to the future, i.e. divergence noise;
- (b) any *nonlinear* seed × timing heterogeneity.

The random-slope model de-biases only *linear* heterogeneity. The honest statement is:
- the in-sample oracle gain is fully explained by a noise-only model;
- under a linear-heterogeneity model, the implied true timing headroom is about 0.002 nats;
- nonlinear heterogeneity is confounded with the residual. Resolving it needs replicate futures, which Fleet A supplies.

| Decision dimension (data) | Naive in-sample oracle gain over the best fixed action | Expected under pure noise (zero true heterogeneity) | De-biased estimate |
|---|---:|---:|---:|
| **When**: T0/T1/T2/T3/T5, rung 4, n = 767 | **0.026** nats [0.022, 0.030] | **0.031** (pooled residual sd 0.049 per cell, iid) | **≈ 0.0016** (random-slope model, true slope sd 0.0106) |
| **What**: `norm` vs `conv_heavy` + no-op, rung 3, same 96 seeds | **0.014** | **≈ 0.015** (norm − conv_heavy: mean −0.042, sd 0.079) | not distinguishable from 0 |
| **Whether**: no-op best | 0.0% (timing set), 2.1% (what set) | n/a | ≈ 0 |

Three consequences follow.

1. **The naive "per-seed best action" is consistent with pure winner's curse.** The observed gain (0.026) is *below* the noise-only expectation (0.031). The iid-noise null is a slight over-estimate, because adjacent cells share a trajectory. Under the linear model, the true timing headroom is about 0.002 nats, roughly 10× below the instrument's ±0.02 resolution. Training a controller on argmin labels from these data would mostly teach it noise.
2. **On this host, "beats no-op" does almost no work.** With `norm`, the graft beats no growth on 94% of units in rung 3 (and in-sample no-op was never best in rung 4). With `conv_heavy` the figure is 69% of units, 2.1% of seeds with no-op best in-sample. C2's no-op comparator carries little information here.
3. **G0 is a multi-host test, not a timing test.** The only plausible source of decision-relevant variation is the host. `DESIGNED_WINNER` (`experiments/kernel_demo.py`: under_normalized→norm, channel_starved→conv_heavy, no_spatial_mix→attn, mild→conv_light) is a pre-existing hypothesis that the best action varies by pathology. Lifecycle-v2 cell C already shows a host where **no-op wins**: `mild` + `conv_light`, graft − no growth +0.029 [+0.003, +0.054]. `channel_starved` and `no_spatial_mix` have never been run on the bounded runner.

**Recommendation.** The first fleet (Fleet A) is a crossed 4-host × 5-action atlas: no-op plus 4 seed types, with replicate futures. It also carries the C1 scale-up arms and the deficit screen for the two unrun hosts. Do not spend anything more on timing-per-seed.

---

## 1. Fact-finding summary

**Read:**
- `docs/results/2026-10-09-graft-capture-v2.md` and its per-unit `training.jsonl`
- `docs/results/2026-10-09-rung4-timing-horizon.md`, with `tables/per-run.jsonl.gz` (fields `cell, seed, late_ce{no_growth,scheduled,static}, status, replay_digest, prefix_digest`), `tables/per-epoch.jsonl.gz` and `exploratory/`
- `docs/results/2026-10-08-lifecycle-v2-validation.md` (cell C, `mild`/`conv_light`), `positive-control-v2.md`, `bounded-screen-v1.md`
- PDR-0050, 0052, 0053, 0054, 0055; `docs/product/vision.md`; `docs/product/current-state.md`
- `docs/design/07-counterfactual-engine.md` (four data roles, no-op anchoring, unit = base trajectory)
- ADR-0011 (anchor corpus, authority-partitioned labels)

**Harness facts that bind the design:**
- `experiments/bounded_data.py::RunSpec`
  - Fields: `seed`, `data_seed` (fixed 20261004), `graft_epoch`, `epochs`, `host ∈ PATHOLOGIES`, `seed_type ∈ SEED_NAMES`.
  - **There is no future-replicate field and no width multiplier.**
- `experiments/bounded_comparison.py::draw_future`
  - The future derives from `derive(spec.seed, "common-future")`, with one generator per epoch, so it is prefix-stable.
  - Adding a replicate index for epochs ≥ the decision epoch is therefore a small change that keeps replicate 0 bitwise.
- `experiments/kernel_demo.py::Host`
  - **There is one slot site** (after `stage2`, [B,64,8,8]). "Where" does not exist yet.
  - Widths are hard-coded at (24, 64, 80).
  - `build_seed(name, channels, …)` already accepts arbitrary channels.
- **Telemetry in the bounded runner is thin.** Per epoch it logs only `train_ce`, `dev{ce,accuracy}` and `gradient_norm_max{host,seed_body,seed_gain}`.
  - The kernel's 20-dimensional `TelemetryRecord` (per-stage grad norm mean/var, activation saturation, weight norm, per-class accuracy sd, confusion entropy) is **not computed by the bounded runner**.
  - A telemetry-driven controller needs it ported.
- **The dev set does double duty.** The 5,000-example dev set is both the endpoint (late dev CE) and the only source of validation-style telemetry. That is a feature/endpoint leakage path (pitfall P5).
- **Cost and throughput.**
  - About 0.66 s per epoch-arm on GPU (from `wall_s`).
  - About 230 three-arm 10-epoch runs per hour, i.e. **about 700 arm-runs/h, or about 7,000 arm-epochs/h** fleet-wide.
  - Rung 4: 4,608 runs in 17.3 h, consistent.
- **Noise numbers used below.**
  - Single graft − no-op contrast sd: 0.05–0.09 (rung 4 per cell: T0 0.090, T5 0.049).
  - Action − action on the same seed: sd 0.079 (`norm` − `conv_heavy`) and 0.089 (T0 − T3).
  - Static − graft: sd 0.128.
  - Horizon contrast at H20: sd 0.393, 1.7× its pilot UCL, because static degrades late.

**Not found or assumed:**
- **No external cost model.** δ values below are ladder conventions (0.02 nats, about 14% of static's gain, PDR-0055) plus a cost exchange rate derived inside Fleet A (§4). This is flagged in the gaps.
- **No replicate-future data exists**, so label reliability is unmeasured.
- **No data on `channel_starved` or `no_spatial_mix`** on the bounded runner.

---

## 2. The counterfactual atlas

### 2.1 Unit hierarchy

```
host h  (fixed set of 4 in Phases 1–2; draws from a parametric family in Phase 3)
 └─ seed s  (host init + common future + seed-body init; crossed with hosts: the same seed integer on every host)
     └─ decision point d  (snapshot after epoch d on the no-op trunk)
         └─ action a ∈ {no-op} ∪ {blueprint × site}
             └─ future replicate r ∈ {0, 1}  (post-d data order and augmentation; r = 0 is bitwise-identical to today's runner)
```

**Independent unit, by phase:**
- **Phases 1–2 (fixed hosts):** the seed.
  - Hosts are crossed with seeds and share the seed's future, so the 4 host contexts of a seed form one cluster.
  - Claims are conditional on the 4 named hosts (fixed effects).
  - *An additional independent observation requires a new seed integer run on all 4 hosts.*
- **Phase 3 (C3):** the host draw.
  - Seeds nest in hosts. Aggregate each host to one number, then test across hosts.
  - *An additional independent observation requires a new host drawn from the family generator.*

**Confidence:** High. This follows from the harness's seed derivation (`derive(spec.seed, …)` drives init and future) and from INV-32.
**Risk if wrong:** counting host × seed contexts as independent in Phase 1 understates the CI by about √(1 + 3·ICC). The shared future makes the ICC non-trivial.

### 2.2 Decision space for v1, chosen to create headroom

| Dimension | v1 (Fleet A, fixed hosts) | v2 (host family, Phase 3) | Why |
|---|---|---|---|
| Whether | no-op always present | same | Mandatory, and it carries real value on `mild` |
| What | 4 seed types (`norm`, `attn`, `conv_light`, `conv_heavy`) | same | The designed-winner map is the headroom hypothesis |
| Where | 1 site (the only one) | 2 sites (after stage 1, after stage 2) and pathology stage ∈ {1, 2} in the generator | "Where" only has headroom when the deficit's location varies |
| When | **one decision point, d = 1** | d = 1; add d = 4 only if G2 on the family shows per-host timing headroom | Rung 4: timing heterogeneity ≈ 0.002 nats. d = 1 rather than 0 so the controller sees one epoch of telemetry. It costs about 0.016 nats against T0, paid equally by every policy |
| Host | 4 pathologies | parametric family (§5) | The only lever with plausible heterogeneity |

With one decision point, the offline evaluation in G3 is **exact**: every action's outcome is measured per context, so no off-policy estimator is needed. Closed loop (G4) is then bitwise-identical to the atlas branch the frozen controller picks. G4's added information is fresh report seeds, a live telemetry pipeline, and a leakage check. It is **not** path-dependence. Sequential decisions, where ADR-0011's path-conditional labels matter, enter only in v2, and only if G2 on the family shows timing headroom.

**Confidence:** Medium-high.
**Risk if wrong:** if the 4 hosts share one best action (for example `norm` wins everywhere), G2 fails cheaply and the pathway moves to the family generator with its cost known.

### 2.3 Labels

- **Per-context, per-action effect:**
  τ_r(x, a) = CE_late(a, r) − CE_late(no-op, r) + λ·Δcost(a)
  - CE_late is the mean dev CE over the last 3 epochs on the **endpoint-dev** split (§3.3).
  - The no-op scores exactly 0.
  - Divergence scores a declared penalty (§4).
- **The controller is trained on all K effects (multi-output regression), never on argmin labels.** Argmin of noisy single-future effects is the winner's curse that §0 measured.
- **Authority routing (ADR-0011, INV-09).** Per-action labels may train a research composite in the bounded ladder. If this pathway reaches HLD contracts:
  - Aurelia may receive only the marginalised slice: min over actions minus no-op, class-blind (whether/when);
  - "what/where" belongs to Momir conditioning and Isperia selection.

  Every gate therefore reports **whether-regret separately** from total regret, so the Aurelia-legal part is measured from day one.

### 2.4 Measuring headroom honestly

Definitions:
- a* = best fixed action, the argmin over actions of the mean of τ.
- π°(x) = per-context oracle.
- H = E_x[τ(x, a*) − τ(x, π°(x))] ≥ 0.

**Estimator (pre-register this exact procedure):**
1. **Cross-fit the fixed policy over seeds.** Split Fleet A's G2 seeds into two folds by hash. Choose a* on fold A and evaluate on fold B, then swap.
2. **Cross-fit the per-context argmin over futures.** π̂₁(x) = argmin over a of τ₀(x, a), evaluated on replicate 1, and the reverse:
   Ĥ_cf = ½ Σ_{r≠r'} mean_x[τ_r'(x, a*) − τ_r'(x, π̂_r(x))]
   This is unbiased for the headroom achievable by an oracle that sees one replicate. That makes it a **conservative lower bound** on true H. Selection on a noisy replicate attenuates it toward 0 when ρ is modest.
   - **Attenuation curve.** Audit seeds run **R = 4** futures for no-op and the 4 grafts. Compute Ĥ_cf selecting on the mean of k ∈ {1, 2, 3} replicates and scoring on a held-out one, and report the curve against k. A rising curve means attenuation is material.
   - **Model-based upper bound Ĥ_mb.** For each action a ≠ a*, the predictable per-context contrast c(x, a) = τ(x, a) − τ(x, a*) has across-context mean m_a and predictable variance σ²_a = Cov(c₀, c₁), the cross-replicate covariance. Then Ĥ_mb = Σ_a E[max(0, −Z_a)] with Z_a ~ N(m_a, σ²_a). That is a union bound, so it is an upper bound on the oracle gain under normality.
   - **The asymmetry is deliberate.** Ĥ_cf is safe for `go` and unsafe for `no_headroom`. A stop therefore needs *both* estimators below δ_H (§5, G2).
3. **Report the bracket.** Show [Ĥ_cf, Ĥ_naive] and the noise-only null (the parametric resample of §0). Ĥ_naive is an upper bound and is never used for a decision.
4. **Report label reliability.** For each action-versus-a* contrast and each host: ρ = corr(τ₀ − τ₀(a*), τ₁ − τ₁(a*)) across seeds. ρ caps the R² any telemetry predictor can reach. Below 0.3, the per-context signal is mostly divergence noise.
5. **Decompose.** H = H_between-host + H_within-host:
   - H_between-host: the oracle restricted to a host lookup table (one action per host), cross-fitted;
   - H_within-host: the remainder.

   If at least 80% of the headroom is between-host, C2 is labelled **"telemetry identifies the pathology"**. That is a legitimate but weaker claim than per-seed adaptation, and it must be reported under that name.
6. **CI.** Seed-cluster bootstrap (resample seeds with all 4 hosts and both replicates), 10,000 resamples.

**Go/no-go for "there is something to learn" (G2):** the lower 97.5% bound of Ĥ_cf must be **≥ δ_H = 0.025 nats** (cost-charged).
- **Derivation, kept consistent with the confirmatory gate.** G4's MDE at n = 192 report seeds is about 0.0125 (§6). A realistic controller recovers about half the oracle headroom. So the headroom has to be at least 2 × 0.0125. A smaller δ_H would allow a G2 pass that no controller could convert into a G4 pass.

---

## 3. Splits

### 3.1 Roles: fixed-host phase (Fleet A, then the G4 fleet)

**Assignment.** `role = H(sha256("simic-s1-roles-v1" ‖ seed)) mod 100`, with whole seeds assigned: all 4 hosts, all branches, both replicates.

| Role | Weight | Fleet A seeds (of 192) | Decides | Never touches |
|---|---:|---:|---|---|
| support | 50 | ≈ 96 | controller fitting; λ fit (scale-up slope) | screen, audit, report |
| screen | 25 | ≈ 48 | model class and hyperparameters; abstention threshold; **choice of the best fixed policy a\*** (on support + screen) | audit, report |
| audit | 25 | ≈ 48 | verifies the selected controller and a* on untouched seeds; the G2 headroom estimate; horizon-stability subsample | — |
| report | — | **a separate fresh fleet** (G4, 192 seeds) | the confirmatory C2 claim only | everything above |

**Seed hygiene:**
- Seeds 1001–9356 are seen. They may serve as prototype or support data only, never screen, audit or report.
- Declare fresh ranges now:
  - Fleet A: 10001–10192;
  - G4 report: 11001–11192;
  - host family: 12001+.
- Dry-run seeds come from a separate range (9901–9910).

### 3.2 Roles: host-family phase (C3)

- **Hosts are the unit.** Role assignment is by `sha256("simic-s1-hosts-v1" ‖ canonical host-config hash)`:
  - support 64 hosts;
  - screen 16;
  - audit 16;
  - report 32.
- Seeds within a host are fresh per host.
- **No host config appears in two roles.** The four named pathologies are excluded from the report role.
- **How many hosts C3 needs (§6.3):** at least 24 report hosts for any confirmatory statement; 32 is recommended. **With the 4 named pathologies, C3 is not testable.** Leave-one-pathology-out (4 folds) is a diagnostic with no CI, reported as "extrapolation, descriptive".
- **Two transfer tiers:**
  - interpolation: report hosts drawn from the same generator distribution. This tier is confirmatory.
  - extrapolation: a held-out pathology class or severity range. This tier is descriptive only.

### 3.3 Leakage walls to build

1. **Split the dev set** by stable example hash into a probe split (1,000, for telemetry) and an endpoint-dev split (4,000, for the late-CE label). The controller's features never see endpoint examples.
2. **Freeze before the next role.** a\*, λ, the divergence penalty and the abstention threshold are each frozen before audit data is read. Each fitted quantity's provenance (role and seeds) is recorded.
3. **One fixed data sample.** `data_seed` is the same 4,096-example sample everywhere. The C3 claim is transfer across hosts on one data sample, never across data. Outer/test data stays owner-gated.

---

## 4. Endpoints, cost charge, failures, horizon

- **Primary endpoint.** Late dev CE: mean over the last 3 epochs, endpoint-dev split, H = 10.
- **Cost charge (λ).** λ is the slope of uniform scale-up's no-op CE against log₂(param-steps multiplier) over m ∈ [1.0, 1.25], fitted on **support seeds** of Fleet A by a pre-registered deterministic procedure.
  - Read: "an intervention is charged what the same compute would have bought by scaling the host uniformly".
  - C1 and C2 then share one currency.
  - Δcost = log₂(param-steps of arm / param-steps of no-op). Param-steps are deterministic, read from the run records.
  - Wall time and parameter count are reported but not charged.
  - λ is frozen before any graft outcome on screen or audit seeds is read.
- **Failures.**
  - A diverged branch scores CE = ln 10 = 2.303 (chance level). It is never dropped.
  - Sensitivity: the rollback-equivalent penalty (CE of the no-op branch plus the wasted-compute charge). The report states whether any reading moves.
  - **Tail gate, lexicographic and separate:** the controller's divergence rate is non-inferior to a\*'s. The upper 95% bound of the paired difference must be ≤ +1.0 percentage point.
- **Robustness (the heavy-tail lesson from H20).** Every primary is an **intersection-union test**: the paired mean *and* a robust companion must both clear. This costs no α and protects against a tail-driven pass like rung 4's horizon contrast.
  - **Choosing the companion.** For controller − a\* (G3, G4), the difference is exactly 0 wherever the two policies agree. Trimming 10% per side would remove nearly all the discordant mass and leave mostly zeros; the IUT could then never pass.
  - **So the companion is computed on discordant contexts only**, where π̂(x) ≠ a\*: a Wilcoxon signed-rank test on the per-seed sum of discordant differences, with seeds that have no discordant context excluded from this companion only.
  - G1 and G5 (host-level means) use the 10%-trimmed mean.
- **Horizon.**
  - H = 10 is primary.
  - Audit seeds also run the 5 actions at H = 20, at R = 0, with static excluded.
  - Pre-registered stability check: agreement of argmin(τ) between H10 and H20 per context. Below 0.7, every C2 claim carries a "10-epoch-myopic labels" caveat.
  - Static's late degradation means it is a ceiling only at H = 10.

---

## 5. Gate structure

There are **two separate claim families**:
- **C1 (G1)** is its own family: Bonferroni over 2 hosts, fixed-sequence over m within each host.
- **C2/C3 (G2 → G3 → G4 → G5)** is a fixed sequence. Each gate runs at one-sided α = 0.025 on a single primary, which is an IUT internally. A gate opens only if its predecessor passed, so the familywise error rate stays at 0.025 along that chain without splitting α.

The C2 chain does **not** depend on G1: a `mild` failure in G1 does not close it. No interim looks except in G5.

### G0: Apparatus (no claim)

**Build:**
- a `future_replicate` field (epochs ≥ d draw from `derive(seed, "common-future", r)`; r = 0 bitwise-identical to now);
- a decision snapshot fan (or deterministic replay) at d;
- a `width_mult` on Host for the no-op scale-up arms;
- the 20-dimensional per-stage telemetry record computed on the probe split (port from `kernel_demo.build_record`);
- the dev probe/endpoint split.

**BatchNorm hazard.** Three of the four hosts use BatchNorm. Per-stage probe forwards for telemetry must run in eval mode, or save and restore running buffers, as the seed witness already does. Otherwise telemetry silently changes training. The on/off digest check below catches this; this note names the likely cause.

**Pass criteria:**
- r = 0 reproduces 3 archived rung-4 T-cell records bitwise (seed, host and no-op digests);
- the no-op branch from the snapshot equals the trunk continuation bitwise;
- turning telemetry on or off leaves training digests unchanged (Tamiyo-isolation analogue);
- a 3-seed real-configuration dry run of Fleet A completes and its analysis runs end to end.

**Kill:** any replay mismatch. Fix it; no science runs until then.
**Cost:** about 0.5 h.

### G1: C1 efficiency on fixed hosts (from Fleet A)

- **Comparator.** Uniform scale-up: no-op arms at m ∈ {1.1, 1.25, 1.5, 2.0} × params, trained from step 0 on the same future. Static is a **descriptive ceiling only**, never the comparator.
- **Contrast.** The host's **pre-declared** blueprint, `DESIGNED_WINNER[host]`, grafted at d = 1, minus scale-up(m); late CE.
  - Choosing the blueprint by data would give the graft about 1 SE of selection edge, with 4 candidates.
  - `mild` → `conv_light` is the honest adverse case: in lifecycle-v2 cell C it hurt, +0.029.
- **Primary and test.**
  - Non-inferiority at margin 0.02, in a fixed-sequence step-down over m = 1.25 → 1.5 → 2.0.
  - Report the largest m passed, m_eq, as "the graft at about 1.001–1.3× param-steps matches uniform scale-up at m_eq×".
- **Co-primaries.** Two, Bonferroni (one-sided α = 0.0125 each):
  - `under_normalized`, where the graft is designed, as an existence test;
  - `mild`, the non-designed host, as the honest test.
  - `channel_starved` and `no_spatial_mix` are descriptive.
- **Unit.** Seed (n = 192). The pairing is weaker here because width changes the init; sizing uses sd ≈ 0.13 (from static − graft).
- **Kill or narrow:**
  - `under_normalized` fails at m = 1.25: C1 is refuted at bounded scale in its most favourable case. This goes to the owner.
  - `mild` fails: C1 is pathology-specific. That is the expected result; the claim is narrowed.

### G2: Headroom (from Fleet A; screen seeds R = 2, audit seeds R = 4)

- **Primary.** Ĥ_cf (§2.4). Always reported with the bracket, the attenuation curve, Ĥ_mb, ρ and the between/within decomposition.
- **Readings (asymmetric on purpose):**
  - `go` if LCB(Ĥ_cf) ≥ 0.025. A lower bound clearing δ_H is safe evidence.
  - `no_headroom` only if UCB(Ĥ_cf) < 0.025 **and** UCB(Ĥ_mb) < 0.025. Ĥ_cf alone is attenuated and must not stop the ladder.
  - `inconclusive` otherwise. This leads to more audit replicates, or the host family, by owner decision.
- **Kill.**
  - `no_headroom` on the fixed hosts means stopping C2 on this host set. One route remains: build the host family and rerun G2 there (G2′, same rule).
  - `no_headroom` again means the ladder stops at rung 5 as a clean negative ("measured counterfactuals show no decision-relevant variation in this action space").
- **Sizing.** The per-seed sd of h_x averaged over 4 hosts is probably 0.04–0.06. At about 96 seeds the SE is ≈ 0.005, ample for the decision.

### G3: Offline learnability (C2, within distribution)

- **Training.** The controller is fit on support seeds. Features: probe-split telemetry at d = 1 from the no-op prefix, identical across actions. a\* is host-blind. Targets: the K cost-charged effects. Model classes are limited to ridge, small GBM and kNN (≤ 3 candidates).
- **Selection.** Model class, the abstention threshold, and a\* are selected on screen seeds.
- **Primary (audit seeds).** Δ = mean_x[τ̄(x, a\*) − τ̄(x, π̂(x))], with τ̄ the average over the audit seeds' 4 replicates.
  - Superiority Δ > 0, one-sided α = 0.025, IUT with the discordant-only signed-rank companion (§4).
  - Also required: the controller's utility versus no-op has LCB > 0.
  - The tail gate must pass.
- **Secondaries (descriptive).**
  - Fraction of Ĥ_cf captured.
  - Whether-regret separately.
  - False-intervention rate (grew when no-op was better by more than 0.01) and miss rate.
  - The between/within split of Δ.
- **Kill and diagnose.** If Δ's LCB ≤ 0:
  - with ρ ≥ 0.3, the features are insufficient (revisit telemetry once);
  - with ρ < 0.3, the labels are noise. Stop.

  At most one revision cycle, and it is spent on support/screen data only.

### G4: Closed loop (C2, confirmatory)

- **Fleet.** Fresh report seeds 11001–11192 on all 4 hosts. The frozen controller runs live at d = 1.
- **Arms per host-seed:**
  - controller;
  - a\* (frozen);
  - no-op;
  - uniform-random policy (descriptive);
  - every graft at R = 0 (descriptive oracle-regret only, never fitted on).
- **Primary.** Controller − a\* on cost-charged late CE.
  - a\* is **host-blind**: one action for every context, frozen on support + screen.
  - A per-host lookup table is the between-host oracle reported in G2, not the comparator.
  - Paired by seed, averaged over the 4 hosts.
  - The difference is exactly 0 on contexts where they agree.
  - One-sided superiority at α = 0.025, IUT with the discordant-only signed-rank companion (§4).
  - Co-conditions: versus no-op LCB > 0; the tail gate.
- **Replay check.** On every context, the live controller's branch must equal the matching atlas branch bitwise. A mismatch is `instrument_failure`.
- **Readings:**
  - `c2_supported`;
  - `c2_not_supported` (upper bound < 0.0125);
  - `inconclusive`.

  `c2_supported` with ≥ 80% between-host headroom is published as "telemetry identifies the pathology".

### G5: Transfer (C3), with C1 on held-out hosts

- **Prerequisite.** The parametric host family. Generator parameters:
  - pathology class;
  - pathology stage ∈ {1, 2};
  - severity (norm gain ∈ [1.2, 2.5] without BN, starvation width ∈ [12, 48], spatial kernel ∈ {1, 3});
  - base width multiplier ∈ [0.75, 1.25].

  The slot is available at 2 sites, giving 9 actions. The generator distribution and its seed are frozen before any family host is trained.
- **Atlas on the family:**
  - support hosts: R = 1;
  - screen and audit hosts: R = 2;
  - G2′ is re-run on screen + audit hosts before any controller is fit.
- **Primary.** On 32 report hosts × 16 fresh seeds, take each host's mean of (controller − a\*_family), aggregate to one number per host, and test across hosts.
  - One-sided t at α = 0.025, IUT with the trimmed mean over hosts, plus the tail gate.
  - **One interim** at 16 report hosts: O'Brien–Fleming efficacy z ≥ 2.96, and a non-binding futility stop if conditional power < 10%.
- **Secondaries:**
  - the transfer ratio Δ_report-hosts / Δ_audit-hosts;
  - C1 on held-out hosts: the share of report hosts where the controller's chosen injection is non-inferior to 1.25× uniform scale-up, using 2 scale-up arms per report host-seed;
  - extrapolation folds (descriptive).
- **Kill.** Failure means C3 is not supported. Publish C2 as within-distribution only.

---

## 6. Sizing and compute

### 6.1 G4 MDE (controller versus a\*, per seed averaged over 4 hosts)

- **Variance model.** sd_d ≈ √p_dis · sd(action-difference) / √(effective hosts).
  - sd(action-difference) ≈ 0.09 per context.
  - Assume hosts are partly correlated through the shared future: effective hosts ≈ 2.5.
- **MDE.** One-sided α = 0.025, power 0.8: MDE = 2.80 · sd_d / √n.

| p_dis (contexts where the controller ≠ a\*) | sd_d | n = 96 | n = 192 | n = 384 |
|---|---:|---:|---:|---:|
| 0.25 | 0.028 | 0.0081 | 0.0057 | 0.0040 |
| 0.50 | 0.040 | 0.0115 | 0.0081 | 0.0057 |
| 0.75 | 0.049 | 0.0141 | 0.0100 | 0.0071 |

- **Tail and UCL inflation.** Inflate sd by ×1.5. Rung 4's horizon sd came in 1.7× its pilot UCL, and divergence penalties fatten the tails.
- **Result.** At p_dis = 0.5, n = 192 gives an **MDE ≈ 0.012**. That is the source of G2's δ_H = 2 × 0.0125.
- **Re-sizing.** Replace the assumed 0.09 with Fleet A's audit-seed sd, taken at its 80% UCL, before the G4 fleet is sized. This is a blinded re-size: it uses audit spread only, never report data.

### 6.2 G1 (C1)

- sd ≈ 0.13, with weak pairing.
- At n = 192 and one-sided α = 0.0125, the half-width is ≈ 0.021. Non-inferiority at margin 0.02 is established when the true graft advantage over scale-up is at least about 0.02.
- On `under_normalized`, T0 captured 0.86 of static's 0.133 gain (≈ 0.115 nats). The test will be decided by the size of scale-up's gain, not by power.
- On `mild`, expect a null-to-adverse result. 192 seeds bound it to about ±0.02.

### 6.3 G5 (host count)

- **Variance model.** Host-level sd σ_h = √(τ_h² + σ_seed²/m), with τ_h = between-host heterogeneity of the controller advantage (assumed 0.025), σ_seed = 0.064 and m = 16, giving σ_h ≈ 0.030.

| Report hosts G | 16 | 24 | **32** | 48 |
|---|---:|---:|---:|---:|
| MDE (point σ_h) | 0.021 | 0.017 | **0.015** | 0.012 |
| MDE (σ_h × 1.3) | 0.027 | 0.022 | **0.019** | 0.016 |

- **Recommendation.** 32 report hosts. Below 24, a C3 null is uninformative. τ_h is a guess; G2′ on screen and audit hosts measures it before the report fleet is sized.

### 6.4 Compute (≈ 700 arm-runs/h; a 10-epoch arm ≈ 1 unit; scale-up arms weighted by m)

| Fleet | Contents | Arm-runs | Hours |
|---|---|---:|---:|
| G0 | builds, bitwise checks, 3-seed dry run | ~200 | 0.5 |
| **Fleet A** (G1 + G2 + G3) | 192 seeds × 4 hosts × [no-op + 4 grafts at R = 1 (support), 2 (screen), 4 (audit); 4 static; 4 scale-ups weighted ≈ 5.9] | ≈ 15,200 | **≈ 22** |
| Fleet A, H20 subsample | 48 audit seeds × 4 hosts × 5 actions × 2 | ≈ 1,900 | ≈ 2.7 |
| G4 | 192 seeds × 4 hosts × (controller, a\*, no-op, random, 4 grafts) ≈ 6 unique runs (controller and a\* coincide with grafts) | ≈ 4,600 | ≈ 6.6 |
| Host family G2′ + G3 + G5 | 64 support hosts × 16 seeds × 9 actions; 32 screen/audit hosts × 16 × 9 × 2; 32 report hosts × 16 × (9 + 2 scale-ups) | ≈ 24,500 | ≈ 35 |
| **Total** | | ≈ 46,400 | **≈ 67 h** (about 3 days of nyx) |

Compute does not bind. Host engineering (G0 telemetry port; the family generator with 2 sites) and review time do.

---

## 7. `preregistration.yaml` (Fleet A: G1 + G2 primaries; G3 is pre-registered as procedure)

```yaml
study: s1-fleet-a-atlas
status: draft            # binding only after owner-signed DECIDE PDR (programme gates) + per-study PDR
question: >
  On four fixed bounded hosts, (G1) is a graft at ~1x params non-inferior to uniform scale-up,
  and (G2) does the per-context best action differ from the best fixed action by enough to learn?
unit:
  definition: seed integer, crossed with the 4 hosts (shared common future)
  id_column: seed
  repeated_measures: [host, action, future_replicate, epoch]
  rationale: "an additional independent observation requires a new seed run on all 4 hosts"
hosts: [under_normalized, channel_starved, no_spatial_mix, mild]
seeds: {range: [10001, 10192], dry_run: [9901, 9903]}
roles:
  method: sha256("simic-s1-roles-v1" || seed) mod 100
  weights: {support: 50, screen: 25, audit: 25}
  consumption_asserts:
    - lambda fit reads support only
    - a_star chosen on support+screen only
    - G2 headroom and G3 primary read screen+audit (G2) / audit (G3) only
decision_point: {epoch: 1, trunk: no_growth}
actions: [noop, norm, attn, conv_light, conv_heavy]       # single site
future_replicates: {support: [0], screen: [0, 1], audit: [0, 1, 2, 3]}
extra_arms:
  static: [norm, attn, conv_light, conv_heavy]            # descriptive ceiling + deficit screen
  uniform_scaleup_m: [1.1, 1.25, 1.5, 2.0]                # no-op host, width scaled to params x m
matching_contract:
  same_host_init_across_actions: yes
  same_future_prefix_epochs_lt_d: yes (bitwise)
  same_future_post_d_within_replicate: yes
  rng_substreams: derive(seed, label[, r]) hash-derived; no additive seeding
  noop_is_genuine: noop branch == trunk continuation bitwise (asserted)
  scaleup_init_matched: NO (width changes init) -> G1 sized on unpaired-init sd 0.13
  telemetry_does_not_perturb: asserted by on/off digest equality
endpoint:
  primary: late dev CE, mean of last 3 epochs, endpoint-dev split (4000 ex), H=10
  cost_charge: lambda * log2(param_steps_arm / param_steps_noop); lambda = OLS slope of noop CE
               on log2(m) over m in {1.0,1.1,1.25}, support seeds, frozen before screen/audit read
  failure_penalty: {primary: 2.302585, sensitivity: rollback_equivalent}
  robust_companion:   # IUT: mean AND companion must both clear
    G1: 10%-trimmed mean
    G3_G4: Wilcoxon signed-rank on per-seed sums over DISCORDANT contexts only (pi_hat != a_star)
    G5: 10%-trimmed mean of host means
G1_c1:
  contrast: graft(DESIGNED_WINNER[host], d=1) - uniform_scaleup(m)   # pre-declared, no selection
  test: non-inferiority, margin 0.02, fixed-sequence m = 1.25 -> 1.5 -> 2.0
  co_primaries: {under_normalized: 0.0125, mild: 0.0125}   # one-sided alpha, Bonferroni
  descriptive: [channel_starved, no_spatial_mix, static ceiling, params, wall]
G2_headroom:
  estimator: H_cf, cross-fit a_star over 2 seed folds and argmin over futures (r<->r')
  ci: seed-cluster bootstrap, 10000, one-sided 97.5% lower bound
  go_if: LCB >= 0.025
  no_headroom_if: UCB(H_cf) < 0.025 AND UCB(H_mb) < 0.025   # H_mb: union-bound model estimate from cross-replicate covariance
  attenuation_curve: H_cf selecting on mean of k in {1,2,3} audit replicates
  report_always: [H_naive, noise-null H, rho per host x contrast, between/within decomposition,
                  H10-vs-H20 argmin agreement on audit subsample]
G3_offline:
  status: procedure fixed here; numbers frozen at audit unblinding
  models: [ridge, gbm_small, knn]  # max 3
  targets: K cost-charged effects (multi-output regression), never argmin labels
  primary: Delta = mean[tau_bar(a_star) - tau_bar(pi_hat)] on audit seeds, one-sided 0.025, IUT
  a_star: host-blind single action, frozen on support+screen
  co_conditions: [controller vs noop LCB > 0, divergence-rate NI upper95 <= +1.0pp]
interim_looks: none
amendments: any change after launch is an amendment; analysis refuses mismatched plan hash
```

---

## 8. Pitfalls specific to this programme

| # | Pitfall | Mechanism in Simic's data | Guard |
|---|---|---|---|
| P1 | **Oracle-static confusion** | Static is the same module at the known site from step 0. It is a ceiling, and an action no growth controller can take after d. Rung 3/4 "graft vs static" framing invites reading static as the comparator | C1 comparator = uniform scale-up; C2 comparator = frozen a\*; static is descriptive only |
| P2 | **Designed-winner circularity** | `DESIGNED_WINNER` builds each host's deficit for one blueprint. C1 on `under_normalized` and between-host C2 headroom are partly true by construction | C1 co-primary on `mild`; between/within decomposition; family generator with severity and stage |
| P3 | **Heavy tails** | Static degrades late at H20 (117/756 late risers, 12 divergences); horizon sd 0.393 vs a sized 0.230 | IUT with a robust companion (discordant-only signed-rank for controller − a\*); sd ×1.5 in sizing; static never in the action set; ln 10 penalty with sensitivity |
| P4 | **Winner's curse in argmin labels** | §0: naive 0.026 vs noise-null 0.031 vs true ≈ 0.002 | Multi-output regression targets; future-replicate cross-fitting; a\* fitted off the report seeds |
| P5 | **Feature/endpoint leakage via dev** | Telemetry val_loss and the endpoint share the 5,000 dev examples | Probe/endpoint dev split by example hash |
| P6 | **Seed leakage across roles** | Crossed hosts share one seed's future; seeds 1001–9356 already seen | Whole-seed role hashing; fresh declared ranges; seen seeds support-only |
| P7 | **Best-fixed and threshold fitted on report** | Gives a\* its own winner's-curse edge, or the controller one | a\* and the threshold frozen on support/screen before audit |
| P8 | **Path-conditional labels** | Labels at a later d are conditional on no-op earlier (ADR-0011) | v1 has a single decision; sequential decisions only if G2′ finds timing headroom |
| P9 | **Cost confound** | `conv_heavy` costs +30% param-steps, `norm` +0.06% | λ from the scale-up slope, frozen before graft outcomes on screen/audit |
| P10 | **One data sample** | `data_seed` is fixed everywhere | C3 is worded "across hosts, one data sample" |
| P11 | **Authority leak** | Per-action labels taught to a whether/when authority (INV-09) | Whether-regret reported separately; composite controller labelled research-only |

---

## 9. Confidence assessment

| Decision | Confidence | Basis |
|---|---|---|
| No detectable within-host timing/what headroom on `under_normalized` | **Medium** for timing (n = 767; noise-only null and random-slope model agree, but nonlinear heterogeneity is confounded without replicate futures); **Medium-low** for what (n = 96, noise-only null only) | Computed from archived tables |
| Unit = seed (crossed), host for C3 | High | Read from the harness's seed derivation; standard |
| Single decision point d = 1 | Medium | Rung-4 timing data; the cost of telemetry delay is measured (0.016/epoch) |
| δ_H = 0.025 and the G4 MDE | Medium-low | sd_action-diff (0.09) is measured; p_dis and the host correlation (effective hosts 2.5) are assumed |
| λ from the scale-up slope | Medium | Principled, but the slope may be nonlinear or noisy at small m (weak pairing) |
| Host count 32 for C3 | Low-medium | τ_h is a guess; G2′ measures it |
| Compute ≈ 67 h | Medium | Throughput measured; branch-fan savings and telemetry overhead not measured |

## 10. Risk assessment

- **Locked at Fleet A launch:**
  - unit and crossing;
  - the role hash and salt;
  - the dev split;
  - the endpoint and penalty;
  - the λ procedure;
  - the G2 rule.

  Getting any of these wrong costs a new fleet (about 22 h), not the programme.
- **Reversible:**
  - the model class (within screen);
  - G4's n (blinded re-size from audit spread);
  - the G5 host count (re-sized from G2′).
- **Most consequential risks:**
  1. All 4 hosts share a best action. G2 fails, and the programme's cost moves to host engineering.
  2. Label reliability ρ is low, so the per-context signal is divergence noise. G3 fails even with headroom.
  3. The scale-up slope is too flat to price cost. λ ≈ 0, and C2 then ranks expensive blueprints too kindly. Report the uncharged ranking beside it.

## 11. Information gaps

- **Label reliability ρ.** No replicate-future data exists. Fleet A's audit seeds measure it; until then δ_H's achievability is unknown.
- **`channel_starved` and `no_spatial_mix`.** Their deficits and divergence rates on the bounded runner are unknown. Fleet A doubles as their deficit screen. A static divergence rate above 10% on either should trigger a host-instability policy before G2 is read.
- **Uniform scale-up's CE-vs-cost curve.** It has never been measured. It sets λ and C1.
- **The cost model.** None exists outside ladder conventions. An owner-stated exchange rate (nats per % compute) would replace the derived λ.
- **The per-stage telemetry port.** Its overhead and its determinism under the GPU profile are unmeasured.
- **p_dis and the cross-host correlation of controller advantage.** Both drive G4's n and come from Fleet A audit data.

## 12. Caveats: what this design cannot establish even if executed perfectly

- **Bounded scale only.** 10-epoch, 4,096-example, one data sample, one CNN family. Esper-lite's regime was about 15× longer. Nothing transfers to scale by this design.
- **Hand-authored blueprints.** The action set is 4 human-authored seed types. Passing every gate supports "a controller selects among reference seeds from telemetry". It does not support "generated structure" (the first claim's core), which needs Momir.
- **A between-host pass is a weaker claim.** If C2 passes on between-host headroom, the claim is pathology recognition from telemetry, not structural taste within a host.
- **C3 is interpolation only.** It covers the declared generator distribution. Extrapolation to new pathology classes is descriptive.
- **One decision per run.** Sequential growth (multi-slot, accumulation, retirement) is untested in v1.

### Where the critic should press

1. The G4 variance model: effective hosts 2.5, p_dis 0.5, the ×1.5 tail factor.
2. Whether the λ-from-scale-up charge is identifiable given weak init pairing at small m.
3. Whether d = 1 telemetry (one epoch, probe split) is rich enough. If not, G3 fails for a fixable reason and the single revision cycle is spent.
