# Current State — Simic        Checkpoint: 2026-10-09 (session 17, rung 4 read)

## Who owns this now
Claude, since 2026-10-08 (PDR-0040): *"you have carriage to bring simic to
green."* Reserved to John:
- vision changes;
- tags, releases and publication;
- paid or off-nyx compute. Jobs on nyx need no permission (PDR-0056);
  every launched fleet is recorded under "Running now" below;
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
  - PDR-0049 (**accepted**) applies that reading: no further positive-control
    runs, the next floor set in the graft redesign, and the line continues
    through the lifecycle fix.
- **Rung 3, does a graft capture the deficit:** **met as a partial
  capture** (PDR-0052, [result](../results/2026-10-09-graft-capture-v2.md)).
  - Both sibling plans read `partial_capture`. The graft beats no growth
    with `norm` (−0.087) and with `conv_heavy` (−0.045). Static beats the
    graft in both: static wins at the declared cost.
  - Capture fractions: 0.60 [0.51, 0.72] with `norm`, 0.31 [0.19, 0.42]
    with `conv_heavy`.
  - The graft−static gap narrows toward the 10-epoch horizon, which is the
    rung-4 timing question.
  - Lifecycle v2 ([PDR-0051](decisions/0051-lifecycle-v2-validation.md),
    accepted) diverged in 0/192 runs here.
  - Static `norm` host instability is now 3/168 (`simic-9c5c3a2acf`).
- **Rung 4, does timing or horizon change the outcome:** **met,
  `lever_found`** (PDR-0055, [result](../results/2026-10-09-rung4-timing-horizon.md)).
  - Timing: grafting at epoch 0 beats epoch 3 by 0.051 nats
    [0.043, 0.059], margin 0.02. Robust on median, trimmed mean and sign.
  - Horizon: the graft − static gap shrinks by 0.101 [0.067, 0.136] at 20
    epochs, margin 0.05. Tail-sensitive: the median shrinkage is 0.067,
    and part of the mean comes from static runs degrading late.
  - At 20 epochs the graft ties static on the median seed. It never beat
    static at 10 epochs (T0: +0.019).
  - Seeds differ in timing preference beyond noise, but modestly. Timing
    alone leaves little for a learned controller.
  - Static degrades late at 20 epochs on 117/756 runs and diverged in
    12/768. Logged on `simic-9c5c3a2acf`.

## The bets now (PDR-0050)
1. **The bounded ladder.** Rung 4 is met (`lever_found`). Under PDR-0055
   the next step is a new owner-signed DECIDE that shapes what follows:
   rung 5, a horizon/host rung, or the controller pathway John asked for on
   2026-10-09 (see the decision queue). Compute on nyx needs no permission
   (PDR-0056).
2. **HLD programme / Phase A:** moved to Later. It is pulled by rung 5.

## Green status (PDR-0040 guardrail)
- **`main` carries all accepted work:** yes. Lifecycle v2, the GPU profile,
  immutable snapshots and the validation study merged as PR #30
  (`9c5c63c`). Earlier work merged as PRs #20, #21, #26, #27, #28 and #29.
- **Full `tests/` suite:** 417 passed at `37e5a5b`, the source state both
  rung-3 fleets ran from. Since then only result and doc text has changed.
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

**For John (2026-10-09):** the post-rung-4 DECIDE. John asked in
session for a "how to train your Tamiyo" pathway: the stages, gates,
transition criteria and work at each stage, then to start training. Claude
is drafting it as a proposed PDR with design spikes. The gates and stop
conditions in it are John's to sign (PDR-0053).

**For Claude, now:**
- close rung 4: reviews of the result note, PR;
- draft the controller pathway and its first stage.

**Running now** (PDR-0056: every fleet on nyx is listed here when
launched): nothing. The rung-4 fleet finished 2026-10-09 21:53 local,
4,608/4,608 runs clean; its data stay in `runs/rung4-timing-horizon/`.

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
