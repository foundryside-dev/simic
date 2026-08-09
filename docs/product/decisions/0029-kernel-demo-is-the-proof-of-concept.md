# PDR-0029 — The kernel demo is the proof of concept: the pointable answer to "how do you know it works"

Date: 2026-08-09   Status: accepted   Author: Claude (product-owner session 12)
Owner sign-off: RECEIVED 2026-08-09 — owner-stated: "the kernel demo is a
'proof of concept' so when people say 'how do you know it works' we have
something to point to, because my view is that this is primarily
engineering, we've already proved the maths."
Related: PDR-0028 (spec provenance; supersedes its "concept artifact only"
characterization of the demo's *purpose* — the spec/commit record there
stands), roadmap.md Later band

## Context

PDR-0028 recorded the kernel demo spec as a parallel-session artifact with
no product meaning assigned — "concept artifact only; building it would be
a new bet." Since then, in the owner's parallel session, the spec was
**locked at rev 6** (commit 98083fd; three panel rounds + external review
patches) with owner verdict **Design APPROVE, Implementation GO** — target
`experiments/kernel_demo.py`. The owner has now also assigned the product
meaning directly in this session.

## The call

The kernel demo ("Simic in 20 minutes") is the programme's
**proof-of-concept artifact**: a runnable, pointable demonstration for the
question *"how do you know it works?"* — aimed at the eventual secondary
audience (the research community at publication, per vision.md) and at
collaborators/skeptics before that. The owner's stated position, now
standing product context: **Simic is primarily an engineering risk, not a
mathematical one — the maths (counterfactual credit assignment via paired
branches; Esper's demonstration that seed telemetry suffices) is already
proved.** With the spec locked and implementation GO already given
(parallel session, 2026-08-09), the demo enters the roadmap **Next band as
intent**: a shaped, owner-approved bet awaiting sequencing against the
burn-down and Phase A (sequencing is /program-management's call, not this
record's).

The demo is deliberately menu-based — it proves the **substrate loop**
(telemetry → learned decision → inject → STE pretrain → blend → end-state
counterfactual reward), not generative morphogenesis; its fan store is
early Momir's counterfactual atlas (memory: kernel-demo-spec-locked).

Boundary kept explicit: the demo *demonstrates the mechanism runs*; it is
not the evidence chain. The confirmatory claim still comes only from the
pre-registered fleet (ADR-0014, K = 1.5 / n = 32) — the demo answers "does
it work at all," the fleet answers "does it beat the controls." Conflating
the two would be the vanity-evidence failure mode; the demo must never be
cited as §28 evidence.

## Rationale

A proof-of-concept with a named audience converts "trust the design docs"
into "watch it run" — the cheapest credibility instrument available while
the fleet is still years of spare-time cadence away. And if the demo
*fails* to run cleanly, that is engineering signal at demo scale, obtained
before the fleet pays for it.

## Reversal trigger

If building the demo displaces burn-down or Phase A work for more than
one session-equivalent without owner direction, it comes back to DECIDE —
the demo is a credibility instrument, not the critical path. (Sequencing
of the build, when the owner wants it, goes to /program-management.)
