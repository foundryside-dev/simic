# PDR-0056 — Compute direction: jobs on nyx need no permission

Date: 2026-10-09   Status: accepted (owner's own words)   Author: Claude (session 17)
Owner sign-off: **RECEIVED 2026-10-09**, unprompted, in session:
*"I'm willing to commit more compute to this - nyx is my hardware so you
don't need to ask for permission to run a job/batch, If I want to stop it I
will."* Later the same day: *"go ahead, proceed autonomously"*.
Related: PDR-0050 (GPU window), PDR-0053 (gate split), PDR-0055 (rung 4
plan); `docs/product/vision.md` (grant, COMPUTE paragraph)

## Context

The rung-4 pilot showed the horizon arm needs far more seeds than the
sketch assumed: about 8 GPU-hours against about 1.5. Claude brought the
trade-off to the owner (PDR-0054's reversal trigger). The owner answered
the trade-off ("bigger pilot, then size") and then gave this direction.
Every earlier grant change has its own PDR, so this one does too.

## The call

- **Jobs and batches on nyx need no permission.** The owner stops a job
  himself if he wants to.
- **Unchanged:**
  - the in-session sketch of a study's design before launch (PDR-0053);
  - programme-level gates, which are the owner's;
  - outer/test data, which stays owner-gated;
  - paid or off-nyx compute, which stays reserved.
- **The GPU window.** PDR-0050 granted "at least the next week or so". This
  direction states no end, and Claude reads it as covering nyx jobs beyond
  that week. The owner can bound it at any time; until then, the reading is
  recorded here so it can be checked.

**Obligation that comes with it.** "If I want to stop it I will" only works
if the owner can see what is running. Every launched fleet is therefore
recorded where he looks, not only in the local `runs/` tree:
- in `current-state.md`, with its root, its seeds and an estimated end time;
- as a comment on the bet's tracker issue.

## Reversal trigger

The owner bounds or withdraws the direction. Or a job runs that the owner
could not have seen, because it was not recorded in `current-state.md` or
the tracker before or at launch; that is a breach of this PDR's obligation.
