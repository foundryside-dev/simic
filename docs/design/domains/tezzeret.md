<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: ../00-INDEX.md -->
[← HLD index](../00-INDEX.md)

<!-- hld: source: v4.1 monolith lines 2150–2173 -->
### 13.9 Tezzeret — Compiler

#### Responsibilities

- lower canonical graphs into executable tensor operations;
- select kernels and layouts;
- fuse compatible operations;
- plan memory;
- compile for target hardware and dtype;
- estimate runtime cost;
- report measured compilation spend;
- and emit reproducibility manifests.

#### Invariants

- Tezzeret cannot change canonical semantic identity.
- Every optimisation is traceable in the compilation manifest.
- Compiled artefacts must pass Urabrask runtime QA.
- Compilation failure remains distinct from structural rejection and adjudication rejection.

#### Smell

> If Tezzeret invents a semantic node to improve predicted performance, the compiler has become Momir.
