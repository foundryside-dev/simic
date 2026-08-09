# Statistical Audit — Kernel Demo Design (rev 2)

**Auditor:** experiment-statistics-reviewer · **Date:** 2026-08-09
**Target:** `docs/superpowers/specs/2026-08-09-kernel-demo-design.md` @ `321c136`
**Catalogue:** `using-counterfactual-statistics/anti-pattern-catalogue.md` (21 entries)

---

## Scope

**Read:**
- The spec at `321c136` (rev 2), in full.
- The rev 1 → rev 2 diff (`git diff 25be1da 321c136`) — to avoid re-reporting what the
  prior review already closed, and to check for drift introduced by the revision.
- The 21-entry anti-pattern catalogue.

**Ran:**
- `git log` on the spec — two commits, both 2026-08-09.
- Repo-wide search for `experiments/`, `kernel_demo*`, pre-registration files, `*.parquet`,
  fan-store `*.jsonl`. **All absent** (the only `.jsonl` hits are wardline scan findings and
  pyarrow test fixtures).

**Unavailable, and how it limits this audit:**
There is **no implementation, no fan store, no results, and no pre-registration**. This is a
design-only audit. I could not run a single corrected number, because there is no data to
correct. Every impact statement below is *inferred from the specified procedure*, not
confirmed by re-running it — with two exceptions (F2, noted inline) that are distribution-free
and therefore computable now. A design-only audit cannot catch data-dependent defects:
actual arm failure rates, actual ICC between arms, actual val-set exploitation, and actual
argmax stability are all invisible from here.

---

## Ground Truth

| Item | Finding |
|---|---|
| Independent unit | The **episode** (one seeded host init + pathology draw + trajectory). |
| Rows vs units | Each episode → 1 fan record → **5 arm outcomes**. Ratio 5:1. Arms share the entire pre-germination trajectory *and* the precomputed common future — maximally correlated, not independent samples. |
| Arms present | 5: `norm`, `attn`, `conv_light`, `conv_heavy`, **no-op**. |
| Control zero-anchored | **Yes.** Reward is defined `R_chosen − R_noop`; no-op utility is exactly zero by construction. AP-19 satisfied. |
| `K` (selection breadth) | **5** at the fan argmax; 4 conditional on acting. Stated in the spec. |
| Family size | **Undeclared.** ≥5 measurement families (headline lift, 2 agreement grains, 20-cell confusion matrix, 2 falsifier controls, fan density), plus per-pathology breakdowns. No confirmatory/exploratory partition. |
| Pre-registration | **Absent.** A prose *freeze discipline* for pathologies exists (the spec's strongest passage) but no committed artifact, no `N_eval`, no numeric thresholds, no analysis plan. |
| Audit split | **Does not exist.** The fan record schema (telemetry context, germination epoch, 5 outcomes, arm curves, pathology id) carries **no split/role field**. Rejection rate: N/A — nothing built. |
| Horizon | Changed **18 → 40** between rev 1 and rev 2; rev 2 adds a config knob and a second 200-epoch regime. |

---

## Findings

Ordered by catalogue group, because group 1 defects invalidate group 3 findings until fixed.
**Load-bearing** markers indicate findings that block a *pre-flight gate* — these must be
fixed before the 30 pilot episodes are spent, because as written those gates cannot fail.

---

### Group 1 — Unit and pairing integrity

```
F1 · AP-20  Pathology-separability probe splits rows, not episodes        CRITICAL
```
- **Evidence** — Pre-flight §2: *"a linear probe (logistic regression / k-NN) over raw
  telemetry records predicts `pathology_id` well above chance."* The unit named is the
  **record**, not the episode. Telemetry is per-epoch; ~30 episodes × ~40 epochs ≈ **1200
  records from 30 independent units**.
- **Mechanism** — Textbook sibling leakage. Under any row-level split, essentially every
  test record has ~39 siblings from the same episode in train. The probe keys on that
  episode's idiosyncratic loss level and init scale — not on the pathology signature. With
  40 rows per unit, the chance a unit has *no* rows in an 80/20 train split is effectively zero.
- **Impact** — Cannot compute pre-implementation. The direction is certain: separability is
  **overstated**, possibly entirely. This is a **project go/no-go gate** — the spec says
  *"If a linear model cannot see the signal, the transformer will not either."* A leaked
  probe passes on episode identity alone, greenlighting a demo whose central premise
  (telemetry carries pathology signal) was never actually tested.
- **Fix** — `grouped-splits-and-leakage.md`. `GroupShuffleSplit(groups=episode_id)`, and
  report the probe at **episode grain** (aggregate the record sequence, or majority-vote
  per-record predictions within an episode) against a 25% chance line.
- **Effort** — One line of scikit-learn. Minutes.
- **Confidence** — **High.** The spec names the unit explicitly; the arithmetic is not in doubt.
- **Risk if wrong** — Near zero. If the implementer already intended a grouped split, this
  costs one clarifying sentence in the spec. Grouped splitting is never *worse*.
- **LOAD-BEARING — blocks pre-flight gate #2.**

```
F2 · AP-03  Gate "no-op wins its share" is satisfied by pure noise         HIGH
```
- **Evidence** — Pre-flight §1: *"no-op is the fan argmax in a **meaningful fraction** of
  mild-handicap episodes. If never, retune the pathology sampler."* No numeric target, and
  the only stated failure condition is *never*.
- **Mechanism** — Under exchangeability (all five arms drawn from the same distribution —
  i.e. the pathologies do nothing at all), the argmax is uniform over arms:

  > **P(no-op is the fan argmax) = 1/5 = 20%, exactly.** Distribution-free, no assumptions
  > beyond exchangeability.

  So a completely inert pathology sampler produces no-op wins in **20% of episodes**, which
  comfortably reads as "a meaningful fraction," and is infinitely far from "never." The gate
  **cannot fail** on the failure mode it was written to catch.
- **Impact** — Computable now, and exact: the gate's null is 20%, its stated threshold is
  "not zero." The design intends no-op to be the *designed* winner for mild-handicap, i.e.
  materially **above** 20% there and **below** 20% in the three pathological classes. Neither
  is tested. Related, and why this stays folded in here rather than becoming its own finding:
  the prose quantity `max_a R_a − R_noop` (§"What the fan does and does not measure") is
  positive **80% of the time under the same null**, by the same symmetry — so any narrative
  claim of the form "acting was worthwhile in X% of episodes" is inflated by construction.
  It is prose, not a reported metric, so it is a caution rather than a defect.
- **Fix** — `selection-bias-and-best-of-k.md`. Restate the gate as two directional tests
  against the 20% null: no-op win rate in mild-handicap **significantly > 20%**, and in the
  three pathological classes **significantly < 20%**. Better still, test the *margin*
  (`R_noop − max_a≠noop R_a` > 0) rather than the rank — rank discards magnitude, which is
  the thing the sampler is supposed to be creating.
- **Effort** — Rewriting one gate criterion. Minutes. No new compute.
- **Confidence** — **High** on the 20% figure (exact). **Medium** on severity, since the
  spec's authors may intend "meaningful" to mean something stricter — but an unstated
  threshold is not a threshold.
- **Risk if wrong** — Low. Worst case, a gate that would have passed anyway now passes with
  a number attached. Adding a null comparison never weakens a gate.
- **LOAD-BEARING — blocks pre-flight gate #1.**

```
F3 · AP-01  Gate "fan contrast vs noise" compares two different            HIGH
       variance components
```
- **Evidence** — Pre-flight §3: *"per (pathology, seed) pair, the **spread of `R_a` across
  episodes** must be smaller than the typical **best-vs-second arm separation**."*
- **Mechanism** — These are not commensurable quantities. Across-episode spread of `R_a`
  is dominated by *between-episode* variance (host init, pathology draw, data order) — the
  very variance the matched fan is designed to cancel. Best-vs-second separation is a
  *within-fan* contrast, computed under common random numbers, and is therefore far quieter
  than the across-episode spread implies. The gate demands that a large variance component
  be smaller than a small one. It will fail even when the fan contrast is excellent, pushing
  the team toward the spec's own remedy — *"widen the end-state averaging window or lengthen
  the horizon"* — to fix a problem that does not exist.
- **Impact** — Cannot compute pre-implementation. Direction: the gate is **biased toward
  false failure**, and its stated remedy (lengthen the horizon) inflates divergence noise,
  making the real contrast worse. A gate that fails wrongly and then prescribes a
  counterproductive fix is worse than no gate.
- **Fix** — `statistical-units-and-clustering.md` + `horizon-choice-and-divergence-noise.md`.
  Restate entirely as a within-fan quantity: the **paired** best-vs-second margin per
  episode, compared to the **replication noise of that same margin** — which is exactly the
  argmax-stability measurement F10 requires. **One new measurement closes both findings.**
- **Effort** — Reuses F10's measurement. No additional compute beyond F10.
- **Confidence** — **High** that the two quantities differ in composition; **Medium** on the
  magnitude of the mismatch, which depends on the realised ICC between arms.
- **Risk if wrong** — Low-Medium. If between-episode variance happens to be small, the
  original gate is merely conservative rather than broken. The restatement is correct either way.
- **LOAD-BEARING — blocks pre-flight gate #3.**

```
F4 · AP-02  Baseline policies evaluated on unshared episode seeds          HIGH
```
- **Evidence** — Measurement §1: *"trained policy's mean lift ... on fresh eval episodes vs.
  **the same number** for a random policy."* The spec commits to matching the *count* of eval
  episodes and says nothing about matching the *seeds*.
- **Mechanism** — Two separate defects riding together. (a) The comparison is unpaired when
  pairing is available for free — the spec already guarantees *"Same seed ⇒ same episode."*
  Discarding that pairing forfeits the `1/(1−ρ)` variance reduction that is the entire reason
  this design uses matched fans. (b) Mean lift is a mixture over four pathologies with, by
  design, very different lift magnitudes; two independent draws of ~N episodes will have
  **different pathology mixes**, so trained-vs-random is confounded by mix imbalance on top
  of being underpowered.
- **Impact** — Cannot compute the variance ratio pre-implementation. Structurally: running
  trained, random, and schedule-only on the **identical eval seed set** makes every
  comparison paired *and* holds pathology mix exactly fixed, at zero additional episode cost.
  This is the single cheapest change in this audit with the largest effect on headline power.
- **Fix** — `paired-comparison-methods.md` + `common-random-numbers-and-matching.md`.
  Pre-draw a frozen eval seed list; run all three policies over it; analyse as paired
  differences, stratified by pathology, reporting a per-pathology lift alongside the
  stratified mean.

  > **Composition note — F4 and F9 must be fixed jointly, or neither works.** The frozen eval
  > specification must be the pair **`(seed, fan_epoch)`**, not the seed alone. A shared seed
  > with a policy-chosen fan epoch gives *nominal* pairing only: each policy still fans at its
  > own epoch, so F9's non-comparability survives untouched and F4's pairing buys nothing. F9
  > option (b) closes this precisely because the epoch is drawn from a frozen distribution and
  > therefore belongs in the same frozen record as the seed. Fixing one without the other is
  > the failure mode most likely to survive into implementation looking correct.
- **Effort** — A list of seeds and a loop. Hours at most. **No extra GPU time** — the same
  number of episodes is already budgeted.
- **Confidence** — **High.** Determinism is already specified, so the fix is known-feasible.
- **Risk if wrong** — Near zero. Shared seeds are never worse than unshared. If the authors
  already intended this, the cost is one sentence.

```
F5 · AP-09  Common-future guarantee covers the data stream only            MEDIUM
```
- **Evidence** — §Fan step 2 precomputes *"batch index order and all augmentation decisions
  (crop offsets, flip masks)."* §Determinism: *"fan arms consume the precomputed common
  future, never live RNG."*
- **Mechanism** — Rev 2 correctly closed the largest matching hole (this is genuinely good
  work — see Sound Dimensions). Three residual channels remain uncovered: (a) **seed-delta
  weight initialisation** — the spec never states the seeding scheme; the catalogue warns
  specifically against additive forms like `base_seed + arm_id`, which collide across
  episodes; (b) **model-internal stochasticity** — any dropout or stochastic layer inside an
  arm consumes model RNG, which the data-stream guarantee does not cover; (c) **kernel
  nondeterminism** — cuDNN's nondeterministic kernels mean two runs of the *same* arm can
  differ, so "same seed ⇒ same episode" is asserted but never verified.
- **Impact** — Cannot compute. If matching silently decays, `sd_d` inflates and the paired
  design's power advantage evaporates — the catalogue's worked example takes a fleet from
  80% power to ~20% on exactly this failure. The tell in the data would be `sd_d` far above
  design expectation, typically explained away as "the task is noisy."
- **Fix** — `common-random-numbers-and-matching.md`. (i) Declare a non-additive seeding
  scheme (hash of `(episode_id, arm_id)`); (ii) emit a **per-arm digest of every shared
  stream** and assert equality within a fan; (iii) add a CI check that re-running one episode
  reproduces it bitwise, so the CRN claim is tested rather than asserted.
- **Effort** — Half a day, mostly the digest plumbing. The bitwise check is a cheap test.
- **Confidence** — **High** that the channels are uncovered by the current text; **Low** on
  whether they will actually bite (dropout may not be used; the host is small).
- **Risk if wrong** — Low. Digests are cheap insurance; the main cost is a modest amount of
  plumbing in a file with an ≲800-line budget.

---

### Group 2 — Data-role walls

```
F6 · AP-04  Fan store is training corpus and evaluation corpus at once,   CRITICAL
AP-20  with no role field to separate them
```
- **Evidence** — Three passages that cannot all hold:
  1. §Measurement header: **"Measurement (all read from the fan store)"**.
  2. §Learning/WHICH: trains *"over the **whole accumulated fan store**, replayed freely."*
  3. §Fan step 6: the record is *"appended to a JSONL store ... **Append-only**"* — and its
     enumerated schema (telemetry context, germination epoch, 5 outcomes, arm curves,
     pathology id) contains **no split, role, or provenance field**.

  Compounding it: *"Multiple episode workers ... fill one fan store; the learner updates
  between episode batches"* — collection and training are **concurrent**, into one store.
- **Mechanism** — The WHICH head's training corpus and the evaluation corpus are the same
  bytes, and nothing in the schema distinguishes them. Only measurement §1 says "fresh eval
  episodes"; measurements §2–§5 (both agreement grains, the money chart, the falsifier
  controls, fan density) inherit the header's "all read from the fan store." An implementer
  reading this schema has no field to filter on and will read the whole store. Worse, because
  the store is append-only and training replays *"the whole accumulated"* store, **eval fans
  become training data** the moment any further training runs — the leak is bidirectional and
  silent.
- **Impact** — Cannot compute. Structurally: fan-winner agreement and the money chart — the
  demo's two most quotable numbers, one of them designated *"the money chart"* — would be
  **in-sample fits reported as evaluation**. The shuffled-telemetry falsifier is also
  compromised, since a memorised training fan can reproduce its diagonal from context alone.
  The gap between in-sample and held-out is invisible in the metric itself.
- **Fix** — `grouped-splits-and-leakage.md`. Add a mandatory `split_role ∈ {preflight, train,
  eval}` field to the fan-record dataclass, assigned **at episode creation from the frozen
  seed, never inferred later**. Assert at load time that the WHICH training loader rejects
  `eval` rows and every measurement loader rejects `train` rows. Given the spec's own stated
  discipline — *"a missing field is a construction error, never a silent 0.0"* — this field
  belongs in exactly the same category.
- **Effort** — One dataclass field plus two loader assertions. Hours. Materially cheaper now,
  pre-implementation, than after a store exists.
- **Confidence** — **High** on the ambiguity (three quoted passages, no field in the schema).
  **Medium** on whether the authors intended the leak — I read this as an under-specification
  rather than a decision, which is precisely why it needs closing before code exists.
- **Risk if wrong** — Low. If a split was always intended, this costs one field and makes the
  intent enforceable instead of implicit.

```
F7 · AP-04  Val set is telemetry input, reward, and report metric          HIGH
```
- **Evidence** — Telemetry record includes *"train/val loss, **val accuracy**"*; `R_a` is
  *"mean **val accuracy** over the final 2–3 epochs"*; the headline is lift in that same
  quantity. The spec **never defines the val split** — there is no third partition anywhere
  in the document.
- **Mechanism** — Two distinct roles collapse onto one set, and they are not equally
  problematic, so separate them:
  - *Val as telemetry input* — **legitimate**. Val accuracy is observable at decision time in
    deployment too. This is not leakage and should not be changed.
  - *Val as both reward and reported metric* — **this is the defect.** A ~100k-parameter
    policy is trained over hundreds-to-thousands of episodes to maximise accuracy on one
    fixed held-out set, and the headline then reports performance on that same set. Every
    episode's reward shares a common sampling-error component from that one draw, so the
    policy can learn set-specific idiosyncrasies ("attn helps on *this* val set") that the
    headline is structurally unable to detect.
- **Impact** — Cannot compute. The claim degrades from "she improves generalisation" to "she
  improves the number she was trained to improve" — a materially smaller claim, and the demo's
  entire intellectual role rests on the larger one.
- **Fix** — `grouped-splits-and-leakage.md`. Three-way split: host-train / **policy-reward
  val** / **report test**. Splitting CIFAR's 10k test into 5k val + 5k test costs nothing and
  the headline is recomputed on the untouched 5k. Note the halved val set slightly increases
  per-episode reward noise — a real trade, worth taking, and worth stating in the spec.
- **Effort** — One slicing line, plus recomputing the headline. Hours.
- **Confidence** — **High** that the sets are shared as written (no third partition exists).
  **Low** on realised magnitude — with a 10k val set and end-state averaging, exploitation may
  be small. The point is that as designed it is **unmeasurable**, not that it is necessarily large.
- **Risk if wrong** — Low-Medium. Cost is a smaller val set and slightly noisier rewards. If
  exploitation turns out to be negligible, the held-out test simply confirms the headline —
  which is itself worth having.

```
F8 · AP-08  WHICH corpus mixes behaviour-policy versions with no           MEDIUM-HIGH
       version field
```
- **Evidence** — WHICH trains *"over the whole accumulated fan store, replayed freely."* The
  NOW head trains **concurrently** and online. The fan record schema has no
  `policy_version` / `behaviour_epoch` field.
- **First, the part that is correct, and it matters:** conditioning WHICH on states where NOW
  fired is **not** a defect. That *is* WHICH's deployment distribution — it is only ever
  consulted given NOW. The spec's factored head and its `J = Σ_a π(a|s, NOW)·R_a` objective
  get this right, and the offline/online split is a sound response to the interference risk
  the spec itself identifies.
- **Mechanism** — The narrow defect: the *behaviour policy that generated the corpus is
  non-stationary*. Early fans come from a near-random NOW head (warm-up, exploration); late
  fans come from a converged one. Replaying the accumulated store with **uniform weight**
  optimises expected reward under a **stale mixture** of germination states, not under the
  current NOW distribution. Because no field records which policy version produced each fan,
  the mixture can be **neither reweighted nor diagnosed** — you cannot even plot the drift.
- **Impact** — Cannot compute. This does **not** invalidate the headline, which is measured on
  fresh eval episodes with the final policy. It does undercut any claim that the WHICH head is
  *optimal* for the states it will actually see, and it makes agreement metrics drift as the
  NOW distribution moves under them.
- **Fix** — `grouped-splits-and-leakage.md`. Add `policy_version` (or a monotone
  `behaviour_epoch`) to the fan record — a one-field change that makes the drift *visible*.
  Whether to then reweight, recency-window, or simply report the shift is a design call for
  the producer, not this audit.
- **Effort** — One field. Minutes. Diagnosis and any remedy come later, once drift is visible.
- **Confidence** — **Medium-High** that the mixture is non-stationary (the spec's own warm-up
  and interference-guard language implies it). **Low** on magnitude — with a small state space
  and a strong pathology signal, the shift may be modest.
- **Risk if wrong** — Very low. The fix is one recorded field; acting on it wrongly costs
  nothing beyond a column.

---

### Group 3 — Selection and testing

```
F9 · AP-08  The fan's trigger is the policy's own decision, so the         HIGH
       ground-truth label set is a function of the policy evaluated
```
- **Evidence** — *"When Aurelia germinates at epoch t"* — the fan exists only where the
  policy acted. *"Never-germinate episodes produce no fan."* Yet measurement §2 claims
  *"five-way agreement with the fan argmax **including restraint** (chance ≈ 20%)."*
- **Mechanism** — Two consequences, and the second is the serious one:
  1. **The 5-way metric is uncomputable as specified.** Scoring restraint as *correct*
     requires knowing no-op was the fan argmax, which requires running the fan, which happens
     only on germination. On restraint episodes there is no ground truth. The metric either
     silently drops those episodes — collapsing it into the conditional 4-way metric plus the
     no-op-wins subset — or it cannot be computed. The stated 20% chance line presumes a
     5-way ground truth exists on every episode. It does not.
  2. **Cross-policy agreement numbers are not comparable — not merely confounded.** Because
     the trigger is the evaluated policy's own decision, the trained policy and the random
     policy generate fans on **different episodes at different decision epochs**. They are
     scored against different label sets. A policy that germinates rarely, only in obvious
     cases, scores high agreement trivially. There is no adjustment that repairs this after
     the fact: the comparison as designed does not have a common denominator.
- **Impact** — Cannot compute. Structurally, measurement §2 — one of the four headline
  criteria — does not currently define a comparable quantity across the policies it compares.
- **Fix** — `selection-bias-and-best-of-k.md` + `abstention-and-calibration.md`. The binding
  constraint: **on eval episodes the fan must be triggered policy-independently**, so every
  compared policy is scored against the same labels on the same episodes. Two options, and
  choosing between them is the producer's call, not mine:
  - *(a) Fixed reference epoch* — fan every eval episode at a pre-declared epoch. Simplest;
    but the reference epoch may not be where any policy would have acted.
  - *(b) Pre-drawn epoch* — draw each eval episode's fan epoch from a **frozen** distribution
    (e.g. the pilot's observed germination-epoch distribution), fixed before eval begins.
    Better state coverage; requires committing that distribution during the freeze.

  Either way, report **restraint rate alongside agreement, always** — agreement without the
  abstention rate is the AP-11 failure, and a restrained policy's agreement number is
  meaningless without it.

  **Whichever option is chosen, the fan epoch must be frozen jointly with the eval seed — see
  the composition note under F4.** F9 and F4 do not compose if the eval spec freezes only the
  seed.
- **Effort** — Medium. Fanning every eval episode rather than only germinating ones raises
  eval GPU cost, bounded by the eval-set size. On dedicated hardware this is hours, not a
  redesign.
- **Confidence** — **High** on (1), which is a logical gap readable directly off the text.
  **High** on (2) — the trigger dependence is structural.
- **Risk if wrong** — Low-Medium. The cost is real GPU time on eval fans. If the authors
  intended eval-time forced fans all along, this is a spec clarification only.

```
F10 · AP-03  No oracle ceiling — fan-argmax stability is never measured     HIGH
```
- **Evidence** — Success criteria: *"fan-winner agreement **well above both chance rates**."*
  A lower reference (chance) is given. **No upper reference is given anywhere.**
- **Mechanism** — The fan argmax is itself a **max over 5 noisy `R_a` values** and is
  therefore a noisy label, not ground truth. When two arms are genuinely close, the argmax is
  near a coin flip between them, and a policy that picks the statistically indistinguishable
  runner-up is scored as *wrong*. The attainable maximum agreement is not 100% — it is the
  argmax's **self-agreement rate**, and nobody knows what that is. Without it, "well above
  chance" is uninterpretable in the direction that matters: a policy scoring 55% against a
  60%-stable label is **near-oracle**; the same 55% against a 95%-stable label is poor. The
  spec's success criterion cannot distinguish these two worlds.
- **Impact** — Cannot compute pre-implementation. This reframes the demo's second headline
  metric: it converts an unbounded "above 20%" into a fraction of an achievable ceiling.
- **Fix** — `selection-bias-and-best-of-k.md` + `frontier-and-reliability-reporting.md`. On a
  subsample (~30 eval episodes), run each fan **twice under two independent common-future
  draws** and report argmax stability. Report agreement as a fraction of that ceiling.
  **This same measurement supplies the within-fan noise floor that F3 needs to restate
  pre-flight gate #3** — one measurement, two findings closed.
- **Effort** — ~30 extra fans (~150 arm-runs). Meaningful but bounded; overnight on the
  stated hardware, and it is reused by F3.
- **Confidence** — **High** that the ceiling is unmeasured and that the argmax is noisy.
  **Low** on where the ceiling actually lands — if the designed contrasts are strong, it may
  be near 90% and this finding's practical impact shrinks. That is exactly what the
  measurement would tell you.
- **Risk if wrong** — Low. Worst case you spend ~30 fans establishing that the ceiling is high
  — which strengthens the headline rather than weakening it.

```
F11 · AP-10  No pre-registered eval size, thresholds, or stopping rule      HIGH
AP-05  and no confirmatory/exploratory partition
```
- **Evidence** — Success criteria are entirely qualitative: *"lift > 0 and **clearly above**
  random,"* *"agreement **well above** both chance rates,"* *"a **visibly diagonal** money
  chart."* Collection is open-ended — *"overnight yields high hundreds to thousands of fan
  records"* — with *"the learner updates between episode batches."* No `N_eval`, no numeric
  thresholds, no look schedule.
- **Mechanism** — Two compounding defects. (a) **Unplanned stopping**: with no declared N and
  no threshold, the natural workflow is to keep collecting until the money chart looks
  diagonal — stopping at the moment of maximum apparent effect, which inflates the estimate.
  Four looks at nominal α=0.05 already gives ~13% type-I error; unlimited looks converge to
  1.0. (b) **Undeclared family**: ≥5 measurement families plus 4 per-pathology breakdowns and
  20 confusion cells, with no partition into confirmatory and exploratory. Under the global
  null at even m=10, P(≥1 false positive) = 1 − 0.95¹⁰ ≈ **40%** — finding something becomes
  the expected outcome.
- **Impact** — Cannot compute. Note this defect is *strictly cheaper to fix now* than at any
  later moment: pre-registration is free before data exists and impossible afterwards.
- **Fix** — `multiple-comparisons-and-sequential-testing.md` +
  `preregistration-and-exploratory-vs-confirmatory.md`. Commit a small pre-registration file
  before eval: `N_eval`, the frozen eval seed list (F4), numeric thresholds replacing
  "clearly"/"well"/"visibly", and an explicit **confirmatory set** (I would expect: headline
  paired lift, plus diagonal-collapse under shuffle) with everything else labeled
  **exploratory** and reported without significance claims.
- **Effort** — One file, an afternoon. The spec already contains most of the content in prose.
- **Confidence** — **High.** The absence is verifiable — I searched the repo; no
  pre-registration artifact exists.
- **Risk if wrong** — Low. Pre-registration constrains only the *confirmatory* claims;
  exploratory findings remain fully reportable, just honestly labeled.

---

### Group 4 — Design adequacy

```
F12 · AP-07  Horizon changed 18 → 40, plus a config knob and a second       HIGH
       200-epoch regime, with no committed headline horizon
```
- **Evidence** — `git diff 25be1da 321c136`: horizon moved **18 → ~40** epochs between rev 1
  and rev 2. Rev 2 adds: *"Horizon is a config; a long-run flag (up to esper's 200-epoch
  regime) exists for stress runs but is not the default."* Separately, rev 2 **weakened a
  checkable claim into an uncheckable one**: rev 1's *"plateaus in ~10–15 epochs"* became
  *"plateaus well inside the horizon."*
- **Mechanism** — This is the exact AP-07 configuration: an already-moved horizon, a knob to
  move it further, and a second regime, with no commitment to which one the headline comes
  from. The catalogue's detector — *"the analysis script's `HORIZON` constant was edited
  after the fleet finished"* — cannot fire yet, but the structure that makes it fire is
  pre-installed. Two inflations would compound: the family includes every horizon evaluated,
  and the reported estimate is a maximum over them. It is aggravated here because
  divergence noise grows with run length, so the largest apparent effect often sits at the
  *least* powerful horizon. The weakened plateau claim removes the one check that would
  independently justify a horizon choice.
- **Impact** — Cannot compute pre-implementation, and **this finding is entirely
  preventable** — it is the only one here that is purely about a commitment not yet made.
- **Fix** — `horizon-choice-and-divergence-noise.md` +
  `preregistration-and-exploratory-vs-confirmatory.md`. One line in the pre-registration:
  **headline horizon = 40, committed**; any other horizon is exploratory and labeled as such.
  Restore a checkable plateau criterion (an epoch number, or a measurable
  "val accuracy improves < x% over n epochs") so the horizon choice has a stated basis.
- **Effort** — Two lines. Minutes.
- **Confidence** — **High** on the evidence (commit-diffed). **Medium** on severity — no
  shopping has occurred; I am flagging pre-installed structure, not a committed offence.
  Rated HIGH because the cost of prevention is two lines and the cost of the cure is a re-run.
- **Risk if wrong** — Very low. Committing a horizon costs nothing if you were never going to
  shop; the long-run flag remains available for explicitly-labeled stress runs.

```
F13 · AP-14  Freeze discipline is prose, with no mechanism to enforce it    HIGH
```
- **Evidence** — §Freeze discipline is well-reasoned and correctly motivated — *"Retuning
  after seeing evaluation fans is test-set engineering and is not done."* But nothing in the
  design **enforces** it: the fan record schema carries no `config_hash`, no `frozen_at`, and
  there is no committed pre-registration to freeze *against*.
- **Mechanism** — An unenforced discipline is an intention. Since headline and pre-flight fans
  land in the same append-only store with no config fingerprint, a post-freeze pathology tweak
  leaves **no trace** — not from malice, but because a debugging session six weeks in looks
  exactly like a legitimate one in the record. Neither the authors nor a later reader can
  demonstrate the freeze held. The catalogue's detector (`git log` on substantive constants
  vs. fleet completion time) has nothing to bind to.
- **Impact** — Cannot compute. The consequence is on *auditability*: the demo's most important
  methodological commitment would be unverifiable, including by its own authors.
- **Fix** — `preregistration-and-exploratory-vs-confirmatory.md`. Record `config_hash` (a
  hash of the frozen pathology + seed + host definitions) and `frozen_at` in **every** fan
  record; commit the frozen config; assert at eval time that all eval fans carry the
  registered hash. This mechanises the discipline the spec has already agreed to — it adds no
  new policy, only teeth.
- **Effort** — One hash, two fields, one assertion. Hours.
- **Confidence** — **High.** The gap between the stated discipline and any enforcing mechanism
  is plainly visible.
- **Risk if wrong** — Very low. Cost is two fields. Config hashing is independently useful for
  reproducibility.

```
F14 · AP-13  Horizon, averaging window, and contrast decisions sized        MEDIUM
       from a 30-episode pilot
```
- **Evidence** — *"Run ~30 random-policy episodes"*, and gate 3's remedy is to *"widen the
  end-state averaging window or lengthen the horizon"* on the basis of those 30. Spread is
  assessed *"per (pathology, seed) pair"* — with 4 pathologies, that is **~7–8 episodes per
  pathology cell**.
- **Mechanism** — Variance estimates from tiny pilots are extremely unstable: the catalogue
  puts the 95% CI on `sd_d` from a 5-unit pilot at `[0.60×, 2.87×]`, implying downstream fleet
  sizes anywhere from 20 to 407. At n≈7 per cell the interval is still wide enough that the
  horizon and averaging-window decisions — which are then **frozen for the headline** — rest
  on a number that could easily be off by 2×.
- **Impact** — Cannot compute. Direction: design parameters may be set wrongly and then
  locked, with the error invisible because the freeze prevents revisiting them.
- **Fix** — `power-and-sample-size-for-paired-designs.md`. Size from the **upper confidence
  limit** on `sd`, not the point estimate; and re-check contrast after the first ~200 frozen
  episodes as a **monitoring** check that cannot alter the frozen config — only raise a flag
  if the design assumption is violated.
- **Effort** — A UCL instead of a point estimate. Minutes. The re-check reuses episodes
  already being collected.
- **Confidence** — **Medium.** The pilot is small, but this is a tech demo whose designed
  contrasts may be large enough that a 2× variance error changes nothing.
- **Risk if wrong** — Low. Using a UCL is mildly conservative — slightly longer horizons or
  wider windows than strictly needed. Cheap insurance.

---

### Group 5 — Utility definition

The utility is `R_chosen − R_noop`: end-state val accuracy, zero-anchored on a measured
control. **This is sound and I am reporting no finding against it.** One note, explicitly
*not* a finding: the four seeds span 600× in parameter count (0.1k → 60k), so raw accuracy
selection will favour capacity wherever arms are close. A cost-charged utility is *available*
without breaching the "no shaping" scope pin — shaping means intermediate/progress rewards,
whereas a cost term on an end-state utility is still end-state. Whether the demo *wants*
capacity-blind selection is a design choice for the owner, not a statistical defect. If
conv_heavy genuinely wins on capacity, that is the truth of the fan. The **reporting**
consequence is real and is filed below as F16.

---

### Group 6 — Reporting integrity

```
F15 · AP-06  No arm-level status field; arm failure is asymmetric           MEDIUM
       by construction
```
- **Evidence** — The spec commendably keeps failures — *"spike-then-crash arms are a headline
  plot, not a discard"*, *"failures and no-op wins kept."* But the enumerated fan-record
  schema has **no per-arm status field**, and `R_a` is undefined for an arm that NaNs or
  diverges outright.
- **Mechanism** — A spike-then-crash arm still has a val accuracy and is fine. A **NaN'd** arm
  has none. With no defined `R_a` and no status field, the implementer's path of least
  resistance is to drop the fan — and arm failure here is **asymmetric by construction**:
  `attn` and `conv_heavy` (5k/60k params, attention softmax) are far likelier to destabilise
  than `norm` (0.1k). Dropping fans that contain a failed arm therefore biases the surviving
  fan set toward episodes where the risky arms happened to behave, systematically **flattering
  exactly the arms most likely to fail** — and it breaks pairing, since the surviving fans are
  non-random.
- **Impact** — Cannot compute pre-implementation. The catalogue's detector (failure rate by
  arm, flagging spreads > 2%) is the right check and cannot currently be run, because the
  schema does not record the input.
- **Fix** — `paired-comparison-methods.md` + `frontier-and-reliability-reporting.md`. Add
  per-arm `status ∈ {completed, diverged, nan}`; define `R_a` explicitly for non-completed
  arms (a floor value, or last finite accuracy — declared in the pre-registration, not chosen
  after seeing which arms failed); **never drop the fan**; report failure rate by arm as a
  standing reliability row.
- **Effort** — One field, one declared convention. Hours.
- **Confidence** — **High** that the schema lacks the field and that failure risk is
  asymmetric across these four architectures. **Low** on realised failure rates — a small CNN
  on CIFAR-10 with fixed blending may simply never NaN, in which case impact is nil.
- **Risk if wrong** — Low. If nothing ever fails, the field is always `completed` and costs a
  column.

```
F16 · AP-17  Money chart has an eyeball criterion, no n per cell,           MEDIUM
       no marginals, no ceiling comparison
```
- **Evidence** — *"**visibly diagonal** money chart"* as a success criterion. §3 specifies a
  pathology × chosen-seed confusion matrix with no counts, no marginals, no interval, and no
  side-by-side reference.
- **Mechanism** — "Visibly diagonal" is not a decision rule, and a 4×5 matrix has 20 cells
  whose per-cell n is never stated (AP-17's fastest tell is exactly a missing `n_units`). Two
  concrete ways the eye is fooled: a strong **column** (one seed chosen predominantly) reads
  as structure to a casual viewer; and a diagonal driven by **pathology base rates** rather
  than telemetry looks identical to one driven by diagnosis. The shuffled-telemetry control
  (a genuinely good design — see Sound Dimensions) catches the second, but only if the
  comparison is quantitative rather than visual.
- **Impact** — Cannot compute. The fix converts the demo's most quotable figure from an
  impression into a number.
- **Fix** — `frontier-and-reliability-reporting.md`. Report **n per cell**; report the
  **chosen-seed marginal distribution** alongside; show the **fan-argmax matrix side by side**
  as the attainable reference (this is F10's ceiling in matrix form); and replace "visibly
  diagonal" with a pre-registered statistic — per-pathology top-1 accuracy with CIs, or
  Cramér's V — plus its value under the shuffle control, so "the diagonal collapses" is a
  number and not a judgement about a picture.
- **Effort** — Reporting only, no new compute. Hours.
- **Confidence** — **High.** The criterion is quoted verbatim from the success criteria.
- **Risk if wrong** — Very low. Adding counts and marginals to a chart cannot mislead.

```
F17 · AP-11  Schedule-only baseline's training procedure unspecified        MEDIUM
```
- **Evidence** — *"a schedule-only baseline **policy** (epoch index in, telemetry ignored)."*
  Whether it is **trained** with the same procedure, budget, and eval protocol as the main
  policy is not stated.
- **Mechanism** — If the schedule-only baseline is untrained or under-trained, it is not a
  baseline — it is a straw man, and beating it demonstrates only that training occurred, not
  that telemetry was used. The falsifier's whole logical force depends on the two policies
  differing in **exactly one** respect: access to telemetry content.
- **Impact** — Cannot compute. If under-trained, the headline's "clearly above baseline"
  overstates the telemetry contribution by an unknown margin.
- **Fix** — `abstention-and-calibration.md`. State that the schedule-only baseline is trained
  with the identical procedure, budget, and eval seed set (F4), differing solely in input
  features. Report both policies' training curves so the reader can confirm both converged.
- **Effort** — Minutes to specify; one extra training run to execute — small, since the policy
  is ~100k params.
- **Confidence** — **Medium.** This may well be the authors' intent; the spec simply does not
  say, and "baseline" is used loosely enough to permit either reading.
- **Risk if wrong** — Low. Cost is one clarifying sentence and one cheap training run.

---

## Sound Dimensions

Reported briefly and deliberately — an audit that only lists defects misrepresents the design,
and several of these are better than typical.

- **AP-19 — control branch: satisfied.** The no-op arm is present, measured, and zero-anchored
  by construction. `R_chosen − R_noop` makes "do nothing" a first-class outcome that can win.
  This is the single most-skipped item in the catalogue and the spec gets it right.
- **AP-01 at the headline: no finding.** The per-episode paired difference collapses the
  5-arm fan into one number per independent unit. The obvious pseudo-replication trap — 5N
  arm rows treated as N independent samples — is **not** present in the headline. (Where the
  unit does slip is in the pre-flight probe, F1, and the gate-3 comparison, F3.)
- **AP-02 within the fan: satisfied.** Arms share the pre-germination trajectory and the
  common future, so within-fan contrasts are paired by construction — the design's core
  strength.
- **AP-18 — negative results retained: explicitly satisfied.** *"Append-only; failures and
  no-op wins kept"*, plus restraint-rate recording and spike-then-crash curves promoted to a
  headline plot. (F15 refines *how* failures are encoded; it does not dispute the intent.)
- **Rev 2's common-future precomputation is exactly right.** Drawing batch order **and
  augmentation decisions** independently of model RNG, with the explicit reasoning that
  *"cloning RNG state alone is insufficient — different arm architectures consume RNG
  differently"* — this is the correct and commonly-missed insight. F5 covers only residual
  channels; the main hole is properly closed.
- **The shuffled-telemetry falsifier is well-constructed.** Shuffling telemetry *between*
  episodes while preserving epoch index correctly isolates telemetry **content** from
  **schedule**, with the schedule signal surviving by design. Pairing it with a schedule-only
  baseline gives two independent routes to the same falsification. Pre-committing that
  *"the demo claim fails honestly"* if the diagonal survives is exactly right.
- **Blindness of `pathology_id` is correctly specified** — *"lives only in the fan record for
  reporting; never enters a telemetry record or the policy's input path"* — blinding by
  construction rather than by convention.
- **I checked the mean-fan-baseline claim and it is correct.** The spec asserts a mean-fan
  baseline would not change the WHICH gradient since Σπ = 1. That holds: for constant `b`,
  `b·∇Σ_a π(a|s) = b·∇1 = 0`. The reasoning for dropping GRPO machinery is sound — with all
  arms measured, this is a full-information objective, not an estimate.

**One wording caution, not a finding:** the WHICH bullet says the objective covers *"all four
seed arms **plus no-op**"*, while `J = Σ_a π(a|s, NOW)·R_a` is explicitly conditional on NOW.
If an implementer reads that as a 5-way softmax including no-op, the no-op decision is
double-counted against the NOW head and the two heads will fight. Tighten to: WHICH is 4-way
over seeds given NOW; no-op enters only as the reward's zero point.

---

## Verdict

There is no headline claim to survive yet — this is a pre-implementation design, so the
question is whether the design **as specified** can produce a defensible headline.

**As written, it cannot** — for two reasons that are each independently sufficient, and both
are cheap to fix now and expensive to fix later:

1. **The fan store has no role field (F6),** so the evaluation corpus and the WHICH training
   corpus are the same bytes with nothing to separate them. Fan-winner agreement and the money
   chart — the demo's two most quotable numbers — would be in-sample fits reported as
   evaluation.
2. **Two of the three pre-flight gates cannot fail (F1, F2),** and the third is
   mis-specified (F3). A row-split separability probe passes on episode identity alone; a
   "no-op wins its share" gate is satisfied by pure noise at exactly 20%. These are the
   project's go/no-go checks, and as written they cannot discharge that role.

**The largest claim the design would support after the cheap fixes** — and it is a genuinely
strong one, well worth having:

> On a frozen set of eval episodes shared across all compared policies, a learned
> telemetry-conditioned policy achieves higher paired lift `R_chosen − R_noop` than random and
> schedule-only baselines, and selects seeds in agreement with the matched-fan argmax at a
> rate materially above chance **and as a stated fraction of the argmax's own stability
> ceiling** — with the money-chart diagonal collapsing under telemetry shuffling. Scoped, as
> the spec already correctly scopes it, to one host, one slot, four authored seeds, four
> canned pathologies, with no universality claim.

Every scope pin the owner set survives this audit intact. Nothing here asks the demo to be
bigger — F1–F17 are about making the numbers it already intends to report *mean what they say*.
Fourteen of the seventeen findings are fixed by adding fields to a dataclass, restating a gate,
or committing a pre-registration — all of which are **free before implementation and costly
after**, which is the strongest argument for acting on this audit now rather than at results time.

---

## Recommended Remediation Order

Split by **what each finding blocks**, which is more actionable than pure severity — two
findings must land before the 30 pilot episodes are spent, or the gates cannot do their job.

### Tier 0 — Before the pilot runs (blocks pre-flight gates)
| # | Finding | Effort |
|---|---|---|
| 1 | **F1** AP-20 — group the separability probe by `episode_id` | Minutes |
| 2 | **F2** AP-03 — restate the no-op gate against the exact 20% null, test the margin | Minutes |
| 3 | **F3** AP-01 — restate gate 3 as a within-fan quantity (pairs with F10) | Minutes |

### Tier 1 — Before any code is written (dataclass fields; free now, costly later)
| # | Finding | Effort |
|---|---|---|
| 4 | **F6** AP-04/20 — `split_role` field + loader assertions | Hours |
| 5 | **F13** AP-14 — `config_hash` + `frozen_at`; mechanise the freeze | Hours |
| 6 | **F8** AP-08 — `policy_version` field | Minutes |
| 7 | **F15** AP-06 — per-arm `status`; define `R_a` for failed arms | Hours |
| 8 | **F7** AP-04 — three-way split; hold out a report test set | Hours |

### Tier 2 — Before eval begins (pre-registration; impossible afterwards)
| # | Finding | Effort |
|---|---|---|
| 9 | **F4** AP-02 — frozen shared eval **`(seed, fan_epoch)`** list, all three policies, stratified by pathology — **fix jointly with F9** | Hours, **no extra GPU** |
| 10 | **F11** AP-10/05 — commit `N_eval`, numeric thresholds, confirmatory/exploratory split | Afternoon |
| 11 | **F12** AP-07 — commit headline horizon = 40; restore a checkable plateau criterion | Minutes |
| 12 | **F9** AP-08 — trigger eval fans policy-independently — **fix jointly with F4** | Medium, real GPU cost |
| 13 | **F17** AP-11 — specify schedule-only baseline training parity | Minutes + 1 run |

### Tier 3 — Before the report is written
| # | Finding | Effort |
|---|---|---|
| 14 | **F10** AP-03 — argmax-stability ceiling on ~30 double-fanned episodes (also closes F3) | ~30 extra fans |
| 15 | **F16** AP-17 — n per cell, marginals, argmax matrix side by side, drop "visibly" | Hours, no compute |
| 16 | **F5** AP-09 — non-additive seeding, per-arm stream digests, bitwise re-run check | Half a day |
| 17 | **F14** AP-13 — size from the UCL on `sd`; re-check contrast at ~200 episodes | Minutes |

---

## Confidence Assessment

**Overall: Medium-High**, with an important and uniform qualifier — **every finding below is
inferred from the specified procedure. None is confirmed by running a corrected analysis,
because no code or data exists.** The catalogue's own standard ("I re-ran the aggregation and
p becomes 0.091" versus "this looks clustered") places this entire audit in the second
category, by necessity rather than by choice.

**Computed and exact (2 of 17):**
- F2 — P(no-op is argmax) = 1/5 under exchangeability. Distribution-free.
- F2 — P(`max_a R_a` > `R_noop`) = 4/5, same symmetry argument.

**High confidence — the defect is readable directly off the spec text or a commit:**
F1 (unit named as "records"), F6 (three quoted passages, no schema field), F4 (seeds unshared),
F11 (no prereg — verified absent by repo search), F12 (horizon change commit-diffed),
F13 (no enforcing mechanism), F9 (trigger dependence is structural), F16 (criterion quoted verbatim).

**Medium confidence — the mechanism is certain, the magnitude is not:**
F3 (mismatch certain; size depends on realised ICC), F7 (sets shared as written; exploitation
may be small), F8 (drift implied by the spec's own warm-up language; magnitude unknown),
F14 (pilot is small; contrasts may be large enough not to matter), F17 (may be authorial intent).

**Low confidence on impact, high on existence:**
F5 (channels genuinely uncovered; may never bite if dropout is unused), F10 (ceiling unmeasured;
could be high, which would shrink this finding), F15 (asymmetry structural; arms may never NaN).

**Explicitly not claimed:** that any of these *will* produce a wrong number. A defect in a
procedure is not always a defect in the result — if the ICC between arms is high and the
designed contrasts are strong, several findings here (F3, F14, F5) will prove immaterial. I
have rated severity by consequence-if-realised, not by tidiness, and said so per finding.

---

## Risk Assessment

False alarms cost real time, and a critic who does not price them is not calibrated.

**Near-zero risk if I am wrong** (the fix is correct regardless, or costs one line):
F1, F2, F4, F6, F8, F11, F12, F13, F16, F17. Grouped splits, shared seeds, recorded provenance
fields, and pre-registration are never *worse* than their absence. If the authors already
intended these, the cost is clarifying sentences.

**Low-Medium risk:**
- **F7** — halving the val set genuinely increases per-episode reward noise. A real trade, and
  if val-set exploitation turns out negligible, the cost was paid for a confirmation. I judge
  the confirmation worth it, but it is not free.
- **F5** — the digest plumbing consumes lines in a file with an ≲800-line budget and a stated
  goal that *"a reader can open the one file and follow the whole loop."* Readability is a real
  success criterion here; this finding is in genuine tension with it.
- **F15** — if arms never fail, the status field is dead weight. Cheap, but not zero.

**Medium risk — the highest-cost recommendation in this audit:**
- **F9** — fanning every eval episode rather than only germinating ones raises eval GPU cost
  materially. If the intended eval set is large, this is the finding most likely to be
  expensive. I believe the metric is genuinely uncomparable across policies without it, but if
  I am wrong about how the authors intend to compute agreement, this buys nothing and costs
  hours of dedicated hardware.
- **F10** — ~30 double-fanned episodes (~150 arm-runs). If the ceiling proves to be ~95%, the
  measurement confirms the metric was fine as-is and the compute was insurance only.

**The risk of acting on this audit as a whole** is that a deliberately-small tech demo accretes
statistical machinery until it stops being readable in 20 minutes — which would defeat its
stated purpose. I have kept Tier 0 and Tier 1 to dataclass fields and restated gate criteria
specifically to avoid this. **If forced to choose only three: F6, F1, F4.** Those three change
what the demo's numbers *mean*, and together they cost roughly a day.

---

## Information Gaps

What I could not check, and the specific artifact that would resolve each:

1. **Every impact number.** No implementation, no fan store. → `experiments/kernel_demo.py`
   plus a pilot fan store; then F1, F3, F5, F10, F15 become computable rather than inferred.
2. **The val split's definition.** The spec never says whether "val" is the CIFAR-10 test set,
   a held-out slice of train, or something else. F7's severity depends entirely on this. → one
   sentence in the spec, or the data-loading code.
3. **Actual arm failure rates.** F15's severity is unknown without them. → failure rate by arm
   from the pilot's 30 episodes.
4. **Realised ICC between fan arms.** Governs how much F3 and F4 actually matter — the
   difference between "worth fixing" and "load-bearing." → per-arm `R_a` from ~30 pilot fans.
5. **Argmax stability (the agreement ceiling).** Cannot be estimated from the spec at all;
   determines whether F10 reframes the headline or merely confirms it. → the F10 measurement.
6. **Intended `N_eval`.** Nowhere stated, so no MDE can be computed and AP-12 could not be
   assessed in either direction. → a pre-registration file (F11).
7. **Whether the schedule-only baseline is trained.** F17 hinges on it. → one sentence.
8. **The intended reading of "all read from the fan store."** F6's severity depends on whether
   the header is loose phrasing or literal. I have audited it as written; the authors may have
   meant something narrower. → author confirmation, or the `split_role` field that makes the
   question moot.

---

## Caveats

**This is a design-only audit. There is no code, no fan store, no results, and no
pre-registration in the repository — I verified this by search, not assumption.** A code-only
audit misses data-dependent defects; this is weaker still, being a *spec*-only audit. It cannot
detect: actual leakage in an implementation that deviates from the spec, actual asymmetric arm
failure, actual val-set exploitation, actual CRN decay, or hardcoded metrics. **A clean bill on
any dimension here is not a clean bill on the implementation.** Re-audit once
`experiments/kernel_demo.py` and a pilot fan store exist — at that point most of the
Information Gaps above close and the inferred impacts become computed ones.

**Scope pins were respected.** The owner-approved pins — tiny demo, one host, four seeds, no
universality claims, end-state-only reward — are not findings and I have not treated them as
such. Where I noted cost-charged utility (Group 5), I filed it explicitly as *not* a finding.
I have flagged statistical validity, not ambition.

**I am auditing the statistics, not the science.** Whether a morphogenetic training loop is
worth demonstrating, whether four canned pathologies are the right vocabulary, and whether the
delta contract is the right envelope for Momir's future candidates are all out of scope.
Whether the evidence would support the claims made about it is in scope, and that is the whole
of what is above.

**Two severity ratings rest on judgement rather than computation.** F12 (AP-07) flags
*pre-installed structure* rather than a committed offence — no horizon shopping has occurred;
I rated it HIGH because prevention costs two lines and cure costs a re-run. F2's severity
depends on reading "meaningful fraction" as an unstated threshold; the exact 20% figure is not
in doubt, but the authors may intend something stricter than the text says.

**Findings count: 17 across all six catalogue groups, plus 8 sound dimensions and 1 wording
caution.** Per the catalogue's discipline, I have neither returned zero findings nor padded to
a quota — every finding cites the spec text at fault, and where the design is genuinely sound
(AP-19, AP-18, AP-02 within-fan, the CRN precomputation, the shuffle falsifier, the mean-fan
baseline algebra) I have said so in one line and moved on.
