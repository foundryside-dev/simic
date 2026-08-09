<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: ../00-INDEX.md -->
[← HLD index](../00-INDEX.md)

<!-- hld: source: v4.1 monolith lines 3143–3245 -->
## 19. Observability and Auditability

Tamiyo exposes the system at three levels.

### 19.1 Live operational view

- current Tolaria training run, device, precision and execution regime;
- current four-axis `ScaffoldState` and gate evidence;
- host loss, optimiser progress and data cursor;
- current Ugin strategic envelope;
- current Nissa observation identity and publication recipients;
- current Aurelia GrowthIntent and resolved GrowthRequest;
- bootstrap ancestry status: supplied, withdrawn or control-only;
- Aurelia’s last action and legal action mask;
- Nissa health summaries;
- active requests and candidate pools;
- Elesh rejection counts and reasons;
- Urabrask compilation state and spend;
- Jin-Gitaxias test-plan progress and QA status;
- Tolaria branch progress and determinism state;
- Isperia no-op margins, verdicts and policy versions;
- Wrenn lifecycle and alpha;
- Emrakul maintenance state;
- and current global resource use.

### 19.2 Investigation view

- complete mainline and branch trees;
- common snapshot and future-sequence identifiers;
- raw, canonical and artefact hashes;
- raw-to-canonical transformations;
- compilation manifests;
- QA tests, defects, warnings and evidence completeness;
- measured versus surrogate-predicted trajectories;
- Isperia eligibility and utility decomposition;
- counterfactual policy sweeps: recorded decisions re-adjudicated under a candidate `adjudication_policy_version`, with decision deltas (retrospective and GPU-free — [`../domains/isperia.md`](../domains/isperia.md#retrospective-policy-re-adjudication));
- lineage and retrieval paths;
- lifecycle transitions;
- and divergence-localisation traces.

### 19.3 Audit bundle

For any intervention, Tamiyo can export:

```text
TrainingRunSpec and Tolaria execution manifest
StrategicEnvelope
TelemetryEnvelope
GrowthIntent
Resolved GrowthRequest
ProposalBatchRequest
BootstrapAncestryContext or explicit null
Raw candidate pool
Elesh reports
Urabrask manifests
Snapshot and determinism manifest
Jin-Gitaxias TestPlan
Tolaria BranchResults
Jin-Gitaxias QualityReport
Isperia AdmissionDecision
Wrenn lifecycle events
Jin-Gitaxias maintenance QualityReports
Isperia MaintenanceDecisions
Emrakul maintenance events
Urborg record references
```

The bundle is sufficient to reconstruct:

- which observation was published;
- why Aurelia commissioned work;
- how the legal request was resolved;
- whether ancestry was supplied or withdrawn;
- what alternatives existed;
- which tests were run;
- what was measured;
- which policy was applied;
- what was spent;
- why no-op did or did not win;
- and how the growth behaved afterward.

### 19.4 Naming-smell view

Tamiyo should surface architecture-smell events such as:

```text
FORBIDDEN_IMPORT_DETECTED
QA_ATTEMPTED_VERDICT
JUDGE_ATTEMPTED_EXECUTION
INFRASTRUCTURE_POLICY_LEAK
SOURCE_BLINDING_BREACH
UI_CONTROL_BACKCHANNEL
NAMESPEC_OWNER_MISMATCH
TELEMETRY_MEDIATION_ATTEMPT
EDITORIAL_ANGLE_IN_GROWTH_INTENT
REQUEST_CHANNEL_COLLUSION
BOOTSTRAP_SCAFFOLD_LEAK
OBSERVATION_IDENTITY_MISMATCH
```

These events do not replace static checks, but they make constitutional violations visible during integration.
