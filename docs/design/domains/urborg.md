<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: ../00-INDEX.md -->
[← HLD index](../00-INDEX.md)

<!-- hld: source: v4.1 monolith lines 1917–1952 -->
### 13.3 Urborg — Historical Infrastructure

#### Responsibilities

- retain append-only records of observations, intents, resolved requests, candidate pools, QA evidence, decisions and lifecycle outcomes;
- maintain raw, canonical and artefact identities and lineage edges;
- hold the versioned bootstrap reference population and its curriculum manifests;
- assemble `BootstrapAncestryContext` only for authorised curriculum stages;
- provide ordinary retrieval and similarity indices without deploying results;
- preserve structural rejects, compilation failures, QA defects, no-op victories and withdrawals;
- enforce base-trajectory grouped splits;
- and expose blinded, provenance-safe views to Momir, Jin-Gitaxias, Isperia and analysis.

#### Retrieval modes

- nearest compatible canonical genotype;
- nearest functional effect;
- nearest host diagnostic context;
- parent and descendant lineage;
- failed-neighbour retrieval;
- reference-population ancestry;
- and sealed control retrieval for evaluation.

#### Invariants

- Urborg never mutates the live host.
- A retrieval result is precedent, not a verdict.
- Failed and withdrawn records are first-class history.
- Bootstrap ancestry is versioned and removable from production inference.
- Aurelia cannot select an ancestor through Urborg.
- Branches from one base trajectory remain in one statistical split.

#### Smell

> If Urborg forgets the dead, history has become propaganda. If it installs a precedent, history has started governing the present.

---

<!-- hld: source: v4.1 monolith lines 2530–2652 -->
### 15. Urborg Data Model and Learning Use

Urborg is both an operational archive and a research data factory.

#### 15.1 Required records

For every case it stores:

- complete Tolaria run and snapshot provenance;
- Ugin envelope;
- Aurelia request and action context;
- Nissa telemetry;
- every raw Momir graph;
- every Elesh rejection and canonicalisation report;
- every Urabrask artefact manifest;
- every Jin-Gitaxias test plan and quality report;
- every Tolaria branch trace;
- every Isperia admission or maintenance decision;
- Wrenn embodiment state;
- maturation and blend history;
- Emrakul maintenance history;
- near-miss records — thin-margin veto passes joined to large uncontained post-commit shock (`isperia.md`);
- and final outcome.

#### 15.2 Blinded views

Urborg maintains a privileged provenance map and produces separate blinded views:

```text
qa_view
    blinded candidate IDs
    no source labels
    canonical and artefact references
    allowed test metadata

adjudication_view
    quality reports
    no source labels
    active envelope and policy references

research_view
    source labels reattached
    complete lineage and experimental metadata
```

Blinding is a data product, not a promise that consumers will ignore a field.

#### 15.3 Failure taxonomy

Failures are classified rather than collapsed into generic rejection:

```text
STRUCTURAL_INVALID
CONTRACT_MISMATCH
ZERO_INFLUENCE_FAILURE
GRADIENT_FLOW_FAILURE
STATIC_BUDGET_EXCEEDED
COMPILATION_FAILURE
QA_SEMANTIC_CONFORMANCE_FAILURE
QA_RUNTIME_FAILURE
QA_NUMERICAL_FAILURE
QA_DETERMINISM_FAILURE
QA_REGRESSION_FAILURE
QA_EVIDENCE_INCOMPLETE
ADJUDICATION_INELIGIBLE
ADJUDICATION_NO_OP
ADJUDICATION_BUDGET_REJECT
ADJUDICATION_RISK_REJECT
ADJUDICATION_UNCERTAINTY_RETEST
MATURED_STALE
INTEGRATION_SHOCK
CONTAINMENT_CATASTROPHE
HOLDING_FAILURE
CONTINUED_TENANCY_FAILURE
HOST_DEPENDENCE_ONLY
LONG_HORIZON_REGRESSION
SEDATED_REDUNDANT
LYSED_OBSOLETE
BUDGET_OVERRUN
BRANCH_TRANSPLANT_VIOLATION
```

`INTEGRATION_SHOCK` and `CONTAINMENT_CATASTROPHE` never share a code: one is a cost, the other is a veto failure (INV-28, ADR-0010).


#### 15.4 Reference ancestry and scaffold status

Every bootstrap record distinguishes:

```text
reference supplied to Momir as ancestry
reference present only as a blinded control
candidate descended from a named parent
candidate generated with no supplied ancestry
```

This prevents a de novo result from being credited to a hidden reference dependency and allows three separate evaluations:

1. Momir with ancestry versus its direct parents;
2. Momir without ancestry versus the same reference controls;
3. Momir without ancestry and with stock-derived lineages excluded from the selected candidate.

The `withdrawal_schedule_id` and `curriculum_stage` are part of record provenance. A production result is not “scaffold free” unless the ancestry context is null at proposal time.

#### 15.5 Retrieval

Retrieval returns evidence and candidate material, not an automatic deployment decision. Every retrieved growth must:

- satisfy current Leyline versions;
- pass Elesh compatibility and canonicalisation;
- compile through Urabrask;
- pass Jin-Gitaxias QA;
- and compete under Isperia against no-op and fresh candidates.

<!-- hld: post-monolith addition (2026-08-08) — future direction, non-binding -->
##### Future direction (non-binding): contextual retrieval over the precedent store

As the precedent store grows beyond the fixed bootstrap population, the
similarity indices behind the retrieval modes above may benefit from
*contextual retrieval*: prepending a short, generated context prefix to each
stored record fragment before embedding, combined with hybrid lexical
(BM25-style) and embedding search plus reranking. Anthropic reported ~49%
fewer retrieval failures with the hybrid form and ~67% with reranking
(["Introducing Contextual Retrieval"](https://www.anthropic.com/news/contextual-retrieval),
Sep 2024), measured on codebase-like corpora — close in character to
canonical genotypes and QA evidence. This is an implementation note for
Urborg's index layer only. It binds nothing: it changes no contract, no
blinded view, no invariant, and no retrieval-mode semantics — a retrieval
result remains precedent, not a verdict, however the index is built.

#### 15.6 Training consumers

- **Momir** consumes successful, failed and contrasting candidate sets.
- **Aurelia** consumes action trajectories and regret labels.
- **Ugin** consumes regional allocation outcomes over long horizons.
- **Jin-Gitaxias’s field surrogate** consumes Academy measurements and evidence-completeness labels.
- **Isperia** may be calibrated or later trained from adjudication cases, but the initial policy is explicit and rule-driven.
- **Emrakul** consumes maintenance, re-adaptation and safe-decay outcomes.

No consumer treats multiple branches from one base trajectory as independent validation or test examples.
