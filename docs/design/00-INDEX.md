# Simic HLD — Index

**Architecture version:** 4.1 · **Namespec:** 2.0 — locked (ADR-0008) · **Status:** canonical
design authority (decomposed from the v4.1 monolith per [ADR-0001](../adr/0001-hld-decomposition-structure.md);
the monolith is archived, content-identical, at
[`../concept/archive/simic-v4.1-monolith.md`](../concept/archive/simic-v4.1-monolith.md)).

Where the HLD's custody language says "this document" (the §30 handoff
declaration in `ops/repo-structure.md`), it means the HLD as a whole — this
chapter set — not the single chapter that happens to carry it.

Every chapter is standalone. Load `02-constitution.md` in every working session;
load the chapters your task names; do not load the rest.

## Chapter map

| File | Contents |
|---|---|
| `01-claim.md` | The scientific claim and its falsifiers (exec summary, problem, goals, non-goals, success criteria, final statement) |
| `02-constitution.md` | **Always load.** Naming constitution, the 45 constitutional invariants (INV-01..INV-45), one-line namespec invariants |
| `03-principles.md` | Design principles and the architectural smell catalogue |
| `04-architecture.md` | Planes, subsystem map, end-to-end operating flow |
| `05-leyline-contracts.md` | All core contract shapes (`StrategicEnvelope` … `ScaffoldManifest`) |
| `06-growth-model.md` | Growth levels, candidate identity, lifecycle FSM and transition authority |
| `07-counterfactual-engine.md` | Branch pools, Academy/Field QA, no-op anchoring, blindness, statistical unit |
| `domains/README.md` | The §13 grouping preamble and navigation to the fourteen domain chapters |
| `domains/<subsystem>.md` | Per-domain specification (responsibilities, invariants, smells); `urborg.md` also carries the data model |
| `programme/curriculum.md` | Static-to-counterfactual curriculum, scaffold withdrawal stages |
| `programme/learning.md` | Learning responsibilities per subsystem |
| `programme/evaluation.md` | Testing strategy and evaluation framework |
| `programme/phases.md` | Minimum Viable System and implementation phases A–K |
| `programme/risks-and-open-decisions.md` | Risk table and open design decisions |
| `ops/observability.md` | Live/investigation/audit views and the naming-smell view |
| `ops/repo-structure.md` | Target codebase layout, dependency direction, repository handoff |
| `ops/migration.md` | Current-to-target migration |
| `appendices/` | Newsroom rendering (alternative lens), scaffold-withdrawal pattern, glossary, good/bad sentences |
| `TEMPLATE-lld.md` | Header template for Tier 2 LLDs; LLDs land just-in-time under `lld/` (reserved, empty until Phase A) |

## Reading paths

- **Implementing a domain:** `02-constitution.md` + `domains/<it>.md` + `05-leyline-contracts.md` (its contracts) + `programme/learning.md` (its entry).
- **Admission / adjudication work:** `02` + `domains/isperia.md` + `domains/jin-gitaxias.md` + `07-counterfactual-engine.md`.
- **Contract / schema work:** `02` + `05-leyline-contracts.md` + `04-architecture.md` (flow).
- **Experiment / curriculum design:** `02` + `01-claim.md` + `programme/*`.
- **New here:** `01` → `04` → `02`; if the codenames aren't carrying the authority model for you, `appendices/newsroom.md` retells it as a newsroom.

## Citation convention

In new text (issues, ADRs, LLDs, commit messages):

- Invariants: **INV-nn** (numbering as listed in `02-constitution.md`, e.g. INV-05 Academy exact replay).
- Contracts: by **name** (`GrowthIntent`), never by section number.
- Chapters: by **path#anchor** (`domains/isperia.md#admission-utility`).
- Legacy **§-numbers** (v4.1 monolith) remain resolvable via the concordance below — do not use them in new text.

Rationale: v2.0→v4.1 renumbering broke every consumer that cited sections;
names and file anchors survive restructuring, numbers do not.

## Concordance (v4.1 monolith § → chapter file)

| Monolith section | File |
|---|---|
| §1–§4 exec summary, problem, goals, non-goals | `01-claim.md` |
| §5 naming constitution | `02-constitution.md` |
| §6 design principles | `03-principles.md` |
| §7–§8 planes, subsystem map | `04-architecture.md` |
| §9 core contracts | `05-leyline-contracts.md` |
| §10 end-to-end flow | `04-architecture.md` |
| §11–§12 growth model, lifecycle/authority | `06-growth-model.md` |
| §13 preamble | `domains/README.md` |
| §13.1–§13.14 subsystem specs | `domains/<subsystem>.md` |
| §14 counterfactual execution, QA, adjudication | `07-counterfactual-engine.md` |
| §15 Urborg data model | `domains/urborg.md` |
| §16 curriculum and scaffold withdrawal | `programme/curriculum.md` |
| §17 learning responsibilities | `programme/learning.md` |
| §18 constitutional invariants (INV-01..45) | `02-constitution.md` |
| §19 observability | `ops/observability.md` |
| §20 target codebase structure | `ops/repo-structure.md` |
| §21–§22 testing, evaluation | `programme/evaluation.md` |
| §23 migration | `ops/migration.md` |
| §24–§25 MVS, implementation phases | `programme/phases.md` |
| §26–§27 risks, open decisions | `programme/risks-and-open-decisions.md` |
| §28–§29 success criteria, final statement | `01-claim.md` |
| §30 repository handoff | `ops/repo-structure.md` |
| App A smells | `03-principles.md` |
| App B one-line namespec invariants | `02-constitution.md` |
| App C good/bad sentences | `appendices/good-bad-sentences.md` |
| App D glossary | `appendices/glossary.md` |
| App E newsroom principle | `appendices/newsroom.md` |
| App F scaffold withdrawal pattern | `appendices/scaffold-pattern.md` |

## Size discipline

Chapters stay under ~600 lines. A chapter that outgrows the budget is split by
an ADR, never silently. (Largest at decomposition: `05-leyline-contracts.md`,
579 lines — flagged as the first candidate for a by-shape-family split.)
