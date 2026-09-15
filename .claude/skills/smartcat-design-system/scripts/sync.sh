#!/usr/bin/env bash
# sync.sh — put a current copy of the Smartcat design system on disk and print
# where it is. Safe to run every time; it is a no-op when already up to date.
#
#   eval "$(scripts/sync.sh)"    # exports DS_ROOT
#   scripts/sync.sh              # or just read the DS_ROOT= line
#
# Resolution order:
#   1. $SMARTCAT_DS_ROOT, if set and valid  — an explicit override
#   2. the repo we are standing in, if it IS the design system
#   3. a sparse clone cached under ~/.cache/smartcat-design-system
#
# Exits non-zero only when there is no usable copy at all. A network failure
# with a warm cache is a warning, not an error: stale beats nothing.

set -uo pipefail

REPO_URL="https://github.com/ess-i-zee/smartcat-design-system.git"
REPO_SLUG="ess-i-zee/smartcat-design-system"
SPARSE_DIRS="tokens base docs components"
CACHE_DEFAULT="${XDG_CACHE_HOME:-$HOME/.cache}/smartcat-design-system"
CACHE="${SMARTCAT_DS_CACHE:-$CACHE_DEFAULT}"

# Bail out of a stalled fetch instead of hanging the caller.
export GIT_HTTP_LOW_SPEED_LIMIT=1000
export GIT_HTTP_LOW_SPEED_TIME=20
export GIT_TERMINAL_PROMPT=0

note() { printf '# %s\n' "$*" >&2; }

emit() {
  # $1 = path, $2 = how we got it
  local root="$1" how="$2" head date
  head=$(git -C "$root" rev-parse --short HEAD 2>/dev/null || echo unknown)
  date=$(git -C "$root" log -1 --format=%cs 2>/dev/null || echo unknown)
  # Quoted so `eval "$(sync.sh)"` survives a path with spaces — the real repo
  # lives under ".../01 Brand/...". The three message values are ours and never
  # contain a single quote, so plain single-quoting keeps them readable.
  printf 'DS_ROOT=%q\n' "$root"
  printf "DS_SOURCE='%s'\n" "$how"
  printf "DS_COMMIT='%s'\n" "$head"
  printf "DS_DATE='%s'\n" "$date"
  exit 0
}

is_design_system() {
  # A directory is the design system if it has the landmark files.
  [ -f "$1/CLAUDE.md" ] && [ -d "$1/tokens" ] && [ -d "$1/components" ]
}

# ── 1. explicit override ──────────────────────────────────────────────────
if [ -n "${SMARTCAT_DS_ROOT:-}" ]; then
  if is_design_system "$SMARTCAT_DS_ROOT"; then
    emit "$SMARTCAT_DS_ROOT" "override (\$SMARTCAT_DS_ROOT)"
  fi
  note "SMARTCAT_DS_ROOT=$SMARTCAT_DS_ROOT is not a design-system checkout; ignoring."
fi

# ── 2. are we standing in the design system already? ──────────────────────
# Working in the repo itself: use it, don't clone a second copy. It may carry
# uncommitted edits — that is usually exactly what you want here.
if top=$(git rev-parse --show-toplevel 2>/dev/null); then
  if is_design_system "$top" && git -C "$top" remote -v 2>/dev/null | grep -q "$REPO_SLUG"; then
    dirty=""
    [ -n "$(git -C "$top" status --porcelain 2>/dev/null)" ] && dirty=", uncommitted changes present"
    emit "$top" "local working repo$dirty"
  fi
fi

# ── 3. the cache ──────────────────────────────────────────────────────────
if [ -d "$CACHE/.git" ]; then
  if git -C "$CACHE" fetch --depth=1 -q origin main 2>/dev/null &&
     git -C "$CACHE" reset --hard -q FETCH_HEAD 2>/dev/null; then
    emit "$CACHE" "cache (pulled)"
  fi
  if is_design_system "$CACHE"; then
    note "Could not reach GitHub — using the cached copy, which may be stale."
    emit "$CACHE" "cache (STALE — fetch failed)"
  fi
  note "Cache at $CACHE is unusable; re-cloning."
  rm -rf "$CACHE"
fi

mkdir -p "$(dirname "$CACHE")"
if git clone --filter=blob:none --sparse --depth=1 -q "$REPO_URL" "$CACHE" 2>/dev/null &&
   git -C "$CACHE" sparse-checkout set $SPARSE_DIRS 2>/dev/null; then
  emit "$CACHE" "cache (fresh clone)"
fi

rm -rf "$CACHE"
note "FAILED: no local copy and GitHub is unreachable."
note "Fall back to the raw-URL method in reference/no-shell.md, or ask the user"
note "to point \$SMARTCAT_DS_ROOT at a local checkout."
exit 1
