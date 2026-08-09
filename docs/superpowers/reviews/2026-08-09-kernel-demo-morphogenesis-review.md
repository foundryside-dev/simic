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

---
---

# Round 2 (rev 3)

**Reviewed:** `docs/superpowers/specs/2026-08-09-kernel-demo-design.md` @ 244accb (478 lines)
**Round-1 baseline:** rev 2, 20 findings + one claim-scoping requirement.

## Verdict

**Round 1 is discharged.** 19 of 20 findings closed, 1 partially closed, 1 not
closed. Critically, the closures are **structural, not cosmetic** — I checked
each fix against the mechanism it was supposed to discharge rather than against
the `(closes: …)` label, and in four cases the spec fixed the root cause more
thoroughly than I asked for:

- **The twin arm** (step 3) is strictly better than the per-arm
  `common_future_hash` I proposed. A hash proves the *inputs* matched; a
  bitwise no-op re-execution from the snapshot proves the whole
  snapshot/restore/executor path matched, continuously, on every fan. It
  converts my one-time assertion into a standing invariant.
- **Median/IQR normalization** (line 222-226) is the right choice over the
  mean/std I suggested — the spiky-grad-norm pathology is precisely where a
  mean/std normalizer would be dragged around by the outliers that carry the
  signal.
- **The FOSSILIZING β-ramp** (line 183-187) is a real fix where I had only
  asked for a plot marker. `lerp(h.detach(), h, β)` being value-identical to
  `h` for every β is a genuinely elegant way to ramp gradient coupling without
  touching the forward value, and it discharges F17 properly rather than
  documenting around it.
- **Deleting REINFORCE entirely** discharges F2, F8 and F16 at the root
  instead of patching each. Removing the policy from its own data-supply loop
  is the correct structural answer, and it is a strictly stronger fix than the
  forced-exploration fraction I proposed.

The Class 1 determinism contract, the `derive(run_seed, ns, i)` namespacing,
the base-run-as-no-op-arm economy, and the oracle-ceiling concept are all
additions I did not ask for and that improve the design.

**Fourteen new findings** follow. Two are High and would leave a headline
number unsupported or a training run undiagnosable; none require widening the
scope pins. The two newest surfaces — schedule-driven collection and the
teacher-forced eval grid — are where most of them live, as expected.

---

## Part 1 — Round-1 disposition

| # | Round-1 finding | Verdict | Evidence in rev 3 |
|---|---|---|---|
| F1 | Money-chart null wrong (uniform prior) | **Closed** | Uniform rates not reported at all (L412); nulls are measured majority-class + schedule-only (L413-415). Pre-flight gate 4 (L368-371) is the seed-dominance check, with the ~40% threshold. See N4 for a residual on *which accuracy* defines the argmax. |
| F2 | WHEN zero-gradient absorbing state | **Closed (root cause removed)** | REINFORCE deleted (L317-324); collection germination comes from a fixed randomized schedule (L248-255), so the policy cannot gate its own data. Stronger than the fix I proposed. An *optimization-side* analogue is filed fresh as N5 — it is a different mechanism, not a reopening. |
| F3 | Matched-arm integrity unverified + concurrency | **Closed, over-delivered** | Twin arm (L267-272), all arms one device (L276-279), full Class 1 flag set (L66-85), `common_future_hash` in schema (L302), `--selftest` (L454). Residuals N3, N11. |
| F4 | No train/eval split — leakage | **Closed** | `split_role ∈ {preflight, train, eval}` (L298); loader asserts `split_role == "train"` on every record entering a gradient step (L339-340). Residual N2 concerns a *different* split. |
| F5 | No observation normalization | **Closed, over-delivered** | Median/IQR per-feature normalizer fitted on pre-flight, frozen with the pathologies (L222-226). The spec also names the linear-probe-gate gap explicitly. |
| F6 | Schedule-only baseline not required | **Closed** | Now a pre-registered pass threshold (L431) and a success criterion (L473-474). |
| F7 | Fan record cannot be replayed or ablated | **Partially closed** | Schema at L295-304 carries everything I asked for except **`schema_version`** — see prose below. `--replay` (L311-315) with env-mismatch refusal is more than I asked for. |
| F8 | Decision-point covariate shift | **Closed** | Schedule-driven collection (L248-255) removes the policy-induced state distribution entirely. |
| F9 | Governor / arm-integrity gate | **Closed, over-delivered** | Twin arm (step 3), bitwise host-weight assertion at end of TRAINING (step 6), `status="diverged"` with retained curves and per-seed failure rates (step 8). Residual N3 is about how step 6 classifies a failure, not whether the gate exists. The one-sentence *declaration* of why there is no governor is still absent — noted, not blocking. |
| F10 | Non-finite telemetry reaches policy input | **NOT closed** | See prose below. |
| F11 | Falsifier 4b self-inconsistent | **Closed** | L416-421 resolves it: histories swapped whole, epoch alignment preserved positionally, epoch-index field position-consistent by construction. Residual N6 is a *different* defect in the same control. |
| F12 | Fan density on wrong quantity | **Closed, over-delivered** | Gate 3 (L358-367) measures within-fan paired quantities, and correctly notes that under Class 1 a naive re-execution measures a trivial zero — hence the refanned noise floor. That correction is better than my finding. Residuals N9, N8. |
| F13 | Trained-vs-random not paired | **Closed** | `N_eval = 100` seeds shared by every policy, paired by seed (L390-391). |
| F14 | Entropy coefficient manufactures restraint | **Closed, over-delivered** | Frozen with the block, reported beside restraint rate (L334-338), and expressed as a fraction of measured fan density — a principled unit I had not suggested. |
| F15 | No precommitted stopping rule | **Closed** | Pre-registered numbers block (L423-435): N_eval, thresholds, test, one-shot evaluation. Residual N7 concerns the test's handling of zeros; N2 concerns a *different* missing stopping rule (policy training). |
| F16 | Trunk interference guard thin | **Closed** | Both heads now train offline on the same store; the interference mechanism is gone with REINFORCE. Residual N5. |
| F17 | Fossilization gradient-path discontinuity | **Closed, over-delivered** | FOSSILIZING β-ramp sub-stage (L183-187). |
| F18 | Optimizer ownership unspecified | **Closed** | SGD + Nesterov, seed params as a second group at germination, byte-identical host group ordering (L191-197). Choosing SGD over Adam also dissolves several sibling-review findings. |
| F19 | Val/test conflation | **Closed** | 5k/5k split by fixed seed, loaders assert the partition (L94-98). Residual N4. |
| F20 | Param cost / dominance linkage | **Closed** | Gate 4 (L368-371) states the capacity-dominance rationale explicitly. |
| Part 4 | Claim-scoping sentence | **Closed** | L24-29 is a better version than I asked for. But it now asserts "at better moments," which N1 shows is unsupported by the eval battery. |

### F7 residual — `schema_version` is absent

The schema at L295-304 is otherwise complete. It has no `schema_version` field.
This is a small gap with a specific consequence: the store is explicitly
intended to outlive the demo as "the counterfactual atlas early Momir needs"
(L34-36), so it *will* be read by code that was not written against this
revision of the dataclass. `config_hash` and `frozen_block_hash` identify the
*run*, not the *record format* — a reader can detect that a record came from a
different configuration but not that it should be parsed differently. One
field. **Severity: Low, cost: one line.**

### F10 — not closed

Rev 3 handles non-finite **arm outcomes** thoroughly (step 8: `status="diverged"`,
`R_a = null`, curves retained, encoder maps non-finite to `null` rather than
bare `NaN`). It does not handle non-finite **telemetry fields**.

The record contract at L218-221 still says only that a missing field is a
construction error. The generalized blindness rule (L116-121) constrains fields
to be *deterministic functions of host state* — a `+inf` grad-norm variance
satisfies that rule perfectly. The median/IQR normalizer maps `inf` to `inf`.
The path is: under-normalized pathology (deliberately induced, L108) → grad-norm
variance overflows → non-finite token → non-finite policy gradient → policy
weights destroyed silently mid-`--train`.

The demo is *designed* to produce hosts with spiky gradients, so this is not a
remote edge case; it is the headline pathology. Fix is unchanged from round 1
and is one assertion at the same site as the missing-field rule: assert
finiteness at `TelemetryRecord` construction, clamp-with-a-flag rather than
propagate, and record the clamp in the fan record. **Severity: Medium.**

---

## Part 2 — New findings

### N1 · Nothing in the eval battery isolates WHEN — HIGH

**Spec text at fault:** L24-27 (*"picks better interventions, **at better
moments**, than doing nothing"*), L392-394 (lift protocol), L397-403 (frozen
grid).

Three separate gaps compose into one hole:

**(a) The live decision rule is undefined.** L392 says each policy "plays its
episode live (its own germination choices)." Nothing states how the NOW logit
`p` becomes an action — sampled Bernoulli, thresholded at 0.5, thresholded at
something else. This materially changes the result and is currently
implementation-defined.

**(b) The trained NOW objective is pointwise "now vs never," so the natural
live rule is greedy-earliest.** `J_now = p·(Σ_a π(a|s)·R_a^val) + (1−p)·R_noop^val`
(L330-332) is evaluated at each labeled decision point independently. Its
optimum at state *s* is `p = 1` iff acting at *s* beats never acting from *s*.
It contains no comparison against acting at *s+1*. A policy that walks the
decision window and fires at the first epoch where that condition holds is
**exactly optimal for the objective it was trained on** — and it is
germinate-as-early-as-viable, not "at better moments."

The spec is aware the data supports better: L242-243 says fans at different
epochs of one episode share one baseline, so the store "natively contains
now-vs-later evidence within an episode." That is true. `J_now` does not
consume it. The evidence is collected and then discarded by the objective.

**(c) No null in the eval battery would detect this.** The frozen grid
(L397-403) is teacher-forced at pre-registered epochs — it measures WHICH,
correctly and deliberately. Live lift measures WHICH+WHEN jointly, and a
greedy-earliest policy scores positive lift. Schedule-only is telemetry-blind,
so beating it establishes "telemetry helps," which both heads contribute to.
**There is no comparison anywhere in the protocol whose difference is
attributable to WHEN.**

**Fix — one null, nearly free, plus one sentence:**

1. Add a **fixed-epoch null**: the *trained WHICH head* with germination forced
   at a single pre-registered epoch, run on the same 100 paired eval seeds. No
   retraining, no new objective, no new collection — it reuses the trained
   policy and the existing battery. `trained_live_lift − fixed_epoch_lift` is
   the WHEN contribution, measured directly. Pre-register it alongside the
   schedule-only threshold.
2. **Specify the live decision rule** explicitly in the spec (L392).
3. If the fixed-epoch null is not beaten, **drop "at better moments" from L26**
   and report the demo as a WHICH result. That is an honest, zero-cost outcome
   and the claim-scope paragraph is already written in the right style to
   absorb it.

I am deliberately *not* recommending a now-vs-later training objective. The
owner removed REINFORCE to simplify the learning story; adding an objective
back immediately would trade that gain away. Measure WHEN first; only if it is
provably absent is a training change worth discussing.

### N2 · No held-out set inside the train split, and no stopping rule for `--train` — HIGH

**Spec text at fault:** L298 (`split_role ∈ {preflight, train, eval}`), L428
(*"Collection: 300 train-namespace episodes"*), L428-429 (*"evaluated once, no
peeking before collection completes, no augmenting after"*).

The eval protection is correct and I do not want it weakened. But it leaves
`--train` with **no signal at all for when to stop.** There are exactly three
namespaces; `train` is monolithic; `eval` is one-shot and un-peekable. So the
policy is trained for... some number of steps, chosen how?

The data volume makes this acute rather than theoretical. 300 episodes × 1–2
scheduled fans ≈ **450 fans**, each labelling 4 arms, against a ~100k-parameter
causal transformer over 40-token sequences. That is a small corpus for that
capacity, and rev 3 *reduced* it from rev 2's "high hundreds to thousands" while
simultaneously making it non-augmentable. Overfitting is the expected outcome,
not a tail risk — and with no held-out signal it is **indistinguishable from
"the approach does not work."** That is the same false-negative class as round-1
F5: the demo fails for a fitting reason and reads as a negative result about the
claim.

**Fix — partition data you already have, using machinery you already built:**

1. Split the `train` namespace into `train` / `tune` **by episode** (grouped —
   all fans of an episode go to the same side, per INV-32). The
   `derive(run_seed, ns, i)` namespacing already supports this; it costs a
   fourth `split_role` value and one loader assertion.
2. Select the policy checkpoint on `tune`. Never touch `eval`.
3. Report the `tune` learning curve in `--report`. This is what makes "we needed
   more fans" diagnosable rather than fatal — and if the curve is still climbing
   at 450 fans, that is a cheap, honest finding rather than a failed demo.

Note this also gives `policy_checkpoint_id` (already in the schema, L300)
something principled to identify.

### N3 · Step 6's assertion misclassifies legitimate seed divergence as a harness bug — MEDIUM-HIGH

**Spec text at fault:** L280-283.

> **Assertion:** host weights are bitwise identical across all arms at the end
> of TRAINING (STE forward is value-exact and the host backward is unaffected
> by Δ, so divergence = harness bug…)

The reasoning is correct in exact arithmetic *and* in IEEE-754: `Δ − Δ.detach()`
is exactly `0.0` and `h + 0.0` is exactly `h`. The assertion is sound. **Except
when Δ is non-finite** — then `Δ − Δ` is `NaN`, `h + NaN` is `NaN`, and the host
is destroyed during the stage the spec describes as "provably invisible."

That case is not a harness bug. It is a seed whose delta overflowed — a
legitimate arm divergence, and one this demo goes out of its way to produce
(deliberately pathological hosts, a `conv_heavy` arm at 40% of host capacity,
crash-and-burn arms wanted as a headline plot at L286-287). The trust-region
term makes it less likely, not impossible.

As written, the two mechanisms collide: step 8 says a non-finite arm is recorded
as `status="diverged"` and the fan is kept; step 6 says any bitwise mismatch is
a harness bug. A non-finite Δ triggers step 6 first, and the run aborts on an
event step 8 explicitly plans for.

**Fix:** condition step 6 on arm finiteness. Check `isfinite(Δ)` first; if
non-finite, route to step 8 (`status="diverged"`, curves retained, fan kept) and
do **not** evaluate the bitwise assertion for that arm. The assertion then means
what it is supposed to mean — *given a finite delta*, any host divergence is a
harness bug — and keeps its full diagnostic force for the other arms.

### N4 · Which accuracy defines the fan argmax is undefined, and the oracle ceiling does not bound that noise — MEDIUM-HIGH

**Spec text at fault:** L96-98 (*"Test accuracy … is the **only** accuracy any
reported metric uses"*), L284-286 (`R_a^val` trains, `R_a^test` reports),
L407-411 (oracle ceiling).

Agreement, the money chart, and pre-flight gates 1/2b/4 are all defined against
"the fan argmax." Rev 3 now has **two** per-arm rewards and does not say which
one defines it. Both readings are defective:

- **Test-argmax** (which L98 mandates for reported metrics): the policy is
  trained on val labels and scored against test labels. With 5k/5k splits and
  arms frequently separated by well under a point of accuracy, val-argmax and
  test-argmax will disagree on a material fraction of fans. Agreement is
  depressed by pure label noise.
- **Val-argmax**: consistent with training, but contradicts L98.

Either way, the **pre-registered thresholds at L432-434** — "≥ majority-class
null + 15 points" and "≥ 60% of the oracle ceiling" and "row-argmax matches the
designed winner for ≥ 3 of 4 pathologies" — were committed against an
unquantified noise floor.

And the oracle ceiling does not rescue it. The ceiling (L407-411) measures
argmax stability across **re-drawn common futures** — a different and equally
real noise source, but not this one. Nothing in the protocol bounds val↔test
argmax disagreement.

**Fix, and it is free because both numbers are already stored per arm
(L302-303):**

1. State explicitly which accuracy defines the fan argmax for agreement and for
   the money chart. Recommend **val** for agreement (consistency with the
   training label is what "agreement" means) and **test** for lift and all
   reported accuracy levels, with L98 amended to say so rather than reading as
   an absolute.
2. Add **val↔test argmax agreement** to the ceiling measurement. It is a
   two-line computation over data already in the store, and it converts the
   ceiling from bounding one noise source to bounding both.
3. Re-derive the L432-434 thresholds against the combined ceiling before freeze.

### N5 · The two objectives' combination is unspecified; one reading attenuates WHICH's gradient — MEDIUM

**Spec text at fault:** L326-332.

The spec lists `J_which = Σ_a π(a|s)·R_a^val` and
`J_now = p·(Σ_a π(a|s)·R_a^val) + (1−p)·R_noop^val` and never states how they
combine into one loss, nor whether `π` inside `J_now` carries gradient.

If both are summed and `π` is live in both, there is no problem — π receives
`(1+p)·∇(Σπ R_a)`, which never vanishes. But a plausible reading is that
`J_now` is the composed objective and `J_which` is descriptive, in which case
`∂J_now/∂π ∝ p`: if the NOW head saturates toward 0 early — which it will while
π is near-uniform and `Σπ R_a ≈ mean_a R_a` sits below `R_noop` for any
pathology where three of four seeds are wrong — then WHICH's gradient is scaled
toward zero, π stays uniform, and `p` stays off. That is round-1 F2's absorbing
structure re-expressed in the offline optimization. The data-supply half is
genuinely and permanently fixed; this is a distinct mechanism in a different
place.

**Fix — specify, do not add machinery:** state the total loss explicitly
(`L = −(J_which + J_now) + entropy terms`) and **detach `π` inside `J_now`**.
Detaching makes the NOW head's target "act if the *current* WHICH policy's
expected value beats no-op," which is the correct decision-theoretic target for
the composed policy, and it removes the coupling entirely. The cost is that π no
longer receives pressure toward states where acting matters — an acceptable
trade when the state distribution is fixed by the exploration schedule anyway.

### N6 · The falsifier's swap can preserve the signal it is meant to destroy — MEDIUM

**Spec text at fault:** L416-421.

> the trained policy is re-scored on the frozen grid with telemetry *histories
> swapped between eval episodes of the same horizon*

Every eval episode has horizon 40 (L425), so "same horizon" is not a constraint
— the swap is effectively unrestricted. Roughly a quarter of unrestricted swaps
pair episodes **of the same pathology**, and a same-pathology swap *preserves
the diagnostic content*: the policy reads under-normalized telemetry and picks
`norm`, correctly, on an episode that genuinely is under-normalized.

So the diagonal partially survives **by construction**, and the pass criterion
— "shuffled-telemetry agreement collapses to within the null's CI" (L434-435) —
can fail for a policy that is doing exactly the diagnosis the demo claims. This
is a false negative on the demo's own honesty check, which is the worst place to
have one.

**Fix:** constrain the swap to a **derangement across pathology classes** —
every episode receives a history from an episode of a *different* pathology.
One line in the shuffle construction, and it makes the control mean what it
says.

### N7 · Wilcoxon drops zero-difference pairs, so effective n is not the pre-registered 100 — MEDIUM

**Spec text at fault:** L392-396, L430-431.

> Never-germinating scores exactly 0 by construction. Statistic: Wilcoxon
> signed-rank on per-episode paired lift, episode as the unit.

The unit choice is right (INV-32, closes round-1 F4's second edge). But the
standard Wilcoxon signed-rank procedure **discards zero-difference pairs before
ranking**. For the "trained lift > 0" test, every episode where the policy
correctly restrained contributes exactly 0 and is dropped. If restraint is 30%
— which the design *wants*, since the mild pathology is one of four and no-op is
its designed winner — the headline test runs on ~70 pairs, not the
pre-registered 100, and the dropped episodes are precisely the ones where the
policy did the right thing.

The paired trained-vs-schedule-only test is less affected (only pairs where both
policies score identically drop out), but the effective n there is also not 100.

**Fix — pre-register the handling, do not change the test:**

1. State that the lift test is **conditional on acting**, and report the
   effective n alongside the p-value.
2. Report the restraint rate as a first-class number beside it.
3. Let **restraint-regret on the frozen grid** (L404-406, already specified and
   a good metric) carry the restraint half of the claim — it distinguishes "0
   from correct restraint" from "0 from leaving value unclaimed," which is
   exactly what the dropped pairs contain.

Optionally use Pratt's method (retains zeros in the ranking) if a single
all-episode number is wanted; either choice is fine, but it must be committed
before freeze.

### N8 · Pre-flight gates treat fans as independent when they cluster by episode — MEDIUM

**Spec text at fault:** L344-379, specifically gate 1's binomial test.

The base run is the no-op arm (L239-241), and multiple fans of one episode share
that single baseline (L242-243). So within an episode, every fan's
`R_a − R_noop` shares one common error term — the fans are **positively
correlated by construction**, not independent draws.

Gate 1 runs a **binomial test** on no-op win rate across fans. Gate 4's ~40%
dominance threshold and gate 3's density averages aggregate across fans the same
way. With 1–2 fans per episode the inflation is modest, but a binomial test is
an explicit independence claim and this is the same INV-32 clustering issue the
eval protocol handles correctly one section later.

**Fix:** cluster the pre-flight gates by episode — either use one randomly
chosen fan per episode for gate 1's binomial test, or cluster-bootstrap by
episode for all three gates. The eval protocol already made the right choice;
the gates should match it.

### N9 · Refanning must re-run the no-op arm — MEDIUM-LOW

**Spec text at fault:** L363-367 and L407-411.

Refanning re-draws the common future from the snapshot to measure how much `R_a`
moves under irrelevant conditions. Correct idea, and the observation that a
naive re-execution measures a trivial zero under Class 1 is sharper than my
round-1 F12.

But the no-op arm **is the base run** (L239-241), and the base run's tail was
trained under the *original* common future. If the refan re-runs only the four
seed arms under the new draw and reuses the original `R_noop`, then every
`R_a − R_noop` in the refan mixes two draws, and the no-op arm gets a systematic
advantage or disadvantage that is pure artifact.

**Fix:** state that a refan re-runs **all five arms including a fresh no-op
continuation** from the snapshot under the re-drawn future. This costs the ~20%
the base-run economy saved, but only on the ~10 pre-flight and ~30 eval refan
points — a rounding error against 300 collection episodes.

### N10 · `policy_run` is a declared record kind with no definition — MEDIUM-LOW

**Spec text at fault:** L298 (`kind ∈ {fan, policy_run}`).

`policy_run` appears exactly once in the spec and is never defined. The schema
enumerated at L295-304 is fan-shaped: `fan_epoch`, `common_future_hash`, a
per-arm array. A live eval episode has one chosen arm and a base run — a
different shape.

This is round-1 F7's heterogeneous-union defect, half-reintroduced by the rename
from my proposed `kind ∈ {fan, never_germinated}`. The `kind` discriminator
exists, which is the important half; the second kind's fields do not.

**Fix:** either define `policy_run`'s fields explicitly, or state that it shares
the fan shape with a single-element arm array and a null `fan_epoch` when the
policy never germinated. Either is fine; leaving it undefined means the first
reader guesses.

### N11 · Twin-arm abort granularity is unspecified — LOW

**Spec text at fault:** L269 (*"any divergence aborts collection"*).

The strictness is **correct** and I am not recommending it be softened — a
bitwise determinism claim that tolerates a divergence rate is not a bitwise
claim. The gap is only that "aborts collection" does not say whether it aborts
*this episode* or *the whole run*, and the two have very different operational
consequences for an overnight 300-episode collection across several workers.

**Fix:** say which. If the whole run — which is defensible — the fan record for
the failed episode should still be written with a `twin_divergence` status so
the failure is diagnosable from the store rather than only from a stack trace.

---

## Part 3 — Low findings

| # | Finding | Spec text | Fix |
|---|---|---|---|
| N12 | **Oracle ceiling estimated from ~30 points.** A proportion from n=30 carries roughly ±18pp at 95%. The pre-registered "≥60% of the oracle ceiling" threshold divides by a noisy denominator, so the gate's effective strictness is unknown at freeze time. | L407-411, L433 | Report the ceiling with a CI and pre-register the rule against its **lower** bound; or raise n. Compounds with N4 — fix N4 first, then re-derive. |
| N13 | **Trust-region minimizer formula drops `‖h‖²`.** With `L(Δ) ≈ L(0) + g·Δ + λ‖Δ‖²/‖h‖²` (‖h‖² detached), the minimizer is `Δ* = −g‖h‖²/(2λ)`, not `−g/(2λ)`. Also a **notation collision**: `g` is the scalar gain at L143 and the loss gradient at L177. | L173-179 | Correct the formula and rename one of the two `g`s. The design intent is right; the stated algebra is what an implementer will copy. |
| N14 | **`derive(run_seed, ns, i)` is unspecified.** The namespacing design is right, but arithmetic mixes (`seed + i`) collide and wide-multiply mixes overflow `manual_seed`. | L124-125, L273-275 | Specify it as a hash-based mix (e.g. truncated SHA-256 of the tuple) masked to 64 bits. One line, and it is a documented footgun in this domain. |
| N15 | **Pre-flight retune rounds are unbounded and undisclosed.** Eval is properly protected so this is not test-set engineering — but a sampler that needed fifteen rounds to pass gate 2b is a different object than one that passed first try, and nothing records which. | L382-384 | Record the retune-round count and the gate that failed each round in the frozen block; report it. Same disclosure discipline already accepted for the freeze. |
| N16 | **Eval grid epochs vs collection schedule distribution.** The exploration schedule draws uniformly from the decision window (L250-252); the eval grid uses "pre-registered epochs" (L398). If the two distributions differ, the teacher-forced agreement is measured off the training state distribution. | L250-252 vs L398 | State that the grid's `fan_epoch`s are drawn from the same distribution as the exploration schedule. |

---

## Round 2 discipline scorecard

| # | Discipline | Round 1 | Rev 3 | Basis |
|---|---|---|---|---|
| 1 | Deterministic given seed | Fail | **Pass** | Class 1 contract with the full flag set (L66-85), namespaced seeds, order-independent arm init, `--selftest`, and the twin arm as a continuous verifier rather than a one-time test. Residual N14 (`derive` unspecified) is a specification gap inside a sound design. |
| 2 | Ablation-friendly schemas | Fail | **Pass** | Provenance-complete record (L295-304), sharded writes with content-ordered canonical merge (L306-309). Two gaps: no `schema_version` (F7 residual), `policy_run` undefined (N10). Neither undermines the design. |
| 3 | Governor as non-policy | Cannot Determine | **Pass** | The substance is present: twin arm, cross-arm bitwise assertion, diverged-arm status with retained curves and reported per-seed failure rates. Residual N3 (the assertion misclassifies a legitimate divergence) is a bug in the gate, not an absence of one. The one-sentence declaration of *why* there is no governor is still missing — worth adding, not scorecard-blocking. |
| 4 | Replay log completeness | Fail | **Pass** | `--replay` by re-derivation under the recorded config, env-block mismatch **refuses** rather than warns (L311-315). |
| 5 | Counterfactual replay | Fail | **Pass** | Any fan re-derivable from `episode_seed` + `fan_epoch`; refanning is a first-class operation used for the noise floor and the ceiling. Residual N9. |
| 6 | Baselines run | Partial | **Pass** | Schedule-only required in the pass thresholds; measured majority-class null replaces uniform chance; oracle ceiling bounds the metric; base run *is* the no-op. Stronger than most published work. The one baseline still absent is the WHEN null — N1. |
| 7 | Multi-seed reporting | Fail | **Partial** | `N_eval = 100` paired episodes, episode as the unit, Wilcoxon, pre-registered thresholds — the structure is right. Open: N7 (zeros drop, effective n ≠ 100), N8 (pre-flight gates ignore episode clustering), N12 (ceiling CI), and N2 (no held-out set for checkpoint selection). |

## Round 2 critical path

1. **N1's fixed-epoch null** — it is the only thing standing between the spec's
   stated claim ("at better moments") and an unsupported half of it, and it
   costs one extra pass over an already-frozen battery with an already-trained
   policy. Pre-register it *before* freeze or the option is gone.
2. **N2's train/tune split** — must be decided before `--collect` writes its
   first shard, because it is a partition of the collected episodes. After
   collection it is still possible but the `split_role` values are already
   burned into the records.
3. **N3, N4** — before `--collect` and before freeze respectively. N3 prevents
   an overnight run aborting on an event the spec plans for; N4 prevents
   thresholds being pre-registered against unquantified noise.
4. **N5, N6, N7, N8** — specification fixes, before implementation of the
   relevant component.

Everything else is a line-level correction that can ride along.

---

## Round 2 — Confidence Assessment

**Overall Confidence:** High on the round-1 dispositions (each checked against
the mechanism, not the label). Moderate-to-High on new findings; still no code,
so all findings are against design text.

| Finding | Confidence | Basis |
|---|---|---|
| Round-1 dispositions (all 21 rows) | **High** | Each verified against specific rev-3 line ranges cited in the table; the four "over-delivered" calls are judgements about fix quality, not facts |
| F10 not closed | **High** | L218-221 and L116-121 read directly; the blindness rule constrains determinism, not finiteness, and `inf` satisfies it |
| N1(a) live rule undefined | **High** | L392-394 contains no decision rule; verified by absence across the whole eval section |
| N1(b) greedy-earliest is objective-optimal | **High** | Follows directly from the form of `J_now` at L330-332 — pointwise in *s*, no *s+1* term |
| N1(c) no WHEN null exists | **High** | Enumerated every comparison in L386-421; none isolates WHEN |
| N2 no stopping rule / no held-out | **High** on absence (three namespaces, L298; one-shot eval, L428-429); **Moderate** on 450 fans being insufficient — that is a judgement about capacity vs corpus, not a measured fact |
| N3 non-finite Δ misclassified | **High** — `Δ − Δ = NaN` for non-finite Δ is IEEE-754; step 6 (L280-283) and step 8 (L288-293) give conflicting dispositions for the same event |
| N4 argmax accuracy undefined | **High** on the ambiguity (L98 vs L284-286 read directly); **Moderate** on the magnitude of val↔test disagreement — depends on arm separation, which pre-flight will measure |
| N5 objective combination unspecified | **High** on the ambiguity; **Moderate** on the degenerate branch being reachable — depends on which reading is implemented |
| N6 same-pathology swaps | **High** — four pathologies, unrestricted swap, so ~25% same-class pairing is arithmetic |
| N7 Wilcoxon drops zeros | **High** — standard procedure; L394's "exactly 0 by construction" makes the interaction certain |
| N8 fan clustering | **High** — the shared base run (L239-243) makes within-episode fans correlated by construction; gate 1 (L346-350) is an explicit binomial test |
| N9 refan no-op arm | **Moderate** — the spec says "the argmax's agreement rate across the two draws," which *may* imply all arms are re-run; the base-run-as-no-op identity makes it easy to implement wrongly either way |
| N10 `policy_run` undefined | **High** — one occurrence at L298, verified absent elsewhere |
| N13 dropped `‖h‖²` | **High** — differentiating `λ‖Δ‖²/‖h‖²` with `‖h‖²` detached gives `2λΔ/‖h‖²`; the stated minimizer omits the factor |

## Round 2 — Risk Assessment

**Implementation Risk of adopting Round 2:** Low. Every fix is a
specification change, a data partition, an assertion condition, or one
additional eval pass. None touches the scope pins, the seed menu, the lifecycle,
the reward definition, or the learning objectives' form.

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| Demo ships and "at better moments" is quoted, with no measurement behind it | High | **High** if N1 is not adopted | N1's fixed-epoch null, pre-registered before freeze |
| Policy overfits ~450 fans; result reads as "the approach doesn't work" | High | Medium-High | N2 train/tune split + reported learning curve |
| Overnight collection aborts on a legitimate crash-and-burn arm | Medium | Medium | N3 — condition step 6 on finiteness |
| Pre-registered thresholds committed against unquantified label noise, then missed or gamed | Medium-High | Medium | N4 — define the argmax accuracy, extend the ceiling, re-derive before freeze |
| Honesty falsifier fails against a genuinely good policy | Medium | Medium | N6 — derangement across pathology classes |
| Headline p-value computed on ~70 pairs while "N_eval = 100" is reported | Medium | **High** if unaddressed | N7 — pre-register the zero handling and report effective n |
| Fixing N1 by adding a now-vs-later objective, undoing rev 3's simplification | Medium | Low-Medium | Explicitly out of scope in N1's fix — measure WHEN before changing how it is trained |
| Line budget: rev 3 already moved from ≲800 to ≲1000 lines | Low-Medium | Medium | Round 2 adds one eval pass, one split value, one assertion condition, and specification text — very little new logic |

## Round 2 — Information Gaps

1. [ ] **Pre-flight gate 3/5 outputs** — arm separation magnitude determines
       whether N4's val↔test disagreement is a rounding error or a headline
       problem. Measurable in the ~30 pre-flight episodes already planned.
2. [ ] **Intended combination of `J_which` and `J_now`** (N5) — I flagged both
       readings; the owner presumably has one in mind.
3. [ ] **Intended live decision rule for `p`** (N1a) — same.
4. [ ] **Whether the four other panel reviews** (lifecycle, reward, statistics,
       determinism, per L5-7) filed findings that overlap N1-N16. I reviewed
       rev 3 against my own round-1 findings and the morphogenetic-RL
       disciplines only, and did not read the sibling reviews. Several rev-3
       `(closes: …)` notes cite reward-review findings adjacent to N1 and N5;
       there may be duplication or, worse, a sibling finding that rev 3's fix
       reopened and I would not have recognized.
5. [ ] **Still no implementation.** `experiments/kernel_demo.py` does not exist;
       every finding is against design text.

## Round 2 — Caveats & Required Follow-ups

### Before relying on this analysis

- [ ] Reconcile against the four sibling panel reviews (gap 4) before treating
      N1-N16 as the complete round-2 set.
- [ ] Confirm with the owner which reading of N5 and N1(a) was intended; if the
      non-degenerate reading was always the plan, both collapse to
      "write it down."

### Assumptions made

- The scope pins at L47-64 remain owner-approved and fixed; I evaluated the
  rev-3 statement that the new harness constants (λ, β-ramp, entropy,
  exploration schedule) are harness properties rather than policy knobs, and
  **agree** — none is visible in the policy's action or observation space.
- Wilcoxon signed-rank means the standard zero-dropping procedure (N7); if
  Pratt's method was intended, N7 is already closed.
- All eval episodes share horizon 40 (L425), which is what makes N6's "same
  horizon" constraint vacuous.
- "The fan argmax" means a single quantity throughout (N4 is the observation
  that it now has two candidate definitions).

### Limitations

Unchanged from round 1: this review does not cover the RL algorithm's
hyperparameters, host-side training mechanics beyond the isolation and
optimizer contracts, low-level PyTorch beyond the determinism flag set, or
statistical power sizing. N2's "450 fans is thin" is a capacity judgement, not
a power calculation — `yzmir-counterfactual-statistics` should size the
corpus properly if the owner wants that number defended rather than
monitored via N2's learning curve.

### Recommended next steps

1. Decide N1 (fixed-epoch null + live decision rule) and N2 (train/tune split)
   — both must land before freeze/collect respectively.
2. Apply N3 and N4 before any collection run.
3. Specify N5, N6, N7, N8; correct N9-N16 inline.
4. Reconcile with the sibling panel reviews.
5. Then implement, with `--selftest` before `--collect` — unchanged from
   round 1, and rev 3 has already put `--selftest` in the mode list.

---
---

# Round 3 (rev 4) — verification pass

**Reviewed:** `docs/superpowers/specs/2026-08-09-kernel-demo-design.md` @ 6b9f496 (445 lines)
**Mandate:** verdict round-2 findings only; no new hunting surfaces unless a
rev-4 edit is actively wrong.

**Verdict: 17 of 18 closed, 1 not closed (Low).** Five closures over-deliver.
No rev-4 edit is wrong. Two implementation notes and one interpretive caveat
are recorded below — none is a reopening.

## Disposition

| # | Round-2 finding | Verdict | Evidence in rev 4 |
|---|---|---|---|
| F7 res. | `schema_version` absent | **Closed** | L282 — first field in the record. |
| F10 | Non-finite telemetry reaches policy | **Closed** | L125-127 — construction asserts all fields finite; a non-finite field marks the run diverged at that epoch with status recorded, "never a silent `inf` into the normalizer." Exactly the fix, at exactly the site. |
| N1 | Nothing isolates WHEN | **Closed** | All three sub-gaps. (a) Deployment rule stated, L194-203: queried only inside the trained window 5-15, germinates at the first epoch where `p > 0.5`, deterministically — and L79-80 confirms no sampling slot exists at eval. (b) Claim rescoped to "at **profitable** moments" (L25-29), with "best moment" reserved for beating the null. (c) Fixed-epoch null in the battery (L360-365): trained WHICH head forced at t\*=10, same 100 seeds, no retraining; `trained_live_lift − fixed_epoch_lift` **is** the WHEN contribution, reported with no pass threshold and gating only the timing wording (L407-408). Bonus: gate 7 (L348-352) now measures now-vs-later materiality from the paired ordered fans, so the deployment rule's known limitation is quantified rather than assumed. |
| N2 | No held-out set / no stopping rule | **Closed** | L315-321 — 80/20 by episode, checkpoint selection on tune via `J_which + J_now`, learning curve reported so "overfit" is distinguishable from "the approach doesn't work," collection extendable on tune evidence pre-eval only. The corpus also grew: exactly 2 fan epochs per episode (L237-239) makes 300 episodes = **600 fans**, not 450. |
| N3 | Step-6 assertion misclassifies divergence | **Closed** | L263-266 — assertion conditioned on arm finiteness; a non-finite Δ is "arm divergence (status), not a harness abort." |
| N4 | Argmax unit undefined; ceiling misses that noise | **Closed, resolved differently and better** | L92-96 establishes a **unit wall**: every reported argmax, ceiling, probe target and agreement number in test units; every training label in val units; each gate states its unit. `P(val-argmax = test-argmax)` is reported beside fan density as "the measured cost of the unit wall." I had recommended val-argmax for agreement; test-argmax with the disagreement rate published is the stronger choice — it makes agreement a claim about ground truth rather than about reproducing the training signal, and it surfaces the noise as a number rather than burying it in a ceiling. |
| N5 | Objective combination unspecified | **Closed** | L213-222 — total loss written out, `sg[π]` inside `J_now`, with the consequence stated ("WHICH trains at 1× regardless of p and the frozen entropy calibration cannot drift"). |
| N6 | Falsifier swap preserves signal | **Closed** | L388-391 — derangement across pathology classes, citing the ~25% same-pathology rate. |
| N7 | Wilcoxon drops zeros | **Closed, over-delivered** | L366-372 — Wilcoxon replaced by a one-sided sign-flip permutation test on mean per-episode lift, with the reason stated in estimand terms: the zero-drop "silently converts the estimand to conditional-on-acting." I proposed documenting the zero handling; changing the test so the estimand matches the claim is strictly better. Pre-registered at L399-400 (10k resamples, one-sided, α=0.05). Sign-flipping is valid here — zeros stay in, contribute no variance, and correctly dilute the mean. |
| N8 | Gates ignore episode clustering | **Closed** | L325-328 — unit of analysis is the episode; where an episode has two fans, gate statistics use the first scheduled fan only. |
| N9 | Refan must re-run the no-op arm | **Closed, over-delivered** | L296-301 — 5 real arms including a fresh no-op continuation under the new future, with a sharper reason than mine: "the twin would abort by construction unless re-based." |
| N10 | `policy_run` undefined | **Closed** | L283-285 — four kinds, each defined where used; `policy_run` spelled out as an eval live episode. |
| N11 | Twin abort granularity | **Closed, over-delivered** | L248-253 — abort names the first differing epoch, emits a divergence report, prior shards remain valid; and the twin is now **non-optional** via the forbidden-relaxations list (L75-78), which is more than I asked. |
| N12 | Ceiling estimated from n=30 | **Closed, over-delivered** | L381-387 — the ceiling is demoted out of every pass threshold and labeled as the Σp² *lower bound* of the true ceiling with a Wilson interval. The Σp² insight (understates by up to ~27%, an anti-conservative denominator) is sharper than my "n=30 is noisy"; the agreement gate now stands on the majority-class null alone. |
| N13 | Trust-region formula / `g` collision | **Closed** | L171-173 — `Δ* = −(∂L/∂Δ)·‖h‖²/(2λ)`, symbol collision removed. |
| N14 | `derive()` unspecified | **Closed, over-delivered** | L64-69 — SHA-256 truncated to 64 bits, plus an RNG ownership rule banning `torch.manual_seed` outside process startup and requiring every draw to come from a named generator. |
| N15 | Retune rounds undisclosed | **Closed** | L135-137 plus `kind="preflight_iter"` (L283) — retune iterations logged to the store with an iteration counter, "a recorded selection process, not an invisible one." |
| N16 | Eval grid epochs vs schedule distribution | **NOT closed** | L373 defines the grid as "frozen `(episode_seed, fan_epoch)`" and never states how `fan_epoch` is drawn. If the grid's epochs are not drawn from the same distribution as the collection schedule (L237-239), teacher-forced agreement is measured off the state distribution the policy was trained on. **Fix: one clause** — state that grid epochs use the same draw as the exploration schedule. Severity Low, unchanged. |

## Checks on rev-4 edits (mandate: flag only if actively wrong)

**Diverged-arm convention (L270-280) — endorsed.** Checked as requested. The
choice of 0.10 is genuinely *measurement*, not convention: NaN logits make
`argmax` return a constant index, so a destroyed classifier scores the frequency
of one class, ≈0.10 on balanced CIFAR-10. All four rejections are correct, and
two are correct for reasons specific to this demo — last-finite-epoch would
score the spike-then-crash arm at its spike (the exact artifact the demo exists
to expose), and `R_noop` would let a seed that wins big and destroys the host
15% of the time be scored as noop-neutral on its failures. Naming null→0.0 as
"the founding silent-default defect" is the right lineage. Scoring 0.10 *in the
objectives* is also right: it teaches the policy to avoid divergence-prone
seeds rather than hiding divergence from it.

**Arithmetic spot-check.** L404's "exact α=5.08%" for ≥3-of-4 pathologies under
a uniform null is correct: `4·(1/4)³·(3/4) + (1/4)⁴ = 13/256 = 5.078%`.

**τ-init vs STE invisibility.** τ-init makes Δ ≠ 0 at germination, which does
**not** break the STE guarantee — `h + (Δ − Δ.detach())` is exactly `h` for any
finite Δ, and L152 says so. Consistent with N3's finiteness condition. Not
wrong.

### Two implementation notes (not reopenings)

1. **τ-init's measurement pass and BN mode.** `g = τ·RMS(h)/RMS(f₀)` is measured
   "on one fixed batch at germination" (L149-151). If that forward pass runs in
   `train()` mode and the host carries BatchNorm, it will update host BN running
   statistics — per arm — and trip the very step-6 bitwise assertion that N3 just
   conditioned. The failure would be loud rather than silent, which is the
   correct outcome, but it costs a debugging cycle. One clause: the τ-init pass
   runs under `eval()` / `no_grad` with BN in inference mode.
2. **`tune`: namespace or partition?** L130 lists `tune` as a top-level seed
   namespace (`ns ∈ {dev, preflight, train, tune, eval}`) while L315 says the
   train namespace "splits 80/20 by episode into `train`/`tune`." Those are two
   different mechanisms. Either discharges N2 — a separate namespace makes the
   grouping automatic, a partition requires the by-episode grouping the spec
   already states — but the loader assertion at L313 needs to know which.

### One interpretive caveat on N1

`live − fixed_epoch` attributes to WHEN everything the NOW head does, which
includes **restraint** as well as **timing**. A policy with no timing skill that
correctly declines to act on mild episodes will produce a positive WHEN
contribution, because the fixed-epoch null germinates unconditionally. This does
not invalidate the null — restraint genuinely is a NOW decision — but "better
moments" and "knows when not to act" are different claims and the difference
does not separate them. Rev 4 already publishes what a reader needs to tell them
apart: realized germination rate beside every lift number (L202-203, L372) and
restraint regret as its own metric (L377-380). Worth one sentence at L365 noting
that the contribution combines timing and restraint, so the wording chosen for
the timing claim is picked with the germination rate in hand.
