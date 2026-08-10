# 00 — Coordination Plan

**Target:** `experiments/` (the Simic kernel demo)
**Coordinator:** Claude (system-archaeologist skill)
**Date:** 2026-08-10

---

## Deliverable Choice

**Selected: Option F — Full Analysis + Quality** (subsystem catalog, C4 diagrams,
final report, code-quality assessment), *without* a blocking menu prompt.

**Reasoning for not prompting:** standing instruction on kernel-demo work is
"execute unprompted; stop only for BLOCKED or load-bearing decisions"
(2026-08-10). Analysis depth is not load-bearing — nothing here is irreversible
or outward-facing, and "mini codebase" is itself the scope signal. Security
surface mapping (Option E) and dependency analysis (6.8) are **deliberately
omitted**: the target is an offline single-process research harness with no
network I/O, no auth, and two third-party deps (torch, matplotlib). They are
offered as extensions in the final hand-back rather than assumed.

## Analysis Plan

- **Scope:** `experiments/kernel_demo.py` (4,066 LOC), `experiments/kernel_demo_plots.py`
  (150 LOC), `experiments/__init__.py` (empty). 4,216 LOC total.
- **Strategy:** **PARALLEL**, 8 explorer subagents over line-range-partitioned
  sections of the monolith.
- **Complexity estimate:** Medium. Low file count, high internal density —
  ~120 top-level symbols, an explicit 17-section internal narrative order, and
  cross-cutting determinism/blinding invariants that span sections.
- **Time constraint:** None stated.

### Why parallel despite being a "mini codebase"

The skill's sequential/parallel heuristic keys on *subsystem count*, not file
count. This is one file containing ~13 cohesive subsystems with an author-declared
section map (module docstring, lines 10–27). Sequential reading of 4,066 dense
lines would exhaust coordinator context — the exact failure the delegation
imperative exists to prevent. Partitioning by the author's own section boundaries
gives clean, low-overlap explorer scopes.

### Deviation from the skill template: catalog write target

The skill's task template says explorers "append your section" to
`02-subsystem-catalog.md`. **Eight concurrent appenders would clobber each other**
(read-then-write races). Each explorer therefore writes a contract-formatted entry
to `temp/catalog-<n>-<slug>.md`; the coordinator concatenates into
`02-subsystem-catalog.md`. The contract *format* is unchanged and the validator
runs against the merged file. Deviation is mechanical, not substantive.

### Explorer partition

| # | Subsystem | Line ranges (kernel_demo.py) |
|---|-----------|------------------------------|
| 1 | Identity, config & determinism spine | 1–251, 917–989, 1534–1546, 2829–2847 |
| 2 | Data, episodes & telemetry | 252–554, 990–1141 |
| 3 | Host, seeds & slot lifecycle | 555–916 |
| 4 | Counterfactual fan executor | 1142–1419 |
| 5 | Records & store | 1420–1681 |
| 6 | Policy & learning | 1682–1978 |
| 7 | Certification: selftest, gates, preflight, statistics | 1979–2306, 2502–3062, 3265–3339 |
| 8 | Run orchestration & CLI + plotting sidecar | 2307–2501, 3063–3264, 3340–4066, `kernel_demo_plots.py` |

## Standing Constraints (given to every explorer)

1. **Single-file layout is a locked spec decision** (spec rev 6.1,
   `docs/superpowers/specs/2026-08-09-kernel-demo-design.md` line 4, line 574:
   "a reader can open the one file and follow the whole loop top-to-bottom").
   Monolith-shaped findings are marked *by design*, not debt. The **line budget**
   is a separate matter: spec line 560 targets "≲1200 lines"; actual is 4,066.
   That gap is a legitimate finding.
2. **Repo naming constitution (Namespec 2.0) does not apply here.** The demo is
   pre-Phase-A and explicitly "deliberately NOT Simic" (module docstring line 3).
   Explorers must not invent domain codenames; use the author's own section names.
3. **Report the certification machinery.** The distinctive property of this
   codebase is that it is *self-certifying*: `semantic()`/`semantic_const()`
   spec-binding, a determinism spine, typed divergence classes, and an 8-gate
   preflight battery. A generic "Data/Model/Training/CLI" catalog would miss it.

## Execution Log

- **06:59** Created workspace `docs/arch-analysis-2026-08-10-0659/`.
- **07:00** Orientation: 5 files, 4,216 LOC, 3 Python. Symbol map extracted
  (~120 top-level defs/classes). Module docstring declares 17-section order.
- **07:02** Read contracts: `analyzing-unknown-codebases.md`,
  `validating-architecture-analysis.md`.
- **07:03** Advisor consulted pre-commitment. Adopted: sequential-tier ruled out
  in favour of line-range parallel partition; per-explorer temp files; locked-spec
  and namespec constraints propagated to explorers.
- **07:05** Verified `_worktree_clean()` (line 2835) is a `git status --porcelain`
  emptiness check → this workspace directory, uncommitted, will fail a certified
  run's preflight. Recorded for the final report.
- **07:06** Deliverable choice recorded (Option F, no blocking prompt). Wrote
  coordination plan.
- **07:08** Wrote `01-discovery-findings.md`.
- **07:10** Spawned 8 `codebase-explorer` subagents in parallel.
- **07:31** Explorer 5 (Records & Store) returned. Entry at `temp/catalog-5-store.md`.
  Note: appended SME-protocol Risk/Gaps/Caveats sections below the contract block —
  **coordinator must strip these at merge** (contract forbids extra sections; the
  explorer flagged this itself). Substance is sound; the extras are procedural.
  - Grouped-statistics wall **confirmed closed** at the storage layer:
    `train_tune_split` (:1540) is deterministic on episode identity, stamped once
    at :2339, inherited by every fan at :2367.
  - Two severe durability findings: torn-tail on `open(..., "a")` (:1595) bricks
    resume via `merge()` → `run_collect` skip-set (:1629, :3157); no lock/PID
    guard/`O_EXCL` anywhere, so concurrent `--collect` runs collide on worker id 0
    (:3225). Correct by discipline, not enforcement.
  - Tolerant-reader hazard at `decode_record` :1574 (`data.get(f.name)` → `None`
    at same schema version; zero beneficiaries at `SCHEMA_VERSION = 1`).
- **07:33** Relayed explorer 5's two cross-explorer flags mid-flight:
  - → **explorer 7**: selftest store battery (:2168–2215) does not cover torn
    lines, concurrent writers, or resume-after-crash — exactly where explorer 5's
    top findings sit. Asked whether any gate catches that class or it passes
    certification silently.
  - → **explorer 6**: asked to confirm nothing in the learning path re-splits or
    re-weights across the train/tune wall after `load_for_training` (:1673)
    returns. Store guarantee covers storage only.
- **07:48** Explorers 4 (Counterfactual Fan Executor) and 2 (Data, Episodes &
  Telemetry) returned. Both wrote contract-clean entries and kept SME-protocol
  material out of the file — merge is clean for both.

  **Explorer 4 — the counterfactual machinery is sound.** Snapshot capture is
  sufficient and its omissions are principled (no sampler to desync; constant LR
  by design, :874–878; slot dormant on the base path). Arms rebuild from snapshot
  *values* rather than restoring shared objects (:1296–1309); one shared
  `CommonFuture` passed by reference to every arm and indexed by absolute epoch
  (:1291→:1316) enforces common random numbers structurally; the no-op arm is a
  really-executed measured arm that doubles as the twin (:1381, :1390); arm
  identity enters only via `derive(episode_seed,"arm",name)` inside `rng_scope`
  (:1174, :730), so arm identity cannot shift the shared stream. This is the
  strongest-engineered part of the codebase.

  **Explorer 2 — no leakage, blinding is real.** Splits are a deterministic
  partition of one permutation (:263–264), test is the official CIFAR-10 test set
  (:284), independently asserted by `partition_check` (:2224–2231). `Normalizer`
  is fit on preflight fans only (:2957–2961), frozen into `frozen.json` (:2878),
  loaded read-only thereafter — **no calibration-on-test**. Blinding in
  `TelemetryRecord` is **by field absence** (:358–369), not by ignoring — the
  distinction the repo cares about, and it is the good one.

  **New cross-range findings routed at 07:50:**
  - → **explorer 8** (HIGH): explorer 4 reports `run_eval` (:3507–3588) bypasses
    the fan executor entirely — no Snapshot, no `run_arm`, no twin — computing the
    headline lift (:3587) across two independently-constructed episodes matched
    only by seed determinism, with no prefix-agreement hash check. If confirmed,
    the headline number rests on a weaker guarantee than the fan records do.
    Also asked to check the `ArmResult`-as-untyped-dict shape mismatch (:1491,
    :2376/:2492 full asdict vs :2188/:3608 hand-built partial).
  - → **explorer 7** (2nd coverage question): `record_to_vector` (:397) and
    `_telemetry_vector_from_dict` (:1811) are a coupled pair with no equality
    check — coupling enforced only by a comment (:1812). Live path uses one
    (:1749), stored/training path the other (:1843, :2959, :3386). Asked whether
    any gate compares them; explorer 2's severity rating depends on the answer.
  - → **explorer 3**: do `Host`/`Slot`/`SeedDelta` forwards contain stochastic
    ops? Determines whether the snapshot RNG machinery defends a live invariant
    or a latent one. Also asked what `FORBIDDEN_RELAXATIONS` (:900–913) contains.

  **Explorer 4's own top findings for the quality pass:** `end_state_R` (:1189) is
  *not* end-state — it is a 3-epoch trailing mean (:1192) with a hard-coded window
  invisible to `config_hash`, so the name misleads; the cross-arm value-exactness
  check (:1400) is a bare `assert` (stripped under `-O`) that also silently no-ops
  when `snap.epoch+stage_k-1 >= horizon`; `torch.set_rng_state` (:1307) is
  process-global so arm correctness depends on sequential execution, undocumented.

  **Explorer 2's second finding:** dataset *content* is not bound to run identity —
  manifest carries `data_split_id` + `n_train` (:2883–2886) but no pixel checksum,
  and all four refusal gates check only those (:3088, :3465, :3955, :3964). A
  modified-but-same-size extraction under `runs/data` passes every gate and replays
  "clean". For a self-certifying pipeline, data is the one uncovered input.

  **Tool note:** explorer 4 reported the `advisor` tool was rate-limited during its
  run, so its entry had no second-model review. Recorded rather than silently
  absorbed; the validator gate and this coordinator's synthesis are the
  compensating controls.
- **08:02** Explorers 7 (Certification Battery) and 6 (Policy & Learning) returned.

  **CONFLICT DETECTED AND RESOLVED — test coverage.** Explorer 7 confirmed my
  discovery-doc Gap #9 ("no `tests/` for `experiments/`"); explorer 6 refuted it.
  Coordinator adjudicated directly (`ls` + `wc` + grep): **explorer 6 is correct.**
  `tests/unit/kernel_demo/` exists — 20 files, 1,828 LOC, 17 test modules including
  `test_preflight_gates.py`, `test_selftest.py`, `test_store.py`. **The error
  originated in my discovery doc**, which explorer 7 then confirmed rather than
  independently checked. Discovery §9 corrected; explorer 7 asked to amend its
  entry and re-answer both coverage questions against the pytest suite. Lesson
  logged: a coordinator-asserted gap propagates as fact to every explorer that
  reads it — discovery claims need the same evidence standard as explorer claims.

  Also corrected in discovery §5 per explorer 7: `_section_source` (:2052) does
  **not** hash source; it slices text between `# section N` markers to grep for
  `nn.init.` (:2159–2162). And `certified.json` (:2297) omits `config_hash`, so
  the certificate binds code via `_worktree_clean()` + HEAD only.

  **Explorer 7 — battery IS falsifiable, with four named soft spots.** Refusal
  chain verified closed: `freeze_manifest` raises on not-ok gate / dirty worktree /
  missing certificate / HEAD≠certified rev (2860–2870) → `run_collect` re-checks
  (3153) → `run_train` (3343) and `run_eval` (3462) refuse on mismatch → `main`
  exits 1 (4043). Verdict thresholds all live in `FROZEN_FIELDS` (211–216) or
  `semantic_const`, so post-hoc tuning invalidates `config_hash` and every
  downstream artifact. Eval is one-shot; re-running demands `--void-preregistration`
  writing an append-only `void_event` (3437–3460). Genuine anti-p-hacking, not
  theatre. Episode-level money null confirmed implemented as rev 6.1 amended
  (2016–2030, raises at 2022–2023 if an episode carries two pathology labels).
  Soft spots: gate7 always passes (2755, `remedy="report-only"` — "8 gates passed"
  means seven); gate8 vacuous on CPU (2761–2762); gate6's ×0.5 multiplier; and
  `verdict()` returns five booleans but **never ANDs them** (3820, 3904, 3920,
  4054 all just print) — the conjunction is left to the reader.
  Two sharp new findings: **(a) CPU freeze hole** — `--device` defaults to `cuda:0`
  (4011) but neither `run_preflight` nor `freeze_manifest` asserts it, so certify on
  GPU then `preflight --freeze --device cpu` at the same clean HEAD yields a frozen
  manifest with vacuous gate8 and CPU-computed gates, no refusal. **(b) Falsifier
  gets EASIER with less data** — `falsifier_collapses` (3324) is an accept-the-null
  test against `wilson_interval(..., n_units)`; smaller n widens the CI and raises
  `null_ci_hi`, and `wilson_interval` returns `(0.0, 1.0)` at n=0 (3268–3269).
  Also: selftest step 1 `forbidden_relaxations` (2079–2082) prints and records an
  unconditional pass — asserts nothing, yet counts toward `--certify`'s zero-failure
  requirement. Docstring line 8 says "rev 6" while `freeze_manifest` writes
  `spec_rev` 6.1 (2877) — stale. Section 14 alone is ~560 lines, the largest single
  contributor to the 3.4× budget overrun.

  **Explorer 6 — pre-registration chain is tight; two high-severity structural
  findings.** Silent-default question answered **clean**: `_as_float` (:1802)
  rejects `bool` before the numeric check (:1805, correct — bool subclasses int)
  and raises on `None` (:1806); `_telemetry_vector_from_dict` uses direct subscript
  `d[key]` (:1814), **not `.get()`** — missing key raises `KeyError`. No silent-zero
  defect. Temperatures verifiably frozen: `frozen_density` is a keyword-only param
  **with no default** (:1934), so recomputation is impossible by signature; sourced
  from `frozen.json` and re-asserted against the manifest (:3353–3354). Checkpoint
  selection is on the **tune** split (:1955, :1964–1972) and eval records cannot
  physically reach the selector (`SplitViolation` first, :1938/:1666). Loss is
  closed-form expected reward under full feedback (:1898) — no REINFORCE, no
  sampling — with `pi.detach()` stop-gradient so WHEN cannot backprop into WHICH
  (:1903–1904). Answering my train/tune-wall question: **the learning path honours
  the wall; nothing re-splits after `load_for_training`.**
  Two high-severity findings: **(a) dual deployment rule** — `decide_live` (:1754)
  has zero production callers (coordinator-verified: only caller repo-wide is
  `tests/unit/kernel_demo/test_policy.py:64`), while `run_eval` re-implements the
  rule inline at :3562–3573; the author knows and requests manual lockstep
  (:3568–3571). The tested code produces nothing; the code producing every recorded
  eval decision has no direct test. They already differ structurally on the window
  guard (:1763 vs :3551). `query_teacher_forced` (:1786) is fully dead — and both
  are `@semantic`, so deleting them changes `config_hash` and makes `run_train`
  refuse: **load-bearing dead code**. **(b) The vectorizer twin, independently
  confirmed** — matches explorer 2's finding 1 from a different direction; explorer 6
  adds that `_telemetry_vector_from_dict` is imported by no test at all.
  Residual: neither `_as_float` nor the dict decoder checks **finiteness**, and
  `json.loads` accepts `NaN`/`Infinity` by default, so a non-finite can bypass
  `TelemetryRecord.__post_init__` (:390–393) and reach the frozen normalizer fit
  (:2959) before failing loud at the logit guards.
- **08:06** Sent explorer 7 an amendment request (test-suite correction + both
  unanswered coverage questions, now checkable against `test_store.py`,
  `test_preflight_gates.py`, `test_selftest.py`). Its CPU-freeze and falsifier-CI
  findings stand and need no rework.
- **08:20** Explorers 1 (Identity/Determinism), 3 (Host/Seeds/Slot) returned;
  explorers 6 and 7 returned answers to the routed questions. 7 of 8 complete;
  only explorer 8 (Run Orchestration & CLI) outstanding.

  **Explorer 1 independently corrected discovery §9** — third agent to touch it,
  second to get it right. Confirms the correction already applied at 08:05. Also
  claimed the stale-docstring finding (rev 6 vs rev 6.1) as in-range; explorer 7
  should not double-report it.

  **Explorer 1 — self-certification confirmed and stronger than hypothesised.**
  `@semantic` is an import-time registration decorator over **109 objects** feeding
  `config_hash()` (SHA-256 over `inspect.getsource()` of each, sorted by source
  text); `frozen_block_hash` is a *separate, non-subsuming* hash over 34
  pre-registered `Config` fields; all four CLI modes refuse on mismatch;
  `_NON_SEMANTIC` (11 opt-outs) is enforced by a real test at `test_derive.py:93`.
  **Notable positive to preserve in the final report:** determinism is achieved by
  *never depending on the global RNG stream* — `torch.manual_seed` is never called —
  rather than by seeding it. The one unscoped `torch.randn` (:1717) is inside a
  `rng_scope` opened at :1715. Enforcement is one text needle (`nn.init.` grep over
  3 sections, :2159–2163) that would not catch a future `torch.randn` lacking
  `generator=`.

  **Explorer 3 — the STE is the load-bearing trick.** Slot lifecycle DORMANT →
  TRAINING(k=3) → BLENDING(m=3) → FOSSILIZING(f=2) → FOSSILIZED. The STE at :819
  (`h + (delta - delta.detach())`) makes the forward value bitwise `h` during
  TRAINING while the seed still receives full gradients — **this is what makes the
  bitwise-twin claim possible at all**, and it connects directly to explorer 4's
  `TwinDivergence`. The trust region (:822–827) exists *because* the STE hides δ
  from the CE loss, so nothing else bounds its magnitude. The host is **never
  frozen** (:1062, opt updates it every step); what is isolated is the seed's
  *influence*, measured at exactly 0.000000 upstream gradient at β=0. Seeds are
  zero-delta at construction but **not at germination** — `tau_init` sets gain
  nonzero (:1181); the no-op property during TRAINING comes from the STE, not from
  a zero gain. The classic `add_param_group` momentum-corruption bug was checked by
  **execution** and confirmed negative; the author designed out the LR-scheduler
  variant structurally (:874–878).

  ### Coordinator adjudications (three questions escalated to me, all settled)

  **(a) `d_model`/`n_layers` unfrozen — DOWNGRADED to by-design.** Explorer 1 rated
  this its strongest finding and named the spec check as the single highest-value
  gap. I hold the spec, so I adjudicated. Spec rev 6.1 lines 151–154 enumerate the
  frozen block **exhaustively**: "pathology definitions, telemetry normalizer,
  entropy temperatures, exploration schedule, λ, τ, stage durations K/M/F, horizon,
  decision window, optimizer constants, diverged-arm convention, all pass
  thresholds." Policy architecture is **not** in that list, and lines 236–237
  describe it approximately ("d_model≈64", "~100k params") — deliberately not
  pinned. So the omission conforms to the locked spec; per standing constraint 1
  this is **by design, not a defect**. *Residual finding retained:* an architecture
  edit moves neither hash and nothing else catches it — see (b).

  **(b) Is `policy_checkpoint_id` ever refused on? NO — coordinator-verified.**
  Explorer 1 rested its mitigation for (a) on `ckpt_id = state_hash(policy)`
  (:3364). Grep of all 16 occurrences: it is *recorded* in `FanRecord` (:1443),
  fed into `fan_identity` (:1468/:1529), used in the merge sort key (:1652), and
  written into checkpoint filenames and JSON (:3365–3371) — but **never compared,
  asserted, or refused on** anywhere. It is `None` at every preflight/collect call
  site (:2180, :2368, :2397, :2453, :2484, :2992, :3173). The mitigation explorer 1
  relied on does not exist, which *raises* the residual severity of (a) even as the
  spec check lowers its classification. Net: not a spec violation, but an unremarked
  hole — architecture drift between freeze and eval is undetectable by any hash.

  **(c) Seed capacity/budget gate — CONFIRMED ABSENT.** Explorer 3 asked explorer 7
  to cross-check; I settled it by grep instead. `numel|param_count|budget|capacity`
  over the whole file yields only the comment at :690, `signs.numel()` in the sign-
  flip test (:1983), split-size checks (:2226–2227), and unrelated uses. **No
  capacity gate exists.** Explorer 3's finding stands: the seed menu spans
  129 / 4,337 / 8,897 / 60,137 params — a **466× spread** — with the budget floor
  enforced only by a comment. In a file that hashes its own source and runs eight
  preflight gates, this is the standout enforcement gap, and it bears directly on
  whether gate 4 (dominance) is measuring seed *design* or seed *capacity*.

  **Explorer 7's answer on store coverage — a useful severity correction.** No gate
  could catch torn-tail/concurrent-writer corruption, and the reason is structural:
  gates read only `seed_namespace == "preflight"` records (:2956) and the battery
  completes at freeze, **before `--collect` writes a byte**. But explorer 7 pushed
  back on "passes certification silently" and is right to: `run_preflight` calls
  `store.merge()` at :2923 before any gate, so a pre-existing torn tail crashes
  preflight fail-closed; `run_eval` refuses on episode count (:3490–3492); and
  concurrent writers on deterministic seeds collide on duplicate `fan_id`, which
  merge's duplicate assert catches. **Residual exposure is availability, not
  validity** — a bricked run needing operator intervention, not a certified false
  claim. Adopting that framing for the final report. Also newly found: `fsync_every`
  is echoed into `plan_authored_constants` (:2906) "for owner sign-off" but is in
  neither `FROZEN_FIELDS` nor `config_hash`, so the durability cadence can change
  between freeze and collect without invalidating the manifest.

  **Explorer 6's answer on the train/tune wall — honoured, with one bounded
  nuance.** `train_policy` uses `split_role` as-is (:1945–1946); batching draws
  `torch.randint(len(train_ex), ...)` (:1957) so tune examples are **outside the
  index space** — the wall is enforced by the index bound, not by convention.
  Nuance reported as a Pattern, not a Concern, and I agree with that call:
  `fan_to_example` drops `episode_seed` (:1847), so the learning path's unit is the
  fan, not the trajectory; with `fans_per_episode = 2` the tune criterion weights an
  episode by its surviving fan count (2, or 1–0 where the base diverged). Bounded at
  a 2:1 ratio, does not cross the wall, touches no reported statistic. Forward
  consequence worth carrying: the learning path is *structurally* incapable of
  episode-clustered training or selection without re-adding that field.

  **Ownership note from explorer 3:** `PATHOLOGIES`/`DESIGNED_WINNER` (:539–551) sit
  under the `# section 4 — HOST` header but fall inside explorer 2's line range.
  Explorer 3 covered them substantively; explorer 2's message does not mention them.
  Coordinator to verify no duplicate at merge and, if absent from both, confirm
  explorer 3's coverage carries.
- **08:34** Explorer 3 answered the stochastic-ops question: **clean negative,
  exhaustively verified.** No `Host`/`Slot`/`SeedDelta` forward or backward draws
  from the global torch RNG. Verified two ways — module-type audit over all 4
  pathologies × 4 seeds (zero `Dropout`/`AlphaDropout`/`RNNBase`; `AttnSeed`'s
  hand-written softmax avoids SDPA so there is no `dropout_p` surface at all), and
  a global-RNG state-comparison probe over **all 80 combinations** of pathology ×
  seed × stage running full forward + backward + `opt.step()`, with a positive
  control confirming the probe detects draws. Construction is RNG-isolated too:
  `build_host`, `build_seed` and `tau_init` all leave the global stream unchanged
  because `rng_scope` restores in its `finally`, so germination does not perturb it.

  **Consequence for explorer 4's finding:** the `cpu_rng` snapshot/restore at
  :1160/:1307 is **belt-and-braces** — nothing in the model path currently threatens
  the invariant it defends, and the sequential-arm constraint is latent rather than
  presently load-bearing. That resolves the open question between explorers 3 and 4.

  **The sharper structural finding.** `FORBIDDEN_RELAXATIONS` (:900–913) has nine
  entries — disabling the twin arm, disabling deterministic algorithms, enabling
  TF32, enabling `cudnn.benchmark`, enabling AMP, adding gradient clipping,
  **adding dropout**, running fans across devices, `torch.compile`. So the single
  change most likely to break the RNG-free property *is* named. But the tuple is
  deliberately **not** a `semantic_const` — the comment at :901–903 says
  "Documentation-only (printed by `--selftest`)" — so it is never hashed into
  `config_hash` and never mechanically checked. A future edit adding `nn.Dropout`
  to a seed would flip the global stream from decorative to load-bearing, make the
  sequential-arm requirement suddenly real, and **pass every gate in the file**.

  ### Emerging cross-cutting theme (for the architecture pass)

  Four independent findings from three explorers share one root cause —
  **load-bearing constraints that live only in comments, inside a codebase that
  otherwise hashes its own source and runs eight preflight gates:**
  - `FORBIDDEN_RELAXATIONS` documentation-only, never hashed (explorer 3, :901–903)
  - seed parameter budget floor is a comment with no `numel` check (explorer 3,
    :690; coordinator-confirmed absent file-wide)
  - `enable_class1()` honoured at process entry points but unenforced for any
    *importing* consumer — i.e. the plotting sidecar and every test module except
    `test_determinism.py` (explorer 1)
  - the `record_to_vector` / `_telemetry_vector_from_dict` field-order twin
    contract, enforced only by the comment at :1812 (explorers 2 and 6,
    independently)
  Recommend the final report consolidate these into **one** recommendation rather
  than four scattered ones, per explorer 3's suggestion. Explorer 1's finding 3
  (`_git_rev`/`_worktree_clean` unhashed and unclassified) belongs to the same
  cluster.

  **Process note, second occurrence:** explorer 3 caught a *false positive* in its
  own first `tau_init` probe (the harness called `torch.randn` inside the measured
  closure) and reran with allocation moved outside. This is the second confounded
  micro-test explorer 3 has caught and disclosed in this range — the first was a
  shift-invariant `sum()` loss masking the β effect. Both disclosed in its entry's
  Confidence section. Recording the pattern: anyone re-deriving these numbers must
  keep allocation out of the measured region and use a non-degenerate loss.
- **08:45** Explorer 8 (Run Orchestration & CLI + Plotting Sidecar) complete — all
  8 entries now on disk. Its entry is the strongest of the eight and is
  contract-clean (two entries, 8 sections each, no extras).

  ### ADJUDICATION — the headline question (explorer 4 vs explorer 8)

  **CONFLICT.** Explorer 4 claimed `run_eval` bypasses the fan executor entirely.
  Explorer 8 listed Counterfactual Fan Executor as an *outbound dependency*
  (`run_base`, `run_fan`, `run_arm`, `take_snapshot`, `TwinDivergence`) and framed
  the battery as "four arms against a shared no-op … common random numbers".
  These cannot both be right. **Coordinator read `:3500–3594` directly and
  adjudicated. Explorer 4 is correct on mechanism; explorer 8 is correct on
  comparator fairness. Neither framing alone is accurate.**

  What the code actually does in the comparator loop (:3507–3588):
  - **No `take_snapshot`, no `run_fan`, no `run_arm`, no `run_base`, no twin.**
  - The no-op is an **independently constructed episode**: `noop_ctx =
    make_episode(cfg, data, device, es, read_test=True)` (:3512), trained through
    the full horizon in a plain loop (:3514–3515).
  - Each comparator is **another independently constructed episode**: `ctx =
    make_episode(...)` (:3542), again a plain `train_one_epoch` loop (:3579).
  - `lift = r_test - r_noop_test` (:3587) therefore compares **two separately
    executed episodes**, matched only because `make_episode` is deterministic
    from `es`.

  So the fan-executor dependency edge explorer 8 recorded is real **only via the
  refan path** (`run_refan` at :3645), not via the headline lift. Explorer 8's
  "common random numbers" is also true in a narrower sense than it reads: all four
  comparators are scored against **one** no-op *number* per episode, which does
  make cross-comparator comparison fair — but that is not the same as branching
  four arms from a shared snapshot.

  **Net finding, stated precisely for the final report:** the fan path verifies its
  own matching (`TwinDivergence` exists precisely to catch a snapshot that fails to
  reproduce its base). The eval path has **no equivalent check** — no prefix hash,
  no twin, no assert that the no-op episode and the comparator episode actually
  agreed before germination. The headline number is therefore sound *if and only
  if* determinism holds, and it does not verify that determinism held. Note the
  supporting evidence is strong (explorer 3: no RNG draws anywhere in the model
  path, verified over 80 combinations; explorer 1: no dependence on the global
  stream; explorer 2: `CommonFuture` precomputed per-episode from `es`), so this is
  **an unverified assumption, not a known error** — the severity is "the headline
  claim rests on a guarantee the codebase elsewhere insists on proving."

  ### Explorer 8's own top finding — possibly the most severe in the analysis

  **Re-freeze silently decouples calibration from records; nothing on the train
  path detects it** (entry Concern 3). `manifest_hash` (:2909) covers the whole
  manifest including `gate_results` detail, `det_mode_cost` and
  `concurrency_factor` — all measured, run-varying — so re-running
  `preflight --freeze` on the *identical commit* yields a *different*
  `manifest_hash`. `freeze_manifest` overwrites `frozen.json` unconditionally
  (:2914) with no guard for a store already holding records. `run_train` then reads
  normalizer and betas from manifest B (:3347–3354) while training on records
  collected under manifest A, checking only `frozen_block_hash` and `config_hash`
  (:3343). `load_for_training` filters on `split_role`/`kind` only. `run_report`'s
  mixed-manifest refusal does not catch it — its comparison set is built from
  eval-namespace records plus `eval_results.json`, so train-namespace records never
  enter it. **Reachability is high**: both freeze preconditions (clean worktree,
  HEAD == certified rev) are satisfied by simply re-running preflight on the same
  commit. And `Store.merge`'s duplicate backstop is keyed `(manifest_hash, fan_id)`
  (:1636), so it *permits* the same fan under two generations — double-counted by
  `tr_fan_counts` (:3486) and by `load_for_training`.

  **Other high-value explorer 8 findings:** `--resume-eval` is a dead flag (:3426
  never read — reproducing verbatim the scar the author names at :4013);
  `--void-preregistration` appends the permanent void_event (:3437–3461) *before*
  the admission checks (:3462–3492), so a failed rerun leaves an unretractable void
  with no eval behind it; `divergence_*.json` is written by three call sites and
  **read by none** — a `TwinDivergence` halts collection but leaves no trace in the
  certified chain; post-halt records are indistinguishable from pre-halt (halt polled
  only between episodes, :3096); `eval` exits 0 regardless of verdict (:4054–4055)
  while selftest/preflight/collect all gate their exit code, so a five-false verdict
  is invisible to CI; `p.join()` (:3247) has no timeout and the parent never reads
  the heartbeats it asks workers to emit (:3119). Also: `run_eval` is a ~400-line
  function with seven responsibilities — explorer 8 correctly notes the single-*file*
  monolith is a locked spec decision but a single 400-line *function* is not covered
  by it, and identifies a clean seam (statistics :3651–3818 vs execution :3507–3646).

  **Plotting sidecar — the separation claim holds for the hash surface only.** No
  `@semantic`/`semantic_const`, so `config_hash` is genuinely untouched. But
  `SPIKE_CRASH_MARGIN = 0.05` (plots :21) *classifies* an arm as "spike-then-crash"
  into a figure legend while being unfrozen and unhashed; `per_seed[n] or [0.0]`
  (plots :121) renders an unmeasured seed identically to a measured zero; and
  `plot_money_chart_trio` defaults **every headline number** with `.get()`
  (plots :82–90) so a missing key plots as a zero bar rather than an error. That is
  the silent-zero pattern the main file goes out of its way to refuse — landing in
  the one module with no test coverage and no repo caller.
- **08:52** Merged 8 temp files → `02-subsystem-catalog.md` (9 entries, 885 lines).
  SME-protocol trailers stripped from catalog-5 (53 of 93 lines kept); all other
  entries were already contract-clean. Verified post-merge: 9 `##` headings, each
  with the 7 required bold sections. One suspected extra section flagged to the
  validator (a bolded "Falsifiability verdict:" block at line 773) rather than
  fixed by me — the skill forbids the coordinator patching subagent work ahead of
  the gate. Spawned `analysis-validator` (independent gate; 9 entries ≥ 3, so
  self-validation is not permitted).

  ### The eval finding, in its strongest form — coordinator-verified

  Advisor observed that two explorers had each found half of a sharper claim.
  Combined and verified against source:
  - `run_replay` refuses anything that is not a fan: `if rec.kind != "fan" or
    rec.fan_epoch is None: raise RuntimeError("replay supports kind='fan'
    records...")` (**:3957–3958**, read directly).
  - `run_eval`'s comparator loop writes `kind="policy_run"` with `fan_epoch=None`
    (**:3592, :3597**, read directly).

  So the headline comparator records fail the replay guard **twice over** — wrong
  kind *and* null fan epoch. Stated precisely:

  > The fan path is verified twice — `TwinDivergence` at runtime, `--replay`
  > post hoc. The headline lift path is verified **neither** way: it has no twin
  > (independent episodes via `make_episode`, :3512/:3542, matched only by seed
  > determinism), and its records are structurally excluded from the one mechanism
  > that could check the matching after the fact.

  **Precision note for the report:** this applies to `policy_run` comparator
  records specifically. The eval *grid* fans remain `kind="fan"` and are replayable
  — the comment at :3959–3961 confirms they carry `r_test` and replay under the
  recorded observation mode. Do not overstate this as "eval is unreplayable".

  This is the analysis's headline finding: not a bug, but the one place where a
  codebase that otherwise proves its claims asserts one instead.
- **09:05** Two peer corrections received; **both improve on my own adjudication**
  and are now authoritative over my 08:45 and 08:52 entries.

  **(i) My eval framing was overstated — explorer 8 re-read the fan executor and
  episode substrate to settle it.** "Matched only by seed determinism" understates
  the guarantee: `make_episode` (:1014) is a pure function of `(cfg, data, device,
  episode_seed, read_test)` with `CommonFuture` from `derive(es,"future",0)`, so
  both episodes share data *and* future by construction, and `train_one_epoch`
  consumes no global RNG. Explorer 8 hypothesised RNG-stream drift (the no-op runs
  first) and **refuted it — there is no shared stream to advance.** Common random
  numbers genuinely are shared.
  **Correct statement:** *the property the fan path re-verifies on every fan, the
  lift path assumes.*
  **Sharper citation than "no prefix check":** every fan records
  `host_init_hash = state_hash(ctx.host)` (:2342, :2374), but `policy_run` records
  **deliberately write `host_init_hash=""`** (:3606) — the field that would let an
  auditor confirm both episodes started from the same host is not stored at all.
  **Scope correction: 2 of 5 verdict booleans, not the whole claim.**
  `lift_positive` and `beats_schedule_only` (:3320–3321) rest on the unverified
  path; the eval *grid* runs through `run_collection_episode` → `run_base`/`run_fan`
  (:3624) with full twin + cross-arm + null-seed verification, so
  `agreement_beats_null`, `money_chart` and `falsifier_collapses` (:3322–3324) are
  properly matched. **What is weakly guaranteed is the lift magnitude, not the
  diagnostic claim.** My earlier "headline number" framing was too broad and has
  been corrected to the user.
  Two further explorer-8 findings from the same trace: eval **resume crosses a
  process boundary** — `r_noop_test` is recomputed live (:3512) while completed
  comparators are read from the store (:3521–3540) and then differenced, with no
  comparison of the record's stored `env` (:3607) against the live one, though
  `run_replay` refuses on exactly those keys via `REPLAY_REFUSAL_KEYS` (:3943); and
  **a diverged baseline is indistinguishable from a poor one** — `r_noop_test` falls
  back to `cfg.diverged_r` (:3519) but the no-op's *status* is never recorded, so
  baseline-diverges-treated-doesn't reads as a large seed-attributable gain.
  Proposed fix, cheap and additive: hash `noop_ctx.host` at construction and store
  it in `host_init_hash` instead of `""`.

  **(ii) Explorer 5's torn-tail mechanism is wrong; explorer 7 corrected it by
  execution, not argument.** `merge()` (1617–1629) *does* repair a torn **final**
  line — loud warning, continue — and `test_store.py:98` covers exactly that and
  passes. Only an *interior* bad line raises. The real defect is one step further
  out: `append` writes the newline as a **suffix** (:1598), so a resume-append fuses
  onto the unterminated partial line. Explorer 7's executed four-step sequence:
  (A) tear → merge = 2 records, correct; (B) resume-append → new record fuses;
  (C) merge = 2 records — **the newly written record silently lost, behind the
  identical benign warning**; (D) next append makes the fused line interior →
  unreadable. So there is a **silent-loss step nobody had**, and it deterministically
  becomes the bricking outcome. Explorer 5 asked to revise; severity re-framed as
  availability + a silent-loss step, not validity.

  **Explorer 7's falsifiability verdict is now demonstrated, not argued.** Gates 1–6
  each have an executable failing fixture in `test_preflight_gates.py`
  (:140/:154/:161/:212/:221/:228); three of four freeze refusals are tested
  (:253/:262/:270); `test_gate7_is_report_only` (:236) **pins** gate 7's always-pass
  as deliberate diagnostic behaviour, not oversight. Four classes still pass
  certification silently: vectorizer-twin desync (checked by nothing in either
  layer — and **gate 2 consumes the untested twin at :2588**), torn-tail resume,
  CPU freeze (gate 8 is the only gate absent from the test suite's imports), and any
  Class-1 relaxation (selftest step 1 asserts nothing; `test_selftest.py:13` accepts
  it as a genuine pass). New: the `--certify` path itself has **no test** —
  `test_selftest.py` never passes `certify=True` — so the mechanism binding code
  identity to results is unexercised.

  **Catalog re-merged at 07:21** (896 lines) after explorers 7 and 8 revised;
  validator notified mid-flight that its earlier read was stale, and given both
  corrections as inputs to check rather than conclusions to adopt.
- **09:12 — NEW DELIVERABLE requested by the user.** A recommended refactoring
  structure decomposing the demo into smaller modules **shaped like Simic**, so
  information flows become visible and the Leyline contract shapes fall out.
  User clarification mid-turn: *"its not going to be a full simic, just the parts
  that are there"* — so the mapping covers only domains the demo actually contains;
  absent domains are named as absent, which is itself informative about what the
  demo does and does not test.
  Framing decision (stated to the user): this is **not** a proposal to refactor the
  demo. Single-file is locked at rev 6.1 and the read-top-to-bottom property is the
  point. The exercise extracts the **contract shapes** the demo already implies —
  a paper decomposition feeding Phase A (Leyline contracts), which is the actual
  next engineering work per `AGENTS.md`.
  Delegated to `axiom-contract-engineering:contract-suite-architect` — the forward-
  design SME for typed cross-boundary contract suites — briefed to work from the
  catalog rather than re-reading 4,066 lines, and to read
  `docs/design/02-constitution.md` (the 45 INV-nn) as domain authority. Output:
  `11-simic-shaped-decomposition.md`.
  Note: I had not loaded `02-constitution.md` this session despite `AGENTS.md`
  requiring it every working session — delegating to an agent that will read it in
  full is the right correction, not a workaround.

- **09:30 — THE REPOSITORY MOVED UNDER THE ANALYSIS.** Caught while reconciling a
  test-suite line-count discrepancy (explorer 5 said 2,067 lines / 21 files; I had
  recorded 1,828 / 20). The discrepancy was real and led straight to it.

  **Timeline, verified against git — not inferred:**
  | Time | Event |
  |---|---|
  | 06:50:45 | `2b48431` — HEAD at session start. `kernel_demo_plots.py` = **150 lines**; `tests/unit/kernel_demo/test_plots.py` **does not exist** (`git cat-file -e` fails against this commit). |
  | ~06:59 | Analysis begins. Discovery records 4,216 LOC. |
  | 07:05:53 | `c666a4c` — peer session commits a product checkpoint. |
  | 07:14–07:19 | Explorer 8 reads the 150-line sidecar; reports silent-zero `.get()` defaults, `per_seed[n] or [0.0]`, and "no test module, no repo caller". **All accurate against `2b48431`.** |
  | **07:19:06** | **`853e9ef` — peer session commits *"kernel demo: plotting sidecar refuses to invent data (review fix pass)"*. Sidecar 150 → 425 lines; `test_plots.py` added (193 lines).** |
  | 07:21 | Further **uncommitted** edits to both files (432 / 239 lines). |

  **The commit fixes precisely what explorer 8 found.** The current sidecar carries
  a `PlotDataError` class (:34) and `require_number`/`require_dict` helpers that
  raise on missing or non-finite fields (:38–63) — i.e. the silent-zero class
  explorer 8 identified is exactly what "refuses to invent data" closes. Whether
  causal or coincidental, the finding was correct.

  **Blast radius — scoped, and smaller than it first appeared.**
  - `experiments/kernel_demo.py` is **unmodified**: mtime 06:51, `git diff --stat`
    empty, identical in worktree and HEAD. **8 of 9 catalog entries, and 4,066 of
    4,216 analysed lines, describe a stable artifact.**
  - **Only the Plotting Sidecar entry (150 lines) is stale.** Explorer 8 re-tasked
    to re-read the working tree and rewrite that entry alone, with an explicit
    version anchor in its Confidence section. Its "Run Orchestration & CLI" entry
    stands unchanged.
  - Validator notified: validate the stale entry for **contract compliance only**,
    skip its factual claims, and **record the moving-target limitation in the
    report** — a limitation the final report must carry.
  - Discovery doc amended with a version warning.

  **Process lessons, both mine:**
  1. **I never established a version anchor.** No commit SHA was recorded in the
     coordination plan, and no explorer was told which revision it was analysing.
     `00-coordination.md` should have opened with `git rev-parse HEAD`. A
     multi-agent analysis of a live repo is a distributed read of mutable state and
     needs a stated snapshot; without one, "the codebase" is not a well-defined
     object. **Fix for next time: record HEAD in the plan and give it to every
     explorer.**
  2. **The catch came from a line-count discrepancy I nearly waved through.**
     Explorer 5 and I disagreed by 239 lines on a number neither of us needed.
     Reconciling it — rather than taking the larger figure — is what surfaced a
     moved HEAD. Small unexplained numeric disagreements between agents are signal.

  **Also noted:** `git status` is now `M experiments/kernel_demo_plots.py`,
  `M tests/unit/kernel_demo/test_plots.py`, `?? docs/arch-analysis-2026-08-10-0659/`.
  All three make `_worktree_clean()` (:2835) return False, so a certified run would
  refuse at freeze until they are committed or the workspace is ignored. The two
  modified source files are a **peer session's in-progress work, not mine** — I have
  touched no source file in this analysis.

- **09:48** Peer session committed twice more: `853e9ef` (07:19) then `aa86388`
  (07:32, *"an empty tune curve is a skip, not a crash"*). Working tree now matches
  HEAD for both files, so explorer 8's rewritten Plotting Sidecar entry is anchored
  to a commit rather than a moving tree. Catalog re-merged: **911 lines, 9 entries**,
  with a version anchor in the header.
  Explorer 8 **ran** `pytest tests/unit/kernel_demo/test_plots.py -q` → **16 passed**
  — the only runtime verification anyone in this analysis has performed. All eight
  of its original sidecar concerns are closed by `853e9ef`; ten new ones replace
  them, sharpest being that `_load_fans` refuses ambiguous namespaces and manifest
  generations but **silently pools `split_role`**, and a `--namespace train` store
  legitimately holds both `train` and `tune` (the held-out selection split) — the
  fabricated aggregate the module's own comment guards against.
  Explorer 8 also settled the §9 provenance: **15 of the 16 test modules predate
  our session** and were present at `2b48431`. So my discovery error was a genuine
  mistake from the outset, not an artifact of the moving repo. That is the worse
  reading and the correct one.

- **09:52 — DELIVERABLE 11 landed:** `11-simic-shaped-decomposition.md` (~1,410
  lines), sections 0/A–F. Three items escalated to me; **all three adjudicated by
  checking source and the constitution, not by rubber-stamping.**

  **(a) Elesh absent → PARTIAL. Accepted.** `02-constitution.md` line 47 gives
  Elesh's mandate as "Structural legality, canonicalisation and semantic identity"
  with the anti-pattern "a utility predictor or task judge"; line 70, "forces it
  into canonical, unified, structurally legal form." The demo's `SeedDelta` uniform
  interface plus `tau_init` driving four dissimilar seeds to a measured
  `rms_ratio = 0.0500` **is** canonicalisation on the constitution's own words, and
  it does not judge utility (computed from host feature statistics, not reward), so
  it avoids the anti-pattern the constitution names at line 119. Contract present,
  conformance *step* absent because nothing arrives unconformed — the menu is
  conformed by authorship. Untested as a result: INV-19, INV-21.

  **(b) Ugin absent → PARTIAL. Accepted with a caveat.** "Grants and constrains
  without instructing" is the right test and `FROZEN_FIELDS` meets it. But it is the
  **weaker of the two partials**: a static config block, not a per-run issued grant,
  so the envelope's shape is present while its *issuance* is absent along with the
  issuer. Architect asked to mark it as such so Phase A does not over-credit it.
  INV-23 is the sharp end — budgets are constants and nothing reports spend.

  **(c) §F.2 freeze-manifest split — the architect's flagged uncertainty is
  RETIRED, and the conclusion is stronger than "harmless".** It asked whether
  removing measured values from the policy identity would weaken the anti-p-hacking
  property. **It cannot, because that property never rested on `manifest_hash`.**
  Read directly: `run_train` (:3343) and `run_eval` (:3462) each check **only**
  `frozen_block_hash` and `config_hash` — `manifest_hash` is **not consulted by
  either**. Threshold tampering is caught by `frozen_block_hash` (carrying the gate
  thresholds at :211–216, per explorer 7), code tampering by `config_hash` over the
  semantic surface. `manifest_hash` (:2909) hashes the whole manifest *including*
  `gate_results`, `det_mode_cost` and `concurrency_factor` — it is a **run
  identity**, and nothing enforcing pre-registration reads it.
  **Therefore the split is not merely safe — it is the fix for the defect that
  motivated it.** Explorer 8's re-freeze decoupling exists precisely because
  `manifest_hash` moves for reasons unrelated to policy and so cannot bind records
  to their calibration. A content-hashed policy record would be stable across a
  re-freeze on the same commit and *could* serve as that key.
  Implementation caveat passed on: `plan_authored_constants` (:2896–2906) mixes
  genuine policy constants with `fsync_every`, which explorer 7 found is in neither
  `FROZEN_FIELDS` nor `config_hash`. The split is the moment to sort that.

  **(d) Architect self-corrected one claim before shipping** — initially wrote that
  the typed telemetry round-trip is broken (`_sanitize_json` maps non-finite→`None`,
  `check_finite` has no `else: raise`), then found `__post_init__` (:375) forecloses
  the path so a non-finite `TelemetryRecord` never exists. Downgraded to "the guard
  has no floor", same Phase-A fix, honest severity. Correct instinct; kept.

- **09:55** Spawned `contract-reviewer` for an adversarial audit of the suite →
  `12-contract-suite-audit.md`. This is the pack's own discipline (the designer must
  not audit its own suite) and the architect requested it. Briefed to spot-check
  citations against source — three claims in this analysis have already been
  corrected by checking, so more are assumed — to re-verify both domain upgrades and
  my own §F.2 reasoning, and to treat a zero-finding audit as a defect of the audit.

- **10:05 — COVERAGE AUDIT: the suite is green and the eval path is untested.**
  Explorer 8 read `test_eval_stats.py`, `test_report.py` and `test_collect.py` in
  full, grepped all 21 modules per behaviour, and **executed the whole suite:
  `pytest tests/unit/kernel_demo/ -q` → 129 passed in 106s.** So "no test covers X"
  is now a demonstrated property of a green suite, not an inference. This is the
  first end-to-end runtime verification in the analysis.

  **Result: 0 COVERED, 2 PARTIAL, 11 UNCOVERED, 0 CONTRADICTED.**

  **The decisive finding — `run_eval`'s body is never executed.** It is called
  exactly twice in the suite (`test_eval_stats.py:86`, `:101`) and **both calls
  raise before the comparator loop at :3507** — one at the one-shot guard (:3433),
  one at the incomplete-collection refusal (:3492). The comparator loop,
  `r_noop_test`, germination, the lift arithmetic, the frozen grid, the refans and
  all six statistical computations are untested. `run_train` has **zero** tests.
  `test_resume_identity_matches_stored_fan_id` pins only `fan_identity` equality on
  a hand-built record whose fixture sets `host_init_hash="i"` — a fixture value, so
  it neither pins nor contradicts the production `""`.
  **Consequence for the headline finding: severity is unchanged or slightly
  increased.** The lift path is unverified by the harness *and* unverified by the
  suite. Nothing tests the pairing.

  **Two findings the audit produced that nobody had:**
  1. **A source comment asserts test coverage that does not exist.** Line 3418 says
     the tie-break is "the same rule `decide_live` implements and tests pin"; :3571
     calls `decide_live` "the tested owner". Neither `_pi_argmax` nor `_test_argmax`
     appears anywhere in the suite, and the sole `decide_live` test
     (`test_policy.py:59–64`) asserts only window-boundary inclusivity — it never
     exercises `p > 0.5` and never checks which seed is chosen. **Both copies of the
     duplicated rule are untested, and a comment claims otherwise.** A reviewer would
     rely on that comment.
  2. **The whole CLI surface is untested, which collapses four concerns into one
     root cause.** `kernel_demo.main` is never invoked by any test. So the dead
     `--resume-eval`, the unexercised `--void-preregistration`, `eval`-exits-0 and
     untested `--extend` are **one gap with four symptoms**, not four independent
     oversights. Phase functions are tested directly by keyword argument; the gap is
     specifically the CLI boundary.

  **Sharpened:** `test_report.py:102` *does* pin the D6 mixed-manifest refusal — but
  its fixture builds `seed_namespace="eval"` records exclusively, so the suite covers
  precisely the path that works and never the train-namespace hole. That makes it an
  **incomplete guard** rather than an oversight — the more actionable reading.

  **Framing to carry into the final report** (explorer 7 asked to assent before I
  use it): *the certification battery is the best-tested part of the demo — gates 1–6
  each have an executable failing fixture — and the eval path is the least-tested,
  which is the inverse of where the published claim comes from.*

  **Fairness note explorer 8 asked to be carried:** 129 passing tests is genuinely
  good work. "UNCOVERED" marks a boundary the suite does not reach, not sloppiness.
  The suite tests phase functions thoroughly and the CLI not at all — a coherent
  choice, just one with consequences.

  **`plot_alpha_beta` is the next instance of the bug `aa86388` just fixed.** The
  peer session's commit made `plot_tune_curve` distinguish absent → skip, empty
  curve → skip, malformed → refuse. `plot_alpha_beta` still *raises* on a legitimate
  absence (an all-diverged population has no non-empty `alpha_beta_log` — a state the
  kernel names at `_all_arms_diverged`, :2515). Same bug class, one function over,
  and the peer session is still active. **Routing to that session is a decision for
  the user — I do not know which peer owns the sidecar work and will not guess.**

- **10:08** Validator pinged: `temp/validation-catalog.md` still absent after ~45
  minutes. Asked for a status line, told it the catalog has been re-merged twice
  since it started, and invited it to report an incomplete validation honestly
  rather than run silently. Diagrams remain gated behind it.

- **10:20 — FRAMING CORRECTED. Explorer 7 declined to assent and was right.**
  I proposed publishing *"the certification battery is the best-tested part of the
  demo and the eval path is the least-tested."* Explorer 7 refused it and supplied
  the counter-citation: **`test_learning.py:91`**. All six statistical estimators
  have direct tests — they simply live in `test_learning.py`, not in
  `test_eval_stats.py` where a per-file audit looks. Publishing my version would
  have let a reviewer falsify the report with a single line reference.

  **Adopted framing:** *the units are well tested on both sides; the assembly is
  not.* Seam located precisely: `verdict` is tested against a **hand-built results
  dict with hardcoded p-values** (`test_eval_stats.py:61–71`) while the functions
  that compute those p-values are tested in isolation — so
  telemetry → permutation test → p-value → verdict boolean has a **tested head, a
  tested tail and an untested join**. Explorer 8's finding that `run_eval`'s body
  never executes is what makes that join unexercised in *both* layers. Its finding
  is load-bearing for the corrected framing, not discarded by it.

  **Promoted to the most important positive finding in the analysis:**
  `test_learning.py:91` pins the rev 6.1 pre-data amendment *discriminatingly* —
  asserts the two-labels-per-episode `ValueError`, then bounds `0.4 < p < 0.6` on a
  cluster-preserving fixture, the band chosen because a point-level shuffle lands
  near 1/6. **It would fail on a regression to point-level shuffling.** The
  amendment is not merely implemented; it is defended against regression. That
  belongs in the final report beside the gaps. (`sign_flip_pvalue` at
  `test_learning.py:110` is comparably strong — both directions, with a comment
  instructing "do not reseed to green".)

  **Methodological defect found, affects the whole team:** per-file coverage
  auditing under-counts, because one subsystem's estimators are tested in another
  subsystem's test file. Both explorer 7 and explorer 8 nearly missed it. Warned
  explorer 8, whose per-concern rows are most exposed; asked it to re-check by
  behaviour (grep each symbol across all 21 modules) rather than by file. **A false
  UNCOVERED damages this report as much as a false COVERED.**

  **Coordinator ran the suite to settle explorer 7's load-bearing caveat.** It asked
  whether the 129 green were partly *skip*-green, since the holes it names are
  GPU-only. Measured on this machine: `torch.cuda.is_available()` → **True**;
  `pytest tests/unit/kernel_demo/ -q -rs` → **129 passed in 110s, zero skips** (no
  `s` markers, no skip section). **The green is real.**

  **And that result sharpens the claim against explorer 7's own explanation.** It
  had offered "those paths are expensive or awkward to test" as the reason the holes
  cluster in GPU-only and identity-binding paths. But a GPU is present, the suite
  runs against it, nothing is environment-gated — and `grep -rn "gate8" tests/`
  still returns **no match**. **Gate 8 is not skipped; it is never written.** Same
  for the `--certify` path and `freeze_manifest`'s missing-certificate refusal.
  Untested **by omission, not by environment gating**, on hardware that could
  exercise them today. "Awkward to test" is available for a GPU-less CI matrix; it
  is not available here.

  **Gate-8 coverage row CLOSED as clean NOT COVERED** on explorer 7's read: gate 8
  absent from `test_preflight_gates.py`'s import block (`:6–25`, which lists gates
  1–7 and `dataclass_gates_ok`); CPU skip path (`:2761–2762`) untested;
  `grep -rn "devices\|cuda" tests/` returns exactly one hit — a TF32 assertion at
  `test_determinism.py:17`.
  New finding from the same check: **`concurrency_factor` appears in tests exactly
  once**, as a hardcoded `1.5` inside a fabricated manifest (`test_report.py:85`).
  The reporting layer consumes a number gate 8 would produce, with nothing testing
  that gate 8 produces it — explorer 7's phrase, adopted: *coverage-shaped but not
  coverage.*

- **10:35 — SOCKET ANALYSIS delivered.** `11-simic-shaped-decomposition.md` now
  **1,728 lines**; new **§A.2** (~285 lines) sits between the presence table and the
  module tree, and every absent/partial row points at its socket. The architect
  verified all four of my candidates in source rather than adopting them: **three
  hold, one corrects me.**

  **Momir — coordinator-verified, and it is an exact identification.** I read
  `docs/design/05-leyline-contracts.md:102` myself: **`preferred_operator` is
  verbatim on `GrowthIntent`'s forbidden block** (:101–110, alongside
  `preferred_topology_family`, `suggested_envelope`, `suggested_ancestor`,
  `rank_hint`, `width_hint`, `deficit_type`, `recommended_mechanism`,
  `expected_internal_structure`, `free_form_designer_message`). So the demo's Momir
  socket is fed by **literally the field INV-09 declares schema-invalid** — a direct
  identification, not an analogy. The cleanest demo-vs-Simic statement in the
  document.
  Outbound side: `SeedDelta` (:638) fixes the entire contract in the abstract base —
  `gain = nn.Parameter(torch.zeros(()))` (:643), `f()` raises `NotImplementedError`
  (:645–646), `forward(h) = self.gain * self.f(h)` (:648–649). With explorer 3's
  execution-verified shape contract, **the demo contains a complete, tested output
  contract for a component that does not exist yet** — the most reusable artifact
  the exercise produced.
  Structural consequence for Phase A: with a fixed menu, *designing* and *selecting*
  collapse — choosing IS designing. Filling the socket splits them, and **a
  fixed-width `Linear(d, 4)` over `SEED_NAMES` does not survive the split.** The
  WHEN head survives; everything downstream of the WHICH head is rebuilt.

  **Urabrask — THIS CORRECTS ME, and the correction is better than my guess.** I had
  offered "may genuinely have no socket". Verified at `:905–913`: the tuple ends
  `"torch.compile (D10: compiled kernels void deterministic-algorithm guarantees)"`,
  with `"enabling AMP"` three lines above. **The socket exists and the demo welds it
  shut with the reason inline.** Reframed: INV-21 exists *because* a compile step is
  precisely what threatens the bitwise-replay contract the demo protects by banning
  it. Caveat retained — the weld is prose, since `FORBIDDEN_RELAXATIONS` is
  deliberately not a `semantic_const` (:901–903) and selftest step 1 asserts nothing.

  **Elesh** — confirmed, and made precise: **magnitude** axis occupied *and verified*
  (gate 5, :2687, which treats no-measurement as explicit failure at :2702–2703);
  **structural** axis empty — no graph to canonicalise, and `canonical_semantic_hash`
  has no analogue because the demo hashes runs and source text, never a design.

  **Ugin** — alignment confirmed against the filigree issue body: `simic-76gg` asks
  for "randomised within declared bounds on a seed… keep it forever as the null",
  and `draw_schedule` (:2313) already is that. **But the demo also instantiates the
  failure the issue warns about**: `cfg.window` is frozen so the *draw* varies while
  the *envelope* never does, and the `Policy` consumes `TELEMETRY_DIM = 20` features
  with **no envelope input at all, not even a constant one** — no slot in the
  feature space for an allocation to occupy. Genuine amendment to that issue, backed
  by live evidence: *vary it **and** give the actor a field to read it in.*

  **Emrakul** — holds. `Stage` (:769) ends at `FOSSILIZED`; `epoch_tick` sets α=β=1
  and stops. INV-33's hysteresis band governs admit↔retain and the demo has **no
  retain decision at all**, so the band has zero exercise. Note: `cosine_ease` is
  symmetric and stage-machine-driven, so a descent path is one enum member and one
  branch away — **what is missing is the authority and its warrant, not the
  mechanism.**

  ### A tool-failure report that turned out to be operator error

  The architect reported, under the dogfooding rule, that `filigree issue get
  simic-76fc6e6618` "returned empty output with exit 0 — no error, no row" while the
  MCP path worked, and flagged a CLI/MCP discrepancy. **I could not reproduce it and
  then found why.** Measured without a pipe masking the exit status:
  - `filigree issue get …` → **exit 2**, with `No such command 'issue'. (Did you mean
    one of: 'get-issue', 'list-issues'?)`
  - `filigree get-issue …` → **exit 0**, 1,640 bytes, the full correct record.

  **There is no discrepancy. Filigree behaved correctly** — errored loudly, exited
  non-zero, suggested the right command. The subcommand form is `get-issue`. The
  "exit 0" came from a pipeline reporting the exit status of the last command in the
  pipe rather than filigree's — **I made the identical mistake on my first attempt**
  and only caught it by re-running without the pipe.
  Retraction requested from the architect. The instinct to flag tool misbehaviour is
  right and must be kept; but **a false tool-bug report is worse than none** — it
  sends someone to debug working software. Recording the failure mode for the team:
  *never measure a CLI's exit status through a pipe.*

- **10:50 — A FALSE STALENESS CLAIM, caught and killed before it spread.** The
  architect's §Gaps.5 asserted `experiments/kernel_demo.py` "is *also* shown modified
  in the working tree" and generalised that inherited citations may have drifted. It
  told the reviewer to spot-check accordingly. **The premise is false.** Measured:
  - `git status --porcelain` → three **untracked** entries only
    (`docs/arch-analysis-2026-08-10-0659/`, `runs/`, `scripts/`). **Zero modified.**
  - `git diff --stat HEAD -- experiments/kernel_demo.py` → **empty**.
  - mtime **06:51:12**, unchanged since before the analysis began; HEAD `aa86388`.

  Almost certainly it saw `M experiments/kernel_demo_plots.py` — the sidecar, which
  genuinely did move — and read it as the main file. **`kernel_demo.py` is
  byte-stable**, now verified three separate times, so 4,066 of 4,216 lines and 8 of
  9 catalog entries rest on a fixed artifact. Left uncorrected, this would have sent
  the reviewer hunting drift that never happened and cast doubt on the most solid
  evidence in the analysis. Corrected to both agents.
  The honest core of the architect's point survives: it inherited a catalog snapshot
  and never re-checked against HEAD. Real methodological lesson — it just applied to
  exactly one file.

  **Also corrected: the architect warned that the catalog's sidecar entry "will
  mislead the next reader". That was already fixed at 07:34**, when explorer 8
  rewrote it against `aa86388`. The architect read the catalog before that re-merge.
  Reviewer told to read the current 911-line version.

  **Convergent independent finding, worth noting as a positive about the process:**
  the architect and the contract-reviewer *independently* discovered the document's
  §E.7 was stale, from different directions — the architect by following a
  `manifest_hash` citation into the sidecar, the reviewer by auditing the header's
  line count. Neither knew the other had found it. Two independent detections of the
  same defect is the strongest evidence yet that the cross-checking discipline works.

  **The reviewer pinned its audit target** (`/tmp/audit-pin.md`, sha256 659bb8bc…,
  1,856 lines, 07:49:49) because the document grew 1,415 → 1,760 → 1,856 lines
  underneath it. Correct call, and it stated the pin rather than silently auditing a
  moving file — the discipline I failed to apply to the repo itself at 06:59.

  **Architect's `manifest_hash` occurrence audit ADOPTED — it strengthens my §F.2
  ruling.** It found `manifest_hash` is compared in exactly three places
  (`run_replay` :3953–3954, `run_report`'s D6 refusal :3834–3839, sidecar :150–152),
  **all wanting a run identity, all surviving the split unchanged.** That converts my
  "the split cannot weaken the property" into the stronger "the split leaves every
  genuine consumer intact while creating the stable key `run_train` currently lacks."
  F.2 upgraded to High; "most likely to be wrong" flag withdrawn.

- **10:52 — Explorer 7 withdrew its own explanation and measured the replacement.**
  It accepted that "expensive or awkward to test" cannot survive a green, zero-skip
  suite on a CUDA machine — then refused to trade one hand-wave for another and
  **measured the uncovered paths**:
  - `gate8_pressure(cfg, None, "cpu", worker_count=6)` → `ok=True,
    reason="skipped (GPU-only)"` in **18 microseconds**. It passed `data=None`
    deliberately: the device check at :2761–2762 precedes every use, so the early
    return never dereferences it. **A test of the exact mechanism behind the
    CPU-freeze hole costs microseconds and needs no fixture.**
  - `freeze_manifest` missing-certificate refusal → `RuntimeError` in **0.5 ms**,
    shape-identical to the three freeze-refusal tests that already exist
    (:253, :262, :270). **It is the fourth sibling of a family where three were
    written.**

  **Sharper finding, adopted:** *the untested paths are where cost is absent, not
  where it is concentrated.* Three of the four gaps are the cheapest code in the
  subsystem.

  **Boundary explorer 7 drew, and I am keeping it so the claim survives review:**
  gate 8's *body* genuinely is expensive — the sibling template hardcodes a full
  `load_data` (:2792) under a 300-second deadline (:2803), so a faithful test with
  `worker_count=6` spawns five subprocesses each materialising CIFAR-10 on the GPU,
  plausibly longer than the suite's whole 110 s. **"Expensive" is available for the
  body; it is not available for the skip path, the certificate refusal, or
  `--certify`.** State it as: the expense is a property of how gate 8 is *written* —
  a sibling reusing `_tiny_bundle_for_selftest` would be testable — not of the
  environment.

  **Explorer 7 declined the coverage-instrumentation offer** as redundant, having
  verified explorer 8's finding itself from both call sites (`test_eval_stats.py:83`
  writes `eval_results.json` first → raises at the one-shot guard :3433; `:89` writes
  only `frozen.json` with no records → `train_eps` empty against `required = 300` →
  raises at :3492; `run_eval` imported by no other test). Correct — control flow
  forces it; instrumentation would only confirm.

  **A REPORTING RISK explorer 7 raised that I am acting on.** *"Report reading as a
  takedown — severity Medium, likelihood Moderate, and rising as findings
  accumulate."* It is right. The certification battery is unusually well built: gates
  1–6 have executable failing fixtures, the rev 6.1 amendment has a discriminating
  regression test, the pre-registration chain is tight, blinding is by construction,
  the grouped-statistics wall holds, and the demo satisfies the mandatory-no-op
  invariant. **If the final report lists ten gaps and one positive it will
  misrepresent the artifact.** Directive for the report: positives get space
  proportionate to their strength, not a token paragraph.

  **And the detail that makes `test_learning.py:91` worth promoting is the BAND, not
  the test's existence.** `0.4 < p < 0.6` was chosen because the episode-level null
  has exactly two label assignments (identity → matched 2, swap → matched 0, hence
  p≈0.5) while a point-level shuffle lands near 1/6 under the lexicographic
  tie-break. **The assertion was constructed to discriminate between the two
  schemes.** That is what makes it a regression defence rather than a smoke test, and
  it gets two sentences in the report, not one.

- **11:05 — FRAMING REFINED A THIRD TIME, and this version is the publishable one.**
  Explorer 8's symbol-level re-audit **found two genuine under-counts in its own
  rows** — a self-reported 2-in-16 error rate on a table it had already grepped
  repo-wide for several entries:
  1. **`run_train` row understated coverage.** "Zero tests" was literally true of
     `run_train` but misleading: `train_policy`, the unit it wraps, **is** tested in
     `test_learning.py` including with `frozen_density`, and `measure_fan_density` is
     pinned loud-on-empty (:120). Corrected to: training logic covered, **assembly**
     not — nothing checks that the manifest supplying normalizer and betas is the
     same generation as the records being trained on.
  2. **Its own shared episode machinery was recorded as uncovered; two of three
     functions are tested — in explorer 7's file.** `draw_schedule` pinned
     two-ordered-in-window (`test_preflight_gates.py:133`); `run_refan`'s
     base-divergence-voids-not-crashes path pinned at `:186`. Exactly the cross-file
     under-count warned about.

  **The corrected framing, which supersedes both mine and explorer 7's:** it is *not*
  "units tested, assembly not" uniformly. **One assembly is genuinely
  integration-tested and the other is not.** `run_collect` is executed for real with
  spawned workers (`test_collect.py:75–142`), asserting idempotency, tune-role
  assignment, partial-episode resume without duplicate `fan_id`s, both manifest
  refusals, and the halt-and-report path. **The uncovered rows cluster specifically
  on the eval assembly and the CLI boundary.** Publish that version.

  **Final tally: 1 COVERED, 2 PARTIAL, 1 NOT COVERED (closed), 14 UNCOVERED, 1 N/A.
  Nothing contradicted.** Method recorded in the legend: symbol-level across 21
  modules, not per-file, plus the skip-free confirmation.

  Two new zero-reference findings worth carrying: **`_query_dicts` has no direct
  test** despite being the policy-query helper every comparator *and* the
  agreement/falsifier computation runs through; and **`_recorded_extensions`**, which
  converts extension events into eval's `required` threshold, is untested.
  **`concurrency_factor` added as its own row** — surfaced by `run_report` (:3902),
  appearing in the whole suite exactly once as a hardcoded `1.5` in a fabricated
  manifest (`test_report.py:85`). A test asserts the report *renders* it; nothing
  asserts it is ever *measured*. Same holds weakly for `det_mode_cost`.
  **Method warning, generalised:** the `n_train` row survived only on a near-miss —
  the suite's `n_train` hits are an unrelated `CommonFuture.draw` keyword plus two
  substring matches on "training". **Grep alone would have scored that row COVERED.**

- **11:08 — Architect retracted the filigree claim, with an exemplary post-mortem.**
  Its original invocation was
  `filigree issue get … 2>/dev/null | head -40 || echo "CLI lookup failed"` — two
  self-inflicted faults: `2>/dev/null` discarded the helpful error, and `||` tested
  `head`'s exit status rather than filigree's, so its own fallback never fired. It
  reported the resulting silence as tool misbehaviour. Its words: *"I manufactured
  the symptom and blamed the tool."* **Blast radius zero** — grep confirms the claim
  never entered the document; it existed only in a message to me.
  Lesson recorded, and it generalises: *the dogfooding rule says surface tool
  failures, but a tool-failure claim needs the same evidence standard as any other
  finding — run it clean, no pipes, no stderr suppression, read the actual exit code,
  before reporting.*
  Also accepted: my `run_eval` citation of `:3462` is the `json.loads`; **the `if` is
  at `:3463`**. Substance unaffected; the document uses `:3463` throughout.

- **11:12 — VALIDATOR RESPAWNED. The first one is my failure, not its.** ~80 minutes,
  no output, no reply to a direct status ping. Reviewing the brief I gave it: 9
  entries of contract checking **plus** a full bidirectional dependency matrix
  **plus** evidence-quality review **plus** independently re-verifying my `run_eval`
  adjudication against source **plus** two mid-flight correction messages. That is
  four jobs, one of which (source re-verification) is a large reading task I had
  already assigned to the contract-reviewer. **I overloaded it.**
  `validator-catalog-2` spawned with a deliberately narrow brief: **contract
  compliance and the bidirectional dependency matrix only.** Explicitly told not to
  deep-dive evidence quality, not to re-verify facts against source, and to check the
  Plotting Sidecar entry for form only. Told to write CHECK 1 to disk before starting
  CHECK 2 so partial results survive, and to report an unfinished validation plainly
  rather than run silently.
  Lesson for the log, alongside the missing version anchor: **when a subagent goes
  silent, suspect the brief before suspecting the agent.**

- **11:30 — CONTRACT AUDIT IN. 1 critical, 2 high, 5 medium, 1 low** against 1,905
  lines and ~150 citations. Report at `12-contract-suite-audit.md`. Reviewer's own
  closing assessment, adopted as the final report's register: **"worth fixing, not
  worth distrusting"** — no fabricated mechanism, no invented record, no citation
  pointing at code that does not exist. §A.2, §C.10 as revised, §D.5 and §C.4's
  `Snapshot` treatment called genuinely good contract analysis.

  ## ★ THE HEADLINE FINDING OF THE ENTIRE ANALYSIS — a defect in shipped code

  **The finiteness guard on the live path does not guard the case it was written to
  catch.** Found by the reviewer inside a table of things the codebase does *right*,
  and **confirmed by the coordinator by execution:**

  ```
  decide_live guard   (:1774, logits):        passes = False   ← correctly rejects
  _query_dicts guard  (:3397, post-sigmoid):  passes = True    ← ADMITS IT
  p = 0.0  ->  p > 0.5 = False                ← reads as restraint, lift exactly 0
  ```

  `decide_live` (:1774) tests `torch.isfinite(p_logit).all() and
  torch.isfinite(seed_logits).all()` — on the **logits**. `_query_dicts` (:3397),
  **the function on every live path**, tests `math.isfinite(p)` where
  `p = sigmoid(p_logit)` — and `sigmoid(-inf) == 0.0`, which **is finite**. So a
  policy emitting ±inf logits passes the deployed guard, returns `p = 0.0`,
  `p > 0.5` is False, and the comparator records a non-germination with **lift
  exactly 0**.

  That is verbatim what the guard's own comment at :3398–3399 forbids: *"a non-finite
  checkpoint would silently read as restraint (lift exactly 0) on every query. Loud,
  never that."* **NaN is still caught** (`sigmoid(nan)` is nan); **±inf is not.**

  Significance:
  - **The only finding in the whole analysis that is a defect in shipped code**
    rather than in an analysis artifact. Goes to the author as a code finding.
  - It was hiding in a **satisfactions** table — certified as closed and carried into
    the transplant list of things to keep unchanged. A positive that was not one.
  - It means the two duplicated deployment rules differ **three** ways — window
    guard, finiteness layer, logit-vs-softmax tie-break — not the one previously
    reported, which materially strengthens the case for collapsing them to one
    resolver.
  - It is the exact silent-zero class this codebase defends hardest against
    everywhere else, surviving in the one place the analysis had already ticked off.

  ## Other findings and rulings

  **F-1 (critical) — accepted, routed for rewrite.** `TelemetryRecord` is the
  precursor of the **blinded projection**, not of `TelemetryEnvelope`.
  `05-leyline-contracts.md:49–69` lists `provenance`/`region_id`/`lifecycle_context`/
  `ablated_context` as envelope fields; :75 names per-consumer projections as the
  blinding mechanism; INV-37 constrains **views**, not the envelope. The document's
  own §C.1 table sealed it — four lines after "the identity is not present to be
  ignored" it asks to *add* `observation_id`/`host_state_id`/`snapshot_id`. Adopted
  as written, INV-08's fail-closed reconciliation could not be implemented. The
  demo's single consumer set made envelope and projection **accidentally identical** —
  itself a contract shape worth stating.

  **F-7 — COORDINATOR RULING: no change; the gates are correctly placed.** "Must not
  issue a verdict" **does** narrow to *a verdict on a candidate*. `02-constitution.md`
  :49 names Jin-Gitaxias's anti-pattern as **"The admission judge"**, and :83 makes
  the violation concrete: *"Jin-Gitaxias issued the admission token"*. Gates 1–8 are
  **instrument-validity QA** — can the harness detect anything at all, asked before
  data exists — not candidate adjudication; Isperia's five-boolean verdict at :3313
  is the separate thing. Gate 4 (dominance) is the closest call but asks whether the
  *menu* is degenerate, which is experimental-design QA.

  **F-5 — MY ERROR, not the architect's.** I told it the demo "has already built"
  what filigree `simic-76fc6e6618` asks for, and asked it to carry that framing.
  Refuted: `draw_schedule` schedules the **harness's** branch points, all three call
  sites are collection/refan/grid, and its output never reaches `Policy`
  (`TELEMETRY_DIM = 20`). Same sampling pattern, different role. **I over-read a
  resemblance and turned it into an instruction.** Softened to: the demo contains a
  deterministic seeded draw of the same shape in a different role; the issue's
  allocator is **not** built. The envelope-input half — no slot in the feature space
  for an allocation to occupy — is untouched and remains the valuable finding.

  **F-4 — §E.1's headline grep is false**: `TwinDivergence` **is** at :3637, inside
  the range the section claims it is absent from. Reviewer's verdict is "neither
  pole": mechanism real and every link verified, **authority-collapse framing is
  decoration** — the defect stands without it. Fix the sentence, keep the finding.

  **F-3 — Ugin verdict survives, stated evidence refuted.** `FROZEN_FIELDS` is 35
  fields of which ~6 are grant-shaped; the largest group is gate/verdict thresholds,
  which `StrategicEnvelope` deliberately does *not* inline (it carries
  `admissibility_policy_id`). §A.2.3's relocation of the socket to `draw_schedule` +
  frozen `cfg.window` is sound; the §A table now contradicts it and must reconcile
  on §A.2.3's terms.

  **§F.2 fully vindicated**, with an addition neither the architect nor I stated: the
  split would actually *deliver* a stable policy hash, because `run_preflight` is
  idempotent on the fan set (:2938, :2953) — a re-freeze on the same commit refits
  the same normalizer over the same vectors, and only gate 8's live
  `concurrency_factor` varies, which sits on the evidence side.

  **Reviewer's catalog-staleness recommendation — premise corrected.** It claimed
  `02-subsystem-catalog.md` "still carries the stale entry and has never been
  revalidated". It does not: the entry describes all 433 current lines, cites
  `PlotDataError`/`require_number`, and carries a version anchor. Fair residual — the
  anchor text says "working tree at 07:21, uncommitted-modified over `853e9ef`"
  rather than naming `aa86388`; **content is identical** (`git diff HEAD` empty), so
  it is an imprecise label, not stale content.

  **Domain calls independently confirmed:** Elesh partial ✓ (clause by clause against
  Appendix B :282–285); Momir/Urabrask/Emrakul absent ✓ — the reviewer looked
  specifically for a sedation analogue in the α/β machinery and found none. Sockets
  judged **real, not retrofitted**, with §A.2 called the strongest section in the
  document, and `preferred_operator` at :102 independently re-verified.

- **11:55 — F-8 EXECUTED AND CLOSED, and the result strengthens the headline fix.**
  The reviewer nominated F-8 as the one open finding worth five minutes, since it
  sits in `run_replay` — the tool the whole replay guarantee rests on — rather than
  in the witness layer. I ran it.

  **F-8 is held shut. Verified by reading all five write sites**, not inferred:
  `common_future_hash=""` is written at :2458 (`kind="void_event"`), :2997
  (`kind="preflight_iter"`), :3178 (`kind="extension_event"`), :3453
  (`kind="void_event"`); :2185 writes the sentinel `"selftest"`, not empty. Genuine
  fans write a real hash (:2373, :2402); refans write `future_k.hash` (:2489). Since
  :3957 refuses anything where `rec.kind != "fan"`, **no record reaching the
  fail-open `and` at :3971 can carry an empty hash.**

  **But it is held shut by a filter fourteen lines upstream, not by the check
  itself** — "correct by discipline, not by construction", the analysis's recurring
  theme appearing once more.

  **Two adjacent guards, opposite absence policies.** :3971 is
  `if rec.common_future_hash and ctx.future.hash != rec.common_future_hash` —
  **fail-open** via `and` short-circuit. :3974 is `if live_init != rec.host_init_hash`
  — **unconditional, fail-closed**. Same function, three lines apart, opposite
  treatment of a missing field. Structurally identical to `_finite_points` vs
  `require_number` in the sidecar, and to the two vectorizers in the policy layer.
  **Third independent instance of the same shape.**

  **★ Why this was worth running — it makes the headline fix order-dependent.**
  `policy_run` records write `host_init_hash=""` (:3454, :3606). So the obvious
  remedy for the lift-path gap — widen the replay filter so comparator records
  become replayable — would make **every** `policy_run` replay raise at :3974 with
  *"diverged at SEEDING (host_init_hash differs)"*, when the real problem is that the
  field was never recorded. Fail-closed, but with a **misleading diagnosis**.

  The fix is therefore not "widen the filter" but **record the hash first, then
  widen** — exactly the architect's proposed remedy (hash `noop_ctx.host` at
  construction, store it in place of `""`), with its **ordering** now established as
  load-bearing rather than incidental.

  Recorded against the reviewer's closing methodological point, which is the real
  result: **a static sweep can locate a guard that does not cover its own stated
  case; it cannot tell you whether that matters.** F-2 arrived with reachability
  explicitly disclaimed, and that disclaimer is what prompted me to execute it —
  turning a documentation finding into the only live code defect in the analysis.

- **11:58 — Catalog re-merged (5th, 965 lines).** Explorer 7 revised to 335 lines
  after the 942-line merge. It also made the session's sharpest methodological
  observation, which goes in the final report: **a merge race in an audit workflow
  preferentially drops late-arriving evidence, and late-arriving evidence skews
  positive** — gaps are found early by reading, defences are found late by checking
  whether something is tested. Uncorrected, the cadence biases toward publishing a
  harsher report than the artifact deserves. Same proportionality risk it raised
  earlier, arriving by a mechanical route rather than an editorial one.

  **Explorer 6 propagated the edge convention honestly and it produced a finding:**
  applying it forced `Data, Episodes & Telemetry` to `[call + serialized-shape]`,
  because `_telemetry_vector_from_dict` (:1823–1834) hardcodes the 20 telemetry key
  names *and their order* against `TelemetryRecord`'s field layout. **That edge is
  the vectorizer-twin concern** — leaving it `[call]` would have hidden the finding
  inside the dependency matrix. Its observation belongs in the synthesis: **the
  edge-kind split predicts where this file's silent failures live** — all three of
  its highest-severity concerns sit on `serialized-shape` edges.

- **12:00 — F-2 escape surface completed; the `+inf` direction is worse than the one
  I executed.**

  | Input | `_query_dicts` tests | Caught? | Silent behaviour |
  |---|---|---|---|
  | `p_logit = -inf` | `sigmoid(-inf) = 0.0` | **No** | never germinates → lift exactly 0 every episode |
  | `p_logit = +inf` | `sigmoid(+inf) = 1.0` | **No** | **germinates every episode** at the window's first epoch |
  | `p_logit = nan` | `sigmoid(nan) = nan` | Yes | — |
  | `seed_logits` has `-inf` | softmax → 0.0, all finite | **No** | that seed silently unselectable |
  | `seed_logits` has `+inf` | softmax → nan | Yes | — |

  Only the `-inf` row was executed; the rest is arithmetic. **The always-germinate
  direction is arguably worse**, because it produces a *plausible non-zero lift*
  rather than a suspicious run of zeros. Neither is distinguishable in the record:
  `decisions` (:3588) stores post-sigmoid `p`, never the logit.

  **Sequencing consequence that matters to the owner:** `config_hash` covers source
  text, so patching `_query_dicts` invalidates every recorded hash and makes
  `run_train` refuse (:3343). **That argues for patching now, pre-data, not later** —
  no store exists yet, so the change is free today and expensive after collection
  starts. Same reasoning the owner applied to the rev 6.1 pre-data amendment.
