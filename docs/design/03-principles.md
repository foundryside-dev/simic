<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: 00-INDEX.md -->
[← HLD index](00-INDEX.md)

<!-- hld: source: v4.1 monolith lines 349–491 -->
## 6. Design Principles

### 6.1 Strategy and tactics are separate

Tamiyo determines where developmental resources may be spent over a slow horizon. Narset decides what local action to take at a particular state. Tamiyo cannot choose a candidate or issue an alpha tick. Narset cannot create capacity that is absent from Tamiyo's envelope.

> **Tamiyo establishes what may be spent and where. Narset decides what to do with it now.**

### 6.2 Observation, commissioning, and interpretation are separate

Nissa produces one canonical, typed, versioned `TelemetryEnvelope` for a particular host observation and publishes it independently to every authorised consumer. Narset and Momir receive the same evidence by identity, not a copy interpreted or rewritten by another agent.

Narset may interpret the observation to decide whether and where to commission work. Momir independently interprets the same observation to decide what phenotype to design. Nissa must not smuggle a lifecycle decision or structural recommendation into telemetry.

> **Nissa sends the photograph directly. Narset sends only the assignment brief.**

“Raw telemetry” means uncaptioned by Narset, not untyped or unconstrained. Nissa may perform neutral normalisation, alignment, missing-value masking, stable feature construction, and provenance attachment. It may not emit `deficit_type`, `recommended_structure`, or equivalent prescriptions.

### 6.3 Developmental intent and phenotype are separate

Narset authors a narrow `GrowthIntent`. It may specify:

- the insertion region;
- a resource or urgency class inside Tamiyo's envelope;
- one-shot versus nursery maturation;
- assurance class;
- and tactical deadline or escalation context.

It must not specify:

- a preferred topology family;
- a diagnosis such as `RANK_COLLAPSE`;
- a suggested ancestor;
- an expected mechanism;
- rank, width, gate, operator, or connectivity hints;
- or any field whose practical purpose is to steer Momir toward a structural answer.

Leyline and Kasmina deterministically resolve the selected region and active capabilities into a `GrowthRequest`. This attaches the tensor contract, grammar profile, exact derived budgets, and compatibility information as system constraints rather than Narset-authored design hints.

> **Narset constrains the feasible solution space. Momir chooses a point within it.**

Coarse enumerated classes are preferred over arbitrary continuous request values. This reduces the opportunity for jointly trained Narset and Momir to invent a covert design code through harmless-looking budget, latency, ordering, or candidate-count fields.

### 6.4 Design, conformance, and compilation are separate

Momir creates possibilities. Elesh establishes structural legality and canonical semantic identity. Tezzeret realises that identity efficiently for a target runtime.

> **Momir establishes possibility. Elesh establishes identity. Tezzeret establishes execution.**

### 6.5 QA and judgement are separate

Urabrask establishes the facts that can only be learned by executing a candidate: runtime conformance, numerical safety, gradients, cost, trajectory behaviour, shock, regression and uncertainty.

Augustin applies policy to those facts: eligibility, the tail-risk veto, budget, expected risk, utility weights, no-op anchoring, admission margins and continued tenancy.

> **Leyline contains the law. Urabrask establishes the evidence. Augustin applies the law.**

Urabrask may report that a mandatory QA test failed. It must not decide which otherwise eligible candidate deserves admission. Augustin may reject every candidate. It must not alter the test plan, future data or measured result.

### 6.6 Kasmina and Tolaria are different substrates

Kasmina is the **model physiology**: the host network, insertion regions, reversible slots, gradients, alpha and lifecycle state.

Tolaria is the **training and execution reality**: data movement, optimiser stepping, devices, precision, distributed scheduling, checkpointing, snapshots, replay, branch execution and rollback.

> **Kasmina is what is trained. Tolaria is where and how it is trained.**

There must be one Tolaria execution path for the live host and counterfactual branches wherever practical. A special branch-only trainer would undermine paired comparisons.

### 6.7 Static validity and dynamic validity are separate

Elesh answers whether a design is legal in principle. Urabrask answers whether Tezzeret's artefact behaves correctly in practice. Static verification does not replace execution, and passing runtime tests does not excuse a structurally illegal graph.

### 6.8 Every intervention is reversible

A growth begins at zero or negligible influence. Influence is controlled through explicit lifecycle state and blend coefficients. Removal is normally a measured blend-out, not an abrupt discontinuity.

### 6.9 Doing nothing is a real competitor

Every adjudication includes a mandatory no-intervention alternative whose policy utility is exactly zero. A growth request does not imply that any growth must be admitted. In newsroom terms, every story may be spiked.

### 6.10 Paired branches differ only in the intervention

Counterfactual branches begin from the same complete snapshot, receive the same future minibatches, and use the same resource accounting. Candidate source must not alter the QA protocol.

### 6.11 The tested object and embodied semantics are identical

The canonical semantic identity tested by Urabrask, selected by Augustin, and embodied by Kasmina must be the same. Compilation may change execution strategy but not meaning.

### 6.12 Costs are contractual

Every constructor, compiler, QA plan, training run, branch, maturation process and maintenance probe receives a declared budget and reports measured spend. Over-budget work is an explicit failure.

### 6.13 Experience includes failures

Every candidate, structural rejection, compilation failure, QA defect, adjudication rejection, no-op victory, stale integration, lifecycle reversal and lysis event is recorded in Sarpadia.

### 6.14 Generalisation follows acquisition

Exact repetition and controlled one-axis variation precede composed variation, unseen host seeds, multiple regions and image-scale tasks.

### 6.15 Observability is read-only

Oona may subscribe to, persist, aggregate and present events. It cannot create actions, mutate budgets or become a hidden dependency of the training path.

### 6.16 Infrastructure remains neutral

Leyline defines records; Tolaria executes requests; Sarpadia retains history. None decides which candidate should live.

### 6.17 Bootstrap ancestry is temporary; controls endure

Conventional Norm, Attention, Convolution, low-rank, and gated-residual seeds may be retained in Sarpadia as a **reference population** for Momir's initial curriculum. They are demonstrations, ancestral material, and counterfactual controls—not Kasmina-owned production blueprints and not Narset actions.

The ancestry context is progressively withdrawn from Momir's proposal input. The same reference seeds may remain permanently in the experimental harness as blinded competitors. Removing a scaffold is not the same as deleting a baseline.

### 6.18 Independent channels preserve attribution

Momir receives three conceptually distinct inputs:

1. diagnostic evidence directly from Nissa;
2. operational constraints through the resolved `GrowthRequest`;
3. optional historical ancestry or retrieval context from Sarpadia.

These channels preserve separate provenance and may be independently ablated. Narset's hidden state, commentary, and diagnostic interpretation are never Momir inputs. This permits failures to be attributed to observation, commissioning, design, conformance, compilation, QA, judgement, embodiment, or maintenance rather than to an inseparable controller-generator pair.

### 6.19 Scaffolds are explicit, independently gated and retained as references

When a learning or measurement problem is initially too noisy, variable, or sparse for reliable causal acquisition, the architecture may introduce an explicit epistemic scaffold. Every scaffold must declare:

- the failure mode it protects against;
- the constrained acquisition regime;
- one or more controlled relaxation regimes;
- a measurable withdrawal gate;
- the authority responsible for certifying that gate;
- its retained reference, calibration, regression, or escalation role;
- and known interactions with other scaffolds.

Scaffolds advance independently. A subsystem does not lose its scaffold merely because another subsystem has passed its own gate. A confirmatory transition changes one scaffold dimension at a time unless the interaction itself is the declared experiment and the corresponding single-withdrawal controls already exist.

> **Constrain until signal is identifiable; calibrate under controlled relaxation; withdraw the dependency; verify that the invariant remains.**

Withdrawal does not imply deletion. Academy-exact Tolaria, repeated acquisition trajectories, and traditional seed references remain available as trusted oracles and controls after ordinary operation no longer depends on them.

---

<!-- hld: source: v4.1 monolith lines 4273–4322 -->
### 6.20 Armour and forward motion

<!-- hld: added post-monolith (simic-00351db32e, 2026-08-08) -->

The architecture is shaped by its predecessors' record
(`01-claim.md#26-the-empirical-driver-the-predecessor-record`), and the
shape follows one rule, stated by the owner: **where capability was
validated, push forward; where the programme struggled, build armour.**

**The armour** is every mechanism that makes a predecessor failure class
unrepresentable rather than policed, and it faces in two directions,
matching the two scar strata:

- **Against silent telemetry fabrication** (stratum one — hallucinated
  interfaces masked by defaulting access): strict Leyline schemas with
  fail-closed compatibility (INV-24), validity masks and the
  absent-is-never-zero rule (INV-38), Nissa's direct publication with no
  editorial intermediary (INV-07), observation binding (INV-08), the
  defaulting-access ban (ADR-0006), and the poison-pill negative-space
  harness.
- **Against learning-loop self-deception** (stratum two): no shaped-reward
  authority anywhere on the constitutional path, the evidence/judgement
  split and frozen thresholds (INV-18), complete negative retention and
  grouped statistics (INV-31, INV-32), mandatory no-op comparison
  (INV-15, INV-16), and blinding by construction (INV-37).

None of it is speculative caution. Each piece traces to a specific,
documented bleed: telemetry reads flooded with fabricated zeros, silently
unlearnable actions, instruments that lied, schema seams that failed open,
cohort statistics that manufactured conclusions, a reward whose optimum
rewarded the wrong behaviour.

**The forward motion** is what the record earned the right to attempt:
telemetry-conditioned structural decisions are *proven* sufficient, and a
clean measurement substrate is proven to carry real topological signal —
so the design pushes from a fixed blueprint menu to generated growth
(Momir), from shaped reward to measured counterfactuals (the branching
engine), and from single-region caution toward strategic allocation
(Tamiyo). The counterfactual engine is simultaneously both: armour against
Goodhartable shaping, and the forward mechanism that makes generation
adjudicable at all.

Two standing obligations for future contributors:

- **Do not strip armour to speed the forward motion, and do not restrict
  the forward motion because the armour is heavy.** The armour is why the
  forward signal exists; a "simplified" telemetry or contract path is the
  first chapter of the predecessor post-mortem, rewritten.
- **Armour must cite its scar.** Every defensive mechanism in this design
  traces to a named failure class; a proposed new constraint that cannot
  name the failure it prevents is bureaucracy, not armour, and should be
  challenged on exactly that ground.

## Appendix A — Architectural Smell Catalogue

| Observation | Likely smell |
|---|---|
| Tolaria rejects or prefers a candidate | Training infrastructure acquired policy |
| Tolaria uses a separate unvalidated trainer for branches | Mainline–counterfactual semantic drift |
| Every Field configuration is required to remain bitwise-identical forever | Academy training wheels became a permanent factory constraint |
| Academy replay is deleted after Field calibration | The factory dismantled its metrology laboratory |
| One global `curriculum_stage` withdraws execution, seed and ancestry scaffolds together | Independent competencies were collapsed into lockstep |
| A confirmatory run changes two scaffold axes without single-axis controls | The result is causally uninterpretable |
| Leyline calculates a case-specific decision | Constitution became case management |
| Leyline's resolver infers a deficit or topology | Contract assembly became design policy |
| Sarpadia deploys a retrieved candidate | History mutated the present |
| Tamiyo chooses blend ticks or candidate IDs | Strategy collapsed into micromanagement |
| Narset exceeds its envelope | Tactics escaped strategic governance |
| Narset forwards a modified telemetry object to Momir | Assignments desk rewrote the source material |
| `GrowthIntent` contains `preferred_topology_family` | Narset became a co-designer |
| `GrowthIntent` contains `deficit_type=RANK_COLLAPSE` | A diagnosis was smuggled into the assignment brief |
| Narset selects a bootstrap ancestor | The legacy blueprint selector reappeared |
| Fine-grained budget values predict topology choice | Narset and Momir formed a covert design channel |
| Nissa emits `should_grow` | Policy hidden in telemetry |
| Nissa emits `recommended_structure` | Source reporting became editorial prescription |
| Momir reads Narset hidden state | Design is coupled to controller implementation rather than contract |
| Momir approves or filters its live pool by admission outcome | Designer judging itself |
| Momir fails when ancestry context is null | Bootstrap scaffold became a production dependency |
| Elesh consumes future utility | Structural conformance contaminated by policy |
| Elesh changes non-equivalent semantics | Canonicaliser became designer |
| Tezzeret invents topology | Compiler became Momir |
| Urabrask returns `ADMIT` or issues a warrant | QA became judge |
| Urabrask changes mandatory tests after seeing results | QA tailored the examination |
| Augustin calls Tolaria or runs a tensor probe | Judge gathered its own evidence |
| Augustin changes future data or requests a favourable branch | Evidentiary tampering |
| Augustin knows candidate source | Adjudication contamination |
| Kasmina owns a preferred stock blueprint library | Host physiology regained a design ontology |
| Kasmina calculates utility | Host physiology acquired opinions |
| Kasmina raises alpha without an Augustin warrant | Constitutional admission bypass |
| Emrakul judges an unborn candidate | Maintenance leaked into admission |
| Emrakul generates a replacement genotype | Destruction became design |
| Oona changes optimiser, alpha or budget | Witness became control plane |
| Sarpadia stores only accepted growth | Survivorship bias |
| Reference seeds disappear from evaluation when withdrawn from Momir | Scaffold removal was confused with baseline deletion |
| Branch-trained growth is copied into a divergent live host | Co-adaptation transplant error |
| Candidate hash changes between QA, judgement and embodiment | Test–judge–deploy identity failure |
| Narset retains authority after commitment | Development never handed off |
| Urabrask and Augustin share one mutable policy object | Evidence and judgement are not independent |
| Candidate source is “hidden” only by convention | Blinding is not enforced by construction |
| A package name no longer supports its canonical sentence | Namespec responsibility drift |
