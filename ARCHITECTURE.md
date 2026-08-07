# Simic Architecture

A one-page digest of the system shape, for orientation. It is **derived**
from the canonical HLD chapter set under [`docs/design/`](docs/design/00-INDEX.md)
— chiefly [`04-architecture.md`](docs/design/04-architecture.md) and
[`02-constitution.md`](docs/design/02-constitution.md). If this file
disagrees with those chapters, they win.

Simic grows a neural network at runtime by **generating** new structure from
the live state of the host — not selecting it from a menu of human-authored
blueprints — then testing that structure in matched counterfactual branches
and admitting it only if it beats doing nothing. The architecture exists to
keep four questions separate: *what* to build, *whether* it is sound,
*whether* it helps, and *who* decides.

## Planes

Authority is split across fourteen bounded domains, grouped into planes.
Three domains are infrastructure (named with prepositions: *under* Leyline,
*in* Tolaria, *from* Sarpadia); eleven are agents (named with verbs). A
subsystem acting contrary to its verb is exercising authority it must not
have — the names are an architecture linter.

| Plane | Domains | Purpose |
|---|---|---|
| Constitutional infrastructure | Leyline | Contracts, grammar profiles, compatibility, the deterministic request resolver |
| Training and execution infrastructure | Tolaria | Trains the live host; executes deterministic ordinary, replay and branch worlds |
| Historical infrastructure | Sarpadia | Append-only history: lineages, outcomes, failures, split-safe datasets |
| Strategic agency | Tamiyo | Allocates regional resources, permissions and risk over long horizons |
| Tactical commissioning | Narset | Decides whether and where to commission growth; pre-commit lifecycle actions |
| Observation | Nissa | Publishes what the host is doing without prescribing what to build |
| Synthesis | Momir, Elesh, Tezzeret | Designs, canonicalises and compiles growth |
| Assurance and adjudication | Urabrask, Augustin | Establishes empirical evidence, then judges it independently |
| Embodiment and maintenance | Kasmina, Emrakul | Introduces growth safely; removes obsolete committed structure |
| Witness | Oona | Exposes an auditable account without steering anything |

## The pipeline

```mermaid
flowchart TD
    TOL["Tolaria: trains the host"] --> KAS["Kasmina: host + reversible growth physiology"]
    KAS --> NIS["Nissa: canonical ablated observation"]
    NIS -->|"TelemetryEnvelope"| NAR["Narset: commissions"]
    NIS -->|"same TelemetryEnvelope"| MOM["Momir: designs candidates"]
    TAM["Tamiyo: strategic controller"] -->|"StrategicEnvelope"| NAR
    NAR -->|"GrowthIntent (assignment brief)"| RES["Leyline: deterministic request resolver"]
    RES -->|"canonical GrowthRequest"| MOM
    MOM -->|"RawGrowthGraph"| ELE["Elesh: verifies + canonicalises"]
    ELE -->|"CanonicalGrowthSpec"| TEZ["Tezzeret: compiles"]
    TEZ -->|"ExecutableGrowthArtifact"| URA["Urabrask: QA in Tolaria branches"]
    URA -->|"blinded QualityReport"| AUG["Augustin: judges vs mandatory no-op"]
    AUG -->|"admission warrant"| KAS
    KAS -->|"committed growth"| EMR["Emrakul: maintains, retires"]
    AUG -->|"maintenance warrant"| EMR
```

Every stage also appends its records to Sarpadia and projects events to
Oona; those edges are omitted above for legibility. Two details in the
diagram are load-bearing:

- **Nissa publishes the same observation identity independently to Narset
  and Momir.** Narset is not a telemetry proxy; the newsroom formulation is
  "Nissa sends the photograph; Narset sends only the assignment brief." A
  `GrowthIntent` carries scope and operational constraints only — diagnosis,
  topology and ancestry hints are schema-invalid (INV-07, INV-09).
- **The request resolver is not a fifteenth agent.** It is a pure Leyline
  service that combines `GrowthIntent` + `StrategicEnvelope` + Kasmina's
  `RegionContract` + the active `GrammarProfile` into one canonical
  `GrowthRequest`, can only narrow authority, and fails closed on
  incompatibility (INV-10, INV-11).

The assurance loop: Urabrask builds a blinded `TestPlan`; Tolaria restores a
common snapshot and runs candidate branches, controls, and a **mandatory
no-op branch** over identical future data; Urabrask certifies the evidence
into a `QualityReport` without issuing a verdict; Augustin applies
eligibility, budget, risk and utility policy and returns one of
`ADMIT / NO_OP / REJECT / DEFER / REQUIRE_RETEST`. Admitted growth
germinates at zero influence, matures, blends in reversibly, and at commit
passes from Narset's ownership to Emrakul's, where it must keep earning its
tenancy through periodic counterfactual review (`RETAIN / RETEST / SEDATE /
DECAY / LYSE`).

## The fourteen domains

The canonical sentence: *Nissa observes and reports. Tamiyo plans. Narset
commissions and acts. Momir designs. Elesh conforms. Tezzeret compiles.
Urabrask tests the compiled result in Tolaria. Augustin judges the resulting
evidence under Leyline. Kasmina embodies the admitted growth. Emrakul
destroys what no longer earns continued tenancy. Sarpadia retains every
precedent. Oona reveals the account.*

| Domain | Key outputs | Explicitly does not own |
|---|---|---|
| **Leyline** | Versioned contracts, validators, resolved requests | Case-specific policy, diagnosis, execution |
| **Tolaria** | `Snapshot`, `BranchResult`, execution manifests | Utility weights, candidate preference, verdicts |
| **Sarpadia** | `GrowthRecord`, retrieval sets, lineage graphs | Live-host mutation, self-approval |
| **Tamiyo** | `StrategicEnvelope` | Local action timing, candidate choice |
| **Narset** | `GrowthIntent`, `LifecycleCommand` | Diagnosis, topology hints, post-commit structure |
| **Nissa** | `TelemetryEnvelope` | `should_grow`, structural recommendations, verdicts |
| **Momir** | `RawGrowthGraph` | Intervention timing, approval, testing |
| **Elesh** | `CanonicalGrowthSpec`, structural reports | Runtime QA, task utility, lifecycle policy |
| **Tezzeret** | `ExecutableGrowthArtifact`, compilation manifest | Semantic topology changes, QA, admission |
| **Urabrask** | `TestPlan`, `QualityReport` | Verdicts, warrants, lifecycle commands |
| **Augustin** | `AdmissionDecision`, `MaintenanceDecision`, warrants | Test execution, compilation, host mutation |
| **Kasmina** | `RegionContract`, embodied state, lifecycle events | Whether a growth deserves admission |
| **Emrakul** | Maintenance requests, warranted lifecycle commands | Candidate construction, judgement |
| **Oona** | Operator views, flight recorder, audit bundles | Training control, source-of-truth schemas |

## Authority model

Control flows down a narrow hierarchy — Tamiyo sets the `StrategicEnvelope`;
Narset chooses local pre-commit actions inside it; after `COMMIT`, ordinary
ownership transfers to Emrakul for post-commit maintenance. Three authorities
sit deliberately **outside** that hierarchy:

- **Urabrask and Augustin are independent** of the command chain: Urabrask
  certifies evidence but never issues verdicts or warrants; Augustin judges
  but never executes or alters tests (INV-18). Neither ever sees candidate
  provenance — blinding is by construction, with source fields absent rather
  than ignored (INV-17, INV-37).
- **Tolaria is beneath the hierarchy** as neutral execution infrastructure:
  it applies no utility weights and issues no verdicts (INV-03).
- **Oona and Sarpadia are outside the control path**: disconnecting Oona
  cannot change training (INV-35), and Sarpadia's history is append-only and
  retains failures, rejected pools, no-op wins and abstentions — never
  winners-only (INV-31, INV-36).

No influence without a warrant: Kasmina cannot raise a newborn growth above
zero influence without a valid Augustin admission warrant (INV-26), and
ordinary post-commit decay or lysis requires a maintenance warrant (INV-27).
Every artefact, QA report, decision and embodiment references the same
canonical semantic hash (INV-20).

## Where the detail lives

All 44 invariants: [`docs/design/02-constitution.md`](docs/design/02-constitution.md)
(always load it when working here). Contract shapes:
[`docs/design/05-leyline-contracts.md`](docs/design/05-leyline-contracts.md).
Growth levels and the lifecycle FSM:
[`docs/design/06-growth-model.md`](docs/design/06-growth-model.md).
Branch pools, QA and no-op anchoring:
[`docs/design/07-counterfactual-engine.md`](docs/design/07-counterfactual-engine.md).
Per-domain specifications: [`docs/design/domains/`](docs/design/domains/README.md).
Target code layout: [`docs/design/ops/repo-structure.md`](docs/design/ops/repo-structure.md).
The full chapter map and reading paths:
[`docs/design/00-INDEX.md`](docs/design/00-INDEX.md).

Citation convention for new text: invariants as **INV-nn**, contracts by
**name** (`GrowthIntent`), chapters by **path#anchor** — never bare
§-numbers, which died with the v4.1 monolith renumbering.
