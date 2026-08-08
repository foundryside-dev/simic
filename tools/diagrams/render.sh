#!/usr/bin/env bash
# Render the Simic architecture diagrams from their Mermaid sources.
#
# The .mmd files in this directory are the SINGLE SOURCE OF TRUTH for each
# diagram. Everything under an output directory is a generated artifact — edit
# the .mmd and re-render; never hand-edit a rendered SVG.
#
#   ./render.sh site      light + dark transparent SVG pairs -> ../../site/assets/diagrams/
#   ./render.sh pdf       (stub — see the pdf target below)
#   ./render.sh           same as `site`
#
# Requires mermaid-cli. Either install it globally:
#   npm install -g @mermaid-js/mermaid-cli
# or let this script fall back to `npx --yes @mermaid-js/mermaid-cli`.
# Puppeteer needs a Chrome/Chromium. puppeteer-config.json passes --no-sandbox,
# which recent Ubuntu (unprivileged user namespaces restricted by AppArmor) and
# most CI containers require; it affects only this local render step and never
# any published artifact.
#
# Why the theme config files matter (do not "simplify" these away):
#   htmlLabels:false  — mermaid otherwise emits <foreignObject> labels, which
#                       are NOT painted for an SVG loaded via <img> (secure
#                       static mode). The boxes would render with no text.
#   Font stack       — mirrors --font-body in ../../site/style.css, so diagram
#                       text matches the surrounding page instead of sitting in
#                       Arial on a system-ui page. CHANGED 2026-08-09 from
#                       Arial/Helvetica/Liberation Sans, which was chosen
#                       because those three are metric-compatible across
#                       Windows/macOS/Linux.
#
#                       That original concern is real and still applies, so read
#                       this before touching the stack: mermaid bakes node box
#                       sizes AND the canvas viewBox in at render time, from
#                       whatever font THIS machine resolves. system-ui resolves
#                       differently per platform, so the geometry is no longer
#                       identical everywhere.
#
#                       Why it is nonetheless safe: on the render machine
#                       system-ui resolved to DejaVu Sans, which is among the
#                       widest common sans faces, so the baked boxes are
#                       generous. Narrower reader fonts (Segoe UI, SF Pro) get
#                       slack, never clipping — slack is the benign direction.
#                       Measured 2026-08-09 across Liberation Sans (== Arial
#                       metrics), DejaVu Sans, Ubuntu and FreeSans: 35 nodes per
#                       diagram, ZERO box overflow and ZERO canvas clipping in
#                       all four.
#
#                       THE TRAP: hand-editing font-family in the rendered SVGs
#                       without re-rendering keeps the old geometry and DOES
#                       clip — measured at 809px declared width, the left edge
#                       label lost its margin and the right one ran off the
#                       canvas. Change the stack HERE and re-render; never patch
#                       the SVGs.
#   -b transparent    — the page background shows through, so one SVG works on
#                       whatever surface it sits on.
#   Palette           — theme-site-{light,dark}.json mirror the CSS custom
#                       properties in ../../site/style.css. Change the site
#                       tokens and you must change these too, then re-render.
set -euo pipefail

cd "$(dirname "$0")"

TARGET="${1:-site}"

if command -v mmdc >/dev/null 2>&1; then
  MMDC=(mmdc)
else
  MMDC=(npx --yes @mermaid-js/mermaid-cli)
fi

# The control hierarchy (docs/design/04-architecture.md §7.5) is deliberately
# NOT here. It is a nested menu of mutually exclusive actions under one owner;
# mermaid renders the two menus as centre-aligned blobs inside a box and loses
# the `|--` tree structure that made the ownership relation legible. It stays as
# the ASCII tree in site/architecture.html#control-hierarchy.
DIAGRAMS=(
  core-loop
  observation-loop
  assurance-loop
)

# --------------------------------------------------------------------------
render_site() {
  local out="../../site/assets/diagrams"
  mkdir -p "$out"

  for name in "${DIAGRAMS[@]}"; do
    for theme in light dark; do
      echo "render: ${out}/${name}-${theme}.svg"
      "${MMDC[@]}" \
        --input  "${name}.mmd" \
        --output "${out}/${name}-${theme}.svg" \
        --configFile "theme-site-${theme}.json" \
        --puppeteerConfigFile puppeteer-config.json \
        --backgroundColor transparent \
        --quiet
    done
  done

  check_site "$out"
}

# --------------------------------------------------------------------------
# STUB — not implemented. Wire this up when the Typst/PDF pipeline lands.
#
# The PDF target differs from the site target in four ways, all of which are
# config, not new sources — the .mmd files above are shared verbatim:
#
#   1. Single theme. Print has no dark mode: render once against a print
#      palette (theme-pdf.json, to be added) — near-black on white, hairline
#      borders, no transparent-surface assumptions.
#   2. Opaque background. Use `--backgroundColor white` rather than
#      transparent, so the diagram does not pick up a tinted page or a
#      figure-frame fill from the Typst template.
#   3. Output format. SVG — measured against Typst by the PDF pipeline
#      (2026-08-08): with `htmlLabels:false` at config TOP LEVEL the SVGs
#      render perfectly (0 foreignObject). The trap: default mermaid emits
#      <foreignObject> labels Typst does not render (typst#1421, all labels
#      blank), and `htmlLabels:false` under `flowchart` only LOOKS like a fix
#      (edge labels return, node labels still blank). Keep the setting at top
#      level in theme-pdf.json and REUSE the site target's foreignObject gate
#      here — that one assertion is what makes SVG safe. Fallback only if a
#      construct ever breaks: `--output x.png --scale 3` (~300dpi, verified).
#   4. Output directory — INTERFACE CONTRACT with tools/pdf/: render into
#      tools/diagrams/build/pdf/ (the PDF build reads it there; env override
#      SIMIC_DIAGRAM_DIR). NOT into site/, NOT into tools/pdf/. Keep the two
#      targets' outputs disjoint so neither can stale the other.
#
# Naming stays semantic (core-loop etc.); the PDF side maps content digests to
# stems in tools/pdf/diagrams.map, so there is no naming coupling.
#
# Deliberately not shared with the site target: the dimension-sync check below
# is an HTML concern and does not apply to PDF output.
#
# NOTE: tools/pdf/ is owned by the document pipeline (committed a67b3eb). This
# target never writes into or restructures it.
render_pdf() {
  cat >&2 <<'MSG'
render.sh: the `pdf` target is a documented stub, not yet implemented.
See the comment block above render_pdf() in this script for the intended
flags (single print theme, opaque background, SVG with htmlLabels:false at
config top level, output into tools/diagrams/build/pdf/). Nothing was rendered.
MSG
  exit 3
}

# --------------------------------------------------------------------------
# Post-render gate for the site target. mermaid-cli emits a self-contained SVG,
# but assert it rather than trust it: an <img>-embedded SVG on a page that makes
# zero external requests must carry no script and no remote reference, and must
# not depend on <foreignObject> text.
check_site() {
  local out="$1" fail=0 f

  for f in "$out"/*.svg; do
    if grep -qi '<script' "$f"; then echo "FAIL $f: contains <script>"; fail=1; fi
    if grep -q  'foreignObject' "$f"; then echo "FAIL $f: foreignObject labels will not paint in <img>"; fail=1; fi
    # Namespace declarations (xmlns=...w3.org...) are identifiers, not fetches;
    # anything else pointing off-origin is.
    if grep -oE '(href|src|url\()[^)"'"'"' >]*https?://[^)"'"'"' >]*' "$f" | grep -qv 'w3\.org'; then
      echo "FAIL $f: external reference"; fail=1
    fi
  done

  # The <img> tag carries width/height so the browser reserves the right box
  # before the SVG loads. Editing a node label — or changing the font stack
  # above — changes the layout and therefore the viewBox, so those attributes
  # drift silently. Assert they still match.
  #
  # The page markup is <picture><source …-dark.svg><img …-light.svg></picture>,
  # so there is exactly ONE <img> per diagram and the light SVG is the one whose
  # dimensions are declared. grep -A1 on the light src still lands on the
  # width/height line.
  local svg name w h page
  for svg in "$out"/*-light.svg; do
    name="$(basename "$svg" -light.svg)"
    read -r w h < <(grep -o 'viewBox="[^"]*"' "$svg" | head -1 |
                    sed 's/viewBox="//; s/"//' | awk '{printf "%d %d\n", ($3+0.5), ($4+0.5)}')
    for page in ../../site/index.html ../../site/architecture.html ../../site/lineage.html; do
      grep -q "diagrams/${name}-light.svg" "$page" 2>/dev/null || continue
      if ! grep -A1 "diagrams/${name}-light.svg" "$page" | grep -q "width=\"${w}\" height=\"${h}\""; then
        echo "FAIL $page: ${name} is now ${w}x${h}; update width/height (and --dmin ~= 0.75*w) on the <img> tag"
        fail=1
      fi
    done
  done

  if [ "$fail" -eq 0 ]; then
    echo "OK: SVGs script-free, self-contained, no foreignObject; HTML dimensions in sync."
  fi
  return "$fail"
}

# --------------------------------------------------------------------------
case "$TARGET" in
  site) render_site ;;
  pdf)  render_pdf  ;;
  *)    echo "usage: $0 [site|pdf]" >&2; exit 2 ;;
esac
