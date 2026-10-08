# Current State — Simic        Checkpoint: 2026-10-08 (session 17, second checkpoint)

## Who owns this now
Claude, since 2026-10-08 (PDR-0040): *"you have carriage to bring simic to
green."* Reserved to John:
- vision changes;
- tags, releases and publication;
- GPU or paid campaigns;
- opening outer/test data;
- deleting run data.

## Where the experiments stand (2026-10-08, end of session 17)
- **Rung 1, the instrument resolves:** met (screen v1, PDR-0045). The graft
  earned nothing on `mild`.
- **Rung 2, a repairable deficit exists:** met as a question, not at the
  pre-registered floor.
  - `positive-control-v1` read `instrument_failure`. The graft arm diverged in
    12/48 units, and the runner aborted those units. Root-caused (PDR-0047)
    and fixed in the runner.
  - `positive-control-v2` (fresh seeds) read **`control_fails_below_floor`**:
    static − no growth −0.119 [−0.151, −0.088], 42/47 finite pairs. The
    estimate exceeds 0.10; a benefit ≥ 0.10 is **not established**. That is
    not "below". Seed 2142's static failure is a separate host-edge
    mechanism.
  - PDR-0049 (**proposed**) applies that reading: no further positive-control
    runs, the next floor set in the graft redesign, and the line continues
    through the lifecycle fix.
- **Rung 3, does a graft capture the deficit:** unblocked. The lifecycle
  fix is validated.
  - Lifecycle v2 (a per-step trust-curvature clamp, `bounded_comparison.py`
    `ScaleAwareSlot`) read **`accepted`** in a pre-registered GPU study
    ([PDR-0051](decisions/0051-lifecycle-v2-validation.md),
    [result](../results/2026-10-08-lifecycle-v2-validation.md)).
  - On `under_normalized`, v1's graft diverged in 6/24 units with `norm` and
    8/24 with `conv_heavy`; v2's diverged in 0/48 on the same seeds.
  - Every v1 divergence crossed the derived limit c*, and v2 was identical
    to v1 where v1 was safe.
  - Descriptive, not a reading: the stable v2 graft beat no growth by 0.068
    (`norm`) and 0.054 (`conv_heavy`), about 40% of static capacity's gain.
  - Static-arm host instability is separate: 2/72 static `norm` arms on
    this host (`simic-9c5c3a2acf`).

## The bets now (PDR-0050)
1. **The bounded ladder.** Rung 3 is next: a graft-capture v2 study on
   lifecycle v2, covering `norm` and `conv_heavy`. Its floor is set from the
   measured deficit, and it must declare its treatment of
   `simic-9c5c3a2acf`. GPU is authorised for an exclusive window of about
   a week from 2026-10-08.
2. **HLD programme / Phase A:** moved to Later. It is pulled by rung 5.

## Green status (PDR-0040 guardrail)
- **`main` carries all accepted work:** yes. Lifecycle v2, the GPU profile,
  immutable snapshots and the validation study merged as PR #30
  (`9c5c63c`). Earlier work merged as PRs #20, #21, #26, #27, #28 and #29.
- **Full `tests/` suite:** 391 passed at the source state of `a2d1062`.
  Since then only plan, result and doc text has changed.
- **No configured tool points at a missing binary:** yes (PDR-0042).
- **Every cited tracker ID resolves:** enforced by
  `tests/unit/test_doc_references.py`.
- **This file describes reality:** as of this checkpoint.

## DECISION QUEUE
The owner answered all three on 2026-10-08:
- PDR-0049 is ratified;
- the ladder is the plan, and Phase A moves to Later (PDR-0050);
- GPU is approved for an exclusive window (PDR-0050).

Outer evaluation stays owner-gated.

**For Claude, now:**
- pre-register graft-capture v2 (rung 3): a full-sample contrast with the
  failure rate reported apart, a host-instability policy, GPU, and a
  real-configuration dry run first;
- review it, then run it.

## Parked, with re-entry conditions
- **Kernel demo campaign.** Its items depend on the parking issue
  `simic-ae339f0555`. Re-entry: an explicit DECIDE recorded as a PDR.
- **Learned structural timing.** Only after a round-2 graft earns its cost.

## Session 17 did (both checkpoints)
- Took over from Codex (PDR-0040).
- Lifted the pilot cap and ran the pilot (PDR-0041).
- Retired Legis, Wardline and Warpline (PDR-0042). An independent review of
  that change found that it had deleted 14 real runtime-contract tests. They
  are restored, and PDR-0042 carries a correction.
- Re-based the roadmap (PDR-0043).
- Pre-registered the screen (PDR-0044). It was amended once before launch:
  review found the gate would have read a noisy static comparator as a failing
  instrument.
- Ran the screen and applied its reading (PDR-0045).
- Tracker:
  - `simic-dda0d0188c`, `simic-7486bc6929`, `simic-6f4f111ec8` and
    `simic-e2f56cfbae` are closed;
  - `simic-f73351380d`, `simic-ae339f0555` and `simic-2035316005` are open;
  - 30 HLD/Phase-A items were unblocked by the gate, and 5 kernel-demo items
    were re-parked.

## Local-only state worth knowing
- Study run roots (local only; manifests, checkpoints and sealed stdout): `runs/positive-control-v1/`, `runs/positive-control-v2/`, `runs/explore-deficit-2026-10-08/`. Screen units: `runs/bounded-screen-v1/`, holding the per-unit manifests and
  144 checkpoints. They are pinned by the archived `complete.json` files.
  **Do not change `experiments/bounded_comparison.py`, `bounded_data.py`,
  `kernel_demo.py`, `__init__.py`, `pyproject.toml` or `uv.lock` before
  re-analysing them**: `verify_run` refuses on source drift.
- Pilot checkpoints: `runs/bounded-pilot-2026-10-08/`.
- Training-only CIFAR view: `runs/cifar-fit-only/`, which holds symlinks to
  the training batches and no `test_batch`. Every development run uses it.
- `.weft/{legis,wardline,warpline}/` and `.wardline/`: ignored local state
  from the retired tools. Left in place, because deleting it is
  owner-reserved.
- Codex's October 4 reports and preservation archive:
  `/home/john/Documents/Codex/2026-10-04/task-7/`.
