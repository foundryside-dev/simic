> These notes are the reconciler's (Claude's) condensed summaries of each reviewer's report, kept for provenance. They are not the reviewers' own text.

# Regime panel 2/5 statistics (counterfactual-statistician). Inputs published (sha listed); scripts in scratchpad/stats-review/ (reanalysis.py 67cfc204…, extra.py 7a6c4ade…, check2.py 2ad50fa0…, out.txt, out-extra.txt). λ refit 0.02709 matches. All seeds already seen, so exploratory.
OBSERVED:
- O1: λ 0.0271 [0.0240, 0.0304] (seed bootstrap keeping arms together, 2,000 resamples); per-host 95% spans 0.016–0.038.
- O2: λ not constant within the regime: 0.019 at e5 → 0.029 at e9 (+0.010 [0.003, 0.017]).
- O3: the measured 1.1× uniform arm gains 0.003–0.011; every 95% UB ≤0.018.
- O4: 0.05 ≈ 3.6× [3.1, 4.3] uniform params (extrapolated past 2×); a 1.10× injection at the uniform price needs λ ≥0.364 (13×).
- O5: norm graft at 1.0008× gains 0.096 [0.091, 0.101], ~3,000× the uniform price per doubling.
- O6: the registered mean rule applied hypothetically to rung-4 H20 (seeds 8001–8768, under_normalized): static gain 0.030 [0.001, 0.058] (failures at ln 10), 0.045 [0.017, 0.072] completed-only, both <0.05; median 0.108, 10%-trimmed 0.083; the same seeds at 10 epochs 0.129. Sensitivity, not a reading.
- O7: at 20 epochs the static paired sd triples 0.133 → 0.400; cross-horizon within-seed r 0.21. n for ±0.01 rises 683 → ~6,200; at n=192 a true-0.04 pass rises 0.15 → 0.37–0.44; the LCB clause starts to bind (needs mean > 0.057).
- O8: the graft gain holds at 20 epochs: 0.087 (ln 10) / 0.093 completed, sd 0.12–0.14.
- O9: under_normalized train–dev gap widens +0.036 [0.028, 0.043] e3→e9 and +0.066 [0.059, 0.074] e9→e19 (78% of seeds); dev still falling e17–19 at −0.011 [−0.015, −0.008]/epoch.
- O10: all four C1 hosts still improving at e9 (no-growth dev −0.028 to −0.040/epoch over e7–9, CIs exclude 0); the per-seed slope of the 2× gain straddles 0 on every BN host.
- O11: BN per-seed spread is epoch-to-epoch noise. Cross-epoch r of the 2×−no-growth contrast and of no-growth CE is −0.08 to +0.09 (incl. non-adjacent pairs e4–e9, e5–e9); under_normalized 0.33–0.52. Persistent seed share on BN ~0–2%.
- O12: one-decision keep/cull with rollback (keep the graft at epoch d if its dev CE < no growth's) never beats the best fixed policy for d=2–6: worse on under_normalized (+0.010 to +0.023) and no_spatial_mix (+0.005), null on the other two. Caveats: dev used for decision and score (favours the rule); the best fixed policy chosen post hoc (disfavours it); one future per seed; the rule was fixed after seeing the published aggregates.
- O13: weak seed pairing for uniform arms: late-CE r with no growth 0.13 (2× on under_normalized), 0.47–0.50 BN; graft 0.64–0.79.
HYPOTHESES:
- H1: λ at 20 epochs > 0.0271 (O2 trend); no scale-up arm past e9, size unknown.
- H2: annealing cuts the BN paired sds several-fold (O11) and may change effect sizes.
- H3: O6 reflects static's late instability (117/756 late rise), not a vanished deficit.
- H4: BN per-seed headroom in this regime is noise no per-seed decision can use (O11, O12).
- A longer constant-lr horizon cuts both ways: bigger capacity contrasts (H1) vs a 3× noisier screen (O7).
TOPIC 3: uniform ≤1.10× cannot reach 0.05 here (O3); no plausible regime change closes a 13× gap (hypothesis). Targeted ≤1.10× can (O5), only where it supplies a function width doesn't. Bar reachability depends mainly on the deficit class, not the regime; capacity-class hosts are unlikely to confirm (hypothesis). Bar frozen.
TOPIC 2:
- Unit = seed (shared data order, augmentation, pinned sets); estimand conditional on the sets.
- Primary equal-steps Δ_S(m,R) = E[CE(graft) − CE(uniform m×)] under regime R, reporting the realised param and param-step multiples. Hardest comparator. A pass implies a pass at matched param-steps only if uniform curves never worsen with steps (O6 shows some do).
- Secondary matched param-steps Δ_C = CE(graft, H) − CE(uniform 2×, H/2), free under constant lr (earlier epochs of the same runs).
- FLOPs not recorded, and a stage-2 graft's FLOPs/param differ, so not primary without instrumentation.
- λ: 0.0271 stays frozen for PDR-0057, never carried to another regime. Each new regime cell has its own no-growth and uniform arms; the cell's λ is fitted and frozen before any intervention arm is read. Uniform-doubling equivalents only within ≤2×; beyond, "beats the largest multiple measured".
EXPERIMENTS (analysis plan v0.1, design only; plan JSON and analysis module hash-pinned before confirmatory seeds, C1-S pattern):
- E0 (no GPU, done above): reaches L7 only as a precondition, which came out negative (O12, H4).
- E1+E2 one fleet, two pre-specified families; fresh out-of-range seeds; dry run twice byte-identical; a 16-seed pilot outside the confirmatory range sets n (never analysed).
- E1 (designed hosts; no L1/L7): no-growth + 2× uniform on all 4 C1 hosts (no selection). Regimes C20 (20 epochs constant; C10 from e7–9 of the same run) and K10 (10 epochs cosine to 0).
  - Estimands: Δλ_R = λ_R − λ_C10 (two-arm, host-averaged per seed; C1 two-arm λ 0.0274); paired-sd ratio R vs C10.
  - Floor: Δλ = 0.023 (= 0.05 − 0.0271, where 2× would earn 0.05). NEW, declared before data, needs John's sign-off.
  - Tests: two-sided α 0.025 per regime (Bonferroni over 2), trimmed-mean companion. n = smallest of 192/256/384 with ≥0.8 power at the floor using the pilot sd's 80% UL; >384 → no launch, back to John. At sd(Δλ) 0.10 power 0.83 / 0.92 / 0.99. One fixed-n analysis, no interim look.
  - Stops: C10 must equal C1 bitwise on 10001–10016, else no reading; comparator >2.5% divergence → unstable; failures at ln 10; cost cap → no reading.
  - Gate: Δλ ≥0.023 with LB >0 → the current regime understates capacity; any future study moves to R (rung parameter, John). Both UBs <0.023 → the regime isn't the capacity limiter; D closes on step/optimisation-bound; data-bound stays untested. sd-ratio UB <0.7 (NEW, owner-gated) → recommend K10 as the measurement regime. Else inconclusive → John, stop on the menu.
- E2 (under_normalized only, chosen after C1; L2 only): graft T1 in C20 and K10 (graft under cosine never tested, so the 2.5% cap per cell); static in K10 only (C20 static already measured O6/O7).
  - G1's registered rule unchanged (margin 0.02; t and trimmed upper bounds; one-sided 0.0125 per regime).
  - Power at n=192, sd 0.2: true −0.07 → 1.00; −0.03 → 0.89; 0 → 0.20; +0.02 → 0.01.
  - Gate: passes both → C1 not a 10-epoch artefact; fails C20 with the gap shrinking 10→20 → C1 gets a horizon scope limit (erratum John's call). Static K10 descriptive (tests H3).
- BUDGET: 28 ten-epoch arm-equivalents per seed (assumes time ~ steps regardless of width; unverified). n=192: 13.9 (cons) / 8.2 (fitted) GPU-h; 256: 18.5 / 10.9; 384: 27.8 / 16.4. +~1.2 pilot, +~0.9 dry runs.
DISAGREES:
1. Rev 3 §6 "LCB never binds" is true only at 10 epochs (O7).
2. Rev 3 D4 bounds a ≤1.10× injection with λ, but λ prices uniform widening only; use the measured 1.1× arm (O3); O5 shows λ doesn't bound targeted gains.
3. Option D "horizon cheaper": put cosine first (1× cost; targets the BN variance O11; horizon at constant lr destabilises static O6/O7).
4. The BN gap across 768 seeds can't be answered from published data (train CE is in sealed records; only means were extracted).
5. Rev 3 §6's sd range treats seed spread as fixed; on BN hosts it is regime noise (O11), so sds for new classes are regime-dependent.
COULD NOT VERIFY: BN train CE per seed; λ/uniform after e9; whether the atlas runner supports an lr schedule/20 epochs and whether the C10 bitwise check can be built; 2×-width cost; cross-GPU equality; the shared fit/dev component.
