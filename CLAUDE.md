# Design System Rules

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

**Two ways to visually separate one Section from the next:**
1. **Background-layer contrast (default).** Adjacent Sections use different `--background-static-gray-layer-*` steps, set with `data-layer="0".."3"` on the band (e.g. layer-0 next to layer-1). Identical in light and dark mode.
2. **Light/dark theme contrast.** One Section in light mode, the next in dark, or vice versa. Use as an occasional accent, not the default for every boundary.

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

**Practical guidance:** aim for at least one dark-mode Section per page, unless the user specified an all-light or all-dark page.

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
2. **New page-level component = explicit justification.** A new page-level component may only be created when:
   - the content genuinely does not fit any existing page-level component (different structure, not just different content), or
   - the user explicitly asks for a new one to be created.
3. **New atomic = same rule.** Same justification required before creating a new atomic component.
4. **Group into Sections.** Before styling a page, decide its Section boundaries first — group page-level components into Sections, then apply background-layer or theme contrast between adjacent Sections per the "Sections (page composition)" guidance above.
5. **No one-off styles.** Do not write inline styles or page-specific CSS that duplicates or overrides component behavior. If a component needs a new state, add it to the component's CSS file as a documented property.

---

## Typography & content conventions

### Heading component levels

The Heading component's title can be styled as **H1, H2, or H3** via `data-level` on `.heading` (default `h1`), chosen by the level of hierarchy the heading represents:

- **H1** — the top-level page heading.
- **H2** — a Section heading.
- **H3** — a sub-block heading within a Section.

`data-level` sets the **visual type style only** — always give the title element the semantically matching tag (`<h1>`/`<h2>`/`<h3>`) for accessibility.

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

## Adding new rules

Append new rules to the relevant section above as conventions are established. Keep each rule short and actionable — describe what to do, not why at length.
