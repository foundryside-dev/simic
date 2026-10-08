# Vision — Simic (Counterfactual Generative Morphogenesis)

## Purpose

> **Positioning (PDR-0039, owner sign-off 2026-08-11): Simic is a novel
> engineering programme, not a confirmatory research study.** Its deliverable is
> a working instrument — a system that measures the causal effect of a
> structural intervention on the trajectory that actually received it — plus
> demonstrations that it works and a retained corpus of what it measured. The
> reason is the feasibility argument, owner-stated: *"the lack of novelty
> doesn't make this less interesting, it makes it more like something that we
> can credibly build."* Most components are established or one hop from it, and
> the speculative risk is concentrated in the counterfactual screen, where it is
> legible and falsifiable early (`docs/design/00-related-work.md`). The
> confirmatory apparatus (K = 1.5 / n = 32) is mothballed with its costings
> intact and is re-commissionable (ADR-0016). **Read the paragraph below through
> this**: "prove or cleanly disprove" is now the *optional-study* ambition, and
> the gating question is the acceptance class of
> `docs/design/01-claim.md#28-success-criteria`, headed by criterion 18.

Simic exists to prove — or cleanly disprove — that useful neural structure can be
**generated from the live state of a host network** and **causally screened against
doing nothing**, rather than selected from a fixed menu of human-authored blueprints.
It is the third incarnation of the morphogenetic research programme (ESPER →
ESPER LITE → Simic). The empirical driver: Esper demonstrated that seed telemetry
is *sufficient* for intelligent structural decisions, and that what failed was RL
reward shaping over a joint categorical-plus-continuous action space with delayed
outcomes — not missing information. The reset rationale (owner-stated
2026-08-08): esper-lite's silent-default defect class — plumbing that quietly
taught the policy "unmeasured means zero" — made continued patching a
months-long whack-a-mole; a clean cut, with those defect classes made
unrepresentable by construction, is faster and cleaner than incremental repair
of the old instrument. Simic therefore replaces the reward function
with **measured counterfactuals**: paired branches from one snapshot over identical
futures cancel ordinary-training variance, so the difference between branches *is*
the intervention effect — converting credit assignment into supervised learning.
The first defensible claim (HLD §4): given a typed insertion contract and a measured
host deficit, the system can generate, verify, compile, causally screen, and safely
integrate a useful constrained growth more quickly and reliably than comparable
online construction, retrieval, random search, analytic construction, or static
over-provisioning.

## Strategy now: the bounded ladder (PDR-0050)

The bounded experiment ladder is the sequencing authority. Each rung is one
pre-registered, reviewed experiment with a stop condition, and a failed rung
is never answered by enlarging the controller (ADR-0018). HLD contracts and
Phase A are pulled by rung 5, never pushed ahead of it. Evidence so far, as
of 2026-10-09; details live in `current-state.md`:

- **Rung 1 is met.** The instrument resolves.
- **Rung 2 is met as a question.** A real deficit exists, but a benefit at
  the pre-registered floor was not established.
- **Rung 3 is met as a partial capture.** A graft grown mid-training repairs
  60% of the deficit with the `norm` seed and 31% with `conv_heavy`. That
  is after a lifecycle fix that took its divergence from 14/48 to 0/240.

Static over-provisioning beats the scheduled graft at the declared cost.
That is a **recorded negative, at bounded scale and a 10-epoch horizon**,
for the first claim's comparison against static over-provisioning (Purpose,
above). It does not refute the claim: the claim is about generated,
screened structure, and rung 4 asks whether the graft's timing or location
changes the outcome. A clean negative remains a useful result.

## Who it serves
- **Primary:** john — researcher-owner. The product is defensible experimental
  evidence (positive *or* negative) about generative morphogenesis; HLD §28 notes a
  clean negative result is scientifically useful.
- **Secondary (operational):** implementation agents (Claude / Codex sessions)
  building against HLD v4.1 — served by contract clarity and the locked
  Namespec, never at the expense of evidential rigor.
- **Secondary (eventual):** the morphogenetic-AI research community, on
  publication — served by the evidence chain and complete history; a clean
  negative result is publishable (§28). *(owner-confirmed 2026-08-08.)*
  **Stakes qualified 2026-08-11 (PDR-0039), owner-stated:** *"any research claim
  I did make would have just been 'hey check this out' rather than an attempt at
  a career."* The publication motive is not career-bearing. Weigh
  publication-shaped work by this constraint, **not by generic academic
  incentives** — a future session must not re-inflate the cost of demoting a
  confirmatory claim. "Check this out" describes a runnable, pointable
  artifact, which is what the engineering positioning optimises for and what
  PDR-0029 already made the kernel demo. This does **not** license asserting a
  novelty claim the search has not earned (`docs/design/00-related-work.md`
  limits).
- **Explicitly not:** production ML teams wanting a turnkey AutoML/NAS service, or
  a general training-framework competitor. The value is the causally-screened
  grown-during-training mechanism and its evidence chain, not model delivery.

## Anti-goals (what it refuses to be)
- **Not unrestricted architecture search** (HLD §4): no source-code generation, no
  whole-network rewriting, no Turing-complete growth grammars, no autonomous
  modification of the training runtime.
- **Never trades evidence discipline for speed.** The mandatory no-op competitor,
  dual provider blindness, and complete (never winners-only) history are
  constitutional (HLD §18) — declined even under schedule pressure.
- **No return to shaped reward.** The pivot's whole point is replacing a
  Goodhartable dense reward with counterfactual measurement; reintroducing reward
  shaping to "speed up learning" is the failure mode that killed Esper.
- **Not a replacement for ordinary host optimisation**, and no
  continual-learning-without-forgetting guarantee (HLD §4).
- **No legacy / backwards-compat / shim code** (carryover of the esper-lite
  No Legacy Code policy).

## Authority grant
Granted by: john (GitHub: tachyon-beep)     Last reviewed: 2026-10-09
Review cadence: on any vision change, or monthly — whichever first.
Status: CONFIRMED — owner directed carryover of the esper-lite grant
(/mnt/data/archive/esper-lite/docs/product/vision.md) adapted to Simic, 2026-08-08;
re-confirmed 2026-08-09 (session 11), ratifying the two mechanical
citation renames in the repo-discipline line below (Namespec 2.0 —
PDR-0020; evidence-routing rule INV-07/INV-09 — ADR-0009).
**WIDENED 2026-08-10 (session 15) — scope CHANGED.** Prompted by the agent
self-reporting that it had pushed a branch and opened PR #10 without an
explicit ask, contrary to the then-standing "never push without an explicit
ask" rule. Owner chose to widen rather than tighten: the full PR lifecycle
inside the active bet is now autonomous. Releases, tags, deprecations and
external-party actions remain reserved. See the two lines marked
**(widened 2026-08-10)** below; everything else is unchanged.
**RATIFIED 2026-08-10 (PDR-0038)** after an explicit side-by-side against the
parent grant. Note for anyone comparing the two files: Simic's remote clause
now **deliberately diverges** from `/mnt/data/archive/esper-lite/docs/product/vision.md`, which
still escalates every GitHub-remote action. That divergence is an owner
decision, not drift — do not "reconcile" it back.
**OWNERSHIP HANDED OVER 2026-10-08 (PDR-0040).** Owner, in session: *"you're
taking over the project, merge it into main, and update all your findings -
you have carriage to bring simic to green."* Claude is the standing owner and
implementer. It MAY, without asking, take any action that brings the repository
to the green state defined in `metrics.md`: merge reviewed work to `main`
through a PR, repair tests and documentation, reconcile the tracker, and remove
configuration for tools that no longer exist. Everything under "Escalate
BEFORE acting" below still applies unchanged. GPU or paid campaigns and opening
outer/test data are also reserved to the owner.
**GPU WINDOW GRANTED 2026-10-08 (PDR-0050).** Owner: *"GPU approved, you
have exclusive use to them for at least the next week or so."* Claude MAY
run GPU experiments on both local RTX 4060 Ti cards for bounded-ladder work.
Each run is a pre-registered, reviewed PDR, and each plan declares its
execution profile. Opening outer/test data remains owner-gated.
**ACCEPTANCE-GATE CLAUSE CLARIFIED 2026-10-09 (PDR-0053).** Owner, in
session: *"ok, please update the vision"*. Claude had surfaced that the
carried-over line "Pre-registered acceptance gates stay owner-gated" read
differently from the PDR-0050 window. The line is resolved under "Run
authorization" below. Nothing else in the grant changed.

Autonomous within strategy — the agent MAY, without asking:
  prioritize the backlog, write specs/PRDs, dispatch delivery, **launch/kill
  training or experiment runs within the active bet** (today the bounded
  ladder's pre-registered runs; Tolaria-hosted runs once it exists), run
  analysis, accept against criteria, reprioritize, kill a failing bet per
  metrics.md, and **commit to the workspace at checkpoint**.
  **Git remote, within the active bet (widened 2026-08-10, session 15):** the
  agent MAY push branches, open pull requests, and MERGE them, for work inside
  the current Now bet, without asking each time. This ratifies how PR #9 in
  fact went and resolves the ambiguity against the 2026-08-10 "stop asking me
  for permission" direction on the kernel-demo loop. Bounds that still hold:
  the work must fall inside a bet already on the roadmap; origin/main stays
  branch-protected so main is only ever reached through a PR; and the standing
  identity rule below is unaffected.
  **Run authorization (owner-stated 2026-07-10 in esper-lite; carried over):** the
  agent may CREATE NEW EXPERIMENTS, EXTEND runs, or ADD runs at its own discretion
  whenever it judges that previous runs did not give us everything we need — within
  the active research program, each recorded as a PDR with a pre-committed reading.
  **Acceptance gates (clarified 2026-10-09, PDR-0053).** The esper-lite line
  "pre-registered acceptance gates stay owner-gated" is split into two levels.
  - **Programme-level gates stay owner-gated.** These are the success criteria
    of `docs/design/01-claim.md#28-success-criteria` (headed by criterion 18),
    the ladder's rungs and stop conditions (PDR-0050), and any reading that
    would treat a stopped rung as passed or move a gate after its data is
    seen.
  - **Per-study plans and reading rules inside an approved ladder rung are
    Claude's to author.** Each is recorded as a PDR. Before launch, each is
    reviewed by independent agents (statistics, product decision, and code
    where code changes), gated by a real-configuration dry run, and frozen by
    hash at launch. A published reading is never re-read. The owner may veto
    or amend any plan before launch, and may reverse any consequence after.
  **Experiment-value principle (owner, 2026-07-10; carried over):** prefer tossing
  a week and restarting with an experiment that answers the question 100% over
  salvaging a near-done run that answers 20%. The test for any run, salvage, or
  redesign is: *"will this give us insights that inform future decisions — by
  ruling things in or out, or verifying a theory?"* Sunk cost and near-completeness
  are not reasons to keep a compromised instrument.

Escalate BEFORE acting — the agent MUST get owner sign-off for:
  changing this vision/strategy/grant; **tagging, releasing, or publishing**;
  **any GitHub-remote or external action OUTSIDE the active bet** — including
  work on a bet not yet on the roadmap (widened 2026-08-10: push/PR/merge
  inside the active bet is now autonomous, see above); deprecating a subsystem
  or contract others rely on; deleting telemetry/run data; anything touching an
  external party; the project-level rename (HLD §27.1) when it lands.
  Standing rules (always): git identity stays **tachyon-beep** (never johnm-dta
  without explicit say-so); **no destructive git without permission — this
  explicitly includes `reset --hard`, which destroyed uncommitted workspace
  edits on 2026-08-10 when chained onto an unrelated command**; a push or merge
  for work outside the active bet still needs an explicit ask.
  Repo discipline (restates HLD §30; owner-confirmed 2026-08-08): HLD
  constitutional constraints (Namespec 2.0, the §18 invariants, the
  authority boundaries, the evidence-routing rule (INV-07/INV-09), the no-op
  requirement, scaffold withdrawal) change only through an ADR naming the
  displaced invariant.
  (Taxonomy + rationale: product-ownership-operating-model.md.)
