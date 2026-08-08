# PDR-0014 — Documentation as derived artifacts: site, generated wiki, and HLD PDF published

Date: 2026-08-08   Status: accepted   Author: Claude (product-owner session)
Owner sign-off: yes — every outward-facing step was owner-directed
in-session: "push to the remote repo and publish simic.foundryside.dev (I
added the DNS)", PDFs + "wiki should be automatically generated not
constructed", "commit it all when it's ready".
Related: commits 98ea01e, a67b3eb, 4538a78, 2fd97e1; tools/{diagrams,wiki,pdf}/;
simic-2c529002cf (invariant-preservation rule), simic-c625991e01 (§16.1 nit)

## Context

The project acquired a public face this session. The owner set one hard
constraint: derived documentation is GENERATED from `docs/design/`, never
hand-constructed — the chapters stay the single source of truth.

## The call

One source of truth, three derived artifacts, all live:

1. **Marketing site** — `site/`, zero-JS/zero-external-request, at
   https://simic.foundryside.dev (GitHub Pages, Weft-pattern CNAME);
   mermaid diagrams pre-rendered to light/dark SVG via shared
   `tools/diagrams/` (gated: script-free, no foreignObject, dimension
   sync).
2. **Wiki** — mkdocs-material over a STAGED copy of the chapters
   (`tools/wiki/`), strict build, auto-derived nav, served at `/design/`;
   redeploys automatically on any chapter push.
3. **HLD PDF** — Typst pipeline (`tools/pdf/`), template + generated
   body, published at `docs/assets/simic-hld.pdf`.

Standing rule adopted from a caught near-miss (a diagram draft silently
dropped INV-27's three words): **derived artifacts that rewrite rather
than pass through chapter text get an invariant-preservation review**
(simic-2c529002cf) — the sentence test applies to derivations.

## Rationale

The derivation discipline mirrors the repo's own constitution (edit the
source, re-render, never hand-edit output) and makes documentation drift
unrepresentable: there is no hand-maintained copy to rot. Publishing
pre-code with an explicit amber status callout was judged a trust asset,
not a risk — the site claims no running system and no results.

## Reversal trigger

If the auto-deploy path ships a broken wiki or an invariant-corrupting
derivation that the strict build + preservation review fail to catch,
the deploy gains a blocking derivation-review gate (human or agent) before
Pages upload — the publication itself is not reversed.
