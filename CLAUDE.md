# Design System Rules

## Output formats

This design system serves two output formats:

- **Web-based interfaces** — landing pages and other web UI. Everything in this document, from "Component tiers" through "Component file structure," is scoped to this format, including the two-breakpoint responsive model in "Breakpoints & layout grid."
- **Presentation decks** — slide decks built with this design system. See "Presentation decks" near the end of this document. Decks reuse the same color, typography, radius, and spacing tokens as web — only the layout treatment differs (a fixed slide canvas instead of a responsive page).

Where "Presentation decks" doesn't override a rule, the general guidance above still applies (icon usage, text casing, tokens-only CSS, component content patterns, etc.) — only layout/responsiveness is format-specific.

## Component tiers

### Atomic components (`components/atomic/`)
Small, self-contained UI elements. Examples: button, input, tag, badge, avatar, icon, checkbox, tooltip.
An atomic component does not own a full page row — it is always embedded inside a page-level component or another atomic component.

### Page-level components (`components/page-level/`)
Full-width page rows stacked vertically to form a page. Examples: hero, cta, features-grid, testimonials, logos, pricing, faq.
A page-level component always spans the full page width and handles its own internal layout, spacing, and responsive behavior.

Not to be confused with a **Section** — a composition-level grouping of page-level components; see below.

### Sections (page composition)
A Section is not a component tier and has no `.html`/`.css` pair of its own. It's how page-level components are grouped when assembling a page: one Section = one or more page-level components (hero-block, numbers, zigzag, cta, etc.) united into a single logical and visual chunk. There's no fixed minimum or maximum — roughly 1 to 3-4 page-level components per Section is typical.

Grouping into Sections makes long pages easier to digest. Compose every page as a sequence of Sections, not a flat, undifferentiated stack of page-level components.

**Every page is divided into Sections — even a page that is a single Section — and every Section carries an explicit background.** There is no "no-background" section: a Section that does not need contrast still gets wrapped, defaulting to `--background-static-gray-layer-0`. Never let components stack on the browser's default background.

**Note — hero-block is self-sufficient.** The hero-block page-level component is a complete, self-contained Section on its own with its own background. Do not wrap it in a `.section-band`, do not group it with other page-level components — place it directly as the page's opening row.

**Three ways to visually separate one Section from the next:**
1. **Background-layer contrast (default).** Adjacent Sections use different `--background-static-gray-layer-*` steps, set with `data-layer="0".."3"` on the band (e.g. layer-0 next to layer-1). Identical in light and dark mode.
2. **Light/dark theme contrast.** One Section in light mode, the next in dark, or vice versa. Alternating light and dark Sections is **highly preferable** for a well-structured page — it breaks a long page into clearly digestible chunks the eye can scan. Reach for this as a primary technique, not a rare accent.
3. **Brand-color band (accent, ≤1–2 per page).** A Section on a saturated brand-purple background (`--background-static-brand-*` tokens) for the page's showcase moments — the closing conversion CTA, a stats/proof band, or a logo wall. Never for ordinary feature content.

**Theme rhythm (patterns observed on smartcat.com — follow unless the user directs otherwise):**
- Themes alternate in **bands of 1–4 related components**, not per component — decide the theme per Section, and give every page at least ~3 theme changes so it scans as distinct chapters.
- **Fixed assignments:** FAQ Sections are always light. Social-proof Sections (review walls, rating sliders) are dark. Runs of feature zigzags lean dark. The **page-closing CTA is always saturated** — brand purple or a dark band — while mid-page CTAs stay neutral/light.
- Heroes are dark or light with roughly equal frequency; a canonical page arc is: hero → benefits (often dark) → proof numbers (light or brand band) → features (alternating) → social proof (dark) → resources (light) → FAQ (light) → final CTA (saturated).

**How to give a Section its background (and optionally a dark theme).** Wrap the Section's components in a `.section-band` (see "Breakpoints & layout grid" below) — a full-bleed wrapper that carries the background and adds no page padding of its own (the page-level components inside already own their horizontal padding, so a `.section` wrapper here would double it). Set the background layer with `data-layer="0".."3"` (omit for the layer-0 default). Add `data-theme="dark"` to flip the band to dark; the layer background and all child content tokens switch automatically. Put the Section's top and bottom **size-8** Components spacing *inside* the band so the padding sits on the band's own background — a boundary between two bands therefore shows a size-8 on each side, one on each background. Never use a one-off class or inline style for this — `.section-band` plus `data-layer`/`data-theme` is the only mechanism.

```html
<!-- default Section (layer-0) -->
<div class="section-band">
  <div class="components-spacing" data-size="8"></div>
  <!-- heading + components … -->
  <div class="components-spacing" data-size="8"></div>
</div>

<!-- next Section, contrasting layer -->
<div class="section-band" data-layer="1"> … </div>

<!-- occasional dark-theme Section -->
<div class="section-band" data-theme="dark"> … </div>
```

**Override rule:** if the user has explicitly requested the page (or a specific section) be light or dark, honor that literally and do not add theme-contrast (technique 2) as a section-boundary device on top of it — use background-layer contrast (technique 1) only.

**Practical guidance:** default to alternating light and dark Sections through the page — not just one dark accent — unless the user specified an all-light or all-dark page (see the override rule above).

### Components spacing

Vertical gaps between page-level components — and the vertical rhythm that structures Sections — are created with the **Components spacing** page-level component (`components/page-level/components-spacing/`), not with ad-hoc margins. It renders as empty vertical space and takes a single `data-size="1".."8"` whose height comes from the responsive `--spacing-page-vertical-*` tokens (mobile→desktop shift is automatic at ≥1280px — no media query, and no Desktop/Mobile variant).

Pick the size by role:

| Size | Use for |
|------|---------|
| **8** (120→160) | Top and bottom padding of a Section. |
| **7** (80→120) | Between components that belong to the same Section but are separate logical blocks — no need to sit close or read as one unit. |
| **6** (64→80) | Between a Heading set to **H1** and the content below it; between independent components within a Section; and as **page top padding** when a page starts with a component *other than* a hero block. (Hero blocks need no top margin when first, and are never wrapped in a Section — see the hero-block note above.) |
| **5** (48→56) | Between a Heading set to **H2** and the content below it. |
| **4 / 3 / 2 / 1** | Tighter, case-by-case gaps. **Size 1 (8px) mimics the layout gutter** — e.g. two stacked 3-card components forming a 3×2 grid use size 1 so the vertical gap equals the horizontal gutter between cards. |

**Two fixed placement rules (always apply):**
- **After the hero block — always a size 8.** The hero is self-sufficient and takes no spacing *above* it when it opens the page. The first body Section still owns a size-8 at its top *inside its band* (on the band's background), opening the body directly below the hero.
- **End of every page — always a size 8.** The last Section owns a size-8 at its bottom *inside its band*, providing the page's bottom padding on the Section's own background.

---

## Icons

- **Use the design system icons only.** Always pick from the 181 icons in `components/atomic/icon/svg/`. Never create a new icon, draw an inline SVG shape, or use an external icon library.
- **Exception — genuinely missing icon.** If a required icon does not exist in the set and no close substitute works, flag it explicitly (e.g., a code comment or a note to the user) rather than silently inventing one. Do not add ad-hoc SVG markup as a workaround.
- **How to use an icon in a component.** Copy the SVG file content and paste it inline. All icon SVGs already use `stroke="currentColor"` / `fill="currentColor"`, so the icon inherits whatever `color` is set on the parent element — no extra CSS needed.

```html
<!-- icon inside a component — inherits color from the parent -->
<span class="btn__icon" aria-hidden="true">
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none" ...>
    <path stroke="currentColor" .../>
  </svg>
</span>
```

---

## Page assembly rules

1. **Reuse first.** When building or modifying a page, always compose it from existing page-level components. Do not create new HTML or CSS for a page row if a matching page-level component already exists.
2. **Pick the specific component, not the generic one.** Match the content's shape to the most structured page-level component that fits it — not the first generic one that could technically hold the text. Use this table to find the shape:

   | Content shape | Preferred component | Not this |
   |---|---|---|
   | Enumerable list of features/benefits/use-cases/steps (many, shallow items) | cards | text-block, image |
   | 2–4 feature highlights, each with a real paragraph and its own visual | zigzag | cards, text-block |
   | Quantified metrics/stats, no single customer story | numbers | case-study, text-block |
   | One customer's metric + narrative + named attribution | case-study | numbers, testimonial |
   | Customer quote is the proof point, metric absent or secondary | testimonial | case-study |
   | Many customer logos, no single attributed story | customer-logos | testimonial, case-study |
   | A handful of topics, each needing an explanation and a distinct visual, browsable in place | accordion-carousel | cards, text-block |
   | Genuine question/answer content | faq | accordion-carousel, text-block |
   | Section intro that leads into more content below it | heading (`data-paragraph`) | cta |
   | Standalone conversion ask, typically closing the page | cta | heading |
   | Single illustrative picture, no accompanying copy | image | zigzag, cards |
   | Pure prose, no stats/list/quote/media pairing | text-block | — |

   **Tie-breakers for overlapping components:**
   - **numbers (`data-case-studies`) vs. case-study.** One customer, one metric, with a narrative paragraph and a named/attributed person → case-study. Multiple stats (2–4), aggregate or company-wide, only needing a logo + CTA footer with no narrative paragraph and no named attribution → numbers with `data-case-studies="true"`.
   - **testimonial vs. case-study.** The quote is the point → testimonial. A metric is the point and the quote/paragraph supports it → case-study.
   - **heading (`data-paragraph`) vs. cta (`data-type="blank"`).** More content follows in the same Section → heading. Nothing follows in the Section (page ends here, or this is the deliberate conversion moment) → cta.
   - **cards vs. zigzag vs. image.** 5+ items with light per-item copy → cards. 2–4 items each needing its own paragraph + CTA + visual → zigzag, stacked with alternating `data-image-position`. A single picture with no copy of its own → image.
   - **mid-page CTA vs. closing CTA.** Both are the cta component, but they are styled as two distinct roles: a mid-page conversion nudge sits on a neutral/light band (title + buttons, no description); the page-closing CTA sits on a saturated band (brand purple or dark) and may carry a short description. Do not give a mid-page CTA the saturated treatment — it dilutes the closing moment.
   - **customer-logos vs. image.** Any strip or wall of partner/customer logos → customer-logos, even when it spans two stacked rows. Never assemble a logo wall from image components.
3. **Generic tier = last resort.** text-block, image, and heading used title-only (no `data-paragraph`) are the least structured components in the set. Reach for them only when content genuinely does not fit any component in the table above — e.g. text-block for pure prose with no stats, list, quote, or media to structure it; image for a standalone illustrative picture with no accompanying narrative; heading title-only as a bare section label with no supporting content. Never default to these because they're the easiest to fill in — check the table first.
4. **Favor minimal, rational layouts.** Use the fewest Sections and page-level components that communicate the content clearly — never add a component, Section, or visual variation purely for variety. When similar content repeats across a page (e.g. two feature call-outs, three CTAs), reuse the same spacing size, media layout, and CTA pattern instead of introducing one-off variations. When two structures would communicate equally well, pick the plainer, more consistent one — clarity and consistency win over decorative complexity.
5. **New page-level component = explicit justification.** A new page-level component may only be created when:
   - the content genuinely does not fit any existing page-level component (different structure, not just different content), or
   - the user explicitly asks for a new one to be created.
6. **New atomic = same rule.** Same justification required before creating a new atomic component.
7. **Group into Sections.** Before styling a page, decide its Section boundaries first — group page-level components into Sections, then apply background-layer or theme contrast between adjacent Sections per the "Sections (page composition)" guidance above.
8. **No one-off styles.** Do not write inline styles or page-specific CSS that duplicates or overrides component behavior. If a component needs a new state, add it to the component's CSS file as a documented property.

---

## Component content & visual patterns

Established patterns reverse-engineered from live smartcat.com pages (evidence and per-page data: `docs/component-usage-patterns.md`). Follow these norms when filling components with content.

### Content norms per component

| Component | Observed norm |
|---|---|
| hero-block | Heading ≤ ~60 chars + one-sentence paragraph; 0, 1, or 2 CTAs depending on the page's conversion intent (when 2: primary demo ask, secondary free-trial). |
| zigzag | Typically a run of **3** with alternating `data-image-position` (singles and pairs occur, trios dominate); each = heading + one 300–500-char paragraph + one visual; no bullet lists inside; per-item CTA rare. |
| cards (big image) | 2–4 cards, paragraph 100–300 chars; the 2-card layout is for heavier story cards that may carry their own CTA. |
| cards (icon) | 5–9 shallow items, paragraph ~120 chars; icons from the design-system set. |
| numbers | 3 stat cards standard (4 max); stat + a 2–6-word label; `data-case-studies` adds quote + customer logo + "Learn more". |
| faq | 5–11 genuine Q/As; titled "FAQs" or "Frequently Asked Questions"; lives in the page-closing region. |
| testimonial / case-study | Always concretely attributed: name + role + company logo (case-study adds the metric as the headline). |
| heading | Section headings use the **largest visual scale** (`data-level="h1"` visual on a semantic `<h2>`), with or without the paragraph (a boolean property of the Heading component) — add the paragraph when the section needs an intro; title-only dominates in practice (~6 in 7). |
| text-block | Footnotes, references, disclaimers at the very bottom of a page — nothing else. |

### Visual type per media slot

Each media slot has an established visual type — pick by slot, and never mix types within one component instance (a cards row is all-icons or all-screenshots, never a blend):

- **Product-UI screenshot** (rounded corners, floating on a soft lavender/purple gradient backdrop) — hero image, cards big-image, video preview.
- **Conceptual illustration** (purple-gradient scene blending product elements: avatars, icon chips, maps, flow diagrams) — zigzag and accordion-carousel images; use a plain UI screenshot instead when the point is the product itself.
- **Icon tile** (small mascot/spot illustration on a lavender rounded tile) — cards small-image.
- **Design-system vector icon** — cards icon variant; only icons from `components/atomic/icon/svg/`.
- **Monochrome customer logo** — customer-logos, numbers, testimonial/case-study attribution; washed-white on color/dark bands, dark monochrome on light bands. Never full-color logo walls.
- **Flat vector diagram** on a light neutral background — the image component (e.g. an integrations wheel).
- **Person photo, circle crop** — testimonial avatars only.

### Section backgrounds beyond the gray layers

The live palette maps exactly onto our tokens — gray layers 0–3 in light mode and dark-mode gray-90/80 cover almost everything. The sanctioned exceptions:

- **Brand-purple band** (`--background-static-brand-*`) — the closing CTA, a showcase stat band, or a logo wall; at most 1–2 per page.
- **Brand-tint band** (light brand-layer-1, ≈purple-10) — soft accent behind a video or a light hero.
- **Alpha tint** (`--background-static-alpha-layer-1`) — card fills on case-study/numbers when a white card is too stark.
- **Radial brand gradients** — hero backgrounds only. **Linear gradients on cards** — a single featured card only.
- Any other accent hue (e.g. the blue CTA on the government page) is a deliberate vertical-specific override — never introduce one without an explicit request.

### Heading component levels

The Heading component's title can be styled as **H1, H2, or H3** via `data-level` on `.heading` (default `h1`), chosen by the level of hierarchy the heading represents:

- **H1** — the top-level page heading, **and Section headings** (live smartcat.com practice: section headings carry the largest visual scale, with or without the paragraph property).
- **H2** — a secondary heading within a Section, or a section heading that must visually defer to a nearby H1.
- **H3** — a sub-block heading within a Section.

`data-level` sets the **visual type style only** — always give the title element the semantically matching tag (`<h1>`/`<h2>`/`<h3>`) for accessibility. A Section heading is therefore typically a semantic `<h2>` styled with `data-level="h1"`.

### Text casing

Never use all-caps for any UI text — not for labels, navigation titles, table column headers, tabs, or any other UI element. This applies to both CSS (`text-transform: uppercase`) and manually uppercased text in HTML.

**Exceptions:** abbreviations, acronyms (e.g. CSS, HTML, API, CTA), and grammatically required contexts (e.g. an acronym that is also the start of a sentence).

Use sentence case for labels, tabs, and most UI copy. Use title case sparingly — only for proper names or top-level navigation items.

**Do not use bold for inline emphasis.** Do not use `<b>`, `<strong>`, or markdown bold (`**word**`) to highlight individual words inside a sentence. If a word needs to stand out, restructure the sentence or use a different typographic level entirely.

**Do not use eyebrow text.** The eyebrow style (`.text-eyebrow`) has been removed from the design system. Do not add it back, do not create ad-hoc eyebrow-style text (small, bold, wide-tracked labels placed above a heading). If a component needs a label above a heading, use a regular paragraph or subtitle instead.

---

## Tech stack

- **HTML** — static files, no build step, no framework.
- **CSS** — token-based system (`main.css` imports all token and component files).
- **Vanilla JS** — interactivity only (tabs, carousels, dropdowns). Never used for rendering markup.

### Design tokens

**There is no JSON and no build step.** The five CSS files in `tokens/` are the single source of truth. Edit values directly in them. When syncing from Figma, update the CSS by hand.

| File | Figma collection | What it holds |
|------|-----------------|---------------|
| `tokens/globals.css` | 01 Globals | Primitive colors (full palette + alpha ramps), spacing scale, border-radius |
| `tokens/colors.css` | 02 Colors | Semantic tokens — reference primitives via `var()`, split into light/dark modes |
| `tokens/sizes.css` | 03 Sizes | Responsive spacing/sizing tokens (mobile base + desktop overrides) |
| `tokens/typography.css` | 04 Typography | Font size, line-height, weight, letter-spacing (mobile base + desktop overrides) |
| `tokens/effects.css` | 05 Effects | Box-shadow tokens |

**Two-layer model.** Component CSS only ever references semantic tokens from `colors.css` (e.g. `var(--background-button-primary-default)`). Semantic tokens point to primitives from `globals.css` (e.g. `var(--color-non-semantic-gray-alpha-90)`). Never skip a layer by hardcoding a primitive directly in a component.

**Alpha colors use 8-digit hex (`#RRGGBBAA`).** Figma exports alpha-ramp variables in this format — the last two digits are the alpha channel (`00` = fully transparent, `ff` = fully opaque). The two alpha ramps in `globals.css` are `--color-non-semantic-white-alpha-*` and `--color-non-semantic-gray-alpha-*`. Do not truncate to 6-digit hex or the alpha is silently lost.

**Dark mode.** `tokens/colors.css` re-declares semantic tokens inside `[data-theme="dark"]` on a page-level component's root or a Section wrapper's root (see "Sections (page composition)" above). Component CSS does not change for dark mode — only the token values change.

---

## Breakpoints & layout grid

This system has **two** breakpoints — components and tokens switch at different widths:

| Boundary | Width | What switches |
|----------|-------|---------------|
| Mobile ↔ tablet | **`@media (min-width: 800px)`** | grid columns (4 → 12); page-level component version |
| Tablet ↔ desktop | **`@media (min-width: 1280px)`** | responsive tokens (`tokens/sizes.css`, `tokens/typography.css`); grid page/column padding |

So tablet (800–1279px) uses the **desktop+tablet layout** but the **mobile/base token values**.

**Authoring rules:**
- **Tokens** are mobile-first: `:root` holds tablet+mobile values; `@media (min-width: 1280px)` overrides for desktop. Never use 769px.
- **Page-level components** are mobile-first: base styles = mobile; one `@media (min-width: 800px)` block = the desktop+tablet version. No other breakpoints.
- **Atomic components** carry **no media queries** — they respond purely through tokens.

**Layout grid** (`base/layout.css`) — grid params live in CSS custom properties (`--grid-columns`, `--grid-gutter`, `--grid-page-padding`, `--grid-column-padding`, `--grid-max-width`) that shift at the two breakpoints:

| | Mobile (<800) | Tablet (800–1279) | Desktop (≥1280) |
|---|---|---|---|
| Columns | 4 | 12 | 12 |
| Gutter | 8px | 8px | 8px |
| Page padding | 16px | 16px | 80px |
| Column padding (inside each cell) | 16px | 16px | 24px |
| Max content width | — | — | 1540px |

**Page nesting:** Page (viewport) → `.section-band` (full-bleed row that carries the Section's background via `data-layer`/`data-theme`; no page padding of its own) → the Section's page-level components, each of which owns its page padding and internally nests `.container` (max-width 1540px, centered) → `.grid` (column grid) → `.grid > *` individual components (column padding inside each, gutters between). Use `data-grid-span="1".."12"` on grid children to set their column span (full-width/stacked below 800px, the given span at ≥800px).

`.section` is the lower-level full-width row that owns **page padding only** (no background) — use it for raw grid content that isn't already inside a padded page-level component. Section backgrounds always come from `.section-band`, never from `.section`. See "Sections (page composition)" above.

---

## Figma property mapping

Figma properties fall into two categories and are handled differently in HTML.

### Visual variant properties → data attributes
Properties that change appearance without changing which elements exist. CSS responds to these.

```html
<!-- Figma: Button · Variant=Primary, Size=L -->
<button class="btn" data-variant="primary" data-size="l">Label</button>

<!-- Figma: Cards · Number of cards=3 -->
<section class="cards-big-image" data-cards="3">…</section>
```

Rules:
- Attribute name = Figma property name, lowercased, spaces → hyphens.
- Attribute value = Figma property value, lowercased, spaces → hyphens.

### Content toggle properties → element presence
Properties like `has-image`, `has-number`, `has-eyebrow`, `has-cta` that show or hide a block of content. Do not use data attributes or CSS visibility for these. Instead, include the element in markup when the property is true; omit it entirely when false.

```html
<!-- has-image=true, has-number=true, has-eyebrow=false, has-secondary-cta=false -->
<div class="card-big-image" data-size="m">
  <div class="card__image"><img src="…" alt="…"></div>
  <div class="card__number">1</div>
  <h3 class="card__heading text-h3">Heading</h3>
  <p class="card__paragraph text-small-reg">Body text</p>
  <div class="card__actions">
    <button class="btn" data-variant="primary" data-size="m">CTA</button>
    <!-- secondary CTA omitted -->
  </div>
</div>
```

---

## CSS conventions

- **Tokens only.** Never use raw color values, raw px sizes, or raw font values in component CSS. Always reference a CSS custom property from the token files.
- **Semantic tokens over primitives.** Prefer `var(--background-button-primary-default)` over `var(--color-non-semantic-gray-alpha-90)`.
- **Component scope.** All component selectors are scoped to the component's root class (`.btn`, `.hero`, etc.). No global element selectors inside component files.
- **Hover/active states** must use the corresponding token (e.g. `--background-button-primary-hover`), never manual opacity or color math.
- **Dark theme** is handled by `[data-theme="dark"]` on a page-level component's root or a Section wrapper's root, which re-declares the relevant tokens. Global dark mode (OS-level) is separate and handled in `tokens/colors.css`.

---

## Component file structure

Each component lives in its own folder with two files:

```
components/
  atomic/
    button/
      button.css    ← styles
      button.html   ← reference template (not an include — copied when building pages)
  page-level/
    cards-big-image/
      cards-big-image.css
      cards-big-image.html
```

**The `.html` file is a reference template**, not a server include or importable module. It shows the full anatomy of the component with all optional elements present and annotated. When building a page, copy the relevant parts and omit unwanted elements.

Pages are standalone HTML files in `pages/` that import `main.css` and contain all markup inline.

Every CSS file opens with a spec comment listing the component name, its Figma source path, and all supported properties:

```css
/* ── Cards / Big image ────────────────────────────────
   Figma: Sections / Cards / Big image
   Component properties (data attributes):
     data-cards : 2 | 3 | 4 | 5-6
   Card properties (element presence):
     .card__image        — include for has-image
     .card__number       — include for has-number
     .card__eyebrow      — include for has-eyebrow
     .card__tag          — include for has-label
     .card__actions      — include for has-cta
     secondary .btn      — include for has-secondary-cta
   Card size is set automatically by data-cards on the component root.
   ──────────────────────────────────────────────────── */
```

---

## Presentation decks

Rules specific to building presentation decks (slide decks) with this design system. Anything not overridden here follows the general rules above — icons, text casing, tokens-only CSS, component content patterns, and Figma property mapping all still apply. Only layout treatment changes.

### Fixed canvas, not responsive

- Every slide is a **fixed 1280×720px canvas** (16:9). Decks have no mobile/tablet/desktop responsive behavior — no media queries, no breakpoint switching. This replaces the "Breakpoints & layout grid" model entirely for decks.
- Colors, typography, radius, and spacing tokens are the same variables used on web (`tokens/*.css`) — decks introduce no new tokens. Values are applied as fixed constants (never a `@media` query).
- Do not reuse the web page grid (`.section` / `.container` / `.grid`, 1540px max-width) as-is for slides — it's sized for a browser viewport and doesn't fit a 1280px canvas.

### Deck layout grid (strict)

These numbers come from measuring the actual Smartcat Google Slides template (exact shape geometry extracted from its PPTX export), not guessed — treat them as fixed, non-negotiable layout rules for every slide:

| Rule | Value | Token |
|---|---|---|
| Page padding (all 4 sides) | **48px** | `--spacing-9` |
| Content width | **1184px** | 1280 − 2×48 |
| Column gutter | **8px** | matches web's `--grid-gutter` |
| Slide title position | flush at the page-padding origin — 48px from top, 48px from left | — |
| Slide title scale | **H1 desktop** (`data-level="h1"` on `heading`) | `--size-h1` / `--line-height-h1` (desktop, 48px/58px) |
| Section-heading / single-statement divider slides | **Display** scale (a whole slide that's just one big headline, no body content) | `--size-display` (desktop, 72px) |
| Big stat figures (a numbers-style slide) | **Display** scale | `--size-display` (desktop, 72px) |
| Heading → content gap | **80px**, applied uniformly regardless of slide type | Components-spacing size-6 (desktop value) |

Every slide is built inside a `.deck-slide` wrapper (fixed 1280×720px box, applies the page padding above). What goes inside it is composed from tokens and atomic components — see "Composing a slide" below.

### Composing a slide — compose freely from tokens and atomic components

**A slide is not "one page-level component in a box."** Build slides by composing from **design tokens and atomic components** upward, and be creative with anything larger. There is no reuse-first rule here and no parallel "deck component" set — do **not** create `components/deck/*`, and do not treat a web page-level component as a fixed unit you must drop in whole.

Concretely, you are free to:
- **Combine components vertically *and* horizontally** — e.g. a row of small cards with a text-block underneath, or two pieces side by side.
- **Mix sub-components** — take individual pieces and place them together, e.g. one card with an icon next to one card with a number; a stat figure beside a quote.
- **Reshape an existing component's internal layout** for the slide — e.g. turn a normally-stacked card into a horizontal card with the icon or image on the left and the text content on the right. Change the arrangement; keep the tokens.

Whatever you build, keep it token-based (colors, type, spacing, radius all from `tokens/*.css`) and assembled from atomic components — that is what keeps a custom slide on-brand. Page-level web components are a convenient *starting point* to reshape, never a constraint.

**Mechanically**, lay a slide out inside `.deck-slide` with a `.grid` row (the same class from `base/layout.css`) below the title and place items with `data-grid-span="1".."12"` — the grid is locked to 12 columns / 24px column padding inside `.deck-slide`, same as web desktop. Stack multiple `.grid` rows for vertical composition.

```html
<div class="deck-slide">
  <div class="heading">…</div>
  <div class="grid">
    <!-- a reshaped horizontal icon-card beside a number-card, 6 + 6 = 12 -->
    <div class="…" data-grid-span="6">…</div>
    <div class="…" data-grid-span="6">…</div>
  </div>
</div>
```

**How to decide what to build for a given slide — and the catalog of recurring slide roles with their composition recipes — lives in `docs/deck-design-brain.md`.** Consult it before designing a deck; extend it as new example slides are provided.

---

## Adding new rules

Append new rules to the relevant section above as conventions are established. Keep each rule short and actionable — describe what to do, not why at length.
