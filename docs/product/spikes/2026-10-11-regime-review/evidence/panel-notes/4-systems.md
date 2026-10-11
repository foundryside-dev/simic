> These notes are the reconciler's (Claude's) condensed summaries of each reviewer's report, kept for provenance. They are not the reviewers' own text.

# Regime panel 4/5 systems/compute (plan-review-systems). Read published records only, stdlib Python.
F1 cost bases verified:
- Fitted: C1-S 3-arm units median 26.8 s, 7-arm 47.0 s → 5.06 s/arm + 11.6 s/unit fixed.
- Conservative 9.3 s = mean unit 27.9/3. Also 8.59 s/arm (5.958 GPU-h / 2,496) and C1 6.00 s (35.84 GPU-h / 21,504).
- The fitted model under-predicts C1 ~8%.
F2 steps drive cost, width barely:
- Rung 4 H20/T2 ratio 1.86, ≈0.66 s/arm-epoch + ~3 s fixed (frozen runner). The fast atlas runner was never timed beyond 10 epochs (extrapolation).
- GPU busy 24% of an epoch (atlas-g0-cotenancy/profile.json): CPU kernel-launch bound. 2× params ≈ 1.0–1.5× time (inferred; no per-arm timing, atlas.py:498 writes wall_s 0.0).
- Fixed: 11.6 s/unit; dev scoring ~15% of an epoch. Larger fit set ≤ its step ratio.
- Spread p95/median 1.07–1.30, max 1.6 (shared CPU). Budget with a 1.3× margin.
F3 compute-matched: records have installed params + param-steps; FLOPs never recorded (computable analytically). Wall time per unit only and favours width (overhead-bound): a machine property, not the method. Match in param-steps (PDR-0057 D7, 0057:105); report FLOPs alongside (a seed at a different stage has a different FLOP/param ratio); wall time for budgets only.
F4 zero-GPU findings (descriptive, unpaired across studies):
- Time beats width on under_normalized at matched 2× param-steps: no-growth 20 epochs (rung 4, n=768) late CE 1.3665 vs scale_x2 10 epochs (C1) 1.5847; Δ 0.218 (se 0.004). Cross-check: no-growth e9 is 1.568 in C1, 1.562 in rung 4.
- λ's fitted domain is width at 10 epochs/4,096; horizon multiples are outside it (scopes λ, doesn't change it).
- channel_starved designed seed 1.46×: static 1.3207 vs scale_x1.5 (1.53×) 1.3075.
F5: ~6/11 sub-questions answerable from records: under_normalized step-bound; BN gap at 10 epochs; param-matched width comparators; time vs width on under_normalized; ≤1.10× injection reach (C1 1.1× arms moved late CE +0.003 to −0.011 vs 0.05); analytic FLOPs. NOT answerable without GPU: BN beyond 10 epochs, lr schedule, fit size, per-arm wall, emergent bottlenecks, L7.
COST TABLE (GPU-h per 100 seeds per arm per host; fitted 0.506 s/arm-epoch, conservative 0.93; ×1.0–1.5 for a 2× arm; + 0.032 h/100 units fixed):
  10ep/4,096 (1,280 steps): 0.14 / 0.26
  20ep (2,560): 0.28 / 0.52
  40ep (5,120): 0.56 / 1.03
  cosine 10+20+40 separate (8,960): 0.98 / 1.81
  10ep/8,192 (2,560): ≤0.28 / ≤0.52
  10ep/16,384 (5,120): ≤0.56 / ≤1.03
  10ep/44,992 (14,060): ≤1.54 / ≤2.84
Resolution: paired late-CE sd 0.08–0.11 in C1; at sd 0.10, 95% half-width ±0.040 (24 seeds), ±0.028 (48), ±0.020 (100). Hosts share each seed's minibatch order, so no pooling. Horizon-change contrasts are much noisier (rung-4 static-gain change sd 0.38).
EXPERIMENTS (all descriptive; 0.05 reference only; none reach L1/L7):
- R0 (0 GPU, first): F3/F4 tables; analytic FLOPs per arm; a 40-epoch sd prior from rung 4.
- R1 horizon ladder: no-growth + scale_x2, constant lr, 40 epochs, 3 BN hosts.
  - Readouts at 10/20/40 nest (each epoch's data order drawn independently, bounded_comparison.py:600-617), giving two param-step-matched time-vs-width contrasts free.
  - 24-seed pilot, +24 only if the paired sd at 40 epochs ≤0.12.
  - Option for John: reuse C1 seeds for a free replay check of epochs 0–9 (against the fleet-c1.json seed-range disclosure; compare per-epoch host hashes, not future_sha256; confirm the hash fields).
  - 48 seeds: 1.8–2.2 GPU-h fitted, 3.0–3.7 conservative; cap 4; ~2.5 min/unit.
  - Stops: cap; >25% no-growth diverge; replay mismatch; >2 failed units.
  - Outcomes: (a) no-growth improves ≥0.05 10→40 and the 2× UB <0.05 → step-bound, C at 10 epochs unsupported; (b) the 2× effect ≥0.05 at 40 → re-pose the host question at that horizon (4× per-arm cost); (c) dev flat/rising while the gap widens → R3; (d) high sd/divergence → R2.
- R2 annealed: cosine 0.05→0, no-growth + 2× only (graft/static excluded: constant lr is load-bearing for germination, kernel_demo.py:877-881). lr set per step as a pure function of the global step, with a bitwise no-op check at constant lr. 10 and 20 epochs; 48 seeds 1.4–1.7 / 2.2–2.8; cap 3.
  - Outcomes: endpoint ≥0.05 better or sd halves → adopt annealing (~4× fewer seeds); 2× ≥0.05 → capacity question under annealing; neither → optimisation not the limit.
- R3 data vs steps: 16,384×10 epochs = 5,120 steps = R1's 4,096×40. Fit sets nest (bounded_data.py:210). no-growth + 2×; 48 seeds ≤1.8–2.2 / ≤3.0–3.7; cap 4. Outcomes: 16k beats 4k@40ep by ≥0.05 → data-bound; 2× ≥0.05 → re-pose with more data. The 44,992 variant only at 24 seeds × 1 host (0.9 / 1.6).
- Ordering: R0 → R1 pilot → rest of R1 → (high sd: R2 first) R2/R3. Worst case ≤11 GPU-h.
- Cap/abandon: no new unit; terminal marker; report only the contiguous completed seed prefix, descriptively; no outcome decided; back to John. (Disagrees with §8 "no reading" for DESCRIPTIVE studies: John's choice.)
- CPU-only: ~123 s per 10-epoch arm per core (~24× slower), competes with Sultai's CPU, can't pair with GPU records. Use only if the GPUs are unavailable for weeks.
PREREQS FOR ANY GPU EXPERIMENT:
1. GPU placement: range(device_count()) (bounded_screen 198-201; c1_study 51) and child CVD replaced (c1_study 536-537,556; c1s 428,448; timing_study 457,480). A single-card grant lands on card 0. BLOCKS any single-card grant.
2. Occupancy ledger (start/end records; resumed log 0 s, killed nothing, c1_study 546-558; no per-arm time). BLOCKS any cap.
3. Per-unit cap projection + terminal marker.
4. Co-tenancy check by GPU UUID; drain at a unit boundary. Co-tenancy is bitwise-safe (5 processes reproduced rung 4) but time-slices at 99%, so it takes time from Sultai.
5. Kill the process group (setsid).
6. nice 19; ≤1 worker per granted card.
7. Resume: same commit, clean tree; pinned worktree; declared max pause.
8. John's explicit grant (card, window, cap); PDR-0056 launch record.
DISAGREES:
- §11 "20 epochs ~2×": one 40-epoch arm gives 10/20/40 for 4×; cosine "~1×" only per horizon (doesn't nest).
- Cosine is engineering, not a switch.
- "45k" fails validation (bounded_data.py:71-72); max 44,992; 11× is an upper bound.
- "Per-arm time scales with steps" is not true for width; wall time is not a matching unit.
- §7's conservative basis is ~1.7× fitted for long units: fine for caps, not estimates.
- Capped descriptive study → report the prefix (John's choice).
