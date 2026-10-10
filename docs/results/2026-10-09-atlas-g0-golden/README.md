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

## Re-run after the code review (2026-10-09)

**Result: pass**, all eight seeds and six cells, bitwise. A PyTorch code review found
record-identity and lineage gaps (global RNG states and the replicate future were not in
the snapshot; a germination-epoch divergence lost its birth record; the runner's
end-state checks and initial scoring were missing). All were fixed and tested, and the
golden check was repeated on the fixed source:

| File | sha256 |
|---|---|
| `experiments/atlas.py` | `af5eb1b0bc4bba3a303fc322fa3005f6f4263b42799cfaff334703532d2cd200` |
| `experiments/atlas_golden.py` | `ec4c467d3f15188a41287bc56974ec209946f2423779781c29959e9f6cc9513a` |

Reports: [`rerun-after-review/`](rerun-after-review/).

## Final run, self-describing report (2026-10-09)

**Result: pass**, all eight seeds and six cells, both arms, bitwise. After a second
PyTorch review, the remaining runner end-of-run checks were ported and the report
was hardened: it now records the source hashes (runner files plus `atlas.py` and
`atlas_golden.py`), the runtime (GPU, CUDA, cuDNN, torch build), each reference
`training.jsonl` hash and the number of records compared per cell and arm. The report
is its own provenance: [`final/`](final/).

What the GPU runs show, and do not: reproduction of the instrument for
`under_normalized` × `norm` on GPU. The RNG-restore and divergence paths are proven
by CPU tests only, because seeds 8001–8008 had no ambient draws or divergences. BN hosts,
the other seed types and co-tenancy are not yet checked on GPU.

## Static arm (G0 item 6, 2026-10-10)

**Result: pass.** The atlas static arm (seed attached fully coupled at birth) reproduces
rung 4's static records bitwise on seeds 8001–8008, every cell, alongside the no-growth and
scheduled arms. The reports carry their own source hashes and record counts:
[`static-arm/`](static-arm/).
