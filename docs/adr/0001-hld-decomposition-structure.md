# ADR-0001 — Decompose the HLD monolith into constitution-spine + domain + programme chapters

Date: 2026-08-08 · Status: accepted
Deciders: john (structure selected from four proposals in-session) · Tracker: simic-573b5b1c35, simic-80cc39ccfc

## Context

The v4.1 HLD was one 4,720-line file. The predecessor programme (esper) failed
in part because design documents grew to thousands of lines and had to be held
whole in context; even with large model contexts, attention needs structure.
The design-hardening wave programme (gate simic-0dd5362f05, adjudicated
2026-08-08) is about to edit the HLD heavily — editing a monolith serialises
those edits and forces every session to carry the whole document.

## Decision

Split `docs/concept/simic.md` into standalone chapters under `docs/design/`
(Option D — hybrid), organised as: a constitution spine (`01-claim` …
`07-counterfactual-engine`), one file per domain (`domains/`), a research
programme volume (`programme/`), operations (`ops/`), and appendices. Entry
point and §→file concordance: `00-INDEX.md`. Every working session loads
`02-constitution.md` plus exactly the chapters its task names.

The split is a **pure content-preserving move**: no wording changes; every
line of the monolith lands exactly once; injected lines are `<!-- hld: -->`
provenance comments only. Verified by script (partition of lines 1–4720 +
verbatim-exactly-once placement per slice). The monolith is archived at
`docs/concept/archive/simic-v4.1-monolith.md`; a pointer stub remains at the
old path; AGENTS.md now names `docs/design/00-INDEX.md` as the entry.

Refinements to the selected option, decided here: §6 + App A form
`03-principles.md` (not part of the constitution file, which stays minimal);
§15 lives with `domains/sarpadia.md`; §17 stays whole in
`programme/learning.md` rather than being interleaved into domain files — all
three preserve contiguous-slice extraction, which is what makes the move
mechanically verifiable.

## Displaced constraints

None. Content is unchanged; the §30 handoff declaration and Namespec 1.0 are
untouched. The *location* of the canonical text moves from one file to the
chapter set; the concordance keeps every legacy §-citation resolvable.

## Options considered

- **A — mirror split (file per §):** cheapest, but preserves the monolith's
  organisation; "everything about Augustin" still spans five files.
- **B — pure domain chapters:** best attention alignment, but cross-cutting
  mechanics get sliced and the migration invites accidental rewriting.
- **C — stability tiers (four volumes):** makes constitutional edits visible,
  but spreads one domain's story across three volumes.
- **D — hybrid (chosen):** C's change discipline for the constitution file,
  B's attention alignment for domains, contiguous slices throughout.

## Consequences

Easier: per-task context loading; parallel wave edits without collisions;
`doc structure = src/simic/<subsystem>/ = tests` alignment. Harder: ~34 files
to navigate (mitigated by `00-INDEX.md` reading paths); cross-cutting flows
rely on the index staying honest. Must update: AGENTS.md (done in the split
commit), skill-pack prompts (simic-e84fe6737c — cite chapters, not §-numbers),
CI doc-lint lane (simic-4da299ff46 — size budget, link check, orphan check).
Reversal trigger: if chapter cross-referencing measurably slows work compared
with the monolith, reconsolidate by ADR — but the esper evidence points the
other way.
