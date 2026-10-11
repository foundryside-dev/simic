# Design panel on the host-family proposal — 2026-10-11

**Read-only design review of revision 2 (draft PR #45 at `d4bb6a5`), for John.** Nothing here
approves training. John has made no choice among the options.

**How the panel ran:**
- Eight specialists each reviewed the same frozen copy of the draft independently, without
  seeing each other's work.
- None of them edited files, ran the repository's code or tests, used a GPU, or opened sealed
  run directories.
- The statistics reviewer ran standalone arithmetic and bootstraps on the published per-arm
  summaries only. The citation reviewer totalled published summaries with `jq`/`awk`.
- The reconciliation below is design documentation only. [Revision 3 of the proposal](proposal.md)
  applies it.

## Verdicts

| # | Remit (installed agent) | Verdict | Blockers | Main should-fix points |
|---|---|---|---|---|
| 1 | Statistics (`experiment-statistics-reviewer`) | Endorse with changes | 0 | The 6-host figures assume independence; near-boundary weakness of n = 192; selection-rule wording; the N0 contrast; sd robustness |
| 2 | Training regime (`training-config-reviewer`) | Endorse with changes | 1 | D4 overstated "capacity-insensitive"; no distinguishing tests named; regime knobs omitted; honest-small caveats; stage-1 sites |
| 3 | Morphogenesis (`morphogenesis-reviewer`) | Endorses the stop as a recommendation; the screen only with changes | 2 | N0 treated as an instrument; "what a counted host feeds" overclaims; missing L7; "no primary source" wrong; "no designed winners" overclaims |
| 4 | Implementation correctness (`pytorch-code-reviewer`) | Endorse with changes | 1 | Seeds hard-coded at 64 channels; `WIDTH_STEP`; config-hash stability; zero-function control; depth vs index-5 hooks; stage-1 capacity mild |
| 5 | Replay and provenance (`determinism-reviewer`) | Endorse with changes | 2 | The phase handoff can't be enforced; the zero-function control can't be bitwise; pairing scope; G5 draw underspecified; seed ranges; draw record |
| 6 | Systems and compute (`plan-review-systems`) | Endorse with changes | 0 | Handoff unbuildable on the launcher; pre-emption; cap mechanics; unit definition; GPU placement; dry-run scope; grant order |
| 7 | Citation and original-claim fidelity (`analysis-validator`) | Endorse with changes | 0 | The over-provisioning foil has primary sources; the POC's static arm; D6 is parity with the original's first phase; L5 attribution; "earliest" wording; the `mild` list |
| 8 | Adversarial (`product-decision-critic`, new instance) | Endorse with changes | 0 | Overstated negatives behind the stop; a tilted §14 and the missing "defer" option; one sentence that pre-empted John; N0; superseded advice not fully listed |

**Totals:** eight "endorse with changes" (one of them endorses the stop and makes the screen
conditional); none "do not endorse"; **six blockers raised, all resolved in design**; no
unresolved blocker.

## Blockers and their resolution

| Blocker | Raised by | Resolution in revision 3 |
|---|---|---|
| The runner builds every seed at 64 channels (`atlas_static.py:61`, `atlas.py:191`), and `_require_slot` rejects w2 ≠ 64 (`atlas.py:254-257`). F2, F4, F5, S1 and S2 could not run | Implementation (also replay) | §12 lists it first: build at `feat_channels`; bit-identical at 64; frozen `bounded_comparison.py` untouched; CPU birth test at w2 = 56. Without this the screen cannot run as written |
| D4: "capacity-insensitive / possibly untestable" contradicts the draft's own numbers | Training regime | D4 rewritten. What the evidence supports: the 10-epoch endpoint is pre-convergence at constant lr; hosts respond to capacity (2× lowers late CE 0.018–0.032); a ≤ 1.10× injection's λ-predicted gain is ≤ 0.004, and the 0.05 bar is about two doublings. §11 option D names the distinguishing tests with costs |
| The N0 negative control turns the original's own target case (augmenting a capable host) into `screen_invalid` | Morphogenesis (stats, regime and adversarial agree) | N0 is descriptive (`reference_gain` / `reference_no_gain`) and out of the instrument checks. A descriptive contrast, gain(F, s\*) − gain(N0, s\*), is added. A non-confirm is defined as "generic benefit probably below about 0.045", not "no bottleneck" |
| "What a counted host feeds" overclaims: "repairs an upstream deficit"; no synthetic-vs-natural or closed-loop boundary | Morphogenesis | The reviewer's replacement text is adopted verbatim in §6: downstream compensation; not naturally occurring; not the closed loop; F4 via `attn` is a redrawn designed pair |
| A hash-committed phase handoff with "nobody reads phase 1" cannot be enforced: `analyze` prints every gain, and `launch` needs a commit between phases | Replay (systems agrees) | One pinned plan, one fleet, two internal phases. Phase 1 writes only a sealed `choice.json`. Phase 2 refuses if any report exists. The final analysis recomputes the choice. Fallback: C1-S's parent-pin pattern (§12) |
| A zero-function static control cannot be bitwise through `Unit._run`: `_check_end_state`, slot state and optimizer groups differ | Replay (implementation agrees) | Predicate named now: per-epoch dev metrics, `host_state_sha256` and `host_parameter_sha256` equal; a test-only `SeedDelta` with an end-state exemption (§6, §12) |

## Where reviewers disagreed with each other, and what I decided

1. **Pre-emption and abandonment.**
   - **The disagreement.** Systems: "no reading" both discourages yielding the GPU to Sultai and
     gives an exit from a likely `no_family`. Replay and adversarial: allow resume. Statistics:
     a capped or abandoned run has no reading.
   - **Decision.** Pre-emption pauses, then resumes under the identity check, with a declared
     maximum pause and nothing opened. A run that cannot resume is "abandoned": it uses up the
     single round and returns to John as no reading. That removes the exit hatch without making a
     stop automatic. A capped run is treated the same way.
2. **The recommendation's framing.**
   - **The disagreement.** Morphogenesis endorses a stop, as a recommendation. Statistics says a
     pass would be weak evidence. Adversarial says a stop is defensible but on grounds the draft
     underused, that reasons 3 and 4 were weak, and that "defer" was missing. It would present
     the options at parity.
   - **Decision.** §11 presents stop, defer, screen-then-decide and the regime question at parity,
     at the same depth. §14 keeps my recommendation (stop), labelled as mine. Its reasons are now
     the ones the panel supports: static is ahead; the chain from `family_viable` cannot reach L1
     or L7; the screen cannot give counted evidence on the founding principle. The regime and
     "the GPU goes to Sultai" are dropped as stop reasons.
   - **Recorded dissent.** The adversarial reviewer's preference for no recommendation at all is
     noted in §14.
3. **The N0 contrast estimate.**
   - **The options.** Statistics offered two: N0's phase-1 estimate for seed types other than its
     own winner, or N0's phase 2 on every eligible seed type (about +1.0 GPU-h).
   - **Decision.** The first, which costs nothing. The headroom under the conservative cost basis
     is thin.
4. **The G5 host list.**
   - **The disagreement.** Replay suggested drawing and committing it now.
   - **Decision.** Proposed for plan freeze, binding only on John's signature, so this design
     review draws nothing new. The identity, exclusion and reject-and-continue rules are specified
     now (§6).

## On independence (requested by John's assistant)

The statistics addendum separates three things, and revision 3 uses its wording:
- **The independence heuristic.** "At least one of six confirms" ≈ 0.48 at a true gain of 0.04
  (sd 0.11, n = 192). This **assumes** that the six host-level estimation errors are mutually
  independent. **Independence is not established.**
- **Bounds that hold under any dependence:** 0.10–0.62 at a gain of 0.04, and at most 0.035 at
  0.03. Across sd 0.08–0.16 the range at 0.04 is 0.04–1.00.
- **Joint calibration.** A seed-level bootstrap on Fleet C1's four hosts gives 0.97–1.00 times
  the independence prediction, with 95% intervals [0.968, 1.004] and [0.983, 1.009].
  - It is consistent with independence or a weak positive dependence.
  - It cannot cover the six drawn architectures, six rather than four hosts, the shared pinned fit
    and dev data, tail dependence, or the phase-1 choice.
  - The pairwise correlations of 0.009–0.054 are descriptive only.

My earlier message to John said independence "holds empirically". That is retracted (§13 of the
proposal).

## Citation ledger (reviewer 7)

About 90 line-level citations were re-resolved: about 79 verified as stated, 5 overstated, 2
misquoted or misattributed, 1 incomplete but true, and 4 unverifiable. All the overstated and
misquoted items are corrected in revision 3:

| Item | Correction |
|---|---|
| HLD:129 | A student seeded at the start of training, not merely distillation |
| POC static arm | It was epoch-matched |
| PAPER:474 | It only defines No-Op |
| HLD:217 | Platform robustness, not policy transfer |
| D5 | It matches the HLD's foil |
| `fleet-c1.md:178-179` | Quoted exactly |
| "no-op often wins" | Its location is now given |

**Unverifiable:**
- byte-for-byte reproduction of the generator (the revision-2 re-review reproduced it; the panel
  did not run it);
- "never measured";
- "seed 42";
- the earlier subagent maps.

## What no reviewer could verify

- The per-seed gain sd for the new classes and for the small hosts.
- Whether S1 and S2 are trainable at lr 0.05.
- The size of the shared dev-set component.
- Whether results are equal across the two GPUs for the new hosts.
- Per-epoch train CE, which is in sealed run directories.
- Draw 0, which rests on the author's word: the first committed generator already used width
  step 8.

## Superseded advice

[§13 of the proposal](proposal.md#13-superseded-and-corrected-statements) lists every superseded or
corrected statement with its location, original wording, correction and status. That includes:
- the `mild` "honest, non-designed" wording;
- the checkpoint's "Rebuild" recommendation;
- the withdrawn "about 4 hours" pilot;
- the withdrawn candidate steer;
- my retracted independence remark.

The published results, PDR-0057 and the earlier spikes are unchanged. Whether to add dated
errata to them is John's decision.
