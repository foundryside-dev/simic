# Roadmap — Simic            Updated: 2026-08-08 (PDR-0001)

> Sequencing, WSJF / cost-of-delay, and dated forecasts are produced by
> /axiom-program-management. This file records bets as INTENT, not a delivery
> schedule. Do not compute WSJF here; hand the committed bet over for sequencing.

## Now  (committed, in-flight)
- **Design hardening — reconcile HLD v4.1 with the 2026-08-08 Esper-pivot peer
  review** — why: 43 open `hld-review` items, including a decision gate at the top
  of the critical path; starting Phase A on an unstable contract surface would
  churn every downstream package · tracker: simic-0dd5362f05 (decision gate),
  simic-aff80b1843 + simic-e84fe6737c (in progress) · metric: design-debt
  burn-down (metrics.md)

## Next (shaped, decreasing certainty)
- **Phase A — Namespec, Leyline contracts, dependency boundaries** (HLD §25.A;
  §30 milestones 1–3) — ADR locking Namespec 1.0, package skeleton with
  forbidden-import checks, core contracts, lifecycle/warrant rules, budgets,
  import-lint and authority tests. (not yet sequenced)
- **Phase B — Tolaria host-training baseline and Academy profile** (HLD §25.B) —
  ordinary host execution behind one deterministic engine; Academy-exact runtime
  profile; deterministic mainline traces. (not yet sequenced)

## Later (directional bets, no order, no dates)
- **Phases C–K toward the §24 Minimum Viable System** — growth mechanics, replay
  and branching, Urabrask QA, Augustin adjudication and controls, Sarpadia/Momir
  bootstrap curriculum, Nissa/Narset routing, Emrakul maintenance, Tamiyo
  allocation, Oona and scale.
- **Esper-derived controls** — the working blueprint selector and the
  degenerate-architecture fixtures (~10%→~40% headroom) as sharp, cheap baselines
  for the generation hypothesis · tracker: simic-1d3aa47ff1 (per the 2026-08-08
  peer review; shape depends on the simic-0dd5362f05 adjudication).
- **Project-level rename decision** (HLD §27.1) — on the map; outward-facing when
  it lands, therefore owner-gated.
