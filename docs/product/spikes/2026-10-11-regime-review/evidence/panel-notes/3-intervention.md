> These notes are the reconciler's (Claude's) condensed summaries of each reviewer's report, kept for provenance. They are not the reviewers' own text.

# Regime panel 3/5 intervention/closed loop (morphogenesis-reviewer). jq over published files; replayed Esper-lite's germination gate (tamiyo/tracker.py:108-160, heuristic.py:179-212, leyline/__init__.py:592-610 @0807ccf): latch = 3 consecutive epochs with relative dev-CE change in (−5%, +3%), reset otherwise; plateau = consecutive epochs with accuracy change <0.5 pt; fire = latched & epoch ≥5 & plateau ≥3. Caveats: C1 has no per-epoch accuracy (latch only); epoch indexing may be off by one; the rule's units were set for 150 epochs at lr 0.01.
OBSERVED:
1. The original trigger almost never fires here. under_normalized no-growth (rung 4, n=768): fires 5/768 at 10 epochs (median e8), 74/768 at 20 (median e16, lower quartile 14). C1 BN latch by e9 only 36–52/768 per host (132 on under_normalized). A Simic lifecycle is 8 epochs (kernel_demo.py:145-147); HLD budgets <30 epochs per lifecycle (HLD:1359); Esper-lite's closed loop ran up to 40 epochs, 3 seeds (poc_tamiyo.py:54-62@0ee3a001). So L7 is unreachable at 10–20 epochs under the original rule, and horizon gates any loop test.
2. Simic has NO cull path: Stage has no CULLED (kernel_demo.py:772-778); epoch_tick fossilises after fixed counts (:858-873). Esper-lite kept/culled on alpha-ablation contribution >0.5 pt (heuristic.py:271-311@0807ccf); its "ransomware" rule (:277-289) exists because ablation measures dependence, not benefit; the commit message calls the signal "obs-blind in multi-seed episodes".
3. The original closed loop ran ONCE, confounded with horizon: README.md:79-88@0ee3a001, heuristic loop 82.16 vs 10-epoch baseline 69.31; n=1, up to 40 vs 10 epochs, selected on the test loader. Here horizon alone is worth ~4× the bar (H20 no-growth dev 1.562 e9 → 1.354 e19).
4. Topic 3: only function restoration has cleared the bar at ≤1.10× (norm static 1.001× ~0.14; 2× uniform 0.028; λ·log2 1.1 ≈ 0.004; needs ≥13× λ efficiency). Only normalisation did it; attn on no_spatial_mix +0.020.
5. "Where" was designed, never demonstrated: HeuristicTamiyo's slot logic is only available_slots<=0 (heuristic.py:193); the POC had one injection point. HLD:367 lists "Models exhibit identifiable bottlenecks through telemetry analysis" as a research ASSUMPTION; HLD:160,215 presuppose identifying a bottleneck independently of its fix. Neither lineage tested it.
HYPOTHESES:
- An emergent bottleneck = an unimpaired host whose no-growth trunk alone meets a detector frozen before any graft, with train and dev CE flat together (capacity or lr floor, not data limit; the BN gap grows .10→.16–.22).
- Most plausible on small hosts with more data (the founding scenario).
- The detector reads only the trunk, so no circularity.
- Plateau firing here may be noise.
- Tension: unimpaired hosts already have the functions the library restores, so the one demonstrated repair route may never meet an emergent bottleneck.
EXPERIMENTS:
- E1 detector on natural hosts, no graft:
  - Hosts N0, S1, S2 (reference ×1, ×0.5, ×0.25), fixed by rule; no-growth only.
  - Cells: 4,096×40 epochs (all three); 40,000×10 epochs (S1, S2) (atlas_telemetry.py:49-53 caps fit at 40,000). 48 seeds per cell.
  - Prereqs: clean train CE; per-stage effective rank (stage 2 only today, atlas_telemetry.py:146).
  - Detector: the original rule verbatim on 128-step ticks (a departure from the HLD EndOfEpoch clock, HLD:691). Where = stage with the largest drop in early-tick effective rank per unit width.
  - Stops: health gate; byte-identical dry run; 5 GPU-h cap; one round; no host or regime added after data.
  - Budget ≈1,517 arm-equivalents × 9.3 s ≈ 3.9 GPU-h (fitted ~2.4); small-host per-step cost unmeasured.
  - Gate: fires in ≥50% of a cell's runs before tick 30 with train and dev flat → freeze that host/regime/site for E2; only data-bound plateaus → no L1 substrate here, option A; never fires → L1 precondition absent at bounded scale, option A, NOT a falsification.
  - Reaches none of L1–L7: tests HLD:367 and qualifies a substrate. No synthetic compensation.
- E2 minimal closed loop, only on E1's frozen cell:
  - Controller: HeuristicTamiyo verbatim, ≤3 seeds; library capped at 1.10× cumulative, fixed per host before data (S2: norm only; S1: norm + attn); E1's site rule over 2 sites (needs G5's second slot). Prereq: a cull mechanic (slot → DORMANT, params out of the optimizer).
  - Arms (paired, same horizon): N never-graft; U uniform 2× (register raw H−U; a new-regime λ from E2's own N/U is an owner sign-off item; the frozen λ doesn't transfer); H loop with rule-based cull; AK always-keep; H1 one germination only (H−H1 bundles retry-after-cull with a second graft); S_k H's first kept blueprint installed from step 0 (grow vs install, D2); a fork at H's first keep/cull decision taking the opposite choice.
  - Anchor (separate from the trigger): under_normalized, forced norm germination at a fixed tick; the fork must show keep wins and the evaluator must keep.
  - 96 seeds per host; paired sd ~0.11 → half-width ~0.022.
  - Stops: the fork bitwise equal to H up to the decision; anchor failure → instrument_failure; no_trigger if <50% of seeds germinate; the 10% divergence cap; terminal GPU cap; one round.
  - Budget: 96×6.5×4 ≈ 2,496 arm-equivalents per host ≈ 12.9 GPU-h for two hosts (7.7 fitted); ~22 (12.8) on the 40k cell.
  - Gate: H−N >0.05 & H>U & H > rate-weighted fork mean → first evidence touching L1, L3, L7; reopen with L4 (learned vs this heuristic, HLD:2225) instead of Fleet A/G2′. H>N but not U → A. Keep vs cull within ±0.018 → L7 has nothing to decide at this scale. Keep/cull differ but H ≤ the fork mean → the in-run signal fails; replace with branch QA, don't tune. S_k vs H decides the D2 hypothesis on a natural host. Nothing beats N → park until generated structure (L6).
  - Reaches L1, L3 (when/which/where), L7, and L2 vs U on the E1 host; not L4–L6. The anchor is an instrument only (synthetic compensation).
- No third experiment: E2 contains D2 (S_k); a function-vs-capacity screen on designed hosts = synthetic compensation again.
DISAGREES:
1. The defer record omits that the only timing evidence (rung 4 T0; static +0.046) runs against L1 timing.
2. Rev 3 §1/D11 should record that Esper-lite DID run L7 once (finding 3).
3. D1 is drift from the HLD design, not from anything Esper-lite demonstrated.
4. §9's cap + bar admit function restoration, not capacity; F1's prior is near zero.
5. B14 is right within the screen; in E1 (no library arm, frozen detector) honest-small hosts could count for emergence. John's call.
6. D3 "easier" applies to L1 evidence only; HLD:2222 trained Tamiyo on a curriculum of simulated scenarios, so designed hosts are a legitimate curriculum.
COULD NOT VERIFY: the accuracy-plateau rule on C1 BN; S1/S2 trainability at 40 epochs or 40k; per-step cost; the Esper-lite POC run records; whether the learned policy used slot_idx; cull/fork build cost.
