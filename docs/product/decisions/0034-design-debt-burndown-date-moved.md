# PDR-0034 — Design-debt burn-down target moved 2026-08-31 → 2026-09-30

Date: 2026-08-10   Status: accepted   Author: Claude (session 15)
Owner sign-off: RECEIVED in-session — the fired date was put to the owner as
the re-plan choice PDR-0033's checkpoint queued, and the owner chose to move it.
Recorded at checkpoint from `metrics.md` as amended in-session; the exchange
itself is not quoted here.
Related: PDR-0005 (pacing posture — a date is a signal, not pressure),
PDR-0031/PDR-0033 (the kernel demo taking the Now slot), `metrics.md`

## Context

The burn-down target (open `hld-review` tracker items → 0 by 2026-08-31)
fired: three consecutive sessions with zero closures, because sessions 12b–14
went to the kernel demo — spec lock, plan, full implementation, merge — and
ADR-0015. 31 open / 23 closed. The metric's own header condition ("a second
no-closure session puts 2026-08-31 out of reach") was met and exceeded:
~15 working days at ≈2.1 closures/day is not a spare-time pace.

Session 14's checkpoint named this the first thing to put to the owner, with
three options and an explicit instruction not to treat it as schedule pressure.

## Options

1. **Move the date.** Keeps the bet alive and the metric honest; admits the
   demo displaced it.
2. **Shrink the scope to a blocking subset** — only the items that actually
   gate Phase A. Preserves the date by redefining the target.
3. **Accept explicitly that the demo displaced it** and drop the date until
   the demo run completes.

## The call

Option 1. Target moves to **2026-09-30**, recorded in `metrics.md` with the
displacement stated in the reading rather than hidden in a silent re-target.
The reading now also carries the context a cold reader needs: the project is
two days old, 23 items closed in that span, and a displaced bet is a choice
being made visibly — which is what PDR-0005 asks a date to do.

## Rationale

Option 2 is the seductive one and the wrong one here: redefining the target to
whatever is already achievable makes the metric unfalsifiable, which is the
failure the scoreboard exists to prevent. Option 3 loses the visibility. Moving
the date keeps a falsifiable target and records the trade honestly.

Noted at the time of the call: 2026-09-30 now shares a month with the Phase A
target, and the two compete for the same spare-time slot.

## Reversal trigger

If a **fourth** consecutive no-closure session occurs, or the burn-down is
still above 20 open on **2026-09-15**, the date is not moved again — the honest
reading at that point is that design hardening is not a Now bet, and it returns
to DECIDE for demotion rather than a third target.
