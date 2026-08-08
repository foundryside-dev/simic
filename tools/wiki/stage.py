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

2.  Links that escape `docs/design/` -> absolute GitHub URLs.
    Two chapters cite `../adr/...` and `../concept/archive/...`, which are real
    files in the repo but outside the wiki's document root. Left alone they are
    broken links; rewritten they resolve to the same content on GitHub.

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

Everything else — the `<!-- hld: ... -->` provenance comments, `\\(...\\)` and
`$$...$$` math, the mermaid fence in 04-architecture.md — is left untouched
and handled by mkdocs config.
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
ESCAPING_PREFIXES = ("adr/", "concept/", "product/")


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
    stem = re.sub(r"^\d+[-_]", "", stem)
    words = [w for w in re.split(r"[-_]", stem) if w]
    # Acronyms the project uses as words; without this "TEMPLATE-lld" reads
    # "Template lld". Mechanical and closed — not a per-file title map.
    acronyms = {"lld", "hld", "qa", "adr", "mvs", "api", "rl"}
    words = [w.upper() if w.lower() in acronyms else w for w in words]
    label = " ".join(words)
    return label[:1].upper() + label[1:]


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
        if not rest.startswith(ESCAPING_PREFIXES):
            print(f"  ! unhandled out-of-tree link: {m.group(0)}", file=sys.stderr)
            return m.group(0)
        return f"]({GITHUB_BLOB}/{rest}"

    text = re.sub(r"\]\(((?:\.\./)+)([^)]+)", to_github, text)
    return text


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

    count = 0
    for md in sorted(STAGED.rglob("*.md")):
        rel = md.relative_to(STAGED)
        depth = len(rel.parts) - 1
        original = md.read_text(encoding="utf-8")
        updated = rewrite(original, depth)
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
