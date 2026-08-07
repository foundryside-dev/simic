<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: ../00-INDEX.md -->
[← HLD index](../00-INDEX.md)

<!-- hld: source: v4.1 monolith lines 2118–2149 -->
### 13.8 Elesh — Structural Verifier and Canonicalizer

#### Responsibilities

- validate graph grammar;
- infer and reconcile tensor shapes;
- verify insertion contracts;
- analyse gradient reachability and declared trainability;
- prove zero-influence or function-preserving birth behaviour;
- reject forbidden operations and host references;
- enforce static parameter, memory and graph-complexity ceilings;
- remove dead or semantically redundant structure;
- canonicalise graph ordering and parameter layout;
- identify equivalent graphs;
- assign canonical semantic hashes;
- and produce structural verification reports.

#### Canonicalisation rule

Every Elesh transformation must be semantics-preserving under the declared numerical contract. Structural pruning is permitted only when it removes dead, unreachable, duplicate, identity or otherwise provably equivalent structure.

#### Invariants

- Elesh does not consume task reward or future utility.
- It does not use candidate source as a structural decision feature.
- Canonicalisation occurs before compilation.
- It does not certify dynamic runtime behaviour; that belongs to Urabrask.

#### Smell

> If Elesh rejects a legal candidate because it is predicted to perform poorly, structural orthodoxy has become the government.
