#!/usr/bin/env python3
"""Offline link + fragment check for the assembled Pages artifact.

Checks every href/src in the hand-written root pages: that the target file
exists in the artifact, and that any #fragment resolves to a real id on the
target page. External (http/https) and mailto links are listed, not fetched —
the deploy must not depend on third-party availability.

The fragment half is the point: the marketing pages cite the design wiki by
deep link, and mkdocs slugs change when a heading is reworded. A silent 404
inside our own domain is exactly what --strict buys on the wiki side.
"""

import html
import re
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else "_pages")
pages = sorted(root.glob("*.html"))
if not pages:
    sys.exit(f"linkcheck: no root pages found under {root}")

ATTR = re.compile(r'(?:href|src|srcset)\s*=\s*"([^"]+)"', re.I)
ID = re.compile(r'\sid="([^"]+)"')
ids_cache: dict[Path, set[str]] = {}


def ids_of(path: Path) -> set[str]:
    if path not in ids_cache:
        try:
            ids_cache[path] = set(ID.findall(path.read_text(encoding="utf-8", errors="replace")))
        except OSError:
            ids_cache[path] = set()
    return ids_cache[path]


def target_file(url: str, page: Path) -> Path:
    base = root if url.startswith("/") else page.parent
    p = (base / url.lstrip("/")).resolve()
    # A directory URL (/design/, /design/01-claim/) serves its index.html.
    return p / "index.html" if p.is_dir() else p


broken, external, checked = [], set(), 0
for page in pages:
    text = page.read_text(encoding="utf-8")
    for raw in ATTR.findall(text):
        url = html.unescape(raw.split()[0] if " " in raw else raw).strip()
        if not url or url.startswith(("http://", "https://", "mailto:", "data:", "//")):
            if url.startswith(("http://", "https://")):
                external.add(url)
            continue
        checked += 1
        path_part, _, frag = url.partition("#")
        tgt = target_file(path_part, page) if path_part else page
        if not tgt.is_file():
            broken.append(f"{page.name}: {url} -> missing {tgt.relative_to(root.resolve())}")
            continue
        if frag and frag not in ids_of(tgt):
            broken.append(f'{page.name}: {url} -> no id="{frag}" in {tgt.relative_to(root.resolve())}')

print(f"linkcheck: {len(pages)} root pages, {checked} internal links checked, {len(external)} external links listed (not fetched)")
for url in sorted(external):
    print(f"  external: {url}")
if broken:
    print("\nlinkcheck: BROKEN INTERNAL LINKS", file=sys.stderr)
    for b in broken:
        print(f"  {b}", file=sys.stderr)
    sys.exit(1)
print("linkcheck: all internal links and fragments resolve")
