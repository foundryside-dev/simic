<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: ../00-INDEX.md -->
[← HLD index](../00-INDEX.md)

<!-- hld: source: v4.1 monolith lines 3861–3947 -->
## 23. Current-to-Target Migration

The target is an evolution of the existing lifecycle architecture, not a wholesale rewrite.

### 23.1 Tolaria remains the training substrate

Legacy ordinary host training remains under Tolaria. Snapshotting, replay and flash cloning extend this authority; they do not replace or fork the training substrate.

Migration introduces explicit execution regimes:

1. wrap the current deterministic training path as `ACADEMY_EXACT`;
2. capture complete replay state and pass the bitwise gate on the supported reference profile;
3. add repeated stochastic branch execution and calibration records;
4. certify bounded `CALIBRATED_STOCHASTIC` profiles against Academy;
5. enable `FIELD` profiles only after decision-aware gates pass;
6. retain Academy as the CI, causal-label, disputed-case and divergence-debugging path.

The target is not bitwise validation on every future production configuration. The target is one maintained exact reference profile and a measured path from that profile to realistic execution.

### 23.2 Controller rename and split

- The existing local/tactical policy responsibility moves to **Narset**.
- **Tamiyo** becomes the strategic controller over regions, budgets, capacity and long horizons.
- Transitional code may use an explicit name such as `LegacyTamiyoController`, but the final API does not use `Tamiyo` for the local controller.
- Any prior allocator implementation migrates to Tamiyo’s target `StrategicEnvelope` interface.

### 23.3 Observation, commissioning and candidate design

- Nissa becomes the canonical source of Momir's diagnostic input and publishes the same observation identity directly to Narset and Momir.
- Narset emits `GrowthIntent`, not a complete design-bearing `GrowthRequest`.
- Leyline and Kasmina deterministically resolve tensor, grammar and budget constraints.
- Fixed blueprint selection is removed from Narset's production action space.
- **Momir** becomes the generated candidate designer.
- Legacy Norm, Attention, Convolution and related seeds migrate from Kasmina's internal blueprint library into a versioned Sarpadian reference population and research-control package.
- Those reference seeds serve as temporary Momir ancestry and permanent experimental controls, not the production ontology.
- Compatibility aliases are permitted only during migration and must not reintroduce topology fields into `GrowthIntent`.

### 23.4 Structural and compilation pipeline

- **Elesh** is inserted after design and before compilation.
- **Tezzeret** becomes the explicit compiler.
- Candidate identity is split into raw design, canonical semantic identity and executable artefact identity.

### 23.5 QA and adjudication split

Any existing combined screening/economy component is decomposed:

- **Urabrask** owns test planning, runtime checks, branch measurement, regression, uncertainty and `QualityReport`.
- **Augustin** owns hard eligibility, no-op anchoring, policy utility, admission, continued tenancy and warrants.

This split is mandatory. Renaming the old judge to Urabrask while leaving admission logic inside it does not satisfy the target design.

### 23.6 Kasmina and lifecycle

Kasmina retains host topology, reversible slots, gradient isolation, maturation, blending, commitment, decay mechanics and state serialization.

The change is constitutional:

- influence-increasing transitions require Augustin warrants;
- post-commit ordinary removal requires maintenance warrants;
- Narset and Emrakul have disjoint authority windows.

### 23.7 Memory and observability

- The static seed catalogue becomes a versioned **Sarpadian reference population** plus an episodic lineage-aware archive.
- Sarpadia records whether ancestry was supplied, withdrawn, or used only as a blinded control.
- Existing telemetry backends remain **Nissa**, with direct publication to Momir added as a locked route.
- Existing operator surfaces migrate under **Oona**.
- Oona gains a newsroom projection showing source observation, assignment, draft, standards, production, QA, judgement, placement, correction and archive.
- Event schemas remain in Leyline and training remains independent of Oona availability.

### 23.8 Namespec migration

Package moves and telemetry names are versioned. Compatibility aliases are time-limited and must be visibly marked as legacy.

The migration should include:

- an ADR locking Namespec 1.0;
- package-owner READMEs;
- import-linter rules;
- telemetry producer-name migration;
- persisted-record schema migration;
- dashboard label migration;
- and removal dates for old aliases.
