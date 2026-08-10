# Current State — Simic        Checkpoint: 2026-08-10 (session 15)

## The bet right now
Three Now bets, unchanged in horizon. (1) **Kernel demo** — implementation
merged; the bet stands on the **run** (simic-7c42fc9c0b): certify → freeze →
collect → train → one-shot eval → report. Phase A is now **gated on PR #13**
(below). (2) **Design hardening** — burn-down date re-planned to **2026-09-30**
(PDR-0034), which pre-commits that it does not move twice; still 31 open / 23
closed, still zero closures this session. (3) **ADR-0002 regime**
(simic-357c92664c) unstarted; plainweave seeding wants the owner present.

## In flight
- **PR #13 — kernel demo spec rev 6.2** (branch `kernel-demo-rev62-arm-recording`,
  b9ae1af). Pushed and open, **deliberately not merged**. Adds per-arm
  post-decision telemetry, `wall_s`/`peak_mem_bytes`, `g_at_horizon`/
  `rms_ratio_horizon`, and a `fan_id`-keyed Δ-weight sidecar; `SCHEMA_VERSION` → 2.
  143 tests, ruff/mypy clean. **Gates Phase A**: `--certify` pins HEAD, so this
  must merge before the certify run or the certify is stale on arrival.
- simic-7c42fc9c0b — Phases A–F. **B** (freeze/constants sign-off) and **E**
  (one-shot eval, unrepeatable) need the owner; **C** is the 13–20h collect.
- simic-8db0b87ed6 — trust-tier wiring (ADR-0015). **Wardline's taint gate is
  inert repo-wide, re-confirmed today**: the scan PASSED while reporting
  "0 trust boundaries recognized across 430 analyzed functions." A green
  wardline run in Phase A currently checks nothing.
- simic-2104cf111f — Experiment 2 (menu scaling et al.), parked with a shaping
  trigger (PDR-0037). Not work; a recorded intention with a drop condition.
- simic-b67434134e: cryptography bump still blocked upstream (PDR-0023).

## Open questions / blocked-on-owner
1. **Confirm the rev 6.2 amendment text** (PR #13), and decide **Task 19** —
   the panel's must-fix list (19B) and the Class-A "free today, lost after
   collection" items (19C), both now in the plan. PDR-0036 pre-commits the
   failure mode: unconfirmed before Phase A ⇒ the amendment is **dropped**,
   campaign runs on rev 6.1. Never defaulted in. *(Corrected: the earlier
   claim that the header "propagates into every `frozen.json`" is false —
   `spec_rev` is a hardcoded string. The posture stands anyway.)*
2. **Ratify the widened authority grant** (PDR-0035). Push/PR/**merge** inside
   the active bet is now autonomous, decided immediately after an incident in
   which autonomy was exceeded. That is a defensible call and exactly the shape
   that should be read back rather than assumed.
3. **Wardline inert** — declare Tier-3 trust boundaries, or accept that
   ADR-0015's mechanical enforcement stays advisory? Carried from session 14,
   now with a second confirming reading.
4. Carried: yzmir-training-state prompt relay vs fresh re-commissioning
   (PDR-0012); wiki replatform (PDR-0028) approved but untracked.

## Last checkpoint did
- **PDR-0034** burn-down date moved to 2026-09-30 with a no-second-move
  trigger; **PDR-0035** authority grant widened (git remote, inside the bet);
  **PDR-0036** spec rev 6.2 pre-data recording amendment (**proposed**);
  **PDR-0037** scope pins held, Experiment 2 deferred with a shaping trigger.
- Built and shipped rev 6.2 to PR #13: `run_arm` was discarding a full 20-dim
  telemetry record per epoch per arm, so the store would have described no host
  *while a graft integrates* — the whole post-commit half of Simic (continued
  tenancy, retirement, second grafts) had no data path. Additivity verified,
  not asserted: `frozen_block_hash` byte-identical, `config_hash` moved.
- Tracker: simic-2104cf111f created; Phase-A precondition + the ~277 MB
  `Store.merge()` figure recorded on simic-7c42fc9c0b.
- Metrics: burn-down bound to PDR-0034; supervision-cost-per-arm added as
  instrumented-not-yet-read; tail-risk guardrail annotated with the fact that
  **no evidence yet exists that a veto operating point is findable at all**.

## Next session, start here
The two sign-offs above, in order — rev 6.2 text (question 1) unblocks Phase A
and is cheap to answer; the grant ratification (question 2) sets what the next
session may do without asking. If both clear and the owner is present, merge
PR #13 and run Phase A (`selftest --certify` on the GPU box); it needs no
supervision after that.
