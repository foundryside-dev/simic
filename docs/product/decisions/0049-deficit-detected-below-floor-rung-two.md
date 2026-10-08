# PDR-0049 — Rung 2: a real deficit is detected below the pre-registered floor; continue through the lifecycle redesign, set the next floor there

Date: 2026-10-08   Status: **accepted**   Author: Claude (session 17)
Owner sign-off: **RECEIVED 2026-10-08**: "1. Approved". The applied reading
was within the grant. The owner ratified the continuation through the graft
lifecycle redesign.
Related: PDR-0046 (δ_pc), PDR-0047, PDR-0048, result
[`docs/results/2026-10-08-positive-control-v2.md`](../../results/2026-10-08-positive-control-v2.md),
`simic-75be93e372`, `simic-f73351380d`

## Context

`positive-control-v2` read `control_fails_below_floor`. Static − no growth
is −0.119 [−0.151, −0.088], and static helped in 89% of units. The plan's
consequence for this reading: "a new PDR chooses between a longer horizon
or budget and stopping".

## The applied reading (within the grant)

**Rung 2 is met as a question and not met at the pre-registered floor.**
Both statements are true, and neither is re-read away.

- On this host there *is* a measurable, repairable deficit. It replicated on
  fresh seeds after the expected shrinkage from the exploratory estimate.
- The data are **not** re-analysed against any lower floor. That would be
  the post-hoc move the pre-registration exists to prevent.

## The recommendation (accepted)

The plan's three options all assume the floor is a property of this host.
It is not. PDR-0046 set δ_pc = 0.10 as **2 × δ_graft**, purely to leave room
for a graft study. That graft study now has no runnable design, because the
graft lifecycle is unstable on this host (`simic-75be93e372`). So the
floor's rationale has gone with it.

1. **No further positive-control run.** Re-measuring will not change the
   deficit. A longer horizon is unlikely to move the gap past 0.10: it has
   been stable at about 0.10–0.14 per epoch since epoch 4, with both arms
   still descending.
2. **No replacement floor is chosen now.** The next floor is set *by the
   graft study's redesign* when it is pre-registered. The measured deficit
   (0.119, [0.088, 0.151]) is an input. Capture-fraction readings
   (`graft-capture-v1`'s `partial_capture`) do not need a hard 0.10.
3. **Do not stop.** The bounded line continues through the lifecycle
   redesign. The kernel sweep's fix set is the input: a scale-aware trust
   region, a frozen trust denominator, a separate gain learning rate, and
   host-edge stability (seed 2142). It is pre-registered and reviewed before
   any graft study.

## Reversal trigger

- If the owner prefers to stop the bounded line, or to test a longer
  horizon first, this proposal is superseded by that decision.
- If the lifecycle redesign cannot produce a graft that is stable on this
  host, the bounded line stops at rung 2, with this deficit as its result.

## Correction to the recommendation (2026-10-08, independent review)

An independent review reproduced the numbers from the archived evidence:
- 0.1194 nats, 95% interval [0.0881, 0.1507];
- 42 of 47 finite pairs benefiting;
- checksums matching.

It corrected three claims, adopted here:

- **"Below the floor" is about what was established, not the estimate.**
  The point estimate, 0.119, *exceeds* δ_pc = 0.10. What the experiment did
  not do is establish a benefit of at least 0.10: the interval's lower end
  is 0.088. The reading `control_fails_below_floor` stands as frozen. Read it
  as "a benefit ≥ 0.10 not established", never as "the benefit is below
  0.10".
- **More seeds would narrow the uncertainty.** The earlier statement that
  "re-measuring will not change the deficit" overstated things. Prioritising
  the lifecycle fix over more positive-control units is a choice about
  effort, not a claim that more data is uninformative.
- **The v1 → v2 shrinkage is consistent with selection, not proven to come
  from it.** v1's −0.159 used reconstructed controls from all 48 units, not
  only the graft survivors.
- **The benefit is conditional on the 47 finite control pairs.** Seed 2142's
  excluded static failure is disclosed. It is a separate mechanism (the
  static arm bypasses the graft's trust penalty), so lifecycle v2 does not
  address it.
