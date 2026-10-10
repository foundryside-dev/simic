# Fleet C1 pilot — 2026-10-10

**A pilot: read for spread and arm stability only. It makes no claim.** The plan carries
`study.pilot: true`, so its analysis cannot produce a reading
([plan](../prereg/fleet-c1-pilot.json), [PDR-0057](../product/decisions/0057-controller-training-pathway.md)).

## What ran

| Item | Value |
|---|---|
| Seeds | 9401–9424, outside every fleet range |
| Hosts | `under_normalized`, `channel_starved`, `no_spatial_mix`, `mild` |
| Arms per host and seed | no growth; the designed graft after epoch 1; static; uniform scale-up at 1.1×, 1.25×, 1.5×, 2.0× |
| Source | Commit `670d798`, launched from a clean detached worktree, both GPUs, niced |
| Time | 2026-10-10 12:39:55 AEDT, about one hour; 24 of 24 seeds exited cleanly |
| Analysis | Run once from the snapshot: `instrument: ok`, `c1: pilot_no_reading` |
| Evidence | [`2026-10-10-fleet-c1-pilot/`](2026-10-10-fleet-c1-pilot/): report, launch records, per-arm summary table |

## What it was for

**Stability.** No arm diverged in 672 runs, so the comparators are stable at this scale.

**Spreads, for sizing.** Per-seed graft − scale-up at 1.25×:

| Host | sd |
|---|---:|
| `under_normalized` | 0.088 |
| `mild` | 0.119 |
| `channel_starved` | 0.086 |
| `no_spatial_mix` | 0.084 |

The committed [sizing script](../prereg/fleet-c1-sizing.py.txt) resamples these differences.
At a true difference of 0, it gives these powers for the G1 step on the co-primary hosts, at the
sd's 80% upper limit:

| Seeds | `under_normalized` 1.25× | `under_normalized` 2× | `mild` 1.25× | `mild` 2× |
|---|---:|---:|---:|---:|
| 192 | 0.26 | 0.33 | 0.39 | 0.41 |
| 576 | 0.75 | 0.85 | 0.91 | 0.76 |
| 768 | 0.88 | 0.91 | 0.95 | 0.90 |

Fleet C1 is sized at 768 seeds.

## Observations, not a reading

These are 24-seed estimates, liable to the winner's curse. They are recorded so the confirmatory
fleet can be compared with them, and they decide nothing.
- On `under_normalized`, the graft was ahead of every uniform scale-up: graft − scale-up
  −0.091 at 1.25× and −0.075 at 2×. Static was still ahead of the graft (+0.067).
- Only `under_normalized` showed a repairable deficit: static − no growth −0.166 there, and
  within ±0.02 of zero on the other three hosts. If the fleet confirms this, Fleet A's
  four-host design fails its own screen, and the rebuild-or-stop decision goes to John.
- The cost price from the pilot: λ ≈ 0.036 nats per doubling of parameters.
