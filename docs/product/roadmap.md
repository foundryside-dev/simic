# Roadmap — Simic            Updated: 2026-10-08 (session 17; PDR-0043 — re-based on the bounded reboot)

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
> **Re-based 2026-10-08 (PDR-0043).** ADR-0018's bounded reboot is the one Now
> bet. It is the smallest experiment that can answer a criterion-18-shaped
> question with the code that already exists. The HLD programme is paused
> behind it, not cancelled: its resumption is gated on what the bounded screen
> shows.

## Now  (committed, in-flight)
- **Bounded structural comparison** (`experiments/bounded_comparison.py`,
  [guide](../bounded-comparison.md), ADR-0018). One host, the `conv_light`
  seed, three arms: no growth, static extra capacity from step zero, and a
  scheduled graft. Training and outer evaluation run as separate commands.
  - Why: esper-lite showed the technique works but could never measure it
    cleanly. This bet asks first whether a structural intervention earns its
    cost against *both* controls, before any controller exists.
  - State: implementation merged; CPU pilot read 2026-10-08 (PDR-0041). All
    three arms learn on CIFAR development data; one seed cannot separate them.
  - Next step: propose the multi-seed development screen with a budget
    (`simic-7486bc6929`).
  - Tracker: `simic-dda0d0188c`.
  - Metric: the bounded-comparison rows in `metrics.md`.
  - Kill / reopen: ADR-0018's trigger. If static capacity wins at the declared
    cost, or measurement noise prevents a credible comparison, reopen the
    design. Do not respond by enlarging the controller.

## Next (shaped, decreasing certainty)
- **Resume the HLD programme: design hardening, then Phase A.** Paused by
  ADR-0018, not dropped.
  - Design-debt burn-down: 31 open / 23 closed `hld-review` items, unchanged
    since 2026-08-10. Its 2026-09-30 date fired. PDR-0034 pre-committed that
    the date does not move a second time, so it is **un-dated** rather than
    re-dated (PDR-0043).
  - Phase A gate: when the bounded screen reports (tracker gate
    `simic-6f4f111ec8`; 35 paused items depend on it). If paired differences are
    resolvable at bounded scale, resume Phase A with the ~10 contract-blocking
    items named in the 2026-08-10 decision queue (`simic-0bf2c40dec` first).
    If they are not, the HLD's central instrument needs redesign before any
    contract is drafted.
  - Phase A also needs the Wardline trust gate re-wired once the tool returns
    (`simic-8db0b87ed6`, `simic-2035316005`).
- **Information-management regime (ADR-0002)** (`simic-357c92664c`): the
  plainweave seeding still wants the owner present. Rides with Phase A.

## Later (directional bets, no order, no dates)
- **Kernel demo campaign** (`experiments/kernel_demo.py`, spec rev 6.1/6.2) —
  **parked, not killed.**
  - The August preflight ran 60 fans and 12 refans, failed gates 1–5, and
    never froze.
  - ADR-0018 retained the code and campaign unchanged. The bounded comparison
    reuses its training primitives.
  - Resuming it needs its own DECIDE: the preflight failures first, then the
    Task 19B/19C items (`simic-e3ad55344f`, `simic-0fd4fcb933`) and the
    Phases A–F run (`simic-7c42fc9c0b`).
- **Learned structural timing** (random → heuristic → learned). Per ADR-0018
  this follows only if the bounded comparison shows the intervention earns its
  cost. The esper-lite "Tamiyo" ambition, telemetry-conditioned and
  cross-model, stays visible here and nowhere nearer.
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
