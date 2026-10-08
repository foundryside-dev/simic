# PDR-0045 — Screen reading `reopen_no_value`: the instrument resolves, the graft earns nothing at bounded scale; the PDR-0043 gate closes

Date: 2026-10-08   Status: accepted   Author: Claude (session 17)
Owner sign-off: within the grant. This applies a reading that was
pre-committed in PDR-0044 before any data; no new judgement is exercised
here.
Related: ADR-0018, PDR-0043 (the gate), PDR-0044 (the frozen plan), result
[`docs/results/2026-10-08-bounded-screen-v1.md`](../../results/2026-10-08-bounded-screen-v1.md),
`simic-6f4f111ec8` (gate), `simic-dda0d0188c`

## Context

The pre-registered screen (PDR-0044) ran on 2026-10-08: 48 paired units, all
completed, no failures, analysed once from clean commit `f5aeda2`. The
endpoint is late-epoch (7–9) development CE.

| Contrast | Mean | 97.5% interval | Half-width | Verdict |
|---|---:|---|---:|---|
| Scheduled − no growth | +0.0016 | [−0.017, +0.020] | 0.018 | equivalent within floor (δ = 0.05) |
| Scheduled − static | −0.0163 | [−0.045, +0.013] | 0.029 | equivalent within floor |

The gate criterion is met (0.018 ≤ 0.05), and so is the static-credibility
criterion (0.029 ≤ 0.05). ADR-0018's trigger does not fire.

## The call — the pre-committed reading, applied

**`reopen_no_value`.** The plan's words: *"Instrument resolves, no trigger,
but the graft does not beat no growth beyond the floor: the lifecycle does
not earn its cost at this scale. Reopen the design, and resume Phase A only
because the instrument itself resolves."*

1. **The PDR-0043 gate closes, on the "resolves" branch.** The paired
   counterfactual instrument bounds a matched-no-op difference to ±0.018 nats
   with 48 units, at about 4.7 CPU-hours. This is the first measured,
   criterion-18-shaped reading in the programme. It concerns *resolution*
   only. No intervention has yet produced an effect that the instrument then
   detected.
2. **Phase A resumes,** starting with the ~10 contract-blocking items led by
   `simic-0bf2c40dec`, as PDR-0043 specified. The design-debt burn-down
   becomes live again. It stays un-dated (PDR-0043): pace is by session, not
   calendar.
3. **The bounded lifecycle design reopens.** At this host, data scale and
   schedule, the scheduled graft is indistinguishable from doing nothing and
   costs 5% more optimizer work. Per ADR-0018: *do not respond by enlarging
   the controller.* No random, heuristic or learned timing work starts on
   this configuration.
4. **The kernel demo campaign stays parked.** PDR-0043 gives it its own
   DECIDE, and this screen gives no reason to reopen it. Its tracker items
   move from the closed gate to their own parking issue, so that closing the
   gate does not silently make them ready.

## What the redesign should start from (exploratory, not a decision)

Static extra capacity is *also* indistinguishable from no growth. So the
likeliest reading is that the experiment had no deficit to repair: a host
that is not capacity-limited cannot show a benefit from any growth
intervention. The next bounded experiment should therefore establish a
**measured, repairable deficit first**, then ask whether a graft repairs it
better than static capacity and cheaper than over-provisioning. Two starting
points:

- Esper's degenerate-architecture fixtures, with known ~10% → ~40%
  headroom;
- a deliberately under-provisioned host at the same data scale.

Before any graft arm runs, a positive control should show that static
capacity beats no growth there, beyond δ. This is shaping input for
`simic-f73351380d`, not a commitment.

## Rationale

The readings were frozen before the data, so applying them is the whole
decision. The alternatives would each be a post-hoc move:
- re-reading the horizon;
- slicing the units;
- treating the −0.016 favouring the graft over static as a signal, when its
  interval spans zero.

The useful output is the instrument's resolution and a sharper question,
not a growth result.

## Reversal trigger

A re-analysis of the archived per-unit logs under the frozen plan that
disagrees with `screen_report.json` would void this reading. The logs are
in the repository, so that check is cheap. Separately: if Phase A contract
work reveals that the bounded instrument's matching contract differs
materially from the HLD's (INV-06 common future, INV-15/16 no-op), the
"resolves" reading applies to the bounded instrument only, and must be
re-earned under Tolaria.
