<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: 00-INDEX.md -->
[← HLD index](00-INDEX.md)

<!-- hld: source: v4.1 monolith lines 724–1300 -->
## 9. Core Contracts

Subsystem boundaries are enforced with typed, immutable or append-only records. Shared mutable objects are not passed across authority boundaries. The observation, commission, design constraints, proposal multiplicity, and optional ancestry context remain distinct records so none can become an undocumented side channel for another.

### 9.1 `StrategicEnvelope`

Issued by Tamiyo and consumed by Narset, the request resolver, Augustin, Kasmina and Emrakul.

```text
StrategicEnvelope
    envelope_id
    issued_at_step
    valid_from_step
    valid_until_step
    host_scope
    region_allocations[]
        region_id
        parameter_budget
        compute_budget
        latency_budget
        max_concurrent_growths
        max_interventions
        cooldown
        exploration_allowance
        risk_ceiling
        preferred_horizon
    global_parameter_ceiling
    global_compute_ceiling
    global_churn_ceiling
    priority_weights
    admissibility_policy_id
    maintenance_policy_id
    permitted_grammar_profiles[]
    policy_version
    schema_version
```

The envelope grants permission and constrains judgement. It does not instruct Narset to act or Augustin which candidate to select.

### 9.2 `TelemetryEnvelope`

Produced once by Nissa for a particular observation and published independently to Tamiyo, Narset, Momir, Sarpadia and Oona according to access policy.

```text
TelemetryEnvelope
    observation_id
    telemetry_id
    host_state_id
    snapshot_id
    logical_step
    region_id
    ablated_context
    task_metrics
    activation_statistics
    spectral_statistics
    local_functional_gradient
    optimisation_velocity
    lifecycle_context
    budget_context
    temporal_context
    validity_mask
    provenance
    normalization_manifest
    schema_version
```

Any change in meaning, width, basis, normalisation or provenance creates a new schema version. Nissa may normalise and align measurements, but the record contains no `should_grow`, deficit diagnosis, topology suggestion, ancestor choice, or recommended mechanism.

The same `observation_id` must be referenced by Narset's intent, Momir's conditioning input, and the Tolaria snapshot later used for counterfactual evaluation. A mismatch fails closed.

`observation_id` and `telemetry_id` are distinct on purpose: `observation_id` names the canonical observation identity that binds downstream records (INV-08); `telemetry_id` names this envelope record instance for storage and audit. Independent publications and permitted per-consumer projections of one observation share `observation_id` but carry distinct `telemetry_id`s.

### 9.3 `GrowthIntent`

Authored by Narset under an active `StrategicEnvelope`. This is the **assignment brief**, not the design brief.

```text
GrowthIntent
    intent_id
    envelope_id
    observation_id
    host_state_id
    insertion_region_id
    requested_resource_class
    maturity_mode
    assurance_class
    urgency_class
    tactical_deadline
    escalation_context | null
    reason_code
    schema_version
```

Permitted fields describe scope, authority and operational conditions. The contract explicitly forbids:

```text
preferred_topology_family
preferred_operator
suggested_envelope
suggested_ancestor
rank_hint
width_hint
deficit_type
recommended_mechanism
expected_internal_structure
free_form_designer_message
```

Narset does not copy, summarise, annotate or forward telemetry inside the intent.

### 9.4 `GrowthRequest`

Resolved deterministically under Leyline from the `GrowthIntent`, active `StrategicEnvelope`, Kasmina `RegionContract`, and compatible `GrammarProfile`. Narset does not author the resolved fields.

```text
GrowthRequest
    request_id
    intent_id
    envelope_id
    observation_id
    host_state_id
    insertion_region_id
    input_output_contract
    grammar_profile_id
    grammar_version
    exact_parameter_budget
    construction_compute_budget
    compilation_budget
    qa_budget
    latency_budget
    maturity_mode
    maturity_budget
    permitted_blend_policy_class
    permitted_evaluation_horizons[]
    assurance_class
    adjudication_policy_id
    region_contract_version
    resolver_version
    schema_version
```

A request states what may legally be designed and spent. It does not contain an interpreted diagnosis, a fixed blueprint identity, a retrieval choice, or an ancestry selection. The resolver may narrow an intent to satisfy compatibility; it cannot invent a more permissive request.

### 9.5 `ProposalBatchRequest`

Execution metadata controlling how many proposals are requested and how generation spend is accounted. It is kept separate from Momir's semantic conditioning wherever possible.

```text
ProposalBatchRequest
    proposal_batch_id
    request_id
    candidate_count
    latent_sampling_policy
    generation_budget
    diversity_requirement | null
    deadline
    schema_version
```

Candidate count is not a design hint. Momir's candidate-generation function should be invariant to irrelevant batch representation and should not receive “candidate 3 of 12” unless an experiment explicitly studies coordinated set generation.

### 9.6 `BootstrapAncestryContext`

An optional, temporary curriculum record assembled from Sarpadia by the curriculum harness. Narset never selects or transmits it.

```text
BootstrapAncestryContext
    ancestry_context_id
    request_id
    reference_population_version
    compatible_ancestor_ids[]
    ancestor_canonical_specs[]
    ancestor_outcome_summaries[]
    permitted_mutation_radius
    recombination_allowed
    de_novo_fraction
    curriculum_stage
    withdrawal_schedule_id
    provenance
    schema_version
```

The context may contain conventional Norm, Attention, Convolution, low-rank, gated-residual, or other known viable microcells represented as canonical graphs. It is a removable training scaffold. Production inference must support `BootstrapAncestryContext = null`. Reference seeds may remain in the blinded control pool even after they are withdrawn from Momir's input.

### 9.7 `RawGrowthGraph`

Produced by Momir.

```text
RawGrowthGraph
    raw_candidate_id
    request_id
    raw_graph_ir
    raw_birth_parameters
    trainability_intent
    parent_lineages[]
    retrieval_provenance[]
    generator_version
    latent_code
    proposal_probability_or_score
    estimated_uncertainty
    generation_spend
```

A raw graph is not executable and not trusted.

### 9.8 `CanonicalGrowthSpec`

Produced by Elesh.

```text
CanonicalGrowthSpec
    canonical_candidate_id
    raw_candidate_id
    request_id
    canonical_graph_ir
    canonical_parameters
    input_output_contract
    trainability_mask
    zero_influence_proof
    gradient_flow_manifest
    parameter_count
    static_compute_estimate
    memory_estimate
    canonical_semantic_hash
    equivalence_class_id
    structural_pruning_report
    verification_report
    grammar_version
    canonicalizer_version
```

The canonical semantic hash identifies developmental meaning independently of compilation strategy.

### 9.9 `ExecutableGrowthArtifact`

Produced by Tezzeret.

```text
ExecutableGrowthArtifact
    artifact_id
    canonical_candidate_id
    canonical_semantic_hash
    device_target
    dtype
    compiled_module_or_graph
    kernel_manifest
    fusion_manifest
    runtime_parameter_layout
    runtime_cost_estimate
    compiler_version
    compilation_spend
    reproducibility_manifest
```

The artefact is not trusted merely because compilation succeeded. Urabrask must dynamically verify it against the canonical specification.

### 9.10 `TrainingRunSpec`

Defined under Leyline and executed by Tolaria.

```text
TrainingRunSpec
    run_id
    host_definition_reference
    task_and_data_definition
    host_optimizer_definition
    scheduler_definition
    device_topology
    dtype_and_precision_policy
    distributed_policy
    determinism_policy
    execution_regime
    calibration_profile_id | null
    scaffold_state_id
    checkpoint_policy
    decision_cadences
    maximum_steps
    random_seed_manifest
    code_and_schema_versions
```

The same execution semantics are used for the live trajectory and paired branches unless a difference is the declared experimental variable.

### 9.11 `Snapshot`

Produced by Tolaria.

```text
Snapshot
    snapshot_id
    run_id
    host_parameters
    host_optimizer_state
    host_scheduler_state
    growth_slot_states
    lifecycle_state
    economy_state
    narset_recurrent_state
    tamiyo_state_reference
    telemetry_history
    random_number_states
    dataloader_cursor
    task_configuration
    recent_batches
    fixed_future_minibatch_sequence
    device_and_determinism_manifest
    execution_regime
    scaffold_state_id
    code_and_schema_versions
```

A snapshot is complete only when it captures enough state to satisfy the Academy-exact replay contract on the supported reference profile. The same snapshot representation may be used in calibrated-stochastic and Field regimes, where repeated outcomes carry measured uncertainty rather than a false claim of bitwise identity.

### 9.12 `TestPlan`

Produced by Urabrask and consumed by Tolaria.

```text
TestPlan
    test_plan_id
    snapshot_id
    request_id
    blinded_candidate_artifacts[]
    mandatory_no_op
    control_artifacts[]
    construction_support_split
    qa_screen_split
    qa_audit_split
    retention_report_split
    future_sequence_id
    horizons[]
    required_runtime_checks[]
    required_regression_checks[]
    per_branch_budget
    required_execution_regime
    calibration_profile_id | null
    escalation_policy
    determinism_manifest
    scaffold_state_id
    qa_policy_version
```

Urabrask controls what evidence must be collected. It does not control the adjudication utility applied later.

### 9.13 `BranchResult`

Produced by Tolaria.

```text
BranchResult
    test_plan_id
    branch_id
    blinded_candidate_id
    canonical_semantic_hash
    execution_status
    execution_regime
    calibration_profile_id | null
    replicate_group_id | null
    loss_trajectory
    accuracy_trajectory
    activation_trajectory
    gradient_trajectory
    runtime_conformance_measurements
    short_horizon_effect
    long_horizon_effect
    integration_shock
    gradient_shock
    parameter_cost
    measured_compute_spend
    measured_latency
    stability_events
    lifecycle_events
    final_state_reference
    execution_uncertainty
    scaffold_state_id
    replay_digest
```

Source provenance is held outside the blinded view and reattached only after QA and adjudication.

### 9.14 `QualityReport`

Produced by Urabrask and consumed by Augustin, Sarpadia, Narset and Emrakul.

```text
QualityReport
    quality_report_id
    test_plan_id
    request_id
    execution_regime
    calibration_profile_id | null
    academy_reference_report_ids[]
    scaffold_state_id
    candidate_reports[]
        blinded_candidate_id
        canonical_semantic_hash
        structural_reference_valid
        compiled_semantics_conformant
        runtime_valid
        deterministic_replay_valid
        finite_outputs_and_gradients
        regression_results
        measured_task_trajectories
        measured_costs
        measured_shock
        uncertainty
        academy_comparison | null
        escalation_required
        hard_defects[]
        soft_warnings[]
    no_op_report
    evidence_completeness
    qa_spend
    qa_policy_version
    evidence_digest
```

A `QualityReport` establishes facts and test status. It does not contain `ADMIT` or `REJECT`.

### 9.15 `AdmissionDecision`

Produced by Augustin.

```text
AdmissionDecision
    decision_id
    quality_report_id
    request_id
    verdict                 # ADMIT | NO_OP | REJECT | DEFER | REQUIRE_RETEST
    selected_candidate_id | null
    selected_semantic_hash | null
    eligibility_results
    tail_veto_results       # per candidate: tail estimate, threshold in force,
                            # snapshot distance, margin, pass | veto (ADR-0004)
    no_op_margin
    adjudicated_utility
    cost_breakdown
    risk_charge
    uncertainty_charge
    decision_reasons[]
    admission_warrant | null
    adjudication_policy_version
```

An admission warrant is required before Kasmina may raise a new growth above zero influence.

### 9.16 `MaintenanceDecision`

Produced by Augustin from a maintenance `QualityReport`.

```text
MaintenanceDecision
    decision_id
    quality_report_id
    target_growth_id
    verdict                 # RETAIN | RETEST | SEDATE | DECAY | LYSE
    retained_utility
    replacement_context
    cost_breakdown
    decision_reasons[]
    maintenance_warrant | null
    adjudication_policy_version
```

Emrakul decides how to execute an authorised safe transition. It does not rewrite the verdict.

### 9.17 `LifecycleCommand`

Issued by Narset before commitment or Emrakul after commitment.

```text
LifecycleCommand
    command_id
    authority               # NARSET or EMRAKUL
    target_growth_id
    requested_transition
    admission_warrant | null
    maintenance_warrant | null
    evidence_reference
    strategic_envelope_id
    budget
    reason
```

Kasmina validates the command against authority, state, warrant, budget and transition rules.

### 9.18 `GrowthRecord`

Stored by Sarpadia.

```text
GrowthRecord
    base_host_trajectory_id
    snapshot_id
    telemetry
    strategic_envelope
    growth_intent
    growth_request
    proposal_batch_request
    scaffold_state
    bootstrap_ancestry_context | null
    raw_growth_graph
    canonical_growth_spec
    executable_artifact_manifest
    test_plan
    branch_results[]
    quality_report
    admission_decision
    selected_or_rejected
    rejection_reason
    maturation_history
    blend_history
    retained_contribution
    maintenance_decisions[]
    maintenance_history
    terminal_outcome
    failure_mode
    lineage_edges
    split_membership
```

The full candidate pool is stored, including stock-reference controls, structurally rejected candidates, scaffold-free de novo pools, and pools in which Augustin selects no-op.

### 9.19 `EventEnvelope`

Defined by Leyline and published by every subsystem for Oona.

```text
EventEnvelope
    event_id
    event_type
    producer
    host_state_id
    correlation_id
    causal_parent_ids[]
    logical_step
    payload_schema_version
    payload
    integrity_digest
```

Oona consumes these events but does not define their source-of-truth semantics.

### 9.20 `ScaffoldManifest` and `ScaffoldState`

Defined by Leyline and included in every curriculum and confirmatory run manifest.

```text
ScaffoldManifest
    scaffold_id
    protected_failure_mode
    constrained_regime
    relaxation_regimes[]
    withdrawal_gate
    gate_owner
    retained_reference_role
    escalation_path
    interaction_risks[]
    version

ScaffoldState
    state_id
    execution_regime
        ACADEMY_EXACT | CALIBRATED_STOCHASTIC | FIELD
    host_distribution_regime
        REPEATED_ACQUISITION | HELD_OUT_IN_FAMILY | OPEN_DISTRIBUTION
    design_prior_regime
        REFERENCE_ANCESTRY | ANCESTRY_DROPOUT | NULL_ANCESTRY
    active_scaffold_ids[]
    passed_gate_evidence_ids[]
    retained_reference_capabilities[]
    interaction_experiment_id | null
    policy_version
    provenance
```

The three regime fields are independent axes, not aliases for one global curriculum stage. A transition that changes more than one axis must carry an explicit interaction experiment identifier and cite the completed single-axis controls. The run fails closed when its declared scaffold state cannot be reconciled with the active Tolaria profile, host split, or Momir ancestry context.
