<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: ../00-INDEX.md -->
[← HLD index](../00-INDEX.md)

<!-- hld: source: v4.1 monolith lines 1993–2036 -->
### 13.5 Aurelia — Tactical Controller

#### Responsibilities

- interpret local telemetry only to decide whether work should be commissioned, where it belongs, and what operational class applies;
- choose among wait, commission, maturation, QA, adjudication, blend, hold, abort, commit and escalation actions;
- choose an insertion region permitted by Ugin;
- author a narrow `GrowthIntent` inside the strategic envelope;
- manage pre-commit lifecycle timing;
- request Jin-Gitaxias QA and Isperia adjudication;
- and escalate strategic shortages or conflicts to Ugin.

#### Inputs

- Nissa's canonical `TelemetryEnvelope`;
- active Ugin envelope;
- Wrenn local lifecycle state and region identifiers;
- Jin-Gitaxias evidence;
- Isperia decisions;
- aggregate operational history without candidate-family or ancestor instructions;
- and Emrakul notifications where committed structure affects local capacity.

#### Outputs

- `GrowthIntent`;
- pre-commit `LifecycleCommand`;
- QA and adjudication requests;
- strategic escalation;
- and action telemetry.

#### Invariants

- Aurelia cannot exceed Ugin's budget.
- It does not send, copy, caption or rewrite Nissa telemetry for Momir.
- It cannot include a diagnosis, topology family, ancestor choice, rank, width, operator or mechanism hint in `GrowthIntent`.
- It cannot choose a structure that bypasses Momir, Elesh and Urabrask.
- It cannot override Isperia's no-op or rejection.
- It relinquishes ordinary ownership at commitment.
- It never exposes hidden recurrent state to Momir.

#### Smell

> If Aurelia tells Momir what the problem “really is” or what kind of answer to produce, the assignments editor has become a co-author.
