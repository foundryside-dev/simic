# 05 — Quality Assessment

**Target:** `experiments/kernel_demo.py` (4,066 lines) + `experiments/kernel_demo_plots.py` (433 lines)
**Version anchor:** `kernel_demo.py` at `2b48431`, byte-unchanged through `aa86388` (verified three times: `git diff` empty, mtime 06:51). Sidecar re-analysed against `aa86388`.
**Date:** 2026-08-10
**Source:** synthesis of `02-subsystem-catalog.md` (9 entries, ~60 concerns with line citations and per-concern coverage tags) and the adjudications in `00-coordination.md`. This document does not re-read the source except for named spot-checks.

---

## 0. Verdict

This artifact is better verified than most research code and considerably better verified than most production code. It hashes its own source, refuses on four independent identity mismatches at every phase boundary, runs an eight-gate admission battery in which six gates have executable *failing* fixtures, keeps failures in an append-only history, and enforces its statistical-unit discipline at four independent sites with the reasoning written down at each. The suite is green and skip-free on hardware that can actually exercise it: **129 passed, zero skips, CUDA available.**

The findings below are therefore not a list of things done badly. They are a list of places where a codebase that mostly *proves* its claims instead *asserts* one — and the assertion is usually correct. That distinction governs every severity rating here. Where the evidence says "unverified assumption," it says so; it does not say "bug."

Three things are structurally true and worth stating before the detail:

1. **The strongest and the weakest parts are adjacent.** The counterfactual fan path re-verifies its own matching on every fan, three ways. The eval lift path — which produces two of the five pre-registered verdict booleans — performs none of those checks and is structurally excluded from the one post-hoc mechanism that could substitute. Same file, same author, same week.
2. **The untested paths are where cost is absent, not where it is concentrated.** Three of the four sharpest coverage gaps are the cheapest code in the subsystem — one was measured at **18 microseconds**, another at **0.5 ms**. "Expensive to test" is not available as an explanation here.
3. **The recurring defect shape is a load-bearing constraint expressed as prose inside a system built to hash its own semantics.** That is one root cause with at least six instances and one fix, not six oversights.

**Scope note carried from the brief:** the single-*file* layout is a locked spec decision (rev 6.1) and monolith-shaped findings are excluded as by-design. Two structural items remain legitimately in scope and are ranked below: the **3.4× overrun** against the spec's own ≲1200-line target, and **`run_eval` as a single ~400-line function with seven responsibilities** — a locked file decision does not cover an oversized function.

---

## 1. What holds

Given proportionate space because it is proportionate to the evidence. Every item below was verified — by reading the mechanism, by grep on a negative, or by execution — not inferred from a name or a comment.

### 1.1 Falsifiability is demonstrated, not argued

**Gates 1–6 each have an executable failing fixture.** `test_preflight_gates.py:140` (gate 1), `:154` (gate 2), `:161` (gate 3), `:212` (gate 4), `:221` (gate 5), `:228` (gate 6) — each gate has both a passing and a *failing* case, so "the battery can fail" is an executed property rather than a structural argument. Three of the four `freeze_manifest` refusals are likewise pinned (`:253`, `:262`, `:270`), and `test_gate7_is_report_only` (`:236`) pins gate 7's always-pass as *deliberate diagnostic behaviour* rather than leaving a reader to guess whether it was an oversight. Pinning an intentional weakness as intentional is a discipline most codebases never reach.

**The refusal chain is closed end to end:** `--certify` refuses on CPU / any failure / any skip (:2290) → `freeze_manifest` refuses on a not-ok gate, dirty worktree, missing certificate, or HEAD ≠ certified rev (:2860–2871) → `run_collect` re-checks (:3153) → `run_train` (:3343) and `run_eval` (:3463) refuse on manifest mismatch → `main` exits 1 (:4043). Every gate threshold lives in `FROZEN_FIELDS` (:211–216) or a `semantic_const`, so post-hoc threshold tuning invalidates `frozen_block_hash` and every downstream artifact. Eval is one-shot; re-running demands `--void-preregistration`, which writes a permanent append-only `void_event` (:3437–3460). This is genuine anti-p-hacking machinery, not theatre.

### 1.2 The rev 6.1 amendment is defended against regression, not merely implemented

`test_learning.py:91` asserts the two-labels-per-episode `ValueError` and then bounds `0.4 < p < 0.6` on a cluster-preserving fixture. **The band is what makes this a regression defence rather than a smoke test:** it was chosen because the episode-level null has exactly two label assignments (identity → 2 matched, swap → 0 matched, hence p ≈ 0.5), while a point-level shuffle lands near 1/6 under the lexicographic tie-break. The assertion was constructed to *discriminate between the two schemes*, so it would fail on a regression to point-level shuffling — the exact defect the pre-data amendment was written to close.

`sign_flip_pvalue` at `test_learning.py:110` is comparably strong: it tests both directions, with a comment instructing "do not reseed to green."

### 1.3 Blinding is by construction

`TelemetryRecord` (:358–369) contains no seed name, arm name, pathology id, episode seed, or provenance field. **The identity is not present to be ignored** — blinding is by field *absence*, which is the distinction the project's own design authority cares about and the correct side of it. `record_to_vector` (:397) maps exactly those 20 metric fields; `epoch` (index 0) is the only non-metric feature and carries no arm or seed information.

### 1.4 No leakage, and no calibration on test

Traced end to end rather than assumed:

- Splits are a deterministic partition of one permutation (:263–264); test is the official CIFAR-10 test split (`train=False`, :284), never drawn from the 50,000. Independently asserted by selftest `partition_check` (:2224–2231).
- **The `Normalizer` is fit on preflight-namespace fans only** (:2957–2961), where episodes run `read_test=False` (:2941), then frozen into `frozen.json` (:2878) and loaded **read-only** thereafter by `run_train` (:3347) and `run_eval` (:3493). The normalizer never sees test material and is frozen before any training or evaluation.
- Training labels are `r_val` only (:1846, :1851); `r_test` never reaches a training example.
- **Checkpoint selection is on the tune split** (:1955, :1964–1972), and eval-role records cannot physically reach the selector — `_assert_trainable` raises `SplitViolation` first (:1938, :1666).

### 1.5 The grouped-statistics wall holds end to end

`train_tune_split` (:1540) is deterministic on **episode identity**, stamped once per episode before any fan exists (:2339), and inherited by every fan of that episode (:2367). It is never recomputed downstream. The learning path enforces the wall **by index bound, not by convention**: minibatches draw `torch.randint(len(train_ex), ...)` (:1957), so tune examples are outside the index space entirely. There is no internal holdout, no re-split, no re-weighting.

And the discipline is not confined to that one wall. Statistical-unit choice is correct at four independent sites, each with its reasoning committed: `_first_fans` takes the lowest-`fan_epoch` fan per episode explicitly against pseudo-replication (:2522–2523); gate 2's probe holdout is by episode (:2592); the money-chart permutation moves every grid point of an episode together (:2016–2030); the falsifier CI and the agreement MDE use the episode count, not the grid-point count (:3693–3698, :3814–3816).

### 1.6 The counterfactual fan executor is genuinely matched

The scientific core is the strongest-engineered part of the codebase:

- **Rebuild-not-restore.** No `restore_snapshot` exists (:1145–1146). Every arm is constructed fresh and loaded from snapshot *values* (:1296–1309), so cross-arm state leakage is prevented by construction. Snapshot tensors are cloned at capture (:1158) and the optimizer state is deep-copied again at load (:1306).
- **Common random numbers enforced by data structure.** One `CommonFuture` is drawn per episode (:1020) and passed *by reference* to every arm (:1291 → :1316), indexed by absolute epoch (:1060, :1069). There is no sampler to desynchronise — which is why "dataloader position" is absent from `Snapshot` without being a gap.
- **The no-op is a really-executed measured arm** (:1381, :1390), not an assumed zero — and it doubles as the harness twin, running first so a broken harness fails the fan before compute is spent.
- **Three graded integrity instruments, deliberately differentiated:** twin hash equality → `TwinDivergence` (:1384–1388); cross-arm post-TRAINING bitwise equality (:1396–1400); null-seed exact reproduction of the base *including mirroring a base divergence at the same epoch*, with an unconditional `RuntimeError` and an explicit "no weaker fallback, curves are never a comparand" comment (:1404–1414).
- **Arm identity cannot shift the shared stream:** it enters only via `derive(episode_seed, "arm", name)` inside `rng_scope` (:1174, :730), which saves and restores the global state in a `finally`.

### 1.7 Illegal states made unrepresentable, at the cheapest possible price

`train_policy(..., frozen_density=...)` is a **keyword-only parameter with no default** (:1934). Recomputing the entropy temperatures from the training records is therefore impossible *by signature* — not by convention, not by a comment, not by a test. `run_train` additionally re-derives the betas and asserts them against the manifest (:3353–3354) and prints the collection-set recomputation explicitly labelled "UNUSED for betas" (:3352). This is the cheapest, highest-leverage correctness construct in the file.

### 1.8 Determinism by avoiding the global stream, not by seeding it

`torch.manual_seed` is never called anywhere in the file. Every draw either takes an explicit `generator=` or runs inside `rng_scope` (:123–133), which is exception-safe via `try/finally`. Verified by execution, not asserted: a state-comparison probe over **all 80 combinations** of pathology × seed × stage, running full forward + backward + `opt.step()`, found the global RNG state byte-identical in every case, with a positive control confirming the probe detects draws. `build_host`, `build_seed` and `tau_init` all leave the global stream unchanged.

The consequence, adopted from the coordinator's adjudication: the snapshot's `cpu_rng` capture/restore is **belt-and-braces** — nothing in the model path currently threatens the invariant it defends.

### 1.9 Loud-on-absence discipline at the decode boundary

The project's silent-zero scar is taken seriously and the audit came back **clean**: `_as_float` (:1802) rejects `bool` before the numeric check (:1805 — correct, `bool` subclasses `int`) and raises on `None` (:1806); `_telemetry_vector_from_dict` uses direct subscript `d[key]` (:1814), **not `.get()`**, so a missing key raises `KeyError`; 3-vector arity is validated (:1818); non-finite logits raise rather than reading as restraint (:1774–1777, :3397–3400); `measure_fan_density` raises on empty input (:1857, pinned at `test_learning.py:120`); `when_contrast` returns `None` for an undefined conditional mean rather than `0.0` (:3305–3307); gate 5 treats *no measurement* as an explicit failure (:2702–2703). The resume path raises rather than defaulting a malformed `decisions` payload to "never germinated, lift 0", with the scar named in the comment (:3524–3531).

### 1.10 One assembly is genuinely integration-tested

`run_collect` is executed for real with spawned workers (`test_collect.py:75–142`), asserting idempotency, tune-role assignment, partial-episode resume without duplicate `fan_id`s, both manifest refusals, and the halt-and-report path. The uncovered rows cluster specifically on the **eval** assembly and the **CLI boundary** — not uniformly across the file.

### 1.11 The author found a defect class eight reviewers missed

Between analysis waves the author committed `853e9ef` ("the plotting sidecar refuses to invent data") and `aa86388` ("an empty tune curve is a skip, not a crash"), closing all eight sidecar concerns explorer 8 had raised. The sharpest construct in that fix is one nobody in this analysis proposed: **`_finite_points` / `_gapped` (plots :65–68, :83–85) keep the original index with each value and re-emit `nan` at the dropped positions**, so a null mid-curve leaves a visible gap instead of silently relabelling the epoch axis. That is a silent-default class one level deeper than "don't use `.get(0.0)`": without it, a dropped point does not become a zero — it becomes a *plausible* value at the wrong epoch, which no reader could detect from the figure.

The praise is for the index preservation specifically. `_finite_points`' *finiteness policy* — silently dropping non-finite values where `require_number` refuses them — is a separate matter and is tracked as a defect at Q11.

---

## 2. Cheap fixes to high-blast-radius gaps

These are listed first because several have measured costs and all are additive. Nothing here requires a design decision.

| Fix | Closes | Measured / estimated cost | Item |
|---|---|---|---|
| Store `state_hash(noop_ctx.host)` in the `policy_run` record's `host_init_hash` instead of `""` (:3606), and compare against the treated episode's | Gives the lift path its only integrity anchor, and gives the eval resume path something to check across a process boundary | One hash, one comparison — **S** | Q2 |
| Test `gate8_pressure(cfg, None, "cpu", worker_count=6)` returns `ok=True, "skipped (GPU-only)"` | The exact mechanism behind the CPU freeze hole | **18 microseconds**, no fixture needed (the device check at :2761–2762 precedes every use, so `data=None` is safe) | Q3 |
| Test `freeze_manifest`'s missing-certificate refusal | The one freeze refusal of four with no test | **0.5 ms**; shape-identical to the three that already exist (`:253`, `:262`, `:270`) — it is the fourth sibling of a family where three were written | Q4 |
| At shard open, seek to the last newline and `truncate()` — or write the newline as a **prefix** rather than a suffix (:1598) | The silent-loss step in the torn-tail resume sequence | One line — **S** | Q6 |
| Move the `--void-preregistration` append (:3437–3461) *after* the admission block (:3463–3492) | A failed rerun leaving a permanent, unretractable void with no eval behind it | Statement reorder — **S** | Q9 |
| Assert `device` is CUDA in `run_preflight` / `freeze_manifest`, or record it in the manifest and refuse on mismatch downstream | The CPU freeze hole itself | **S** | Q3 |
| Add a `test_vectorizers_agree` comparing `record_to_vector(rec)` to `_telemetry_vector_from_dict(asdict(rec))` | The twin contract currently held by a comment (:1812) | **S** — and it is the precondition for Q5's consolidation | Q5 |

---

## 3. Findings, ranked by blast radius

Ranked by *validity impact first, then reachability, then cost to close*. The validity-vs-availability axis the coordination log adopted for the store finding is applied uniformly here: a finding that can produce a **wrong published number** outranks one that can only produce a **bricked run**.

Coverage tags are the catalog's own, from the symbol-level re-audit across all 21 test modules (final tally: 1 COVERED, 2 PARTIAL, 1 NOT COVERED–closed, 14 UNCOVERED, 1 N/A, 0 CONTRADICTED).

---

### Q1 — Re-freezing silently decouples calibration from records

**Category:** Architecture (identity binding) · **Effort:** M · **Coverage:** UNCOVERED · **Class:** validity

**Instances**
- `manifest_hash` (:2909) hashes the *whole* manifest including `gate_results` detail, `det_mode_cost` and `concurrency_factor` — all measured, run-varying values. Re-running `preflight --freeze` on the **identical commit** therefore yields a **different** `manifest_hash`.
- `freeze_manifest` overwrites `frozen.json` unconditionally (:2914), with no guard for a store that already holds collected records.
- `run_train` reads the normalizer and betas from manifest B (:3347–3354) while training on records collected under manifest A, checking only `frozen_block_hash` and `config_hash` (:3343) — never the records' own `manifest_hash`.
- `load_for_training` (:1673) filters on `split_role` and `kind` only.
- `run_report`'s D6 mixed-manifest refusal does not catch it: its comparison set is built from **eval-namespace** records plus `eval_results.json` (:3835–3837), so train-namespace records never enter it, and the live `frozen.json` loaded one line later (:3841) is never added to the set.
- `Store.merge`'s duplicate backstop is keyed `(manifest_hash, fan_id)` (:1636), so it **permits** the same fan under two generations — double-counted by `tr_fan_counts` (:3486) and by `load_for_training`.

**Blast radius.** Highest in the analysis. Reachability is high — both freeze preconditions (clean worktree, HEAD == certified rev) are satisfied by simply re-running preflight on the same commit, which is a natural operator action, not an exotic one. The consequence is a policy trained against a normalizer and entropy temperatures from a *different manifest generation* than the records it trains on, with every hash check green and no message printed. `run_report` then prints `fan_density` and `temperatures_in_force` from whichever manifest is currently on disk, beside numbers a different generation produced.

**Coverage.** `test_report.py:102` *does* pin the D6 mixed-manifest refusal — but its fixture builds `seed_namespace="eval"` records exclusively. The suite covers precisely the path that works and never the train-namespace hole. This makes it an **incomplete guard**, which is more actionable than an absent one.

**Recommended fix.** Split the identity: `manifest_hash` is a **run** identity (it hashes measured values) and is currently doing a **policy** identity's job. Introduce a content hash over the pre-registered policy block only — the normalizer, the frozen density, the derived temperatures, `frozen_block_hash`, `config_hash`, `schedule_id`, `data_split_id`, `n_train` — stable across a re-freeze on the same commit, and refuse in `run_train` when the records' policy hash differs from the manifest's.

Independently verified as safe: `manifest_hash` is compared in exactly three places (`run_replay` :3953–3954, `run_report`'s D6 refusal :3834–3839, sidecar :150–152), **all of which want a run identity and all of which survive the split unchanged**. The anti-p-hacking property never rested on `manifest_hash` — `run_train` (:3343) and `run_eval` (:3463) consult only `frozen_block_hash` and `config_hash`. So the split does not weaken pre-registration; it creates the stable key `run_train` currently lacks.

**Do at the same time:** `plan_authored_constants` (:2896–2906) mixes genuine policy constants with `fsync_every`, which is in neither `FROZEN_FIELDS` nor `config_hash` (see Q7). The split is the moment to sort that.

---

### Q2 — The lift path assumes the property the fan path re-verifies

**Category:** Architecture (verification) · **Effort:** S (fix) / M (with the resume check) · **Coverage:** UNCOVERED · **Class:** validity, bounded to 2 of 5 verdict booleans

**Instances**
- `run_eval`'s comparator loop (:3507–3588) calls no `take_snapshot`, no `run_base`, no `run_arm`, no `run_fan`, and has no twin. The no-op is an independently constructed episode (`make_episode`, :3512) trained through the full horizon in a plain loop; each comparator is *another* independently constructed episode (:3542). `lift = r_test - r_noop_test` (:3587) differences two separately executed episodes.
- Every fan record stores `host_init_hash = state_hash(ctx.host)` (:2342, :2374). **`policy_run` records deliberately write `host_init_hash=""`** (:3606) — the one field that would let an auditor confirm both episodes started from the same host is not stored at all. `common_future_hash` is recorded for the treated episode (:3605) but never computed for `noop_ctx`.
- `run_replay` refuses anything that is not a fan: `if rec.kind != "fan" or rec.fan_epoch is None: raise` (:3957–3958). `policy_run` records carry `kind="policy_run"` and `fan_epoch=None` (:3592, :3597), so they fail the replay guard **twice over**.
- **On resume the assumption crosses a process boundary.** `r_noop_test` is recomputed live (:3512) while completed comparators are read back from the store (:3521–3540) and then differenced — with no comparison of the record's stored `env` (:3607) against the live one, though `run_replay` refuses on exactly those keys via `REPLAY_REFUSAL_KEYS` (:3943).
- **A diverged baseline is indistinguishable from a poor one.** `r_noop_test` falls back to `cfg.diverged_r` (:3519) but the no-op's *status* is never recorded — only the bare float (:3588), while every fan arm carries an explicit `status` (:1211). Baseline-diverges-treated-doesn't reads as a large seed-attributable gain.

**Blast radius — stated precisely, because the loose version is wrong.** The fan path is verified twice: `TwinDivergence` at runtime and `--replay` post hoc. The lift path is verified **neither** way. But the supporting evidence for the assumption is strong: `make_episode` (:1014) is a pure function of `(cfg, data, device, episode_seed, read_test)` with `CommonFuture` from `derive(es,"future",0)`, so both episodes share data *and* future by construction; `train_one_epoch` consumes no global RNG; and no model-path operation draws from the global stream (verified over 80 combinations). Common random numbers genuinely **are** shared. The correct statement is therefore:

> **The property the fan path re-verifies on every fan, the lift path assumes.** It is an unverified assumption, not a known error.

**Two scope corrections that must not be lost:**
1. This affects **2 of the 5 pre-registered verdict booleans** — `lift_positive` and `beats_schedule_only` (:3320–3321). The eval *grid* runs through `run_collection_episode` → `run_base`/`run_fan` (:3624) with full twin, cross-arm and null-seed verification, so `agreement_beats_null`, `money_chart` and `falsifier_collapses` (:3322–3324) rest on properly matched branches. What is weakly guaranteed is the **lift magnitude**, not the diagnostic claim.
2. The replay exclusion applies to `policy_run` comparator records **only**. Eval grid fans remain `kind="fan"` and *are* replayable (:3959–3961). Do not restate this as "eval is unreplayable."

**Coverage.** `run_eval` is called exactly twice in the suite (`test_eval_stats.py:86`, `:101`) and **both calls raise before the comparator loop at :3507** — one at the one-shot guard (:3433), one at the incomplete-collection refusal (:3492). The comparator loop, `r_noop_test`, germination, the lift arithmetic, the frozen grid, the refans and all six statistical computations never execute under test. `test_resume_identity_matches_stored_fan_id` pins only `fan_identity` equality on a fixture that sets `host_init_hash="i"` — a fixture value, so it neither pins nor contradicts the production `""`.

**Recommended fix (cheap, additive, three parts).**
1. Hash `noop_ctx.host` at construction and store it in `host_init_hash` instead of `""`; compare it against the treated episode's before computing lift. One hash, one comparison.
2. Compare the resumed record's stored `env` against the live one using `REPLAY_REFUSAL_KEYS` — the mechanism already exists at :3943.
3. Record the no-op's `status` alongside its float, so a diverged baseline is separable from a poor one. The fan path already does exactly this separation for the grid via the diverged-excluded money-chart companion (:3718–3732); the lift table has no equivalent.

---

### Q3 — A CPU preflight can freeze a manifest whose gates were computed on CPU

**Category:** Security/Integrity of the certification chain · **Effort:** S · **Coverage:** UNCOVERED · **Class:** validity

**Instances**
- `--device` merely *defaults* to `cuda:0` (:4011). Neither `run_preflight` (:2919) nor `freeze_manifest` (:2848) asserts it. Exhaustive grep for `cuda` confirms no CUDA assertion anywhere on the preflight/freeze path.
- `gate8_pressure` returns `GateResult(True, "skipped (GPU-only)", …)` on a non-CUDA device (:2761–2762), and `dataclass_gates_ok` (:2843) accepts it.
- Reproduction is two commands: `selftest --certify` on GPU, then `preflight --freeze --device cpu` at the same clean HEAD. The certificate check passes (it binds `git_rev`, not device), gate 8 is vacuous, and gates 2/3/5/6 are computed from CPU numerics.
- Downstream, `run_replay` reads the vacuous result as `ok=True` → `worker_count = 1` (:3938–3941).

**Blast radius.** Validity-affecting and inherited by everything downstream of the freeze: the frozen normalizer, the frozen density, both entropy temperatures and four gate outcomes all derive from CPU-computed numerics, while the manifest asserts a certified GPU run. `concurrency_factor: None` in the manifest makes it detectable *after the fact* — but nothing refuses.

**A second symptom, recovered late and worth its own line: the reporting layer consumes a gate-8 output that nothing tests gate 8 for producing.** `concurrency_factor` is surfaced by `run_report` (:3902) and appears in the entire suite exactly once — as a hardcoded `1.5` inside a fabricated manifest (`test_report.py:85`). A test asserts the report *renders* the number; nothing asserts it is ever *measured*. The same holds weakly for `det_mode_cost`. Explorer 7's phrase for this, adopted: **coverage-shaped but not coverage.** It is the clearest illustration of why gate 8's absence propagates past the gate itself.

**Coverage.** Gate 8 is **the only gate absent from `test_preflight_gates.py`'s import block** (`:6–25`, which lists gates 1–7 and `dataclass_gates_ok`). `grep -rn "gate8" tests/` returns no match; `grep -rn "devices\|cuda" tests/` returns exactly one hit, a TF32 assertion at `test_determinism.py:17`. **Gate 8 is not skipped; it was never written.** And that cannot be explained by environment gating: a GPU is present, the suite runs against it, and nothing is skip-marked.

**Recommended fix.** Assert the device is CUDA in `freeze_manifest`, or record it in the manifest and refuse downstream on mismatch. Add the 18-microsecond skip-path test.

**Honest boundary, kept so the claim survives review:** gate 8's *body* genuinely is expensive — the sibling template hardcodes a full `load_data` (:2792) under a 300-second deadline (:2803), so a faithful test with `worker_count=6` spawns five subprocesses each materialising CIFAR-10 on the GPU, plausibly longer than the suite's whole 110 s. "Expensive" is available for the body. **It is not available for the skip path, the certificate refusal, or `--certify`.** The expense is a property of how gate 8 is *written* — a sibling reusing `_tiny_bundle_for_selftest` would be testable — not of the environment.

---

### Q4 — "A pass that isn't": four ways to succeed without being checked, and a verdict nobody conjoins

**Category:** Architecture (certification semantics) · **Effort:** M · **Coverage:** PARTIAL (gate 7's always-pass *is* pinned as deliberate) · **Class:** validity of the headline claim

**Not an instance, but the context for the cluster:** gate 7's always-pass (:2755, `remedy="report-only"`) is **deliberate and pinned as such** by `test_gate7_is_report_only` (:236). It is named here only because it means "8 gates passed" already denotes seven evaluated — it is not itself a finding, and §1.1 counts it as evidence of discipline.

**Instances**
- **Gate 8 self-skips to `ok=True` on CPU** (:2761–2762) — see Q3. Combined with gate 7, "8 gates passed" can mean six were evaluated.
- **Selftest step 1 asserts nothing.** `forbidden_relaxations` prints the tuple and records `{"status": "pass"}` unconditionally (:2079–2082). No code path verifies that any listed relaxation is absent, yet it counts toward `--certify`'s zero-failure requirement — and `test_selftest.py:13` accepts it as a genuine pass.
- **The falsifier gets easier with less data.** `falsifier_collapses` (:3324) is an *accept-the-null* comparison against `wilson_interval(round(majority_null * n_units), n_units, alpha)` (:3698). Smaller `n_units` widens the interval and raises `null_ci_hi`, so weaker evidence makes the criterion **more** likely satisfied. `wilson_interval` returns `(0.0, 1.0)` at `n == 0` (:3268–3269) — vacuously true, unreachable in practice only because `run_eval` refuses on incomplete collection (:3490–3492).
- **`verdict()` returns five booleans and never ANDs them** (:3313–3325). Every consumer just prints or passes through (:3820, :3904, :3920, :4054). The conjunction — the actual claim — is left to the reader.
- **`eval` exits 0 regardless of the verdict** (:4054–4055), while `selftest` (:4039), `preflight` (:4043) and `collect` (:4047) all gate their exit codes. A five-false verdict is indistinguishable from a five-true one to CI or to a shell `&&` chain. (Why this was never caught belongs to Q8.)
- **The `--certify` path itself has no test.** `test_selftest.py` never passes `certify=True`, so the refusal at :2290–2291 and the atomic certificate write (:2297–2300) — the mechanism binding code identity to results — are unexercised in either layer. `freeze_manifest`'s missing-certificate refusal (:2866) is the one freeze refusal of four with no test.

**Blast radius.** This cluster attacks the credibility of the certification *headline* rather than any single number. A green run currently means "six gates were evaluated and passed, one reported by design, one may not have run at all, one selftest step asserted nothing, and five verdict booleans were printed without being combined." Every individual decision here is defensible in isolation — gate 7's is explicitly tested as intentional — but the aggregate presentation is not.

**Recommended fix (one change, several call sites).** Make `ran / passed / skipped / report-only` distinguishable in `gate_results` rather than collapsing all four into `ok: bool`; have `dataclass_gates_ok` refuse a *skipped* gate at `--certify` (the selftest already refuses skips at :2290 — extend the same rule to the gate battery); give `verdict()` an explicit conjunction and make `eval`'s exit code carry it; and give selftest step 1 a real assertion (which is the same fix as Q7's `FORBIDDEN_RELAXATIONS` hashing). Add the 0.5 ms missing-certificate test.

**Note on the falsifier:** the n-dependence is a design property of an accept-the-null criterion, not a coding error. The actionable part is to record `n_units` and the realised interval width in `eval_results.json` so a reader can see how much of the "collapse" is evidence and how much is width.

---

### Q5 — One rule, two implementations — and the canonical, tested copy is the dead one

**Category:** Code Quality / Correctness · **Effort:** M (must land at a re-freeze boundary) · **Coverage:** UNCOVERED (both copies) · **Class:** validity, latent

**Instances**
- **The deployment rule.** `decide_live` (:1754) has **zero production callers** — its only caller repo-wide is `tests/unit/kernel_demo/test_policy.py:64`. `run_eval` re-implements the rule inline at :3562–3573 using `_query_dicts` (:3385) and `_pi_argmax` (:3416). The author knows and asks for manual lockstep (:3568–3571, "`decide_live` is the tested owner"). **They already differ structurally**: `decide_live` owns the window guard internally (:1763) while the deployed copy depends on the caller's `lo <= e <= hi` at :3551. This is realised divergence, not hypothetical drift.
- **The telemetry vectorizer.** `record_to_vector` (:397) and `_telemetry_vector_from_dict` (:1811) must emit the same 20 values in the same order; the contract is a comment at :1812 and nothing else. `record_to_vector` appears in exactly one test (`test_telemetry.py:32`, pinning only `v.shape` and `v[EPOCH_FEATURE_IDX]`); `_telemetry_vector_from_dict` is imported by **no test at all**.
- **A source comment asserts test coverage that does not exist.** Line 3418 describes the tie-break as "the same rule `decide_live` implements and tests pin"; :3571 calls `decide_live` "the tested owner." Neither `_pi_argmax` nor `_test_argmax` appears anywhere in the suite, and the sole `decide_live` test asserts only window-boundary inclusivity — it never exercises `p > 0.5` and never checks which seed is chosen. **Both copies of the duplicated rule are untested, and a comment claims otherwise.** A reviewer would rely on that comment.
- `query_teacher_forced` (:1786) is fully dead; the teacher-forced agreement it was written to serve is computed by `_query_dicts(..., mask=False)` (:3562, :3567).

**Blast radius — and an explicit correction to a claim this analysis carried at higher severity for most of its run.**

*Spot-checked for this document:* `_policy_tokens` (:1747), the only consumer of `record_to_vector` outside its definition, has exactly two callers — `decide_live` (:1766) and `query_teacher_forced` (:1789), **both dead**. Every live consumer goes through the dict twin: the normalizer fit (:2959), policy training (:1843), eval queries (:3386), and gate 2 (:2588). **Fit and inference therefore cannot desynchronise from each other today** — the vectorizer twin is a *latent* hazard, not a live silent-failure class.

**The correction, recorded rather than quietly applied.** `02-subsystem-catalog.md` calls the vectorizer twin "the clearest silent-failure class I found" and states that a desync "corrupts gate 2's own inputs" so that "training and inference features would diverge with every gate still green." That overstates the *present* reachability. Two explorers converged on the finding independently from different directions, and the coordinator carried it at that severity in the log — **three independent parties over-rated it, and one grep on the caller set settles it.** Independent convergence raised confidence that the coupling is real, which it is; it did not test whether anything currently traverses it, and nobody checked. Worth recording as a method note: *convergence is evidence of existence, not of reachability.* The mechanism claim in the catalog stands; only the severity moves.

But it becomes live precisely when this item is fixed. Consolidating the deployment rule onto `decide_live` — the correct fix — is exactly what puts `record_to_vector` back on the live decision path, at which point a field-order drift between the twins would silently permute the feature space between what the normalizer was fit on and what a decision reads, with no failing test.

**Recommended fix (one shape, sequenced).** Delete the inline twin and call `decide_live` from `run_eval`; delete `query_teacher_forced`; correct the two comments that claim coverage. **Preconditions, both load-bearing:**
1. Land the `test_vectorizers_agree` equality test (Section 2) **before** the consolidation, because the consolidation is what activates the twin contract.
2. Both dead functions are `@semantic` (:1753, :1785), so deleting either moves `config_hash` and makes `run_train` refuse against an existing manifest (:3343). **The consolidation must land at a re-freeze boundary, in one commit with the twin test.** Dead code on the semantic surface is load-bearing dead code — costlier to remove than to keep, and the incentive runs toward keeping it. That incentive is itself worth naming as a design consequence of hashing the semantic surface.

---

### Q6 — A record written after a torn tail is silently lost, then the store bricks

**Category:** Code Quality (durability) · **Effort:** S · **Coverage:** PARTIAL (steps A and D covered; B and C not) · **Class:** availability, reached by a silent-loss step

**Instance.** `Store.append` opens mode `"a"` (:1595) and writes the newline as a **suffix** (:1598), so a partial line carries no terminator and the next append fuses onto it. Reproduced end to end against the real `Store`:

- **(A)** Tear a shard mid-record → `merge()` returns the 2 prior records with a loud warning. Correct, and covered by `test_store.py:98`.
- **(B)** Resume and append a third record → the file still has 3 lines, the new record having fused into the partial one.
- **(C)** `merge()` returns **2 records — the record just written is gone**, behind the *identical* "skipping torn final line" message (:1627), indistinguishable from (A).
- **(D)** One further append makes the fused line interior → `merge()` raises → the store is unreadable by every consumer.

The apparent mitigation is the trigger: the lost `fan_id` is absent from the `merge()`-derived skip set (:3157), so collection re-runs it — and that re-collection append is exactly step (D).

**Blast radius — availability, not validity, and the distinction is load-bearing.** The blast radius stops short of a wrong published number: a pre-existing torn tail crashes `run_preflight` at its very first `store.merge()` (:2922–2923) *before any gate runs*, so freeze is fail-closed against it; and `run_eval` refuses on an episode-count shortfall (:3491–3492), so a quietly dropped episode cannot silently shrink the eval population. The cost is a bricked collection run, its compute, and operator confusion. What earns it this rank rather than a lower one is step (C): a **silent** loss behind a benign-looking warning, in a store whose stated premise is complete append-only history.

**Related, same subsystem, lower severity:** interior corruption escapes as an untyped `json.JSONDecodeError` (:1629) where every other failure in this file has a named class; the skipped-record warning is a stdout `print`, not a record; there is no lockfile, PID guard or `O_EXCL`, though the failure mode of concurrent writers is **loud** (duplicate-but-valid records tripping `merge()`'s duplication assert at :1638), not corrupting — appends were measured line-atomic on Linux/ext4, a platform-scoped guarantee that should be written down since **NFS `O_APPEND` does not provide it**.

**Recommended fix.** One line at shard open: seek to the last newline and `truncate()`. Or write the newline as a prefix. Add a test for the append-after-tear sequence, which `test_store.py:98` currently stops one step short of.

---

### Q7 — Load-bearing constraints live only in comments

**Category:** Architecture (enforcement) · **Effort:** M · **Coverage:** UNCOVERED · **Class:** regression surface, not a live defect

This is one root cause with six instances and **one recommendation, not six**. It is notable precisely because it sits inside a codebase that hashes its own source and runs an eight-gate battery — enforcement-by-comment is the outlier here, not the norm. (Gate 7's always-pass is a related shape but is *not* one of these: it is deliberate and pinned as such — see Q4.)

| Instance | Evidence | What a future edit could do unchecked |
|---|---|---|
| `FORBIDDEN_RELAXATIONS` is documentation-only and never hashed | :900–913; the comment at :901–903 explicitly designates it "printed by `--selftest`" and deliberately not a `semantic_const` | Nine entries name every change that voids the Class-1 claim — including **"adding dropout"**, the single change most likely to break the RNG-free property. Adding `nn.Dropout` to a seed would flip the global stream from decorative to load-bearing, make the sequential-arm requirement suddenly real, and **pass every gate in the file.** |
| The seed parameter-budget floor is a comment with no `numel` check | :690 ("budget floor (2,657 / 4,737 params)"), :707 ("valid band [31, 77]"); coordinator-confirmed absent file-wide by grep | The menu spans 129 / 4,337 / 8,897 / 60,137 params — a **466× spread**. An edit to `mid`/`cb` passes silently. Bears directly on whether gate 4 (dominance) measures seed *design* or seed *capacity*. |
| `enable_class1()` is enforced at process entry points only | :918 states it "MUST be the first statement of every process"; honoured at :4005, :3077, :2088, :2258 — but no import-time call and no runtime assertion | Every *importing* consumer runs semantic functions with the Class-1 knobs unset — that is the plotting sidecar and every test module except `test_determinism.py`. |
| The `record_to_vector` / `_telemetry_vector_from_dict` field-order contract | Comment at :1812 and nothing else | See Q5 — latent today, activated by Q5's fix. |
| `_git_rev` / `_worktree_clean` are certification primitives that are neither hashed nor classified | :2829, :2835; `test_derive.py:99` skips names starting with `_` and neither carries `@semantic` | Adding `--untracked-files=no` to the argv at :2838 would materially weaken the freeze gate while moving no hash and failing no test. The underscore boundary is also inconsistent — `_sanitize_json` (:1547) *is* `@semantic` — so "private means non-semantic" is not a rule a reader can rely on. |
| `fsync_every` is echoed into `plan_authored_constants` "for owner sign-off" but bound by nothing | :2906; absent from `FROZEN_FIELDS` (:188–223), and `Config` is off the semantic surface by explicit opt-out (:91) | The durability cadence can change between freeze and collect without invalidating the manifest. The echo is a record to *sign*, not a *binding*. |

**Two adjacent gaps of the same shape.** The classification test (`test_derive.py:100`) filters to `inspect.isclass or inspect.isfunction`, so a new behaviour-changing **module constant** whose author forgets `semantic_const` is covered by no gate at all. And `FROZEN_FIELDS` is a hand-maintained list parallel to `Config` with **no completeness test** — nothing asserts that every `Config` field is either frozen or on a documented lever list, so a field added in a future edit lands outside the frozen block silently. Both are the config-field analogue of the class/function gate that already exists.

**Recommended fix (one change).** Promote the constraint register to the hashed surface: make `FORBIDDEN_RELAXATIONS` a `semantic_const`, give selftest step 1 real assertions for the mechanically checkable entries (deterministic algorithms on, TF32 off, `cudnn.benchmark` off, AMP absent, no `Dropout` module in any seed or host — a module-type walk, cheap), add a `numel` band assertion to the seed path, add an import-time or first-call assertion for `enable_class1()`, classify `_git_rev`/`_worktree_clean` explicitly, and add the `FROZEN_FIELDS` completeness test. **The single highest-value element is the seed capacity gate**, because it is the one whose absence bears on a *reported* gate outcome rather than on a latent regression.

**Also in this family, lower value:** the "no unscoped draw" invariant is enforced by one text needle — a grep for the literal `nn.init.` over sections 4/5/11 (:2159–2163). It would not catch `torch.randn(...)` without `generator=`, an in-place `.normal_()`, or an `nn.init.` call in any other section. The invariant holds today (verified at :1715–1717), so this is regression surface, but it is the weakest link in an otherwise mechanically-enforced spine.

---

### Q8 — The CLI boundary is untested: one gap with four symptoms

**Category:** Test Coverage · **Effort:** M · **Coverage:** UNCOVERED · **Class:** mixed

**Instance.** `kernel_demo.main` (:4004) is **never invoked by any test.** Phase functions are tested directly by keyword argument; the gap is specifically the CLI boundary. That single fact is the root cause of four findings previously counted separately:

1. **`--resume-eval` is a dead flag.** `run_eval`'s `resume` parameter (:3426) is never read in the body — verified by grep, only the signature and the call site at :4053 occur. Resume is unconditional via the `existing` id set. This reproduces verbatim the scar the author names 24 lines later at :4013: "a flag that parses everywhere but is silently ignored (collect, replay) is the scar."
2. **`--void-preregistration` records the void before validating that the eval can run** (append at :3437–3461, admission checks at :3463–3492). A void-and-rerun that then fails admission leaves a permanent, unretractable `void_event` in an append-only store with no eval behind it.
3. **`eval` exits 0 regardless of verdict** (:4054–4055) — see Q4.
4. **`--extend` is not idempotent and cannot be undone.** Each invocation appends another `extension_event` (:3162–3186), so `--extend 5` twice raises the collection target by 10 and permanently raises `required` in `run_eval` (:3490). There *is* a real guard — it refuses once eval-namespace records exist, protecting the pre-registration (:3160–3161) — but nothing protects an accidental repeat before eval, and there is no confirmation prompt or dry-run.

**Blast radius.** Mostly operational rather than validity-affecting, with one exception: symptom 3 makes a false verdict invisible to CI. Symptom 2 writes an irreversible record into an append-only store.

**Recommended fix.** A small `main`-level test module invoking each subcommand with `--help`-style and dry-run paths plus one end-to-end `eval` on fixtures, asserting **exit codes**. Fix the two ordering/dead-flag defects in the same commit. Note that fixing `--resume-eval` and `eval`'s exit code touches `@semantic` source and therefore moves `config_hash` — batch with Q5 at a re-freeze boundary.

**Fairness note, carried deliberately:** 129 passing tests is genuinely good work. "UNCOVERED" marks a boundary the suite does not reach, not sloppiness. The suite tests phase functions thoroughly and the CLI not at all — a coherent choice, just one with consequences.

---

### Q9 — Identity is bound in some places and not others

**Category:** Architecture (identity) · **Effort:** M · **Coverage:** UNCOVERED · **Class:** validity, low-to-moderate reachability

The two highest-value instances of this cluster are promoted to Q1 (`manifest_hash` as a run identity doing a policy identity's job) and Q2 (`host_init_hash=""`). What remains:

- **`certified.json` binds a git revision, not a semantic hash.** The payload (:2297) carries `git_rev` but **no `config_hash`**, so code identity at freeze rests on `_worktree_clean()` (:2835) plus HEAD equality (:2870) rather than the semantic-surface hash the module otherwise computes. Any source change invisible to `git status` breaks the binding silently. Fix: add `config_hash` to the certificate payload and compare it in `freeze_manifest`. **Effort S.**
- **`policy_checkpoint_id` is recorded but never refused on.** Grep of all 16 occurrences: it is recorded in `FanRecord` (:1443), fed into `fan_identity` (:1468, :1529), used in the merge sort key (:1652), written into checkpoint filenames and JSON (:3365–3371) — but **never compared, asserted, or refused on**, and it is `None` at every preflight/collect call site. This matters because it was the assumed mitigation for the next item.
- **`d_model` (:176) and `n_layers` (:177) are outside `FROZEN_FIELDS`.** *Adjudicated as by-design*: spec rev 6.1 lines 151–154 enumerate the frozen block exhaustively and policy architecture is not in the list; lines 236–237 describe it approximately ("d_model≈64", "~100k params"), deliberately unpinned. **This is not a spec violation.** The residual finding is that an architecture edit moves neither hash, and the mitigation a reader would assume — `ckpt_id = state_hash(policy)` at :3364 — does not refuse on anything. The comment at :3362 ("the env pins make any numerics drift refusable") asserts coverage the env pins do not provide for an architecture change. **Architecture drift between freeze and eval is undetectable by any hash.** Fix: refuse on `policy_checkpoint_id` where it is available, and correct the comment.
- **Dataset *content* is not bound to run identity.** `data_split_id` (:268) hashes index bytes only; the manifest carries `data_split_id` + `n_train` (:2883–2886) but no pixel checksum, and all four refusal gates check only those two (:3088, :3465, :3955, :3964). `load_data` fetches with `download=True` into a hardcoded `runs/data` (:282–284), where torchvision's integrity check applies to the downloaded archive, not to an already-extracted tree. A modified-but-same-size extraction passes every gate and replays "clean." **In a pipeline whose thesis is that a result traces to the code and configuration that produced it, the data is the one input not covered.** Fix: hash the extracted tensors once at load and freeze the digest. **Effort S.**
- **CPU thread count is recorded but not controlled and not refused on.** `torch.set_num_threads` is never called; :980–982 records `torch_num_threads`, states plainly that CPU GEMM reductions are thread-count dependent and that policy training runs on CPU (:3360) — then places it outside `REPLAY_REFUSAL_KEYS`. Bounded: `--replay` accepts only `kind='fan'` records and fans run on `device`, so the bitwise-replay claim for fans stands. What is exposed is the **policy-training leg**, reproducible only on a host with the same thread count, with nothing to tell you when it is not.

---

### Q10 — `run_eval` is a single ~400-line function with seven responsibilities

**Category:** Code Quality (structure) · **Effort:** M · **Coverage:** UNCOVERED (this is Q2's coverage finding restated structurally) · **Class:** maintainability, with a coverage consequence

The single-*file* monolith is a locked spec decision and is correctly out of scope. A single 400-line *function* is not covered by that decision. `run_eval` (:3425) carries resume bookkeeping, the comparator loop, the frozen grid, refans, six statistical computations, results assembly and the atomic write.

**Why it earns a rank rather than a style note:** it is the direct cause of Q2's coverage gap. Both existing tests raise before the comparator loop, and the reason they can is that there is no smaller unit to call. A clean seam already exists with no shared mutable state beyond `grid`, `per_comp` and `merged` — **statistics (:3651–3818) split from execution (:3507–3646)**. Extracting the statistics block makes the six estimators individually callable on fixtures, which is precisely the "tested head, tested tail, untested join" seam identified in the coverage audit.

**On the line budget.** The spec targets ≲1200 lines (spec line 560); actual is 4,066 — a **3.4× overrun**. The single largest contributor is section 14 at roughly 560 lines. The overrun is a real deviation from a stated target and is recorded as such, but it is the *least* actionable finding in this document: the certification apparatus is what makes the file expensive, and that apparatus is the artifact's main virtue. The honest framing is that the ≲1200 estimate was wrong about what self-certification costs, not that the file is bloated. **Recommendation: amend the target, extract `run_eval`'s statistics block, and leave the rest.**

---

### Q11 — Plotting sidecar: uncertified analytic constants and two inconsistent absence policies

**Category:** Code Quality · **Effort:** S · **Coverage:** COVERED for the four named fabrication modes (16 tests, executed green); UNCOVERED for selection semantics · **Class:** presentation validity

**Staleness caveat, stated up front — and narrower than the catalog's own wording suggests.** This file moved twice mid-analysis (150 → 425 → 433 lines). The catalog entry describes itself as read from an *uncommitted working tree over `853e9ef`*, which contradicts the catalog header's claim that it was re-done against `aa86388`; the explorer's unmerged revision resolves the contradiction — **the working-tree state read at 07:21 is exactly what was committed, unchanged, as `aa86388`**. So the entry is properly anchored to a commit, not to a moving tree. The residual risk is only that a peer session commits *further* changes after `aa86388`. Re-read at current HEAD before acting; some findings below may already be closed.

- **The docstring's population-refusal invariant is enforced on two of three axes.** `_load_fans` refuses a mixed *namespace* (plots :148) and a mixed *manifest generation* (:151), but never refuses a mixed `split_role` — it filters when `--split-role` is given and pools silently when it is not (:135–138). A `--namespace train` store legitimately holds both `train` and `tune` roles, and `tune` is the **held-out selection split**, so pooling them into one RMS boxplot is exactly the fabricated aggregate the module's own comment (:117–119) says it is guarding against. Highest-value item in this cluster.
- **`plot_alpha_beta` refuses on a legitimate absence, unlike its sibling.** It raises on "no arm carried a non-empty `alpha_beta_log`" (:229) — but an all-diverged population has no non-empty logs, a state the kernel names explicitly (`_all_arms_diverged`, :2515) and treats as legitimate. `plot_tune_curve` handles its equivalent case by skipping (:297). **This is the next instance of the bug `aa86388` just fixed, one function over.**
- **`SPIKE_CRASH_MARGIN = 0.05` (plots :30) classifies an arm into a figure legend while being unfrozen and unhashed.** Composing it with the certified `end_state_R` (:102) arguably makes it *harder* to notice, because the rule now looks kernel-derived. A "(spike-then-crash)" label remains an uncertified analytic claim that can change with no hash moving and no replay refusing.
- **One of two verdict thresholds on the money-chart trio is imported; the other is hardcoded.** Panel 2 correctly draws `majority + AGREEMENT_MARGIN` from the imported `semantic_const` (:265); panel 1 hardcodes `axhline(3, …)` (:259), duplicating the `>= 3` rule that `verdict()` owns at :3323. A change to the pre-registered rule would move the verdict and leave the chart's reference line stale — and the chart is what a reader trusts. The author demonstrably knows the right pattern, having applied it one panel over.
- **`plot_manifest.json` records which records were selected but not what drew them** (:400–427): no `config_hash()`, no sidecar git rev, no `SPIKE_CRASH_MARGIN`. It cannot answer "which plotting code, with which thresholds, drew this PNG."
- **A refusal partway through `main` leaves unattributed PNGs beside a stale manifest.** Figures are written incrementally (:414–424) and the manifest last (:427), with no temp-staging and no atomic `os.replace` — which `kernel_demo.py` uses for every artifact it writes (:2914, :3059, :3823). The provenance artifact is the one thing that should be crash-consistent with the images and is the least protected.
- **`_finite_points` silently drops non-finite values while `require_number` refuses them** (:78 vs :48–51) — two validators in one module with opposite policies on the same input class.

**Recommended fix.** Refuse a mixed `split_role` population; make `plot_alpha_beta` skip on legitimate absence; move `SPIKE_CRASH_MARGIN` into the frozen block or record it in `plot_manifest.json`; import the money-chart threshold; stage output to a temp directory and `os.replace` the manifest last.

---

## 4. Noted, minor, not ranked

Real but small. Listed so they are not lost; none justifies its own work item.

- **`end_state_R` is misnamed.** It is a 3-epoch trailing mean (:1189–1192), not an end state, and the window width is a hardcoded literal invisible to `config_hash`. A reader reasoning about single-epoch end-state semantics will be wrong. Rename, or make the window a `Config` field.
- **The cross-arm value-exactness check is a bare `assert`** (:1400), stripped under `python -O` — unlike the null-seed check (:1411), which correctly raises. It also silently no-ops when `snap.epoch + stage_k - 1 >= horizon`. Unreachable under the shipped `Config`, so latent.
- **`end_state_R`'s ≥3-entry precondition is an unvalidated cross-field `Config` coupling** (`cfg.window[1] + 3 <= cfg.horizon`). The gate-battery config at :2767 sits exactly on the boundary.
- **The module docstring cites "LOCKED, rev 6"** (:8) while `freeze_manifest` stamps rev 6.1 (:2877). The docstring is the first thing a reader of a single-file demo encounters.
- **`divergence_*.json` is written by three call sites and read by none** (:2945, :3115, :3639). A `TwinDivergence` halts collection and leaves a localisation artifact, but nothing in the certified chain records that it happened.
- **Post-halt records are indistinguishable from pre-halt records.** `halt` is polled only between episodes (:3096), so other workers finish their current episode — potentially hours — and append normally. Nothing marks a record as produced after the determinism contract broke.
- **A hung worker hangs `collect` indefinitely.** `p.join()` (:3247) has no timeout, and the parent never reads the heartbeats it asks workers to emit (:3119).
- **`decode_record` is a tolerant reader with no current beneficiary** (:1574): `data.get(f.name)` fills absent fields with `None` at the *same* `schema_version`. At `SCHEMA_VERSION = 1` there are zero additive-evolution cases, so the tolerance is currently pure hazard.
- **`policy_run` arms are a partial `ArmResult` shape** (:3608, 4 of 12 fields) held off from every consumer by four independent `kind` filters and nothing else. Also, `name = chosen or "noop"` labels a never-germinating comparator's arm `"noop"`, colliding with the name of a genuine no-op arm.
- **An empty tune split silently disables checkpoint selection.** `train_policy` raises loudly on an empty `train_ex` (:1947–1948) but takes no position on `tune_ex`: the run degrades from early-stopped to last-iterate with only an empty `"curve"` as signal.
- **`_telemetry_vector_from_dict` validates type and arity but never finiteness**, and `json.loads` accepts `NaN`/`Infinity` by default, so a non-finite could reach the frozen normalizer fit (:2959) before failing loud at the logit guards.
- **`train` and `report` do not re-check `n_train`** where `collect`, `eval` and `replay` all do. Covered transitively; the guard is absent where the pattern is otherwise uniform.
- **In-process arm parallelism would break matching silently.** `torch.set_rng_state` (:1307) is process-global, so correctness depends on `run_fan` running arms strictly sequentially — undocumented, and absent from `FORBIDDEN_RELAXATIONS`.
- **Gate quality notes:** gate 3's floor is a heuristic ratio with a hardcoded ×2.0 (:2655); gate 2's holdout is roughly six episodes; gate 6 requires only that late density reach *half* early density (:2725); the money-chart statistic is integer-bounded 0–4 so `matched >= 3` admits two passing values.
- **`tau_init` calibrates on a validation batch** (:1178) and arm reward is in VAL units. Small, deterministic, and disclosed — but it is a genuine val-touching initialization path.
- **`feat_channels = 64` is hardcoded** (:575) rather than derived from `w2` (:563) — one invariant maintained by two independent literals.
- **`derive` stringifies labels** (:105), so `derive(s, 1)` and `derive(s, "1")` collide. No current call-site pair collides; the property is undocumented.

---

## 5. Coverage picture

Final tally from the symbol-level re-audit across all 21 test modules: **1 COVERED, 2 PARTIAL, 1 NOT COVERED (closed), 14 UNCOVERED, 1 N/A, 0 CONTRADICTED.** Suite state at audit: **129 passed, zero skips, CUDA available** (`pytest tests/unit/kernel_demo/ -q -rs`, 110 s).

The publishable framing, arrived at after two rejected drafts:

> **The units are well tested on both sides; one assembly is integration-tested and the other is not.** `run_collect` is executed for real with spawned workers. The uncovered rows cluster specifically on the **eval assembly** and the **CLI boundary**.

The seam is precise: `verdict` is tested against a hand-built results dict with hardcoded p-values (`test_eval_stats.py:61–71`), while the functions that compute those p-values are tested in isolation in `test_learning.py`. So telemetry → permutation test → p-value → verdict boolean has a **tested head, a tested tail, and an untested join** — and `run_eval`'s body never executing is what leaves that join unexercised in both layers.

**Two method warnings that belong with the tally, because they bound how much to trust it:**
- **Per-file coverage auditing under-counts.** One subsystem's estimators are tested in another subsystem's test file — all six statistical estimators live in `test_learning.py`, not `test_eval_stats.py` where a per-file audit looks. Two of the eight explorers nearly published a false UNCOVERED on that basis. A false UNCOVERED damages this report as much as a false COVERED.
- **Grep alone is not sufficient evidence for a COVERED row.** The `n_train` row survived on a near-miss: the suite's `n_train` hits are an unrelated `CommonFuture.draw` keyword plus two substring matches on "training." Grep would have scored it COVERED.

---

## 6. Limitations

Stated plainly; several bear directly on how much weight the severity ratings can carry.

1. **No end-to-end run backs any severity rating.** No `--selftest`, `--preflight`, `--collect`, `--train` or `--eval` invocation was performed by this analysis. No gate outcome, hash value, refusal path or p-value was observed against real data. The **only** runtime verification is the pytest suite (129 passed, zero skips) plus targeted micro-executions by individual explorers: the 80-combination RNG probe, the `add_param_group` momentum check, the four-step torn-tail reproduction against the real `Store`, the concurrent-append atomicity measurement, the 18 µs gate-8 skip call, the 0.5 ms freeze refusal, and the 16-test sidecar suite run.
2. **The catalog passed its validation gate on form; its dependency matrix had two contradictions, now resolved.** `temp/validation-catalog.md` (08:03) reports **CHECK 1 contract compliance: PASS, 9/9** — all 63 section blocks present, in contract order, no extras, no truncation, no naming drift, and every Confidence section citing specific files and line ranges. **CHECK 2** found 8 dependency asymmetries, 2 of them critical (one direction contradiction, one intra-entry contradiction); overall status NEEDS_REVISION (CRITICAL), **blocking diagram generation only**, and the two critical items have since been fixed by the owning explorers. So the evidence base is validated on form with a known and closed defect in the dependency matrix.

   **Two scope facts that bound what that validation means.** The validator explicitly did **not** open `experiments/kernel_demo.py`, so every asymmetry it found is "the catalog contradicts itself," never "the code says otherwise" — no factual claim in the catalog was checked against source by the gate. And evidence *quality* was out of its brief: it verified that citations are present, not that they are right.

3. **The merged catalog I worked from is stale against two explorer entries — but this document does not inherit the gaps.** The last re-merge ran at 07:34; explorers 7 and 8 revised their temp files at 07:49 and 07:52, and those revisions were never merged. The unmerged content is substantive: the `test_learning.py:91` discriminating-band paragraph, the measured 18 µs / 0.5 ms timings, per-Concern coverage tags on the CLI entry, and two Concerns absent from the catalog entirely. **All of it reached me by another route** — the coordination log and the task brief carried the band rationale, both timings, the coverage tally and the COVERED counter-finding, and §1.2, §2, §3-Q3 and §1.10 of this document reflect them. One item did **not**: the `concurrency_factor` "coverage-shaped but not coverage" finding, which I recovered from the validation report and added to Q3 while making this correction. Any *further* unmerged content in those two temp files is a residual gap I have not enumerated.
4. **One catalog entry rests on a Medium self-grade, and several top-ranked findings come from it.** Explorer 8 graded its "Run Orchestration & CLI" entry **Medium** because `run_preflight`'s body (:2919–3033) was never read; the Certification Battery inbound edge is inferred from two call sites rather than from reading the caller. Q1 (re-freeze) and Q2 (lift path) originate in that entry — though both were independently re-verified against source by the coordinator, which is why they are ranked where they are.
5. **One entry had no second-model review.** Explorer 4 (Counterfactual Fan Executor) reported its advisor tool rate-limited during its run. Its findings feed Section 1.6 (positives) and two minor items.
6. **The Plotting Sidecar entry was analysed against a moving target.** The file was rewritten upstream mid-analysis (150 → 425 lines at `853e9ef`, then `aa86388`); the entry was re-done against `aa86388`, but a peer session may still be active on that file. Treat Q11 as provisional.
7. **No version anchor existed at analysis start.** `00-coordination.md` opened without a `git rev-parse HEAD`, and no explorer was told which revision it was reading. That is how a coordinator-asserted error in the discovery document ("no tests exist for `experiments/`") propagated to one explorer as fact before two others independently corrected it. `kernel_demo.py` has since been verified byte-stable three times, so 4,066 of 4,216 lines and 8 of 9 entries rest on a fixed artifact — but the process gap is real and is why limitation 6 exists.
8. **The coverage tally rests on a re-audit that followed a self-reported error.** Explorer 8 found two genuine under-counts in its own rows on re-check — a 2-in-16 error rate on a table it had already grepped repo-wide. The corrected table is more trustworthy than the first, but the base rate is a reason to spot-check any individual row before acting on it.
9. **Security surface mapping and dependency analysis were deliberately omitted** — the target is an offline single-process research harness with no network I/O, no auth, and two third-party dependencies. That omission is a scoping decision, not a clean bill of health on either axis.
10. **Nothing here has been reconciled against the spec line by line.** One finding (`d_model`/`n_layers` unfrozen) was downgraded from "strongest finding" to "by design" purely by reading spec rev 6.1 lines 151–154. Others in this document may deserve the same treatment; the spec was consulted for that one item, not systematically.

---

## Confidence Assessment

**Overall Confidence:** Moderate-to-High. High on the *findings* (each traces to a line citation an explorer read directly, and the highest-ranked ones were independently re-verified by the coordinator against source); Moderate on the *severity ordering*, because no end-to-end run exists to calibrate reachability against real operator behaviour.

| Finding | Confidence | Basis |
|---|---|---|
| Q1 re-freeze decoupling | **High** | Mechanism read directly at :2909, :2914, :3343–3354, :1636; the `manifest_hash` occurrence audit (three consumers, all run-identity) was independently performed and adopted. Reachability claim is inference from the freeze preconditions, not observation. |
| Q2 lift path unverified | **High** on mechanism, **High** on scope | Coordinator read :3500–3594 and :3957–3958 directly and adjudicated a conflict between two explorers. Scope correction to 2-of-5 booleans came from a re-read of the grid path at :3624. The "assumption, not error" framing rests on three independent negative verifications (80-combination RNG probe, no global-stream dependence, `CommonFuture` per-episode purity). |
| Q3 CPU freeze hole | **High** | Negative established by exhaustive grep for `cuda` on the preflight/freeze path, and by `grep -rn "gate8" tests/` returning no match. The 18 µs figure was measured. |
| Q4 "a pass that isn't" | **High** on each instance, **Moderate** on the aggregate framing | Each instance is a line read directly. The framing that the aggregate misrepresents the run is my synthesis, not an explorer's finding. |
| Q5 dual implementation | **High**, and sharpened by a spot-check for this document | `grep -rn "decide_live\|query_teacher_forced"` returned one test caller and zero production callers. I additionally verified `_policy_tokens`' caller set (:1766, :1789 — both dead) and all four live consumers of the dict twin, which **downgrades the twin from a live silent-failure class to a latent one activated by the fix.** This corrects the catalog's "clearest silent-failure class I found." |
| Q6 torn tail | **High** | The four-step sequence was **executed** against the real `Store` in a temp directory, twice by different explorers, correcting an earlier mechanism claim in the process. |
| Q7 constraints in comments | **High** on each instance | Five of six established by grep on a negative; the seed-budget absence was coordinator-confirmed file-wide. |
| Q8 CLI untested | **High** | `main` never invoked is a demonstrated property of a green, zero-skip suite, not an inference. |
| Q9 identity gaps | **High** on `certified.json` and `policy_checkpoint_id` (16 occurrences grepped); **High** on the `d_model` by-design adjudication (spec read directly) | |
| Q10 `run_eval` size / line budget | **High** | Both are counts. |
| Q11 sidecar | **Moderate** | Read in full and its 16 tests executed green, but against a file a peer session may have moved since. |
| Positives §1 | **High** throughout | Every item is a mechanism read at a cited line, a grep on a negative, or an execution. §1.8 and §1.6 in particular rest on executed probes with positive controls. |

**Where I would be least surprised to be wrong:** the *ranking* of Q1 above Q2. Q1 has higher reachability; Q2 touches the headline number. An operator who never re-freezes sees Q1 never fire.

## Risk Assessment

**Implementation Risk (of acting on this document):** Medium. **Reversibility:** Moderate — most fixes are additive, but several move `config_hash`.

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| **A fix moves `config_hash` and invalidates an existing manifest mid-flight.** Q5, Q8 and parts of Q7 edit `@semantic` source. `run_train` and `run_eval` then refuse against any existing `frozen.json`. | High | High — it is a certainty for those items, not a risk | Batch all semantic-surface edits into **one commit landing at a deliberate re-freeze boundary**, before any collection has begun. Do Q2, Q3's test, Q6 and Q9's `certified.json` change first: they are additive or test-only. |
| **Fixing Q5 activates the latent vectorizer twin hazard.** Consolidating on `decide_live` puts `record_to_vector` back on the live decision path. | High | Certain if sequenced wrongly | Land `test_vectorizers_agree` **before** the consolidation. This is a hard ordering constraint, not a preference. |
| **Splitting `manifest_hash` (Q1) is a schema change to a record already written.** | Medium | Moderate | Verified safe on the read side: all three current consumers want a run identity and survive unchanged. Add the new field rather than repurposing the old one; `SCHEMA_VERSION` is additive-only post-collection by the module's own stated policy (:1569–1572). |
| **Acting on Q11 collides with an active peer session.** The sidecar moved twice during this analysis. | Medium | Moderate | Re-read the file at current HEAD before editing. Route rather than patch. |
| **Over-correcting on severity — treating Q2 as a known error rather than an unverified assumption** and rewriting sound machinery. | Medium | Moderate | The fix is one hash and one comparison. Anything larger is over-scoped; the supporting determinism evidence is strong. |
| **Under-reacting to Q7 because nothing is currently broken.** Every instance is latent by construction. | Medium | Moderate | The seed capacity gate is the one instance with a *present* consequence (it bears on gate 4's interpretation). Do that one even if the rest waits. |
| **A finding in this document is a spec conformance question I did not check.** | Low-Medium | Moderate | See Limitation 9. Check the spec before treating any item as a defect rather than a design choice — one finding already flipped that way. |

## Information Gaps

- **No independent check of any catalog claim against source.** The validation gate covered form and self-consistency only and never opened `kernel_demo.py` (Limitation 2). Would change: confidence that the ~60 concerns say what the code says. The one spot-check performed for this document (Q5) found a severity over-rating, which is weak evidence that more would surface.
- **Whatever else sits unmerged in `temp/catalog-7` and `temp/catalog-8`.** I recovered the items the validation report enumerated (Limitation 3) but did not diff the temp files myself. Would change: possibly one or more findings or coverage tags absent from this synthesis.
- **`run_preflight`'s body (:2919–3033) was never read by anyone.** Would change: the confidence grade on Q1 and Q2's provenance, and would settle whether the preflight call sequence introduces a further identity binding not visible from its call sites.
- **No observed gate outcome, p-value or hash on real data.** Would change: whether gate 2's ~six-episode holdout, gate 3's ×2.0 heuristic and gate 6's ×0.5 bar are *actually* discriminating or merely passable — currently a structural concern with no measurement behind it.
- **Reachability of Q1 in practice.** I do not know how often the author re-runs `preflight --freeze` on the same commit. If the answer is "never, by habit," Q1 drops below Q2.
- **The current state of the plotting sidecar.** A peer session was active on it during the analysis; the working tree may have moved again.
- **Whether the `≲1200 lines` spec target was a budget or an estimate.** Determines whether the 3.4× overrun is a deviation to remediate or an estimate to amend. I recommend amending, but that is the owner's call.
- **Historical context for two deliberate choices** — why `FORBIDDEN_RELAXATIONS` was explicitly kept off `semantic_const` (:901–903 gives the *what*, not the *why*), and why `host_init_hash=""` was chosen over omitting the field or hashing the no-op host. Both read as deliberate. If there is a reason, Q7 and Q2 need re-scoping.
- **CI configuration.** Q4's "eval exits 0" matters a great deal if a CI job shells `&&` on it and not at all if no CI consumes it.

## Caveats & Required Follow-ups

**What you must verify before relying on this analysis**

1. **Spot-check any single row before acting on it.** The coverage tally follows a self-reported 2-in-16 error rate on a first pass, and one row survived on a near-miss (Limitation 8).
2. **Re-read the plotting sidecar at current HEAD.** Q11 is anchored at `aa86388` and a peer session may have moved it.
3. **Confirm Q1's reachability against your own workflow** before accepting it as the top-ranked item.
4. **Check the spec before treating any finding as a defect.** One already flipped from "strongest finding" to "by design" on a direct spec read.

**Assumptions this rests on**

- That `02-subsystem-catalog.md` and the coordination log accurately report what their authors read. I re-verified one claim directly (the `_policy_tokens` caller set, which produced a correction) and accepted the rest on the strength of their citations. Note what the validation gate does **not** cover here: it confirmed citations are *present*, not that they are *right*, and it never opened `kernel_demo.py`. So no catalog claim has been independently confirmed against source except by the coordinator's targeted re-reads and my one spot-check — and the one spot-check that was made found an over-rating.
- That `kernel_demo.py` is byte-stable at `aa86388` — verified three times, and the basis for treating 8 of 9 entries as sound.
- That the severity axis the owner cares about is **validity first, availability second**. If the priority is instead "never lose a collection run," Q6 moves to the top.

**What this explicitly does NOT account for**

- Security surface and dependency analysis, both deliberately out of scope.
- Runtime behaviour of any CLI mode. No gate has been observed firing on real data.
- Performance and memory, beyond the noted whole-store eager `merge()` (~8.5 MB decoded per call at configured scale).
- Whether the findings are *worth fixing given the demo's remaining lifespan*. This is a pre-Phase-A demo; several items may be correctly answered with "the demo ends before this matters." That is the owner's judgement, not mine.

**Recommended next steps, in order**

1. **Land the four additive fixes** — `host_init_hash` (Q2), the gate-8 skip test and device assertion (Q3), the shard newline fix (Q6), the `--void-preregistration` reorder (Q9/Q8). All are S, none moves `config_hash`, and three have measured costs. Do these before any collection begins.
2. **Add the seed capacity gate** (Q7) — the one constraints-in-comments instance with a present consequence for a reported gate outcome.
3. **Decide Q1's fix shape** — split the policy identity out of `manifest_hash`. This is the only item needing a design decision, and the read-side analysis says it is safe.
4. **Batch the semantic-surface work into one re-freeze commit** — Q5's consolidation (twin-equality test *first*), Q8's dead flag and exit code, and Q7's `FORBIDDEN_RELAXATIONS` promotion with real selftest assertions.
5. **Extract `run_eval`'s statistics block** (Q10) and add tests for the six estimators at the assembly level — this closes the "untested join" rather than adding more unit tests to a well-tested head and tail.
6. **Re-merge the catalog from `temp/`** — it is stale against explorers 7 and 8 (Limitation 3). The unmerged content includes the strongest verification evidence in the analysis (the `test_learning.py:91` band paragraph) and the measured timings that defeat the "expensive to test" explanation. Anyone reading `02-subsystem-catalog.md` rather than this document is currently missing both. The validation gate itself is satisfied — CHECK 1 PASS 9/9, and the two critical dependency contradictions are fixed, which unblocks diagram generation.
7. **Route `plot_alpha_beta`** (Q11) to whichever session owns the sidecar. I have not attempted to identify it.
