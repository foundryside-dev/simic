# Roadmap — Simic            Updated: 2026-08-08 (PDR-0007, PDR-0008, PDR-0009)

> Sequencing, WSJF / cost-of-delay, and dated forecasts are produced by
> /axiom-program-management. This file records bets as INTENT, not a delivery
> schedule. Do not compute WSJF here; hand the committed bet over for sequencing.

## Now  (committed, in-flight)
- **Design hardening — reconcile HLD v4.1 with the 2026-08-08 Esper-pivot peer
  review** — why: starting Phase A on an unstable contract surface would churn
  every downstream package. The decision gate is adjudicated and closed
  (PDR-0007); the HLD is decomposed into docs/design/ chapters (PDR-0009,
  ADR-0001); remaining work runs as six region-based waves stamped as
  `wave:*` labels (PDR-0008) · tracker: critical path simic-ae3caf44f1 →
  simic-ed2698fafd; wave:0 remnants simic-aff80b1843, simic-e84fe6737c,
  simic-a708c5b1b7 · metric: design-debt burn-down (metrics.md)

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
  for the generation hypothesis · adjudicated at the gate (PDR-0007): accepted
  as a permanent blinded control; the spec task simic-1d3aa47ff1 is wave:2 work
  inside the Now bet, the running control itself lands with the QA-pool phases.
- **Project-level rename decision** (HLD §27.1) — on the map; outward-facing when
  it lands, therefore owner-gated.
