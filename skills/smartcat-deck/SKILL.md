---
name: smartcat-deck
description: >-
  Build a Smartcat-branded presentation deck as HTML — a sequence of fixed
  1280×720 slides composed from the design system. Use whenever someone wants a
  Smartcat deck, slides, a presentation, a pitch, a QBR or a customer-facing
  walkthrough: "make a deck", "turn this into slides", "build a presentation for
  X", "put this in Smartcat style as a deck". Reach for it especially when the
  deck should be visually designed — stats, comparisons, timelines, diagrams —
  rather than plain bullets. Not for one-pagers, printed documents or social
  graphics; those have their own skills.
---

# Smartcat deck

A deck is a sequence of **fixed 1280×720px slides**. No responsive behavior, no
media queries, no breakpoints — the canvas never changes size.

## Step 1 — load the design system

Use the **smartcat-design-system** skill first. It syncs the repo and gives you
`DS_ROOT`. Then read, and nothing else:

- `INDEX.md` — the component manifest
- `CLAUDE.md` → the "Presentation decks" section
- `docs/deck-design-brain.md` — how to decide what each slide should be

```bash
sed -n '/^## Presentation decks/,/^## One-pagers/p' "$DS_ROOT/CLAUDE.md"
```

Do not read the one-pager, document or social sections. Do not read
`components/` wholesale.

## Step 2 — plan the deck before writing any HTML

Work out the full slide list first — one line per slide, each naming its **role**
(cover, agenda, section divider, stat, comparison, process, quote, closing) and
its theme. Section D of the deck brain is the decision procedure; section C is the
role catalog with composition recipes.

Then check the arc:

- **Light sandwich.** Content slides light; cover, section dividers and the
  closing slide dark or brand-purple. A deck that is all one treatment reads flat.
- **One idea per slide.** If a slide needs two headlines, it is two slides.
- **A divider every 3–5 content slides** on anything longer than ~10 slides.

Show the user the slide list before building if the deck is longer than about six
slides — restructuring costs nothing at this stage and a lot later.

## Step 3 — compose each slide

**A slide is not "one page-level component in a box."** Build from **tokens and
atomic components** upward and be inventive above that level. There is no
`components/deck/*` tier — do not create one.

You may freely:
- combine components vertically *and* horizontally
- mix pieces — an icon card beside a number card, a stat figure beside a quote
- reshape a web page-level component's internal layout for the slide (turn a
  stacked card horizontal, put the icon left and text right)

Keep every color, type size, spacing and radius a token. That is what keeps an
invented layout on-brand.

Mechanically, inside `.deck-slide` put a `.grid` row below the title and place
items with `data-grid-span="1".."12"`. The grid is locked to 12 columns with an
8px gutter and no column padding, so content sits flush to the slide's 48px
padding, aligned with the title. Stack multiple `.grid` rows to compose
vertically.

```html
<div class="deck-slide">
  <div class="heading">…</div>
  <div class="grid">
    <div class="…" data-grid-span="6">…</div>
    <div class="…" data-grid-span="6">…</div>
  </div>
</div>
```

### Fixed geometry — do not improvise these

| Rule | Value |
|---|---|
| Canvas | 1280×720, fixed |
| Padding, all four sides | 48px (`--spacing-9`) |
| Content width | 1184px |
| Slide title | `data-level="h1"`, flush at the padding origin |
| Divider / single-statement slide | Display scale |
| Big stat figures | Display scale |
| Heading → content gap | 80px, every slide type |

### Buttons are pictures here

A deck is presented, not clicked. Render a CTA as `<span class="btn">`, never
`<button>` or `<a>` — this is the opposite of the one-pager rule.

## Step 4 — write the file

`output/decks/<deck-name>/<deck-name>.html`, one file for the whole deck. Follow
the house boilerplate: `<html lang="en" data-theme="light">`, a link to
`main.css` at the right relative depth, the Inter + Plus Jakarta Sans font link,
and a "Preview chrome only" `<style>` block that centers the canvas and stacks
slides with a gap. Copy the head of an existing one-pager or document in
`output/` and adjust the depth.

Comment each slide with a banner so the file stays navigable:

```html
<!-- ═══ SLIDE 4 — Why it matters (dark) ═══════════════════════ -->
```

## Step 5 — verify every slide fits

Overflow is the one failure mode that matters: a fixed 720px canvas silently
clips or spills. Start the preview server and measure — never eyeball it, and
never ask the user to check.

```
preview_start  { name: "static" }
navigate       http://localhost:8912/output/decks/<name>/<name>.html
```

Then run this in `javascript_tool`:

```js
[...document.querySelectorAll('.deck-slide')].map((s, i) => ({
  slide: i + 1,
  w: s.offsetWidth, h: s.offsetHeight,
  overflows: s.scrollHeight > s.offsetHeight || s.scrollWidth > s.offsetWidth,
  spill: s.scrollHeight - s.offsetHeight
})).filter(r => r.overflows || r.w !== 1280 || r.h !== 720)
```

An empty array is a pass. Anything listed needs content cut or moved to another
slide — never shrink the canvas, never drop the type scale below the tokens to
make something fit.

Screenshot two or three representative slides and share them. Check console
messages for missing assets while you are there.

## Step 6 — report

Say which commit of the design system you built against (from the loader), how
many slides, and the theme arc. Flag anything you had to cut to make a slide fit.
