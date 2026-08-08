#!/usr/bin/env bash
#
# Build the consolidated Simic HLD PDF from the design chapters.
#
# Runs end to end from a clean checkout:
#
#   tools/pdf/build.sh                 # build docs/assets/simic-hld.pdf
#   tools/pdf/build.sh --check         # build, then verify the result
#   tools/pdf/build.sh --keep          # keep build/ intermediates for debugging
#   tools/pdf/build.sh --no-provenance # omit the ADR/monolith provenance notes
#   tools/pdf/build.sh --no-mermaid    # never call mmdc; keep diagram source
#
# Pipeline:
#   docs/design/*.md
#     -> preprocess.py   assemble in concordance order, print transforms
#     -> pandoc          markdown -> Typst, via pandoc-typst.typ
#     -> postprocess.py  repair pandoc's table column widths
#     -> typst compile   -> docs/assets/simic-hld.pdf
#
# Required:  pandoc >= 3.2 (Typst writer), typst >= 0.14, python3 >= 3.10
# Optional:  mmdc (mermaid-cli)  renders mermaid diagrams; without it they fall
#                                back to monospace source blocks
#            pdfinfo, pdftotext, pdftoppm (poppler-utils)  needed by --check
#
# The design chapters are the single source of truth. Nothing in this pipeline
# writes to docs/design/, and nothing writes to tools/diagrams/.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

DESIGN_DIR="$REPO_ROOT/docs/design"
BUILD_DIR="$SCRIPT_DIR/build"
OUT_PDF="$REPO_ROOT/docs/assets/simic-hld.pdf"

# Pre-rendered print-palette diagrams from the shared diagram tooling. Read-only
# and optional: when this directory exists its assets take precedence over any
# local mmdc render. Override with SIMIC_DIAGRAM_DIR.
DIAGRAM_DIR="${SIMIC_DIAGRAM_DIR:-$REPO_ROOT/tools/diagrams/build/pdf}"

BODY_MD="$BUILD_DIR/body.md"
GEN_TYP="$BUILD_DIR/simic-hld.typ"

DO_CHECK=false
KEEP=false
PROVENANCE=--provenance
MERMAID=()

for arg in "$@"; do
  case "$arg" in
    --check)          DO_CHECK=true ;;
    --keep)           KEEP=true ;;
    --no-provenance)  PROVENANCE= ;;
    --no-mermaid)     MERMAID=(--no-render-mermaid) ;;
    -h|--help)        sed -n '2,40p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown argument: $arg" >&2; echo "try: $0 --help" >&2; exit 2 ;;
  esac
done

# --- Tool checks ----------------------------------------------------------

require() {
  local tool="$1" hint="$2"
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "error: required tool '$tool' not found on PATH — $hint" >&2
    exit 1
  fi
}

echo "=== Checking toolchain ==="
require pandoc  "install pandoc >= 3.2 (needs the Typst writer)"
require typst   "install typst >= 0.14"
require python3 "install python3 >= 3.10"

PANDOC_VERSION="$(pandoc --version | head -1 | awk '{print $2}')"
TYPST_VERSION="$(typst --version | awk '{print $2}')"
echo "  pandoc  $PANDOC_VERSION"
echo "  typst   $TYPST_VERSION"
echo "  python3 $(python3 --version | awk '{print $2}')"

# Version floors. pandoc's Typst writer is only reliable from 3.2; Typst's
# `context` keyword (used by the running header) needs 0.11+, and tagged-PDF
# export needs 0.14+.
python3 - "$PANDOC_VERSION" "$TYPST_VERSION" <<'PY' || exit 1
import sys

def parse(v):
    parts = []
    for chunk in v.split("."):
        digits = "".join(c for c in chunk if c.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts + [0, 0])[:3]

pandoc, typst = parse(sys.argv[1]), parse(sys.argv[2])
ok = True
if pandoc < (3, 2, 0):
    print(f"error: pandoc {sys.argv[1]} is too old; need >= 3.2", file=sys.stderr)
    ok = False
if typst < (0, 14, 0):
    print(f"error: typst {sys.argv[2]} is too old; need >= 0.14", file=sys.stderr)
    ok = False
sys.exit(0 if ok else 1)
PY

if command -v mmdc >/dev/null 2>&1; then
  echo "  mmdc    $(mmdc --version 2>/dev/null | tail -1) (mermaid rendering available)"
else
  echo "  mmdc    not found — mermaid diagrams will render as source blocks"
fi

if [[ -d "$DIAGRAM_DIR" ]]; then
  echo "  diagrams: using pre-rendered assets from ${DIAGRAM_DIR#"$REPO_ROOT"/}"
else
  echo "  diagrams: ${DIAGRAM_DIR#"$REPO_ROOT"/} absent (shared tooling not built yet)"
fi

# --- Reproducible date ----------------------------------------------------
# Taken from the last commit touching docs/design/ so a clean checkout of a
# given revision always yields the same PDF. Override with SIMIC_PDF_DATE.

if [[ -n "${SIMIC_PDF_DATE:-}" ]]; then
  DOC_DATE="$SIMIC_PDF_DATE"
elif git -C "$REPO_ROOT" rev-parse --git-dir >/dev/null 2>&1; then
  DOC_DATE="$(git -C "$REPO_ROOT" log -1 --format=%cs -- docs/design 2>/dev/null || true)"
  [[ -z "$DOC_DATE" ]] && DOC_DATE="$(date -u +%Y-%m-%d)"
else
  DOC_DATE="$(date -u +%Y-%m-%d)"
fi
echo "  date    $DOC_DATE"

# --- Assemble -------------------------------------------------------------

echo
echo "=== Assembling chapters ==="
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

python3 "$SCRIPT_DIR/preprocess.py" \
  --design-dir "$DESIGN_DIR" \
  --chapters "$SCRIPT_DIR/chapters.txt" \
  --output "$BODY_MD" \
  --cache-dir "$BUILD_DIR" \
  --typst-root "$REPO_ROOT" \
  --diagram-dir "$DIAGRAM_DIR" \
  --diagram-map "$SCRIPT_DIR/diagrams.map" \
  ${PROVENANCE:+$PROVENANCE} \
  "${MERMAID[@]+"${MERMAID[@]}"}"

# --- Markdown -> Typst ----------------------------------------------------
#
# Reader extensions:
#   tex_math_single_backslash  the chapters use \( ... \) for inline math
#                              alongside $...$ and $$...$$; without this the
#                              delimiters render as literal parentheses.
#   pipe_tables / grid_tables  the chapters' table styles.
#   fenced_divs                lets preprocess.py mark the §18 invariants list.
#
# --columns=200 keeps pandoc from re-wrapping wide table source, which would
# distort the column widths it computes.

echo
echo "=== Generating Typst ==="
pandoc "$BODY_MD" \
  --from=markdown+tex_math_single_backslash+pipe_tables+grid_tables+fenced_divs \
  --to=typst \
  --template="$SCRIPT_DIR/pandoc-typst.typ" \
  --metadata-file="$SCRIPT_DIR/metadata.yaml" \
  --metadata=date="$DOC_DATE" \
  --standalone \
  --wrap=preserve \
  --columns=200 \
  -o "$GEN_TYP"
echo "  -> ${GEN_TYP#"$REPO_ROOT"/}"

python3 "$SCRIPT_DIR/postprocess.py" "$GEN_TYP"

# --- Typst -> PDF ---------------------------------------------------------
#
# --root is the repo so the generated Typst may reference diagram assets that
# live outside tools/pdf/ (Typst refuses paths above its root).

echo
echo "=== Compiling PDF ==="
mkdir -p "$(dirname "$OUT_PDF")"
typst compile \
  --root "$REPO_ROOT" \
  "$GEN_TYP" \
  "$OUT_PDF"
echo "  -> ${OUT_PDF#"$REPO_ROOT"/}"

# --- Report ---------------------------------------------------------------

echo
echo "=== Result ==="
SIZE="$(du -h "$OUT_PDF" | cut -f1)"
if command -v pdfinfo >/dev/null 2>&1; then
  # poppler mis-validates the `/Suspects false` boolean that Typst writes into
  # the tagged-PDF MarkInfo dictionary, and prints a "Syntax Error" for a file
  # that is in fact well-formed (Tagged: yes, all metadata readable). Filtered so
  # a clean build does not look like a failing one.
  PAGES="$(pdfinfo "$OUT_PDF" 2> >(grep -v 'Suspects object is wrong type' >&2) | awk '/^Pages:/ {print $2}')"
  echo "  pages   $PAGES"
fi
echo "  size    $SIZE"
echo "  path    $OUT_PDF"

# --- Verification ---------------------------------------------------------

if $DO_CHECK; then
  echo
  echo "=== Verifying ==="
  "$SCRIPT_DIR/check.sh" "$OUT_PDF" "$BUILD_DIR"
fi

if ! $KEEP; then
  # Keep the generated .typ: it is the useful debugging artefact and is small.
  find "$BUILD_DIR" -name 'body.md' -delete
fi

echo
echo "Done."
