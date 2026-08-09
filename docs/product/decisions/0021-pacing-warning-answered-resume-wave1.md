# PDR-0021 — Pacing warning answered: resume wave:1, retain the 2026-08-31 date

Date: 2026-08-09   Status: accepted   Author: Claude (product-owner session 11)
Owner sign-off: RECEIVED 2026-08-09 (session 11 AskUserQuestion — "Resume
wave:1 (Recommended)" selected over critical-path-first, date re-plan, and
ADR-0002-first)
Related: PDR-0005 (pacing-signal discipline), PDR-0008 (wave programme),
metrics.md design-debt burn-down, ADR-0010, simic-d6ea02f9a9

## Context

The pacing warning fired at session 9 and stood unanswered through session
10 and the design-system-recovery session: four working sessions of
owner-directed quality/consistency work (wiki projection, static hardening,
Namespec 2.0, design-system recovery) with the burn-down flat at 38. At
2026-08-09 the 2026-08-31 pacing date needed ~1.7 closures per working day.
PDR-0005's rule: a fired signal must be answered by DECIDE — resumed or
re-planned — never silently drifted past.

## The call

Resume wave:1 closures; the 2026-08-31 date is retained, not re-planned.
Executed immediately: simic-d6ea02f9a9 (containment accountability) claimed
and closed VERIFIED the same session via ADR-0010 — the first wave:1
closure since session 6. Burn-down 38 → 37; five wave:1 items remain.

Options considered and declined this round: critical-path-first
(simic-0bf2c40dec — remains the named alternative when wave order and
leverage conflict); re-planning the date by PDR (legitimate under PDR-0005,
but the owner chose cadence over slippage); starting ADR-0002
(simic-357c92664c — does not move the burn-down and needs owner presence at
the seeding gate).

## Rationale

The warning existed to force a choice, and the owner made it: the date is a
real pacing signal, so the answer is closures, not a moved goalpost. The
quality work of sessions 7–10 was each individually owner-directed and
correct; the discipline failure would have been letting that pattern
continue *silently*. It did not.

## Reversal trigger

Re-plan the date by PDR — do not carry it — if the burn-down is not ≤ 33 by
the 2026-08-16 reading (i.e. fewer than four further closures in the next
week of working sessions), or at any earlier point where remaining items ÷
remaining working days exceeds ~3/day. Either reading fires the PDR-0005
re-plan obligation; silent carry remains the one disallowed outcome.
