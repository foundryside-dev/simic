### Reading

- Instrument: `ok`; failed units 0, failed seeds 0.
- C1: `supported_at_bounded_scale`; on `mild`: `inconclusive`.
- Fleet A hosts, registered screen: ['under_normalized'].

### G1: graft against uniform scale-up

| Host | Role | Reading | m | Graft - scale-up, mean | Trimmed mean | Non-inferior | Divergence graft / comparator |
|---|---|---|---|---|---|---|---|
| under_normalized | co_primary | non_inferior | 1.25x | -0.080 (upper -0.071) | -0.082 (upper -0.074) | yes | 0.1% / 0.0% |
| under_normalized | co_primary | non_inferior | 1.5x | -0.076 (upper -0.066) | -0.075 (upper -0.067) | yes | 0.1% / 0.0% |
| under_normalized | co_primary | non_inferior | 2x | -0.071 (upper -0.061) | -0.072 (upper -0.063) | yes | 0.1% / 0.0% |
| channel_starved | exploratory | non_inferior | 1.25x | +0.010 (upper +0.018) | +0.009 (upper +0.017) | yes | 0.0% / 0.0% |
| channel_starved | exploratory | non_inferior | 1.5x | +0.014 (upper +0.022) | +0.013 (upper +0.021) | no | 0.0% / 0.0% |
| no_spatial_mix | exploratory | non_inferior | 1.25x | +0.002 (upper +0.008) | +0.001 (upper +0.008) | yes | 0.0% / 0.0% |
| no_spatial_mix | exploratory | non_inferior | 1.5x | +0.004 (upper +0.010) | +0.003 (upper +0.010) | yes | 0.0% / 0.0% |
| no_spatial_mix | exploratory | non_inferior | 2x | +0.018 (upper +0.025) | +0.017 (upper +0.024) | no | 0.0% / 0.0% |
| mild | co_primary | inconclusive | 1.25x | +0.012 (upper +0.020) | +0.011 (upper +0.018) | no | 0.0% / 0.0% |

### Deficit screen

| Host | Registered static gain [95%] | Divergence | Screen |
|---|---|---|---|
| under_normalized | +0.142 [+0.133, +0.151] | 0.0% | pass |
| channel_starved | -0.000 [-0.007, +0.007] | 0.0% | fail |
| no_spatial_mix | +0.020 [+0.014, +0.026] | 0.0% | fail |
| mild | +0.003 [-0.004, +0.010] | 0.0% | fail |

### Graft minus static (descriptive)

| Host | Graft - registered static [95%] |
|---|---|
| under_normalized | +0.046 [+0.037, +0.055] |
| channel_starved | +0.001 [-0.006, +0.008] |
| no_spatial_mix | +0.008 [+0.003, +0.014] |
| mild | +0.001 [-0.006, +0.008] |

### λ, the cost price

| Fit | Slope (nats per doubling) | λ |
|---|---|---|
| pooled | -0.0271 | +0.0271 |
| under_normalized | -0.0232 |  |
| channel_starved | -0.0318 |  |
| no_spatial_mix | -0.0296 |  |
| mild | -0.0233 |  |
| sensitivity (failures at ln 10) | -0.0271 | +0.0271 |

Excluded runs in the primary fit: 0.

### Divergences

| Host | Arm | Diverged | 95% (Clopper-Pearson) |
|---|---|---|---|
| under_normalized | graft | 1/768 | [0.0%, 0.7%] |
