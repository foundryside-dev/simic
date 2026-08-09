<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: ../00-INDEX.md -->
[← HLD index](../00-INDEX.md)

<!-- hld: source: v4.1 monolith lines 2952–3093 -->
## 17. Learning Responsibilities

Authority boundaries remain in force even when subsystems are learned. The MVP does not use an end-to-end objective that allows one subsystem’s gradients to silently redefine another subsystem’s mandate.

<!-- hld: added 2026-08-09 (simic-4282dadb69, peer review) -->
A third distinction cuts deeper than mechanical-versus-policy and governs this chapter's sequencing: **not everything that needs judgement should be learned — a policy is only safely learnable when something else can measure it.** Momir and Aurelia can be learned aggressively because they are graded against counterfactuals by something other than themselves: Jin-Gitaxias measures, Isperia judges. Isperia is the terminal authority, so a learned Isperia grades itself, and its only external signal is containment rollbacks (ADR-0010), which approach zero exactly when the veto works; Emrakul sits downstream of Isperia's verdicts and inherits the same problem. The rule-driven starts in §17.5 and §17.6 are therefore structural, not engineering conservatism: the learnability boundary sits wherever external measurement runs out.

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

Momir is trained to consume Nissa telemetry and the resolved request as separate inputs. During bootstrap it may additionally consume `BootstrapAncestryContext`; ancestry dropout progressively replaces this with null context. A training-only utility head does not grant Momir live admission authority. At inference, Momir proposes a pool that still passes through Elesh, Urabrask, Jin-Gitaxias and Isperia.

### 17.2 Aurelia

Recommended training sequence:

1. heuristic commissioning demonstrations;
2. enumerated or oracle local actions;
3. imitation pretraining;
4. targeted repeated-trajectory curriculum;
5. reinforcement-learning refinement;
6. held-out generalisation.

Aurelia's objective must not pay it for outcomes caused solely by Ugin granting a larger budget. It is evaluated on action quality inside the envelope it received.

The bootstrap source of Aurelia's counterfactual labels is the anchor corpus (ADR-0011): scheduled or random decision points on the declared seed set, forked per action class and run to end-of-run, generated before any policy exists so the labels carry no on-policy sampling bias. Aurelia consumes only the marginalised slice — best-over-action-set versus no-op, class-blind — because a topology preference is a signal it cannot legally express (INV-09); the per-action detail routes to telemetry-sufficiency validation, the Urborg/Momir bootstrap corpus, and Ugin class statistics.

The `GrowthIntent` action channel is deliberately coarse and canonical. Aurelia is never rewarded for selecting a topology family, ancestor, diagnosis, rank, width or operator. Joint training with Momir must include anti-collusion tests so the pair cannot encode structural hints in nominally irrelevant continuous values, field ordering, candidate count or aliases. Early training should hold Momir fixed or use a known-good provider so Aurelia learns commissioning rather than co-design.

### 17.3 Ugin

Ugin learns on a slower horizon and initially consumes aggregate regional outcomes rather than raw local telemetry.

Training may use:

- supervised allocation from oracle or search;
- contextual bandits;
- hierarchical reinforcement learning;
- constrained optimisation;
- or delayed long-horizon utility.

Ugin is introduced only after Aurelia’s local behaviour, Isperia’s adjudication and Emrakul’s maintenance are stable enough that strategic outcomes are interpretable.

### 17.4 Jin-Gitaxias field surrogate

A field-QA surrogate may be trained against Academy-exact `BranchResult` and `QualityReport` labels. It predicts:

- runtime conformance risk;
- task-trajectory measurements;
- integration shock;
- cost;
- execution and model uncertainty;
- evidence incompleteness;
- and escalation need.

It does **not** predict `ADMIT` as an authoritative output. Its result is part of Jin-Gitaxias's evidence process and remains auditable against Academy QA.

The surrogate's withdrawal gate is decision-aware. It must demonstrate acceptable:

- within-state rank correlation and selection regret;
- accept/no-op agreement with Academy;
- uncertainty calibration and interval coverage;
- tail failure detection;
- and stability across the declared Field device, precision and kernel profiles.

Calibration expires when the host family, grammar level, compiler backend, execution profile or evidence distribution moves outside the certified envelope. Expired or low-margin cases escalate to Academy rather than silently extending the surrogate's authority.

### 17.5 Isperia

The initial Isperia is explicit, rule-driven and pre-registered. It applies:

- hard eligibility;
- no-op anchoring;
- declared cost and risk weights;
- uncertainty margins;
- budget constraints;
- and transparent decision rules.

Later learned adjudication is possible, but only after:

- Jin-Gitaxias evidence is trustworthy;
- validation and test partitions are sealed;
- decision calibration is measurable;
- reasons and policy versions remain inspectable;
- and a fixed-rule baseline is understood.

A learned Isperia still cannot inspect candidate source or collect its own evidence.

**The tail-risk veto is the known-hard case, not an afterthought.** It is the one place where judgement is essential, learning is desirable, and the grading signal is structurally sparse — its true positives are containment rollbacks, rare by construction. The mitigations are the permanent harmful fixtures and near-miss records ([`../domains/isperia.md`](../domains/isperia.md#the-vetos-training-signal)); until that corpus demonstrably supports calibration, the veto stays rule-driven regardless of how trustworthy the rest of the evidence becomes.

### 17.6 Emrakul

The first maintenance behaviour is fixed and pre-registered. Learned maintenance begins only after Isperia continued-tenancy decisions and Jin-Gitaxias re-adaptation measurements are reliable.

Emrakul may learn *how* to execute safe sedation and decay efficiently. It does not learn to override the tenancy verdict.

### 17.7 Elesh and Urabrask

Elesh is primarily rule-driven. Learned structural analyses may be added only where they cannot replace hard safety and type checks.

Urabrask may use learned compilation heuristics, but semantic equivalence remains verified by Jin-Gitaxias runtime QA against the Elesh canonical reference.

### 17.8 Nissa

Nissa may learn feature extractors or diagnostic embeddings only under a separately defined observation objective. It is not trained end to end through Aurelia's action reward or Momir's preferred output in a way that would turn the observation into an undocumented policy message.

Any learned telemetry must retain:

- stable schema and basis semantics;
- direct publication to Aurelia and Momir;
- observation and snapshot identity;
- provenance;
- information ablations;
- and tests showing that structurally prescriptive labels are not embedded as explicit contract fields.

The existence of useful latent information is not itself a violation; the violation is allowing one agent to rewrite or selectively expose the evidence another agent receives.

### 17.9 Tolaria, Leyline and Urborg

These infrastructure domains are not policy learners.

- Tolaria may autotune execution or compilation-independent scheduling, but it may not optimise for candidate preference.
- Leyline may generate code from schemas and deterministically resolve requests, but it does not learn case-specific rules or infer diagnoses.
- Urborg may learn retrieval indices, but retrieval remains precedent selection rather than deployment policy.
- Urborg's bootstrap reference population is curated and versioned by curriculum manifests; it does not become a hidden production ontology.
- Request resolution must remain a pure, reproducible transformation whose output can be recomputed from recorded inputs.
- Tolaria may learn or autotune Field execution only inside a profile calibrated against Academy-exact evidence; exact replay remains available as a non-learned reference path.
- `ScaffoldState` is declarative experiment metadata, not a policy output inferred by infrastructure.
