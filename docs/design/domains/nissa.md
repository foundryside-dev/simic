<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: ../00-INDEX.md -->
<!-- hld: source: v4.1 monolith lines 2037–2075 -->
### 13.6 Nissa — Observer and Source Desk

#### Responsibilities

- observe the host and insertion regions;
- produce ablated-path telemetry for growth decisions;
- compute typed activation, gradient, spectral, temporal and task diagnostics;
- perform neutral normalisation, alignment, validity masking and stable feature construction;
- bind every observation to the exact host state and Tolaria snapshot;
- attach provenance and normalisation manifests;
- publish the same canonical observation independently to Narset and Momir;
- provide only permitted coarse summaries to Tamiyo;
- and emit stable, versioned `TelemetryEnvelope` records.

#### Invariants

- Nissa observations do not mutate host gradients or training state.
- Germination context is measured without the contribution being diagnosed or replaced.
- Narset and Momir receive the same `observation_id`, not separately interpreted records.
- Every derived signal includes provenance and normalisation semantics.
- Task-specific information is included only when the experiment permits it.
- Nissa does not infer an editorial conclusion for either consumer.

#### Forbidden authority

Nissa must not emit:

- `should_grow`;
- `deficit_type` as a prescriptive class;
- `recommended_structure`;
- candidate rankings;
- admission recommendations;
- lifecycle actions;
- or maintenance verdicts.

#### Smell

> If Nissa captions the photograph with the answer it is supposed to prove, observation has become policy.

