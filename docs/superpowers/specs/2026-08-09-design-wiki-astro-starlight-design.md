# Design Wiki on Astro + Starlight — Design

**Date:** 2026-08-09
**Status:** Approved design, pending implementation plan
**Replaces:** `tools/wiki/` (MkDocs Material projection of `docs/design/`, published at `/design/`)
**Untouched:** `site/` (the three hand-written zero-JS marketing pages at `/`)

## Problem

The design-docs wiki at simic.foundryside.dev/design/ is an MkDocs Material
projection of `docs/design/` + `docs/adr/`. It works, but:

- Material for MkDocs' long-term supportability is questionable, and deep
  design control means fighting theme overrides rather than owning components.
- The wiki's structural knowledge — the 45 INV-nn invariants, the 14 domains,
  the ADR set — exists only as prose conventions. `stage.py` already parses
  invariants for anchors and linkifies `INV-nn`/`ADR-nnnn` citations, but
  nothing validates the other direction: a dangling citation, an orphaned
  invariant, or a renumbering publishes silently.
- Navigation is a chapter list. For a document set this cross-referential,
  the reading paths, invariant citations, and domain structure should be
  first-class navigable surfaces.

This design adapts the approach proven in
`~/agentic-coding-threat-model/docs/superpowers/specs/2026-08-09-unified-site-astro-starlight-design.md`
(schema-validated registries, single Node toolchain, build-failing link
integrity), with one structural difference: that project migrated content
*into* its site as a new home; Simic's wiki is a **projection** (ADR-0001,
ADR-0007) and must remain one. The chapters are canonical and are never
edited to suit the renderer.

## Decision summary

- **One new top-level `website/` directory** holds an Astro + Starlight
  project that replaces `tools/wiki/` at cutover. `site/` is untouched; the
  built wiki continues to deploy under `/design/`.
- **The projection regime survives.** A Node stager (replacing `stage.py`)
  builds from a throwaway copy of `docs/design/` + `docs/adr/`; nothing under
  `website/build/` is committed; "edit this page" points at the canonical
  chapters on GitHub.
- **Registries are extracted, never authored.** Invariants, domains, and ADRs
  are parsed from the canonical chapters at stage time into generated JSON
  data collections, validated by zod schemas. There is no second copy to
  drift — a malformed chapter edit fails the build with a pointed error.
- **Citation integrity is a build gate.** Dangling `INV-nn` / `ADR-nnnn` /
  domain references, orphaned invariants after a renumbering, and reading
  paths naming missing chapters all fail the build.
- The Structurizr/PlantUML diagram pipeline (`model.dsl` → SVGs via the
  pinned jars and JDK) is kept as-is; its SVG output is staged in.

## Architecture

```
docs/design/ + docs/adr/          canonical, never edited for the renderer
        │
        ▼
website/stager/  (Node, replaces tools/wiki/stage.py)
  ├─ copies chapters + ADRs into a throwaway build/content/ tree
  ├─ extracts registries → build/data/{invariants,domains,adrs}.json
  ├─ records every INV-nn / ADR-nnnn citation site (for backlinks)
  ├─ rewrites out-of-tree links → GitHub, in-tree links → wiki routes
  └─ validates citations (dangling refs = build failure)
        │
        ▼
astro build  (Starlight; content collections + zod schemas over build/*)
  ├─ starlight-links-validator: broken internal links + anchors fail
  └─ Pagefind search index (Starlight default)
        │
        ▼
website/dist/  → deployed at /design/
```

Starlight supplies the commodity machinery — sidebar, search, dark/light,
mobile layout, link validation — so effort goes to the Simic-specific
surfaces. A bespoke no-framework Astro build and an extend-mkdocs option were
considered and rejected: the former hand-builds weeks of undifferentiated
machinery (and becomes its own supportability risk), the latter keeps the
Material dependency and buys no design control.

## The three registries

All three are **extracted, never authored**. The zod schemas validate what
the parser produced. Parser error messages must name the file and line; the
expected chapter formats are documented in `website/README.md` as a contract
on the chapter set. (Header-format parsing is brittle by design: format drift
becomes a build failure, not silent wrongness.)

**Invariants** — parsed from `docs/design/02-constitution.md` §18: numbered
item → `INV-nn`, bold label → name, body → text, trailing `(ADR-nnnn)` → ADR
link. Produces:

- `/design/invariants/` registry index, filterable by domain touched and
  ADR-backed status, with a per-invariant anchor.
- **Backlinks**: the stager records every `INV-nn` citation site across
  chapters, so each invariant shows "cited by: 03-principles §…, isperia, …".
- Build failures on: a citation of a nonexistent invariant (e.g. `INV-46`),
  and a constitution renumbering that orphans existing citations.

**Domains** — one record per `docs/design/domains/*.md` (14): name,
verb/mandate (from the constitution's canonical sentence), faction
(Phyrexian synthesis core vs governance cage, per Namespec 2.0 / ADR-0008),
cross-references. Produces:

- `/design/domains/` index rendering the canonical sentence as a navigable
  strip, grouped by faction.
- A generated infobox at the top of each domain page: verb, faction,
  forbidden decisions, invariants that name the domain.

**ADRs** — parsed from `docs/adr/` headers (`Date: … · Status: …`). Produces:

- `/design/adr/` index with status column.
- Validated two-way links: chapters and invariants cite ADRs; each ADR page
  shows which invariants and chapters cite it.

The registry JSON shapes are chosen so plainweave (ADR-0002) could consume or
verify them later; no plainweave coupling in v1.

## Information architecture & navigation

The chapter tree stays the spine; generated surfaces are added alongside:

```
/design/                     Landing: what the HLD is, reading paths, canonical sentence
/design/chapters/…           00-INDEX … 07-counterfactual-engine (authored order)
/design/domains/             Domain index (canonical-sentence strip, faction grouping)
/design/domains/<name>/      14 domain pages, each with generated infobox
/design/invariants/          Invariant registry (filterable index)  ← generated
/design/adr/                 ADR index + staged ADR pages           ← index generated
/design/appendices/…         glossary, newsroom, scaffold-pattern, …
/design/programme/, /ops/    as in the tree today
/design/diagrams/            the rendered Structurizr views
```

- **Reading paths as first-class routes.** 00-INDEX's reading paths become
  guided sequences: prev/next footer navigation within a path and a "you are
  on the X path, step 3 of 7" indicator. Paths are parsed from 00-INDEX (the
  index stays canonical); a path naming a missing chapter fails the build.
- **Citation hovers.** `INV-nn` and `ADR-nnnn` citations in prose become
  links with hover popovers (invariant name + first sentence), driven by the
  registry data.
- **Sidebar** groups: Chapters / Domains / Invariants / ADRs / Appendices /
  Programme & Ops (Starlight collapsible sidebar).
- **Search**: Pagefind (Starlight default), full-text, client-side, includes
  generated registry pages.

## Identity

- Theming from the **simic-design skill's tokens**, applied as Starlight CSS
  custom-property overrides — same source of truth as `site/style.css`, so
  `/` and `/design/` agree on palette.
- Same font policy as today: no third-party font requests (system stack, or
  self-hosted faces if the simic-design skill specifies them).
- Dark/light: Starlight's three-state toggle (OS default + explicit
  override), matching the current wiki's model; the marketing pages keep
  their two-state zero-JS behavior.
- The brand mark is staged from `site/assets/mark.svg` at build time — one
  file, one place it is edited, as now.

## Build, deploy, verification

- `deploy-site.yml`: swap the Python/mkdocs steps for Node (`npm ci` →
  stager → `astro build`), keep the Java diagram step and the existing
  `tools/ci` pre-upload gate. `site/` is assembled with `website/dist/` at
  `/design/` exactly as today. Version pinning via `package-lock.json`; the
  pip pin-drift check dies with mkdocs. Local: `npm run dev` (stager in
  watch mode or run-before).
- **Gates, all build-failing:** registry extraction errors; dangling
  citations; reading-path integrity; `starlight-links-validator` (internal
  links *and anchors*); external-link checking retained (port of
  `check_links.py` or a Node equivalent).
- **Testing:** the stager gets unit tests — parser fixtures with a
  known-good constitution excerpt plus deliberately malformed ones asserting
  pointed errors — and one snapshot-style test that the staged tree for the
  current repo builds clean. These run in the wiki CI path, not the Python
  test suite.

## Migration approach

1. Scaffold `website/` (Starlight, stager skeleton, schemas, tokens); CI
   builds it to a preview path alongside the live wiki.
2. Port the stager transforms from `stage.py` (link rewriting, provenance
   masking, heading normalisation, title derivation) and add the registry
   extractors with their tests.
3. Build the generated surfaces: invariant registry + backlinks, domain
   index + infoboxes, ADR index, reading-path routes, citation hovers.
4. Verification: page-inventory checklist (every page in the current wiki
   accounted for), all gates green, visual spot-check of infoboxes and
   diagrams in both themes.
5. Cutover: deploy workflow points at the new build; delete `tools/wiki/`;
   append a superseding note to ADR-0007 recording that the projection
   regime survives with a new renderer (the regime is the ADR's substance,
   the toolchain an implementation detail).

## Out of scope

- Any change to `site/` or the marketing pages' zero-JS regime.
- Glossary popovers (v1 defers the glossary collection).
- Contract-shape registry — waits on the §9 contract shapes
  (filigree simic-0bf2c40dec).
- Plainweave integration (registry JSON is shaped for later adoption).
- Any change to `docs/design/` content or the PDF pipeline.
- URL preservation for individual wiki pages: the `/design/` root stays, but
  per-page paths may change with the new IA; no redirects.
