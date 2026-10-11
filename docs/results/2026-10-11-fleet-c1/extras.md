## E1. Realised installed parameters, as a multiple of the host's no-growth arm

| Host | No growth | graft | static | scale_x1.1 | scale_x1.25 | scale_x1.5 | scale_x2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| under_normalized | 161,010 | 1.001 | 1.001 | 1.105 | 1.244 | 1.482 | 1.984 |
| channel_starved | 129,922 | 1.463 | 1.463 | 1.094 | 1.241 | 1.530 | 2.014 |
| no_spatial_mix | 116,626 | 1.037 | 1.037 | 1.102 | 1.229 | 1.460 | 1.990 |
| mild | 142,006 | 1.063 | 1.063 | 1.112 | 1.260 | 1.517 | 1.985 |

## E2. Arms that did not complete

- seed 10203, under_normalized, graft: diverged at epoch 3 step 74, stage blending, non-finite training objective; witness gain_min -1.605e+08, gain_max 113.7

## E3. under_normalized static arm against the earlier studies

Fleet C1: 0/768 did not complete; worst late CE among completed runs 2.013 (chance is ln 10 = 2.303).

| Comparison | Earlier | Fleet C1 | P(0 failures at the earlier rate) | One-sided Fisher p (earlier rate higher) |
|---|---:|---:|---:|---:|
| rung 4, 10 epochs (same config and arm) | 3/768 | 0/768 | 0.049 | 0.125 |
| all five studies, 10 epochs | 6/984 | 0/768 | 0.009 | 0.031 |

Pooled 10-epoch rate including Fleet C1: 6/1752 = 0.34% (95% Clopper-Pearson 0.13-0.74%).
