# Document design brain

How to decide what a paginated document should look like and how to build it. This is the *reasoning* layer for documents; the hard layout rules (fixed 1290×1670px `.doc-page` canvas, header/content/footer mechanics, the cover spec) live in `CLAUDE.md` → "Documents", and the mechanics of `.doc-page`/`.doc-content` live in `base/document-layout.css`. Read those first, plus every file in `components/document/*`; this doc tells you how to *think*.

Everything below was reverse-engineered from 3 real-world documents in `references/documents/` (visually inspected page-by-page, not inferred from extracted text — the same method `docs/deck-design-brain.md` and `docs/onepagers-design-brain.md` use): Ramp's *Business Spending Report* (27pp, data/editorial report), Zapier's *Is your AI strategy built for everyone or just engineers?* (14pp, pillar-page whitepaper), and WRITER's *The Agentic Compact* (76pp, long-form enterprise whitepaper). Rebuild that inspection whenever a new reference document is added; fold in what's genuinely new (see "E. Extending the brain").

**The governing principle: borrow layout thinking, never borrow color.** All three source documents have their own brand palettes (Ramp navy/orange, Zapier orange/cream, WRITER black/periwinkle/lavender) — none of that hex data belongs in our system. Every pattern below is reformulated against *our* tokens (`--background-static-brand-layer-1`, `--content-static-brand`, the pink/blue/orange layer tokens, etc.) or dropped outright if it can't be. Never introduce a raw color, a new font, or a new spacing value copied from a source PDF — if a pattern doesn't cleanly resolve to an existing token, treat it as a proposal (marked below) that needs sign-off before it's built, not a fact to implement silently.

---

## A. Design DNA — the invariants

- **Type stays exactly as documented.** Headings in `--family-heading` (Plus Jakarta Sans Bold), body in `--family-body` (Inter Regular) — same as web/decks/one-pagers. None of the three references' display faces (Ramp's grotesk, Zapier's rounded grotesk, WRITER's rounded sans) are adopted; our existing type scale already does the job of a report-style headline at `.text-display`/`.text-h1`.
- **A document reads like a printed manual — restraint over density.** All three references favor generous whitespace on text-heavy pages (Ramp's report pages routinely leave the bottom third of the page empty; WRITER's prose pages do the same). Don't fill a `.doc-page` to its content-area ceiling just because there's room — if a page is light, let it breathe. This is closer to the deck brain's "whitespace is deliberate" than the one-pager brain's density-is-the-point stance.
- **Structural bold, never emphasis bold.** All three references bold individual words or clauses inside running prose for emphasis — this directly conflicts with CLAUDE.md's "do not use bold for inline emphasis" and is dropped everywhere it appears as emphasis. The one bold usage that *is* kept: a bold **lead-in term** at the start of a bullet or line (e.g. "**Core mandate:** ...", "**Access controls:** Allow the client to...") — that's a structural label naming what follows, the same convention `.doc-callout__term` already uses, not mid-sentence emphasis.
- **No eyebrows, no all-caps — full stop.** All three references lean heavily on all-caps kicker labels (cover eyebrows, running chapter pills, box headers like "CASE STUDY"/"ZAPIER AUTOMATION INSIGHTS"/"ARTICLE I"). Every one of these is dropped as literal all-caps and reformulated in sentence case using existing components (see section C) — the *functional* idea (a running chapter label, a categorized callout) is almost always worth keeping; the typographic treatment never is.
- **Color-coding uses our existing layer system, never a new hue.** When a source document color-codes categories (WRITER's pink case-study boxes, blue/purple pillar labels, colored 3-card lists), reformulate using the existing `--background-static-{pink,blue,orange,brand}-layer-1` + matching `--content-static-*` pairs — the same system `.doc-meta__pill`'s `data-color` already implements. Never invent a new semantic hue for a category label.
- **A document can flip an individual page to dark theme or a tint for emphasis — this is already fully supported.** WRITER's mid-document dark Q&A spread and lavender/brand-tint chapter-opener pages are just `.doc-page[data-theme="dark"]` or a full-page `--background-static-brand-layer-1` fill — no new mechanism needed, just confirmation that per-page theme flips (not only on the cover) are a legitimate, recurring craft choice for a long document.

---

## B. Choosing layout treatment per page

Three page "modes" recur across all three references. Decide the mode per page, not per document:

1. **Running content page (the default).** Full `.doc-header`/`.doc-content`/`.doc-footer` structure, light theme, one topic per page. This is what CLAUDE.md already documents and what the vast majority of pages in all three references use.
2. **Chapter-opener / part-title page.** A page that introduces a new major part of a long document (WRITER uses this for each of its ~6 top-level sections). Full-bleed background tint (brand-tint or dark, never the plain white `.doc-page` default), a large display title, and often a floating summary card. See the "Chapter opener" recipe in section C — this is the paginated-document equivalent of a deck's section-divider slide.
3. **Emphasis page (occasional).** A running content page that flips to `data-theme="dark"` for one especially important spread (a Q&A, a pull-out framework) rather than staying light throughout. Use sparingly — at most a small handful of times in a long document, the same restraint the deck brain applies to brand-gradient slides.

**When to reach for a chapter-opener page vs. a same-page `.doc-divider`:** CLAUDE.md already says a new top-level Section can continue on the same page via `.doc-divider`, or open fresh via a page break. The chapter-opener treatment (mode 2) is an *optional, stronger* version of "opens on a fresh page" — reach for it only in genuinely long, multi-part documents (roughly 30+ pages, several major parts) where a reader benefits from a clear visual chapter break; for a short document, a plain fresh-page break (no special tint) is enough.

**Running chapter label.** For any document with named top-level parts, put the current part's name in `.doc-header__tag` (already part of the header spec) and keep the exact same wording on every content page belonging to that part — this is the running-head convention all three references use (rendered there as an all-caps pill; render it here as plain sentence-case text per CLAUDE.md's existing `.doc-header__tag` spec). Update it only when a new top-level Section begins.

---

## C. Content/section-role catalog — recipes

Each entry: *when to reach for it*, and *how to build it from existing tokens/components*. Entries originally marked **[proposal]** have all since been signed off and built — marked **[built]** below, with the component/variant that implements them. Everything else was already buildable with zero code changes.

### Data / stat pages
- **Chart scaffold.** Ramp's recurring data page: a small tertiary-colored index label (`.text-caption`, `content-static-tertiary` — e.g. "Chart 01"), a bold headline (`text-h3 doc-heading`), a one-sentence dek (`.doc-heading-intro`), then the visual, then generous empty space below. The chart/graph itself is out of scope — this tier has no charting component — but the textual scaffold around a data visual (label → headline → dek → visual) is a valid, reusable recipe for any page whose point is a single data takeaway.
- **Big-stat callout.** Zapier's huge-numeral stat page ("80%", "1.6x"): one or two big figures at `.text-display`, colored `content-static-brand`, each paired with a short `.text-small` caption, inside a bordered box (reuse the `.doc-meta` bordered-container styling). Good for a single standout metric worth calling out on its own.

### Callouts and boxes
- **Categorized callout.** WRITER's pink case-study boxes and colored 3-item lists map directly onto `.doc-callout` **[built: `data-color` variant]** mirroring `.doc-meta__pill`'s existing `gray | blue | orange | pink` system, so a callout can be thematically tinted (e.g. pink for a case study, blue for a definition) instead of always the neutral gray-layer-1 background it has today.
- **Icon-led insight callout.** Zapier's lightbulb-icon "insight" boxes: a design-system icon (per CLAUDE.md's icon rules) leading a single bold sentence, in a bordered box. **[built: `.doc-callout__head` + `.doc-callout__icon` leading-icon slot]**.
- **Checklist callout.** WRITER's "First 30/60/90 days" checkbox lists: same bordered/divided-row structure as `.doc-callout`, but each item gets an empty-square checkbox glyph instead of the dot bullet. **[built: `data-marker="checkbox"` on `.doc-callout`]** — swaps `::before`'s dot for an outlined square; no new tokens required.

### Lists and catalogs
- **Bordered catalog / roadmap list.** WRITER's "Six articles of the Compact" and myth-debunking pages: a bordered container (`.doc-meta`'s box-with-divided-rows styling) where each row pairs a small colored tag (reuse `.doc-meta__pill`'s color system) with a bold lead-in term and a description. Fully buildable today as a documented *composition* of `.doc-meta` + `.doc-callout__term` — no new component.
- **Icon-led row list.** WRITER's 3-row "judgment rubric": the same bordered/divided-row container, but each row leads with a circular icon tile (a design-system icon on a `--background-static-*-layer-1` circle) instead of a pill, followed by a heading and a paragraph. A variant of `.doc-steps` with the numbered badge swapped for an icon tile — **[built: `data-marker="icon"` on `.doc-steps`]**.
- **Numbered list with circular badge numerals.** WRITER's plain numbered lists (e.g. "3 fundamental questions") confirm `.doc-steps__number`'s circular-badge treatment is exactly right for this — no change needed, just validated as transferable to plain numbered arguments, not only literal how-to steps. Lettered sub-items nested one level under a numbered item (a, b, c) are a natural extension using the same type styles, no new token.
- **Role / profile mini-pattern.** WRITER's recurring role write-ups ("AI Program Director — Formal role" / "Core mandate:" / "Key responsibilities:" / "Strategic importance:") are a pure content convention: a bold title + qualifier line, then bold structural lead-ins (`.doc-callout__term`-style) introducing each block. Zero new tokens or components — just a documented prose pattern for any "define a role/entity" page.

### Quotes and citations
- **Pull-quote.** WRITER's large-scale quotes set off with a left border rule and no quotation-mark glyph (`border-left: 1px solid var(--border-divider-default)`, padding-left, text at `.text-h3`/`.text-h2` weight, `content-static-primary`). **[built: `doc-pullquote` component]**.
- **Attributed quote with photo.** Zapier's serif-quote-beside-photo pattern is a valid recipe *if* reformulated to reuse `.doc-screenshot__frame`'s existing border/radius/shadow treatment for the photo, so the framing stays consistent with the rest of the document rather than introducing a new image treatment.
- **Footnotes / citations block.** All of WRITER's pages number claims with superscripts and list sources at the bottom, separated by a thin top rule, in small tertiary-colored text. **[built: `doc-footnotes` component]**.

### Chapter/cover-adjacent pages
- **Chapter opener.** For long, multi-part documents: a full-page tint (`--background-static-brand-layer-1` or `data-theme="dark"`), a large `.text-display` title (vertically centered), page number top-right, and an optional floating summary card. **[built: self-sufficient `doc-chapter-opener` component]** — structurally similar to `.doc-hero` (no running header/footer — its own page number instead) but for interior part-openers rather than the document cover.
- **Extended table of contents.** The cover's `.doc-hero__toc` now supports a nested sub-level. **[built: `.doc-hero__toc-item` wraps `.doc-hero__toc-item-main` + optional `.doc-hero__toc-subitem` rows (indented, dotted leader to a right-aligned page number); page numbers added to top-level rows via `.doc-hero__toc-page`]** — useful once a document exceeds roughly 20–30 pages with real sub-sections worth listing.

### Milestone / roadmap visuals
- **Timeline diagram.** WRITER's "First 30/60/90 days" horizontal milestone timeline (pill labels, a connecting line with dots, boxed captions below each milestone). **[built: `doc-timeline` component]** for any document that needs to show a short rollout plan or phased roadmap.

---

## D. The decision procedure — turning a document brief into page-by-page composition

1. **Is this a short (under ~20pp) or long (30pp+), multi-part document?** Short documents stay entirely in "running content page" mode (section B, mode 1) with plain fresh-page breaks between top-level Sections. Long, multi-part documents earn chapter-opener pages (mode 2) at each major part boundary.
2. **What is each page's job?** Map its content to a recipe in section C: a data takeaway → chart scaffold; a single standout number → big-stat callout; a themed aside → categorized/icon-led/checklist callout; an enumerable catalog → bordered list; a sequence → numbered steps; a notable claim → pull-quote; a sourced fact → footnotes block.
3. **Does the page need a running chapter label?** If the document has named top-level parts, set `.doc-header__tag` to the current part's name and keep it constant across every page in that part.
4. **Pick theme per page, sparingly.** Default every page to light. Reserve `data-theme="dark"` or a brand-tint fill for a chapter opener or one genuinely emphasis-worthy spread — not as a rhythm device the way decks alternate light/dark.
5. **Compose from `components/document/*` + tokens only** (per CLAUDE.md — never reuse web/one-pager components). Every recipe above is now buildable today with zero further sign-off — treat future genuinely-new patterns the same way: mark them **[proposal]** and confirm with the user before writing new component code.
6. **Sanity-check against the DNA (A):** no eyebrow/all-caps labels anywhere; no inline emphasis bold (structural lead-in bold only); no color introduced outside the existing token set; whitespace left generous rather than padded to the content-area ceiling; screenshots still framed only via the single uniform `.doc-screenshot__container` treatment.

---

## E. Extending the brain

This doc grows as real reference documents are analyzed or new documents are built. When given a new example (or a correction):

1. **Inspect it visually, every page** (render each page to an image and look — don't infer from extracted text). For anything beyond a handful of pages, this is large enough work to hand to a forked/background agent rather than doing it inline.
2. **Extract, in order:** page-mode used (running/chapter-opener/emphasis), which recipe in section C each page maps to (or whether it's genuinely new), any color-coding and which existing token it should map to, anything that conflicts with a hard rule in CLAUDE.md.
3. **Fold it in:** refine an existing recipe in C, add a new one if the page truly doesn't fit, and mark any component-level change **[proposal]** until the user has explicitly signed off — never silently ship a new component or token from a reference-document pass.

### Changelog
- Initial version — derived from full page-by-page visual inspection of 3 reference documents in `references/documents/`: Ramp's *Business Spending Report* (27pp), Zapier's *Is your AI strategy built for everyone or just engineers?* (14pp), and WRITER's *The Agentic Compact* (76pp) — 117 pages total, read in full with no sampling. Produced: design DNA, page-mode framework, a 13-entry recipe catalog (7 buildable today with zero code changes, 9 flagged as proposals pending sign-off — categorized-callout color variant, icon-led callout, checklist callout, icon-led step variant, pull-quote element, footnotes component, chapter-opener element, extended nested TOC, timeline component), and the decision procedure above. Patterns dropped as conflicting with hard rules: all-caps eyebrow/kicker labels (pervasive across all 3), bold inline emphasis in running prose (WRITER, Zapier), decorative full-bleed chapter-divider art (Ramp), italicized display headlines (WRITER), arched/curved photo-crop framing (WRITER foreword), and hand-drawn signature graphics (WRITER foreword).
- All 9 proposals signed off and built: `data-color` + leading-icon + `data-marker="checkbox"` on `.doc-callout`; `data-marker="icon"` on `.doc-steps`; new `doc-pullquote`, `doc-footnotes`, `doc-chapter-opener`, `doc-timeline` components; `.doc-hero__toc-item` extended with page numbers + nested `.doc-hero__toc-subitem`. Wired into `main.css`, documented in `CLAUDE.md` → "Documents". Dropped/conflicting patterns re-confirmed excluded — none introduced anywhere in this round. `examples/documents/aem-reviewer-workflow` re-flowed to apply the fitting subset (categorized callouts, TOC page numbers) — the AEM guide is short and single-part, so chapter-opener/pull-quote/footnotes/timeline/checklist/icon-led-steps had no genuine content fit there and stay documented-but-unused for this example, per section D step 2's "map content to a recipe" (no recipe should be forced where the content doesn't call for it).
