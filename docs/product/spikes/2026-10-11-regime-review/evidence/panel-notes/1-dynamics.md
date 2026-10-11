> These notes are the reconciler's (Claude's) condensed summaries of each reviewer's report, kept for provenance. They are not the reviewers' own text.

# Regime panel 1/5 training dynamics (training-diagnostician)
VERDICT: not at convergence on any host; the two families are limited differently. BN hosts are train-limited with an emerging data/generalisation gap; under_normalized is under-trained with no overfit. Capacity limitation can't be told (confounded). The regime can't support "capacity effects are small" nor "a 0.05 repair is impossible".
OBSERVED:
- O1: BN e9 train 1.05–1.09, dev 1.23–1.29, gap +0.16–0.22 (≈+0.10 at e3); dev slope −0.028 to −0.036. ×2 lowers train and dev similarly (cs train 1.089→1.055, dev 1.293→1.264); gap ~+0.2 unchanged.
- O2: under_normalized gap ≈0; dev slope −0.035 to −0.045 at e9; rung-4 H20 no_growth dev 1.562 (e9) → 1.354 (e19); gap +0.06–0.10 at e19; dev slope −0.011 (decelerating, no plateau).
- O3 (CPU arithmetic on the published rung-4 per-epoch table; H20 paired, finite runs; n=756 static, 763 scheduled; exploratory): gain = no_growth − arm dev CE.
  - static mean: e3 .125, e6 .139, e9 .122, e12 .110, e15 .087, e19 .041
  - static median: .128 .146 .136 .132 .119 .107; p10: e9 −.071, e19 −.163
  - scheduled median: .023 .053 .084 .099 .104 .112
  - So it is not a transient: the median stays >0.10 at e19, and the mean's fall is the lower tail (divergence).
  - Time-equivalence: no_growth reaches static's e9 mean at ~e13.5 (≈4.5 epochs); at e19 the 0.107 median ≈ 9 epochs. Shrinks in nats, grows in epoch-equivalents: an offset/rate difference, not a capacity ceiling.
- O4: BN graft ≈ static ≈ no_growth within 0.003–0.01 at e9; ×2 buys 0.018–0.032.
- O5: train CE is on augmented batches in train mode, so the true gap is larger.
HYPOTHESES (with falsifiers):
- H1: BN hosts heading into a data/generalisation limit at 4,096 (gap doubled, insensitive to ×2). Falsified if 16k examples give the same dev CE and gap at equal epochs.
- H2: also step-limited (pre-plateau). Falsified if dev flattens by e20 at lr 0.05.
- H3: under_normalized is optimisation-rate-limited; the norm static is a function repair (persistent median offset). Falsified if the median static gain is ≤0.02 by e40, or a tuned lr/schedule on no-growth matches static.
- H4: constant lr 0.05 + Nesterov + wd is above optimum late; the late dev rise, rung-4 late degradation and static gain divergence fit a high-lr late phase (spike exposure). Falsified if a decayed lr gives the same late-failure rate.
- H5: capacity benefit grows with horizon/data. Untested; at this horizon ×2 is a fit-rate effect (train drops 0.034 = dev).
0.05 IMPLICATIONS:
- Capacity: λ·log2(1.10) ≈ 0.0037; the bar ≈ 1.85 doublings (≈3.6×); a 1.10× seed would need ~13× widening's per-log-parameter efficiency. No evidence for that.
- Repair: shown on one designed host (median 0.12–0.14 at ~1.0×). So 0.05 is reachable by function repair, not capacity. The bar selects for "fixable deficit": a regime/host question.
- On hosts without a repairable deficit, a pass needs much larger per-parameter returns (e.g. much smaller hosts; nothing <117k has run).
COMPUTE-MATCHED: parameters alone are insufficient. Report at equal parameters AND steps AND epochs, saying which. Add a descriptive epochs-equivalent / time-to-target metric. Use median and tail rate separately (static divergence tail 1.56% at 20 epochs). Comparators must share the lr schedule.
EXPERIMENTS:
- E0 (0 GPU): offline decomposition of the existing per-epoch data (rung-4 tables, C1 arms-summary): per-seed time-to-target, median gain curves, fraction of seeds with gain >0.05 by epoch. Same on the BN hosts (is ×2 a time shift?). Gate: BN time-shift matches ×2 → H2 supported; gain persistence confirmed → E1 uses the median. No L1/L7.
- E1: horizon and schedule, no intervention. no_growth and ×2 at 40 epochs, constant 0.05 vs a prespecified cosine/step decay; hosts channel_starved and under_normalized; 96 seeds; 768 arm-seeds ≈ 7.9 GPU-h (37 s per arm-seed at 40 epochs).
  - Stops: futility at e30 if |dev slope| <0.002 for both schedules and the ×2 gain is within ±0.005 of e10's; divergence: abort non-finite arms, the cell if >10%; data limit: dev rising 5 consecutive epochs on 90% of seeds → mark data-limited.
  - Gate: plateau with ×2 gain <0.02 → BN capacity-insensitive at 4,096 (E2 or abandon these hosts); gain growing → capacity matters at horizon (E2); decay helps both equally → fix the schedule. No L1/L7.
- E2: data size. no_growth and ×2 on channel_starved at 4,096/8,192/16,384, steps-matched and epoch-matched cuts, E1's schedule, 64 seeds, ~2.3 GPU-h at 10-epoch equivalents, up to ~4× if epochs are fixed; plan 6–9 GPU-h.
  - Futility if the 16k-vs-4k dev gain is <0.02 at matched steps.
  - Gate: the gap shrinks and ×2 gain grows → propose a larger fit set; no change → H1 rejected (optimisation-limited). No L1/L7.
- E1+E2 ≈ 14–17 GPU-h, serial, only when Sultai is idle.
DISAGREES:
1. "Before convergence" for all hosts is true for under_normalized, but the BN gap is already +0.2, so more epochs at the same data may not help; don't extrapolate.
2. The "two doublings" framing implies capacity is the only route; on under_normalized the observed route is repair (median > 2× the bar at e19). Use median and tail.
3. The brief's rung-4 line implies degradation; by the median it is mild (0.146→0.107).
4. Option D must fix the lr schedule before any horizon test.
COULD NOT VERIFY: per-seed C1 BN epoch tables; whether rung 4's late rise is overfit or lr noise; time-equivalence is an interpolation, not a registered estimand; lifecycle code; wd×4,096 interaction.
