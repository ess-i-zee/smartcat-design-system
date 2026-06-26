# Design System Rules

## Component tiers

### Atomic components (`components/atomic/`)
Small, self-contained UI elements. Examples: button, input, tag, badge, avatar, icon, checkbox, tooltip.
An atomic component does not own a full page row — it is always embedded inside a section or another atomic component.

### Section components (`components/sections/`)
Full-width page rows stacked vertically to form a page. Examples: hero, cta, features-grid, testimonials, logos, pricing, faq.
A section always spans the full page width and handles its own internal layout, spacing, and responsive behavior.

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

1. **Reuse first.** When building or modifying a page, always compose it from existing section components. Do not create new HTML or CSS for a section if a matching section component already exists.
2. **New section = explicit justification.** A new section component may only be created when:
   - the content genuinely does not fit any existing section (different structure, not just different content), or
   - the user explicitly asks for a new section to be created.
3. **New atomic = same rule.** Same justification required before creating a new atomic component.
4. **No one-off styles.** Do not write inline styles or page-specific CSS that duplicates or overrides component behavior. If a component needs a new state, add it to the component's CSS file as a documented property.

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

**Dark mode.** `tokens/colors.css` re-declares semantic tokens inside `[data-theme="dark"]` on the section root. Component CSS does not change for dark mode — only the token values change.

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
- **Dark theme** is handled by `[data-theme="dark"]` on the section root, which re-declares the relevant tokens. Global dark mode (OS-level) is separate and handled in `tokens/colors.css`.

---

## Component file structure

Each component lives in its own folder with two files:

```
components/
  atomic/
    button/
      button.css    ← styles
      button.html   ← reference template (not an include — copied when building pages)
  sections/
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
   Section properties (data attributes):
     data-cards : 2 | 3 | 4 | 5-6
   Card properties (element presence):
     .card__image        — include for has-image
     .card__number       — include for has-number
     .card__eyebrow      — include for has-eyebrow
     .card__tag          — include for has-label
     .card__actions      — include for has-cta
     secondary .btn      — include for has-secondary-cta
   Card size is set automatically by data-cards on the section.
   ──────────────────────────────────────────────────── */
```

---

## Adding new rules

Append new rules to the relevant section above as conventions are established. Keep each rule short and actionable — describe what to do, not why at length.
