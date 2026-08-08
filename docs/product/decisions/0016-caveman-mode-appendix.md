# PDR-0016 — Caveman Mode: plain-language summary as canonical Appendix G; source deck adopted

Date: 2026-08-08   Status: accepted   Author: Claude (product-owner session)
Owner sign-off: yes — owner supplied the deck, asked to shrink it and
"pull it apart and put the content on the wiki as a 'caveman mode'
summary".
Related: docs/design/appendices/caveman-mode.md, docs/misc/Growing_Big_Brain.pdf,
commit a8e41ac, simic-2c529002cf (the review rule applied)

## Context

The owner supplied "How We Grow Big Brain" (Gemini NotebookLM, 15
image-only slides, 25 MB) — a caveman-register explainer of the full
architecture — and wanted its content on the wiki, generated-not-
constructed rules intact.

## The call

The content was adapted (slides read visually; no extractable text) into
`docs/design/appendices/caveman-mode.md` — an explicitly **non-normative**
Appendix G that flows into both derived artifacts automatically (wiki page
live; HLD PDF 121 → 124 pp). The invariant-preservation review
(simic-2c529002cf) was applied and caught two deck defects that were
corrected in adaptation: the blindness framing (the Maker DOES see the
Scout's photograph; the Hitter/Elder never learn who made the rock —
INV-17/37) and the Reaper's missing warrant dependency (INV-27). The deck
itself was ghostscript-recompressed 25 MB → 2.2 MB at visually identical
quality and committed as provenance at `docs/misc/`.

**Faithful-report note:** the compression replaced the original file in
place; the untracked 25 MB original is not recoverable from this repo —
re-export from NotebookLM if the full-resolution original is ever needed.

## Rationale

The register fits the project's constitutional position that deliberately
goofy naming is load-bearing; a plain-language telling with an explicit
"constitution wins" disclaimer widens the audience without weakening the
canon. Putting it under docs/design/ (rather than site-only prose) is what
keeps it inside the derivation discipline and the preservation review.

## Reversal trigger

If the appendix is ever cited as authority in a design dispute (the
non-normative disclaimer failing socially), it moves out of docs/design/
to site-only content by a recorded decision.
