<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: ../00-INDEX.md -->
[← HLD index](../00-INDEX.md)

<!-- hld: source: v4.1 monolith lines 2952–3093 -->
## 17. Learning Responsibilities

Authority boundaries remain in force even when subsystems are learned. The MVP does not use an end-to-end objective that allows one subsystem’s gradients to silently redefine another subsystem’s mandate.

### 17.1 Momir

Candidate-design objectives may include:

- canonical parameter reconstruction;
- functional-effect matching;
- min-over-\(K\) or winner-take-all reconstruction;
- reference behaviour prediction;
- parent-relative improvement;
- reference-frontier improvement;
- no-op margin;
- utility prediction through a training-only auxiliary head;
- pairwise and listwise ranking over complete candidate neighbourhoods;
- diversity in functional space;
- lineage-conditioned mutation;
- recombination;
- ancestry-dropout training;
- and contrastive learning from successful and failed candidates.

The first generator should be a small deterministic or latent-conditioned network. Flow or diffusion models are introduced only if simpler models fail to provide useful candidate coverage.

Momir is trained to consume Nissa telemetry and the resolved request as separate inputs. During bootstrap it may additionally consume `BootstrapAncestryContext`; ancestry dropout progressively replaces this with null context. A training-only utility head does not grant Momir live admission authority. At inference, Momir proposes a pool that still passes through Elesh, Tezzeret, Urabrask and Augustin.

### 17.2 Narset

Recommended training sequence:

1. heuristic commissioning demonstrations;
2. enumerated or oracle local actions;
3. imitation pretraining;
4. targeted repeated-trajectory curriculum;
5. reinforcement-learning refinement;
6. held-out generalisation.

Narset's objective must not pay it for outcomes caused solely by Tamiyo granting a larger budget. It is evaluated on action quality inside the envelope it received.

The `GrowthIntent` action channel is deliberately coarse and canonical. Narset is never rewarded for selecting a topology family, ancestor, diagnosis, rank, width or operator. Joint training with Momir must include anti-collusion tests so the pair cannot encode structural hints in nominally irrelevant continuous values, field ordering, candidate count or aliases. Early training should hold Momir fixed or use a known-good provider so Narset learns commissioning rather than co-design.

### 17.3 Tamiyo

Tamiyo learns on a slower horizon and initially consumes aggregate regional outcomes rather than raw local telemetry.

Training may use:

- supervised allocation from oracle or search;
- contextual bandits;
- hierarchical reinforcement learning;
- constrained optimisation;
- or delayed long-horizon utility.

Tamiyo is introduced only after Narset’s local behaviour, Augustin’s adjudication and Emrakul’s maintenance are stable enough that strategic outcomes are interpretable.

### 17.4 Urabrask field surrogate

A field-QA surrogate may be trained against Academy-exact `BranchResult` and `QualityReport` labels. It predicts:

- runtime conformance risk;
- task-trajectory measurements;
- integration shock;
- cost;
- execution and model uncertainty;
- evidence incompleteness;
- and escalation need.

It does **not** predict `ADMIT` as an authoritative output. Its result is part of Urabrask's evidence process and remains auditable against Academy QA.

The surrogate's withdrawal gate is decision-aware. It must demonstrate acceptable:

- within-state rank correlation and selection regret;
- accept/no-op agreement with Academy;
- uncertainty calibration and interval coverage;
- tail failure detection;
- and stability across the declared Field device, precision and kernel profiles.

Calibration expires when the host family, grammar level, compiler backend, execution profile or evidence distribution moves outside the certified envelope. Expired or low-margin cases escalate to Academy rather than silently extending the surrogate's authority.

### 17.5 Augustin

The initial Augustin is explicit, rule-driven and pre-registered. It applies:

- hard eligibility;
- no-op anchoring;
- declared cost and risk weights;
- uncertainty margins;
- budget constraints;
- and transparent decision rules.

Later learned adjudication is possible, but only after:

- Urabrask evidence is trustworthy;
- validation and test partitions are sealed;
- decision calibration is measurable;
- reasons and policy versions remain inspectable;
- and a fixed-rule baseline is understood.

A learned Augustin still cannot inspect candidate source or collect its own evidence.

### 17.6 Emrakul

The first maintenance behaviour is fixed and pre-registered. Learned maintenance begins only after Augustin continued-tenancy decisions and Urabrask re-adaptation measurements are reliable.

Emrakul may learn *how* to execute safe sedation and decay efficiently. It does not learn to override the tenancy verdict.

### 17.7 Elesh and Tezzeret

Elesh is primarily rule-driven. Learned structural analyses may be added only where they cannot replace hard safety and type checks.

Tezzeret may use learned compilation heuristics, but semantic equivalence remains verified by Urabrask runtime QA against the Elesh canonical reference.

### 17.8 Nissa

Nissa may learn feature extractors or diagnostic embeddings only under a separately defined observation objective. It is not trained end to end through Narset's action reward or Momir's preferred output in a way that would turn the observation into an undocumented policy message.

Any learned telemetry must retain:

- stable schema and basis semantics;
- direct publication to Narset and Momir;
- observation and snapshot identity;
- provenance;
- information ablations;
- and tests showing that structurally prescriptive labels are not embedded as explicit contract fields.

The existence of useful latent information is not itself a violation; the violation is allowing one agent to rewrite or selectively expose the evidence another agent receives.

### 17.9 Tolaria, Leyline and Sarpadia

These infrastructure domains are not policy learners.

- Tolaria may autotune execution or compilation-independent scheduling, but it may not optimise for candidate preference.
- Leyline may generate code from schemas and deterministically resolve requests, but it does not learn case-specific rules or infer diagnoses.
- Sarpadia may learn retrieval indices, but retrieval remains precedent selection rather than deployment policy.
- Sarpadia's bootstrap reference population is curated and versioned by curriculum manifests; it does not become a hidden production ontology.
- Request resolution must remain a pure, reproducible transformation whose output can be recomputed from recorded inputs.
- Tolaria may learn or autotune Field execution only inside a profile calibrated against Academy-exact evidence; exact replay remains available as a non-learned reference path.
- `ScaffoldState` is declarative experiment metadata, not a policy output inferred by infrastructure.
