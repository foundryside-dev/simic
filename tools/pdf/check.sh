#!/usr/bin/env bash
#
# Verify a built Simic HLD PDF.
#
#   tools/pdf/check.sh [pdf] [workdir]
#
# Defaults to docs/assets/simic-hld.pdf. Invoked by `build.sh --check`.
#
# Checks content that must survive the markdown -> Typst -> PDF path, so a
# silent rendering regression fails the build rather than shipping:
#   * page count within a sane band
#   * cover page carries title, version and licence
#   * the table of contents was generated
#   * INV-01 and INV-45 both present, i.e. the invariants list rendered whole
#   * math survived: symbols from the admission-utility equation are present
#   * no leaked source syntax (raw HTML comments, unconverted markdown links,
#     stray fenced-div markers, literal \( \) math delimiters)
#   * sample pages rendered to PNG for visual inspection of wide tables
#
# Requires poppler-utils (pdfinfo, pdftotext, pdftoppm).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

PDF="${1:-$REPO_ROOT/docs/assets/simic-hld.pdf}"
WORK="${2:-$SCRIPT_DIR/build}"

for tool in pdfinfo pdftotext pdftoppm; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "error: '$tool' not found — install poppler-utils to run checks" >&2
    exit 1
  fi
done

[[ -f "$PDF" ]] || { echo "error: no such PDF: $PDF" >&2; exit 1; }

mkdir -p "$WORK"
TXT="$WORK/extracted.txt"

# poppler prints a spurious "Syntax Error: Suspects object is wrong type
# (boolean)" for Typst's tagged-PDF MarkInfo dictionary, where `/Suspects false`
# is spec-correct. Filtered so it does not read as a defect in this document.
POPPLER_NOISE='Suspects object is wrong type'

pdftotext -layout "$PDF" "$TXT" 2> >(grep -v "$POPPLER_NOISE" >&2)

FAIL=0
pass() { printf '  \033[32mok\033[0m   %s\n' "$1"; }
fail() { printf '  \033[31mFAIL\033[0m %s\n' "$1"; FAIL=1; }
warn() { printf '  \033[33mwarn\033[0m %s\n' "$1"; }

# --- Page count -----------------------------------------------------------

PAGES="$(pdfinfo "$PDF" 2> >(grep -v "$POPPLER_NOISE" >&2) | awk '/^Pages:/ {print $2}')"
if (( PAGES >= 60 && PAGES <= 220 )); then
  pass "page count sane ($PAGES pages)"
else
  fail "page count $PAGES outside expected 60-220 band — structure may have broken"
fi

# --- Required content -----------------------------------------------------

check_contains() {
  local needle="$1" label="$2"
  if grep -qF -- "$needle" "$TXT"; then
    pass "$label"
  else
    fail "$label — not found in extracted text"
  fi
}

check_contains "Counterfactual Generative Morphogenesis" "cover: subtitle present"
check_contains "Apache-2.0"                              "cover: licence present"
check_contains "Contents"                                "table of contents generated"
check_contains "Namespec"                                "cover: document-control block present"

# Invariants: first and last must both be present, and the count must be right.
check_contains "INV-01" "invariants: INV-01 rendered"
check_contains "INV-45" "invariants: INV-45 rendered"

INV_COUNT="$(grep -oE 'INV-[0-9]{2}' "$TXT" | sort -u | wc -l)"
if (( INV_COUNT == 45 )); then
  pass "invariants: all 45 chips present and distinct"
else
  fail "invariants: found $INV_COUNT distinct INV-nn labels, expected 45"
fi

# Math: the admission-utility equation's operands should survive as glyphs.
if grep -qE 'admit' "$TXT" && grep -qE 'no-op|no−op' "$TXT"; then
  pass "math: admission-utility equation operands present"
else
  fail "math: could not find admission-utility equation text"
fi

# --- Leaked source syntax -------------------------------------------------

check_absent() {
  local pattern="$1" label="$2"
  local hits
  hits="$(grep -cE -- "$pattern" "$TXT" || true)"
  if [[ "$hits" == "0" ]]; then
    pass "$label"
  else
    fail "$label — $hits occurrence(s) leaked into the PDF"
    grep -nE -m3 -- "$pattern" "$TXT" | sed 's/^/         /' >&2 || true
  fi
}

check_absent '<!--'                    "no raw HTML comments"

# 01-claim.md's `**Key:** value` front-matter block is cover material. It is
# stripped by a narrowly-scoped rule in preprocess.py, and that scoping has
# regressed once during development — so assert the block did not leak back into
# the body rather than trusting the strip.
check_absent 'Supersedes:.*Version 3\.0'   "front matter not duplicated into body"
check_absent 'Working package root:'       "front matter: package-root line stripped"
check_absent '^:::|[^:]::: '           "no stray fenced-div markers"
check_absent '\]\([^)]*\.md'           "no unconverted markdown links"
check_absent '\\\(|\\\)'               "no literal \\( \\) math delimiters"
check_absent '\$\$'                    "no literal \$\$ math fences"
check_absent '```'                     "no literal code fences"

# Predecessor naming. Reported, never failed: this pipeline does not author the
# chapters, and the occurrences it finds are all pre-existing prose in
# docs/design/. The count is surfaced so a reviewer can confirm each mention is
# the intended lineage framing, and so a NEW mention introduced by a chapter edit
# shows up here rather than passing unnoticed.
ESPER_TOTAL="$(grep -oiE 'esper' "$TXT" | wc -l)"
if (( ESPER_TOTAL == 0 )); then
  pass "predecessor naming: no mentions"
else
  warn "predecessor naming: $ESPER_TOTAL mention(s) — confirm each is the intended lineage framing"
  grep -niE -m6 -o '.\{0,60\}esper.\{0,40\}' "$TXT" | sed 's/^/         /' >&2 || true
fi

# --- Visual samples -------------------------------------------------------
#
# Rendered so wide tables and code blocks are inspected, not assumed. Page
# numbers are resolved by content so they survive pagination changes.

SAMPLE_DIR="$WORK/pages"
mkdir -p "$SAMPLE_DIR"
rm -f "$SAMPLE_DIR"/*.png 2>/dev/null || true

# Split on form feeds rather than counting them with awk: pdftotext puts the
# form feed on the same line as the first text of the next page, so a
# line-oriented counter attributes that page's content to the previous page.
find_page() {
  python3 - "$TXT" "$1" <<'PY'
import sys
pages = open(sys.argv[1], encoding="utf-8", errors="replace").read().split("\f")
for i, page in enumerate(pages, start=1):
    if sys.argv[2] in page:
        print(i)
        break
PY
}

# Cover, ToC, and the pages carrying the constructs most likely to break.
SAMPLES=(1 2 3)
for needle in "Failure mode protected against" "INV-01" "Newsroom shorthand" "src/simic/" "Architecture diagram"; do
  p="$(find_page "$needle" || true)"
  [[ -n "$p" ]] && SAMPLES+=("$p")
done

RENDERED=0
for p in $(printf '%s\n' "${SAMPLES[@]}" | sort -un); do
  (( p >= 1 && p <= PAGES )) || continue
  pdftoppm -f "$p" -l "$p" -r 100 -png "$PDF" "$SAMPLE_DIR/page" 2>/dev/null || continue
  RENDERED=$((RENDERED + 1))
done
pass "rendered $RENDERED sample page(s) to ${SAMPLE_DIR#"$REPO_ROOT"/}/ for visual inspection"

# --- Overfull-line detection ---------------------------------------------
#
# Typst emits no TeX-style overfull warnings, so approximate it: pdftotext
# -layout pads with spaces to preserve horizontal position, so a line materially
# wider than the text measure means content sits past the margin — normally an
# unbreakable construct (a raw block or a display equation, neither of which
# Typst wraps).
#
# Two classes of false positive must be excluded or the signal is worthless:
# table-of-contents dot leaders, and footer lines padded out around a centred
# page number.

LONG_LINES="$(grep -vE '\. \. \.' "$TXT" | grep -vE '^(High-Level Design|Simic HLD)' | awk 'length($0) > 200')"
LONG="$(printf '%s' "$LONG_LINES" | grep -c . || true)"
if (( LONG == 0 )); then
  pass "no over-wide lines (no unwrapped content past the margin)"
else
  fail "$LONG line(s) exceed the text measure — unwrapped content is running off the page"
  printf '%s\n' "$LONG_LINES" | head -3 | cut -c1-140 | sed 's/^/         /' >&2
fi

echo
if (( FAIL )); then
  echo "verification FAILED" >&2
  exit 1
fi
echo "verification passed"
