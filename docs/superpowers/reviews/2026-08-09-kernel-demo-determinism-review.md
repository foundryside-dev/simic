# Determinism Review — Kernel Demo ("Simic in 20 minutes")

- **Reviewed by**: `determinism-reviewer` (axiom-determinism-and-replay v1.1.0)
- **Subject**: `docs/superpowers/specs/2026-08-09-kernel-demo-design.md` (rev 2, approved design, pre-implementation)
- **Class reviewed against**: **inferred** — no `01-determinism-class.md` exists. The
  strongest claim in the spec ("Same seed ⇒ same episode", L265–267) reads as Class 1
  (bit-exact) scoped to one machine. Reviewed against that inference.
- **Tier**: **M** (multi-worker, multi-device, single machine; replay artefacts consumed by
  `--train`/`--eval`), with `09-gpu-determinism-config.md` promoted in by the GPU surface.
  Not L — no cross-machine claim is made.
- **Mode**: greenfield-design (spec only; `experiments/kernel_demo.py` does not exist)
- **Scope**: the whole spec. Reviewed as a pedagogical artefact, not as Simic proper.

> **Severities are advisory.** `01-` is absent, so the class against which "class-breaking"
> is judged was inferred from L265–267 rather than declared. If the designer declares a
> weaker class (e.g. Class 2 with a measured ε), several CRITICAL/HIGH findings drop a
> band — but only if the weaker claim is *written down and measured*, which is itself the
> fix for most of them.

## Summary

- Critical: **2**
- High: **7**
- Medium: **6**
- Low: **3**
- Informational: **1**

**Class judgement: mismatched-to-inferred-class, but the mismatch is cheaply closable.**
Class 1 (bit-exact, same host, same GPU SKU, pinned torch/CUDA/cuDNN/driver) is *feasible
here at affordable cost* — the host is ~150k params, the cards are dedicated, and the
deterministic-kernel penalty on a tiny convnet is throughput the demo can absorb. Class 2
with a measured ε is the honest fallback. **Which class to declare is the designer's call**
(`determinism-vs-reproducibility.md`); this review reports that both are reachable and that
the current spec has neither.

---

## Findings

### CRITICAL — "Same seed ⇒ same episode" is false as written on CUDA

- **Channel**: GPU determinism (8) / determinism class (0)
- **Location**: spec L265–267 (`Engineering → Determinism`); consequences land at L169–172
  (arm outcomes `R_a`) and L235–239 (headline lift, fan-winner agreement)
- **Observation**: The spec's determinism bullet enumerates *seeding* (host init, pathology
  draw, data order) and the precomputed common future, then concludes "Same seed ⇒ same
  episode." No framework determinism configuration appears anywhere in the spec. The demo
  trains a CNN on CUDA with PyTorch defaults.
- **Why class-breaking**: Under PyTorch defaults, convolution backward on CUDA may select
  algorithms that accumulate via `atomicAdd(float*)`; float addition is not associative and
  the commit order follows warp scheduling, so gradients differ run-to-run at the same seed
  (`gpu-determinism.md` §"The Five Sources", items 1–3). `CUBLAS_WORKSPACE_CONFIG` is
  unset, which leaves cuBLAS non-deterministic since CUDA 10.2. `torch.backends.cudnn.
  deterministic` defaults `False`. Over a ~40-epoch horizon these differences compound into
  materially different `R_a`. Seeding governs *draws*; it does not govern *kernels*. The
  claim is therefore not merely unproven — it is false on every run.
- **The second-order damage is the one that matters.** The fan's arms are matched on data
  and nothing else. Each arm's `R_a` carries an independent, unnamed, unmeasured
  nondeterminism term. That noise is *inside* the WHICH label (`J = Σ_a π(a|s,NOW)·R_a`,
  L199–201) and inside the WHEN reward (`R_chosen − R_noop`, L206). Pre-flight check 3
  ("fan contrast vs noise", L225–229) measures spread *across episodes* and so cannot
  separate this term from genuine pathology variance. The demo's central economic claim —
  dense, *full-information* labels — is weaker than stated by an amount nobody has measured.
- **Resolving sheet**: `09-gpu-determinism-config.md` items 2 (framework knobs), 3
  (atomic-float audit), 6 (TF32 policy), 8 (run-start assertion); and
  `01-determinism-class.md` items 1–2 (class + equivalence predicate).
- **Classification**: Library default + class downgrade.
- **Suggested action** — pick (a) or (b), and do the control in either case:

  **(a) Pay for Class 1 (recommended as feasible; the choice is yours).** At the very top of
  the file, before `import torch`:

  ```python
  os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"   # must precede CUDA context creation
  ```

  then at run start:

  ```python
  torch.use_deterministic_algorithms(True, warn_only=False)
  torch.backends.cudnn.deterministic = True
  torch.backends.cudnn.benchmark = False
  torch.backends.cuda.matmul.allow_tf32 = False
  torch.backends.cudnn.allow_tf32 = False
  ```

  Read every knob back and abort on mismatch (`09-` item 8) — a config set but not asserted
  is a config that gets lost in a refactor. Then the claim becomes true *and precise*:
  "bitwise-identical on the same GPU SKU, driver, and torch version; no cross-machine claim."

  **Expect `use_deterministic_algorithms(True)` to raise, and treat the raise as
  information, not breakage.** It names the offending op. Flag in advance:
  `scaled_dot_product_attention`'s flash and mem-efficient backward paths are
  nondeterministic, and **`attn` is one of the four seeds** (L101) — the raise will land on
  the demo's most interesting arm. The substitution (force the math backend for the seed's
  attention, or hand-write the single-head attention residual) is a *recorded decision* in
  `09-` item 3, not a surprise on the day.

  **(b) Downgrade the claim honestly.** Replace L265–267 with: *"Episodes are seeded on
  every draw (host init, pathology, data order, arm init); arms are matched on data —
  identical images, identical order. Arm numerics are not bit-matched: GPU kernel
  nondeterminism contributes a measured ±ε to each `R_a`, reported alongside fan density."*
  This is Class 2 with a stated ε and it is a perfectly respectable claim for a demo — but
  ε must be a number, not a hedge (`determinism-vs-reproducibility.md`, "Class 3 without
  numbers is a vibe" — the same applies to an unquantified Class 2).

  **Define ε once, in one place.** Under (b) this number is load-bearing for every claim the
  demo makes, so it needs a definition rather than a per-plot recomputation: *ε is the pooled
  spread of the duplicate no-op pair over the ~30-episode pre-flight run (L216), stated as a
  single number in `01-`, and re-measured whenever the `env` block changes.* Everything
  downstream — fan density (L228), the test vector, the replay comparison — cites that one
  number rather than deriving its own.

  **The control, required under both (a) and (b) — run the no-op arm twice.** Make the fan
  six arms: `{chosen, other×3, no-op, no-op′}`. The spread between the two identical no-op
  arms *is* the fan's noise floor, measured on every single fan, for the cost of one extra
  arm. Under (b) it is the ε you must report. Under (a) it is **Property 1 (replay
  equivalence) from `12-property-test-suite.md` embedded in the artefact as a continuous
  assertion**: the duplicate must come back bit-identical, and the run aborts if it does
  not. That single extra arm is the cheapest honesty mechanism in this review — it converts
  the determinism claim from an assertion into a measurement the demo reports about itself.

---

### CRITICAL — The fan record cannot be tied to a reproducible episode

- **Channel**: Replay infrastructure (5) / seed governance (1)
- **Location**: spec L173–174 (fan record contents); L258 (`--collect/--train/--eval/--report`)
- **Observation**: The fan record carries "telemetry context, germination epoch, 5 outcomes,
  arm curves, pathology id." It does not carry the episode seed, the policy checkpoint that
  made the germination decision, the config (horizon, subset flag, hyperparameters), or any
  environment identity (torch / CUDA / cuDNN / driver / GPU SKU / dataset hash).
- **Why class-breaking**: Under any class, the equivalence predicate is over *two runs of
  the same thing*. Nothing in the store identifies "the same thing." A recorded fan cannot
  be re-executed, cannot be checked against a re-run, and cannot be attributed to a code
  version when a result looks wrong. **Why this clears the CRITICAL bar despite being a
  provenance gap rather than a per-run class violation**: the spec names the fan store as
  its own deliverable — "exactly the counterfactual atlas and proven substrate that early
  Momir needs" (L24–26) — so the artifact fails its own stated contract on every run, not
  merely its determinism claim. A table of numbers with no provenance cannot be an atlas.
- **Answering the direct question — "can a fan record be re-executed from the stored
  snapshot?"** No, twice over. There is no *stored* snapshot: step 1 (L162) snapshots into
  memory and the spec never says the snapshot is persisted or retained past the fan's
  completion. And re-running the episode from its seed would *not* reproduce the same fan
  even with the seed recorded, because the germination epoch was chosen by a policy that is
  being trained concurrently — a later policy germinates elsewhere.
- **Resolving sheet**: `06-replay-infrastructure-spec.md` items 1 (replay kinds), 3
  (rehydration validation), 6 (replay vs re-run); `02-seed-governance-spec.md` item on
  recording seeds in the run; `11-canonical-state-encoding.md` item 8 (envelope schema).
- **Classification**: Unspecified channel.
- **Suggested action** — one schema change plus one mode, and it closes three channels at
  once. Add to the fan-record dataclass:

  ```
  schema_version, episode_seed, episode_index, worker_id,
  germination_epoch,            # already present — now load-bearing for replay
  policy_checkpoint_id,         # which policy made the NOW/WHICH call
  config_hash,                  # horizon, subset flag, blend/stage durations, lr, ...
  env: {torch, cuda, cudnn, driver, gpu_sku, dataset_sha256, git_rev}
  ```

  Then add `--replay <fan_id>`: rebuild the episode from `episode_seed`, **force germination
  at the recorded `germination_epoch`** (bypassing the policy entirely), re-run the fan, and
  compare the six arm curves against the record. That is *re-run with a substituted input* —
  the branching-replay surface from `06-`, which is what this system already is. It is
  maybe forty lines and it makes every recorded fan falsifiable. Do not also claim read-only
  replay; the demo does not have it and does not need it (`06-` item 6: declare which).

  **`--replay` must validate the `env` block and refuse — not warn — on mismatch**
  (`06-` item 3, rehydration validation). A cuDNN, driver, or torch difference does not make
  the comparison noisier; it makes it meaningless, because the kernels being compared are
  not the same kernels. `config_hash` and `env` are separate assertions: the first says "same
  experiment", the second says "same machine and libraries". Both must hold before a curve
  comparison means anything.

---

### HIGH — The snapshot enumeration is three items long and misses at least six

- **Channel**: Snapshot strategy (3)
- **Location**: spec L162 — "Snapshot the run state (host weights, optimizer state, data position)."
- **Observation**: Three categories named. `snapshot-strategy.md`'s core principle is that a
  snapshot is defined by what it omits; here the omissions are unenumerated.
- **Why class-breaking**: Each omission makes the five arms start from *different* states
  than the parent run did, which silently breaks the "matched" premise the whole fan rests on.
- **What is missing, concretely**:
  - **RNG state.** Not mentioned at all. Needed: the CPU `torch.Generator`, **the CUDA
    generator for each device in use** (Philox offset is per-device; `torch.cuda.get_rng_state_all()`),
    and any `numpy.random.Generator` / stdlib `random` used for the pathology draw.
    `rng-isolation-patterns.md` §"RNG State as Part of the Snapshot": re-seeding from the
    master at branch time loses mid-run progress and is not the same thing as restoring state.
  - **BatchNorm / normalisation buffers.** One of the four pathologies is *under-normalized*
    (L70) and one seed is `norm` (L99), so the host demonstrably has normalisation layers.
    `running_mean` / `running_var` / `num_batches_tracked` are buffers, not parameters — if
    "host weights" means `model.parameters()` rather than `model.state_dict()`, they are
    lost and every arm restarts from stale statistics.
  - **LR scheduler state** and the epoch counter, if a schedule is used.
  - **AMP `GradScaler` state**, if mixed precision is used (unstated).
  - **Deep-copy semantics.** `state_dict()` returns *references to live tensors*. If five
    arms rehydrate from the same dict, they share and mutate the same storage. This is the
    single most likely implementation bug in the whole design. The spec must say: the
    snapshot is `{k: v.detach().clone() for ...}` and each arm rehydrates via
    `load_state_dict` into a freshly constructed model.
  - **Data position** is fine *given* the precomputed common future (it degenerates to an
    index into a fixed schedule) — say so, so nobody re-derives it from a live iterator.
- **Resolving sheet**: `04-snapshot-strategy.md` items 3 (state enumeration), 4
  (outside-the-snapshot enumeration), 7 (snapshot-equivalence test).
- **Classification**: Unspecified channel.
- **Suggested action**: Replace L162 with a six-row table (domain / RNG-per-device /
  component / schedule / lazy-init / external cursors), each row either "captured at field
  X" or an explicit "N/A because Y". Add the snapshot-equivalence test as a `--selftest`:
  snapshot at epoch t, run N epochs, rehydrate, run N epochs, assert the curves match.
  With the duplicate no-op arm in place, you get this test for free on every fan.

---

### HIGH — Arm initialisation has no stated derivation rule, and the chosen arm's execution path is never declared identical to the counterfactuals'

- **Channel**: RNG isolation (2) / seed governance (1)
- **Location**: spec L169–170 (steps 3–4)
- **Observation**: "Branch into 5 matched arms: chosen seed, the other 3, no-op. Each arm
  runs the automatic lifecycle." Nothing states where the four seed modules' initial
  parameters come from.
- **Why class-breaking**: Two failure shapes, both live:
  1. **Sequential draws from a shared init stream.** If the arms' seed modules are
     initialised by successive draws from one generator, each arm's init depends on *arm
     ordering*, and ordering depends on scheduling. This is the counter-based sub-seed
     anti-pattern from `seed-governance.md` §"The Three Anti-Patterns of Sub-Seed Derivation".
     Re-running the fan with arms in a different order produces different `R_a` — and the
     comparison across arms becomes a comparison across inits as much as across
     architectures.
  2. **Asymmetry between the chosen arm and the counterfactuals.** The plain reading of
     steps 1–4 is that the episode *is* the fan — there is no privileged live run continuing
     alongside; the chosen seed is arm 1 of 5. **That reading is correct and should be kept.
     The finding is that the spec never says it.** If an implementer instead lets the parent
     process continue the chosen arm in place while the four counterfactuals are dispatched
     elsewhere (a natural thing to do with two GPUs), then `R_chosen` and `R_noop` come from
     different execution paths, possibly different devices, and the headline number
     `R_chosen − R_noop` (L206, L235) is confounded by execution path rather than by the
     intervention. That is exactly the confound the mandatory-no-op discipline exists to
     exclude.
- **Resolving sheet**: `03-rng-isolation-spec.md` items 2 (named slots), 3 (ownership);
  `02-seed-governance-spec.md` §"Seed Propagation: Derivation, Not Sharing".
- **Classification**: Unspecified channel (1) + hidden dependency (2).
- **Suggested action**: Add two sentences to the fan section.
  1. *"Each arm's seed module is initialised from `derive(episode_seed, "seed_init",
     arm_name)` — a named per-arm slot, independent of arm ordering and of germination
     epoch."* (The specific rule is contestable; the absence of any rule is not. Deriving
     from arm name *only* — not from `germination_epoch` — has the extra virtue that fans
     germinated at different epochs are not confounded by different inits, which matters
     if the WHEN limitation at L176–180 is ever relaxed.)
  2. *"The chosen arm has no privileged status: all arms, including no-op, are produced by
     one code path from one snapshot, on one device, and the chosen arm is distinguished
     only by a label in the record."*

---

### HIGH — Arms scheduled on different cards are not comparable, and the mechanism is concrete

- **Channel**: Floating point (7) / GPU (8)
- **Location**: spec L268–270 (both 4060 Tis dedicated; several concurrent workers per card)
- **Observation**: The spec places workers on both GPUs but never says whether the five arms
  of a single fan stay on one device.
- **Why class-breaking**: Two identical SKUs is the *good* case — but not a safe one here.
  cuDNN's heuristic algorithm selection is **workspace-size dependent**, and free VRAM on
  the two cards differs at any instant because other episode workers are resident and at
  different lifecycle stages. So the same convolution can select a different algorithm on
  card 0 than on card 1 *at the same moment on identical hardware*, producing different
  bits. Under (a) above this is largely closed by `cudnn.deterministic = True`; under (b) it
  adds an unmeasured cross-device term to arm-to-arm comparisons — which are the demo's
  entire output.
- **Resolving sheet**: `09-gpu-determinism-config.md` item 7 (cross-device policy);
  `08-floating-point-policy.md` items 8–9 (tolerance ε, hash policy).
- **Classification**: Single-machine determinism (here: single-*device* determinism).
- **Suggested action**: **Pin all arms of one fan to one device.** This costs nothing — the
  spec already parallelises at *episode* granularity (L269–270: "several concurrent episode
  workers per card"), so a fan never needed to straddle cards. Record `device_index` in the
  fan record. If you later want the cross-card term as a number, run the duplicate no-op
  arm on the *other* card in a diagnostic mode and read the spread directly.

---

### HIGH — Optimizer-state rehydration across arms with different parameter sets is unspecified

- **Channel**: Snapshot strategy (3)
- **Location**: spec L162 ("optimizer state"), against L169 (arms differ in architecture) and
  L118–126 (TRAINING trains Δ at effective α=1, then FOSSILIZED trains it as host tissue)
- **Observation**: The snapshot captures the parent's optimizer state over the host's
  parameters. Four of the five arms then add a seed module with 0.1k–60k new parameters
  (L99–102) that the parent optimizer never saw; the no-op arm adds none.
- **Why class-breaking**: `torch.optim.Optimizer.state_dict()` keys its state by *parameter
  index within param_groups*, not by name. Loading a host-only state dict into an optimizer
  constructed over host + seed parameters either raises on a size mismatch or — worse —
  silently misaligns Adam moments onto the wrong tensors. Getting this wrong makes the four
  seeded arms differ from the no-op arm in a way that has nothing to do with the seeds:
  every host parameter carries corrupted momentum. `R_chosen − R_noop` would then measure
  the bug.
- **Resolving sheet**: `04-snapshot-strategy.md` items 3 and 5 (state enumeration,
  re-derivation rules); `snapshot-strategy.md` §"What's Easy to Forget" ("Optimiser state").
- **Classification**: Unspecified channel.
- **Suggested action**: State the restore rule explicitly: *"Each arm constructs its
  optimizer over host parameters in the parent's exact order, loads the parent's optimizer
  state into that group, then adds the seed's parameters as a **second param group** with
  fresh (zero) moment state and `step=0`. The no-op arm has one group. Host-parameter
  optimizer state is therefore bit-identical across all arms at the branch point."* Assert
  it: on the duplicate no-op arm, the two optimizers must hash equal after restore.

---

### HIGH — Learner-side RNG is entirely ungoverned; `--train` is not reproducible and cannot be tested

- **Channel**: Seed governance (1) / RNG isolation (2)
- **Location**: spec L195–213 (`Learning: offline-online split`), against L265 (the seeding
  enumeration covers only "host init, pathology draw, data order")
- **Observation**: Episode reproducibility and *learner* reproducibility are separate
  surfaces, and only the first is addressed. The learner has at least four RNG-bearing
  components, none named: policy-network initialisation; REINFORCE action sampling for the
  NOW/WAIT head (L205–206); the entropy term; and minibatch draws over the accumulated fan
  store for the offline WHICH objective (L197–204).
- **Why class-breaking**: The demo's success criteria (L278–283 — lift above random,
  fan-winner agreement above chance, a diagonal money chart) are all properties of the
  *trained policy*. Nothing in the spec would let anyone re-produce a specific trained
  policy, and the interference guard at L207–210 ("assert the NOW head's outputs actually
  move") is a diagnostic that cannot be reproduced when it fires.
- **Resolving sheet**: `03-rng-isolation-spec.md` items 2 (named slots) and 3 (ownership
  table); `02-seed-governance-spec.md` item 1 (seeds as inputs).
- **Classification**: Unspecified channel.
- **Suggested action**: Add named slots to the seeding rule: `policy_init`, `policy_sample`,
  `learner_minibatch`, each `derive(run_seed, slot_name)` and each an owned `torch.Generator`
  passed explicitly — never the global. Record `run_seed` and `policy_checkpoint_id`
  alongside every reported metric. Then state plainly whether `--train` is claimed
  reproducible; if the answer is "yes given the same store contents in the same order", that
  answer depends on the next finding.

---

### HIGH — Store write concurrency has no named model and no atomicity rule

- **Channel**: Concurrency (6)
- **Location**: spec L173–174 (append to one JSONL store), L211–213 (multiple workers fill
  one store), L262–264 (free-threading available but "not load-bearing")
- **Observation**: Several concurrent episode workers append fan records to a single JSONL
  file. The spec never says whether workers are **processes or free threads** (3.14t), and
  names no append-atomicity rule.
- **Why it matters**: The store is the demo's sole durable deliverable and the input to
  `--train`, `--eval`, and `--report`. Whether concurrent appends of multi-kilobyte records
  can interleave depends on the writer model, the buffering, and the filesystem — and I
  cannot determine any of the three from the spec. That uncertainty is itself the finding: a
  torn or interleaved line silently drops a fan (or, worse, produces a parseable-but-wrong
  one), and nothing in the design would notice. Under a free-threaded worker model there is
  a second, independent exposure: the *global* `torch` generator is shared mutable state
  across threads, so any code path that draws from it (rather than from an owned
  `Generator`) interleaves draws between arms and episodes non-deterministically.
- **Resolving sheet**: `07-concurrency-determinism-spec.md` items 1 (concurrency model), 2
  (strategy A/B/C), 3 (schedule-sensitive operations).
- **Classification**: Concurrency leak.
- **Suggested action**: Two lines of spec and the question disappears:
  1. *"Episode workers are separate **processes**, one CUDA device each, N per device."*
     (Or free threads — but then every RNG must be an explicitly-passed owned `Generator`
     and that must be stated as a rule, not an intention.)
  2. *"Each worker appends to its own shard, `fans/worker-{k}.jsonl`. Readers glob the shard
     set, **sort the file list**, and merge in canonical `(episode_index, worker_id)` order."*
     Sharding removes the interleaving question entirely rather than reasoning about it, and
     it hands you the next finding's fix for free.

---

### HIGH — Store order is arrival order, so the trained policy — the headline result — is not reproducible

- **Channel**: Concurrency (6) / replay (5)
- **Location**: spec L211–213 ("Multiple episode workers … fill one fan store; the learner
  updates between episode batches") and L197–204 (offline WHICH replays "the whole
  accumulated fan store")
- **Observation**: Records land in the store in completion order, which is a function of
  worker scheduling, GPU contention, and episode length. The learner then iterates that
  store.
- **Why class-breaking**: Even with every episode perfectly seeded and every arm bit-exact,
  two collection runs at the same run seed produce the *same set* of fan records in a
  *different order*. Minibatch composition differs, so the trained policy differs, so the
  headline lift (L235), the fan-winner agreement (L237–239), and the money chart (L240–241)
  differ. This is the classic case where a system is deterministic in the spine and
  non-deterministic at the join, and nobody notices until a result won't reproduce.
- **Resolving sheet**: `07-concurrency-determinism-spec.md` item 3 (schedule-sensitive
  operations — this is the "arrival order" row); `13-cost-of-determinism.md` item 4
  (partial-determinism boundary).
- **Classification**: Concurrency leak.
- **Suggested action**: Make the *store* an unordered set and the *learner's view* canonical.
  Assign episode seeds from a deterministic global schedule (`episode_index → derive(run_seed,
  "episode", i)`) rather than from worker-local counters, record `episode_index` in each fan,
  and have `--train` sort by `episode_index` before batching. Then declare the boundary
  explicitly in the class doc: *"the collection order is nondeterministic; the learner's
  consumption order is canonical; nothing downstream reads collection order."*

---

### MEDIUM — "Common future" matches the data stream but not model-side stochasticity

- **Channel**: RNG isolation (2)
- **Location**: spec L163–168 (precompute batch order and augmentation decisions)
- **Observation**: The precompute covers batch index order and augmentation decisions (crop
  offsets, flip masks). The reasoning at L166–168 is exactly right and is the best
  determinism thinking in the spec. But the matching stops at the data.
- **Why it matters**: If the host contains dropout, stochastic depth, or any other
  train-time stochastic layer, each arm draws its own masks from the model RNG. Two arms
  then differ by *architecture and by regularisation noise*, and "every branch sees literally
  identical images" (L168) becomes a narrower claim than the word "matched" (L169) carries.
  The host's use of dropout is not stated either way, which is why this is Medium and not High.
- **Resolving sheet**: `03-rng-isolation-spec.md` item 2 (named slots); `01-` item 4
  (what the equivalence predicate actually covers).
- **Suggested action**: State the host's stochastic-layer inventory. If there is none, say
  *"the host contains no train-time stochastic layers; the common future is therefore the
  complete shared-input surface"* — one sentence and the claim is airtight. If there is
  dropout, either precompute the masks for the shared pre-slot stages into the common future
  too, or narrow the wording from "matched arms" to "data-matched arms" and name the
  remaining axis.

---

### MEDIUM — No divergence detection and no test vector

- **Channel**: Divergence detection (4)
- **Location**: absent throughout; nearest neighbours are the pre-flight checks (L215–231)
  and the falsifier controls (L242–246)
- **Observation**: The spec has an admirable falsification culture for its *scientific*
  claims (shuffled telemetry, schedule-only baseline) and none at all for its *determinism*
  claim. There is no compare-point, no state hash, no recorded run that future runs must
  reproduce.
- **Why it matters**: Consistency-gate Check 10 — without a test vector, "deterministic" is
  an assertion, not a property. A demo whose thesis is "measure everything against a
  counterfactual" should not exempt its own substrate from measurement.
- **Resolving sheet**: `05-divergence-protocol.md` items on compare-points and localisation;
  `12-property-test-suite.md` Property 1 (replay equivalence) and Property 3 (snapshot
  round-trip).
- **Suggested action**: Three cheap things, all of which you now have the machinery for:
  1. The duplicate no-op arm (CRITICAL #1) — Property 1, continuously, on every fan.
  2. One pinned test vector: a recorded `(episode_seed, git_rev) → six arm curves` checked
     into the repo, re-run by `--selftest`. Under Class 1 assert equality; under Class 2
     assert within the reported ε.
  3. Per-epoch host-state hash (`sha256` over sorted `state_dict` tensors, cast to a fixed
     dtype and byte order) written into the arm curve. Free localisation: when a replay
     diverges you get the epoch, not just the final number.

---

### MEDIUM — Non-finite values will break the JSONL store, and the design specifically wants the runs that produce them

- **Channel**: Canonical encoding (9)
- **Location**: spec L171–172 ("spike-then-crash arms are a headline plot, not a discard"),
  L173–174 (JSONL store), L282–283 (a recorded spike-then-crash plot is a success criterion)
- **Observation**: The spec explicitly commits to retaining diverged arms, and equally
  explicitly stores everything as JSONL.
- **Why it matters**: A crashed arm produces `nan` or `inf` losses. Python's `json.dumps`
  emits bare `NaN` / `Infinity` by default — **not valid JSON**. The store is then readable
  by Python and unreadable by anything stricter, and if a reader is ever swapped the crash
  arms are exactly the records that vanish. The demo would lose its stated headline plot to
  an encoder default.
- **Resolving sheet**: `11-canonical-state-encoding.md` item 8 (envelope schema) and item 7
  (pickle policy, by analogy — the encoder is part of the contract).
- **Suggested action**: `json.dumps(..., allow_nan=False)` and encode non-finite values as
  `null` alongside a per-epoch `finite: false` flag (or as the strings `"nan"`/`"inf"` with a
  documented decoder). Add `schema_version` to the record while you are there. Also state the
  float policy: cast tensors to Python `float` (float64) at the boundary — `float32` widened
  to `float64` round-trips exactly, so the store is lossless and stable.

---

### MEDIUM — The blindness rule covers `pathology_id` but not the other channels that leak into telemetry

- **Channel**: External effects (9) / canonical encoding
- **Location**: spec L77–78 (blindness), L143–148 (`TelemetryRecord` contents)
- **Observation**: The spec's blindness discipline is sharp on `pathology_id` and the
  dataclass discipline ("a missing field is a construction error, never a silent 0.0",
  L143–144) is exactly right. But the *rule* is stated for one field rather than as a class.
- **Why it matters**: The listed fields are all clean. The risk is what gets added later —
  a `wall_time`, an `epoch_duration`, a `device_index`, a `worker_id` for debugging. Any of
  these is (i) nondeterministic, so it breaks episode reproducibility from the input side,
  and (ii) a covert channel the policy can learn from, which the shuffled-telemetry falsifier
  (L243–246) would *not* catch — shuffling preserves epoch index, and a schedule-correlated
  field survives shuffling the same way epoch index does.
- **Resolving sheet**: `10-external-effects-substitution.md` items 1 (inventory) and 5
  (audit procedure).
- **Suggested action**: Generalise the rule at L77: *"A `TelemetryRecord` field must be a
  deterministic function of the host's state and the logical epoch index. Wall-clock,
  durations, device identity, worker identity, and `pathology_id` are all excluded by
  construction — absent from the dataclass, not filtered downstream."* Add the one-line
  grep-based audit (`time.time|monotonic|datetime.now|os.getenv|listdir|glob` outside the
  designated boundary) to `--selftest`; that is `10-` item 5 at the scale a single file
  deserves.

---

### MEDIUM — The freeze discipline has no enforceable seed partition

- **Channel**: Seed governance (1)
- **Location**: spec L79–84
- **Observation**: "Pathology definitions are tuned on development seeds … then **locked
  before headline evaluation**. Headline runs use fresh host initialisations. Retuning after
  seeing evaluation fans is test-set engineering and is not done."
- **Why it matters**: The commitment is exactly the right one and it is currently
  unenforceable — no recorded dev seed range, no eval seed range, no disjointness assertion,
  and no record in the fan of which side of the line it came from. "Is not done" is a promise
  about behaviour; the pack's position is that it should be a property of the seed schedule.
  This is `seed-governance.md` §"Seed Reuse, Seed Sweeps, and the Orchestrator" applied to
  the demo's own methodology.
- **Resolving sheet**: `02-seed-governance-spec.md` item on seed sweeps and the orchestrator.
- **Suggested action**: Partition by construction: `dev` seeds are
  `derive(run_seed, "dev", i)`, `eval` seeds are `derive(run_seed, "eval", i)`, the two
  namespaces cannot collide, every fan records its `seed_namespace`, and `--report` refuses
  to mix namespaces in one headline number. Record the git rev at which the pathology
  definitions were frozen; `--eval` asserts the current rev's pathology block hashes equal.

---

### MEDIUM — Precision policy (TF32) unpinned

- **Channel**: GPU (8)
- **Location**: absent; implied by L268 (4060 Ti = Ada, SM 8.9) and L254 (torch)
- **Observation**: On Ada, `torch.backends.cudnn.allow_tf32` defaults `True` while
  `matmul.allow_tf32` defaults `False`. Neither is stated.
- **Why it matters**: TF32 is not itself a *nondeterminism* source, but it is a silent
  precision choice that (i) sets the numerical noise floor the fan's contrasts must exceed,
  (ii) has changed defaults across torch releases, so an unpinned demo drifts under a routine
  upgrade, and (iii) is invisible in every plot the demo produces.
- **Resolving sheet**: `09-gpu-determinism-config.md` item 6 (TF32 / mixed-precision policy).
- **Suggested action**: Set both flags explicitly (either value — just pick and record it),
  and put the pair in the fan record's `env` block. If the demo uses AMP anywhere, say so
  and record the dtype.

---

### LOW — Environment identity is never pinned or recorded

- **Channel**: GPU (8) / canonical encoding (9)
- **Location**: spec L253–271 (`Engineering`)
- **Observation**: No versions anywhere: torch, torchvision, CUDA, cuDNN, driver, GPU SKU,
  CIFAR-10 provenance.
- **Why it matters**: A cuDNN or driver upgrade changes selected algorithms; a torchvision
  change could alter the CIFAR-10 bytes or normalisation constants. Without the record, a
  future "why doesn't this reproduce" question has no starting point. Low, because the fix
  is subsumed by the CRITICAL #2 `env` block.
- **Resolving sheet**: `09-gpu-determinism-config.md` item 4 (driver and library pinning).
- **Suggested action**: The `env` block from CRITICAL #2, plus a `sha256` of the CIFAR-10
  tensor after load — cheap, and it catches the dev-subset flag (L59–60) silently differing
  between a collection run and a report run.

---

### LOW — No cost record for the determinism knobs

- **Channel**: Cost (cross-cutting)
- **Location**: absent
- **Observation**: The runtime budget at L268–271 ("an episode with its fan is minutes;
  overnight yields high hundreds to thousands of fan records") is stated without reference to
  determinism cost. Deterministic convolution kernels typically cost 10–30%; the sixth
  (duplicate) arm costs a further ~20% of fan wall-clock.
- **Why it matters**: `cost-of-determinism.md`'s central warning is that unrecorded costs get
  relaxed silently under deadline — someone flips `cudnn.benchmark = True` at 2am to make the
  overnight run fit, and the demo's central claim quietly becomes false again with no diff
  that looks like a determinism change.
- **Resolving sheet**: `13-cost-of-determinism.md` items 1 (per-rule cost), 6 (forbidden
  silent relaxations), 7 (budget-breach response).
- **Suggested action**: A five-line block in the file header: measured episodes/hour with
  knobs on vs off (measure it; don't quote my range), the note that `cudnn.benchmark = True`
  / `warn_only=True` / dropping the duplicate arm are **class-breaking, not optimisations**,
  and the pre-agreed response if the overnight budget misses (shorten the horizon or reduce
  worker count — never relax the knobs).

---

### LOW — Persisted snapshots, if any, and directory iteration

- **Channel**: Canonical encoding (9) / concurrency (6)
- **Location**: implied by L162 and by `--report` reading the store (L233)
- **Observation**: Two small hygiene items. If a snapshot is ever persisted for `--replay`,
  `torch.save` is pickle-based (`11-` item 7 bans pickle in the snapshot path for
  cross-machine identity — acceptable for a local demo, but say so rather than inherit it).
  And any `glob` over shard files or plot outputs returns OS-dependent order.
- **Resolving sheet**: `11-canonical-state-encoding.md` item 7;
  `07-concurrency-determinism-spec.md` item 3 (`os.listdir`/`glob` row).
- **Suggested action**: `sorted(glob(...))` everywhere, no exceptions. If snapshots persist,
  note the pickle dependency and that snapshot bytes are not a cross-machine identity.

---

### INFORMATIONAL — The gap between this demo's class and Simic's INV "Academy exact replay"

- **Channel**: Determinism class (0)
- **Location**: spec L6–19 ("What this is — and is not"); `AGENTS.md` non-negotiable
  invariants; `docs/design/02-constitution.md`
- **Observation**: Simic proper carries *Academy exact replay* as a spine invariant —
  identical snapshot + identical future data ⇒ bitwise-identical traces, with non-exact
  profiles carrying **measured** uncertainty. This demo is a rehearsal of exactly that
  machinery: a snapshot, an identical future data stream, matched branches.
- **Why it is informational**: The demo is explicitly not Simic (L15–19), so it is not bound
  by INV-nn. But it will be cited as precedent — the spec says its output "is exactly the
  counterfactual atlas and proven substrate that early Momir needs" (L24–26). If the demo
  ships with an unmeasured non-exact profile, the first thing Simic proper inherits from its
  own kernel demo is the habit the invariant exists to forbid. Note that "measured
  uncertainty" is the invariant's own escape hatch and it is precisely what the duplicate
  no-op arm produces. The demo can satisfy the *spirit* of the invariant at the cost of one
  extra arm, which is a better precedent to set than either silence or full rigour.
- **Resolving sheet**: `01-determinism-class.md` item 6 (reproducibility axis) and item 7
  (class-breaking events).
- **Suggested action**: One line in the file header alongside the existing "this is not
  Simic" caveat, naming the demo's class and its distance from Academy exact replay.

---

## Cross-Channel Patterns

1. **The demo is rigorous on one matching axis and silent on the rest.** The common-future
   precompute (L163–168) is genuinely excellent determinism engineering — it identifies that
   cloning RNG state is insufficient because different architectures consume RNG differently,
   which is a subtle point most designs get wrong. But "matched" then does duty for four
   other axes that were never considered: numerics (CRITICAL #1), arm initialisation (HIGH),
   device (HIGH), and optimizer state (HIGH). **One table headed "what 'matched' means" with
   a row per axis and its treatment closes four findings at once** and is the single highest-
   value edit to the spec's prose.

2. **The fan record was designed as a training label and needs to be a run record.** Its
   current fields (L173–174) are exactly what `--train` consumes and nothing more. The
   replay finding, the seed-audit finding, the environment-pinning finding, the
   store-ordering finding, and the freeze-partition finding all resolve into fields on one
   dataclass. **One schema change closes five findings across four channels.**

3. **Concurrency and scientific reproducibility are the same problem here.** The store is
   both the concurrency hazard and the learner's input, so the fix that makes writes safe
   (per-worker shards) is the same fix that makes the trained policy reproducible (canonical
   merge order). Treating them separately would produce two mechanisms where one suffices.

4. **GPU nondeterminism does not just weaken a claim — it enters the reward.** This is the
   pattern worth carrying to Simic. Every arm's `R_a` carries an independent kernel-noise
   term, so the noise sits *inside* the full-information objective rather than beside it. The
   demo's own pre-flight machinery cannot separate it from pathology variance. A system whose
   thesis is "measure against a counterfactual" needs its counterfactuals to differ by the
   intervention alone; that is a scientific requirement before it is a determinism one.

---

## Confidence Assessment

- **Static-analysis confidence**: Medium-High. Greenfield review of a well-specified design
  with no code to check against; the PyTorch and CUDA behaviours cited (atomic-float conv
  backward, `CUBLAS_WORKSPACE_CONFIG`, cuDNN heuristic/workspace coupling, SDPA backward
  nondeterminism, TF32 defaults on Ada) are documented framework behaviour, but the *degree*
  of resulting drift over 40 epochs on this specific host is an empirical question I have not
  measured. The duplicate-arm control is proposed partly because it answers that question
  directly rather than asking anyone to trust my estimate.
- **Severity-rating confidence**: Low-Medium, and structurally so — `01-` is absent, so the
  class was inferred from one sentence (L265–267). Every severity is conditional on that
  inference. This is why the missing class is finding #1 rather than a footnote.
- **Coverage confidence**: High for the spec as written; all ten channels walked. Necessarily
  low for the implementation, which does not exist — several findings (deep-copy semantics,
  optimizer param-group alignment, JSON encoder defaults) are predictions about the most
  likely implementation of an under-specified step, not observations.
- **Drivers**: Provided — the full spec, the team lead's framing of the concurrency and
  branch-point questions, the pack's thirteen sheets at v1.1.0. Inferred — the determinism
  class, the tier, the worker model, the host's stochastic-layer inventory, whether AMP is
  used. Out of scope — Simic proper's `docs/design/` chapters (referenced only for the
  informational finding), and the lifecycle/RL design (covered by the sibling review at
  `2026-08-09-kernel-demo-lifecycle-review.md`, which I did not read).

## Risk Assessment

- **If unaddressed, what breaks first and how it is observed**: Not a crash — a slow erosion
  of the demo's evidentiary value, in this order. (1) Someone re-runs a headline episode to
  make a plot and gets different arm curves; the natural response is to assume a bug in the
  fan logic and go looking in the wrong place, because the spec promised "same seed ⇒ same
  episode." (2) Fan density (L228) comes in lower than expected and the pre-flight
  prescription ("widen the end-state averaging window or lengthen the horizon", L228–229) is
  applied to a problem that is actually kernel noise — burning hours of GPU time on the wrong
  remedy. (3) A `--train` result cannot be reproduced when someone asks for the money chart
  at a different checkpoint. (4) Latest and worst: the demo's central claim — dense
  *full-information* counterfactual labels — turns out to have carried an unmeasured noise
  term all along, discovered by whoever tries to build Momir on the atlas.
- **Highest-leverage fix for claim honesty**: **the duplicated no-op arm.** Six arms instead
  of five. Under Class 2 it *is* the ε you must report; under Class 1 it is a continuous,
  free assertion that deterministic mode is genuinely in effect (the duplicate must return
  bit-identical, and the run aborts if not) — Property 1 from `12-` embedded permanently in
  the artefact. It also does double duty as the snapshot-equivalence test and the
  optimizer-restore check. Nothing else in this review buys as much per line of code.
- **Highest-leverage fix for replayability**: **the fan-record schema change** (episode_seed,
  policy_checkpoint_id, germination_epoch, config_hash, env block) **plus `--replay <fan_id>`
  forcing germination at the recorded epoch.** One dataclass edit and ~40 lines close the
  replay, seed-audit, environment-pinning, and encoding findings together, and turn the store
  from a table of numbers into the atlas the spec claims it is.
- **Sequence** (each step makes the next cheaper):
  1. Write `01-` — one paragraph naming the class and its predicate. Everything below is
     conditional on it and several findings may re-rate.
  2. Determinism knobs + run-start assertion. Absorb the `use_deterministic_algorithms`
     raises now, while there is no code to refactor — the `attn` seed is where to look first.
  3. Duplicate no-op arm + one-device-per-fan. Now every subsequent change is verified by
     the artefact itself.
  4. Snapshot enumeration + arm-init derivation rule + optimizer param-group rule. The
     duplicate arm from step 3 will catch mistakes in all three.
  5. Fan-record schema + `--replay`.
  6. Worker model + sharded store + canonical merge order + learner RNG slots.
  7. The Medium/Low hygiene items — they are one-liners once the above exists.

## Information Gaps

- **No `01-determinism-class.md` exists.** The class was inferred from L265–267 as Class 1
  scoped to one machine. This is the highest-severity finding and the reason every other
  severity is advisory.
- **Worker model unstated** — processes or free threads (L262–264 says free-threading is
  "available but not load-bearing", which is an intention rather than a decision). The
  concurrency findings are written to hold under either, but the specific mechanisms differ.
- **Host architecture details unavailable** — no stochastic-layer inventory (dropout?), no
  normalisation-layer placement, no AMP/precision statement. The BatchNorm-buffer and
  common-future findings are inferred from the pathology table (L70) and seed table (L99).
- **No code exists.** Deep-copy semantics, optimizer param-group handling, and JSON encoder
  configuration are predictions about the likely implementation of under-specified steps.
- **Runtime characteristics unmeasured** — the deterministic-kernel throughput penalty on
  this host is unknown to me; the cost finding asks for a measurement, not a number.
- **The sibling lifecycle review** (`2026-08-09-kernel-demo-lifecycle-review.md`) was not
  read; if it already covers the STE/blend numerics, findings may overlap.
- **Simic's `docs/design/` chapters** were consulted only via `AGENTS.md` for the
  informational finding on Academy exact replay.

## Caveats

- This review covers the bytes of the spec. Code paths not yet written are not in scope, and
  several findings will resolve differently once the implementation exists.
- **Class choice is a designer responsibility** (`determinism-vs-reproducibility.md`). This
  review reports that Class 1 (single-machine, single-SKU, pinned versions) is *feasible at
  affordable cost here*, and that Class 2 with a measured ε is an honest alternative. It does
  not pick between them. What it does insist on is that one of them be written down — the
  current state, an unqualified "Same seed ⇒ same episode", is neither.
- Severity ratings assume the inferred class. If the designer declares Class 2 with a stated
  ε, CRITICAL #1 becomes a MEDIUM documentation-and-measurement finding — **but only if the ε
  is measured**, which requires the duplicate-arm control either way.
- The demo is a pedagogical artefact, and this review is calibrated to that: where full
  bitwise discipline was not obviously worth it, the recommended fix is an honest weaker
  claim plus a measurement (CRITICAL #1 option (b), MEDIUM findings on divergence and
  matching scope). Where the fix is nearly free (one-device-per-fan, sorted globs, the
  duplicate arm, the record schema), the recommendation is to just do it.
- Live divergences are out of scope; if two runs already disagree, use `replay-debugger`.
- Implementation is out of scope. This report identifies gaps; the designer or
  `/scaffold-replay-system` turns them into spec and code.

## Result Statement (Plain Language)

The demo's determinism thinking is genuinely good in one place and absent everywhere else.
The precomputed common future is the right idea for the right reason — but "matched" then
silently covers four other axes nobody specified, and "Same seed ⇒ same episode" is simply
false on CUDA under PyTorch defaults, in a way that puts unmeasured noise *inside* the
counterfactual reward the whole demo is built to measure. Two changes fix most of it: declare
a class and make it true — either turn on deterministic algorithms, or state *and measure*
the weaker claim — and **run the no-op arm twice in every fan**, where the duplicate is
either the ε you must report or a free, permanent proof that
determinism is on. Separately, the fan record needs to carry its own seed, policy checkpoint,
config and environment, or nothing in the store can ever be re-executed — which matters
because the spec says the store *is* the deliverable to Simic proper.

---

- **Statement signature**: `determinism-reviewer`, axiom-determinism-and-replay v1.1.0
- **Issued at**: 2026-08-09T11:07:26Z
