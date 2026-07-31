# Component usage patterns — evidence from smartcat.com (July 2026)

Source: structural analysis of 10 live smartcat.com pages (raw HTML + builder payload props):
`/ai-agents/`, `/enterprise/`, `/ai-agents/learning-content-agent/`, `/ai-agents/ai-content-marketing/`,
`/ai-agents/quality-assurance-agent/`, `/ai-course-creator/`, `/ai-agents/elearning-software/`, `/figma/`,
`/ai-translation-software-for-schools/`, `/government-translation/`.

This file holds the evidence behind the usage rules in `CLAUDE.md` ("Page assembly rules",
"Sections", "Component content & visual patterns"). Update it when re-auditing the live site.

## 1. Component frequency and content shapes

| Live component (builder key) | n | Our component | Typical content shape observed |
|---|---|---|---|
| heading | 64 | heading | Title-only, largest visual scale (`title_size:1`) even for mid-page section headings; paragraph variant rare (~9/64) |
| cards / cards-small-image / cards-icon / cards-carousel | 48 | cards | 2–4 big-image cards (para 100–300 chars); 3–4 small-image cards; 5–9 icon cards (para ~120 chars, shallow); 8–9 items → carousel behavior |
| cta | 19+ | cta | Two distinct roles: mid-page "blank" (title + 2 buttons, neutral bg) and page-closing conversion (saturated bg, optional description) |
| zigzag | 17+ | zigzag | Almost always a run of exactly 3, `data-image-position` alternating; heading + 300–500-char paragraph + one visual; no bullet lists; item CTA rare |
| spacing | 312 | components-spacing | Distribution: size 8 ×163, 6 ×69, 1 ×40, 5 ×20, 7 ×9, 4 ×8 — matches our size-role table |
| numbers | 9 | numbers | 3 stat cards standard (one 4); stat + 2–6-word label; optional quote + customer logo + "Learn more" CTA (= our `data-case-studies`) |
| faq | 9 | faq | 5–11 Q/A items, titled "FAQs"/"Frequently Asked Questions"; always light; always in the page-closing region |
| hero (4 variants) | 10 | hero-block | Heading ≤60 chars + 1-sentence paragraph + exactly 2 CTAs (primary "Book a demo", secondary free-trial); product-UI screenshot or interactive widget |
| testimonial | 6 | testimonial | Quote + name + role + company logo; 4/6 dark |
| customer-logos (+two-lines) | 5 | customer-logos | 7–10 monochrome logos, directly under hero, light gray band |
| image-chain | 10 | (customer-logos / image) | 2 stacked rows × 6 washed-white logos on deep-purple brand band — a logo wall, built from image rows |
| tabsNew-seo (carousel-tabs) | 3 | accordion-carousel | 4–5 tabs, each title + linked paragraph + visual; 2/3 dark |
| case-study-single | 2 | case-study | 1 metric + caption + named person + logo + CTA; light, alpha-tint card `#3C445A0A` |
| g2Slider + reviews | 4+4 | (no equivalent) | Paired dark social-proof band: big claim + rating badges, then 3 G2 quote cards with star ratings |
| calc-widget, zero (embeds), video, image-single, text | ~10 | (partial) | Interactive calculator on brand-purple band; Arcade demo embeds; video with UI-composition preview; single diagram image; rich-text = footnotes/references only |

## 2. Dark/light theme logic observed

- Pages alternate in **thematic bands of 1–4 components**, not per-component. Every page has 3+ theme flips.
- **Stable assignments:** FAQ always light (9/9). G2 social proof always dark (8/8 blocks). Zigzag benefit trios predominantly dark (13/17). Page-closing CTA is always saturated — brand purple `#670FDA` (5×), near-black violet `#0F0D19`/`#1A1824` (6×), or blue `#066FED` (1×, vertical-specific). Mid-page CTAs are neutral/light (white, gray-5, gray-10 tiers).
- Heroes: 6 dark / 4 light — both common; dark heroes use radial brand gradients over near-black.
- Canonical page arc: hero → (benefits, often dark) → proof numbers (light or brand-purple band) → feature sections (mixed, alternating) → social proof (dark) → resources/related (light) → FAQ (light) → final CTA (saturated).

## 3. Background colors observed (beyond black/white)

| Observed hex | Where | Token mapping |
|---|---|---|
| `#F4F5F8`, `#F0F1F4`, `#E5E5EA` | light section bands (logos, FAQ, heading bands, text) | gray-5/10/20 = `--background-static-gray-layer-1/2/3` (light) — exact match |
| `#1A1824`, `#1F1D2A` | dark section bands / dark cards (zigzag, tabs, g2) | gray-90/80 = dark `--background-static-gray-layer-0/1` — exact match |
| `#670FDA` | final CTA band, calculator band | purple-80 (brand); nearest semantic: `--background-static-brand-inverted` |
| `#4300AE` | deep-purple showcase band (numbers, logo walls, testimonials-with-numbers) | off-ramp (between purple-90 and purple-100) — treat as brand band, use brand tokens |
| `#066FED` | government page final CTA | blue-80 — vertical-specific accent, one page only |
| `#F3F0FB` | video band, light hero tint | ≈ purple-10 (`--background-static-brand-layer-1` light) |
| `#3C445A0A` | case-study / numbers card tint | alpha tint ≈ `--background-static-alpha-layer-1` |
| radial gradients (`#D600FE→#4C00E2`, `#7615FF→#100D17`, `#29A5FF→#103EB6`) | hero backgrounds only | brand gradients — hero-only device |
| `linear-gradient(#35006B→#161424)`, `linear-gradient(#E5E5EA→#BB9FFF)` | featured card / one cards band | gradient accents — featured-content-only device |
| `#0F0D19`, `#171424`, `#171622`, `#161424`, `#100D17`, `#201c2c` | some dark bands/cards | off-token hand-tuned near-blacks; our equivalent is gray-90/100 |

## 4. Visual types per component slot

Sampled and visually classified from live assets:

| Slot | Visual type |
|---|---|
| hero image, cards big-image, video preview | **Smartcat product-UI screenshot** — rounded corners, floating on soft lavender/purple gradient backdrop |
| zigzag image, accordion-carousel image | **Conceptual illustration** — purple-gradient scenes blending product elements (avatars, icon chips, maps, flow diagrams); sometimes a UI screenshot when the point is the product itself |
| cards small-image | **Icon tile** — 3D pastel mascot icon or flat gray spot-illustration on a lavender rounded tile (dark variant: gradient shield/badge in dark circle) |
| cards icon | **Design-system vector icons** — builder references the same `icon-24-*` names as our icon set |
| customer-logos, image-chain, numbers logo, testimonial logo | **Monochrome customer logos** — washed white on color bands, dark monochrome on light bands; never full-color logo walls |
| image (single) | **Flat vector diagram** (e.g. integration wheel with partner logos), light neutral background |
| testimonial avatar | Real person photo, circle crop |
| g2 slider | Rating badge images |

Never mixed within one component instance: a cards row is all-icons or all-screenshots or all-mascots, never a blend.

## 5. Known deviations in existing pages

`output/pages/content-operations-enterprise-ai.html` predates these rules and deviates in three ways
(acceptable as-is; align if the page is next revised):
- Its closing CTA sits on a neutral `data-layer="1"` band instead of a saturated (brand/dark) band.
- Section headings use `data-level="h2"` instead of the observed largest-scale (`data-level="h1"` visual on semantic `<h2>`).
- text-block is used for section intro prose; the observed pattern reserves text-block for footnotes/references and would use heading `data-paragraph` for intros.
