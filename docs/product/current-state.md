# Current State — Simic        Checkpoint: 2026-10-08 (session 17, second checkpoint)

## Who owns this now
Claude, since 2026-10-08 (PDR-0040): *"you have carriage to bring simic to
green."* Reserved to John:
- vision changes;
- tags, releases and publication;
- GPU or paid campaigns;
- opening outer/test data;
- deleting run data.

## Milestone reached this session
**The PDR-0043 gate closed with a measured answer (PDR-0045).** The
pre-registered bounded screen ran 48 paired units on CIFAR development data:
CPU, 5.2 CPU-hours measured, analysed once from clean commit `f5aeda2`. The reading
is **`reopen_no_value`**:

- **The paired instrument resolves.** Scheduled − no growth is bounded to
  ±0.018 nats, against a 0.05-nat floor. This is the first measured
  criterion-18-shaped reading in the programme. It covers resolution only.
- **The scheduled graft earns nothing at this scale.**
  - Against no growth: +0.002 [−0.017, +0.020].
  - Against static capacity: −0.016 [−0.045, +0.013].
  - Both are equivalent within the floor, and the graft costs 5% more
    optimizer work.
- **Static capacity is flat against no growth too, at a borderline
  margin.** The host is far from fitting its training data, so this is not
  "no deficit". It means that +6% parameters at this slot, within ten epochs,
  changes nothing (narrowed after the audit). Note also that "resolves" is
  a precision claim: a graft would need ~0.075 nats of true benefit for an
  80% chance of a progress reading.

Write-up: `docs/results/2026-10-08-bounded-screen-v1.md`, with all per-unit
evidence archived beside it.

## The bets now (roadmap Now)
1. **Bounded comparison, round 2** (`simic-f73351380d`): find a configuration
   where added capacity measurably helps *before* asking whether a graft
   captures it.
   - Pre-register a positive control: static capacity must beat no growth
     beyond δ in the chosen configuration.
   - Candidates: Esper's degenerate-architecture fixtures (~10%→~40%
     headroom). They are somewhere in the esper archives under
     `/mnt/data/archive/`, but a quick search of esper-lite did not find them,
     so locate them before shaping. The other candidate is an
     under-provisioned `mild` host.
   - Reuse `experiments/bounded_screen.py`.
   - Per ADR-0018: do not enlarge the controller.
2. **HLD programme resumed: design hardening into Phase A** (PDR-0043/0045).
   - Start with the ~10 contract-blocking items, led by `simic-0bf2c40dec`.
   - The burn-down is live again, at 31 open / 23 closed, un-dated.

## Green status (PDR-0040 guardrail)
- **`main` carries all accepted work:** yes once the `bounded-screen` PR
  merges. This session's earlier work merged as PR #20.
- **Full `tests/` suite:** recorded in the merge PR for this branch. The
  last recorded result on `main` was 190 passed in 7m31s. Since then the
  branch adds 14 restored contract tests and 14 screen tests.
- **No configured tool points at a missing binary:** yes (PDR-0042).
- **This file describes reality:** as of this checkpoint.

## DECISION QUEUE
**For John (owner-gated):**
- **Q1 — Outer evaluation.** Nothing needs it yet. The screen was
  development-only, and the next round should be too.

**For Claude, within the grant, in order:**
1. Shape round 2 (`simic-f73351380d`). Choose the deficit configuration with
   a cheap exploratory probe, then freeze a positive-control plan as a PDR.
2. Start Phase A contract work at `simic-0bf2c40dec`.
3. When Wardline returns: `simic-2035316005`.

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
- Screen units: `runs/bounded-screen-v1/`, holding the per-unit manifests and
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
