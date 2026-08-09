<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: ../00-INDEX.md -->
[← HLD index](../00-INDEX.md)

<!-- hld: source: v4.1 monolith lines 4616–4720 -->
## Appendix F — The Scaffold Withdrawal Pattern

### F.1 Why this is constitutional

The architecture repeatedly faces problems whose unrestricted form is initially too noisy or sparse to teach anything reliable:

- Tolaria cannot attribute branch differences while execution noise is unknown;
- Aurelia cannot learn intervention timing when every host trajectory diverges for unrelated reasons;
- Momir cannot learn useful design when almost every unconstrained graph proposal is invalid or useless.

The response is not to pretend the unrestricted problem is easy. It is to establish a controlled classroom in which causal signal exceeds nuisance variation, calibrate the instruments there, and then remove the classroom constraints one at a time.

This is a uniform theory of generalisation rather than four unrelated training tricks.

<!-- hld: added 2026-08-09 (ADR-0012, simic-eb0cf50deb) -->
The posture distinguishes **three kinds of training wheels**, because they withdraw differently:

1. **Measurement scaffolds** constrain the *world* so instruments can be calibrated (Academy exactness, repeated host trajectories, the anchor corpus, the field surrogate). Withdrawal means the cheap instrument carries a measured error bar.
2. **Capability curricula** constrain the *action or design space* while competence grows (reference ancestry, the candidate-level ladder, the §16 schools). Withdrawal means competence demonstrated without the constraint.
3. **Authority maturity ladders** keep an authority rule-driven before it is (maybe) learned (Isperia, Emrakul, Ugin). These are governed by the learnability boundary — only learn a policy something else can measure — and **may correctly never withdraw: a rule-driven terminal authority is a success state, not a stalled curriculum.**

The **conversion rule** is the default fate of every wheel: withdrawal removes a production dependency and *produces a permanent instrument* (INV-42 generalised) — the harmful fixtures, the Ugin null allocator, Academy replay as the metrology lab, the reference seeds and the predecessor's blueprint selector as blinded controls. The wheels do not come off; they become the test rig.

### F.2 The four primary scaffolds

Every scaffold axis is a three-rung ladder with the same named rungs (ADR-0012): **TIGHT** — the classroom, constraint fully active, ground truth manufactured here; **LOOSE** — constraint partially lifted *with the tight instrument still auditing*; **FREE** — constraint withdrawn as a production dependency and converted to a permanent instrument. The rungs map onto the `ScaffoldState` enumerations directly:

| Axis | TIGHT | LOOSE | FREE |
|---|---|---|---|
| Execution | `ACADEMY_EXACT` | `CALIBRATED_STOCHASTIC` | `FIELD` |
| Host distribution | `REPEATED_ACQUISITION` | `HELD_OUT_IN_FAMILY` | `OPEN_DISTRIBUTION` |
| Design priors | `REFERENCE_ANCESTRY` | `ANCESTRY_DROPOUT` | `NULL_ANCESTRY` |
| Anchoring | `FULL_DECISION_FANOUT` | `ADMISSION_ANCHORED` | `UNANCHORED` |

The **measuring stick** at every rung is decision-aware, never merely numeric: does the looser instrument make the same calls as tight ground truth — rank correlation, accept/no-op agreement, selection regret, tail-error detection, uncertainty coverage. The **transition metric** is a pre-registered gate on that stick, counted at the statistical-unit level (INV-32), owned by the named gate owner, one axis per confirmatory transition.

| Scaffold | Protects against | Acquisition regime | Relaxation | Withdrawal gate | Retained role |
|---|---|---|---|---|---|
| Tolaria Academy exactness | Attribution error | Bitwise-exact paired worlds | Repeated stochastic worlds and surrogate calibration | Ranking, decision, uncertainty and tail criteria | Causal oracle, CI, regression and disputed-case retest |
| Repeated host trajectories | Host variance | Fixed acquisition seeds and identical trajectories | Held-out in-family initialisations and one-axis variation | Stable tactical timing and lifecycle outcomes | Policy-language and regression fixtures |
| Urborg reference ancestry | Generator collapse | Reconstruction, imitation and bounded mutation | Ancestry dropout and partial de novo design | Structural validity and positive coverage with null ancestry | Blinded controls and historical precedent |
| Anchor corpus (ADR-0011) | Unvalidated tenancy evidence and unlabelled commissioning decisions | Per-decision, per-action full-trajectory counterfactual fan-out on a declared seed set, decision points scheduled or random (policy-independent) | Admission-anchored only, then sampled subsets | Production instruments decision-calibrated against anchored ground truth, counted at seed level (INV-32) | Audit hosts, disputed-tenancy escalation, periodic anchor refresh |

### F.3 Tolaria's training wheels

Bitwise replay is deliberately strict because it establishes the reference equality:

$$
\text{branch difference} = \text{intervention effect}.
$$

Field execution instead operates under:

$$
\text{branch difference} = \text{intervention effect} + \epsilon,
$$

where $\epsilon$ must be measured, modelled and priced. The progression is not exactness followed by sloppiness. It is:

```text
unknown noise
    ↓
eliminated noise
    ↓
measured noise
    ↓
modelled and tolerated noise
```

Academy exactness therefore remains available after withdrawal. It defines the unit of causal measurement, calibrates Field QA, diagnoses divergence and adjudicates cases too close to call under stochastic execution.

### F.4 Independent gate ownership

The primary gate owners are:

- **Jin-Gitaxias** certifies Tolaria execution and Field-surrogate evidence against Academy results;
- **Isperia** authorises use of that evidence for a declared assurance class and applies uncertainty margins;
- **Aurelia curriculum evaluation** certifies host-distribution generalisation;
- **Momir curriculum evaluation** certifies null-ancestry design competence;
- **Jin-Gitaxias** certifies anchor-corpus calibration evidence, and **Isperia** authorises unanchored maintenance evidence for a declared assurance class (ADR-0011);
- **Leyline** validates that the run's declared `ScaffoldState` matches the actual configuration.

No owner may certify another dimension merely because its own dimension is ready.

### F.5 One-axis withdrawal and interactions

The default confirmatory sequence is:

```text
Academy exact + repeated hosts + ancestry
    ↓ relax execution only
Field-calibrated + repeated hosts + ancestry
    ↓ relax host distribution only
Field-calibrated + held-out hosts + ancestry
    ↓ withdraw ancestry only
Field-calibrated + held-out/open hosts + null ancestry
```

The order may change, but only one scaffold changes per confirmatory transition. After the main effects are known, declared interaction experiments test whether scaffold effects are correlated.

Transitions are earned in both directions (ADR-0012): every scaffold declares a **re-tightening trigger** — the named degradation of its measuring stick that escalates the axis back a rung. A stick that only ever ratchets looser is not a gate; it is a schedule wearing a gate's clothes.

A multi-axis transition without those controls is not necessarily unsafe, but it is scientifically uninterpretable and cannot support an attribution claim.

### F.6 Adding a new scaffold

Any future proposal for restricted grammar profiles, fixed blend schedules, synthetic tasks, single-slot hosts, known-rank repairs or other training wheels must answer (the anchor corpus filed its answers in ADR-0011):

```text
Which of the three kinds is it, and what are its tight, loose and free rungs?
What failure mode does this scaffold protect against?
What is the Learn-the-Land regime?
What is the controlled relaxation path?
What decision-aware measuring stick compares each looser rung against tight?
What measurable gate permits withdrawal, and what re-tightens it?
Who owns that gate?
What remains as a reference after withdrawal?
What other scaffolds might it correlate with?
How will ambiguous Field cases escalate?
```

A scaffold proposal without those answers is an undocumented permanent assumption.

### F.7 Review shorthand

The review question is:

> **Where is the classroom, where is the graduation test, and where is the retained laboratory?**

If the classroom can never be left, the system has not generalised. If the laboratory is dismantled after graduation, the system can no longer calibrate or explain itself.
