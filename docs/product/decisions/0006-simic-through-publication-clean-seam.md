# PDR-0006 — Simic is the name through publication; predecessors present as a clean seam

Date: 2026-08-08   Status: accepted   Author: Claude (product-owner session)
Owner sign-off: yes — owner-stated in-session 2026-08-08.
Related: HLD §27.1, PDR-0004 (reset rationale), simic-0dd5362f05 (gate docket),
vision.md (Purpose)

## Context
§27.1 left the umbrella name open (remain `simic`, return to `esper`, or adopt
another). The working-name half had to settle before Phase A creates
`src/simic/`; the publication-identity half was going to be deferred to the
publication gate. The owner resolved both at once.

## Options considered
1. **`simic` throughout, predecessors as history (chosen)** — the published
   system is presented as a clean seam; esper/esper-lite become an anecdote in a
   future "history of simic" document and candidate material for a
   "how not to run an ML project" autopsy.
2. **Return to `esper` (publication as ESPER v3)** — rejected: continuity naming
   contradicts the clean-cut reset rationale (PDR-0004); the old name carries
   the failed instrument's baggage.
3. **New name at publication** — rejected as default: no benefit over `simic`
   once the seam is clean; revisitable only if an external constraint (e.g. a
   trademark-level collision) forces it.

## The call
`simic` is the repository, package, and presumptive publication name. The
predecessors are presented as lineage history, not identity — whatever succeeds
is a clean seam. Formal closure of §27.1 in the HLD lands as an ADR (per the
PDR-0002 tiering) at or alongside the decision-gate session; proposed resolution
filed on the gate docket. Publication itself remains owner-gated regardless
(authority grant: external actions escalate).

## Rationale
The name should tell the same story the reset rationale tells: a new instrument,
not a patched one. The raw material for the eventual history/autopsy documents
is already being kept deliberately (peer review, esper-lite CI/controls review,
the esper-lite defect register) — complete-history discipline applied to the
programme itself, not just to Sarpadia.

## Reversal trigger
Reopen only if an external naming constraint surfaces at the publication gate,
or if the §27.1 ADR adjudication uncovers a conflict not visible now. Absent
that, the decision stands unrevisited — naming churn is pure cost.
