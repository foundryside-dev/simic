<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: ../00-INDEX.md -->
<!-- hld: source: v4.1 monolith lines 3506–3860 -->
## 21. Testing and Verification Strategy

### 21.1 Namespec and architecture-lint tests

- package ownership manifest is complete;
- every package declares its verb or infrastructure context;
- forbidden imports fail CI;
- Urabrask cannot import Augustin policy;
- Augustin cannot import Tolaria execution;
- Leyline imports no agent package;
- Sarpadia storage imports no agent policy;
- Oona is absent from training-critical dependency paths;
- and public cross-boundary types use plain-English names.

### 21.2 Leyline contract tests

- schema round trips;
- version incompatibility failures;
- unknown-field behaviour;
- budget-unit consistency;
- warrant binding;
- lifecycle command authority;
- evidence-digest integrity;
- and event-envelope integrity.


### 21.3 Observation routing and assignment-brief tests

- Nissa publishes one `observation_id` to Narset and Momir.
- Narset cannot construct or substitute a second Momir-facing telemetry record.
- `GrowthIntent` rejects every forbidden diagnostic, topology, ancestry and free-form design field.
- Equivalent intent representations canonicalise identically.
- Request resolution is deterministic and cannot exceed the active envelope.
- Region contracts and grammar profiles are system-derived rather than Narset-authored.
- Observation, intent, request and Tolaria snapshot mismatches fail closed.
- Replacing Narset with another controller that emits the same canonical intent does not change Momir's output distribution.
- Changing candidate count outside Momir's semantic condition does not change single-candidate semantics.

### 21.4 Tolaria training, determinism and Field-calibration gates

**Academy-exact gate:**

- ordinary host training reaches the expected deterministic trace;
- mainline and replay use the same step implementation;
- restore one snapshot twice;
- run the same $H$ steps;
- assert bit-identical loss and state traces;
- bisect to the first differing step on failure;
- report the first differing tensor;
- compare mainline and branch optimiser semantics;
- and rerun after device, library, kernel, thread-count, dtype, compiler or precision changes.

**Calibrated-stochastic and Field gates:**

- repeat identical branches and estimate the execution-noise distribution;
- compare candidate ranking against Academy-exact outcomes;
- measure selection regret and accept/no-op disagreement;
- verify uncertainty interval coverage, including tails;
- verify that low-margin cases escalate rather than silently pass;
- invalidate calibration after an out-of-envelope runtime or model change;
- and prove that Academy-exact replay remains callable as a retained reference path.

### 21.5 Momir tests

- request compliance;
- reproducible design under fixed latent and RNG;
- candidate-count guarantees;
- spend reporting;
- grammar compliance at the raw IR boundary;
- lineage provenance;
- candidate diversity in canonical and functional space;
- parent-relative and reference-frontier improvement;
- ancestry-dropout and scaffold-free generation;
- output invariance to irrelevant request serialisation and orchestration metadata;
- no dependency on Narset hidden state or captioned telemetry;
- and valid production inference with `BootstrapAncestryContext = null`.

### 21.6 Elesh tests

- shape inference;
- illegal graph rejection;
- zero-influence proof;
- gradient-flow validation;
- canonicalisation idempotence;
- equivalent-graph hash equality;
- non-equivalent-graph hash separation;
- and semantics-preserving pruning.

### 21.7 Tezzeret tests

- deterministic compilation manifests;
- canonical-hash preservation;
- cross-layout equivalence candidates;
- compile failure classification;
- measured cost reporting;
- and reproducible artefact identity.

Reference-versus-compiled behaviour is certified by Urabrask integration tests rather than trusted as a compiler self-test.

### 21.8 Urabrask QA tests

- `QualityReport` contains no admission verdict;
- candidate source is absent from the QA view;
- mandatory runtime checks cannot be omitted;
- reference and compiled outputs are compared correctly;
- gradient conformance failures are detected;
- non-finite and hidden-state failures are detected;
- deterministic replay failures are detected;
- all-harmful and short-term-regressing fixtures are measured accurately;
- QA uncertainty is calibrated;
- evidence digests bind to the exact plan and results;
- and field-surrogate error is measured against Academy QA.

### 21.9 Augustin adjudication tests

- no-op is always available and exactly zero;
- source labels are absent from the adjudication view;
- hard-defect candidates are ineligible;
- all-net-harmful pools select no-op;
- equal-benefit cases prefer lower declared cost according to policy;
- excessive uncertainty produces retest or defer;
- Tamiyo envelope limits are enforced;
- thresholds remain frozen in confirmatory mode;
- warrants bind to the selected semantic hash and evidence digest;
- and repeated identical evidence produces identical decisions.

### 21.10 Kasmina tests

- admitted hash equals embodied hash;
- no influence before an Augustin warrant;
- gradient isolation;
- blend monotonicity where required;
- smooth decay;
- state serialization;
- illegal authority rejection;
- invalid-warrant rejection;
- and occupant-state reset on recycling.

### 21.11 Sarpadia tests

- full-pool retention;
- structural-reject retention;
- QA-failure retention;
- no-op and abstention retention;
- append-only history;
- split grouping by base trajectory;
- lineage integrity;
- blinded-view field exclusion;
- retrieval compatibility filtering;
- explicit ancestry-present versus ancestry-null provenance;
- reference controls remain available after scaffold withdrawal;
- Narset cannot select or mutate ancestry context;
- and raw/canonical/artifact/evidence/decision identity linkage.

### 21.12 Tamiyo and Narset authority tests

- Tamiyo cannot issue a lifecycle command;
- Narset cannot exceed an envelope;
- Narset cannot name a raw graph implementation;
- Narset cannot include diagnosis, topology, rank, width, operator, ancestor or mechanism fields in `GrowthIntent`;
- Narset cannot construct a Momir-facing telemetry record;
- Narset cannot select bootstrap ancestors;
- canonical-equivalent intents produce identical resolved requests;
- request values cannot exceed the bandwidth allowed by declared coarse classes;
- Narset cannot bypass Urabrask or Augustin;
- and commitment removes Narset's ordinary authority.

### 21.13 Emrakul tests

- cannot act on pre-commit growth;
- cannot issue a continued-tenancy verdict;
- cannot construct replacement candidates;
- maintenance warrant is required for ordinary lysis;
- grace and patience behaviour;
- sedation before lysis where configured;
- real lysis counted once;
- and capacity return after recycling.

### 21.14 Oona isolation tests

- training trace is identical with Oona enabled and disabled;
- missing projection data fails visibly;
- audit bundle completeness;
- no direct state mutation path from UI adapters;
- and architecture-smell events are surfaced without becoming control inputs.

### 21.15 Scaffold withdrawal tests

- every scaffold has a versioned `ScaffoldManifest`;
- every run records a reconcilable three-axis `ScaffoldState`;
- each withdrawal gate can pass or fail independently;
- a multi-axis transition without an interaction experiment fails closed;
- single-axis controls exist before a declared interaction run;
- withdrawal removes the ordinary dependency while preserving the reference capability;
- Field execution can escalate disputed cases to Academy;
- acquisition trajectories remain available after host-distribution expansion;
- stock references remain blinded controls after Momir ancestry withdrawal;
- and the fully withdrawn corner can be traced back to the relevant single-axis and interaction evidence.

---

## 22. Evaluation Framework

The system is evaluated as a quality–cost–stability frontier rather than by peak accuracy alone.

### 22.1 Tolaria training, execution and scaffold withdrawal

- host-training throughput;
- optimiser-step equivalence across mainline and branch modes;
- checkpoint and restore latency;
- Academy-exact replay divergence rate;
- divergence-localisation time;
- calibrated-stochastic outcome variance;
- Field-to-Academy within-state rank correlation;
- Field selection regret;
- Field-to-Academy accept/no-op disagreement;
- uncertainty interval coverage and calibration error;
- tail numerical-failure and escalation rates;
- branch launch overhead;
- device and precision reproducibility;
- calibration-envelope age and invalidation frequency;
- Academy retest rate;
- and host-equivalent compute per trial in each execution regime.

### 22.2 Task performance

- recovery latency after a shift;
- loss area under the recovery curve;
- worst post-shift loss;
- final task quality;
- retained performance after commitment;
- and performance after lysis or capacity recycling.

### 22.3 Candidate design

- probability that a \(K\)-candidate set contains positive-evidence growth;
- best-of-\(K\) measured trajectory curve;
- canonical and functional diversity;
- duplicate rate after Elesh canonicalisation;
- structural validity with and without bootstrap ancestry;
- parent-relative utility improvement;
- reference-frontier utility improvement;
- scaffold-free positive-candidate coverage;
- de novo selection share;
- generation latency;
- structural rejection rate;
- compilation success rate;
- and total design cost.

### 22.4 Structural and compilation pipeline

- raw-to-canonical reduction ratio;
- canonicalisation stability;
- equivalence-detection precision;
- compile latency;
- runtime cost-estimation error;
- Urabrask semantic-conformance failure rate;
- gradient-conformance failure rate;
- and cross-device semantic agreement.

### 22.5 Urabrask QA quality

- defect-detection sensitivity and specificity;
- evidence reproducibility;
- within-state ranking correlation between field and Academy measurements;
- measurement error by horizon;
- uncertainty calibration;
- evidence-incompleteness detection;
- false-pass and false-fail rates;
- and QA cost–coverage Pareto frontier.

### 22.6 Augustin adjudication quality

- best-candidate selection regret;
- no-op precision and recall;
- false-intervention rate;
- harmful-admission rate;
- unnecessary-retest rate;
- decision stability under identical evidence;
- policy sensitivity to declared weights;
- provider-blindness audit results;
- and reason-code completeness.

### 22.7 Narset tactical quality

- intervention timing regret;
- unnecessary-intervention rate;
- missed-intervention rate;
- insertion-region regret;
- request correctness;
- assignment-brief purity;
- diagnostic-caption violation rate;
- covert-channel sensitivity under semantically equivalent requests;
- premature QA or blend requests;
- premature commitment;
- abort-too-late rate;
- and lifecycle completion rate.

### 22.8 Tamiyo strategic quality

- budget utilisation;
- regional starvation rate;
- capacity fragmentation;
- strategic regret against oracle allocation;
- excess churn induced by allocation;
- exploration efficiency;
- and performance under constrained global resources.

### 22.9 Integration stability

- instantaneous loss jump;
- activation change;
- gradient shock;
- recovery steps;
- alpha reversals;
- rollback frequency;
- and host divergence from no-op.

### 22.10 Maintenance quality

- continued-tenancy decision regret;
- retain-too-long rate;
- lyse-too-early rate;
- host-dependence versus intrinsic-value separation;
- successful sedation rate;
- capacity reclaimed;
- post-lysis recovery;
- and install–lyse oscillation.

### 22.11 Economy

- active and committed dynamic parameters;
- host-equivalent forward and backward passes;
- design, canonicalisation, compilation, QA, adjudication, maturation and maintenance costs;
- churn;
- rent paid;
- total accelerator time;
- offline training cost;
- and amortised cost per successful intervention.

### 22.12 Reliability

For each main endpoint report:

- mean;
- median;
- interquartile range;
- worst decile;
- failure rate;
- and confidence interval across independent base host trajectories.

Counterfactual branches are paired measurements, not additional independent hosts.

---

