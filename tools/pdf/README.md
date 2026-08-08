# Simic HLD PDF pipeline

Renders the design chapters under `docs/design/` into one consolidated,
typeset PDF at `docs/assets/simic-hld.pdf`.

```bash
tools/pdf/build.sh              # build the PDF
tools/pdf/build.sh --check      # build, then verify the result
tools/pdf/check.sh              # verify an existing PDF
```

**`docs/design/` is the single source of truth and this pipeline never writes to
it.** Chapters are transformed at build time. The PDF is a generated artefact:
never hand-edit it, and never fix a rendering problem by editing a chapter's
prose when the fix belongs in the template.

## Requirements

| Tool | Version | Needed for |
|---|---|---|
| `pandoc` | >= 3.2 | Markdown to Typst. The Typst writer is only reliable from 3.2. |
| `typst` | >= 0.14 | Compilation. 0.11+ for `context`, 0.14+ for tagged PDF and `image(alt:)`. |
| `python3` | >= 3.10 | `preprocess.py`, `postprocess.py` (`X \| Y` type syntax). |
| `mmdc` | any | Optional. Renders mermaid diagrams; without it they fall back to monospace source. |
| poppler-utils | any | Optional. `pdfinfo`/`pdftotext`/`pdftoppm` for `--check`. |

`build.sh` checks the two hard version floors and fails with a clear message
rather than producing broken output. Built and verified against pandoc 3.9 and
typst 0.14.2.

Fonts must be installed system-wide; check with `typst fonts`. The template names
a fallback chain for each role, but the intended faces are **Libertinus Serif**
(body), **Lato** (headings) and **Noto Sans Mono** (code).

## Files

| File | Role |
|---|---|
| `build.sh` | Entry point: tool checks, assembly, pandoc, post-processing, compilation. |
| `check.sh` | Verifies a built PDF. Fails the build on a rendering regression. |
| `chapters.txt` | Chapter order, one path per line. **The only place ordering is defined.** |
| `metadata.yaml` | Title, version, author, licence, repo, site, cover abstract. |
| `preprocess.py` | Markdown-level transforms; assembles the chapters into one body. |
| `postprocess.py` | Repairs pandoc's Typst table output (widths, alignment, landscape). |
| `template.typ` | The design system. Owns all typography and layout. |
| `pandoc-typst.typ` | Pandoc template: cover, colophon, table of contents. |
| `build/` | Intermediates. `simic-hld.typ` is kept; it is the debugging artefact. |

Adding a chapter means adding a line to `chapters.txt`. `preprocess.py` warns
about any `docs/design/*.md` missing from the manifest, so a new chapter cannot
be silently omitted.

## Rendering decisions

**Section numbering.** The chapters carry the v4.1 monolith's own numbers in
their heading text (`## 18.`, `### 13.11`) and their heading *depths* already
agree with those numbers. Typst therefore adds no numbering of its own — doing so
would double up ("1.1 6.1 Strategy..."). Heading levels are passed through
untouched, and concatenating in concordance order yields one coherent hierarchy:
level 2 is a monolith section, level 3 a subsection, level 4 a sub-subsection.

**Section ordering is by chapter, not by section number.** Ordering follows the
`00-INDEX.md` concordance, and several chapters bundle non-adjacent monolith
sections: `01-claim.md` holds §1–§4 *and* §28–§29, `02-constitution.md` holds §5,
§18 and Appendix B, `03-principles.md` holds §6 and Appendix A. The document
therefore reads 1, 2, 3, 4, 28, 29, 5, 18, B, 6, A, 7… — this is what
chapter-order assembly yields, and it is correct. Chapters are the units ADR-0001
makes standalone and the units the project maintains and cites, so they are kept
whole; slicing them to force ascending section numbers would make the PDF's
structure diverge from the source of truth.

**Math.** Three notations appear in the chapters: `$$...$$` display, `$...$`
inline, and `\(...\)` inline. The last needs pandoc's
`tex_math_single_backslash` extension; without it the delimiters render as
literal parentheses. Pandoc's Typst math output was checked against
hand-written Typst and renders correctly — `u_{\mathrm{admit}}(c,s,H)` becomes
`u_(upright(a d m i t)) \( c \, s \, H \)`, which looks wrong as source but sets
as "u_admit(c, s, H)". No math filter is needed.

**Wide tables.** Pandoc derives Typst column widths from *source markdown*
character counts, which is a poor proxy for rendered width, so
`postprocess.py` corrects them: it drops pandoc's per-column `align`, strips the
`align(center)` wrapper that centres cell text (every table here is prose, so
cells are left-aligned), applies explicit width overrides for three tables, and
lifts starved columns in any other table. The §16.1 scaffold-withdrawal table has
six prose columns and cannot be rescued by width tuning at A4 portrait; it is
placed on a **landscape page** via `LANDSCAPE_TABLES`.

**Unwrappable content.** Typst does not line-break inside raw blocks or display
equations, so anything wider than the measure runs off *both* page edges. Both
element types are wrapped in a measure-and-scale shrink-to-fit in
`template.typ`: over-wide content is scaled down to fit, normal content is
untouched. `check.sh` fails the build if any line still exceeds the measure.

**HTML comments.** The `<!-- hld: ... -->` markers carry decomposition
provenance ("source: v4.1 monolith lines 3094–3142 · amended by ADR-0004"). They
render as a small grey note under each section heading, which is useful in a
document under active ADR governance. Turn off with `build.sh --no-provenance`.
The per-chapter boilerplate banner is always dropped.

**Cross-links.** Relative `.md` links cannot resolve in a PDF and are reduced to
their link text, which in this corpus already reads correctly ("ADR-0001",
"`05-leyline-contracts.md`"). Absolute `http(s)` links are left intact and stay
clickable. The 34 per-chapter `[← HLD index]` navigation links are dropped
entirely — they are site furniture, and the PDF's table of contents does that job.

**The 45 invariants.** `preprocess.py` wraps the §18 list in a
`::: {#simic-invariants}` div; pandoc emits that identifier as a Typst label,
and `template.typ` renders the enum markers as **INV-01 … INV-45** chips rather
than 1…45, matching how they are cited everywhere else. `check.sh` asserts all
45 are present and distinct, so a broken list fails the build.

Two traps here, both hit during development. A fenced div's *class*
(`::: invariants`) produces no Typst label at all — only an *identifier*
(`{#...}`) does. And the name must be prefixed: `<invariants>` is already
pandoc's auto-generated anchor for the "Invariants" heading in all fourteen
domain chapters, so a rule keyed on it would restyle fourteen unrelated lists.

**Diagrams: SVG if clean, otherwise raster.** Mermaid puts node labels inside SVG
`<foreignObject>` elements by default, and Typst does not render those
([typst#1421](https://github.com/typst/typst/issues/1421)) — such an SVG comes
out as correctly positioned, entirely **empty** boxes, silently.

The precondition that makes SVG safe is `htmlLabels: false` **at the config top
level**. Setting it only under `flowchart` is not enough: measured on this
repo's diagram, that leaves 28 foreignObjects and recovers edge labels only, node
labels still blank. At top level they are eliminated completely, and the SVG then
renders in Typst as perfect full vector — verified directly against
`tools/diagrams/theme-site-*.json` output, which already sets it that way.

So this pipeline checks an SVG before trusting it: a clean SVG wins on quality; an
SVG carrying foreignObjects is **refused** in favour of a raster sibling, with a
warning, rather than silently yielding empty boxes. The local `mmdc` fallback has
no such config and therefore renders PNG at scale 3.

Diagrams are placed on a dedicated landscape page — the architecture flowchart's
labels render at roughly 4pt at the portrait text measure.

Resolution order, most-preferred first:

1. A pre-rendered asset in `$SIMIC_DIAGRAM_DIR` (default
   `tools/diagrams/build/pdf/`) — the intended steady state once the shared
   diagram tooling has a `pdf` target. Format preference `.svg` (if clean),
   `.pdf`, `.png`. An asset outside the Typst root is staged into `build/`
   automatically, since Typst refuses to read above its `--root`.
2. A local `mmdc` render into `build/diagrams/` — a fallback so this PDF is
   buildable today.
3. The mermaid source as a monospace block.

Stems are looked up via `diagrams.map` first, then by content digest, then by
index. The map exists because the shared tooling names its diagrams semantically
(`core-loop`, `observation-loop`, `assurance-loop`) and those `.mmd` files are
hand-authored decompositions rather than copies of a chapter's embedded block — so
nothing matches automatically, and asserting equivalence is an editorial call. See
`diagrams.map` for the pending decision on `04-architecture.md` §7.1.

**This pipeline never writes to `tools/diagrams/`; it only reads.**

## Reproducibility

`build.sh` from a clean checkout produces the same PDF for a given revision. The
cover date comes from the last commit touching `docs/design/` (`git log -1
--format=%cs`), not from the clock; override with `SIMIC_PDF_DATE=YYYY-MM-DD`.
Diagram renders are content-hash-keyed and cached.

## Known issues and owner decisions

**`primary`/`accent` are an assumption, not a brand.** The project states no
brand palette. `template.typ` uses a deep teal with a moss-green accent, derived
from the blue-green Simic guild identity that names the project and its
subsystems. All contrast ratios clear WCAG 2.2 AA. Replace the two colours at the
top of `template.typ` to rebrand; nothing else hardcodes a colour.

**§16.1's progression is an equation but reads as a list.**
`programme/curriculum.md` expresses a four-stage prose progression as a single
`$$ \text{...} \rightarrow \text{...} $$` chain about 150 characters wide. The
shrink-to-fit keeps it on the page but leaves it small. It would set far better
as a list or with explicit line breaks in the source — a chapter-owner change,
not a template one.

**The architecture flowchart is dense.** The `04-architecture.md` mermaid
flowchart has twenty nodes with crossing edges. Even on a full landscape page its
labels are small. Splitting it into two diagrams (observation/commissioning loop,
then assurance/adjudication loop) would help both the PDF and the site.

**Predecessor naming is reported, not enforced.** `check.sh` warns with the count
and context of every predecessor mention rather than failing, because the
mentions are pre-existing chapter prose and their framing is broader than a
single fixed string. A new mention introduced by a chapter edit will show up in
the warning.

**`pdfinfo` prints a spurious syntax error.** poppler mis-validates the
`/Suspects false` boolean Typst writes into the tagged-PDF `MarkInfo`
dictionary. The file is well-formed (`Tagged: yes`, all metadata readable); the
message is filtered from build output.

**PDF/UA is not asserted.** Typst 0.14 tags the output by default, and the
diagram carries alt text, but `--pdf-standard ua-1` is not enabled: it would need
alt text and a verified reading order for every table and equation. Worth doing
if the document is ever published as an accessibility-conformant artefact.
