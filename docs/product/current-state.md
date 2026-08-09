# Current State — Simic        Checkpoint: 2026-08-10 (session 13)

## The bet right now
Three Now bets. (1) **Kernel demo implementation** — moved to Now by
PDR-0031: plan rev 3.3 panel-green, owner-granted full execution
autonomy, subagent-driven; tracker simic-4a44ed57c9 (in_progress,
claude-main). Build underway on branch `kernel-demo` (worktree
`.claude/worktrees/kernel-demo`): tasks 1–4 of 18 done; authoritative
resume point is the SDD ledger
`.superpowers/sdd/2026-08-09-kernel-demo/progress.md` in that worktree.
Nothing on main yet (`experiments/` not created there). (2) **Design
hardening** — hld-review burn-down **stalled at 31 open**, zero closures
across sessions 12b–13; pace to 2026-08-31 has steepened to ≈2.1/working
day — one more no-closure session is the re-plan signal. Next band:
wave:2-momir (8 items, head simic-0e6445d894). (3) **ADR-0002 regime**
(simic-357c92664c) still unstarted; plainweave seeding gate wants owner
presence.

## In flight
- simic-4a44ed57c9 — kernel demo build per locked spec rev 6; stop-points
  only BLOCKED/load-bearing and GPU-checkpoint phases (owner grant,
  2026-08-10; memory: kernel-demo-full-autonomy).
- **New this session:** ADR-0015 (three-tier trust model, elspeth
  lineage) adopted as doctrine — owner-directed, doctrine-only;
  mechanical enforcement rides the in-progress **wardline trust-model
  enhancement** (upstream Weft work, not tracked here). Phase A
  enforcement wiring: simic-8db0b87ed6. Wave:4-leyline contract shapes
  now record a tier per record class (ADR-0015 consequence).
- **Publish queue (owner-gated): 22 unpublished commits** on local main
  (design wiki, kernel demo spec+plan, cost model, ADR-0015, checkpoints).
  Publish = PR branch + merge, never direct push.
- simic-b67434134e: cryptography bump still blocked upstream (PDR-0023).

## Open questions / blocked-on-owner
- **Publish the queue?** 22 commits local-only and growing.
- Burn-down: if session 14 also closes nothing, the 2026-08-31 target
  fires — bring to DECIDE (re-plan, not pressure; PDR-0005 posture).
- Carried: yzmir-training-state prompt relay vs fresh re-commissioning
  (PDR-0012 reversal path) — owner call.
- Wiki replatform (PDR-0028): approved design, still untracked as work;
  enter into filigree when the owner wants it scheduled.

## Last checkpoint did
- PDR-0030: three-tier trust model adopted (ADR-0015, commit 5b66b97);
  enforcement deferred to wardline enhancement; Phase A wiring task
  simic-8db0b87ed6 filed; ruff posture recorded in ADR consequences.
- PDR-0031: kernel demo horizon reconciled Next → Now (owner-authorized
  execution in parallel session); roadmap updated.
- Metrics: burn-down read 31/23 (stalled), pace steepened to ≈2.1/day.

## Next session, start here
Check simic-4a44ed57c9 progress first (subagent-driven build may have
advanced in parallel). Then either claim simic-0e6445d894 to open
wave:2-momir — the burn-down needs closures this week — or run the
plainweave seeding gate (simic-357c92664c) with the owner present;
ADR-0015 just added tier assignments worth locking alongside ADR-0014's
definitions.
