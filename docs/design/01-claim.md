<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: 00-INDEX.md -->
[← HLD index](00-INDEX.md)

<!-- hld: source: v4.1 monolith lines 1–168 -->
# High-Level Design: Counterfactual Generative Morphogenesis

**Working architecture:** Simic Engine with Phyrexian Orthodoxy and independent adjudication  
**Status:** Final repository-handoff target architecture  
**Architecture version:** 4.1  
**Namespec:** 1.0 — locked  
**Supersedes:** Version 3.0, Version 2.0, and the temporary lettered subsystem design  
**Working package root:** `src/simic/`; the umbrella project name remains separable from the subsystem names.

---

## 1. Executive Summary

This design describes a lifecycle-driven neural training system in which new computational structure is **designed from the live state of a host network**, rather than selected permanently from a fixed menu of human-authored module blueprints.

The existing morphogenetic chassis remains intact: a growth can begin at zero influence, mature behind the host, blend in gradually, hold for qualification, enter active service, become committed structure, or be sedated and lysed when it no longer earns its cost. What changes is the source of growth and the discipline with which observation, commissioning, design, conformance, compilation, testing, judgement, embodiment, memory, and maintenance are kept separate.

The system is divided into fourteen bounded domains:

- **Leyline** defines the contracts, schemas, grammar profiles, policy records, compatibility rules, and ordering invariants through which every other subsystem communicates.
- **Tolaria** is the deterministic training and execution substrate in which the host, ordinary training runs, QA trials, flash clones, replays, and counterfactual worlds execute.
- **Sarpadia** is the persistent historical substrate in which candidate lineages, reference ancestry, counterfactual outcomes, failures, abstentions, and retrieval indices are retained.
- **Tamiyo** is the strategic controller. It allocates long-horizon developmental resources, permissions, risk, and capacity across regions.
- **Narset** is the tactical controller. It decides whether and where to commission local growth, and manages the pre-commit lifecycle inside Tamiyo's active strategic envelope.
- **Nissa** observes the host and publishes one canonical, typed diagnostic record directly to every authorised consumer, including Narset and Momir, without embedding policy or editorial interpretation.
- **Momir** designs raw candidate growth graphs, parameters, mutations, and recombinations from Nissa's diagnostic context and a separately resolved assignment contract.
- **Elesh** verifies and canonicalises those designs into structurally legal, shape-safe, gradient-safe, semantically stable specifications.
- **Tezzeret** compiles canonical specifications into efficient executable artefacts without changing their meaning.
- **Urabrask** performs quality assurance. It designs test plans, requests execution in Tolaria, detects defects, measures behaviour, and produces certified evidence.
- **Augustin** is the judge. It applies admission and continued-tenancy policy to Urabrask's evidence, compares every candidate against no intervention, and issues decisions or warrants.
- **Kasmina** embodies admitted growth inside the host through reversible slots, isolated maturation, alpha blending, and lifecycle mechanics.
- **Emrakul** safely sedates, decays, consolidates, or lyses committed structure after Augustin has judged that continued tenancy is no longer justified.
- **Oona** reveals the system's account through event projections, flight recording, operator interfaces, audit bundles, and alerts.

The ordinary host-training loop and the growth loop share one execution reality:

```text
Task and data configuration
        ↓
Tolaria trains the Kasmina host
        ↓
Nissa publishes one canonical TelemetryEnvelope
        ├──→ Narset decides whether and where to commission growth
        └──→ Momir receives the same uncaptioned diagnostic evidence directly
        ↓
Tamiyo authorises strategic resources
        ↓
Narset emits a narrow GrowthIntent: the assignment brief
        ↓
Leyline and Kasmina deterministically resolve the legal GrowthRequest
        ↓
Sarpadia may supply temporary bootstrap ancestry or ordinary precedents
        ↓
Momir designs → Elesh conforms → Tezzeret compiles
        ↓
Urabrask specifies QA; Tolaria executes the tests
        ↓
Urabrask certifies the evidence
        ↓
Augustin judges candidate versus no-op
        ↓
Kasmina embodies an admitted growth
        ↓
Emrakul later removes what Augustin judges no longer earns its place
        ↓
Every success, failure, abstention, and lineage is retained in Sarpadia
        ↓
Oona reveals the complete account
```

The locked narrative grammar is:

> **Under Leyline, Tamiyo plans, Narset commissions and acts, Nissa observes, Momir designs, Elesh conforms, Tezzeret compiles, Urabrask tests in Tolaria, Augustin judges, Kasmina embodies, Emrakul destroys, and Oona reveals; every precedent is kept in Sarpadia.**

The deliberately goofy names are not decorative aliases. They encode which parts of the system are allowed to exercise agency, which parts must remain neutral infrastructure, and which sentences should sound architecturally wrong. The naming layer therefore acts as a lightweight responsibility and dependency lint.

The architecture also resembles a newsroom for a non-coincidental reason: both systems must keep source observation, commissioning, authorship, standards review, production, fact-checking, publication judgement, integration, correction, archival memory, and presentation distinct. The central newsroom rule is load-bearing here:

> **Nissa sends the photograph directly. Narset sends only the assignment brief. Momir must never receive reality through Narset's caption.**

The newsroom analogy is documented as an explanatory aid in §5.5 and Appendix E. The actual enforcement remains contractual: direct evidence publication, a narrow `GrowthIntent`, deterministic request resolution, immutable provenance, and tests that reject diagnostic or structural hints in Narset's channel.

A uniform **Scaffold Withdrawal Pattern** governs how the architecture learns under initially noisy, variable, or sparse conditions. Tolaria first establishes causal ground truth under an Academy profile with bitwise-exact replay, Narset first learns on repeated host trajectories, and Momir first learns near a viable Sarpadian reference population. Each scaffold then passes through controlled relaxation and an independent withdrawal gate. Withdrawal removes the scaffold as an ordinary production dependency while retaining it as a reference, calibration, regression, or escalation capability. Exact replay is therefore Tolaria's metrology laboratory—not a requirement that every future field execution remain bitwise identical.

## 2. Problem Statement

A fixed-blueprint morphogenetic controller must solve too many coupled decisions at once:

- determine whether the host needs intervention;
- identify the correct insertion region;
- select a module family such as normalisation, convolution, or attention;
- initialise and train the module;
- decide when it is mature enough to blend;
- control its blend schedule;
- decide whether its contribution is temporary or persistent;
- and eventually retain, fossilise, sedate, prune, or recycle it.

This coupling creates several recurring failure modes.

### 2.1 The moving-target problem

The host continues to learn while a component is being constructed. A structure designed for host state \(s_t\) may be integrated into a materially different state \(s_{t+\delta}\). If construction is slow, component quality and component freshness become opposing objectives.

### 2.2 The curriculum problem

A controller exposed immediately to broad, unrelated training trajectories must discover the entire causal language of intervention through sparse exploration. It is asked to generalise before it has learned stable primitives such as:

- wait when the host is healthy;
- request growth only when the deficit is repairable;
- reject an entire candidate pool;
- blend cautiously;
- abort stale growth;
- and remove structure that no longer pays rent.

### 2.3 The blueprint problem

A human-authored blueprint catalogue limits growth to structures the designer anticipated. It also forces a tactical policy to learn a categorical ontology that may not align with the actual functional deficit in the host.

### 2.4 The attribution problem

A host that has trained with a component may become dependent on it. Removing that component from the same host measures both the component’s intrinsic value and the host’s acquired dependence. Reliable admission and retention therefore require matched no-intervention branches, not same-host ablation alone.

### 2.5 The authority problem

When generation, validation, screening, deployment, and retention are implemented in one intelligent controller, the system can no longer explain why an intervention succeeded or failed. It also becomes easy for one subsystem to approve its own work, modify evaluation criteria, or hide policy inside telemetry.

This design addresses those failures by decomposing developmental intent, structural invention, structural legality, compilation, causal evaluation, embodiment, memory, and maintenance into separate authorities.

---

## 3. Goals

The architecture has ten primary goals.

1. **Replace fixed blueprint selection with generated growth.** Production growth should be conditioned on the host’s functional state rather than restricted to a predefined semantic menu.
2. **Preserve reversible lifecycle mechanics.** Generated structures must remain isolatable, blendable, measurable, removable, and recyclable.
3. **Separate strategic and tactical control.** Slow allocation decisions and local lifecycle actions must not collapse into one policy.
4. **Make structural legality independent from task utility.** A candidate may be perfectly legal and completely useless; the system must preserve that distinction.
5. **Ground admission and retention in causal comparisons.** Candidates should be evaluated against matched no-op futures wherever the decision justifies the cost.
6. **Make abstention first-class.** Every candidate pool must be allowed to lose against doing nothing.
7. **Retain complete evolutionary history.** Failures, rejected pools, stale candidates, and abstentions are training data, not logging noise.
8. **Make resource use mechanical and auditable.** Budgets are declared at subsystem boundaries and spend is measured rather than inferred.
9. **Teach elementary intervention grammar before broad generalisation.** Static and repeated counterfactual curricula precede unrestricted environments.
10. **Use the naming scheme as an architecture linting language.** Each subsystem has explicit authorities and explicit forbidden knowledge.

---

## 4. Non-Goals

The initial implementation does not attempt:

- unrestricted source-code generation;
- arbitrary whole-network rewriting;
- autonomous modification of the training runtime;
- unbounded or Turing-complete growth grammars;
- learned control of every lifecycle and economy parameter from the outset;
- simultaneous growth across many regions before single-region reliability is established;
- continual learning without forgetting as a guaranteed property;
- replacement of ordinary host optimisation;
- or proof that generated growth is superior at every scale.

The first defensible claim is narrower:

> Given a typed insertion contract and a measured host deficit, can the system generate, verify, compile, causally screen, and safely integrate a useful constrained growth more quickly and reliably than comparable online construction, retrieval, random search, analytic construction, or static over-provisioning?

---


<!-- hld: source: v4.1 monolith lines 4206–4251 -->
## 28. Success Criteria

The architecture is successful at the first stage when it demonstrates that:

1. Tolaria trains the live Kasmina host reproducibly, passes one Academy-exact causal reference gate, and uses equivalent semantics for replay and counterfactual branches;
2. Momir candidate pools contain useful canonical growth at a materially higher rate than random search and at lower online cost than comparable iterative construction;
3. Elesh and Tezzeret transform raw designs into executable artefacts without silent structural or semantic drift;
4. Urabrask detects runtime defects, measures trajectories and certifies evidence with an acceptable accuracy–cost trade-off;
5. Augustin selects useful candidates with low regret, reliable no-op behaviour, stable policy and no source bias;
6. generated birth plus bounded maturation improves adaptation speed without unacceptable integration shock or harmful-intervention rate;
7. Narset learns reliable local lifecycle behaviour inside fixed strategic envelopes;
8. Emrakul safely reclaims obsolete committed capacity in accordance with Augustin tenancy decisions;
9. Sarpadia retrieval or lineage conditioning improves future design quality while preserving failures, blinding and split integrity;
10. Tamiyo allocates scarce developmental resources more effectively than uniform or heuristic allocation once multiple regions exist;
11. Oona reconstructs every case and surfaces constitutional smells without entering the control path;
12. performance transfers from repeated acquisition trajectories to held-out host seeds and controlled task variations;
13. the namespec remains semantically stable enough that code review and incident discussion use it as a reliable responsibility shorthand;
14. Field Tolaria achieves acceptable ranking and accept/no-op agreement against Academy with calibrated uncertainty and escalation;
15. execution, host-distribution and design-prior scaffolds can be withdrawn independently without losing their declared invariants;
16. the fully withdrawn operating corner is interpretable against measured single-axis and interaction controls;
17. and the complete system lies on a better quality–cost–stability frontier than small and comparably provisioned static hosts.

A negative generative result remains scientifically useful if the architecture cleanly shows that analytic construction, retrieval, bounded online optimisation or static over-provisioning dominates Momir at the tested scale.

---

## 29. Final Design Statement

> **Counterfactual Generative Morphogenesis is a hierarchical, lifecycle-driven neural adaptation architecture in which Tolaria trains the host; Nissa publishes the host's diagnostic evidence directly; Tamiyo allocates strategic developmental resources; Narset commissions and manages local work without prescribing its answer; Leyline and Kasmina resolve the legal assignment contract; Sarpadia may provide temporary ancestral precedent; Momir designs candidate growth; Elesh forces it into canonical legality; Tezzeret compiles it without changing meaning; Urabrask tests it in matched possible futures; Augustin publishes it only when the certified evidence beats doing nothing; Kasmina embodies it reversibly; Emrakul removes it when it no longer earns continued tenancy; Sarpadia preserves every accepted, rejected, failed and withdrawn lineage; and Oona reveals the complete account.**

The governing engineering principle is:

> **Every intervention must be reversible, measurable, provider-blind, and allowed to lose against doing nothing.**

The governing evidence principle is:

> **Nissa sends the photograph. Narset sends the assignment. Momir writes the answer.**

The governing curriculum principle is:

> **Constrain until the signal is identifiable, calibrate under controlled relaxation, withdraw each dependency independently, and retain the scaffold as a reference oracle.**

The governing namespec principle is:

> **Actors have verbs. Infrastructure has prepositions. A sentence that sounds wrong is an architecture smell until shown otherwise.**
