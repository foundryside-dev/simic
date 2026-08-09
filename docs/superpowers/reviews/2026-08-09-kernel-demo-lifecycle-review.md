# Kernel demo — growth/lifecycle design review

**Reviewer:** yzmir-dynamic-architectures (dynamic-architecture-advisor)
**Target:** `docs/superpowers/specs/2026-08-09-kernel-demo-design.md` (rev 2)
**Date:** 2026-08-09
**Scope:** gradient isolation, stage-transition stability, optimizer lifecycle,
fan fairness-of-comparison, blend/pathology interaction, growth-timing
pathologies. Scope pins (fixed menu, zero controller knobs, end-state-only
reward) are treated as owner-approved and are not relitigated.

---

## Verdict

The isolation *mechanism* is correct — I verified the detach placement gives
exactly the guarantee claimed, and the delta contract genuinely removes the
esper-lite train-additive/blend-replacement ambiguity (esper-lite's
`blend_ops.blend_add` really is `lerp`, i.e. interpolative, while
`isolation.ste_forward` really is additive; the spec's diagnosis of its
predecessor is accurate).

What is missing is not isolation but **magnitude control**. The lifecycle
specifies *when* the delta is introduced and *how fast*, but nothing anywhere
determines *how large* the delta is when introduction begins. Three of the
lead's six questions are the same defect seen from different sides. One unified
fix closes them.

---

## Findings

### F1 — HIGH — STE pretrain has no restoring force; Δ's magnitude is undetermined

**Spec text at fault:** lines 118–121 — "STE forward `h + (Δ − Δ.detach())`.
Forward value bit-identical to the host's; Δ receives full task gradients at
effective α=1 … what is trained is *exactly* the additive delta that blending
will introduce."

The last clause is false, and this is the design's central mechanism.

Because the forward value is exactly `h`, everything downstream — and therefore
`g = ∂L/∂h'` — is evaluated at the **unperturbed** operating point. The
gradient reaching Δ's parameters is `J_θᵀ g`, where `g` does not depend on Δ.
The objective in Δ is therefore **linear**:

```
L(h + Δ) ≈ L(h) + g·Δ      (first order, and the forward never leaves this point)
```

A linear objective has no minimiser. There is no curvature term and no term
proportional to `+Δ`, so nothing tells Δ it has gone far enough. Δ integrates
`−Σ_t g_t` across the pretrain steps and drifts monotonically in the
descent direction.

"Effective α=1" in the spec describes the gradient *scale* (`∂out/∂Δ = 1`), not
the operating point. The operating point is α=0. So the answer to the lead's
first question is **yes, but the mismatch is worse than stated**: STE does not
merely train Δ for a regime it later doesn't experience — it trains Δ under an
objective in which Δ's own effect on the loss is *definitionally* zero, which is
exactly the assumption that fails as α → 1.

What STE does buy is real and worth keeping: it identifies the **direction** of
a useful delta at zero cost to the host, and does so provably invisibly. What it
cannot do is determine the delta's **magnitude**. Magnitude is set by
`lr × steps × gradient consistency` — a per-seed accident, not a property of the
task. (I deliberately give no numeric drift estimate: the honest bound depends
on cross-batch gradient sign consistency, which is unmeasured.)

I checked whether the predecessor bounded this. It did not — `esper-lite`'s
`SeedSlot.forward` (`src/esper/kasmina/slot.py:2191`) applies `ste_forward`
unmodified with no magnitude cap, and neither `blending.py` nor
`alpha_controller.py` contains any norm or magnitude clamp (only `_clamp01` on
α itself). The demo is inheriting this gap by re-implementation, not fixing it.

**Fix:** see *The unified fix* below.

---

### F2 — HIGH — Detach-drop at fossilization is an unmitigated gradient-path discontinuity

**Spec text at fault:** lines 125–126 — "**FOSSILIZED:** `h + Δ`, detach
dropped; the delta trains jointly as ordinary host tissue."

The forward **value** is continuous across this transition (`h + 1·Δ(h.detach())`
and `h + Δ(h)` are numerically identical). The **gradient** is not. For every
host parameter below the slot, the backward path changes in one step from

```
∂L/∂h · I        →        ∂L/∂h · (I + ∂Δ/∂h)
```

Two compounding problems:

1. **`∂Δ/∂h` is unconstrained.** Δ was trained exclusively on `h.detach()`, so it
   was never under any pressure to be a well-conditioned *function* of its input —
   only to produce a useful output vector. Its input-Jacobian spectral norm is
   whatever training happened to leave behind.
2. **Adam's second moment is stale.** The host's `v` for those parameters is
   calibrated on the pre-fossil gradient scale and re-adapts over roughly
   `1/(1−β₂)` steps — ≈1000 steps at β₂=0.999, which at CIFAR-10/bs128
   (391 steps/epoch) is **≈2.6 epochs**. The first post-fossil steps are
   oversized by roughly the gradient-norm ratio, and stay oversized for epochs.

This is the *stage transition shock* failure mode named in
`progressive-training-strategies.md` (§Failure Modes, "Stage Transition Shock" —
sharp drop at transition, many epochs to recover, sometimes never). The spec
carries none of that sheet's three named mitigations: no LR cooldown, no
settling period, no distillation. The ≥15-epoch fossil runway gives room to
*recover*, but recovery time is charged against the end-state reward window, so
the shock is silently priced into `R_a` — and priced unequally across seeds,
since `∂Δ/∂h` differs per architecture.

**Fix:** see *The unified fix*. Note that the β-ramp alone is insufficient here —
it removes the value/Jacobian shock but not the Adam-lag shock. Pair it with
either a β ramp spanning ≥3 epochs (longer than the Adam adaptation window,
affordable inside the 15-epoch runway) **or** an explicit `exp_avg_sq` reset for
host parameters below the slot at the transition.

---

### F3 — HIGH — Fan fairness: per-seed Δ scale at blend entry is an uncontrolled confound, and its direction is *undetermined from the spec*

**Spec text at fault:** the seed table, lines 97–103; and the absence of any
seed-initialisation or seed-internal-normalisation contract anywhere in the
document.

The lead asked whether 3 epochs of STE is "enough" for conv_heavy (60k) versus
norm (0.1k), and whether the asymmetry biases the fan against heavy seeds.
Under F1 the sufficiency framing does not apply — there is no convergence
target to be sufficient *for*. The real defect is a **confound**, and I have to
report that the spec does not determine which way it points. Two independent
uncontrolled sources of per-seed Δ scale:

**(a) Implicit magnitude bounds are architecturally selective and unstated.**
The spec names the four deltas but never their internals. If `conv_heavy`
("full residual block") terminates in BatchNorm — the conventional
construction — its output RMS is bounded by that BN's γ, a small, slowly-moving
parameter set: the F1 runaway is *substantially damped*. If `conv_light`
("depthwise-separable 3×3 residual") terminates in a raw pointwise conv — also
the conventional construction — it is **unbounded**. `attn` is bounded only if a
final projection is normalised. `norm` is `GroupNorm(h) − h`: its γ and β are
directly exposed to the linear objective, and β in particular is a per-channel
bias whose gradient is `g` summed over batch and space — the single most
runaway-prone parameter in the whole menu.

So the honest answer to "does this bias against heavy seeds" is: **no —
plausibly the opposite, and in any case undetermined.** The seed most at risk of
magnitude runaway is `norm`, the 0.1k one, and it is the seed that must win the
`under-normalized` episodes for the money chart's diagonal to exist.

**(b) There is no seed-initialisation contract.** `norm` has a *large* Δ at
initialisation by construction (`GroupNorm(h) − h` with γ=1, β=0 is the entire
normalisation correction). Conv seeds are zero-init by convention — if anyone
remembers, and the spec never says. So even before a single pretrain step, the
four arms enter TRAINING at incomparable operating points.

The consequence for the demo's claim: the fan measures **seed type × accidental
Δ scale**, not seed type. `R_a` differences between arms are partly attributable
to a nuisance variable nobody controlled, and the WHICH head is trained by
directly maximising `Σ_a π(a|s)·R_a` over exactly those confounded labels. This
is a fairness-of-comparison defect in the supervision signal itself, not a
scope limitation.

**Fix:** the unified fix normalises (a). For (b), add an explicit
seed-initialisation clause to the seed table: every seed is zero-initialised in
its output projection *except* `norm`, whose identity-at-init form is
`γ=1, β=0` scaled by the same trust-region constant as every other arm.

---

### F4 — MEDIUM — The α ramp gates forward contribution but not Δ's learning rate

**Spec text at fault:** line 124 — "BLENDING (fixed M≈3 epochs): `h + α·Δ`, α on
one fixed cosine ease at one fixed speed, 0 → 1."

**This finding is conditional on Adam/AdamW**, which is assumed throughout this
review and is not stated in the spec — see Information Gaps. Under
SGD+momentum this finding dissolves entirely (the α ramp *would* genuinely gate
Δ's learning rate), and F2's Adam-lag half disappears with it.

Under Adam, a *constant* multiplicative scaling of a parameter's gradient is
absorbed: `m` and `v` both scale, and `m̂/√v̂` is invariant. So α scaling does
**not** gently introduce Δ's *learning* — only its *forward contribution*. The
"gradual integration" semantics the sheet describes
(`gradient-isolation-techniques.md`, §Alpha Blending) is half-implemented here.

During the ramp α is not constant, so `v` lags `m` upward and step sizes are
transiently inflated — the effect is in the destabilising direction, not the
stabilising one. This is not fatal (it is bounded by Adam's implicit trust
region) but it means the M≈3 blend window should not be reasoned about as
"Δ learns slowly at first."

Worth stating plainly in the spec so the implementer does not assume a
protection that is not there.

---

### F5 — MEDIUM — Optimizer lifecycle across stage transitions and across fan arms is entirely unspecified

**Spec text at fault:** `optimizer` occurs exactly once in the document —
line 159, "Snapshot the run state (host weights, optimizer state, data
position)." Nothing else.

`dynamic-architecture-patterns.md` lists "Ignoring optimizer: new params have no
momentum" as a named pitfall, and `gradient-isolation-techniques.md` §Common
Pitfalls opens with optimizer-state-with-frozen-parameters. The spec is silent
on all of:

- **Construction order.** Seed parameters do not exist at episode start. If the
  optimizer is built over `model.parameters()` at t=0, seed params are never
  optimised — a silent no-training bug that presents as "the seed did nothing,"
  indistinguishable from a genuine null result. This is precisely the
  silent-default class the project has scarred on.
- **Param-group semantics.** A separate group for seed params (with its own LR)
  versus `add_param_group` onto the host's optimizer are different experiments.
  Pick one and write it down.
- **Fan-arm restore ordering.** Step 1 snapshots optimizer state *before* any
  arm's seed exists. Each of the 5 arms then restores that snapshot and adds a
  *different* param group (or none, for no-op). The restore-then-extend sequence
  must be byte-identical across arms or the arms are not matched — and the
  matching contract is the demo's entire statistical backbone.
- **Weight decay on Δ.** If the shared optimizer carries weight decay, it
  silently becomes the *only* thing bounding F1's runaway, and the pretrained Δ
  magnitude is then an artifact of `lr/wd` rather than of the task. If it does
  not, F1 is fully unbounded. Either way the spec should say which.

**Fix:** add an "Optimizer contract" subsection to §Lifecycle: one AdamW over
host params created at episode start; seed params added as a **second param
group at germination** with explicitly stated LR and weight decay; the fan
snapshot/restore is defined as (restore host group state) → (construct arm seed)
→ (append seed group), in that fixed order, for all five arms including no-op
(which appends nothing).

---

### F6 — MEDIUM — Fixed α speed is not fixed blend speed; the interaction lands hardest on the pathologies the money chart needs

**Spec text at fault:** line 42 ("one blend waveform, one speed, fixed stage
durations") read together with line 124.

One fixed α schedule across four seeds whose Δ magnitudes differ by orders of
magnitude (F1/F3) means the *perturbation* rate `d‖αΔ‖/dt` differs by orders of
magnitude across arms. "One fixed speed" is fixed in α, not in anything the host
experiences.

The pathology interaction compounds this in the worst direction:

- **`under-normalized` × `norm`.** This host's defining property is unstable
  activation statistics. The blend perturbs exactly those statistics while the
  downstream host layers must re-adapt within 3 epochs — and per F3(a), `norm`
  is the arm most prone to magnitude runaway. The pathology/seed pair that the
  money chart's diagonal most depends on is the pair most exposed to blend
  transient.
- **`no-spatial-mixing` × `attn`.** Attention changes the effective receptive
  field of everything downstream. Stage-3 filters were fit to un-mixed features;
  a fast ramp is a distribution shift, not a capacity addition.
- **`mild` × everything.** A blend transient that depresses all four acting arms
  uniformly makes no-op win *more* often — inflating the measured restraint rate
  for a mechanical reason rather than a learned one. Since the demo explicitly
  wants no-op to win its share (line 74–75), this failure mode is
  indistinguishable from success by the current pre-flight checks.

The ≥15-epoch fossil runway is the existing mitigation and is a real one: a
transient that washes out before the end-state window does not enter `R_a`. But
"washes out" is an assumption, and it is exactly what F2's Adam-lag argument
says may take ~3 epochs *after* fossilization, on top of the blend transient.

**Fix:** normalising Δ scale (unified fix) converts "one fixed α speed" into
"one fixed perturbation speed," which is what the scope pin actually intends.
Additionally: report per-arm activation-RMS change at the slot across the blend
window in the arm curves, so a blend transient is visible rather than inferred.

---

### F7 — MEDIUM — Pre-flight validation cannot detect uniform single-seed dominance

**Spec text at fault:** lines 220–229, pre-flight checks 1–3.

`conv_heavy` adds 60k parameters to a *deliberately undersized* 150k host — a
40% capacity increase. On CIFAR-10 at 40 epochs, added capacity to an
under-capacity model is close to a free win regardless of which pathology is
active. If `conv_heavy` becomes the fan argmax across all four pathologies, the
money chart's diagonal collapses and the demo's central claim ("she reads
telemetry rather than schedules") fails.

None of the three existing checks catch this. Check 1 tests no-op's share,
check 2 tests whether telemetry *separates* pathologies (it would still pass —
the telemetry signal is real; it is the *label* that has collapsed), check 3
tests fan contrast (a uniformly dominant seed produces excellent contrast).

**Fix:** add pre-flight check 4 — **no single seed is the fan argmax in a
majority of episodes for every pathology.** Report the per-pathology argmax
distribution. If one seed dominates uniformly, the pathology sampler has not
created a discriminating problem and freezing it would bake in a demo that
cannot fail honestly.

---

### F8 — LOW — α granularity is ambiguous, and the natural reading is the bad one

**Spec text at fault:** line 113 ("transitions once per epoch") read against
line 124 (cosine ease, no granularity given).

Line 113 most plainly means *FSM state* transitions occur at epoch boundaries,
which is fine. But it can be read as α being piecewise-constant per epoch, which
over M=3 gives α ∈ {0, 0.25, 0.75} at `p = 0, 1/3, 2/3` — three step
discontinuities rather than a ramp, and a **dead first blending epoch** in which
α=0 means Δ receives exactly zero gradient for a whole epoch (having just come
off full-gradient STE), while Adam's `m` and `v` decay toward zero.

This is a spec ambiguity, not a committed defect — but the bad reading is the
one an implementer reaches for.

**Fix:** state explicitly that α is updated **per optimizer step**, with the
endpoint convention `p = (step+1)/total_steps` so α > 0 from the first blending
step and reaches exactly 1.0 at the last. (The cosine ease is a good choice
independently: `0.5(1−cos πp)` is C¹ at both endpoints, so the
TRAINING→BLENDING and BLENDING→FOSSILIZED joins are smooth in the α direction.)

---

### F9 — LOW — The isolation claim is overstated as written

**Spec text at fault:** lines 116–117 — "Structural isolation at all pre-fossil
stages: the delta consumes `h.detach()` — seed gradients cannot reach the host,
by construction."

The mechanism is correct and I verified it: during BLENDING, `h + α·Δ(h.detach())`
gives the host gradient only through the direct `h` term. Nothing flows through
`∂Δ/∂h`. Credit where due — this is right, and it is the property esper-lite
also got right.

But the *host is still affected by the seed*, because its own gradients are now
evaluated at the perturbed activation `h + αΔ` rather than at `h`. That is
intended (it is how the host adapts around the delta) and it is not a bug — but
"seed gradients cannot reach the host" reads as full isolation and it is only
Jacobian-path isolation. Since the demo's file header is meant to be read
top-to-bottom by someone learning the substrate, the distinction is worth one
sentence.

**Fix:** amend to "no seed gradient reaches the host *through the delta path*;
the host still adapts to the delta's presence via its own operating point."

---

## The unified fix

F1, F2, F3(a), F4 and F6 are all the same missing quantity: **a trust region on
Δ**. Two changes close them, and neither adds a knob for Aurelia — both are
fixed schedules, so scope pin line 42 holds.

### 1. Extend the slot equation with a gradient-coupling scalar

```
h' = h + α · Δ( lerp(h.detach(), h, β) )
```

`lerp(h.detach(), h, β) = (1−β)·h.detach() + β·h` is **value-identical to `h` for
every β**, so this is a pure gradient-coupling knob with zero effect on the
forward. It preserves the spec's "one equation, three regimes" aesthetic and
extends it to a path through (α, β) space:

| Stage | α | β |
|---|---|---|
| TRAINING | STE (`Δ − Δ.detach()`) | 0 |
| BLENDING | cosine 0 → 1 | 0 |
| FOSSILIZING *(new)* | 1 | cosine 0 → 1 over ~3 epochs |
| FOSSILIZED | 1 | 1 |

This converts F2's step discontinuity in the host's backward path into a ramp.
Per the advisor's correction and my own F4 argument: the β ramp must span
**longer than Adam's second-moment adaptation window** (~2.6 epochs at
β₂=0.999, bs=128, full CIFAR-10) or it fixes the Jacobian shock and leaves the
Adam-lag shock. Three epochs is affordable inside the ≥15-epoch runway. The
alternative, if the extra stage is unwelcome, is an explicit `exp_avg_sq` reset
for host parameters below the slot at the fossilization boundary — cheaper, less
elegant, and it must be stated rather than left to chance.

### 2. Make the STE objective well-posed with a trust-region term

Add to the pretrain loss, during TRAINING only:

```
L_pretrain = L_task(STE forward) + λ · ‖Δ‖² / (‖h‖².detach())
```

This does **not** disturb the "provably invisible" property: the penalty depends
only on Δ's parameters and contributes nothing to the forward value, and because
Δ consumes `h.detach()` it contributes nothing to the host's gradient either.
(Use `‖h‖².detach()` for the normaliser — a live `‖h‖` would leak a gradient
into the host and break the isolation claim outright.)

**Notation, load-bearing:** `‖Δ‖` here is the norm of the delta's **output
tensor** `Δ(h.detach())`, not of its parameters. This matters. A
parameter-space penalty would bite unevenly across the menu — a BN-terminated
`conv_heavy` already has its output RMS pinned near its final γ, so penalising
its weights would constrain something other than what F3 and F6 care about. The
output-space form constrains the quantity that actually reaches the host,
identically for all four architectures regardless of how each one internally
bounds itself.

What it buys: the objective in Δ becomes **quadratic instead of linear**, with a
finite minimiser `Δ* = −g/(2λ)`. Δ now has a determined magnitude set by a
*shared* constant rather than by per-architecture accident. That is the whole of
F1.

For F3(a) the property is stronger than "same trust region." Because all five
arms branch from one snapshot and consume the identical common future
(spec lines 159–165), `g` is **the same vector in every arm**. So every seed is
optimising toward the *same* ideal delta `−g/(2λ)`, and the arms differ only in
how well each architecture can express it within its realisable subspace. That
is precisely what the fan is supposed to measure, and it is a much cleaner
fairness guarantee than magnitude-matching alone. It also makes `‖αΔ‖`
comparable across arms, so "one fixed α speed" finally means one fixed
perturbation speed (F6).

A hard RMS cap at the slot — `Δ̂ = Δ · min(1, τ·RMS(h)/RMS(Δ))`, still
bit-identical in forward under STE — is the cheaper alternative and also
operates in output space. I prefer the penalty: the cap only binds on arms that
run away (leaving the others at accidental magnitudes, so the confound survives
in the arms it doesn't clip), whereas the penalty gives every arm the same
target. Use the cap only if the penalty's λ proves hard to tune.

### Verification to add alongside

`gradient-isolation-techniques.md` ships a `verify_isolation` harness; the demo
should carry a three-assertion version as a startup self-test, not a comment:

1. **Isolation:** after one backward at each of the three stages, host
   parameters below the slot have zero grad in TRAINING and BLENDING, and
   nonzero grad in FOSSILIZED.
2. **Invisibility:** in TRAINING, `slot_out` equals `h` to bitwise identity, and
   one full optimizer step leaves every host parameter unchanged relative to a
   no-seed control run on the same batch.
3. **Trust region:** `RMS(Δ)/RMS(h)` at blend entry is within a stated band, and
   is **reported per seed type in the fan record**. If the four arms enter
   BLENDING at wildly different ratios, F3 is live and the fan labels are
   confounded — this makes it observable rather than silent.

---

## Adjacent, not blocking

Two items sit on the matching contract and the measurement path rather than on
the lifecycle design. Noting them for completeness; neither is severity-rated
here and the lead's framing suggests both are already owned elsewhere.

- **RNG stream separation for seed init.** §Determinism (lines 265–267) pins the
  *data* stream — correctly, and the "cloning RNG state alone is insufficient"
  reasoning at lines 160–165 is exactly right. But seed *parameter*
  initialisation also consumes RNG, and the four arms consume different amounts.
  A single shared generator would shift every downstream draw differently per
  arm. Dedicated generators keyed on `(episode_seed, arm_id)` for seed init (and
  for any dropout inside a seed) would close it.
- **BN running-stat lag as a curve artifact.** If the host carries BatchNorm
  downstream of the slot, its running statistics chase a moving distribution
  throughout the α ramp, so per-epoch val accuracy *during* BLENDING is
  systematically depressed by a measurement artifact. `R_a` is safe — it is read
  from the final 2–3 epochs, long after α=1 — but the arm curves and the
  spike-then-crash plot (success criterion 4) will show blend-window dips that
  are partly instrumentation. Worth a caption caveat on that plot.

---

## Confidence Assessment

**Overall Confidence:** High for F1, F2, F5, F9; Moderate for F3, F4, F6, F7;
High for F8 as *ambiguity* (not as defect).

| Finding | Confidence | Basis |
|---|---|---|
| F1 STE linearity | **High** | Derived from the spec's own equation (line 118); the forward value is `h` by construction, so `g` is Δ-independent. Confirmed the predecessor has no magnitude bound: `esper-lite/src/esper/kasmina/isolation.py:86`, `slot.py:2191`, and no clamp in `blending.py`/`alpha_controller.py` beyond `_clamp01` on α. |
| F2 fossilization shock | **High** (mechanism) / **Moderate** (magnitude) | Gradient-path change is exact algebra. The Adam-lag window is arithmetic from β₂=0.999 and an *assumed* bs=128 — batch size is not in the spec. `∂Δ/∂h` magnitude is genuinely unknown. |
| F3 fan confound | **Moderate** | The confound follows from F1. The *direction* is explicitly reported as undetermined, because seed internals are unspecified — that undeterminedness is the finding, and it is High confidence. |
| F4 Adam absorbs α | **High** (theory) / **Moderate** (practical impact) | Adam's scale invariance under constant gradient scaling is standard; the transient during a *ramp* is reasoned, not measured. |
| F5 optimizer silence | **High** | Verified by grep: `optimizer` appears once in the whole document (line 159). No LR, no param groups, no weight decay, anywhere. |
| F6 blend×pathology | **Moderate** | Follows from F1/F3 plus the pathology table's own design intent (lines 67–73). The specific claim that transients hit `under-normalized × norm` hardest is reasoned inference, not measured. |
| F7 capacity confound | **Moderate** | 60k on 150k is arithmetic from the spec's own numbers. Whether `conv_heavy` actually dominates is an empirical question — which is exactly why it belongs in pre-flight, not in a review verdict. |
| F8 α granularity | **High** as ambiguity | Lines 113 and 124 verified; neither fixes granularity. The α values quoted assume the per-epoch reading, which I explicitly do not assert the spec commits to. |
| F9 overstated claim | **High** | Detach placement verified against the spec's equation; the isolation property holds exactly as claimed, and the wording overreaches exactly as described. |
| Unified fix (α,β) | **High** on correctness | `lerp(h.detach(), h, β)` is value-identical to `h` by inspection. That it is *sufficient* for stability is Moderate — it is the right mechanism, but the β-ramp duration is calibrated against an assumed batch size. |
| Unified fix (λ term) | **High** on well-posedness | Quadratic objective has minimiser `Δ* = −g/(2λ)` by inspection. That λ is *tunable to a good value* is untested. |

---

## Risk Assessment

**Implementation Risk:** Medium. **Reversibility:** Easy — all recommendations
are pre-implementation spec edits to a single-file demo with no downstream
consumers yet.

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| F1/F3 ship unfixed → fan labels confounded, WHICH head trains on `seed type × accidental scale`, money chart diagonal is partly an artifact | **Critical** to the demo's claim | High if unaddressed — nothing in the current design bounds it | Trust-region term + report `RMS(Δ)/RMS(h)` at blend entry in every fan record so it is observable |
| F2 ships unfixed → fossilization shock priced unequally into `R_a` across seeds | High | Moderate–High; depends on unknown `∂Δ/∂h` | β-ramp ≥3 epochs, or `exp_avg_sq` reset |
| F5 ships unfixed → seed params silently never optimised | **Critical** if it fires | Low–Moderate; a classic construction-order slip | Startup self-test assertion 2, plus the explicit optimizer contract |
| F7 ships unfixed → `conv_heavy` dominates uniformly, pathologies frozen around a non-discriminating problem, demo cannot fail honestly | High | Moderate — 40% capacity on an undersized host is a strong prior | Pre-flight check 4 *before* the freeze at line 84 |
| Adding λ makes Δ's magnitude an artifact of λ instead of of the task | Medium | Certain by construction | Accepted deliberately: a *shared* artifact is a fair comparison; a *per-seed* artifact is not. State λ in the fan record. |
| Fix scope creep — new FOSSILIZING stage widens the FSM | Low | Low | It adds no Aurelia knob (fixed schedule), so scope pin line 42 holds. If even that is unwelcome, the `exp_avg_sq` reset is a one-line alternative. |
| Maintenance: three self-test assertions add startup cost to every episode | Low | Certain | Gate behind a `--selftest` flag run once per session, not per episode |

---

## Information Gaps

- **Batch size and learning rate.** Not in the spec. The Adam-adaptation-window
  arithmetic in F2 (≈2.6 epochs) and therefore the recommended β-ramp duration
  are calibrated on an assumed bs=128 over full CIFAR-10. A different batch size
  moves the recommendation proportionally.
- **Seed module internals.** The four deltas are named by type and parameter
  count only. Whether each terminates in a normalisation layer determines
  whether F1's runaway is damped or unbounded *per arm* — this is the single
  most load-bearing unknown in the review, and is why F3's bias direction is
  reported as undetermined rather than resolved.
- **Host normalisation.** Whether the 3-stage CNN uses BatchNorm, GroupNorm, or
  none changes both the `under-normalized` pathology's construction and the
  BN-lag artifact in the adjacent notes.
- **Optimizer identity.** AdamW vs Adam vs SGD+momentum changes F4 entirely
  (SGD does *not* absorb α scaling — under SGD the α ramp genuinely does gate
  Δ's learning rate, and F4 dissolves) and changes F5's weight-decay sub-point.
- **Empirical `∂Δ/∂h` and `RMS(Δ)/RMS(h)` at blend entry.** Both are directly
  measurable in a 30-episode random-policy run and would convert F1/F2/F3 from
  reasoned to measured. The pre-flight phase (lines 218–231) is the natural
  place; it costs nothing extra since those runs are already planned.
- **No implementation exists.** `experiments/kernel_demo.py` is not yet written,
  so every finding is against spec text, not behaviour.

---

## Caveats & Required Follow-ups

**What must be verified before relying on this analysis:**

1. **Confirm the optimizer is Adam/AdamW.** F4 is written on that assumption. If
   the demo uses SGD+momentum, F4 dissolves and F2's Adam-lag half disappears —
   the β-ramp could then be shortened to one epoch.
2. **Settle the four seeds' internal normalisation** and record it in the seed
   table. Until that is written down, F3's bias direction genuinely cannot be
   resolved, and the fan's fairness is unaudited rather than sound.
3. **Instrument before deciding λ.** Run the planned 30-episode random-policy
   pre-flight with `RMS(Δ)/RMS(h)` logged at blend entry per seed type. If the
   four arms already enter within a factor of ~2, F1's practical impact is
   smaller than the theory suggests and λ can be set loosely. If they span
   orders of magnitude, the trust-region term is load-bearing.

**Assumptions this rests on:** that the host carries BatchNorm downstream of the
slot (affects F2 and the adjacent BN note); that bs=128 on full CIFAR-10; that
seeds are constructed with conventional PyTorch idioms for their stated types;
that "3 epochs" means ~3× steps-per-epoch optimizer steps, not 3 steps.

**What this review does NOT cover:** the RL/controller side (action space,
reward, entropy, the offline/online interference guard) — that is
`yzmir-morphogenetic-rl` and `yzmir-deep-rl` territory. The counterfactual
statistics (fan density, the independent statistical unit, selection effects in
`max_a R_a`) — that is `yzmir-counterfactual-statistics`; I note only that F3's
confound would be an input to any such audit. The determinism/matching contract
beyond the single RNG-stream observation — `axiom-determinism-and-replay`.
Nothing here relitigates the scope pins.

**Recommended next steps, in order:**

1. Write the seed-internals and seed-initialisation contract into the seed table
   (closes F3(b), and makes F3(a) resolvable).
2. Add the optimizer contract subsection (closes F5) — cheapest fix, highest
   silent-failure risk.
3. Adopt the (α, β) equation with a FOSSILIZING stage, or commit explicitly to
   the `exp_avg_sq` reset alternative (closes F2).
4. Adopt the trust-region term in the TRAINING loss (closes F1, F3(a), F6).
5. Fix the α-granularity wording and the isolation-claim wording (closes F8, F9)
   — pure text edits.
6. Add pre-flight check 4 and the `RMS(Δ)/RMS(h)` fan-record field, then run the
   30-episode pre-flight **before** the pathology freeze at line 84 (closes F7,
   and converts F1/F3 from reasoned to measured).

---

# Round 2 (rev 3)

**Reviewed:** `docs/superpowers/specs/2026-08-09-kernel-demo-design.md` @ 244accb
**Date:** 2026-08-09
**Asked:** (1) verdict each round-1 finding; (2) assess the new lifecycle
surfaces — λ × zero-init gain, and twin-arm/branch mechanics touching optimizer
restore.

## Headline

Rev 3 closes seven of nine round-1 findings outright and materially improves on
two of my recommendations (pre-flight gate 4 gained an overall-rate limb I did
not propose; the twin arm is a stronger optimizer-restore check than the
byte-ordering discipline I asked for). Both of my open questions are answered.

**But the round-1 F3 confound is not closed — it has been re-created through a
new mechanism.** The zero-init scalar gain `g` was adopted to equalize the arms
at germination. It does equalize them, at the value zero, which is a degenerate
equalization: it makes all four arms *dead* at entry and then lets them come
alive at architecture-dependent rates over the fixed K≈3 TRAINING epochs. The
bias direction is now the **opposite** of rev 2's — rev 2 favoured whichever
seed ran away fastest (likely `norm`); rev 3 favours whichever seed bootstraps
fastest (also `norm`, for a different reason). Same confound, flipped mechanism,
still pointing at the arm that must win `under-normalized`.

The good news: pre-flight gate 5 is exactly the right detector and it is already
in the spec. I expect it to fire.

## Part 1 — Round-1 finding verdicts

| # | Finding | Verdict | Note |
|---|---|---|---|
| F1 | STE objective linear / unbounded | **Closed** | Trust-region term adopted with output-tensor norms and λ as a fixed harness constant (spec 173–179). One formula error inherited from my round-1 text — see R2-F5. |
| F2 | Fossilization gradient discontinuity | **Closed** | β-ramp + FOSSILIZING sub-stage adopted (183–187). SGD dissolution reasoning confirmed below; 2 epochs is ample. Residual: see R2-F6. |
| F3 | Fan fairness / per-seed Δ scale | **NOT CLOSED** | Init contract fixes the *stated* problem (accidental scale at entry) and introduces a new one at the same site. See R2-F1. |
| F4 | Adam absorbs α scaling | **Closed by dissolution** | Reasoning confirmed below. |
| F5 | Optimizer lifecycle unspecified | **Closed**, with new findings on the added surface | Contract added (191–197), state deep-copied (259–263), twin arm verifies restore empirically — better than what I asked for. R2-F2 and R2-F4 are findings about the *new* contract, not residue of the old gap. Converged independently with the determinism reviewer's HIGH on the same site. |
| F6 | Fixed α speed ≠ fixed perturbation speed | **Closed, conditional** | The trust region makes `‖αΔ‖` comparable *provided gate 5 passes*. Inherits R2-F1's risk; per-arm blend curves retained for monitoring (443). |
| F7 | Pre-flight blind to uniform dominance | **Closed** | Gate 4 (368–371) is stronger than my proposal — the >40%-overall limb catches capacity dominance that the per-pathology limb alone would miss. |
| F8 | α granularity ambiguity | **Closed** | Per-step, `p=(step+1)/total_steps` (180–182). |
| F9 | Isolation claim overstated | **Closed** | Reworded to Jacobian-path isolation with the operating-point distinction named as embodiment (166–170). |

### Confirming the two dissolutions (asked explicitly)

**F4 dissolves — confirmed.** SGD's update is `lr · (momentum-smoothed gradient)`.
Scaling a gradient by α scales the update by α; there is no per-parameter
normalizer to absorb it. So under SGD the α ramp genuinely does gate Δ's
learning rate, which is what the design always intended. My round-1 F4 was
Adam-specific and is void.

**The Adam-lag half of F2 dissolves — confirmed, and 2 epochs is comfortably
enough.** My 3-epoch figure was calibrated on Adam's second-moment window,
`1/(1−β₂) ≈ 1000` steps ≈ 2.6 epochs. SGD has no preconditioner, so there is no
stale-scale state to re-adapt. The only carryover is the momentum buffer, whose
timescale is `1/(1−μ) ≈ 10` steps at μ=0.9 — about 2.5% of one epoch, i.e.
negligible. The binding constraint at fossilization is now the raw Jacobian
magnitude `‖∂Δ/∂h‖`, which the β ramp addresses directly and proportionally
regardless of its length. **2 epochs (~780 steps of gradual opening) is ample;
even 1 would likely do. Keep 2 for margin.**

One consequence that cuts the other way and is worth stating in the spec: SGD
does **not** normalize a sudden gradient-magnitude increase the way Adam would.
Adam would have damped a fossilization spike automatically; SGD passes it
straight to the update. Combined with "no gradient clipping anywhere" (79–80,
adopted deliberately to close reward F3), **the β ramp is now the sole
stability mitigation at fossilization.** That is an acceptable design — the ramp
is the right mechanism and it is proportional by construction — but it is a
single point of failure and should be named as one. The α(t)/β(t) trajectory
plot (442) and per-arm curves make a failure visible after the fact; that is
adequate for a demo.

## Part 2 — New lifecycle surfaces

### R2-F1 — HIGH — Zero-init gain creates an architecture-selective bootstrap deadlock

**Spec text at fault:** lines 142–152 — "every seed terminates in a **scalar gain
`g`, initialized to 0**, so Δ ≡ 0 at germination for all four seeds — no
accidental-scale confound at entry."

This directly answers the lead's question 2, and the answer is that **the
duration is not the issue — the asymmetry is.**

With `Δ = g · f(h)` and `g = 0`:

```
∇_g L      = ⟨δ, f(h)⟩            where δ = ∂L/∂Δ     — nonzero
∇_{θ_f} L  = g · (∂f/∂θ)ᵀ δ = 0   at g = 0            — exactly zero
```

At germination the inner module `f` receives **exactly zero gradient**. Only the
scalar `g` moves, and it moves by the alignment of the *randomly initialized* `f`
with the descent direction. Once `g ≠ 0`, `f` gets gradient proportional to `g`
and aligns so that `g·f` points along `−δ`; `g` then grows faster. It is a
coupled, self-reinforcing takeoff seeded by a small random kick — a symmetry-
breaking instability, not a deadlock in the permanent sense. It does bootstrap.
**The problem is that its takeoff time is architecture-dependent, and the spec
gives all four arms the same fixed K≈3 epochs.**

Per seed, at initialization:

- **`norm`** — `f₀ = GroupNorm(h) − h` with γ=1, β=0 is **not random**. It is a
  deterministic, meaningful function that already computes the correction the
  seed exists to provide. On an under-normalized host `⟨δ, f₀⟩` is systematically
  signed from step 1, so `g` grows immediately and consistently. `norm`
  effectively skips the bootstrap.
- **`attn`, `conv_light`, `conv_heavy`** — `f₀` is a random-init network (LN and
  internal BN fix its *scale* at O(1), but not its *direction*). `⟨δ, f₀⟩` is a
  near-zero-mean random variable, so `g` starts as a random walk near zero and
  `f`'s gradient stays near zero with it. Takeoff is slower, and slower still the
  more parameters must organize — worst for `conv_heavy` at 60k.

So rev 3 equalizes the arms at germination by making them all identically dead,
then lets them diverge at rates set by architecture. That is the round-1 F3
confound in new clothes, with a *predictable* direction this time: **biased in
favour of `norm` and against the high-parameter random-init seeds.** Note that
rev 2's bias pointed the same way for the opposite reason (`norm`'s GroupNorm β
was the most runaway-prone parameter under the linear objective). Rev 3 flipped
the mechanism without moving the bias.

**The critical observation: zero-init `g` buys nothing here.** Its stated purpose
is invisibility and entry equalization, but —

- **Invisibility is already guaranteed by STE**, for *any* Δ. `h + (Δ − Δ.detach())`
  is bit-identical to `h` whatever Δ is. `g = 0` adds nothing.
- **Blend-entry continuity is already guaranteed by α**, which starts at
  `p = 1/total_steps ≈ 0`. `g = 0` adds nothing there either.
- The equalization that actually matters is at **blend entry**, not germination —
  and that is precisely what gate 5 measures.

**Fix — normalize at a nonzero τ instead of at zero.** Initialize `g` per seed so
that `RMS(Δ)/RMS(h) = τ` at germination, with τ a single fixed harness constant
shared by all four arms (measure `f₀`'s output RMS on one batch at germination
and set `g = τ·RMS(h)/RMS(f₀)`). This:

- keeps the entry equalization the spec wants — and makes it non-degenerate, at
  the same value gate 5 checks at exit;
- gives `f` a nonzero gradient from step 1, removing the takeoff asymmetry
  entirely;
- costs nothing in invisibility (STE) or blend continuity (α);
- remains a harness property invisible to the policy, so scope pin line 52 holds.

**Rejected alternative, for the record:** making TRAINING duration adaptive
("train until `RMS(Δ)/RMS(h) ≥ τ`, capped at K_max"). This looks attractive but
is *worse* — arms would then reach BLENDING and FOSSILIZED at different epochs,
so they would have different full-influence runways at the horizon, which breaks
the matched comparison that the fan depends on. Do not do this.

### R2-F2 — HIGH — Weight decay on the zero-init gain is a decay-to-death trap

**Spec text at fault:** line 192 — "SGD + Nesterov momentum (fixed LR and weight
decay, stated in code)." No no-decay exclusion list appears anywhere in the spec.

If weight decay applies uniformly to the seed param group, the gain obeys

```
dg/dstep ∝ ⟨−δ, f⟩ − (lr · wd) · g
```

For the three random-init seeds, `⟨−δ, f₀⟩ ≈ 0` during exactly the window in
which `f` cannot improve (because its own gradient is ∝ `g`). Weight decay
supplies a restoring force toward zero during precisely that window. The
bootstrap of R2-F1 is a small signal racing an exponential pull toward the state
it is trying to escape.

This is a well-known interaction — it is why ReZero, LayerScale, and every
production zero-init-residual-gain implementation exclude the gain from weight
decay, alongside biases and normalization parameters.

**Fix:** state an explicit no-decay list in the optimizer contract: the scalar
gain `g`, all normalization affine parameters (GN/LN/BN γ and β), and all biases
are excluded from weight decay. One clause at line 191–197.

**Relationship to R2-F1 — adopt both, for distinct reasons.** τ-init moves `g`
off the absorbing point, so weight decay is no longer racing a near-zero signal;
that removes the *trap*. It does not remove the *distortion*: the equilibrium
`g* = ⟨−δ, f⟩ / wd` remains an artifact of the weight-decay coefficient rather
than of the task, and it scales differently per seed because `⟨−δ, f⟩` does. The
no-decay list is what makes the gain's magnitude a property of the trust region
(λ, τ) rather than of an unrelated regularization constant. Neither fix
subsumes the other.

### R2-F3 — MEDIUM — Gate 5 is the right detector, but its failure routes to the wrong remedy

**Spec text at fault:** gate 5 at lines 372–375, read against the remedy clause
at line 383 — "Failing gates retunes the sampler and re-runs pre-flight."

Gate 5 (`RMS(Δ)/RMS(h)` at blend entry, arms within ~2×) is exactly the right
instrument, correctly placed, and I expect **it will fire** on rev 3 as written,
because R2-F1 predicts a spread that is architectural rather than incidental.

The problem is the remedy. Retuning the *pathology sampler* cannot fix a
bootstrap asymmetry rooted in the seed parameterization — the sampler controls
the host's deficiency, not the rate at which a random-init 60k block organizes
itself. An implementer following line 383 literally will retune the sampler,
watch gate 5 keep failing, and conclude the pathologies are the problem.

**Fix:** make the remedy table gate-specific. Gates 1, 2, 4 and 6 route to the
pathology sampler. **Gate 5 routes to the seed init constant τ, λ, or the seed
LR — never to the sampler.** Gate 3 routes to the horizon or the averaging
window. One sentence at line 383.

### R2-F4 — MEDIUM — The twin arm cannot verify the seed param-group path

**Spec text at fault:** the twin arm, lines 267–272, read against the optimizer
contract at 191–197.

The twin arm is the strongest thing in rev 3 and I want to be clear it is a
better answer than what I asked for in round 1 — it verifies snapshot
completeness, branch-executor equivalence, optimizer restore, and that
deterministic mode is actually in force, continuously rather than once. Step 6's
cross-arm host-weight assertion (280–283) is also excellent, and it happens to
catch the most likely implementation error in the trust-region term: if someone
forgets the `.detach()` on `‖h‖²`, host gradients change and step 6 fires.

But the twin arm runs the **no-op** continuation, so it never appends a seed
param group. The single thing that most distinguishes a seed arm from the base
run — creating a second param group at germination, with its own momentum
buffers, alongside a restored host group — is precisely what the twin arm cannot
exercise. Step 6 covers this partially, but only through **end of TRAINING**;
after that the host legitimately diverges across arms and no bitwise assertion is
possible.

**Fix — add a null-seed arm.** An arm that appends a real seed param group whose
gain is frozen at zero (so `Δ ≡ 0` identically, for the whole lifecycle). Under
the delta contract this arm must reproduce the base run **bitwise through the
entire horizon**, because:

- TRAINING: `h + (0 − 0) = h`; trust-region term is 0 with zero gradient.
- BLENDING: `h + α·0 = h` for every α.
- FOSSILIZING/FOSSILIZED: `lerp` feeds a Δ that is identically zero for every β.

So it is a valid null, and it verifies everything the twin arm cannot: param-
group append ordering, seed-group momentum isolation, the α/β schedule
machinery, the STE code path, and per-arm seed-init RNG derivation — through
BLENDING and FOSSILIZING, where step 6's assertion cannot reach.

Cost is one extra arm per fan (~20% of fan compute). That is real, so run it on a
**subsample** — every 10th fan, plus always in `--selftest`. The twin arm stays
on every fan as the cheap continuous check; the null-seed arm is the periodic
deep check.

**Reconciled with the determinism review — complementary, not duplicate.** Their
HIGH "Optimizer-state rehydration across arms with different parameter sets is
unspecified" (determinism review L283–306) is the source of rev 3's second-param-
group contract, and it converged independently with my round-1 F5 on the same
site. Their proposed assertion is *"on the duplicate no-op arm, the two
optimizers must hash equal after restore"* — a check at the **branch point**, on
an arm they explicitly specify as having **one group** ("The no-op arm has one
group", L304). That is precisely the blind spot R2-F4 names, stated in their own
words. Their check verifies host-group restore is bit-identical; the null-seed
arm verifies that the *two-group* configuration stays bit-identical **through
BLENDING and FOSSILIZING**, where neither their hash check nor step 6's
assertion can reach. Adopt both; neither substitutes for the other.

### R2-F5 — LOW — `g` notation collision, and the `Δ*` formula drops a factor

Two small errors at the same site, one of which I introduced in round 1 and
should own.

**(a) Collision.** Line 143 defines `g` as the **scalar gain**. Line 175 writes
the trust-region minimizer as `Δ* = −g/(2λ)`, where `g` means **the loss gradient
`∂L/∂Δ`** — my round-1 notation. Two different `g`s, 32 lines apart, in a
document whose stated success criterion is that a reader can follow the file
top-to-bottom.

**(b) Missing factor — my error, inherited.** With the normalizer in place the
stationary point is

```
δ + 2λΔ/‖h‖² = 0   ⟹   Δ* = −δ · ‖h‖² / (2λ)
```

Line 175's `Δ* = −g/(2λ)` omits the `‖h‖²`. My round-1 text stated the
unnormalized form and rev 3 copied it faithfully; the error is mine.

**Fix:** rewrite line 175 as `Δ* = −(∂L/∂Δ)·‖h‖²/(2λ)`. This resolves both at
once and requires no change to the seed table's use of `g`.

### R2-F6 — LOW — β ramps linearly where α ramps on a cosine

**Spec text at fault:** line 184 — "β ramps 0 → 1 linearly", against line 180's
cosine ease for α.

A linear ramp has nonzero slope at both endpoints, so the FOSSILIZING →
FOSSILIZED join carries a slope discontinuity in the gradient-coupling schedule.
The cosine ease `0.5(1−cos πp)` was chosen for α precisely because it is C¹ at
both ends; the same argument applies to β, and arguably more so, since β's ramp
is the sole fossilization mitigation (see the SGD note in Part 1).

**Fix:** use the same cosine ease for β. It is the same helper function, it costs
nothing, and it makes "one blend waveform" true of both schedules rather than
one — which is closer to what scope pin line 52 says than the current text is.

## Confidence Assessment

**Overall Confidence:** High on the round-1 verdicts and the two dissolutions;
High on R2-F2/F4/F5/F6; High on R2-F1's *mechanism* with Moderate on its
*magnitude*.

| Item | Confidence | Basis |
|---|---|---|
| Round-1 verdicts (all 9) | **High** | Each checked against specific rev-3 line ranges, cited above. |
| F4 dissolution | **High** | SGD has no per-parameter normalizer; gradient scaling passes through to the update. Elementary. |
| F2 Adam-lag dissolution; 2 epochs adequate | **High** | `1/(1−μ) ≈ 10` steps vs `1/(1−β₂) ≈ 1000`. Two orders of magnitude; the conclusion is not sensitive to the exact μ. |
| R2-F1 mechanism (`∇_{θ_f}L = 0` at `g=0`; takeoff is coupled and architecture-dependent) | **High** | Direct differentiation of `Δ = g·f(h)`. Not an inference. |
| R2-F1 *magnitude* — that the asymmetry is large enough to matter over K≈3 | **Moderate** | Rests on `⟨δ, GN(h)−h⟩` being systematically signed on an under-normalized host (reasoned, plausible, unmeasured) versus `⟨δ, f₀⟩ ≈ 0` for random init (solid). Gate 5 measures exactly this — the honest position is that the mechanism is certain and the size is empirical. |
| R2-F1 fix (τ-init) is safe | **High** | STE guarantees bit-identical forward for any Δ (verified round 1); α starts at `1/total_steps`. Neither property depends on `g = 0`. |
| R2-F2 weight-decay trap | **High** on mechanism | The `−lr·wd·g` term is arithmetic. Confirmed by grep that no exclusion list exists in the spec. Severity depends on the unstated `wd` value — hence the fix is stated as unconditional standard practice rather than tuned. |
| R2-F3 remedy misrouting | **High** | Line 383 says "retunes the sampler" with no gate-specific branching; verified by reading. |
| R2-F4 twin-arm blind spot | **High** | The twin arm is defined as a no-op continuation (267–268); a no-op arm appends no seed param group by construction. |
| R2-F4 null-seed arm is a valid bitwise null | **High** | Walked each lifecycle stage with `Δ ≡ 0`; every stage reduces to `h`. |
| R2-F5 both errors | **High** | Both verified by grep against lines 143, 175, and by re-deriving the stationary point. |

## Risk Assessment

**Implementation Risk:** Low–Medium (all recommendations are pre-implementation
spec edits). **Reversibility:** Easy — no code exists yet.

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| R2-F1 ships → arms enter BLENDING at architecture-determined magnitudes; the WHICH head trains on confounded labels and the money chart is partly an artifact | **High** — same blast radius as round-1 F3 | Moderate–High; mechanism is certain, size is not | τ-init (primary). Gate 5 is a real backstop — this is *detected*, not silent, which is the material difference from round 1. |
| R2-F2 ships → gain pinned near zero for random-init seeds; arm looks like a genuine null result | **High** if it fires | Moderate; depends on the unstated `wd` | No-decay list. One clause, standard practice, no downside. |
| R2-F3 ships → gate 5 fires, implementer retunes the sampler, concludes pathologies are at fault, possibly loosens the band to pass | **Medium**, but corrosive — it would launder the confound past the freeze | Moderate if gate 5 fires at all | Gate-specific remedy table |
| R2-F4 ships → a param-group or momentum-isolation bug survives into BLENDING/FOSSILIZING unverified | Medium | Low–Moderate; step 6 already covers TRAINING | Null-seed arm on a 1-in-10 subsample + `--selftest` |
| Null-seed arm adds ~20% fan compute if run on every fan | Low | Certain if unsubsampled | Subsample explicitly; the twin arm remains the per-fan check |
| R2-F5 ships → implementer reads `Δ* = −g/(2λ)` with `g` as the gain and mis-implements the trust region | Medium | Moderate — the collision is genuinely confusing | One-line formula rewrite |
| τ-init makes Δ's germination magnitude an artifact of τ | Low | Certain by construction | Accepted deliberately, same argument as λ in round 1: a *shared* artifact is a fair comparison, a *per-seed* one is not. Record τ in the fan record beside λ. |
| Over-fitting the design to reviewer findings — rev 3 added λ, τ, β-length, entropy coefficients, exploration schedule as harness constants | Low–Medium | Present | Scope pin line 52 already anticipates this and holds (none are policy-visible). Worth watching that the *count* of frozen constants stays auditable via `frozen_block_hash`. |

## Information Gaps

- **Weight-decay value, seed LR, and momentum μ.** All stated as "fixed … stated
  in code" (192–196) but no numbers appear. R2-F2's severity and the exact
  momentum timescale in Part 1 both depend on them. My μ=0.9 is assumed.
- **Whether `f`'s output projection is zero-init in addition to the gain.** If
  `conv_heavy`'s final BN γ or the `attn` output projection is *also* zero-init,
  the bootstrap is deadlocked harder than R2-F1 describes (two nested zeros).
  The table (147–152) does not say.
- **τ, if adopted.** Its value is an empirical question the pre-flight answers;
  gate 5's ~2× band is the natural place to calibrate it.
- **Magnitude of `‖∂Δ/∂h‖` at fossilization.** Still unmeasured, and still the
  quantity that determines whether the β ramp's length matters at all. The
  α(t)/β(t) plot plus per-arm curves will show it after the fact.
- **The other panel reviews.** I reconciled R2-F4 against the determinism
  review's optimizer-rehydration HIGH (result recorded under R2-F4:
  complementary, no conflict). I have **not** read the reward, statistics, or
  morphogenesis reviews. R2-F1's confound has downstream consequences for the
  WHICH objective and for gate 4's dominance logic, which are those reviewers'
  territory; if any of them reasoned about per-seed Δ magnitude, that is
  unreconciled.
- **No implementation exists.** All findings are against spec text.

## Caveats & Required Follow-ups

**What must be verified before relying on this:**

1. **Confirm the seed-module output projections are *not* zero-init.** If they
   are, R2-F1 understates the problem materially.
2. **Get the weight-decay value.** If `wd = 0` on the seed group already, R2-F2
   is moot; the spec should then say so explicitly rather than leaving it to code.
3. **Treat R2-F1's size as empirical.** I am confident in the mechanism and
   deliberately not confident in the magnitude. Gate 5 on the pre-flight
   episodes settles it — and that run is already planned, so the cost of finding
   out is zero.

**Assumptions:** μ ≈ 0.9; bs = 128 on 50k train (391 steps/epoch); GroupNorm
init γ=1, β=0; internal BN γ init 1; standard (non-zero) init on inner
projections.

**What this review does NOT cover:** the reward/learning redesign (REINFORCE
removal, `J_now`/`J_which`, entropy coupling) — reward reviewer's territory; the
determinism contract, twin-arm bitwise machinery and store concurrency beyond
where they touch optimizer restore — determinism reviewer's; the statistical
protocol (nulls, ceiling, Wilcoxon, GroupShuffleSplit) — statistics reviewer's.
I did not reconcile against those four reviews.

**Recommended next steps, in order:**

1. **τ-init replacing zero-init `g`** (R2-F1) — the one finding that changes a
   result rather than a safeguard.
2. **No-decay list in the optimizer contract** (R2-F2) — one clause, standard,
   no downside, partially redundant with (1) but adopt both.
3. **Gate-specific remedy table** (R2-F3) — one sentence at line 383; cheap
   insurance against laundering the confound past the freeze.
4. **Fix the `g` collision and the `Δ*` factor** (R2-F5) — pure text, my error.
5. **Cosine β ramp** (R2-F6) — one-line consistency edit.
6. **Null-seed arm on a 1-in-10 subsample plus `--selftest`** (R2-F4) — the only
   item with a compute cost; defer if the schedule is tight, since step 6 already
   covers the highest-risk window.

---

# Round 3 (rev 4)

**Reviewed:** `docs/superpowers/specs/2026-08-09-kernel-demo-design.md` @ 6b9f496
**Date:** 2026-08-09
**Mode:** verification pass — round-2 dispositions only. No new hunting.

## Verdict: all six round-2 items closed

Verified against rev-4 text, not against the disposition summary.

| # | Item | Verdict | Verified at |
|---|---|---|---|
| R2-F1 | Zero-init gain → bootstrap deadlock | **Closed** | L146–155. τ-init `g = τ·RMS(h)/RMS(f₀)`, τ=0.05 shared, gain-only. The rationale is recorded correctly, including "zero-init bought nothing" and why. **Q2 answered:** internal projections standard-init, final BN γ=1 — no nested zeros, so the harder deadlock I flagged does not exist. |
| R2-F2 | Weight decay on the gain | **Closed** | L100–107. No-decay list is exactly gain + norm affines + biases. **Q1 answered:** μ=0.9 (my assumption confirmed), lr=0.05, wd=5e-4. |
| R2-F3 | Gate-5 remedy misrouted | **Closed** | L344–345. *"Remedy: τ, λ, seed LR — never the sampler."* Per-gate remedies now on all seven gates, and the other six route sensibly (gate 4 → sampler/menu balance, gate 3 → averaging window/horizon). |
| R2-F4 | Twin arm can't verify the param-group path | **Closed** | L254 (1-in-10 subsample) + L425 (`--selftest`). Both limbs present, as agreed. |
| R2-F5 | `g` collision + missing `‖h‖²` | **Closed** | L167–170. `Δ* = −(∂L/∂Δ)·‖h‖²/(2λ)` — factor restored, symbol disambiguated. The stale "replacement-via-delta" description of `norm` is also gone from the seed table, which it needed to be once the gain made it partial. |
| R2-F6 | β linear vs α cosine | **Closed** | L175–179. β is cosine, and the ramp is named in-spec as the sole fossilization mitigation under SGD-without-clipping. |

The SGD confirmations from round 2 are recorded accurately at L181–184.

## Constant LR vs my F5 concerns — sanity-check requested

**Endorsed, and the justification is stronger than the one recorded.** The spec
gives the reason as "no scheduler → no scheduler state in snapshots" (L102),
which is true but is the smaller half of it.

The larger half: `torch.optim.lr_scheduler` captures `base_lrs` from
`optimizer.param_groups` **at construction time**. This design adds a second
param group *at germination*, i.e. after any scheduler would already exist. That
leaves `base_lrs` shorter than `param_groups`, and the next `.step()` either
raises or silently mismatches LRs across groups depending on torch version.

That is precisely the F5 bug class — optimizer state keyed positionally to a
param-group list that changes mid-run — and it is the same failure shape as the
determinism review's `state_dict()`-keyed-by-index HIGH (their L291–297). A
scheduler would have re-opened it on a second front. **Constant LR eliminates it
structurally rather than by discipline, which is the right kind of fix.** Worth
amending L102 to say so, so the decision is recorded with its actual load-bearing
reason.

One cost to name, already covered by an existing gate: constant LR for 40 epochs
means no annealing, so end-state val accuracy is noisier epoch-to-epoch than a
decayed run, which widens the noise floor gate 3 measures fan density against.
Real tension, but gate 3 detects it, and constant LR simultaneously *serves* the
premise that the host must plateau by epoch ~12–15 (L96–98). Net: right call.

## Two observations on rev-4 edits (both LOW, neither blocks)

Raised only because both are new in rev 4 and cheap to close.

**R3-1 — `g = τ·RMS(h)/RMS(f₀)` divides by a quantity that can approach zero for
`norm`.** `norm`'s `f₀ = GroupNorm(h) − h` is the one seed whose `f₀` is small
exactly when the host does not need it. On a well-normalized host the denominator
shrinks and `g` blows up. I judge this **unlikely** in practice — post-ReLU
activations carry a positive mean that GN recenters, so `RMS(GN(h)−h)` stays
O(RMS(h)) even on a healthy host — but the failure is worth one line of guard
because of how it would *present*: a huge `g` at germination yields either a gate-5
failure or an immediately diverged arm, and the diverged-arm convention (L279,
L293) would record it as `status="diverged"` on `norm`. That reads as an inflated
per-seed-type failure rate — a property of the seed — when it is an init-guard
bug. **Fix:** floor the denominator, `g = τ·RMS(h)/max(RMS(f₀), ε·RMS(h))`, and
log `g` at germination in the fan record beside `RMS(Δ)/RMS(h)`.

**R3-2 — the seed group takes the host's LR (L103–104, "same LR"), and the scalar
gain sits in that group.** Under SGD, `∇_g = ⟨δ, f(h)⟩` is a dot product summed
over the whole Δ tensor (~10⁵ elements), so the gain's gradient is structurally
different in scale from the conv weights beside it in the same group. The trust
region makes this a *stable* equilibrium rather than a runaway — curvature w.r.t.
`g` is `2λ‖f‖²/‖h‖²`, which at the τ-init operating point is ≈ `2λ` — but
stability of gradient descent needs `lr < 2/curvature`, giving roughly

```
λ < 1 / lr_seed ≈ 20        (at lr = 0.05)
```

λ's value is not yet in the spec (gate 5's remedy line is the only place it
appears). **Fix:** when λ is chosen, respect that bound, or give the gain its own
smaller LR. Gate 5 already detects the failure — an oscillating gain puts
`RMS(Δ)/RMS(h)` out of band — so this is a "know the constraint before tuning"
note, not a defect.

## Confidence Assessment

**Overall Confidence:** High on all six closure verdicts — each checked against
cited rev-4 line ranges rather than against the disposition summary. High on the
constant-LR endorsement (the `base_lrs` capture behaviour is standard torch
semantics). **Moderate** on R3-1 (mechanism certain, likelihood judged low on a
reasoned argument about post-ReLU activation statistics, unmeasured) and
**Moderate** on R3-2 (the curvature derivation is sound, but it rests on the
τ-init operating point holding and on λ's unstated value; the numeric bound is
order-of-magnitude guidance, not a threshold to tune against).

## Risk Assessment

**Implementation Risk:** Low. **Reversibility:** Easy — both items are
one-line spec edits, pre-implementation.

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| R3-1 fires → `norm` shows an inflated failure rate misread as a seed property | Medium *if* it fires | Low | ε-floor + log `g` at germination |
| R3-2 → λ chosen above the stability bound; gain oscillates | Low–Medium | Low; needs an unusually large λ | Respect `λ < 1/lr_seed`, or separate gain LR. Gate 5 detects. |
| Constant LR widens the R_a noise floor, compressing fan contrast | Low | Moderate | Already gated (gate 3); remedy line points at averaging window/horizon |

## Information Gaps

- **λ's value** is still unstated. It is the one harness constant in the
  trust-region mechanism that has no number, and R3-2's bound is only actionable
  once it is chosen.
- **Whether `--selftest`'s null-seed smoke episode exercises a `norm` arm on a
  healthy host** — the configuration that would surface R3-1 fastest.
- I did not re-read the reward, statistics, or morphogenesis reviews this round.
  Rev 4 folds their round-2 findings too (deployment rule, gate 7, permutation
  tests); I verified only that none of those edits contradict the lifecycle items
  above, not that they are correct on their own terms.

## Caveats & Required Follow-ups

This was a scoped verification pass, not a fresh review. It confirms that the six
round-2 items are implemented as agreed and that no rev-4 lifecycle edit is
wrong; it does not re-audit surfaces rev 4 changed for other reviewers.

From my side the lifecycle design is **done** — no open HIGH or MEDIUM findings
remain across three rounds. Recommended before implementation, in order:

1. Pick λ, respecting `λ < 1/lr_seed ≈ 20` (R3-2).
2. Add the ε-floor to the τ-init denominator and log `g` at germination (R3-1).
3. Amend L102 to record the `base_lrs`/param-group footgun as the constant-LR
   decision's load-bearing reason.

The remaining risk in this area is now empirical, not structural: gate 5 is the
instrument that decides whether the trust region and τ-init actually delivered
comparable arms, and it runs on episodes already planned.
