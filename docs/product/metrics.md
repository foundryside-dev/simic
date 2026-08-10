# Metrics — Simic             Last read: 2026-08-10 (session 15)

> Dates here are pacing signals for the owner's own use — this is a spare-time
> moonshot (owner-stated 2026-08-08, PDR-0005). A fired date is a re-plan signal
> for DECIDE, never a broken commitment — but it must still fire; silent drift
> defeats the point. Targets bound to future adjudications say so explicitly.

## North-star
| Metric | Target (falsifiable) | Current | Read on | Trend |
|--------|----------------------|---------|---------|-------|
| **The instrument resolves an intervention effect.** A deliberately strong hand-built intervention, measured against the matched no-op (INV-15/INV-16) from a common snapshot over a common future (INV-06), produces a difference distinguishable from branch-divergence noise at a declared horizon — and a deliberately null intervention does not (`docs/design/01-claim.md#28-success-criteria` criterion 18) | Pass/fail, both directions required. Horizon declared before the run (`programme/risks-and-open-decisions.md#275-qa-horizon-and-evidence-floor`). **If this fails, no other metric on this page means anything** — every measurement in the programme is a difference between paired branches | N/A — answerable at Phase D, before Momir exists | 2026-08-11 | — |

**North-star changed 2026-08-11 (PDR-0039, ADR-0016).** The previous north-star
was *"Generation beats controls: K = 1.5, N = 256 adjudicated pools = 32 base
trajectories × 8 pools"* (fixed 2026-08-09, ADR-0014/PDR-0026). Simic is now
positioned as an engineering programme rather than a confirmatory research
study, so that target is **mothballed with its costings intact** — a costed
option the owner may commission, not a gate. It moves to the optional-study
class below. Three repairs are prerequisites of re-commissioning it, not of
continuing: define the hit predicate once (`QualityReport` carries no threshold,
horizon selector or decision rule); recompute the operating-characteristics
table with per-K sd_d and name D1's alternative (the published table applies a
constant 0.292, which puts P(abandon | K=1.0) at 0.153 where the correct value
is 0.458, and 80% power needs n ≈ 73); and declare per-arm candidate counts with
arm-size matching. See ADR-0016.

## Input metrics (the levers that move the north-star)
| Metric | Target | Current | Read on |
|--------|--------|---------|---------|
| Design-debt burn-down: open `hld-review` tracker items | 0 by **2026-09-30** (moved from 2026-08-31, owner decision 2026-08-10 — **PDR-0034**, which pre-commits that the date is not moved a second time) | 31 open / 23 closed. The 2026-08-31 date fired and was re-planned: the kernel demo took the recent sessions, the owner accepted it displaced this bet, and the date moved a month. **Context for anyone reading this cold: the project is two days old** (started 2026-08-08) and this is a spare-time moonshot — 23 items closed in two days is the actual signal, and a displaced bet is a choice being made, not a slip. The date exists so the choice stays visible (PDR-0005), not as pressure. Note 2026-09-30 shares a month with the Phase-A target below | 2026-08-10 (session 15) |
| Phase progression: HLD §25 phases with acceptance tests (§21) passing | Phase A complete by 2026-09-30 (provisional — revise by PDR if the gate reshapes §9 materially) | 0 of 11. (No longer "pre-code" as of 2026-08-10: `experiments/kernel_demo.py` is on main — but the demo is deliberately outside the HLD phase ladder and closes no phase, PDR-0029) | 2026-08-10 (session 14) |
| Supervision cost per counterfactual arm (demo-scale proxy for the §28 cost model) | No target — **instrumented, not yet read.** The demo's own claim is fan supervision *economics* and until rev 6.2 the store carried no denominator | N/A — `wall_s` / `peak_mem_bytes` land with the first Phase-C collect (PDR-0036) | 2026-08-10 (session 15) |

## Optional studies (costed, commissionable, NOT gating — PDR-0039 / ADR-0016)

These are real questions with real prices. They are not on the critical path and
their absence is not a programme failure. Kept here so the costings are not lost
and re-commissioning is a decision, not a redesign.

| Study | Price | Entry conditions |
|--------|-------|------------------|
| **Generation beats controls** — rate at which Momir pools contain admission-worthy canonical growth vs the random-search control (`01-claim.md#28-success-criteria` criterion 2) | K = 1.5, N = 256 adjudicated pools = **32 base trajectories × 8 pools**; ~493 HER for the 8-cell fleet (`programme/cost-model.md`). Note n ≈ 73, not 32, if the declared *negative* is wanted at 80% power | The three ADR-0016 repairs: hit predicate defined once; operating-characteristics table recomputed with per-K sd_d and D1's alternative named; per-arm counts declared with arm-size matching |
| **Scaffold interaction matrix** — interpreting the fully withdrawn corner against single-axis and interaction controls (criterion 16) | two corners at n = 32, six interactions at n = 16, MDE 2.19× the random-arm rate | criterion 15 (independent withdrawal) passing as an acceptance gate first |
| **Anchor corpus** — dense per-step counterfactual labels for Aurelia (ADR-0011) | ~168 HER at 24 seeds / D_samp = 4 / A = 3 — the largest single line item, larger than the QA fleet | Aurelia being on the critical path at all, which under PDR-0039 it currently is not |

## Guardrails (must NOT degrade)
| Metric | Floor / ceiling | Current | Read on |
|--------|-----------------|---------|---------|
| Academy exact-replay gate: identical snapshot + identical future data ⇒ bitwise-identical traces (HLD §18, invariant 5) | Floor: 100% pass, from Phase D onward | N/A — the gate itself begins at Phase D. Note (2026-08-10): the kernel demo now implements a *rehearsal* of this machinery — Class-1 determinism knobs, zero-normalized state hashes, a bitwise twin arm that halts the fleet on divergence, and a null-seed arm that must reproduce the base exactly. It is evidence the mechanism is buildable, **not** a reading of this gate | 2026-08-10 (session 14) |
| History completeness: candidate pools, failures, rejections, no-op wins and abstentions retained in Urborg (never winners-only) | Floor: 100% of cases | N/A — pre-code | 2026-08-08 |
| Harmful-intervention rate under admitted growth (HLD §28.6) | Ceiling: the tail-risk veto's declared operating point per assurance class — shape fixed by ADR-0004 (INV-45: veto precedes utility, non-tradeable, priced against snapshot distance); numbers land with the Phase-A adjudication-policy LLD | N/A — pre-code. Note (2026-08-10): there is still **no evidence such an operating point is findable at all**. Registered exploratory study E1 against the demo store is the first attempt to price it — divergence predictability from pre-decision telemetry, with the foregone benefit at each operating point | 2026-08-10 (session 15) |
