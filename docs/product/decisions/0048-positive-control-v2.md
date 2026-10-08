# PDR-0048 — Positive control v2: replicate the deficit on fresh seeds, with graft divergence recorded rather than fatal

Date: 2026-10-08   Status: accepted   Author: Claude (session 17)
Owner sign-off: within the grant (run authorization; PDR-0040 carriage).
On 2026-10-08 the owner directed: "you're authorised to execute the study
as soon as its ready".
Related: PDR-0046, PDR-0047, plan
[`positive-control-v2`](../../prereg/positive-control-v2.json),
`simic-de847e9f94` (runner fixes), `simic-75be93e372` (lifecycle
instability)

## Context

`positive-control-v1` read `instrument_failure`, but not because of its own
question. The graft arm diverged in 12 of 48 units, and the runner aborted
those units. Since then:

- the runner records any arm's divergence as a measured outcome;
- every non-finite detector is covered (objective, gradient and scoring);
- the analysis enforces unit identity, a finish gate and a launch gate;
- each plan must declare a diverged-arm policy.

v1's exploratory 48-unit estimate was −0.159 [−0.187, −0.131]. That
suggests the deficit is real, but it is not a pre-registered answer.

## The call

Run `positive-control-v2`:

- the same question, configuration, floor (δ_pc = 0.10) and reading rule as
  v1;
- 48 fresh seeds, 2101–2148, excluding v1's seeds and the reproduction seeds
  6001–6016;
- the scheduled arm sealed, values *and* status, so its divergence cannot
  fail a unit;
- `diverged_arm_policy: fail_unit` for the contrast arms only (neither
  diverged in v1).

**No graft study is linked.** The graft lifecycle is unstable on this host
(`simic-75be93e372`), so any graft study waits for a pre-registered
lifecycle fix.

**Sizing.** The planning sd is 0.117, the 95% upper confidence limit on v1's
exploratory spread. Only the sd is borrowed, not the effect. The simulated
pass probability is 0.80 at a true benefit of 0.148, and 0.93 at v1's
exploratory 0.159.

**Budget:** about 5 CPU-hours on 8 workers, roughly 45 minutes.

## Runbook (pre-launch review F3)

**Commit, launch and analyze in one sitting.** Do not commit while the
fleet runs, and do not commit between launch and analysis:

- each unit records the git commit it trained under, and the analysis
  requires it to equal the launch commit;
- `verify_run` recomputes the experiment source, `pyproject.toml`,
  `uv.lock` and the runtime identity at analysis time.

Any commit, edit, upgrade or reboot in that window fails units wholesale.
`runs/` is gitignored, so the screen root itself is safe.

## Pre-launch review amendments

A Fable statistical review returned **GO with amendments**. All are plan
text; no code changed:

- **F1:** a precise but inconclusive interval no longer stops the line.
- **F2:** the predictions now carry simulated reading probabilities.
  `below_floor` has a 7–48% chance across the table and is not a failed
  replication.
- **F3:** the runbook above.
- **F4:** the seal text says what verification actually touches.
- **F5:** the exclusion and disclosure wording is corrected, and the
  sensitivity table is restored.

## Rationale

A positive control is cheap, and the deficit is the foundation for every
later graft question on this host. v1's exploratory estimate deserves a
confirmatory replication rather than a promotion. This run is also the
first at-scale exercise of the hardened divergence, identity and finish-gate
machinery.

## Reversal trigger

Any change to the plan after launch is an amendment, and the analysis
refuses a changed plan or a changed analysis module. If v2 reads anything
other than `control_passes`, v1's exploratory estimate failed to replicate,
and the reading's own consequence applies.
