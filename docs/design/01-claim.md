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
- **Urborg** is the persistent historical substrate in which candidate lineages, reference ancestry, counterfactual outcomes, failures, abstentions, and retrieval indices are retained.
- **Ugin** is the strategic controller. It allocates long-horizon developmental resources, permissions, risk, and capacity across regions.
- **Aurelia** is the tactical controller. It decides whether and where to commission local growth, and manages the pre-commit lifecycle inside Ugin's active strategic envelope.
- **Nissa** observes the host and publishes one canonical, typed diagnostic record directly to every authorised consumer, including Aurelia and Momir, without embedding policy or editorial interpretation.
- **Momir** designs raw candidate growth graphs, parameters, mutations, and recombinations from Nissa's diagnostic context and a separately resolved assignment contract.
- **Elesh** verifies and canonicalises those designs into structurally legal, shape-safe, gradient-safe, semantically stable specifications.
- **Urabrask** compiles canonical specifications into efficient executable artefacts without changing their meaning.
- **Jin-Gitaxias** performs quality assurance. It designs test plans, requests execution in Tolaria, detects defects, measures behaviour, and produces certified evidence.
- **Isperia** is the judge. It applies admission and continued-tenancy policy to Jin-Gitaxias's evidence, compares every candidate against no intervention, and issues decisions or warrants.
- **Wrenn** embodies admitted growth inside the host through reversible slots, isolated maturation, alpha blending, and lifecycle mechanics.
- **Emrakul** safely sedates, decays, consolidates, or lyses committed structure after Isperia has judged that continued tenancy is no longer justified.
- **Tamiyo** reveals the system's account through event projections, flight recording, operator interfaces, audit bundles, and alerts.

The ordinary host-training loop and the growth loop share one execution reality:

```text
Task and data configuration
        ↓
Tolaria trains the Wrenn host
        ↓
Nissa publishes one canonical TelemetryEnvelope
        ├──→ Aurelia decides whether and where to commission growth
        └──→ Momir receives the same uncaptioned diagnostic evidence directly
        ↓
Ugin authorises strategic resources
        ↓
Aurelia emits a narrow GrowthIntent: the assignment brief
        ↓
Leyline and Wrenn deterministically resolve the legal GrowthRequest
        ↓
Urborg may supply temporary bootstrap ancestry or ordinary precedents
        ↓
Momir designs → Elesh conforms → Urabrask compiles
        ↓
Jin-Gitaxias specifies QA; Tolaria executes the tests
        ↓
Jin-Gitaxias certifies the evidence
        ↓
Isperia judges candidate versus no-op
        ↓
Wrenn embodies an admitted growth
        ↓
Emrakul later removes what Isperia judges no longer earns its place
        ↓
Every success, failure, abstention, and lineage is retained in Urborg
        ↓
Tamiyo reveals the complete account
```

The locked narrative grammar is:

> **Under Leyline, Ugin plans, Aurelia commissions and acts, Nissa observes, Momir designs, Elesh conforms, Urabrask compiles, Jin-Gitaxias tests in Tolaria, Isperia judges, Wrenn embodies, Emrakul destroys, and Tamiyo reveals; every precedent is kept in Urborg.**

The deliberately goofy names are not decorative aliases. They encode which parts of the system are allowed to exercise agency, which parts must remain neutral infrastructure, and which sentences should sound architecturally wrong. The naming layer therefore acts as a lightweight responsibility and dependency lint.

At the centre of the authority model sits one load-bearing routing rule:

> **Nissa publishes the evidence directly to Aurelia and Momir (INV-07). Aurelia sends only the assignment brief (INV-09). Momir must never receive reality through Aurelia's caption.**

The enforcement is contractual: direct evidence publication, a narrow `GrowthIntent`, deterministic request resolution, immutable provenance, and tests that reject diagnostic or structural hints in Aurelia's channel. (Readers who want the authority model without the codenames will find it retold as a newsroom in Appendix E.)

A uniform **Scaffold Withdrawal Pattern** governs how the architecture learns under initially noisy, variable, or sparse conditions. Tolaria first establishes causal ground truth under an Academy profile with bitwise-exact replay, Aurelia first learns on repeated host trajectories, and Momir first learns near a viable Urborg reference population. Each scaffold then passes through controlled relaxation and an independent withdrawal gate. Withdrawal removes the scaffold as an ordinary production dependency while retaining it as a reference, calibration, regression, or escalation capability. Exact replay is therefore Tolaria's metrology laboratory—not a requirement that every future field execution remain bitwise identical.

## 2. Problem Statement

<!-- hld: §2.6 added post-monolith (simic-00351db32e, 2026-08-08) — the empirical driver -->

Sections 2.1–2.5 describe the structural failure modes of fixed-blueprint
morphogenesis. The proximate, empirical driver of this design is §2.6: the
predecessor record — what the esper line proved, where it bled, and why the
correct response was to replace the reward function rather than repair it.

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

The two cases are not symmetric. Admission evidence is branch-paired from a common snapshot over a common future — the full counterfactual. Once a growth is committed, the host that never received it no longer exists: measuring it honestly would mean running a parallel no-op branch for the entire tenure, a permanent doubling of training cost per committed growth. What tenancy evidence actually measures is **replaceability at a chosen horizon**, a different and weaker quantity — maintenance decisions therefore operate under an explicitly weaker evidentiary standard than admission decisions (`domains/isperia.md#continued-tenancy-utility`). During bootstrap that weaker standard is itself scaffolded: on a declared anchor host set the full-tenure counterfactual *is* paid, so the cheap instrument's error is measured before it is trusted (ADR-0011).

### 2.5 The authority problem

When generation, validation, screening, deployment, and retention are implemented in one intelligent controller, the system can no longer explain why an intervention succeeded or failed. It also becomes easy for one subsystem to approve its own work, modify evaluation criteria, or hide policy inside telemetry.

This design addresses those failures by decomposing developmental intent, structural invention, structural legality, compilation, causal evaluation, embodiment, memory, and maintenance into separate authorities.

### 2.6 The empirical driver: the predecessor record

This architecture is the third incarnation of one research programme — early
versions of the simic project (known as ESPER, then ESPER LITE) built the
morphogenetic chassis this design retains, and their record is the reason
for every major choice here.

**What the predecessors proved.** Seed telemetry is *sufficient* for
intelligent structural decisions: the information needed to choose useful
interventions was demonstrably present in the host-side diagnostics. When
the measurement path was clean, the controller found real topological
signal — including independently rediscovering that a convolution-plus-
normalisation structure outperformed a heavier convolution alternative
(owner-recalled result, an attention-adjacent principle found from
telemetry alone). The hypothesis was never the casualty.

**Where they bled.** The scars are layered in two strata, and they defend
different parts of this architecture.

**Stratum one — telemetry-access corruption (the silent-zero era).** In one
generation, machine-generated telemetry code contained *hallucinated
interfaces* — plausible-looking accessors for fields that did not exist —
and permissive defaulting access (`.get()` with a silent default) converted
those hallucinations into zero-filled telemetry reads. The host signal
existed; the read path fabricated zeros over it, and the reward read
collapsed without a single error being raised. The failure mode deserves
its precise name, because it is characteristic of AI-assisted engineering
rather than ordinary bad code: **a model can hallucinate an interface and
then use permissive access idioms to hide the hallucination behind silent
defaults**. The predecessor response was severe enough to become tooling —
a CI ban on defaulting telemetry access — and is constitutional here:
typed `TelemetryEnvelope` contracts, `validity_mask`, *absent signal stays
absent — never a fabricated zero* (INV-38, runtime policy P2), fail-closed
typed compatibility (INV-24), direct Nissa publication (INV-07),
observation binding (INV-08), the defaulting-access ban (ADR-0006), and
the poison-pill acceptance harness.

**Stratum two — learning-loop and instrument failures.** After telemetry
access was hardened, the RL loop and its instruments still failed, in five
recurring classes documented in the predecessor's working record:

1. **Silent signal destruction in the learning plumbing.** An action-
   probability floor made floor-bound actions' log-probabilities constants
   — zero policy gradient — so ~94% of commit-class decisions could not
   learn *despite a strong, correctly measured, monotonic reward*. The
   signal existed; the optimiser could not receive it.
2. **Instruments that lied.** A headline "entropy collapse" blocking a
   causal read for weeks was a detector artifact (statistics over
   structurally-zero placeholder steps); a companion alarm was a dead
   false-negative; a key metric was mislabelled.
3. **Fail-open schema seams.** A new metric key without a registered
   reducer crashed every live run while the unit suite stayed green — the
   second occurrence of that exact class. Hence evidence gates that run
   the real pipeline, not only unit suites.
4. **Over-read epidemics.** Seven over-reads in one diagnostic thread:
   cohort statistics over mostly-unset fields, non-causal surrogates read
   as causal, mismatched statistics manufacturing false effects, a
   pre-registered discriminator that could not discriminate. Hence frozen
   thresholds, complete negative retention (INV-31), grouped statistics
   (INV-32), and the evidence/judgement split (INV-18).
5. **Reward-optimum defects.** An unclipped dense attribution term running
   ~100× over terminal scale made farming the shaping optimal; broken
   potential-based-shaping telescoping and a lifecycle quirk made
   commitment avoidance partly *structurally rational*. The policy was
   never broken; the reward's optimum was wrong.

The two strata are two distinct ways the system learned to lie — first
through silent telemetry fabrication, then through learning-loop and
statistical self-deception — and the armour is built in both directions
accordingly.

**The pivot, stated plainly.** The predecessors could not shape a reward to
incentivise behaviour the reward provably contained. The uncharitable
reading — "DRL didn't converge, so they built something more complicated" —
is wrong. This design **replaces the reward function with measured
counterfactuals**: paired branches from one snapshot over identical futures
cancel ordinary-training variance, so the difference between branches *is*
the intervention effect. That converts credit assignment into supervised
learning — Momir becomes ranking over measured pools, Aurelia becomes
per-step supervised classification against counterfactual labels, and
Isperia becomes explicit adjudication rules. The genuinely irreducible RL
shrinks to Ugin's allocation and Aurelia's timing. The counterfactual
apparatus is therefore not overhead wrapped around a policy learner; **it
is the machine that manufactures the supervision signal RL could not
extract**, and the programme's cost model is honestly read as the price of
that conversion.

**Attribution honesty.** Part of the expected improvement over the
predecessors — dense per-step labels, attributable failures — is a
training-procedure win that could arguably have been retrofitted to the old
system. The architecture's irreducible contributions are the ones that
could not: generated (not selected) structure, separated authorities, and
provider blindness. Claims in `01-claim.md` §28 should be read against this
split.

The design-level consequence of this record is the armour-and-forward-
motion principle (`03-principles.md#620-armour-and-forward-motion`).

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

1. Tolaria trains the live Wrenn host reproducibly, passes one Academy-exact causal reference gate, and uses equivalent semantics for replay and counterfactual branches;
2. Momir candidate pools contain useful canonical growth at a materially higher rate than random search and at lower online cost than comparable iterative construction;
3. Elesh and Urabrask transform raw designs into executable artefacts without silent structural or semantic drift;
4. Jin-Gitaxias detects runtime defects, measures trajectories and certifies evidence with an acceptable accuracy–cost trade-off;
5. Isperia selects useful candidates with low regret, reliable no-op behaviour, stable policy and no source bias;
6. generated birth plus bounded maturation improves adaptation speed without unacceptable integration shock or harmful-intervention rate;
7. Aurelia learns reliable local lifecycle behaviour inside fixed strategic envelopes;
8. Emrakul safely reclaims obsolete committed capacity in accordance with Isperia tenancy decisions;
9. Urborg retrieval or lineage conditioning improves future design quality while preserving failures, blinding and split integrity;
10. Ugin allocates scarce developmental resources more effectively than uniform or heuristic allocation once multiple regions exist;
11. Tamiyo reconstructs every case and surfaces constitutional smells without entering the control path;
12. performance transfers from repeated acquisition trajectories to held-out host seeds and controlled task variations;
13. the namespec remains semantically stable enough that code review and incident discussion use it as a reliable responsibility shorthand;
14. Field Tolaria achieves acceptable ranking and accept/no-op agreement against Academy with calibrated uncertainty and escalation;
15. execution, host-distribution and design-prior scaffolds can be withdrawn independently without losing their declared invariants;
16. the fully withdrawn operating corner is interpretable against measured single-axis and interaction controls;
17. and the complete system lies on a better quality–cost–stability frontier than small and comparably provisioned static hosts.

A negative generative result remains scientifically useful if the architecture cleanly shows that analytic construction, retrieval, bounded online optimisation or static over-provisioning dominates Momir at the tested scale.

---

## 29. Final Design Statement

> **Counterfactual Generative Morphogenesis is a hierarchical, lifecycle-driven neural adaptation architecture in which Tolaria trains the host; Nissa publishes the host's diagnostic evidence directly; Ugin allocates strategic developmental resources; Aurelia commissions and manages local work without prescribing its answer; Leyline and Wrenn resolve the legal assignment contract; Urborg may provide temporary ancestral precedent; Momir designs candidate growth; Elesh forces it into canonical legality; Urabrask compiles it without changing meaning; Jin-Gitaxias tests it in matched possible futures; Isperia publishes it only when the certified evidence beats doing nothing; Wrenn embodies it reversibly; Emrakul removes it when it no longer earns continued tenancy; Urborg preserves every accepted, rejected, failed and withdrawn lineage; and Tamiyo reveals the complete account.**

The governing engineering principle is:

> **Every intervention must be reversible, measurable, provider-blind, and allowed to lose against doing nothing.**

The governing evidence principle is:

> **Nissa sends the photograph. Aurelia sends the assignment. Momir writes the answer.**

The governing curriculum principle is:

> **Constrain until the signal is identifiable, calibrate under controlled relaxation, withdraw each dependency independently, and retain the scaffold as a reference oracle.**

The governing namespec principle is:

> **Actors have verbs. Infrastructure has prepositions. A sentence that sounds wrong is an architecture smell until shown otherwise.**
