<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: ../00-INDEX.md -->
[← HLD index](../00-INDEX.md)

<!-- hld: source: v4.1 monolith lines 2322–2357 -->
### 13.13 Emrakul — Maintenance and Destruction

#### Responsibilities

- monitor committed growth over long horizons;
- schedule or request periodic continued-tenancy QA;
- detect suspected decline, redundancy or replacement pressure;
- execute warranted alpha reduction or sedation;
- initiate safe gradual decay;
- lyse obsolete structures;
- consolidate capacity where separately authorised;
- and return recycled capacity to Tamiyo’s strategic view.

#### Inputs

- Urabrask maintenance `QualityReport`;
- Augustin `MaintenanceDecision`;
- Tolaria maintenance execution;
- Kasmina lifecycle and alpha state;
- Nissa long-horizon telemetry;
- Tamiyo strategic budgets;
- and Sarpadia lineage and historical outcomes.

#### Invariants

- Emrakul acts only on committed or explicitly handed-off growth.
- It does not construct replacements.
- It does not decide continued-tenancy utility.
- It does not alter Urabrask test policy or Augustin adjudication policy.
- Sedation precedes lysis where safety permits.
- A lysis event is emitted once on a real transition.

#### Smell

> If Emrakul decides which unborn candidate should be admitted, destruction has leaked into birth.
