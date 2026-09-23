# Design System Rules

## Output formats

This design system serves five output formats:

- **Web-based interfaces** — landing pages and other web UI. Everything in this document, from "Component tiers" through "Component file structure," is scoped to this format, including the two-breakpoint responsive model in "Breakpoints & layout grid."
- **Presentation decks** — slide decks built with this design system. See "Presentation decks" near the end of this document. Decks reuse the same color, typography, radius, and spacing tokens as web — only the layout treatment differs (a fixed slide canvas instead of a responsive page).
- **One-pagers** — fixed-width, variable-height documents (PDF/web factsheets, sales one-pagers). See "One-pagers" near the end of this document. One-pagers also reuse the same tokens as web and decks, on their own fixed-width canvas, they can reuse or reshape web atomic components but never use web page-level components. One-pagers compose from their own dedicated component tier (`components/onepager/`) and atomic web components, if there's a need to create something missing in the dedicated component tier (`components/onepager/`).
- **Documents** — fixed-width, fixed-height, genuinely paginated documents (help articles, workflow guides, reference manuals — printed/exported to PDF as multiple physical pages). See "Documents" near the end of this document. Documents reuse the same tokens as the other three formats, on their own fixed-size page canvas, and — like one-pagers — never reuse or reshape web page-level components: they compose exclusively from their own dedicated component tier (`components/document/`).

- **Social assets** — fixed-size single graphics exported as images for social feeds, or dropped into a web page (campaign posts, link cards, blog headers). See "Social assets" near the end of this document. Social assets reuse the same tokens as the other four formats on their own fixed canvas, and follow the deck model rather than the one-pager/document model: they compose freely from tokens and atomic components, with no dedicated component tier of their own.

Where "Presentation decks," "One-pagers," "Documents," or "Social assets" doesn't override a rule, the general guidance above still applies (icon usage, text casing, tokens-only CSS, etc.) — component content patterns are web-specific; decks, one-pagers, documents, and social assets each carry their own content-treatment reasoning in their respective sections/brain docs. Only layout/responsiveness and component reuse are format-specific.

## Component tiers

### Atomic components (`components/atomic/`)
Small, self-contained UI elements. Examples: button, input, tag, badge, avatar, icon, checkbox, tooltip.
An atomic component does not own a full page row — it is always embedded inside a page-level component or another atomic component.

### Page-level components (`components/page-level/`)
Full-width page rows stacked vertically to form a page. Examples: hero, cta, features-grid, testimonials, logos, pricing, faq.
A page-level component always spans the full page width and handles its own internal layout, spacing, and responsive behavior. It never applies its own side (left/right) padding at any breakpoint — that always comes from the enclosing `.section-band` — but it does still cap and center its own content width by wrapping it in a `.container` div (`max-width: 1540px`, centered). See "Sections" below for the full mechanism, and the hero-block note there for the one exception.

Not to be confused with a **Section** — a composition-level grouping of page-level components; see below.

### Onepager components (`components/onepager/`)
A separate, one-pager-only tier — full rules live in "One-pagers" near the end of this document. Not reused by web pages, and never itself reused/reshaped from web page-level components (the reverse of how decks treat page-level components).

### Document components (`components/document/`)
A separate, document-only tier — full rules live in "Documents" near the end of this document. Not reused by web pages, one-pagers, or decks, and never itself reused/reshaped from web page-level components — same reuse boundary as the onepager tier.

### Sections (page composition)
A Section is not a component tier and has no `.html`/`.css` pair of its own. It's how page-level components are grouped when assembling a page: one Section = one or more page-level components (hero-block, numbers, zigzag, cta, etc.) united into a single logical and visual chunk. There's no fixed minimum or maximum — roughly 1 to 3-4 page-level components per Section is typical.

Grouping into Sections makes long pages easier to digest. Compose every page as a sequence of Sections, not a flat, undifferentiated stack of page-level components.

**Every page is divided into Sections — even a page that is a single Section — and every Section carries an explicit background.** There is no "no-background" section: a Section that does not need contrast still gets wrapped, defaulting to `--background-static-gray-layer-0`. Never let components stack on the browser's default background.

**Note — hero-block is self-sufficient.** The hero-block page-level component is a complete, self-contained Section on its own with its own background — and, since nothing else wraps it, it's also the one page-level component that owns its own side padding directly (`padding-inline: var(--grid-page-padding)`, the same token every `.section-band` uses). Do not wrap it in a `.section-band`, do not group it with other page-level components — place it directly as the page's opening row.

**Note — the 2026 heroes are NOT self-sufficient.** The hero variants in `output/hero-blocks-2026/` are the exception to the exception: they are ordinary page-level components that carry neither a background nor side padding, and each is wrapped in its own `.section-band` (`data-layer="2"`) as a single-component Section. They take no Components spacing inside the band — their vertical rhythm is specified per region by the Figma frames. Build any new 2026 hero variant this way; leave the older `hero-block` component self-sufficient as described above.

**Three ways to visually separate one Section from the next:**
1. **Background-layer contrast (default).** Adjacent Sections use different `--background-static-gray-layer-*` steps, set with `data-layer="0".."3"` on the band (e.g. layer-0 next to layer-1). Identical in light and dark mode.
2. **Light/dark theme contrast.** One Section in light mode, the next in dark, or vice versa. Alternating light and dark Sections is **highly preferable** for a well-structured page — it breaks a long page into clearly digestible chunks the eye can scan. Reach for this as a primary technique, not a rare accent.
3. **Brand-color band (accent, ≤1–2 per page).** A Section on a saturated brand-purple background (`--background-static-brand-*` tokens) for the page's showcase moments — the closing conversion CTA, a stats/proof band, or a logo wall. Never for ordinary feature content.

**Theme rhythm (patterns observed on smartcat.com — follow unless the user directs otherwise):**
- Themes alternate in **bands of 1–4 related components**, not per component — decide the theme per Section, and give every page at least ~3 theme changes so it scans as distinct chapters.
- **Fixed assignments:** FAQ Sections are always light. Social-proof Sections (review walls, rating sliders) are dark. Runs of feature zigzags lean dark. The **page-closing CTA is always saturated** — brand purple or a dark band — while mid-page CTAs stay neutral/light.
- Heroes are dark or light with roughly equal frequency; a canonical page arc is: hero → benefits (often dark) → proof numbers (light or brand band) → features (alternating) → social proof (dark) → resources (light) → FAQ (light) → final CTA (saturated).

**How to give a Section its background, padding, and optionally a dark theme.** Wrap the Section's components in a `.section-band` (see "Breakpoints & layout grid" below) — a full-bleed wrapper that carries BOTH the background AND the responsive side padding (`--grid-page-padding`) for every component inside it. This is the *only* place side padding is ever applied — components themselves never carry `padding-inline` (the one exception is hero-block, see above). Padding on `.section-band` doesn't clip its background: CSS paints the background under the padding by default, so the band still reads as genuinely full-bleed edge-to-edge even though its content is inset. Set the background layer with `data-layer="0".."3"` (omit for the layer-0 default), or `data-layer="brand-gradient"` for a **hero-only** gray→brand-purple ramp (see "Section backgrounds beyond the gray layers" below). Add `data-theme="dark"` to flip the band to dark; the layer background and all child content tokens switch automatically. Put the Section's top and bottom **size-8** Components spacing *inside* the band so the padding sits on the band's own background — a boundary between two bands therefore shows a size-8 on each side, one on each background. Never use a one-off class or inline style for this — `.section-band` plus `data-layer`/`data-theme` is the only mechanism.

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

## Logo

- **Always use the real logo asset.** The Smartcat wordmark lives at `images/smartcat-logo-black.svg` (light backgrounds) and `images/smartcat-logo-white.svg` (dark backgrounds). Reference one of these two files with an `<img>` whenever the logo appears — never render "Smartcat" as styled text in any font, and never recreate the wordmark from scratch.
- **Never add anything to the logo.** No icons, shapes, circles, squares, or other decorative elements attached to or wrapped around the logo mark. Use it exactly as provided, at any size, with nothing added.

---

## Client logos

`images/client-logos/` holds real customer logos as monochrome SVGs — use them for every logo strip, logo wall, or customer-proof row in any format. **Never fill a customer-logo slot with the Smartcat wordmark or a placeholder.**

- When a component needs N logos, take the first N from the **preferred order** in `images/client-logos/README.md` (LG, Clarins, Smith+Nephew, Stanley Black & Decker, L’Oréal, S&P Global, Topcon, Trip.com, Mars, Peloton, …). Use a different customer from the folder only when the content calls for one (an industry page, a named case study).
- Size logos by height and let the width follow; the files are cropped tight to the mark.
- They are black; invert them to white on a dark or brand-purple surface. The `alt` text is the company name.

---

## Promo UI mockups

`images/promo-ui-mockups/` holds real, already-finished promotional screenshots of the newer AI coworker products — ready to drop directly into a build, not raw material that needs compositing. This is different from `skills/smartcat-mockup/mockups/`: that folder holds scene backgrounds and bare UI screenshots for the `smartcat-mockup` skill's Krea compositing pipeline; this one holds finished, on-brand marketing visuals a deck, one-pager, or document can embed as-is.

**Folder structure — one numbered subfolder per product:**

```
images/promo-ui-mockups/
├── 01-ai-chief-of-staff/
├── 02-content-translato-coworker/
├── 03-reviewer-coworker/
└── 04-scorm-studio/
```

Treat this as a live catalog, not a fixed list — a folder added later for another product follows the same `NN-product-name/` convention and the same file-naming rule below.

**Every file is named `<description> -- <tag> - <tag> - <tag>.<ext>`** — a plain-English description of what the image actually shows, then a literal ` -- ` (space, two hyphens, space), then a run of ` - `-separated tags (product area, feature, UI surface). For example:

```
configuring your chief of staff through chat -- chief of staff - settings - chat - personalization.jpg
```

parses to description `configuring your chief of staff through chat` and tags `chief of staff`, `settings`, `chat`, `personalization`.

**Placeholders are encouraged — reserve first, match second, always in that order.** Every format in this system has its own way of reserving room for a screenshot that isn't in hand yet (a dashed image slot in a deck, a `placeholder-screenshot*.png` in a one-pager or document). Keep doing that every time, for every slide, band, or step about a product surface — the absence of a real matching file in `images/promo-ui-mockups/` is never a reason to skip the reservation, and the presence of an expected match is never a reason to skip it either. The two steps are always separate and always in this order:

1. **Reserve.** Build the slide, band, or step with its placeholder, exactly as if `images/promo-ui-mockups/` didn't exist.
2. **Match and replace.** Only once the whole build is drafted, go back through every placeholder as its own pass. For each one, look through the filenames in `images/promo-ui-mockups/` (the description AND the tags, not just the folder name) for the best keyword match to what that placeholder is actually standing in for, and use that file directly if one exists. Split each filename on the first ` -- ` to get the description, then split the remainder on ` - ` to get individual tags; match case-insensitively; a stray typo in a tag (missing space, plural mismatch) is not a reason to discard an otherwise-clear match. If nothing in the folder genuinely matches, leave the placeholder exactly as it is rather than forcing a weak match or inventing a visual — the same rule as any other asset lookup in this system.

Each format skill documents its own mechanics for both steps (see that skill's own instructions).

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
- **`.section-band[data-layer="brand-gradient"]`** — the sanctioned way to give a hero a vertical gray→brand-purple ramp: flat `gray-layer-2` through the upper part of the band, saturated `brand-inverted` at the bottom edge, so a full-bleed hero visual can sit in a purple wash. **Hero sections only** — never an ordinary content Section. Because it lives on the band it spans the full viewport width automatically, which is why a hero's own gradient belongs here and not on a component inside the `.container`. In use by `output/hero-blocks-2026/centered/`.
- Any other accent hue (e.g. the blue CTA on the government page) is a deliberate vertical-specific override — never introduce one without an explicit request.
- **Never a soft-focus gradient "blob," orb, or glow — in any format.** A blurred, soft-edged circular gradient shape — especially one bleeding off a corner like a spotlight or lens flare — is a generic AI-generated-marketing cliché, not a Smartcat pattern. This applies to web, decks, one-pagers, documents and social assets alike. Everywhere a gradient is sanctioned above, it is a flat wash with a sharp edge — a linear ramp or the vertical `brand-gradient` band — never a blurred radial glow. If a layout wants a decorative accent, reach for a flat brand-purple shape or the sanctioned `brand-gradient` band; do not invent a glow.

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

### Punctuation, quotes & dashes

These apply to **rendered copy in every format** — web, decks, one-pagers, documents. They are correctness rules, not style preferences: the wrong character is a typographic error. They do **not** apply to code — see "Where straight characters stay" below.

**Use curly quotes and curly apostrophes. Never straight ones.**

| Use | Character | HTML entity | Never |
|---|---|---|---|
| Opening double quote | `“` U+201C | `&ldquo;` | `"` |
| Closing double quote | `”` U+201D | `&rdquo;` | `"` |
| Opening single / nested quote | `‘` U+2018 | `&lsquo;` | `'` |
| Closing single / nested quote | `’` U+2019 | `&rsquo;` | `'` |
| Apostrophe — contractions, possessives | `’` U+2019 | `&rsquo;` | `'` |

The apostrophe is the **same character as the closing single quote**: `it’s`, `don’t`, `the markets’ own versions`. A straight apostrophe is never correct in prose. Nest quotes double-outside, single-inside: `“He said ‘no’ twice.”`

Either literal UTF-8 characters or the named entities are fine in HTML — pick one and stay consistent within a file. Entities are the safer choice for content that may be copied between tools.

**Em dash: always spaced on both sides.** `approved — but weeks of rebuilding still stand between`. Never set it closed up (`approved—but`), and never substitute a double hyphen (`--`). At most one or two per sentence; more than that means the sentence wants restructuring, not more dashes.

**Pick the right dash — three characters, three jobs.**

| Character | Name | Job | Spacing | Examples |
|---|---|---|---|---|
| `-` U+002D | Hyphen | Joins a compound word or modifier | Closed up | `market-ready`, `best-fit accounts`, `version-control`, `Global-to-Local`, `re-review`, `10+ markets/languages` |
| `–` U+2013 | En dash | A range (it reads as "to"), or a compound where one side is already multi-word | Closed up | `1–2 weeks`, `2024–2026`, `Q1–Q3`, `New York–London` |
| `—` U+2014 | Em dash | A parenthetical break or interruption in a sentence | **Spaced** | `the design is done — but the page is not live` |

Misuses to catch, all of which appear in real source copy:

- Hyphen doing an em dash's job: `design - but weeks` → `design — but weeks`
- Hyphen in a numeric range: `1-2 weeks` → `1–2 weeks`
- Em dash in a range: `1—2 weeks` → `1–2 weeks`
- En dash as a parenthetical break: `approved – but` → `approved — but`
- Unspaced em dash: `cost—faster launches` → `cost — faster launches`
- A minus sign (`−` U+2212), bullet (`•`), or middle dot (`·`) pressed into service as a dash. The middle dot is legitimate only as a list separator inside a run-on line (e.g. `.op-checklist__note`), never as a dash.

**Where straight characters stay.** HTML attributes (`class="btn"`), CSS values (`font-family: "Inter"`), `<code>` spans and code samples, file paths, and URLs all keep straight quotes and plain hyphens. Curly quotes break code, so never "upgrade" them there. These rules govern the copy a reader reads, not the markup they don't.

**Auditing a file.** There is no build step, so check by hand. These four patterns catch nearly every real violation:

```bash
grep -nE "[A-Za-z]'[A-Za-z]|[0-9]-[0-9]| - |[^ ]—|—[^ ]" path/to/file.html
```

Straight double quotes need an eye rather than a pattern, since attributes legitimately use them: search for `"` and confirm each one is inside a tag, not inside copy.

**Rebuilding source content.** When copy comes from a PDF, doc, or transcript, the source will often use straight quotes and hyphen-as-dash. Fixing those on the way in is required, not optional — it is the one class of change always allowed to content that is otherwise reproduced verbatim (see "Content fidelity" under Documents).

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
| Mobile ↔ tablet | **`@media (min-width: 800px)`** | grid columns (4 → 12); grid page padding (16 → 32); page-level component version |
| Tablet ↔ desktop | **`@media (min-width: 1280px)`** | responsive tokens (`tokens/sizes.css`, `tokens/typography.css`); grid page padding (32 → 80); grid column padding |

So tablet (800–1279px) uses the **desktop+tablet layout** but the **mobile/base token values**.

**Authoring rules:**
- **Tokens** are mobile-first: `:root` holds tablet+mobile values; `@media (min-width: 1280px)` overrides for desktop. Never use 769px.
- **Page-level components** are mobile-first: base styles = mobile; one `@media (min-width: 800px)` block = the desktop+tablet version. No other breakpoints.
- **Atomic components** carry **no media queries** — they respond purely through tokens.

**Layout grid** (`base/website-layout.css`) — grid params live in CSS custom properties (`--grid-columns`, `--grid-gutter`, `--grid-page-padding`, `--grid-column-padding`, `--grid-max-width`) that shift at the two breakpoints:

| | Mobile (<800) | Tablet (800–1279) | Desktop (≥1280) |
|---|---|---|---|
| Columns | 4 | 12 | 12 |
| Gutter | 8px | 8px | 8px |
| Page padding | 16px | **32px** | 80px |
| Column padding (inside each cell) | 16px | 16px | 24px |
| Max content width | — | — | 1540px |

**Page padding is the one grid parameter that changes at BOTH breakpoints** (16 → 32 → 80), matching the three Figma variables `Dimension/Page padding/Mobile|Tablet|Desktop`. Every other parameter changes at only one of them. Never hand-roll a tablet side padding — always take it from `--grid-page-padding`.

**Page nesting:** Page (viewport) → `.section-band` (full-bleed row that carries BOTH the Section's background via `data-layer`/`data-theme` AND the responsive page padding — this is the only place page padding is applied) → the Section's page-level components, each of which wraps its own content in a `.container` (max-width 1540px, centered) purely for its own max-width — never its own page padding → `.grid` (column grid, where a component uses one internally) → `.grid > *` individual components (column padding inside each, gutters between). Use `data-grid-span="1".."12"` on grid children to set their column span (full-width/stacked below 800px, the given span at ≥800px).

The lone exception is `components/page-level/hero-block`: since it is never wrapped in a `.section-band` (it forms its own self-sufficient Section), it owns its own page padding directly, using the same `--grid-page-padding` token — so it still picks up the tablet step automatically. See "Sections (page composition)" above. This exception does **not** extend to the 2026 hero exploration in `output/hero-blocks-2026/`, which are deliberately ordinary components inside a band.

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

Pages are standalone HTML files in `output/pages/` that import `main.css` and contain all markup inline.

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
- Do not reuse the web page grid (`.section-band` / `.container` / `.grid`, 1540px max-width) as-is for slides — it's sized for a browser viewport and doesn't fit a 1280px canvas.

### Deck layout grid (strict)

These numbers come from measuring the actual Smartcat Google Slides template (exact shape geometry extracted from its PPTX export), not guessed — treat them as fixed, non-negotiable layout rules for every slide:

| Rule | Value | Token |
|---|---|---|
| Page padding (all 4 sides) | **48px** | `--spacing-9` |
| Content width | **1184px** | 1280 − 2×48 |
| Column gutter | **8px** | matches web's `--grid-gutter` |
| Slide title position | flush at the page-padding origin — 48px from top, 48px from left | — |
| Slide title scale | **H1 desktop** (`data-level="h1"` on `heading`) | `--size-h1` / `--line-height-h1` (desktop, 48px/58px) |
| Section-heading / single-statement divider slides | **Display** scale (a whole slide that's just one big headline, no body content) | `--size-display` (desktop, 64px) |
| Big stat figures (a numbers-style slide) | **Display** scale | `--size-display` (desktop, 64px) |
| Heading → content gap | **80px**, applied uniformly regardless of slide type | Components-spacing size-6 (desktop value) |

**How a slide divides** (a composition rule, not a measured template value). A slide resolves into **at most 3 column bands × 4 row bands** — more than that is two slides. Column divisions come from this set, as `data-grid-span` values: full `12` · `6+6` · `7+5` · `8+4` · `4+4+4` · `9+3`. Every division is a rectangular band on the 12-column grid, inside the 48px padding — there is no diagonal split, and nothing bleeds off an edge.

Every slide is built inside a `.deck-slide` wrapper (fixed 1280×720px box, applies the page padding above). What goes inside it is composed from tokens and atomic components — see "Composing a slide" below.

### Composing a slide — compose freely from tokens and atomic components

**A slide is not "one page-level component in a box."** Build slides by composing from **design tokens and atomic components** upward, and be creative with anything larger. There is no reuse-first rule here and no parallel "deck component" set — do **not** create `components/deck/*`, and do not treat a web page-level component as a fixed unit you must drop in whole.

Concretely, you are free to:
- **Combine components vertically *and* horizontally** — e.g. a row of small cards with a text-block underneath, or two pieces side by side.
- **Mix sub-components** — take individual pieces and place them together, e.g. one card with an icon next to one card with a number; a stat figure beside a quote.
- **Reshape an existing component's internal layout** for the slide — e.g. turn a normally-stacked card into a horizontal card with the icon or image on the left and the text content on the right. Change the arrangement; keep the tokens.

Whatever you build, keep it token-based (colors, type, spacing, radius all from `tokens/*.css`) and assembled from atomic components — that is what keeps a custom slide on-brand. Page-level web components are a convenient *starting point* to reshape, never a constraint.

**Mechanically**, lay a slide out inside `.deck-slide` with a `.grid` row (the same class from `base/website-layout.css`) below the title and place items with `data-grid-span="1".."12"` — the grid is locked to 12 columns with an 8px gutter and **no column padding**, so grid content sits flush to the slide's 48px padding on both edges (aligned with the title's origin). Stack multiple `.grid` rows for vertical composition.

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

## One-pagers

Rules specific to building one-pagers (fixed-width documents — sales/product factsheets, PDF or web) with this design system. Anything not overridden here follows the general rules above — icons, text casing, tokens-only CSS, and Figma property mapping all still apply. Component content patterns and layout are entirely one-pager-specific — see `docs/onepagers-design-brain.md`.

### Fixed width, variable height — not reused web components

- Every one-pager is a **fixed 1280px-wide, auto-height canvas** (`.op-page`, `base/onepagers-layout.css`). Width never changes; height grows with content. A one-pager that stops at its shortest still keeps a **1656px minimum height** — the exact US-Letter (8.5:11) proportion at this width — so a short one-pager still prints/exports at a familiar document ratio. Taller documents are normal and expected.
- Colors, typography, radius, and spacing tokens are the same variables used on web and decks (`tokens/*.css`) — one-pagers introduce no new tokens.
- **Never reuse or reshape web page-level components for a one-pager — not even as a starting point.** This is the opposite of the deck rule. One-pagers compose exclusively from their own dedicated tier, `components/onepager/*` (hero, lead, logo-strip, comparison, callout, flow, numbered-cards, checklist, signals, roster, benefit-cards, steps, quote, impact-tiles, stat-band, rating-tiles, platform-pillars, cta-band, footer), plus raw tokens and the type-style utility classes (`.text-h1`, etc. from `base/type-styles.css`). If a new layout idea is genuinely needed and none of the existing onepager components fit, design a new one in this same tier — don't drop in `hero-block`, `cards`, `numbers`, `testimonial`, or any other web component.
- **Real interactive UI is allowed here — unlike decks.** A one-pager is opened and read as a document, not presented live, so `.btn` (and real links) are correct for CTAs. Every reference one-pager uses a real button for "Schedule a demo," and it must be a link to `https://www.smartcat.com/book-a-demo/` (`<a class="btn" href>`, never `<button>`); the footer URL links to `https://www.smartcat.com`. Both stay clickable in the exported PDF and the Canva copy.
- **Reading measure: ~80 characters.** Every paragraph on a one-pager is capped at `--op-measure` (`base/onepagers-layout.css`). A component that caps its own text points at `var(--op-measure)`, never at a wider pixel value.

### One-pager layout grid

| Rule | Value | Token |
|---|---|---|
| Page width | **1280px**, fixed | — |
| Page height | auto, **1656px minimum** | — |
| Band side padding (all bands) | **48px** | `--spacing-9` (same value validated for the deck canvas) |
| Band vertical padding (default) | **96px** top/bottom | `--spacing-13` |
| Band vertical padding (compact) | **48px** top/bottom — `data-padding="compact"` | `--spacing-9` |
| Compact as a document-wide choice | every content band on an internal reference sheet | see the brain doc's "Internal reference sheet" archetype |
| Heading → content gap within a band | **40px** | `--spacing-8` (`.op-band` is itself a flex column with this gap) |

Every band is a `.op-band` — a full-bleed row that supplies both background (`data-layer` × `data-theme`, mirroring the deck canvas's two composable axes) and the fixed 48px side padding. This is the *only* place side padding is ever applied; onepager components never carry their own side padding. Two components are self-sufficient and carry their own solid brand-purple background directly, exactly like hero-block on web: `.op-hero` (opens every one-pager) and `.op-cta-band` (closes most of them) — never wrap either in `.op-band`. `.op-footer` is also self-sufficient (a fixed near-black bar) and always closes the document.

`.op-band`'s `data-layer` values: `"0"`–`"3"` (gray steps, default `"0"`), `"brand-tint"` (soft accent — reserved almost exclusively for `.op-platform-pillars`), `"brand"` (solid saturated purple — reserved for `.op-stat-band`; self-contained pairing with `--content-static-inverted`, same mechanism as the deck canvas's `data-layer="brand"` — do not combine with `data-theme="dark"`, for the same reason documented in `base/deck-layout.css`).

Section headings inside a band are composed directly from type-style classes, paired with the `.op-heading`/`.op-heading-intro` color utilities (`base/onepagers-layout.css`) rather than a dedicated heading component: `<h2 class="text-h1 op-heading">Title</h2>`.

The shared `.grid`/`[data-grid-span]` system (`base/website-layout.css`) is available inside a band for freeform multi-column composition, scoped the same way the deck canvas scopes it (`--grid-column-padding: 0` so grid content sits flush to the band's own 48px padding). For a plain **pair of columns**, use `.op-columns` (`base/onepagers-layout.css`) instead — `--grid-gutter` is 8px, a page-grid gutter meant to separate cards, and two columns of dense body copy set 8px apart read as one ragged column. `.op-columns` supplies a real 48px column gap, takes `data-split="even"` (default) or `"wide-narrow"` (first column ~1.4×, for a narrative paired with a supporting `.op-callout`), and wraps each multi-block column in `.op-columns__col`.

**Match a card component's fill to its band's layer.** Onepager card components carry a fixed fill and no border, so the band underneath has to differ from it or the cards vanish:

| Component | Card fill | Put it on |
|---|---|---|
| `.op-benefit-cards` | layer-1 | a **layer-0** band |
| `.op-numbered-cards`, `.op-checklist[data-marker="number"]` | layer-0 + shadow | a **layer-1 or higher** band |
| `.op-flow` | layer-0 + shadow, highlight panel brand | any light band |
| `.op-signals` | pink tint | any band |

Because adjacent bands must also contrast with each other, this constrains the whole sequence: a document alternating benefit-cards and numbered-cards bands necessarily alternates layer-0 / layer-1, which is the rhythm to aim for anyway. Two further pairings to avoid: never put `.op-flow` (or anything else that repoints `--content-static-*` to inverted for a brand-purple surface) inside a `data-theme="dark"` band — in dark mode `--content-static-inverted` is near-black, so the purple panel would render black text; and never combine `data-layer="brand"` with `data-theme="dark"`, for the same reason.

**How to decide what belongs in each band — and the catalog of recurring one-pager sections, document archetypes, and their composition recipes — lives in `docs/onepagers-design-brain.md`.** Consult it before building a one-pager; extend it as new reference one-pagers are provided.

---

## Documents

Rules specific to building documents (fixed-size, genuinely paginated PDFs — internal help articles, workflow guides, reference manuals) with this design system. Anything not overridden here follows the general rules above — icons, text casing, tokens-only CSS, and Figma property mapping all still apply.

### Content fidelity

Text content for every page except the cover must match the original source (the PDF, doc, or transcript being rebuilt) exactly — copy it *wording*-for-wording, never paraphrase, summarize, condense, or invent replacement copy. "Verbatim" governs the words, not the characters: casing and punctuation still follow "Text casing" and "Punctuation, quotes & dashes" above, so a source's all-caps heading, straight quotes, inline bold, and hyphen-as-dash are all corrected on the way in. That is the only class of change allowed without asking. The cover page (title, accent word, audience line, subtitle, TOC labels) is the one place original wording is expected, since the source material rarely has a cover-page-shaped opening to draw from. Only deviate from verbatim source content elsewhere when the user explicitly asks for it (e.g. "adjust the content," "use this text but feel free to change it where needed for the design") — absent that instruction, default to keeping the original content intact.

### Fixed width AND height, genuinely paginated — not reused web/onepager components

- A document is the one format that is **truly paginated**: it prints/exports as a sequence of discrete physical pages, each repeating a running header and footer — unlike a one-pager (single scrolling canvas) or a deck (independent slides with no running header/footer). Every physical page is a `.doc-page` (`base/document-layout.css`): a **fixed 1290×1670px canvas** (≈ US-Letter 8.5:11 proportion at this width). Both width and height are fixed — content is authored to fit within one page's content area, not left to grow it.
- Colors, typography, radius, and spacing tokens are the same variables used on web, decks, and one-pagers (`tokens/*.css`) — documents introduce no new tokens.
- **Never reuse or reshape web or onepager components for a document — not even as a starting point.** Documents compose exclusively from their own dedicated tier, `components/document/*` (doc-hero, doc-meta, doc-steps, doc-callout, doc-screenshot, doc-divider, doc-pullquote, doc-footnotes, doc-chapter-opener, doc-timeline, doc-table), plus raw tokens and the type-style utility classes (`.text-h1`, etc. from `base/type-styles.css`). If a new content shape is genuinely needed and none of the existing document components fit, design a new one in this same tier.
- **Screenshots are kept as-is, but always framed in a container.** A document's whole point is often to document a real product UI — never redraw or mock up a screenshot from scratch; embed the original image (including any pre-existing callout arrows/highlights) inside `.doc-screenshot`, which always wraps it in the `.doc-screenshot__container` (tinted background, padding, centers the image) — see "Image containers" below.
- **Real interactive UI is allowed here — unlike decks.** A document is read like a printed manual, not presented live.
- **Body-text color.** Flowing prose/step copy (`.doc-steps__text`, `.doc-heading-intro`, `.doc-callout__item-text`) is `content-static-secondary`, not primary — it should read a shade lighter than headings. Short data/label text (`.doc-meta__value`, pills, `.doc-callout__term`) stays `content-static-primary` — those aren't prose.

### Image containers

Every `.doc-screenshot` wraps its bordered image frame in a `.doc-screenshot__container`. The **container** caps at **1080px max-width** and centers itself on the page (`margin-inline: auto`) — it no longer stretches to the full content width, regardless of how wide its wrapping context is (a direct `.doc-content` child or a step's full-width breakout). It has `background-static-gray-layer-2`, `40px` vertical padding (`--spacing-8`) and **no horizontal padding**, `16px` border-radius (`--radius-5`), and `display:flex; justify-content:center` so the frame inside is always horizontally centered. There is a single, uniform treatment for every screenshot regardless of what it depicts (a full page, a modal, a small detail crop) — no size variant to choose between. The frame itself keeps its existing hairline border + 8px radius + soft shadow; never crop or re-annotate the source screenshot.

**Sizing the image inside the frame** — the frame never distorts an image or stretches it past its own resolution just to fill the container:
1. **Always keep the source image's original proportions.** Never stretch or squash an image to a different aspect ratio.
2. **If the source image is smaller than 40px on both sides, display it at 2x** (double its original pixel dimensions) — a sub-40px crop is otherwise too small to read.
3. **For every other image, use `width: auto`** (not a forced `100%`) — the frame sizes to the image's own resolution rather than stretching to fill the container's width; proportions stay intact, and the container's `justify-content: center` still centers it horizontally.
4. **960px is a ceiling on the frame's width, never a target.** An image already narrower than 960px stays at its own size (per rule 3) — it is never stretched up to meet the cap; only an image at or above 960px gets capped down to it.

### Cover page

Every document defaults to opening with a **left-aligned, dark-mode title page** — skip it only when a specific document has an explicit reason not to. It's `.doc-hero` (`components/document/doc-hero`) alone inside a `.doc-page[data-theme="dark"]`: no `.doc-header`/`.doc-content`/`.doc-footer` on this page at all. This is the tier's one self-sufficient element, exactly like `.op-hero` (one-pagers) and `hero-block` (web) — it owns its own full-page layout directly and is never wrapped in the normal header/content/footer structure.

**Layout, top to bottom, each pinned a fixed distance below the previous block (remaining space settles at the bottom):**
1. **Topbar** — the Smartcat logo (white variant, `images/smartcat-logo-white.svg` — see "Logo" above) top-left, and an optional tag pill (`.doc-hero__tag`, e.g. "Internal guide" — reuse the same wording as `.doc-header__tag` on the content pages for continuity) top-right.
2. **Title block**, 160px below the topbar — the document name (`.doc-hero__title`, `text-display`), with an optional key word/phrase wrapped in `.doc-hero__title-accent` to render it in brand purple (a deliberate display-title accent, not prose emphasis — the "no bold inline emphasis" rule is about body copy). Below it, an optional audience/client line (`.doc-hero__meta`, e.g. "For Linguists") with the audience name wrapped in `.doc-hero__meta-accent` (same brand purple). Below that, an optional 1–3 line description (`.doc-hero__subtitle`).
3. **Table of contents**, 96px below the title block — optional, include when the document has a clean set of top-level (H1) sections worth listing. `.doc-hero__toc` holds one or two `.doc-hero__toc-column`s, each a plain list of `.doc-hero__toc-item`s (a two-digit `.doc-hero__toc-number` in brand purple + a `.doc-hero__toc-label`, bottom-divided rows). Split sections evenly across columns in reading order (column 1 gets the first half, column 2 the second) — never interleave.

Every color in `.doc-hero` is a semantic token, already re-declared under `[data-theme="dark"]` — dark mode is free.

No page number is shown on the cover (no footer); the next physical page (the first with a `.doc-header`/`.doc-footer`) is numbered **2**, since the cover still counts toward the total page count.

### Section structure

A document's top-level Sections don't need a fresh page each — continuing a new Section on the *same page* as the previous one's ending is fine, and preferred whenever it fits. When it does, mark the boundary with a `.doc-divider` (`components/document/doc-divider`): it wraps the new Section's `<h1 class="text-h1 doc-heading">` directly, with **120px** between the previous section's last block and the divider line, then **another 120px** between the line and the H1 inside it. Skip the divider only when the new Section instead opens a *fresh page* — the page break already separates them, and a divider with nothing above or below it on the page is a broken pattern.

H2/H3 headings (subsections within a Section, no divider) get a proportional top margin instead: **80px** total above an H2, **56px** above an H3. Mechanically, `.doc-content`'s ambient inter-block gap is 32px (`--spacing-7`) — the H2/H3 rules add a token-clean top-up on top of that ambient gap to reach their total (80 = 32 + `--spacing-9`; 56 = 32 + `--spacing-6`). The divider's own spacing is computed the same way but expressed as `calc(--spacing-14 - --spacing-7)`, since 120 total minus the 32px ambient gap (88px) isn't itself a scale value. A heading that opens the page itself (nothing above it to separate from) is exempted automatically.

### Continuing content across pages

When a Section's content (a step list, a long paragraph, a run of screenshots) doesn't fit on one physical page, split it at a clean point and just continue it in `.doc-content` on the next page — **never add a label like "[Section name] — continued" at the top of the continuation page**, or anything else that announces "this is a continuation." The running `.doc-footer__title` already carries the document's identity on every page; content simply flows from page to page with no re-announcement needed.

### Callout variants

`.doc-callout` (`components/document/doc-callout`) has three independent, combinable variants on top of the base gray tip box:
- **`data-color`** — `gray` (default) | `blue` | `orange` | `pink`. Tints the box background with `background-static-{color}-layer-1`, mirroring `.doc-meta__pill`'s color system exactly. Use it to group callouts by category (a tip vs. a warning vs. a shortcut list) — not decoratively.
- **Leading icon** — wrap the heading in `.doc-callout__head` alongside a `.doc-callout__icon` (a single 20×20 inline svg, `stroke="currentColor"`, `aria-hidden="true"`). Omit the wrapper entirely when there's no icon — a bare `.doc-callout__heading` still works on its own.
- **`data-marker="checkbox"`** — swaps every `.doc-callout__item`'s dot bullet for an outlined square, for a scannable checklist. Default (or `data-marker="dot"`) keeps the bullet.

### Icon-led step lists

`.doc-steps` (`components/document/doc-steps`) defaults to a solid numbered badge (`.doc-steps__number`, brand-inverted background, white numeral) for literal ordered sequences. `data-marker="icon"` on `.doc-steps` swaps every step's badge to a light `background-static-brand-layer-1` circle holding an 18×18 inline svg instead of a numeral — use it for an unordered row list (options, checks) where the items aren't a literal 1-2-3 sequence; keep the numbered badge for anything the reader actually performs in order.

### Table-of-contents page numbers and sub-sections

`.doc-hero__toc-item` (`components/document/doc-hero`) wraps its number+label row in `.doc-hero__toc-item-main`, with an optional trailing `.doc-hero__toc-page` right-aligned via the label's `flex: 1 1 auto`. A top-level entry can carry one or more nested `.doc-hero__toc-subitem` rows directly inside the same `.doc-hero__toc-item` — each is indented 48px, with a dotted leader (`.doc-hero__toc-subitem-leader`) filling the gap before its own `.doc-hero__toc-subitem-page`. Omit page numbers or subitems on any entry that doesn't need them; the bottom divider follows the whole item (main row + subitems), not just the main row.

### Pull-quotes

`.doc-pullquote` (`components/document/doc-pullquote`) is a lightweight left-border rule around a large `.doc-pullquote__text` (apply a heading type-style class — `text-h2`/`text-h3`) in `content-static-primary`, with an optional `.doc-pullquote__attribution` below. No quote-mark glyph — decorative glyph ornaments are a dropped pattern for this tier. Reserve it for a genuine pulled-out statement, not as a generic "important paragraph" box (that's `.doc-callout`).

### Footnotes

`.doc-footnotes` (`components/document/doc-footnotes`) is a closing citations/notes list: a top divider rule above a small (`text-caption-reg`), `content-static-tertiary` numbered list (`.doc-footnotes__item`, `.doc-footnotes__number`). Place it at the end of the section or document the notes belong to — never as its own standalone page.

### Chapter openers (long, multi-part documents)

`.doc-chapter-opener` (`components/document/doc-chapter-opener`) is a second self-sufficient element, alongside `.doc-hero` — same rule: placed directly as a `.doc-page`'s only child, never wrapped in `.doc-header`/`.doc-content`/`.doc-footer`. Use it only for long, multi-part documents (roughly 30+ pages across several distinct parts) to open each part; for anything shorter, a `.doc-divider` is enough. Unlike `.doc-hero` (top-pinned, once per document), its title block (`.doc-chapter-opener__label` + `__title`, `text-display`) vertically centers on the page — the conventional book/report part-opener placement — and it carries its own top-right page number (`.doc-chapter-opener__pagenum`), since it has no `.doc-footer`. An optional floating `.doc-chapter-opener__summary` card (`background-static-gray-layer-1`) can preview what the part covers. Place it on a dark-themed page (matching the cover) or a light page for a brand-tint variant.

### Timelines

`.doc-timeline` (`components/document/doc-timeline`) is a horizontal milestone/roadmap strip — equal-width `.doc-timeline__milestone` columns (CSS grid), each a pill label (`.doc-timeline__pill`) above a dot (`.doc-timeline__dot`) sitting on a continuous connecting line, with a boxed `.doc-timeline__caption` below. Use it for a small number of milestones (roughly 3–5); beyond that, a plain list reads better.

### Tables

`.doc-table` (`components/document/doc-table`) is a comparison / reference table — a row-label column plus two or more value columns, hairline-ruled with no fill. It is authored as a real `<table>` (a document is printed and read like a manual, so the semantic element and its header cells are correct), and it sits at **960px**, matching `.doc-divider`, because a 3-column table doesn't fit the 800px text column. `data-columns="3"` narrows the row-label column for a third value column.

Reach for it only when the content is genuinely tabular. A bulleted set of tips is `.doc-callout`; an ordered procedure is `.doc-steps`.

### Titled steps

`.doc-steps__step` may open its body with a `.doc-steps__heading` (H4 scale, `content-static-primary`) above `.doc-steps__text` — for a step that names itself before explaining itself (a titled practice or option). Omit it for a bare instruction; the heading carries the badge-alignment padding itself, so a titled step still optically centers against its number.

### Document layout grid

| Rule | Value | Token |
|---|---|---|
| Page width | **1290px**, fixed | — |
| Page height | **1670px**, fixed | — |
| Header height (logo, repeats every page) | auto (~68px) | `--spacing-6` block padding |
| Footer height (doc title + page number, repeats every page) | auto (~48px) | `--spacing-5` block padding |
| Content side padding | **48px** | `--spacing-9` |
| Content top/bottom padding | **32px** | `--spacing-7` |
| Gap between components in the content area | **32px** | `--spacing-7` (`.doc-content` is a flex column with this gap) |
| Text column max-width | **800px**, fixed, centered (`margin-inline: auto`) | — |
| Divider max-width | **960px**, fixed, centered | — |
| Screenshot frame max-width | **960px** ceiling only — `width:auto`, never stretched up to it; proportions always preserved | — |
| Screenshot @2x threshold | source image **under 40px on both sides** → display at 2x its original size | — |
| Screenshot container max-width | **1080px**, centered on the page (`margin-inline: auto`) | — |
| Screenshot container background | `background-static-gray-layer-2` | — |
| Screenshot container padding | **40px** top/bottom, **0** left/right | `--spacing-8` |
| Screenshot container radius | **16px** | `--radius-5` |
| Gap between numbered steps | **24px** | `--spacing-6` |
| Section-divider spacing (each side) | **120px** total (32 ambient gap + 88 top-up) | `calc(--spacing-14 - --spacing-7)` |
| H2 top margin | **80px** total (32 ambient gap + 48 top-up) | `--spacing-9` top-up |
| H3 top margin | **56px** total (32 ambient gap + 24 top-up) | `--spacing-6` top-up |
| Callout leading icon size | **20×20px** | — |
| Icon-led step badge icon size | **18×18px** | — |
| Pull-quote left border + inset | 1px rule, **24px** text inset | `--spacing-6` |
| Chapter-opener summary card gap below title | **96px** | `--spacing-13` |
| Timeline dot size | **10×10px** | — |
| Table width | **960px**, centered (matches the divider) | — |
| Table row-label column | **160px** (**140px** at `data-columns="3"`) | — |



Every page is a `.doc-page` containing, in order: `.doc-header` (self-sufficient — Smartcat logo, flush top, bottom divider), `.doc-content` (the page's body — fixed side padding, vertical flex rhythm, `min-height: 0` + the page's own `overflow: hidden` so authored content is trusted to fit rather than silently overflowing into the next page), and `.doc-footer` (self-sufficient — document title left, page number right, top divider). `.doc-header` and `.doc-footer` repeat identically on every page, exactly like a printed manual's running header/footer. (The cover page is the one exception — see "Cover page" above.)

**Pagination is authored, not automatic.** Because height is fixed, decide page breaks by hand: a `.doc-page` never contains more than its content area can hold (~1490px at the default padding). Never split a `.doc-steps__step` or a `.doc-screenshot` across two pages — move the whole block to the next page instead. `base/document-layout.css` sets `break-after: page` on every `.doc-page` (removed on the last) so printing/exporting the HTML produces one physical PDF page per `.doc-page`, with `@page { size: 1290px 1670px; margin: 0 }` under `@media print`.

Section headings inside the content area are composed directly from type-style classes, paired with the `.doc-heading`/`.doc-heading-intro` color utilities (`base/document-layout.css`), the same mechanism as the one-pager tier's `.op-heading`: `<h2 class="text-h2 doc-heading">Title</h2>`.

## Social assets

Rules specific to building social assets (fixed-size single graphics exported as images — campaign posts, link cards, blog headers) with this design system. Anything not overridden here follows the general rules above — icons, text casing, punctuation, tokens-only CSS, and Figma property mapping all still apply.

### Fixed canvas, three formats — composed freely, no component tier

- Every asset is one `.social-canvas` (`base/social-layout.css`) at a fixed native export size, chosen with `data-format`:

  | `data-format` | Size | Placement |
  |---|---|---|
  | `square` | **1080×1080** | Instagram / LinkedIn feed post |
  | `portrait` | **1080×1350** | Instagram / LinkedIn 4:5 feed post |
  | `wide` | **1200×675** | LinkedIn / X link card, blog header |

  Author at these sizes — never at a scaled-down proxy. Export at 1x or 2x as the placement needs.
- Colors, typography, radius, and spacing tokens are the same variables used everywhere else (`tokens/*.css`) — social assets introduce no new tokens.
- **Social assets follow the deck model, not the one-pager/document model.** There is no `components/social/*` tier and you must not create one. Compose each asset from raw tokens, the type-style utilities (`base/type-styles.css`), and **atomic components** (`.btn`, `.badge`, icons, text fields) — reshaping an atomic's internal layout for the canvas is fine, changing its tokens is not.
- **Never reuse web page-level components, or onepager/document components, on a social canvas.** A 1080px canvas is not a page row; `hero-block`, `cards`, `numbers`, `.op-*` and `.doc-*` all assume a width and a rhythm this canvas doesn't have.
- **Campaign shapes live with the campaign.** A social asset almost always needs some composition CSS (a card grid, a stat row, a two-up comparison). Put it in a single campaign stylesheet next to the assets — `output/social/<campaign>/<campaign>.css` — with every class namespaced to the campaign and every value a token. Do not push campaign shapes up into `base/social-layout.css`; that file owns the canvas and its furniture, nothing else. This mirrors `output/hero-blocks-2026/centered/centered.css`.
- **One asset per file.** Each `.html` holds exactly one `.social-canvas`, so a full-page screenshot is the finished asset with nothing to crop. Add an `index.html` contact sheet linking them when a campaign runs to more than a handful.
- **Assets are static.** They become flat images, so nothing is interactive: no JS, no hover states to design for, no real links. A `.btn` on a social canvas is a picture of a button — render it as a `<span class="btn">`, never a `<button>` or `<a>`, so it is never focusable or announced as an interactive control.

### Social canvas grid

| Rule | Value | Token |
|---|---|---|
| Canvas padding — `square` / `portrait` | **64px** | `--spacing-11` |
| Canvas padding — `wide` | **48px** | `--spacing-9` (the deck canvas value) |
| Region gap — `square` / `portrait` | **64px** minimum | `--spacing-11` |
| Region gap — `wide` | **40px** minimum | `--spacing-8` |
| Region gap — `data-rhythm="tight"` | **40px** minimum | `--spacing-8` |
| Column grid inside the canvas | 12 columns, 8px gutter, no column padding | `--grid-gutter` |
| Logo height | **28px** | — |

Padding differs by format deliberately: `square` and `portrait` are read on a phone at thumbnail size and need the wider margin to survive platform cropping, while `wide` is a landscape 16:9 canvas read on a desktop and takes the deck's measured 48px.

The canvas is a flex column of three optional regions — `.social-canvas__topbar` (pinned top), `.social-canvas__body` (`flex: 1`, absorbs the slack), `.social-canvas__footer` (pinned bottom). The canvas gap is therefore a *minimum* separation, not a fixed one. Use `data-rhythm="tight"` when the body is a dense grid that needs the height back.

**The desktop typography tier is pinned on `.social-canvas`.** The deck, one-pager and document canvases are 1280–1290px wide, so any window showing one is already past the 1280px token breakpoint; a 1080px social canvas is not, and would otherwise pick up the mobile type scale and shrink every headline by a third. Never rely on the ambient viewport for type size here.

### Backgrounds

Same two composable axes as the deck canvas and the one-pager band — `data-layer` picks the surface, `data-theme="dark"` flips the token set underneath it:

- **`data-layer="0".."3"`** — the gray steps, in either theme. The everyday background.
- **`data-layer="brand"`** — solid saturated purple, self-contained with `--content-static-inverted`. Never combine with `data-theme="dark"` (same reason documented in `base/deck-layout.css`).
- **`data-layer="brand-gradient"`** — a soft purple bloom over the base surface; both stops are tokens, so it reads as a pale lavender wash in light mode and a deep purple glow on near-black in dark. This is the campaign's showcase background — the opener, the offer, the closing card. Not a default, and never on more than a few assets in a set.

**Alternate light and dark across a campaign set**, the same way Sections alternate on a web page: a run of assets that are all light reads as one undifferentiated block in a feed. Decide the theme per asset by the role it plays — the problem/tension assets go dark, the product and offer assets go light.

### Content treatment

- **Headline accent.** A social headline usually turns on one word or phrase. Wrap it in `.social-canvas__accent` to set it in brand purple — the same deliberate display accent as `.doc-hero__title-accent` on a document cover. This is a title treatment, not prose emphasis, so it is not covered by the "no bold inline emphasis" rule. Never use a gradient fill on text: the system sanctions brand gradients as backgrounds only.
- **Headline scale.** Display for the one-line statement assets, H1 for a headline that shares the canvas with real content. Both are pinned to their desktop values on the canvas.
- **Sign-off.** Close an asset with `.social-canvas__footer` — the real Smartcat wordmark (`images/smartcat-logo-black.svg` on light, `-white.svg` on dark and brand) opposite a one-line `.social-canvas__note`. Keep the note to a short sentence; it is the asset's caption, not a paragraph.
- **All-caps and eyebrows are banned here too.** Social source material is full of both — set-tinted category labels, table column headers, and small tracked-out lines above a headline. Convert every one of them to sentence case, and rebuild an eyebrow as an ordinary label or paragraph. See "Text casing" above.
- **Product UI is redrawn from atomics, not screenshotted.** Unlike a document — which embeds the real screenshot — a social asset showing product UI is an illustration of the product, sized and simplified for a thumbnail. Build it from `.badge`, `.btn`, `.text-field` and tokens, and keep it to the few elements that carry the point.

---

## Adding new rules

Append new rules to the relevant section above as conventions are established. Keep each rule short and actionable — describe what to do, not why at length.
