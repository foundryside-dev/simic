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

`mkdocs build --strict` is used, so a broken cross-reference between chapters
**fails the deploy** instead of shipping. Chapter-to-chapter relative `.md`
links and `#anchor` fragments are both validated.

## Files

| File | Role |
|---|---|
| `stage.py` | Copies `docs/design/` to `build/src/` and applies the render-only transforms |
| `mkdocs.yml` | Theme, extensions, validation. `docs_dir` is the staged copy, never `docs/design/` |
| `requirements.txt` | Pinned mkdocs + plugins |
| `overrides/partials/source.html` | Material partial override — drops the api.github.com call |
| `assets/mathjax-config.js` | Copied into the staged tree; configures MathJax delimiters |
| `build.sh` | Stage, then build or serve |

## What stage.py does, and why

`docs/design/` is written for humans reading the repo, not for mkdocs. Four
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

Everything else is left exactly as written: the `<!-- hld: ... -->` provenance
comments (they render as nothing), the `[← HLD index]` breadcrumbs, the
`\(...\)` and `$$...$$` maths, and the mermaid fence in `04-architecture.md`.

## Navigation

There is no `nav:` block. mkdocs derives the tree from the staged directory
structure, so **adding a chapter to `docs/design/` puts it in the wiki with no
config change** — which is the whole point. Filenames order the nav; the
derived titles label it.

## External dependencies

The marketing pages at `/` make zero external requests. The wiki does not
inherit that rule — JavaScript is expected here — but every third-party URL is
**pinned to an exact version**, and two of Material's defaults are switched off:

| Dependency | Why | Status |
|---|---|---|
| MathJax 3.2.2 (jsDelivr) | Renders the `$$` and `\(...\)` maths | Pinned |
| mermaid 11.12.0 (jsDelivr) | Renders the fence in `04-architecture.md` | Pinned — and it *replaces* an unpinned dependency: Material's bundle otherwise fetches `unpkg.com/mermaid@11`, which drifts. Loading our own first suppresses it. |
| Google Fonts | — | **Disabled** (`theme.font: false`). Material otherwise fetches Roboto from `fonts.googleapis.com` on every page load. |
| api.github.com | — | **Disabled** via `overrides/partials/source.html`. Material otherwise fetches star/fork counts on every page load. |

**To go fully self-contained**, vendor both scripts and drop the two CDN lines
from `mkdocs.yml`:

```sh
npm pack mathjax@3.2.2 mermaid@11.12.0
# unpack, then copy into assets/:
#   mathjax: es5/tex-mml-chtml.js + es5/output/chtml/fonts/woff-v2/
#   mermaid: dist/mermaid.min.js
# and reference them as assets/... instead of the https:// URLs
```
That adds ~2–3 MB to the repo and a node step to the build, which is why it is
not the default. It is a one-config-change decision, not a rewrite.

## Known rough edge

The mermaid diagram in `04-architecture.md` §7.1 has fourteen nodes and forty-
odd edges; Material scales it to the content column, where the labels get
small. Leaving it that way is deliberate — the chapter is the source of truth
and the fence stays a fence. If it ever needs to be legible at a glance, the
fix is to pre-render it through `tools/diagrams/` (which already does exactly
this for the marketing site) and have `stage.py` swap the fence for the image.
