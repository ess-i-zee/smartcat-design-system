---
name: smartcat-onepager
description: >-
  Build a Smartcat-branded one-pager — a fixed 1280px-wide, variable-height
  document for reading or printing. Use whenever someone wants a one-pager,
  solution brief, product or sales factsheet, battlecard, cheat sheet, leave-
  behind, or "a single page about X" for a customer or an internal team. Also use
  it for the brief/cheat-sheet pairs that accompany a launch. Not for slide decks,
  paginated multi-page guides or social graphics; those have their own skills.
---

# Smartcat one-pager

A one-pager is a **fixed 1280px-wide canvas with variable height** (`.op-page`),
minimum 1656px — the US-Letter proportion at this width. Taller is normal. It is
read as a document, not presented.

## Step 1 — load the design system

Use the **smartcat-design-system** skill first. Then read, and nothing else:

- `INDEX.md` — the component manifest
- `CLAUDE.md` → the "One-pagers" section
- `docs/onepagers-design-brain.md` — the section catalog and archetypes

```bash
sed -n '/^## One-pagers/,/^## Documents/p' "$DS_ROOT/CLAUDE.md"
```

## Step 2 — pick the archetype, then plan the bands

Section D of the brain doc lists the document archetypes (solution brief, sales
cheat sheet, internal reference sheet…). Pick one — it decides the section
sequence, the density and whether the whole document runs compact.

Then plan the band stack top to bottom: one line per band, naming its component,
its `data-layer` and whether it is dark. Section C is the recipe catalog; section
E is the decision procedure.

## Step 3 — the reuse boundary (the rule most often broken)

**Compose exclusively from `components/onepager/*`.** Never reuse or reshape a
web page-level component — not `hero-block`, not `cards`, not `numbers`, not
`testimonial`, not even as a starting point. This is the opposite of the deck
rule.

Available alongside the tier: raw tokens and the type-style utilities
(`.text-h1` etc. from `base/type-styles.css`). If a layout genuinely needs
something the tier lacks, design a new component **in the same tier** and say so
— do not import one from elsewhere.

## Step 4 — bands, backgrounds and the card-fill trap

Every section is an `.op-band` — it supplies the background (`data-layer` ×
`data-theme`) and the fixed 48px side padding. It is the only place side padding
is applied.

Three components are self-sufficient and carry their own background directly —
**never wrap these in `.op-band`**: `.op-hero` (opens every one-pager),
`.op-cta-band` (closes most), `.op-footer` (always last).

**Match each card component's fill to its band, or the cards vanish:**

| Component | Card fill | Must sit on |
|---|---|---|
| `.op-benefit-cards` | layer-1 | a **layer-0** band |
| `.op-numbered-cards`, `.op-checklist[data-marker="number"]` | layer-0 + shadow | a **layer-1 or higher** band |
| `.op-flow` | layer-0 + shadow | any light band |
| `.op-signals` | pink tint | any band |

Because adjacent bands must also contrast with each other, a document alternating
benefit-cards and numbered-cards necessarily alternates layer-0 / layer-1 — which
is the rhythm to aim for anyway.

Two pairings that render black-on-purple or invisible text — never do either:
- `.op-flow` (or anything repointing `--content-static-*` to inverted) inside a
  `data-theme="dark"` band
- `data-layer="brand"` combined with `data-theme="dark"`

**Two columns of prose use `.op-columns`, not `.grid`.** The grid gutter is 8px —
meant to separate cards, not columns of body copy, which read as one ragged
column at that spacing. `.op-columns` gives a real 48px gap and takes
`data-split="even"` (default) or `"wide-narrow"` (a narrative paired with a
supporting `.op-callout`).

## Step 5 — real interactive UI is correct here

Unlike a deck, a one-pager is opened and read, so `.btn` and real links are
right. Every reference one-pager uses a real button for "Schedule a demo."

## Step 6 — write the file

`output/onepagers/<name>.html`. Follow the house boilerplate:
`<html lang="en" data-theme="light">`, `main.css` at the right relative depth,
the Inter + Plus Jakarta Sans font link, and a "Preview chrome only" `<style>`
block that centers the fixed-width canvas. Copy the head of an existing file in
`output/onepagers/` and adjust.

Comment each band so the file stays navigable.

Section headings inside a band are composed from type-style classes plus the
colour utility — `<h2 class="text-h1 op-heading">Title</h2>` — not a heading
component.

## Step 7 — verify

```
preview_start  { name: "static" }
navigate       http://localhost:8912/output/onepagers/<name>.html
```

Then in `javascript_tool`:

```js
const p = document.querySelector('.op-page');
({
  width: p.offsetWidth,                    // must be 1280
  height: p.offsetHeight,                  // must be >= 1656
  horizontalSpill: p.scrollWidth > p.offsetWidth,
  bands: [...document.querySelectorAll('.op-band')].map(b => b.dataset.layer ?? '0'),
  clipped: [...p.querySelectorAll('*')].filter(e =>
    e.scrollHeight > e.offsetHeight + 1 &&
    getComputedStyle(e).overflow !== 'visible').length
})
```

Width must be exactly 1280, height at least 1656, `horizontalSpill` false and
`clipped` zero. Read the `bands` array and confirm adjacent values differ — two
identical layers in a row means the section boundary is invisible.

**The browser pane crops a tall canvas**, so a single screenshot will not show
the whole document. Scroll and capture in sections, or render the full page with
headless Chrome and downscale.

## Step 8 — report

Give the design-system commit, the archetype used, and the band sequence with
layers. Flag any component you had to add to the tier.
