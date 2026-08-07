# PDR-0009 — Decompose the HLD into chapters before any wave edits

Date: 2026-08-08   Status: accepted   Author: Claude (product-owner session)
Owner sign-off: yes — owner directed the decomposition ("the first thing I
want to do"), selected structure Option D from four proposals in-session, and
directed the tech-writer verification pass.
Related: ADR-0001 (docs/adr/), simic-573b5b1c35 (closed), simic-80cc39ccfc
(closed), commits 0e0f1ea + ca25d92

## Context
The v4.1 HLD was one 4,720-line file. Owner-stated: esper failed in part
because design documents grew to thousands of lines and had to be held whole
in context; even with large model contexts, attention needs structure. The
wave programme (PDR-0008) was about to edit that file heavily.

## The call
Split the monolith into 34 standalone chapters under docs/design/ (Option D
hybrid — constitution spine + domain chapters + programme volume; structure
and mapping recorded in ADR-0001) **before** wave:1 starts. Pure
content-preserving move, script-verified, then independently verified by four
tech-writer review agents (zero blockers; byte-exact four ways), with their
findings applied as a separate visible commit. Every working session now
loads the small locked constitution chapter plus exactly its task's chapters.
Citation convention (INV-nn, contract names, path#anchor) replaces bare
§-numbers in new text; a §→file concordance keeps legacy citations resolvable.

## Rationale
This is the counter-design to a named esper failure mode, applied to the
programme's own documents — the same move as the product's "unrepresentable
by construction" principle: sessions physically cannot be forced to hold the
whole design in attention, and renumbering can no longer break consumers.

## Reversal trigger
ADR-0001's: if chapter cross-referencing measurably slows work compared with
the monolith, reconsolidate by ADR. The doc-lint lane (simic-4da299ff46) is
the standing guard on size budget and link integrity.
