# PDR-0041 — Pilot artifact cap lifted; the first real CIFAR development reading

Date: 2026-10-08   Status: accepted   Author: Claude (session 17)
Owner sign-off: "lift the cap, the server has hardware its an artificial
constraint" (2026-10-08).
Related: ADR-0018, `simic-e2f56cfbae` (closed), `simic-dda0d0188c`,
`simic-7486bc6929`, result note
`docs/results/2026-10-08-bounded-cpu-pilot.md`

## Context

On 2026-10-04 John approved a single CPU-only development pilot for the
bounded comparison:

- seed 7, data seed 20261004;
- 1,024 fit and 256 development examples;
- three arms, ten epochs, batch 32;
- graft before epoch 2, stages K1/M2/F1.

The approval came with resource caps. Codex stopped before training because
one of them, an OS-hard 64 MiB aggregate output quota, could not be enforced
on this host (the systemd tmpfs probe failed with `226/NAMESPACE`).

## The call

The resource caps are withdrawn as preconditions. The scientific parameters
are unchanged, and so are the access constraints:
- no outer/test data;
- no download;
- no tuning or retry;
- CPU only, one thread.

The pilot ran on 2026-10-08 from clean commit `4186a9c`.

## Pre-committed reading, and what was read

The approved reading was whether each arm's final development CE is below
its initial CE. Failure to improve would mean diagnosis comes before any
progression.

| Arm | Initial → final dev CE | Decreased |
|---|---|:---:|
| No growth | 2.306 → 1.691 | yes |
| Static capacity | 2.306 → 1.605 | yes |
| Scheduled graft | 2.306 → 1.722 | yes |

**The answer is yes for all three arms.** The October 4 smoke's CE failure
came from its 128-example budget; it is not a defect in the pipeline. Static
capacity finished best on one seed, but the arm differences (at most 0.12 CE)
are smaller than a single epoch's swing within one arm (up to 0.47 CE after
epoch 4). Under the approval's own terms, a positive pilot "only informs a
separately approved, predeclared paired screen". That proposal is
`simic-7486bc6929`.

## Rationale

The cap protected against a failure mode, runaway output, that the runner's
design already excluded: it writes a fixed set of files and refuses to
overwrite. The cost of the cap was four days of stall, and the measured run
used 3% of it. Enforcing an unenforceable control by withholding the
experiment taught nothing.

## Reversal trigger

A future run's output or memory grows large enough to threaten the host. That
is plausible for a GPU campaign or a full-dataset sweep, not for this runner
at pilot scale. If it happens, size a cap for that run and enforce it with a
mechanism the host actually supports.
