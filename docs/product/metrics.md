# Metrics — Simic             Last read: 2026-08-09 (session 11, second checkpoint)

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
| Design-debt burn-down: open `hld-review` tracker items | 0 by 2026-08-31 | 32 open / 22 closed — **wave:1 COMPLETE** (zero `wave:1-augustin` items). Session 11 closed nine: six wave:1 (ADR-0010 containment, re-adjudication, veto signal, learnability boundary, tenancy tiers, ω/κ reconciliation) plus three owner-originated same-day open-and-close (anchor corpus ADR-0011, posture ADR-0012, stack identity ADR-0013 — net zero each). PDR-0021's re-plan trigger (≤ 33 by 2026-08-16) satisfied a week early. Remaining: wave:2-momir 8, wave:3-narset 7, wave:4-leyline 10, wave:5-scoreboard 4, unwaved 3; 22 days needs ~1.5 closures per working day | 2026-08-09 (session 11, second checkpoint) |
| Phase progression: HLD §25 phases with acceptance tests (§21) passing | Phase A complete by 2026-09-30 (provisional — revise by PDR if the gate reshapes §9 materially) | 0 of 11 (pre-code) | 2026-08-08 |

## Guardrails (must NOT degrade)
| Metric | Floor / ceiling | Current | Read on |
|--------|-----------------|---------|---------|
| Academy exact-replay gate: identical snapshot + identical future data ⇒ bitwise-identical traces (HLD §18, invariant 5) | Floor: 100% pass, from Phase D onward | N/A — pre-code | 2026-08-08 |
| History completeness: candidate pools, failures, rejections, no-op wins and abstentions retained in Urborg (never winners-only) | Floor: 100% of cases | N/A — pre-code | 2026-08-08 |
| Harmful-intervention rate under admitted growth (HLD §28.6) | Ceiling: the tail-risk veto's declared operating point per assurance class — shape fixed by ADR-0004 (INV-45: veto precedes utility, non-tradeable, priced against snapshot distance); numbers land with the Phase-A adjudication-policy LLD | N/A — pre-code | 2026-08-08 (session 6: shape bound) |
