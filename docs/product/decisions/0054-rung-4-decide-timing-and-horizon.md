# PDR-0054 — Rung 4 DECIDE: does the graft's timing, or the training horizon, change the outcome? (`norm`; stop at rung 4 if neither does)

Date: 2026-10-09   Status: **accepted (owner-signed)**   Author: Claude (session 17)
Owner sign-off: **RECEIVED 2026-10-09**, in session, choosing from Claude's
options:
- rung 4 scope: "Timing + horizon, norm";
- stop condition: "Stop at rung 4".

Under PDR-0053, the question and stop condition are programme-level, so
they are the owner's. The per-study plan that operationalises them is
Claude's, under review, a dry run, a hash freeze and an in-session sketch
before launch.
Related: PDR-0050 (ladder), PDR-0052 (rung 3: partial capture), PDR-0053
(gate split); `docs/results/2026-10-09-graft-capture-v2.md`

## Context

Rung 3 read partial capture. With the `norm` seed, a graft germinated
before epoch 2 recovers 0.60 [0.51, 0.72] of static capacity's gain over no
growth, and static beats it by 0.057 [0.028, 0.086]. The graft−static gap
was still narrowing at the 10-epoch horizon: +0.087 at epoch 6, +0.044 at
epoch 9 (descriptive). Static is the same capacity, fully coupled from step
zero, so two hypotheses remain open:
- **Timing:** grafting earlier captures more.
- **Head start:** static's lead is a head start that a longer horizon would
  erase.

They are confounded at a single timing and horizon.

**Location is out of scope.** The bounded host has one insertion site, so
location needs host engineering first. It is a later, separate owner
decision.

## The call

**The rung-4 question.** On the `under_normalized` host with the `norm` seed
and lifecycle v2, does the graft's germination timing (`graft_epoch` from
0 to 5, the range the 10-epoch lifecycle allows), or the training horizon
(10 epochs against 20), change how much of static's gain the graft
captures?

**Stop condition (owner-signed).** If neither timing nor horizon changes
the outcome (capture stays flat and static still wins), **the ladder stops
at rung 4.** The result is written up as a clean negative for the scheduled
graft at this scale. Location, or a different host, proceeds only through a
new owner decision.

**What the per-study plan must do** (Claude's, under PDR-0053):
- operationalise "changes the outcome" and "flat" as a pre-registered
  reading rule, with stated margins and simulated operating
  characteristics;
- report failure rates apart from finite performance, as in PDR-0051 and
  PDR-0052;
- declare the static host-instability policy (`simic-9c5c3a2acf`). Earlier
  grafts spend longer in fully coupled joint training, the regime where
  static diverges;
- run on fresh seeds with the GPU profile, from snapshots, with a gating
  dry run, and be sketched to the owner in session before launch.

## Rationale

Timing is the cheapest lever the ladder has: one RunSpec field, no new
apparatus. The horizon arm is what separates "graft earlier" from "train
longer". Without it, a timing effect could not be told apart from a
head-start effect.

`norm` is the right single seed type. It captured the most (60%), at
almost no added compute (+0.06% optimizer parameter-steps).

Rung 5 (can telemetry predict the best choice?) only has something to
predict if some choice matters. Rung 4 finds out whether timing is such a
choice, at the cost of about 1–2 GPU-hours.

## Reversal trigger

- The owner widens rung 4, to `conv_heavy` or to location. That is a new
  owner-signed PDR.
- The per-study plan cannot operationalise "flat" with useful power within
  the GPU window. Bring the trade-off back to the owner before launch; do
  not weaken the stop condition.
