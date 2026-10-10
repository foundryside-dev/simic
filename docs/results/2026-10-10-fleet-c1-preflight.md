# Fleet C1 pre-flight check — 2026-10-10

**Result: ready to launch, on `1f58080`.** Every check below passed first on `1e37d4a`; the
exact-records speed tier (`1f58080`) then passed the same checks with identical records and is
about 1.25× faster, so it is the launch commit. The launch waits only for John's go (he asked to
hold it until nyx is free).

**Speed tier, `1f58080`** (atlas train and score with fewer host–device syncs; the frozen runner
is untouched):
- the GPU golden check reproduces rung 4 bitwise on seeds 8001–8008, every cell, no-growth,
  graft and static arms ([reports](2026-10-10-fleet-c1-preflight/fast-path/));
- a dry run on `1f58080` gives `arms.jsonl` byte-identical to the frozen-path dry runs for all
  three seeds, every host and arm ([hashes](2026-10-10-fleet-c1-preflight/arms-sha256.txt));
- per seed 173–188 s against 218–230 s on the frozen path; the fleet drops from about 31 hours
  to about 20;
- the full test suite passes on `1f58080` (581 tests).

| Check | Result | Evidence |
|---|---|---|
| Plan pinned and reviewed | Pass | [`fleet-c1.json`](../prereg/fleet-c1.json): 768 seeds 10001–10768, signed design (PDR-0057 G1), caps 2.5% below the 10% trim; a test pins it to the PDR and to fresh seeds |
| Sizing justified | Pass | [Pilot](2026-10-10-fleet-c1-pilot.md) and [sizing script](../prereg/fleet-c1-sizing.py.txt): power 0.88–0.95 at a true difference of 0 |
| Module reviewed | Pass | Code and statistics reviews of `experiments/c1_study.py`, all findings fixed before the pilot |
| Dry run, every host and arm, twice on GPU | **Pass** | Seeds 9903–9905, 4 hosts × 7 arms each: every `arms.jsonl` byte-identical between two runs ([hashes](2026-10-10-fleet-c1-preflight/arms-sha256.txt)); both analyses `instrument: ok`, reports equal apart from their timestamps; 0 divergences |
| Arms reproduce the instrument | Pass | The atlas reproduces rung 4's GPU records bitwise, no-growth, graft and static arms ([golden](2026-10-09-atlas-g0-golden/README.md)) |
| Co-tenancy | Not needed | Fleets run one process per GPU; four per GPU was shown bitwise anyway ([co-tenancy](2026-10-09-atlas-g0-cotenancy/README.md)) |
| Data | Pass | Source files match the plan's pins; no test batch in view of the data root |
| Clean launch tree | Pass | A detached worktree at `1f58080` (`/home/john/simic-worktrees/fleet-c1`), clean; the main checkout carries an uncommitted filigree tooling update that is not ours |
| Disk | Pass | 575 GB free; the fleet needs about 0.4 GB |
| GPUs | Pass | Both RTX 4060 Ti, driver 580.178.04, 55–68 °C; a unit uses about 450 MB of 16 GB |
| Analysis path | Pass | Analyse-once from the snapshot ran end to end on the pilot and both dry runs |

**Cost.** About 20 hours on two GPUs at the speed tier's pace (about 31 at the pilot's); a loaded
CPU stretches that. It runs under `nice -n 19`, two single-threaded workers.

**Launch** (from the worktree, when John gives the go):

```bash
cd /home/john/simic-worktrees/fleet-c1 && nice -n 19 env OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /home/john/simic/.venv/bin/python -B -m experiments.c1_study launch --root runs/fleet-c1 --plan docs/prereg/fleet-c1.json --data-root /home/john/simic/runs/cifar-fit-only --workers 2
```

**Resume** after an interruption: the same command with `--resume`, same worktree and commit (`1f58080`).

**First launch Fleet C1-S** ([its pre-flight](2026-10-10-fleet-c1s-preflight.md) has the command). A fresh C1-S launch is refused once this fleet's `c1_report.json` exists (PDR-0057 amendment, 2026-10-10).

**Then analyse once** when `launch-finished.json` exists:

```bash
cd /home/john/simic-worktrees/fleet-c1/runs/fleet-c1/src && PYTHONPATH=$PWD:$PWD/src /home/john/simic/.venv/bin/python -B -m experiments.c1_study analyze --root /home/john/simic-worktrees/fleet-c1/runs/fleet-c1 --plan /home/john/simic-worktrees/fleet-c1/docs/prereg/fleet-c1.json
```

At launch: a "Running now" entry in `current-state.md` and a tracker comment on
`simic-b8e492f669` (PDR-0056).
