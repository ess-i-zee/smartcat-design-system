---
name: smartcat-onepager
description: >-
  Build a Smartcat-branded one-pager — a fixed 1280px-wide, variable-height
  document — and deliver it as a downloadable PDF on Google Drive. Use whenever
  someone wants a one-pager, solution brief, product or sales factsheet,
  battlecard, cheat sheet, leave-behind, or "a single page about X" for a
  customer or an internal team. Also use it for the brief/cheat-sheet pairs
  that accompany a launch. Not for slide decks, paginated multi-page guides or
  social graphics; those have their own skills.
---

# Smartcat one-pager

A one-pager is a **fixed 1280px-wide canvas with variable height** (`.op-page`),
minimum 1656px — the US-Letter proportion at this width. Taller is normal. It is
read as a document, not presented.

## Step 1 — load the design system

Use the **smartcat-design-system** skill first. Then read, in this order:

- `INDEX.md` — the component manifest
- **the shared rules** — icons, logo, page assembly, text casing, punctuation,
  section-background rules, CSS conventions. **Read this every time; it is not
  optional.** The eyebrow-text ban and the gradient-blob ban both live here, not
  in the "One-pagers" section below — skipping straight to the format section
  misses them.
- `CLAUDE.md` → the "One-pagers" section
- `docs/onepagers-design-brain.md` — the section catalog and archetypes

```bash
sed -n '/^## Icons/,/^## Component file structure/p' "$DS_ROOT/CLAUDE.md" | sed '$d'
sed -n '/^## One-pagers/,/^## Documents/p' "$DS_ROOT/CLAUDE.md"
```

Two of those shared rules are easy to reintroduce by accident when filling a
band with a category tag or a showcase panel:

- **No eyebrow text** — no small, bold, all-caps, wide-tracked label above or
  beside a heading (e.g. a "best for X" tag over `.op-hero__headline`). Use a
  regular line of body text instead.
- **No gradient blobs, orbs, or glows** — no soft blurred circle, especially
  bleeding off a corner. `.op-band[data-layer="brand-tint"]` and the sanctioned
  gradients are flat washes with a sharp edge, never a glow.

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

**That `clipped` check has a blind spot: it only catches overflow on an element
that also clips it (`overflow !== 'visible'`).** A stat figure or long word that
spills past its own card *without* being clipped — the number simply renders
past the card's edge, plainly visible — passes that check clean while looking
broken. Run this too:

```js
[...document.querySelectorAll('.op-page *')].filter(el =>
  el.children.length === 0 && el.textContent.trim() &&
  (() => {
    const r = el.getBoundingClientRect(), c = el.parentElement.getBoundingClientRect();
    return r.right > c.right + 1 || r.bottom > c.bottom + 1;
  })()
).map(el => ({ tag: el.tagName, class: el.className, text: el.textContent.trim().slice(0, 40) }))
```

An empty array is a pass. This is the check that catches a big number spilling
past a stat card.

**When something overflows or spills, fix it in this order:**

1. **Shorten the content first.** Abbreviate a number — `500,000` → `500K`,
   `$1,200,000` → `$1.2M` — keeping the currency symbol and at most one decimal.
   Cut words from a long label rather than shrinking them.
2. **If still tight, step down one type-scale token**, never an arbitrary px
   value below the scale.
3. **If the content is right but the card is too small, resize it** — a wider
   `data-grid-span`, or fewer items in the row.
4. **Never** shrink below the token scale, and never leave it spilling.

**The browser pane crops a tall canvas**, so a single screenshot will not show
the whole document. Scroll and capture in sections, or render the full page with
headless Chrome and downscale.

## Step 8 — export to PDF and deliver via Google Drive

The deliverable is a downloadable PDF on Google Drive, not the local HTML file
— the HTML in `output/onepagers/` is the source, this step is what actually
ships. Do this after step 7 passes clean, never before.

**1. Measure the real height first.** A one-pager's height is variable, and
there is no way to know it without measuring — in `javascript_tool`:

```js
document.querySelector('.op-page').getBoundingClientRect().height
```

**2. Render, passing that height explicitly.** A one-pager does NOT get its
own `@page` size the way a document does — `main.css` imports every `base/*`
file into one global stylesheet, and CSS's `@page` at-rule cannot be scoped to
a class selector, so `base/document-layout.css`'s `@page { size: 1290px
1670px }` leaks into anything else that links `main.css`. Printed with no
override, a one-pager silently comes out paginated at the DOCUMENT format's
page size, not its own — confirmed empirically, not a hypothetical. The export
script works around this by printing a disposable copy of the file with a
page-specific override injected, not by touching the source HTML:

```bash
export SMARTCAT_STATIC_ROOT="$DS_ROOT"
bash scripts/export-pdf.sh "http://localhost:8912/output/onepagers/<name>.html" <height-from-step-1> "<name>.pdf"
```

Confirmed empirically: this produces exactly one page, at exactly 1280px by
the given height, regardless of what `main.css` declares.

**3. Confirm it rendered correctly** before uploading: exactly one page, and a
size roughly matching the measured height (a few hundred KB is typical for a
file this size; 0 bytes or missing means the script failed).

**4. Upload it to Google Drive.** Find whichever Drive-capable tool or
connector is available in this session — do not assume a specific tool name,
since it varies by installation. Base64-encode the PDF and create the file
with:
- `contentMimeType: application/pdf`
- `disableConversionToGoogleType: true` — **without this, Drive silently
  converts the PDF into a Google Doc**, which is not the deliverable asked
  for. Confirmed empirically: omitting it changes the stored file's type.

**If no Drive connector is available in this session**, say so plainly and
hand over the local PDF instead — do not silently skip the upload, and do not
treat "no connector" as a reason to fail the whole build.

**Large files.** Base64 inflates size by about a third. If the upload call
fails or is clearly impractical at the file's size, say so rather than
retrying blindly — this is a real, observed ceiling (a 312KB PDF already
produces well over 400KB of base64 text), not a hypothetical edge case.

The upload response includes the file's Drive link — that link is the
deliverable to hand back, not a description of the file.

## Step 9 — report

Give the design-system commit, the archetype used, and the band sequence with
layers. Flag any component you had to add to the tier. Give the Drive link,
and say plainly if step 8 fell back to a local file instead.
