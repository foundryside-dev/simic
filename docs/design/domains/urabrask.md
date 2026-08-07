<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: ../00-INDEX.md -->
<!-- hld: source: v4.1 monolith lines 2174–2209 -->
### 13.10 Urabrask — Quality Assurance

#### Responsibilities

- construct blinded, versioned `TestPlan` records;
- verify the compiled artefact against the canonical specification at runtime;
- test reference-output and gradient agreement;
- test zero-influence behaviour;
- test numerical stability and finite gradients;
- request deterministic replay in Tolaria;
- run regression and stress suites;
- measure immediate and multi-horizon task trajectories;
- measure integration shock, gradient shock, latency and spend;
- quantify uncertainty and evidence completeness;
- classify hard defects and soft warnings;
- and produce signed `QualityReport` records.

#### QA modes

**Academy QA** uses full or multi-horizon branch execution for research labels, regression, calibration and curriculum acquisition.

**Field QA** uses a budgeted hierarchy of local checks, learned measurement surrogates and short rollouts, escalating when uncertainty or risk requires it.

#### Invariants

- Urabrask cannot issue `ADMIT`, `REJECT`, `NO_OP` or lifecycle tokens.
- It cannot see candidate source where source could affect testing or interpretation.
- It cannot change the candidate, canonical graph or compiled artefact.
- It reports measurements, defects and uncertainty separately from policy utility.
- A test-plan version and evidence digest accompany every report.
- Mandatory tests cannot be weakened after viewing a candidate’s result.

#### Smell

> If Urabrask issues an admission token, QA has put on the judge’s robes.

