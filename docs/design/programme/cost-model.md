<!-- hld: simic HLD v4.1 chapter (split from programme/evaluation.md §22.11 by ADR-0014) · index: ../00-INDEX.md -->
[← HLD index](../00-INDEX.md)

## 22.11.1 The Worked Cost Model

The growth machinery is not free and its price is not a rounding error on
host training. This chapter fixes the arithmetic that turns declared
budgets (INV-23) into a programme number, so that the QA hierarchy is
chosen from data rather than discovered to be unaffordable in Phase E.
It is the referent of `evaluation.md#2211-economy`'s "amortised cost per
successful intervention" bullet, the §27.15 scaffold-cell budget
(`risks-and-open-decisions.md#2715-scaffold-interaction-budget`), and the
K/N constants of the `01-claim.md#28-success-criteria` headline criterion.
Adopted by ADR-0014; owner decisions D1 (negative-result scope) and D2
(endpoint family) are recorded there.

Every quantity below is a **declared placeholder with a named retirement
path**. None is a measurement. The model's product is not the point
estimates — it is the *iso-surface*: the region of parameter space in
which the design is affordable, and the boundary at which the correct
response is to restructure rather than to optimise. The companion
pre-registration (`prereg-cost-model-campaign-1.md`) commits the
measurement campaign that retires the placeholders.

**The unit of account** is the **host-equivalent run (HER)**: one complete
ordinary MVP host training run (`phases.md` Phase B baseline), with no
growth machinery attached, on the declared execution stack (INV-05,
ADR-0013). A branch that runs a tenth of a host trajectory costs 0.1 HER.
HER is chosen over accelerator-hours because it is invariant to the
CPU-lab-versus-GPU choice that ADR-0013 leaves open.

### (a) Declared parameters

| Symbol | Meaning | Placeholder | Retires when |
|---|---|---|---|
| $S$ | host run length, steps | 25 000 | Phase B baseline is running (`phases.md` Phase B) |
| $h = H/S$ | QA branch horizon as a fraction of a host run | **0.02** | §27.5 is closed — the $d_z(H)$ curve is measured and its interior optimum chosen (see the coupling note below) |
| $P$ | candidates per adjudicated pool, excluding no-op | 12 | pool composition (`../07-counterfactual-engine.md`) is fixed for the MVP |
| $r$ | repeated branches per candidate for execution-noise estimation | 1 (`ACADEMY_EXACT`), 5 (`CALIBRATED_STOCHASTIC`) | Phase D measures the calibrated-stochastic variance (`phases.md` Phase D) |
| $\tau$ | exactness tax — deterministic-kernel overhead multiplier | 1.30 (GPU), 1.00 (CPU lab) | **Phase B measures it on the MVP hosts** (ADR-0013) — already a committed milestone |
| $a$ | admission rate: adjudicated pools yielding an admitted growth | 0.25 | Phase F produces the adjudication-regret curve (`phases.md` Phase F) |
| $D$ | decision points (adjudicated pools) per base trajectory | 8 | Phase H, from Aurelia's commissioning cadence |
| $\rho$ | intra-trajectory correlation (ICC) of pool outcomes | **0.30** | **free from the anchor corpus** — multiple decision points per seed is exactly the ICC estimator (ADR-0011) |
| $p_R$ | per-pool hit rate of the random-search control arm | **0.10** | **campaign 1** — random candidates are already permanent pool members, so a random-only pilot measures it directly |
| $r_{\text{rej}}$ | Elesh structural rejection rate | 0.30 | Phase C (`evaluation.md#224-elesh` already names it) |
| $r_{\text{cf}}$ | Urabrask compile-failure rate | 0.05 | Phase C |
| $\phi$ | Nissa observation cadence, steps between `ablated_context` reads | 50 | Phase B telemetry config |
| $\mu$ | **rent** — per-step host forward-pass multiplier of an embodied growth | 1.05 (small cell) – 1.35 (attention class) — **measured from the predecessor** | Phase C, once the MVP growth envelope is compiled |
| $R$ | Esper library reuse factor (the amortisation denominator) | **$\gtrsim 10^2$ — measured, not assumed** | see (d) |
| $\nu$ | Urborg retrieval hit rate for recurrent candidates | 0.0 initially | Phase G; retrieval quality metrics should carry it as an endpoint |

**Note on $\mu$ — HER is not quite unity once a growth lands.** The HER
definition above is an *ordinary* host run with no growth attached. A
trajectory in the fleet does not stay that way: once a growth is admitted
and blending, every mainline step carries the growth's forward-pass
overhead. This is the Economy list's existing "rent paid" bullet, and it
has measured placeholder values — the predecessor's
`BLUEPRINT_COMPUTE_MULTIPLIERS` (`esper-lite`,
`src/esper/nissa/analytics.py`) records 1.02 for a normalisation cell, 1.05
for a small conv or LoRA adapter, 1.25 for a double conv block and 1.35 for
a self-attention head. A trajectory carrying one attention-class growth for
the back half of its run therefore costs $\approx 1.18$ HER, not 1.00.
Rent is second-order against the QA branch term at MVP scale and is
**excluded from the (c) and (g) arithmetic below** — but it is excluded by
declaration, not by oversight, and it is not second-order at Phase K where
several committed growths coexist.

**Coupling note on $h$.** The cost model **cannot be closed tighter than
§27.5** (`risks-and-open-decisions.md#275-qa-horizon-and-evidence-floor`).
The QA horizon has an interior optimum set by the ratio of intervention
signal to branch-divergence noise, not by budget; if that optimum lands at
$h = 0.10$ the per-intervention numbers below rise fivefold. $h = 0.02$ is
a placeholder for arithmetic, never a recommendation. This is why (g)
states a decision surface rather than a decision number. The model is
provisional by construction until §27.5 closes.

### (b) Fleet arithmetic — why branches do not buy power

The independent statistical unit is the **base host trajectory**
(`../07-counterfactual-engine.md#149-statistical-unit`), and branches from
one base trajectory never cross splits or inflate independent sample
counts (INV-32). Counterfactual branches are paired measurements, not
additional independent hosts (`evaluation.md#2212-reliability`).

The consequence is quantitative, not stylistic. Averaging $D$ pools within
one trajectory yields an effective count

$$
D_{\text{eff}} = \frac{D}{1 + (D-1)\rho} \;\xrightarrow[D \to \infty]{}\; \frac{1}{\rho},
$$

which at $\rho = 0.30$ **saturates at 3.33 regardless of how many pools
are run**:

| $D$ | 1 | 2 | 4 | 8 | 16 | 32 | $\infty$ |
|---|---|---|---|---|---|---|---|
| $D_{\text{eff}}$ | 1.00 | 1.54 | 2.11 | 2.58 | 2.91 | 3.11 | 3.33 |

Beyond $D \approx 8$ additional pools buy precision inside a trajectory
and almost no inference about the population. **Statistical power is
bought with base trajectories; branches are bought with pool budget.** The
two are not substitutes, and the eight-cell interaction matrix
(`curriculum.md`) multiplies the trajectory count, not the branch count.

Per-trajectory cost is one host run plus its pools:

$$
C_{\text{traj}} = 1 + D \cdot C_{\text{pool}} \quad\text{HER}.
$$

At the placeholders (Academy CPU lab, $h=0.02$, $P=12$, $D=8$):
$C_{\text{pool}} = 0.260$, $C_{\text{traj}} = 3.08$ HER.

**Cell allocation (the §27.15 recommendation, adopted by ADR-0014):** run
the two corner cells — fully scaffolded (`ACADEMY_EXACT` /
`REPEATED_ACQUISITION` / `REFERENCE_ANCESTRY`) and fully withdrawn — at
full $n = 32$ trajectories, and the six intermediate single-axis and
interaction cells at $n = 16$ with their MDE declared rather than at full
power.

| Allocation | Trajectories | HER (Academy) | HER (`CALIBRATED_STOCHASTIC`, $r{=}5$) |
|---|---|---|---|
| all 8 cells at $n = 32$ | 256 | 788 | 2 918 |
| **2 corners at 32 + 6 interactions at 16** | **160** | **493** | **1 824** |

The $n=16$ interaction cells carry an MDE of $0.219$ — they can detect a
Momir-versus-random gap of $2.19\times p_R$ or larger, and nothing
smaller. That is an interpretability instrument for explaining a gap
between the corners (which is all `curriculum.md` asks of them: *"enough
intermediate cells to explain any gap"*), not a confirmatory claim.
**Stating that MDE is what converts the allocation from a cost line into a
closed decision.**

### (c) Per-admitted-growth cost stack

The stack is generation → Elesh → Urabrask → Jin-Gitaxias QA branches
(including the mandatory no-op arm) → Isperia.

**Generation inflation.** Momir must emit more than $P$ because Elesh
rejects and Urabrask fails to compile:

$$
P_{\text{generated}} = \frac{P}{(1 - r_{\text{rej}})(1 - r_{\text{cf}})}
= \frac{12}{0.70 \times 0.95} = 18.0 .
$$

At $r_{\text{rej}} = 0.50$, $r_{\text{cf}} = 0.20$ it is 30.0. Both rates
are already evaluation endpoints; this is the term that makes them
economic rather than merely diagnostic.

**Rollout-free stages.** Momir design, Elesh canonicalisation, Urabrask
eager compilation and Isperia adjudication consume no Tolaria rollout.
At MVP scale they are $\ll 0.01$ HER per pool and are **declared
negligible-but-not-zero**; they are not negligible at Phase K scale, and
Isperia's re-adjudication is explicitly GPU-free. Carry them as declared
spend (INV-23), not as an omission.

**The QA branch term dominates.** The mandatory no-op arm is
constitutional — every admission case includes a measured no-intervention
alternative (**INV-15**) and Isperia assigns it policy utility exactly
zero (**INV-16**), with Jin-Gitaxias always measuring a matched no-op
branch (`../07-counterfactual-engine.md`). It is a real, separately-paid
branch, not an accounting convenience:

$$
C_{\text{pool}} = (P + 1)\, h\, \tau\, r , \qquad
C_{\text{admit}} = \frac{C_{\text{pool}}}{a} .
$$

Multi-horizon measurement is **nested, not additive** — horizons are read
along one branch, so the pool pays $\max(H)$, not $\sum H$. This is worth
stating because the naive reading multiplies the cost by the horizon
count.

| Regime | $r$ | $\tau$ | HER / pool | **HER / admitted growth** |
|---|---|---|---|---|
| `ACADEMY_EXACT`, CPU lab | 1 | 1.00 | 0.260 | **1.04** |
| `ACADEMY_EXACT`, GPU | 1 | 1.30 | 0.338 | **1.35** |
| `CALIBRATED_STOCHASTIC` | 5 | 1.00 | 1.300 | **5.20** |
| `CALIBRATED_STOCHASTIC` | 10 | 1.00 | 2.600 | **10.40** |

These are *cells on a surface*, not the answer. The same formula at
$h = 0.10$, $P = 24$, $r = 10$, $\tau = 1.3$ gives **130 HER per admitted
growth** — see (g).

### (d) The amortisation bar

Esper amortises generation and validation across every future use of a
library entry; Simic amortises neither. A bespoke candidate used once
carries the full Jin-Gitaxias cost for that one use, plus a per-candidate
safety characterisation never reread (the `QualityReport` is Simic's BSDS,
produced per candidate and read once).

**The reuse factor is measured, not assumed.** The predecessor
`esper-lite` library is **13 entries**
(`src/esper/leyline/factored_actions.py:BLUEPRINT_ID_TO_INDEX`), and a
single 48-environment training log records **thousands of germination
events** — order 450 uses per entry in one run, with usage spread
near-uniformly across the CNN families. Discounting heavily for failed
germinations, $R \gtrsim 10^2$ per entry per run, and the library is
authored once across the whole programme. **Esper's amortised per-use
validation cost is therefore effectively zero.**

That fact sets the shape of the bar. It is *not* "bespoke must be $R$
times better" — that would compare a cost ratio against a utility ratio, a
category error. Because $Q_{\text{lib}}/R \to 0$, the bar is the **full
un-amortised bespoke cost**:

$$
\underbrace{\Delta U_{\text{reference}}(c)}_{U(c) - \max_{r \in R} U(r)}
\;\ge\;
\lambda_{\text{cost}} \left[
\underbrace{(1-\nu)\,C_{\text{admit}} + \nu\,C_{\text{retrieval}}}_{\text{Simic, per use}}
\;-\;
\underbrace{\frac{Q_{\text{lib}} + G_{\text{lib}}}{R}}_{\approx\, 0}
\right]
$$

where $\lambda_{\text{cost}}$ is the utility function's cost weight
(shared between selection and retention per INV-33) and $\nu$ is the
Urborg retrieval hit rate. Two consequences the design should carry:

- **The bar softens exactly as $\nu$ rises.** Canonical semantic hashes,
  equivalence classes and Urborg retrieval mean a recurring bespoke
  candidate is served from history rather than regenerated. **Retrieval
  hit rate is therefore an economic endpoint, not merely a quality
  metric** — a high $\nu$ means Simic converges toward Esper and Esper was
  right; a low $\nu$ with positive $\Delta U_{\text{reference}}$ is the
  strongest available result for the pivot.
- **$\Delta U_{\text{reference}}$ is the quantity the bar is denominated
  in.** `evaluation.md` already carries "reference-frontier utility
  improvement"; this chapter is why it is load-bearing rather than one
  metric among thirteen.

### (e) Anchor corpus pricing

ADR-0011 requires the corpus be priced here. The naive reading of
"seeds × (1 + sampled decisions × action-set size) full-length runs"
**overcharges by roughly 2×**, for two reasons worth stating explicitly
because a reader will make the same mistake:

1. **Branches are tails, not full runs.** A fork at step $t$ runs
   $t \to S$. ADR-0011's "every branch runs to end-of-run" describes
   *trajectory completeness* — the branch is not truncated at a QA horizon
   — not incremental compute. With decision points spread through the run,
   mean incremental cost is $\approx 0.5$ HER per branch.
2. **The no-op arm is already paid.** Labels are path-conditional (a
   decision's counterfactual is measured given the decisions before it),
   so all sampled decision points sit on one spine — the base seed's own
   trajectory. The no-op continuation from $t_k$ **is** that spine. It is
   free here. *(It is emphatically not free in the QA pool stack of (c),
   where INV-15/INV-16 make it a real extra branch. Do not blur the two
   cases.)*

$$
C_{\text{corpus}} = \text{seeds} \times \bigl(1 + D_{\text{samp}} \times A \times \bar{f}_{\text{tail}}\bigr)
\quad\text{HER},\qquad \bar{f}_{\text{tail}} = 0.5,
$$

with $A$ the action set **excluding** no-op.

| seeds | $D_{\text{samp}}$ | $A$ | HER |
|---|---|---|---|
| 24 | 2 | 3 | 96 |
| **24** | **4** | **3** | **168** |
| 24 | 4 | 5 | 264 |
| 24 | 8 | 5 | 504 |
| 36 | 8 | 5 | 756 |

**The sampling budget that caps it.** ADR-0011 rejected the every-decision
× every-action fan-out as combinatorial; the cap is
$D_{\text{samp}} \le 4$ and $A \le 3$ at MVP scale, giving **168 HER for a
24-seed corpus**. ADR-0011's reversal trigger orders the shrink correctly
and this model concurs: **shrink $A$ and $D_{\text{samp}}$ before shrinking
seeds, because $n$ is seeds** (INV-32) and seeds are the only axis that
buys inference. The corpus is nonetheless the largest single line item in
the programme at these settings — larger than the entire QA fleet — which
is the number the owner pre-accepted in principle and has now seen
(ADR-0014).

### (f) `ablated_context` forward-pass overhead

`TelemetryEnvelope.ablated_context`
(`../05-leyline-contracts.md#92-telemetryenvelope`) requires Wrenn to
expose an ablated forward path (`../domains/wrenn.md`) and Nissa to
produce ablated-path telemetry (`../domains/nissa.md`), which is an
**extra forward pass per observation**. Taking a forward pass as
$\approx 1/3$ of a forward+backward training step:

| cadence $\phi$ (steps) | 1 | 10 | 50 | 200 |
|---|---|---|---|---|
| host-cost overhead | **+33.3%** | +3.3% | +0.67% | +0.17% |

**Design consequence, not merely a sensitivity:** a per-step ablated
context costs a third of all host training, permanently, on mainline *and*
on every branch. The model recommends a **declared observation-cadence
floor** of $\phi \ge 25$ steps in the `TelemetryEnvelope` profile, with
per-step ablation available only as an explicitly budgeted diagnostic
regime (ADR-0014). Telemetry purity (INV-34) is unaffected either way;
this is economy, not correctness.

### (g) Headline outputs and the decision rule

**Programme budget** (Academy CPU lab, placeholders as declared):

$$
\underbrace{493}_{\text{8-cell fleet}} \;+\; \underbrace{168}_{\text{anchor corpus}} \;+\; \underbrace{300}_{\text{Stage 0–9 schools (placeholder)}} \;\approx\; 960 \ \text{HER}.
$$

In `CALIBRATED_STOCHASTIC` at $r = 5$ the fleet term rises to 1 824 and the
total to $\approx 2\,300$ HER. **The programme is order $10^3$
host-equivalent runs**, and it is robust to the placeholders at that
resolution: no plausible parameter set puts it at $10^2$, and only the
worst corner of (c) puts it at $10^4$.

**Per admitted growth: 1.0–5.2 HER** at the declared placeholders; the
honest statement is the surface, not the cell.

**The decision rule.** The restructure threshold is
$C_{\text{admit}} = 40$ HER per admitted growth — the figure the peer
review named, and the point at which growth QA costs more than the
adaptation it protects (*QA cost dominance*,
`risks-and-open-decisions.md`). The threshold is crossed when

$$
\frac{(P+1)\,h\,\tau\,r}{a} > 40 .
$$

Maximum branch horizon $h$ before crossing, at $\tau = 1$:

| | $r{=}1$ | $r{=}3$ | $r{=}5$ | $r{=}10$ |
|---|---|---|---|---|
| $P{=}6$, $a{=}0.25$ | 1.43 | 0.48 | 0.29 | 0.14 |
| $P{=}12$, $a{=}0.25$ | 0.77 | 0.26 | **0.15** | 0.077 |
| $P{=}24$, $a{=}0.25$ | 0.40 | 0.13 | 0.080 | 0.040 |
| $P{=}12$, $a{=}0.10$ | 0.31 | 0.10 | 0.062 | 0.031 |
| $P{=}24$, $a{=}0.10$ | 0.16 | 0.053 | 0.032 | 0.016 |

The threshold is **live, not hypothetical**. At $P = 24$, $r = 10$,
$a = 0.10$, any horizon beyond 1.6% of a host run crosses it. The
combination that actually breaches — long horizons, large pools, stochastic
replication, and a *low* admission rate — is the combination the design is
otherwise steering toward: the pool composition lists thirteen classes,
§27.5 may well want a long horizon, Phase D wants repeats, and a healthy
Isperia choosing no-op often (INV-15/16, and the no-op precision/recall
endpoints) *lowers* $a$. **A well-behaved judge makes the economics worse,
and the model says so plainly.** For exactly that reason, cost per
*adjudicated pool* is reported alongside cost per admitted growth, so that
a system correctly declining to intervene does not read as an economic
failure.

**The restructure lever, named in advance.** If the measured
$C_{\text{admit}}$ exceeds 40 HER, the response is not optimisation but the
**tiered Field QA cascade** (`../07-counterfactual-engine.md`): move the
modal candidate to tier 1 (static artefact checks and horizon-zero
measurement) and tier 2 (learned measurement with predicted uncertainty),
and reserve full paired branches for tier-3 survivors. That reduces the
*effective* $P$ in the expensive tier rather than the *nominal* $P$ in the
pool — which preserves pool composition, complete negative retention
(INV-31), and the permanent harmful/long-term-regressing fixtures
(ADR-0010) that the tail veto (INV-45) needs. The lever is already
specified; what this model adds is the **trigger** and the fact that
pulling it is a Phase-E-or-earlier decision, not a Phase K optimisation.

### (h) $K$ and $N$ for the headline criterion

The success criterion (`../01-claim.md#28-success-criteria`) asks that
Momir pools contain useful canonical growth *at a materially higher rate
than random search*. Random candidates are already permanent pool members,
so this is a **within-pool matched comparison** at a common host state
over a common future (INV-06), anchored on the same no-op (INV-15/16) —
the strongest available design, and the reason $sd_d$ is small enough to
be affordable at all.

**The estimand.** Per pool $i$, let $M_i$ and $R_i$ indicate whether the
Momir arm and the random arm respectively yielded at least one candidate
with positive certified evidence. With $b = \Pr(M{=}1, R{=}0)$ and
$c = \Pr(M{=}0, R{=}1)$, the paired difference is $\delta = b - c$ and the
claim ratio is $K = p_M / p_R$. **Test the difference, report the ratio**
— per-trajectory ratios are unstable with zero denominators, and the
aggregate-then-test route (one difference per trajectory, then a paired
test across trajectories) is the boring choice INV-32 requires.

**The derivation.** At $p_R = 0.10$ with positive within-pool association
$\Pr(\text{both}) = 0.7 \min(p_M, p_R)$:

| $K_{\text{true}}$ | $p_M$ | $b$ | $c$ | $\delta$ | $sd$ (per pool) | $sd_d$ (per trajectory, $D{=}8$, $\rho{=}0.30$) |
|---|---|---|---|---|---|---|
| 2 | 0.20 | 0.130 | 0.030 | 0.100 | 0.387 | 0.241 |
| **3** | 0.30 | 0.230 | 0.030 | 0.200 | 0.469 | **0.292** |
| 4 | 0.40 | 0.330 | 0.030 | 0.300 | 0.520 | 0.323 |

Trajectories needed for 80% power to put the CI lower bound above the
declared floor $K_{\text{floor}}$ (i.e. margin $\delta - (K_{\text{floor}}-1)p_R$):

| $K_{\text{true}}$ \\ $K_{\text{floor}}$ | 1.0 | 1.5 | 2.0 | 2.5 |
|---|---|---|---|---|
| 2 | 48 | 185 | — | — |
| **3** | 19 | **32** | 69 | 270 |
| 4 | 12 | 16 | 23 | 39 |

**Fixed by ADR-0014: $K = 1.5$, $N = 256$ adjudicated pools — which is
32 base trajectories × 8 pools.** State it in that order, always:
$n = 32$, not $n = 256$ (INV-32). The rationale is the shape of the table,
not a preference: $K_{\text{floor}} = 2.0$ is the intuitively attractive
"twice random search" and it **more than doubles the fleet** (32 → 69
trajectories, +115% compute) for a claim only one notch stronger.
$K_{\text{floor}} = 1.0$ is cheap (19) but is not "materially higher" in
any defensible sense. $K = 1.5$ is the knee.

**Running the criteria forward** at $n = 32$, $sd_d = 0.292$,
floor $\delta = 0.05$:

| true $K$ | ship | abandon | inconclusive |
|---|---|---|---|
| 1.0 | 0.002 | 0.153 | **0.845** |
| 2.0 | 0.152 | 0.002 | 0.846 |
| **3.0** | **0.805** | 0.000 | 0.195 |
| 4.0 | 0.997 | 0.000 | 0.003 |

The fleet reliably confirms the criterion when Momir is genuinely 3× random
search, and reliably confirms nothing otherwise. That asymmetry is real;
its consequence for the promised negative result is an owner decision
recorded in ADR-0014 (D1): **the inferiority margin the budget buys is
pre-registered** — at $n = 32$ the fleet can conclude "Momir is not
$\ge 1.5\times$ random search" with 80% power, and the negative-result
clause of `../01-claim.md` holds at that stated, weakened strength. The
symmetric refutation (185 trajectories, ~6× the confirmatory fleet) was
priced and declined.

**The endpoint family (owner decision, ADR-0014 D2).** The success
criterion has *two* clauses: a materially higher rate than random search,
**and lower online cost than comparable iterative construction** — the
latter against the bounded online-optimised candidates already in the pool
and built as a Phase F control. Everything above prices the rate clause.
The decision: **the rate clause is the single primary confirmatory
endpoint; the cost clause is descriptive** — reported with a bootstrap CI
over units, no $\alpha$ spent, no correction carried, $n$ unchanged at 32.
(The declared-family-of-2 alternative at $\alpha = 0.025$ and $n = 39$ was
priced and declined. The previously implicit position — two clauses, one
power calculation, no declared family — is the one option that was never
legitimate.) Whichever pre-registration runs first must restate this
declaration before the first confirmatory unit runs.

---

### Status, confidence and risk

| Decision | Confidence | Basis |
|---|---|---|
| HER as unit of account | **High** | standard practice; the evaluation framework already asks for "host-equivalent compute per trial" |
| Branches ≠ power; $D_{\text{eff}}$ saturation | **High** | INV-32 reads directly; the arithmetic is a definition, not an estimate |
| No-op arm is a real paid branch | **High** | INV-15, INV-16 read directly |
| Multi-horizon is nested not additive | **High** | measurement is along a branch |
| Corpus tail-fraction correction | **Medium-high** | mechanism follows from path-conditional labelling (ADR-0011); the 0.5 mean tail assumes decision points uniform over the run |
| Reuse factor $R \gtrsim 10^2$ | **Medium-high** | *measured* — 13-entry catalogue, thousands of germinations in one log; but one log, and germination ≠ successful admission |
| Programme total $\approx 10^3$ HER | **Medium** | robust at order-of-magnitude across the placeholder ranges; not at 2 significant figures |
| $K = 1.5$, $n = 32$ trajectories | **Medium** | derivation is sound; rests on invented $p_R = 0.10$ and $\rho = 0.30$ |
| Per-admitted-growth 1.0–5.2 HER | **Low** | a restatement of $h = 0.02$; the surface in (g) is the defensible artifact |
| 40 HER restructure threshold | **Low-medium** | the *form* is confident; the *level* is inherited from the peer review, not derived from a Simic measurement |

**Locked at launch (irreversible once the fleet starts):** the unit of
analysis; $K_{\text{floor}}$ and $n$ (pre-registered — changing them after
seeing data destroys the confirmatory status; if $\rho$ is 0.5 rather than
0.30, $n = 32$ is underpowered by ~30%, which is ADR-0014's reversal
trigger); the split assignment (grouped by base trajectory, INV-32).
**Reversible mid-experiment:** $h$, $P$, $r$, $\tau$ (per-pool
configuration, re-declarable between cells provided the change is recorded
in `ScaffoldState` (INV-39) and cells are not silently pooled); the corpus
sampling budget (ADR-0011's reversal trigger governs, shrink $A$ and
$D_{\text{samp}}$ before seeds); the QA-hierarchy restructure itself —
that is what the threshold is for.

**What breaks if the model is simply wrong:** the failure mode is not
overspend, it is **arriving at Phase E with a QA hierarchy that cannot be
afforded and no pre-declared lever**, which historically becomes "optimise
later" and then "reduce the pool," which silently deletes the harmful and
long-term-regressing fixtures that the tail veto depends on (ADR-0010).
The threshold in (g) exists to make that trade explicit rather than
emergent.

### Caveats

- This model prices **compute**, not wall-clock or engineering time. A
  960-HER programme on a spare-time cadence is bounded by neither.
- HER assumes MVP-scale hosts. This chapter does **not** extrapolate to
  Phase K image-scale tasks, where the rollout-free stages stop being
  negligible and the compile budget becomes material.
- The eight-cell matrix is priced as eight independent cells. The
  curriculum permits staging; a staged schedule changes the cash-flow
  profile but not the total, and this model says nothing about ordering.
- No number here is a measurement of Simic. Every one is either a declared
  placeholder or an arithmetic consequence of declared placeholders. The
  companion pre-registration (`prereg-cost-model-campaign-1.md`) fixes
  which measurements retire which placeholder, and in what order.
- Even executed perfectly, this model cannot establish that the growth
  machinery is *worth* its cost. It establishes what the cost is and where
  the affordability boundary lies; whether $\Delta U_{\text{reference}}$
  clears the bar in (d) is an empirical result of the programme, not an
  output of its budget.
