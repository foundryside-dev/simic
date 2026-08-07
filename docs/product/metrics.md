# Metrics — Simic             Last read: 2026-08-08

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
| Design-debt burn-down: open `hld-review` tracker items | 0 by 2026-08-31 | 41 (2 in progress, 34 ready, 5 blocked — post-gate: 27 blocked collapsed to 5, all behind real edit/logic dependencies; net −2 despite two items added in-session) | 2026-08-08 (post-gate) |
| Phase progression: HLD §25 phases with acceptance tests (§21) passing | Phase A complete by 2026-09-30 (provisional — revise by PDR if the gate reshapes §9 materially) | 0 of 11 (pre-code) | 2026-08-08 |

## Guardrails (must NOT degrade)
| Metric | Floor / ceiling | Current | Read on |
|--------|-----------------|---------|---------|
| Academy exact-replay gate: identical snapshot + identical future data ⇒ bitwise-identical traces (HLD §18, invariant 5) | Floor: 100% pass, from Phase D onward | N/A — pre-code | 2026-08-08 |
| History completeness: candidate pools, failures, rejections, no-op wins and abstentions retained in Sarpadia (never winners-only) | Floor: 100% of cases | N/A — pre-code | 2026-08-08 |
| Harmful-intervention rate under admitted growth (HLD §28.6) | Ceiling: the tail-risk veto's operating point, set by the simic-ae3caf44f1 (lexicographic admission) adjudication — deliberately unnumbered until then | N/A — pre-code | 2026-08-08 |
