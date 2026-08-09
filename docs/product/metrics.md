# Metrics — Simic             Last read: 2026-08-10 (session 13)

> Dates here are pacing signals for the owner's own use — this is a spare-time
> moonshot (owner-stated 2026-08-08, PDR-0005). A fired date is a re-plan signal
> for DECIDE, never a broken commitment — but it must still fire; silent drift
> defeats the point. Targets bound to future adjudications say so explicitly.

## North-star
| Metric | Target (falsifiable) | Current | Read on | Trend |
|--------|----------------------|---------|---------|-------|
| Generation beats controls: rate at which Momir pools contain admission-worthy canonical growth vs the random-search control on the MVP fixture (HLD §28.2) | **K = 1.5, N = 256 adjudicated pools = 32 base trajectories × 8 pools** (fixed 2026-08-09 by the worked cost model, ADR-0014/PDR-0026; provisional until campaign 1 measures p_R and ρ — `docs/design/programme/prereg-cost-model-campaign-1.md`). Rate clause is the single primary endpoint; online-cost clause descriptive (D2). Pre-registered negative margin: "not ≥ 1.5× random" at 80% power (D1) | N/A — pre-code | 2026-08-09 | — |

## Input metrics (the levers that move the north-star)
| Metric | Target | Current | Read on |
|--------|--------|---------|---------|
| Design-debt burn-down: open `hld-review` tracker items | 0 by 2026-08-31 | 31 open / 23 closed — **no closures since session 12**; sessions 12b–13 went to the kernel demo (spec lock, plan, execution start) and ADR-0015. Pace needed has steepened to ≈ 2.1 closures per working day (~15 working days left). Not yet fired, but a second no-closure session puts 2026-08-31 out of reach at spare-time cadence — re-plan signal per the header note | 2026-08-10 (session 13) |
| Phase progression: HLD §25 phases with acceptance tests (§21) passing | Phase A complete by 2026-09-30 (provisional — revise by PDR if the gate reshapes §9 materially) | 0 of 11 (pre-code) | 2026-08-08 |

## Guardrails (must NOT degrade)
| Metric | Floor / ceiling | Current | Read on |
|--------|-----------------|---------|---------|
| Academy exact-replay gate: identical snapshot + identical future data ⇒ bitwise-identical traces (HLD §18, invariant 5) | Floor: 100% pass, from Phase D onward | N/A — pre-code | 2026-08-08 |
| History completeness: candidate pools, failures, rejections, no-op wins and abstentions retained in Urborg (never winners-only) | Floor: 100% of cases | N/A — pre-code | 2026-08-08 |
| Harmful-intervention rate under admitted growth (HLD §28.6) | Ceiling: the tail-risk veto's declared operating point per assurance class — shape fixed by ADR-0004 (INV-45: veto precedes utility, non-tradeable, priced against snapshot distance); numbers land with the Phase-A adjudication-policy LLD | N/A — pre-code | 2026-08-08 (session 6: shape bound) |
