#!/usr/bin/env python3
"""Repair pandoc's generated Typst tables in place.

Pandoc derives Typst column widths from the *source markdown* character widths
of each column, which is a poor proxy for rendered width: a column of one-word
enum values written in a wide markdown cell gets a wide column, and a column of
long prose written compactly gets a narrow one. Left alone this produces columns
so narrow that every word hyphenates, beside columns of mostly whitespace.

Three passes:

  1. Alignment. Drop pandoc's per-table `align: (auto, ...)` so template.typ's
     table styling governs alignment uniformly.

  2. Explicit overrides. A table whose rendered result was inspected and found
     wrong gets its widths pinned here, keyed by a distinctive string from its
     header row. This is the escape hatch for tables the heuristic cannot fix.

  3. Minimum-width heuristic. For any remaining table, lift columns below a
     floor and renormalise to 100%. Catches the systematic "one starved column"
     case without needing an entry per table.

Pass 3 is a heuristic and can be wrong. Every change it makes is logged, and the
build script's --check step renders sample pages so the result is inspected
rather than assumed.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# --- Explicit per-table overrides -----------------------------------------
#
# Keyed by a string that appears within 20 lines after the table's `columns:`
# line — normally distinctive header-cell text. Values are the full column spec.
#
# Each entry records why it exists, so a future editor can tell a deliberate
# pin from an accident.

TABLE_OVERRIDES: dict[str, str] = {
    # programme/curriculum.md §16.1 — the scaffold withdrawal pattern. Six
    # columns, four of which hold full sentences; the widest source table in the
    # document. Dimension and failure-mode stay narrow so the four stage columns
    # get usable width.
    "Failure mode protected against": "13%, 17%, 18%, 18%, 17%, 17%",
    # appendices/glossary.md App D — codename, plain-English role, newsroom
    # shorthand. Codenames are single words; the two prose columns need the room.
    "Newsroom shorthand": "16%, 46%, 38%",
    # programme/risks-and-open-decisions.md §26 — risk table. The mitigation
    # column carries the longest prose and was being starved.
    "Mitigation": "26%, 12%, 62%",
}

# Columns below this percentage are lifted to it, then all columns renormalised.
MIN_WIDTH = 11.0
FLOOR = 14.0

RE_COLUMNS = re.compile(r"columns:\s*\(([^)]*)\)")
RE_PERCENT = re.compile(r"([0-9.]+)%")

# Pandoc emits `columns: 3` (an integer) when the source markdown gave no
# relative widths, which Typst reads as three `auto` columns. Auto sizing is
# usually acceptable, but an override needs to be able to replace this form too.
RE_COLUMNS_ANY = re.compile(r"columns:\s*(?:\([^)]*\)|\d+)")


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def strip_alignment(text: str) -> tuple[str, int, int]:
    """Remove pandoc's per-table alignment so template.typ governs it.

    Two separate things to undo:

      `align: (auto, auto, ...)` inside the table call — pandoc's per-column
      alignment, which overrides the template's uniform left alignment.

      `align(center)[#table(...)]` wrapping the table — pandoc centres every
      table, and because the wrapper sets the alignment context, it centres the
      cell *text* too. Every table in this document is prose, which reads badly
      centred.
    """
    lines = text.split("\n")
    kept, removed = [], 0
    for line in lines:
        if re.fullmatch(r"\s*align:\s*\([^)]*\),\s*", line):
            removed += 1
            continue
        kept.append(line)
    text = "\n".join(kept)

    text, uncentred = re.subn(r"align\(center\)\[#table", "[#table", text)
    return text, removed, uncentred


# --- Tables that need a landscape page ------------------------------------
#
# Keyed the same way as TABLE_OVERRIDES. A table listed here has its whole
# `#figure(...)` wrapped in a flipped page, roughly 25cm of text width instead of
# 15.5cm. Reserved for tables that fit portrait only by hyphenating nearly every
# word — six prose columns cannot be rescued by width tuning alone.

LANDSCAPE_TABLES: set[str] = {
    # programme/curriculum.md §16.1 — six columns, four of them full sentences.
    # Portrait gives each stage column ~2.6cm, which breaks words on every line.
    "Failure mode protected against",
}


def wrap_landscape_tables(text: str) -> tuple[str, list[str]]:
    """Wrap flagged table figures in a landscape page.

    Relies on the shape pandoc's Typst writer gives every table figure:

        #figure(
          align(center)[#table(   <- the `align(center)` is already stripped
            ...
          )]
          , kind: table
          )

    The figure opens with `#figure(` at column 0 and closes with a `  )` line
    following `  , kind: table`. Anything that does not match that shape is left
    alone and reported, so a pandoc output change degrades to "no landscape page"
    rather than to corrupted Typst.
    """
    lines = text.split("\n")
    applied: list[str] = []

    for marker in sorted(LANDSCAPE_TABLES):
        start = None
        for i, line in enumerate(lines):
            if line.startswith("#figure("):
                start = i
            if start is not None and marker in line:
                break
        else:
            log(f"  [warn] landscape table {marker!r} matched nothing")
            continue
        if start is None:
            log(f"  [warn] landscape table {marker!r}: no enclosing #figure(")
            continue

        end = None
        for j in range(start, min(start + 400, len(lines))):
            if lines[j].strip() == ", kind: table":
                if j + 1 < len(lines) and lines[j + 1].rstrip() == "  )":
                    end = j + 1
                break
        if end is None:
            log(f"  [warn] landscape table {marker!r}: could not find figure end")
            continue

        lines[start : end + 1] = [
            "#page(flipped: true, margin: (x: 1.8cm, y: 1.8cm))[",
            *lines[start : end + 1],
            "]",
        ]
        applied.append(marker)

    return "\n".join(lines), applied


def apply_overrides(text: str) -> tuple[str, list[str]]:
    lines = text.split("\n")
    applied: list[str] = []
    for marker, widths in TABLE_OVERRIDES.items():
        for i, line in enumerate(lines):
            if "columns:" not in line:
                continue
            window = "\n".join(lines[i : i + 20])
            if marker in window:
                new = RE_COLUMNS_ANY.sub(f"columns: ({widths})", line)
                if new != line:
                    lines[i] = new
                    applied.append(f"{marker!r} -> ({widths})")
                break
    return "\n".join(lines), applied


def widen_narrow_columns(text: str) -> tuple[str, list[str]]:
    changes: list[str] = []
    pinned = set(TABLE_OVERRIDES.values())

    def fix(match: re.Match[str]) -> str:
        spec = match.group(1)
        # Leave anything already pinned by an override untouched.
        if spec.strip() in pinned:
            return match.group(0)
        found = RE_PERCENT.findall(spec)
        if not found:
            return match.group(0)
        vals = [float(v) for v in found]
        if len(vals) < 3 or not any(v < MIN_WIDTH for v in vals):
            return match.group(0)
        lifted = [max(v, FLOOR) for v in vals]
        total = sum(lifted)
        norm = [v * 100.0 / total for v in lifted]
        new_spec = ", ".join(f"{v:.2f}%" for v in norm)
        changes.append(f"({', '.join(f'{v:.1f}%' for v in vals)}) -> ({', '.join(f'{v:.1f}%' for v in norm)})")
        return f"columns: ({new_spec})"

    return RE_COLUMNS.sub(fix, text), changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("typ", type=Path, help="Generated .typ file to repair in place")
    args = parser.parse_args()

    text = args.typ.read_text(encoding="utf-8")

    text, removed, uncentred = strip_alignment(text)
    text, applied = apply_overrides(text)
    text, widened = widen_narrow_columns(text)
    # Last, so the figure shape it matches on is still intact.
    text, landscaped = wrap_landscape_tables(text)

    args.typ.write_text(text, encoding="utf-8")

    log(f"  [postprocess] dropped {removed} align() spec(s), uncentred {uncentred} table(s)")
    for marker in landscaped:
        log(f"  [postprocess] landscape page for table {marker!r}")
    for entry in applied:
        log(f"  [postprocess] override {entry}")
    unapplied = len(TABLE_OVERRIDES) - len(applied)
    if unapplied:
        matched = {e.split(" -> ")[0].strip("'\"") for e in applied}
        for marker in TABLE_OVERRIDES:
            if marker not in matched:
                log(f"  [warn] table override {marker!r} matched nothing — the source table may have been renamed or removed")
    for entry in widened:
        log(f"  [postprocess] widened {entry}")
    if not widened:
        log("  [postprocess] no narrow-column tables needed widening")
    return 0


if __name__ == "__main__":
    sys.exit(main())
