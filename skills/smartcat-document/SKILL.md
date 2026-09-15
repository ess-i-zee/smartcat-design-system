---
name: smartcat-document
description: >-
  Build a Smartcat-branded multi-page document — a genuinely paginated
  1290×1670px guide that prints or exports to PDF as discrete pages with a
  running header and footer. Use for help articles, workflow and how-to guides,
  onboarding material, reference manuals, playbooks, SOPs and internal
  handbooks — anything that runs to several pages and is read like a manual.
  Also use when rebuilding an existing PDF, doc or transcript in Smartcat style.
  Not for one-pagers (single variable-height canvas), decks or social graphics;
  those have their own skills.
---

# Smartcat document

A document is the one format that is **truly paginated**. Every page is a
`.doc-page` — a fixed **1290×1670px** canvas repeating a running header and
footer, like a printed manual. Both dimensions are fixed: content is authored to
fit a page, never left to grow it.

## Step 1 — load the design system

Use the **smartcat-design-system** skill first. Then read, and nothing else:

- `INDEX.md` — the component manifest
- `CLAUDE.md` → the "Documents" section
- `docs/document-design-brain.md` — the content-role catalog

```bash
sed -n '/^## Documents/,/^## Social assets/p' "$DS_ROOT/CLAUDE.md"
```

## Step 2 — content fidelity comes before design

**Every page except the cover must reproduce the source wording exactly.** Do not
paraphrase, summarise, condense, reorder or invent replacement copy. If the
source is a PDF, doc or transcript, the words are the words.

"Verbatim" governs the words, not the characters. These you fix on the way in,
always, without asking:

- all-caps headings → sentence case
- straight quotes and apostrophes → curly (`&rsquo;`, `&ldquo;`, `&rdquo;`)
- hyphen-as-dash → spaced em dash; numeric ranges → en dash
- inline bold for emphasis → removed (restructure, or use a real type level)

The **cover page** is the one place original wording is expected — source
material rarely has a cover-shaped opening. Write the title, accent word,
audience line, subtitle and TOC labels yourself.

Deviate from verbatim elsewhere only when the user explicitly says you may
("adjust the content", "change it where needed for the design").

## Step 3 — the reuse boundary

**Compose exclusively from `components/document/*`** — doc-hero, doc-meta,
doc-steps, doc-callout, doc-screenshot, doc-divider, doc-pullquote,
doc-footnotes, doc-chapter-opener, doc-timeline, doc-table. Never reuse or
reshape a web or one-pager component, not even as a starting point. Plus raw
tokens and the type-style utilities.

## Step 4 — page structure

**Cover page** — `.doc-hero` alone inside `.doc-page[data-theme="dark"]`. No
header, content or footer on this page at all. Include a table of contents when
the document has a clean set of top-level sections. No page number.

**Every other page** — `.doc-page` containing, in order: `.doc-header` (logo,
bottom divider), `.doc-content` (the body), `.doc-footer` (document title left,
page number right). Header and footer repeat identically throughout. **The page
after the cover is numbered 2** — the cover counts toward the total.

**Section boundaries** — continuing a new section on the same page is fine and
preferred when it fits: mark it with a `.doc-divider` wrapping the new
`<h1 class="text-h1 doc-heading">`. Skip the divider only when the section opens
a fresh page; the page break already separates them.

**Screenshots** — embed the original image inside `.doc-screenshot`, which frames
it in `.doc-screenshot__container`. Never redraw, re-annotate or crop a product
screenshot; keep any callout arrows the source already has. Preserve the image's
own proportions — `width: auto`, never stretched up to the 960px cap. An image
under 40px on both sides displays at 2x.

## Step 5 — pagination is authored by hand

This is the hard part and the main failure mode. Height is fixed, so you decide
every page break.

- A page's content area holds **~1490px** at the default padding.
- **Never split a `.doc-steps__step` or a `.doc-screenshot` across two pages** —
  move the whole block to the next page.
- **Never label a continuation page.** No "[Section] — continued", no "cont'd",
  nothing announcing the break. The running footer already carries the identity;
  content simply flows on.

Estimate as you draft, then verify in step 7 and move blocks until every page
passes.

## Step 6 — write the file

`output/documents/<name>/<name>.html` — its own folder, since a document usually
carries images. Follow the house boilerplate: `<html lang="en" data-theme="light">`,
`main.css` at the right relative depth, the Inter + Plus Jakarta Sans font link,
and the preview-chrome `<style>` block **wrapped in `@media screen`** so it
cannot introduce blank pages when printing. Copy the head of an existing file in
`output/documents/` and adjust.

Banner-comment every page:

```html
<!-- ═══ PAGE 4 — Reviewing the translation ═══════════════════ -->
```

Body prose (`.doc-steps__text`, `.doc-heading-intro`, `.doc-callout__item-text`)
is `content-static-secondary`, a shade lighter than headings. Short data and
label text stays primary.

## Step 7 — verify every page fits

```
preview_start  { name: "static" }
navigate       http://localhost:8912/output/documents/<name>/<name>.html
```

Then in `javascript_tool`:

```js
[...document.querySelectorAll('.doc-page')].map((p, i) => {
  const c = p.querySelector('.doc-content');
  return {
    page: i + 1,
    size: `${p.offsetWidth}×${p.offsetHeight}`,
    overflow: c ? c.scrollHeight - c.clientHeight : 0
  };
}).filter(r => r.overflow > 0 || r.size !== '1290×1670')
```

An empty array is a pass. Any page with `overflow > 0` is spilling into nothing —
move a block to the next page and re-check. Do **not** fix it by shrinking type,
tightening spacing below the tokens, or cropping an image.

Also confirm the footer page numbers run consecutively and match the real page
order, and that the TOC page numbers on the cover point at the right pages.

Screenshot the cover and one content page to share.

## Step 8 — report

Give the design-system commit, the page count, and confirm the content is
verbatim from the source with only casing and punctuation corrected. Flag any
page where you had to move content to make it fit, and anything the source left
ambiguous.
