---
name: smartcat-design-system
description: >-
  Load the current Smartcat design system — tokens, layout rules and component
  specs — live from the GitHub repo, so a build uses today's rules instead of a
  stale embedded copy. Use this FIRST, before building anything Smartcat-branded:
  a web page, presentation deck, one-pager, document, or social asset. Also use it
  to look up a token value, check a component's properties, or settle what a design
  rule says. Other Smartcat skills (deck-builder, onepager, document, social)
  delegate here rather than carrying their own copy of the rules.
---

# Smartcat design system — loader

This skill does one job: **put the current design system in front of you, cheaply.**
It does not build anything. The format skills build; this one supplies the rules
they build from.

The design system lives at `github.com/ess-i-zee/smartcat-design-system`. It is the
single source of truth. A rule change there reaches every skill on its next run,
with nothing to re-upload.

## Step 1 — sync

Run `scripts/sync.sh` from **this skill's own directory**. Where that is depends
on how the skill was installed: `skills/smartcat-design-system/` inside the
design-system repo itself, `~/.claude/skills/smartcat-design-system/` when
installed for every local project, or the skill's own directory on claude.ai.

```bash
eval "$(bash skills/smartcat-design-system/scripts/sync.sh)"
```

Run it from any working directory. It prints four shell-quoted lines, so `eval`
is safe even though the usual checkout path contains a space:

```
DS_ROOT=C:/Users/isizo/Dropbox/Marketing/01\ Brand/00-claude-design-system
DS_SOURCE='local working repo, uncommitted changes present'
DS_COMMIT='19ebbe9'
DS_DATE='2026-09-15'
```

`DS_ROOT` is what every path below is relative to. The script resolves, in order:
an explicit `$SMARTCAT_DS_ROOT`, the repo you are standing in if it *is* the design
system, then a sparse clone cached under `~/.cache/smartcat-design-system`
(~3 MB, ~3s first time, ~0.8s after).

It is a no-op when already current, so run it every time rather than assuming a
warm cache.

**If it reports `STALE — fetch failed`:** GitHub was unreachable and you are on a
cached copy. Keep working, but say so when you report back.
**If it exits non-zero:** there is no local copy at all — use
`reference/no-shell.md`.

## Step 2 — read the index, not the system

```bash
cat "$DS_ROOT/INDEX.md"
```

~5k tokens. It lists every component with its root class, its `data-` properties
and a one-line purpose, plus which rules each output format needs. It exists so
you can pick the right files without opening sixty of them.

**The full corpus is ~116k tokens. Never read it whole.** Not `components/`, not
all of `tokens/`, not all of `CLAUDE.md`.

## Step 3 — read the shared rules, THEN the ONE format in play

**Two reads, every time — not one.** `CLAUDE.md` has a shared prelude ("Icons"
through "CSS conventions": icon usage, the logo, page-assembly principles, text
casing, punctuation, section-background rules, CSS conventions) that every format
section explicitly depends on — each format section opens by saying "anything not
overridden here follows the general rules above." Reading only your format's
section skips the sentence that bans eyebrow text, the dash and quote rules, and
the ban on decorative gradient blobs — all real rules that a build has shipped
without, because this step was skipped. Read both, always:

```bash
# 1. Shared rules — read this one EVERY time, regardless of format
sed -n '/^## Icons/,/^## Component file structure/p' "$DS_ROOT/CLAUDE.md" | sed '$d'

# 2. Then your format's own section
sed -n '/^## One-pagers/,/^## Documents/p' "$DS_ROOT/CLAUDE.md"
```

The shared read is ~6k tokens — cheap next to what it prevents. The `sed '$d'`
drops the trailing "## Component file structure" heading the range picks up
(that section is about documenting a *new* component, not building *from*
existing ones — skip it when composing).

`INDEX.md` has the per-format table for step 2's range:

| Building | Format-specific read |
|---|---|
| Web page | `CLAUDE.md` → "Output formats" through "Component file structure" (i.e. the shared read above already covers most of it — a web build additionally wants "Component tiers" and "Page assembly rules", both *before* "Icons") |
| Deck | `CLAUDE.md` → "Presentation decks" + `docs/deck-design-brain.md` |
| One-pager | `CLAUDE.md` → "One-pagers" + `docs/onepagers-design-brain.md` |
| Document | `CLAUDE.md` → "Documents" + `docs/document-design-brain.md` |
| Social | `CLAUDE.md` → "Social assets" + `base/social-layout.css` |

`CLAUDE.md` is ~19k tokens covering all five formats — the two targeted reads
above stay well under half that, which is the point of reading sections instead
of `cat`-ing the file.

## Step 4 — read only the components you will actually use

Pick them from `INDEX.md`, then read those files and no others:

```bash
cat "$DS_ROOT/components/onepager/flow/flow.css"     # the spec + styles
cat "$DS_ROOT/components/onepager/flow/flow.html"    # full anatomy, annotated
```

The `.html` is a reference template, not an include — copy the parts you need and
drop the rest. Three to five components is a normal build. If you find yourself
reading a tenth, stop and re-read `INDEX.md`; you are probably reaching for the
wrong tier.

Token values: `tokens/colors.css`, `sizes.css`, `typography.css`, `globals.css`,
`effects.css`. Grep for the one you want rather than reading the file:

```bash
grep -n "background-static-brand" "$DS_ROOT/tokens/colors.css"
```

## Rules that hold no matter what you are building

- **Tokens only.** Never a raw hex, px, or font value in component CSS. Semantic
  tokens (`--background-button-primary-default`) over primitives.
- **Never invent a component.** If nothing in `INDEX.md` fits, say so and ask —
  do not improvise a new one silently.
- **Icons come from `components/atomic/icon/svg/` only** — 181 of them. No inline
  shapes, no external icon libraries. If none fits, flag it.
- **The logo is an asset**, `images/smartcat-logo-{black,white}.svg` — never
  "Smartcat" set as text, never decorated.
- **Respect the reuse boundaries.** One-pagers and documents compose only from
  their own tier. Decks and social assets compose freely from atomics. Web
  page-level components are web-only.
- **Punctuation is a correctness rule**, not a preference: curly quotes and
  apostrophes, spaced em dashes, en dashes for ranges. See `CLAUDE.md` →
  "Punctuation, quotes & dashes".
- **No eyebrow text, anywhere.** Small, bold, wide-tracked, all-caps labels
  placed above or beside a heading are banned system-wide. Use a regular
  paragraph or subtitle instead.
- **No gradient blobs, orbs, or glows, anywhere.** A blurred soft-edged circular
  gradient shape — especially bleeding off a corner — is a generic AI-marketing
  cliché, not a Smartcat pattern. Every sanctioned gradient is a flat wash with a
  sharp edge. See `CLAUDE.md` → "Section backgrounds beyond the gray layers".

## When there is no shell

Read `reference/no-shell.md` — the same system over `raw.githubusercontent.com`,
one file per fetch.

## Report back

When you hand off, say which commit you built against and what you loaded:

> Design system `19ebbe9` (2026-09-15) · one-pager rules + flow, numbered-cards,
> cta-band.

If the sync was stale or fell back to raw URLs, say that too — it is the
difference between "these are the rules" and "these were the rules last time I
could reach GitHub".

## Maintaining the index

`INDEX.md` is generated from the spec comment at the top of each component CSS
file. After adding or changing a component, regenerate and commit it:

```bash
python skills/smartcat-design-system/scripts/build-index.py
```
