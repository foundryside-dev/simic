<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: 00-INDEX.md -->
[← HLD index](00-INDEX.md)

<!-- hld: source: v4.1 monolith lines 169–348 -->
## 5. Locked Naming Constitution

### 5.1 Why the names are deliberately goofy

The subsystem names are deliberately non-obvious to an outsider. This is useful for five reasons.

First, the names provide **cognitive compression**. “Urabrask tests; Augustin judges” is easier to retain and repeat than a long explanation of the distinction between evidence production and policy adjudication.

Second, the names create a **sentence test**. A sentence that sounds wrong in the project's narrative grammar often describes a real responsibility leak:

- “Tolaria rejected the candidate” sounds wrong because a training substrate should not judge.
- “Augustin ran the CUDA probe” sounds wrong because a judge should not gather its own evidence.
- “Momir admitted its design” sounds wrong because a designer should not approve its own work.
- “Nissa said `should_grow=True`” sounds wrong because observation should not conceal policy.
- “Narset told Momir to use attention” sounds wrong because an assignments editor should not pre-write the answer.
- “Sarpadia deployed the module” sounds wrong because history should not mutate the present.
- “Oona changed alpha” sounds wrong because a witness should not steer the process.

Third, the names create a **neutral review vocabulary**. Engineers can say “this makes Elesh too political,” “Narset has added an editorial angle,” or “Tolaria has acquired opinions” without making the discussion personal. The metaphor points at the boundary violation rather than the author.

Fourth, the names define a small **architectural grammar**. People and entities exercise agency; infrastructure supplies contexts. The project can reason in verbs and prepositions rather than memorising an arbitrary package map.

Fifth, uniform opacity is preferable to a mixed scheme in which one package is obvious and every other package is lore. The system therefore uses one intentionally idiosyncratic internal vocabulary, backed by explicit plain-English documentation. The joke works only if an outsider can infer approximately zero package responsibilities from the names alone.

The codenames do **not** replace proper API names. Cross-boundary records remain things such as `TelemetryEnvelope`, `GrowthIntent`, `GrowthRequest`, `QualityReport`, `AdmissionDecision`, and `TrainingRunSpec`. Every package README must begin with a plain-English role statement. The names are not security by obscurity and should not be relied on to conceal behaviour.

### 5.2 The grammar: actors have verbs; infrastructure has prepositions

The locked convention distinguishes **agents** from **infrastructure**.

People and entities represent agents. They observe, plan, commission, act, design, conform, compile, test, judge, embody, destroy, or reveal.

Places, systems, and phenomena represent infrastructure. They are the contexts **under**, **in**, or **from** which the agents operate.

#### Agent names

| Agent | Narrative verb | Architectural authority | Must not become |
|---|---|---|---|
| **Tamiyo** | Plans | Strategic allocation, regional permissions, long-horizon budgets and risk | A local action selector |
| **Narset** | Commissions and acts | Tactical intervention timing, insertion-region choice, operational constraints, and pre-commit lifecycle control | A co-designer or source of unallocated authority |
| **Nissa** | Observes and reports | Typed host diagnostics, direct evidence publication, and provenance | A hidden controller or editorial intermediary |
| **Momir** | Designs | Candidate topology, parameters, mutation and recombination | The approver of its own work |
| **Elesh** | Conforms | Structural legality, canonicalisation and semantic identity | A utility predictor or task judge |
| **Tezzeret** | Compiles | Lowering and executable realisation | A semantic graph designer |
| **Urabrask** | Tests | Dynamic QA, regression, runtime conformance and evidence certification | The admission judge |
| **Augustin** | Judges | Admission, no-op comparison, policy utility and continued-tenancy rulings | A test runner or compiler |
| **Kasmina** | Embodies | Host topology, slots, maturation, blending and physical lifecycle | A candidate selector or blueprint catalogue |
| **Emrakul** | Destroys | Safe post-commit sedation, decay, consolidation and lysis | A constructor or newborn judge |
| **Oona** | Reveals | Flight recording, projections, operator surfaces and audit | A control-plane backchannel |

#### Infrastructure names

| Infrastructure | Grammatical use | Neutral service | Must not own |
|---|---|---|---|
| **Leyline** | *under/through Leyline* | Contracts, schemas, grammar profiles, versions, invariants and policy record formats | Case-specific decisions or subsystem policy |
| **Tolaria** | *trained/executed/tested in Tolaria* | Host training, data and optimiser execution, devices, snapshots, replay, branching and rollback | Preferences, utility weights or verdicts |
| **Sarpadia** | *recorded in/retrieved from Sarpadia* | History, lineage, bootstrap ancestry, counterfactual outcomes, retrieval and datasets | Live-host mutation or self-approval |

Infrastructure can be highly active software. “Infrastructure” means it provides a neutral capability rather than exercising a preference about what ought to happen.

### 5.3 The canonical sentence

The architecture should remain intelligible as a sentence:

> **Nissa observes and reports. Tamiyo plans. Narset commissions and acts. Momir designs. Elesh conforms. Tezzeret compiles. Urabrask tests the compiled result in Tolaria. Augustin judges the resulting evidence under Leyline. Kasmina embodies the admitted growth. Emrakul destroys what no longer earns continued tenancy. Sarpadia retains every precedent. Oona reveals the account.**

This sentence is a compact authority map.

### 5.4 The sentence test

The following sentences are healthy:

```text
Nissa published the same TelemetryEnvelope to Narset and Momir.
Narset issued a GrowthIntent for Region A under Tamiyo's envelope.
Leyline resolved the legal GrowthRequest from the intent and Kasmina region contract.
Momir used compatible ancestors retrieved from Sarpadia during the bootstrap curriculum.
Urabrask requested a deterministic trial in Tolaria.
Tolaria returned branch measurements.
Augustin selected no-op from the certified evidence.
Kasmina rejected a lifecycle command whose Augustin warrant was invalid.
Oona displayed the rejection without altering the run.
```

The following sentences should trigger review:

```text
Narset forwarded a captioned telemetry summary to Momir.
Narset requested an attention-like topology.
Nissa recommended a wide bottleneck.
Tolaria rejected the candidate.
Urabrask issued the admission token.
Augustin reran the branch with a more favourable batch.
Momir filtered out designs that scored poorly in the current live trial.
Elesh used future task reward to reject a legal graph.
Tezzeret inserted a new semantic node during optimisation.
Sarpadia installed the nearest historical candidate.
Oona changed the learning rate directly.
Leyline imported Narset to decide a default action.
```

The sentence test is not a proof, but it is an intentionally cheap architecture lint.

### 5.5 The newsroom principle

> **Sidebar — Why the architecture resembles a newsroom**
>
> The similarity is structural rather than decorative. A newsroom separates source observation, assignment, authorship, standards review, production, fact-checking, publication judgement, placement, correction, archive, and presentation because allowing one desk to control the complete chain corrupts both evidence and accountability.
>
> In this architecture:
>
> - Nissa is the reporting, photography, and data desk: it publishes what was observed.
> - Tamiyo is the editor-in-chief or managing editor: it allocates desks, time, and strategic resources.
> - Narset is the assignments editor: it decides whether there is a story, which beat owns it, what scope and deadline apply, and what resources may be spent.
> - Momir is the writer or investigative journalist: it determines the substantive answer from the evidence and commission.
> - Elesh is the copy and standards desk: it enforces structural, typed, and house-form conformity without deciding whether the story is valuable.
> - Tezzeret is production: it turns canonical copy into an executable edition without changing meaning.
> - Urabrask is fact-checking and QA: it establishes what the finished artefact actually does.
> - Augustin is the publishing editor: it decides whether the evidence justifies running, returning, deferring, or spiking the story.
> - Kasmina integrates accepted material into the live edition.
> - Emrakul handles correction, withdrawal, and retirement after publication.
> - Sarpadia is the morgue and archive, including corrections, failed investigations, and abandoned drafts.
> - Oona is presentation: front page, broadcast desk, dashboards, and public account.
> - Leyline is the stylebook, editorial constitution, and record format.
> - Tolaria is the newsroom production environment, CMS, presses, and test editions.
>
> The load-bearing rule is: **Narset does not send the photograph. Nissa sends the photograph directly to Momir. Narset sends only the assignment brief.**
>
> The code-review question is therefore: **does this field belong in an assignment brief, or does it impose an editorial angle?** Scope, region, resource class, deadline, maturity mode, and assurance class are assignment fields. A deficit diagnosis, topology preference, ancestor choice, expected mechanism, or proposed solution is an editorial angle and is prohibited from Narset's channel.
>
> Appendix E develops the analogy, its smell tests, and its limits. The metaphor is never the enforcement mechanism; Leyline contracts and authority tests are.

### 5.6 Dependency consequence

The naming grammar implies two dependency rules:

1. Agents may consume neutral services from Leyline, Tolaria, and Sarpadia through typed interfaces.
2. Infrastructure must not import agent policy or encode agent-specific preferences.

Examples:

```text
urabrask → tolaria protocol                 healthy
augustin → leyline contracts                healthy
momir → sarpadia retrieval API              healthy
nissa → leyline telemetry schema            healthy
narset → leyline GrowthIntent schema        healthy

tolaria → augustin policy                   suspect
sarpadia → momir training code              suspect
leyline → narset implementation             prohibited
narset → momir graph grammar implementation prohibited
momir → narset hidden state                 prohibited
```

Tolaria may execute a Kasmina host through a neutral host-runtime protocol. Sarpadia may store Momir records as opaque contract values. Neither requires ownership of the corresponding agent's policy.

### 5.7 Change control

Namespec 1.0 is considered locked for this design:

```text
Leyline
Tolaria
Sarpadia
Tamiyo
Narset
Nissa
Momir
Elesh
Tezzeret
Urabrask
Augustin
Kasmina
Emrakul
Oona
```

Changing a codename or moving an authority between names requires an architecture decision record because it changes the project's shared responsibility grammar, package paths, telemetry names, tests, and operational language.

---

<!-- hld: source: v4.1 monolith lines 3094–3142 · amended by ADR-0004 (INV-45 added), ADR-0005 (INV-33 amended) -->
## 18. Safety, Correctness and Constitutional Invariants

The following are blocking invariants.

1. **Namespec ownership:** every package has one documented authority, one narrative verb or infrastructure context, and a list of forbidden decisions.
2. **Leyline dependency direction:** contracts and schemas do not import agent implementations.
3. **Tolaria neutrality:** training and execution code applies no candidate utility weights and issues no verdicts.
4. **Mainline–branch parity:** live and counterfactual host steps use the same execution semantics unless the difference is explicitly measured.
5. **Academy exact replay:** identical snapshot plus identical future data produces bitwise-identical traces under Tolaria's Academy-exact determinism contract; non-exact profiles carry measured uncertainty rather than pretending to satisfy this invariant.
6. **Common future:** paired branches receive identical future minibatches and equivalent random streams.
7. **Direct evidence publication:** Nissa publishes one canonical observation identity independently to Narset and Momir; Narset is not the designer's telemetry intermediary.
8. **Observation binding:** `TelemetryEnvelope`, `GrowthIntent`, `GrowthRequest`, Momir proposals and Tolaria trials reconcile to the same observation, host state, region and snapshot.
9. **Assignment-brief boundary:** `GrowthIntent` contains scope and operational constraints only; diagnosis, topology, ancestry and mechanism hints are schema-invalid.
10. **Deterministic request resolution:** `GrowthRequest` is reproducible from recorded intent, envelope, region contract and grammar profile and can only narrow authority.
11. **No covert request channel:** equivalent intents resolve to one canonical request; irrelevant serialisation, aliases, candidate count and field ordering cannot steer Momir.
12. **No hidden-state coupling:** Momir cannot access Narset recurrent state or implementation-specific features.
13. **Bootstrap provenance:** ancestry context is explicit, versioned and independently supplied from Sarpadia; null ancestry is supported.
14. **Scaffold-versus-control distinction:** removal of ancestry from Momir does not remove reference candidates from blinded evaluation controls.
15. **No-op availability:** every admission and continued-tenancy case includes a measured no-intervention alternative.
16. **No-op convention:** Augustin assigns no-op policy utility exactly zero.
17. **Dual provider blindness:** neither Urabrask nor Augustin accesses candidate source during QA interpretation or adjudication.
18. **Evidence–judgement separation:** Urabrask cannot issue admission or maintenance warrants; Augustin cannot execute or alter tests.
19. **Raw-to-canonical traceability:** every canonical growth links to the exact raw proposal and Elesh report.
20. **Canonical semantic identity:** every artefact, QA report, Augustin decision and Kasmina embodiment references the same canonical semantic hash.
21. **Compiler semantic preservation:** every Tezzeret artefact passes Urabrask runtime conformance against the canonical reference.
22. **No branch transplant:** branch-matured growth is deployed only by branch adoption or exact replay.
23. **Budget enforcement:** every constructor, compiler, test plan, branch and maturation phase declares budget and reports spend.
24. **Typed compatibility:** incompatible schema, grammar, insertion, device, telemetry, QA or policy versions fail closed.
25. **Reversible influence:** every non-merged growth can be brought to zero influence without an uncontrolled discontinuity.
26. **Augustin admission warrant:** Kasmina cannot raise a newborn growth above zero influence without a valid warrant.
27. **Augustin maintenance warrant:** ordinary post-commit decay or lysis requires a valid maintenance decision.
28. **Containment distinction:** emergency safety reduction is recorded as containment, not disguised as economic judgement.
29. **Authority enforcement:** Narset cannot manage post-commit structure; Emrakul cannot manage unborn structure; Tamiyo cannot issue local transitions.
30. **Grace-period protection:** contribution-based removal cannot fire before declared blend and holding windows complete.
31. **Complete negative retention:** structural rejects, compilation failures, QA failures, adjudication rejects, no-op decisions and abstentions are stored.
32. **Grouped statistics:** branches from one base trajectory never cross splits or inflate independent sample counts.
33. **Selection–retention consistency:** shared cost terms use shared weights unless a structural difference is documented; admission and retention thresholds are deliberately asymmetric — the admit threshold sits strictly above the retain threshold by a versioned hysteresis band sized against measured execution noise. (ADR-0005)
34. **Telemetry purity:** Nissa observation cannot perturb host training state.
35. **Oona isolation:** disconnecting Oona cannot alter training outcomes.
36. **Sarpadia append-only history:** corrections create new records rather than rewriting causal history.
37. **Blinding by construction:** source fields are absent from QA and adjudication views rather than merely ignored.
38. **Failure visibility:** invariant breaches fail loudly and are visible through Oona; no silent fallback fabricates valid-looking state.
39. **Declared scaffold state:** every curriculum, QA and confirmatory run records its execution, host-distribution and design-prior regimes.
40. **Independent withdrawal gates:** one scaffold cannot advance because a different scaffold passed its gate.
41. **One-axis confirmatory transition:** withdrawing multiple scaffolds at once requires a declared interaction experiment and completed single-axis controls.
42. **Retained reference capability:** withdrawal removes a production dependency, not the Academy replay harness, acquisition fixtures or blinded reference controls.
43. **Field calibration:** Field evidence is valid only inside a current calibration envelope and carries uncertainty and escalation provenance.
44. **Decision-aware execution gate:** Field-to-Academy accept/no-op disagreement and selection regret must remain inside declared limits, including tail cases.
45. **Lexicographic admission:** the tail-risk veto is adjudicated before any utility comparison and cannot be traded against measured benefit; the assurance class owns the veto operating point. (ADR-0004)

---

<!-- hld: source: v4.1 monolith lines 4323–4395 -->
## Appendix B — One-Line Namespec Invariants

**Scaffolds:** constrain acquisition, relax under measurement, withdraw independently, and remain available as references.

```text
LEYLINE
Defines what may be said, what may be requested, and how evidence and decisions are represented.
May resolve contracts deterministically.
Must not diagnose or decide an individual case.

TOLARIA
Is where the host is trained and where possible futures are executed.
Must not prefer one future.

SARPADIA
Is where precedents, failures, reference ancestry and lineages are kept.
May supply temporary ancestry and ordinary retrieval.
Must not act on the live host.

TAMIYO
Plans long-horizon developmental authority.
Must not micromanage local actions.

NARSET
Commissions and acts locally inside granted authority.
May specify scope and operational class.
Must not caption evidence, choose ancestry, or prescribe phenotype.

NISSA
Observes and reports the host directly to authorised consumers.
May normalise and attach provenance.
Must not hide decisions or structural recommendations inside observations.

MOMIR
Designs possibilities from evidence, constraints and optional precedent.
May produce bad ideas.
Must not receive Narset's hidden interpretation or approve its own work.

ELESH
Makes designs structurally legal and canonical.
May reject malformed structure.
Must not judge task utility.

TEZZERET
Compiles canonical designs into executable artefacts.
May optimise implementation.
Must not change meaning.

URABRASK
Tests artefacts and certifies evidence.
May report defects and uncertainty.
Must not issue a verdict.

AUGUSTIN
Judges certified evidence under declared policy.
May choose no-op.
Must not gather or alter evidence, or trade tail risk against measured benefit.

KASMINA
Embodies legal, warranted growth and declares insertion-region contracts.
Must not own a preferred blueprint catalogue or decide whether growth deserves to exist.

EMRAKUL
Safely removes committed structure that has outlived its value.
Must not design or judge newborn growth.

OONA
Reveals the system's account.
Must not steer the system through the act of observing it.
```
