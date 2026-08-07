<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: ../00-INDEX.md -->
<!-- hld: source: v4.1 monolith lines 1820–1862 -->
### 13.1 Leyline — Constitutional Infrastructure

#### Responsibilities

- define every cross-subsystem record;
- define schema versions and compatibility rules;
- define canonical ordering and enum stability;
- define `GrowthIntent`, `GrowthRequest`, `RegionContract` and `GrammarProfile` vocabularies;
- provide the pure deterministic request resolver;
- validate that resolved requests remain inside Tamiyo's envelope and Kasmina's region contract;
- define lifecycle state and transition vocabulary;
- define budget, spend and cost units;
- define determinism, numerical tolerance and evidence-completeness contracts;
- define warrant and decision record formats;
- define event envelopes and provenance fields;
- and provide pure validation functions.

#### Invariants

- Leyline has no dependency on subsystem implementations.
- Schema changes are explicit and versioned.
- Unknown fields fail closed where safety or reproducibility is affected.
- A consumer cannot silently accept a schema it was not trained, compiled or calibrated against.
- Policy *formats* and deterministic compatibility resolution may live in Leyline; case-specific policy *choices* and diagnoses do not.

#### Forbidden authority

Leyline must not:

- choose candidates;
- set a case-specific verdict;
- calculate live reward;
- compile graphs;
- execute a host;
- store experiment history;
- infer a deficit or preferred phenotype;
- select reference ancestry;
- or call agent services.

#### Smell

> If Leyline imports Narset, Augustin, Momir or Kasmina—or if its resolver starts diagnosing the case—the constitution has started governing individual cases.

