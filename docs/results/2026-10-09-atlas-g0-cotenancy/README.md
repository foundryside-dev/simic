# Atlas G0 item 1: co-tenancy and GPU profile, 2026-10-09 (PDR-0057)

**Co-tenancy: pass.** Four atlas golden processes shared GPU 0 (seeds 8001–8004) while one
ran alone on GPU 1 (seed 8005). All five reproduced rung 4's records bitwise, all six cells,
both arms ([reports](reports/)). Peak memory on the shared GPU was 1,789 MiB.

**Throughput: co-tenancy does not pay.**

| Setup | Seeds | Wall time |
|---|---:|---:|
| One process alone (GPU 1) | 1 | 60.5 s |
| Four processes sharing GPU 0 | 4 | 231–232 s each, 232 s in all |

Four seeds took 232 s together, against about 242 s for four 60.5 s runs in sequence: about
1.04×. The shared GPU showed 99% utilisation, so it was time-slicing, not idle. CPU on nyx is
shared with other work, so these figures are approximate.

**Why: the loop launches many tiny kernels.** One profiled training epoch (seed 8001,
`under_normalized`, no growth, epoch 1 after a warm-up) and one scoring pass:

| Pass | CUDA kernels | Host–device syncs | GPU kernel time |
|---|---:|---:|---:|
| Training epoch (128 steps) | 31,912 | 8,234 | 0.316 s |
| Dev scoring (5,000 examples) | 7,896 | 1,753 | 0.045 s |

That is about 249 kernels and 64 syncs per training step. Profiler overhead inflates wall time,
so wall times from the profile are not used.

**Consequence for PDR-0057.** Fleets stay at one process per GPU. The speed lever is fewer
kernels and syncs per step, the "exact-records" tier in spike S3 (stacked per-step syncs,
deferred epoch scalars, batched scoring, pre-augmented epochs), each gated on bitwise equality
with the current records. Script: [`g0_gpu_profile.py.txt`](g0_gpu_profile.py.txt).
