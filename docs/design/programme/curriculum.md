<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: ../00-INDEX.md -->
[← HLD index](../00-INDEX.md)

<!-- hld: source: v4.1 monolith lines 2653–2951 -->
## 16. Static-to-Counterfactual Curriculum and Scaffold Withdrawal

The curriculum teaches causal intervention grammar before broad exploration. It uses one repeatable meta-curricular pattern across three initially difficult dimensions: execution attribution, host-trajectory variance, and component-design sparsity.

### 16.1 The Scaffold Withdrawal Pattern

| Dimension | Failure mode protected against | Learn the Land | Controlled relaxation | Operational generalisation | Retained reference capability |
|---|---|---|---|---|---|
| **Execution — Tolaria** | Attribution error caused by runtime noise | Academy-exact bitwise replay and noiseless paired counterfactuals | Repeated stochastic branches and Field surrogate calibration against Academy | Full validated Field execution with uncertainty, margins and escalation | Academy-exact replay remains the causal oracle, CI profile and divergence laboratory |
| **Host trajectories — Narset curriculum** | Host trajectory variance obscuring intervention timing and lifecycle learning | Fixed, repeated host seeds and identical trajectories | Held-out initialisations from the same family and controlled one-axis changes | Unseen geometries, scales, data orders and task distributions | Acquisition trajectories remain regression and policy-language fixtures |
| **Design prior — Momir** | Generator collapse in a sparse graph search space | Reference reconstruction, imitation and bounded mutation | Ancestry dropout, recombination and partial de novo generation | Null ancestry and the full permitted grammar | Reference seeds remain blinded controls and Sarpadian precedent |

The common progression is:

$$
\text{constrain until signal is identifiable}
\rightarrow
\text{calibrate under controlled relaxation}
\rightarrow
\text{withdraw the production dependency}
\rightarrow
\text{verify retained invariants}.
$$

Each scaffold protects a different failure mode and has an independent gate. Tolaria may be ready for calibrated Field execution while Momir still needs ancestry; Momir may pass null-ancestry generation while Narset still needs repeated host trajectories. The architecture therefore records a three-axis `ScaffoldState` rather than one global `curriculum_stage` flag.

A confirmatory transition withdraws one scaffold at a time. Two or more may change together only when their interaction is the declared experiment and the corresponding single-axis controls have already been measured. This rule prevents a failed run from becoming uninterpretable.

The first withdrawal gates are:

- **Tolaria:** Field-to-Academy ranking regret, accept/no-op disagreement, uncertainty coverage and tail-failure rate remain inside declared limits; ambiguous cases can still escalate to Academy.
- **Host distribution:** Narset's intervention timing, harmful-action rate and lifecycle completion remain stable on held-out in-family initialisations before task-family expansion.
- **Momir:** structural validity, positive-candidate coverage and reference-relative utility remain acceptable with `BootstrapAncestryContext = null`.

Hidden correlations between scaffolds are tested explicitly. Fixed host seeds may be unusually deterministic, and stock reference seeds may cover only the viable repairs for those seeds. The final programme therefore measures selected interaction cells before claiming full scaffold-free operation.

### Stage 0 — Namespec, contracts, training substrate and determinism

Use a fixed host with manually constructed helpful and harmful growths.

Validate:

- Namespec package ownership and forbidden imports;
- Leyline schema round trips;
- direct Nissa publication of one observation identity to Narset and Momir;
- rejection of diagnostic or topology fields in `GrowthIntent`;
- deterministic `GrowthIntent` to `GrowthRequest` resolution;
- Tolaria ordinary host training;
- mainline–replay equivalence;
- exact snapshot and restore;
- bit-identical common-future execution under Tolaria's Academy-exact profile;
- `ScaffoldManifest` and `ScaffoldState` validation;
- rejection of multi-axis withdrawal without an interaction experiment identifier;
- Kasmina isolated maturation;
- smooth blend-in and blend-out;
- lifecycle authority enforcement;
- rollback;
- and slot recycling.

No learned controller or generator is required.

### Stage 1 — Momir reference-seed bootstrap

Freeze the host at selected snapshots. Fix the insertion site, request and budget. Build a versioned Sarpadian reference population of conventional and synthetic known-good canonical cells.

#### Stage 1A — Structural literacy

Train Momir to encode and reconstruct reference graphs without structural corruption. Measure graph validity, canonical identity, typed ports, zero-influence behaviour and parameter reconstruction before spending Tolaria rollout budget.

#### Stage 1B — Behavioural imitation and prediction

Show Momir the same Nissa context used to evaluate each reference. Train it to predict reference utility, shock, cost and lifecycle outcome, and to reproduce a compatible design. This teaches:

```text
host diagnostic context → viable known structure
```

without granting Narset a blueprint action.

#### Stage 1C — Local mutation

Allow bounded graph and parameter mutations around one ancestor. For every state, test:

```text
parent
Momir mutations
other compatible references
retrieval and analytic controls
no-op
```

Train on the ordered neighbourhood rather than only the winner.

#### Stage 1D — Recombination

Permit composition of compatible substructures from multiple ancestors. Elesh must identify malformed, redundant and equivalent combinations. Tezzeret must compile canonical meaning rather than raw syntax.

#### Stage 1E — Ancestry-optional generation

Require a declared fraction of candidates to use `parent_lineages = []`. Keep references in the control pool but stop supplying them to selected Momir calls.

#### Stage 1F — Scaffold withdrawal gate

Evaluate with `BootstrapAncestryContext = null` on held-out host states. Momir must retain acceptable structural validity, positive-candidate coverage and reference-relative performance. Stock seeds remain blinded controls; they are no longer proposal scaffolds.

### Stage 2 — Structural conformance and compilation school

Stress Momir, Elesh and Tezzeret independently with:

- malformed graphs;
- shape edge cases;
- zero-influence failures;
- illegal gradient paths;
- duplicate and equivalent graphs;
- dead structure;
- compiler fusion cases;
- memory-layout cases;
- and cross-device artefacts.

The goal is reliable canonical identity and compilation before task utility is involved.

### Stage 3 — Urabrask QA school

Use known canonical specifications and artefacts with injected defects.

Teach and test Urabrask to detect:

- semantic drift;
- wrong gradients;
- non-finite values;
- nondeterminism;
- hidden state mutation;
- budget overrun;
- performance regression;
- short-term benefit followed by long-term failure;
- and incomplete evidence.

The expected output is a reliable `QualityReport`, not an admission decision.

### Stage 4 — Augustin adjudication school

Hold Urabrask reports fixed and vary policy cases.

Teach or calibrate Augustin to:

- reject hard-defect candidates;
- choose no-op when all candidates are net harmful;
- prefer lower-cost candidates at equal benefit;
- request retest when uncertainty is excessive;
- obey Tamiyo's envelope;
- and produce stable, explicit reasons.

This isolates judgement from QA quality.

### Stage 5 — Short-horizon flash-clone school

Allow the host to move only inside matched Tolaria branches.

Teach the system to distinguish:

- immediate and trajectory benefit;
- short-term repair and long-term regression;
- component quality and integration shock;
- construction delay and staleness;
- intrinsic contribution and host dependence;
- admission value versus continued-tenancy value;
- and intervention signal versus execution noise.

This stage creates the Academy evidence used to validate Field QA and Augustin's policy. It then repeats selected candidate pools under the calibrated-stochastic profile to estimate execution variance, ranking stability and accept/no-op decision disagreement. Field execution cannot advance merely because mean loss traces look similar; its operational decisions and uncertainty coverage must meet the declared Tolaria withdrawal gate.

### Stage 6 — Narset tactical language acquisition

Use a known-good candidate source and reliable QA/adjudication so tactical failure cannot be blamed on Momir, Urabrask or Augustin.

Nissa continues to publish source evidence directly. Narset is trained only to commission and manage work:

```text
WAIT
COMMISSION_GROWTH
CONTINUE_MATURATION
REQUEST_QA
REQUEST_ADJUDICATION
BEGIN_BLEND
CONTINUE_BLEND
HOLD
ABORT
COMMIT
```

Use short action-sequence search or counterfactual enumeration to create imitation targets before reinforcement learning. The `GrowthIntent` channel remains narrow throughout; no topology or diagnosis labels are added to make the policy easier to train.

### Stage 7 — Emrakul maintenance school

Use committed structures with known utility trajectories and fixed Augustin maintenance policy.

Calibrate:

```text
REQUEST_REVIEW
HOLD
SEDATE
DECAY
LYSE
```

Include useful structures, host-dependent but replaceable structures, redundant structures, long-term regressors and regime-specific structures that become obsolete.

### Stage 8 — Tamiyo strategic allocation school

Introduce multiple regions or multiple Narset-controlled cells with constrained global resources.

Teach Tamiyo to allocate:

- capacity;
- intervention quotas;
- exploration budgets;
- cooldowns;
- permitted grammar profiles;
- adjudication risk;
- and maintenance pressure.

Local Narset, Urabrask, Augustin and Emrakul behaviour is held fixed initially so strategic failure is attributable.

### Stage 9 — Joint few-trajectory, many-variation training

Run the complete system repeatedly on a small set of base host trajectories while recording the full three-axis `ScaffoldState` for every run.

Begin with exact repetition, then vary one ordinary experimental axis at a time:

- shift timing;
- shift severity;
- host learning rate;
- insertion width;
- data order;
- observation noise;
- telemetry schema;
- maturation budget;
- generation latency;
- compilation target;
- QA horizon;
- adjudication weights;
- blend duration;
- rent;
- candidate randomness;
- request resource class;
- bootstrap ancestry present versus absent;
- execution regime;
- and regional budget pressure.

Add request-channel ablations:

- same telemetry and effective constraints, different irrelevant serialisation;
- same resolved request, different Narset implementation;
- candidate count varied outside Momir's semantic condition;
- and equivalent resource-class encodings canonicalised by the resolver.

Momir's candidate distribution should not change under semantically irrelevant request variations. Only after individual invariances are learned are multiple ordinary axes composed.

Scaffold withdrawal is governed separately from ordinary variation:

1. hold host distribution and design prior fixed while relaxing Tolaria execution;
2. hold execution and design prior fixed while relaxing host-distribution restriction;
3. hold execution and host distribution fixed while withdrawing Momir ancestry;
4. then run declared two-way interactions;
5. finally run the fully withdrawn corner.

The minimum scaffold interaction matrix is:

| Execution | Host distribution | Momir ancestry | Purpose |
|---|---|---|---|
| Academy exact | Repeated acquisition | Present | Fully scaffolded causal reference |
| Calibrated stochastic / Field | Repeated acquisition | Present | Execution withdrawal effect |
| Academy exact | Held-out in-family | Present | Host-distribution withdrawal effect |
| Academy exact | Repeated acquisition | Null | Design-prior withdrawal effect |
| Field | Held-out in-family | Present | Execution × host interaction |
| Field | Repeated acquisition | Null | Execution × design interaction |
| Academy exact | Held-out in-family | Null | Host × design interaction |
| Field | Held-out / open | Null | Fully withdrawn operating condition |

The matrix may be staged rather than run exhaustively at every scale, but the final claim must include enough intermediate cells to explain any gap between the fully scaffolded and fully withdrawn corners.

### Stage 10 — Generalisation and scaling

Evaluate on:

- unseen host initialisations;
- unseen data orders;
- unseen shift times;
- unseen task geometries;
- different insertion widths;
- no bootstrap ancestry;
- held-out reference families;
- multiple growth requests over one trajectory;
- additional insertion regions;
- small image tasks;
- and larger benchmarks.

The broad environment is the examination, not the initial classroom. Narset's repeated host-seed curriculum and Momir's reference-ancestry curriculum are both successful only if the scaffolds can be removed. Tolaria's execution curriculum is successful when Field operation remains decision-calibrated against Academy rather than when Academy is deleted. Final reporting names the exact `ScaffoldState` of every result and distinguishes scaffold-free operation from reference-assisted escalation.
