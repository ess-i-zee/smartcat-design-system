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

Run `scripts/sync.sh` from **this skill's own directory** — which is
`.claude/skills/smartcat-design-system/` when the skill is installed in the
design-system project, and wherever the skill was installed otherwise:

```bash
eval "$(bash .claude/skills/smartcat-design-system/scripts/sync.sh)"
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

## Step 3 — read the rules for the ONE format in play

`INDEX.md` has the table. In short:

| Building | Read |
|---|---|
| Web page | `CLAUDE.md` up to "Component file structure" |
| Deck | `CLAUDE.md` → "Presentation decks" + `docs/deck-design-brain.md` |
| One-pager | `CLAUDE.md` → "One-pagers" + `docs/onepagers-design-brain.md` |
| Document | `CLAUDE.md` → "Documents" + `docs/document-design-brain.md` |
| Social | `CLAUDE.md` → "Social assets" + `base/social-layout.css` |

`CLAUDE.md` is ~19k tokens covering all five. Read the section, not the file —
`sed -n '/^## One-pagers/,/^## Documents/p'` beats `cat`. The shared rules (icons,
logo, casing, punctuation, tokens-only CSS) sit *above* "Presentation decks" and
apply to every format.

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
python .claude/skills/smartcat-design-system/scripts/build-index.py
```
