<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: ../00-INDEX.md -->
[← HLD index](../00-INDEX.md)

<!-- hld: source: v4.1 monolith lines 1953–1992 -->
### 13.4 Ugin — Strategic Controller

#### Responsibilities

- allocate parameter, compute, latency and churn budgets across regions;
- set maximum concurrent growth;
- establish global and regional cooldowns;
- balance exploitation and exploration allowances;
- set long-horizon priorities and risk ceilings;
- coordinate multiple Aurelia-controlled regions or cells;
- react to persistent trends rather than individual noisy steps;
- and emit versioned `StrategicEnvelope` records.

#### Inputs

- coarse Nissa summaries;
- Urborg history and regional performance;
- current host capacity and committed growth;
- aggregate Isperia and Emrakul outcomes;
- strategic task objectives;
- and global resource availability.

#### Outputs

- `StrategicEnvelope`;
- allocation updates;
- embargoes or emergency restrictions;
- and strategic-review requests.

#### Invariants

- Ugin operates on a slower cadence than Aurelia.
- It cannot name a candidate, graph node, kernel or blend tick.
- It cannot directly mutate alpha or issue a local lifecycle transition.
- All local resource use is traceable to an active envelope.

#### Smell

> If Ugin chooses the next candidate or alpha increment, strategy has collapsed into micromanagement.
