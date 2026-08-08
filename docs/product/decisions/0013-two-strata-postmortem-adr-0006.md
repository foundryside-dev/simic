# PDR-0013 — Two-strata post-mortem adopted; silent-defaulting telemetry access banned (ADR-0006)

Date: 2026-08-08   Status: accepted   Author: Claude (product-owner session)
Owner sign-off: yes — owner corrected the session's one-stratum reading
in-session ("it's not that it's not real, it's we paid our dues fixing
it") and supplied ADR-0006's core rule and CI additions directly.
Related: ADR-0006, simic-108cdb52bc (closed), simic-00351db32e (closed),
simic-5503bbe389 (Gate-0 harness), 01-claim.md §2.6, 03-principles.md §6.20

## Context

The session initially recorded the esper post-mortem as a single stratum
(learning-loop/instrument failures) and called the external reviewers'
".get() returned zeros" story a folk narrative. The owner corrected this:
the silent-zero era was real — machine-generated telemetry code with
hallucinated interfaces, masked by permissive defaulting access, fixed at
the time with a custom CI ban — and it simply predates the esper-lite
memory record because the dues were already paid.

## The call

The canonical lineage is **two scar strata** (telemetry-access corruption,
then learning-loop/statistical failure), codified in `01-claim.md#26` and
`03-principles.md#620`, with the armour facing both directions. The
code-level rule became **ADR-0006**: typed, explicit, fail-closed
telemetry access; absent is `None` or `validity_mask=false`, never a
fabricated default; CI rejects untyped defaulting access on contract
paths; hallucinated field names fail closed. Framed explicitly as an
AI-code-generation safety rule. Enforcement wiring is Phase A work; the
poison-pill harness (simic-5503bbe389) is its acceptance gate.

## Rationale

Collapsing the strata is the error in both directions: stratum one alone
(the reviewers' version) hides that hardened telemetry did NOT save the RL
loop; stratum two alone (the session's overcorrection) erases a real,
paid-for scar and the CI ban it justified. Both defend different armour.

## Reversal trigger

ADR-0006's: the principle (absent-is-never-zero) has none — it is
constitutional; the lint mechanism may narrow scope (to Leyline contract
types) by superseding ADR if false positives on non-contract mappings
prove costly, never by relaxing contract paths.
