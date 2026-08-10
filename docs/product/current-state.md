# Current State — Simic        Checkpoint: 2026-08-10 (session 14)

## The bet right now
Three Now bets, and the balance between them is the live question.
(1) **Kernel demo** — implementation **done and merged** (PDR-0033, PR #9,
merge 2b48431): `experiments/kernel_demo.py` on main, 113 tests, three
review waves closed. The bet is not finished — its whole point is the
**run**: certify → freeze → collect → train → one-shot eval → report
(simic-7c42fc9c0b). Pre-registration of record is spec **rev 6.1**
(PDR-0032). (2) **Design hardening** — burn-down **31 open, third
straight session with zero closures; the 2026-08-31 target has now
fired** (metrics.md). Next band would be wave:2-momir (head
simic-0e6445d894). (3) **ADR-0002 regime** (simic-357c92664c) still
unstarted; plainweave seeding wants the owner present.

## In flight
- simic-7c42fc9c0b — kernel demo Operational Phases A–F. **A** (GPU
  `selftest --certify` + wardline scan) is runnable now and unattended;
  **B** (freeze — constants sign-off) and **E** (one-shot eval, literally
  unrepeatable) need the owner; **C** is the 13–20h collect.
- simic-8db0b87ed6 — trust-tier enforcement wiring (ADR-0015). Now carries
  a hard empirical input: **wardline's taint gate is inert repo-wide** (0
  declared trust boundaries), so a green wardline run is currently vacuous.
- simic-b67434134e: cryptography bump still blocked upstream (PDR-0023).
- Publish queue: **cleared**. Merging PR #9 (owner-directed, including
  "fold the latest commits on main into your branch first") pushed the
  22-commit local-main backlog to the public repo along with the demo.

## Open questions / blocked-on-owner
- **The burn-down date has fired.** Not pressure — a re-plan trigger
  (PDR-0005 posture). Three options for DECIDE: move 2026-08-31, shrink
  to a blocking subset, or accept explicitly that the demo displaced it.
  This is the first thing the next session should put in front of the owner.
- **Sequencing after the demo merge:** Phase A of the demo run vs opening
  wave:2-momir. They compete for the same spare-time slot.
- **Wardline inert repo-wide** — ADR-0015's mechanical enforcement rests on
  a gate that currently checks nothing. Declare Tier-3 boundaries, or
  accept the doctrine stays advisory until then?
- Carried: yzmir-training-state prompt relay vs fresh re-commissioning
  (PDR-0012 reversal path); wiki replatform (PDR-0028) approved but
  untracked.

## Last checkpoint did
- **PDR-0032** — spec rev 6.1, owner-approved pre-data amendment: the
  money-chart permutation null and falsifier CI move from grid-point to
  **episode** level (the grid clusters 2 fans per episode; the old null
  under-dispersed by up to 2× and could have passed or failed the demo on
  miscalibration). Free now, impossible after Phase E.
- **PDR-0033** — implementation accepted against its criteria and merged:
  18 tasks, then a 35-agent review workflow (10 findings), a generalist
  fix pass (8 more — including a gate that was statistically unpassable),
  and four SME role reviews (~26). All mechanical findings fixed.
- Tracker: simic-4a44ed57c9 closed; simic-7c42fc9c0b (the run) created;
  wardline-inert finding recorded on simic-8db0b87ed6. Worktree, branches
  and the SDD workspace cleaned up.
- Metrics: burn-down 31/23 — **fired**; Phase progression still 0 of 11
  (the demo closes no HLD phase, by design).

## Next session, start here
Put the fired burn-down date to the owner as a re-plan choice — that
decision sets the session's shape. If the owner is present and wants the
demo to keep moving, Phase A (`selftest --certify` on the GPU box +
wardline scan) is the cheapest next step and needs no supervision.
