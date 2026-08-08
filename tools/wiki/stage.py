#!/usr/bin/env python3
"""Stage docs/design/ into a build directory mkdocs can consume.

The design chapters are the canonical authority and are NEVER edited to suit
the wiki. Anything the renderer needs is done here, on a throwaway copy, so
`docs/design/` stays exactly as its owner wrote it and the wiki stays a pure
projection of it: edit the chapter, re-render, the wiki follows.

Three transforms, each with a reason:

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

4.  Support assets (MathJax config, extra CSS) copied in.
    mkdocs resolves `extra_javascript`/`extra_css` relative to `docs_dir`, so
    they have to live inside the staged tree.

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
    citations link to the staged pages. Code fences, inline code, HTML
    comments and self-references are left alone.

Everything else — the `<!-- hld: ... -->` provenance comments, `\\(...\\)` and
`$$...$$` math, the mermaid fence in 04-architecture.md — is left untouched
and handled by mkdocs config.

Beyond the transforms, staging GENERATES a `reference/` section: registry
pages scraped from the canonical chapters (invariants from 02-constitution.md
§18, contracts from 05-leyline-contracts.md §9, the domain roster from
domains/*.md) plus a diagrams page for the SVGs compiled from
docs/design/assets/model.dsl by build.sh. Generated pages exist only in the
staged tree — never in docs/design/ — so they cannot drift: re-render and
they follow the chapters. The same step enforces the model's subordination
to the canon: if model.dsl's container set stops matching domains/*.md, the
build fails here rather than publishing a diagram that contradicts the text.
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
SOURCE = REPO / "docs" / "design"
STAGED = HERE / "build" / "src"
ASSETS = HERE / "assets"

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
    words = [w for w in re.split(r"[-_]", stem) if w]
    # Acronyms the project uses as words; without this "TEMPLATE-lld" reads
    # "Template lld". Mechanical and closed — not a per-file title map.
    acronyms = {"lld", "hld", "qa", "adr", "mvs", "api", "rl"}
    words = [w.upper() if w.lower() in acronyms else w for w in words]
    label = " ".join(words)
    label = label[:1].upper() + label[1:]
    if adr:
        label = f"ADR-{adr.group(1)} {label}"
    return label


def add_front_matter(text: str, title: str) -> str:
    """Prepend a metadata block. Must be the very first bytes of the file, so
    it goes above the `<!-- hld: ... -->` provenance comment. mkdocs strips it
    as metadata; it never renders."""
    if text.startswith("---\n"):
        return text  # already has front matter — leave the author's alone
    return f"---\ntitle: {title}\n---\n\n{text}"


def rewrite(text: str, depth: int) -> str:
    """Rewrite links in one staged file. `depth` = directories below SOURCE."""

    # 1. 00-INDEX.md -> index.md, at any relative depth.
    text = re.sub(r"\]\(((?:\.\./)*)00-INDEX\.md", r"](\1index.md", text)

    # 1b. Drop the GitHub-reading breadcrumb line (transform 6 above). Matched
    #     after the index rewrite so both source spellings are one pattern.
    text = re.sub(r"(?m)^\[← HLD index\]\([^)]*\)\s*\n", "", text)

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
PROTECTED_SEGMENT = re.compile(r"(<!--.*?-->|`[^`]*`)")


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

    out_lines = []
    in_fence = False
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        if in_fence or line.lstrip().startswith("```"):
            out_lines.append(line)
            continue
        parts = PROTECTED_SEGMENT.split(line)
        for i in range(0, len(parts), 2):  # even indices are outside comments/code
            parts[i] = CITE_ADR.sub(adr_link, parts[i])
            parts[i] = CITE_INV.sub(inv_link, parts[i])
        out_lines.append("".join(parts))
    return "".join(out_lines)


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
    for svg in svgs:
        shutil.copy2(svg, dest / svg.name)
        stem = re.sub(r"^structurizr-", "", svg.stem)
        if stem.endswith("-key"):
            legends[stem[: -len("-key")]] = svg.name
        else:
            keyed[stem] = svg.name
    ordered = [k for k in VIEW_ORDER if k in keyed]
    ordered += sorted(k for k in keyed if k not in VIEW_ORDER)

    descriptions = parse_view_descriptions()
    lines = [GENERATED_BANNER.format(source="`docs/design/assets/model.dsl`")]
    lines.append(
        "Compiled from the Structurizr model, itself a transcription of "
        "[Architecture](../04-architecture.md) and the [domain chapters](../domains/README.md). "
        "The build fails if the model's domain set drifts from `domains/*.md`.\n"
    )
    for key in ordered:
        title = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", key)
        # Same closed acronym set as derive_title: "Qa Adjudication" -> "QA Adjudication".
        title = " ".join(w.upper() if w.lower() in {"qa", "hld", "adr"} else w for w in title.split())
        lines.append(f"## {title}\n")
        if key in descriptions:
            lines.append(f"{descriptions[key]}\n")
        lines.append(f"![{title}](../assets/diagrams/{keyed[key]})\n")
        if key in legends:
            lines.append('??? info "Key"\n')
            lines.append(f"    ![{title} key](../assets/diagrams/{legends[key]})\n")
    return "\n".join(lines)


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


def gen_domains_page() -> str:
    """The fourteen-domain roster, scraped from each domain chapter's
    `### 13.x Name — Epithet` heading."""
    rows = []
    for md in (SOURCE / "domains").glob("*.md"):
        if md.stem == "README":
            continue
        m = re.search(r"^### (13\.(\d+)) (.+?) — (.+?)\s*$", md.read_text(encoding="utf-8"), re.M)
        if not m:
            raise SystemExit(f"stage.py: no '### 13.x Name — Epithet' heading in domains/{md.name}")
        rows.append((int(m.group(2)), m.group(1), m.group(3), m.group(4), md.stem))
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


def generate_reference(invariants: list[tuple[int, str, str]]) -> None:
    """Write the generated reference/ section into the staged tree."""
    errors = check_model_matches_domains()
    if errors:
        for e in errors:
            print(f"stage.py: model drift: {e}", file=sys.stderr)
        raise SystemExit("stage.py: model.dsl no longer matches the canonical domain set")
    ref = STAGED / "reference"
    ref.mkdir()
    (ref / "diagrams.md").write_text(gen_diagrams_page(), encoding="utf-8")
    (ref / "invariants.md").write_text(gen_invariants_page(invariants), encoding="utf-8")
    (ref / "contracts.md").write_text(gen_contracts_page(), encoding="utf-8")
    (ref / "domains.md").write_text(gen_domains_page(), encoding="utf-8")


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

    count = 0
    for md in sorted(STAGED.rglob("*.md")):
        rel = md.relative_to(STAGED)
        depth = len(rel.parts) - 1
        original = md.read_text(encoding="utf-8")
        updated = rewrite(original, depth)
        # Transform 8: invariant anchors on the staged constitution, then
        # citation linkification everywhere (both presentation-only).
        if rel.as_posix() == "02-constitution.md":
            updated = anchor_invariants(updated)
        updated = linkify(updated, rel, depth, len(invariants), adrs)
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

    total = sum(1 for _ in STAGED.rglob("*.md"))
    print(f"staged {total} chapters into {STAGED.relative_to(REPO)} ({count} with rewritten links)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
