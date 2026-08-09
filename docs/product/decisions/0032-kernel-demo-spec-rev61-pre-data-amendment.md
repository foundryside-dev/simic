# PDR-0032 — Kernel demo spec rev 6.1: episode-level money-chart null + falsifier CI (pre-data amendment)

Date: 2026-08-10   Status: accepted   Author: Claude (session 14)
Owner sign-off: RECEIVED in-session ("ok, lets do it now") — the amendment
was presented with its statistical rationale and the free-now/unfixable-later
framing, and the owner directed immediate execution.
Related: PDR-0028 (spec provenance), PDR-0029 (proof-of-concept purpose),
[[kernel-demo-spec-locked]] memory, spec `docs/superpowers/specs/2026-08-09-kernel-demo-design.md`

## Context

The locked spec (rev 6) pre-registered the money-chart permutation null as
"pathology labels shuffled across eval fans" and the falsifier's Wilson CI
at the grid-point count. A counterfactual-statistics SME review of the
finished implementation (session 14) confirmed both are cluster-blind:
pathology is an episode-level attribute and the two grid fans of one
episode carry correlated picks, so the 200-point null under-disperses by
up to 2× — money_p biased low (the gate could pass on miscalibration) and
the falsifier CI too tight (the demo could honestly fail its own falsifier
through miscalibration alone). Two of the five pre-registered verdict
booleans were affected. No data existed (no store, pre-Phase-B).

## Options

1. Amend now, pre-data: episode-level shuffle + episode-count CI; spec
   edited in place with rev 6.1 markers; statistically free because no
   observation could yet favor either scheme.
2. Leave rev 6 as-is and note the defect: preserves the lock ceremony but
   knowingly runs a miscalibrated pre-registration; post-Phase-E amendment
   would void the one-shot eval.
3. Amend at freeze (Phase B): same effect but leaves a window in which a
   preflight iteration could be argued to have informed the choice.

## The call

Option 1. Spec is now **rev 6.1**: permutation unit = episode (all of an
episode's grid points move together; two labels on one episode raises),
falsifier Wilson CI and agreement MDE at the episode count (N_eval=100).
Implemented same-session (commit 5cf44b8): spec amended in place with
rev 6.1 markers, manifest `spec_rev` literal names the amendment,
clustered-permutation tests pin the scheme.

## Rationale

A pre-registration's value is calibration; a knowingly miscalibrated null
is worse than an amended one, and the amendment window closes permanently
at Phase E. Recording the amendment inside the spec (not a side note)
keeps the lock ceremony honest: rev 6.1 is the pre-registration of record,
timestamped pre-data.

## Reversal trigger

None in the ordinary sense — reverting to point-level shuffling after any
data exists would itself be the defect this PDR closes. If a future
statistical review shows the episode-level scheme is ALSO miscalibrated
(e.g. cross-episode dependence via shared schedules), that is a new
pre-data amendment gated on the same condition: no eval store may exist.
