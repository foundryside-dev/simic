# Fleet C1-S pre-flight check — 2026-10-10

**Result: ready to launch, on `af46997`, as soon as Fleet C1 finishes and before Fleet C1's own
analysis.** Fleet C1-S re-reads Fleet C1's deficit screen on the three BatchNorm hosts with the
static arm born at τ (`simic-e3803e8200`; John's choice and the rules are in the PDR-0057
amendment of 2026-10-10; [plan](../prereg/fleet-c1s.json)).

| Check | Result | Evidence |
|---|---|---|
| Plan pinned to Fleet C1 | Pass | Same seeds (10001–10768), config, data and screen criteria as [`fleet-c1.json`](../prereg/fleet-c1.json), enforced at load; hosts exactly the three BatchNorm hosts; every module the arm and the reading run through pinned by hash; a test pins the plan |
| Reviews | Pass | PyTorch and statistics reviews, both "endorse with changes"; every change taken in `af46997` (listed in that commit and in the amendment) |
| The corrected arm | Pass | Born at τ on every host: realised ratio 0.0500 on CIFAR for all four hosts and three seeds, against 0.0013–0.0018 for the registered arm on the BatchNorm hosts (Fleet C1 pilot). On `under_normalized` it equals the registered arm bit for bit (CPU test and GPU pairing) |
| Dry run on GPU, twice | **Pass** | Seeds 9903–9905, every row: `arms.jsonl` byte-identical between the two runs ([hashes](2026-10-10-fleet-c1s-preflight/arms-sha256.txt)); both analyses `instrument: ok`, reports equal apart from their timestamps; no failed units ([c](2026-10-10-fleet-c1s-preflight/dryrun-c/), [d](2026-10-10-fleet-c1s-preflight/dryrun-d/)) |
| Pairing and identity on GPU | Pass | Against the Fleet C1 dry run, which ran the frozen path at `1e37d4a`: re-trained no-growth and the control's corrected arm equal its records bit for bit on every seed; every corrected arm starts from its static arm's start (birth hashes, future, data). So the pairing holds across commits and across the frozen and fast paths |
| The review revision changed no record | Pass | `arms.jsonl` from `5cc456f` ([rev1](2026-10-10-fleet-c1s-preflight/rev1-5cc456f/)) and `af46997` are byte-identical: the fixes add checks, not training |
| Tests | Pass | 32 C1-S tests, 15 for the corrected arm, 2 for the tables; full suite on `af46997`: 630 passed, run in the worktree |
| Clean launch tree | Pass | A detached worktree at `af46997` (`/home/john/simic-worktrees/fleet-c1s`), clean |

**Order.** A confirmatory launch needs Fleet C1's `launch-finished.json` and is refused once
Fleet C1's `c1_report.json` exists. So, when Fleet C1 finishes:

1. launch Fleet C1-S;
2. analyse Fleet C1 once, from its snapshot (commands in the
   [Fleet C1 pre-flight](2026-10-10-fleet-c1-preflight.md));
3. analyse Fleet C1-S once when it finishes;
4. render the checkpoint tables:
   `python -m experiments.c1_tables <fleet-c1>/c1_report.json <fleet-c1s>/c1s_report.json`.

**Launch** (from the worktree):

```bash
cd /home/john/simic-worktrees/fleet-c1s && nice -n 19 env OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /home/john/simic/.venv/bin/python -B -m experiments.c1s_study launch --root runs/fleet-c1s --plan docs/prereg/fleet-c1s.json --data-root /home/john/simic/runs/cifar-fit-only --workers 2
```

**Resume** after an interruption: the same command with `--resume`, same worktree and commit.

**Analyse once** when its `launch-finished.json` exists:

```bash
cd /home/john/simic-worktrees/fleet-c1s/runs/fleet-c1s/src && PYTHONPATH=$PWD:$PWD/src /home/john/simic/.venv/bin/python -B -m experiments.c1s_study analyze --root /home/john/simic-worktrees/fleet-c1s/runs/fleet-c1s --plan /home/john/simic-worktrees/fleet-c1s/docs/prereg/fleet-c1s.json
```

**Cost.** About 3–4 hours on two GPUs. The dry run's seeds, all pairing seeds with seven rows
each, took about 73 s while sharing the GPUs with Fleet C1. The other 720 seeds train three rows.

**Not read.** The dry run's screen numbers on these three pre-flight seeds were not read (the
plan's acceptance rule). No Fleet C1 unit output has been opened.
