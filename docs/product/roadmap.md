# Roadmap — Simic            Updated: 2026-10-08 (session 17; PDR-0045 — screen read, gate closed)

> Sequencing, WSJF / cost-of-delay, and dated forecasts are produced by
> /axiom-program-management. This file records bets as INTENT, not a delivery
> schedule. Do not compute WSJF here; hand the committed bet over for sequencing.

> **Framing (PDR-0039, 2026-08-11).** Simic is an engineering programme, not a
> confirmatory research study. Bets are judged against the *acceptance* class of
> `docs/design/01-claim.md#28-success-criteria`, headed by criterion 18: does
> the paired-branch difference resolve an intervention effect above
> branch-divergence noise? The confirmatory apparatus is mothballed with its
> costings intact (ADR-0016).
>
> **Re-based 2026-10-08 (PDR-0043), then the gate closed (PDR-0045).** The
> bounded screen showed that the paired instrument resolves: the no-op
> contrast is bounded to ±0.018 nats at n = 48. The scheduled graft earned
> nothing measurable at that scale, and static capacity didn't either. So the
> HLD programme resumes, and the bounded experiment reopens around a host with
> a real deficit.

## Now  (committed, in-flight)
- **Bounded comparison, round 2: find a measured, repairable deficit**
  (`simic-f73351380d`, ADR-0018, PDR-0045).
  - Why: screen v1 found no growth effect in *either* added-capacity arm, so
    the experiment had nothing to repair. Before asking whether a graft
    repairs a deficit, establish one.
  - Next step: pre-register a configuration in which static capacity beats
    no growth beyond δ (the positive control). Candidates are Esper's
    degenerate-architecture fixtures (~10%→~40% headroom) and an
    under-provisioned `mild` host. Then the graft question, frozen as
    PDR-0044 was.
  - Reuses `experiments/bounded_comparison.py` and
    `experiments/bounded_screen.py`. About 5 CPU-hours per 48-unit screen.
  - Metric: the bounded-comparison rows in `metrics.md`.
  - Kill / reopen: ADR-0018. Do not respond by enlarging the controller. If no
    configuration within bounded scale shows a positive control, record that
    as a result and stop the bounded line.
- **HLD programme resumed: design hardening into Phase A** (PDR-0043/0045).
  - Why: the counterfactual instrument has now been shown to resolve at
    bounded scale, which is the gate PDR-0043 set.
  - Start with the ~10 contract-blocking items, led by `simic-0bf2c40dec`
    (§9 contract shapes).
  - Design-debt burn-down: 31 open / 23 closed `hld-review` items. Live
    again, and un-dated (PDR-0043): paced by session, not calendar.
  - Phase A also needs the Wardline trust gate re-wired once the tool returns
    (`simic-8db0b87ed6`, `simic-2035316005`).
  - Caveat (PDR-0045): "resolves" is a property of the bounded instrument. It
    has to be re-earned under Tolaria (INV-06, INV-15/16).

## Next (shaped, decreasing certainty)
- **Information-management regime (ADR-0002)** (`simic-357c92664c`): the
  plainweave seeding still wants the owner present, and the Legis drift gate
  needs a replacement mechanism (PDR-0042). Rides with Phase A.
- **Learned structural timing** (random → heuristic → learned): only after the
  round-2 bounded experiment shows a graft that earns its cost.

## Later (directional bets, no order, no dates)
- **Kernel demo campaign** (`experiments/kernel_demo.py`, spec rev 6.1/6.2) —
  **parked, not killed.**
  - The August preflight ran 60 fans and 12 refans, failed gates 1–5, and
    never froze.
  - ADR-0018 retained the code and campaign unchanged. The bounded comparison
    reuses its training primitives.
  - Its tracker items depend on the parking issue `simic-ae339f0555`.
  - Resuming it needs its own DECIDE: the preflight failures first, then the
    Task 19B/19C items (`simic-e3ad55344f`, `simic-0fd4fcb933`) and the
    Phases A–F run (`simic-7c42fc9c0b`).
- **Phases C–K toward the §24 Minimum Viable System**: growth mechanics, replay
  and branching, Jin-Gitaxias QA, Isperia adjudication and controls,
  Urborg/Momir bootstrap curriculum, Nissa/Aurelia routing, Emrakul
  maintenance, Ugin allocation, Tamiyo and scale.
- **Esper-derived controls**: the working blueprint selector and the
  degenerate-architecture fixtures (~10%→~40% headroom) as sharp, cheap
  baselines for the generation hypothesis. Adjudicated as a permanent blinded
  control (PDR-0007); the spec task is `simic-1d3aa47ff1`.
- **Project-level rename decision** (HLD §27.1) — **decided** (ADR-0003,
  owner commit b42250c): Simic through publication, predecessors behind a
  clean seam. Off the map; only an external naming constraint at the
  publication gate reopens it.
