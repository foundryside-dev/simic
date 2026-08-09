# Edit Review: docs/superpowers/plans/2026-08-09-kernel-demo.md (rev 2)

**Reviewer:** complex-reviewer (document intent-fit + structural integrity only; engineering
and spec content deliberately not relitigated)
**Target:** `docs/superpowers/plans/2026-08-09-kernel-demo.md` @ 7b8d1df (995 lines)
**Before-state:** same path @ 5021e29 (1020 lines)
**Edit type:** full rewrite folding ~70 findings from ten SME reviews + two external reviews

**Overall verdict: NEEDS CORRECTIONS.**

---

## Summary

Rev 2 is a substantive improvement on rev 1 — the load-bearing fixes (arm-local
materialization, `read_test` unit wall, `rng_scope`, FreezeManifest, `stage_k/m/f` rename,
`diverged_r` rename, the D1–D7 register, the Operational Phases split) all landed and are
internally coherent where they touch. The `CommonFuture.order` shape, the D7 parameter
arithmetic, the FROZEN_FIELDS↔Config↔test triangle, the 17-file test list, and the ruff/mypy
claims about this repo all check out (verified against `pyproject.toml` and by recomputation).

But the rewrite left the document **not self-contained**, and that is not a cosmetic problem:
the plan's own banner instructs a subagent to execute it task-by-task, and four tasks cannot
be executed from rev 2 alone. On top of that there are eleven concrete symbol/signature/
cross-reference defects and two silently-dropped deviation records.

---

## Critical

### 1. The plan defers to rev 1 nine times and never says where rev 1 is

**Locations:** L298, L343 (Task 2), L358 (Task 3), L519, L524, L526 (Task 6), L551, L553
(Task 7), L625 (Task 8), L671 (Task 9), L711, L712, L718 (Task 10), L755, L759 (Task 11),
L794 (Task 12).

Task 6 (`**Interfaces:** as rev 1, with corrections:`), Task 10 (`rev 1's FanRecord/Store,
corrected`), Task 11 (`rev 1, corrected and pinned`) and Task 12 (`rev 1, corrected`) do not
state their interfaces at all — they state a *delta* against a document that is not cited,
not linked, and not identified by commit. Everything below is consequently unreachable from
rev 2: `Stage`, `cosine_ease`, `Slot` (attributes and `forward`), `TelemetryDivergence`,
`take_snapshot`, `restore_snapshot`, `FanRecord`, `SCHEMA_VERSION`, `Store`, `encode_record`,
`decode_record`, `SplitViolation`, `fan_to_example`, `policy_loss` body, `Policy.forward`,
`query_teacher_forced`, `NO_DECAY_KEYWORDS` replacement rationale, and the test helpers
`_rec`, `_armed_slot`, `_episode_with_base`, `CFG`.

Grep confirms zero occurrences in rev 2 of `take_snapshot`, `restore_snapshot`, `cosine_ease`,
`collect_stage_stats`, `attach_stat_hooks`, `stage_stats`, `train_tune_split`.

**Minimal correction:** either (a) inline the inherited interface blocks into Tasks 6, 10, 11,
12 (and the Task 3/8/9 test suites), or at minimum (b) add to the Plan-provenance paragraph:
"Interfaces marked *as rev 1* are inherited verbatim from
`git show 5021e29:docs/superpowers/plans/2026-08-09-kernel-demo.md`, which is a REQUIRED read
dependency for Tasks 2, 3, 6, 7, 8, 9, 10, 11 and 12." (a) is strongly preferred — a plan whose
execution requires a superseded revision defeats the freeze/`config_hash` discipline it argues for.

### 2. `fan_id` uniqueness assert collides with `policy_run` and `preflight_iter` records

**Locations:** L714 (new assert) vs L710-rev1 (`fan_id` = sha256 of
`episode_seed:fan_epoch:kind:refan_k`) vs L917 (`preflight_iter` per invocation) and L951
(four comparators per eval episode, all `kind="policy_run"`).

`Store.merge()` now "asserts `fan_id` uniqueness". But `fan_id`'s identity tuple contains no
comparator and no iteration counter, so the four comparator runs (`trained`, `random`,
`schedule_only`, `fixed_epoch`) of a single eval episode all hash to one `fan_id`, and every
`preflight_iter` record for a given iteration collides with the next. `merge()` will raise on
any real store.

**Minimal correction:** in Task 10, extend the `fan_id` identity tuple to
`episode_seed:fan_epoch:kind:refan_k:policy_checkpoint_id:iteration`, **or** scope the
uniqueness assert to `kind in ("fan", "refan")` and say so explicitly.

### 3. The retained rev-1 `_rec` helper hardcodes `fan_id="x"`, so the new merge test cannot pass

**Locations:** L718 ("rev 1's round-trip/merge tests"), L721-726 (new duplicate test) vs
rev 1 L723-733 (`_rec(...)` ends `telemetry=[], fan_id="x"`).

Rev 1's retained `test_shards_merge_content_ordered` appends three `_rec()`s, all with
`fan_id="x"` — under the Task 10 uniqueness assert that test now fails, and the new
`test_merge_rejects_duplicate_fan_ids` passes for the wrong reason.

**Minimal correction:** state in Task 10 that `_rec` must compute `fan_id` from its identity
fields (not the literal `"x"`), matching `FanRecord`'s definition.

### 4. `host_init_hash = state_hash` in Task 4 forward-references Task 7

**Locations:** L392 (Task 4 Produces: "`host_init_hash = state_hash` alias") vs L548 (Task 7
defines `state_hash`), and L423-424 (Task 4's test calls `host_init_hash`).

Task 4's TDD step must go green three tasks before its only dependency exists. Rev 1 handled
this correctly: Task 4 defined `host_init_hash(host)` standalone (rev1 L334) and Task 7 said
"`host_init_hash` becomes an alias" (rev1 L534). The rewrite collapsed both statements into
the Task 4 line and dropped the Task 7 rebinding.

**Minimal correction:** restore the two-step form — Task 4 Produces `host_init_hash(host) -> str`
(sha256 over sorted `state_dict` bytes); Task 7 Produces `state_hash` and rebinds
`host_init_hash = state_hash` (noting the zero-normalization now applies).

### 5. `policy_loss`'s scalar `fan_density` contradicts the two-key frozen temperature mapping

**Locations:** L795 (`measure_fan_density` returns `{best_minus_second, best_minus_noop}`;
`β_which = beta_which_frac × best_minus_second`, `β_now = best_minus_noop / beta_now_div`)
vs L798 ("`policy_loss` — rev 1's body verbatim") and the call sites L830, L842
(`policy_loss(pol, batch, cfg, fan_density=0.05, enable_now=...)`).

Rev 1's verbatim body computes **both** temperatures from **one** scalar
(`b_which = beta_which_frac * fan_density`, `b_now = fan_density / beta_now_div`). Keeping it
verbatim means the pre-registered two-scale mapping — the thing the FreezeManifest records at
L918 — is never actually applied in the loss.

**Minimal correction:** change the signature to
`policy_loss(policy, batch, cfg, *, beta_which: float, beta_now: float, enable_now, mask_fn=None)`,
state that `train_policy` derives the two values from `frozen_density`, and update the two test
call sites at L830/L842.

### 6. `--freeze`'s "HEAD equals the recorded Phase-A commit" precondition has no artifact

**Locations:** L918 (freeze refuses unless "HEAD equals the recorded Phase-A commit"), L52 and
L984-985 (Phase A produces a "final implementation commit"), L985 ("`preflight --freeze` at the
Phase-A commit").

No task writes the Phase-A commit SHA anywhere `run_preflight` could read it. The refusal as
written is unimplementable.

**Minimal correction:** name the artifact — e.g. Phase A writes
`runs/kernel_demo/phase_a_commit.txt` (or Task 14 takes an explicit `--expect-head <sha>`
argument that the operator supplies and the manifest records).

### 7. `kind` union does not admit the two event records the plan writes

**Locations:** L932 ("writes an extension event record"), L949 ("writes a store event record"),
vs Task 10's `kind` union (inherited: `"fan"|"refan"|"policy_run"|"preflight_iter"`).

Both `--extend` and `--void-preregistration` write records whose `kind` is undefined, and
neither has a defined `split_role` (union is `{preflight, train, tune, eval}`).

**Minimal correction:** in Task 10, extend `kind` to include `"extension"` and
`"void_preregistration"` (or a single `"event"`), and state the `split_role` these records carry.

---

## Major

### 8. Symbols used in test code but defined in no task's Produces/Files block

| Symbol | Used at | Defined |
|---|---|---|
| `build_seed` | L467, L472, L480, L491, L499 (Task 5 tests), L584 (Task 8 Consumes) | nowhere — Task 5's Produces lists `SeedDelta` and the four subclasses but not the factory (rev 1 L382 had it) |
| `build_record` | L584 (Task 8 Consumes) | nowhere — rev 1 declared it in Task 3 (rev1 L278) |
| `_assert_trainable` | L737 ("the guard itself, exercised directly") | nowhere — Task 10 produces only `load_for_training` |
| `synthetic_batch` | L826 | nowhere — Task 12's `helpers.py` list is `synthetic_fans`, `synthetic_holdout` |
| `adversarial_batch_with_divergent_arm` | L841 (comment says "# helpers.py") | nowhere |
| `synthetic_agreement` | L813 | nowhere in rev 2 (rev 1 L886 mentioned it) |
| `_rec_at` | L779 | nowhere, in either revision |
| `CFG` | L634, L638, L645, L646, L679, L680, L700 | nowhere in rev 2 |
| `TelemetryDivergence` | L353 (prose only) | never declared as produced (rev 1 L275 did) |

**Minimal correction:** add `build_seed(name, channels, init_seed) -> SeedDelta` to Task 5's
Produces; add `build_record(...)` and `class TelemetryDivergence(RuntimeError)` to Task 3's
Produces; add `_assert_trainable(records) -> None` to Task 10's Produces; add `synthetic_batch`,
`adversarial_batch_with_divergent_arm`, `synthetic_agreement`, `_rec_at` to Task 12/Task 11's
helper inventories; define the `CFG` fixture in Task 8's conftest section (see #9).

### 9. `CFG` — the shared tiny-config fixture — is undefined, and rev 1's version uses dead field names

**Locations:** seven call sites (L634-700) vs rev 1 L593 (`CFG = dataclasses.replace(Config(),
horizon=4, batch_size=64)`) and rev 1 L651 (`CFG = dataclasses.replace(Config(), horizon=6,
K=1, M=1, F=1, batch_size=64, window=(1, 3))`).

`K`, `M`, `F` no longer exist — the rename to `stage_k/stage_m/stage_f` (Config L201-203) is
recorded only in the self-review note at L995 and was never propagated to the test fixture the
tasks depend on. An implementer inheriting rev 1's `CFG` gets a `TypeError` from
`dataclasses.replace`.

**Minimal correction:** define `CFG` explicitly in the Task 8 conftest block (alongside
`make_tiny_bundle`) using `stage_k=1, stage_m=1, stage_f=1`, and have Task 9 reference the same
fixture rather than redeclaring it.

### 10. `run_fan`'s signature is elided while its call site pins four positional arguments

**Locations:** L667 (`run_fan(...) -> tuple[list[ArmResult], dict]`) vs L700
(`run_fan(ctx, snap, base, CFG)`).

Rev 1 declared `run_fan(ctx, snap, base_hashes, cfg)`; rev 2 changed the third argument from a
hash list to a `BaseTrace` (the test uses `base.host_hashes`, `base.snapshots`) but replaced the
signature with `...`. `run_fan` also has to pass `read_test` down to `run_arm` (L665) and that
parameter appears nowhere.

**Minimal correction:** write
`run_fan(ctx, snap, base: BaseTrace, cfg, *, read_test: bool) -> tuple[list[ArmResult], dict]`
and state the returned `dict`'s keys (rev 1's test asserted `meta["twin_ok"]`).

### 11. `_episode_with_base` changed contract silently; `run_base` gained an argument

**Locations:** L677, L687 (`ctx, base = _episode_with_base()` then `base.snapshots[2]`,
`base.host_hashes[2:]`) vs rev 1 L653-656 (`_episode_with_base` returns `(ctx, hashes)` and
calls `run_base(ctx, CFG)`), vs L666 (`run_base(ctx, cfg, fan_epochs) -> BaseTrace`).

The step text at L671 only says "rev 1's twin-match / corrupted-hash / null-seed **tests**
updated to the new signatures" — the shared *helper* is not covered, and its inherited body
calls `run_base` with the wrong arity.

**Minimal correction:** restate `_episode_with_base(seed=31) -> tuple[EpisodeCtx, BaseTrace]`
and its `run_base(ctx, CFG, fan_epochs=[2, ...])` call in Task 9.

### 12. `take_snapshot` / `restore_snapshot` dropped from Produces while a retained test uses them

**Locations:** L590 (Task 8 Produces `@dataclass Snapshot` only), L625 ("rev 1's ...
snapshot-roundtrip ... tests"), L660 (Task 9 Consumes list omits them) vs rev 1 L572.

`run_base` must take snapshots at scheduled epochs (L664), and rev 1's retained roundtrip test
calls both functions. Separately, rev 2's arm-local materialization (L665) rebuilds state via
`load_state_dict` rather than `restore_snapshot`, so it is now ambiguous whether
`restore_snapshot` survives at all.

**Minimal correction:** add `take_snapshot(ctx) -> Snapshot` to Task 8's Produces and state
explicitly whether `restore_snapshot` is retained (and if not, that rev 1's roundtrip test is
rewritten against `take_snapshot` + fresh materialization).

### 13. `--extend` is described but absent from `run_collect`'s signature

**Locations:** L929 (`run_collect(cfg, store_root, devices, n_workers_per_device, limit=None)`)
vs L932 (`--extend N` bullet, directly beneath it) and L947, L987 (Phase D lever).

**Minimal correction:** `run_collect(cfg, store_root, devices, n_workers_per_device,
limit=None, extend=None)`.

### 14. Two deviations recorded in rev 1 vanished from a register that claims exhaustiveness

**Locations:** L15 ("Known, surfaced deviations live in the Deviations Register below — nothing
else may deviate"), L11 ("the register below records every deliberate deviation from the spec's
letter"), Deviations Register L28-36 (D1–D7) vs rev 1 L1019.

Rev 1's self-review recorded two deliberate deviations that rev 2 still *implements* but no
longer *registers*:

- **GERMINATED collapses into TRAINING's first tick** — still the behaviour at L591
  (`slot.stage = TRAINING` straight out of `germinate`), and `Stage` still lists GERMINATED
  (rev 1 L442, inherited).
- **Gate 2's probe is a 200-step `nn.Linear` rather than sklearn** (no new dependency) — L909
  now says only "probe→pathology, GroupShuffleSplit by episode", with no note that the probe and
  the group split are both hand-rolled.

**Minimal correction:** re-add both as D8 and D9 (or as explicit "not a deviation" lines).

### 15. Two rev-2 decisions look like unregistered deviations from spec letter

Flagging as candidates, since the register's own rule at L15 is absolute:

- **Universal signed-zero canonicalization** (L19, L548): the plan states the spec names
  zero-normalized hashing as the *null-seed contingency* mechanism, but rev 2 applies it to
  every hash — twin, cross-arm, host_init — and redefines every "bitwise" claim in the document
  as "bitwise modulo signed-zero canonicalization". That is a widening beyond the spec's letter
  with no D-entry.
- **Plan-chosen gate multipliers** (L220 comment "2x/0.5x are plan-chosen, surfaced"; L910
  `gate3_contrast_mult=2.0`, L913 `gate6_late_density_mult=0.5`): "surfaced" here means a code
  comment, not a register entry. D1 covers gate 1 only.

Lower-confidence candidates in the same class, listed for the owner to adjudicate: `torch.compile`
added to `FORBIDDEN_RELAXATIONS` (L16, L550 — a tightening, probably fine) and the τ-init
measurement mode flipped from eval to train (L457, L485 — rev 1 did eval; justified inline but
unregistered).

---

## Minor

16. **"The subset flag" (L985) is defined by no task.** `load_data` has a `subset=None`
    parameter (L296) but no CLI flag is created anywhere. Rev 1 carried the same orphan
    (rev1 L940). *Fix:* add `--subset N` to the preflight subparser in Task 14, or reword
    Phase B to name `load_data(subset=...)` and how it is reached.

17. **Section count disagrees between L7 and L40.** L7's Architecture blurb collapses
    "episode/fan executor" into one item (12 sections); L40's File Structure lists 13, with
    8=episode and 9=fan. This is not cosmetic — the certification rule at L23 and Phase A at
    L984 both cite "sections 4/5/6/8/9" *by number*. *Fix:* split "episode → fan" in L7.

18. **The FreezeManifest and divergence-report paths are never named.** L918 ("writes the
    FreezeManifest atomically"), L934 ("to a well-known path"), L930 ("Refuses without a
    FreezeManifest"). Rev 1 named `runs/kernel_demo/frozen.json` (rev1 L935). *Fix:* name both
    paths in Task 14 / Task 15.

19. **`load_for_training`'s stated guard is vacuous.** L715 says it "raises `SplitViolation` if
    any record it is about to yield has `split_role == "eval"`" — but it filters to train+tune
    first, so the guarded set can never contain one; the test at L733-737 confirms the happy
    path does not raise. The real guard is `_assert_trainable`. *Fix:* reword to "filters to
    train+tune, then calls `_assert_trainable` on the result, which raises `SplitViolation` on
    any `split_role == "eval"` or `kind not in ("fan",)`".

20. **Absence encoding is inconsistent between `EpisodeCtx` and `BaseTrace`.** L586/L648:
    `ctx.curves_test == []` when `read_test=False`. L664: `BaseTrace.curve_test` is `None`
    pre-freeze. `run_base` builds one from the other. *Fix:* pick one (`None` reads better
    against `ArmResult.curve_test: list | None` at L663).

21. **The reward definition disappeared from the plan's own text.** Rev 1's Global Constraints
    (rev1 L19) stated "Reward `R_a` = mean accuracy over final 3 epochs; end-state only; zero
    shaped terms". Rev 2 has `end_state_R(curve)` (L592) with no definition anywhere except
    rev 1's inherited test. *Fix:* restore the one-line constraint.

22. **Rev 1's selftest τ-init RMS check was dropped without a note.** Rev 1's `run_selftest`
    item 6 (rev1 L906) checked τ-init RMS on all four seeds against a real host batch; rev 2's
    eight-item list (L886-893) does not include it. Gate 5 measures RMS at *blend entry*, which
    is a different quantity. *Fix:* re-add, or note the deliberate removal.

23. **Task 3's stat-collection plumbing lost its names.** Rev 1 produced
    `collect_stage_stats(host)` (rev1 L278) and `host.attach_stat_hooks()` /
    `host.stage_stats["saturation"]` (rev1 L335); rev 2 compresses this to "stat hooks" (L392),
    leaving `act_saturation` (L353) with no stated source. *Fix:* restore the two names.

24. **Header pins `torchvision 0.28`; Task 1 does not.** L9 vs L77 (`uv add torchvision`,
    unpinned). Verified: `torch 2.13.0+cu130` at L9 is accurate. *Fix:* either pin in Task 1 or
    soften L9 to "torchvision (resolved in Task 1)".

25. **Rev 1's spec-coverage traceability paragraph was dropped.** Rev 1's self-review (rev1
    L1018) mapped every spec section to a task; rev 2's self-review (L993-995) does not. *Fix:*
    restore the mapping — it is the only artifact showing the plan covers the whole spec.

26. **Test snippets from Task 3 onward show no import blocks** — Task 9's monkeypatch test
    (L689, L698) specifically needs `import experiments.kernel_demo` (module-object attribute
    patching), and several use `pytest` / `dataclasses` / `torch` unshown. Acceptable as a doc
    convention, but call it out once so an implementer does not read the snippets as complete.

27. **`run_preflight` takes `store` while every other mode takes `store_root`** (L916 vs L929,
    L947, L965). Trivial, but the CLI wiring differs.

---

## What checked out clean

- **D1–D7 all land where they claim** (D1→L908/Config L221; D2→L20/L888/L905; D3→L353;
  D4→L965-966; D5→L38-43; D6→L965 + L950; D7→L387-391).
- **D7's arithmetic is self-consistent by recomputation:** 32/64/128 double-conv = 286,560 conv
  params (≈289k with BN+linear) ✓; 24/64/80 = 160,200 (≈162k) ✓; mild 20/72 = 140,652 (≈142k) ✓.
  All four pathologies fall inside the test's `80_000 < n < 250_000` band, `no_spatial_mix`
  (≈117k) included.
- **`TELEMETRY_DIM = 20`** is arithmetically correct for the field list at L353 (6 scalars +
  4 triples + 2 new = 20) and `EPOCH_FEATURE_IDX = 0` matches "epoch first".
- **Config ↔ FROZEN_FIELDS ↔ tests agree**: `gate4_dominance_max`, `policy_lr`, `warmup_frac`,
  `lam` all present and frozen; `n_collect` present and correctly *excluded* from FROZEN_FIELDS,
  matching L21, the L233 comment and `test_n_collect_not_frozen`.
- **File Structure's 17 test files exactly match** the files Tasks 1–17 create, including
  `conftest.py` (Task 8) and `helpers.py` (Task 12). `tests/__init__.py` already exists in the
  repo, so the `tests.unit.kernel_demo.*` import path works once Task 1's two `__init__.py`
  files land.
- **Line-count checkpoints agree**: L47 (Tasks 6/10/14 at ~500/~850/~1150) ↔ L538, L747, L920.
- **Repo claims verified**: `pyproject.toml` has `select = ["E","W","F","I","N","UP","B","C4",
  "SIM","RUF"]`, `ignore = ["E501"]`, `pythonpath = ["src"]`, `strict = true` — L16, L22 and
  L65 are all accurate. Task 1's code block is import-clean (rev 1's was not).
- **Operational-phase flags mostly resolve**: `--freeze`→Task 14, `--void-preregistration`→Task
  16, `--limit`→Task 15 signature, `--devices`/`--workers`→Task 15, `replay <fan_id>`→Task 1.
  Only `--extend` (#13) and "the subset flag" (#16) do not.
- **Rev 1's genuine defects are fixed**: the `run_base` arity contradiction, the
  `CommonFuture.order` `[E,S]`→`[E,S*B]` shape error, `d = lambda t:` (E731), semicolon-joined
  Config fields (E702), unused imports (F401), the cross-test-file `tiny_bundle` import, and
  `pytest.approx(abs=0)`'s live `rel=1e-6`.

---

## Confidence Assessment

**Confidence: High** for findings #1–#14 and #16–#27 — each is grounded in a line-number pair
within the two revisions, or in a `grep` over the document showing zero definition sites, or in
direct verification against `pyproject.toml` / recomputed parameter counts.

**Confidence: Medium** for #15 — whether the universal signed-zero canonicalization and the
plan-chosen gate multipliers *are* deviations from the spec's letter depends on the spec, which
I did not read (see Information Gaps). I am confident they are unregistered; I am not confident
they require registration.

## Risk Assessment

**Residual risk:** The largest is that the rev-1 dependency (#1) hides further drift I cannot
see — where rev 2 says "rev 1's suite plus X", I verified that X is coherent, but I could not
verify that the *unchanged* rev-1 content is still coherent against rev 2's renames beyond the
cases I caught (`K/M/F`, `fan_id="x"`, `diverged_R`, `TELEMETRY_DIM 18→20`). There are likely
one or two more of these latent in rev 1's inherited test bodies.

Second risk: `--eval`'s battery (L951-952) is described in one dense paragraph enumerating ~15
statistics. I checked the named symbols against Task 12's Produces but did not attempt to verify
that every statistic named there has a defined producer; several (`verdict`'s five booleans,
Wilson CI, derangement, restraint regret) are named only in prose.

## Information Gaps

- **I did not read the spec** (`docs/superpowers/specs/2026-08-09-kernel-demo-design.md` rev 6),
  by instruction. Every "matches the spec" judgment in the Deviations Register is therefore
  unverified by me; D2's and D6's fidelity to spec fan-step 7 and the spec's report list are
  outside what I checked.
- I did not verify the engineering claims (PyTorch semantics, statistical validity, the STE
  signed-zero argument, the arm-materialization fix) — out of scope by instruction.
- I did not check the ~70 SME findings against rev 2 to confirm each was actually folded in;
  I only checked the claims rev 2 makes about itself (L993-995).
- I did not verify `torchvision 0.28` resolves against `torch 2.13.0+cu130` (not yet installed).

## Caveats

- This review is **document integrity only**. A clean bill here means the plan is internally
  consistent and executable as written — not that the plan is engineeringly correct.
- Finding counts are not a quality verdict on the rewrite. Rev 2 fixed more than it broke; the
  defects listed are overwhelmingly *compression artifacts* of a rewrite that traded
  self-containment for delta-against-rev-1 brevity, which is the single systemic fix to make.

---

# Addendum: rev 3 verification (7e8371f, 1523 lines)

**Verdict: 27/27 closed. 7 fresh defects, none structural — 2 would fail at first test run.**

Self-containment confirmed: the only `rev 1`/`rev 2` mentions remaining (L11, L1418) are
historical prose, not execution dependencies. Every task states full interfaces; every test
block carries its import header; `CFG` fixtures are defined in-file with `stage_k/m/f`.

## Defect-by-defect

| # | Defect (rev 2) | rev 3 | Evidence |
|---|---|---|---|
| 1 | rev-1 deference | **closed** | L3 banner asserts self-containment; T6 inlines `Stage`/`cosine_ease`/`Slot.forward`; T10 inlines the full `FanRecord`/`Store`/`SplitViolation`; T11 `Policy`/`decide_live`; T12 `policy_loss` body + helpers |
| 2 | `fan_id` collision | **closed** | L1075 identity tuple + `policy_checkpoint_id` + `iteration`; uniqueness scoped to `{fan,refan}` within one `manifest_hash`; test L1156 |
| 3 | `_rec` hardcoded `fan_id="x"` | **closed** | replaced by `make_fan_record` (L1104); merge-ordering test L1139 now uses distinct identities |
| 4 | `host_init_hash` forward-ref | **closed** | standalone L552, rebound L796 |
| 5 | scalar `fan_density` | **closed** | L1277 `*, beta_which, beta_now`; both call sites L1361/L1373 |
| 6 | Phase-A commit unrecorded | **closed** | `certified.json` L55/L62/L1425; freeze checks `HEAD == certified.json["git_rev"]` L1448 |
| 7 | `kind` union | **closed** | `extension_event`, `void_event` L1074 |
| 8 | undefined symbols | **closed** | `build_seed` L610, `build_record` L470, `synthetic_batch`/`adversarial_batch_with_divergent_arm`/`synthetic_agreement` L1304, `_assert_trainable` L1078, `_rec_at` L1212 |
| 9 | `CFG` undefined / stale names | **closed** | L912, L1002 with `stage_k/m/f` |
| 10 | `run_fan(...)` elided | **closed** | L980 full signature; call sites L1017/L1029/L1061 all 9-arg — verified matching |
| 11 | `_episode_with_base` | **closed** | `_base()` L1008, returns `(ctx, BaseTrace)`, `run_base(ctx, CFG, fan_epochs=(2,))` matches L978 |
| 12 | `take_snapshot`/`restore_snapshot` | **closed** | `take_snapshot` L863; `restore_snapshot` explicitly removed with the replacement stated; roundtrip test rewritten L927 |
| 13 | `--extend` | **closed** | L1459 `extend=0` |
| 14 | dropped rev-1 deviations | **closed** | D12 (GERMINATED), D13 (gate-2 probe) L46-47 |
| 15 | unregistered deviations | **closed, exceeded** | D8/D9/D10/D11 L42-45, plus a new "Plan-authored constants" block L27-29 |
| 16 | "subset flag" | **closed** | `--subset` L302, Phase B L1519 |
| 17 | section count | **closed** | 13 in both L7 and L51 |
| 18 | artifact paths | **closed** | L55 names all seven |
| 19 | vacuous split guard | **closed** | L1078 yield-path; test L1166 |
| 20 | `curves_test` convention | **closed** | L858 `None` iff `read_test=False`; test L951 |
| 21 | reward definition | **closed** | L16 |
| 22 | selftest τ-init check | **closed** | L1418 |
| 23 | saturation source | **closed** | L550 `attach_stat_hooks` → `stage_stats`; L470 `build_record` |
| 24 | torchvision pin | **closed** | L9 + L76 both `0.28.0+cu130` |
| 25 | coverage traceability | **closed** | L1512-1514, honestly framed as record-of-check |
| 26 | test imports | **closed** | every block |
| 27 | `store_root` naming | **closed** | L1448 |

## Fresh defects (rev 3)

**F1 (blocking — TypeError at first run).** `_rec` L1101-1120 passes `policy_checkpoint_id=None`
positionally-by-keyword *and* forwards `**kw`. `test_comparator_policy_runs_do_not_collide`
(L1158-1159) calls `_rec(..., policy_checkpoint_id="trained")` → `make_fan_record() got multiple
values for keyword argument 'policy_checkpoint_id'`. *Fix:* give `_rec` explicit
`policy_checkpoint_id=None, iteration=None` parameters and drop them from the body, or build a
kwargs dict and `.update(kw)` before the call.

**F2 (blocking — production path).** `Store.merge()` sorts by
`(episode_seed, fan_epoch, kind, refan_k)` (L1077), but `fan_epoch` and `refan_k` are now
`int | None` (L1074) and event records legitimately carry `None`. Any store holding an
`extension_event` alongside fans of the same `episode_seed` raises
`TypeError: '<' not supported between 'NoneType' and 'int'`. *Fix:* coalesce in the sort key —
`(episode_seed, -1 if fan_epoch is None else fan_epoch, kind, -1 if refan_k is None else refan_k)`.

**F3.** `_SEMANTIC_SURFACE` is appended to *inside the factories*: `build_host` L551 and
`build_seed` L610 both "append … to `_SEMANTIC_SURFACE`". Called per-episode, the list grows
unboundedly and `config_hash()` becomes call-count-dependent — which breaks
`test_config_hash_stable_within_process` (L144) after the first `build_host`, and, worse, makes
the freeze/replay identity non-deterministic. *Fix:* register at module-definition time
(module-level `_SEMANTIC_SURFACE.extend([Host, NormSeed, AttnSeed, ConvLightSeed, ConvHeavySeed])`
right after the class definitions), never inside a factory.

**F4.** `make_fan_record` is imported by the test (L1097) and is the stated `fan_id` deriver
(L1102) but does not appear in Task 10's Produces list. *Fix:* add
`make_fan_record(**fields) -> FanRecord` (computes `fan_id` from the identity tuple) to L1074-1079.

**F5.** "asserts" vs the tests' expected exception type: `decode_record` "asserts
`schema_version == SCHEMA_VERSION`" (L1076) but the test expects `ValueError` (L1135); `merge()`
"asserts uniqueness" (L1075) but the test expects `ValueError` (L1152). A bare `assert` raises
`AssertionError` and is stripped under `-O`. *Fix:* reword both to "raises `ValueError`".

**F6.** `data_split_id` appears in the FreezeManifest (L1448) and is defined nowhere —
`schedule_id` got its definition in this revision, `data_split_id` did not. *Fix:* define it
(e.g. sha256 over `split_indices(cfg.run_seed)` bytes), matching `schedule_id`'s treatment.

**F7 (minor).** `test_policy.py` imports `_rec` from `tests.unit.kernel_demo.test_telemetry`
(L1209) — a cross-test-file import of a private helper, which is exactly the pattern rev 2
eliminated for `tiny_bundle` by moving it to `conftest.py`. *Fix:* move `_rec` to `conftest.py`
alongside `make_tiny_bundle` and import both from there.

## Observations (not defects)

- `TwinDivergence.first_bad_epoch` — the corruption test (L1027-1030) corrupts absolute index 3
  of `base.host_hashes` and expects `first_bad_epoch == 3`, implying an absolute-epoch
  convention while the comparison runs over `base.host_hashes[snap.epoch:]`. The convention is
  correct as written but never stated; one clause in `TwinDivergence`'s definition would pin it.
- Selftest step 10 measures deterministic-mode cost "flags on vs. off" (L1424) — toggling
  `use_deterministic_algorithms` off is itself a `FORBIDDEN_RELAXATIONS` entry. Scoped to a
  throwaway copy inside selftest it is defensible; saying so explicitly would prevent a future
  reader reading it as a licence.
- `run_preflight` does not state how many refans it runs, yet gate 3 (L1442) compares against a
  "refan floor". `run_refan` exists (L1438) but its invocation count is unstated.
- Runtime budget (L67) recomputes correctly: 300 × 340 × 2.78 s = 78.8 GPU-h; 48k × 2.78 s =
  37.1 GPU-h; ÷12 workers = 6.6 h / 3.1 h. Phase C's `--devices cuda:0,cuda:1 --workers 6` is
  6 *per device* = 12 total — consistent with the "overnight is real at 12" claim.
- D7 arithmetic re-verified unchanged (162k / 142k / 289k).

## Caveats

Unchanged from the rev-2 review: I did not read the spec, so D1–D13's fidelity to spec letter is
unverified by me; I verified only that each registered deviation is implemented where it claims
and that the register is internally exhaustive against what rev 3 actually does.
