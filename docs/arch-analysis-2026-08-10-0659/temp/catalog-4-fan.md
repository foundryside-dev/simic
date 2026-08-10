## Counterfactual Fan Executor

**Location:** `experiments/kernel_demo.py` (lines 1142–1419)

**Responsibility:** Runs the demo's scientific core — from one snapshot of a single
base training pass, it re-materialises N independent arms (a measured no-op plus each
candidate seed) over identical future data, verifies bitwise that the arms are genuinely
matched, and reduces each arm's validation curve to a scalar reward.

**Key Components:**
- `Snapshot` (line 1142) - dataclass capturing exactly five fields: `host_state`
  (full `state_dict`, params + BN buffers), `opt_state`, `cpu_rng`, `cuda_rng`,
  `epoch`. Comment (1143–1146) states the invariant that makes this sufficient:
  snapshots are taken only on the base path, where the optimizer is always the
  never-germinated 2-group state, and there is deliberately no `restore_snapshot`.
- `take_snapshot` (line 1155) - clones host state (`.detach().clone()`, 1158),
  `copy.deepcopy`s optimizer state (1159), captures global CPU RNG (1160) and the
  device-specific CUDA RNG only when the device is CUDA (1161). `epoch` is derived
  as `len(ctx.telemetry)` (1162), not passed in.
- `germinate` (line 1167) - the single sanctioned influence-raising path. Refuses
  unless the slot is `DORMANT` (1169–1173, guarding against duplicate optimizer param
  groups and a silently orphaned seed); builds the seed under
  `derive(episode_seed, "arm", seed_name)` (1174); measures host features under
  `host.eval()` + `no_grad` with a *fixed* val batch (1176–1180) so tau calibration
  cannot touch host BN statistics; runs `tau_init`, appends the seed's optimizer
  groups, sets `Stage.TRAINING` directly (GERMINATED is zero-duration, 1184).
  Returns the tau gain `g`.
- `end_state_R` (line 1189) - reward = arithmetic mean of the **last three** curve
  entries (1192), i.e. a 3-epoch trailing window, not a single end-state value.
  Hard-fails with `ValueError` if the curve has fewer than 3 entries (1190–1191).
- `TwinDivergence` (line 1196) - harness-integrity exception carrying
  `first_bad_epoch` in **absolute** episode epoch numbering, not an offset from
  `snap.epoch` (1198–1201). Registered as non-semantic (1204).
- `ArmResult` (line 1209) - per-arm result: status, `r_val`/`r_test`, curves,
  `init_seed` provenance, `g_at_init`, `rms_ratio_blend_entry`,
  `hash_after_training` (every arm), `host_hashes` (noop/nullseed only, 1220),
  `alpha_beta_log`.
- `BaseTrace` (line 1226) - base-pass result carrying `host_hashes`, curves,
  `snapshots` keyed by fan epoch (1230), status and `diverged_at`.
- `_run_span` (line 1236) - THE inner epoch loop, deliberately the single
  implementation shared by base and arms so "base/twin drift is structurally
  impossible" (1243–1245). Snapshots are taken *before* the fan epoch trains
  (1252–1253), which is what aligns an arm's hash list with
  `base.host_hashes[snap.epoch:]`. Catches `TelemetryDivergence` and converts it to
  `status="diverged"` + `diverged_at` (1256–1259).
- `run_base` (line 1268) - one pass over `range(0, horizon)` collecting per-epoch
  host hashes and the scheduled snapshots (1273).
- `run_arm` (line 1285) - "arm-local materialization" (1296–1297): builds a **fresh**
  `Host` (1298), re-attaches stat hooks (1299), `load_state_dict` from the snapshot
  (1300), fresh `Slot` (1301), fresh 2-group optimizer (1302), then loads a
  `deepcopy` of the optimizer state (1306), then restores global CPU/CUDA RNG
  (1307–1309). Dispatches on `arm_name` into seed / `nullseed` / `noop` (1326–1338).
- `run_fan` (line 1367) - orchestrates the fan: twin first (1381), twin hash
  comparison against the base tail (1382–1388), then each seed arm (1391–1392), then
  the cross-arm post-TRAINING bitwise check (1396–1400), then the optional null-seed
  arm with its hard-stop value-exactness check (1401–1415).

**Dependencies:**
- Inbound: Run Orchestration & CLI (calls `run_base` :2343, `run_fan` :2355 and
  :3980, and calls `germinate`/`end_state_R` directly on the eval-comparator path
  :3576/:3581); Certification Battery (`run_fan` :2108, `run_arm` :2472,
  `run_base` :2773, `take_snapshot` :2468, catches `TwinDivergence` :2942, and
  reads serialized `ArmResult` field names at :2511/:2517); Policy & Learning
  (reads serialized `ArmResult` field names via `rec.arms` :1845); Plotting
  Sidecar (imports `end_state_R` :1189 and reads the serialized `ArmResult`
  fields `curve_val`, `alpha_beta_log`, `rms_ratio_blend_entry`, `status`).
  Records & Store is **not** a consumer and takes no edge in either direction: it
  carries arms only as an opaque `list[dict[str, object]]` — field declaration
  :1451, parameter :1491, assignment :1525 — and reads no `ArmResult` field name
  anywhere in 1420–1681 (verified by field-name grep over that range).
- Outbound: Identity, Config & Determinism Spine (`derive` :1174/:1298/:1357,
  `state_hash` :1260, `Config` :1268, `@semantic` registration); Data, Episodes &
  Telemetry (`EpisodeCtx` :1310, `CommonFuture` :1291, `train_one_epoch` :1255,
  `TelemetryDivergence` :1256, `DataBundle` :1286, `normalize_u8` :1178); Host,
  Seeds & Slot Lifecycle (`build_host` :1298, `build_seed` :1174, `tau_init` :1181,
  `Slot` :1301, `build_optimizer` :1302, `append_seed_group` :1182, `Stage` :1169,
  `SEED_NAMES` :1326).

**Patterns Observed:**
- **Rebuild-not-restore.** No `restore_snapshot` exists (1145–1146). Every arm is
  constructed fresh and loaded from snapshot *values*, so cross-arm state leakage is
  prevented by construction rather than by discipline (1296–1297). Verified: the
  snapshot's own tensors are protected — host tensors were cloned at capture (1158)
  and `load_state_dict` copies into the destination, and the optimizer state is
  `deepcopy`d again at load (1306) so in-place momentum updates cannot reach `snap`
  (comment 1305).
- **Common random numbers enforced by data structure, not by re-seeding.** `future`
  is a `CommonFuture` of *precomputed* tensors drawn once per episode
  (`CommonFuture.draw`, :316–328, called at :1020) and passed by reference into every
  arm (1291 → 1316). `train_one_epoch` indexes it by **absolute** epoch —
  `ctx.future.order[epoch]` (:1060), `crops[epoch, s]`, `flips[epoch, s]` (:1069) —
  and arms iterate `range(snap.epoch, horizon)` (1251, 1339). Arm epoch *e*
  therefore consumes byte-identical batch order, crops and flips as base epoch *e*.
  There is no sampler to desynchronise, which is why "dataloader position" is absent
  from `Snapshot` without being a gap.
- **Arm identity is isolated from the shared RNG stream.** All arms restore the
  *same* `snap.cpu_rng` (1307) — the per-arm seed is **not** re-derived from arm
  identity for the global stream. Arm identity enters only via
  `derive(episode_seed, "arm", seed_name)` (1174) handed to `build_seed`, which
  constructs under `rng_scope(make_generator(...))` (:730). `rng_scope` (:123–133)
  saves and restores the process-global state, so a seed class drawing more
  parameters than another cannot shift the shared stream. This is the mechanism that
  makes the cross-arm bitwise assertion at 1398–1400 achievable at all.
- **The no-op is a real measured arm, not an assumed zero.** `run_fan` executes
  `"noop"` through the identical `run_arm` → `_run_span` → `train_one_epoch` path
  (1381), its reward comes from `end_state_R(ctx.curves_val)` (1341), and it is the
  first element of the returned `arms` list (1390). It is measured *and* doubles as
  the harness twin.
- **Twin-first ordering as an economic guard.** The twin runs before any seed arm so
  a broken harness fails the fan before compute is spent (1379–1380).
- **Three graded integrity instruments, deliberately differentiated.** (a) Twin hash
  equality vs the base tail → `TwinDivergence` (1384–1388); (b) cross-arm
  post-TRAINING host-hash equality → bare `assert` (1398–1400); (c) null-seed exact
  reproduction of the base, *including mirroring a base divergence at the same
  epoch* → unconditional `RuntimeError` with an explicit "no weaker fallback, curves
  are never a comparand" comment (1404–1414).
- **Failure is typed and non-collapsing.** A telemetry failure inside an arm becomes
  `status="diverged"` + the sentinel `cfg.diverged_r` (1343–1345), which is a
  *result*; a harness failure becomes an exception that aborts the fan. The null-seed
  comment (1407–1409) explicitly forbids downgrading instrument failure into an
  ordinary diverged-arm record.
- **Provenance names the stream actually drawn from.** `init_seed` for the
  `nullseed` arm records `conv_light`'s derivation, not a fictional `"nullseed"`
  stream, because that is the generator the module was really built from
  (1354–1357).
- **Zero-normalized hashing is load-bearing here.** During TRAINING the slot returns
  `h + (delta - delta.detach())` (:819). For finite `h` this is value-identical but
  maps `-0.0 → +0.0`, so the arms' hosts are bitwise-equal only under
  `state_hash`'s zero normalization (:934–940, "D8"). The fan's value-exactness
  assertions depend on that normalization existing.
- **Constant LR removes a whole snapshot field.** `build_optimizer`'s comment
  (:874–878) records that constant LR is load-bearing twice — no scheduler state to
  snapshot, and no positional `base_lrs` mismatch when a group is appended at
  germination. Verified: `Snapshot` carries no scheduler state and none is needed.
- **Optimizer group ordering is a matching invariant.** Seed groups are *appended*
  as groups 2/3 (:892–896) after the 2-group host state is loaded (1303–1306), so
  host groups 0/1 keep identical identity and iteration order across every arm.

**Concerns:**
- **The cross-arm value-exactness check is a bare `assert` and silently no-ops near
  the horizon.** Line 1400 uses `assert`, which is stripped under `python -O` —
  unlike the null-seed check (1411) which correctly raises. Worse, the loop at
  1398–1400 is guarded by `twin_hash_at is not None` and
  `a.hash_after_training is not None`; when `snap.epoch + cfg.stage_k - 1 >= horizon`
  (1339, 1396–1397) both are `None` and the demo's central matching assertion
  degrades to nothing with no log, no counter, and no record field. Under the shipped
  `Config` (`window=(5,15)`, `stage_k=3`, `horizon=40`, :142–146) this cannot fire,
  so the defect is latent — but the check's own coverage is not asserted anywhere.
- **`end_state_R`'s ≥3-entry precondition is a cross-field Config coupling that is
  never validated.** Line 1191 raises an uncaught `ValueError` (it is not a
  `TelemetryDivergence`, so `_run_span` will not convert it to a diverged arm) if
  `horizon - snap.epoch < 3`. That invariant is `cfg.window[1] + 3 <= cfg.horizon`,
  and nothing in `Config` (:136–175) or `draw_schedule` (:2307–2315) enforces it. The
  gate-battery config at :2767 (`horizon=4`, `fan_epochs=(1,)`) sits exactly on the
  boundary at span 3.
- **The reward is named "end state" but is a 3-epoch trailing mean** (1189–1192).
  The `noqa` comment explains the *name* comes from the spec but does not flag that
  the implementation is a smoothing window. Any reader reasoning about single-epoch
  end-state semantics will be wrong, and the window width is a hard-coded literal
  `3`/`[-3:]` rather than a `Config` field, so it is invisible to `config_hash`.
- **The eval-comparator path bypasses this subsystem entirely and gets no twin
  check.** `run_eval` (:3507–3588) does not use `Snapshot`/`run_arm`/`run_fan`; it
  builds two independent episodes from the same `episode_seed` (`noop_ctx` :3512,
  `ctx` :3542) and computes `lift = r_test - r_noop_test` (:3587) across them. The
  matching there is *matched-from-birth by seed determinism* rather than
  *matched-from-snapshot*, and — unlike every fan — it is asserted by construction
  and never measured: no hash comparison verifies that the two runs agree on their
  shared pre-germination prefix. The headline lift number therefore rests on a
  weaker guarantee than the fan records do. (Code is outside this range; the
  contract it weakens is this subsystem's.)
- **`ArmResult` crosses into persistence as an untyped `dict` with two different
  shapes.** `make_fan_record` accepts `arms: list[dict[str, object]]` (:1491);
  producers use `dataclasses.asdict` (:2376, :2492) but other sites hand-build
  partial arm dicts with only `name`/`status`/`r_val`/`r_test` (:2188, :3608).
  Consumers index `rec.arms` by key (:1845, :2511, :2517), so the full and partial
  shapes must be tolerated by every reader — a silent-default hazard at exactly the
  boundary the codebase elsewhere defends hardest.
- **In-process arm parallelism would break matching silently.** `torch.set_rng_state`
  (1307) mutates *process*-global state; correctness depends entirely on `run_fan`
  running arms strictly sequentially (1381, 1391–1392, 1402). This constraint is not
  stated in a comment and is not in `FORBIDDEN_RELAXATIONS` (:900–913), which names
  "running fans across devices" but not "running arms concurrently".
- **Snapshot RNG capture covers only torch's CPU and CUDA generators** (1160–1161) —
  not Python's `random` nor NumPy. No draw from either was found on the training path
  (`train_one_epoch` :1058–1137, `augment` :332–343 are torch-only), so this is a
  narrow-but-currently-sound contract rather than an active defect; it is undocumented
  as a contract, so a future `random.` call would break matching without tripping any
  check.
- **`meta` is a bare `dict[str, object]`** (1389, 1415) with keys set only on
  success, so a consumer distinguishes "check passed" from "check not run" only by
  key absence; `run_fan` returns it but the primary caller discards it (`_meta`,
  :2354).

**Confidence:** High - Read lines 1142–1419 in full (the entire assigned range), plus
every symbol it calls: `derive`/`make_generator`/`rng_scope` (:100–133), `Config`
(:136–175), `DataBundle`/`CommonFuture`/`augment` (:252–343), `Host`/`build_host`
(:555–630), `SeedDelta` and the four seed classes/`build_seed`/`tau_init`/
`split_decay_groups` (:637–764), `Stage`/`Slot`/`build_optimizer`/`append_seed_group`
(:768–896), `enable_class1`/`state_hash`/`env_block` (:917–985),
`EpisodeCtx`/`make_episode`/`evaluate_acc`/`train_one_epoch`/`normalize_u8`
(:990–1137). Cross-checked callers by grep for `ArmResult|BaseTrace|end_state_R|
TwinDivergence|Snapshot|germinate|run_fan|run_base|take_snapshot|fan_epochs|
diverged_r|stage_k`, and read the call sites that mattered: `draw_schedule`
(:2307–2315), `make_fan_record`'s signature (:1473–1495), and the eval comparator
(:3490–3599). Every claim about matching was traced to a mechanism rather than to a
comment: CRN verified through `CommonFuture.draw` → absolute-epoch indexing at
:1060/:1069; RNG isolation verified through `rng_scope`'s save/restore at :127–133;
snapshot-immunity verified through the clone at :1158 and the deepcopy at :1306;
STE bitwise-equality verified through `Slot.forward`'s detach at :814 and
`trust_region_loss`'s detached denominator at :827. Confidence is High on
mechanism, Medium on the two boundary conditions I could not exercise (the
`end_state_R` span floor and the silently-skipped assert), because both are
runtime-config-dependent and this was static analysis only.

---
