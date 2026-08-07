# Vision — Simic (Counterfactual Generative Morphogenesis)

## Purpose
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

## Who it serves
- **Primary:** john — researcher-owner. The product is defensible experimental
  evidence (positive *or* negative) about generative morphogenesis; HLD §28 notes a
  clean negative result is scientifically useful.
- **Secondary:** implementation agents (Claude / Codex sessions) building against
  HLD v4.1 — served by contract clarity and the locked Namespec, never at the
  expense of evidential rigor. *(assumption — inferred from HLD §30 handoff
  framing; confirm.)*
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
Granted by: john (GitHub: tachyon-beep)     Last reviewed: 2026-08-08
Review cadence: on any vision change, or monthly — whichever first.
Status: CONFIRMED — owner directed carryover of the esper-lite grant
(~/esper-lite/docs/product/vision.md) adapted to Simic, 2026-08-08.

Autonomous within strategy — the agent MAY, without asking:
  prioritize the backlog, write specs/PRDs, dispatch delivery, **launch/kill
  training or experiment runs within the active bet** (once Tolaria exists), run
  analysis, accept against criteria, reprioritize, kill a failing bet per
  metrics.md, and **commit to the workspace at checkpoint**.
  **Run authorization (owner-stated 2026-07-10 in esper-lite; carried over):** the
  agent may CREATE NEW EXPERIMENTS, EXTEND runs, or ADD runs at its own discretion
  whenever it judges that previous runs did not give us everything we need — within
  the active research program, each recorded as a PDR with a pre-committed reading.
  Pre-registered acceptance gates stay owner-gated.
  **Experiment-value principle (owner, 2026-07-10; carried over):** prefer tossing
  a week and restarting with an experiment that answers the question 100% over
  salvaging a near-done run that answers 20%. The test for any run, salvage, or
  redesign is: *"will this give us insights that inform future decisions — by
  ruling things in or out, or verifying a theory?"* Sunk cost and near-completeness
  are not reasons to keep a compromised instrument.

Escalate BEFORE acting — the agent MUST get owner sign-off for:
  changing this vision/strategy/grant; **pushing/tagging/releasing or any
  GitHub-remote/external action**; deprecating a subsystem or contract others rely
  on; deleting telemetry/run data; anything touching an external party; the
  project-level rename (HLD §27.1) when it lands.
  Standing rules (always): git identity stays **tachyon-beep** (never johnm-dta
  without explicit say-so); **never push without an explicit ask**; no destructive
  git without permission.
  Repo discipline (restates HLD §30, not a grant extension — flagged for owner
  review): HLD constitutional constraints (Namespec 1.0, the §18 invariants, the
  authority boundaries, the newsroom rule, the no-op requirement, scaffold
  withdrawal) change only through an ADR naming the displaced invariant.
  (Taxonomy + rationale: product-ownership-operating-model.md.)
