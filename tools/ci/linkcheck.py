#!/usr/bin/env python3
"""Offline link + fragment check for the assembled Pages artifact.

Checks every href/src in the hand-written root pages: that the target file
exists in the artifact, and that any #fragment resolves to a real id on the
target page. Third-party http(s) and mailto links are listed, not fetched —
the deploy must not depend on someone else's availability.

The fragment half is the point: the marketing pages cite the design wiki by
deep link, and mkdocs slugs change when a heading is reworded. A silent 404
inside our own domain is exactly what --strict buys on the wiki side.

Usage: linkcheck.py <pages-dir>
"""

import html
import re
import sys
from pathlib import Path

# Absolute URLs on our own origin are NOT third-party: canonical and og:url
# point at the very pages in this artifact, and a typo in one is exactly the
# silent breakage this gate exists to catch. They are rewritten to root-relative
# and checked like any internal link.
SELF_ORIGINS = ("https://simic.foundryside.dev", "http://simic.foundryside.dev")

root = Path(sys.argv[1]).resolve()
pages = sorted(root.glob("*.html"))
if not pages:
    sys.exit(f"linkcheck: no root pages found under {root}")

# The attribute name is CAPTURED, not just matched: only srcset is a
# comma-separated candidate list, and the splitter must be able to tell which
# attribute it is looking at. (When this group was non-capturing, every value
# got comma-split — which broke every data: URI, since RFC 2397 puts a comma
# between the media type and the payload.)
#
# `content` is included for the same-origin metadata check below: og:url,
# og:image and twitter:image are real URLs that must resolve, but they live in
# content= alongside prose like og:description, so they are filtered by value
# (must start with one of SELF_ORIGINS) rather than by attribute name.
ATTR = re.compile(r"\b(href|src|srcset|content)\s*=\s*([\"'])(.*?)\2", re.I | re.S)

# Schemes that never denote a file inside the artifact. Checked BEFORE any
# comma-splitting: `data:` payloads legitimately contain commas, semicolons and
# base64 that must never be parsed as a path.
NON_FILE_SCHEMES = ("data:", "mailto:", "tel:", "javascript:", "blob:", "about:")

# Fragment targets. Accepts single-quoted, double-quoted and bare id values,
# case-insensitively.
#
# ASSUMPTION, and the reason this is deliberately permissive: the ids we resolve
# against live in the mkdocs-generated wiki under /design/, so this regex is
# coupled to that build's HTML serializer. Today it emits unminified
# double-quoted attributes and mkdocs.yml has no minify plugin. If one is ever
# enabled, single-quoted or unquoted ids would stop matching and this gate would
# report BROKEN for links that are actually fine — failing a clean deploy, which
# is the dangerous direction for a gate to fail in. Handling all three quoting
# styles makes that config change a non-event.
ID = re.compile(r"""\sid\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>=`]+))""", re.I)

ids_cache: dict[Path, set[str]] = {}


def ids_of(path: Path) -> set[str]:
    if path not in ids_cache:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            ids_cache[path] = set()
        else:
            ids_cache[path] = {m[0] or m[1] or m[2] for m in ID.findall(text)}
    return ids_cache[path]


def candidate_urls(attr: str, raw: str) -> list[str]:
    """Every URL in one attribute value.

    Comma-splitting applies to `srcset` ONLY. srcset is a comma-separated
    candidate list, each entry optionally followed by a descriptor
    ("img.svg 2x", "img.svg 800w"), so splitting on whitespace alone would
    check the first candidate and silently ignore the rest.

    Every other attribute is returned whole. Commas are legal and common in
    ordinary URLs — a `data:` URI always contains one (RFC 2397 separates the
    media type from the payload), and a path like `/a,b/c.html` is perfectly
    valid. Splitting those produces garbage fragments that then get reported as
    missing files, failing a deploy over markup that is completely fine.
    """
    value = html.unescape(raw).strip()
    if attr.lower() != "srcset":
        return [value] if value else []
    out = []
    for part in value.split(","):
        part = part.strip()
        if part:
            out.append(part.split()[0])
    return out


def target_file(url: str, page: Path) -> Path | None:
    """Resolve a URL to a file in the artifact, or None if it escapes it."""
    base = root if url.startswith("/") else page.parent
    p = (base / url.lstrip("/")).resolve()
    # Containment: a `../` chain can resolve to a real file OUTSIDE the artifact,
    # which exists on this disk but 404s in production. Refuse to be reassured
    # by the local filesystem.
    if not p.is_relative_to(root):
        return None
    # A directory URL (/design/, /design/01-claim/) serves its index.html.
    return p / "index.html" if p.is_dir() else p


broken: list[str] = []
external: set[str] = set()
selfref = 0
checked = 0

for page in pages:
    text = page.read_text(encoding="utf-8")
    for attr, _quote, raw in ATTR.findall(text):
        is_content = attr.lower() == "content"

        # Scheme filter runs on the WHOLE value, before any splitting, so a
        # data: payload is discarded intact rather than shredded on its commas.
        whole = html.unescape(raw).strip()
        if whole.lower().startswith(NON_FILE_SCHEMES):
            continue

        # `content` carries mostly prose (og:description, viewport, the theme
        # colour...). Only same-origin absolute URLs in it are checkable; a bare
        # sentence must never be resolved as a path. This is intentionally
        # stricter than href/src: no relative paths, no root-relative, no
        # fragments — if it does not start with our own origin, it is ignored.
        if is_content and not whole.startswith(SELF_ORIGINS):
            continue

        for url in candidate_urls(attr, raw):
            if not url:
                continue

            # Rewrite same-origin absolutes to root-relative, then check them
            # like any internal link.
            same_origin = False
            for origin in SELF_ORIGINS:
                if url.startswith(origin):
                    url = url[len(origin) :] or "/"
                    selfref += 1
                    same_origin = True
                    break

            if not same_origin:
                if url.startswith(("http://", "https://", "//")):
                    external.add(url)  # third-party: listed, never fetched
                    continue
                if url.lower().startswith(NON_FILE_SCHEMES):
                    continue  # not a file in this artifact
            # Everything else — including a bare "#frag" (checked against the
            # page it appears on, which is how the skip link and the heading
            # permalinks get verified) — falls through to the check below.

            checked += 1
            path_part, _, frag = url.partition("#")
            tgt = target_file(path_part, page) if path_part else page
            if tgt is None:
                broken.append(f"{page.name}: {url} -> escapes the artifact root")
            elif not tgt.is_file():
                broken.append(f"{page.name}: {url} -> missing {tgt.relative_to(root)}")
            elif frag and frag not in ids_of(tgt):
                broken.append(f'{page.name}: {url} -> no id="{frag}" in {tgt.relative_to(root)}')

print(
    f"linkcheck: {len(pages)} root pages, {checked} internal links checked "
    f"({selfref} same-origin absolute), {len(external)} third-party listed (not fetched)"
)
for url in sorted(external):
    print(f"  external: {url}")
if broken:
    print("\nlinkcheck: BROKEN INTERNAL LINKS", file=sys.stderr)
    for b in broken:
        print(f"  {b}", file=sys.stderr)
    sys.exit(1)
print("linkcheck: all internal links and fragments resolve")
