<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: 00-INDEX.md -->
[← HLD index](00-INDEX.md)

<!-- hld: source: v4.1 monolith lines 169–348 · superseded in vocabulary by ADR-0008 (Namespec 2.0) -->
## 5. Locked Naming Constitution

### 5.1 Why the names are deliberately goofy

The subsystem names are deliberately non-obvious to an outsider. This is useful for five reasons.

First, the names provide **cognitive compression**. “Jin-Gitaxias tests; Isperia judges” is easier to retain and repeat than a long explanation of the distinction between evidence production and policy adjudication.

Second, the names create a **sentence test**. A sentence that sounds wrong in the project's narrative grammar often describes a real responsibility leak:

- “Tolaria rejected the candidate” sounds wrong because a training substrate should not judge.
- “Isperia ran the CUDA probe” sounds wrong because a judge should not gather its own evidence.
- “Momir admitted its design” sounds wrong because a designer should not approve its own work.
- “Nissa said `should_grow=True`” sounds wrong because observation should not conceal policy.
- “Aurelia told Momir to use attention” sounds wrong because an assignments editor should not pre-write the answer.
- “Urborg deployed the module” sounds wrong because history should not mutate the present.
- “Tamiyo changed alpha” sounds wrong because a witness should not steer the process.

Third, the names create a **neutral review vocabulary**. Engineers can say “this makes Elesh too political,” “Aurelia has added an editorial angle,” or “Tolaria has acquired opinions” without making the discussion personal. The metaphor points at the boundary violation rather than the author.

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
| **Ugin** | Plans | Strategic allocation, regional permissions, long-horizon budgets and risk | A local action selector |
| **Aurelia** | Commissions and acts | Tactical intervention timing, insertion-region choice, operational constraints, and pre-commit lifecycle control | A co-designer or source of unallocated authority |
| **Nissa** | Observes and reports | Typed host diagnostics, direct evidence publication, and provenance | A hidden controller or editorial intermediary |
| **Momir** | Designs | Candidate topology, parameters, mutation and recombination | The approver of its own work |
| **Elesh** | Conforms | Structural legality, canonicalisation and semantic identity | A utility predictor or task judge |
| **Urabrask** | Compiles | Lowering and executable realisation | A semantic graph designer |
| **Jin-Gitaxias** | Tests | Dynamic QA, regression, runtime conformance and evidence certification | The admission judge |
| **Isperia** | Judges | Admission, no-op comparison, policy utility and continued-tenancy rulings | A test runner or compiler |
| **Wrenn** | Embodies | Host topology, slots, maturation, blending and physical lifecycle | A candidate selector or blueprint catalogue |
| **Emrakul** | Destroys | Safe post-commit sedation, decay, consolidation and lysis | A constructor or newborn judge |
| **Tamiyo** | Reveals | Flight recording, projections, operator surfaces and audit | A control-plane backchannel |

#### Infrastructure names

| Infrastructure | Grammatical use | Neutral service | Must not own |
|---|---|---|---|
| **Leyline** | *under/through Leyline* | Contracts, schemas, grammar profiles, versions, invariants and policy record formats | Case-specific decisions or subsystem policy |
| **Tolaria** | *trained/executed/tested in Tolaria* | Host training, data and optimiser execution, devices, snapshots, replay, branching and rollback | Preferences, utility weights or verdicts |
| **Urborg** | *recorded in/retrieved from Urborg* | History, lineage, bootstrap ancestry, counterfactual outcomes, retrieval and datasets | Live-host mutation or self-approval |

Infrastructure can be highly active software. “Infrastructure” means it provides a neutral capability rather than exercising a preference about what ought to happen.

#### The synthesis core and the governance cage

The names carry a second, deliberate layer: faction. Four agents form the **Phyrexian industrial synthesis core** — a single compleation assembly line running inside the architecture:

- **Momir** (Simic genesis) designs the raw specimen in the bio-lab.
- **Elesh** (the Machine Orthodoxy) forces it into canonical, unified, structurally legal form.
- **Urabrask** (the Quiet Furnace) manufactures it into an executable artifact. He is the factory foreman: he may optimise the production line — kernel fusion, memory layout, device-specific lowering, cheaper compilation paths — but he cannot change the blueprint. If he changes semantic meaning, he has violated the Orthodoxy.
- **Jin-Gitaxias** (the Progress Engine) stress-tests the manufacture with ruthless, iterative empirical experimentation and certifies what the artifact actually does.

Bio-foundry → standardisation → manufacturing → quality control: these four are one industrial organism. The remaining authorities are **the governance cage** that contains it:

- **Ugin** plans long-horizon resource allocation from a distance.
- **Aurelia** commissions local tactical assignments within Ugin's envelope.
- **Isperia** judges whether the certified evidence justifies admission or lysis.
- **Nissa** observes and publishes direct evidence.
- **Wrenn** is the symbiotic host who physically embodies the growth and manages its lifecycle.
- **Tamiyo** reveals the complete account without steering it.

Emrakul is claimed by neither side: post-commit destruction acts only under the cage's maintenance warrants. This framing is a **warning system**, not decoration. An authority violation reads as faction contamination — the factory issuing a verdict, the judge running the presses. “Jin-Gitaxias issued the admission token” is audibly a Phyrexian hand on a governance lever before it is ever a diff to review. The tension between the synthesis core and the cage is the central narrative of the architecture.

### 5.3 The canonical sentence

The architecture should remain intelligible as a sentence:

> **Under Leyline, Ugin plans, Aurelia commissions and acts, Nissa observes, Momir designs, Elesh conforms, Urabrask compiles, Jin-Gitaxias tests in Tolaria, Isperia judges, Wrenn embodies, Emrakul destroys, and Tamiyo reveals; every precedent is kept in Urborg.**

This sentence is a compact authority map, and it must remain intelligible as the architecture's creation myth.

### 5.4 The sentence test

The following sentences are healthy:

```text
Nissa published the same TelemetryEnvelope to Aurelia and Momir.
Aurelia issued a GrowthIntent for Region A under Ugin's envelope.
Leyline resolved the legal GrowthRequest from the intent and Wrenn's region contract.
Momir used compatible ancestors retrieved from Urborg during the bootstrap curriculum.
Jin-Gitaxias requested a deterministic trial in Tolaria.
Tolaria returned branch measurements.
Isperia selected no-op from the certified evidence.
Wrenn rejected a lifecycle command whose Isperia warrant was invalid.
Tamiyo displayed the rejection without altering the run.
```

The following sentences should trigger review:

```text
Aurelia forwarded a captioned telemetry summary to Momir.
Aurelia requested an attention-like topology.
Nissa recommended a wide bottleneck.
Tolaria rejected the candidate.
Jin-Gitaxias issued the admission token.
Isperia reran the branch with a more favourable batch.
Momir filtered out designs that scored poorly in the current live trial.
Elesh used future task reward to reject a legal graph.
Urabrask inserted a new semantic node during optimisation.
Urborg installed the nearest historical candidate.
Tamiyo changed the learning rate directly.
Leyline imported Aurelia to decide a default action.
```

The sentence test is not a proof, but it is an intentionally cheap architecture lint.

### 5.5 The evidence-routing rule

The naming grammar carries one routing rule important enough to state here in full. Nissa publishes one canonical observation identity independently to Aurelia and Momir (INV-07). Aurelia commissions work from that evidence but is never the channel through which Momir receives it: a `GrowthIntent` carries scope and operational constraints only — insertion region, resource class, urgency, tactical deadline, maturity mode, assurance class — and a deficit diagnosis, topology preference, ancestor choice, or mechanism hint is schema-invalid (INV-09). **Nissa sends the evidence. Aurelia sends only the assignment brief. Momir must never receive reality through Aurelia's caption.**

The code-review question is therefore: **does this field specify the assignment, or does it smuggle a conclusion?** Scope fields commission work; conclusion fields do the designer's job for it, and are prohibited from Aurelia's channel.

For readers who prefer an institution to a mythology, Appendix E (`appendices/newsroom.md`) retells the entire authority model as a newsroom — the same separations in civilian dress, kept in lockstep with this constitution (ADR-0009). The rendering is explanatory only; Leyline contracts, blinding by construction, and the authority tests are the enforcement mechanism.

### 5.6 Dependency consequence

The naming grammar implies two dependency rules:

1. Agents may consume neutral services from Leyline, Tolaria, and Urborg through typed interfaces.
2. Infrastructure must not import agent policy or encode agent-specific preferences.

Examples:

```text
jin_gitaxias → tolaria protocol             healthy
isperia → leyline contracts                 healthy
momir → urborg retrieval API                healthy
nissa → leyline telemetry schema            healthy
aurelia → leyline GrowthIntent schema       healthy

tolaria → isperia policy                    suspect
urborg → momir training code                suspect
leyline → aurelia implementation            prohibited
aurelia → momir graph grammar implementation prohibited
momir → aurelia hidden state                prohibited
urabrask → elesh canonicalisation internals prohibited
tamiyo ← any training-critical code path    prohibited
```

Tolaria may execute a Wrenn host through a neutral host-runtime protocol. Urborg may store Momir records as opaque contract values. Neither requires ownership of the corresponding agent's policy.

### 5.7 Change control

Namespec 2.0 is considered locked for this design (ADR-0008, superseding Namespec 1.0 in its entirety; no legacy aliases):

```text
Leyline
Tolaria
Urborg
Ugin
Aurelia
Nissa
Momir
Elesh
Urabrask
Jin-Gitaxias
Isperia
Wrenn
Emrakul
Tamiyo
```

Changing a codename or moving an authority between names requires an architecture decision record because it changes the project's shared responsibility grammar, package paths, telemetry names, tests, and operational language.

**Reading historical records.** Two names appear in both namespecs with different referents: *Urabrask* (1.0: QA and testing → 2.0: compilation) and *Tamiyo* (1.0: strategic planning → 2.0: witness and revelation). Documents whose content predates ADR-0008 — the archived v4.1 monolith, `docs/concept/reviews/`, the bodies of ADR-0001..0007, and product decision records through PDR-0019 — use Namespec 1.0 names where they name domains at all, and are read through the concordance table in ADR-0008. Those records are never rewritten; corrections create new records (INV-36).

---

<!-- hld: source: v4.1 monolith lines 3094–3142 · amended by ADR-0004 (INV-45 added), ADR-0005 (INV-33 amended), ADR-0008 (Namespec 2.0 renames; content unchanged) -->
## 18. Safety, Correctness and Constitutional Invariants

The following are blocking invariants.

1. **Namespec ownership:** every package has one documented authority, one narrative verb or infrastructure context, and a list of forbidden decisions.
2. **Leyline dependency direction:** contracts and schemas do not import agent implementations.
3. **Tolaria neutrality:** training and execution code applies no candidate utility weights and issues no verdicts.
4. **Mainline–branch parity:** live and counterfactual host steps use the same execution semantics unless the difference is explicitly measured.
5. **Academy exact replay:** identical snapshot plus identical future data produces bitwise-identical traces under Tolaria's Academy-exact determinism contract; non-exact profiles carry measured uncertainty rather than pretending to satisfy this invariant.
6. **Common future:** paired branches receive identical future minibatches and equivalent random streams.
7. **Direct evidence publication:** Nissa publishes one canonical observation identity independently to Aurelia and Momir; Aurelia is not the designer's telemetry intermediary.
8. **Observation binding:** `TelemetryEnvelope`, `GrowthIntent`, `GrowthRequest`, Momir proposals and Tolaria trials reconcile to the same observation, host state, region and snapshot.
9. **Assignment-brief boundary:** `GrowthIntent` contains scope and operational constraints only; diagnosis, topology, ancestry and mechanism hints are schema-invalid.
10. **Deterministic request resolution:** `GrowthRequest` is reproducible from recorded intent, envelope, region contract and grammar profile and can only narrow authority.
11. **No covert request channel:** equivalent intents resolve to one canonical request; irrelevant serialisation, aliases, candidate count and field ordering cannot steer Momir.
12. **No hidden-state coupling:** Momir cannot access Aurelia recurrent state or implementation-specific features.
13. **Bootstrap provenance:** ancestry context is explicit, versioned and independently supplied from Urborg; null ancestry is supported.
14. **Scaffold-versus-control distinction:** removal of ancestry from Momir does not remove reference candidates from blinded evaluation controls.
15. **No-op availability:** every admission and continued-tenancy case includes a measured no-intervention alternative.
16. **No-op convention:** Isperia assigns no-op policy utility exactly zero.
17. **Dual provider blindness:** neither Jin-Gitaxias nor Isperia accesses candidate source during QA interpretation or adjudication.
18. **Evidence–judgement separation:** Jin-Gitaxias cannot issue admission or maintenance warrants; Isperia cannot execute or alter tests.
19. **Raw-to-canonical traceability:** every canonical growth links to the exact raw proposal and Elesh report.
20. **Canonical semantic identity:** every artefact, QA report, Isperia decision and Wrenn embodiment references the same canonical semantic hash.
21. **Compiler semantic preservation:** every Urabrask artefact passes Jin-Gitaxias runtime conformance against the canonical reference.
22. **No branch transplant:** branch-matured growth is deployed only by branch adoption or exact replay.
23. **Budget enforcement:** every constructor, compiler, test plan, branch and maturation phase declares budget and reports spend.
24. **Typed compatibility:** incompatible schema, grammar, insertion, device, telemetry, QA or policy versions fail closed.
25. **Reversible influence:** every non-merged growth can be brought to zero influence without an uncontrolled discontinuity.
26. **Isperia admission warrant:** Wrenn cannot raise a newborn growth above zero influence without a valid warrant.
27. **Isperia maintenance warrant:** ordinary post-commit decay or lysis requires a valid maintenance decision.
28. **Containment distinction:** emergency safety reduction is recorded as containment, not disguised as economic judgement.
29. **Authority enforcement:** Aurelia cannot manage post-commit structure; Emrakul cannot manage unborn structure; Ugin cannot issue local transitions.
30. **Grace-period protection:** contribution-based removal cannot fire before declared blend and holding windows complete.
31. **Complete negative retention:** structural rejects, compilation failures, QA failures, adjudication rejects, no-op decisions and abstentions are stored.
32. **Grouped statistics:** branches from one base trajectory never cross splits or inflate independent sample counts.
33. **Selection–retention consistency:** shared cost terms use shared weights unless a structural difference is documented; admission and retention thresholds are deliberately asymmetric — the admit threshold sits strictly above the retain threshold by a versioned hysteresis band sized against measured execution noise. (ADR-0005)
34. **Telemetry purity:** Nissa observation cannot perturb host training state.
35. **Tamiyo isolation:** disconnecting Tamiyo cannot alter training outcomes.
36. **Urborg append-only history:** corrections create new records rather than rewriting causal history.
37. **Blinding by construction:** source fields are absent from QA and adjudication views rather than merely ignored.
38. **Failure visibility:** invariant breaches fail loudly and are visible through Tamiyo; no silent fallback fabricates valid-looking state.
39. **Declared scaffold state:** every curriculum, QA and confirmatory run records its execution, host-distribution and design-prior regimes.
40. **Independent withdrawal gates:** one scaffold cannot advance because a different scaffold passed its gate.
41. **One-axis confirmatory transition:** withdrawing multiple scaffolds at once requires a declared interaction experiment and completed single-axis controls.
42. **Retained reference capability:** withdrawal removes a production dependency, not the Academy replay harness, acquisition fixtures or blinded reference controls.
43. **Field calibration:** Field evidence is valid only inside a current calibration envelope and carries uncertainty and escalation provenance.
44. **Decision-aware execution gate:** Field-to-Academy accept/no-op disagreement and selection regret must remain inside declared limits, including tail cases.
45. **Lexicographic admission:** the tail-risk veto is adjudicated before any utility comparison and cannot be traded against measured benefit; the assurance class owns the veto operating point. (ADR-0004)

---

<!-- hld: source: v4.1 monolith lines 4323–4395 · renamed by ADR-0008 (Namespec 2.0; content unchanged) -->
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

URBORG
Is where precedents, failures, reference ancestry and lineages are kept.
May supply temporary ancestry and ordinary retrieval.
Must not act on the live host.

UGIN
Plans long-horizon developmental authority.
Must not micromanage local actions.

AURELIA
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
Must not receive Aurelia's hidden interpretation or approve its own work.

ELESH
Makes designs structurally legal and canonical.
May reject malformed structure.
Must not judge task utility.

URABRASK
Compiles canonical designs into executable artefacts.
May optimise implementation.
Must not change meaning.

JIN-GITAXIAS
Tests artefacts and certifies evidence.
May report defects and uncertainty.
Must not issue a verdict.

ISPERIA
Judges certified evidence under declared policy.
May choose no-op.
Must not gather or alter evidence, or trade tail risk against measured benefit.

WRENN
Embodies legal, warranted growth and declares insertion-region contracts.
Must not own a preferred blueprint catalogue or decide whether growth deserves to exist.

EMRAKUL
Safely removes committed structure that has outlived its value.
Must not design or judge newborn growth.

TAMIYO
Reveals the system's account.
Must not steer the system through the act of observing it.
```
