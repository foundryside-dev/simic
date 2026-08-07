<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: ../00-INDEX.md -->
<!-- hld: source: v4.1 monolith lines 3246–3505 -->
## 20. Target Codebase Structure

```text
src/simic/
├── leyline/          # Contracts, schemas, versions, grammar profiles, request resolution, warrants
│   ├── contracts.py
│   ├── telemetry.py
│   ├── intent.py
│   ├── requests.py
│   ├── request_resolution.py
│   ├── region_contracts.py
│   ├── grammar_profiles.py
│   ├── lifecycle.py
│   ├── budgets.py
│   ├── evidence.py
│   ├── decisions.py
│   ├── events.py
│   ├── scaffolds.py
│   ├── compatibility.py
│   └── versions.py
├── tolaria/          # Universal host-training and execution substrate
│   ├── engine.py
│   ├── training.py
│   ├── optimizers.py
│   ├── schedulers.py
│   ├── data.py
│   ├── devices.py
│   ├── precision.py
│   ├── distributed.py
│   ├── checkpoints.py
│   ├── snapshots.py
│   ├── restore.py
│   ├── replay.py
│   ├── branching.py
│   ├── futures.py
│   ├── adoption.py
│   ├── profiles.py
│   ├── calibration.py
│   └── determinism.py
├── sarpadia/         # Append-only history, lineage, bootstrap ancestry, retrieval and datasets
│   ├── records.py
│   ├── store.py
│   ├── lineage.py
│   ├── equivalence.py
│   ├── blinding.py
│   ├── retrieval.py
│   ├── reference_population.py
│   ├── ancestry_context.py
│   ├── withdrawal.py
│   ├── splits.py
│   └── datasets.py
├── tamiyo/           # Strategic controller and long-horizon allocation
│   ├── allocator.py
│   ├── envelopes.py
│   ├── regional_state.py
│   ├── constraints.py
│   └── training.py
├── narset/           # Tactical commissioning and pre-commit lifecycle policy
│   ├── controller.py
│   ├── actions.py
│   ├── masks.py
│   ├── intents.py
│   ├── escalation.py
│   └── training.py
├── nissa/            # Ablated host diagnostics and direct telemetry publication
│   ├── observer.py
│   ├── publisher.py
│   ├── activations.py
│   ├── gradients.py
│   ├── spectra.py
│   ├── temporal.py
│   ├── provenance.py
│   └── normalization.py
├── momir/            # Raw candidate design, mutation and recombination
│   ├── generator.py
│   ├── conditioning.py
│   ├── grammar_client.py
│   ├── latent.py
│   ├── mutation.py
│   ├── recombination.py
│   ├── ancestry_dropout.py
│   └── training.py
├── elesh/            # Static structural verification and canonicalisation
│   ├── verifier.py
│   ├── shape_inference.py
│   ├── gradients.py
│   ├── zero_influence.py
│   ├── canonicalizer.py
│   ├── equivalence.py
│   └── reports.py
├── tezzeret/         # Lowering, fusion, compilation and artefact manifests
│   ├── lowering.py
│   ├── fusion.py
│   ├── layouts.py
│   ├── compiler.py
│   ├── costs.py
│   └── manifests.py
├── urabrask/         # Dynamic QA and evidence certification
│   ├── plans.py
│   ├── runtime_conformance.py
│   ├── numerical.py
│   ├── gradients.py
│   ├── trajectories.py
│   ├── regression.py
│   ├── uncertainty.py
│   ├── reports.py
│   └── surrogate.py
├── augustin/         # Independent adjudication and warrants
│   ├── policy.py
│   ├── eligibility.py
│   ├── utility.py
│   ├── no_op.py
│   ├── admission.py
│   ├── maintenance.py
│   ├── calibration.py
│   └── warrants.py
├── kasmina/          # Host model, insertion regions, slots and lifecycle
│   ├── host.py
│   ├── regions.py
│   ├── region_contracts.py
│   ├── slots.py
│   ├── lifecycle.py
│   ├── maturation.py
│   └── ablation.py
├── emrakul/          # Post-commit maintenance, sedation, decay and lysis
│   ├── policy.py
│   ├── review.py
│   ├── sedation.py
│   ├── decay.py
│   ├── lysis.py
│   └── training.py
├── oona/             # Event projections, flight recorder and UI adapters
│   ├── bus.py
│   ├── recorder.py
│   ├── projections.py
│   ├── newsroom_view.py
│   ├── sanctum.py
│   ├── overwatch.py
│   └── audit.py
├── controls/         # Research-only candidates and policy controls
│   ├── no_op.py
│   ├── reference_norm.py
│   ├── reference_attention.py
│   ├── reference_convolution.py
│   ├── reference_low_rank.py
│   ├── reference_gated_residual.py
│   ├── random.py
│   ├── gradient_svd.py
│   ├── least_squares.py
│   ├── online_optimised.py
│   └── oracle.py
├── curriculum/
│   ├── momir_bootstrap/
│   ├── narset_acquisition/
│   ├── scaffold_withdrawal/
│   └── manifests/
├── benchmarks/
├── experiments/
├── analysis/
└── scripts/

tests/
├── namespec/
├── contracts/
├── observation_routing/
├── request_resolution/
├── bootstrap_withdrawal/
├── scaffold_withdrawal/
├── unit/
├── integration/
├── training/
├── determinism/
├── counterfactual/
├── authority/
├── blinding/
└── end_to_end/
```

### 20.1 Package README rule

Every package README begins with:

```text
Plain-English role:
Narrative verb or infrastructure context:
Newsroom analogue, where useful:
Owns:
Does not own:
Consumes:
Produces:
Forbidden imports:
Canonical smell:
```

This preserves discoverability while retaining the deliberately opaque internal names.

### 20.2 Dependency direction

The preferred authority and evidence flow is:

```text
                                 tamiyo
                                    │ StrategicEnvelope
                                    ▼
nissa ──────────► narset ─────► GrowthIntent
   │                                │
   │ same TelemetryEnvelope         ▼
   └────────────► momir ◄──── resolved GrowthRequest
                       ▲             ▲
                       │             │
              optional ancestry   leyline resolver
               from sarpadia       + kasmina RegionContract
                       │
                       ▼
                    elesh ──► tezzeret ──► urabrask
                                               │
                                           TestPlan
                                               ▼
                                            tolaria
                                               │
                                          BranchResults
                                               ▼
                                            urabrask
                                               │
                                          QualityReport
                                               ▼
                                            augustin
                                               │
                                      decision / warrant
                                      ┌────────┴────────┐
                                      ▼                 ▼
                                   kasmina           emrakul
```

Neutral infrastructure is available across this flow:

```text
all domains → Leyline contracts
agents → Tolaria execution protocols where required
agents → Sarpadia storage/retrieval protocols where required
all domains → Oona events only; decision-critical code never imports Oona
```

### 20.3 Prohibited dependency examples

```text
tolaria importing augustin.policy                 prohibited
urabrask importing augustin.admission              prohibited
augustin importing tolaria.engine                  prohibited
sarpadia importing momir.training                  prohibited
leyline importing any agent implementation         prohibited
oona imported by training-critical code            prohibited
narset importing momir grammar or generator         prohibited
momir importing narset controller or hidden state   prohibited
narset constructing TelemetryEnvelope for Momir     prohibited
kasmina importing reference blueprint catalogue     prohibited
```

Integration occurs through Leyline records and protocols, not circular implementation imports.

<!-- hld: source: v4.1 monolith lines 4252–4272 -->
## 30. Repository Handoff and Custody

This document is the authoritative target HLD for repository implementation. Namespec 1.0, the authority boundaries, the newsroom routing rule, the no-op requirement, and the Scaffold Withdrawal Principle are constitutional constraints. They may be changed only through an architecture decision record that names the displaced invariant and its replacement.

Codex or any other implementation agent may stage, simplify or defer unbuilt capabilities, but it must not represent a target capability as implemented, collapse two named authorities for convenience without an explicit adapter boundary, or silently turn an Academy scaffold into a permanent production assumption.

The first repository milestones should:

1. commit this HLD and an ADR locking Namespec 1.0;
2. create the package skeleton and forbidden-import checks;
3. define Leyline contracts, including `ScaffoldManifest` and `ScaffoldState`;
4. place ordinary host training behind Tolaria's Academy profile;
5. establish the exact replay and divergence-localisation harness;
6. preserve legacy stock blueprints only as Sarpadian bootstrap references and research controls;
7. implement each subsequent phase against explicit acceptance tests in §21;
8. record every deviation, approximation and unimplemented target in the repository status map.

The handoff rule is:

> **Implement the architecture incrementally, but preserve the evidence and authority boundaries from the first commit.**

