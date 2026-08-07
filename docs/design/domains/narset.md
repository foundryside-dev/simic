<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: ../00-INDEX.md -->
<!-- hld: source: v4.1 monolith lines 1993–2036 -->
### 13.5 Narset — Tactical Controller

#### Responsibilities

- interpret local telemetry only to decide whether work should be commissioned, where it belongs, and what operational class applies;
- choose among wait, commission, maturation, QA, adjudication, blend, hold, abort, commit and escalation actions;
- choose an insertion region permitted by Tamiyo;
- author a narrow `GrowthIntent` inside the strategic envelope;
- manage pre-commit lifecycle timing;
- request Urabrask QA and Augustin adjudication;
- and escalate strategic shortages or conflicts to Tamiyo.

#### Inputs

- Nissa's canonical `TelemetryEnvelope`;
- active Tamiyo envelope;
- Kasmina local lifecycle state and region identifiers;
- Urabrask evidence;
- Augustin decisions;
- aggregate operational history without candidate-family or ancestor instructions;
- and Emrakul notifications where committed structure affects local capacity.

#### Outputs

- `GrowthIntent`;
- pre-commit `LifecycleCommand`;
- QA and adjudication requests;
- strategic escalation;
- and action telemetry.

#### Invariants

- Narset cannot exceed Tamiyo's budget.
- It does not send, copy, caption or rewrite Nissa telemetry for Momir.
- It cannot include a diagnosis, topology family, ancestor choice, rank, width, operator or mechanism hint in `GrowthIntent`.
- It cannot choose a structure that bypasses Momir, Elesh and Tezzeret.
- It cannot override Augustin's no-op or rejection.
- It relinquishes ordinary ownership at commitment.
- It never exposes hidden recurrent state to Momir.

#### Smell

> If Narset tells Momir what the problem “really is” or what kind of answer to produce, the assignments editor has become a co-author.

