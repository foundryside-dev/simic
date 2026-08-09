# Morphogenesis Review — Kernel Demo Design (rev 2)

**Target:** `docs/superpowers/specs/2026-08-09-kernel-demo-design.md` (rev 2, 284 lines)
**Reviewer:** morphogenesis-reviewer (`yzmir-morphogenetic-rl`), SME Agent Protocol
**Date:** 2026-08-09
**Scope discipline:** the owner-approved pins (one host, one slot, four seeds, zero
lifecycle knobs, end-state-only reward, no universality claims) are treated as
**fixed constraints**, not review targets. Every fix below is designed to fit
inside them. No finding recommends widening scope; where a defect could only be
fixed by widening scope, it is reported as a **claim-scoping requirement**
(add a sentence) rather than a build request.

---

## Verdict

**Do not implement as written.** Seven defects are demo-invalidating: each one
either makes a headline number un-interpretable, makes the fan store
un-replayable, or lets the demo fail for a reason that has nothing to do with
the claim being tested. All seven have fixes that are cheap and inside the pins.

The design's core is sound and unusually well-disciplined for a tech demo — the
delta contract is correct, the STE isolation is provably invisible, the
precomputed common future is the right call (and rev 2's reasoning for why
RNG-state cloning is insufficient is exactly right), the WAIT-vs-no-op
factoring is correct, and the freeze discipline plus the shuffled-telemetry
falsifier show the spec is already trying to be falsifiable. The defects below
are almost all in the **measurement and record layers**, not the mechanics.

---

## Part 1 — Demo-invalidating findings (fix before implementation)

### F1 · The money chart's null hypothesis is wrong — CRITICAL

**Spec text at fault** (lines 237-239):

> **Fan-winner agreement**, reported at both grains: five-way agreement with the
> fan argmax including restraint (chance ≈ 20%), and conditional-on-acting seed
> agreement (chance ≈ 25%).

And line 279: *"fan-winner agreement well above both chance rates"* as a success
criterion.

**Defect.** `20%` and `25%` are the chance rates of a *uniform-random* policy.
They are not the null hypothesis the money chart is testing. The seeds are not
exchangeable: `conv_heavy` is 60k parameters bolted onto a 150k host — a 40%
capacity increase — while `norm` is 0.1k. On an *undersized* host that
*plateaus inside the horizon* (line 57), raw capacity is the dominant term in
end-state accuracy for most pathologies. If `conv_heavy` is the fan argmax in,
say, 60% of fans, then a policy that has learned nothing except "always pick
conv_heavy" scores **60% agreement** and the spec reports it as "well above
chance ≈ 25%." The demo would declare success for a constant policy.

The honest null is the **marginal-best-seed rate**: the accuracy of the best
telemetry-blind constant policy, measured on the same fans. The claim
"she reads telemetry" requires beating *that*, not uniform.

**Fix (two parts, both cheap):**

1. Report agreement against three references, not one: uniform chance, the
   **marginal-best-seed policy** (argmax of the seed's overall fan-win rate),
   and the **schedule-only policy** from Measurement 4a. Success criterion
   becomes "clearly above the marginal-best-seed rate," which is the only
   version of the criterion that is a claim about diagnosis.
2. Add a **pre-flight check 0** — *seed-dominance* — to the §"Pre-flight
   validation" block, run before checks 1-3: **no single seed may be the fan
   argmax in more than ~40% of fans, and every seed must win somewhere.** If
   `conv_heavy` dominates, the money chart's diagonal is unachievable *by
   construction* and no amount of policy training fixes it — the pathology
   sampler must be rebalanced (or `conv_heavy` param-matched down) during the
   construction phase, before the freeze.

Check 0 is the single highest-value line in this review: it tells you the demo
is dead **before** you spend a night collecting fans, rather than after.

---

### F2 · The WHEN objective has a zero-gradient absorbing state — CRITICAL

**Spec text at fault** (lines 182-187, 205-206):

> **Never-germinate episodes** produce no fan and train nothing — and that is
> principled, not a gap: with reward defined as `R_chosen − R_noop`, the
> never-intervene trajectory has utility exactly zero by construction.

> **WHEN — online.** The NOW/WAIT decisions train by plain REINFORCE on fresh
> episodes only, reward `R_chosen − R_noop`, small entropy bonus.

**Defect.** The spec correctly maps INV-16 ("Isperia assigns no-op policy
utility exactly zero") onto the reward's zero point — but then conflates *zero
reward* with *zero gradient*. Under plain REINFORCE with no baseline, an
episode that never germinates contributes **no gradient at all**. Therefore:

- The region of policy space where `P(NOW) → 0` is an **absorbing fixed point**.
  Once the policy drifts there — and a run of mild-handicap episodes, where
  germinating correctly earns negative lift, drives it there — it stops
  generating germination events, stops receiving WHEN gradient, and cannot
  recover except by entropy-driven random walk.
- The spec's mitigation (line 210: *"assert during online training that the NOW
  head's outputs actually move"*) is a **detector for the symptom, not a fix for
  the cause**. It converts a silent failure into a loud one, which is worth
  having, but the run still fails.
- Naive fixes are wrong here. A **global** REINFORCE baseline `b` would give
  never-germinate episodes advantage `−b < 0`, pushing toward NOW — which
  actively *punishes correct restraint* in mild episodes. That is exactly the
  "enthusiasm over restraint" failure the spec's own line 75 forbids.

**Fix — forced-exploration collection episodes.** Reserve a fixed fraction ε
(≈20-30%) of *collection* episodes in which germination fires at a **uniformly
random epoch in the decision window**, regardless of what the policy wants,
flagged in the fan record as `decision_source: forced | policy`.

This is a **collection** policy, not a training policy, and that distinction is
what keeps it in scope — no importance weights, no value head, no lifecycle
knob for the controller, no shaped reward term:

- These fans feed **WHICH** unchanged. The spec's own argument (lines 200-204)
  that full-information labelling is off-policy-safe holds exactly as written.
- They establish the empirical **value-of-acting-at-*t*** curve, which is the
  state-dependent quantity a WHEN baseline needs, measured rather than assumed.
- The on-policy REINFORCE gradient still consumes **only** policy-chosen
  episodes. Nothing about the WHEN estimator changes.

One fix closes three findings: this one, F8 (decision-point covariate shift),
and F9 (the seed head being evaluated off the state distribution NOW fires at).

---

### F3 · The matched-arm claim is never verified, and concurrency can break it — CRITICAL

**Spec text at fault** (lines 159-165, 266-271):

> **Precompute the common future** … Every branch sees literally identical images.

> Multiple episode workers across both GPUs (redlined — dedicated hardware);
> several concurrent episode workers per card.

**Defect — two independent halves.**

**(a) Nothing checks it.** Matched arms are the entire epistemic foundation of
this demo — INV-06 (*"paired branches receive identical future minibatches and
equivalent random streams"*) is what makes `R_chosen − R_noop` a causal
quantity rather than a difference of two noisy runs. The design asserts it and
records nothing that could falsify it. A one-line bug in the branch loop (an
arm that re-draws augmentation, an off-by-one in the batch index cursor)
silently degrades every reward in the store, and no plot in Measurement §
would look wrong.

**(b) Concurrency can break it even if the code is correct.** With cuDNN
autotune enabled (`benchmark=True`, the PyTorch default idiom for a fixed-shape
CNN) and several workers per card contending for memory, two arms of the *same
fan* can be assigned different convolution algorithms — different reduction
orders, different numerics. The arms then differ for a reason that has nothing
to do with the seed under test. The spec's determinism claim (line 267,
*"Same seed ⇒ same episode"*) is stated but not defended against its own
runtime plan.

**Fix:**

1. Record a `common_future_hash` **per arm** in the fan record — a hash over the
   arm's actual consumed `(batch_index_order, crop_offsets, flip_masks)`
   sequence. Assert all five match before the record is written.
2. **Pin all five arms of one fan to one device**, run within one worker. Arms
   may never be split across the two cards, and a fan is the unit of work
   scheduled to a GPU (not an arm).
3. Set `torch.backends.cudnn.benchmark = False`,
   `torch.backends.cudnn.deterministic = True`,
   `torch.use_deterministic_algorithms(True)`. Accept the throughput cost; the
   host is 150k params and the data is resident, so it is small.
4. Add a `--selftest` mode: run one episode twice from the same seed and assert
   the two fan records are byte-identical. This is the CI test the determinism
   claim currently lacks, and it is the demo-scale version of INV-05.

---

### F4 · No train/eval split on the fan store — leakage — HIGH

**Spec text at fault** (lines 200-204 vs 233):

> the seed head trains … **over the whole accumulated fan store**, replayed freely

> ## Measurement (**all read from the fan store**)

**Defect.** WHICH trains on the entire store; Measurement reads from the store.
The headline (Measurement 1) says "fresh eval episodes," but Measurements 2, 3
and 4 do not, and nothing in the record structure *prevents* an eval fan from
being appended to the store the offline learner then replays. This is
straightforward train-on-test, and it directly violates INV-32 (*"branches from
one base trajectory never cross splits or inflate independent sample counts"*).

The invariant has a second edge the spec also does not address: the **five arms
of one fan are one unit**, not five samples. Any n, any error bar, any
significance test must count **episodes**, not arms and not fans-times-arms.

**Fix.** Add a `split: "train" | "eval"` field to the fan record, assigned by
the **episode seed** at episode start (before anything is measured), and make it
a hard filter — the WHICH objective's loader asserts `split == "train"`; the
Measurement loaders assert `split == "eval"`. State in the spec that the
independent statistical unit is the **episode**.

---

### F5 · No observation normalization at the boundary — HIGH

**Spec text at fault** (lines 144-151):

> **Telemetry record** (per epoch, a dataclass …): train/val loss, val accuracy,
> loss deltas, per-stage grad-norm mean/var, activation saturation fraction,
> weight norms, epoch index.
> **Embedded tokens…:** a small learned MLP embeds each record into a
> d_model≈64 token.

**Defect.** These fields span several orders of magnitude — saturation fraction
∈ [0,1], loss ≈ 2.3, grad-norm *variance* on an under-normalized host
potentially in the thousands. Nothing normalizes them before the embedding MLP.
`rl-controller-for-morphogenesis` is explicit: *"All scalar features should be
normalized at the observation boundary, not inside the policy network. Without
this, gradient norms in the high tens-of-thousands will dwarf loss-window
features in the low single digits."* The pathology signature the demo most needs
the policy to read — *"spiky grad norms"* for under-normalized — is precisely
the feature whose raw scale will swamp everything else.

**This fails in the worst possible way**: the demo fails for a preprocessing
reason and the result reads as *"the transformer cannot do diagnosis"* — the
exact negative claim the demo exists to refute.

**And the spec's own gate will not catch it.** Pre-flight check 2 (line 224)
uses a **linear probe** over raw telemetry. A regularized logistic regression is
scale-tolerant in a way a small MLP+transformer trained by policy gradient is
not. The gate passes; the transformer still fails. That is a gap between the
gate and the thing it gates.

**Fix.** Fit running mean/std on the ~30 pre-flight random-policy episodes,
**freeze the normalizer statistics at the same moment the pathologies are
frozen**, and persist them (alongside the fan store, and in the record's
provenance block). Do **not** fit the normalizer online during collection —
that makes the observation episode-order-dependent and breaks
*"same seed ⇒ same episode."*

---

### F6 · The strongest baseline is defined but not required — HIGH

**Spec text at fault** (lines 242-246 vs 278-281):

> **Falsifier controls:** (a) a schedule-only baseline policy (epoch index in,
> telemetry ignored) …

> `--eval`/`--report` show: lift > 0 and clearly above random, fan-winner
> agreement well above both chance rates, a visibly diagonal money chart, **and**
> the shuffled-telemetry control collapsing the diagonal.

**Defect.** Measurement 4a *is* the fixed-schedule baseline — the one baseline
that decomposes `lift_from_having_grown` from `lift_from_choosing_well`, and the
only one that isolates controller skill. It is correctly specified. It then
**does not appear in the success criteria at all**. As written, the demo can be
declared successful while losing to a policy that ignores telemetry entirely.

Compounding this: the headline comparator is a **random policy** (line 236),
which is the weakest available bar. Beating random shows the policy learned
*something*; beating schedule-only shows it learned *diagnosis*.

**Fix.** Promote 4a into the success criteria: *"mean lift clearly above the
schedule-only baseline's mean lift, on the same eval episode seeds."* Keep
random as a sanity floor, not the headline. This costs one extra eval pass over
an already-collected set of episodes.

---

### F7 · The fan record cannot be replayed or ablated — HIGH

**Spec text at fault** (lines 171-174):

> The **fan record** (telemetry context, germination epoch, 5 outcomes, arm
> curves, pathology id) is appended to a JSONL store (schema = the dataclass
> that serializes it, defined adjacent).

**Defect.** As enumerated, the record contains **no seeds and no identity**.
Consequences, all concrete:

- **No arm can be re-run.** "Re-run the `attn` arm of fan 412 with a fix" is
  impossible — the episode seed, the seed-module init seed, and the
  common-future seed are all unrecorded. Counterfactual replay capability is
  absent, and with it the ability to ablate a single decision.
- **No provenance.** The store accumulates across policy checkpoints. Without
  `policy_version`, you cannot tell which decisions came from which policy, and
  you cannot detect the distribution shift in F8.
- **Heterogeneous union with no discriminator.** Line 186-187 says
  never-germinate episodes "still land in the store." Those records have no
  germination epoch and no arms — a structurally different shape sharing a JSONL
  file with no `kind` field to switch on. The first reader breaks.
- **Failure status undefined.** Line 174 says "failures … kept," but no field
  records *that an arm failed*. A diverged or OOM'd arm becomes indistinguishable
  from a legitimately bad one, and INV-38's "no silent fallback fabricates
  valid-looking state" is exactly what a missing status field produces.

**Fix.** Make the record explicitly self-describing. Minimum fields to add:

```
schema_version, kind ("fan" | "never_germinated"),
episode_id, episode_seed, split, pathology_id,
policy_version, decision_source ("policy" | "forced"),
normalizer_stats_id,
telemetry_context_hash,
per-arm: { seed_type, seed_init_seed, common_future_hash,
           status ("complete" | "diverged" | "failed"), R_a, curve[] }
```

The demo's scale makes the two-table (step/event) discipline unnecessary — 40
epochs × 5 arms is tiny and the arm curves can live inside the record. But
**identity, seeds, hashes and the kind discriminator are not optional at any
scale**; they are what make the store the "counterfactual atlas early Momir
needs" (line 24) rather than a one-shot log.

---

## Part 2 — Medium findings

### F8 · Decision-point covariate shift (Medium)

The WHICH head trains on `(state, germination epoch)` pairs *the policy itself
chose*. As the policy improves, that distribution concentrates, and the offline
objective — which is unbiased *given the state distribution* — is being
optimized against a non-stationary, self-selected one. The spec's off-policy
argument (lines 200-204) is correct about the *labels* and silent about the
*states*. **Closed by F2's forced-exploration episodes**, provided they run at a
constant rate throughout collection, not only during pre-flight.

### F9 · The governor question, in its in-scope form (Medium)

There is no non-policy veto layer, and for this demo **that is defensible** —
each episode is disposable, the host is never persistent, and a crash-and-burn
arm is deliberately *data* (line 170), so a governor that vetoed would destroy
the measurement the demo wants. The spec should **say so**, in one sentence,
rather than leave the absence unremarked.

But the demo does need the *record-integrity* half of the governor's job, and it
is ~10 lines of non-policy assertion run before any fan record is written:

- all five arms reached the horizon (`status == complete`),
- all five `R_a` are finite,
- all five `common_future_hash` values are equal (F3),
- the telemetry context contains no non-finite values.

This is a gate the controller cannot influence, it produces a structured event
rather than an exception, and it is the correct minimal form of the discipline
here. Recommend adding it as an explicit "fan admission check" step between
spec steps 5 and 6.

### F10 · Non-finite telemetry can reach the policy input path (Medium)

The dataclass discipline (line 145) catches a *missing* field, never a `NaN` or
`inf` one. The under-normalized pathology *deliberately induces* spiky grad
norms; a grad-norm variance that overflows produces a non-finite token, which
produces a non-finite policy gradient, which destroys the controller weights
silently mid-run. Fix: assert finiteness at `TelemetryRecord` construction
(same site, same discipline as the missing-field rule) and clamp-with-a-flag
rather than propagate. `R_a` itself is safe — accuracy is bounded — which is a
genuine strength of choosing accuracy over loss as the reward; worth stating.

### F11 · Measurement 4b is self-inconsistent as written (Medium)

Line 244-245: *"the trained policy re-evaluated with telemetry shuffled between
episodes, **epochs preserved**."* But line 148 places `epoch index` **inside**
the telemetry record. Shuffling the record shuffles the epoch index — the
control contradicts its own qualifier. Since 4b is one of the four success
criteria, this must be resolved: carry the epoch index (and any other
positional feature) **outside** the shuffled payload, so the shuffle replaces
only the diagnostic content.

Related and worth stating explicitly rather than fixing: retaining the epoch
index is **correct**, not a leak. With a fixed 40-epoch horizon, remaining
runway genuinely determines value — germinating at epoch 15 leaves less fossil
time than at epoch 5 — so time is a legitimate feature, and 4b is precisely the
control that separates "uses time because time matters" from "learned a
schedule." Say that in the spec so a reader does not mistake it for a defect.

### F12 · Fan density is measured on the wrong quantity (Medium)

Line 226-229 compares the across-episode spread of `R_a` against the
best-vs-second arm separation. Because the arms share a common future, most of
`R_a`'s variance is **common-mode** and cancels in the paired difference. Testing
raw `R_a` spread is the wrong, systematically over-conservative test: it can
fail — triggering the prescribed "lengthen the horizon" remedy — on a design
whose paired contrast is perfectly adequate. Measure the spread of
`R_a − R_noop` (matched, within-fan) instead. This is the gate that decides
whether the whole demo proceeds; it should test the quantity the demo actually
uses.

### F13 · Trained-vs-random comparison is not paired (Medium)

Line 235-236 compares the trained policy's mean lift to *"the same number"* of
random-policy episodes — same count, not the same episodes. Use **common random
numbers**: run both policies (and the schedule-only baseline from F6) on the
**same eval episode seed set**, so host init, pathology draw and common future
are identical and the comparison is a paired difference. Free variance
reduction; directly in the spirit of the fan design the spec already committed
to.

### F14 · Entropy coefficient manufactures the restraint result (Medium)

Entropy bonuses appear on both heads (lines 203, 206). Entropy regularization is
not reward shaping and does not violate the no-shaping pin — but the NOW head's
entropy coefficient **directly sets the germination rate**, and "restraint rate"
(line 187) is a reported result. A tuned coefficient can manufacture the
appearance of learned restraint. Fix: freeze the entropy coefficients at the
same moment the pathologies and normalizer freeze; report restraint rate
**alongside** the coefficient in force; and state that entropy is a policy
regularizer, not a reward term, so a reader does not read it as a pin violation.

### F15 · No precommitted stopping rule for evaluation (Medium)

The spec establishes exemplary freeze discipline for the pathology sampler
(lines 79-84) and then leaves collection open-ended (*"overnight yields high
hundreds to thousands"*) with no precommitted eval-episode count and no
precommitted decision rule. That is the same test-set-engineering hazard the
freeze discipline was written to prevent, one level up: collect, look at the
money chart, collect more, look again. Fix: precommit the eval episode count
(n), the significance test (paired, non-parametric — Wilcoxon signed-rank on
per-episode lift, episode as the unit per F4), and the pass threshold, **before**
the first eval fan is examined. Extend the existing freeze paragraph to cover
evaluation; it is one sentence and the discipline is already accepted.

### F16 · Trunk interference guard is thin (Medium)

Lines 207-210. One trunk, two objectives with very different densities and
scales; the offline WHICH objective updates far more often and will dominate the
representation. The proposed guard — warm-up plus "assert the NOW head's outputs
move" — is weak on both ends: warm-up does not prevent later drift, and *outputs
moving* is not evidence of *learning*. Stronger and simpler, still one trunk in
the narrative: **freeze the trunk after the offline warm-up and train only the
NOW head online.** If the shared representation is to stay trainable, change the
assertion to a real one — NOW-head lift improving against the schedule-only
baseline (F6), which is the thing you actually care about.

---

## Part 3 — Low findings

| # | Finding | Spec text | Fix |
|---|---|---|---|
| F17 | **Fossilization drops the detach**, changing the gradient path into the host discontinuously at one epoch boundary. Forward value `h + Δ` is continuous, so this is a training-dynamics discontinuity, not a reversibility problem — but it is unmeasured. | line 125-126 | Mark the fossilization epoch on the α(t) plot (Measurement 5) and on arm curves. Do not ramp — that would be a lifecycle knob. |
| F18 | **Optimizer ownership of Δ is unspecified** — same optimizer as host, or separate? Adam state for new params, LR-schedule position at germination. Affects arm matching if handled differently per seed type. | §Lifecycle | State it. Whatever the choice, it must be identical across all four seed arms. |
| F19 | **`R_a` measured on the same val set the policy is optimized against**, with no held-out set. Within-fan pairing means this does not bias the fan winner, so it is low — but the headline is still measured on the selection set. | line 167-169 | One line: split CIFAR-10 train into train/val for `R_a`, report the headline on the 10k test set. Or state explicitly that no generalization claim is made. |
| F20 | **No parameter cost anywhere in `R_a`.** Correct for this demo (accuracy-only end-state is the pin) but it is the mechanism behind F1's dominance risk. | line 167 | No change; note the linkage in the spec so F1's pre-flight check 0 reads as principled rather than arbitrary. |

---

## Part 4 — Claim-scoping requirement (not a build request)

**Static-final baseline.** The pack requires it; this demo does not need to
*run* it. The demo's claim is about **controller diagnosis** — can a transformer
read telemetry and pick the right intervention — not about growth beating an
always-on architecture. A static-final baseline answers a question the demo
explicitly does not ask.

But success criterion *"lift > 0"* (line 279) **reads** as a growth claim, and a
reader will take it as one. The fix is a sentence, not a run: state that
`R_chosen − R_noop` measures *the value of this intervention at this decision
point against not intervening*, and that the demo makes **no claim** that grown
structure beats the same structure present from initialization. That sentence
costs nothing and closes the only place where the spec's stated scope and its
stated success criteria disagree.

---

## Discipline scorecard

| # | Discipline | Verdict | Basis |
|---|---|---|---|
| 1 | Deterministic given seed | **Fail** | Determinism asserted (line 267); no stream separation for controller sampling / seed-module init; no CI test; concurrent-worker + cuDNN-autotune path uncontrolled (F3). |
| 2 | Ablation-friendly schemas | **Fail** | Fan record has no identity, no schema version, no `kind` discriminator across two record shapes, no split column, no reward-mode/provenance axis (F4, F7). Two-table discipline correctly unnecessary at this scale. |
| 3 | Governor as non-policy | **Cannot Determine** | The absence of a governor is undeclared and therefore unjustified in text, and the record-integrity gate the demo does still need is missing (F9). What *can* be verified: no controller-disables-gate anti-pattern appears anywhere — the controller has no gate to disable. That is not the same as passing. |
| 4 | Replay log completeness | **Fail** | No seeds, no observation/context hash, no common-future hash, no policy version, no arm status (F3, F7). |
| 5 | Counterfactual replay capability | **Fail** | Cannot re-run a single arm of a stored fan. Note: per-arm randomness is *structurally* independent of arm ordering (precomputed common future) — the design is right, the record just does not preserve what replay needs (F7). |
| 6 | Baselines run | **Partial pass** | Off-switch and static-initial are structurally built in as the no-op arm — genuinely strong, and better than most published work. Fixed-schedule is specified but not required (F6). Static-final absent, correctly (Part 4). |
| 7 | Multi-seed reporting | **Fail** | No n, no variance, no significance test, no stopping rule, and the independent unit is unstated while the record structure invites counting arms (F4, F13, F15). "Clearly above random" is unfalsifiable as written. |

---

## Cross-discipline root causes

Two root causes generate most of the above.

**Root cause A — the fan record was specified by its *analysis* content, not by
its *provenance* content.** Line 171 enumerates what a plot needs (telemetry
context, epoch, outcomes, curves, pathology id) and stops. Everything a
*re-run* or a *cross-run comparison* needs — seeds, hashes, versions, split,
kind, status — is absent. This single omission produces F3(a), F4, F7, F8 and
half of F9. Fix the record and five findings close together. **This is the
critical path.**

**Root cause B — the measurement section names the right controls and then
omits them from the pass criteria.** The schedule-only baseline (F6) and the
seed-dominance risk (F1) are both cases where the spec demonstrably *knows* the
right comparison and does not make it binding. The success criteria at lines
278-283 are the weakest paragraph in an otherwise rigorous document.

## Critical path

**Fix the fan record schema first (F7), including the split field (F4), the
per-arm common-future hash (F3) and the forced-exploration flag (F2).** It is
the lowest-numbered failing discipline, it is the substrate every other fix
writes into, and — because the store is intended as "the counterfactual atlas
early Momir needs" — it is the one artifact of this demo with a life beyond it.
Retrofitting identity into an append-only JSONL store after a night of
collection means discarding the collection.

Then, in order: **pre-flight check 0 (F1)** before any collection run, because
it can kill the demo cheaply; **normalizer freeze (F5)** and
**forced exploration (F2)** before any policy training; **success criteria
rewrite (F1, F6, F15)** before any eval.

---

## Confidence Assessment

**Overall Confidence:** High (on the design as specified) / Moderate (on
runtime behaviour, since no code exists yet)

| Finding | Confidence | Basis |
|---|---|---|
| F1 wrong null / seed dominance risk | **High** on the null being wrong (arithmetic — lines 237-239 assume a uniform prior); **Moderate** on `conv_heavy` actually dominating (inference from the 60k-on-150k param ratio at line 102 plus "undersized … plateaus" at line 57; unmeasurable before pre-flight runs) |
| F2 zero-gradient absorbing state | **High** — follows directly from "train nothing" (line 184) plus baseline-free REINFORCE (line 205); no code needed to establish it |
| F3(a) no matched-arm verification | **High** — spec lines 159-174 enumerate the record; no hash or assertion appears |
| F3(b) cuDNN autotune under concurrency | **Moderate** — depends on implementation choices not yet made; the risk is real and the mitigation is free, so it is worth pinning regardless |
| F4 no train/eval split | **High** — direct contradiction between line 202 ("whole accumulated fan store") and line 233 ("all read from the fan store") |
| F5 no observation normalization | **High** — lines 144-151 specify the raw fields and the embedding MLP with nothing between them, and lines 150-153 add no normalization layer anywhere in the policy path |
| F5 linear-probe gate will not catch it | **Moderate** — reasoning from the scale-tolerance difference between regularized logistic regression and a policy-gradient-trained MLP; not empirically verified |
| F6 schedule-only absent from criteria | **High** — verified by direct comparison of lines 242-246 against lines 278-283 |
| F7 record cannot be replayed | **High** — the enumerated field list at line 171 contains no seed and no identity |
| F9 governor absence defensible | **Moderate** — a judgement call about this demo's disposability, not a fact about the text |
| F11 4b self-inconsistency | **High** — line 148 places epoch index in the record; line 245 says epochs are preserved under record shuffling |
| F12 fan density on wrong quantity | **High** — line 227 says "spread of `R_a` across episodes"; common-mode cancellation under a shared common future is a property of the design, not an assumption |
| F17 fossilization discontinuity | **Moderate** — mechanism is certain from lines 118-126; whether it is visible in practice is not |

## Risk Assessment

**Implementation Risk of adopting this review:** Low
**Reversibility:** Easy — every fix is pre-implementation, and no fix touches
the scope pins, the seed menu, the lifecycle, or the reward definition.

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| Demo collects overnight, then the money chart proves unachievable because one seed dominates | **Critical** | Medium | F1 pre-flight check 0 — costs ~30 episodes, run before any collection |
| Fan store collected without identity/seeds must be discarded and re-collected | High | **High** if F7 is deferred | Fix the record schema before the first `--collect` run; it is the critical path |
| Policy training collapses to always-WAIT and the run is written off as "the transformer can't learn" | High | Medium | F2 forced-exploration episodes; the spec's existing assert becomes the detector of last resort rather than the only defence |
| Headline reported against a uniform-chance or random-policy null and later withdrawn | High | Medium | F1 + F6 — promote marginal-best-seed and schedule-only into the success criteria |
| Demo fails for scale/preprocessing reasons and is read as a negative result about the approach | High | Medium | F5 normalizer, frozen with the pathologies |
| Arms of one fan silently diverge; every reward in the store is quietly degraded | High | Low-Medium | F3 — per-arm common-future hash + fan-level device pinning + deterministic kernels |
| Over-correcting: adding governor/lifecycle machinery in response to Discipline-3 language | Medium | Low | Explicitly out of scope — F9 is a ~10-line record-integrity assertion, nothing more |
| Fixes add enough machinery that the file exceeds ≲800 lines and stops being readable | Medium | Low-Medium | Everything above is fields, assertions and criteria text; the only new *logic* is forced-exploration episode selection (a few lines) and the arm-admission check |

## Information Gaps

The following would sharpen this analysis:

1. [ ] **Empirical fan-win distribution across the four seeds.** F1's severity is
       inferred from the parameter ratio. Thirty random-policy pre-flight
       episodes would settle it, and that run is already in the spec.
2. [ ] **Whether the ~30 pre-flight episodes are intended to be reusable as the
       normalizer-fitting set.** F5's fix assumes yes; if they are discarded, a
       separate fitting pass is needed.
3. [ ] **The intended `val` set.** Whether "val accuracy" means the CIFAR-10 test
       split or a held-out slice of train determines whether F19 is Low or
       Medium.
4. [ ] **Optimizer ownership of the delta parameters** (F18) — not stated
       anywhere in the spec.
5. [ ] **Whether esper-lite's fan/branch harness has an existing record schema**
       worth inheriting. AGENTS.md forbids importing its code, but its *schema
       lessons* are exactly the scar-catalogue material F7 is trying to avoid
       re-learning. Not inspected — `~/esper-lite` is outside this repo.
6. [ ] **No implementation exists.** `src/simic/` contains only `__init__.py` and
       `py.typed`; `experiments/` does not exist. Every finding is against the
       design text, and none is verified against behaviour.

## Caveats & Required Follow-ups

### Before relying on this analysis

- [ ] Confirm F1 empirically with the pre-flight episodes before treating the
      seed-dominance risk as real; the *null-hypothesis* half of F1 is
      arithmetic and stands regardless.
- [ ] Decide the `val` set question (gap 3) before F19 is filed either way.
- [ ] Re-read F2's fix against the "zero lifecycle knobs for the controller" pin.
      My reading is that forced-exploration episodes are a **collection-harness**
      property invisible to the controller's action space, and therefore inside
      the pin. If the owner reads it as a knob, the finding still stands and
      needs a different fix — the defect is real either way.

### Assumptions made

- The scope pins (lines 37-51) are fixed and owner-approved; I did not evaluate
  whether they are the right pins.
- "Val accuracy" is a single fixed evaluation set shared by all arms of a fan
  (which is what makes within-fan pairing valid).
- The policy samples stochastically during collection and the WHEN head is
  trained on-policy, per lines 205-206.
- The four seeds are trained by the same optimizer configuration (F18 notes this
  is unstated).

### Limitations

This analysis does **not** cover:

- The underlying RL algorithm's hyperparameters (REINFORCE step size, entropy
  coefficient magnitude, warm-up length) → `yzmir-deep-rl/rl-training-diagnostician`
- Host-side training mechanics beyond the isolation contract — the CNN design,
  the STE's numerical behaviour, the α waveform shape →
  `yzmir-dynamic-architectures`
- Low-level PyTorch concerns beyond the determinism flags in F3 →
  `yzmir-pytorch-engineering`
- Statistical power — how many eval episodes n actually needs for the F15 test
  → `yzmir-counterfactual-statistics` (the paired-difference structure here is
  squarely in that pack's territory and worth a second opinion before n is
  precommitted)
- Whether the demo's constitutional framing (the Nissa/Kasmina provenance
  question deferred at lines 46-51) is correctly deferred — that is a
  constitutional question, not a morphogenesis-discipline one

### Recommended next steps

1. Revise the fan-record dataclass in the spec (F7 + F4 + F3 + F2 flag) — this
   is the critical path and everything else writes into it.
2. Add pre-flight check 0 (F1) and fix check 3's statistic (F12).
3. Rewrite the success criteria block (lines 278-283) against F1, F6 and F15.
4. Add the normalizer to the freeze paragraph (F5) and the entropy coefficients
   with it (F14).
5. Add the fan-admission integrity check and the one-sentence statement of why
   there is no governor (F9), plus the claim-scoping sentence (Part 4).
6. Then implement, with `--selftest` (F3.4) written before `--collect`.
