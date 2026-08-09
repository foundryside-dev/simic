# PDR-0028 — Record the parallel-session design artifacts: design-wiki replatform (Astro + Starlight) and the kernel demo spec

Date: 2026-08-09   Status: accepted (recorded post-hoc; decisions made in
owner-attended parallel sessions, commits owner-co-authored)
Author: Claude (product-owner session 12)
Related: ADR-0001/ADR-0007 (projection regime the wiki design preserves),
PDR-0017 (session-7 wiki projection reconciliation), memory:
simic-wiki-build-invocation (mkdocs build path — still live until the
Astro site is built)

## Context

ORIENT found five commits on local main that no product record covered,
all from owner-attended parallel sessions on 2026-08-09:

- **692014f** — approved design for replacing the mkdocs wiki projection
  with a purpose-built **Astro + Starlight** site under `website/`:
  projection regime preserved (ADR-0001/0007), registries for
  invariants/domains/ADRs extracted from canonical chapters at stage time,
  citation integrity as a build gate, reading paths as first-class routes.
  Design only — 203 lines; the mkdocs path remains the live build until
  implemented.
- **25be1da..6b9f496** — the **kernel demo spec**, "Simic in 20 minutes":
  a single-file tech demo (one fixed host, one Wrenn slot, four fixed
  seeds, embedded-telemetry transformer Aurelia, 5-arm counterfactual fan
  per germination with offline-online GRPO, end-state-only reward,
  GPU-resident CIFAR), taken through four revisions with two SME panel
  rounds and a statistics audit (~6,100 lines under docs/concept/).

## The call

Both are recorded here for continuity, not relitigated — the owner was in
the loop in both sessions and co-authored the commits, which is the
sign-off. Product-state consequences worth naming:

1. The wiki replatform, once implemented, retires the mkdocs build
   invocation (and its memory note) and adds an implementation work item
   that is currently untracked — it should enter filigree when the owner
   wants it scheduled.
2. The kernel demo is a new standing artifact class (a demo spec, distinct
   from the HLD and the MVP phases). It is currently a concept document,
   not a roadmap bet; if it is to be built, that is a DECIDE for a future
   session and would enter the roadmap as intent.

## Reversal trigger

None of its own — this PDR records provenance. The wiki design carries its
own regime constraints (ADR-0001/0007); the demo spec becomes a product
decision only if/when the owner asks to build or schedule it.
