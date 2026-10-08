# PDR-0052 — Rung 3: graft-capture v2 on lifecycle v2, for both seed types

Date: 2026-10-08   Status: proposed (pending pre-launch review)   Author: Claude (session 17)
Owner sign-off: within the grant (PDR-0040 carriage, PDR-0050 ladder and
GPU window). On 2026-10-08 Claude proposed: "pre-register graft-capture v2
(rung 3) on lifecycle v2, covering both seeds, with graft value measured
over all units, the failure rate reported apart, and a host-instability
policy; then review, dry-run, run". The owner replied "great, lets do it".
After the design sketch (main contrast graft − no growth, static secondary
with a declared failure policy, fresh seeds, review and dry run before
launch), the owner said "go ahead, proceed autonomously with fable reviews".
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
  to the seen numbers. **δ gates precision and `progress` only.**
  `partial_capture` has no value floor by design (PDR-0046 F1). What this
  study measures is the capture-fraction interval, not a 0.05 threshold.
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
  observed extreme favouring one arm, independently per co-primary (every
  corner), and the report states whether the reading moves. This is a
  heuristic, not a bound. Beside it, a **selection diagnostic** reports
  graft − no growth separately for units that lost static and units that
  did not;
- **capture fraction**: reported descriptively, with a 95% paired
  bootstrap interval. The interval is withheld if any resampled deficit
  reaches zero.

**Ladder deviation, named.** Rung 2 was met with `norm` only. `conv_heavy`
enters rung 3 without its own rung-2 study, because the validation measured
its deficit descriptively: static − no growth −0.142 over 24 units. Its
descriptive static − no growth contrast here is that seed type's first
pre-registered deficit measurement.

**Rung-3 verdict, composed from the two plans before launch.** Both plans
carry this table in `decision.rung_composition`, so it is hash-pinned.

The first matching row applies.
- **Conclusive** readings: `progress`, `partial_capture`,
  `reopen_static_wins`, `reopen_no_value`.
- **Inconclusive** readings: `reopen_static_not_credible`,
  `reopen_instrument_imprecise`.

| # | Readings (either order) | Rung-3 verdict |
|---|---|---|
| 1 | `graft_unstable` in either | Lifecycle v2 is unstable at scale. No capture claim for either seed type. Diagnose before rung 4. |
| 2 | `instrument_failure` in either | That seed type is unresolved. Re-run on fresh seeds. No rung verdict until it is resolved. |
| 3 | `progress` + `progress` | **Capture.** |
| 4 | both in {`progress`, `partial_capture`}, not both `progress` | **Partial capture.** The graft repairs part of the deficit. Static wins at the declared cost (ADR-0018), which is a negative on graft ≥ static at this horizon. |
| 5 | both in {`reopen_static_wins`, `reopen_no_value`} | **No capture.** The ladder stops at rung 3 (PDR-0050). |
| 6 | one in {`progress`, `partial_capture`}, the other in {`reopen_static_wins`, `reopen_no_value`} | **Seed-type dependent.** Rung 3 is met only for the capturing seed type. |
| 7 | one conclusive, the other inconclusive | The verdict comes from the conclusive plan alone, labelled single-seed-type. A single-seed-type *no capture* does **not** stop the ladder: it holds until the inconclusive plan's own consequence (a new PDR) is resolved. |
| 8 | both inconclusive | **Rung 3 unresolved**, no verdict. Each plan routes to its own consequence. |

**Two decisions recorded with this one:**
- **The static comparator is handled by policy, not fixed first.**
  `simic-9c5c3a2acf` is handled by `per_contrast`, a cap and a
  sensitivity check. The static arm *is* ADR-0018's comparator (the same
  capacity, trained normally from step zero). Stabilising it would change
  the question, and the GPU window is time-limited.
- **The window plan after rung 3.** The next step is a rung-4 DECIDE PDR,
  drafted only after both plans read. It covers whether timing or location
  changes the outcome, fanned from snapshots by the bounded runner, not the
  parked kernel demo. If the window closes first, rung 4 waits for the next
  GPU window.

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

## Pre-launch reviews

Three Fable reviews of `e63a1e3` (statistics, product decision, and code)
returned GO / PROCEED with changes:

- **Statistics.** All numbers reproduced. The sensitivity covered only two
  of its four corners, the static losses needed a selection diagnostic,
  and the capture interval needed a guard.
- **Product.**
  - The two plans had no pre-committed way to combine split readings into
    a rung verdict; the table above was added.
  - The reversal trigger softened PDR-0050's stop rule; it was aligned.
  - `partial_capture` had been framed as progress.
  - `metrics.md`, `roadmap.md` and `current-state.md` carried stale lines.
- **Code.** `fail_unit` output was byte-identical to `main` across 10
  cases. It found that:
  - the fit/dev pin was checked only after a fleet had run;
  - older rules could be run under `per_contrast`;
  - costs mixed diverged and finished arms;
  - a cap reading hid the v1 gates.

All of these were fixed before launch, with tests. Both 3-seed dry runs are
re-run on the amended commit, analysis included.

## Rationale

The likely reading is `partial_capture`, predicted at ≥ 0.97 from seen
numbers, so the categorical label is not the point. What the study buys:

- **Graft stability at scale.** The graft gate runs on 192 v2 graft arms,
  four times the validation. Zero divergences would bound the rate per
  seed type at about 3.1% (0/96, exact one-sided 95%), against 11.7%
  (0/24) now. That matters
  because rung 4 fans from this lifecycle.
- **Precision.** The capture-fraction interval comes out about twice as
  narrow as the validation's, on fresh seeds and pre-registered.
- **New measurements.** It gives `conv_heavy`'s first pre-registered
  deficit measurement, and a static-arm failure count over 192 static arms
  for `simic-9c5c3a2acf`.

Under ADR-0018, `partial_capture` means **static wins at the declared
cost**. That is a negative on graft ≥ static at this horizon, not progress
toward it. The ladder's response is to reopen the design at rung 4 (timing
and location), never to enlarge the controller. The cost is about 40
minutes of GPU.

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
amendment, and the analysis refuses a changed plan or module. If the
composed rung-3 verdict is **no capture**, the ladder stops at rung 3 and
records that as its result, as PDR-0050 requires. Any continuation, such as
a horizon or timing probe, is a new owner-signed decision.

## Re-analysis note

Editing `bounded_screen.py` changes its hash, so earlier screens (screen v1
and positive control v1/v2) cannot be re-analysed at HEAD. They could not
be anyway, because the runner's source identity changed. Each is re-analysed
from its own snapshot or commit.
