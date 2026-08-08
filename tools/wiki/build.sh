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
