# Roadmap — Simic            Updated: 2026-08-09 (session 12; PDR-0029 — kernel demo enters Next as the proof-of-concept bet)

> Sequencing, WSJF / cost-of-delay, and dated forecasts are produced by
> /axiom-program-management. This file records bets as INTENT, not a delivery
> schedule. Do not compute WSJF here; hand the committed bet over for sequencing.

## Now  (committed, in-flight)
- **Design hardening — reconcile HLD v4.1 with the 2026-08-08 Esper-pivot peer
  review** — why: starting Phase A on an unstable contract surface would churn
  every downstream package. The decision gate is adjudicated and closed
  (PDR-0007); the HLD is decomposed into docs/design/ chapters (PDR-0009,
  ADR-0001); remaining work runs as six region-based waves stamped as
  `wave:*` labels (PDR-0008) · tracker: wave:0 cleared and the wave:1
  Isperia pair landed (ADR-0004, ADR-0005); dependency-critical path now
  simic-0bf2c40dec → simic-38a07fad39, six wave:1 items remain ·
  metric: design-debt burn-down (metrics.md)
- **Information-management regime (ADR-0002)** — why: data management was the
  owner-named second esper bugbear (definition drift, no sign-or-lock,
  lost lineage, silent mutation); Phase A binds code to contracts, so the
  lock machinery must exist first. Named-definition lifecycle in plainweave,
  runtime data policy P1–P7; runs alongside the waves, does not displace the
  critical path (PDR-0010) · tracker: simic-357c92664c · metric: none of its
  own — guarded by the design-debt burn-down staying on pace

## Next (shaped, decreasing certainty)
- **Kernel demo — the proof of concept** ("Simic in 20 minutes",
  `experiments/kernel_demo.py`) — why: the pointable answer to "how do you
  know it works"; owner position (PDR-0029): the maths is proved, the risk
  is engineering, so a runnable substrate-loop demo is the cheapest
  credibility instrument while the fleet is far off. Spec locked rev 6
  with implementation GO (2026-08-09, commit 98083fd); never citable as
  §28 evidence — the pre-registered fleet (ADR-0014) owns the claim.
  (not yet sequenced)
- **Phase A — Namespec, Leyline contracts, dependency boundaries** (HLD §25.A;
  §30 milestones 1–3) — namespec ADR (Namespec 2.0 — done, ADR-0008), package skeleton with
  forbidden-import checks, core contracts, lifecycle/warrant rules, budgets,
  import-lint and authority tests. (not yet sequenced)
- **Phase B — Tolaria host-training baseline and Academy profile** (HLD §25.B) —
  ordinary host execution behind one deterministic engine; Academy-exact runtime
  profile; deterministic mainline traces. (not yet sequenced)

## Later (directional bets, no order, no dates)
- **Phases C–K toward the §24 Minimum Viable System** — growth mechanics, replay
  and branching, Jin-Gitaxias QA, Isperia adjudication and controls, Urborg/Momir
  bootstrap curriculum, Nissa/Aurelia routing, Emrakul maintenance, Ugin
  allocation, Tamiyo and scale.
- **Esper-derived controls** — the working blueprint selector and the
  degenerate-architecture fixtures (~10%→~40% headroom) as sharp, cheap baselines
  for the generation hypothesis · adjudicated at the gate (PDR-0007): accepted
  as a permanent blinded control; the spec task simic-1d3aa47ff1 is wave:2 work
  inside the Now bet, the running control itself lands with the QA-pool phases.
- **Project-level rename decision** (HLD §27.1) — **decided** (ADR-0003,
  owner commit b42250c): Simic through publication, predecessors behind a
  clean seam. Off the map; only an external naming constraint at the
  publication gate reopens it.
