#!/usr/bin/env bash
# NOTE: verbatim copy of skills/smartcat-design-system/scripts/sync.sh, bundled so the
# packaged smartcat-onepager skill works alone in a workspace without the loader skill.
# Re-copy when the loader's script changes; do not edit this copy directly.
# sync.sh — put a current copy of the Smartcat design system on disk and print
# where it is. Safe to run every time; it is a no-op when already up to date.
#
#   eval "$(scripts/sync.sh)"                        # exports DS_ROOT
#   scripts/sync.sh                                  # or just read the DS_ROOT= line
#   eval "$(scripts/sync.sh --references decks/light)"   # also pull one reference folder
#
# Resolution order for DS_ROOT:
#   1. $SMARTCAT_DS_ROOT, if set and valid  — an explicit override
#   2. the repo we are standing in, if it IS the design system
#   3. a sparse clone cached under ~/.cache/smartcat-design-system
#
# Exits non-zero only when there is no usable copy at all. A network failure
# with a warm cache is a warning, not an error: stale beats nothing.
#
# --references <path-under-references/> additionally makes sure that one
# folder or file under references/ is on disk, fetching it on demand rather
# than as part of every sync — see "Reference examples" in SKILL.md for why.
# (mockups/ lives at skills/smartcat-mockup/mockups/ and is not handled by
# this script at all — smartcat-mockup fetches it directly; see that skill's
# SKILL.md.)

set -uo pipefail

REPO_URL="https://github.com/ess-i-zee/smartcat-design-system.git"
REPO_SLUG="ess-i-zee/smartcat-design-system"
# images/ is the logo SVGs plus images/promo-ui-mockups/ (~6.3MB of real,
# ready-to-embed product screenshots — see CLAUDE.md "Promo UI mockups") —
# still cheap enough to always have on hand. references/ is NOT here: it's
# ~55MB of example screenshots and PDFs, fetched on demand instead via
# --references (see below). skills/smartcat-mockup/mockups/ (~68MB) is NOT
# here either and has no on-demand flag in this script at all — smartcat-mockup
# fetches it independently via raw.githubusercontent.com URLs built from its
# own listing, so it never needs a local checkout.
SPARSE_DIRS="tokens base docs components images"
CACHE_DEFAULT="${XDG_CACHE_HOME:-$HOME/.cache}/smartcat-design-system"
CACHE="${SMARTCAT_DS_CACHE:-$CACHE_DEFAULT}"

# Bail out of a stalled fetch instead of hanging the caller.
export GIT_HTTP_LOW_SPEED_LIMIT=1000
export GIT_HTTP_LOW_SPEED_TIME=20
export GIT_TERMINAL_PROMPT=0

note() { printf '# %s\n' "$*" >&2; }

is_design_system() {
  # A directory is the design system if it has the landmark files.
  [ -f "$1/CLAUDE.md" ] && [ -d "$1/tokens" ] && [ -d "$1/components" ]
}

# ── parse args ──────────────────────────────────────────────────────────────
REF_PATH=""
if [ "${1:-}" = "--references" ]; then
  REF_PATH="${2:-}"
  if [ -z "$REF_PATH" ]; then
    note "Usage: sync.sh --references <path-under-references/>, e.g. decks/light"
    exit 2
  fi
fi

ROOT=""
HOW=""

# ── 1. explicit override ──────────────────────────────────────────────────
if [ -n "${SMARTCAT_DS_ROOT:-}" ]; then
  if is_design_system "$SMARTCAT_DS_ROOT"; then
    ROOT="$SMARTCAT_DS_ROOT"
    HOW="override (\$SMARTCAT_DS_ROOT)"
  else
    note "SMARTCAT_DS_ROOT=$SMARTCAT_DS_ROOT is not a design-system checkout; ignoring."
  fi
fi

# ── 2. are we standing in the design system already? ──────────────────────
# Working in the repo itself: use it, don't clone a second copy. It may carry
# uncommitted edits — that is usually exactly what you want here. A full
# working repo like this has no sparse-checkout, so references/ is already
# on disk and --references is always a no-op against it.
if [ -z "$ROOT" ] && top=$(git rev-parse --show-toplevel 2>/dev/null); then
  if is_design_system "$top" && git -C "$top" remote -v 2>/dev/null | grep -q "$REPO_SLUG"; then
    dirty=""
    [ -n "$(git -C "$top" status --porcelain 2>/dev/null)" ] && dirty=", uncommitted changes present"
    ROOT="$top"
    HOW="local working repo$dirty"
  fi
fi

# ── 3. the cache ──────────────────────────────────────────────────────────
if [ -z "$ROOT" ] && [ -d "$CACHE/.git" ]; then
  if git -C "$CACHE" fetch --depth=1 -q origin main 2>/dev/null &&
     git -C "$CACHE" reset --hard -q FETCH_HEAD 2>/dev/null; then
    ROOT="$CACHE"
    HOW="cache (pulled)"
  elif is_design_system "$CACHE"; then
    note "Could not reach GitHub — using the cached copy, which may be stale."
    ROOT="$CACHE"
    HOW="cache (STALE — fetch failed)"
  else
    note "Cache at $CACHE is unusable; re-cloning."
    rm -rf "$CACHE"
  fi
fi

# ── 3b. fresh clone ─────────────────────────────────────────────────────────
if [ -z "$ROOT" ]; then
  mkdir -p "$(dirname "$CACHE")"
  if git clone --filter=blob:none --sparse --depth=1 -q "$REPO_URL" "$CACHE" 2>/dev/null &&
     git -C "$CACHE" sparse-checkout set $SPARSE_DIRS 2>/dev/null; then
    ROOT="$CACHE"
    HOW="cache (fresh clone)"
  else
    rm -rf "$CACHE"
  fi
fi

if [ -z "$ROOT" ]; then
  note "FAILED: no local copy and GitHub is unreachable."
  note "Fall back to the raw-URL method in reference/no-shell.md, or ask the user"
  note "to point \$SMARTCAT_DS_ROOT at a local checkout."
  exit 1
fi

# ── optional: pull one reference example on demand ─────────────────────────
# references/ is ~55MB total (deck screenshots, one-pager and document PDFs) —
# far too much to add to SPARSE_DIRS above, so it is fetched one folder (or
# file) at a time, only when a build actually wants to look at a finished
# example. A blobless sparse clone makes this cheap: `sparse-checkout add`
# fetches just the blobs under the new path, not the rest of the tree.
REF_STATUS=""
if [ -n "$REF_PATH" ]; then
  rel="references/$REF_PATH"
  if [ -e "$ROOT/$rel" ]; then
    REF_STATUS="already present"
  elif git -C "$ROOT" sparse-checkout list >/dev/null 2>&1; then
    if git -C "$ROOT" sparse-checkout add "$rel" 2>/dev/null && [ -e "$ROOT/$rel" ]; then
      REF_STATUS="pulled"
    else
      note "Could not find '$rel' — check the path against INDEX.md's reference-examples table."
      REF_STATUS="not found"
    fi
  else
    note "'$rel' is not in this checkout and it isn't sparse — the path likely doesn't exist."
    REF_STATUS="not found"
  fi
fi

# ── emit ─────────────────────────────────────────────────────────────────
head=$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)
date=$(git -C "$ROOT" log -1 --format=%cs 2>/dev/null || echo unknown)
# Quoted so `eval "$(sync.sh)"` survives a path with spaces — the real repo
# lives under ".../01 Brand/...". The three message values are ours and never
# contain a single quote, so plain single-quoting keeps them readable.
printf 'DS_ROOT=%q\n' "$ROOT"
printf "DS_SOURCE='%s'\n" "$HOW"
printf "DS_COMMIT='%s'\n" "$head"
printf "DS_DATE='%s'\n" "$date"
if [ -n "$REF_PATH" ]; then
  printf 'DS_REFERENCE=%q\n' "$ROOT/$rel"
  printf "DS_REFERENCE_STATUS='%s'\n" "$REF_STATUS"
fi
exit 0
