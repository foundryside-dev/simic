# Metrics — Simic             Last read: 2026-08-09 (session 11 checkpoint)

> Dates here are pacing signals for the owner's own use — this is a spare-time
> moonshot (owner-stated 2026-08-08, PDR-0005). A fired date is a re-plan signal
> for DECIDE, never a broken commitment — but it must still fire; silent drift
> defeats the point. Targets bound to future adjudications say so explicitly.

## North-star
| Metric | Target (falsifiable) | Current | Read on | Trend |
|--------|----------------------|---------|---------|-------|
| Generation beats controls: rate at which Momir pools contain admission-worthy canonical growth vs the random-search control on the MVP fixture (HLD §28.2) | ≥ K× the random-search rate over the first N adjudicated pools after Phase G; K and N fixed by the §22.11 cost model (simic-642c2c1823) before Phase A | N/A — pre-code | 2026-08-08 | — |

## Input metrics (the levers that move the north-star)
| Metric | Target | Current | Read on |
|--------|--------|---------|---------|
| Design-debt burn-down: open `hld-review` tracker items | 0 by 2026-08-31 | 37 open / 14 closed — **the session-9 pacing warning is ANSWERED (PDR-0021)**: owner chose to resume wave:1 and retain the date; the first closure since session 6 landed same session (simic-d6ea02f9a9 → ADR-0010, containment accountability). Five wave:1 items remain; 22 days needs ~1.8 closures per working day. PDR-0021 carries the re-plan trigger: burn-down not ≤ 33 at the 2026-08-16 reading fires a date re-plan by PDR | 2026-08-09 (session 11 checkpoint) |
| Phase progression: HLD §25 phases with acceptance tests (§21) passing | Phase A complete by 2026-09-30 (provisional — revise by PDR if the gate reshapes §9 materially) | 0 of 11 (pre-code) | 2026-08-08 |

## Guardrails (must NOT degrade)
| Metric | Floor / ceiling | Current | Read on |
|--------|-----------------|---------|---------|
| Academy exact-replay gate: identical snapshot + identical future data ⇒ bitwise-identical traces (HLD §18, invariant 5) | Floor: 100% pass, from Phase D onward | N/A — pre-code | 2026-08-08 |
| History completeness: candidate pools, failures, rejections, no-op wins and abstentions retained in Urborg (never winners-only) | Floor: 100% of cases | N/A — pre-code | 2026-08-08 |
| Harmful-intervention rate under admitted growth (HLD §28.6) | Ceiling: the tail-risk veto's declared operating point per assurance class — shape fixed by ADR-0004 (INV-45: veto precedes utility, non-tradeable, priced against snapshot distance); numbers land with the Phase-A adjudication-policy LLD | N/A — pre-code | 2026-08-08 (session 6: shape bound) |
