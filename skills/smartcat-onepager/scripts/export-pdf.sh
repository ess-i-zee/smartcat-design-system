#!/usr/bin/env bash
# export-pdf.sh — render a finished one-pager HTML file to a single-page PDF
# at its own natural size (1280px wide, whatever height it actually rendered
# to).
#
#   scripts/export-pdf.sh <url> <height-px> <output.pdf>
#
# <url> is the LIVE preview URL. <height-px> is the .op-page element's real
# rendered height in CSS pixels — get it from the browser BEFORE calling this
# script, there is no way to measure it from inside a shell script:
#
#   javascript_tool: document.querySelector('.op-page').getBoundingClientRect().height
#
# Why a one-pager needs a height argument and a document does not: main.css
# imports every base/*.css file into one global stylesheet, and CSS's `@page`
# at-rule cannot be scoped to a class selector — it always applies to the
# whole print context. base/document-layout.css's `@page { size: 1290px
# 1670px }` is correct FOR DOCUMENTS, but it leaks into anything else that
# also links main.css. A one-pager printed with no override silently comes
# out at the DOCUMENT's page size (1290x1670 per page, paginated), not its
# own — confirmed empirically, not a hypothetical.
#
# The fix: inject a page-specific override into a disposable COPY of the
# file, placed after main.css's <link> so it wins the cascade for the `size`
# property. Never edit the source .html to add this — it is exported per
# invocation and needs the CURRENT rendered height every time, which a
# one-pager's actual height changes as content changes. Confirmed
# empirically: this override produces exactly one page, at exactly the
# requested size, regardless of what main.css declares.

set -euo pipefail

url="${1:?usage: export-pdf.sh <url> <height-px> <output.pdf>}"
height="${2:?usage: export-pdf.sh <url> <height-px> <output.pdf>}"
out="${3:?usage: export-pdf.sh <url> <height-px> <output.pdf>}"

case "$height" in
  ''|*[!0-9]*) echo "ERROR: height-px must be a positive integer, got: $height" >&2; exit 1 ;;
esac

# Resolve the source HTML file from the URL's path so we can copy it. This
# script assumes a local static server (the same one Step 7's verify uses),
# rooted at the design-system repo, e.g.
#   http://localhost:8912/output/onepagers/reviewer-agents.html
url_path="${url#*://*/}"
src="$SMARTCAT_STATIC_ROOT/${url_path}"
if [ -z "${SMARTCAT_STATIC_ROOT:-}" ] || [ ! -f "$src" ]; then
  echo "ERROR: could not resolve '$url' to a file. Set SMARTCAT_STATIC_ROOT to" >&2
  echo "the directory the preview server is serving (the design-system repo root)." >&2
  exit 1
fi

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

profile_dir="$(mktemp -d)"

# The disposable copy lives alongside the source (not in a scratch dir), so
# its relative ../../main.css and image links keep resolving through the
# live preview server exactly as the original does.
tmp_name="_export-$(basename "$src" .html)-$$.html"
tmp_path="$(dirname "$src")/$tmp_name"
trap 'rm -rf "$profile_dir"; rm -f "$tmp_path"' EXIT

sed "s#</head>#<style>@media print { @page { size: 1280px ${height}px; margin: 0; } }</style>\n</head>#" \
  "$src" > "$tmp_path"

tmp_url="$(dirname "$url")/$tmp_name"

mkdir -p "$(dirname "$out")"

"$CHROME" \
  --headless=new \
  --disable-gpu \
  --no-pdf-header-footer \
  --print-to-pdf="$out" \
  --user-data-dir="$profile_dir" \
  "$tmp_url" >/dev/null 2>&1

if [ ! -s "$out" ]; then
  echo "ERROR: PDF was not created (or is empty): $out" >&2
  exit 1
fi

echo "wrote $out ($(wc -c < "$out") bytes) at 1280x${height}px"
