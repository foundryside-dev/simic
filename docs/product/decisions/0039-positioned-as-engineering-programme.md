# PDR-0039 — Simic is positioned as a novel engineering programme, not a confirmatory research study

Date: 2026-08-11   Status: **proposed** — owner sign-off required
Author: Claude (session 16)
Owner sign-off: PENDING. This record proposes a **vision-level** change and is
on `vision.md`'s escalate list. `vision.md` is deliberately untouched; nothing
here is enacted until the owner rules.
Related: PDR-0029 (extends its position, relaxes its boundary clause),
ADR-0014 (K/N — demoted, not deleted), `docs/design/00-related-work.md`
(the evidence), `docs/concept/reviews/2026-08-11-morphogenesis-concept-panel.md`
(owner decision G, which this closes)

## Context

The owner already holds this position for the demo. PDR-0029 records it with
sign-off, 2026-08-09, owner-stated:

> "the kernel demo is a 'proof of concept' so when people say 'how do you know
> it works' we have something to point to, because my view is that **this is
> primarily engineering, we've already proved the maths**."

PDR-0029 then drew a boundary that this record proposes to relax: *"The
confirmatory claim still comes only from the pre-registered fleet (ADR-0014,
K = 1.5 / n = 32) — the demo answers 'does it work at all,' the fleet answers
'does it beat the controls.'"*

Two things have changed since, and both point the same way.

**The novelty map** (`docs/design/00-related-work.md`, added 2026-08-11)
grades every generation-side component against checked prior art. The result
inverts `01-claim.md#26-the-empirical-driver`, which names "generated (not
selected) structure" as irreducible contribution #1: **the generator is the
most-precedented component in the system.** Zero-influence residual insertion,
function-preserving morphism, canonicalisation and isomorphism hashing, and
best-of-K pooling are commodity; telemetry-conditioned generation is one hop
from the zero-cost-proxy line. What has no precedent found is the **screen** —
every surveyed growth criterion (GradMax, Firefly, zero-cost proxies, Gstack)
is a one-step surrogate validated end-of-pipeline by rank correlation against
final accuracy, and none forks a matched no-growth continuation over a common
future (INV-06, INV-15, INV-16) to measure the causal effect of the insertion.

**The confirmatory claim is weakly obtainable.** The concept panel verified
three defects in the apparatus that would carry it:
`cost-model.md#h-k-and-n-for-the-headline-criterion` puts INCONCLUSIVE at
0.845 and 0.846 for the two most likely truths; the declared negative is not
deliverable at n = 32 (80% power needs n ≈ 73); and the single primary
endpoint has no defined success predicate, because `QualityReport` carries no
threshold, horizon selector or decision rule and
`05-leyline-contracts.md#914-qualityreport` states it "does not contain
`ADMIT` or `REJECT`."

## The call

**Simic is a novel engineering programme.** Its deliverable is a working
instrument — a system that measures the causal effect of a structural
intervention on the trajectory that actually received it — together with
demonstrations that it works and a retained corpus of what it measured. It is
not a confirmatory study whose value is concentrated in one hypothesis test.

Three consequences:

1. **`01-claim.md#28-success-criteria` splits into two classes** —
   *engineering acceptance* (must pass, can fail, gates calling the system
   working) and *optional study* (reportable, not gating). The seventeen
   criteria keep their numbering and wording; a classification layer is added
   above them. Criterion 2 — Momir beats random search — moves from headline
   to one member of the optional class.
2. **The confirmatory statistical apparatus is mothballed, not deleted.**
   ADR-0014's K = 1.5 / n = 32, the α-family declaration (D2), the negative
   margin (D1), and the eight-cell allocation at n = 32/16 stop gating the
   programme and become a costed study the owner may commission later. The
   sizing work already done is not wasted; it is the price list.
3. **A new acceptance criterion is added for the instrument itself** — see
   the companion edit. §28 currently has no criterion asserting that the
   paired-branch difference resolves an intervention effect above
   branch-divergence noise. Under a research framing that gap was hidden
   behind criterion 2; under an engineering framing it is *the* criterion.

## The line that does not move

The distinction is mechanical and `01-claim.md#26-the-empirical-driver`
already draws it. **If an invariant came from a predecessor scar, it stays.
If it came from needing a publishable result, it is negotiable.**

| Origin | Examples | Disposition |
|---|---|---|
| Predecessor scar | INV-05 exact replay; INV-07/INV-09 direct evidence routing; INV-15/INV-16 mandatory no-op at utility zero; INV-24 fail-closed typed compatibility; INV-31 complete negative retention; INV-32 grouped statistics; INV-37 blinding by construction; INV-38 failure visibility | **Unchanged.** These stop the system lying to itself, and nothing about the audience changes that. |
| Confirmatory statistics | ADR-0014 D1/D2; K = 1.5, n = 32; the eight-cell allocation; α spending | **Mothballed.** Reporting, not gating. |

INV-15/INV-16 is the one that will be argued into the second column. It does
not go there: the mandatory no-op is not a statistical nicety, it **is** the
instrument.

## Rationale

Three independent judges scoring the panel's fifteen proposals on evidential
strength, solo feasibility and strategic optionality converged on
engineering-shaped work without being asked to — the headroom probe, the
reference-population argmax question, and the instrument falsifier are all
acceptance tests that can fail, not confirmatory experiments. The programme's
own selection pressure was already pointing here.

It also closes the panel's owner decision G ("what should be true at write-up
if Momir loses") by dissolving it: a Momir null becomes one measurement the
instrument produced, not a programme-level failure.

## What this costs — stated plainly

- **The right to claim a result.** `vision.md` currently names the
  morphogenetic-AI research community as a secondary audience and says a clean
  negative is publishable. That audience changes: engineering framing points at
  systems/tooling venues and a released artifact, not a main-track claim.
- **The related-work chapter's negative half is ~12 queries** and is absence of
  evidence. The positioning rests on it and should not be published without a
  deeper search.
- **Reduced external pressure for rigour.** A pre-registration is a commitment
  device. Removing it removes a reason to be honest that was doing real work.
  The scar-derived invariants in the table above are what replaces it, which is
  why none of them moves.

## Reversal triggers

Two, and both can actually fire.

1. **Back to research framing.** If the instrument acceptance criterion passes
   *and* the headroom probe reports non-zero off-menu headroom *and* the owner
   wants a venue claim, the confirmatory apparatus returns to DECIDE. It was
   mothballed with its costings intact precisely so this is a re-commissioning,
   not a redesign.
2. **Anti-build-trap.** If two consecutive checkpoints report progress with no
   acceptance-class criterion having been *run*, the reframe has become the
   build trap and this record returns to DECIDE. "Success = it is implemented"
   is the failure mode of this decision and this trigger is its detector.
