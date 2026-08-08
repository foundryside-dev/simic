# tools/wiki — the generated design-docs wiki

Builds `docs/design/` into the browsable wiki published at
**simic.foundryside.dev/design/**, alongside the hand-written marketing pages
at the root.

**The wiki is generated, never authored.** `docs/design/` is the canonical
design authority (ADR-0001) and the wiki is a pure projection of it: edit a
chapter, push, and the wiki follows on the next deploy. There is no parallel
content here — no copied prose, no hand-written nav, no per-chapter titles to
drift out of sync. If a chapter will not render correctly, the fix goes in
`mkdocs.yml` or `stage.py`, **never** in `docs/design/`.

## Build

```sh
pip install -r requirements.txt
./build.sh              # -> build/site/   (what CI publishes at /design/)
./build.sh serve        # live preview on http://127.0.0.1:8000
```

`build/` is git-ignored. CI runs the same `build.sh`, then copies `site/` to
the artifact root and `build/site/` to `/design/` — see
`.github/workflows/deploy-site.yml`.

`build.sh` refuses to run if the installed `mkdocs`, `mkdocs-material` or
`pymdown-extensions` differ from `requirements.txt`, because CI installs those
pins exactly and a local build against different versions would produce a
different site from the same commit while still passing `--strict`. Override
deliberately with `WIKI_ALLOW_VERSION_DRIFT=1 ./build.sh`.

`mkdocs build --strict` is used, so a broken cross-reference between chapters
**fails the deploy** instead of shipping. Every level in `validation:` is
`warn`, and under `strict: true` a warning aborts the build — so chapter-to-
chapter relative `.md` links, `#anchor` fragments (on another page *and* on
this one), root-relative `](/...)` links and unrecognised links are all hard
gates. Verified by injecting each kind and watching the build fail.

### 404s

mkdocs emits `404.html`, and it is published at `/design/404.html` — where
**GitHub Pages will never serve it**, because Pages only uses the 404 at the
*site* root. A mistyped `/design/...` URL therefore gets whatever `/404.html`
the marketing half provides. That file is outside this directory; nothing here
can fix it, and adding a wiki-local 404 would only produce a page nobody
reaches. Flagged rather than worked around.

## Files

| File | Role |
|---|---|
| `stage.py` | Copies `docs/design/` to `build/src/` and applies the render-only transforms |
| `hooks.py` | mkdocs hooks: canonical nav order, and edit links that point at the real source |
| `mkdocs.yml` | Theme, extensions, validation. `docs_dir` is the staged copy, never `docs/design/` |
| `requirements.txt` | Pinned mkdocs + plugins — `build.sh` refuses to build against a different version |
| `overrides/main.html` | Adds the announce-bar link back out to the marketing site at `/` |
| `overrides/partials/source.html` | Material partial override — drops the api.github.com call |
| `assets/mathjax-config.js` | Copied into the staged tree; configures MathJax delimiters |
| `assets/simic.css` | Simic tokens mapped onto Material, plus the diagram frame and contrast fixes |
| `build.sh` | Check the version pins, compile diagrams, stage, then build or serve |
| `../../docs/design/assets/model.dsl` | Structurizr model of the 14 domains — canonical, reviewed with chapter edits |
| `../../site/assets/mark.svg` | The brand mark, staged in — one mark in the repo, owned by the site half |

## What stage.py does, and why

`docs/design/` is written for humans reading the repo, not for mkdocs. The
transforms bridge the gap, all on a throwaway copy:

1. **`00-INDEX.md` → `index.md`**, with every link to it rewritten. mkdocs
   serves a directory's landing page from `index.md`; without this, `/design/`
   would 404 and the natural entry point would be buried in the nav.
2. **Links that escape `docs/design/` → absolute GitHub URLs.** Two chapters
   cite `../adr/...` and `../concept/archive/...` — real repo files, outside
   the wiki's document root. Rewritten, they resolve to the same content on
   GitHub instead of 404ing. If a chapter starts citing another out-of-tree
   directory, `stage.py` warns and `--strict` fails the build; add the prefix
   to `ESCAPING_PREFIXES`.
3. **A `title:` front-matter key on every chapter.** Only three of the 36 open
   with an H1 — the rest start at `## N.` because the section numbers came from
   the v4.1 monolith. Titles are derived *mechanically from the filename*
   (numeric prefix stripped, hyphens to spaces), so there is no hand-maintained
   title map to drift. Ordering still comes from the filename, so `01`–`07`
   stay in sequence.
4. **Support assets copied in**, because mkdocs resolves `extra_javascript`
   relative to `docs_dir`.
5. **The Tier 1 ADRs staged in as `decisions/`** (ADR-0007). `docs/adr/`
   stays the canonical home; the staged copies make the ADRs browsable,
   searchable and strict-validated, with `../adr/` links from chapters
   rewritten to in-wiki links instead of GitHub escapes. `TEMPLATE.md` is
   dropped; nav labels keep the number ("ADR-0004 Lexicographic admission").
6. **Citation linkification** (ADR-0007, render-only). Plain-text `INV-nn`
   and `ADR-nnnn` citations become links: each §18 invariant gets an
   `#inv-nn` anchor injected into the *staged* constitution (attr_list, so
   `--strict` validates the deep links), and ADR citations point at the
   staged pages. Code fences (both ``` and `~~~`), inline code, HTML comments
   (including multi-line ones) and self-references are left alone; the
   canonical files keep plain text per the citation convention.
7. **Heading levels normalised** so the shallowest heading on a page sits at
   `##`, directly under the `<h1>` the theme renders from the title. The
   `domains/*.md` chapters open at `### 13.x` — right in the v4.1 monolith,
   where §13 was a third-level section, and a heading-order break (WCAG
   1.3.1) once the page has its own H1. Chapters already opening at `##` are
   untouched. **The shift does not move anchors**: python-markdown slugs come
   from heading text, never its level, and the built heading ids were diffed
   either side of the change to prove it — 396 ids across 48 pages, zero
   changed. Inbound deep links from outside the repo survive.

Everything else is left exactly as written: the `<!-- hld: ... -->` provenance
comments (they render as nothing), the `[← HLD index]` breadcrumbs, the
`\(...\)` and `$$...$$` maths, and the mermaid fence in `04-architecture.md`.

## Navigation and edit links: `hooks.py`

Two things have to happen inside mkdocs, because they act on objects that only
exist once the staged tree has been read.

**Edit links.** `edit_uri` is a single prefix mkdocs appends the *staged* path
to, and three classes of page have no source there: `index.md` (staged from
`00-INDEX.md`), the eight `decisions/*` pages (staged from `docs/adr/`) and the
generated `reference/*` and section landing pages. GitHub turns
`edit/main/<path-that-does-not-exist>` into its **new-file editor**, so the
pencil invited a reader to create a second, divergent copy of a canonical
document inside `docs/design/`. `on_files` repoints the first two classes and
sets `edit_uri = None` on generated pages, which is what mkdocs' own
`File.edit_uri` docstring prescribes. `stage.py` lists the generated pages, so a
new one cannot quietly reacquire a broken link.

**Nav order.** Filename order is right for `01-`..`07-` and wrong everywhere
else: it listed the fourteen domains alphabetically, contradicting
`reference/domains.md` — generated by this same build — which lists them in
§13.x order, the order of the canonical sentence. `on_nav` restores the
canonical order, read from `00-INDEX.md`'s chapter-map table and the §13.x
headings, never from a hand-written list. Anything the canon does not mention
still falls back to filename order within its own section, so **adding a
chapter still needs no config change**.

## The generated `reference/` section

Beyond the transforms, `stage.py` *generates* pages that exist only in the
staged tree, never in `docs/design/` — pure projections, so they cannot drift
from the chapters they are scraped from:

| Page | Scraped from |
|---|---|
| `reference/diagrams.md` | The SVGs compiled from `docs/design/assets/model.dsl` (view descriptions come from the DSL) |
| `reference/invariants.md` | The 45 blocking invariants in `02-constitution.md` §18, labelled `INV-nn` as the chapters cite them |
| `reference/contracts.md` | The `### 9.x` contract headings in `05-leyline-contracts.md`, linked to their anchors |
| `reference/domains.md` | The `### 13.x Name — Epithet` heading of each `domains/*.md` chapter |
| `appendices/`, `ops/`, `programme/`, `reference/` `index.md` | A linked contents list of that section's staged files |

The scrapers fail the build on surprises (non-contiguous invariant numbering, a
domain chapter without its heading) rather than publishing a partial registry.

The section landing pages exist because without them `/design/appendices/` and
friends 404, and `navigation.indexes` leaves the section header linking
nowhere. They are contents lists only — no prose is invented, because inventing
prose would be authoring and this is a projection. `domains/` and `decisions/`
are excluded: they have real authored `README.md` chapters already.

## Compiled diagrams

`build.sh` exports every view in `docs/design/assets/model.dsl` with the
Structurizr CLI and renders SVGs with PlantUML (`-Playout=smetana`, PlantUML's
bundled layout engine, so no graphviz dependency). Both jars are **pinned by
version** and cached in `.cache/` (git-ignored): the first build downloads
them, every later build is offline.

The model serves the decided design, never the other way around: it is a
transcription of `04-architecture.md` §7.1/§7.5/§10 and the domain chapters,
and `stage.py` **fails the build** if its container identifiers stop matching
`docs/design/domains/*.md` exactly. If a diagram and a chapter disagree, the
chapter wins and the model is wrong — fix `model.dsl`.

The model itself is published at `/design/assets/model.dsl` and linked from the
diagrams page — compiled diagrams are only worth trusting if the source they
were compiled from is readable.

### Size and theme

The export is light-only and very wide — the ten views run 1305–4774px, against
a content column of roughly 589px. Both are handled at render time so the model
stays untouched:

- **Size.** Each figure sits in a frame that **scrolls** rather than shrinking
  past `--dmin`, and links to its full-size SVG. Fitting a 3792px diagram to
  the column put PlantUML's 12px labels at 2–3px; legibility beats fitting,
  which is the same call `site/style.css` makes for the marketing diagrams.
- **Theme.** The SVGs carry `background:#FFFFFF` and `#444444` text, so in
  slate they punched a white slab through an ink-950 page. `assets/simic.css`
  frames each one as a **light plate** — padded, bordered, rounded, inset from
  the page — so the light surface reads as a printed figure deliberately laid
  on the page rather than as a lighting bug. Nothing in the export is
  recoloured.

The alternative treatment — a second, recoloured SVG swapped on
`[data-md-color-scheme]`, the way the marketing site swaps its mermaid pair —
is written up in `stage.py`'s diagram section, along with the element-scoped
rules it would need. It is not shipped because it cannot be signed off without
looking at it, and it should not be adopted on reasoning alone. (A blanket CSS
`filter: invert()` is *not* the alternative: it inverts the teal accents too.)

`DIAGRAM_PALETTE` in `stage.py` lists every colour the export is allowed to
emit. A new style in `model.dsl` whose legibility on the plate nobody has
checked **fails the build** rather than publishing a diagram nobody has looked
at.

## Navigation

There is no `nav:` block. mkdocs derives the tree from the staged directory
structure, so **adding a chapter to `docs/design/` puts it in the wiki with no
config change** — which is the whole point. The derived titles label it, and
`hooks.py` orders it from the canon (see above) rather than from the
filesystem's alphabet.

## External dependencies

**The published wiki makes no third-party request**, which is the same rule the
marketing pages at `/` follow — they get there by shipping no JavaScript, the
wiki by vendoring everything at build time.

| Dependency | Why | Status |
|---|---|---|
| MathJax 3.2.2 | Renders the `$$` and `\(...\)` maths | Pinned, **vendored** into `assets/external/` |
| mermaid 11.12.0 | Renders the fence in `04-architecture.md` | Pinned, **vendored** — and it *displaces* an unpinned dependency: Material's bundle otherwise fetches `unpkg.com/mermaid@11`, which drifts |
| Google Fonts | — | **Disabled** (`theme.font: false`). Material otherwise fetches Roboto from `fonts.googleapis.com` on every page load |
| api.github.com | — | **Disabled** via `overrides/partials/source.html`. Material otherwise fetches star/fork counts on every page load |

`material/privacy` does the vendoring: it downloads each external asset during
the build into `build/site/assets/external/` (cached in `.cache/plugin/privacy`,
alongside the diagram jars) and rewrites the `src` attributes. Confirm it after
a version bump with:

```sh
find tools/wiki/build/site/assets/external -type f
grep -rhoE '(src|href)="https?://[^"]*"' tools/wiki/build/site --include='*.html' | sort -u
```

The second command should return only `github.com` links, which are navigation
a reader clicks, not resources the page fetches.

Two consequences worth knowing:

- **MathJax is the SVG build, not CHTML.** `tex-mml-chtml.js` resolves its
  `woff-v2` fonts from a path it builds at *runtime* relative to its own script
  URL, so no build-time vendoring step can discover them: privacy fetched the
  script and none of its fonts, and the maths would have rendered with fallback
  metrics. `tex-mml-svg.js` embeds every glyph as a path — 2.1 MB instead of
  1.2 MB, and genuinely self-contained. (`grep -c woff`: 5 in the CHTML build,
  0 in this one.) If you ever switch back to CHTML, the fonts have to be
  vendored explicitly.
- **Subresource Integrity is no longer needed and is no longer set.** SRI
  answers "did the CDN serve me different bytes" — a question that only exists
  for a runtime fetch. Nothing is fetched at runtime now. Keeping the hashes
  would only have added a version-bump trap where a stale hash blocks a
  *local* script.

Privacy also vendors Material's own `unpkg.com/mermaid@11` fallback URL, so the
guard-order trick in `extra_javascript` — loading our pinned mermaid first so
Material's `typeof mermaid == "undefined"` check never fires — is now a
belt-and-braces measure rather than the only thing standing between the wiki
and an unpinned dependency.

All three scripts are `defer`red: they are large, they previously blocked the
parser at the end of every page, and deferred scripts still execute in document
order and still finish before `DOMContentLoaded` — which is what both timing
dependencies need (`mathjax-config.js` before MathJax, and our mermaid before
Material's `document$`-driven loader looks for it).

## Known rough edge

The mermaid diagram in `04-architecture.md` §7.1 has fourteen nodes and forty-
odd edges; Material scales it to the content column, where the labels get
small. Leaving it that way is deliberate — the chapter is the source of truth
and the fence stays a fence. The legible-at-a-glance rendering of the same
architecture now lives on the generated diagrams page (`reference/diagrams.md`),
compiled from `model.dsl` — including focused subset views that the single
mermaid diagram cannot provide.
