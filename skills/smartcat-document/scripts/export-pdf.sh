#!/usr/bin/env bash
# export-pdf.sh — render a finished document HTML file to a PDF that matches
# its own fixed page geometry exactly.
#
#   scripts/export-pdf.sh <url> <output.pdf>
#
# <url> is the LIVE preview URL (e.g. http://localhost:8912/output/documents/
# <name>/<name>.html) — not a bare file path. Chrome's headless print renders
# whatever the URL serves, and the preview server is already how this skill's
# own verify step (Step 7) looks at the page, so this reuses that same server.
#
# Why this works with no extra flags: base/document-layout.css already
# declares `@media print { @page { size: 1290px 1670px; margin: 0 } }` and
# `break-after: page` on every `.doc-page`. Headless Chrome's print-to-pdf
# respects a page's own `@page` size by default, so each `.doc-page` becomes
# exactly one physical PDF page at the exact design size — verified empirically
# (9 .doc-page elements in a row -> a 9-page PDF, each 1290x1670px converted to
# points). No CDP scripting, no extra packages needed.
#
# The one-pager skill needs a DIFFERENT script, not this one — see
# skills/smartcat-onepager/scripts/export-pdf.sh and its header comment for why.

set -euo pipefail

url="${1:?usage: export-pdf.sh <url> <output.pdf>}"
out="${2:?usage: export-pdf.sh <url> <output.pdf>}"

CHROME="${SMARTCAT_CHROME:-}"
if [ -z "$CHROME" ]; then
  for candidate in \
    "/c/Program Files/Google/Chrome/Application/chrome.exe" \
    "/c/Program Files (x86)/Google/Chrome/Application/chrome.exe" \
    "$(command -v google-chrome 2>/dev/null || true)" \
    "$(command -v chromium 2>/dev/null || true)"
  do
    if [ -n "$candidate" ] && command -v "$candidate" >/dev/null 2>&1; then
      CHROME="$candidate"
      break
    fi
  done
fi
if [ -z "$CHROME" ]; then
  echo "ERROR: no Chrome/Chromium found. Set SMARTCAT_CHROME to its path." >&2
  exit 1
fi

# A dedicated, throwaway profile dir — never reuse the user's real Chrome
# profile (it may be running, and headless will refuse to share a live
# profile). Cleaned up on exit regardless of success or failure.
profile_dir="$(mktemp -d)"
trap 'rm -rf "$profile_dir"' EXIT

mkdir -p "$(dirname "$out")"

"$CHROME" \
  --headless=new \
  --disable-gpu \
  --no-pdf-header-footer \
  --print-to-pdf="$out" \
  --user-data-dir="$profile_dir" \
  "$url" >/dev/null 2>&1

if [ ! -s "$out" ]; then
  echo "ERROR: PDF was not created (or is empty): $out" >&2
  exit 1
fi

echo "wrote $out ($(wc -c < "$out") bytes)"
