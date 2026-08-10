# Roadmap — Simic            Updated: 2026-08-10 (session 14; PDR-0033 — kernel demo implementation accepted and merged, bet continues as the run)

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
  metric: design-debt burn-down (metrics.md). The three-tier trust model
  is now adopted doctrine (ADR-0015, PDR-0030) — wave:4-leyline contract
  shapes record a tier per record class; enforcement wiring is
  simic-8db0b87ed6 (Phase A)
- **Kernel demo — the proof of concept** ("Simic in 20 minutes",
  `experiments/kernel_demo.py`) — why: the pointable answer to "how do you
  know it works" (PDR-0029: maths proved, risk is engineering). Moved to
  Now by PDR-0031. **Implementation is done and merged** (PDR-0033, PR #9);
  the bet now stands on the RUN — certify, freeze, collect, train, the
  one-shot eval, report. Pre-registration of record is spec rev 6.1
  (PDR-0032, pre-data amendment) · tracker: simic-4a44ed57c9 (closed) →
  simic-7c42fc9c0b (Phases A–F; B and E need the owner present) · metric:
  none of its own — never citable as §28 evidence; guarded by the
  burn-down staying on pace (PDR-0031/0033 reversal triggers)
- **Information-management regime (ADR-0002)** — why: data management was the
  owner-named second esper bugbear (definition drift, no sign-or-lock,
  lost lineage, silent mutation); Phase A binds code to contracts, so the
  lock machinery must exist first. Named-definition lifecycle in plainweave,
  runtime data policy P1–P7; runs alongside the waves, does not displace the
  critical path (PDR-0010) · tracker: simic-357c92664c · metric: none of its
  own — guarded by the design-debt burn-down staying on pace

## Next (shaped, decreasing certainty)
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
