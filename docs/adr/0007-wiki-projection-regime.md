# ADR-0007 — The wiki is a projection: staged ADRs, generated registries, subordinate architecture model

Date: 2026-08-09 · Status: accepted
Deciders: John (owner-directed, in-session 2026-08-09) ·
Tracker: simic-dd5a578332

## Context

The design wiki (`tools/wiki/`, published at `/design/`) renders the Tier 0
chapters under the rule that the wiki is **generated, never authored**: every
transform happens on a throwaway staged copy, and `docs/design/` is never
edited to suit the renderer.

Three extensions now push against the edges of that rule and need their
status recorded rather than implied by tooling comments:

1. An architecture model (`docs/design/assets/model.dsl`, Structurizr DSL)
   was added *inside* the Tier 0 tree so that it is reviewed alongside
   chapter edits. ADR-0001 locked the chapter decomposition; a new
   non-chapter file in that tree needs its authority relationship to the
   chapters stated explicitly, or it will drift into being a second
   architecture.
2. The wiki gained a generated `reference/` section (diagram pages compiled
   from the model; registries scraped from `02-constitution.md` §18,
   `05-leyline-contracts.md` §9 and the `domains/` headings). Generated
   pages that *look* authored need a recorded rule saying they never are.
3. The Tier 1 ADRs (`docs/adr/`) are invisible in the published wiki —
   links to them escape to raw GitHub blobs, unvalidated — even though
   ADR-0004 and ADR-0005 amend live invariants. The tiering doc
   (`README.md` in `docs/adr/`) makes ADRs first-class design authority;
   the wiki should render them.

The citation convention (INV-nn, contracts by name, chapters by
path#anchor) produces dozens of plain-text `INV-nn` / `ADR-nnnn` citations
across the chapters. In the repo they are deliberate plain text; in the
wiki they can be links — but only if linkification is a render transform,
never an edit to the chapters.

## Decision

The wiki is a **pure projection of canon**, and each artefact's authority
is fixed as follows:

1. **`docs/design/assets/model.dsl` is canonical but subordinate.** It is
   a transcription of `../design/04-architecture.md` (§7.1, §7.5, §10) and
   the `domains/` chapters into Structurizr DSL, reviewed with chapter
   edits like any Tier 0 change. Where the model and a chapter disagree,
   **the chapter wins and the model is defective**. The build enforces the
   mechanical half of this: staging fails if the model's container
   identifiers stop matching `docs/design/domains/*.md` exactly. The
   mermaid fence in `04-architecture.md` §7.1 remains the chapter's own
   diagram; the model does not replace it.
2. **The `reference/` section is generated, never committed.** Diagram
   pages, the invariant registry, the contract registry and the domain
   roster are scraped from canon at render time by `tools/wiki/stage.py`,
   exist only in the staged tree, and fail the build on scrape surprises
   (non-contiguous §18 numbering, a domain chapter missing its heading)
   rather than publishing a partial registry. No hand-edits, no committed
   copies, no drift.
3. **ADRs are staged into the wiki, canonical where they are.** `docs/adr/`
   remains the Tier 1 home; staging copies it into the published tree
   (rendered under `decisions/`, template excluded) so ADRs are browsable,
   searchable and link-validated under `mkdocs build --strict`. Links from
   chapters to ADRs become in-wiki links instead of GitHub escapes.
4. **Citation linkification is presentation-only.** At render time,
   plain-text `INV-nn` and `ADR-nnnn` citations become links (per-invariant
   anchors are injected into the staged copy of `02-constitution.md` §18;
   ADR citations link to the staged ADR pages). The canonical files keep
   plain-text citations per the citation convention; the transform lives
   entirely in `stage.py`.

## Displaced constraints

None. ADR-0001's chapter decomposition is unchanged; no chapter text, name
or number moves. The Tier 0 tree gains one subordinate non-chapter file
(`assets/model.dsl`), whose subordination is the point of this ADR.

## Options considered

- **Move `docs/adr/` into `docs/design/`** so ADRs render without staging
  tricks. Rejected: the tiering (PDR-0002) deliberately separates Tier 1
  from Tier 0 — ADRs absorb change so the constitution stays stable — and
  ADR-0001 locked the Tier 0 layout. Staging achieves the rendering without
  the move.
- **Keep the model in `tools/wiki/`** as build tooling. Rejected: the
  architecture model is design content; hiding it in tooling would create
  wiki-owned parallel content, the exact failure the projection rule
  exists to prevent. In-tree-but-subordinate keeps review and authority
  aligned.
- **Hand-author registry pages** (invariant index, contract index).
  Rejected: parallel content; would drift from §18/§9 on the first
  amendment.
- **Linkify citations in the canonical files.** Rejected: churns every
  chapter, violates the render-only rule, and makes future amendments
  (a new invariant, a renumbered ADR) touch dozens of files instead of
  zero.

## Consequences

- The wiki build requires Java (Structurizr CLI + PlantUML jars, pinned by
  version, cached); CI pins Temurin 21 and caches the jars.
- ADR edits and additions republish the wiki: `docs/adr/**` joins the
  deploy workflow's trigger paths.
- A future ADR renumbering or invariant amendment changes wiki links
  automatically on the next render — nothing to update by hand.
- The model must be maintained alongside architecture-affecting chapter
  edits; the drift gate catches domain-set divergence mechanically, but
  edge/flow divergence still relies on review discipline.
