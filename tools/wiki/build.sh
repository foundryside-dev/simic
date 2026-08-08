#!/usr/bin/env bash
# Build the generated design-docs wiki from docs/design/.
#
#   ./build.sh          stage + build   -> build/site/   (what CI publishes at /design/)
#   ./build.sh serve    stage + live preview on :8000
#
# The wiki is GENERATED. docs/design/ is the single source of truth and is never
# edited to suit the renderer — stage.py works on a throwaway copy under build/.
# Nothing in build/ is committed (.gitignore already ignores build/).
set -euo pipefail

cd "$(dirname "$0")"

MKDOCS="${MKDOCS:-mkdocs}"
if ! command -v "$MKDOCS" >/dev/null 2>&1; then
  if [ -x "$HOME/.local/bin/mkdocs" ]; then
    MKDOCS="$HOME/.local/bin/mkdocs"
  else
    echo "build.sh: mkdocs not found. Install with:" >&2
    echo "  pip install -r $(pwd)/requirements.txt" >&2
    exit 1
  fi
fi

# CI installs requirements.txt exactly; a local build resolves whatever mkdocs
# is on PATH. Without this check the two could silently diverge and produce
# different sites from the same commit while --strict still passed.
check_pin() {
  local dist="$1" want actual
  want="$(sed -n "s/^${dist}==//p" requirements.txt)"
  [ -n "$want" ] || return 0
  actual="$("$PYTHON" - "$dist" <<'PY' 2>/dev/null || true
import importlib.metadata, sys
try:
    print(importlib.metadata.version(sys.argv[1]))
except importlib.metadata.PackageNotFoundError:
    pass
PY
)"
  if [ -z "$actual" ]; then
    echo "build.sh: $dist is not installed — pip install -r requirements.txt" >&2
    exit 1
  fi
  if [ "$actual" != "$want" ]; then
    echo "build.sh: $dist $actual is installed but requirements.txt pins $want." >&2
    echo "  CI builds against the pin, so this build would not match the deploy." >&2
    echo "  Fix with: pip install -r $(pwd)/requirements.txt" >&2
    echo "  Override deliberately with: WIKI_ALLOW_VERSION_DRIFT=1 ./build.sh" >&2
    [ "${WIKI_ALLOW_VERSION_DRIFT:-}" = "1" ] || exit 1
  fi
}

PYTHON="${PYTHON:-python3}"
check_pin mkdocs
check_pin mkdocs-material
check_pin pymdown-extensions

# --- Compile docs/design/assets/model.dsl to SVGs -------------------------
# Structurizr CLI exports the views to PlantUML; PlantUML renders SVG with its
# pure-Java layout engine (no graphviz dependency). Both jars are PINNED and
# cached in .cache/ (gitignored) — first run downloads them, later runs are
# offline. The staged wiki fails without these SVGs: no silent fallback.
STRUCTURIZR_VERSION="2025.11.09"
PLANTUML_VERSION="1.2026.6"
CACHE=".cache"
SCLI_DIR="$CACHE/structurizr-cli-$STRUCTURIZR_VERSION"
PLANTUML_JAR="$CACHE/plantuml-$PLANTUML_VERSION.jar"

if ! command -v java >/dev/null 2>&1; then
  echo "build.sh: java not found — needed to compile model.dsl diagrams" >&2
  exit 1
fi

mkdir -p "$CACHE"
if [ ! -d "$SCLI_DIR" ]; then
  echo "fetching structurizr-cli v$STRUCTURIZR_VERSION ..."
  curl -fsSL -o "$CACHE/structurizr-cli.zip" \
    "https://github.com/structurizr/cli/releases/download/v$STRUCTURIZR_VERSION/structurizr-cli.zip"
  unzip -q -o "$CACHE/structurizr-cli.zip" -d "$SCLI_DIR"
  rm "$CACHE/structurizr-cli.zip"
fi
SCLI_SH="$SCLI_DIR/structurizr.sh"
if [ ! -f "$SCLI_SH" ]; then
  echo "build.sh: no structurizr.sh launcher under $SCLI_DIR" >&2
  exit 1
fi
if [ ! -f "$PLANTUML_JAR" ]; then
  echo "fetching plantuml v$PLANTUML_VERSION ..."
  curl -fsSL -o "$PLANTUML_JAR" \
    "https://github.com/plantuml/plantuml/releases/download/v$PLANTUML_VERSION/plantuml-$PLANTUML_VERSION.jar"
fi

rm -rf build/diagrams
mkdir -p build/diagrams
bash "$SCLI_SH" export \
  -workspace ../../docs/design/assets/model.dsl \
  -format plantuml -output build/diagrams
# -Playout=smetana: PlantUML's bundled layout engine, so the render is
# reproducible and dependency-free wherever the wiki builds.
java -Djava.awt.headless=true -jar "$PLANTUML_JAR" \
  -tsvg -Playout=smetana build/diagrams/*.puml
echo "diagrams -> build/diagrams ($(find build/diagrams -name '*.svg' | wc -l) SVGs)"

python3 stage.py

case "${1:-build}" in
  build)
    # --strict is also set in mkdocs.yml; passing it here too means an edited
    # config can't silently downgrade a broken link to a warning.
    "$MKDOCS" build --strict
    echo
    echo "wiki -> $(pwd)/build/site  ($(find build/site -name '*.html' | wc -l) pages)"
    ;;
  serve)
    exec "$MKDOCS" serve
    ;;
  *)
    echo "usage: $0 [build|serve]" >&2
    exit 2
    ;;
esac
