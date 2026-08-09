<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: ../00-INDEX.md -->
[← HLD index](../00-INDEX.md)

<!-- hld: source: v4.1 monolith lines 2150–2173 -->
### 13.9 Urabrask — Compiler

#### Responsibilities

- lower canonical graphs into executable tensor operations;
- select kernels and layouts;
- fuse compatible operations;
- plan memory;
- compile for target hardware and dtype;
- estimate runtime cost;
- report measured compilation spend;
- and emit reproducibility manifests.

#### Operating modes

Urabrask runs in two modes; both are bound by the same invariants.

1. **On-demand manufacturing.** When Aurelia commissions a growth, Urabrask
   compiles the canonical specification under the declared deadline and
   budget, emitting an `ExecutableGrowthArtifact` and a compilation manifest
   bound to the canonical semantic hash.
2. **Background industrial R&D.** During idle cycles, Urabrask may compile
   canonical backlogs and experiment with kernel fusions, layout plans, and
   device-specific optimisations, reporting production discoveries as
   versioned compiler improvements. It cannot invent new topologies (that is
   Momir's domain) and cannot alter semantic meaning (that is fixed by
   Elesh's canonical identity). It may only discover that *adjusting the
   alloy generates the same screws faster*.

#### Invariants

- Urabrask cannot change canonical semantic identity.
- Every optimisation is traceable in the compilation manifest.
- Compiled artefacts must pass Jin-Gitaxias runtime QA.
- Compilation failure remains distinct from structural rejection and adjudication rejection.

#### Smell

> If Urabrask invents a semantic node to improve predicted performance, the compiler has become Momir.
