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
