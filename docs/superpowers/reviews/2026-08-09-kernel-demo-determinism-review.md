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

---

# Round 2 (rev 3)

- **Reviewed by**: `determinism-reviewer` (axiom-determinism-and-replay v1.1.0)
- **Subject**: `docs/superpowers/specs/2026-08-09-kernel-demo-design.md` rev 3 (commit `244accb`)
- **Class reviewed against**: **declared** — rev 3 states Class 1 (single machine, single GPU
  SKU, pinned environment, bitwise). Round 1's severities were advisory against an inferred
  class; **round 2's are not.** There is now a contract to review against.
- **Mode**: spec-update
- **Issued at**: 2026-08-09T11:24:44Z

## Verdict summary

**15 closed · 4 partial · 0 not closed.** Seven new findings, all arising from rev 3's own
changes (free-threaded workers, base-run-as-no-op, refanning). None re-opens a round-1 item.

The response is unusually strong. Three things rev 3 did that go beyond what was asked:
folding the observation normalizer and entropy coefficients into the frozen block; switching
Adam → SGD, which dissolves the optimizer-restore finding rather than patching it; and turning
the duplicate-arm control into the **twin arm**, which verifies more than I proposed. Rev 3
also correctly noticed that under a bitwise contract the duplicate self-agrees trivially, and
re-derived the noise floor from refanning — a consequence I did not anticipate and which is
right (see N3 and the scope note under it).

## Round-1 findings — disposition

| # | Round-1 finding | Verdict | Evidence in rev 3 |
|---|---|---|---|
| C1 | Class absent; "same seed ⇒ same episode" false on CUDA | **CLOSED** | L66–85: Class 1 declared; all four knobs; TF32 off both + recorded; no AMP; **explicit-matmul `attn`** (took the SDPA flag); no dropout; no clipping; claim scoped to the contract and twin-verified rather than asserted |
| C2 | Fan record not replayable | **CLOSED** | L295–315: full schema (`episode_seed`, `config_hash`, `frozen_block_hash`, `common_future_hash`, `env`, per-arm `init_seed`); `--replay` re-derives, forces the recorded `fan_epoch`, **refuses** on env mismatch. Re-derivation instead of persisted snapshots is a better answer than the one I proposed — cheaper and it removes the pickle question entirely |
| H1 | Snapshot enumeration incomplete | **CLOSED** | L259–263: deep-copied `state_dict()` **parameters and buffers**, deep-copied optimizer state, CPU + per-device CUDA RNG, data-stream position; the live-reference trap is called out in the spec text. No scheduler/GradScaler rows needed — fixed LR, no AMP |
| H2 | Arm-init derivation rule unstated | **CLOSED** | L273–275: `derive(episode_seed, arm_name)`, order-independent. Correctly excludes `fan_epoch`, which is what makes L242–243's new within-episode now-vs-later evidence sound: at two fan epochs the same arm gets a *bitwise identical* module, so the comparison isolates timing |
| H3 | Chosen-arm execution path never declared symmetric | **CLOSED** | L264–272 — but by a different mechanism than I proposed; see N-note below, and **the twin arm is load-bearing for this, not decorative** |
| H4 | Arms across cards not comparable | **CLOSED** | L276–279, verbatim with the workspace mechanism |
| H5 | Optimizer restore across differing param sets | **CLOSED, improved** | L191–197: SGD+Nesterov (dissolves the Adam findings), seed params as a second group with fresh momentum, host group ordering byte-identical; plus assertion L280–283 (host weights bitwise identical across arms at end of TRAINING) — a stronger check than I asked for |
| H6 | Learner RNG ungoverned | **PARTIAL** | L81–82 closes training-side (policy init, minibatch order) and REINFORCE's removal deletes the sampling slot from training. **Eval-time action selection is still ungoverned** → N5 |
| H7 | Store writes: no worker model, no atomicity rule | **PARTIAL** | L306–309 per-worker shards close the write-interleaving question completely. L460–461 now *names* the worker model — free-threaded — which resolves the gap and opens N1/N2 |
| H8 | Store order → learner order → policy not reproducible | **CLOSED** | L306–309: canonical merge on `(episode_seed, fan_epoch)`; input order is a function of content. Minor: `policy_run` records need a tiebreak key if they lack `fan_epoch` |
| M1 | Common future covers data, not model stochasticity | **CLOSED** | L79: "No dropout anywhere in host, seeds, or policy" — closed by construction, which is the strongest form |
| M2 | No divergence detection, no test vector | **CLOSED** | Twin arm (L267–272) + `--selftest` (L469–470). Residual is cross-version only → N6 |
| M3 | Non-finite values break JSONL | **CLOSED, extended** | L288–293: `status="diverged"`, `R_a = null`, curves retained, encoder never emits bare `NaN` — and rev 3 went further, reporting per-seed-type failure rates because dropping such fans would flatter the riskiest arms |
| M4 | Blindness rule stated for one field, not as a class | **CLOSED** | L116–121, generalized as recommended, with the `--selftest` grep |
| M5 | Freeze discipline unenforceable | **CLOSED, extended** | L123–131: namespaced `derive(run_seed, ns, i)`, `frozen_block_hash`, `--eval` asserts it; normalizer/entropy/schedule folded into the frozen block |
| M6 | TF32 unpinned | **CLOSED** | L73–74, off for both, explicitly set and recorded |
| L1 | Environment identity unrecorded | **CLOSED** | `env` block, L301–303 |
| L2 | No cost record | **PARTIAL** | L83 records the slowdown measurement. No forbidden-silent-relaxations list → N7 |
| L3 | Pickle / glob hygiene | **CLOSED** | Re-derivation removes persisted snapshots entirely; content-keyed merge is stronger than a sorted glob |
| I1 | Gap to Academy exact replay | **CLOSED** | Class 1 + twin arm makes the demo a *better* precedent for the invariant than I expected — continuous verification, not a one-off assertion |

**Note on H3 (the sharpest point in this round).** Rev 3 closes the chosen-arm asymmetry, but
the compute optimization at L240 reintroduces one in a new place: the base run *is* the no-op
arm, and the base run is **not** executed by the branch executor — it is the ordinary episode
loop. So `R_noop` and the four `R_a` now come from genuinely different code paths. Rev 3
handles this correctly, and elegantly: rather than avoid the asymmetry it **verifies it away**,
because the twin arm re-runs the no-op continuation *through the branch executor* and demands
bitwise equality with the base tail. That is the right trade — it buys ~20% compute back and
converts a structural assumption into a per-fan measurement.

The consequence must be written down: **the twin arm is not optional.** If it is ever put
behind a flag and the flag is off — or dropped under deadline, which is what happens to the
thing that costs 20% of fan compute — the base/branch asymmetry returns *silently* and
`R_chosen − R_noop`, the headline number, is confounded again with no symptom. This belongs
on N7's forbidden-relaxations list, at the top.

## New findings (rev 3 surfaces)

### N1 — HIGH: no RNG ownership rule, and free-threaded workers make one natural implementation silently corrupting

- **Channel**: RNG isolation (2) / concurrency (6)
- **Location**: L460–461 (free-threaded workers), L462 (several workers per card), against
  L259–263 (snapshot captures "CPU and per-device CUDA RNG states") and L273 (`derive(...)`)
- **Observation**: Rev 3 names the worker model but no RNG *ownership* rule. `derive(...)`
  describes how sub-seeds are computed; it does not say what object receives them.
- **Why it matters**: `torch.manual_seed()` sets the process-global CPU generator and every
  device generator. Under free threads that state is shared by every worker in the process.
  Seeding an episode by calling `torch.manual_seed(episode_seed)` — the obvious
  implementation, and the one the current wording invites — means worker A's episode start
  clobbers worker B's stream mid-initialisation.
  **I am not claiming this will happen; I am claiming the spec does not rule it out.** If
  modules are constructed the ordinary way (`nn.Conv2d(...)` reading the global generator
  without reseeding), no corruption occurs. The exposure is specifically the per-episode
  reseed. This is the same discipline as round 1's store finding: the unstated rule is the
  finding.
- **Why it is HIGH rather than MEDIUM — nothing in the design catches it.** The blast radius
  is confined to init-time draws (host init, pathology draw, common-future precompute, arm
  init), because with no dropout and no stochastic layers *nothing downstream of init
  consumes RNG at all*. That narrowness is good news for the spine and bad news for
  detection: a corrupted host init produces a valid-looking episode whose host simply does
  not match its `episode_seed`. The twin arm does **not** catch it (it verifies branch-executor
  equivalence *within* an episode, not that the episode matched its seed). Assertion L280–283
  does not catch it (it compares arms to each other, all downstream of the same corrupt init).
  It surfaces only if someone runs `--replay`, months later, on the one record they happened
  to check.
- **Resolving sheet**: `03-rng-isolation-spec.md` items 2–3 (named slots, ownership table)
  and item 5 (hot-path discipline: hold an owned `Generator`, never a factory call).
- **Suggested action** — the rule, then the detector:
  1. *"Every episode owns explicit `torch.Generator` objects (CPU and one per device it
     touches), seeded by `derive(...)` and passed explicitly to every draw — host init,
     pathology, common-future precompute, arm init. `torch.manual_seed` /
     `torch.cuda.manual_seed*` are banned outside process startup."* Module construction
     that must read a global generator is wrapped so it draws into tensors from the owned
     generator instead.
  2. Add **`host_init_hash`** to the fan record, computed over the host `state_dict` at
     episode start. One field, and it converts a silent corruption into a loud one: `--replay`
     re-derives the episode and the hash mismatches immediately, at the point of failure
     rather than 40 epochs downstream. `common_future_hash` already does exactly this job for
     the data stream — this extends the same idea to the other init-time draw that matters.

### N2 — HIGH: `worker_count` is part of the pinned environment and is not in the env block

- **Channel**: GPU (8) / replay (5)
- **Location**: L301–303 (env block contents), L462 (several workers per card), L276–279
  (one device per fan), L311–315 (`--replay` env-mismatch refusal)
- **Observation**: Rev 3 correctly pins fans to one device on the grounds that cuDNN
  algorithm selection is workspace-dependent. It then runs several workers per card, so free
  VRAM on that one card varies with how many co-resident workers are mid-lifecycle — and
  `worker_count` is not in the env block that `--replay` checks.
- **Why it matters**: `cudnn.deterministic = True` and `use_deterministic_algorithms(True)`
  guarantee that the algorithm chosen *is* deterministic. They do not guarantee that the
  *same* algorithm is chosen under different conditions. With `benchmark = False`, PyTorch
  takes the heuristic-ranked algorithm list and picks the first whose workspace fits in
  available memory — so lower free VRAM can select a different (still deterministic)
  algorithm, producing different bits. The mechanism rev 3 cites for cards applies within a
  card.
- **The consequence that makes this a scheduled failure rather than a hypothetical**: the
  twin arm runs under the *same instantaneous memory pressure* as its base run, milliseconds
  apart, so **the twin can pass all night while `--replay` fails weeks later** on a quieter
  or busier machine. The design's two verification instruments are blind to precisely this
  axis, and the failure appears at the worst moment — when someone is trying to check a
  published number.
- **Resolving sheet**: `09-gpu-determinism-config.md` item 7 (cross-device policy — read
  here as cross-*condition*) and item 9 (class-breaking events); `01-` item 7.
- **Suggested action**: three cheap moves, in order of value.
  1. Add `worker_count` and `device_index` to the env block. `--replay` already refuses on
     env mismatch, so this costs one field and inherits the enforcement.
  2. **Run `--replay` single-worker** and record that as the replay contract. Reproduction
     does not need throughput.
  3. Set an explicit cuDNN workspace limit so selection is pressure-independent by
     construction rather than by luck. If that proves awkward, (1)+(2) alone are adequate.
  Note this is one of the few claims here I would want confirmed empirically — the cheap
  test is a twin-arm run at 1 worker vs at full worker count on the same episode seed.

### N3 — MEDIUM: a refan must re-run the no-op continuation, or paired quantities mix two futures

- **Channel**: Replay (5) / divergence (4)
- **Location**: L358–367 (pre-flight gate 3, noise floor from ~10 refanned episodes) and
  L407–411 (oracle ceiling from ~30 refanned eval-grid points)
- **Observation**: Refanning is defined as "same snapshot, same epoch, a *re-drawn common
  future*". Two things are unspecified, and the second one changes numbers.
- **The load-bearing part**: a re-drawn common future changes the data stream from the fan
  epoch to the horizon **for every arm — including the baseline**. The no-op arm is the base
  run (L240), whose tail was trained under the *original* future. So unless the no-op
  continuation is re-run under the new future, a refan compares seed arms under future-2
  against a baseline under future-1, and the difference absorbs the future change. That
  contaminates exactly the quantities the pre-registered thresholds are stated against:
  `mean(R_best − R_noop)` within fans (L358–361), the oracle ceiling that agreement is
  reported as a fraction of (L407–411), and restraint-regret with no-op eligible (L404–406).
  **Corollary with a budget consequence**: in a refan the twin arm cannot stand in for the
  no-op, because the original base tail is no longer a valid comparand. A refan is therefore
  **5 real arms** (4 seeds + a fresh no-op continuation), plus a 6th if the twin verification
  is retained — not the 4 that "same snapshot, same epoch" implies. Across ~10 pre-flight
  and ~30 eval refans that is a real, plannable cost, and it should be in the budget rather
  than discovered.
- **The minor part**: the re-drawn future needs a stated derivation —
  `derive(episode_seed, "refan", k)` for refan index `k`, with `k` and the resulting
  `common_future_hash` in the record. Otherwise the noise floor and the oracle ceiling are
  themselves unreproducible, and `--replay` cannot reach a refanned point at all. The schema
  already carries `common_future_hash`, which *records* which future was used — but a hash
  identifies, it does not re-derive.
- **Resolving sheet**: `06-replay-infrastructure-spec.md` item 7 (branching primitives —
  per-branch input substitution); `02-seed-governance-spec.md` §"Seed Propagation".
- **Suggested action**: state both — *"A refan re-derives the episode to the fan epoch, draws
  a fresh common future from `derive(episode_seed, "refan", k)`, and re-executes **all five
  arms including the no-op continuation** under it. `k` and the resulting
  `common_future_hash` are recorded; refanned records carry `kind = "refan"` and are excluded
  from training."* The last clause matters: `--train` must not treat refans as extra fans,
  or the same episode-epoch appears repeatedly in the objective.
- **Scope note — the noise floor changed owners.** Rev 3's derived change is correct: under
  Class 1 the *determinism* noise floor is exactly zero and the twin arm proves it, so the
  refan-measured quantity is an **experimental-design sensitivity** (how much does `R_a` move
  under an irrelevant draw), not a determinism quantity. I am verifying only that the
  mechanism is deterministic, reproducible, and correctly paired. Whether ~10 and ~30 refans
  give adequate precision for a floor and a ceiling, and whether that ceiling is the right
  denominator for the agreement thresholds, is the statistics reviewer's call.

### N4 — MEDIUM: twin-arm abort semantics are unspecified in all four dimensions

- **Channel**: Divergence detection (4)
- **Location**: L267–272 ("must reproduce the base run's tail **bitwise**; any divergence
  aborts collection")
- **Observation**: The twin arm is now the demo's primary determinism instrument. What it
  compares, when it compares, what "abort" does, and what it leaves behind are all unstated.
- **Why it matters**: a divergence detector that fires without localising costs a day. The
  pack's position (`05-`) is that the value of a compare-point is the *localisation*, not the
  alarm.
  - **What is compared**: "the tail" could mean final weights, the val-accuracy curve, or the
    full `state_dict` at every epoch. Only the last localises.
  - **When**: comparing per-epoch names the *first* differing epoch; comparing at the end
    names only that something differed.
  - **What aborts**: the worker, or the process? Under free threading these differ, and a
    worker that dies quietly while its siblings keep collecting produces a store that is part
    verified and part not, with nothing marking the boundary.
  - **What survives**: records written before the divergence were each verified by their own
    twin and remain valid — that should be stated so an abort does not trigger a
    precautionary discard of a night's collection.
- **Resolving sheet**: `05-divergence-protocol.md` items on compare-points, hash function,
  and the localisation procedure.
- **Suggested action**: *"The twin arm compares a hash of the host `state_dict` (parameters
  and buffers) at **every epoch** of the tail. On mismatch, collection aborts the whole
  process and writes a divergence report: first differing epoch, first differing tensor key,
  `episode_seed`, `fan_epoch`, `device_index`, `worker_count`, and the env block. Shards
  written before the abort remain valid — every record in them carries its own passed twin."*
  The per-epoch hash costs almost nothing at this model size and turns an abort into a
  diagnosis.

### N5 — MEDIUM: eval-time action selection is ungoverned, so the headline comparison is not reproducible

- **Channel**: Seed governance (1) / RNG isolation (2)
- **Location**: L388–396 (eval battery; "each policy plays its episode live (its own
  germination choices)"), L414–415 (random and schedule-only baselines), against L81–82
  (learner RNG covers policy init and minibatch order only)
- **Observation**: REINFORCE's removal deleted the *training*-time sampling slot, and rev 3
  correctly claims `--train` bit-reproducibility. But the trained policy still acts live at
  evaluation, and the spec never says whether it acts by **argmax or by sampling** from
  `p` and `π(a|s)`. The random baseline is by definition a sampler and has no named RNG at all.
- **Why it matters**: if evaluation samples, the headline lift, the Wilcoxon test, the money
  chart and the restraint rate all carry an unrecorded RNG draw, and re-running the frozen
  eval battery gives different numbers from the same policy and the same 100 seeds — for
  results that are pre-registered and quoted. The whole point of L388–396's frozen, paired
  battery is that everything except the policy is held fixed.
- **Resolving sheet**: `03-rng-isolation-spec.md` item 2 (named slots — this is a missing
  slot, not a missing value); `02-` item on recording seeds in the run.
- **Suggested action**: state the rule. Cleanest: *"At evaluation all policies act
  **greedily** (argmax on NOW and on the seed head); the random baseline draws from
  `derive(run_seed, "eval_random", episode_seed)`. Evaluation consumes no other randomness."*
  Greedy removes the slot rather than governing it, and it is the right choice for a
  pre-registered comparison. If sampling is wanted for a restraint-rate distribution, it
  needs its own named slot and the draw recorded in the `policy_run` record.

### N6 — LOW: no committed golden test vector

- **Channel**: Divergence detection (4)
- **Location**: L469–470 (`--selftest`), L83
- **Observation**: The twin arm proves *internal* consistency within a run: base ≡ branch,
  snapshot complete, deterministic mode in force. It cannot detect a change that shifts every
  result consistently — a torch or driver upgrade, or an edit to the host architecture.
- **Why it matters**: gate Check 10 — one recorded run whose hash all future runs must
  reproduce is what distinguishes a determinism *property* from a determinism *assertion*.
  Rev 3's env-mismatch refusal covers the upgrade case partially (it refuses rather than
  silently drifting), so this is genuinely LOW.
- **Resolving sheet**: `12-property-test-suite.md` Property 1; gate Check 10.
- **Suggested action**: commit one small record — a 5-epoch smoke episode at a fixed seed,
  with its `host_init_hash`, `common_future_hash`, and final host-state hash — and have
  `--selftest` assert it. Under the env block it should be exact; on env mismatch it reports
  rather than fails, and becomes the artifact you diff after an upgrade.

### N7 — LOW: the cost record has no forbidden-silent-relaxations list, and the twin arm is the obvious cut

- **Channel**: Cost (cross-cutting)
- **Location**: L83 ("Deterministic-mode slowdown is measured once in pre-flight and recorded")
- **Observation**: The measurement is there; the trade record around it is not.
- **Why it matters**: `13-`'s whole argument is that unrecorded determinism costs get relaxed
  silently under deadline. Rev 3 has created a perfect candidate: the twin arm is 1 of 5
  branch arms, ~20% of fan compute, contributes no data to the store, and looks exactly like
  a free win at 2am against a 300-episode overnight budget. Disabling it silently restores
  the base/branch asymmetry described under H3 — with no symptom.
- **Resolving sheet**: `13-cost-of-determinism.md` items 6 (forbidden silent relaxations) and
  7 (budget-breach response).
- **Suggested action**: five lines in the file header. *"Class-breaking, not optimisations:
  disabling the twin arm; `cudnn.benchmark = True`; `use_deterministic_algorithms(warn_only=True)`;
  enabling TF32 or AMP; changing `worker_count` between collection and replay. If the
  overnight budget misses, shorten the horizon or reduce episode count — never these."*

## Worker model — the trade, for the lead to pick

Rev 3 chose free-threaded workers (L460–461). N1 and N2 are both downstream of that choice,
so it is worth stating the alternative plainly rather than only the risk.

- **What free threading buys**: CIFAR-10 resident once per *card* (~180MB) rather than once
  per worker; no IPC.
- **What it costs**: every worker shares torch's process-global state — the default
  generators (N1), the deterministic-mode flags (benign, all workers want them on), and one
  CUDA context whose memory pressure is the sum of all workers (N2). The CUDA *current
  device* is thread-local in modern PyTorch, so per-thread device pinning does work as rev 3
  assumes.
- **What processes would cost instead**: ~180MB × N per card of duplicated dataset. At 4
  workers that is ~720MB on a 4060 Ti — comfortable on either the 8GB or 16GB SKU with a
  150k-parameter host.
- **The observation that makes this cheap**: the GIL argument that motivates free threading
  is largely dissolved by rev 3's own no-loader design. With CIFAR-10 GPU-resident and
  augmentation as tensor ops, episode workers spend nearly all their time awaiting CUDA, and
  release the GIL while doing so. Free threading is buying throughput the design already had.

One process per worker, each with its own CUDA context, removes N1 entirely and reduces N2 to
a per-process memory question. I am not filing this as a finding — it is the resolution
mechanism for two already filed, and the choice is the designer's.

## Confidence Assessment

- **Verdict confidence**: High. Rev 3's `(closes: …)` annotations made disposition checkable
  against specific text rather than inferred, and each verdict above cites the line range it
  rests on.
- **New-finding confidence**: High for N3, N4, N5, N6, N7 — these are statements about what
  the spec does not say, verified by grep. Medium-High for N2: the workspace-fits-available-
  memory selection path is real, but I have not confirmed empirically that it bites at this
  model size, and the cheap test is named in the finding. Medium for N1's *impact*: the
  mechanism requires a specific implementation choice (per-episode `manual_seed`) that the
  spec neither mandates nor forbids, which is precisely why it is filed as a missing rule.
- **Severity confidence**: Materially higher than round 1 — the class is declared, so
  "class-breaking" has a referent. This is the single biggest improvement in reviewability
  between the two revisions.
- **Coverage confidence**: High for the ten channels against rev 3's text. Still zero for
  the implementation, which does not exist.

## Information Gaps

- **No code.** N1's exposure, the twin arm's comparison granularity, and the refan's arm count
  are all properties of an implementation that has not been written. These findings are
  requests for the spec to constrain it.
- **Empirically unverified**: whether cuDNN algorithm selection actually shifts at this model
  size under realistic per-card memory pressure (N2), and the deterministic-mode slowdown —
  rev 3 correctly schedules the latter as a pre-flight measurement.
- **Not in my scope**: whether ~10 refans give an adequate noise floor and ~30 an adequate
  oracle ceiling, and whether that ceiling is the right denominator for the agreement
  thresholds (statistics reviewer). Whether the trust-region term, β-ramp, and SGD contract
  behave as intended (lifecycle / dynamic-architectures reviewers). I did not read the four
  sibling reviews, so rev 3 changes that close *their* findings are unassessed here.

## Caveats

- Round-2 severities are measured against rev 3's **declared** Class 1 contract. If the class
  is later relaxed, N1–N7 re-rate.
- Verdicts cover the spec text at commit `244accb`. A `(closes: …)` annotation is evidence of
  intent; only code closes a finding in the end, and four of these (N1's generator rule, N4's
  comparison granularity, N3's arm count, N5's action rule) are exactly the kind that get
  closed in prose and reopened in implementation.
- The twin arm is now load-bearing for the demo's central comparison, not merely for its
  determinism claim. Treat any change to it as class-breaking.

## Result Statement (Plain Language)

Rev 3 closes fifteen of nineteen round-1 findings outright and leaves nothing unaddressed; the
four partials are each one sentence from closed. The twin arm is a better instrument than the
control I proposed — it verifies snapshot completeness, executor equivalence, optimizer
restore and deterministic mode at once — and it is now what makes the base-run-as-no-op
optimization safe, which means it must never become optional. The seven new findings all come
from rev 3's own changes: the free-threaded worker model needs an RNG ownership rule and
`worker_count` in the env block (a twin arm can pass all night while `--replay` fails weeks
later), and the refan mechanism must re-run the no-op continuation under the new future or the
paired numbers the thresholds are stated against will quietly mix two data streams.

---
- **Statement signature**: `determinism-reviewer`, axiom-determinism-and-replay v1.1.0
- **Issued at**: 2026-08-09T11:24:44Z
