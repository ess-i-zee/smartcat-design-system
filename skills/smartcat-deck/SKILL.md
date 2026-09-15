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
`DS_ROOT`. Then read, in this order:

- `INDEX.md` — the component manifest
- **the shared rules** — icons, logo, page assembly, text casing, punctuation,
  section-background rules, CSS conventions. **Read this every time; it is not
  optional.** It's where the eyebrow-text ban and the gradient-blob ban live —
  a deck has shipped with both, in a build that skipped straight to the
  "Presentation decks" section below and never saw them.
- `CLAUDE.md` → the "Presentation decks" section
- `docs/deck-design-brain.md` — how to decide what each slide should be

```bash
sed -n '/^## Icons/,/^## Component file structure/p' "$DS_ROOT/CLAUDE.md" | sed '$d'
sed -n '/^## Presentation decks/,/^## One-pagers/p' "$DS_ROOT/CLAUDE.md"
```

Do not read the one-pager, document or social sections. Do not read
`components/` wholesale.

Two rules worth restating here because a deck's freedom to invent layouts makes
them easy to reinvent by accident:

- **No eyebrow text.** No small, bold, all-caps, wide-tracked label above or
  beside a slide title or a heading inside a panel — not as a category tag, not
  as a "best for X" callout. Use a regular line of body text instead.
- **No gradient blobs, orbs, or glows.** No soft-edged blurred circle, especially
  bleeding off a slide corner as a "spotlight" or decorative cover object. Every
  brand gradient on a slide is a flat wash with a sharp edge — see the deck
  brain's Design DNA → Color for the sanctioned forms.

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

**Check the whole slide first**, in `javascript_tool`:

```js
[...document.querySelectorAll('.deck-slide')].map((s, i) => ({
  slide: i + 1,
  w: s.offsetWidth, h: s.offsetHeight,
  overflows: s.scrollHeight > s.offsetHeight || s.scrollWidth > s.offsetWidth,
  spill: s.scrollHeight - s.offsetHeight
})).filter(r => r.overflows || r.w !== 1280 || r.h !== 720)
```

**Then check individual elements** — a stat figure or a long word can spill past
its own card without ever making the *slide* taller than 720px, since the slack
is absorbed elsewhere. The check above misses this; this one does not:

```js
[...document.querySelectorAll('.deck-slide *')].filter(el =>
  el.children.length === 0 && el.textContent.trim() &&
  (() => {
    const r = el.getBoundingClientRect(), p = el.parentElement.getBoundingClientRect();
    return r.right > p.right + 1 || r.bottom > p.bottom + 1;
  })()
).map(el => ({ tag: el.tagName, class: el.className, text: el.textContent.trim().slice(0, 40) }))
```

Both must return an empty array. This is exactly the check that catches a
6-digit stat figure spilling past its card edge — the failure mode looks fine at
the slide level and wrong only at the element level.

**When something overflows, fix it in this order — never by eyeballing a smaller
raw font-size:**

1. **Shorten the content first.** A number is the easiest case: abbreviate —
   `500,000` → `500K`, `$1,200,000` → `$1.2M`. Keep the currency symbol, one
   decimal place at most. For a long label or headline, cut words rather than
   shrink them.
2. **If it's still tight, step down one type-scale token** — e.g. Display → H1
   for a stat figure. Never an arbitrary px value below the token scale.
3. **If the content is right but the box is too small, resize the layout** —
   widen the `data-grid-span`, or put fewer stats in the row.
4. **If nothing above fits, split it into two slides.** A deck has no "next
   page" to flow onto — restructuring is the deck's version of that.
5. **Never** shrink the canvas, and never leave it clipped silently.

Screenshot two or three representative slides and share them. Check console
messages for missing assets while you are there.

## Step 6 — report

Say which commit of the design system you built against (from the loader), how
many slides, and the theme arc. Flag anything you had to cut to make a slide fit.
