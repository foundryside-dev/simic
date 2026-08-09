<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: 00-INDEX.md -->
[← HLD index](00-INDEX.md)

<!-- hld: source: v4.1 monolith lines 2397–2529 -->
## 14. Counterfactual Execution, QA and Adjudication

### 14.1 Candidate pool

For each selected host state, the pool may include:

- mandatory no-op;
- compatible stock reference seeds such as Norm, Attention, Convolution, low-rank and gated residual cells;
- the direct parent of each Momir mutation;
- fresh Momir candidates;
- ancestry-free Momir candidates;
- random candidates;
- retrieved historical candidates;
- bounded online-optimised candidates;
- gradient-SVD candidates;
- least-squares or Gauss–Newton candidates;
- deliberately harmful candidates;
- short-term-helpful but long-term-regressing candidates;
- and oracle or near-oracle candidates where available.

During the bootstrap, reference seeds may appear both in Momir's ancestry context and as independent controls. After scaffold withdrawal they remain only as blinded controls unless an experiment explicitly restores ancestry.

The deliberately harmful and long-term-regressing candidates are **permanent pool members, not a curriculum stage**: they survive every scaffold withdrawal as retained reference capability (INV-42) because they are the tail veto's continuous exercise against known-bad structure. Real rollbacks approach zero when the veto works (ADR-0010), so these fixtures — together with near-miss records (`domains/isperia.md`) — are the veto's only dense, renewable source of evidence.

Jin-Gitaxias and Isperia receive blinded identifiers. Candidate source and ancestry are reattached only after QA and adjudication.

### 14.2 Data separation

The target design separates four data roles:

1. **Construction support:** Momir generation, analytic fitting or nursery maturation.
2. **QA screen:** ranking and broad behavioural measurement within the candidate pool.
3. **QA audit:** an independent partition used to verify the selected evidence and detect best-of-\(K\) overfit.
4. **Retention and report:** periodic maintenance and headline reporting, untouched by construction or admission.

Isperia consumes certified summaries and does not access raw batches. This protects the evidentiary boundary while keeping the decision reproducible.

### 14.3 Academy QA

Academy QA is the high-assurance causal reference regime. It uses Tolaria's Academy-exact profile and is used for:

- multi-horizon utility evidence;
- candidate construction comparisons;
- field-QA surrogate calibration;
- execution-noise measurement;
- Isperia threshold calibration;
- Aurelia imitation targets;
- Ugin allocation outcomes;
- Emrakul maintenance cases;
- disputed or low-margin Field decisions;
- regression and divergence diagnosis;
- and Urborg dataset construction.

Its cost is measured as a product of snapshots, candidate families, candidates per family, horizons and rollout length. It is the system's metrology laboratory: narrow, expensive and trusted. Withdrawal from Academy as the default operating profile does not remove Academy as a reference capability.

### 14.4 Field QA

Field QA trades evidence quality against cost through a tiered process:

1. static artefact checks and local horizon-zero measurement;
2. learned measurement and uncertainty prediction;
3. repeated or short statistical branches for close or high-cost cases;
4. Academy-exact QA when required by risk, uncertainty, calibration age or policy.

The field surrogate predicts measurements and uncertainty. It does not issue Isperia's verdict. Field calibration is judged not only by numerical prediction error but by:

- candidate-ranking agreement with Academy;
- selection regret relative to Academy;
- accept/no-op decision disagreement;
- confidence-interval coverage;
- tail numerical-failure rate;
- and stability across device, precision and kernel profiles.

#### 14.4.1 Execution uncertainty and adjudication margins

Once Tolaria operates outside the Academy-exact regime, Isperia judges conservative evidence rather than point estimates that pretend execution is noiseless. A representative lower-confidence utility is:

$$
U^{-}(c) = \widehat U(c) - \kappa\,\sigma_{\mathrm{exec}}(c),
$$

where $\widehat U(c)$ is estimated candidate utility, $\sigma_{\mathrm{exec}}(c)$ is execution and surrogate uncertainty, and $\kappa$ is the versioned assurance coefficient. Admission requires the conservative margin over no-op to exceed the applicable policy threshold.

A numerically imperfect Field estimate may be operationally adequate when its margin is large. A small prediction error may be unacceptable near the no-op boundary. Low-margin cases resolve to `REJECT`, `DEFER`, or `REQUIRE_RETEST`; they are never forced through merely because Field execution is cheaper.

#### 14.4.2 Tail-risk veto and lexicographic order

<!-- hld: added by ADR-0004 (lexicographic admission) -->

The margin discipline above governs the **utility** stage. Before any
utility comparison, every candidate faces the **tail-risk veto** (ADR-0004,
INV-45): Isperia estimates the tail of the intervention-outcome
distribution — the catastrophic case, not the expectation — from certified
Jin-Gitaxias measurements (integration shock, instability, numerical events,
trajectory behaviour), and removes from contention any candidate whose
estimate breaches the veto threshold. No measured benefit can offset a
veto.

The two mechanisms answer different questions with different functionals:

- \(U^{-}(c)\) asks *"is the expected benefit still positive under
  conservative measurement error"* — an expectation with an uncertainty
  margin;
- the veto asks *"could this candidate cost us the trajectory"* — a tail
  bound, priced against current snapshot distance, because the real
  downside of a bad admission is not a bad growth but a rollback to the
  last snapshot.

The assurance class owns the veto operating point — its primary semantics,
beyond setting evidence-completeness requirements. Every veto and every
thin-margin pass is recorded per candidate in the `AdmissionDecision`'s
`tail_veto_results` (INV-31); thin-margin passes are the dense shoulder of
the distribution whose extreme events are, by design, rare.

### 14.5 No-op anchoring

Jin-Gitaxias always measures a matched no-op branch. Isperia assigns no-op policy utility exactly zero.

This separation matters:

- Jin-Gitaxias establishes what happened in the no-op world.
- Isperia establishes whether any candidate earns admission relative to it.

### 14.6 Branch adoption invariant

A candidate matured or evaluated inside a branch is never copied into a live host that followed a different trajectory.

Deployment occurs by either:

- adopting the winning branch’s complete state; or
- restoring the common snapshot and deterministically replaying the winning branch.

Copying only a co-adapted candidate into a divergent host is invalid.

### 14.7 Dual provider blindness

Candidate source is hidden from:

- Jin-Gitaxias while constructing source-neutral tests and interpreting results;
- Isperia while applying eligibility and utility policy.

Source provenance is reattached only after the decision for research analysis and Urborg storage.

### 14.8 Mainline–branch parity

Tolaria must use the same training semantics for the live host and branches:

- same optimiser implementation;
- same scheduler semantics;
- same precision policy;
- same model-runtime interface;
- same data transformations;
- and same lifecycle execution.

A branch-only shortcut is permitted only as an explicitly validated approximation with measured error.

### 14.9 Statistical unit

Counterfactual branches are paired observations. The independent statistical unit is the **base host trajectory**, not the branch, candidate, intervention or epoch.

All branches derived from one base trajectory remain in the same acquisition, validation or test split.
