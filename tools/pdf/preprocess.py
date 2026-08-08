#!/usr/bin/env python3
"""Assemble docs/design chapters into one markdown body for the HLD PDF.

The design chapters are the single source of truth and are never modified. This
script reads them, applies print-oriented transforms, and writes a single
concatenated markdown file that pandoc turns into Typst.

Transforms, and why each one exists:

  nav links      Every chapter opens with `[← HLD index](../00-INDEX.md)`. That
                 is site navigation; in a consolidated PDF it is noise and the
                 target is not in the document. Dropped.

  html comments  `<!-- hld: ... -->` markers carry decomposition provenance
                 ("source: v4.1 monolith lines 3094-3142 - amended by
                 ADR-0004"). With --provenance they are rendered as a small
                 grey note under the section heading; otherwise dropped.

  document h1    01-claim.md opens with the document title as an h1, followed by
                 a block of `**Key:** value` front-matter lines. Both are cover
                 page material, so both are dropped. Only a *leading* h1 is
                 dropped, and the front-matter strip is armed only between that
                 dropped h1 and the next heading — so it cannot fire in a chapter
                 that has no title h1, and cannot eat body prose that happens to
                 begin with bold text.

  hrules         Standalone `---` separators; Typst's section styling provides
                 the visual break instead. Dropped.

  md cross-links Relative `.md` links cannot resolve in a PDF. Reduced to their
                 link text, which in this corpus already reads correctly
                 ("ADR-0001", "`05-leyline-contracts.md`"). Absolute http(s)
                 links are left intact and stay clickable.

  invariants     The 45-item ordered list under the §18 heading is wrapped in a
                 `::: {#simic-invariants}` div. Pandoc emits that identifier as a
                 Typst `<simic-invariants>` label, which template.typ targets to
                 number the items INV-01..INV-45 instead of 1..45, matching how
                 they are cited everywhere else. The name is prefixed because
                 `invariants` is already pandoc's auto-generated anchor for the
                 "Invariants" heading in all fourteen domain chapters.

  mermaid        Resolved against pre-rendered assets from the shared diagram
                 tooling when available, else rendered locally with mmdc, else
                 left as a monospace block, and placed on its own landscape page.
                 See resolve_mermaid().

Heading levels are deliberately left untouched. The chapters carry the v4.1
monolith's own numbering in their heading text (`## 18.`, `### 13.11`), and
their heading depths already agree with that numbering: assembling them in
concordance order yields one coherent hierarchy with no renumbering needed.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

# --- Patterns -------------------------------------------------------------

# `[← HLD index](00-INDEX.md)` / `(../00-INDEX.md)` on a line of its own.
RE_NAV_LINE = re.compile(r"^\s*\[\s*←[^\]]*\]\([^)]*00-INDEX\.md\)\s*$")

RE_HTML_COMMENT = re.compile(r"<!--(.*?)-->", re.DOTALL)

# `<!-- hld: source: v4.1 monolith lines 3094-3142 - amended by ADR-0004 -->`
RE_PROVENANCE = re.compile(r"^\s*hld:\s*(?P<text>.+?)\s*$", re.DOTALL)

# Front-matter key lines in 01-claim.md: `**Architecture version:** 4.1`
RE_FRONTMATTER_KEY = re.compile(r"^\*\*[A-Z][^*]{0,40}:\*\*\s")

RE_HRULE = re.compile(r"^-{3,}\s*$")

RE_ATX_HEADING = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<text>.*?)\s*#*\s*$")

# Markdown inline link whose target is a relative .md path (optionally #anchor).
RE_MD_LINK = re.compile(r"\[(?P<text>[^\]]*)\]\((?!https?:)(?P<href>[^)]*?\.md(?:#[^)]*)?)\)")

RE_FENCE = re.compile(r"^(?P<indent>\s*)(?P<ticks>`{3,}|~{3,})\s*(?P<info>.*?)\s*$")

# The §18 heading that introduces the 45 constitutional invariants.
RE_INVARIANTS_HEADING = re.compile(r"^#{2,4}\s+18\.\s", re.IGNORECASE)

RE_ORDERED_ITEM = re.compile(r"^\s*\d+\.\s")


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


# --- Mermaid --------------------------------------------------------------


def resolve_mermaid(
    source: str,
    index: int,
    diagram_dir: Path | None,
    cache_dir: Path,
    typst_root: Path,
    render: bool,
    diagram_map: dict[str, str],
) -> list[str]:
    """Turn one mermaid block into markdown lines.

    Resolution order, most-preferred first:

      1. A pre-rendered asset in --diagram-dir (the print-palette output of the
         shared tools/diagrams tooling). This is the intended steady state:
         diagrams rendered once, with the project's print theme, by the tooling
         that owns them.
      2. A local mmdc render into this pipeline's build cache. A fallback so the
         PDF is buildable before the shared tooling's pdf target lands.
      3. The mermaid source as a monospace block. Always correct, never pretty.

    Format preference is SVG *if it is clean*, then PDF, then PNG.

    The qualifier is the whole story. Mermaid puts node labels inside SVG
    `<foreignObject>` elements by default, and Typst does not render those
    (typst/typst#1421) — such an SVG comes out as correctly positioned, entirely
    EMPTY boxes, silently. Setting `htmlLabels: false` only under `flowchart`
    recovers edge labels but leaves node labels in foreignObjects; setting it at
    the CONFIG TOP LEVEL eliminates them completely, and the resulting SVG renders
    perfectly in Typst as full vector. tools/diagrams/theme-site-*.json already
    does this, and its output was verified against Typst directly.

    So an SVG is checked before it is trusted: clean SVG wins on quality, an SVG
    carrying foreignObjects is REFUSED in favour of a raster sibling (with a loud
    warning) rather than silently producing a diagram of empty boxes. A local mmdc
    render has no such config and so goes to PNG at scale 3.

    This pipeline never writes into the shared diagram directory; it only reads.
    """
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:12]
    alt = f"Architecture diagram {index + 1}"

    # (1) Pre-rendered asset from the shared diagram tooling.
    if diagram_dir is not None and diagram_dir.is_dir():
        for stem in _candidate_stems(digest, index, diagram_map):
            for ext in (".svg", ".pdf", ".png"):
                candidate = diagram_dir / f"{stem}{ext}"
                if not candidate.is_file():
                    continue
                if ext == ".svg" and "foreignObject" in candidate.read_text(encoding="utf-8", errors="ignore"):
                    # Refuse, do not merely warn: using it would yield empty boxes.
                    log(
                        f"  [warn] {candidate.name} contains <foreignObject>; Typst renders "
                        "no labels from it. Skipping. Re-render with htmlLabels:false at the "
                        "config top level, or supply a PNG."
                    )
                    continue
                log(f"  [diagram] {candidate.name} (pre-rendered)")
                staged = _stage_asset(candidate, cache_dir, typst_root)
                return _diagram_page(_typst_path(staged, typst_root), alt)

    # (2) Local mmdc render into our own cache.
    if render and shutil.which("mmdc"):
        cache_dir.mkdir(parents=True, exist_ok=True)
        png = cache_dir / f"{digest}.png"
        if not png.is_file():
            mmd = cache_dir / f"{digest}.mmd"
            mmd.write_text(source, encoding="utf-8")
            puppeteer = cache_dir / "puppeteer.json"
            puppeteer.write_text('{ "args": ["--no-sandbox"] }\n', encoding="utf-8")
            result = subprocess.run(
                [
                    "mmdc",
                    "-i",
                    str(mmd),
                    "-o",
                    str(png),
                    "-b",
                    "white",
                    "-t",
                    "neutral",
                    "-s",
                    "3",  # 3x supersample: keeps text crisp at print DPI
                    "--quiet",
                    "-p",
                    str(puppeteer),
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0 or not png.is_file():
                log(f"  [warn] mmdc failed for diagram {index}; falling back to source block")
                log(f"         {result.stderr.strip()[:300]}")
                return _mermaid_as_text(source)
        log(f"  [diagram] {png.name} (local mmdc render, PNG @3x)")
        return _diagram_page(_typst_path(png, typst_root), alt)

    # (3) Honest fallback.
    if render:
        log(f"  [diagram] mmdc unavailable; diagram {index} kept as source block")
    return _mermaid_as_text(source)


def _candidate_stems(digest: str, index: int, diagram_map: dict[str, str]) -> list[str]:
    """Filename stems to look for in the pre-rendered diagram directory, in order.

    The shared diagram tooling names its sources semantically (`core-loop`,
    `observation-loop`, `assurance-loop`) rather than by content hash, and those
    sources are hand-authored decompositions — they are not byte-identical to the
    mermaid block embedded in a chapter, so neither a content hash nor a positional
    index will ever match them by luck.

    `diagrams.map` closes that gap explicitly: it maps a chapter block's content
    digest to the stem of the pre-rendered asset that supersedes it. Asserting that
    a hand-authored diagram is equivalent to a chapter's block is an editorial
    judgement, so it is recorded in a reviewable file rather than guessed here.
    """
    stems = []
    if digest in diagram_map:
        stems.append(diagram_map[digest])
    stems += [digest, f"diagram-{index}", f"diagram-{index + 1}"]
    return stems


def read_diagram_map(path: Path) -> dict[str, str]:
    """Parse `diagrams.map`: `<content-digest> <asset-stem>` per line, # comments."""
    mapping: dict[str, str] = {}
    if not path.is_file():
        return mapping
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 2:
            log(f"  [warn] {path.name}:{lineno}: expected '<digest> <stem>', ignoring")
            continue
        mapping[parts[0]] = parts[1]
    if mapping:
        log(f"  [diagram] {len(mapping)} mapping(s) from {path.name}")
    return mapping


def _mermaid_as_text(source: str) -> list[str]:
    return ["```text", *source.splitlines(), "```", ""]


def _diagram_page(rel_path: str, alt: str) -> list[str]:
    """Emit raw Typst placing the diagram on its own landscape page.

    A markdown image would be laid out at the 15.5cm text measure, where a large
    flowchart's labels come out around 4pt. `diagram-page` in template.typ gives
    it a flipped page instead. Emitted as a raw Typst block because pandoc has no
    markdown syntax for "put this on a landscape page".
    """
    escaped = rel_path.replace("\\", "/").replace('"', '\\"')
    return [
        "```{=typst}",
        f'#diagram-page("{escaped}", caption: [{_typst_escape(alt)}], alt: "{_typst_escape_str(alt)}")',
        "```",
        "",
    ]


def _typst_escape_str(text: str) -> str:
    """Escape for a Typst double-quoted string literal."""
    return text.replace("\\", "\\\\").replace('"', '\\"')


def _stage_asset(source: Path, cache_dir: Path, typst_root: Path) -> Path:
    """Copy a pre-rendered asset into the build cache if it lives outside the root.

    Typst refuses to read any path above its `--root`, so a diagram directory
    pointed somewhere else — which `SIMIC_DIAGRAM_DIR` explicitly allows — cannot
    be referenced in place. Staging a copy inside the build tree makes the
    override work from any location and keeps the generated Typst self-contained.

    Assets already under the root are used where they are, not copied.
    """
    try:
        source.resolve().relative_to(typst_root.resolve())
        return source
    except ValueError:
        cache_dir.mkdir(parents=True, exist_ok=True)
        staged = cache_dir / source.name
        shutil.copyfile(source, staged)
        log(f"  [diagram] staged {source.name} into the build cache (outside typst root)")
        return staged


def _typst_path(target: Path, typst_root: Path) -> str:
    """Root-absolute Typst path for an asset, e.g. `/tools/pdf/build/x.png`.

    Deliberately not relative. Typst resolves a relative path in `image()`
    against the file that *contains the call*, and the call lives in
    template.typ, not in the generated body — so a path relative to the body
    silently resolves one directory too high. A leading-slash path is resolved
    against `typst compile --root` and is correct from any calling file.
    """
    try:
        return "/" + target.resolve().relative_to(typst_root.resolve()).as_posix()
    except ValueError as exc:  # pragma: no cover — _stage_asset should prevent this
        raise SystemExit(
            f"error: diagram asset {target} lies outside the typst root {typst_root}, "
            "so Typst cannot read it. --cache-dir must be inside the typst root "
            "(build.sh always puts it there); pre-rendered assets from elsewhere are "
            "staged into it automatically."
        ) from exc


# --- Per-chapter transform ------------------------------------------------


def transform_chapter(
    path: Path,
    text: str,
    *,
    provenance: bool,
    diagram_dir: Path | None,
    cache_dir: Path,
    typst_root: Path,
    render_mermaid: bool,
    diagram_map: dict[str, str],
    counters: dict[str, int],
) -> list[str]:
    lines = text.splitlines()
    out: list[str] = []

    # Both strippers below are scoped as tightly as possible, because a stripper
    # that stays armed deletes content silently — there is nothing left in the
    # output to detect it by.
    #
    # `seen_heading` tracks ANY heading, at any level. It must not be keyed on a
    # level-2 heading: the fourteen domains/*.md chapters have none at all, they
    # open at `### 13.n`, so a level-2 key would leave the strippers armed for the
    # whole of every domain chapter.
    seen_heading = False

    # True only between a dropped leading title h1 and the next heading — i.e.
    # exactly the `**Key:** value` block in 01-claim.md. A chapter with no leading
    # h1 (every other chapter) can never enter this state, so the front-matter
    # pattern cannot fire on body prose that happens to start with bold text.
    in_front_matter = False
    pending_provenance: list[str] = []
    in_fence = False
    fence_ticks = ""
    in_invariants = False
    invariants_pending = False  # §18 heading seen, waiting for the list to start

    i = 0
    while i < len(lines):
        line = lines[i]

        # --- fenced blocks: pass through verbatim, except mermaid ---
        fence = RE_FENCE.match(line)
        if not in_fence and fence and fence.group("ticks"):
            info = fence.group("info").strip().lower()
            if info == "mermaid":
                # Collect the block body.
                closing = fence.group("ticks")
                body: list[str] = []
                i += 1
                while i < len(lines):
                    close = RE_FENCE.match(lines[i])
                    if close and close.group("ticks").startswith(closing[0] * 3) and not close.group("info"):
                        break
                    body.append(lines[i])
                    i += 1
                i += 1  # consume closing fence
                idx = counters["mermaid"]
                counters["mermaid"] += 1
                out.extend(
                    resolve_mermaid(
                        "\n".join(body),
                        idx,
                        diagram_dir,
                        cache_dir,
                        typst_root,
                        render_mermaid,
                        diagram_map,
                    )
                )
                continue
            in_fence = True
            fence_ticks = fence.group("ticks")
            out.append(line)
            i += 1
            continue

        if in_fence:
            close = RE_FENCE.match(line)
            if close and close.group("ticks").startswith(fence_ticks[0] * 3) and not close.group("info"):
                in_fence = False
            out.append(line)
            i += 1
            continue

        # --- chapter nav link ---
        if RE_NAV_LINE.match(line):
            counters["nav"] += 1
            i += 1
            continue

        # --- html comments (may span lines) ---
        if "<!--" in line:
            block = line
            while "-->" not in block and i + 1 < len(lines):
                i += 1
                block += "\n" + lines[i]

            def _capture(match: re.Match[str]) -> str:
                inner = match.group(1).strip()
                counters["comment"] += 1
                prov = RE_PROVENANCE.match(inner)
                if provenance and prov:
                    note = " ".join(prov.group("text").split())
                    # Skip the boilerplate per-chapter banner; keep real provenance.
                    if not note.startswith("simic HLD v4.1 chapter"):
                        pending_provenance.append(note)
                        counters["provenance"] += 1
                return ""

            residue = RE_HTML_COMMENT.sub(_capture, block).strip()
            if residue:
                out.append(residue)
            i += 1
            continue

        # --- headings ---
        heading = RE_ATX_HEADING.match(line)
        if heading:
            level = len(heading.group("hashes"))

            # Drop a LEADING h1 only — that is the document title, which the
            # cover page carries. An h1 appearing after any heading is real
            # content and must survive.
            if level == 1 and not seen_heading:
                counters["title_h1"] += 1
                seen_heading = True
                in_front_matter = True
                i += 1
                continue

            seen_heading = True
            in_front_matter = False

            if in_invariants:
                out.append(":::")
                out.append("")
                in_invariants = False

            out.append(_rewrite_links(line, counters))

            # Emit any provenance captured just above this heading.
            if pending_provenance:
                out.append("")
                out.append("```{=typst}")
                for note in pending_provenance:
                    out.append(f"#provenance-note[{_typst_escape(note)}]")
                out.append("```")
                pending_provenance.clear()

            invariants_pending = bool(RE_INVARIANTS_HEADING.match(line))
            i += 1
            continue

        # --- open the invariants div at the start of the §18 list ---
        if invariants_pending and RE_ORDERED_ITEM.match(line):
            # An explicit identifier, not a class: pandoc's Typst writer emits a
            # `<simic-invariants>` label for `{#id}` but emits nothing at all for
            # a bare class. The name is prefixed to avoid colliding with the
            # heading anchors pandoc auto-generates — `invariants` is already
            # taken by the "Invariants" heading in all fourteen domain chapters.
            out.append("::: {#simic-invariants}")
            in_invariants = True
            invariants_pending = False
            counters["invariant_lists"] += 1

        # --- close it when the list ends ---
        if in_invariants and line.strip() and not RE_ORDERED_ITEM.match(line) and not line.startswith((" ", "\t")):
            out.append(":::")
            out.append("")
            in_invariants = False

        # --- front-matter `**Key:** value` lines, before the first section ---
        if in_front_matter and RE_FRONTMATTER_KEY.match(line):
            counters["frontmatter"] += 1
            i += 1
            continue

        # --- horizontal rules ---
        if RE_HRULE.match(line):
            counters["hrule"] += 1
            i += 1
            continue

        out.append(_rewrite_links(line, counters))
        i += 1

    if in_invariants:
        out.append(":::")

    if pending_provenance:
        log(f"  [warn] {path}: {len(pending_provenance)} provenance note(s) had no following heading")

    return out


def _rewrite_links(line: str, counters: dict[str, int]) -> str:
    """Reduce relative .md links to their link text; leave http(s) links alone."""

    def repl(match: re.Match[str]) -> str:
        counters["mdlink"] += 1
        text = match.group("text").strip()
        return text if text else match.group("href")

    return RE_MD_LINK.sub(repl, line)


def _typst_escape(text: str) -> str:
    for char in ("\\", "#", "[", "]", "*", "_", "$", "@", "<", ">", "`"):
        text = text.replace(char, "\\" + char)
    return text


# --- Driver ---------------------------------------------------------------


def read_chapter_list(path: Path) -> list[str]:
    chapters: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            chapters.append(line)
    return chapters


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design-dir", required=True, type=Path)
    parser.add_argument("--chapters", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cache-dir", required=True, type=Path)
    parser.add_argument(
        "--typst-root",
        required=True,
        type=Path,
        help="Directory passed to `typst compile --root`; asset paths are emitted relative to it.",
    )
    parser.add_argument(
        "--diagram-dir",
        type=Path,
        default=None,
        help="Read-only directory of pre-rendered print diagrams (shared tooling output).",
    )
    parser.add_argument(
        "--diagram-map",
        type=Path,
        default=None,
        help="File mapping a chapter mermaid block's content digest to a pre-rendered asset stem.",
    )
    parser.add_argument(
        "--provenance",
        action="store_true",
        help="Render <!-- hld: ... --> decomposition provenance as notes under headings.",
    )
    parser.add_argument(
        "--no-render-mermaid",
        dest="render_mermaid",
        action="store_false",
        help="Never invoke mmdc; keep mermaid blocks as monospace source.",
    )
    args = parser.parse_args()

    chapters = read_chapter_list(args.chapters)
    if not chapters:
        log(f"error: no chapters listed in {args.chapters}")
        return 1

    missing = [c for c in chapters if not (args.design_dir / c).is_file()]
    if missing:
        for c in missing:
            log(f"error: chapter not found: {args.design_dir / c}")
        return 1

    # Warn about design chapters absent from the manifest, so new chapters are
    # not silently omitted from the document.
    listed = set(chapters)
    known_excluded = {"00-INDEX.md", "TEMPLATE-lld.md"}
    on_disk = {str(p.relative_to(args.design_dir)) for p in args.design_dir.rglob("*.md")}
    unlisted = sorted(on_disk - listed - known_excluded)
    if unlisted:
        log("warning: design chapters not listed in chapters.txt (omitted from the PDF):")
        for c in unlisted:
            log(f"  - {c}")

    counters = {
        "nav": 0,
        "comment": 0,
        "provenance": 0,
        "title_h1": 0,
        "frontmatter": 0,
        "hrule": 0,
        "mdlink": 0,
        "mermaid": 0,
        "invariant_lists": 0,
    }

    diagram_map = read_diagram_map(args.diagram_map) if args.diagram_map else {}

    args.output.parent.mkdir(parents=True, exist_ok=True)

    pieces: list[str] = []
    for chapter in chapters:
        path = args.design_dir / chapter
        log(f"  [chapter] {chapter}")
        lines = transform_chapter(
            path,
            path.read_text(encoding="utf-8"),
            provenance=args.provenance,
            diagram_dir=args.diagram_dir,
            cache_dir=args.cache_dir / "diagrams",
            typst_root=args.typst_root,
            render_mermaid=args.render_mermaid,
            diagram_map=diagram_map,
            counters=counters,
        )
        chunk = "\n".join(lines).strip("\n")
        if chunk:
            pieces.append(chunk)

    args.output.write_text("\n\n".join(pieces) + "\n", encoding="utf-8")

    log(
        "  [preprocess] "
        f"{len(chapters)} chapters, "
        f"{counters['nav']} nav links, "
        f"{counters['comment']} comments ({counters['provenance']} kept), "
        f"{counters['frontmatter']} front-matter lines, "
        f"{counters['hrule']} rules, "
        f"{counters['mdlink']} md links, "
        f"{counters['mermaid']} mermaid, "
        f"{counters['invariant_lists']} invariant list(s)"
    )
    if counters["invariant_lists"] != 1:
        log(
            f"  [warn] expected exactly 1 invariants list, found {counters['invariant_lists']} "
            "— check the §18 heading in 02-constitution.md"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
