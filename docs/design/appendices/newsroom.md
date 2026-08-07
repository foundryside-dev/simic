<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: ../00-INDEX.md -->
<!-- hld: source: v4.1 monolith lines 4476–4615 -->
## Appendix E — The Newsroom Principle

### E.1 Purpose of the analogy

The newsroom model is useful because this architecture is fundamentally concerned with **epistemic separation**: who may observe, who may commission work, who may author a solution, who may verify it, who may judge it, who may integrate it, and who may later correct or withdraw it.

A single controller that observes the host, diagnoses the deficit, selects a topology, generates parameters, evaluates itself, approves deployment and decides retention is equivalent to a newsroom in which one person assigns the story, rewrites the notes, authors the conclusion, fact-checks it, publishes it and destroys the corrections file. It may be fast, but neither evidence nor failure attribution remains trustworthy.

The newsroom analogy therefore explains why the architecture contains more roles than a minimal implementation apparently requires. It is not bureaucracy for its own sake; it is a defence against authority collapse.

### E.2 Role mapping

| System role | Newsroom analogue | Legitimate question |
|---|---|---|
| Tamiyo | Editor-in-chief / managing editor | Which desks, beats and investigations receive resources? |
| Narset | Assignments editor | Is there a story here, which region owns it, by when, and under what scope and budget? |
| Nissa | Reporting, photography and data desk | What was actually observed? |
| Momir | Writer / investigative journalist | What coherent candidate follows from the evidence and assignment? |
| Elesh | Copy, standards and house-form desk | Is the submission structurally legitimate, coherent and conformant? |
| Tezzeret | Production, layout and publishing pipeline | Can canonical copy become an executable edition without changing meaning? |
| Tolaria | Newsroom production environment, CMS and test presses | Where are ordinary and experimental editions produced and replayed? |
| Urabrask | Fact-checking and QA | Are the claims and executable behaviour supported by evidence? |
| Augustin | Publishing editor | Does this run, get returned, deferred, retested, rejected, or spiked? |
| Kasmina | Live-edition integrator | How is accepted material placed into the running edition safely? |
| Emrakul | Corrections, withdrawal and retirement | What published material should be sedated, corrected, deprecated or removed? |
| Sarpadia | Morgue and archive | What did we report, try, reject, retract and learn? |
| Oona | Front page, broadcast desk and presentation | What does the operator or reader see? |
| Leyline | Stylebook and editorial constitution | What language, records and procedures govern the newsroom? |

### E.3 Assignment brief versus editorial angle

The most important review test is:

> **Does this field specify the assignment, or does it impose an editorial angle?**

Legitimate assignment fields include:

```text
insertion region
resource class
urgency class
tactical deadline
maturity mode
assurance class
```

System-resolved constraints include:

```text
input/output tensor contract
grammar profile
exact budget derived from the authorised class
compatible compiler and verifier versions
permitted evaluation horizons
```

Prohibited editorial-angle fields include:

```text
preferred topology family
deficit diagnosis
suggested ancestor
expected mechanism
rank or width hint
attention-like / convolution-like / norm-like recommendation
free-form message to the designer
```

Narset may see Nissa's evidence because it must decide whether to commission work. It must not become the channel through which Momir sees that evidence. The assignments desk is allowed to say “investigate Region A under this scope.” It is not allowed to say “write a story proving rank collapse and conclude that attention is the answer.”

### E.4 The source-routing rule

```text
Nissa observes host state S
    ├──→ TelemetryEnvelope O ──→ Narset
    └──→ TelemetryEnvelope O ──→ Momir

Narset emits GrowthIntent I
Leyline resolves GrowthRequest Q
Sarpadia optionally emits ancestry A

Momir designs from O + Q + optional A
```

The following are constitutional failures:

- Narset forwards a rewritten observation to Momir;
- Nissa emits a recommended solution;
- Momir reads Narset hidden state;
- the request resolver infers a diagnosis;
- an ancestor is selected by Narset rather than the curriculum or retrieval policy;
- or the observation referenced by Momir differs from the one that triggered Narset's commission.

### E.5 The right to spike the story

A commissioned story does not have to run. Likewise, a `GrowthIntent` does not imply that any candidate must be admitted.

The chain contains multiple legitimate stopping points:

- Narset may choose `WAIT` and issue no assignment.
- Momir may produce no structurally viable proposal.
- Elesh may reject malformed designs.
- Tezzeret may fail to compile faithfully.
- Urabrask may find runtime defects or inadequate evidence.
- Augustin may select no-op, reject, defer or require retest.
- Narset may abort stale growth before integration.
- Emrakul may later withdraw committed growth under a maintenance warrant.

This is the editorial equivalent of spiking a story, returning copy, publishing a correction, or withdrawing an obsolete article. The architecture is intentionally not a content mill that must publish something every time an assignment is raised.

### E.6 Archive discipline

A credible newsroom archive contains accepted stories, abandoned drafts, corrections, retractions, failed investigations and source notes. Sarpadia must likewise retain:

- stock reference seeds and their outcomes;
- Momir children and parents;
- structural rejects;
- compilation failures;
- QA defects;
- Augustin rejections and no-op decisions;
- stale integrations;
- maintenance withdrawals;
- and scaffold-withdrawal status.

A winners-only Sarpadia is not institutional memory. It is mythology.

### E.7 Where the analogy stops

The newsroom model is not a literal organisational chart and should not determine implementation details by itself.

- Nissa may be automated and highly mathematical; it is not a human reporter.
- Elesh's structural proofs are stronger than ordinary copy editing.
- Tolaria is both the ordinary training substrate and the counterfactual production environment.
- Augustin's utility policy is formal and versioned, not editorial taste.
- Kasmina and Emrakul operate on a neural host, not a publication.

The analogy is used to explain and lint authority boundaries. Leyline schemas, dependency rules, tests, blinding and deterministic provenance remain the source of architectural truth.

---

