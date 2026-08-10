# PDR-0039 — Simic is positioned as a novel engineering programme, not a confirmatory research study

Date: 2026-08-11   Status: **accepted**
Author: Claude (session 16)
Owner sign-off: **RECEIVED 2026-08-11** — "PDR-0039 is endorsed."
This is a vision-level change on `vision.md`'s escalate list; it is enacted on
explicit owner ratification, never autonomously. `vision.md` and `metrics.md`
carry the change but **cannot be edited from a `main`-based branch** without
reverting the PDR-0035/0038 grant widening — see "Downstream" below.
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

**The primary reason, owner-stated 2026-08-11: the lack of novelty is not a
consolation, it is the feasibility argument.** A programme whose fifteen
generation-side components are all speculative is not schedulable by one person
on a spare-time cadence — it has fifteen open-ended debugging tails and no
estimable path. The novelty map says this programme is not that. Ten of its
components are established or one hop from established, with settled failure
modes and multiple independent implementations to copy from; **the speculative
risk is concentrated in one place — the screen — where it is legible and can be
attacked first.** That is the profile of something credibly buildable, and it is
the positive case for the reframe.

Read the two framings side by side. Under a research framing, "most of this is
already published" is an objection to be defended against. Under an engineering
framing it is the reason to believe the thing will exist: the parts that are
commodity are cheap and predictable, and the one part that is not has a
falsifiable acceptance test available at Phase D for roughly 30 HER
(criterion 18). **The same fact reads as a weakness in one frame and a strength
in the other, and the second reading is the accurate one for this programme's
actual constraints** — where wall-clock and owner attention bind, not compute.

This is recorded deliberately and in the owner's own terms, because a future
reader comparing this record against ADR-0014's mothballed fleet could
reasonably suspect the reframe was cost-driven retreat. It was not. The cost
arithmetic below is corroborating, not causal.

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

- **The right to claim a result.** `vision.md` names the morphogenetic-AI
  research community as a secondary audience and says a clean negative is
  publishable. That audience changes: engineering framing points at
  systems/tooling venues and a released artifact, not a main-track claim.

  **This cost is smaller than it first appears, and the reason is now standing
  context.** Owner-stated 2026-08-11: *"any research claim I did make would
  have just been 'hey check this out' rather than an attempt at a career."*
  The publication motive was never career-bearing, so demoting the confirmatory
  claim forfeits little that was actually wanted — and *"hey check this out"*
  describes a runnable, pointable artifact, which is precisely what the
  engineering framing optimises for and precisely PDR-0029's proof-of-concept
  logic. **Future sessions must not re-inflate this cost.** A later reader
  weighing publication-shaped work against engineering work should weight it
  by this constraint, not by generic academic incentives.
- **The related-work chapter's negative half is ~12 queries** and is absence of
  evidence. The positioning rests on it and should not be published without a
  deeper search. Unchanged by the above — a "check this out" artifact still
  should not assert a novelty claim it has not earned.
- **Reduced external pressure for rigour.** A pre-registration is a commitment
  device. Removing it removes a reason to be honest that was doing real work.
  Partially discounted by the same constraint — a pre-registration aimed at
  reviewers who were never the point was buying less than it appeared to. What
  it *was* genuinely buying is protection against self-deception, and that is
  replaced by the scar-derived invariants in the table above, which is why none
  of them moves.

## Downstream — what still carries this change

| Artifact | Change | Status |
|---|---|---|
| `docs/design/01-claim.md#28-success-criteria` | Classification layer; criterion 18 | **Done** — pending banner removed on ratification |
| `docs/product/roadmap.md` | Now/Next framing reads as engineering acceptance | **Done** |
| ADR-0014 | Confirmatory apparatus mothballed | **Done** — superseding record, not an edit |
| `docs/product/vision.md` | Purpose, "Who it serves", the "check this out" constraint | **BLOCKED on PR #13** |
| `docs/product/metrics.md` | North-star row is currently K = 1.5 / n = 32 | **BLOCKED on PR #13** |

The last two have moved on `kernel-demo-rev62-arm-recording` and those changes
are not on `main`. Editing them from a `main`-based branch would conflict with,
or silently revert, the PDR-0035/0038 grant widening. **Sequencing: merge PR #13
first, then apply.** This is a mechanical constraint, not a deferral of the
decision — PDR-0039 is accepted and the other three artifacts already carry it.

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
