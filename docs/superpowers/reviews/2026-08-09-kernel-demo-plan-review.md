# Kernel Demo Implementation Plan — Solution Design Review

**Source:** `docs/superpowers/plans/2026-08-09-kernel-demo.md` (1020 lines)
**Baseline (not under review):** `docs/superpowers/specs/2026-08-09-kernel-demo-design.md` rev 6, LOCKED
**Reviewed:** 2026-08-09
**Reviewer:** solution-design-reviewer (axiom-solution-architect)

## Summary (machine-readable)

- verdict: NEEDS-WORK
- critical_count: 3
- high_count: 7
- medium_count: 8
- low_count: 3
- scope: targeted
- tier_declared: N/A
- tier_artifact_consistency: N/A

*Note on the tier fields: this is a review of an implementation plan against a
locked spec, not of a `solution-architecture/` workspace. The tier checks
(failure mode 11) have no artifact set to score. Failure modes 1 (tech-before-
problem), 7 (diagram proliferation) and 10 (stakeholder capture) are not
applicable to a single-file demo with a pre-locked tech stack and no vendor
surface; they were checked and found clean rather than skipped.*

## Executive summary

This is a well-built plan — TDD-structured, spec-cited to the R2/R3 disposition
level, with GPU checkpoints correctly marked as needing the owner's presence and
the one-shot eval discipline preserved. It is also **not yet safe to execute past
Task 3.**

Three defects are load-bearing. One crashes loudly and early: the slot width is
hardcoded to 64 while two of the four pathologies change stage-2 width, so
germination fails on half the sampler and the seed param budgets vary up to 16×.
Two are silent and post-freeze, which is worse: the frozen block is **not
enforceable** (pathology definitions, every gate threshold, every eval threshold
and `batch_size` sit outside `FROZEN_FIELDS`, and `config_hash` — the field the
spec's R3 determinism note added *specifically* to cover the host architecture and
`derive()` — is never computed by any task), and the append-only store has no
run/attempt identity, so a restart of the ~10-hour one-shot eval silently
double-counts episodes against "evaluated once, no peeking."

Separately: the plan's **"Self-review notes (done)"** asserts "every spec section
maps to a task." A mechanical reverse sweep falsifies that — nine spec
requirements have no owning task. That self-certified coverage claim is itself the
finding that best justifies running an external review.

Runtime is the unquantified NFR that bites; memory is fine and I say so with
arithmetic below.

---

## Findings

### CRITICAL

#### C1 — Slot width is fixed at 64 while two pathologies change stage-2 width
*Failure mode: integration reality gap · Blocks: Task 4, Task 5, Task 8*

**Evidence.** Plan Task 4 (line 332) declares `host.feat_channels = 64` as the
slot width. Plan Task 4 (line 333) wires pathologies as `channel_starved →
widths 32/24/32` and `mild → widths 32/48/96`. The slot site is after stage 2, so
the actual slot channel count is **64, 24, 64, 48** across
`(under_normalized, channel_starved, no_spatial_mix, mild)`. Task 5's tests
(lines 394–423) build every seed at `channels=64`, and Task 8's `germinate` is
specified to build from the host's slot width.

**Impact.** Three distinct failures, one loud and two silent:

1. Shape error at germination on `channel_starved` and `mild` — half the sampler —
   the first time a fan runs. Task 5's unit tests pass throughout because they
   hardcode 64.
2. Seed parameter budgets fall outside the plan's own asserted bands at the widths
   it never tests (computed):

   | C | pathology | `norm` | `attn` | `conv_light` | `conv_heavy` |
   |---|---|---|---|---|---|
   | 24 | channel_starved | 49 | **1,657** ✗ | **1,417** ✗ | **8,425–22,617** ✗ |
   | 48 | mild (stage2=48) | 97 | 3,265 | 5,137 | 33,697–45,129 |
   | 64 | under_norm / no_spatial_mix | 129 | 4,337 | 8,897 | 59,905–60,137 |
   | 96 | — | 193 | 6,481 | 19,489 | **90,153–134,785** ✗ |

   Plan bands (line 412–416): `attn` 2k–12k, `conv_light` 5k–20k, `conv_heavy`
   35k–90k. Only C=64 lands inside every band — i.e. only the two pathologies that
   happen to preserve width. (The `conv_heavy` range is two-valued because the plan
   says only "channel bottleneck sized to land ~60k params" and never states
   whether the bottleneck is fixed or proportional to C — that ambiguity is itself
   part of the defect.)
3. **Confound in the headline artifact.** The relative capacity a seed adds varies
   by pathology: `conv_heavy` is 21.6%–79% of host parameters depending on the
   unspecified bottleneck rule. The money chart's designed-winner map and gate 4's
   dominance check would then be partly measuring stage-2 width rather than
   pathology diagnosis.

**Root cause, one level deeper.** `feat_channels = 64` is the symptom. The cause is
that the plan varies stage widths per pathology at all, while the spec's scope pin
reads "One fixed host architecture. One fixed slot site." `under_normalized`
(BN→Identity) and `no_spatial_mix` (1×1 stage-2 convs) preserve widths;
`channel_starved` and `mild` do not. That is a deviation from a LOCKED spec that
the plan's own **Global Constraint #1** ("any deviation discovered during
implementation is surfaced to the user, never silently patched") obligated it to
surface, and it does not appear in the "Deliberate deviations" list (line 1019).

**Recommendation.** Before Task 4:
- Surface the deviation to the owner and pick one: (a) hold stage-2 width fixed at
  64 across all four pathologies and express `channel_starved` / `mild` as
  stage-1/stage-3 width reductions only, or (b) get an owner amendment to the scope
  pin. (a) preserves both the spec text and the seed param contract.
- Delete `host.feat_channels = 64` as a constant; make it `host.slot_channels`,
  derived from the built stage-2 output.
- Parametrise Task 5's tests over the realised widths:
  `@pytest.mark.parametrize("C", sorted({slot_channels(build_host(p,1)) for p in PATHOLOGIES}))`.
- State the `conv_heavy` bottleneck rule explicitly in Task 5's interface block.

---

#### C2 — The frozen block is not enforceable (under-frozen and over-frozen, both silently)
*Failure mode: weak decision record / untraceable design · Blocks: Task 14 step 6*

**Evidence.** Spec, §Freeze discipline, enumerates the frozen block *exhaustively*:
"**pathology definitions**, telemetry normalizer, entropy temperatures, exploration
schedule, λ, τ, stage durations K/M/F, horizon, decision window, optimizer
constants, diverged-arm convention, **all pass thresholds**." Plan `FROZEN_FIELDS`
(lines 121–126) contains 22 scalars and **none** of the following:

*Under-frozen — inside the spec's list, outside the plan's hash:*
- **Pathology definitions.** Hardcoded as literal widths inside `build_host`
  (Task 4, line 333). Editable post-freeze with zero assertion failing.
- **Every gate threshold.** Task 14 states them in prose inside the gate function
  bodies: gate 1 "≥2 mild episodes"; gate 2a "accuracy > 0.5"; gate 3 "density >
  2× floor"; gate 4 ">40%"; gate 5 "≤ 2"; gate 6 "≥ 0.5× early". None reach `Config`.
- **Every eval threshold.** Spec §Pre-registered numbers: "agreement ≥
  majority-class null + 15 points", "≥3 of 4 pathologies". Task 16's `verdict()`
  is described but the constants are nowhere in `Config`.
- **`batch_size = 128`.** Placed under "non-frozen engineering knobs" (line 118).
  It is an optimizer constant in every meaningful sense — it sets the SGD step
  count per epoch, the α/β per-step cosine denominators (`M * steps_per_epoch`),
  and the shape of `CommonFuture`.
- **`tune_frac = 0.2`.** The spec names the 80/20 train/tune split explicitly;
  changing it post-freeze changes checkpoint selection, which selects the policy
  that produces the headline.
- **`config_hash`.** `FanRecord` declares the field (Task 10, line 710). **No task
  computes it.** Task 1 implements `frozen_block_hash` only. This is precisely the
  gap the spec's R3 determinism note was added to close: "`config_hash` covers the
  host architecture definition and `derive()` itself — both are plausible
  mid-development edits sitting outside the frozen block."

*Over-frozen — outside the spec's list, inside the plan's hash, and it forbids a
spec-mandated lever:*
- `n_preflight`, `n_collect`, `n_eval` appear in `FROZEN_FIELDS` but in none of the
  spec's enumeration. Freezing `n_collect` is not merely redundant: spec §Learning
  states collection "may be extended on tune-curve evidence, but only before any
  eval-namespace episode runs," and rev 6 pre-states extension as one of the two
  legitimate remedies for a bad tune curve. Task 15 (line 951) "asserts
  `frozen.json` exists and its `frozen_block_hash` matches the live `Config`
  (refuses otherwise)." Changing `n_collect` changes the hash, so `--collect`
  refuses. **The plan structurally forbids a remedy the LOCKED spec pre-states.**

**Impact.** Composed, these mean: after freeze, an agent (or the owner, or a
crash-recovery edit) can change a pathology width, a gate threshold, an eval
threshold, or the batch size, and **every assertion the plan defines still passes.**
The `frozen_block_hash` gate reports green. This is a silent, post-freeze defect
that lands directly on the headline number `R_chosen − R_noop`, and it is exactly
the failure class this project's scar catalogue names.

**Recommendation.** Before Task 14 step 6 (and ideally in Task 1, where it is cheap):
- Move pathology width tuples, all gate thresholds and all eval thresholds into
  `Config` as frozen fields (e.g. `pathology_widths: tuple[tuple[int,int,int], ...]`,
  `gate4_max_share: float = 0.40`, `agreement_margin: float = 0.15`).
- Add `batch_size` and `tune_frac` to `FROZEN_FIELDS`; remove `n_preflight`,
  `n_collect`, `n_eval` from it, and record collection size as run provenance in
  `frozen.json` instead of in the hash.
- Implement `config_hash(cfg) -> str` in Task 1 = sha256 over
  (`inspect.getsource(build_host)`, `inspect.getsource(derive)`, `git rev-parse HEAD`),
  populate the `FanRecord` field, and have `--collect` / `--train` / `--eval` refuse
  on mismatch the same way they refuse on `frozen_block_hash`.
- Add the test that makes the whole thing non-vacuous:
  `assert set(FROZEN_FIELDS) == {f.name for f in fields(Config)} - NON_FROZEN`, so a
  newly added field must be *classified*, not silently defaulted to unfrozen. The
  plan's existing `test_frozen_hash_moves_with_frozen_fields_only` (lines 61–65)
  only checks that `lam` moves the hash; it never checks that a non-frozen field
  leaves it unchanged, so its name promises a property it does not test.

---

#### C3 — The append-only store has no run/attempt identity; `schema_version` is written but never checked
*Failure mode: missing migration/rollback thinking · Blocks: Task 10*

**Evidence.** Task 10 sets `SCHEMA_VERSION = 1` and puts `schema_version` on
`FanRecord` (line 710). `decode_record` never reads it. `Store.merge()` sorts by
`(episode_seed, fan_epoch, kind, refan_k)` and `Store.load()` filters on
`split_role` only (line 712). `fan_id` is `sha256(episode_seed:fan_epoch:kind:refan_k)`
— it contains no run identity and no attempt counter.

**Impact, three ways:**

1. **Eval double-count (the sharpest).** `fan_id` carries no run identity, so **any**
   interrupted-and-restarted `--eval` double-counts: attempt 1 and attempt 2 write
   `policy_run` records that are **indistinguishable** into an append-only store —
   same `episode_seed`, same `kind`, same `fan_id`. The report then averages the
   completed prefix twice, and the spec's "evaluated once, no peeking, no augmenting"
   is violated invisibly. There is no dedup, no idempotency contract, and no resume
   design anywhere in the plan. This does not depend on how long eval takes; H2's
   estimate only establishes that the run is long enough for interruption to be a
   realistic event rather than a hypothetical one.
2. **Mid-development schema bump.** The record shape *will* change between Tasks 10
   and 17 (see H1: `policy_run` and `preflight_iter` payloads have no fields yet).
   A worker writing v2 into a shard directory containing v1 merges silently.
   `decode_record` on a v1 line missing a v2 field raises a bare `TypeError` deep in
   `merge()` — no quarantine, no skip-with-count, and "prior shards remain valid"
   (a spec claim, §fan step 2) becomes false.
3. **No stated remedy.** The plan never says whether a schema bump means *migrate*
   or *re-collect*. That is an 85+ GPU-hour decision (H2) and it deserves a
   pre-stated answer, in the same spirit as the spec's other pre-stated
   contingencies.

**Recommendation.** In Task 10:
- Add `run_id: str` (uuid or `derive(run_seed, "run", wall_start)` passed in) and
  `attempt: int` to `FanRecord`; include both in `fan_id`.
- `decode_record` raises `SchemaMismatch` on `schema_version != SCHEMA_VERSION`;
  `Store.merge()` catches per-line decode errors, counts them, and **refuses** if any
  occur unless `--allow-legacy` is passed — never silently skips.
- `Store.merge()` deduplicates on `(run_id, kind, episode_seed, fan_epoch, refan_k)`
  keeping the highest `attempt`, and prints the dedup count.
- Add one paragraph under "Execution ordering": *schema bump after collection
  begins ⇒ re-collect; the store is not migrated.* If the owner prefers migration,
  say so and add the migration task.
- `--eval` gains a resume contract: it refuses to start if `policy_run` records for
  this `policy_checkpoint_id` already exist, unless `--resume` is passed, in which
  case it skips completed `episode_seed`s and increments `attempt`.

---

### HIGH

#### H1 — Reverse traceability: nine spec requirements have no owning task, against a self-certified "every spec section maps to a task"
*Failure mode: untraceable design*

The plan's **"Self-review notes (done)"** (line 1018) claims complete forward
coverage. Forward coverage (spec → task) is in fact good — I found no spec *section*
without a task. Reverse and requirement-level coverage is not. Orphans:

| # | Spec requirement | Location in spec | Status in plan |
|---|---|---|---|
| 1 | Null-seed arm **on a 1-in-10 subsample** of fans | §fan step 3 | Only in `--selftest` (T13) and a unit test (T9). `run_fan` (T9, line 640) is "4 seeds + noop-twin" — no nullseed, no subsampling, in any collection path. |
| 2 | Twin divergence **"halts all workers"**, not just its own | §fan step 2 (R2 det N4) | T9 raises `TwinDivergence` in-process. T15's parent `run_collect` has no halt mechanism, no shared abort flag, no signal. |
| 3 | "Deterministic-mode slowdown measured once in pre-flight and recorded" | §Determinism contract | No task measures it. T17 *prints* it. |
| 4 | `config_hash` covering host arch + `derive()` | §Store (R3 det) | Field declared, never computed. (See C2.) |
| 5 | `policy_run` payload: "telemetry, decisions, germination epoch, `R^test`, status" | §Fan record | `FanRecord` has no field for decisions or germination epoch. |
| 6 | `preflight_iter` records with "an iteration counter" | §Freeze discipline (R2 stats R2-7) | `kind` value exists; `FanRecord` has no field for gate results or iteration. |
| 7 | α/β trajectories in the report | §Report | T17 declares `plot_alpha_beta(record, ...)`. Nothing records α/β per epoch — `ArmResult` (T9, line 638) has no such field. **A plot with no data source.** |
| 8 | "realized p split by sign(A)" | §Telemetry and policy; §Report | T17 prints it; T16's output dict does not contain it; nothing stores per-grid-point `p` and `A`. |
| 9 | `rms_ratio_blend_entry` (gate 5's only input) | §Pre-flight gate 5 | Declared on `ArmResult`; no task states where it is measured. Gate 5 (T14, line 931) consumes it. |

Also unowned but lower-stakes: `schedule_id` (field declared, never defined);
`--eval` asserting the frozen-block hash (spec §Freeze discipline says "`--eval`
asserts it"; T16 only checks that eval records post-date the freeze); the dev
subset flag (`load_data(subset=)` exists, no CLI flag reaches it); `--replay` at
the recorded `worker_count` under gate 8's re-scoping contingency.

**Impact.** Items 1, 2 and 4 are correctness/assurance mechanisms the spec added
*in response to panel findings* — dropping them silently un-does R2 dynarch R2-F4,
R2 determinism N4, and R3 determinism respectively. Items 7, 8 and 9 will surface
as "the report can't be produced" at Task 17, after collection is spent.

**Recommendation.** Add the nine to their owning tasks (1→T15's
`run_collection_episode` with `derive(episode_seed,"nullseed-subsample") % 10 == 0`;
2→T15 via a `multiprocessing.Event` the parent polls and workers check per fan;
3→T14 gate 8, see H2; 4→T1; 5,6→T10 as an optional `payload: dict` on `FanRecord`
with per-`kind` required keys; 7,8,9→T9's `ArmResult` and T16's output dict).
Then **replace the self-review section's coverage claim with a checklist that a
reader can mechanically verify**, or delete the claim.

---

#### H2 — Runtime is unquantified; both stated estimates are optimistic by roughly 2×, and the full programme is a ~34-hour multi-day run
*Failure mode: NFR handwaving*

**Measured floor.** I benchmarked the plan's host (widths 32/64/128, Conv-BN-ReLU
×2 + pool per stage, GAP, linear; 288,746 params) on one of the two RTX 4060 Ti
16GB cards under the plan's exact Class-1 flags (`use_deterministic_algorithms`,
`cudnn.deterministic`, `benchmark=False`, TF32 off both, `CUBLAS_WORKSPACE_CONFIG=:4096:8`),
batch 128, 351 steps, including the per-step per-stage grad-norm capture the plan
requires:

```
1 train epoch = 2.78 s
```

Treat that as a **floor**: it excludes the batch gather from resident CIFAR, the
`augment` call, the per-epoch 5k val evaluation, telemetry construction, the seed
module's own forward/backward, the trust-region term, and any H2D transfer of
`CommonFuture` indices (the plan never states whether they live on GPU or CPU).
A realistic per-epoch figure is ~3.0–3.3 s.

**Derived budget** (fan at epoch t ~ U[5,15], mean t=10, arms run t→39 ≈ 30 epochs):

| Phase | Epoch count | GPU-hours @3.0 s |
|---|---|---|
| One episode (collect) | 40 base + 2 fans × 5 arms × 30 = **340** | 0.28 |
| Collection, 300 episodes | 102,000 | **85** |
| Preflight, 30 episodes + 10 refans | 11,700 | **9.8** |
| Eval, 100 episodes × (40 base + 4 comparators × 40 + 2 grid fans × 5 × 30) | 46,000 | **38** |
| Eval ceiling refans (30 × 5 × 30) | 4,500 | 3.8 |
| **Total** | **~164,000** | **~137 GPU-h** |

Aggregate throughput across 2 cards × 3 process workers is **not** 6×; the workers
timeshare each card. At 7.9 ms/step this workload is partly launch-bound so
concurrency does help — I estimate **3–5× aggregate** (this factor is a guess and I
label it as such). At 4×:

- Collection ≈ **21 hours** (range 17–28 h). Plan/spec say "fit overnight with
  margin"; T15 step 6 says "300 episodes / 600 fans by morning." **~2× optimistic.**
- Preflight ≈ **2.4 hours** per iteration. T14 step 6 says "~1–2 h" — close, but
  step 6 also says "iterate the sampler per gate remedies **until all gates pass**"
  and gives no per-iteration budget. Three iterations is a full working day.
- Eval ≈ **10 hours**, as a one-shot with no resume contract (see C3).
- **Full programme ≈ 34 hours wall-clock**, before any preflight re-iteration.

**Impact.** This is not just scheduling. It changes the plan's shape: (a) a 21-hour
collection means the twin-abort halt (H1 #2) is the difference between losing an
hour and losing a night; (b) a 10-hour one-shot eval with no resume is a real risk
of an unrepeatable run (C3); (c) an unbudgeted preflight tuning loop is the phase
most likely to be cut short under time pressure, and it is the phase the spec's
freeze discipline depends on.

**Recommendation — a two-line change that makes the estimate exist.** Spec gate 8
already runs the twin at 1 worker vs full worker count on one episode seed. Have it
**record wall-clock alongside the bitwise verdict**, and have Task 13's `--selftest`
time one epoch with Class 1 on and off. That single addition yields, from runs the
spec already mandates:
- the concurrency factor (1-worker vs N-worker epoch throughput) → replaces my guess;
- the **deterministic-mode cost** the spec requires measuring and no task measures
  (H1 #3);
- a measured per-epoch figure → a real budget table.

Then put the budget table in the plan's "Execution ordering" section and revise
T14/T15 step 6's expectations to the measured numbers.

---

#### H3 — The host is ~2× the spec's stated size and varies 7.4× across pathologies; the plan's own param test covers only the pathology that passes
*Failure mode: NFR handwaving / untraceable design*

Spec: "deliberately undersized 3-stage CNN (**~150k params**)". Measured, building
the plan's Task 4 wiring exactly:

| Pathology | Widths | Params |
|---|---|---|
| `under_normalized` | 32/64/128, BN removed | **288,746** |
| `no_spatial_mix` | 32/64/128, stage2 1×1 | 239,594 |
| `mild` | 32/48/96 | 170,730 |
| `channel_starved` | 32/24/32 | 38,986 |

The plan's `test_param_count_undersized` (line 350) asserts `80_000 < n < 250_000`
and runs on `"mild"` (170,730) only. `under_normalized` at 288,746 **fails the
plan's own band** and no test catches it. Spread across pathologies is **7.4×**.

**Impact.** (a) Direct spec-fidelity deviation, unsurfaced, in violation of Global
Constraint #1. (b) The spec's checkable property "plateaus by epoch ~12–15" was
calibrated for a ~150k host; the plan's is 1.9× that. **Whether the decision window
(5–15) still brackets the profitable region is unverified** — I did not train to
convergence (Information Gap #5). If it does not, it would present as a gate 6
(horizon adequacy) failure whose real cause is host size, and gate 6's stated remedy
(horizon, window) would not fix it. Resolvable in ~10 minutes of GPU time: one
40-epoch run per pathology before Task 14. (c) Combined with C1, capacity varies so
much across pathologies that the money chart is partly a width experiment.

**Recommendation.** Resolve jointly with C1. Reduce healthy widths to land near
150k (e.g. 32/48/96 as the *healthy* baseline gives 170.7k; 24/48/96 gives ~150k),
hold stage-2 width fixed for the slot contract, and make the param test parametric
over all four pathologies with a band derived from the spec's figure.

---

#### H4 — Plan-authored constants are presented under a "verbatim from the locked spec" banner
*Failure mode: weak decision record*

Plan line 11: "**Global Constraints (verbatim from the locked spec** — every task
inherits these)". Line 17's list includes `tau_eps=1e-6`. The spec says only
"ε a floor on the denominator" — **no value**. Further constants introduced by the
plan and not in the spec at all:

- `seed_lr = 0.05` (Task 1 `Config`, line 108) — placed in `FROZEN_FIELDS`, which is
  correct *if* it is a frozen constant, but it is a **new pre-registered number
  added to a LOCKED spec's frozen block** by the plan. Spec gate 5's remedy list
  names "seed LR", so the spec assumes one exists — it never fixes its value.
- `Adam(1e-3)` for the policy optimizer (Task 12, line 850) — not in the spec, not
  in `Config`, not in any hash, therefore not replayable and not frozen. It selects
  the checkpoint that produces the headline.
- `warmup_frac = 0.3` (line 117) — the spec's R3 reward N10 disposition
  *explicitly* justified the warm-up as "pure ordering, offline, replayable, **no new
  constant**." The plan adds a constant, and puts it under "non-frozen engineering
  knobs" where it is tunable post-freeze.
- Eval chunk size 1000 (Task 8, line 571) — minor, but it is the one lever that
  could move the memory budget (see the PASS section).

**Impact.** The plan's own Global Constraint #1 says deviations are "surfaced to the
user, never silently patched." Four constants entered a LOCKED spec's parameter set
under a banner asserting they came from it. For a run whose entire epistemic value
rests on pre-registration, that is a provenance defect, not a formatting one.

**Recommendation.** Split line 11's section into **"Verbatim from the spec"** and
**"Introduced by this plan — requires owner sign-off before Task 14 step 6"**, list
the four there with their justification, and route them through the freeze decision
explicitly. `Adam(1e-3)` and `warmup_frac` move into `Config`; decide per-constant
whether each is frozen (I would freeze `policy_lr` and `warmup_frac`; both change the
selected checkpoint).

---

#### H5 — No telemetry feature carries "class-confusion spread", the designed signature for one of the four pathologies
*Failure mode: untraceable design / integration reality gap*

Spec §Pathology sampler, row 3: `no spatial mixing (1×1 stage 2)` → telemetry
signature **"class-confusion spread"** → fan winner `attn`. Plan Task 3's
`TelemetryRecord` fields (line 274) are exhaustive and closed ("NO other fields ever"):
`epoch, train_loss, val_loss, val_acc, train_loss_delta, val_loss_delta,
grad_norm_mean(3), grad_norm_var(3), act_saturation(3), weight_norm(3)` =
`TELEMETRY_DIM = 18`. **Nothing derived from the confusion matrix or per-class
accuracy.** The other three signatures map cleanly (spiky grad norms →
`grad_norm_var`; activation saturation → `act_saturation`; early plateau + high
train-loss floor → `train_loss` + `train_loss_delta`).

**Impact.** Gate 2a (linear probe telemetry → pathology) must separate four classes,
one of which has no distinguishing feature. Gate 2's remedy is stated as "sampler" —
so a failure caused by a missing telemetry feature would be "remedied" by retuning
the pathology sampler, which is the wrong lever and burns preflight iterations
(H2) chasing the wrong cause. Worse, if gate 2a passes anyway, `no_spatial_mix` is
being identified by an *incidental* correlate, which weakens the demo's central
claim (telemetry → diagnosis) exactly where the money chart reads it.

**Recommendation.** Add to `TelemetryRecord` before Task 3 is implemented — e.g.
`val_class_acc: tuple[float, ...]` (10 entries) or its two summary statistics
`val_class_acc_std` and `val_top2_confusion_mass`, computed in the existing per-epoch
val pass at no extra cost. Update `TELEMETRY_DIM` and note it as a plan-introduced
addition under H4's new section (it does not violate the blindness rule — it is a
deterministic function of host state and logical epoch).

---

#### H6 — The no-decay split is a name-substring heuristic that misses host BatchNorm affine weights, and its test is vacuous on that path
*Failure mode: silent default*

Spec §Optimizer contract: "**no-decay list: the scalar gain, all norm affines, all
biases**". Plan Task 5 (line 384): `NO_DECAY_KEYWORDS = ("gain", "bias", "bn", "ln",
"norm")`, matched as a substring against the qualified parameter name; Task 6 applies
the same `split_decay_groups` to the **host** in `build_optimizer` (line 460).

Under the positional `nn.Sequential` construction Task 4 describes ("three stages
(`stage1/2/3`: Conv-BN-ReLU ×2 + pool each)", line 332), host parameter names are
`stageN.M.weight` — matching none of the five keywords, so **every host BN `weight`
receives `wd=5e-4`**, against the spec's no-decay list. Only `.bias` params are
caught, by luck of the attribute name. Under any other module naming
(`OrderedDict`, named submodules) the behaviour differs — and *that* is the defect
regardless of which naming the implementer picks: **a correctness-critical
classifier whose result depends on unspecified module naming.** `NormSeed`'s
internal `GroupNorm` is a second exposure by the same mechanism.

The plan's test (line 418) is:
```python
no_decay_names = {n for n, _ in no_decay}
assert any("gain" in n for n in no_decay_names)
assert all("bias" not in n for n, _ in decay)
```
It runs on a *seed* module only, asserts one positive and one negative, and would
pass unchanged while every host norm affine is wrongly decayed.

**Impact.** Weight decay on BN γ is a decay-toward-zero trap — the exact failure the
spec's R2 dynarch R2-F2 disposition was written to prevent for the seed gain. Applied
to the host it changes the baseline no-op trajectory, which is the denominator of the
headline. And it is silent: nothing asserts it.

**Recommendation.** Replace substring matching with type/shape classification:
`isinstance(module, (nn.BatchNorm2d, nn.GroupNorm, nn.LayerNorm))` → all its params
no-decay; `param.ndim <= 1` → no-decay; plus the explicit `gain` parameter. Then make
the test exhaustive rather than illustrative:
```python
decay, no_decay = split_decay_groups(build_host("mild", 1))
assert all(p.ndim >= 2 for _, p in decay)          # only conv/linear weight matrices
assert {n for n, _ in decay} | {n for n, _ in no_decay} == all_param_names  # partition, nothing dropped
```

---

#### H7 — Twin divergence does not halt sibling workers
*Failure mode: integration reality gap*

Broken out from H1 #2 because it has a distinct blast radius. Spec §fan step 2 is
emphatic and explains why: an abort "**halts all workers**, not just its own: a twin
divergence means deterministic mode is not holding, so sibling records are equally
suspect (R2: determinism N4; R3: determinism LOW)."

Plan Task 9 raises `TwinDivergence` inside `run_fan`. Task 15's `run_collect` spawns
workers via `multiprocessing.get_context("spawn")` and "parent joins and prints
per-worker counts" — no abort propagation, no shared event, no exit-code inspection
described. One worker dying at hour 3 of a 21-hour run leaves five workers writing
suspect records until morning, and `Store.merge()` will happily merge them.

**Recommendation.** T15: pass a `multiprocessing.Event` to each worker; workers check
it before each fan and after each arm; on `TwinDivergence` a worker sets it, writes a
divergence-report record, and exits non-zero. Parent watches the event, terminates
stragglers, and prints the first-differing epoch. Add a CPU test that a raised
`TwinDivergence` in worker 0 stops worker 1 within one fan.

---

### MEDIUM

#### M1 — The plan's literal code does not run: lint, imports and an arity contradiction
*Failure mode: integration reality gap*

The plan states (line 21) "pre-commit runs ruff/mypy — code must pass both" and
commits after every task. I ran the plan's own Task 1/Task 2 snippets through the
project's ruff config (`select = ["E","W","F","I","N","UP","B","C4","SIM","RUF"]`,
`ignore = ["E501"]`):

```
E401  Multiple imports on one line              (line 84: import argparse, dataclasses, ...)
E702  Multiple statements on one line (×4)      (lines 103, 110: K: int = 3; M: int = 3; F: int = 2)
E731  Do not assign a lambda expression         (line 225: d = lambda t: t.to(device))
N815  Variable `diverged_R` in class scope should not be mixedCase
N806  Variable `B` in function should be lowercase   (line 251, augment)
I001  Import block un-sorted
```
**E702, E731, N815 and N806 are not auto-fixable**, so `ruff --fix
--exit-non-zero-on-fix` will not rescue them — Task 1's first commit fails its own gate.

Three more mechanical breaks:

- **Missing `tests/unit/__init__.py`.** `tests/__init__.py` exists in the repo;
  `tests/unit/` does not. The plan's File Structure (line 28) creates
  `tests/unit/kernel_demo/__init__.py` but not `tests/unit/__init__.py`. Task 9
  (line 649) does `from tests.unit.kernel_demo.test_episode import tiny_bundle` and
  Task 12 (line 861) `from tests.unit.kernel_demo.helpers import synthetic_fans` —
  both `ModuleNotFoundError` without it. It also changes pytest's rootdir insertion,
  which is what makes `experiments` importable at all.
- **`experiments` is not on the test path.** `pyproject.toml` sets
  `pythonpath = ["src"]`. `from experiments.kernel_demo import ...` works only via
  pytest's prepend-mode rootdir side-effect, and only if the `__init__.py` chain is
  complete. Fix: `pythonpath = ["src", "."]`.
- **`run_base` arity contradiction.** Task 9's interface block declares
  `run_base(ctx, cfg) -> list[str]` (line 641); Task 9's own test calls
  `hashes, curves = run_base(ctx, CFG)` (line 655) and Task 14 describes it as
  recording "hashes + both unit curves". Pick one and state it once.
- **`synthetic_agreement` is used but not imported** in `test_learning.py`
  (line 867 calls it; lines 858–861 import only `synthetic_fans`).

**Recommendation.** Fix the snippets in place (they are copy-paste sources for
agentic workers, which is why this matters more than usual), add
`tests/unit/__init__.py` to File Structure, add `"."` to `pythonpath` in Task 1
step 1, and reconcile `run_base`.

---

#### M2 — The money-chart test's red-green example is arithmetically impossible
*Failure mode: risk theatre (a test that cannot pass)*

Task 12, lines 878–883:
```python
paths = ["a"]*10 + ["b"]*10 ; picks = ["x"]*10 + ["y"]*10 ; designed = {"a":"x","b":"y"}
obs, p = money_chart_permutation_pvalue(paths, picks, designed, n=2000, seed=3)
assert obs == 2 and p < 0.05
```
The permutation null shuffles pathology labels across fans, keeping picks fixed.
Row `a`'s modal pick is `x` iff more than 5 of the 10 `x`-items land in row `a`:

P(both rows match | null) = Σ_{k=6..10} C(10,k)·C(10,10−k) / C(20,10)
= (1 + 100 + 2025 + 14400 + 44100) / 184756 = **0.328**

So `p ≈ 0.33` and the assertion **fails**. `obs == 2` is correct; the p-value
assertion is not. With only two rows and two categories there is no fixture that
gives p < 0.05 — the statistic is too coarse.

**Impact.** A TDD plan whose worked red-green example cannot go green will either
burn an agent's cycle or, worse, prompt it to "fix" `money_chart_permutation_pvalue`
until the test passes — silently breaking the statistic that judges the headline
money chart.

**Recommendation.** Replace with a 4-pathology × 4-seed fixture matching the real
case (where the ≥3-of-4 null is genuinely small), or split into two assertions:
`assert obs == 2` and `assert 0.30 < p < 0.36` (a calibration check against the
closed form above, which is a *stronger* test of the implementation than `p < 0.05`).

---

#### M3 — τ-init is measured in `eval()` mode but the arm trains in `train()` mode, so BN-carrying seeds do not enter TRAINING at τ
*Failure mode: integration reality gap*

Spec (R3 morpho) requires τ-init "under `eval()`/no-grad" because "a training-mode
pass would update host BN stats per arm and trip the cross-arm assertion." The
concern is the **host**. Plan Task 5's `tau_init` (line 383) applies `seed.eval()`
to the **seed**, computes `f0` from the seed's *running* BN statistics (freshly
initialised to mean 0 / var 1, i.e. near-identity), then restores `seed.train()`.

`conv_light` and `conv_heavy` both carry internal BN. In training mode they
normalise by *batch* statistics, so the realised `RMS(Δ)/RMS(h)` at the first
TRAINING step differs from τ by whatever the gap is between fresh running stats and
real batch stats — potentially a large factor on the first epoch.

The plan's own test exposes this and then asserts it away: `test_tau_init_hits_target_rms`
(line 402) calls `tau_init` (eval mode) then re-measures `s(h)` in **train** mode and
asserts agreement within 5%. For `conv_light`/`conv_heavy` that assertion is
measuring the very discrepancy it should catch, and its pass/fail is data-dependent.

**Impact.** Spec: "Every arm enters TRAINING at the same `RMS(Δ)/RMS(h) = τ`". If
BN seeds do not, arms wake at architecture-dependent rates — the exact failure R2
dynarch R2-F1 reopened zero-init to prevent. Gate 5 (2× band across arms) is the
instrument that would catch it, at the cost of a preflight iteration.

**Recommendation.** Separate the two mode concerns: forward the **host** under
`eval()`/`no_grad` to obtain `host_feats` (satisfying the spec's stated reason), and
evaluate `seed.f` in **train** mode on that fixed batch (its BN sees the same batch
it will see in training). Or, equivalently, warm the seed's BN running stats on the
fixed batch before measuring `f0`. Then make the test assert the mode it actually
uses, and add a cross-arm assertion that all four realised ratios agree within gate
5's 2× band on a real host batch.

---

#### M4 — `run_fan` and `run_refan` are two branch executors; the spec requires one
*Failure mode: integration reality gap*

Spec §fan step 2: arms run "all through the **one branch executor (no privileged
path)**." Plan declares `run_fan(ctx, snap, base_hashes, cfg)` (Task 9, arms = 4
seeds + twin) and `run_refan(cfg, data, device, episode_seed, fan_epoch, k, ...)`
(Task 14, arms = 4 seeds + fresh no-op) as separate functions with different arm
sets and different signatures. A divergence in their behaviour is exactly the class
of asymmetry the twin exists to detect and cannot detect here, because the twin
lives in only one of them.

**Recommendation.** One executor: `run_branch_set(ctx, snap, arms: list[str], baseline: list[str] | None, cfg)`.
`run_fan` = `arms=[*SEED_NAMES, "twin"]` with `baseline=base_hashes`; `run_refan` =
`arms=[*SEED_NAMES, "noop"]` with `baseline=None` (the spec's stated reason the twin
cannot apply under a redrawn future). The null-seed subsample (H1 #1) becomes a
sixth arm name, not a third code path.

---

#### M5 — How fans obtain their snapshot is unspecified, with a runtime consequence
*Failure mode: integration reality gap*

`run_fan` takes a `snap` (Task 9). Task 14's `run_collection_episode` says "base run
(recording hashes + both unit curves), two fans at the scheduled epochs" — it never
says whether the snapshot is captured *during* the base run at the scheduled epochs
or obtained by re-running the prefix. Task 9's test does the latter (`make_episode`
then two `train_one_epoch` calls, line 661–665).

Re-running prefixes costs an extra 2 × ~10 epochs per episode (~6% of the episode
budget, ~5 GPU-hours over collection) and, more importantly, is a **second path to
the same state**, which is precisely what the twin exists to rule out.

**Recommendation.** State it in Task 14's interface: `run_collection_episode` takes
snapshots inline during the single base run at the two scheduled epochs and passes
them to `run_fan`. Add it to the T8 `EpisodeCtx` contract.

---

#### M6 — Window inclusivity and the `random` comparator's span are ambiguous, with an off-by-one that silently changes the null
*Failure mode: NFR handwaving*

`window = (5, 15)`. Task 14's `draw_schedule` uses `range(window[0], window[1]+1)` —
**11 epochs, inclusive**. Task 11's `decide_live` "returns `(False, None)` outside
`cfg.window`" — inclusivity unstated. Task 16's `random` comparator is
`derive(episode_seed,"random-null") % window-span + window[0]` — `window-span` is
not defined and is 10 or 11 depending on reading, so epoch 15 is either reachable or
not. Task 16 also writes `draw_schedule(episode_seed ⊕ "evalgrid")` — `⊕` between an
int and a string is not an operation; presumably `derive(episode_seed, "evalgrid")`.

Additionally the `random` comparator's *seed* choice is described as "uniform over
the four" with no `derive` label, which violates the plan's own Global Constraint
(line 16: every draw from a named generator).

**Impact.** `random` is one of the four constitutional comparators; the spec (rev 6)
explicitly says they "are load-bearing and may not be inherited from review threads."
An off-by-one in its support changes the null the headline is measured against.

**Recommendation.** Define `WINDOW_EPOCHS = tuple(range(window[0], window[1]+1))`
once in `Config`, use it in `draw_schedule`, `decide_live` and the `random`
comparator, and give the random comparator's seed draw its own label
(`derive(episode_seed, "random-null-seed")`).

---

#### M7 — A stochastic learning threshold is a flaky gate in the unit suite
*Failure mode: risk theatre*

Task 12, line 863–868: `train_policy` on 120 synthetic fans, `assert acc > 0.6`,
with a stated "keep it < 60 s by capping steps". A trained-model accuracy threshold
under a step cap is the classic flaky test — it will pass locally and fail on a
slower runner or after any unrelated change to the initialisation order.

**Recommendation.** Pin the generator seed (already done), assert on a *monotone*
property instead — e.g. `assert final_tune_objective > initial_tune_objective` and
`assert acc > 0.4` as a loose smoke floor — and move the `> 0.6` check to a
`@pytest.mark.slow` test excluded from the default run. Note the repo uses
`--strict-markers`, so register the marker in `pyproject.toml`.

---

#### M8 — Defensive machinery declared but never exercised
*Failure mode: gold-plating / vacuous tests*

- `SplitViolation` (Task 10) is described as a "defensive double-wall" that raises
  when a caller requests `train` and eval records match the filter path. Task 10's
  `test_split_wall` (line 749) only asserts that filtering *works* — it never
  triggers `SplitViolation`. An unexercised exception class is not a wall.
- `test_frozen_hash_moves_with_frozen_fields_only` (line 61) tests only the positive
  direction (see C2).
- `FROZEN_FIELDS` is a hand-maintained duplicate of a subset of `Config`'s field
  names with nothing asserting the two stay in sync (see C2's recommendation).

**Recommendation.** Either test the violation path or delete the class and rely on
the filter; add the partition test for `FROZEN_FIELDS`; add the negative case to the
frozen-hash test.

---

### LOW

- **L1 — pre-commit's mypy hook has no `additional_dependencies`.** `.pre-commit-config.yaml`
  runs `mirrors-mypy` in an isolated venv with no `torch`. Every task's commit gate
  (plan line 21) will either fail on `import torch` or silently degrade to
  `ignore-missing-imports`. Untested today because the repo has no torch-importing
  code yet. Add `additional_dependencies: [torch, torchvision]` or exclude
  `experiments/` from the hook and rely on Task 18's explicit `uv run mypy`.
- **L2 — CLI surface has no owner.** Task 1 builds an argparse where every mode
  takes only `--store` and unconditionally raises `SystemExit("not implemented")`.
  Tasks 13–17 each mention new flags in prose (`--device`, `--devices`, `--workers`,
  `--limit`, subset) but no task owns updating the parser, and nothing retires
  Task 1 step 5's expectation that `selftest` prints "not implemented". Add an
  explicit "extend `main()`" step to each mode task.
- **L3 — `--selftest`'s blindness grep does not check `pathology_id`.** Task 13
  item 3 greps for `time.time|datetime.now|monotonic|os.environ|hostname`. The
  spec's blindness rule also forbids `pathology_id` and device/worker identity in
  the telemetry path. Task 3's field-name test covers `pathology_id` at the dataclass
  level; add it to the grep so the *path* is covered too.

---

## NFR verification: memory — **PASS**, with arithmetic

The lead asked specifically whether 16 GB/card holds with GPU-resident CIFAR ×3
workers/card + model + fan arms. **It does, with ~5× headroom.** Measured on the
actual hardware (RTX 4060 Ti, 15.6 GiB usable), building the plan's largest
pathology (288,746 params — worst case) at batch 128 under Class-1 flags:

| Component | Size | Basis |
|---|---|---|
| CUDA context + kernels | ~241 MiB | measured (447 MiB process footprint − 206 MiB peak alloc) |
| CIFAR-10 resident, uint8 NCHW | 184.3 MB | 45k×3072 + 5k×3072 + 10k×3072 |
| `CommonFuture` (if GPU-resident) | 19.8 MB | order 40×44,928×8B + crops 40×351×128×2 + flips 40×351×128 |
| Training activations, peak | 206 MiB | measured, `max_memory_allocated` |
| Eval chunk of 1000 (no-grad high-water) | ~300–400 MB | 1000×32×32×32×4B per stage-1 tensor, retained by the caching allocator |
| Snapshot deep-copy (params + momentum + buffers) | ~2.5 MB | 288,746 × 4B × 2 + BN buffers |
| Seed module + its activations | ~2 MB | worst case `conv_heavy` |
| **Per worker** | **~850 MB – 1.05 GB** | |
| **3 workers/card** | **~2.6 – 3.2 GB of 15.6 GB** | |

Fan arms do **not** multiply this: the spec (R3 determinism) requires arms to run
*sequentially within a worker*, and the plan preserves that (Task 9 `run_fan` runs
arms sequentially). The only lever that could move the budget is the **eval chunk
size of 1000**, which is plan-introduced and not in the spec (see H4) — at 4000 it
would still hold.

**The headroom is itself actionable:** at ~1 GB/worker, 6 workers/card fits inside
7 GB. If gate 8's timing instrumentation (H2) shows throughput still scaling, worker
count is the cheapest lever on the 34-hour programme — bounded by the fact that
`worker_count` is provenance-only in the replay key *provided gate 8 passes*.

**Conclusion: memory is not a risk. Time is.** The plan quantifies neither; only one
of them needed quantifying.

---

## What the plan does well

Stated plainly, because it makes the Criticals mean something:

1. **Spec citation is genuinely traceable at the disposition level.** Task interfaces
   cite `R2: dynarch R2-F4`, `R3: morpho`, `rev 6, external review` — not "per the
   spec". Forward coverage (spec section → task) is complete; it is the
   *requirement*-level reverse direction that fails (H1).
2. **The STE/β trick is correct and the tests prove the right property.** `hin =
   h.detach()*(1−β) + h*β` is value-identical to `h` for all β while gating the
   gradient path, and `test_training_isolates_host_gradient` asserts `h.grad == I`
   exactly — the strongest available statement of the spec's isolation requirement.
   I checked the gradient algebra; it holds.
3. **The objective implementation matches the spec formula exactly**, including the
   stop-gradient placement (`pi.detach()` inside `J_now` only) that R2 morpho N5 /
   reward N6 were written to pin down.
4. **GPU checkpoints are marked as needing the user's presence**, and the one-shot
   eval discipline ("no peeking, no reruns") is carried into Task 16 step 6 as an
   explicit gate rather than a hope.
5. **Task 13 step 4's instruction is exactly right**: "If the twin trips on GPU but
   held on CPU, the Class 1 knob set is incomplete — debug THAT... do not weaken the
   check." That is the correct disposition toward the assurance mechanism, and it is
   the sentence most plans get wrong.
6. **Deliberate deviations are declared** (GERMINATED collapsing into TRAINING's
   first tick; a hand-rolled probe instead of sklearn) — the discipline exists; it
   simply was not applied to the four deviations in C1/H3/H4.

---

## Confidence Assessment

**Overall Confidence: High.**

| Finding | Confidence | Basis |
|---|---|---|
| C1 (slot width) | **High** | Plan lines 332–333 read directly; param counts computed and cross-checked against the plan's own asserted bands (lines 412–416). The only inference is the `conv_heavy` bottleneck rule, which the plan leaves unstated — I report both readings. |
| C2 (freeze unenforceable) | **High** | `FROZEN_FIELDS` (lines 121–126) vs spec §Freeze discipline compared field by field; `config_hash` absence confirmed by searching all 18 tasks; Task 15's refusal text read verbatim (line 951). |
| C3 (store identity) | **High** for the mechanism (fields absent, `schema_version` unread — directly verified); **Moderate** for the eval-restart scenario, which depends on H2's runtime estimate being right about the ~10-hour one-shot. |
| H1 (reverse traceability) | **High** | Each of the nine checked in both documents individually. |
| H2 (runtime) | **Moderate.** Epoch time is **measured** (2.78 s, High) and explicitly a floor. The 340-epochs-per-episode decomposition is arithmetic (High). The **3–5× aggregate concurrency factor is a labelled estimate (Low confidence)** — it is the single number that could move the conclusion, which is why the recommendation is to measure it in gate 8 rather than to argue about it. Even at a generous 6× the collection is ~14 h and eval ~6 h. |
| H3 (host size) | **High** | Param counts measured by building the described architecture. |
| H4 (constant provenance) | **High** | Spec searched for each constant; `tau_eps`, `seed_lr`, Adam lr, `warmup_frac` absent. |
| H5 (class-confusion telemetry) | **High** for the absence; **Moderate** for the gate-2 impact, which depends on whether an incidental correlate happens to separate the class. |
| H6 (no-decay heuristic) | **High** | Keyword list and `nn.Sequential` naming both read from the plan; the miss is mechanical. |
| H7 (worker halt) | **High** | Spec requirement explicit; T15 description contains no mechanism. |
| M1 | **High** — ruff run against the plan's literal snippets with the project's own config; repo tree inspected (`tests/unit/` absent, `pythonpath = ["src"]`). |
| M2 | **High** — closed-form hypergeometric computed (0.3281). |
| M3 | **Moderate** — the mode mismatch is certain from the code; the *magnitude* of the resulting τ deviation is not measured and depends on how far fresh BN running stats sit from batch statistics on real host features. |
| M4–M8, L1–L3 | **High** (documentary) except M3-adjacent judgement calls. |

One hypothesis I formed and **discarded on evidence**: I expected `append_seed_group`
to crash for the `norm` seed, whose parameters are all no-decay, leaving an empty
decay group. I tested it — `torch.optim.SGD.add_param_group` accepts an empty
`params` list (torch 2.13.0+cu130), group count stays symmetric across arms, and the
spec's "param-group ordering byte-identical across arms" holds. Not a finding.

## Risk Assessment

**Implementation Risk: High. Reversibility: Moderate** (Tasks 1–3 are sound and all
fixes are localised; the irreversible boundary is Task 14 step 6, the freeze).

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| Headline number computed under a silently mutated frozen block | **Critical** | Medium — requires only one post-freeze edit to a gate threshold or pathology width, with no assertion firing | C2: move thresholds and pathology definitions into `Config`; implement `config_hash`; add the partition test |
| Eval episodes silently double-counted after a restart | **Critical** | Medium — a 10-hour one-shot on consumer GPUs will sometimes not finish | C3: `run_id` + `attempt` + dedup on merge + explicit `--resume` contract |
| Germination crashes on half the sampler at first fan | High | **Certain** as written | C1 |
| Money chart partly measures stage-2 width rather than diagnosis | High | Medium — conditional on C1's resolution | C1 (hold slot width fixed) |
| Collection or eval overruns its window; preflight tuning loop unbudgeted | High | High — my estimate says ~2× over on both stated figures | H2: instrument gate 8 and `--selftest`; publish a budget table |
| Suspect records accumulate for hours after a twin abort | Medium | Low-Medium (the twin should rarely fire; that is the point) | H7 |
| Host BN affine weights decayed toward zero, shifting the no-op baseline | Medium | **Certain** as written | H6 |
| Preflight iterations burned on gate 2 failures caused by a missing telemetry feature | Medium | Medium | H5 |
| An agentic worker "fixes" `money_chart_permutation_pvalue` to satisfy an impossible test | Medium | Medium — this is the specific hazard of TDD plans with wrong fixtures | M2 |
| Task 1 commit blocked by the plan's own lint gate | Low | Certain | M1 |

**Compatibility/maintenance risk:** low — single file, no public interface, no
consumers. **Security risk:** none identified; no external input beyond the CIFAR-10
download. I did not run `wardline scan` (no code exists yet); Task 18 step 3 schedules it.

## Information Gaps

1. **Aggregate throughput of 3 process workers per 4060 Ti** — I measured single-stream
   epoch time only. If the real factor is 6× rather than my assumed 4×, H2's
   conclusions shrink by a third (collection ~14 h, still not "overnight with
   margin", but closer). *Resolved by:* gate 8 recording wall-clock — a two-line change.
2. **Deterministic-mode cost** — the spec requires measuring it; nothing does. My
   2.78 s is *with* Class 1 on, so it is the right number for the budget, but the
   ratio is unknown and it is the plan's cheapest available speed lever if the
   claim were ever re-scoped (it must not be — it is on the forbidden-relaxations list).
3. **`conv_heavy`'s bottleneck rule** — "sized to land ~60k params" admits both a
   fixed and a proportional bottleneck, which differ by 2.7× at C=24 and 1.5× at
   C=96. Changes C1's numbers, not its verdict.
4. **Whether the pre-commit mypy hook currently passes** — untestable; the repo has
   no torch-importing code. (L1.)
5. **Actual plateau epoch of the host as specified** — the spec's checkable property
   ("plateaus by epoch ~12–15") was calibrated for ~150k params. I did not train to
   convergence. If the 289k host plateaus later, the decision window (5–15) may not
   bracket the profitable region, and gate 6 would fail for a reason gate 6's stated
   remedy (horizon, window) would not fix. *Resolved by:* one 40-epoch training run
   per pathology before Task 14 — ~10 minutes of GPU time.
6. **Whether `CommonFuture` tensors live on GPU or CPU** — unstated in the plan;
   affects both the memory table (+19.8 MB/worker) and per-step H2D traffic in the
   runtime floor.

## Caveats & Required Follow-ups

**The spec was treated as fixed and correct.** Per the review brief, rev 6 is the
requirements baseline and not under review. Where the plan and spec disagree I scored
the *plan*. In two places (C1's per-pathology width variation, H3's host size) the
plan may have been resolving a genuine under-specification in the spec — if so, the
resolution needed to reach the owner via the plan's own Global Constraint #1, and
that is what I scored. **If the owner decides the spec's scope pin should change
instead, that is a spec amendment, not a plan fix, and it re-opens the freeze.**

**What you must verify before relying on this analysis:**
- My 3–5× concurrency factor. Everything in H2's wall-clock column scales inversely
  with it. The epoch time itself is measured and solid.
- That the `conv_heavy` bottleneck reading I used matches the author's intent.
- That `tests/unit/` genuinely does not exist in a branch I did not inspect — I read
  `main` at the session's starting commit.

**What this review does not cover:**
- The statistical validity of the eval battery (permutation test, Σp² ceiling,
  derangement falsifier). The stats panel reviewed rev 5/6; I checked only that the
  plan *implements* what the spec pre-registered, not whether the spec's design is
  sound. The one exception is M2, which is an arithmetic error in the plan's fixture,
  not a critique of the statistic.
- Whether the demo will produce a positive result. Nothing here bears on that.
- Any code, since none exists.

**Recommended next steps, in order:**
1. **Before Task 4** — resolve C1 with the owner (slot width / scope pin), and H3
   with it. These are the same decision.
2. **In Task 1, while it is cheap** — C2's `Config` restructuring, `config_hash`,
   and the `FROZEN_FIELDS` partition test. Doing this at Task 14 means editing every
   gate function. **Ordering hazard:** step 1 gates the `pathology_widths` *values*
   in step 2 — if C2 lands before C1 is decided, the frozen constants get baked
   around the wrong architecture. The rest of C2 (thresholds, `config_hash`,
   partition test) can proceed immediately and independently.
3. **In Task 3** — H5's telemetry feature, before `TELEMETRY_DIM` is baked into the
   policy and the normalizer.
4. **In Task 10** — C3's `run_id`/`attempt`/dedup/`--resume` contract.
5. **In Tasks 13/14** — H2's instrumentation (epoch timing in `--selftest`,
   wall-clock in gate 8), then publish the budget table and revise the step-6
   expectations before committing the machine to a 21-hour collection.
6. **Housekeeping, any time** — M1 (lint + `tests/unit/__init__.py` + `pythonpath`),
   M2 (fixture), H4's provenance split, H6's no-decay classifier, H7's worker halt.
7. **Replace or delete** the "Self-review notes (done)" coverage claim (H1). A
   self-certified claim that a mechanical check falsifies is worse than no claim.
