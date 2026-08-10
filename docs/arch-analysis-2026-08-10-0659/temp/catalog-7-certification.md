## Certification Battery

**Location:** `experiments/kernel_demo.py` (lines 1979–2306, 2502–3062, 3265–3339);
external test layer at `tests/unit/kernel_demo/` (`test_preflight_gates.py` 297 lines,
`test_selftest.py` 14 lines, `test_store.py` 142 lines)

**Responsibility:** Decides whether a run of the demo is permitted to produce a
claim at all — a self-test check battery that emits a code-identity certificate,
an eight-gate admission battery whose pass is a hard precondition for the freeze
manifest, and the pre-registered statistical estimators that compute the run's
five verdict booleans.

**Key Components:**

- `sign_flip_pvalue` (line 1979) — one-sided sign-flip permutation p-value,
  `(count+1)/(n+1)` (1986). Null: the per-unit lift distribution is symmetric
  about zero. Unit is the **episode**: its `lifts` argument is built from
  `per_comp["trained"]`, one entry per eval episode (3711–3714).
- `money_chart_permutation_pvalue` (line 1990) — permutation test on a
  classes-matched count. `matched()` (2000–2013) computes the modal pick per
  pathology class with a deterministic lexicographic tie-break (2010). The
  permutation unit is the **EPISODE**: `ep_order`/`ep_path` are built per episode
  (2016–2021), `torch.randperm` permutes episodes (2028), and `remap` moves every
  grid point of an episode together (2029–2030); 2022–2023 raises if one episode
  carries two pathology labels. **This matches the rev 6.1 pre-data amendment
  ("episode-level money null") exactly** — the rationale at 1993–1999 states that
  point-level shuffling would under-disperse the null by up to the cluster size.
  The amendment is pinned by a *discriminating* test
  (`test_learning.py:91`): it asserts the two-labels-per-episode `ValueError`, then
  bounds `0.4 < p < 0.6` on a cluster-preserving fixture — a band chosen because a
  point-level shuffle would land near 1/6. That test would fail on a regression to
  point-level shuffling, which is the strongest verification of the rev 6.1
  amendment anywhere in the repo.
- `_tiny_bundle_for_selftest` (line 2036) — synthetic CIFAR-shaped data on a
  hardcoded literal seed 0 (2039), so the smoke episode is byte-identical across
  invocations rather than varying with `run_seed`.
- `_section_source` (line 2052) — reads `Path(__file__)` at runtime and slices
  text between `# section N ` markers. **It does not hash.** Its sole use is a
  source-text grep for `nn.init.` in sections 4/5/11 (2159–2162), with the needle
  split at 2159 so the checking code never matches itself.
- `run_selftest` (line 2061) — ten-step battery. `record()` (2068–2076) traps
  every exception into `{"status": "fail"}` so one broken check cannot abort the
  table, and marks GPU-only steps `"skipped"` on CPU. Steps: (1)
  `forbidden_relaxations` (2079–2082, unconditional pass); (2) `determinism_probe`
  (2087–2097, GPU-only); (3) `smoke_episode` asserting `twin_ok`/`nullseed_ok`
  (2101–2113); (4) `tau_init_rms` within 5% of `cfg.tau` (2118–2134); (5)
  `signed_zero_scan` (2139–2148); (6) `blindness_and_init_grep` (2154–2163); (7)
  `store_checks` (2169–2219); (8) `partition_check` (2224–2230); (9)
  `rng_scope_isolation` (2235–2241); (10) `det_mode_cost` (2251–2280, GPU-only).
- `--certify` artifact (2288–2301) — refuses unless CUDA **and** zero failed
  **and** zero skipped (2290–2291), then atomically writes `certified.json`
  containing `git_rev`, step results and `det_mode_cost` (2297–2300). Records the
  git revision but **not** `config_hash`.
- `GateResult` (line 2502) — `ok`/`reason`/`detail`/`remedy`; `remedy` names the
  licensed knob per gate (e.g. 2688 "tau, lambda, seed_lr — never the sampler").
- `_arm_by_name` (2510), `_all_arms_diverged` (2515), `_first_fans` (2521),
  `_val_argmax` (2535) — `_first_fans` takes the lowest-`fan_epoch` fan per
  episode, one unit per trajectory, explicitly against pseudo-replication
  (2522–2523); `_val_argmax` breaks ties by `SEED_NAMES` order (2539).
- `gate1_noop_sanity` (2547) — no-op must win ≥ `gate1_min_mild_noop_wins` of mild
  first-fans **and** must not be modal in any targeted pathology (2557–2571).
  FAILS on no records, all-diverged, too few mild wins, or no-op modal anywhere
  targeted. Pass/fail/all-diverged cases pinned at `test_preflight_gates.py:140`,
  `:147`.
- `gate2_signal` (2577) — two linear probes on mean telemetry with a by-episode
  holdout (2592). FAILS if pathology probe ≤ `gate2_probe_min_acc`, winner probe ≤
  holdout majority, or the split is degenerate (2598–2619). Consumes
  `_telemetry_vector_from_dict` at **2588**. Pinned at `:154`.
- `gate3_contrast` (2634) — fan density must exceed `gate3_contrast_mult` × the
  **paired refan noise floor**, mean per-arm `|R_fan − R_refan|` at matched
  (episode, epoch) (2643–2657). Comment 2638–2642 records why density computed
  *on* refans would make the gate structurally unpassable. Pinned at `:161`, plus
  an unpaired-refans loud-failure case at `:178`.
- `gate4_dominance` (2664) — FAILS if any seed wins > `gate4_dominance_max` of
  first-fans, or is a within-pathology majority everywhere (2678–2681). Pinned `:212`.
- `gate5_magnitude` (2687) — mean `rms_ratio_blend_entry` inside
  `[tau/band, tau*band]`. **No measurement is an explicit failure, not a pass**
  (2702–2703). Pinned `:221`.
- `gate6_horizon` (2715) — late density ≥ `gate6_late_density_mult` × early,
  split at the window midpoint (2717–2725). Pinned `:228`.
- `gate7_now_vs_later` (2733) — **report-only; returns `GateResult(True, ...)`
  unconditionally** (2755). `test_gate7_is_report_only` (`:236`) pins the
  always-pass behaviour as intended, not accidental.
- `gate8_pressure` (2759) — twin hash under worker pressure; siblings load the
  full bundle and touch a ready sentinel before the timed run (2786–2810). FAILS
  if the pressured host hash differs from solo, or siblings never become resident
  (2808). Returns `ok=True` with `"skipped (GPU-only)"` on non-CUDA (2761–2762).
  **The only gate with no test** — absent from `test_preflight_gates.py`'s imports.
- `run_refan` (2418) — replays the base prefix, snapshots, draws a **fresh**
  `CommonFuture` and re-runs all five arms including a fresh no-op (2468–2472); a
  deterministic base divergence records a `void_event` with `refan_k` rather than
  crashing (2437–2467). Fault-injection test at `test_preflight_gates.py:186`.
- `dataclass_gates_ok` (2843) — conjunction over all eight `ok` flags. Pinned `:293`.
- `freeze_manifest` (2848) — **refuses** on any not-ok gate (2860–2862), dirty
  worktree (2863), missing `certified.json` (2866), or `HEAD != certified["git_rev"]`
  (2870). Freezes `frozen_block_hash`, `config_hash`, `git_rev`, `certified_rev`,
  the literal `spec_rev` naming rev 6.1 (2877), the fitted `normalizer`,
  `fan_density`, derived temperatures, `schedule_id`, `data_split_id`, `n_train`
  (2884–2886), all eight `gate_results`, `gate8_outcome`, `det_mode_cost`,
  `concurrency_factor`, and a `plan_authored_constants` echo for owner sign-off
  (2891–2907). `manifest_hash` is a sha256 over the sorted manifest (2909); write
  is atomic (2914). Three of the four refusals plus atomicity are pinned at
  `test_preflight_gates.py:253`, `:262`, `:270`, `:280`.
- `run_preflight` (2919) — fan-granular resume (2927–2941), runs
  `cfg.preflight_refans` refans for gate 3's floor (2951–2954), fits the
  `Normalizer` on **preflight** telemetry only (2958–2961), evaluates all eight
  gates (2964–2975), and appends a `preflight_iter` whose `iteration` is derived
  from store state (2980) — every attempt counted in append-only history.
- `write_divergence_report` (3034) — atomic per-episode localisation artifact.
- `wilson_interval` (3265) — score interval; returns vacuous `(0.0, 1.0)` at
  `n == 0` (3268–3269).
- `class_derangement` (3279) — deterministic rotation by a seed-derived nonzero
  shift, guaranteed both a derangement and a permutation (3286–3287).
- `when_contrast` (3291) — the conditional mean over zero acted episodes is
  `None`, never a silent `0.0` (3305–3307).
- `verdict` (3313) — pure function returning **five** pre-registered booleans
  (3319–3325). It returns the dict; it never ANDs them — the conjunction is left
  to the reader (3820, 3904, 3920, 4054 all print or pass through).

**Dependencies:**

- Inbound: Run Orchestration & CLI
- Outbound: Identity, Config & Determinism Spine; Data, Episodes & Telemetry;
  Host, Seeds & Slot Lifecycle; Counterfactual Fan Executor; Records & Store;
  Policy & Learning; Run Orchestration & CLI

**Patterns Observed:**

- **Verification is two-layer, and the layers cover different things.** External
  pytest (`tests/unit/kernel_demo/`, 20 files, 1,828 LOC) proves each gate's
  *decision logic* on synthetic fixtures; in-band `--selftest` proves the
  *live substrate* (GPU determinism, tau-init RMS, signed zeros, rng isolation) on
  the real machine. Neither layer subsumes the other, and each covers a real gap
  in the other.
- **Every blocking gate is demonstrated falsifiable, not merely structurally so.**
  `test_preflight_gates.py` gives gates 1–6 a passing **and** a failing fixture
  (`:140`, `:154`, `:161`, `:212`, `:221`, `:228`). This is the strongest evidence
  in the codebase that the battery can actually fail: the negative cases are
  executable, not argued.
- **Refusal-chained certification.** `--certify` refuses on CPU/failure/skip
  (2290) → `freeze_manifest` refuses on failed gate, dirty worktree, missing
  certificate, HEAD mismatch (2860–2871) → `run_collect` re-checks
  `dataclass_gates_ok` (3153) → `run_train` (3343) and `run_eval` (3462) refuse on
  manifest mismatch → `main` exits 1 (4043).
- **Thresholds frozen before data, by hash.** All eight gate thresholds are in
  `FROZEN_FIELDS` (211–216) so editing one changes `frozen_block_hash` and
  invalidates every downstream artifact; `AGREEMENT_MARGIN` is a `semantic_const`
  (3256) and so enters `config_hash`.
- **One-shot pre-registration with a visible escape hatch.** `run_eval` refuses if
  `eval_results.json` exists; `--void-preregistration` overrides but writes a
  permanent append-only `void_event` (3430–3460). Re-rolling is possible, never
  invisible.
- **Clustering respected at every statistical unit.** `_first_fans` (2522), the
  by-episode probe split (2592), the episode-level money permutation (2016–2030),
  and the falsifier CI at episode count (3693–3698).
- **Absence is a failure, not a pass.** Gate 5 marks unmeasured seeds out-of-band
  (2702–2703); gate 3 fails outright with no paired refans (2652–2653);
  `when_contrast` returns `None` for an undefined conditional mean (3305–3307).
- **Measurement exceptions are scoped to subprocesses.** The flags-off
  determinism leg (2265–2277) and the gate-8 siblings (2787–2802) run in fresh
  interpreters, so a measured relaxation never touches the live process or a store.

**Concerns:**

- **Falsifiability assessment: the battery can genuinely fail and block the
  programme's claim — but four classes of failure pass it silently.** The positive
  half is demonstrated, not merely structural: gates 1–6 each carry an executable
  *failing* fixture (`test_preflight_gates.py:140`, `:154`, `:161`, `:212`, `:221`,
  `:228`), three of four freeze refusals are tested (`:253`, `:262`, `:270`), and
  the refusal chain (2860–2871 → 3153 → 3343/3462 → 4043) means a failed gate
  blocks collection, training and evaluation outright. The concern is what the
  battery cannot see. Four failure classes reach a green certification undetected,
  each detailed in its own entry below: a **vectorizer-twin desync**, checked by
  nothing in either verification layer and feeding gate 2's own inputs; a
  **torn-tail resume**, which silently drops the re-written record behind a
  benign-looking warning before bricking the store; a **CPU freeze**, which renders
  gate 8 vacuous while `dataclass_gates_ok` accepts it; and **any Class-1
  relaxation**, since selftest step 1 asserts nothing and the suite accepts its
  unconditional pass as genuine. A reader should take the battery's green as strong
  evidence about the properties it measures and no evidence at all about these four.
- **The two telemetry vectorizers are never compared — nothing, in either
  verification layer, checks that they agree.** `record_to_vector` (:397) serves
  the live decision path (:1749); `_telemetry_vector_from_dict` (:1811) serves the
  stored path — normalizer fit (2959), policy training (:1843), eval (:3386) and
  **gate 2 (2588, in this scope)**. Their field order is coupled by a comment at
  :1812 and nothing else. Verified by exhaustive grep over `experiments/` and
  `tests/`: `_telemetry_vector_from_dict` is referenced in **zero tests**;
  `record_to_vector` appears in exactly one (`test_telemetry.py:32`) which pins
  only `v.shape` and `v[EPOCH_FEATURE_IDX]` — a single-path assertion that would
  pass unchanged if the twin desynced. No selftest check compares them either:
  step 6 (2154–2163) checks `TelemetryRecord` **field names** for blindness, not
  vector ordering. **A desync passes certification silently and corrupts gate 2's
  own inputs**: the normalizer is calibrated through one twin and the policy
  infers through the other, so training and inference features would diverge with
  every gate still green. This is the clearest silent-failure class I found.
- **Torn-tail coverage is real but stops one step short of the failure that
  matters — and I measured the gap.** Correcting a premise in the referral:
  `merge()` **does** tolerate a torn tail (1617–1629) — it catches
  `JSONDecodeError`, and if the bad line is last it prints a loud WARNING and
  continues; only an interior line raises. `test_store.py:98` covers exactly that.
  What neither the test nor any gate covers is the **resume** sequence, because
  `append` opens mode `"a"` (1595) and writes the newline as a *suffix* (1598), so
  a partial line has no terminator and the next append fuses onto it. Executed
  against the real `Store`: (A) tear → merge = 2 records, warning, correct; (B)
  resume-append → the file still has 3 lines, the new record fused into the
  partial one; (C) merge = **2 records, and the newly written record is silently
  lost behind the identical "skipping torn final line" warning**; (D) one further
  append makes the fused line interior → `JSONDecodeError` → store unreadable.
  So (C) is a silent-loss path indistinguishable from the benign case, and it
  deterministically becomes (D) on the next resume. Partial mitigations: the lost
  record's `fan_id` is absent from the `merge()`-derived resume skip-set (3157) so
  it is re-collected, and `run_eval` refuses on `len(train_eps) < cfg.n_collect +
  _recorded_extensions(merged)` (3490–3492) — but the re-collection append is what
  triggers (D). Net: availability failure, not a false claim, but reached by a
  silent step.
- **No gate can speak to durability or concurrency, and gate 8 — the one gate that
  creates concurrency — deliberately writes nothing.** Grep over the gate-8 body
  (2768–2812) finds no `Store` construction or record append; the only `.append`
  hits are Python list operations. The sibling template ends at
  `run_base(..., fan_epochs=())` (2795), so it measures GPU contention and
  twin-hash stability (2815), never concurrent shard writes. Structurally, gates
  1–8 read only `seed_namespace == "preflight"` records (2956) and complete at
  freeze, before `--collect` writes a byte: a green preflight is not evidence
  about the collection substrate. No lock, PID guard or `O_EXCL` exists, and no
  test exercises two writers.
- **`preflight --freeze` asserts no device, so gate 8 can be frozen vacuously.**
  `--device` merely defaults to `cuda:0` (4011); neither `run_preflight` (2919)
  nor `freeze_manifest` (2848) checks it, and gate 8 self-skips to `ok=True` on
  CPU (2761–2762). Repro: `selftest --certify` on GPU, then
  `preflight --freeze --device cpu` at the same clean HEAD — certificate check
  passes, gate 8 vacuous, gates 2/3/5/6 computed from CPU numerics. The manifest
  records `concurrency_factor: None`, so it is detectable after the fact but never
  refused. Untested in either layer, since gate 8 has no test at all.
- **The falsifier criterion gets easier to pass with less data.**
  `falsifier_collapses` (3324) is an *accept-the-null* comparison against
  `wilson_interval(round(majority_null * n_units), n_units, alpha)` (3698). Smaller
  `n_units` widens the interval and raises `null_ci_hi`, so weaker evidence makes
  the falsifier more likely satisfied. `wilson_interval` returns `(0.0, 1.0)` at
  `n == 0` (3268–3269), vacuously true on empty data — unreachable in practice only
  because `run_eval` refuses on incomplete collection (3490–3492).
- **The `--certify` path itself is untested.** `test_selftest.py` (14 lines) calls
  `run_selftest(Config(), "cpu")` and asserts every step is `pass`/`skipped`; it
  never passes `certify=True`. The two `certified.json` references in the suite
  (`test_preflight_gates.py:273`, `:283`) are hand-written fixtures for the freeze
  tests. So the refusal at 2290–2291 and the atomic certificate write (2297–2300)
  — the mechanism that binds code identity to results — have no executable check
  in either layer. Relatedly, `freeze_manifest`'s missing-certificate refusal
  (2866) is the one freeze refusal with no test. **These gaps are not explained by
  cost.** The suite runs green with zero skips on a CUDA-capable machine, and the
  uncovered refusal paths are the cheapest code in the subsystem: measured here,
  `gate8_pressure(cfg, None, "cpu", 6)` returns `ok=True, "skipped (GPU-only)"` in
  **18 microseconds** without ever dereferencing its `data` argument (2761–2762
  precedes every use), and `freeze_manifest`'s missing-certificate refusal costs
  **0.5 ms** and is shape-identical to the three freeze-refusal tests that do exist
  (`:253`, `:262`, `:270`). Gate 8's *body* is genuinely expensive — the sibling
  template hardcodes a full `load_data` (2792) under a 300 s deadline (2803) — but
  that expense is a property of how the gate is written, and it does not extend to
  the skip path or the adjacent refusals. The untested paths are where cost is
  absent, not where it is concentrated.
- **Selftest step 1 asserts nothing.** `forbidden_relaxations` prints the tuple and
  records `{"status": "pass"}` unconditionally (2079–2082). No code path verifies
  any listed relaxation is absent, yet it counts toward `--certify`'s zero-failures
  requirement — and `test_selftest.py:13` accepts it as a genuine `pass`.
- **`certified.json` binds git revision, not semantic hash.** The payload (2297)
  carries `git_rev` but no `config_hash`, so code identity at freeze rests on
  `_worktree_clean()` (2835) plus HEAD equality (2870), not the semantic-surface
  hash the module otherwise computes. Any source change invisible to
  `git status` breaks the binding silently.
- **The durability cadence is echoed for sign-off but not hash-frozen.**
  `fsync_every` is written into `plan_authored_constants` (2906) yet is absent from
  `FROZEN_FIELDS` (188–223), and `Config` is off the semantic surface by explicit
  opt-out (91). It enters neither hash, and `run_collect` checks only those two
  plus gate results (3149–3154) — so it can change between freeze and collect
  without invalidating the manifest. Unfrozen fields are a licensed lever by
  design; the finding is that the echo is a record to sign, not a binding.
- **Gate 3's floor is a heuristic ratio, not a calibrated test.**
  `dict.fromkeys(density, noise)` (2655) assigns one scalar to both density keys
  despite differing noise structure, and pits a mean-absolute-deviation against a
  mean gap with a hardcoded ×2.0.
- **Gate 2's holdout is very small.** With `n_preflight = 30` and a 1-in-5
  by-episode holdout (2592), `win_acc > majority` (2619) is decided on roughly six
  episodes.
- **Gate 6's bar is weak.** `gate6_late_density_mult = 0.5` requires only that late
  density be at least *half* early density (2725).
- **The money-chart statistic is coarse.** `matched()` is integer-bounded 0–4
  (2000–2013), so `matched >= 3` (3323) admits only two passing values. The
  lexicographic tie-break (2010) favours the alphabetically first seed name;
  validity holds because the rule applies identically under permutation.
- **`_section_source` reads the on-disk file, not the imported module** (2053), and
  covers only sections 4, 5 and 11 (2160) — not slot-lifecycle or fan-executor.
- The module docstring still cites "LOCKED, rev 6" (line 8) while `freeze_manifest`
  writes `spec_rev` as rev 6.1 (2877). The code is on 6.1; the docstring is stale.
- Section 14 is ~560 lines, the single largest contributor to the file's ~3.4×
  overrun against the spec's ≲1200-line target. The single-file layout is a locked
  spec decision; the certification apparatus is what makes it expensive.

**Confidence:** High — read the full assigned scope (1979–2306, 2502–3062,
3265–3339) plus `run_refan` (2418–2497), and the external test layer
(`test_preflight_gates.py` all 297 lines, `test_selftest.py` all 14,
`test_store.py` all 142, `test_telemetry.py` all 51). A correction was applied
mid-analysis: an earlier version of this entry repeated the discovery doc's claim
that no `tests/` coverage exists for `experiments/`, which was wrong — verification
is two-layer, and the coverage claims above were re-derived against both layers
rather than against `--selftest` alone. Cross-checked out-of-range: `Config`/`FROZEN_FIELDS`
(136–223) to confirm all eight thresholds are hash-frozen and `fsync_every` is not;
`config_hash`/`frozen_block_hash` (226–237); `Store.append`/`merge` (1590–1648) to
adjudicate the torn-tail question; `measure_fan_density` (1856–1871); `run_collect`
(3145–3157); `run_eval` (3425–3500, 3660–3824); `main` (4004–4054). Two claims were
settled empirically rather than by reading: (1) exhaustive grep over `experiments/`
and `tests/` establishes that `_telemetry_vector_from_dict` appears in no test and
that no file compares it to `record_to_vector`; (2) the torn-tail chain was
**executed** against the real `Store` in a temp directory, producing the four-step
result quoted in Concerns — tear handled, resume-append silently lost, next append
bricks. Exhaustive grep for `cuda` (971, 1161, 2065–2069, 2262, 2290, 2761, 3079)
confirms no CUDA assertion on the preflight/freeze path. Two further claims were
measured by executing the real functions in this working tree rather than reading
them: `gate8_pressure(cfg, None, "cpu", 6)` returns its skip result in 18
microseconds without dereferencing `data`, and `freeze_manifest`'s
missing-certificate refusal raises in 0.5 ms — the timings quoted in Concerns.
All six statistical estimators in this scope have direct tests, several
discriminating rather than merely smoke: `sign_flip_pvalue` in both directions
(`test_learning.py:110`), `money_chart_permutation_pvalue` including the rev 6.1
clustering band (`:91`), `wilson_interval` against a known value
(`test_eval_stats.py:21`), `class_derangement` over 20 seeds (`:27`),
`when_contrast` including the `None`-not-`0.0` case (`:53`), and `verdict`'s key
set and threshold logic (`:74`). The suite was executed by Explorer 8 —
129 passed — so every "no test covers X" claim above is a property of a **green**
suite, not an inference from reading. Not verified: no runtime execution of
`--selftest` or `--preflight` end-to-end, so gate outcomes and p-values on real
data remain unobserved; and `verdict` is tested against a hand-built results dict
with hardcoded p-values (`test_eval_stats.py:61–71`), so the seam between the
tested estimators and the tested threshold logic — that `run_eval` files each
computed p-value under the right key — is covered by neither.

---
