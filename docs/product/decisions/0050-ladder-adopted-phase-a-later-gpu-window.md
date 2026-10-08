# PDR-0050 — The experiment ladder is the sequencing authority; Phase A moves to Later; GPU authorised for an exclusive window

Date: 2026-10-08   Status: accepted   Author: Claude (session 17)
Owner sign-off: **RECEIVED 2026-10-08**, verbatim:

> "1. Approved, 2. Per your recommendation, 3. GPU approved, you have
> exclusive use to them for at least the next week or so so that's why
> we're keep to get you working"

Related: PDR-0043, PDR-0045 (which resumed Phase A; partly reversed here),
PDR-0049, ADR-0018, `vision.md` authority grant

## Context

PDR-0045 applied a pre-committed reading that resumed Phase A: contract
shapes for all fourteen HLD domains. Claude then recommended reversing that
as strategy, because it rebuilds esper-lite's weight before any growth
effect exists. The reboot's one defence is to build nothing until a bounded
experiment needs it. ADR-0018 also authorised no GPU work, and every rung
from 4 on needs GPU-scale compute.

## The calls

1. **The bounded ladder is the sequencing authority.** It replaces the
   Phase A–K order for experimental work:

   | Rung | Question | Status (2026-10-08) |
   |---|---|---|
   | 1 | Is the measurement precise enough? | met (PDR-0045) |
   | 2 | Is there a repairable deficit? | met as a question, below the floor (PDR-0049) |
   | 3 | Does a graft capture the deficit? | **next**, after the lifecycle redesign (`simic-75be93e372`) |
   | 4 | Does the timing or location of the graft change the outcome? | needs GPU |
   | 5 | Can telemetry predict the best choice better than a fixed schedule? | the first Tamiyo-shaped result |

   Every rung is one pre-registered, reviewed experiment with a stop
   condition.
2. **Phase A moves to Later.** HLD contracts are drafted only when a rung
   needs them, starting at rung 5, and only for the parts that rung touches.
   This reverses the "Phase A resumes" consequence of PDR-0045. The
   instrument-resolution finding it rested on still stands. The ~30
   HLD/Phase-A tracker items are re-parked behind a rung-5 gate.
3. **GPU is authorised.** The owner gives exclusive use of both RTX 4060 Ti
   GPUs (16 GB each) for at least about a week from 2026-10-08. This lifts
   ADR-0018's "no GPU campaign" for ladder work. Bounds:
   - every GPU run is inside the active bet;
   - every run is a pre-registered PDR, reviewed before launch;
   - every plan declares its execution profile.

   Bitwise CPU pairing is the reference. A GPU plan must state whether
   pairing holds bitwise, through deterministic algorithms and a fixed
   CUBLAS workspace, or carries measured uncertainty (INV-05).

## Rationale

The ladder reaches esper-lite's strategic intent, a learned controller with
structural taste, by the shortest route that is measurable at every step.
Its stop conditions are what keep it from collapsing the same way. The GPU
window is time-limited, so lifecycle-redesign work that can run on GPU
should use it.

## Reversal trigger

The owner may restore Phase A, withdraw the GPU window, or stop the
ladder. Separately, if a rung's stop condition fires, the ladder stops at
that rung and records it as the result.
