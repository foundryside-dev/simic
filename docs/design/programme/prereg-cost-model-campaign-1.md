<!-- hld: pre-registration record (ADR-0014) · companion to programme/cost-model.md · index: ../00-INDEX.md -->
[← HLD index](../00-INDEX.md)

# Pre-registration — Cost-Model Measurement Campaign 1

**Status:** committed (ADR-0014) · **Retires:** placeholders in
`cost-model.md` · **Tracker:** simic-642c2c1823 · **Runs before:** Phase E
(`phases.md`); earliest possible after Phase D branch/replay lands.

This file is committed before the first measurement run. Its purpose is to
fix what is measured and how it is counted *before* data can influence the
answer. Amendments are new records, never edits (INV-36).

---

## 1. Unit of analysis

The independent statistical unit is the **base host trajectory**
(`../07-counterfactual-engine.md#149-statistical-unit`, INV-32). One
independently seeded full host run = one observation. Branches, candidates,
pools, decision points and horizons are **repeated measures within a unit**
and never increment `n`.

- `unit_id` = base trajectory seed; recorded on every row of every results
  table.
- Aggregate to **one number per unit** before any test.
- Every reported interval is across units. Any table reporting `n` greater
  than the number of host runs launched is a defect.

This holds for every measurement below, including the ones that look like
pure engineering telemetry — $\tau$ and the `ablated_context` overhead are
per-step ratios, but their *variability* is a trajectory-level quantity.

## 2. What is measured

| # | Quantity | Instrument | Retires |
|---|---|---|---|
| **M1** | $d_z(H)$ curve: standardised paired effect vs horizon | branches measured at $H \in \{100, 250, 500, 1000, 2500\}$ steps, **nested along one branch** (not re-forked) | $h$ — and feeds §27.5 (`risks-and-open-decisions.md#275-qa-horizon-and-evidence-floor`) |
| **M2** | $p_R$: per-pool hit rate of the random control arm | random-only pools; positive certified evidence per `QualityReport` | $p_R$ |
| **M3** | $\rho$: intra-trajectory ICC of pool outcomes | variance decomposition across the $D$ pools within each unit (free from M2) | $\rho$ |
| **M4** | $sd_d$: SD across units of the per-unit Momir−random paired difference | one difference per unit from the same pools | the modelled $sd_d = 0.292$ |
| **M5** | $\tau$: exactness tax | identical host run under deterministic-kernel and default-kernel profiles, CPU and GPU | $\tau$ (**already an ADR-0013 / Phase B milestone**) |
| **M6** | `ablated_context` overhead | host run at $\phi \in \{1, 25, 50, 200\}$; wall-clock and FLOP ratio | the $1/3$-of-a-step estimate and the recommended cadence floor |
| **M7** | $r_{\text{rej}}$, $r_{\text{cf}}$ | Elesh reject / Urabrask compile-fail counts over generated candidates | $P_{\text{generated}}$ inflation |
| **M8** | $C_{\text{pool}}$ realised | measured spend records (INV-23), not inferred from the formula | validates the cost stack of `cost-model.md#c-per-admitted-growth-cost-stack` as a whole |

**M1 is the priority.** $h$ is the most leveraged parameter in the model and
the only one that can move the headline by 5×. If budget permits one
measurement, it is M1.

**Not measured in campaign 1:** $a$ (admission rate — needs Phase F),
$\nu$ (retrieval hit rate — needs Phase G), $R$ (Esper reuse factor — a
log-mining task, not a run). These retire later; the model carries them as
declared placeholders until then.

## 3. Planned n

- **M1:** $n = 8$ base trajectories. Sufficient for a curve *shape* and an
  interior optimum; explicitly **not** sufficient for a confirmatory
  horizon claim. The chosen $H$ is provisional until M1 repeats at $n \ge 12$.
- **M2 / M3 / M4:** $n = 12$ base trajectories × $D = 8$ pools = 96
  adjudicated pools. **Twelve units, ninety-six pools** — stated in that
  order. $n = 12$ is the minimum for a usable variance estimate; at that
  size the 95% CI on $sd_d$ still spans $[0.71\times, 1.70\times]$, which
  is why §5 mandates UCL planning downstream.
- **M5 / M6:** $n = 3$ trajectories per configuration. These are ratios with
  small trajectory-level variance; 3 is adequate and will be reported with
  its range, not an interval.
- **M7:** rides along on M2/M4; no additional runs.

Total campaign cost at the `cost-model.md` placeholders: **$\approx 60$
HER** (12 units × 3.08 HER for M2–M4/M7, plus 8 short-branch units for M1,
plus ~12 for M5/M6). This is ~6% of the projected programme and is the
cheapest possible insurance against sizing the confirmatory fleet wrong.

## 4. Stopping rule

**Fixed-n. No interim look at any effect.**

- The campaign stops at the planned `n` for each measurement. It does not
  stop early because a curve looks clean, and it does not extend because a
  number looks marginal.
- **One permitted blinded interim, for M4 only:** at $n = 8$, re-estimate
  $sd_d$ **without examining the effect direction or magnitude**, solely to
  decide whether the confirmatory fleet of `cost-model.md#h-k-and-n-for-the-headline-criterion`
  needs resizing. This is blinded sample-size re-estimation and spends no
  $\alpha$.
- **Failed runs are scored, never dropped.** A trajectory that crashes,
  diverges, or fails the Academy determinism gate is recorded with its
  failure class and retained (INV-31); it does not silently reduce `n`.
  Pairs are never partially dropped — if one arm of a pool fails, the pool
  is scored as a failure for both arms.
- **Re-tightening trigger (ADR-0012):** if M5 returns $\tau > 2.0$ on the
  intended Academy host, the CPU-lab option is taken by default rather than
  re-litigated, per ADR-0013.

## 5. Placeholder retirement map

| Placeholder in `cost-model.md` | Value | Retired by | Until then |
|---|---|---|---|
| $h = 0.02$ | branch horizon fraction | **M1** (+ §27.5 closure) | every cost-model number is quoted with its $h$ |
| $p_R = 0.10$ | random-arm hit rate | **M2** | $K$/$N$ are provisional |
| $\rho = 0.30$ | intra-trajectory ICC | **M3** | $D_{\text{eff}}$ ceiling of 3.33 is provisional |
| $sd_d = 0.292$ | per-unit difference SD | **M4** | fleet sized at the **80% UCL** of the M4 estimate, never its point estimate |
| $\tau = 1.30$ | exactness tax | **M5** (Phase B, ADR-0013) | GPU/CPU lab choice stays open |
| $\phi$ overhead $\approx 1/3$ per read | ablated forward pass | **M6** | cadence floor $\phi \ge 25$ recommended, not enforced |
| $r_{\text{rej}} = 0.30$, $r_{\text{cf}} = 0.05$ | pipeline loss rates | **M7** | $P_{\text{generated}} = 18$ is provisional |
| $C_{\text{pool}}$ formula | cost stack | **M8** | formula is unvalidated arithmetic |
| $\mu = 1.05$–$1.35$ | rent (embodied-growth step multiplier) | Phase C | measured from `esper-lite`; excluded from the headline arithmetic by declaration |
| $a = 0.25$ | admission rate | Phase F | **not in this campaign** |
| $\nu = 0$ | retrieval hit rate | Phase G | **not in this campaign** |
| $R \gtrsim 10^2$ | Esper reuse factor | esper-lite log mining | measured order-of-magnitude, one log |

**Sizing discipline, pre-committed:** when M4 returns, the confirmatory
fleet is sized at the **80% upper confidence limit** of $sd_d$, not its
point estimate. From $n_{\text{pilot}} = 12$ that is a $1.25\times$
inflation. $\delta$ is taken from the cost model (the $K_{\text{floor}}$
margin), **never** from this campaign's observed effect — a pilot's point
estimate at this power is inflated 1.4–1.8× and sizing from it produces a
confirmatory fleet that fails to replicate.

**Endpoint family — decided (ADR-0014 D2):** the rate clause of the
success criterion is the single primary confirmatory endpoint at $n = 32$;
the online-cost clause is descriptive (bootstrap CI across units, no
$\alpha$ spent). The confirmatory pre-registration that follows this
campaign must restate this declaration before the first confirmatory unit
runs. **Negative-result margin — decided (ADR-0014 D1):** the
pre-registered inferiority margin is $1.5\times p_R$; "Momir is not
$\ge 1.5\times$ random search" is the strongest negative statement the
confirmatory fleet may issue.

## 6. What this campaign cannot establish

It cannot establish that the cost model is *right* — only that its inputs
are measured. It produces no evidence about Momir's quality, no admission
decisions, and no headline claim. All of its outputs are inputs to a later
confirmatory fleet, and none of them may be reported as a result.
