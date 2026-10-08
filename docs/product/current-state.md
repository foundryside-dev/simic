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
    static − no growth −0.119 [−0.151, −0.088], 89% of units.
  - PDR-0049 (**proposed**) applies that reading: no further positive-control
    runs, the next floor set in the graft redesign, and the line continues
    through the lifecycle fix.
- **Rung 3, does a graft capture the deficit:** blocked. The graft lifecycle
  is numerically unstable on this host (`simic-75be93e372`; the trust-region
  curvature violates the kernel's comment-only bound). The kernel stability
  sweep left a concrete fix set on that issue.

## The bets now (roadmap Now; unchanged pending the owner's answer on Phase A)
1. **Bounded comparison, round 2 and beyond** (`simic-f73351380d`): the
   deficit is established; the graft lifecycle redesign is next
   (`simic-75be93e372`, PDR-0049 proposed).
2. **HLD programme, design hardening into Phase A** (PDR-0045): unblocked but
   not worked this session. Recommended back to Later (decision 2).

## Green status (PDR-0040 guardrail)
- **`main` carries all accepted work:** yes once this checkpoint's PR
  merges. This session's earlier work merged as PRs #20, #21, #26 and #27.
- **Full `tests/` suite:** 307 passed (8m19s) at `ac9237e`. Since then only
  plan and doc text has changed.
- **No configured tool points at a missing binary:** yes (PDR-0042).
- **Every cited tracker ID resolves:** enforced by
  `tests/unit/test_doc_references.py`.
- **This file describes reality:** as of this checkpoint.

## DECISION QUEUE — owner decisions, all pending
1. **Ratify PDR-0049 (continue the bounded line through a lifecycle
   redesign).** Recommended: yes. The deficit is real, and the graft
   instability has a concrete, reviewed fix set.
2. **Phase A back to Later, with the ladder as the plan** (asked earlier this
   session). Recommended: yes. Draft contracts only when a rung needs one.
   Until answered, the ladder takes precedence in practice and the roadmap is
   unchanged.
3. **GPU authorization for rung 4** (asked earlier). Recommended: approve as
   a bounded line item. Rungs 2–3 run on CPU.
4. **Outer evaluation** stays owner-gated. Nothing needs it yet.

**For Claude, once 1 is answered:** pre-register the lifecycle fix (a
scale-aware trust region, a frozen trust denominator, a separate gain lr,
host-edge stability), have it reviewed, test it on exploratory seeds, then
design graft-capture v2 with its floor set from the measured deficit.

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
