#!/usr/bin/env python3
"""Post-build gate: every local URL in the built HTML resolves to a real file.

`mkdocs --strict` does NOT cover this. It validates links that came from
markdown, which is most of them — but anything emitted as raw HTML is stashed
by python-markdown and restored *after* the relative-path pass, so its paths
are never rewritten and never checked. That gap shipped twenty broken diagram
images and twenty broken full-size links: `../assets/...` from a page served at
`/reference/diagrams/` resolves one directory too shallow, and every check in
the build was blind to it.

The same technique had already been applied to the "edit this page" URLs, where
it caught a real defect — extract the attribute from the built HTML, resolve it,
assert the target exists. It was applied to one class of URL and not the other.
This closes that: `src` and `href` on every element, checked against the built
tree, so the class is gated by the build rather than by whoever remembers to
look.

Checked:  `src`, `href` and `srcset` on <img>, <a>, <script>, <link> and
          <source>. Every candidate in a srcset is checked, not just the first.
Skipped:  external URLs (scheme-relative or absolute), mailto:/data:, and bare
          fragments — none of them name a file in the output tree. Root-absolute
          URLs outside this wiki's mount point belong to the other half of the
          site and are not ours to verify.

Assumes, and does NOT check:

  * Attributes are double-quoted. Both mkdocs and python-markdown always emit
    them that way (verified: zero single-quoted or unquoted src/href in the
    built site), so a full HTML parser would buy nothing here — but hand-written
    markup in an override template could evade this and would be missed
    silently.
  * URLs live in markup attributes. CSS `url()`, `@import`, and anything a
    script constructs at runtime are outside this net. The broken-diagram class
    this exists to close lives entirely in markup.

Exit 1 with the offending page, attribute and resolved path on any failure.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

HERE = Path(__file__).resolve().parent
SITE = HERE / "build" / "site"


def base_path() -> str:
    """The path `site_url` mounts this wiki at, e.g. `/design/`.

    Root-absolute URLs in the output (mkdocs emits them in 404.html, which may
    be served from any path) are relative to the DEPLOYMENT root, not to
    build/site. Without stripping this prefix every one of them looks broken.
    """
    text = (HERE / "mkdocs.yml").read_text(encoding="utf-8")
    m = re.search(r"^site_url:\s*(\S+)", text, re.M)
    return urlsplit(m.group(1)).path.rstrip("/") if m else ""


ATTR = re.compile(
    r"<(?P<tag>img|a|script|link|source)\b[^>]*?\b(?P<attr>src|srcset|href)=\"(?P<url>[^\"]*)\"",
    re.I | re.S,
)
EXTERNAL = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//)", re.I)


def candidate_urls(attr: str, value: str) -> list[str]:
    """The URLs in one attribute value.

    `srcset` is a comma-separated candidate list, each entry a URL optionally
    followed by a width or density descriptor (`img.svg 2x`). Every candidate
    is a real request the browser may make, so every one is checked — taking
    only the first would let a broken high-DPI variant through silently.
    """
    if attr.lower() != "srcset":
        return [value]
    return [part.split()[0] for part in value.split(",") if part.strip()]


def resolves(page: Path, url: str, base: str) -> Path | None:
    """The file a URL points at, or None if it is not ours to check."""
    if not url or url.startswith("#") or EXTERNAL.match(url):
        return None
    path = unquote(urlsplit(url).path)
    if not path:
        return None
    if path.startswith("/"):
        # Root-absolute: relative to the deployment root, so drop the mount
        # prefix. A root-absolute URL OUTSIDE our mount belongs to the other
        # half of the site and is not ours to verify.
        if base and not (path == base or path.startswith(base + "/")):
            return None
        target = SITE / path[len(base) :].lstrip("/")
    else:
        target = page.parent / path
    target = Path(target).resolve()
    # A directory URL is served by its index.html.
    return target / "index.html" if url.endswith("/") or target.is_dir() else target


def main() -> int:
    if not SITE.is_dir():
        print(f"check_links.py: no built site at {SITE} — run the build first", file=sys.stderr)
        return 1

    base = base_path()
    pages = sorted(SITE.rglob("*.html"))
    broken: list[tuple[str, str, str, str]] = []
    checked = 0

    for page in pages:
        html = page.read_text(encoding="utf-8", errors="replace")
        for m in ATTR.finditer(html):
            for url in candidate_urls(m.group("attr"), m.group("url")):
                target = resolves(page, url, base)
                if target is None:
                    continue
                checked += 1
                if not target.exists():
                    broken.append(
                        (
                            str(page.relative_to(SITE)),
                            m.group("tag"),
                            url,
                            str(target),
                        )
                    )

    if broken:
        print(f"check_links.py: {len(broken)} broken local link(s) in the built site:", file=sys.stderr)
        for where, tag, url, missing in broken[:40]:
            print(f"  {where}: <{tag}> {url}  ->  {missing} (missing)", file=sys.stderr)
        if len(broken) > 40:
            print(f"  ... and {len(broken) - 40} more", file=sys.stderr)
        print(
            "\n  Raw HTML emitted by stage.py is the usual cause: mkdocs rewrites relative\n"
            "  paths only in markdown-derived elements, so a raw <img src> or <a href> is\n"
            "  published verbatim and resolves relative to the page's directory URL.\n"
            '  Emit markdown inside a `markdown="span"` container instead.',
            file=sys.stderr,
        )
        return 1

    print(f"links: {checked} local URLs across {len(pages)} pages all resolve")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
