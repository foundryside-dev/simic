# Peer review: the Esper → Simic pivot (2026-08-08)

**Source.** A claude.ai conversation, reviewed as a *pivot document* rather than a
spec — "does the architecture serve the scientific claim, and is the claim
testable at the cost implied." Reviewed against HLD v4.1
([`../simic.md`](../simic.md), then at `docs/concept/simic_new.md`).

> **⚠️ This is a partial record.** It was reconstructed from a paste of the
> shared conversation; the share link itself is not machine-readable. Several
> of John's turns were collapsed in the source and are **missing** — they are
> marked below. Every reviewer turn is present; the prompts that provoked
> roughly half of them are not. Where a reviewer turn opens by agreeing with
> or correcting something, the thing it responds to may be one of the missing
> turns. Read accordingly.

**Reconciliation note.** The thread revises itself repeatedly. Findings filed
into filigree under the `hld-review` label reflect the *final* state of each
argument, not its first statement. The most significant reversals:

| Opening position | Final position |
|---|---|
| Promote Stage 1B to a §28 go/no-go gate | Keep Stage 1A as structural pretraining, **drop 1B–1F entirely** |
| Level 1 (low-rank residual) is the wrong MVP | Adopt the revised **L0–L3 ladder** starting at retrieval over the fixed five |
| Flash-clone landing is a blocking concern | Emphasis withdrawn — "Simic with ordinary blending is still Simic" |
| Karn/Momir is an offline/online split | Karn/Momir is a **tier priced by token**, with retrieval-hit-rate as the load-shedding parameter |
| Momir's gate is "better than no-op" | **Two** gates: ΔU_no-op is the safety gate, ΔU_reference is the pivot gate |

---

## 1. John — opening prompt

> Can you peer review this pivot to Esper

---

## 2. Reviewer — initial review

Reviewing this as a pivot document rather than a spec — i.e. does the
architecture serve the scientific claim, and is the claim testable at the cost
implied.

### The two things I'd fight about

**1. The MVP scopes the experiment to where the null hypothesis is strongest.**

Level 1 (§11.1) is `h' = h + αB_θ(h)` with low-rank / gated-residual envelopes.
Your own control list (§14.1) includes gradient-SVD and least-squares/Gauss–Newton
candidates. For a shape-preserving low-rank residual update against a measured
local deficit, the analytic construction is close to optimal and available in
closed form. Momir has to beat a near-optimal analytic baseline on the one
search space where analysis has a closed form.

The interesting regime for a generator is Level 2/3, where topology is the
choice and no analytic solution exists. So the design either (a) deliberately
runs the hardest test first, which is defensible but should be stated as such
and paired with a pre-registered expectation of a Level 1 null, or (b) risks
producing a null result at Level 1 that says nothing about the actual
hypothesis, and burns the programme's credibility before Level 3 is reachable.
§28 doesn't distinguish these. It should, because the correct response to
"Momir lost to Gauss–Newton at Level 1" is *proceed to Level 2*, and that will
not be the instinctive reading in a review meeting.

**2. Stage 1B is your kill gate and it's filed as a training stage.**

Everything downstream assumes Nissa's `TelemetryEnvelope` contains enough
information to determine a useful repair. If activation/spectral/gradient
statistics at an insertion region don't predict which reference seed helps,
Momir degenerates into a learned prior over the reference population — a smart
random search — and no amount of Elesh/Urabrask/Augustin rigour recovers that.

Stage 1B ("predict reference utility, shock, cost and lifecycle outcome from the
same Nissa context") is exactly the right instrument, and it's cheap: frozen
host, no branch rollouts beyond building the labels once. It should be promoted
out of §16 into §28 as a go/no-go with a declared threshold, run before Phase C.
"Telemetry underspecification" currently sits in the risk table (§26) with a
mitigation of "add more features," which is not a gate.

### Technical points

**Admission/retention hysteresis is the wrong shape.** §13.11 drops shock from
the retention utility and §18.33 pushes toward shared cost weights to prevent
install–lyse oscillation. That's backwards. Shared weights with no threshold
band means a growth sitting near the boundary gets admitted and lysed
repeatedly as execution noise moves the estimate — which is precisely the
oscillation you're trying to prevent. You want deliberate asymmetry: admit
threshold strictly above retain threshold, i.e. a Schmitt trigger. Cooldowns
(§26) are a time-domain patch for a threshold-domain problem; they suppress the
frequency without removing the instability. Make the hysteresis band an
explicit, versioned Augustin policy parameter and measure the width against
observed σ_exec.

**Continued-tenancy evidence is structurally weaker than admission evidence and
the document doesn't say so.** §2.4 states the attribution problem correctly.
But once a growth is committed, the honest counterfactual — the host that never
received it — requires having run a parallel no-op branch from the admission
snapshot for the entire tenure. That's a permanent doubling of training cost per
committed growth. The re-adaptation branch you actually specify measures
*replaceability at horizon H*, which is a different quantity and is dominated by
the choice of H. Right now §13.11 gives retention the same utility formalism as
admission with one term deleted, which implies parity of evidence that doesn't
exist. I'd add an explicit statement that maintenance decisions operate under a
weaker evidentiary standard, and correspondingly bias Emrakul toward SEDATE over
LYSE (which you already do mechanically, but for safety reasons rather than
epistemic ones).

**No cost model.** For a document that makes budgets contractual at every
boundary, there is no number anywhere for what fraction of total training
compute the growth machinery consumes. Two things drive it and they compound:
(a) §14.9 correctly makes the base host trajectory the independent statistical
unit, so power for the headline claim scales with independently seeded full host
runs, not with branches; (b) the §16 interaction matrix has eight cells. Eight
cells × usable n × Academy-exact rollouts is the programme budget, and it's
parked in Open Decisions (§27.15). The statistics are right and the implication
doesn't propagate. I'd put a worked estimate in §22.11 before Phase A — even an
order-of-magnitude one — because if it comes out at 40× host-equivalent compute
per admitted growth, the answer isn't "optimise later," it's "change the QA
hierarchy now."

**The covert channel you're policing isn't the one with bandwidth.** §21.3 tests
invariance to irrelevant serialisation, field ordering, aliases, candidate
count. Good tests, but the *permitted* fields carry the signal: insertion region
plus resource class plus urgency class is a substantial, legitimate description
of where and how big the deficit is. If Narset and Momir co-train, Momir learns
a mapping from (region, budget class) → structure family, and that mapping is
not distinguishable from the collusion you're trying to prevent. Coarse enums
reduce bits; they don't close it, and closing it entirely would require Narset
not to choose the region, which defeats the point.

Worth separating two harms that §18.11 currently conflates. *Operationally*, a
channel through legitimate fields is fine — Narset is supposed to constrain the
space. *Scientifically*, it breaks the ablation in §6.18, because "replace
Narset with a different controller emitting the same canonical intent" no longer
isolates anything if the intent itself is sufficient. The invariance test
(§21.3) is the one that matters and it's the one most likely to fail for benign
reasons.

**Canonicalisation is sound-but-incomplete and the diversity metrics inherit
it.** True semantic equivalence over numeric graphs isn't decidable; Elesh
implements normalisation under a declared rewrite set. §21.6's
"non-equivalent-graph hash separation" is testable, but "equivalent-graph hash
equality" only holds for rewrites you implemented. Consequence: "duplicate rate
after Elesh canonicalisation" (§22.3) systematically understates redundancy, and
functional-space diversity is the only metric you can trust. Say this in §13.8
or the metric will be quoted as if it were exact.

**`ablated_context` is underspecified.** §10.3 says germination telemetry comes
from the ablated path. With multiple resident growths, ablate-all describes a
host that no longer exists and never will again; ablate-region-only is a
different measurement with different attribution properties. §9.2 has the field
but no semantics. Pick one, and note the extra forward pass per observation in
the cost model.

**Minor FSM collision.** §12.1 has QUALIFYING before BLENDING, and §12.4 refers
to a "qualification window" inside HOLDING. Two distinct things sharing a word,
in a state machine, with property tests to be written against it.

**Diversity vs index invariance.** §9.5 forbids "candidate 3 of 12" while
`diversity_requirement` sits in the same record. Calibrated set diversity from K
i.i.d. latent samples is hard; sequential conditioning needs the index. You flag
the exception but default to the setting that makes the objective difficult.

### The rename

§23.2 inverts the meaning of the most-referenced name in the existing codebase.
Tamiyo currently *is* the tactical controller across ~80k lines, commit history,
test names, telemetry labels and your own recall. Reassigning the name to the
strategic layer and calling the old one `LegacyTamiyoController` maximises
confusion for a year. Cheaper and safer: Tamiyo stays tactical, the new
strategic layer gets a new name. That's one ADR against a locked namespec,
versus a permanent ambiguity in every incident discussion that references
anything pre-pivot.

### What's actually load-bearing and new

Two things, specifically.

**The three-axis `ScaffoldState` with independently owned gates and the one-axis
confirmatory transition rule.** Not the idea of curricula — the insistence that
execution determinism, host-trajectory variance and design-prior sparsity are
orthogonal scaffolds that must not be withdrawn in lockstep, with a named owner
per gate and a fail-closed on undeclared multi-axis transitions. That's a
reusable methodological artefact, and the smell "one global `curriculum_stage`
withdraws all three together" is the kind of thing that catches a real bug.

**And the framing that withdrawal removes a production dependency, not a
capability** — Academy-exact as retained metrology rather than deleted training
wheels. That inverts the usual failure mode, where the calibration harness rots
the moment it stops being on the critical path.

The rest — no-op at policy utility exactly zero, blinding by construction,
grouped splits, complete negative retention — is correct but not novel; it's
standard experimental hygiene that most systems of this kind simply don't do.

Happy to go deeper on any of these, or to do a separate pass purely on §21's
test suite against the §18 invariants (my quick read says **invariants 11, 14
and 41 have no corresponding test that would actually fail**).

---

## 3. John — the Esper precursor result

> for what it's worth the precursor (esper) demonstrated that seed telemetry
> does contain enough to make intelligent decisions (in esper's case about which
> of a number of preset blueprints [norm, attn, conv etc]) — from that tamiyo
> made decisions on when to intervene, where to intervene (among the three seeds
> on the host), what alpha waveform and blendspeed, whether to fossilise or
> prune etc — the problem was that we couldn't tweak the reward function to
> fully incentivise that behaviour — although you and I worked in claudecode to
> prove that the reward function did have the information in it

---

## 4. Reviewer — response

That changes the shape of my first objection, mostly in your favour — and it
sharpens the second one.

**Stage 1B becomes a regression test, not a gate.** If Esper's Tamiyo could pick
among norm/attn/conv from seed telemetry, then M0/M1 are reproducing a known
result in the new formalism. That's a much better position than an unknown.
Concretely: **Esper's blueprint selector should go into §14.1 as a named
permanent blinded control**, alongside the reference seeds. "Old Tamiyo picks a
preset" is the sharpest possible baseline for the generation hypothesis, it
costs nothing to run, and if Momir can't beat it you learn that at Stage 1
rather than Stage 9. The document currently has random, analytic, retrieval and
oracle controls but not the one control you already have working code for.

The bar has moved though. 1-of-5 discrimination is ~2.3 bits; conditioning a
generator over a graph space needs the telemetry to be informative about
*structure*, not merely discriminative among a small labelled set. So keep 1B,
just treat its floor as known.

**The document is motivated on the wrong failure.** §2 lists moving target,
curriculum, blueprint, attribution, authority. None of those is "we couldn't
shape the reward to incentivise the behaviour we could prove the reward
contained." That's the actual empirical driver and it's absent, which matters
because §28's success criteria are written against the stated problems rather
than the real one.

Stated properly, the pivot is: **replace a reward function with measured
counterfactuals.** Paired branches from one snapshot over identical futures
cancel the ordinary-training variance that was swamping your gradient signal.
The difference between branches *is* the intervention effect. That converts an
RL credit-assignment problem into a supervised ranking problem for Momir, and
it's the strongest available justification for the entire expensive apparatus.
§22.11's cost accounting is really answering "what did we pay to turn RL into
supervised learning" — which is also a far better framing for an SES3 briefing
than "QA cost dominance."

**But the cancellation doesn't reach Narset, and Narset is where Esper actually
died.** Candidate-vs-no-op at fixed *t* is cheaply branchable and pairs cleanly.
"Intervene at *t* versus *t*+500" requires branches that diverge for 500+ steps,
at which point the pairing degrades and you're back to disentangling
intervention effect from trajectory drift — the original problem, unchanged.
Same for fossilise-vs-prune, worse, for the reasons in my earlier note about
tenancy evidence.

§17.2 answers this in one line: "enumerated or oracle local actions."
Enumerating intervention times with full rollouts per candidate time is the
single most expensive item in the programme, and it maps directly onto the thing
that already failed. It deserves a subsection, a cost estimate, and an honest
statement that Narset's timing problem is *not solved* by the counterfactual
machinery — it's made attributable (Stage 6 holds Momir/Urabrask/Augustin fixed
so tactical failure can't be blamed elsewhere) and better-labelled, but not
structurally dissolved.

Which raises a question worth answering explicitly in the doc: **how much of
Narset's improvement over Esper's Tamiyo comes from the architecture versus from
the training procedure?** Attributable failures and dense imitation targets are
training-procedure wins that could arguably have been retrofitted to Esper. The
architecture's irreducible contribution is elsewhere — generation, authority
separation, provider blindness. Being precise about this makes the pivot more
defensible, not less, because it stops a reviewer from asking it first.

**The capability you built and didn't notice.** Augustin's explicit rule-driven
policy *is* the Esper reward function, promoted to a versioned, hand-editable
artefact. And because `QualityReport`s are immutable, stored in Sarpadia, and
Augustin consumes nothing else — **you can re-adjudicate the entire historical
corpus under new weights with zero retraining and zero GPU time.** Sweep λ, μ,
ν, ξ, ω across every decision the system has ever made and see how the admission
and tenancy history changes.

That is a direct, specific answer to "we couldn't tweak the reward function," and
it's nowhere in the document. §22.6 lists "policy sensitivity to declared
weights" as a metric without noting it's now retrospective and nearly free. I'd
make it a first-class capability in §13.11 and give it a line in §19.2 — an
operator-facing counterfactual policy sweep is exactly the kind of thing that
makes the evidence/judgement split earn its cost to someone who hasn't read
Appendix E.

**And it hardens the MVP-scoping objection.** Esper's demonstrated result is
about discriminating among *structurally distinct families*. Level 1 collapses
the space to a shape-preserving low-rank residual — precisely the region where
that capability doesn't transfer and where Gauss–Newton has a closed form. You'd
be starting the new programme in the one corner where the old programme's
positive result is irrelevant and the analytic baseline is strongest. If there's
a way to make Level 2 the MVP target with a restricted operator whitelist, I'd
take the extra Elesh/Tezzeret complexity over that.

---

## 5. John — *[turn missing — collapsed in source]*

Context inferred from the reply: proposed keeping Simic's shape but using
**Momir v1 as a fetch-one-of-five stub**, and asked about rehydrating Esper /
Karn rather than pivoting.

---

## 6. Reviewer — containment

Simic, with Momir v1 as the fetch-one-of-five stub. The containment argument
settles it.

Karn is Momir running offline. Karn generates candidates, Urabrask validates
them, good ones land in a library that Tamiyo selects from. In Simic terms
that's Momir populating Sarpadia out-of-band, plus retrieval as the fast path at
request time — §10.6 and §15.5 already permit exactly this. **Esper is an
execution mode of Simic. Simic is not an execution mode of Esper**, because
Esper's library entries are context-free assets and the context-matching happens
in the tactical policy.

Which is the actual lock-out, and it isn't infrastructure:

**Esper-Lite's reward-shaping work doesn't transfer, because the action space is
different.** Tamiyo's action is roughly (when, where, which blueprint, blend
target, waveform, speed, fossilise/prune) — a joint categorical-plus-continuous
action with delayed outcomes. That joint structure is a large part of why the
credit assignment was intractable. Simic deletes the blueprint dimension from
the tactical policy entirely and hands structure selection to Momir, adjudicated
by counterfactual against no-op. Narset's residual problem is timing, placement
and blend management. Strictly smaller.

So if you fix Esper-Lite's reward first, you fix a reward over an action space
Simic doesn't have. That's the thing you'd be locked into — not the plumbing.

**The stub MVP is better than a compromise.** Five fixed blueprints, retrieved
rather than generated, everything else Simic-shaped, gives you a direct A/B
against Esper-Lite with the host, seeds and blueprint set held constant. The
only moved variable is *where structure selection lives*. If reward shaping was
the disease, that experiment shows it cheaply, and it's a defensible result on
its own.

It also fixes the scoping objection I raised earlier. Level 1 as written
(`h + αB_θ(h)`, low-rank residual) starts in the corner where Gauss–Newton has a
closed form and where Esper's demonstrated telemetry-discrimination result
doesn't transfer. Norm/attn/conv-light/conv-heavy are structurally distinct
families — exactly where the existing positive result lives. Revised ladder:

```
L0  retrieval over the fixed five        (Esper-Lite content, Simic interfaces)
L1  bounded mutation around those five
L2  constrained genotype
L3  typed graph
```

Each rung is a real experiment against the rung below plus no-op.

**Cost of Simic-shaped over Esper-shaped at MVP.** Elesh and Tezzeret must
exist, but for five known-good blueprints canonicalisation is near-identity and
compilation is what Kasmina already does — plumbing, not algorithms. The
Urabrask/Augustin split is real work you need regardless, since it *is* the
reward replacement. Tolaria snapshot/branch/replay is the expensive item and
it's required for either path. The genuine incremental tax is the
`GrowthIntent`/`GrowthRequest` split, the deterministic resolver, and
observation routing: a schema, a pure function, and their tests.

Two snags to check before committing.

**Flash-clone landing collides with §14.6.** A candidate matured in a branch is
co-adapted to that branch; copying it into a live host that followed a different
trajectory is the transplant the invariant forbids. Fast landing therefore
requires *branch adoption* as the deployment mechanism — which is §27.3, still
open. The flash-clone advantage isn't free; it's conditional on resolving that
decision toward adoption, with whatever hardware-placement and checkpoint cost
that implies. If you end up on restore-and-replay instead, you've paid the
replay cost and the staleness window reopens.

**And §12.4's minimum blend and holding windows are written assuming gradual
alpha.** A candidate that can land in one or two steps will trip them. The
windows exist to stop premature contribution-based removal, which is still a
real concern — but the mechanism needs to be re-derived for a regime where alpha
isn't the thing taking time.

**One thing worth instrumenting deliberately.** The
upstream-partial-blend / downstream-fossilise / upstream-pull sequence is
host-internal scaffolding — a temporary structure that alters the representation
a permanent structure trains against, then withdraws. That's the same pattern as
Appendix F, discovered by the policy rather than designed in. It survives the
authority split (upstream stays pre-commit, so Narset keeps it; downstream
commits to Emrakul independently), but only if Narset can hold a growth at
partial alpha across a long window without the grace/qualification machinery
forcing it up or out. Check that it can. If flash-clone landing becomes the
default, also check whether the behaviour still has room to appear — it may need
slow blending as an available mode, not just a legacy one.

---

## 7. John — *[turn missing — collapsed in source]*

Context inferred from the reply: reframed the claim as **bespoke fit** rather
than speed, and described Karn as a 24/7 NAS producing a tagged,
BSDS-characterised, reusable library.

---

## 8. Reviewer — bespoke fit and amortisation

That reframes it, and I had the emphasis wrong. Speed isn't the claim — bespoke
fit is. Let me redo the argument on that basis.

**Karn's library is Simic's reference population, and the comparison is already
in the doc.** A 24/7 NAS producing tagged, BSDS-characterised, reusable
structures is exactly max_{r∈R} U(r) — the best general-purpose structure
available for this state. §11.4 already defines
ΔU_reference = U(c) − max_r U(r) as one of Momir's three margins. **That
quantity is the Esper-vs-Simic question, stated numerically. It should be §28's
headline criterion**, because everything else in the document is machinery for
measuring it credibly.

So the rehydration answer doesn't change — Esper remains inside Simic as the
control arm — but for a better reason than I gave. It's not that Karn is
Momir-offline. It's that the amortised library is the thing bespoke design has
to beat, and you want it permanently in the branch pool, not left behind in the
previous codebase.

**The cost bar is steeper than I said, and it's the real objection to Simic.**
Esper amortises generation and validation across every future use of a library
entry. Karn's compute is a background constant; the BSDS is written once and
read many times. Simic amortises neither. A frankenblueprint used once carries
the full Urabrask cost for one use, and a per-candidate safety characterisation
that can never be reread. **Per-intervention QA cost is therefore structurally
higher in Simic by roughly the library's reuse factor** — which for Esper is
presumably large and which you can measure from existing logs. Bespoke fit has
to beat generic fit by at least that margin. §22.11's "amortised cost per
successful intervention" is the right metric and it's buried at the bottom of a
list.

**The partial escape is already specified:** canonical semantic hashes,
equivalence classes and Sarpadia retrieval mean a bespoke candidate that recurs
gets served from history rather than regenerated. Retrieval-hit-rate over time
is then an emergent measurable and a genuinely interesting one — it tells you
what fraction of the problem space is actually one-off versus recurrent. High
hit rate means Simic converges toward Esper and Esper was right. Low hit rate
with positive ΔU_reference is the strongest possible result for the pivot. Worth
adding to §22.3 explicitly.

**Staleness is now the decay of the value proposition, not an operational
nuisance.** If the value is fit-to-state, then a candidate designed at *t* and
landed at *t*+δ is fitted to a state that no longer exists, and its utility
decays toward that of a generic structure — toward the library. So **the
staleness curve is literally the rate at which Simic degrades into Esper.**

That gives you a clean experiment with a crossing point: measure U(c_t)
evaluated at *t*+δ against max_r U(r) evaluated at *t*+δ, sweep δ. Where the
curves cross is the maximum latency budget under which bespoke design is worth
doing at all. That number determines design latency, compilation budget, QA
horizon and whether asynchronous compilation is viable — all currently open
decisions (§27.5, §27.13) with no principled way to set them. It's cheap to
measure once Phase D exists and it should be a Stage 5 deliverable.

I'd also drop my flash-clone emphasis. Simic with ordinary blending is still
Simic. Though there's a hypothesis worth testing while you're there: a candidate
function-matched to the current host state might produce *less* integration shock
than a generic blueprint, which would shorten the blend and reduce staleness
exposure. If true, it's a second measurable advantage and it compounds with the
first. If false — if bespoke candidates shock as much as stock ones — that's
mild evidence that Momir is re-deriving generic structure rather than fitting,
which is a useful early warning that nothing else in the harness would give you.

**One thing Simic loses that Esper had.** The tag grammar and the BSDS made
Esper's selection *legible*: "attention, because the tags say rank-deficiency
and the sheet says don't use it here." Momir emits a graph. The diagnosis is
implicit in the design and not readable. §9.7's `RawGrowthGraph` has no "why"
field, and **it shouldn't get one** — a Momir-authored rationale would be an
editorial channel pointed backwards, and it'd be unfalsifiable besides.

The correct replacement is that **the BSDS becomes Urabrask's `QualityReport`**:
measured behaviour rather than declared traits. Epistemically better, and it's
why the QA/judgement split earns its cost. But it's produced per candidate and
never reread — which is the same amortisation problem again, and worth stating
in those terms in §13.10 so the cost is attributed to the right decision rather
than looking like QA overhead.

---

## 9. John — *[turn missing — collapsed in source]*

Context inferred from the reply: raised **recursion / hierarchy** — nesting
Tamiyo over multiple Narsets, and scaling toward a "Mythos" host.

---

## 10. Reviewer — the upward contract

The recursion is the right instinct and the doc doesn't support it yet. One
specific gap, and it's an interface, which means it has to be right before you
train anything.

**There's no upward contract.** §9.1's `StrategicEnvelope` with its
`region_allocations[]` is already nestable — that's the downward half and it
mostly works as-is. But upward, §13.4 says Tamiyo consumes "coarse Nissa
summaries," which hardcodes one level. For recursion you need a **`RegionReport`
whose shape is identical whether the producer is a leaf region or an
intermediate Tamiyo aggregating children.** That schema is the whole scaling
story and it doesn't exist in the document.

**And it must be produced by Nissa, not by the subordinate.** "Here's everything
you need to know about my sector, I took out what might confuse you" is a
subordinate compressing the evidence its own parent will use to evaluate it.
Tamiyo learns "gave token to X, things got better" — if X controls the
measurement of "better," X's budget-seeking gradient runs straight through its
own performance signal. That's the same evidence/judgement collapse the entire
constitution is built to prevent, rotated ninety degrees into the vertical.

The fix follows the existing rule exactly: **Nissa aggregates and reports state
upward; Narset reports only actions and spend.** Same photograph/assignment
split, applied to the reporting chain. It also means the aggregator is neutral
infrastructure with a versioned compression function rather than a learned
component inside a policy that benefits from the compression — which matters,
because the compression is lossy by design and someone will want to learn it.

**Your exploration allowance is an identification strategy, not just
exploration.** Tamiyo can't be counterfactually grounded at scale — you cannot
branch a Mythos host, and sibling interventions interact through a shared
substrate, so the paired-branch machinery that grounds Momir and Augustin simply
doesn't reach the allocation layer. What replaces it is breadth: many children,
many rounds, repeated allocation. That's a contextual bandit, and unbiased credit
assignment needs variation in allocation that isn't caused by the same telemetry
driving the decision. `exploration_allowance` (§9.1) is exactly that
randomisation. It should be documented as the mechanism that makes Tamiyo's
learning signal *identifiable*, not as a nice-to-have knob — and the doc should
state plainly that **Tamiyo operates under a weaker evidentiary standard than
Augustin, for structural reasons.**

**The token economy is a delayed-feedback control loop and nobody's specified
its gain.** Spend token → destabilise → propagate up → allocate fewer next
round. With L layers, aggregation lag, and growth maturation time inside the
loop, you have exactly the conditions for oscillation — 40 tokens, then 3, then
40. §13.4's "slower cadence than Narset" generalises to a **required cadence
ratio per layer**, and that ratio, plus cooldowns as damping, is a stability
parameter you should declare and test rather than tune later. Cheapest test: a
3-region CIFAR fixture with an artificially long report lag, checking that
allocation converges rather than rings.

**The O/Q split is already what makes LoRA-later possible; protect it
deliberately.** Momir conditions on Nissa's telemetry (invariant statistics)
plus the resolved `GrowthRequest` (concrete tensor contract). That factorisation
is exactly right for cross-architecture transfer — the policy sees
architecture-invariant state and gets shapes handed to it explicitly.
Esper-Lite's "40 obs per seed" died because those two were fused. **Add an
explicit §18 invariant: telemetry and policy conditioning are functions of
region statistics, never region layout or width.** It costs nothing now and it's
unrecoverable if violated in a trained artifact.

**Karn/Momir stops being a split and becomes a tier, priced by token.** At Mythos
scale you cannot run bespoke design per Narset per intervention — the
amortisation argument from before reasserts itself hard. Library retrieval for
the common case, Momir for the expensive case, and the boundary set by token
price. Which means **the retrieval-hit-rate metric isn't just diagnostic, it's
the load-shedding parameter.** That's a coherent scaling story and it makes the
Esper-vs-Simic question resolve into "where's the tier boundary" rather than
"which one."

**Two things to build now despite the 1:1 MVP:** the `RegionReport` schema with
a Nissa aggregator, and a multi-region test fixture. A Tamiyo with one child is
degenerate and will never exercise the allocation interface — you'd discover the
schema is wrong at the point where retraining is most expensive.

---

## 11. John — Tamiyo has no job yet

> right, and the reality is that tamiyo doesn't have a job in simic as written
> (I'll write it for you right now: `int receiveTacticalPicture(StrategicEnvelope se) { return 1.0; }`),
> since cifar isn't complicated enough to need more than one narset, there's no
> need for a strategic monitor to watch the narsets and make sure they don't trip
> over each other too much — tamiyo will snap into place when we graduate cifar
> to something like tinystories and can justify a few controllers with say a few
> hundred seeds

---

## 12. Reviewer — the stub must vary

Agreed on the sequencing — building a real Tamiyo for one Narset is building
against a degenerate case, which is worse than not building it. But the stub has
a specific failure mode worth avoiding.

**`return 1.0` is a constant allocator.** Narset then learns in an environment
where the envelope never varies, which means it never learns to *read* the
envelope. When Tamiyo snaps in at TinyStories and starts varying budgets,
Narset's inputs shift distribution on an axis it has no representation for, and
you retrain it.

Cheap fix: **the stub varies.** Fixed schedule, or better, randomised within
declared bounds — 40 tokens, then 8, then 25, on a seed. Costs nothing, and it
does three things at once. Narset learns envelope-conditional behaviour from the
start. §21.12's authority tests (Narset cannot exceed an envelope) get something
real to bite on. And §22.7's timing-regret metrics become measurable under
scarcity, which is the regime that actually matters — behaviour under a generous
constant budget tells you very little about behaviour when tokens are rationed.

**A randomised stub is also the right permanent control.** When learned Tamiyo
arrives it needs a baseline, and §28.10 says exactly this: better than uniform or
heuristic allocation. Build the random allocator now, keep it forever as the
null.

**The other thing to keep alive is `RegionReport`.** With one Narset the schema
is trivially satisfiable, so producing it is a few hours of work and no design
pressure — which is precisely why it'll be wrong. Two mitigations, both cheap:
define it with a synthetic 3-region fixture that never runs a real experiment
but forces the aggregator to actually aggregate, and add a §21 test asserting
the schema is **producer-agnostic** (leaf and intermediate produce the same
shape). Otherwise the interface gets designed at TinyStories under delivery
pressure, with a trained Narset already depending on it.

**On the graduation point:** TinyStories is the right next rung for the reason
you gave, but note it moves two axes at once — task complexity and multi-region
allocation. §16's one-axis rule applies. Either a multi-region CIFAR fixture
first (artificial, cheap, isolates allocation), or single-Narset TinyStories
first (isolates task), then combine. Given Tamiyo is the piece with no
counterfactual grounding, I'd take multi-region CIFAR — you want allocation
debugged where branches are still affordable.

---

## 13. John — *[turn missing — collapsed in source]*

Context inferred from the reply: proposed inverting the experiment to **180
candidates on one host** rather than spreading counterfactuals across many
hosts; raised Narset's credit assignment over ~200 steps and self-corrected
mid-sentence; noted "Momir blows it and Narset gets the nastygram";
checkpoint-and-rehydrate to skip warmup; the degenerate architectures Esper
lifted from 10% to 40%.

---

## 14. Reviewer — the 180-on-one-host inversion

The 180-candidates-on-one-host inversion is the strongest idea in this thread.
It's not a compromise, it's the correct experimental design for Momir, and it's
worth being precise about why.

Because you're holding the host fixed, all 180 branches share one snapshot and
one future. That's a complete ranked neighbourhood over the same state — 180
candidates plus no-op, fully ordered, one measurement round. §11.4 already says
train on the ordered neighbourhood rather than the winner. At 180-wide you get
**listwise ranking with a dense signal, not pairwise-with-noise.** Compare that
with 180 hosts × 8 counterfactuals: 180 nearly-independent problems, 8 samples
each, most of the compute spent re-establishing that different hosts are
different.

There is a real cost: Momir learns the conditional distribution over designs
given a state, but sees very few *states*. That's overfitting-to-state, and the
fix is your own — sweep RNG seeds per host, then impairment types, then
architectures. Just be explicit that **the ladder is measured in distinct host
states seen, not gradient steps**, because 500 candidates on one state is one
state.

**On Narset's credit assignment, your mid-sentence correction is the right
answer** and it's stronger than you gave it credit for. The 200-step problem is
only a problem if the label is "did the episode go well." It isn't. Augustin's
`AdmissionDecision` is a per-intervention verdict grounded in a measured
counterfactual, available the moment QA completes. So Narset's supervision is
dense: at every decision point, either it commissioned and the pool measurably
beat no-op (or didn't), or it waited and you can — with one extra branch —
measure whether waiting was right.

That's not RL over 200 steps. It's **supervised, per-step, with a counterfactual
ground truth.** Which is precisely the thing Esper-Lite couldn't construct, and
it's why the reward-shaping problem dissolves rather than gets solved.

The residual genuinely-long-horizon parts are timing (intervene now vs. in 50
steps) and tenancy. Those don't dissolve. But they're a much smaller surface
than "learn everything from episode return," and they can be attacked separately
once the per-step behaviour is competent.

**Your "Momir blows it and Narset gets the nastygram" observation deserves to be
a stated design property, not an aside.** Narset never bears Momir's failure,
because Augustin sits between them: a bad pool resolves to NO_OP, and Narset's
commission was still correct. Attribution is structural. Add it to §6.18 — it's
a concrete payoff of the authority split that a reader would otherwise mistake
for bureaucracy.

**Sequencing, with one correction.** Momir solo → Narset on frozen Momir →
unfreeze both is right, and Stage 6 already specifies the middle step. But the
unfreeze is a co-adaptation risk, and §17.2's anti-collusion tests were designed
for exactly this moment. Run the §21.3 invariance tests *before* unfreezing to
get a baseline, then again after. If Momir's output distribution starts varying
with semantically irrelevant properties of Narset's intent, you'll catch it as
drift from a known-good measurement rather than as an absolute threshold you'd
have to guess.

Also worth pre-declaring: **unfreeze one at a time.** Simultaneous unfreeze of
Momir and Narset is a two-axis transition and §16's own rule applies to it.

Two practical notes.

**Checkpoint-and-rehydrate to skip warmup** is obviously right, but every host
that shares a pretrained checkpoint is *one base trajectory* under §14.9 — same
statistical split, not independent samples. Easy to violate accidentally when
the whole point is reuse. Worth a test.

**The degenerate architectures that Esper lifted from 10% to 40% are your best
fixtures** and I'd use them early rather than as a late impairment stage. Large,
unambiguous headroom means candidate ranking is dominated by signal rather than
noise, which is exactly what a curriculum wants at the start — and you already
have the Esper result to compare against on the same hosts.

---

## 15. John — Momir's passing grade

> yes I recognise that momir will be 'underwhelming' and I might have overstated
> how good he will be out of the box, but if it becomes a problem, that's a lever
> we can control — if I get overeager and try to push momir in while he's still
> too green and narset can't converge specifically because momir is performing
> worse than 'do nothing' we can just go back to momir and add more host seeds,
> more configurations, more sizes, more impairment and more counterfactuals — our
> 'passing grade' for momir should be 'on a random seed/impairment/problem momir
> reliably picks something that's better than do nothing' — if we can hit that
> level, we can trust it to work on narset's factory floor

---

## 16. Reviewer — two gates, and legibility of failure

That's the right gate, and it's essentially §16's Stage 1F written as a pass
condition. Two refinements worth making before you calibrate it.

**"Better than do nothing" is the wrong bar for Narset's purposes — "better than
the reference population" is.** If Momir clears no-op but loses to the fixed
five, Narset can converge fine and you've built Esper with extra steps. §11.4
already defines both margins; **positive ΔU_no-op is the safety gate, positive
ΔU_reference is the pivot gate.** They're different graduations and it's worth
naming them separately, because you can legitimately let Narset start training
against a Momir that has only cleared the first one.

**Narset can converge on an unreliable Momir, provided the failure is legible.**
What breaks convergence isn't Momir being bad — it's Momir being bad in a way
Narset can't *predict* from telemetry. If Momir fails on a recognisable subset of
states, Narset learns to WAIT there, which is a correct policy and one you
actively want it to have. If Momir fails at, say, 30% uniformly at random,
Narset's action values get uniformly diluted and it learns nothing about timing.

So the diagnostic when convergence stalls isn't "Momir's pass rate is too low,"
it's **"is Momir's failure predictable from the observation?"** — which is
directly measurable, since you have the paired data. If yes, keep going and let
Narset learn the refusal. If no, go back and add host diversity. That
distinction tells you which lever to pull instead of guessing.

Which means **Momir's gate needs a variance term, not just a mean.** "Reliably
picks something better than no-op" should be reported as pass rate **stratified
by impairment type, architecture and severity** — because a 70% aggregate that's
95% on two families and 20% on a third is a very different object from a uniform
70%, and only the first one is safe to hand to Narset. §22.3's "scaffold-free
positive-candidate coverage" is the right metric; just make sure it's reported
per-stratum. §22.12 already asks for worst-decile on main endpoints, which is the
same instinct.

One thing that makes this cheaper than it sounds: the coverage measurement is a
byproduct of Momir's own training runs. You're already generating ranked
neighbourhoods per state; pass rate per stratum falls out of data you have. No
extra branches.

---

## 17. John — Momir learns the classics from counterfactuals

> actually, that's a great point, momir won't *need* a library, because every
> seed will include a counterfactual that says 'oh and here's what would have
> happened if you'd used norm' — every static blueprint is taught every training
> round, momir will learn the classics

---

## 18. Reviewer — the ancestry scaffold never needs erecting

Right — and it's cleaner than the doc's version. §11.4 has ancestry supplied
through `BootstrapAncestryContext` and then withdrawn on a schedule, with the
whole `withdrawal_schedule_id` / `curriculum_stage` apparatus around it. If the
references are always present as *outcomes* rather than as *inputs*, that
scaffold never gets erected, so it never needs withdrawing.
**`BootstrapAncestryContext` = null from day one, and §16's design-prior axis
reduces to a constant.**

Worth being precise about what changes: **Momir learns the classics through the
ranking signal, not through the conditioning channel.** It never sees a norm
graph as an input to copy; it sees that norm scored 0.31 on this state while its
own candidate scored 0.18. That's a fundamentally different learning problem —
it teaches *when the classics win*, not *what they look like* — and it's the
signal you actually want, because "when does a generic structure beat a bespoke
one" is exactly the tier-boundary question from earlier.

**One thing you lose: structural literacy.** Stage 1A's reconstruction task
exists because a randomly-initialised generator emitting typed DAGs mostly emits
garbage, and reference reconstruction is a cheap way to teach the grammar before
spending rollout budget. Ranking-only means Momir's early candidates are
near-uniformly invalid and every branch round is dominated by Elesh rejections.
That's a warmup cost, not a design flaw, and it's separable — reconstruction
against canonical graphs needs no Tolaria time at all. So: **keep 1A as pure
structural pretraining, drop 1B through 1F entirely.**

The cost side is real but bounded. Five permanent reference branches per state,
forever, on top of the candidate pool. At 180 branches that's under 3% —
negligible. It matters more at production scale, where you'd want reference
measurement sampled rather than exhaustive.

And the useful side effect: **§18.14** (removal of ancestry from Momir doesn't
remove references from evaluation controls) **becomes unviolatable by
construction rather than by test**, since the references only ever existed as
controls. One fewer invariant that depends on somebody remembering it.

---

## 19. John — *[turn missing — collapsed in source]*

Context inferred from the reply: proposed training a **critic on the ranked
neighbourhoods** and having Momir search against it; a corpus built by
perturbing around the big five; a "soft online" phase.

---

## 20. Reviewer — the critic, and four things to get right

Yes, and the data-efficiency argument is stronger than I put it.
Maximum-likelihood-on-winners uses the top few percent of the corpus; a critic
trained on ranked neighbourhoods uses *all* of it, including — especially — the
catastrophic ones. Same three or four weeks of compute, an order of magnitude
more usable signal. It also means **§6.13's "failures are training data" stops
being a principle you have to defend on cost grounds and becomes the majority of
your training set.** And the 180-on-one-state design is close to ideal for it:
dense listwise supervision over a shared state, which is what ranking losses
want.

Four things to get right.

**It collides with the constitution and needs an ADR.** §17.1 permits a utility
head as training-only; §13.7 says Momir must not approve its own work.
Search-against-critic at inference is exactly what those were written to forbid,
so you need to draw the line deliberately rather than let it erode. The
defensible version: **Momir's critic may be a pure function of (state, design)
and must have no access to measurements from the current pool.** A learned prior
over designs is not self-approval — it's what any competent generator does
internally. Filtering on live results is. That distinction survives review; "we
relaxed it because search works better" doesn't.

**Momir's critic and Urabrask's field surrogate are the same object with
different authorities.** §17.4 predicts utility, shock, cost and uncertainty from
design and state. So does this. Keep them separate anyway, and say why in the
doc: Urabrask's carries a decision-aware calibration gate and its errors corrupt
evidence, while Momir's is a search heuristic whose errors cost compute and
nothing else — every candidate still goes through Elesh, Tezzeret, Urabrask and
Augustin regardless. Same architecture, possibly the same initial weights,
different obligations. **Sharing one instance would let a search heuristic
inherit evidentiary authority.**

**The real failure mode is search exploiting critic error, and you already have
the fix.** Hard optimisation against a learned model finds the model's blind
spots, not good designs — standard offline model-based optimisation pathology.
The answer is pessimism: **search against Û − κσ rather than Û**, which is the
identical form to §14.4.1's conservative adjudication margin. Ensemble
disagreement gives you σ cheaply. Practical consequence: the critic must be
trained to be well-calibrated *off-support*, not merely accurate on-support,
which means the corpus needs deliberate coverage of bad regions — and random
perturbation gives you that for free.

**Which makes perturbation radius the corpus's most important parameter.**
Perturbing around the big five samples a ball, so novelty is bounded by the
radius and the critic only learns the cliff edge if some samples go over it.
Stratify it: a majority tight (dense signal near the classics), a minority wild
(calibration at the edges, and the only place genuine novelty can appear).
Uniform radius gives you a critic that's confident everywhere it's been and
confidently wrong past the boundary — the exact condition under which
pessimistic search fails.

Two smaller notes. **The corpus is a seed, not a finished artifact:** the moment
Momir searches, it queries regions the corpus doesn't cover, so budget for
refitting on measured results from Momir's own selections. That's what your
"soft online" phase is, and it's the part that closes the loop.

And there's a tension worth measuring rather than guessing at: **search costs
inference latency, latency is staleness, and staleness is the decay of the
bespoke-fit advantage.** More search buys a better candidate for a state that has
moved further away. The crossing-point experiment from earlier — where U(c_t)
evaluated at *t*+δ meets max_r U(r) — sets your search budget directly. It's the
same number twice, which is a good sign the framing is right.

---

## 21. John — the writer and the critic

> well, I'd argue that momir does need a critic in the same way a writer needs a
> critic, but that doesn't mean you don't have the new york times review corner —
> the judge still decides what sends but momir needs to be able to judge what
> they want to put forward — in a sense the judge isn't judging 'the quality of
> the submission', it's looking at the host and the graph and going 'are you out
> of your fucking mind? If I let that go, Tolaria is going to roll us back to the
> dawn of time'

---

## 22. Reviewer — the editor, and lexicographic admission

That's the right frame and it resolves the constitutional tension cleanly — but
the newsroom analogy you're reaching for isn't the critic, it's **the editor**. A
writer self-edits: drafts six openings, keeps one, submits it. Nobody thinks that
usurps the publishing editor. That's Momir searching against its own prior, and
§6.4 already licenses it — "Momir establishes possibility" doesn't mean Momir
must submit its first draft.

The line that holds is the one from before, restated in your terms: **Momir may
use any judgement formed *before* the pool is measured; it may not use judgement
formed *from* the pool's measurements.** Self-edit before submission, yes.
Withdrawing a submission after seeing the fact-checker's report, no — that's
§13.7's smell, and it's a real one because it lets Momir launder selection
through Urabrask's evidence without accountability.

Your characterisation of Augustin is doing something more interesting than
clarifying the split, though, and I think it's actually a **correction to the
document**.

Augustin as written is a *scalar comparator* — §13.11 computes u_admit, ranks,
picks the max, checks it clears no-op. That's a quality judgement. What you're
describing is closer to a **risk judgement**: not "which of these is best" but
"is any of these going to destroy the host." Those are different functions and
the document conflates them under one utility expression.

The eligibility gate (§10.10) is the risk half and it's currently binary — hard
defects make a candidate ineligible, full stop. But "will this blow up the host"
is not a defect flag, it's a **tail estimate**. A candidate can pass every
conformance check and still be the one that costs you a rollback, and the ξR_c
risk term buried in a weighted sum can't express that, because a large enough
measured benefit will always outweigh it. What you want is a separate veto on
tail risk, evaluated *before* utility comparison and *not tradeable against it*.

That's a genuine structural point: **admission should be lexicographic, not
scalar.** Survive the tail test first; compete on utility second. It also gives
the assurance class something real to do — it sets the veto threshold rather than
just adjusting evidence completeness requirements.

And it produces a much cleaner division of labour than "designer proposes, judge
ranks":

- **Momir optimises expected value**, and can afford to be wrong often, because
  it costs compute.
- **Augustin bounds worst case**, and must be conservative, because it costs the
  host.

Both use learned estimates of the same underlying quantity. They're not
redundant — they're optimising **different functionals of the same
distribution**. That's a far better justification for the split than "separation
of concerns," and it's the version that survives someone asking why you need two
models predicting utility.

Worth noting the Tolaria rollback is what makes this asymmetry real: the downside
isn't a bad growth, it's losing the trajectory. So **the veto should be priced
against snapshot distance**, which the system already tracks.

---

## 23. John — who gets the politely worded letter

> and this is quite interesting because it changes the crime and punishment view
> as well — when tolaria detects INF/NaN/the end of days, it rolls back and sends
> out a politely worded letter; that should go to the judge instead, because
> narset is only responsible for 'is there a problem' and momir is only
> responsible for 'here, try this' — the only one who could possibly be
> responsible is augustin

---

## 24. Reviewer — containment accountability

Right — and it fixes a real hole. **§18.28 has emergency containment "logged and
reviewed" with no named owner, which means in practice nobody.** The rollback is
evidence that a warrant was issued wrongly, and warrants are Augustin's sole
output. Nothing else in the system could have prevented it.

Three consequences worth building in.

**The rollback event needs a route back to the decision, not just to the log.**
`AdmissionDecision` already carries `evidence_digest`, `selected_semantic_hash`,
`adjudication_policy_version`, and the eligibility results. So a containment
event can name the warrant that authorised the growth, the policy version in
force, and — critically — **the specific eligibility checks that passed and
shouldn't have.** That's a defect report against a *policy*, and it's actionable
in a way "candidate X was bad" isn't.

**It's the veto's only real training signal, and it's rare by construction.** If
the tail veto works, rollbacks approach zero, which starves the thing that would
improve it. Two mitigations, both cheap: keep deliberately harmful candidates
**permanently** in the QA pool (§14.1 has them; make them permanent rather than
curriculum-stage), and record **near-misses** — candidates that passed the veto
with thin margin and then produced large integration shock without triggering
rollback. Those are dense where rollbacks are sparse, and they're the same
distribution's shoulder.

**Blame lands on the policy version, not on Augustin-the-component.** With the
initial rule-driven Augustin this is literally true — a rollback means the
declared thresholds were wrong, and the fix is an ADR and a version bump. That's
the correct granularity: it makes the failure attributable to a specific,
inspectable, versioned artifact rather than to a black box. It also means
retrospective re-adjudication (the free policy sweep from earlier) can ask
directly: *under the revised policy, would this warrant have issued?* That's a
**regression test for judgement**, which is not a thing most systems can
construct.

Worth adding to §15.3's failure taxonomy — there's INTEGRATION_SHOCK but nothing
for containment-triggering catastrophe, and **they shouldn't share a code**,
because one is a cost and the other is a veto failure.

The one refinement: **Tolaria still owns detection and the rollback itself.** It
must — waiting for adjudication while the host is producing NaNs would be absurd.
Tolaria acts, then reports to Augustin. **Detect-and-contain is mechanical;
accountability is judicial.** That keeps §13.2's neutrality invariant intact,
which matters, because "Tolaria decides when to roll back on safety grounds" is a
much smaller step to "Tolaria has opinions about candidates" than it looks.

---

## 25. John — mechanical or policy, and the lineage

> right, stuff is either mechanical or it's policy, and the conceit of the system
> is that anything that needs judgment or would benefit from it is a policy
> learning from experience — we already recognise that LLMs are going to be
> smarter than humans, why wouldn't we use policies to tune models in ways that
> let us fuck with the minutia (esper started because I asked the question 'huh,
> why don't we use DRL to teach a policy how to tune models' which lead to esper
> and blueprints which lead to me going 'actually, rather than blueprints, let's
> use diffusion to grow something bespoke' to the current system)

---

## 26. Reviewer — the learnability boundary

The mechanical/policy split is the right organising principle, but the document
quietly makes a **third** distinction that's worth naming, because it's where the
interesting constraints live.

**Not everything that needs judgement should be learned.** Augustin needs
judgement — that's the whole argument for splitting it from Urabrask — and yet
§17.5 says it starts rule-driven and stays that way until QA evidence is
trustworthy and partitions are sealed. Same for Emrakul. That isn't a concession
to engineering conservatism; it's structural. Momir and Narset are graded against
counterfactuals **by something else**. Augustin is the terminal authority, so a
learned Augustin grades itself, and the only external signal is rollbacks —
which, if the veto works, approach zero. **You can only safely learn a policy
that something else can measure.** That's the actual boundary, and it's sharper
than mechanical-vs-policy.

Which makes **the tail veto the interesting case** rather than an afterthought.
It's the one place where judgement is essential, learning is desirable, and the
grading signal is structurally sparse. Worth flagging in the doc as a known-hard
problem rather than letting it sit inside "Augustin applies policy."

**On the lineage:** the through-line from "why don't we use DRL to tune models"
to blueprints to bespoke generation is coherent, and the DRL framing is doing
real work in a way the pivot slightly obscures. Esper-Lite failed on RL credit
assignment. Simic's answer isn't better RL — it's **replacing the return signal
with measured counterfactuals**, which converts most of the problem to supervised
learning. Momir becomes ranking, Narset becomes per-step supervised
classification with counterfactual labels, Augustin becomes explicit rules. The
genuinely irreducible RL is Tamiyo's allocation and Narset's timing, and both are
small compared with what you started with.

That's worth saying plainly somewhere, because "we tried DRL, it didn't converge,
so we built something more complicated" is the uncharitable reading, and it's
wrong. **The accurate version is that the machinery exists to manufacture the
supervision signal RL couldn't extract. The counterfactual apparatus isn't
overhead around a policy learner — it's the thing that makes the policy
learnable.**
