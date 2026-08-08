# Commissioning prompt — yzmir-training-state-engineering (update applied, v4.1)

Status: pack **in flight** upstream · Tracker: simic-e84fe6737c (closed) ·
Roster: PDR-0011 · Provenance: PDR-0012

This file is the original in-flight skill-creator prompt (recovered from the
2026-08-07 drafting session, where it existed only as a conversation
artifact) with the update brief
(`yzmir-training-state-engineering.md`) applied: grounding re-cited to the
decomposed v4.1 HLD and the execution-regime scope addition folded in. Every
citation below was verified against `docs/design/` on 2026-08-08. Use it as
the applied form of the brief when relaying to the in-flight upstream
session, or as the full re-commissioning prompt if that build is superseded
(the PDR-0012 reversal path). Beyond the brief's three corrections, applying
it surfaced further v2.0→v4.1 drift now fixed here: `TrialPlan` is renamed
`TestPlan`; Tolaria's work moved from "Phase C" to Phases B and D; and the
v2.0 invariant numbers the original cited no longer correspond.

---

Commission a new skillpack: **yzmir-training-state-engineering** —
"Engineering complete capture, exact restore, and cheap branching of neural
training state: the full state inventory (model, optimizer, AMP, RNG
streams, dataloader cursors, controller state), snapshot envelope design,
flash-cloning under GPU memory budgets, matched-branch execution without
cross-contamination, rollback and branch adoption, and execution-regime
engineering — from the bitwise-exact reference regime, through calibrated
bounded nondeterminism, to production execution carrying measured
uncertainty. The machine that lets one training run be forked into many
matched possible futures — and merged back." Yzmir faction (ML-science
discipline).

## Motivation and grounding

The immediate consumer is Simic, whose Tolaria subsystem provides training
and execution infrastructure across Phases B and D
(`programme/phases.md`: Phase B — host-training baseline and Academy
profile; Phase D — replay, branching and execution calibration). Ground in
the decomposed HLD: entry point `docs/design/00-INDEX.md`; cite chapters by
path#anchor, invariants as INV-nn, contracts by name — never bare
§-numbers. Key grounding:

- The `Snapshot` contract
  (`docs/design/05-leyline-contracts.md#911-snapshot`) — study its field
  list; it IS the completeness checklist: host parameters, optimizer state,
  slot/lifecycle/economy state, controller recurrent state, RNG states,
  dataloader cursor, recent batches, fixed future minibatch sequence,
  device-and-determinism manifest, code-and-schema versions. The
  completeness criterion — restoring it twice and consuming the same future
  produces bit-identical traces — holds under the **Academy-exact
  determinism contract** (INV-05); non-exact regimes carry measured
  uncertainty instead of pretending to satisfy it.
- The adjacent contracts: `TrainingRunSpec`
  (`docs/design/05-leyline-contracts.md#910-trainingrunspec`), `TestPlan`
  (`#912-testplan` — v2.0 called it TrialPlan) and `BranchResult`
  (`#913-branchresult`; every non-exact `BranchResult` carries
  execution-regime identity and uncertainty provenance).
- Tolaria's chapter (`docs/design/domains/tolaria.md`): responsibilities,
  the four execution modes (mainline, replay, branch, acquisition), the
  orthogonal three-regime model (below), and its invariants — including
  neutrality (INV-03), mainline–branch parity (INV-04), and the common
  future (INV-06: paired branches receive identical future minibatches and
  equivalent random streams, differing only in declared interventions and
  explicitly modelled execution noise).
- The counterfactual engine: Academy QA
  (`docs/design/07-counterfactual-engine.md#143-academy-qa`), Field QA
  (`#144-field-qa`), the branch-adoption invariant
  (`#146-branch-adoption-invariant`: branch-matured state is deployed ONLY
  by adopting the winning branch or exactly replaying it under the declared
  protocol — never by copying a candidate into a divergent host), and the
  statistical unit (`#149-statistical-unit`; INV-32: branches from one base
  host trajectory never cross splits or inflate independent sample counts).
- The gate suite:
  `docs/design/programme/evaluation.md#214-tolaria-training-determinism-and-field-calibration-gates`
  — the Academy-exact restore-twice/bisection procedure AND the
  calibrated-stochastic and Field gates.
- The open deployment tradeoff: adopt vs restore-and-replay
  (`docs/design/programme/risks-and-open-decisions.md#273-winning-branch-deployment`).

Use Simic as the running example but write the pack GENERAL:
population-based training, evolutionary fine-tuning, checkpoint-and-branch
ablation studies, and speculative training all need this machine; no Simic
vocabulary in the normative text. That applies to the regime model too:
normative text names the regimes generically (exact-reference /
calibrated-stochastic / production), with Academy/Field as the worked
Simic example.

## The execution-regime model (v4.1 scope — not optional)

The pack must NOT assume universal bitwise replay. Exact replay is one
regime among three (`docs/design/domains/tolaria.md`):

- **Academy-exact** — the causal reference and metrology profile. Device,
  kernels, library/compiler versions, dtype, thread count, random state,
  optimiser state, dataloader state and future minibatches pinned; restore
  plus common future ⇒ bitwise-identical traces (INV-05). Deliberately
  narrow and possibly slow; retained permanently as a reference capability
  (INV-42), not the factory-floor profile.
- **Calibrated-stochastic** — bounded nondeterminism with repeated matched
  branches (replicate groups); outcome distribution, ranking stability and
  decision disagreement measured against Academy-exact.
- **Field** — production kernels, mixed precision, distributed execution;
  evidence carries execution uncertainty and escalates to Academy-exact on
  thin margin, high risk, or expired calibration (INV-43).

Consequences the pack's guidance must carry everywhere, not in one
quarantined sheet:

- Non-exact regimes carry **measured uncertainty fields**
  (\(\sigma_{\mathrm{exec}}\)) rather than pretending determinism:
  `docs/design/07-counterfactual-engine.md#1441-execution-uncertainty-and-adjudication-margins`.
- Regime advancement is gated **decision-aware**: ranking agreement,
  selection regret, accept/no-op disagreement and tail cases inside
  declared limits (INV-44), not merely numeric closeness.
- \(\sigma_{\mathrm{exec}}\) is load-bearing beyond QA: it sizes the
  admission/retention hysteresis band (ADR-0005, INV-33), so
  training-state capture must preserve whatever the calibration machinery
  needs to keep measuring it.
- Regime state is one axis of the three-axis `ScaffoldState` (execution,
  host-distribution, design-prior:
  `docs/design/appendices/scaffold-pattern.md`, INV-39); withdrawal gates
  are independent and one-axis-at-a-time (INV-40, INV-41).

## Composition boundary

axiom-determinism-and-replay owns the determinism CHANNELS taxonomy, seed
governance, and the divergence-localisation protocol — cite its sheets,
don't restate them. yzmir-pytorch-engineering owns general PyTorch
mechanics. yzmir-counterfactual-statistics owns the statistics the Field
withdrawal gates consume (selection regret, coverage, calibration) — this
pack owns the state capture/restore/branch machinery that makes those
statistics measurable, not the statistics themselves. This pack owns the
snapshot/clone/branch/adopt machine and its regime engineering, built on
top of all three.

## House style (mirror yzmir-morphogenetic-rl's layout)

- skills/using-training-state-engineering/SKILL.md — router with
  symptom→sheet table; trigger on: "snapshot the training state", "resume
  is not identical", "restore diverges", "fork/branch a training run",
  "matched rollouts", "A/B the same run", "checkpoint the dataloader",
  "RNG state", "copy-on-write clone", "GPU memory for parallel branches",
  "merge the winning branch back", "bit-identical replay", "execution
  regime", "calibrated nondeterminism", "execution uncertainty",
  "escalate to exact replay".
- ~13 reference sheets (below). commands/: 3. agents/: 2 following
  meta-sme-protocol.
- .claude-plugin/plugin.json, version 0.1.0.

## Reference sheets

Each: principle, the failure it prevents, worked example, executable
decision procedure.

1. the-complete-state-inventory — enumerating EVERYTHING that is training
   state: params, buffers, optimizer state, LR schedulers, AMP/GradScaler,
   RNG streams (python/numpy/torch CPU/per-device CUDA), dataloader cursor
   and worker state, augmentation state, EMA copies, controller/policy
   recurrent state, step counters, task config; the completeness TEST
   (restore twice → bit-identical, under the exact-reference regime) as the
   only honest definition of "complete"; a checklist template.
2. capturing-pytorch-state — state_dict discipline: optimizer state
   gotchas (per-param keys, device placement, capturable state), buffers
   vs params, tied/shared weights, lazy modules, non-tensor attributes;
   capturing RNG correctly (get_rng_state per device, generator objects,
   fork_rng).
3. dataloader-and-data-stream-state — deterministic, RESUMABLE data
   pipelines: cursor serialization, worker seeding, prefetch buffers,
   shuffle-state capture; when to sidestep it all by materialising a fixed
   future minibatch sequence into the snapshot itself.
4. snapshot-envelope-design — the snapshot as a typed, versioned record:
   what to embed vs reference, the device-and-determinism manifest and
   execution-regime identity, code/schema version pins, integrity digests,
   storage format tradeoffs (torch.save/safetensors/custom).
5. exact-restore — restore semantics and ordering, device remapping, RNG
   restoration, the restore-twice self-test as the exact-reference
   contract; failure taxonomy (optimizer state on wrong device, missing
   buffer, scheduler off-by-one, un-restored generator) with symptoms.
6. cheap-cloning-under-memory-budgets — deep copy vs serialization
   round-trip vs copy-on-write; sharing frozen/common state across clones;
   CPU-offload staging; GPU memory arithmetic for N concurrent branches;
   when the safe answer is serialize-restore and eat the latency.
7. matched-branch-execution — running N branches from one snapshot without
   cross-contamination: process/stream isolation, global-state hazards
   (cudnn.benchmark autotune caches, dynamo caches, module-level
   singletons, torch.compile state), per-branch spend metering,
   equivalent-random-streams policy with a declared-variable exception;
   replicate groups — repeating matched branches under bounded
   nondeterminism to estimate the execution-noise distribution.
8. common-futures — materialising one future minibatch sequence and
   feeding it identically to every branch; verifying branches consumed
   identical data (digest the stream); horizon control.
9. rollback-and-branch-adoption — the no-transplant rule: never copy a
   co-adapted artifact from a branch into a host that followed a different
   trajectory; adopt-winning-branch vs restore-and-replay tradeoffs
   (memory, latency, checkpoint cost); verifying adoption reproduced the
   branch state exactly.
10. execution-regime-engineering — the three-regime model as an
    engineering object: regime declaration in the snapshot/result records;
    the calibration envelope and its lifecycle (measure, expire on
    device/library/kernel/compiler/precision change, re-measure);
    measuring \(\sigma_{\mathrm{exec}}\) from replicate groups and
    propagating it as a first-class evidence field; decision-aware
    advancement gates (ranking agreement, selection regret, accept/no-op
    disagreement, tail coverage — not float tolerances); escalation
    plumbing from production regime back to the exact-reference regime;
    the retained-reference rule (withdrawal removes a production
    dependency, never the exact-replay harness).
11. the-determinism-gate-as-ci — restore-twice bit-identical trace tests
    as a blocking CI gate for the exact-reference regime: trace digests,
    first-differing-step bisection, first-differing-tensor reporting;
    environment pinning (deterministic algorithms, cublas workspace,
    threads, dtype); the calibrated/production counterpart gates (repeat
    identical branches, estimate execution noise, compare rankings and
    accept/no-op decisions against exact-reference outcomes, verify
    interval coverage including tails, verify low-margin escalation
    fires); rerun and calibration-invalidation policy on
    device/library/kernel/compiler change; hand off root-causing to the
    determinism-and-replay pack's divergence protocol.
12. snapshot-lifecycle-and-storage — cadence, retention,
    content-addressing and dedup (most of a snapshot doesn't change
    between nearby steps), integrity verification on read, storage cost
    modelling.
13. tiered-evaluation-engineering — cheap screens before full branches:
    short-horizon partial branches, frozen-clone probes, surrogate hooks,
    and the escalation plumbing between tiers and between regimes;
    metering so the evaluation machine reports its own cost.

Anti-pattern catalogue (router or sheet 14): a snapshot missing one
channel, discovered only when replay diverges a week later; restore
without RNG (silently "works"); resumed dataloader replaying or skipping
samples; branches sharing a mutable global (autotune cache, singleton);
"close enough" float tolerance on the exact-regime determinism gate;
pretending determinism in a non-exact regime — results published without
uncertainty fields; advancing a regime on numeric closeness when
accept/no-op decisions disagree; production evidence consumed past its
calibration expiry; candidate weights transplanted from a co-adapted
branch into a divergent host; snapshot format with no version pin restored
by newer code; branch spend unmetered so evaluation cost is invisible;
withdrawing two scaffold axes in one step with no interaction experiment.

## Commands

- inventory-training-state — walk an actual training loop and emit the
  complete state inventory with per-channel capture status and gaps,
  against the sheet-1 checklist.
- scaffold-snapshot-branching — scaffold snapshot/restore/clone/branch
  harness for a given training loop, with the restore-twice determinism
  test failing-first and a replicate-group noise-measurement stub for the
  non-exact regimes.
- diagnose-restore-divergence — given a failed determinism gate, bisect to
  the first differing step and tensor, classify against the failure
  taxonomy (including regime misdeclaration: an exact-regime claim on a
  stochastic execution), and route root-cause analysis to the
  determinism-and-replay divergence protocol.

## Agents (SME protocol, confidence/risk per finding)

- state-capture-architect — forward-design SME: snapshot envelope, clone
  strategy, branch-execution plan and regime/calibration plan for a given
  training loop, memory budget and target assurance level.
- snapshot-completeness-reviewer — critic SME: hunts missing state
  channels, cross-branch contamination paths, transplant violations,
  tolerance-softened exact gates, and regime violations (uncertainty-free
  non-exact results, decision-unaware advancement, expired calibration,
  missing escalation paths) in designs or code; zero-findings runs are
  treated as an audit defect.

## Quality bar

skill-creator eval discipline: every sheet gets at least one RED scenario
(a realistic capture hole — e.g. a resumed run whose CUDA RNG was never
restored; two "matched" branches whose cudnn autotune picked different
kernels; a production-regime result consumed as if exact, with no
uncertainty field and no calibration check) with verified GREEN behavior.
Executable procedures (state-inventory walkers, restore-twice harnesses,
trace-digest bisectors, replicate-group noise estimators) as runnable
Python (torch only) inline. Every normative claim names the concrete
failure it prevents.
