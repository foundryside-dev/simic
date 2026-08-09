# ADR-0009 — Demote the newsroom analogy to a single appendix rendering

Date: 2026-08-09 · Status: accepted
Deciders: John (owner-directed, product session 11) · Tracker: simic-7e2683f3cd

## Context

Namespec 2.0 (ADR-0008) locked the codename grammar as the design's operating
frame: the canonical sentence, the faction layer, and the sentence lint in
`../design/02-constitution.md` are how authority is stated, checked, and
smelled. The newsroom analogy, however, still operates as a second co-primary
frame: the constitution carries a full fourteen-role newsroom sidebar
(§5.5), `../design/04-architecture.md#76-the-newsroom-authority-model`
repeats the complete mapping, the README and public site introduce the
architecture as "deliberately resembling a newsroom", and several Tier-0
constraint lists cite "the newsroom rule" as if the metaphor were the rule's
identity.

Two parallel operating analogies split the design's voice. Every authority
change must be narrated twice; the metaphor reads as normative when the
enforcement was always contractual — INV-07 (direct evidence publication),
INV-09 (assignment-brief boundary), blinding by schema absence, and the
authority tests. One frame must own the design; the other must serve it.

## Decision

The Namespec 2.0 codename grammar is the sole operating frame. The newsroom
becomes exactly one thing: **Appendix E**
(`../design/appendices/newsroom.md`), reframed as an alternative rendering
of the authority model — a deliberate second way in for readers to whom the
codenames do not speak. It stays tightly coupled to the design: any change
to an authority boundary must update the rendering in the same change set.
It is no longer given primacy anywhere else.

Mechanics:

- Normative statements formerly cited as "the newsroom rule" are cited by
  their invariants: **INV-07** and **INV-09** (with INV-08, INV-10, INV-11,
  INV-12 supporting). The rule was never the metaphor.
- Chapters keep at most a one-line pointer to Appendix E; no chapter carries
  a parallel role mapping. The §5.5 sidebar and the §7.6 mapping collapse to
  native statements of the routing rule plus the pointer.
- Appendix-tier and implementation-surface couplings are retained: the
  glossary's newsroom column, the package-README "Newsroom analogue, where
  useful" line, Tamiyo's optional newsroom projection (`newsroom_view.py`),
  and the good/bad-sentences translation aid.
- Historical records (the archived monolith, ADR bodies 0001–0008, PDRs,
  peer reviews) are never rewritten (INV-36).

## Displaced constraints

None. INV-07, INV-08, INV-09, INV-10, INV-11 and INV-12 are unchanged in
wording and force. The Tier-0 constraint lists that named "the newsroom
rule" (`README.md` in `docs/adr/`, `../design/ops/repo-structure.md`
§30, and the repo-discipline line of the authority grant) now name **the
evidence-routing rule (INV-07/INV-09)** — a citation rename, not a
constraint change.

## Options considered

- **Keep both frames co-primary (status quo).** Rejected: two operating
  analogies split the voice, double the narration cost of every authority
  change, and let the metaphor masquerade as the enforcement mechanism.
- **Delete the newsroom entirely.** Rejected: it is genuinely useful to
  readers outside the codename idiom, and live design surface couples to it
  (Tamiyo projection, glossary column, package-README line); deletion would
  orphan those and discard a good teaching instrument.
- **Move it outside the HLD (site/marketing only).** Rejected: outside
  design custody it would drift from the authority model it renders; the
  appendix keeps it under the ADR discipline and the same-change-set
  coupling duty.

## Consequences

The constitution gets shorter and speaks with one voice; Appendix E becomes
the only complete mapping and explicitly carries the duty to track authority
changes. Updated in this change set: `02-constitution.md` §5.5,
`04-architecture.md` §7.6 and the Tamiyo view line, `01-claim.md`,
`03-principles.md` 6.9, `appendices/newsroom.md` (reframed),
`00-INDEX.md`, `appendices/good-bad-sentences.md`, `ops/migration.md`,
`ops/repo-structure.md` §30, `assets/model.dsl`, `AGENTS.md`,
`ARCHITECTURE.md`, `README.md`, `docs/adr/README.md`, the vision
repo-discipline citation (mechanical; flagged for grant review), and the
public site pages. Wiki and site gates re-run.

Reversal trigger: if new contributors or publication reviewers repeatedly
fail to grasp the authority model from the codenames alone, re-promote a
condensed mapping into `04-architecture.md` — by ADR, never silently.
