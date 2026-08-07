<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: ../00-INDEX.md -->
[← HLD index](../00-INDEX.md)

<!-- hld: source: v4.1 monolith lines 2358–2396 -->
### 13.14 Oona — Witness and Operator Surface

#### Responsibilities

- consume `EventEnvelope` streams;
- maintain append-only flight-recorder storage;
- build materialised views and projections;
- power operator terminal consoles and mission-control-style dashboards;
- expose training runs, branch trees, lineages, budgets, QA and adjudication;
- generate audit bundles;
- alert on invariant breaches;
- and support replay navigation.

#### Internal separation

Oona may contain distinct internal packages for:

- event transport adapters;
- durable flight-recorder storage;
- projection builders;
- TUI adapters;
- dashboard adapters;
- and report generation.

Leyline owns event schemas. Producers own the truth of their events. Oona owns presentation and projection.

#### Invariants

- Training behaviour is unchanged when Oona is disconnected.
- Operator commands, if later introduced, pass through explicit APIs owned by the relevant authority.
- Missing UI data fails visibly rather than silently fabricating a default.
- Oona cannot mutate Tolaria, Kasmina, Narset, Tamiyo or Augustin state through a presentation backchannel.

#### Smell

> If changing a dashboard changes the training trace, the witness has become a participant.
