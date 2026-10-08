# PDR-0044 — The bounded multi-seed screen is pre-registered and funded

Date: 2026-10-08   Status: accepted   Author: Claude (session 17)
Owner sign-off: within the grant. The run authorization lets Claude add
experiments "each recorded as a PDR with a pre-committed reading", and
PDR-0040 gives carriage. ADR-0018's "propose with its budget before
execution" is met by this record, which is committed before the first
confirmatory unit runs.
Related: ADR-0018, PDR-0041 (the pilot), PDR-0043 (the gate this closes),
`simic-7486bc6929`, `simic-6f4f111ec8`, frozen plan
[`docs/prereg/bounded-screen-v1.json`](../../prereg/bounded-screen-v1.json),
code `experiments/bounded_screen.py`

## Context

The pilot (PDR-0041) showed that every arm learns, but one seed cannot
separate the arms. The design was then timed on one exploratory unit (seed 7)
at the screen's configuration: 4,096 fit / 5,000 dev examples, ten epochs,
5 min 50 s of single-threaded CPU, about 1 GB of memory. On that unit static
capacity finished *last*:

| Arm | Final dev CE |
|---|---|
| Static | 1.391 |
| No growth | 1.135 |
| Scheduled graft | 1.128 |

The pilot at 1,024 examples had ranked static capacity *first*. Two single
seeds pointing in opposite directions is exactly the situation a paired fleet
exists to resolve.

## The call

Run **48 paired units** (seeds 1001–1048). Seeds 7 and 999 are excluded as
exploratory. The run stays on development data only, under the frozen plan:

- **Endpoint:** mean development CE over epochs 7–9, per arm per unit. One
  paired difference per unit per contrast.
- **Co-primary contrasts:**
  - scheduled − no growth;
  - scheduled − static.

  Each gets a paired t interval at 97.5% (Bonferroni, family α 0.05), checked
  against a percentile bootstrap over units. Static − no growth is
  descriptive.
- **Floor δ = 0.05 nats.** It is fixed before the fleet, not fitted to the
  pilot.
- **Gate (PDR-0043):** the instrument *resolves at bounded scale* if the
  scheduled − no growth CI half-width is ≤ δ. This is precision on the matched
  no-op contrast, not significance.
- **Static comparison credible:** the scheduled − static CI half-width is ≤ δ.
  This is reported separately, because the static arm's own instability is not
  a property of the instrument.
- **ADR-0018 reopen trigger:** static wins (scheduled − static CI lower bound
  > 0), or either precision criterion fails.
- **Readings, all pre-committed:**
  - progress: shape timing next and resume Phase A;
  - reopen because static wins;
  - reopen because the graft adds no value, while still resuming Phase A
    because the instrument resolves;
  - reopen because the static comparison is not credible, while Phase A may
    still resume;
  - reopen because the instrument is imprecise: report the MDE, and keep
    Phase A paused.
- **The verdict table is deliberately asymmetric.** "Scheduled worse" fires
  on any significant deficit. "Scheduled better" needs the whole interval
  beyond −δ. Under ADR-0018 the burden of proof is on the intervention.
- **No exclusions, no re-runs, no interim looks.** Failed units are recorded.
  If more than 4 units fail, the verdict is instrument failure. The analysis
  publishes once and refuses to overwrite.

**Budget:** 48 × ~5.8 CPU-min ≈ 4.7 CPU-hours, run as 8 parallel
single-threaded workers (~8 GB of memory, ~35–45 min wall time) on nyx. The
host had 17 GB free, and a memory kill would count as a unit failure under
the frozen rules, so the worker count leaves headroom. CPU
only. No outer or test data: the launcher refuses a data root that exposes
`test_batch`, and the screen module has no evaluate path.

## Rationale

- **Unit = training seed.** The arms within a seed share initialization,
  seed body and every minibatch, so they are repeated measures. 48 seeds give
  48 observations, not 144.
- **Late-epoch mean.** The pilot showed single-epoch swings of up to
  0.47 nats. Declaring the late-epoch mean now removes the "pick the horizon
  where the gap is widest" degree of freedom.
- **Fixed budget, not a target power.** The across-seed spread is unknown:
  the pilot measured within-trajectory noise, not between-unit `sd_d`. Sizing
  from one seed would be the pilot-variance trap. So the fleet is fixed by
  budget, the precision criterion is stated in advance, and the MDE is
  reported whatever the outcome. At n = 48, an observed `sd_d` of 0.1 nats
  gives a half-width of ≈ 0.033 and an MDE of ≈ 0.046.
- **What the result does not cover.** One fixed data sample (data seed
  20261004), one host, one seed type, CPU. Inference covers training
  randomness only.

## Pre-launch amendment

The first committed plan (`d640434`) required *both* contrasts to be precise
for the gate. A review before launch pointed out that this would read a noisy
static comparator as a failing instrument, contrary to PDR-0043's own
definition of the gate. So the gate was re-scoped to the no-op contrast, and
`static_comparison_credible` was added as its own criterion. No confirmatory
unit had run when this was changed. The change is recorded in the plan's
`deviations` field. The exploratory timing unit is archived at
`docs/results/2026-10-08-bounded-screen-exploratory-seed7/`.

## Reversal trigger

Any change to the frozen plan after launch is an amendment. The analysis
refuses to run if the plan file's hash differs from the one recorded at
launch. If more than 4 units fail, the verdict is instrument failure, and the
fix is a new pre-registration, not a re-run.

## Source note (2026-10-08, systemic defect flush)

"5 min 50 s" is the shell's `time` for the whole exploratory timing run.
The archived per-epoch `wall_s` values in
`docs/results/2026-10-08-bounded-screen-exploratory-seed7/training.jsonl`
sum to 337.5 s; scoring and setup account for the remainder.
