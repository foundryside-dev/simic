# PDR-0037 — Kernel demo scope pins HELD; menu scaling and friends become a successor experiment

Date: 2026-08-10   Status: accepted   Author: Claude (session 15)
Owner sign-off: covered by the same "I'll take your recommendations" as
PDR-0036 — this is the half of that recommendation that says *no*.
Related: PDR-0029 (what the demo is for), PDR-0036 (what was added instead),
analysis `docs/superpowers/reviews/2026-08-10-kernel-demo-enhancement-analysis.md` (Tier 3)

## Context

The same cold read that produced PDR-0036 surfaced four changes that would
answer more than the demo can: growing the seed menu to ~16 parameterized
variants, adding a second slot / sequential grafts, testing a held-out host
family, and adding a retirement ("un-graft") arm.

Each of them touches `SEED_NAMES` / `DESIGNED_WINNER`, gate 4's dominance
threshold, the money chart's four-row structure, or the β calibration. The
spec's scope pins say, verbatim, "agreed, do not widen."

The strongest of the four is menu scaling, and it is worth stating why: the
demo's headline claim is the **inversion of the sparse-bandit regime** — full
counterfactual labels at every measured decision point. That inversion holds
only while the action space is enumerable. **Simic's is generative, and
therefore is not.** So the demo's central economic claim has a known
scaling boundary that the demo itself cannot probe.

## Options

1. **Widen the demo** to answer the scaling question now — voids five SME
   panels' sign-off, re-opens a locked spec's pinned scope, and delays a run
   that is already built and waiting.
2. **Hold the pins; defer to a successor experiment** with this store as its
   baseline.
3. **Hold the pins and drop the question** — cheapest, and loses the one
   result that decides whether Simic's supervision model survives contact
   with a generative action space.

## The call

Option 2. The scope pins hold. The four proposals are recorded as **Experiment
2**, explicitly *not* as enhancements to this demo, in the Tier-3 section of
the analysis document. Their pilot is already licensed inside the current
campaign as exploratory study E5 (rank quality as a function of arms actually
run), which needs no spec change and no new collection.

## Rationale

Presenting menu growth as an "enhancement" to a locked spec would be scope
creep wearing a helpful face, against a design that three review rounds signed
off. And the demo's value is precisely that it is small enough to finish: its
purpose (PDR-0029) is the pointable answer to "how do you know it works," and
that answer is worth more delivered than enlarged.

Deferring is not dropping. Experiment 2's headline question — how policy
quality decays as the fraction of the menu actually run falls — determines
whether Simic needs a learned value model that predicts a candidate's outcome
*without* running it, and how good that model must be. That is a Phase-C-and-
beyond design input, not a blocker for the demo run.

## Reversal trigger

Reopen as a shaped bet when **either**: the kernel demo run completes through
Phase F (the baseline store exists, so Experiment 2 becomes cheap), **or** a
Phase-A/B design decision turns out to depend on the menu-scaling answer — at
which point it is on the critical path and must be shaped rather than deferred.
If neither has happened by the time Phase C of the HLD ladder is shaped,
Experiment 2 is dropped explicitly rather than left standing as an unfunded
intention.
