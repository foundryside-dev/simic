#!/usr/bin/env python3
"""Stage docs/design/ into a build directory mkdocs can consume.

The design chapters are the canonical authority and are NEVER edited to suit
the wiki. Anything the renderer needs is done here, on a throwaway copy, so
`docs/design/` stays exactly as its owner wrote it and the wiki stays a pure
projection of it: edit the chapter, re-render, the wiki follows.

Ten transforms, each with a reason:

1.  `00-INDEX.md` -> `index.md`, and every link to it rewritten.
    mkdocs serves a directory's landing page from `index.md`/`README.md`.
    Without this, `/design/` would 404 and the natural entry point would be
    buried in the nav like any other chapter.

2.  Links that escape `docs/design/` -> absolute GitHub URLs — except ADRs.
    Chapters cite `../adr/...` and `../concept/archive/...`, which are real
    files in the repo but outside the wiki's document root. The ADRs are
    staged INTO the wiki (transform 7), so `../adr/` links become in-wiki
    links validated by --strict; everything else still escapes to GitHub.

3.  A `title:` front-matter key injected into every chapter.
    Only three of the 36 chapters open with an H1 — the rest start at `## N.`
    because the section numbers came from the v4.1 monolith. Without a title
    mkdocs falls back to the filename, so the nav would read "04 architecture",
    and using the first `##` would label chapter 04 with "7. System Context",
    which is worse. The injected title is derived mechanically from the
    filename (numeric prefix stripped, hyphens to spaces) — presentation only,
    no hand-authored titles to drift out of sync with the chapters.

4.  Support assets copied in: the MathJax config and extra CSS (mkdocs
    resolves `extra_javascript`/`extra_css` relative to `docs_dir`, so they
    have to live inside the staged tree), and the brand mark, taken from
    `site/assets/mark.svg` so the repo holds exactly one copy of it.

    `docs/design/assets/model.dsl` rides along in the copytree and is
    PUBLISHED at `/design/assets/model.dsl`. That is deliberate, not an
    accident of the copy: the compiled diagrams are only trustworthy if the
    model they came from is readable, so reference/diagrams.md links to it.

5.  `TEMPLATE-lld.md` is dropped from the staged tree.
    It is authoring scaffolding (the Tier 2 LLD header template), not a
    chapter: publishing it gave the wiki a nav entry full of angle-bracket
    placeholders. The index's chapter map mentions it as inline code only,
    so nothing links to it; readers who need it find it in the repo.

6.  The `[<- HLD index]` breadcrumb line is stripped from every chapter.
    It exists for people reading the markdown on GitHub; in the wiki the
    nav, tabs and logo already do that job, so it rendered as a stray
    dangling link at the top of all 34 pages.

7.  `docs/adr/` is staged in as `decisions/` (ADR-0007). ADRs are Tier 1
    design authority and two of them amend live invariants; leaving them as
    GitHub-escape links kept them out of the wiki's nav, search and link
    validation. They remain canonical at `docs/adr/`; `TEMPLATE.md` is
    dropped for the same reason as TEMPLATE-lld.md.

8.  Citation linkification (ADR-0007, presentation-only). Plain-text
    `INV-nn` and `ADR-nnnn` citations — deliberate plain text in the repo,
    per the citation convention — become links in the wiki: per-invariant
    anchors are injected into the staged constitution's §18 list, and ADR
    citations link to the staged pages. Code fences (both ``` and ~~~),
    inline code, HTML comments (including multi-line ones) and
    self-references are left alone.

9.  Heading levels normalised on chapters that start below H2.
    The `domains/*.md` chapters open at `### 13.x` — correct in the v4.1
    monolith, where §13 was a third-level section — so the rendered page ran
    H1 (the theme's title) straight to H3, a WCAG 1.3.1 heading-order break on
    all fourteen, under a synthesised title duplicating the chapter's own.
    They now shift up so the chapter heading IS the page H1 and the theme
    injects nothing; `sarpadia.md`, which carries two headings at that level
    (§13.3 and the §15 data model), shifts to H2 instead so the page still has
    exactly one H1. Chapters already opening at `##` are untouched. The shift
    is anchor-neutral: python-markdown slugs come from heading TEXT and never
    encode level — verified by diffing the built heading ids either side of
    the change (396 ids across 48 pages, zero changed).

10. Sections get a landing page at `index.md`. `domains/README.md` and
    `decisions/README.md` are authored chapters and are renamed into place
    (with links to them rewritten); `appendices/`, `ops/`, `programme/` and
    `reference/` have no such chapter, so a contents list is generated. Before
    this, four section URLs 404'd and `navigation.indexes` had nothing to hang
    a section header on. No published URL moves: mkdocs already served
    `README.md` as the section index, so `/design/domains/` was and remains
    the address.

Everything else — the `<!-- hld: ... -->` provenance comments, `\\(...\\)` and
`$$...$$` math, the mermaid fence in 04-architecture.md — is left untouched
and handled by mkdocs config.

Beyond the transforms, staging GENERATES a `reference/` section: registry
pages scraped from the canonical chapters (invariants from 02-constitution.md
§18, contracts from 05-leyline-contracts.md §9, the domain roster from
domains/*.md) plus a diagrams page for the SVGs compiled from
docs/design/assets/model.dsl by build.sh, and a landing page for each section
that has no authored README. Generated pages exist only in the staged tree —
never in docs/design/ — so they cannot drift: re-render and they follow the
chapters. The same step enforces the model's subordination to the canon: if
model.dsl's container set stops matching domains/*.md, or the export uses a
colour nobody has checked against the light plate the diagrams sit on, the
build fails here rather than publishing a diagram that contradicts the text or
that nobody has looked at.

Staging also writes `build/nav-order.json`: the canonical nav order (read out
of 00-INDEX.md's chapter map and the §13.x domain headings) and the list of
generated pages. `hooks.py` consumes both — the first to order the sidebar as
the chapters declare rather than as the filesystem sorts, the second to
suppress the "edit this page" link on pages that have no source to edit.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from collections.abc import Iterator
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
SOURCE = REPO / "docs" / "design"
STAGED = HERE / "build" / "src"
ASSETS = HERE / "assets"
# The brand mark is the marketing site's, not a second copy kept in step by
# hand: one file, one place it is edited, and the wiki picks it up on render.
BRAND_MARK = REPO / "site" / "assets" / "mark.svg"

GITHUB_BLOB = "https://github.com/foundryside-dev/simic/blob/main/docs"

# Paths that exist in the repo but outside SOURCE. A relative link to one of
# these is correct in the repo and broken in the wiki, so it becomes a link to
# the same file on GitHub. Extend this list if a chapter starts citing another
# out-of-tree directory; the link check in build.sh will tell you when.
# `adr/` is NOT here: ADRs are staged into the wiki (transform 7), so links
# to them are rewritten in-tree instead of escaping.
ESCAPING_PREFIXES = ("concept/", "product/")

ADR_SOURCE = REPO / "docs" / "adr"
ADR_STAGED_DIR = "decisions"

DIAGRAMS = HERE / "build" / "diagrams"
# Build metadata consumed by hooks.py, not a published page.
NAV_ORDER = HERE / "build" / "nav-order.json"

# Presentation order for the diagrams page: overview first, then the focused
# flows, then component internals. Views missing from this list (a new view
# added to model.dsl) still render, appended alphabetically — the list orders,
# it never filters.
VIEW_ORDER = [
    "SimicContext",
    "SimicContainers",
    "CoreGrowthFlow",
    "QaAdjudication",
    "MaintenanceLoop",
    "ArchiveIngestion",
    "RequestResolution",
    "MomirComponents",
    "UrabraskComponents",
    "AugustinComponents",
]

# Hyphenated filename fragments that stand for a slashed term in prose.
SLASH_PAIRS = (("good", "bad"),)

# Staged paths of pages this script GENERATES (no counterpart in docs/design/
# or docs/adr/). hooks.py suppresses the "edit this page" pencil for these:
# mkdocs' own File.edit_uri docstring says generated files should have none,
# and pointing GitHub at a path that does not exist opens its new-file editor.
GENERATED_PAGES: list[str] = []

GENERATED_BANNER = (
    '!!! note "Generated page"\n'
    "    Built by `tools/wiki/stage.py` from {source} at render time. "
    "Nothing here is authored: cite the canonical chapter, not this page.\n\n"
)


def slugify(text: str) -> str:
    """Mimic python-markdown's toc slugify, so links into chapter headings
    resolve under mkdocs' anchor validation. "9.1 `StrategicEnvelope`" and its
    rendered heading both become "91-strategicenvelope"."""
    text = text.replace("`", "")
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[\s]+", "-", text.strip())


def derive_title(rel: Path) -> str:
    """A nav title from the filename alone. Mechanical, so it cannot drift.

    `04-architecture.md`               -> "Architecture"
    `programme/risks-and-open-decisions.md` -> "Risks and open decisions"
    `domains/augustin.md`              -> "Augustin"

    The numeric prefix is dropped from the *label* only; mkdocs still orders
    the nav by filename, so 01..07 stay in sequence.
    """
    stem = rel.stem
    if stem in ("index", "README"):
        stem = rel.parent.name or "index"
    # Staged ADRs keep their number in the nav label: "ADR-0004 Lexicographic
    # admission", matching how the chapters cite them.
    adr = re.match(r"^(\d{4})[-_]", stem) if rel.parts[0] == ADR_STAGED_DIR else None
    stem = re.sub(r"^\d+[-_]", "", stem)
    # Vocabulary pairs the project writes with a slash. A filename cannot carry
    # `/`, so "good-bad-sentences" has to be re-joined or it reads "Good bad
    # sentences" instead of "Good/Bad sentences". Closed and mechanical, in the
    # same spirit as `acronyms` below — a vocabulary rule, not a per-file title.
    for a, b in SLASH_PAIRS:
        stem = re.sub(rf"\b{a}-{b}\b", f"{a}/{b}", stem)
    words = [w for w in re.split(r"[-_]", stem) if w]
    # Acronyms the project uses as words; without this "TEMPLATE-lld" reads
    # "Template lld". Mechanical and closed — not a per-file title map.
    acronyms = {"lld", "hld", "qa", "adr", "mvs", "api", "rl"}
    words = [w.upper() if w.lower() in acronyms else w for w in words]
    label = " ".join(words)
    # Capitalise both halves of a slashed pair: "Good/bad" -> "Good/Bad".
    label = re.sub(r"(?<=/)([a-z])", lambda m: m.group(1).upper(), label)
    label = label[:1].upper() + label[1:]
    if adr:
        label = f"ADR-{adr.group(1)} {label}"
    return label


def add_front_matter(text: str, title: str) -> str:
    """Prepend a metadata block. Must be the very first bytes of the file, so
    it goes above the `<!-- hld: ... -->` provenance comment. mkdocs strips it
    as metadata; it never renders."""
    if text.startswith("---\n"):
        # Never silently: a chapter that grows its own front matter would keep
        # the author's title, but a chapter that grows a front-matter-shaped
        # first line would silently fall back to a filename nav label.
        print(
            f"  ! {title}: source already starts with front matter — derived title not applied",
            file=sys.stderr,
        )
        return text  # already has front matter — leave the author's alone
    return f"---\ntitle: {title}\n---\n\n{text}"


def rewrite(text: str, depth: int, authored_sections: tuple[str, ...] = ()) -> str:
    """Rewrite links in one staged file. `depth` = directories below SOURCE."""

    # 1. 00-INDEX.md -> index.md, at any relative depth.
    text = re.sub(r"\]\(((?:\.\./)*)00-INDEX\.md", r"](\1index.md", text)

    # 1b. Drop the GitHub-reading breadcrumb line (transform 6 above). Matched
    #     after the index rewrite so both source spellings are one pattern.
    text = re.sub(r"(?m)^\[← HLD index\]\([^)]*\)\s*\n", "", text)

    # 1c. Sections whose landing chapter is staged as index.md: follow the
    #     rename in links too. No chapter links to one today (they name the
    #     file in inline code, which is left alone), but --strict would fail
    #     the build the day one does, and the fix belongs here.
    for directory in authored_sections:
        text = re.sub(rf"\]\(([^)]*{directory}/)README\.md", r"](\1index.md", text)

    # 2. Links that climb out of docs/design/ -> GitHub.
    #    A link is out-of-tree when it has more `../` than the file has depth.
    def to_github(m: re.Match[str]) -> str:
        ups, rest = m.group(1), m.group(2)
        climbs = ups.count("../")
        if climbs <= depth:
            return m.group(0)  # still inside the wiki; mkdocs resolves it
        # Climbed past docs/design/ — `rest` is relative to docs/.
        if rest.startswith("adr/"):
            # ADRs are staged in (transform 7): point back into the wiki.
            return "](" + "../" * depth + ADR_STAGED_DIR + "/" + rest[len("adr/") :]
        if not rest.startswith(ESCAPING_PREFIXES):
            print(f"  ! unhandled out-of-tree link: {m.group(0)}", file=sys.stderr)
            return m.group(0)
        return f"]({GITHUB_BLOB}/{rest}"

    text = re.sub(r"\]\(((?:\.\./)+)([^)]+)", to_github, text)
    return text


INVARIANT_ITEM = re.compile(r"^(\d+)\.\s+\*\*(.+?):?\*\*\s*(.*)$")


def parse_invariants() -> list[tuple[int, str, str]]:
    """(number, name, statement) for every §18 item, contiguity-checked."""
    text = (SOURCE / "02-constitution.md").read_text(encoding="utf-8")
    section = re.search(r"^## 18\..*?$(.*?)(?=^## |^---$)", text, re.M | re.S)
    if not section:
        raise SystemExit("stage.py: cannot find §18 in 02-constitution.md")
    items: list[tuple[int, str, str]] = []
    for line in section.group(1).splitlines():
        m = INVARIANT_ITEM.match(line)
        if m:
            items.append((int(m.group(1)), m.group(2), m.group(3)))
        elif items and line.strip() and not line.startswith("<!--"):
            n, name, body = items[-1]
            items[-1] = (n, name, f"{body} {line.strip()}")
    numbers = [n for n, _, _ in items]
    if numbers != list(range(1, len(items) + 1)):
        raise SystemExit(f"stage.py: §18 numbering is not contiguous 1..{len(items)}: {numbers}")
    return items


def anchor_invariants(text: str) -> str:
    """Give each §18 list item an id (`inv-01`..`inv-nn`) in the STAGED copy of
    the constitution, so INV-nn citations can deep-link. attr_list syntax on
    the bold name, not raw HTML, so mkdocs' anchor validation sees the ids."""
    section = re.search(r"^## 18\..*?$(.*?)(?=^## |^---$)", text, re.M | re.S)
    if not section:
        return text
    block = section.group(1)
    anchored = re.sub(
        r"^(\d+)\.\s+\*\*(.+?)\*\*",
        lambda m: f"{m.group(1)}. **{m.group(2)}**{{: #inv-{int(m.group(1)):02d} }}",
        block,
        flags=re.M,
    )
    return text.replace(block, anchored, 1)


def adr_pages() -> dict[str, str]:
    """ADR number ("0004") -> staged page filename, from docs/adr/."""
    pages = {}
    for md in ADR_SOURCE.glob("[0-9][0-9][0-9][0-9]-*.md"):
        pages[md.stem[:4]] = md.name
    return pages


# A linkifiable citation: not already inside a link label, not part of a
# longer word. Fences, inline code and HTML comments are handled by the
# segment splitting in linkify().
CITE_ADR = re.compile(r"(?<!\[)\bADR-(\d{4})\b")
CITE_INV = re.compile(r"(?<!\[)\bINV-(\d{1,2})\b")
PROTECTED_SEGMENT = re.compile(r"(`[^`]*`)")
# HTML comments are masked over the WHOLE text before the line loop, because
# they span lines — the provenance headers do not, but `caveman-mode.md`'s
# opening note does, and a per-line match silently linkified inside it.
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
# Both fence spellings. Tracked as a marker (not a boolean) so a `~~~` inside a
# ``` block, or a longer run of the same character, cannot close the wrong fence.
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")


def linkify(text: str, rel: Path, depth: int, max_inv: int, adrs: dict[str, str]) -> str:
    """Turn plain-text INV-nn / ADR-nnnn citations into wiki links
    (transform 8). The repo keeps plain text; only the staged copy links."""
    up = "../" * depth
    self_posix = rel.as_posix()

    def adr_link(m: re.Match[str]) -> str:
        num = m.group(1)
        page = adrs.get(num)
        if page is None or f"{ADR_STAGED_DIR}/{page}" == self_posix:
            return m.group(0)
        return f"[{m.group(0)}]({up}{ADR_STAGED_DIR}/{page})"

    def inv_link(m: re.Match[str]) -> str:
        n = int(m.group(1))
        if not 1 <= n <= max_inv:
            return m.group(0)
        target = "" if self_posix == "02-constitution.md" else f"{up}02-constitution.md"
        return f"[{m.group(0)}]({target}#inv-{n:02d})"

    # Mask HTML comments (possibly multi-line) so nothing inside one is touched.
    comments: list[str] = []

    def _mask(m: re.Match[str]) -> str:
        comments.append(m.group(0))
        return f"\x00COMMENT{len(comments) - 1}\x00"

    text = HTML_COMMENT.sub(_mask, text)

    out_lines = []
    fence: str | None = None  # the marker that opened the current fence
    for line in text.splitlines(keepends=True):
        m = FENCE.match(line)
        if fence is None:
            if m:
                fence = m.group(1)[0]  # ` or ~
                out_lines.append(line)
                continue
        else:
            if m and m.group(1)[0] == fence:
                fence = None
            out_lines.append(line)
            continue
        parts = PROTECTED_SEGMENT.split(line)
        for i in range(0, len(parts), 2):  # even indices are outside inline code
            parts[i] = CITE_ADR.sub(adr_link, parts[i])
            parts[i] = CITE_INV.sub(inv_link, parts[i])
        out_lines.append("".join(parts))

    out = "".join(out_lines)
    for i, original in enumerate(comments):
        out = out.replace(f"\x00COMMENT{i}\x00", original)
    return out


ATX_HEADING = re.compile(r"^(#{1,6})(\s)")


def _outside_fences(text: str) -> Iterator[tuple[str, bool]]:
    """Yield (line, is_code) for every line, tracking both fence spellings."""
    fence: str | None = None
    for line in text.splitlines(keepends=True):
        m = FENCE.match(line)
        if fence is None:
            if m:
                fence = m.group(1)[0]
                yield line, True
                continue
            yield line, False
        else:
            if m and m.group(1)[0] == fence:
                fence = None
            yield line, True


def normalise_heading_levels(text: str) -> str:
    """Shift a chapter whose headings start below H2 up so it carries its own H1.

    The `domains/*.md` chapters open at `### 13.x` — correct in the v4.1
    monolith, where §13 was a third-level section, and wrong once the page has
    its own H1: the theme renders the derived title as H1 and the page then
    jumped straight to H3, a WCAG 1.3.1 heading-order break on all fourteen,
    with the chapter's real title ("13.11 Augustin — Independent Judge") sitting
    redundantly under a synthesised one ("Augustin").

    Shifting to H1 fixes both at once: the chapter's own heading becomes the
    page H1, so the theme stops injecting a duplicate. The nav label still comes
    from the front-matter title, so the sidebar keeps reading "Augustin".

    Chapters that already open at `##` (01-07) are left exactly as they are —
    there the synthesised H1 is a genuinely better page title than "5. Locked
    Naming Constitution", and H1 -> H2 is already contiguous.

    A chapter with SEVERAL headings at its shallowest level shifts to H2, not
    H1, keeping the synthesised title as the one H1 that describes the page.
    `domains/sarpadia.md` is the case: it carries both §13.3 and the §15 data
    model at the same level, and promoting both would give the page two H1s.

    Anchors are unaffected: python-markdown's toc slugify derives an id from
    the heading TEXT and never encodes its level, so every `#...` deep link —
    including inbound external ones that no link checker can see — survives.
    Verified end-to-end by diffing the built heading ids before and after.
    """
    levels = [len(m.group(1)) for line, is_code in _outside_fences(text) if not is_code and (m := ATX_HEADING.match(line))]
    if not levels or min(levels) <= 2:
        return text
    top = min(levels)
    # One top-level heading -> it becomes the page H1 and the theme injects
    # nothing. Several -> land them at H2 under the single synthesised H1.
    shift = top - 1 if levels.count(top) == 1 else top - 2
    out = []
    for line, is_code in _outside_fences(text):
        if not is_code and ATX_HEADING.match(line):
            out.append(line[shift:])  # drop `shift` leading '#' characters
        else:
            out.append(line)
    return "".join(out)


def check_model_matches_domains() -> list[str]:
    """The DSL serves the decided design, never the other way around: its
    container identifiers must be exactly the canonical domain set. Returns a
    list of error strings (empty = consistent)."""
    dsl = SOURCE / "assets" / "model.dsl"
    if not dsl.is_file():
        return [f"model.dsl missing: {dsl}"]
    modelled = set(re.findall(r"^\s*(\w+)\s*=\s*container\s", dsl.read_text(encoding="utf-8"), re.M))
    canonical = {p.stem for p in (SOURCE / "domains").glob("*.md") if p.stem != "README"}
    errors = []
    for name in sorted(canonical - modelled):
        errors.append(f"domain {name} (domains/{name}.md) has no container in model.dsl")
    for name in sorted(modelled - canonical):
        errors.append(f"model.dsl container {name} matches no domains/*.md chapter")
    return errors


def parse_view_descriptions() -> dict[str, str]:
    """View key -> description, from the views block of model.dsl. The DSL is
    the single source for what each diagram claims to show."""
    dsl = SOURCE / "assets" / "model.dsl"
    if not dsl.is_file():
        return {}
    pattern = r'^\s*(?:systemContext|container|component)\s+\w+\s+"(\w+)"\s+"([^"]*)"'
    return dict(re.findall(pattern, dsl.read_text(encoding="utf-8"), re.M))


# --- Diagram theming -------------------------------------------------------
#
# The PlantUML export is light-only: every SVG carries `background:#FFFFFF` on
# its root and paints titles, edges and arrowheads in #444444, so in the slate
# scheme each diagram punched a white slab through an ink-950 page.
#
# The chosen treatment is DELIBERATE, not corrective: assets/simic.css frames
# each diagram as a light plate — its own padded, bordered, rounded surface —
# so in dark mode it reads as a printed figure laid on the page rather than as
# a lighting bug. No colour in the export is altered, which is why this is the
# option that ships: a recoloured variant cannot be signed off without looking
# at it, and no browser was available during this work.
#
# The alternative, if someone can eyeball it: emit a second SVG that is the
# same file plus an injected stylesheet remapping only the page-level colours
# (svg background, #444444 titles/edges/arrowheads, the 15 white cluster and
# card rects — NOT the 2371 white label-text fills, which must stay white), and
# swap the pair on [data-md-color-scheme]. That is the shape the marketing site
# uses for its mermaid diagrams. A blanket CSS filter is NOT the alternative —
# it inverts the teal accents along with the white.
#
# Every (element, property, colour) the export is allowed to emit. Anything
# else means model.dsl grew a style whose legibility on the plate nobody has
# checked, so the build fails here rather than publishing a diagram nobody has
# looked at — the same discipline as check_model_matches_domains().
DIAGRAM_PALETTE = {
    # page-level colours: these are what the light plate exists to sit behind
    ("svg", "background", "#ffffff"),
    ("rect", "fill", "#ffffff"),
    ("rect", "stroke", "#444444"),
    ("text", "fill", "#444444"),
    ("path", "stroke", "#444444"),
    ("polygon", "fill", "#444444"),
    ("polygon", "stroke", "#444444"),
    # element palettes: legible on the plate, deliberately untouched
    ("text", "fill", "#ffffff"),
    ("text", "fill", "#042f2e"),
    ("rect", "fill", "#0d9488"),
    ("rect", "stroke", "#09675f"),
    ("rect", "fill", "#115e59"),
    ("rect", "stroke", "#0b413e"),
    ("rect", "fill", "#99f6e4"),
    ("rect", "stroke", "#6bac9f"),
    ("rect", "fill", "#334155"),
    ("rect", "stroke", "#232d3b"),
    ("rect", "fill", "#64748b"),
    ("rect", "stroke", "#465161"),
    ("ellipse", "fill", "#334155"),
    ("ellipse", "stroke", "#232d3b"),
    # structural non-colours
    ("path", "fill", "none"),
    ("rect", "fill", "none"),
    ("rect", "stroke", "none"),
}

SVG_ELEMENT = re.compile(r"<(\w+)([^>]*)>")
SVG_ATTR_COLOUR = re.compile(r'\b(fill|stroke)="(#[0-9A-Fa-f]{6}|none)"')
SVG_STYLE_COLOUR = re.compile(r"\b(fill|stroke|background)\s*:\s*(#[0-9A-Fa-f]{6}|none)")


def svg_palette(text: str) -> set[tuple[str, str, str]]:
    """Every (element, property, colour) triple used in one SVG."""
    used = set()
    for m in SVG_ELEMENT.finditer(text):
        tag, attrs = m.group(1), m.group(2)
        for prop, value in SVG_ATTR_COLOUR.findall(attrs):
            used.add((tag, prop, value.lower()))
        style = re.search(r'style="([^"]*)"', attrs)
        if style:
            for prop, value in SVG_STYLE_COLOUR.findall(style.group(1)):
                used.add((tag, prop, value.lower()))
    return used


def svg_dimensions(text: str) -> tuple[int, int]:
    """Intrinsic width/height in px, from the root element."""
    root_match = re.search(r"<svg\b[^>]*>", text)
    if root_match is None:
        raise SystemExit("stage.py: diagram SVG has no <svg> root element")
    root = root_match.group(0)
    w = re.search(r'\bwidth="(\d+)px"', root)
    h = re.search(r'\bheight="(\d+)px"', root)
    if not (w and h):
        raise SystemExit("stage.py: diagram SVG root has no pixel width/height")
    return int(w.group(1)), int(h.group(1))


# The width below which a diagram stops shrinking and its frame scrolls
# instead. Material's content column is ~589px; these views are 1305-4774px
# wide, so fitting them to the column put PlantUML's 12px labels at 2-3px.
# Same trade as site/style.css's --dmin, and the same reason: legibility beats
# fitting. Anything wider than this also gets an explicit full-size link,
# because no in-column rendering of a 3792px diagram is genuinely readable.
DIAGRAM_MIN_WIDTH = 1100


def gen_diagrams_page() -> str:
    """Stage the compiled SVGs and build the diagrams page. Hard failure when
    the export has not run: a wiki silently missing its diagrams would look
    valid while being incomplete."""
    svgs = sorted(DIAGRAMS.glob("*.svg")) if DIAGRAMS.is_dir() else []
    if not svgs:
        raise SystemExit(
            f"stage.py: no compiled diagrams in {DIAGRAMS} — run tools/wiki/build.sh, "
            "which exports docs/design/assets/model.dsl before staging"
        )
    dest = STAGED / "assets" / "diagrams"
    dest.mkdir(parents=True, exist_ok=True)
    keyed: dict[str, str] = {}
    legends: dict[str, str] = {}
    sizes: dict[str, tuple[int, int]] = {}
    unmapped: set[tuple[str, str, str]] = set()

    for svg in svgs:
        body = svg.read_text(encoding="utf-8")
        unmapped |= svg_palette(body) - DIAGRAM_PALETTE
        shutil.copy2(svg, dest / svg.name)
        stem = re.sub(r"^structurizr-", "", svg.stem)
        sizes[stem] = svg_dimensions(body)
        if stem.endswith("-key"):
            legends[stem[: -len("-key")]] = svg.name
        else:
            keyed[stem] = svg.name

    if unmapped:
        for tag, prop, value in sorted(unmapped):
            print(f"stage.py: unreviewed diagram colour: <{tag} {prop}={value}>", file=sys.stderr)
        raise SystemExit(
            "stage.py: model.dsl introduced diagram colours nobody has checked against the "
            "light plate — look at them, then add them to DIAGRAM_PALETTE"
        )

    ordered = [k for k in VIEW_ORDER if k in keyed]
    ordered += sorted(k for k in keyed if k not in VIEW_ORDER)

    descriptions = parse_view_descriptions()
    lines = [GENERATED_BANNER.format(source="`docs/design/assets/model.dsl`")]
    lines.append(
        "Compiled from the Structurizr model, itself a transcription of "
        "[Architecture](../04-architecture.md) and the [domain chapters](../domains/README.md). "
        "The build fails if the model's domain set drifts from `domains/*.md`. "
        "The model source is published alongside them as "
        "[`model.dsl`](../assets/model.dsl).\n"
    )
    lines.append(
        "These are large views — several are wider than any text column. Each frame scrolls "
        "rather than shrinking its labels into illegibility, and every diagram links to its "
        "full-size SVG.\n"
    )
    for key in ordered:
        title = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", key)
        # Same closed acronym set as derive_title: "Qa Adjudication" -> "QA Adjudication".
        title = " ".join(w.upper() if w.lower() in {"qa", "hld", "adr"} else w for w in title.split())
        lines.append(f"## {title}\n")
        description = descriptions.get(key, "")
        if description:
            lines.append(f"{description}\n")
        lines.append(diagram_figure(title, keyed[key], sizes[key], description))
        if key in legends:
            # Raw <details> rather than pymdownx's `??? info "Key"`, because the
            # four-space indent that syntax needs makes python-markdown treat the
            # figure as inline content and wrap it in a <p>. Same element and
            # class pymdownx.details would emit, so the theme styles it
            # identically. `markdown` on it too: md_in_html only descends into
            # elements that carry the attribute, so without it the nested
            # figure's markdown would ship as literal text.
            legend = diagram_figure(f"{title} key", legends[key], sizes[f"{key}-key"], f"Legend for {title}.")
            lines.append(f'<details class="info" markdown>\n<summary>Key</summary>\n{legend}</details>\n')
    return "\n".join(lines)


def diagram_figure(title: str, filename: str, size: tuple[int, int], description: str) -> str:
    """One diagram as a framed light plate.

    The image and the full-size link are written as MARKDOWN inside
    `markdown="span"` containers, not as raw `<img>`/`<a>` tags. This is a
    correctness requirement, not a style preference: mkdocs' relative-path
    treeprocessor rewrites asset paths only in markdown-derived elements, and
    python-markdown restores raw HTML blocks *after* that pass — so a raw
    `src="../assets/..."` is emitted verbatim and, under `use_directory_urls`,
    resolves one directory too shallow and 404s. Markdown paths are rewritten
    to the correct depth, and would also be caught by `--strict` if the target
    went missing, which raw HTML never is.

    `markdown="span"` rather than bare `markdown`: block mode wraps the image
    in a `<p>`, and leaves a `markdown`-less `<figcaption>` unprocessed. Span
    mode gives the same markup with correct paths and no wrapper.

    `alt=""` on the image with the accessible name on the frame (role="img" +
    aria-label), so exactly ONE name is exposed — the same split the marketing
    site uses. The name is the view's own description from model.dsl, which is
    a real sentence about what the diagram shows, rather than the view key
    repeated from the heading above it. `tabindex="0"` makes the scrolling
    frame keyboard-operable (WCAG 2.1.1) — without it a keyboard-only reader
    could not pan a 3792px diagram at all.

    `role="img"` on a focusable element is a known tension (`role="group"` is
    the tidier pairing), but this is deliberately the same shape
    `site/architecture.html` uses for its own `.diagram__frame` and
    `.tablewrap`: one convention across both halves of the site beats two
    defensible ones. Verified in-browser: the frame takes focus and ArrowRight
    scrolls it.
    """
    width, height = size
    label = description or title
    dmin = min(width, DIAGRAM_MIN_WIDTH)
    src = f"../assets/diagrams/{filename}"
    attrs = f'{{ .simic-diagram__img width="{width}" height="{height}" style="--dmin: {dmin}px" }}'
    return (
        # `markdown` on the figure so md_in_html descends into it at all; the
        # children carry `markdown="span"` so their contents are parsed inline.
        f'<figure class="simic-diagram" markdown>\n'
        f'<div class="simic-diagram__frame" role="img" tabindex="0" '
        f'aria-label="{escape_attr(label)}" markdown="span">\n'
        f"![]({src}){attrs}\n"
        f"</div>\n"
        f'<figcaption markdown="span">'
        f"[Open {title} full size ({width}&times;{height})]({src})</figcaption>\n"
        f"</figure>\n"
    )


def escape_attr(text: str) -> str:
    return text.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


def gen_invariants_page(items: list[tuple[int, str, str]]) -> str:
    """The 45 blocking invariants, scraped from 02-constitution.md §18 and
    labelled INV-nn to match how the chapters cite them. Each row deep-links
    to the per-item anchor injected by anchor_invariants()."""
    section = "../02-constitution.md#18-safety-correctness-and-constitutional-invariants"
    lines = [GENERATED_BANNER.format(source="`02-constitution.md` §18")]
    lines.append(
        f"All {len(items)} blocking invariants, labelled `INV-nn` as the chapters cite them. "
        f"The authoritative statements live in [the constitution]({section}).\n"
    )
    lines.append("| Invariant | Name | Statement |")
    lines.append("|---|---|---|")
    for n, name, body in items:
        lines.append(f"| [INV-{n:02d}](../02-constitution.md#inv-{n:02d}) | **{name}** | {body} |")
    lines.append("")
    return "\n".join(lines)


def gen_contracts_page() -> str:
    """The §9 contract registry: every contract heading in
    05-leyline-contracts.md, linked to its anchor."""
    text = (SOURCE / "05-leyline-contracts.md").read_text(encoding="utf-8")
    contracts = re.findall(r"^### (9\.\d+) (.+?)\s*$", text, re.M)
    if not contracts:
        raise SystemExit("stage.py: no §9.x contract headings in 05-leyline-contracts.md")
    lines = [GENERATED_BANNER.format(source="`05-leyline-contracts.md` §9")]
    lines.append(
        f"The {len(contracts)} core Leyline contract shapes. Schemas, field tables and "
        "constraints live in the chapter; this page is a linked table of contents.\n"
    )
    lines.append("| § | Contract |")
    lines.append("|---|---|")
    for num, heading in contracts:
        anchor = slugify(f"{num} {heading}")
        lines.append(f"| {num} | [{heading}](../05-leyline-contracts.md#{anchor}) |")
    lines.append("")
    return "\n".join(lines)


def parse_domain_roster() -> list[tuple[int, str, str, str, str]]:
    """(n, "13.n", Name, Epithet, stem) per domain chapter, in §13.x order.

    §13.x order is the canonical sentence's order — infrastructure first, then
    agents — so it drives both the roster page and the sidebar (hooks.py).
    """
    rows = []
    for md in (SOURCE / "domains").glob("*.md"):
        if md.stem == "README":
            continue
        m = re.search(r"^### (13\.(\d+)) (.+?) — (.+?)\s*$", md.read_text(encoding="utf-8"), re.M)
        if not m:
            raise SystemExit(f"stage.py: no '### 13.x Name — Epithet' heading in domains/{md.name}")
        rows.append((int(m.group(2)), m.group(1), m.group(3), m.group(4), md.stem))
    return sorted(rows)


def gen_domains_page() -> str:
    """The fourteen-domain roster, scraped from each domain chapter's
    `### 13.x Name — Epithet` heading."""
    rows = parse_domain_roster()
    lines = [GENERATED_BANNER.format(source="the `domains/` chapter headings")]
    lines.append(
        "The fourteen domains in specification order — infrastructure "
        "(prepositions) first, then agents (verbs), per the "
        "[naming constitution](../02-constitution.md).\n"
    )
    lines.append("| § | Domain | Mandate |")
    lines.append("|---|---|---|")
    for _, num, name, epithet, stem in sorted(rows):
        lines.append(f"| {num} | [{name}](../domains/{stem}.md) | {epithet} |")
    lines.append("")
    return "\n".join(lines)


# Sections staged in rather than named by the index's chapter map, and where
# they belong relative to the sections the map DOES name. `decisions/` sorts
# with the substantive chapters because ADRs are Tier 1 authority that amends
# them (ADR-0001); `reference/` sorts last because it is generated lookup
# material — the back of the book.
SECTION_INSERTS = {"decisions/": "appendices/"}  # section -> insert before this one
SECTION_TAIL = ["reference/"]


# Which sections get which kind of landing page is DERIVED from the staged
# tree, not listed here: a section directory with an authored README.md has its
# README staged as index.md, and one without gets a generated contents page.
# A hardcoded list would mean a new section directory in docs/design/ silently
# 404s at /design/<new>/ with navigation.indexes linking its header nowhere —
# the m9 defect, reintroduced with no build failure to catch it.
def classify_sections() -> tuple[list[str], list[str]]:
    """(authored, generated) section directories, from the staged tree."""
    authored: list[str] = []
    generated: list[str] = []
    for directory in sorted(p for p in STAGED.iterdir() if p.is_dir()):
        if directory.name == "assets" or not any(directory.glob("*.md")):
            continue
        (authored if (directory / "README.md").is_file() else generated).append(directory.name)
    return authored, generated


CHAPTER_MAP_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|")


def parse_chapter_map() -> list[str]:
    """The staged paths named by 00-INDEX.md's chapter-map table, in order.

    This is what makes the nav order a projection rather than a second, hand-
    maintained copy: the index already states the reading order in prose, and
    the sidebar now follows it instead of the filesystem's alphabet.
    """
    text = (SOURCE / "00-INDEX.md").read_text(encoding="utf-8")
    paths = []
    for line in text.splitlines():
        m = CHAPTER_MAP_ROW.match(line)
        if not m:
            continue
        path = m.group(1)
        if "<" in path or path == "TEMPLATE-lld.md":
            continue  # a placeholder row, or scaffolding stage.py drops
        paths.append(path)
    if not paths:
        raise SystemExit("stage.py: no chapter-map rows found in 00-INDEX.md")
    return paths


def build_nav_order(domain_order: list[str], authored_sections: list[str]) -> dict[str, list[str]]:
    """A flat, canonical ordering of every nav entry, for hooks.py's on_nav.

    Anything the canon does not mention is simply absent from this list and
    falls back to filename order within its own level — so adding a chapter to
    `docs/design/` still needs no config change.
    """
    # The chapter map names `domains/README.md`; staging renames it to
    # index.md, so follow that here or the landing page sorts as unknown.
    mapped = [re.sub(r"/README\.md$", "/index.md", p) if p.split("/")[0] in authored_sections else p for p in parse_chapter_map()]
    order: list[str] = ["index.md"]
    sections: list[str] = []
    per_section: dict[str, list[str]] = {}

    for path in mapped:
        if path.endswith("/"):
            if path not in sections:
                sections.append(path)
            continue
        directory = path.split("/")[0] + "/" if "/" in path else ""
        if not directory:
            order.append(path)
            continue
        if directory not in sections:
            sections.append(directory)
        per_section.setdefault(directory, []).append(path)

    for section, before in SECTION_INSERTS.items():
        sections.insert(sections.index(before) if before in sections else len(sections), section)
    sections += [s for s in SECTION_TAIL if s not in sections]

    for section in sections:
        order.append(section)
        directory = section.rstrip("/")
        # The section's own landing page first, then the canon's order, then
        # the §13.x roster for domains/, then whatever is left by filename.
        listed = per_section.get(section, [])
        staged = sorted(p.relative_to(STAGED).as_posix() for p in (STAGED / directory).glob("*.md"))
        landing = [p for p in staged if p.endswith(("/index.md", "/README.md"))]
        canon = [p for p in listed if p not in landing]
        if directory == "domains":
            canon += [f"domains/{stem}.md" for stem in domain_order]
        rest = [p for p in staged if p not in landing and p not in canon]
        for path in landing + canon + rest:
            if path not in order:
                order.append(path)

    return {"order": order, "sections": sections}


def gen_section_index(directory: str, mapped: list[str]) -> str:
    """A generated landing page for a section with no authored README.

    Without one, `/design/appendices/` and friends 404 — and with
    `navigation.indexes` the section header has nothing to link to. Purely a
    linked table of contents scraped from the staged files: no prose is
    invented here, because inventing prose is authoring and this is a
    projection.

    Ordered by the index's chapter map, the same source the sidebar uses. A
    generated contents list that disagreed with the nav beside it would be
    exactly the defect this whole pass is fixing — one page's order
    contradicting another's, a click apart.
    """
    listed = [p.split("/", 1)[1] for p in mapped if p.startswith(f"{directory}/")]
    present = {p.name for p in (STAGED / directory).glob("*.md") if p.name not in ("index.md", "README.md")}
    ordered = [n for n in listed if n in present] + sorted(present - set(listed))
    lines = [GENERATED_BANNER.format(source=f"the `{directory}/` chapter files")]
    lines.append(f"The chapters in `{directory}/`.\n")
    for name in ordered:
        lines.append(f"- [{derive_title(Path(directory) / name)}]({name})")
    lines.append("")
    return "\n".join(lines)


def generate_reference(invariants: list[tuple[int, str, str]]) -> None:
    """Write the generated reference/ section into the staged tree."""
    errors = check_model_matches_domains()
    if errors:
        for e in errors:
            print(f"stage.py: model drift: {e}", file=sys.stderr)
        raise SystemExit("stage.py: model.dsl no longer matches the canonical domain set")
    ref = STAGED / "reference"
    ref.mkdir()
    for name, body in (
        ("diagrams.md", gen_diagrams_page()),
        ("invariants.md", gen_invariants_page(invariants)),
        ("contracts.md", gen_contracts_page()),
        ("domains.md", gen_domains_page()),
    ):
        (ref / name).write_text(body, encoding="utf-8")
        GENERATED_PAGES.append(f"reference/{name}")


def main() -> int:
    if not SOURCE.is_dir():
        print(f"stage.py: no such directory: {SOURCE}", file=sys.stderr)
        return 1

    if STAGED.exists():
        shutil.rmtree(STAGED)
    shutil.copytree(SOURCE, STAGED)

    index = STAGED / "00-INDEX.md"
    if index.exists():
        index.rename(STAGED / "index.md")
    else:
        print("stage.py: 00-INDEX.md missing — /design/ will have no landing page", file=sys.stderr)
        return 1

    # Transform 5: authoring scaffolding is not a chapter.
    template = STAGED / "TEMPLATE-lld.md"
    if template.exists():
        template.unlink()

    # Transform 7: stage the Tier 1 ADRs in as decisions/ (ADR-0007). They
    # remain canonical at docs/adr/; the template is authoring scaffolding.
    if not ADR_SOURCE.is_dir():
        print(f"stage.py: no such directory: {ADR_SOURCE}", file=sys.stderr)
        return 1
    shutil.copytree(ADR_SOURCE, STAGED / ADR_STAGED_DIR)
    (STAGED / ADR_STAGED_DIR / "TEMPLATE.md").unlink(missing_ok=True)

    invariants = parse_invariants()
    adrs = adr_pages()

    # Generated registry + diagram pages. Written before the transform loop so
    # they get the same mechanical titles and link handling as the chapters.
    generate_reference(invariants)

    # Every section gets a landing page, or `/design/<section>/` 404s and
    # navigation.indexes leaves the section header linking nowhere. Which kind
    # each section gets is derived from the staged tree, so a NEW section
    # directory is handled without touching this file.
    authored_sections, generated_sections = classify_sections()

    # An authored landing chapter is staged as an explicit index.md. mkdocs
    # already treats README.md as a section index, so no published URL moves
    # (`/design/domains/` either way) — this just stops the tree depending on
    # that convenience and makes every section uniform. hooks.py maps the edit
    # link back to the real README, using the list exported below.
    for directory in authored_sections:
        (STAGED / directory / "README.md").rename(STAGED / directory / "index.md")

    chapter_map = parse_chapter_map()
    for directory in generated_sections:
        (STAGED / directory / "index.md").write_text(gen_section_index(directory, chapter_map), encoding="utf-8")
        GENERATED_PAGES.append(f"{directory}/index.md")

    # Build metadata for hooks.py — the canonical nav order, the generated
    # pages, and the sections whose index came from a README. hooks.py needs
    # that last set to point the edit pencil back at the README; deriving it
    # here and exporting it means the two files cannot disagree, where a
    # hand-mirrored copy in hooks.py would silently resurrect the C1 defect
    # (pencil -> a path that does not exist -> GitHub's new-file editor) the
    # day someone adds an ops/README.md. Written into build/ rather than the
    # staged tree: it is metadata, not a page.
    metadata = build_nav_order([r[4] for r in parse_domain_roster()], authored_sections)
    metadata["generated"] = sorted(GENERATED_PAGES)
    metadata["authored_sections"] = authored_sections
    NAV_ORDER.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    count = 0
    for md in sorted(STAGED.rglob("*.md")):
        rel = md.relative_to(STAGED)
        depth = len(rel.parts) - 1
        original = md.read_text(encoding="utf-8")
        updated = rewrite(original, depth, tuple(authored_sections))
        # Transform 8: invariant anchors on the staged constitution, then
        # citation linkification everywhere (both presentation-only).
        if rel.as_posix() == "02-constitution.md":
            updated = anchor_invariants(updated)
        updated = linkify(updated, rel, depth, len(invariants), adrs)
        # Heading hierarchy: the theme renders an H1 from the derived title, so
        # a chapter that opens at `###` produced an H1 -> H3 skip on the page.
        updated = normalise_heading_levels(updated)
        # Chapters get a derived title. Applied broadly rather than only to the
        # H1-less ones: mkdocs does not reliably pick up an H1 that sits below
        # the provenance comment and the breadcrumb line, and the chapters that
        # do have one produce worse nav labels from it anyway ("LLD — ()", once
        # the angle-bracket placeholders in TEMPLATE-lld.md parse as tags). The
        # H1 still renders in the body; only the nav/tab label comes from here.
        #
        # The landing page is the exception: "# Simic HLD — Index" is a proper
        # document title and beats anything derivable from the filename.
        if rel.as_posix() != "index.md":
            updated = add_front_matter(updated, derive_title(rel))
        if updated != original:
            md.write_text(updated, encoding="utf-8")
            count += 1

    if ASSETS.is_dir():
        shutil.copytree(ASSETS, STAGED / "assets", dirs_exist_ok=True)

    # The logo/favicon comes from the marketing site so there is exactly one
    # mark in the repo. Fail loudly rather than shipping a wiki with a broken
    # logo if the site half ever moves it.
    if not BRAND_MARK.is_file():
        print(f"stage.py: brand mark missing: {BRAND_MARK}", file=sys.stderr)
        return 1
    shutil.copy2(BRAND_MARK, STAGED / "assets" / "mark.svg")

    total = sum(1 for _ in STAGED.rglob("*.md"))
    print(f"staged {total} chapters into {STAGED.relative_to(REPO)} ({count} with rewritten links)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
