# Metrics — Simic             Last read: 2026-08-10 (session 15)

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
| Design-debt burn-down: open `hld-review` tracker items | 0 by **2026-09-30** (moved from 2026-08-31, owner decision 2026-08-10 — **PDR-0034**, which pre-commits that the date is not moved a second time) | 31 open / 23 closed. The 2026-08-31 date fired and was re-planned: the kernel demo took the recent sessions, the owner accepted it displaced this bet, and the date moved a month. **Context for anyone reading this cold: the project is two days old** (started 2026-08-08) and this is a spare-time moonshot — 23 items closed in two days is the actual signal, and a displaced bet is a choice being made, not a slip. The date exists so the choice stays visible (PDR-0005), not as pressure. Note 2026-09-30 shares a month with the Phase-A target below | 2026-08-10 (session 15) |
| Phase progression: HLD §25 phases with acceptance tests (§21) passing | Phase A complete by 2026-09-30 (provisional — revise by PDR if the gate reshapes §9 materially) | 0 of 11. (No longer "pre-code" as of 2026-08-10: `experiments/kernel_demo.py` is on main — but the demo is deliberately outside the HLD phase ladder and closes no phase, PDR-0029) | 2026-08-10 (session 14) |
| Supervision cost per counterfactual arm (demo-scale proxy for the §28 cost model) | No target — **instrumented, not yet read.** The demo's own claim is fan supervision *economics* and until rev 6.2 the store carried no denominator | N/A — `wall_s` / `peak_mem_bytes` land with the first Phase-C collect (PDR-0036) | 2026-08-10 (session 15) |

## Guardrails (must NOT degrade)
| Metric | Floor / ceiling | Current | Read on |
|--------|-----------------|---------|---------|
| Academy exact-replay gate: identical snapshot + identical future data ⇒ bitwise-identical traces (HLD §18, invariant 5) | Floor: 100% pass, from Phase D onward | N/A — the gate itself begins at Phase D. Note (2026-08-10): the kernel demo now implements a *rehearsal* of this machinery — Class-1 determinism knobs, zero-normalized state hashes, a bitwise twin arm that halts the fleet on divergence, and a null-seed arm that must reproduce the base exactly. It is evidence the mechanism is buildable, **not** a reading of this gate | 2026-08-10 (session 14) |
| History completeness: candidate pools, failures, rejections, no-op wins and abstentions retained in Urborg (never winners-only) | Floor: 100% of cases | N/A — pre-code | 2026-08-08 |
| Harmful-intervention rate under admitted growth (HLD §28.6) | Ceiling: the tail-risk veto's declared operating point per assurance class — shape fixed by ADR-0004 (INV-45: veto precedes utility, non-tradeable, priced against snapshot distance); numbers land with the Phase-A adjudication-policy LLD | N/A — pre-code. Note (2026-08-10): there is still **no evidence such an operating point is findable at all**. Registered exploratory study E1 against the demo store is the first attempt to price it — divergence predictability from pre-decision telemetry, with the foregone benefit at each operating point | 2026-08-10 (session 15) |
