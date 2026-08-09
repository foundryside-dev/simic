# PDR-0022 — Newsroom demoted to a single appendix rendering (ADR-0009)

Date: 2026-08-09   Status: accepted   Author: Claude (product-owner session 11)
Owner sign-off: RECEIVED 2026-08-09 (session 11, owner-directed mid-session:
demote the newsroom analogy to an appendix as an eloquent alternative
construct — "we don't need two parallel operating analogies")
Related: ADR-0009 (architecture tier), ADR-0008/PDR-0020 (Namespec 2.0),
simic-7e2683f3cd, PR #5

## Context

After Namespec 2.0 locked the codename grammar as the operating frame
(ADR-0008), the newsroom analogy still ran co-primary: a fourteen-role
sidebar in the constitution, a duplicate mapping in the architecture
chapter, and "deliberately resembles a newsroom" framing on the README and
public site. Two parallel operating analogies split the design's voice and
let the metaphor read as normative when enforcement was always contractual.

## The call

One operating analogy. The newsroom survives as exactly one thing: Appendix
E, reframed as an alternative rendering of the authority model for readers
to whom the codenames don't speak — tightly coupled (lockstep-maintenance
duty) but subordinate. Normative citations re-anchor to the native
invariants: "the newsroom rule" becomes the evidence-routing rule
(INV-07/INV-09). Architecture tier recorded as ADR-0009 (no invariant
displaced); executed as a same-session cascade (constitution, chapters,
appendix, README/AGENTS/ARCHITECTURE, site pages), published via PR #5 and
verified live on simic.foundryside.dev.

## Rationale

Every authority change was being narrated twice, and the second narration
carried no enforcement weight. Product-tier value: the design speaks with
one voice to implementers (the audience vision.md names), while the
newsroom keeps its genuine onboarding value at appendix tier for the
eventual publication audience.

## Reversal trigger

Mirrors ADR-0009: if new contributors or publication reviewers repeatedly
fail to grasp the authority model from the codenames alone, re-promote a
condensed mapping into the architecture chapter — by ADR, never silently.
