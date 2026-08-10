<!-- hld: simic HLD chapter — NEW content, not decomposed from the v4.1 monolith · index: 00-INDEX.md -->
<!-- hld: created 2026-08-11 from the concept panel's P10 carve-out (../concept/reviews/2026-08-11-morphogenesis-concept-panel.md) -->
[← HLD index](00-INDEX.md)

# Related Work and Novelty Position

## Why this chapter exists

Before this chapter the design corpus cited **zero external work anywhere**. That
is a defect with two distinct costs. The reviewer cost is obvious: a submission
claiming "generated (not selected) structure" as an irreducible contribution
(`01-claim.md#26-the-empirical-driver`) against a dense published literature on
growing networks during training will be rejected on novelty before it is read on
method. The design cost is subtler and larger: **without a map of what is already
solved, the programme cannot tell which of its components carry engineering risk
and which carry research risk**, and it will therefore schedule them as if they
were the same thing.

This chapter is a positioning instrument, not a literature review. It grades each
component of the system against prior art so that phase sequencing, effort
estimation and the pre-registration can distinguish *building a known thing* from
*testing an unknown one*.

## The grading scale

| Grade | Meaning | The risk you are carrying |
|---|---|---|
| **Established** | Commodity. Multiple independent implementations, settled failure modes. You are implementing, not researching. | Engineering only. Schedule risk is estimable. |
| **Adapted** | A well-understood technique used one hop from the setting in which it was validated. | Transfer. The technique works; whether it works *here* is unmeasured. |
| **Speculative** | No direct precedent — *or* precedent exists but has never been validated in the way this design requires. | Research. Outcome is genuinely unknown and schedule is not estimable. |

"Speculative" is not a criticism. It names where the contribution is, and where
the programme should expect to spend.

## The map

| Component | Design locus | Grade |
|---|---|---|
| Zero-influence residual envelope $h' = h + \alpha B_\theta(h)$ | `06-growth-model.md#111-growth-progression` (Level 1) | **Established** |
| Alpha blend schedule; reversible influence (INV-25) | `06-growth-model.md#12-lifecycle-and-authority-model` | **Established** |
| Compilation preserving semantics, verified by runtime conformance (INV-21) | `domains/urabrask.md` | **Established** |
| Best-of-$K$ candidate pooling; diversity in functional space | `domains/momir.md#candidate-modes` | **Established** |
| Canonicalisation → semantic hash → identity (INV-19, INV-20) | `domains/elesh.md`, `06-growth-model.md#113-candidate-identity` | **Established** |
| Generating parameters/rank/gates from a conditioning vector | `domains/momir.md`, Level 1 | **Adapted** |
| Host telemetry as the design conditioning signal (INV-07) | `domains/nissa.md` → `domains/momir.md` | **Adapted** |
| Mutation and recombination over a reference population (M0–M5) | `06-growth-model.md#114-reference-seed-bootstrap-and-scaffold-withdrawal` | **Adapted** |
| Nursery: isolated maturation behind the host | `06-growth-model.md#112-one-shot-and-nursery-modes` | **Adapted** |
| Retrieval conditioning over prior candidates | `domains/urborg.md` | **Adapted** |
| Training the generator by ranking over measured pools | `programme/learning.md` (Momir) | **Adapted** |
| Typed-graph generation (Level 2–3), online, mid-training | `06-growth-model.md#111-growth-progression` | **Speculative** |
| **Counterfactual screen as the growth criterion** | `07-counterfactual-engine.md` | **Speculative** |
| Staleness / moving-target under a design latency budget | `01-claim.md#21-the-moving-target-problem` | **Speculative** |
| Provider blindness (INV-17, INV-37); mandatory no-op at utility zero (INV-15, INV-16) | `domains/isperia.md` | **Speculative, low-cost** |

---

## Established — the parts that are already solved

**The insertion contract.** Level 1's shape-preserving residual with a scalar gate
is not a novel form; it is the convergent answer several literatures reached
independently. [ReZero](https://arxiv.org/pdf/2003.04887) (Bachlechner et al.,
UAI 2021) gates each residual branch with a single zero-initialised parameter and
shows it satisfies initial dynamical isometry.
[LayerScale](https://openaccess.thecvf.com/content/ICCV2021/papers/Touvron_Going_Deeper_With_Image_Transformers_ICCV_2021_paper.pdf)
(Touvron et al., ICCV 2021) adds a near-zero-initialised diagonal on each residual
block's output. [ControlNet](https://openaccess.thecvf.com/content/ICCV2023/papers/Zhang_Adding_Conditional_Control_to_Text-to-Image_Diffusion_Models_ICCV_2023_paper.pdf)
(Zhang, Rao & Agrawala, ICCV 2023) injects a side branch through zero-initialised
convolutions specifically so that the pre-trained model's output is unchanged at
initialisation and no harmful noise reaches it during fine-tuning.

The consequence for this design: **INV-25 (reversible influence) and the
zero-influence birth in `06-growth-model.md` are not a research bet.** They are the
standard mechanism, and if they misbehave the fault is implementation, not concept.
Do not spend argument defending them.

**Function-preserving structural change.** [Net2Net](https://arxiv.org/abs/1511.05641)
(Chen, Goodfellow & Shlens, ICLR 2016) introduced `Net2WiderNet` and
`Net2DeeperNet` as function-preserving transformations; [Network
Morphism](https://proceedings.mlr.press/v48/wei16.html) (Wei, Wang, Rui & Chen,
ICML 2016) generalised these to kernel-size and subnet morphisms.
[Path-Level Network Transformation](https://arxiv.org/pdf/1806.02639) extends the
operator set to path topology. Recent work continues to formalise the family:
[Towards a More Complete Theory of Function Preserving
Transforms](https://arxiv.org/html/2410.11038) and
[Exact Network Surgery](https://arxiv.org/pdf/2607.16568) (functional invariance
and gradient behaviour under structural edits) are directly load-bearing for the
legality argument Elesh must make.

**Canonicalisation and identity.** Treating architectures as DAGs and collapsing
isomorphic forms to one representation is standard in NAS.
[GATES](https://arxiv.org/pdf/2004.01899) (ECCV 2020) maps isomorphic
architectures to identical encodings by construction; graph-hash duplicate
detection is routine when generating architecture neighbourhoods. Compiler
practice (common-subexpression elimination, e-graphs) covers the rest. INV-20's
canonical semantic hash is therefore an engineering problem with known solutions.
**The corpus's own concession that Elesh is sound-but-incomplete is the honest
position and matches the literature** — canonical labelling of general graphs has
no cheap complete algorithm, and NAS implementations live with the same
incompleteness.

**Best-of-$K$ with functional diversity.** Sampling a pool and ranking it is the
core loop of predictor-based and evolutionary NAS
([Regularized Evolution](https://ojs.aaai.org/index.php/AAAI/article/view/4405),
Real, Aggarwal, Huang & Le, AAAI 2019).

---

## Adapted — one hop from validated ground

**Host state as the conditioning signal.** Reading a network's live internal state
to make a structural decision is exactly what the zero-cost-proxy line does.
[Zero-Cost Proxies for Lightweight NAS](https://iclr.cc/virtual/2021/poster/2861)
(Abdelfattah et al., ICLR 2021) scores architectures from a single minibatch's
forward/backward pass. [GradMax](https://arxiv.org/pdf/2201.05125) (ICLR 2022)
initialises new neurons to maximise their gradient norm. Firefly
([Firefly Neural Architecture Descent](https://www.semanticscholar.org/paper/Firefly-Neural-Architecture-Descent:-a-General-for-Wu-Liu/3e1b060ebacfc7a966ec735c940e2ee48f2a7a99),
Wu, Liu et al.) adds neurons that minimise loss under neighbourhood constraints.

Two hops separate this design from that work, and both are real: Nissa publishes a
**rich typed telemetry record** rather than one scalar proxy, and Momir uses it to
**generate** rather than to **score**. The inherited risk is documented in the
source literature and should be carried explicitly: zero-cost proxies are
"unreliable, especially on larger search spaces," provide "only relative rankings
rather than predicted accuracies," and degrade as the space grows
([NAS: Insights from 1000 Papers](https://arxiv.org/pdf/2301.08727);
[Zero-Cost Operation Scoring](https://arxiv.org/pdf/2106.06799)). **A telemetry
vector is a richer proxy, not a different kind of object, and nothing yet shows
richness fixes the generalisation failure.**

**Parameter generation from a conditioning vector.** Hypernetwork-generated
adapters are a dense line — see
[HyperLoader](https://arxiv.org/html/2407.01411v1) as one representative of many.
The hop: that literature conditions on **task or query embeddings**; Momir
conditions on **the host's diagnostic state**. The machinery transfers; the
conditioning source is untested.

**Mutation and recombination over a population.** Evolutionary NAS, established.
The hop: this design runs it **online inside a single training run** against a
moving host, not offline across many independent trainings.

**Nursery maturation.** Training a new module while the host is held is standard
(progressive and side-tuned module families). The hop is specific and
under-appreciated: maturation happens **inside a counterfactual branch**, and
INV-22 forbids transplanting the result into a host that followed a different
trajectory. That combination — mature in a branch, then adopt-or-replay rather
than copy — has no precedent this survey found, and it is priced nowhere in
`programme/cost-model.md`.

**Model growth at scale is now a live, competitive field.**
[Stacking Your Transformers](https://papers.nips.cc/paper_files/paper/2024/file/143ea4a156ef64f32d4d905206cf32e1-Paper-Conference.pdf)
(NeurIPS 2024) reports a depthwise stacking operator reaching equal loss with
194B rather than 300B tokens at 7B scale, and — directly relevant to Aurelia —
formalises **growth timing and growth factor** guidelines.
[AutoGrow](https://arxiv.org/pdf/1906.02909) automates layer growth with
stopping policies. The programme should expect a reviewer to ask why Aurelia's
learned timing beats Gstack's fitted schedule, and `programme/evaluation.md`
should carry that comparison.

---

## Speculative — where the actual contribution is

### How the growth literature validates its criteria

This is the load-bearing observation of the chapter, and it inverts the corpus's
own novelty claim.

Every growth criterion surveyed is a **cheap one-step surrogate, argued
theoretically and validated end-of-pipeline**:

| Method | Criterion | How validated |
|---|---|---|
| GradMax | maximise gradient norm of new neurons | benchmark accuracy after full training |
| Firefly | loss reduction under neighbourhood constraint | benchmark accuracy after full training |
| Zero-cost proxies | single-minibatch statistic | **rank correlation with final accuracy** |
| Gstack | fitted timing/factor schedule | loss curve and downstream benchmarks |

None of them forks a **matched no-growth continuation from the same snapshot over
the same future data** and measures the causal effect of the insertion itself.
The counterfactual question — *would this host have been better off had nothing
been inserted here, on this data, from this state?* — is the question the whole
field answers by proxy.

The apparatus this design uses to answer it directly is borrowed and sound.
Paired/matched comparison and common random numbers are textbook variance
reduction; [CUPED](https://dl.acm.org/doi/10.1145/2433396.2433413) (Deng, Xu,
Kohavi & Walker, WSDM 2013) is the industrial form and reports ~50% variance
reduction on Bing. Checkpoint forking to measure intervention effects exists in
adjacent fields — interpretability uses it for activation patching along training
trajectories ([pyvene](https://arxiv.org/pdf/2403.07809)), and agentic RL uses
rollout fork points for per-step credit assignment.

**The transposition of that apparatus onto architecture-growth decisions is where
this programme is genuinely alone.** Not the generator — the screen.

That has three consequences the design should absorb:

1. `01-claim.md#26-the-empirical-driver` names "generated (not selected)
   structure" as irreducible contribution #1. **On this survey it is the
   most-precedented component in the system, not the least.** The novelty
   ordering in that section is inverted and should be re-recorded — it bears
   directly on owner decision G in
   `../concept/reviews/2026-08-11-morphogenesis-concept-panel.md`.
2. The measurement standard survives a Momir null. If generation loses, a
   calibrated counterfactual growth criterion is still a result; if the corpus
   stakes everything on the generator, a null is a programme-level failure. This
   is an argument about what `01-claim.md#28-success-criteria` should headline,
   not about what to build.
3. A reviewer will position this inside an **established genre** —
   zero-cost-proxy calibration — and ask why it is not simply a better proxy
   study. The defensible answer is that proxy calibration measures rank
   correlation against *final accuracy of a separately trained network*, whereas
   this measures the *causal effect of the insertion on the trajectory that
   actually received it*. That answer should be written down before it is needed.

### Online typed-graph generation

Generative models over architecture DAGs exist. Running one **mid-training,
conditioned on live host state, with a legality gate and a compile step inside
the loop, under a latency budget set by host drift** has no precedent this survey
found. Levels 2–3 in `06-growth-model.md#111-growth-progression` are research, and
the Level-1 result does not transfer to them for free.

### The moving-target problem

NAS is offline: the network being designed for does not move while the design is
computed. `01-claim.md#21-the-moving-target-problem` states the constraint, and
the survey found no prior work that has had to solve it, because no prior setting
creates it. The staleness crossing point is genuinely unmeasured territory.

### Blindness and the mandatory no-op

Provider blindness by construction (INV-37) and a no-intervention alternative at
policy utility exactly zero (INV-15, INV-16) have no ML systems precedent this
survey found. The technical risk is near zero — they are cheap to build and
trivially understood — but they are **governance claims, not capability claims**,
and no external evidence shows they change outcomes. They should be defended as
evidential hygiene, never as contributions that carry the paper.

---

## Named baselines this survey obliges the pool to carry

`07-counterfactual-engine.md#141-candidate-pool` lists candidate classes
generically. Three now have specific published referents and should be named, so
that the analytic and reference arms are recognisable rather than hand-rolled:

| Pool class | Published referent |
|---|---|
| "least-squares or Gauss–Newton candidates" | [Learning Morphisms with Gauss-Newton Approximation for Growing Networks](https://arxiv.org/pdf/2411.05855) |
| "compatible stock reference seeds" / analytic construction | Net2Net and Network Morphism operators (above) |
| gradient-derived construction | GradMax; Firefly; the zero-cost-proxy family |

Naming them converts `programme/phases.md` Phase F's control line from "add
random, analytic, retrieval and bounded online controls" into a list a reviewer
can check.

---

## Limits of this survey — read before relying on it

- **Roughly a dozen queries.** The positive half (how the named methods validate
  their criteria) is verified against primary sources. The negative half — *no one
  validates a growth criterion against a matched counterfactual* — is **absence of
  evidence, not evidence of absence**, and it is the claim doing the most work here.
  It should be re-run at greater depth before any submission relies on it.
- **Every citation above was checked against a primary or indexing record**
  (arXiv, PMLR, AAAI/ICLR/ICCV/NeurIPS proceedings, dblp, ACM DL). Where a venue
  could not be confirmed it is omitted rather than guessed.
- **Citation gaps knowingly left open.** These families are referenced by
  description above but have no pinned canonical citation yet: hypernetworks as a
  general mechanism, LoRA/AdaLoRA, progressive and side-tuned module families,
  generative models over architecture DAGs, and counterfactual credit assignment
  in multi-agent RL. Closing them is a bounded follow-up, not a research task.
- **This chapter grades components, not the system.** A system of established
  parts can still be novel in composition, and a system of speculative parts can
  still be worthless. The grading answers "where is the risk", not "is it good".
