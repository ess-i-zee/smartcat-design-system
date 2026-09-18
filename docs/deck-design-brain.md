# Deck design brain

How to decide what a slide should look like and how to build it. This is the *reasoning* layer for presentation decks; the hard layout rules (fixed 1280×720 canvas, 48px padding, grid, title scale) live in `CLAUDE.md` → "Presentation decks", and the mechanics of `.deck-slide` live in `base/deck-layout.css`. Read those first; this doc tells you how to *think*.

The core principle (from CLAUDE.md): **compose every slide from design tokens and atomic components upward, and be creative with anything larger.** There are no deck-specific components. Every recipe below is a *composition* of existing atomic/page-level pieces and raw tokens — reshape them freely (horizontal cards, mixed sub-components, side-by-side or stacked), never treat a web component as a fixed unit.

**When a reshape recurs**, promote it to a documented component variant (in the component's own CSS) rather than re-declaring the same override in slide after slide — e.g. a horizontal card layout, or a brand-coloured stat figure. Slide-local CSS is fine for a genuine one-off; it is a smell once you've written it twice.

This is a living document. New reference slides refine it — see "E. Extending the brain" at the end.

---

## A. Design DNA — the invariants

These are what make a slide read as Smartcat. Hold them constant no matter what you're building. Values are the source-of-truth tokens; the hex shown is for recognition only.

- **Type.** Headings in Plus Jakarta Sans Bold (`--family-heading`), body in Inter Regular (`--family-body`). Headlines are large and tight, and frequently **end with a period** as a stylistic device — "Deck heading.", "Thank you.". Match that voice.
- **Title placement.** The **cover** anchors its headline **bottom-left**. **Every other slide** anchors its title **top-left**, flush at the 48px padding origin.
- **Whitespace is deliberate.** Most content slides fill only ~60–70% of the canvas. The title sits alone at the top with a large gap (the fixed 80px heading→content gap) before content, and content rarely runs to the bottom edge. Do not fill empty space just because it's there — restraint is the look.
- **Layout is not always even, and not always one layer.** An even `.grid` row of equal-width panels and a single heading+paragraph are two of the recipes below — correct and common, not the only shapes. Reference decks also split a slide at an *uneven* ratio (a short highlighted stat beside a wider table; a narrow narrative beside a bigger card grid) and *stack* two different components vertically in one slide (a process chain with a supporting card row underneath it; a quote panel over its attribution bar). See "Asymmetric & stacked layouts" in section C, and the decision procedure in section D for when each earns its place over the even/single-layer default.
- **Color.**
  - Neutrals: near-black `#13101C` text / off-white + gray surfaces in light mode; white text / near-black surfaces in dark mode. Always via `--content-*` and `--background-static-gray-layer-*` tokens.
  - **Brand gradient** (the signature accent): white → pink `#DA00FE` → purple `#731EF2` → indigo, left-to-right, always as a **flat linear fill with a sharp edge**. Used for hero moments — section-divider backgrounds, the testimonial/comparison "hero" panel, chart fills. Not for ordinary content, and **never a blurred radial blob, orb, or glow** — that generic "AI-marketing" mesh-gradient look is explicitly banned (see CLAUDE.md → "Section backgrounds beyond the gray layers"). A decorative accent, if one is wanted, is a flat brand-purple shape with a hard edge — not a soft gradient glow.
  - **Brand purple** `#731EF2` for single-color brand emphasis — stat figures, chart primaries, active/"our" elements, number badges. For text and figures the token is **`--content-static-brand`** (not a background token).
  - **Semantic green/red** (`--...-positive` / `--...-negative`) **only for genuinely positive/negative meaning** — highlights vs lowlights, Gantt done vs pending, thumbs up/down. Never decoratively.
- **Surfaces (panels/cards).** Rounded corners, generous internal padding. On **light** backgrounds → solid gray layer-1 panels. On **dark** backgrounds → translucent frosted alpha panels (`--background-static-alpha-*`), not solid blocks. One featured panel per comparison may use the brand gradient fill.
- **Gutter vs. slide padding.** The 8px gutter (`--grid-gutter`) is for the gap between two adjacent elements that **each carry their own visible surface** — stacked cards, side-by-side panels — where the tight gap reads as edges within one grid. It assumes a surface on both sides of the gap. When one side of a gap is **bare** (no background of its own — a hero stat, a bare heading, plain text) next to a paneled neighbour, there is no second edge for the gutter to relate to; use the slide's own padding value instead (**48px**, `--spacing-9`), so the bare content reads as sitting in the slide's whitespace rather than glued to the panel. Apply this per adjacency, not globally — override that one row's gap locally; do not redefine `--grid-gutter` itself, since other rows/stacks in the same slide may still be panel-to-panel and need the true 8px gutter.
- **No interactive UI — ever.** A deck is presented and viewed, not operated. The button paradigm (`.btn`, hover/active states, a click affordance) belongs to web UI and has no place on a slide. For a call to action, next step, or contact info, set it as **plain or link-styled text** (`--content-link-default` for a hyperlink-like emphasis, or just regular text) — never a pill, fill, border, or anything shaped like a clickable button. This applies everywhere a web instinct might reach for `.btn`, most commonly the closing slide.

---

## B. Choose the background and theme

Theme and background are **two independent, composable axes** (set on `.deck-slide`: `data-theme` × `data-layer`). Decide both per slide, then keep them steady across a run of related slides.

**Theme** — light is the default; dark is for rhythm and emphasis. Alternate in *bands* (a run of related slides), not per slide, so the deck scans as chapters. Section dividers are a natural place to flip.

**Background** — pick the least intense one that does the job:

| Background | `.deck-slide` | Use for |
|---|---|---|
| Solid white | light, layer-0 | The majority of regular light slides. |
| Solid gray | light, layer-1 | Light slides that need to differ from their neighbours; light-mode section titles. |
| Dark gradient (flat brand-gradient wash, sharp-edged) | dark | Regular dark slides; can also carry a light-mode section title. |
| Solid black | dark, layer-0 | Regular dark slides; strong section titles. |
| **Brand / inverted background** | `data-layer="brand"` (no theme flip — see note) | Hero moments only: section dividers, the closing "thank you", at most 1–2 per deck. |

Rule of thumb: **content slides** lean solid (white / gray / black); **gradients are reserved for dividers and the open/close** — and even there, a gradient is always a flat wash, never a soft blob/orb/glow (see Design DNA → Color). There is no "mesh gradient" asset in this system — do not improvise one with a CSS radial gradient or a blurred shape; that is exactly the banned pattern.

**Note on brand/inverted backgrounds.** `background-static-brand-inverted` (and every other `*-inverted` background token) is a self-contained pair with `--content-static-inverted` — it already contrasts correctly in whichever theme is ambient (dark purple + white text in light mode; pale purple + near-black text in dark mode). Do **not** add `data-theme="dark"` to "get" white text — that flips the background to the pale dark-mode value while independently flipping content to white, which is illegible. `base/deck-layout.css` handles this correctly by repointing `--content-static-primary`/`secondary` to `--content-static-inverted` on `data-layer="brand"`; when hand-building a slide outside that mechanism (e.g. authoring raw shapes), use the inverted background with the inverted content color directly, in one theme, with no flip.

---

## C. Slide-role catalog — recipes

Each role: *when to reach for it*, and *how to compose it* from tokens + atomic/existing pieces. These are starting points — combine and reshape as the content demands.

### Openers & dividers
- **Cover.** Headline bottom-left (Display/H1 scale), logo top-left. Background: dark, brand purple (`data-layer="brand"`), or the flat brand-gradient wash — never a soft gradient blob/orb (see Design DNA → Color). Build from `heading` alone; no decorative object is needed, and restraint is the look here too.
- **Section divider.** One big title **top-left** (Display scale), full-bleed background, no body. This is where you flip theme/background for chapter rhythm — solid gray, dark, or brand gradient. Build from `heading` alone.
- **One big statement.** A single sentence at large scale, vertically centered or top-left, nothing else. Build from `heading` (title-only) or `text-block`.

### Text-forward
- **Heading + paragraph.** Title top-left, one paragraph below after the 80px gap, occupying the left ~half. Optional subtitle line under the title (muted, `--content-static-secondary`). Build from `heading` (`data-paragraph`).
- **Bulleted list.** Title + a single column of bullets, left ~half. Keep bullets short. Compose with raw list markup styled by tokens.
- **N columns of text.** Title + 2–3 equal text columns (each an optional sub-heading + paragraph) across a `.grid` row. Use for parallel explanations with no visual per item.

### Asymmetric & stacked layouts
These aren't a separate "purpose" the way the sections around them are — they're a reshape that applies across several purposes above and below. Reach for them when the content itself is uneven or layered; don't apply them for variety's sake to content that's genuinely parallel (that's still N cards).
- **Asymmetric split.** Two panels at an uneven width ratio (e.g. 5:7 or 4:8), not an even column division — a short narrative beside a wider card grid, or one highlighted stat beside a comparison table. Use when one side is inherently smaller (a framing sentence, a single headline figure) and the other carries the supporting detail; forcing both to the same width under-serves whichever side actually has less to say. Panel gap follows the gutter-vs-padding rule above: 8px when both sides carry their own surface, 48px when one side is bare text or a bare heading.
- **Stacked composition.** Two different components stacked vertically in one slide instead of side by side — a process chain with a supporting detail-card row underneath, or a quote panel over an attribution bar (the existing Testimonial recipe below is one instance of this, not a one-off). Use when a slide needs both a headline element and the detail behind it, and putting them side by side would starve one of them of width.
- **Hierarchy within a repeated component.** A row of otherwise-identical cards need not stay uniform — one card can be visually promoted (a brand-purple fill or border, a small "recommended"/featured marker) to read as the featured option among peers, without breaking out of the N-cards shape entirely.

### Enumerated content
- **N cards (2–4).** Title + a `.grid` row of panels, each = sub-heading + paragraph. Light → gray panels; dark → frosted alpha panels. Built from `cards` (`data-media="none"`) or composed panels. Reshape to horizontal (media left, text right) when useful. One card in the row may be promoted over its neighbours — see "Hierarchy within a repeated component" above — when the content has a genuine featured/recommended option; don't promote a card just to break up the row.
- **Icon cards.** Same as N cards but each panel leads with a circular icon tile (design-system icon, brand-purple) above a caption + paragraph. Built from `cards` (`data-media="icon"`).
- **Agenda.** Full-width stacked rows (~65% width), each = an icon tile on the left + a label. Emphasize the final/action row with a brand-purple fill. Compose from atomic icon tiles + token-styled rows.

### Quantitative & proof
- **Numbers / stats.** Title + a `.grid` row of 2–4 panels, each = a big **brand-purple** figure (Display scale) + bold caption + supporting paragraph. Built from `numbers`. Note: `numbers.css` paints `.numbers__value` in `--content-static-primary`; for the deck's brand-purple figure set the value colour to `--content-static-brand`. That override recurs — a candidate to graduate into a `numbers` brand-figure variant.
- **Charts.** Title + a `.grid` row of panels, each holding one simple chart (donut, bar pair, arrow/pentagon). **Purple = the primary/highlighted series; white/outline = the comparison series.** Caption paragraph under each. Compose chart shapes from token-colored elements.
- **Key metrics / OKR.** A row of "KR" cards (white number badge + text) above a "Steps established" sub-heading and a row of numbered step cards. Step number badges may use semantic green. Compose from panels + badges.
- **Highlights vs lowlights.** Two panels side by side, each = heading + a semantic icon badge top-right (green thumbs-up / red thumbs-down) + bulleted list. Compose from panels + semantic-colored atomic badges.
- **Testimonial.** A brand-gradient quote panel (large white quote) stacked over a gray attribution bar: circular photo + name/title on the left, customer logo on the right. Built from `testimonial`, reshaped to the stacked two-part card.

### Comparison & relationships
- **Comparison v1 (side by side).** Two panels: neutral gray (dark text) vs **brand-purple gradient** (white text, Smartcat monogram top-right). The purple side reads as "ours"/preferred. Each = heading + bullets.
- **Comparison v2 (2×2 with flow).** Two stacked rows of the v1 pairing, with a downward chevron between the two brand panels to show progression.
- **Alignment matrix.** Two columns of numbered cards — **purple numbers = Smartcat (left), black numbers = client (right)** — with center labels between them and inward-pointing chevrons. "Smartcat" label top-left, client logo top-right.

### Time & structure
- **Timeline.** A horizontal center bar (alternating light/dark purple segments); milestones alternate above and below with dotted connectors; each = bold title + muted "(Day N)" + paragraph. Compose from token-colored bar + positioned text blocks.
- **Gantt.** A table with a Workstream/Description column and a numbered week or named month axis; process bars span columns — **solid purple = completed, light outline = future** — with a Completed/Future legend. Month variant adds dotted vertical gridlines.
- **Flow / graph.** Node boxes (brand-gradient pills, gray boxes, circular nodes — black or purple) connected by dotted arrows, optionally grouped under "Timeline point" columns divided by baseline rules. The simplest form of this recipe is a single straight left-to-right chain of pill nodes joined by solid arrows, no grouping or dotted lines — reach for the fuller node/branch/dotted treatment only when the content genuinely branches or needs milestones grouped under headers. A straight chain reads well paired with a stacked detail-card row underneath it (see "Asymmetric & stacked layouts" above).

### Tabular
- **Table.** Bold column headers, thin row dividers, muted values. Highlight the key column with a gray fill (e.g. the label column of a pricing table); add a bold summary/total row below when relevant. Compose from token-styled table markup.

### Closing
- **Closing / thank-you.** Title top-left ("Questions? Thank you."), on a brand-gradient, dark, or gray background — mirror the cover's treatment. Optional contact info or next-step links, set as plain/link-styled text — **not `.btn`** (see "No interactive UI" in Design DNA). Build from `heading`.

---

## D. The decision procedure — turning content into a slide

Run these in order for each slide:

1. **What is this slide's *job*?** Map the intent to a role in section C:
   - Open / divide a section → cover / section divider
   - Land one idea → one big statement
   - Explain in prose → heading + paragraph / bulleted list / N columns
   - Enumerate parallel items → N cards / icon cards / agenda
   - Quantify or prove → numbers / charts / key metrics / testimonial
   - Contrast options → comparison v1 or v2 / alignment matrix
   - Show sequence or plan → timeline / Gantt / flow
   - Present rows of data → table
   - Close → thank-you
2. **How much content, how many items — and does it want an even shape or an uneven one?** Item count narrows the options; it doesn't hand you a single answer:
   - 1 item → full-width or centered.
   - 2–4 *genuinely parallel* items (same weight, same structure) → an even `.grid` row of panels/columns — N cards, N stats. This is still the right call whenever the items really are peers.
   - One headline element plus a larger block of supporting detail (a framing sentence next to a card grid; one highlighted stat next to a comparison table) → an **asymmetric split** at an uneven ratio instead of forcing an even division.
   - A summary plus the detail behind it (a process chain and what backs each step; a quote and its attribution) → **stack** two components vertically in one slide rather than only side by side.
   - Many shallow items → cards or a list. Paired items → side-by-side panels.
   Respect the "whitespace is deliberate" invariant — if it's getting cramped, split into two slides.

   **None of this makes the even card row or a plain heading+paragraph a worse choice** — for content that's actually parallel or actually a single idea, they're the correct, most-used answer in this catalog, not a fallback. The failure mode isn't using them; it's reaching for them by reflex on every slide without checking whether *this* slide's content is actually asymmetric or layered. Run this step as a real choice among the options above each time, not a formality on the way to the default.
3. **Where does this slide sit in the deck's rhythm?** Pick theme + background per section B — alternate light/dark in bands, reserve gradients for dividers and the open/close.
4. **Compose it** from tokens + atomic components (section A + the recipe). Reshape components as needed; keep every color/size/space/radius a token.
5. **Sanity-check against the DNA (A):** right title placement (cover = bottom-left, else top-left); period-style headline where it fits; semantic colors only for real positive/negative; brand gradient only on a hero moment; panels styled per light/dark; generous whitespace; **for every gap between adjacent elements, check whether both sides have a surface — gutter (8px) if both do, slide padding (48px) if either is bare**; **no `.btn` anywhere — any call to action or link is plain/link-styled text.**

When two roles both fit the content equally well, choose the one that needs the least visual machinery — a clean heading + paragraph beats a forced diagram. This is a tie-breaker between options that already fit, not a reason to skip step 2's check of whether an asymmetric or stacked shape fits *better* than the even default.

---

## E. Extending the brain

This doc is meant to grow as real example slides are provided. When given a new example (or a correction):

1. **Inspect it visually** (render to an image and look — don't infer from text).
2. **Extract, in this order:**
   - **Background & theme** — which of section B, light or dark.
   - **Layout skeleton** — title position, how the canvas is divided (columns/rows/panels), what's left empty.
   - **Atomic pieces used** — which atomic/existing components, and how they were *reshaped* (e.g. horizontalized card, mixed sub-components).
   - **Tokens** — the specific color/type/spacing/radius roles in play, especially any semantic or brand-gradient use.
   - **Anything new** — a pattern not already in section C.
3. **Fold it in:** refine an existing recipe in C, or add a new role; adjust A or B only if the example reveals a genuine invariant. Keep recipes short and composition-based. Log it below.

Do **not** move deck reasoning into `CLAUDE.md` — that file holds only the hard, binding rules; the how-to-think stays here.

### Changelog
- Initial version — derived from visual inspection of the "Smartcat deck template 2026 – All Designs" reference deck (106 slides): design DNA, background/theme axes, slide-role catalog, decision procedure.
- Test-driven refinements — built and rendered a sample composition slide ("What slow localization costs you"): named `--content-static-brand` as the stat-figure token; added the "recurring reshape → component variant" principle. Same test fixed a deck-grid bug: `.deck-slide` now zeroes column padding so grid content sits flush to the 48px slide padding (see `base/deck-layout.css`).
- Correctness fix — a token audit (ahead of a full generated deck) found the "brand + `data-theme=dark`" guidance from the prior refinement was wrong: `*-inverted` background tokens are self-contained pairs with `--content-static-inverted`, already correct in either ambient theme; combining with a theme flip breaks contrast. `base/deck-layout.css` and the background table above corrected — no code elsewhere had shipped this yet.
- Rule added — a full 10-slide test deck used real `.btn` components for the closing slide's CTAs. Corrected: decks are presented/viewed, not operated, so the button paradigm doesn't belong on a slide at all. Added "No interactive UI — ever" to Design DNA, updated the Closing recipe and the decision procedure's sanity-check to require plain/link-styled text instead of `.btn` for any call to action or link.
- Layout-variety correction (2026-09-18) — a generated deck was reviewed against `references/decks/` (the source reference images, not this doc's summary of them) and every content slide turned out to be either a single heading+paragraph or an even row of cards. Inspecting real examples — `exec-summary-3col.jpg`, `math-savings.jpg`, `compliance-risk-grid.jpg`, `pricing-table.jpg`, `stat-cards-quote.jpg`, `choice-cards.jpg` among them — showed real decks use those two shapes plenty, but also routinely reach for an **asymmetric split** (an uneven-ratio two-panel layout — a short narrative beside a wider card grid, one highlighted stat beside a table), a **stacked composition** (two different components in one slide, e.g. a process chain over a supporting card row, or a quote over its attribution bar), and **hierarchy within a repeated component** (one card in an otherwise-even row visually promoted as the featured option). Added a new "Asymmetric & stacked layouts" subsection to C, a hierarchy note to the N-cards recipe, a "simplest form" note to Flow/graph, and a new Design DNA bullet naming these as real options. Rewrote decision-procedure step 2 (D) to lay out per-situation options instead of one item-count → one-layout mapping.
  **Explicit correction, since the first pass at this got it backwards:** an even card row and a plain heading+paragraph are not problems to design around — they're the correct, most common answer whenever content is genuinely parallel or genuinely a single idea, and both recipes stay exactly as documented above. The actual defect was building slide after slide by reflex, on the nearest available shape, without asking each time whether *this* slide's content is asymmetric or layered enough to want something else. The fix is a deliberate per-slide choice among the options in C/D, not avoidance of cards or heading+paragraph — see step 2's explicit note.
