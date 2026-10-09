# Atlas G0 golden check, 2026-10-09 (PDR-0057, G0 item 3)

**Result: pass.** The atlas fork core reproduces rung 4's GPU records bitwise, wall time
aside, on seeds 8001–8008, all six cells (T0, T1, T2, T3, T5 and H20), both the
no_growth and the scheduled arm.

- One 10-epoch trunk per seed with decision points 0, 1, 2, 3 and 5, and a `norm` fork at
  each. One 20-epoch trunk with a fork at 2.
- Reference: `runs/rung4-timing-horizon/units/seed-*/{T0..T5,H20}/training.jsonl`
  (rung-4 fleet, snapshot of `991dcdc`).
- Ran on nyx, one process per GPU (`CUDA_VISIBLE_DEVICES=0` seeds 8001–8004, `=1` seeds
  8005–8008), the same SKU, driver and build as rung 4.
- Source: the working tree on branch `controller-pathway` from main `6d38c81`, before
  commit. The files that ran are byte-identical to the committed ones:

| File | sha256 |
|---|---|
| `experiments/atlas.py` | `200b0b3baa1e90f75909dac23b83d3129c31cc7c37e170541b309529d51f3b02` |
| `experiments/atlas_golden.py` | `ec4c467d3f15188a41287bc56974ec209946f2423779781c29959e9f6cc9513a` |

Command (repeat per GPU and seed list):

```bash
CUDA_VISIBLE_DEVICES=0 .venv/bin/python -B -m experiments.atlas_golden --root runs/rung4-timing-horizon --data-root runs/cifar-fit-only --seeds 8001 8002 8003 8004 --out <json>
```
