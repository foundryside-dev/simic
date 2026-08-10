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

## DECISION QUEUE — answer in this order, all before Phase A

**Everything below shuts at `--certify`, and two items shut earlier still (at
*collection*).** `--certify` pins HEAD; `freeze_manifest` refuses when
`HEAD != certified_rev`. Phase A (`simic-7c42fc9c0b`) is now tracker-blocked on
Q2 and Q3, so it will not present as ready until they are answered.

**Q1 — Confirm the rev 6.2 amendment text** (PR #13, branch
`kernel-demo-rev62-arm-recording`, head `4de447f`). You accepted the
recommendation; the wording has not been read back. PDR-0036 pre-commits the
failure mode: unconfirmed before Phase A ⇒ the amendment is **dropped** and the
campaign runs on rev 6.1. Never defaulted in.
*(Corrected 2026-08-10: the earlier justification — that the header "propagates
into every `frozen.json`" — is false; `spec_rev` is a hardcoded string. The
posture stands on simpler ground: don't write an unearned human-approval claim
into a locked spec.)*

**Q2 — Task 19B, the panel's must-fix list** (`simic-e3ad55344f`; plan Task 19B).
Four items; 19B.4 is explicitly yours to defer knowingly. **19B.1 and 19B.2
touch `run_report`, which is `@semantic` — their window shuts at COLLECTION,
not certify.** Three of six panel lenses had that timing wrong; the adversarial
pass caught it.

**Q3 — Task 19C, which of the six "free today" items to land**
(`simic-0fd4fcb933`; plan Task 19C). You directed these into the plan; *which*
is still open. The panel judged items 1–3 worth more than rev 6.2 itself.
19C.1 is the standout: the eval no-op baseline's **full trajectory is computed
and discarded**, and it is the paired control every lift is measured against —
the instrument that separates "the reward was unclear" from "the obs were
unclear" from "the technique doesn't work". Cost ~1.9 MB.

**Q4 — Phase-A sequencing, once the spike is in flight** (analysed, unrecorded —
no PDR yet). Not either/or: `ops/repo-structure.md`'s own milestone list puts
*package skeleton + forbidden-import checks* (milestone 2) **before** *define
Leyline contracts* (milestone 3). Milestone 2 is blocked by nothing and is the
natural fit for the 13–20 h unattended collect. Contracts are genuinely blocked
— but by **10 named items**, not all 31: `simic-0bf2c40dec`, `simic-38a07fad39`,
`simic-e3d6ff10c0`, `simic-4438123141`, `simic-0ec359f7fa`, `simic-1850e5e748`,
`simic-c726274799`, `simic-04ff4144b3`, `simic-e08aa5dd60`, `simic-c912a35aa7`
(+ `simic-5503bbe389`, `simic-c304afab12` as Phase-A acceptance work). Offered
reversal trigger if you want it recorded: *if the burn-down posts a fifth
consecutive zero-closure session, draft the contracts anyway as a forcing
function.*

**Q5 — Wardline inert / Tier-3 mechanical enforcement.** Boundaries are now
*declared* (`experiments/__init__.py`, ADR-0015 rule 2 form) but not
*enforced*: wardline's vocabulary is runtime decorators from
`wardline.decorators`, wardline is not a project dependency, and
`kernel_demo.py` is spec-pinned to torch + torchvision only. So a green
`wardline scan` still checks nothing. Needs a dependency decision
(`simic-8db0b87ed6`).

Carried: yzmir-training-state prompt relay vs fresh re-commissioning (PDR-0012);
wiki replatform (PDR-0028) approved but untracked.

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
**Work the decision queue above, Q1 → Q3.** Those three are the whole gate on
Phase A and they share one re-certify, so they should land in **one commit**.
Q4 and Q5 shape the session *after* the spike is running and can wait.

Then: merge PR #13 (**do not squash** — b9ae1af is the explicit retraction of
b5c10db's over-claim), re-run the additivity check *mechanically at the actual
certify commit* (`frozen_block_hash` byte-identical, `config_hash` moved, all 34
`FROZEN_FIELDS` values identical — the branch has moved five times today and
none of those is the certify commit), then Phase A unsupervised.

Owner's framing for why this run matters, recorded 2026-08-10: *"esper(ish) with
the new rapid training approach — esper-lite demonstrated the technique was
excellent, but we could never teach her to do it cleanly because our reward
function and obs were unclear."* The demo attacks both by construction (reward
end-state-only with the diverged-arm convention pre-registered as measurement;
telemetry a fixed 20-dim dataclass, blind by construction, missing field = error).
**The `beats_schedule_only` verdict boolean is the pre-registered test of which
one was the binding constraint** — schedule-only is the same policy with
telemetry masked to the epoch index alone.
