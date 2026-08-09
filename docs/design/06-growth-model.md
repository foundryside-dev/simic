<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: 00-INDEX.md -->
[← HLD index](00-INDEX.md)

<!-- hld: source: v4.1 monolith lines 1570–1815 -->
## 11. Generated Growth Model

### 11.1 Growth progression

The growth language expands only after the preceding level passes reliability gates.

### Level 1 — Generated phenotype inside a universal envelope

The first implementation uses a shape-preserving residual form:

\[
h' = h + \alpha B_\theta(h).
\]

Momir generates parameters, rank, gates, scale, permitted width, and trainability mask inside a constrained envelope such as:

- a low-rank linear update;
- a small gated residual multilayer perceptron;
- or another typed residual microcell.

This removes semantic blueprint labels while keeping the search space safe and measurable.

### Level 2 — Generated constrained genotype

Momir may choose from a safe graph grammar:

- hidden width;
- number of internal stages;
- activation family;
- gating pattern;
- residual topology;
- sparse connectivity;
- normalisation placement;
- low-rank factorisation;
- and trainability mask.

Elesh canonicalises semantically equivalent graph forms into one identity.

### Level 3 — Generated typed graph

Momir emits a small directed acyclic graph over whitelisted operators. Elesh proves contract compliance and canonicalises it. Urabrask compiles it.

The grammar remains bounded by:

- operator whitelist;
- maximum nodes and edges;
- maximum parameter and memory cost;
- shape-preserving insertion contracts;
- deterministic execution requirements;
- reversible zero-influence behaviour;
- and declared gradient-flow rules.

Arbitrary code generation is not required.

### 11.2 One-shot and nursery modes

### One-shot mode

- Momir emits the complete final growth.
- Wrenn holds it frozen after admission.
- Only alpha and lifecycle state may change.
- This is the cleanest test of generative construction as a final answer.

### Nursery mode

- Momir emits structure, birth parameters, and a trainability mask.
- Wrenn grants bounded isolated maturation.
- Host and growth optimisation streams remain explicit and separately accounted.
- The growth is re-qualified against the current host before blending.
- Maturation spend is charged to the candidate.

Nursery mode is the default ecological configuration because it preserves safe behind-the-host maturation. One-shot mode remains a required scientific ablation.

### 11.3 Candidate identity

Three identities are distinct:

1. **Raw identity:** the exact graph Momir proposed.
2. **Canonical semantic identity:** the graph after Elesh’s semantics-preserving canonicalisation.
3. **Executable artefact identity:** Urabrask’s device-specific implementation.

Urborg stores all three. Jin-Gitaxias tests canonical semantics through Urabrask’s executable artefact in Tolaria. Isperia judges the resulting evidence. Wrenn embodies the same canonical semantic identity selected by Isperia.

Two compiled artefacts may implement the same canonical growth. Two raw graphs may canonicalise to the same semantic identity. Candidate diversity is therefore measured primarily in canonical and functional space, not raw syntax or compiler artefact space.


### 11.4 Reference-seed bootstrap and scaffold withdrawal

Momir is not initially asked to invent useful neural machinery from an unrestricted grammar with no examples. The first curriculum supplies a small, versioned **reference population** of known mechanically viable microcells held in Urborg, such as:

- normalisation-derived cells;
- attention-derived cells;
- convolution-derived cells;
- low-rank residual cells;
- gated residual cells;
- and synthetic known-repair cells.

These are represented as canonical graphs and outcome records, not permanent blueprint enums. Wrenn can embody them because it can embody any legal warranted growth, but it does not own them as an internal stock library.

The reference population has three bootstrap roles:

1. **Demonstration:** teach graph literacy, typed flow, zero-influence structure, parameter scaling and viable initialisation.
2. **Ancestry:** give Momir local neighbourhoods in which to learn mutation and recombination before de novo invention.
3. **Counterfactual control:** remain in the branch pool so a mutation must beat its parent, compatible traditional seeds, and no-op rather than receive credit merely for functioning.

The staged progression is:

```text
M0  structural reconstruction of reference graphs
M1  prediction and imitation of reference behaviour by host context
M2  bounded local mutation around one parent
M3  recombination across compatible ancestors
M4  ancestry-optional and explicitly de novo proposals
M5  withdrawal of reference ancestry from Momir's production input
```

At every stage, Jin-Gitaxias tests the child, its parent, compatible reference seeds, retrieval and analytic controls where available, and mandatory no-op under identical Tolaria futures. Urborg retains the ordered neighbourhood, not only the winner:

```text
child A > parent > reference B > no-op > child C
```

Momir may therefore learn three increasingly demanding margins:

\[
\Delta U_{\text{no-op}} = U(c),
\]

\[
\Delta U_{\text{parent}} = U(c) - U(p),
\]

\[
\Delta U_{\text{reference}} = U(c) - \max_{r \in \mathcal R} U(r).
\]

The scaffold is considered withdrawn when Momir is evaluated with `BootstrapAncestryContext = null`. Conventional reference seeds may remain permanently in sealed or routine experiments as blinded controls. This preserves the scientific question—whether Momir beats known alternatives—without making those alternatives an enduring production dependency.

Aurelia never chooses the ancestor. The curriculum harness assembles ancestry context from Urborg under a fixed manifest. Otherwise the old blueprint selector would simply reappear inside the tactical controller.

The analogy to Aurelia's own curriculum is deliberate: both subsystems first learn a restricted causal language on repeated, interpretable examples, then face the broader CIFAR-scale distribution without the classroom scaffold.

---

## 12. Lifecycle and Authority Model

The target lifecycle is:

```text
DORMANT
  → GERMINATED
  → MATURING or QUALIFYING
  → BLENDING
  → HOLDING
  → ACTIVE
  → COMMITTED
  → SEDATED or DECAYING
  → DORMANT
```

Permitted early exits include:

```text
GERMINATED → ABORTED → DORMANT
MATURING → ABORTED → DORMANT
QUALIFYING → REJECTED → DORMANT
BLENDING → DECAYING → DORMANT
HOLDING → DECAYING → DORMANT
ACTIVE → DECAYING → DORMANT
```

### 12.1 State meanings

| State | Meaning | Ordinary authority |
|---|---|---|
| **DORMANT** | Slot empty and available | Wrenn mechanics; Aurelia may request germination |
| **GERMINATED** | Isperia-admitted growth installed at zero influence | Aurelia |
| **MATURING** | Optional isolated optimisation executed in Tolaria | Aurelia within budget |
| **QUALIFYING** | Jin-Gitaxias QA followed by Isperia adjudication or re-adjudication | Aurelia requests; Jin-Gitaxias tests; Isperia judges |
| **BLENDING** | Alpha rises under a bounded schedule | Aurelia |
| **HOLDING** | Target alpha reached; grace and qualification window | Aurelia, constrained by current Isperia warrant |
| **ACTIVE** | Growth serves under local pre-commit lifecycle control | Aurelia |
| **COMMITTED** | Growth becomes maintained structure | Ownership transfers to Emrakul |
| **SEDATED** | Influence reduced while dispensability or replacement is assessed | Emrakul under a maintenance warrant |
| **DECAYING** | Alpha ramps to zero before recycling | Emrakul, or Aurelia before commitment |
| **DORMANT** | Slot recycled; occupant-specific state reset | Wrenn |

### 12.2 Transition authority

Wrenn is the sole executor of growth-state transitions and enforces these rules:

- Ugin never issues a lifecycle transition.
- Aurelia may issue only pre-commit transitions.
- Emrakul may issue only post-commit maintenance transitions.
- Jin-Gitaxias issues QA evidence, never lifecycle authority or admission tokens.
- Isperia issues admission and maintenance warrants, never physical transitions.
- Tolaria executes optimisation and tests, never lifecycle preferences.
- A transition that raises influence requires a valid Isperia warrant.
- A transition that removes influence for ordinary economic reasons requires the appropriate authority and, post-commit, an Isperia maintenance warrant.
- Emergency containment may reduce influence without prior economic adjudication only when a declared safety invariant is breached; Tolaria detects and contains mechanically, the event is recorded as containment (`CONTAINMENT_CATASTROPHE`, never `INTEGRATION_SHOCK`), and Isperia adjudicates it back to the admitting warrant and policy version (INV-28, ADR-0010).

### 12.3 Commitment handoff

Commitment is an ownership boundary, not merely a label.

Before commitment:

- Aurelia manages the growth as an intervention under evaluation.

After commitment:

- Emrakul manages its physical maintenance as part of the host’s established structure;
- Isperia remains the authority for continued-tenancy judgements;
- Jin-Gitaxias remains the authority for certified maintenance evidence.

Aurelia may ask Emrakul to request review but may not directly lyse committed growth. Emrakul may identify replacement pressure but may not ask Momir for a specific replacement without a new Aurelia request under a valid Ugin envelope.

### 12.4 Grace-period protection

A growth cannot be condemned merely because low early alpha yields low measured contribution.

- utility does not accrue during initial blend unless explicitly defined;
- ordinary removal is blocked during the minimum blend and holding windows;
- QA and adjudication data partitions are declared in advance;
- and the qualification window is pre-registered.

### 12.5 QA and adjudication are not lifecycle states

Jin-Gitaxias and Isperia can be invoked at several lifecycle points, but neither becomes the owner of the growth.

```text
Aurelia or Emrakul requests review
        ↓
Jin-Gitaxias specifies and certifies tests
        ↓
Isperia issues a verdict or warrant
        ↓
Aurelia or Emrakul requests a legal physical transition
        ↓
Wrenn executes it in Tolaria
```

This prevents an evidence subsystem or judge from quietly becoming a lifecycle controller.
