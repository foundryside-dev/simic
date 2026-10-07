# PDR-0043 — Roadmap re-based on the bounded reboot; the fired burn-down date is un-dated, not moved

Date: 2026-10-08   Status: accepted   Author: Claude (session 17)
Owner sign-off: within the grant ("reprioritize", "kill a failing bet per
metrics.md"; PDR-0040 carriage). The underlying scope change is owner-made:
ADR-0018, 2026-10-04.
Related: ADR-0018, PDR-0034 (burn-down date, no second move), PDR-0031/0033
(kernel demo as a Now bet)

## Context

On 2026-10-04 ADR-0018 put the bounded structural comparison ahead of the
older Phase A sequence. The roadmap was not updated to match. It still showed
three Now bets: the kernel demo run, design hardening and the ADR-0002
regime. None of them has moved since 2026-08-10:

- **Design-debt burn-down:** 31 open / 23 closed `hld-review` items, the same
  count as on 2026-08-10. Its 2026-09-30 date fired. PDR-0034 pre-committed:
  *"the date is not moved a second time."*
- **Phase A** had a provisional target of 2026-09-30. It fired at 0 of 11
  phases.
- **Kernel demo:** the preflight failed gates 1–5 and never froze. ADR-0018
  kept the code and campaign "unchanged" and built the bounded comparison on
  its primitives instead.

## Options

1. **Re-date both fired targets.** This breaks PDR-0034's pre-commitment, and
   the "date that moves every month" is the failure mode that PDR-0005 exists
   to make visible.
2. **Kill design hardening and Phase A.** This overreaches. ADR-0018 is
   explicitly bounded ("does not implement the full HLD") and says that more
   work follows only if the comparison warrants it. Killing the programme
   would be a vision change, which belongs to the owner.
3. **Re-base on ADR-0018.** Make the bounded comparison the one Now bet. Move
   design hardening and Phase A to Next, *un-dated*, gated on the bounded
   screen's result. Park the kernel demo campaign in Later with its re-entry
   conditions named.

## The call

Option 3. The fired dates are honoured, not moved: they are removed, and
their place is taken by an evidence gate. Phase A resumes when the bounded
multi-seed screen (`simic-7486bc6929`) reports. The tracker
enforces this: the paused items depend on the gate issue `simic-6f4f111ec8`.
- If paired differences are resolvable at bounded scale, resume with the ~10
  contract-blocking items.
- If they are not, the HLD's central instrument needs redesign before any
  contract is drafted.

## Rationale

This records what ADR-0018 already decided, and keeps PDR-0034's promise
literally: the date did not move a second time. An evidence gate fits a
spare-time moonshot better than a calendar, because the calendar has fired
twice with zero movement and the evidence gate is about an hour of CPU away.

## Reversal trigger

The owner restores design hardening as a Now bet, or the bounded screen
reports. Either one returns this to DECIDE, and the screen's result decides
the direction.
