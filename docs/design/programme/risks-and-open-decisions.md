<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: ../00-INDEX.md -->
[← HLD index](../00-INDEX.md)

<!-- hld: source: v4.1 monolith lines 4094–4205 -->
## 26. Risks and Mitigations

| Risk | Consequence | Mitigation |
|---|---|---|
| **Tolaria policy creep** | Training infrastructure begins ranking or rejecting candidates | No utility imports; neutral protocols; namespec and import tests |
| **Mainline–branch divergence** | Counterfactual results do not describe live training | One step engine; parity tests; explicit approximation error |
| **Momir mode collapse** | Best-of-\(K\) candidates are functionally identical | Explicit latent, winner-take-all objective, functional diversity metrics |
| **Elesh overreach** | Structural gate pre-judges utility and biases the pool | Deny reward/future-utility inputs; rule-driven hard checks |
| **Tezzeret semantic drift** | Compiled artefact differs from canonical design | Canonical hash, manifests and Urabrask runtime conformance |
| **Urabrask judicial creep** | QA begins issuing admission recommendations or tokens | `QualityReport` schema excludes verdicts; forbidden imports; tests |
| **Augustin evidentiary creep** | Judge alters tests or gathers favourable evidence | Augustin consumes immutable reports only; no Tolaria dependency |
| **QA overfitting** | Test plans are tuned to known candidate families | Pre-versioned plans, source blindness, sealed regression fixtures |
| **Adjudication overfitting** | Thresholds are tuned after seeing confirmatory results | Validation-only calibration and frozen policy versions |
| **Provider leakage** | Candidate origin influences tests or judgement | Blinded Sarpadia views and source-absence tests |
| **Telemetry underspecification** | Different deficits appear identical | Orientation-bearing gradients, temporal context and information ablations |
| **Moving target** | Candidate becomes stale before integration | Latency budgets, staleness curves and re-qualification |
| **Counterfactual nondeterminism** | Branch differences reflect runtime noise | Academy-exact causal reference, divergence localisation, measured Field uncertainty and escalation |
| **QA cost dominance** | Evidence costs more than the adaptation it protects | Predeclared budget and QA coverage–cost Pareto curve |
| **Survivorship bias** | System cannot learn refusal or failure modes | Retain structural rejects, QA failures, no-op and long-term regressors |
| **Host co-adaptation** | Same-host ablation exaggerates value | Separate no-op and re-adaptation branches |
| **Install–lyse oscillation** | Admission and continued-tenancy policy disagree | Shared cost weights, churn metrics, cooldowns and pre-registration |
| **Tamiyo micromanagement** | Strategic controller becomes local policy | Slow cadence, aggregate inputs and interface prohibition |
| **Narset budget escape** | Tactical controller creates ungoverned capacity | Envelope validation in Leyline, Augustin and Kasmina |
| **Narset co-design / editorial angle** | Tactical policy encodes diagnosis, topology or ancestry into the assignment | Narrow `GrowthIntent`; schema-forbidden fields; direct Nissa-to-Momir route |
| **Telemetry mediation** | Momir sees Narset's interpretation rather than the host observation | One canonical Nissa publication with shared observation identity |
| **Covert request channel** | Narset and Momir encode designs through continuous budgets, aliases or candidate count | Coarse enums, deterministic canonical resolution, invariance and anti-collusion tests |
| **Bootstrap ceiling** | Momir becomes a blueprint selector or mutation table | Parent-relative and reference-frontier objectives; ancestry dropout; de novo gate |
| **Permanent scaffold dependence** | Production generation fails without stock reference seeds | Explicit null ancestry, withdrawal schedule, held-out scaffold-free evaluation |
| **Permanent bitwise burden** | Exactness requirements prevent realistic kernels, scale or hardware evolution | Treat Academy exactness as a retained metrology profile; calibrate Field execution rather than requiring universal bitwise identity |
| **Premature execution withdrawal** | Field noise changes rankings or no-op decisions before it is understood | Decision-aware Field gate, uncertainty margins and Academy escalation |
| **Lockstep scaffold withdrawal** | One subsystem loses support because another subsystem is ready | Independent three-axis `ScaffoldState` and separate gate ownership |
| **Multi-scaffold confounding** | A failure after simultaneous withdrawal cannot be attributed | One-axis confirmatory transitions and declared interaction experiments |
| **Hidden scaffold correlation** | Fixed seeds, exact execution and stock ancestry make one another look stronger than they are | Selected scaffold interaction matrix and final fully withdrawn corner |
| **Kasmina legacy blueprint creep** | Host physiology quietly regains a preferred design catalogue | Reference population lives in Sarpadia/controls; Kasmina imports no blueprint library |
| **Sarpadia leakage** | Related branches cross train/test boundaries | Group split by base host trajectory |
| **Oona control coupling** | UI or logging changes training behaviour | Read-only events and isolation tests |
| **Codename opacity** | New contributors cannot find responsibilities | Plain-English README header, glossary, typed record names and diagrams |
| **Namespec drift** | One codename accumulates multiple meanings | ADR, package ownership manifest and compatibility sunset dates |
| **Toy-task non-separability** | Methods appear equal because the space is too small | Sweep width and grammar complexity before broad conclusions |
| **Graph grammar explosion** | Design and verification become intractable | Staged grammar levels and explicit ceilings |
| **Asynchronous compilation staleness** | Candidate is obsolete before Tezzeret finishes | Compilation budget, caching and re-qualification |

---

## 27. Open Design Decisions

The subsystem names and their principal authorities are **not** open decisions. Namespec 1.0 is locked. The following implementation choices remain open.

### 27.1 Project-level name

The umbrella package or programme may remain `simic`, return to `esper`, or adopt another name. This does not change the subsystem names.

### 27.2 Default maturation mode

Should the ecological default be one-shot generation, isolated nursery training, or a mixed Narset policy after both modes are characterised?

### 27.3 Winning-branch deployment

Should live operation adopt the winning branch state directly or restore and replay it? The answer may depend on hardware placement, branch latency and checkpoint cost.

Conditionality note (§6/§8 of `docs/concept/reviews/2026-08-08-esper-pivot-peer-review.md`, ruled at the decision gate): fast landing (flash-clone) is not required for the pivot — ordinary blending is sufficient — but if it is ever pursued, two collisions bite. A candidate matured in a branch is co-adapted to that branch, so copying it into a live host that followed a different trajectory is the transplant §14.6 forbids; fast landing therefore requires resolving this decision toward branch adoption (restore-and-replay instead pays the replay cost and reopens the staleness window). And §12.4's minimum blend and holding windows assume gradual alpha; a one-or-two-step landing trips them, so that mechanism would need re-deriving for a regime where alpha is not the thing taking time.

### 27.4 Growth grammar

What is the smallest safe grammar materially more expressive than a residual microcell without becoming unrestricted architecture search?

### 27.5 QA horizon and evidence floor

What horizon captures trajectory value before branch-divergence noise overwhelms the intervention signal? What evidence-completeness threshold should force retest?

### 27.6 Urabrask–Augustin contract

Which measurements are raw, which are certified derived facts, and which hard QA statuses make a candidate ineligible by policy? The separation is locked; the exact report surface is not.

### 27.7 Commitment semantics

Does commitment retain a named removable growth indefinitely, or may a later authorised consolidation merge it into the host while preserving lineage?

### 27.8 Retrieval similarity

Should Sarpadia retrieve by telemetry distance, learned state embeddings, gradient alignment, functional effect, task context, lineage history or a calibrated mixture?

### 27.9 Augustin–Emrakul maintenance boundary

Should Augustin issue only a tenancy verdict, or also a bounded class of permitted maintenance actions? The preferred direction is verdict plus constraints, with Emrakul selecting the safe physical schedule.

### 27.10 Oona transport boundary

Should Oona own the event bus implementation or only durable projections and operator adapters? In either case, Leyline owns schemas and training remains independent of Oona availability.

### 27.11 Request-channel granularity

Fix the smallest set of coarse `GrowthIntent` classes that gives Narset useful tactical authority without creating a high-bandwidth covert design channel to Momir.

### 27.12 Bootstrap reference population

Fix the initial reference families, canonical graph forms, mutation radii, ancestry-dropout schedule and scaffold-withdrawal gate. The corpus must be broad enough to teach structural literacy without becoming the permanent ceiling.

### 27.13 Tolaria integration boundary

Should Tolaria call a generic Kasmina host protocol, or should a thin integration adapter live outside both domains? The result must preserve infrastructure neutrality and one execution path.

### 27.14 Tolaria Field-withdrawal gate

Fix the acceptable Field-to-Academy selection regret, accept/no-op disagreement, uncertainty coverage, tail-failure rate, calibration expiry conditions and mandatory escalation policy for each assurance class.

### 27.15 Scaffold interaction budget

Fix which two-way and three-way scaffold interaction cells are required at toy, image and scaled stages. The programme must preserve interpretability without committing to an unnecessarily exhaustive Cartesian product at every scale.
