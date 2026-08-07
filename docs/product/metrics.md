# Metrics — Simic             Last read: 2026-08-08

> Targets marked TBD are placeholders for the owner to set real numbers/dates
> against. A target with no number and no date is not falsifiable and cannot fire
> an acceptance verdict or a PDR reversal trigger.

## North-star
| Metric | Target (falsifiable) | Current | Read on | Trend |
|--------|----------------------|---------|---------|-------|
| Generation beats controls: rate at which Momir pools contain admission-worthy canonical growth vs the random-search control on the MVP fixture (HLD §28.2) | ≥ TARGET× the random-search rate by TBD (measurable from Phase F/G; BASELINE = measured random-search hit rate) | N/A — pre-code | 2026-08-08 | — |

## Input metrics (the levers that move the north-star)
| Metric | Target | Current | Read on |
|--------|--------|---------|---------|
| Design-debt burn-down: open `hld-review` tracker items | 0 by TBD | 43 (2 in progress, 14 ready, 27 blocked; the 44-label total includes 1 closed item, and the ready count excludes the unlabeled `Future` release simic-78039ae681) | 2026-08-08 |
| Phase progression: HLD §25 phases with acceptance tests (§21) passing | Phase A complete by TBD | 0 of 11 (pre-code) | 2026-08-08 |

## Guardrails (must NOT degrade)
| Metric | Floor / ceiling | Current | Read on |
|--------|-----------------|---------|---------|
| Academy exact-replay gate: identical snapshot + identical future data ⇒ bitwise-identical traces (HLD §18, invariant 5) | Floor: 100% pass, from Phase D onward | N/A — pre-code | 2026-08-08 |
| History completeness: candidate pools, failures, rejections, no-op wins and abstentions retained in Sarpadia (never winners-only) | Floor: 100% of cases | N/A — pre-code | 2026-08-08 |
| Harmful-intervention rate under admitted growth (HLD §28.6) | Ceiling: TBD | N/A — pre-code | 2026-08-08 |
