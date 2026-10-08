# PDR-0052 — Rung 3: graft-capture v2 on lifecycle v2, for both seed types

Date: 2026-10-08   Status: proposed (pending pre-launch review)   Author: Claude (session 17)
Owner sign-off: within the grant (PDR-0040 carriage, PDR-0050 ladder and
GPU window). On 2026-10-08 the owner directed: "great, lets do it", then
"go ahead, proceed autonomously with fable reviews".
Related: PDR-0046 (graft-capture v1), PDR-0049 (floor deferred to here),
PDR-0050 (ladder), PDR-0051 (lifecycle v2 accepted); plans
[`graft-capture-v2-norm`](../../prereg/graft-capture-v2-norm.json) and
[`graft-capture-v2-conv-heavy`](../../prereg/graft-capture-v2-conv-heavy.json);
`simic-9c5c3a2acf` (static-arm host instability), `simic-f73351380d`

## Context

Rung 3 asks whether a graft captures the deficit that rung 2 measured.
Lifecycle v2 removed the graft's divergence: 0/48 units, against v1's
14/48 (PDR-0051). The validation's descriptive numbers were seen, so this
study is a confirmatory replication of a seen estimate:

| Seed | Graft − no growth | Static − no growth | Capture (graft ÷ static) |
|---|---:|---:|---:|
| `norm` | −0.068 | −0.154 | about 44% |
| `conv_heavy` | −0.054 | −0.142 | about 38% |

`partial_capture` is the predictable reading, and the plans say so.

Two things stop graft-capture-v1 from being run as written:
- its launch condition (positive-control-v1 `control_passes`) never held;
- its `fail_unit` policy would let a static-arm divergence remove the
  graft − no-growth pair too. The static `norm` arm diverges on this host:
  2/72, 95% interval 0.3%–9.7% (`simic-9c5c3a2acf`).

## The call

Run two sibling plans, `graft-capture-v2-norm` and
`graft-capture-v2-conv-heavy`. Each is graft-capture-v1 plus these
deviations:

- **lifecycle v2** on the GPU profile, from one immutable snapshot, with the
  data identity pinned;
- **96 fresh seeds (7001–7096)**, the same in both plans. n is set so the
  graft − static half-width, at the sd's 95% upper confidence limit, is
  ≤ δ in the harder cell (0.043 at α = 0.0125);
- **one multiplicity family of four co-primaries across both plans**
  (α = 0.0125 each, 98.75% intervals). Rung 3 is answered by both seed
  types together, and the two plans share one host trajectory per seed.
  Each plan is read on its own; nothing is pooled.
- **δ = 0.05 is retained**, as the graft floor from PDR-0044 and PDR-0046.
  PDR-0049 deferred the floor to this redesign. It is kept because it
  predates every lifecycle-v2 estimate, so choosing it now cannot be fitted
  to the seen numbers. The capture-fraction readings do not need a hard
  δ_pc.
- **`diverged_arm_policy: per_contrast`** (new in `bounded_screen`). A unit
  enters each contrast if and only if both of its arms finished. A static
  divergence therefore costs only the pairs that need static.
- **reading rule `graft-capture-v2`** (new). It applies v1's precedence
  behind two gates:
  - `graft_unstable` if more than 3 of 96 graft arms diverge. The graft's
    failures are counted against it, never dropped.
  - `reopen_static_not_credible` if more than 10 of 96 static arms diverge.

  The rationale for both caps is in each plan's `decision.caps_rationale`.
- **declared sensitivity**: each lost co-primary pair is imputed at the
  observed extreme favouring each arm in turn, and the report states
  whether the reading moves;
- **capture fraction**: reported descriptively, with a 95% paired
  bootstrap interval.

For `conv_heavy`, the descriptive static − no growth contrast is that seed
type's first deficit measurement, because rung 2 was met with `norm` only.

**Order:**
1. Tests, then the full suite, then commit.
2. Reviews: Fable statistics review, product-decision critique, and code
   review.
3. A 3-seed real-config GPU dry run per plan (seeds 9207–9209), read for
   mechanics only.
4. Amend if needed, then commit.
5. Launch **both** fleets before analysing **either**, so one seed type's
   result cannot inform the other's plan.
6. Analyse each fleet from its snapshot, and write up.

## Rationale

The graft is the first growth mechanism on this ladder that is both stable
and measurable on a host with a real deficit. A confirmatory reading on
fresh seeds turns the validation's descriptive capture estimate (about 40%)
into a pre-registered answer for rung 3, at low cost: about 40 minutes of
GPU. `partial_capture` would mean "a graft repairs part of the deficit, but
adding the same capacity later loses most of its value". That would point
rung 4 at timing and location, not at the controller.

## Reading consequences

These are each plan's `decision.readings`, unchanged. In short:
- `partial_capture` → shape rung 4 (timing and location).
- `progress` → shape rung 4 from full capture.
- `reopen_static_wins` → check the trajectories (head start versus repair)
  before a structural claim.
- `graft_unstable` → diagnose lifecycle v2 at scale before any capture
  claim.
- `reopen_static_not_credible` → the comparator needs fixing
  (`simic-9c5c3a2acf`) or more units.
- `instrument_failure` → investigate. Any re-run uses fresh seeds.

## Reversal trigger

Any change to either plan, or to `bounded_screen.py`, after launch is an
amendment, and the analysis refuses a changed plan or module. If both plans
read `reopen_static_wins` or `reopen_no_value`, the bounded line records
rung 3 as "no capture at this horizon". A new PDR then decides between a
horizon or timing probe (rung 4's question asked early) and stopping.

## Re-analysis note

Editing `bounded_screen.py` changes its hash, so earlier screens (screen v1
and positive control v1/v2) cannot be re-analysed at HEAD. They could not
be anyway, because the runner's source identity changed. Each is re-analysed
from its own snapshot or commit.
