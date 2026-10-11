> These notes are the reconciler's (Claude's) condensed summaries of each reviewer's report, kept for provenance. They are not the reviewers' own text.

# Regime panel 5/5 adversarial (product-decision-critic, independent) on review.md @ aebd3ad: endorse with changes, no blockers; R2/R3 gates not signable as written; items 1–5 must be fixed before John signs any NEW threshold.
SHOULD-FIX:
1. An R2 null routes to stop, but the detector already missed a known deficit: under_normalized fires 5/768 by e9 while the norm graft gains 0.096 (O7), a rate deficit (H3) not a plateau, so silence is weak evidence of absence.
   - §5's "useful… not identified" mixes incidence and usefulness and contradicts §4's "precondition not observed under this detector". "Only data-bound plateaus" ≠ low incidence (the trigger fired). Missing outcomes: 1–49% flat-firing; S2 health-gate failure.
   - Fix: add the miss to O12; map an R2 null to A / B / new detector at parity; use §4's wording in §5; split the data-bound and no-firing outcomes; add the two missing outcomes.
2. The detector isn't verbatim and the gate isn't fully pre-specified. 128-step ticks = 1 epoch at 4,096 but 0.1 epoch at 40,000, while the constants are per epoch (EL leyline:482-485, which the cited 592-610 omits): 3%/−5%, 0.5 accuracy points, 3 and 5 epochs. "Before tick 30" = epoch 30 vs ~epoch 3. "Train and dev flat" has no numeric definition. "R2's where-rule" is undefined (post hoc if set after R2 data). Fix: list departures as NEW, define "flat", freeze the where-rule before any R2 data.
3. R3's L1/L3/L7 claim exceeds its arms. HeuristicTamiyo's "which" is round-robin with prune penalties (_get_next_blueprint @0807ccf), not diagnosis; "where" is new and undefined; no arm randomises when, which or where. L1 needs H ≥ S_k. Rev 3 said S1/S2 were chosen after C1 and S2 is capacity-limited by construction; not reconciled. Fix: L3 → "when only, partly"; L1 conditional on H ≥ S_k and a cell not capacity-limited by construction; random-site and random-blueprint arms if L3 is wanted.
4. R3's gate isn't in the document and is underpowered.
   - The intervention review and stats plan v0.1 aren't committed. ±0.018 < the half-width 0.022 at n=96, sd 0.11; sd 0.11 contradicts O9 (tripled at 20 epochs); ±0.018 is C1's 10-epoch resolution carried into a new regime (the move §3 forbids for λ). No "indeterminate" outcome.
   - Keep/cull mechanics undefined: HOLDING fossilises above 0.5 accuracy points on counterfactual_contribution, but on which split and how it maps to CE; cull = prune or rollback; the "rate-weighted fork mean". Decisions on dev scored on dev repeat O11 and B8. Whether "H − N > 0.05" is a point estimate or a bound is unstated; outcomes overlap and don't cover every case.
   - Fix: write the gate in the document; derive the band from R3's own sizing (NEW); add indeterminate → no reading; declare a separate decision split.
5. Budgets: R3 on a 40k cell ≈ 2.44× steps ≈ 31 GPU-h vs cap 15 ("higher" doesn't disclose it). Hypothesis: 4,096×40 cells may come out data-bound, making a 40k cell likelier to qualify. R1 + replay: 64×54×9.3 ≈ 8.9 > cap 8. R2 omits per-tick dev and clean-train evaluation (~98 ticks × 45k forwards on the 40k cell). R2/R3 cap consequences unstated. Fix: R3 as capped fits only a 4,096×40 cell; "cap hit → no reading, round used up, never read as no qualifying cell".
6. The order follows 1 of 4 reviewers, undisclosed. 3 of 4 put regime first (dynamics and systems horizon, stats cosine); §6.1 names only stats and dynamics. R2/R3 commit to the noisy 40-epoch constant-lr regime (O9) before R1's annealing answer. The reconciler recommended A in rev 3 §14, and an R2 null routes to A. Fix: say "3 of 4", make R3's regime depend on R1, disclose the earlier recommendation.
NITS:
- §3.3 "depends mainly on the deficit class" is a hypothesis → §2.
- §3.1 "three times noisier" rests on one arm on one host.
- §7 "regime noise (O4)" attributes a cause → H4/H6.
- O10 "Time beats width" is an interpretation.
- O6 is wrong for channel_starved (1.1× is 0.0031 worse).
- O14 omits the fixed-schedule 80.16: loop vs fixed is +2.0 pts, single seed.
- Falsifiers: H5 "within CI" treats a non-result as falsification; H6 points to a different regime; H8 names a test, not an outcome.
- R1 "well below / holds / reaches" undefined; "C1's pass is not a 10-epoch artefact" overclaims from 48 descriptive seeds.
- R3 arm "H1" collides with hypothesis H1.
- Line 19 pre-claims the fifth review "at the end".
- O4 "0–2%" doesn't follow from r ≤ +0.09; cite the e7–9 jitter decomposition (out-extra.txt).
- Sources not in the snapshot: O8 e6 median/p10, O16, the reviewer note numbers. O12 should cite rung-4 per-epoch.jsonl.gz and the C1 arms-summary.
AGREES (verified independently with scratch scripts at scratchpad/advcheck/):
- O12 reproduced exactly (5/768 by e9, 74/768 by e19, median e16; the off-by-one changes neither count). C1 latch 132/52/36/39. The blocking clause is the accuracy plateau: 142 latched by e9, 428 by e19 (fits O1, still improving).
- O4 reproduced, framed descriptively. No independence claim from low correlations.
- O13, O14 (82.16/69.31), O15, HLD:367/691 and the 40,000/44,992 limits confirmed.
- R1 6.7 GPU-h checks; the 2.5% / 10% caps match fleet-c1.json.
- The topic-2 separation paragraph is sound; R2 "qualifies" is correctly limited; the founding-loop table is honest for R0/R1/R2/C.
DISAGREES:
- Defer-record timing: on a host handicapped from step 0, "earliest is best" is what L1 predicts, so the evidence is uninformative about L1's timing, not adverse.
- O12 is informative mainly about the detector (it missed a known deficit), not about incidence.
COULD NOT VERIFY: O16 and the cost bases; the O8 e6 median/p10; uncommitted specialist notes; whether N0 uses BN.
