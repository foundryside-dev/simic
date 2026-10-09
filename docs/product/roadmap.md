# Roadmap — Simic            Updated: 2026-10-09 (session 17; rung 4 met; PDR-0057 proposed)

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
- **The bounded experiment ladder** (PDR-0050; ADR-0018). This is the
  sequencing authority for experimental work. Each rung is one
  pre-registered, reviewed experiment with a stop condition.
  - Rung 1, the instrument resolves: **met** (PDR-0045).
  - Rung 2, a repairable deficit: **detected; a benefit ≥ the 0.10 floor not
    established** (estimate 0.119, 95% interval 0.088–0.151; conditional on 47
    finite pairs).
  - Rung 3, does a graft capture the deficit: **met as a partial capture**
    (PDR-0052, 2026-10-09). The graft repairs 60% [51, 72] of static's gain
    with `norm` and 31% [19, 42] with `conv_heavy`. Static wins at the
    declared cost. Lifecycle v2 was stable (0/192).
  - Tracker: `simic-f73351380d`.
  - Kill / reopen: each rung's stop condition. Per ADR-0018, do not respond
    to a failed rung by enlarging the controller.

## Next (shaped, decreasing certainty)
- **Rung 4 (met 2026-10-09, `lever_found`, PDR-0055;
  [result](../results/2026-10-09-rung4-timing-horizon.md)): did graft
  timing or horizon change the outcome, on `under_normalized` × `norm`?**
  Yes. Earlier grafts were better, and a longer horizon let the graft catch
  static on the median seed. Six cells ran: graft epochs 0, 1, 2, 3 and 5
  at 10 epochs, and graft epoch 2 at 20 epochs. What follows is a new owner
  DECIDE. Location stayed out of scope.
- **Proposed, not adopted: the controller training pathway** (PDR-0057,
  gates G0–G5, awaiting John's D1–D9). If adopted, it replaces the rung-5
  line below with G2 + G3, and adds rungs 6 (closed loop) and 7 (transfer).
  G0 apparatus work, which makes no claim, has started.
- **Rung 5: can telemetry predict the label better than a fixed schedule?**
  This is the first Tamiyo-shaped result. HLD contracts are drafted here,
  only for what it touches.

## Later (directional bets, no order, no dates)
- **HLD programme: design hardening and Phase A contracts** (moved to Later
  by PDR-0050). Pulled by rung 5, never pushed ahead of it. The ~30 items
  are parked behind the rung-5 gate `simic-e0bafbe10f`.
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
