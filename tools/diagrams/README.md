# tools/diagrams — shared Mermaid sources

The `.mmd` files here are the **single source of truth** for the Simic
architecture diagrams, shared by two consumers that render them differently:
the **static site** (`site/`), which needs a light/dark pair of
transparent-background SVGs because it ships zero JavaScript and therefore
cannot run the mermaid runtime in the browser; and the **PDF document
pipeline** (`tools/pdf/`, in progress), which will need a single print-palette
render on an opaque background. Both read the same `.mmd`; only the render
config differs, so a diagram edit propagates to both on the next render.

**Everything under an output directory is a generated artifact.** Edit the
`.mmd` and re-render — never hand-edit a rendered SVG. The site's SVGs are
committed (`site/assets/diagrams/`) because GitHub Pages deploys `site/`
verbatim with no build step.

## Rendering

```sh
./render.sh site     # -> ../../site/assets/diagrams/*-{light,dark}.svg
./render.sh pdf      # documented stub; see render_pdf() in render.sh
```

Per-diagram, the `site` target runs mermaid-cli twice:

```sh
mmdc --input core-loop.mmd \
     --output ../../site/assets/diagrams/core-loop-light.svg \
     --configFile theme-site-light.json \
     --puppeteerConfigFile puppeteer-config.json \
     --backgroundColor transparent --quiet
# ... and again with theme-site-dark.json -> core-loop-dark.svg
```

The intended `pdf` invocation — single theme, opaque background, output into
the PDF pipeline's build dir, with a `--scale 3` PNG fallback only if Typst
cannot embed the SVG — is specified in the comment block above `render_pdf()`.
That target is deliberately unimplemented; `tools/pdf/` is owned by the
document pipeline.

## Files

| File | Role |
|---|---|
| `core-loop.mmd`, `observation-loop.mmd`, `assurance-loop.mmd` | Diagram sources — edit these |
| `theme-site-light.json`, `theme-site-dark.json` | Mermaid `base` theme + palette mirroring the CSS tokens in `site/style.css` |
| `puppeteer-config.json` | `--no-sandbox` for headless Chrome; render-time only |
| `render.sh` | Target-aware renderer plus the post-render gate |

## Constraints the render config encodes

These are load-bearing, not style preferences:

- **`htmlLabels: false`** — mermaid otherwise wraps label text in
  `<foreignObject>`, which is **not painted** when an SVG loads via `<img>`
  (secure static mode). You would get correctly-shaped boxes with invisible
  text. Because auto-wrapping is weaker without HTML labels, put explicit
  `<br/>` in the `.mmd` where a line should break.
- **`Arial, Helvetica, 'Liberation Sans', sans-serif`** — metric-compatible
  across Windows, macOS and Linux. Node box sizes are baked in at render time,
  so a font with different metrics on the reader's machine overflows the boxes.
  Deliberately *not* `system-ui`, which resolves differently per platform.
- **Palette mirrors `site/style.css`** — the theme JSONs carry the resolved hex
  of the site's CSS custom properties. If you change the site tokens, change
  these and re-render, or the diagrams drift out of the palette.

## The post-render gate

`./render.sh site` fails the build if any of these regress:

- a rendered SVG contains `<script>`;
- a rendered SVG contains `foreignObject` (invisible labels — see above);
- a rendered SVG references anything off-origin (`xmlns` w3.org URIs are
  namespace identifiers, not fetches, and are excluded);
- the `width`/`height` attributes on the `<img>` tags in `site/*.html` no
  longer match the rendered `viewBox`. Editing a node label changes the layout
  and therefore the intrinsic size; without this check the pages ship a wrong
  aspect ratio and a layout shift. Update both `<img>` tags and the inline
  `--dmin` (≈ 0.75 × width) when it fires.

## Not every diagram belongs here

The control hierarchy (`docs/design/04-architecture.md` §7.5) stays as an ASCII
tree in `site/architecture.html`. It is a nested menu of mutually exclusive
actions under one owner; mermaid centre-aligns the two action menus inside a
box and loses the `├──` structure that made the ownership relation legible.
Reach for mermaid when the content is a graph, not when it is a list.
