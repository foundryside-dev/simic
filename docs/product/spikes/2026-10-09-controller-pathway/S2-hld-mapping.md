> **Design spike, 2026-10-09, input to [PDR-0057](../../decisions/0057-controller-training-pathway.md).** Written by a subagent (Opus) from the repository at main `6d38c81`. Scripts it cites under `scratchpad/` were not committed. Where a number here disagrees with a committed script, the committed script wins. In particular, S1's §0 headroom claim is superseded by `docs/results/2026-10-09-rung4-timing-horizon/exploratory/timing_headroom_null.py.txt`: single-future data cannot separate per-seed headroom from noise.

# Spike S2: the "train the growth controller" pathway mapped onto the HLD

Date: 2026-10-09. Status: design spike. Nothing here is decided. It informs
the rung-5 DECIDE PDR and the unparking of items behind gate
`simic-e0bafbe10f`.

Sources: `AGENTS.md`; `docs/design/{00-INDEX,01-claim,02-constitution,04-architecture,05-leyline-contracts,06-growth-model,07-counterfactual-engine}.md`;
`domains/{aurelia,nissa,isperia,wrenn,momir,ugin,tamiyo,jin-gitaxias,tolaria}.md`;
`programme/{phases,learning,curriculum}.md`; ADR-0008, ADR-0011, ADR-0018;
PDR-0050 and PDR-0054; `docs/product/{vision,roadmap,current-state}.md`;
`experiments/{bounded_comparison,timing_study}.py`; the tracker; and the
**untracked draft** `docs/results/2026-10-09-rung4-timing-horizon.md`.

---

## 0. Bottom line

1. **The learned decision belongs to Aurelia, with a degenerate Momir beside
   it. Isperia never learns.**
   - "Whether, where and when" are Aurelia's `WAIT`/`COMMISSION_GROWTH`.
   - "What", chosen from a fixed library, is Momir at rung L0 ("retrieval
     over the fixed five", `simic-03de2210b6`).
   - Isperia stays a fixed rule that compares against no-op.
2. **"Tamiyo" stays a prose nickname for the ambition.** It is never a
   package, contract, test or telemetry name.
3. **Rung 5 = S0 + S1 (offline).** Rung 5 needs **no** `RegionContract`,
   `GrammarProfile` or `Warrant`. Those enter at **S2**, the first time a
   policy, not a pre-registered schedule, raises influence.
   - Warrant freshness (`simic-38a07fad39`) can be satisfied trivially as
     late as S2 by branch adoption.
4. **The rung-4 draft changes the bar.**
   - Its reading is `lever_found`, and the effect is monotone: earlier is
     better, T0 is best, and the graft never beats static at 10 epochs.
   - Rung 5's baseline must therefore be the **best fixed schedule (T0)**.
   - Rung 5 is well-posed only if the best choice varies across seeds by
     more than the noise.
   - S3 is where the ladder is most likely to end, and an ending there is a
     legitimate result.

---

## 1. Naming

### 1.1 Where the decision lives

| Esper sense ("Tamiyo germinates seed X") | Simic authority | Grounds |
|---|---|---|
| *whether* to intervene, *when* (decision point), *where* (region) | **Aurelia** commissions | `domains/aurelia.md#responsibilities` ("decide whether work should be commissioned, where it belongs"); `04-architecture.md#104-tactical-commission` (`WAIT` / `COMMISSION_GROWTH`) |
| *what* to grow (norm / attn / conv_light / conv_heavy) | **Momir** designs; L0 is retrieval over a fixed library | Aurelia is schema-forbidden from it: INV-09; `02-constitution.md#55-the-evidence-routing-rule`; `05-leyline-contracts.md#93-growthintent` (forbidden `preferred_topology_family`, `suggested_ancestor`). L0 rung: `simic-03de2210b6` |
| does it beat doing nothing | **Isperia** judges, with a rule-driven, pre-registered policy | INV-15/16/18/45; `programme/learning.md#175-isperia` |
| "germinate" (install at zero influence, then blend) | **Wrenn** embodies, under an admission warrant | INV-25/26; `06-growth-model.md#121-state-meanings` (`GERMINATED` = "Isperia-admitted growth installed at zero influence") |
| measure the candidates and no-op in matched branches | **Jin-Gitaxias** tests in **Tolaria** | INV-05/06/18; `07-counterfactual-engine.md#145-no-op-anchoring` |

**Why Isperia is not the learned part.** The learnability boundary
(`programme/learning.md`, preamble of §17) says "a policy is only safely
learnable when something else can measure it."
- Aurelia and Momir can be learned because Jin-Gitaxias measures and Isperia
  judges.
- A learned Isperia would grade itself. Its only external signal is
  containment rollbacks, which are rare by construction (ADR-0010).
- Making the judge learned is therefore out of scope for this pathway at
  every stage.

**Why Aurelia's training signal is class-blind.** ADR-0011 partitions the
labels: Aurelia receives only "best-over-action-set versus no-op". The
per-action detail goes to telemetry sufficiency, the Momir corpus and Ugin
statistics (`programme/learning.md#172-aurelia`). An Aurelia trained on
per-seed-type labels would learn a topology preference it cannot legally
express. That is covert-channel pressure on INV-09 at training time.

### 1.2 Honouring "Tamiyo" without an authority smell

- **Settled precedent.**
  - ADR-0018 §Consequences: "the eventual telemetry-conditioned … learned
    structural adaptation ambition — called Tamiyo in the Esper-lite
    discussion … Simic's existing Namespec meaning of Tamiyo remains
    unchanged."
  - PDR-0050 calls rung 5 "the first Tamiyo-shaped result".
  - ADR-0008 records the owner ruling that "Tamiyo does not return to the
    tactical role" (`simic-3a17fe545d`, WONTFIX).
- **Recommended convention.**
  - **Prose:** "the Tamiyo-shaped result" or "the growth policy (Esper's
    *Tamiyo*)", once per document, as a gloss on the ambition.
  - **Code, contracts, packages, tests, telemetry, PDR titles:** Aurelia's
    *commissioning policy* (`aurelia`) plus Momir's *L0 selector*
    (`momir`). Example: "Aurelia commissioning policy v0 (the Tamiyo-shaped
    controller)".
- **Why this is not cosmetic.**
  - "Tamiyo changed alpha" and "Tamiyo changed the learning rate directly"
    are the constitution's own bad sentences (`02-constitution.md#51-why-the-names-are-deliberately-goofy`,
    `#54-the-sentence-test`).
  - A `tamiyo` module in the control path makes INV-35 unsatisfiable by
    definition: disconnecting it would change training.
  - The dependency rule `tamiyo ← any training-critical code path` is
    **prohibited** (`02-constitution.md#56-dependency-consequence`).
- **Tamiyo's legitimate part.** Tamiyo can *reveal* the controller's
  decisions: flight recorder, branch-tree view, audit bundle
  (`domains/tamiyo.md#responsibilities`).

---

## 2. Stage map

Notation: **XG** = experiment-grade minimum, to be built now as frozen
dataclasses inside `experiments/`. **HLD** = the full contract, deferred.
Every XG record keeps the HLD **field names** for the fields it carries, so
that the later promotion only adds fields and never renames them.

### S0: Counterfactual atlas. Branch K actions plus no-op from snapshots (rung 5, part 1)

This is ADR-0011's anchor corpus in miniature, at `FULL_DECISION_FANOUT`,
generated before any policy exists.

- **What it is.** `timing_study.py` generalised. For each seed:
  - one no-growth mainline;
  - snapshots at declared decision points (graft epochs);
  - at each snapshot, a fork for each library seed type, run to end-of-run
    on the prefix-stable common future;
  - the static arm.
- **What already exists.** The bounded harness already provides seed-level
  pairing, Academy-exact replay, immutable snapshots and a prefix-stable
  future. Rung 4 verified 4,608/4,608 runs with no replay mismatch.
- **Domains acting.**
  - Tolaria (fan-out mechanics, which are authority-agnostic per ADR-0011);
  - Wrenn (slot, lifecycle v2);
  - Nissa (telemetry at each decision point, captured from the ablated path);
  - Jin-Gitaxias stub (turns branch outcomes into measurements);
  - Urborg (append-only run root).
  - No Aurelia, Momir policy or Isperia acts. There are no decisions.
- **INV binding.** INV-05, 06, 15, 16 (no-op is the zero of every label),
  31 (keep diverged and non-finite branches), 32, 34 (telemetry must not
  perturb the host), 36, 38 and 39 (declare
  `counterfactual_anchor_regime = FULL_DECISION_FANOUT`).
- **Minimal contracts (XG).**
  - `ScaffoldState` with all four axes as constants:
    `ACADEMY_EXACT`, `REPEATED_ACQUISITION`, `NULL_ANCESTRY` (per
    `simic-4438123141`: references are outcomes, not inputs) and
    `FULL_DECISION_FANOUT`.
  - `TelemetryEnvelope`-lite: `observation_id`, `telemetry_id`,
    `snapshot_id`, `host_state_id`, `logical_step`, `region_id`,
    `task_metrics`, `activation_statistics`, `optimisation_velocity`,
    `validity_mask`, `provenance`, `schema_version`.
    - `ablated_context` is declared trivially: one slot and no resident
      growth, so the host *is* the ablated path.
    - The envelope has no `should_grow` or diagnosis fields. A
      `validity_mask` keeps absent values absent (ADR-0006).
  - `BranchResult`-lite: `branch_id`, `blinded_candidate_id`, `snapshot_id`,
    `execution_status`, `execution_regime`, late-CE trajectory,
    `integration_shock`, `parameter_cost`, `measured_compute_spend`,
    `stability_events`, `replay_digest`.
  - The candidate-identity map (blinded id → seed type) is kept in a
    **separate file**, as the INV-37 pattern requires.
- **Deferred.**
  - The full `Snapshot` (aurelia/ugin state fields are not yet meaningful);
  - `TestPlan` data-role splits beyond the S1 screen/audit split;
  - `GrowthRecord`.
- **Precondition deliverable: label reliability.**
  - On a subset of seeds, fork each decision point under **two** common
    futures (test–retest).
  - If the per-seed identity of the best action does not replicate across
    futures, no telemetry can beat a fixed schedule. That is the rung-5
    stop condition, measured before any model is fit.
  - Hint from the draft's confirmatory table (sourced from
    `fleet/timing_report.json`): the paired T0−T3 contrast has sd 0.089
    against a mean of −0.051, n = 767.
  - A per-seed look at that spread would use
    `docs/results/2026-10-09-rung4-timing-horizon/tables/per-run.jsonl.gz`.
    It cannot separate heterogeneity from noise, because each seed has only
    one future. That is why the retest arm is needed.

### S1: Offline predictor, telemetry → per-action effect (rung 5, part 2)

**Split S1 into two predictors by authority. This is the core of the
spike.**

| Predictor | Label | Consumer | Becomes |
|---|---|---|---|
| **P-marginal** | max over (t, a) effect vs no-op, class-blind (ADR-0011 slice) | Aurelia | the S2 commissioning policy (`WAIT` vs `COMMISSION`, and when) |
| **P-action** | per-seed-type effect vs no-op | telemetry-sufficiency instrument; Momir L0 critic | the S2 pool-narrowing critic (`simic-0e6445d894`: Momir may search against its own critic, formed *before* the pool is measured) |

- **The test.**
  - Regret on held-out *seeds* relative to the **best fixed schedule**
    (T0 + `norm` per the rung-4 draft).
  - Named comparators: **random** timing; the **Esper preset selector**
    (`simic-1d3aa47ff1`, a permanent blinded control and the telemetry
    floor); the **oracle** (best-in-hindsight from the atlas).
- **Domains.** Nissa (publishes the same `observation_id` to both
  predictors' input views; INV-07); Aurelia and Momir (learning offline);
  Urborg (the corpus). No embodiment.
- **INV adds.**
  - INV-07 and 09: Aurelia's view carries **no seed-type field** by
    construction.
  - INV-12: P-action never sees P-marginal internals.
  - INV-32: seed-grouped splits.
  - INV-34.
  - ADR-0006: validity masks honoured, never imputed as zero.
  - `simic-0ec359f7fa`: conditioning on region *statistics*, never layout or
    width. This costs nothing now and cannot be recovered once a trained
    artefact exists.
- **Minimal contracts (XG).**
  - Two **authority-partitioned blinded views** of the S0 atlas: one
    function per consumer, returning a record whose type lacks the
    forbidden fields.
  - A `split_membership` keyed by `base_trajectory_id`, with three roles:
    construction, screen and audit (`07-counterfactual-engine.md#142-data-separation`).
  - No `GrowthIntent` yet. Prediction is not commissioning.

### S2: Closed-loop controller vs fixed policy (rung 6)

This is where the HLD's admission chain becomes real. A policy, not a
pre-registered schedule, now causes influence to rise.

- **The loop at each decision point.**
  1. Nissa publishes O.
  2. Aurelia-policy chooses `WAIT` or `COMMISSION`, which emits a
     `GrowthIntent`.
  3. A trivial resolver produces the `GrowthRequest`.
  4. Momir-L0 proposes a pool: all K, or the critic's top-m, plus no-op
     added by Jin-Gitaxias.
  5. Jin-Gitaxias runs matched short branches from the snapshot.
  6. Jin-Gitaxias returns a `QualityReport`-lite with no verdict.
  7. Isperia-rule applies eligibility, then a tail veto (non-finite output,
     loss spike), then a margin over no-op above θ (frozen and
     pre-registered).
  8. Isperia issues an `AdmissionDecision` and a `Warrant`.
  9. Wrenn germinates by **branch adoption** (INV-22).
- **Evaluation arms, paired by seed.** Learned policy; best fixed schedule
  (T0); random timing; no growth; static; the Esper preset selector.
- **The WAIT label.** Measure WAIT with **one extra branch** at sampled
  decision points (`simic-d176c4ebcd`).
- **What pairing does not fix.** Timing choices separated by δ are still
  path-conditional. State this up front rather than claiming the pairing
  removes it (same item).
- **Domains.** All of the core loop except Elesh, Urabrask, Emrakul and
  Ugin. Ugin is a **fixed** `StrategicEnvelope`: one region, at most one
  growth, a parameter budget (MVP: `programme/phases.md#24-minimum-viable-system`).
- **INV adds.**
  - 08 (observation binding);
  - 10/11 (deterministic resolution; equivalent intents → one request);
  - 15/16 at *every* commission;
  - 17/37 (the decision function's input type has no seed-name field);
  - 18 (the measure and judge modules are separate: the judge imports no
    torch or Tolaria; the measurer cannot construct a verdict enum);
  - 20 (at L0, "semantic hash" = blueprint id + init-parameter hash);
  - 22, 23, 25, 26, 29 and 45.
- **Minimal contracts (XG).**
  - `StrategicEnvelope`-lite (constant);
  - `GrowthIntent` (full field list; it is small);
  - `GrowthRequest`-lite (`request_id`, `intent_id`, `observation_id`,
    `insertion_region_id`, `exact_parameter_budget`, `qa_budget`,
    `permitted_evaluation_horizons`, `resolver_version`);
  - `RegionContract`-stub (`region_id`, the I/O shape, `version`);
  - `QualityReport`-lite (`candidate_reports[]` keyed by blinded id,
    `no_op_report`, `evidence_digest`, `qa_policy_version`; **no**
    verdict);
  - `AdmissionDecision` (verdict, `no_op_margin`, `tail_veto_results`,
    `adjudication_policy_version`, `admission_warrant`);
  - **minimal `Warrant`** (`warrant_id`, `decision_id`, `evidence_digest`,
    `selected_semantic_hash`, `snapshot_id`/`host_state_id`, `envelope_id`,
    `adjudication_policy_version`, validity = *exact host_state_id only*);
  - `LifecycleCommand`-lite. Wrenn's attach path refuses a missing or
    mismatched warrant.
- **Deferred.**
  - `GrammarProfile`: use a constant id, `fixed-library-v1`.
  - Nursery maturation, and with it real warrant freshness.
  - `ProposalBatchRequest` beyond `candidate_count`.
  - Field QA. Admitting on *predicted* effect is the Jin-Gitaxias Field
    surrogate, gated by INV-43/44. Report it only as a labelled ablation
    ("accept/no-op disagreement vs Academy"), never as the primary arm.

### S3: Efficiency vs uniform scale-up

- **The question.** Does the controller's growth sit on a better
  quality–cost frontier than the same budget spent as width from step 0?
  - This is criterion 17 (optional study), `01-claim.md#28-success-criteria`.
  - The static comparator is ADR-0018's.
- **Domains.**
  - Ugin: a budget-matched `StrategicEnvelope` makes cost-matching
    mechanical.
  - Isperia: its cost terms λC and νP are versioned *policy*, not
    experiment knobs.
  - Tolaria measures spend.
- **INV.** 23 (every arm declares budget and reports spend), 32, and 33
  (shared cost weights).
- **Contracts.** `StrategicEnvelope` budgets; `cost_breakdown` in the
  decision; measured spend in `BranchResult`. Nothing new beyond S2.
- **Warning.** This is the likeliest place for the ladder to end.
  - The rung-4 draft shows static beating the graft at 10 epochs at every
    timing, and tying it on the median seed at 20 epochs.
  - A negative here is a recorded result (`01-claim.md#283-on-the-negative-result`;
    ADR-0018: "do not respond merely by enlarging the controller").

### S4: Transfer to held-out hosts

- **The change.** `host_distribution_regime: REPEATED_ACQUISITION →
  HELD_OUT_IN_FAMILY`. This is one axis only (INV-40/41). It covers other
  `PATHOLOGIES`, then host seeds and widths, and it is criterion 12.
- **Domains.** As in S2. Nissa's schema must be host-invariant.
- **INV adds.**
  - 24 (an incompatible telemetry schema fails closed across hosts);
  - 32 (split by host *family*, as well as by seed);
  - 39–42;
  - `simic-0ec359f7fa` (statistics, not layout), which is now tested rather
    than merely declared.
- **Contracts.** `ScaffoldState` actually moves. `TelemetryEnvelope` needs
  a versioned `normalization_manifest`.
  - `RegionContract` becomes non-trivial *only* if host width changes.
  - `RegionReport` (`simic-e3d6ff10c0`) only if regions multiply, which is
    out of scope.

### S5: Generated structure (Momir proper)

- **The change.** L0 → L1 (bounded mutation around the library) →
  L2/L3 (`simic-03de2210b6`). This is Phase C + G.
- **Domains.** Elesh and Urabrask enter. Blinding becomes non-trivial
  because the source now carries lineage.
- **INV adds.** 11, 12, 13/14 (`simic-4438123141` makes 14 hold by
  construction), and 19, 20, 21.
- **Contracts.** `RawGrowthGraph`, `CanonicalGrowthSpec`,
  `ExecutableGrowthArtifact`, the full `GrammarProfile`,
  `ProposalBatchRequest`, and a named blinding service (`simic-04ff4144b3`).
  The library is retained as permanent blinded controls.

---

## 3. Tracker: what each stage pulls, and what must not be pulled

| Stage | Pull (unpark from `simic-e0bafbe10f`) | Why |
|---|---|---|
| S0 | `simic-1850e5e748` (ablated_context; declare it trivially for the single-slot case); `simic-01fb964d23` (count distinct host states; shared-checkpoint = one base trajectory, plus its test) | the atlas's unit and telemetry semantics |
| S1 | `simic-0ec359f7fa` (statistics-not-layout invariant); `simic-1d3aa47ff1` (Esper selector control); `simic-d176c4ebcd` (the dense-label spec, *label half only*); `simic-5503bbe389` (poison-pill / round-trip / null-branch parity, scoped to the S0/S1 pipeline) | the first trained artefact must not depend on layout; the floor and comparators; ADR-0006 silent-default scar |
| S2 | `simic-0bf2c40dec`, **Warrant + RegionContract-stub only**; `simic-38a07fad39`, resolved narrowly (valid only at the evidence `host_state_id`, embodied by branch adoption); `simic-04ff4144b3` in minimal form (who mints blinded ids before QA); `simic-d176c4ebcd` WAIT-branch half; `simic-03de2210b6` (adopt L0 as the stage's frame) | the first policy-driven influence raise |
| S3 | none new | |
| S4 | `simic-e471ac72d8` (one-axis unfreeze discipline, if Momir's critic and Aurelia are both learned) | INV-41 |
| S5 | `simic-4438123141`, `simic-0e6445d894`, `simic-c912a35aa7` (proposal-batching authority), `simic-0b259d9d6c`, `simic-c726274799`; `GrammarProfile` remainder of `simic-0bf2c40dec` | Phase C/G proper |

**Must not be pulled early:**

- **`GrammarProfile` before S5.** At L0 it is a constant id. Designing it
  now is grammar work with no grammar.
- **Warrant freshness beyond "exact `host_state_id`" before nursery
  maturation exists.** Adjudication and embodiment happen on the same
  snapshot (one-shot plus branch adoption), so there is no drift to bound.
- **`RegionReport` (`simic-e3d6ff10c0`), the varying Ugin stub
  (`simic-76fc6e6618`) and multi-region work (`simic-f417165990`)** until
  more than one region exists.
- **Field or calibrated-stochastic regimes, Emrakul, tenancy and
  maintenance warrants, and the Urborg data model / `GrowthRecord`.** None
  of S0–S4 needs them. A run root plus the identity-map file stands in for
  Urborg.
- **Learned Isperia, at any stage** (§17.5). Do not "learn θ". Freeze it,
  and sweep policy versions retrospectively if needed
  (`domains/isperia.md#retrospective-policy-re-adjudication`).
- **Phase A in full: all fourteen packages, import-lint and CI lanes
  (`simic-4da299ff46`, `simic-8db0b87ed6`).** Each XG record should have
  one fail-closed round-trip test. That is enough.

---

## 4. Risks, and how to stay honest cheaply

| Risk | Where it bites | Cheap structural guard |
|---|---|---|
| **No-op not mandatory.** The controller installs argmax(predicted) directly. This is the Esper shape: Aurelia fused with Isperia, and INV-15 is gone. | S2 | The only path to `Slot.attach` takes a `Warrant`. A `Warrant` is constructible only from an `AdmissionDecision`, which needs a `QualityReport` with a non-null `no_op_report`. Admission on prediction exists only as a labelled Field ablation. |
| **Provider blindness.** The judge rule or the measurement summariser sees seed type (for example, a "prefer norm" tie-break). | S2, and S1 for the Aurelia view | The decision function is pure over a dataclass that **has no** seed-name field (INV-37 by construction, not by convention). Ids are blinded per pool by a seeded permutation. The map lives in a separate file and is joined only after the decision. |
| **QA/judgement split collapses.** The branch runner returns ADMIT, or the judge reruns a branch. | S2 | Two modules. The measurer's return type has no verdict. The judge module imports neither torch nor the runner (one import test). θ and the veto threshold live in a frozen, hashed policy file cited by `adjudication_policy_version`. |
| **Tamiyo isolation.** Telemetry capture, progress writes, or a module named `tamiyo` sits in the control path. | S0–S2 | No `tamiyo` identifier in any control path. Run a **telemetry-on/off bitwise test**: the same seed with Nissa capture on and off gives an identical `replay_digest` (INV-34/35). This matters because a capture forward pass in train mode moves BatchNorm running stats, and RNG draws shift the future. Run the capture under `no_grad` + `eval()` on a state clone, using its own generator. |
| **Grouped statistics, pseudo-replication.** Branches, decision points or cells are counted as n. Hosts sharing a pretrained checkpoint are treated as independent. | S0, S1, S4 | `split_membership` is keyed by `base_trajectory_id` (seed + init hash), with a disjointness assertion. Every interval counts seeds, as rung 4 already does. In S4, also split by host family. |
| **Winner's curse.** The best (t, a) is selected on the same seeds it is scored on, or θ is tuned on test. | S1, S2 | The construction / QA-screen / QA-audit split is by seed (`07-counterfactual-engine.md#142-data-separation`). Thresholds are calibrated on validation only (`domains/isperia.md#invariants`). Report the oracle's regret on audit seeds, not screen seeds. |
| **Strawman baseline.** "Beats a fixed schedule" is shown against T2, not T0. | S1, S2 | Fix the baseline as the best fixed schedule in the rung-4 record (T0 + `norm`), plus static. Name it in the prereg. |
| **Ill-posed rung 5.** The best action does not vary by seed beyond noise, so any predictor "loses", or "wins" on noise. | S1 | The S0 test–retest arm gives the stop condition: label replicability below a declared floor → stop at rung 5. Consider redefining the choice as {graft vs no graft, seed type} if timing is uniformly "earliest". |
| **Shaped-reward re-entry.** S2 is trained by RL on a constructed signal. | S2 | S2 is **supervised** from S0/ADR-0011 labels: imitation before any RL (§17.2 sequence). Anti-goal: "No return to shaped reward" (`docs/product/vision.md`, Anti-goals). A failed rung is not answered by enlarging the controller (ADR-0018). |
| **Silent defaults in telemetry.** This is the esper-lite scar. | S0, S1 | ADR-0006: `validity_mask` plus absent-stays-absent; one poison-pill test (`simic-5503bbe389`, item 1) on the real pipeline. |
| **Covert channel in the intent.** Aurelia's continuous outputs (urgency, deadline) leak seed preference into Momir. | S2 (only if both are learned) | Momir-L0 at S2 is either exhaustive (all K) or critic-ranked from **O + Q only**. Add one invariance test: perturbing irrelevant intent fields leaves the pool unchanged (INV-11). |

---

## 5. Questions for the owner (rung-5 DECIDE)

1. Is rung 5 *offline* (S0 + S1: predict, scored by regret against T0) or
   *closed-loop* (S2)? This spike recommends offline. Closed-loop is the
   point where warrants and the resolver become mandatory.
2. What is the choice set: timing × seed type, or {no graft, seed type} at
   T0? The rung-4 monotonicity argues for the second, unless the test–retest
   arm shows that the best timing varies by seed.
3. Is "Tamiyo-shaped" the agreed prose gloss, with `aurelia` and `momir` in
   code? This is a naming convention, not a namespec change. No ADR is
   needed while no codename moves.
