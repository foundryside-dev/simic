# PDR-0004 — Record the owner-stated reset rationale in vision.md

Date: 2026-08-08   Status: accepted   Author: Claude (product-owner session)
Owner sign-off: yes — the content is the owner's own statement, made in-session
2026-08-08; recording it verbatim-in-substance is not an autonomous vision edit.
Related: vision.md (Purpose), simic-00351db32e (§2 re-motivation, comment #2),
docs/concept/reviews/2026-08-08-esper-lite-ci-controls-review.md (CT1)

## Context
During the esper-lite CI/controls review, the owner stated that cautionary tale
1 — the silent-default defect class ("unmeasured means zero") — is the main
reason for the Esper→Simic reset: months of whack-a-mole on the old instrument
versus a clean cut with those defect classes unrepresentable by construction.
This sharpens the recorded motivation beyond both the HLD's current §2 and the
bootstrap vision.

## Options considered
1. **Record it in vision.md Purpose (chosen)** — the reset rationale is
   vision-tier content; the owner stated it explicitly.
2. **Leave it only in the tracker comment** — rejected: the next session resumes
   from the workspace; motivation buried in a comment gets relitigated.
3. **Hold it for the §2 rewrite** — rejected: simic-00351db32e is gated behind
   the decision gate; the workspace should not wait on the HLD's editorial queue.

## The call
vision.md Purpose now carries the owner-stated rationale, attributed and dated.
The design consequence — value/observed/age triples, generated layouts with
hashes, and transport-completeness tests are constitutional-grade, not CI
hygiene — was filed as gate input (comments on simic-00351db32e and
simic-4da299ff46), not enacted.

## Rationale
Vision is where "why does this product exist" lives; an owner-stated motivation
that reframes the reset belongs there with provenance, so no future session can
mistake it for an agent inference.

## Reversal trigger
If the adjudicated §2 rewrite (post simic-0dd5362f05) lands a materially
different formulation of the reset rationale, reconcile vision.md to the
adjudicated version via a superseding PDR.
