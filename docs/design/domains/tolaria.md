<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: ../00-INDEX.md -->
[← HLD index](../00-INDEX.md)

<!-- hld: source: v4.1 monolith lines 1863–1916 · amended by ADR-0010 (containment detect-and-contain boundary) -->
### 13.2 Tolaria — Training and Execution Infrastructure

#### Responsibilities

- materialise and execute `TrainingRunSpec`;
- run ordinary host forward, backward, optimiser and scheduler steps;
- manage dataloaders, batch ordering and logical time;
- manage devices, dtype, mixed precision and distributed execution;
- capture complete snapshots;
- restore exact state where the active profile requires it;
- materialise common future minibatches;
- execute QA and maintenance branches;
- support deterministic replay, rollback and branch adoption;
- characterise stochastic replay where exactness is deliberately relaxed;
- measure runtime spend, latency, uncertainty and resource use;
- and produce execution, replay and calibration digests.

#### Execution modes

**Mainline mode** runs the live host trajectory.

**Replay mode** restores and reproduces a prior trajectory.

**Branch mode** executes matched counterfactual worlds from a common snapshot.

**Acquisition mode** performs expensive multi-horizon rollouts for curriculum and research labels.

These modes describe *what Tolaria is doing*. An orthogonal execution regime describes the level of determinism and assurance under which it does it:

**Academy-exact regime** is the causal reference and metrology profile. Device, kernels, library and compiler versions, dtype, thread count, random state, optimiser state, dataloader state and future minibatches are pinned. Restore plus common future must produce bitwise-identical traces. This regime is deliberately narrow and may be slower than ordinary operation.

The pinned configuration is a declared **execution-stack identity** (ADR-0013): bitwise identity holds within it and is never a portability claim across stacks. Moving the pin is a recorded re-baselining event — replay fixtures re-run under the candidate stack, acceptance recorded, both identities retained in Urborg provenance. The device class is not the profile: the metrology lab may be hosted on CPU, where exactness is nearly free at MVP host scale, while calibrated-stochastic and Field regimes use the GPUs. Kernel-selection and RNG-stream rules for paired branches across a topology change — the same semantics recompiling to different kernels — are a named Tolaria LLD deliverable.

**Calibrated-stochastic regime** permits bounded nondeterminism while executing repeated matched branches. Tolaria measures the resulting outcome distribution, ranking stability and decision disagreement against Academy-exact results.

**Field regime** permits production-oriented kernels, mixed precision, distributed execution and other validated stochastic behaviour. Field evidence carries execution uncertainty and may be escalated to Academy-exact execution when the candidate margin is too small, risk is high, or calibration has expired.

All modes and regimes use the same host-runtime interface and, wherever possible, the same optimiser and data-path implementation. Exact replay is retained permanently as a reference capability; it is not required to be the permanent factory-floor profile.

#### Invariants

- Tolaria applies no utility weights and issues no verdicts.
- Paired branches differ only in declared interventions and explicitly modelled execution noise.
- Candidate source does not alter execution protocol.
- Restore plus common future is bit-identical under the **Academy-exact** determinism contract.
- Calibrated-stochastic and Field regimes are unavailable until their ranking, decision and tail-error gates pass against Academy-exact evidence.
- Every non-exact `BranchResult` carries execution-regime identity and uncertainty provenance.
- Mainline and branch training semantics are equivalent unless a difference is explicitly part of the experiment.
- A branch-matured candidate is deployed only by adopting the branch or replaying it under the declared validated deployment protocol from the common snapshot.
- Ambiguous or low-margin Field cases can be escalated to Academy-exact execution.
- Execution failures are reported, not interpreted as policy decisions.
- Emergency containment is detect-and-contain only: on a declared safety-invariant breach Tolaria reduces influence mechanically and reports to Isperia; the report is an account of the breach, never an opinion about the candidate (INV-28, ADR-0010).

#### Smell

> If Tolaria “likes,” “rejects,” or “prefers” a candidate, the training substrate has acquired opinions. If Field execution cannot be audited against Academy execution, the factory has thrown away its metrology laboratory.
