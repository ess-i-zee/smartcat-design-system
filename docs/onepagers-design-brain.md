# One-pager design brain

How to decide what a one-pager should look like and how to build it. This is the *reasoning* layer for one-pagers; the hard layout rules (fixed 1280px width, variable height, band mechanics) live in `CLAUDE.md` → "One-pagers", and the mechanics of `.op-page` / `.op-band` live in `base/onepagers-layout.css`. Read those first; this doc tells you how to *think*.

Everything below was reverse-engineered from 8 real Smartcat one-pagers in `references/one-pagers/` (visually inspected, not inferred from extracted text — the same method `docs/deck-design-brain.md` uses). Rebuild that inspection whenever a new reference one-pager is added; fold in what's genuinely new (see "E. Extending the brain").

The core principle: **a one-pager is a stack of full-bleed bands, each composed from a dedicated onepager-tier component** (`components/onepager/*`) **plus raw tokens — never a reused web page-level component.** This is a stronger rule than decks (which allow reshaping web components as a starting point): one-pagers get their own purpose-built layout vocabulary because the reference documents behave nothing like a responsive web page — they're dense, fixed-width, print-shaped documents with their own recurring block library.

---

## A. Design DNA — the invariants

- **Type.** Same voice as web and decks: Plus Jakarta Sans Bold headings, Inter Regular body. Headlines are stacked into short phrase fragments on their own line (`<br>` breaks), often punctuated with a period between fragments — e.g. "Review Less. / Catch More. / Improve Every Time" — but unlike decks, the *final* fragment usually does **not** take a trailing period. Treat the period as a separator between stacked phrases, not a mandatory sentence-ending device.
- **Density — the opposite of a deck's whitespace discipline.** Decks fill ~60-70% of the canvas and treat restraint as the look. One-pagers do the opposite: they are dense, information-rich documents that use most of the available width and stack sections back-to-back with generous-but-not-extravagant band padding (96px, `--spacing-13`). Don't import the deck's "restraint" instinct here — a sparse one-pager reads as unfinished, not elegant.
- **Bookends.** Every one-pager opens with `.op-hero` (solid brand-purple, self-sufficient) and closes with `.op-footer` (solid near-black bar, self-sufficient). Almost every one also closes its body with `.op-cta-band` (solid brand-purple) directly before the footer — see "soft closing" in section C for the documented exception.
- **Color.**
  - Brand purple (`--background-static-brand-inverted`) is reserved for the two bookend moments (hero, CTA band) and, mid-document, for a dedicated `.op-stat-band` proof moment. It is never the default background for ordinary content sections.
  - Brand-tint (`--background-static-brand-layer-1`) is reserved almost exclusively for `.op-platform-pillars` — every reference one-pager uses this exact light-purple band for the platform block and nothing else. A quote can also sit on brand-tint as a secondary use.
  - Near-black / dark (`data-theme="dark"` on a gray-layer-0 band) marks a "product depth" moment: the numbered `.op-steps` mechanics section is always dark, and industry one-pagers also put the quote+stats and rating-tiles moments on dark.
  - **Comparison contrast is gray-vs-purple, not semantic red/green.** This is a deliberate divergence from the deck brain's "highlights vs lowlights" pattern (which does use green/red thumbs). In every reference one-pager, the "problem" column is neutral gray with a tertiary-colored icon and the "solution" column is brand-tint with a brand-purple icon — semantic green/red never appears. Don't reach for the deck's red/green habit here.
- **Icons.** Design-system icons only, per CLAUDE.md. `thumbs-down` + `check-in-circle` is the established pair for comparison rows; everything else (benefit cards, impact tiles, platform pillars) picks whatever icon best represents the idea.
- **Buttons are real.** Unlike decks ("presented, not operated"), one-pagers are opened and read as documents (PDF or web), so `.btn` is correct here — every reference uses a real button-styled "Schedule a demo" CTA, both in the hero top-bar and the closing CTA band.
- **Length is a signal, not a target.** The reference documents range from a compact ~6-band factsheet to a dense ~10-band showcase. If a composed one-pager is pushing past roughly two US-Letter page-heights (~2×1656px) of content, that's a sign the brief may actually want a longer format (a deck or a landing page) — don't pad a one-pager just to look substantial, and don't cram a landing-page's worth of content into one either.

---

## B. Choose the background and theme

Same two composable axes as the deck canvas: `data-layer` × `data-theme` on `.op-band`. Decide both per band.

| Background | `.op-band` | Use for |
|---|---|---|
| Solid white | `data-layer="0"` (default) | The majority of regular content bands: logo strip, comparison, benefit cards, impact tiles. |
| Solid light gray | `data-layer="1"`/`"2"`/`"3"` | A content band that needs to read as distinct from its light neighbor. |
| Brand tint | `data-layer="brand-tint"` | `.op-platform-pillars`, almost exclusively; occasionally a standalone `.op-quote`. |
| Solid brand purple | `data-layer="brand"` | `.op-stat-band` mid-document; never for ordinary content. |
| Dark | `data-theme="dark"` (on any `data-layer`) | `.op-steps` always; a quote+stats combo or `.op-rating-tiles` in industry one-pagers. |

`.op-hero` and `.op-cta-band` are self-sufficient — they carry their own solid brand-purple background directly and are never wrapped in `.op-band` (same reasoning as hero-block on web: the bookend treatment never varies, so there's no axis to make it composable over).

**Section headings** (e.g. "Built for Teams Where Review is Complex") are composed directly from the type-style utility classes, not a web `heading` component: `<h2 class="text-h1 op-heading">Title</h2>`, optionally followed by `<p class="text-paragraph-reg op-heading-intro">…</p>`. The `.op-heading`/`.op-heading-intro` utilities (defined in `base/onepagers-layout.css`) exist purely to supply color — the raw `.text-h1` etc. classes carry font metrics only — and they read `--content-static-primary`/`secondary`, so they automatically go white inside a `data-layer="brand"` or `data-theme="dark"` band with no extra work.

---

## C. Section catalog — recipes

Each entry: *when to reach for it*, and *which onepager component builds it*. Section is `.op-band` unless marked self-sufficient.

### Bookends
- **Hero** (`components/onepager/hero`, self-sufficient). Opens every one-pager. Logo + CTA button top bar, stacked short-phrase headline, one supporting paragraph, product screenshot (`.op-media`) with 0-2 floating annotation tags.
- **CTA band** (`components/onepager/cta-band`, self-sufficient). Closes the body of most one-pagers, directly before the footer. Heading (H1 scale) + paragraph + a real `.btn`.
- **Footer** (`components/onepager/footer`, self-sufficient). Closes every one-pager: logo + URL on a fixed near-black bar.

### Trust & proof
- **Logo strip** (`components/onepager/logo-strip`). Logos only, no attribution — sits directly beneath the hero, compact padding (`data-padding="compact"`). Use when the message is "trusted by," not "here's what one customer said."
- **Quote** (`components/onepager/quote`). One attributed customer voice. `data-layout="standalone"` (centered, on `brand-tint`) when the quote stands alone; `data-layout="with-stats"` (row layout, usually on a dark band) when that same customer's story comes with 1-2 supporting numbers.
- **Stat band** (`components/onepager/stat-band`, on `data-layer="brand"`). 2-4 big aggregate proof numbers as their own dedicated moment — not tied to one customer, a company-wide metric instead.
- **Rating tiles** (`components/onepager/rating-tiles`, industry one-pagers only, usually dark). G2-style X.X/10 gauge tiles and open-ended counts ("1,000+") as a distinct, denser proof strip.

### Narrative & argument
- **Comparison** (`components/onepager/comparison`). The content genuinely opposes two states: problem vs. solution, status quo vs. approach, without Smartcat vs. with Smartcat. Two columns, paired rows, gray-vs-purple contrast (see Design DNA). Always follows a plain section heading.
- **Benefit cards** (`components/onepager/benefit-cards`). The content is 2-4 *independent* value props with no opposing pole — nothing to contrast against. This is the default for industry/vertical one-pagers, where the pitch is "here's what we solve for you" rather than "here's the old way vs. the new way."

  **Comparison vs. benefit cards — the tie-breaker:** if you can write the content as two honest column headers that oppose each other ("Review Slows Growth" / "AI That Makes Review Faster"), it's a comparison. If forcing an opposing header would feel invented, it's benefit cards.

### Mechanics & impact
- **Steps** (`components/onepager/steps`, always `data-theme="dark"`). Sequential "how it works" — numbered rows pairing a short explanation with a product screenshot. 3 steps is the common case; 5 for a more mechanically complex product (see the Storyline reference).
- **Impact tiles** (`components/onepager/impact-tiles`). 3-5 short aggregate outcomes across the organization — smaller and shallower than benefit cards, usually titled "Business Impact Across the Organization." Optional closing summary pill.
- **Platform pillars** (`components/onepager/platform-pillars`, always `data-layer="brand-tint"`). The fixed 4-item "Powered by Smartcat's AI Enterprise Platform" block. This is real, unchanging marketing copy (Intelligence Fabric / Agents & Orchestration / Expert Collaboration / Smartcat AI Visibility & Control) — reuse verbatim, don't rewrite it per one-pager.

### Soft closing (documented exception to the CTA-band default)
The two industry/vertical references end on a *plain* heading + paragraph + a text link (e.g. "👉 See how to cut your next product or promo training update from months to days"), with **no** `.op-cta-band` — a deliberately softer, more editorial close than the hard-sell CTA used by every product one-pager. Reach for this when the one-pager's tone is consultative/thought-leadership rather than a direct product pitch. Build it from `.op-heading`/`.op-heading-intro` plus a `.btn[data-type="text-purple"]` or a plain `.text-link`-styled anchor — never omit the footer.

---

## D. Document archetypes

Three recurring shapes emerged across the 8 references. Pick one as a starting skeleton, then adapt — don't treat these as rigid templates.

**1. Full product one-pager** (e.g. Reviewer Agents, Website Translation) — the richest shape:
Hero → Logo strip → Comparison → Steps (dark) → Quote → Impact tiles → Platform pillars → CTA band → Footer.

**2. Compact product one-pager** (e.g. Articulate Storyline Translation) — same DNA, shorter, for a narrower or newer product story:
Hero → section heading/intro → Comparison → Steps (dark) → Impact tiles (4-5 items) → Platform pillars → CTA band → Footer. Skips the logo strip and quote.

**3. Industry/vertical one-pager** (e.g. L&D - Manufacturing, Marketing - CPG/Retail) — denser, proof-heavy, softer close:
Hero → Logo strip → Benefit cards → Impact tiles (smaller, 4-col) → Quote with-stats (dark, decorative) → Stat band → Rating tiles (dark) → Soft closing (no CTA band) → Footer.

Choosing between them: a single product/feature pitch to a general audience → archetype 1 (or 2 if the story is thin). A pitch aimed at a specific industry vertical, leaning on aggregate proof and multiple customer logos more than one product mechanic → archetype 3.

---

## E. The decision procedure — turning a brief into a one-pager

1. **Which archetype?** Match the brief's intent to section D. When unsure, default to archetype 1 (full product) and cut sections down rather than guessing at 3's denser proof stack.
2. **What is each band's job?** Walk the chosen archetype's section list and map each to a recipe in section C. Swap Comparison for Benefit cards (or vice versa) if the tie-breaker in C says so — don't force the archetype's default if the actual content disagrees.
3. **Pick background/theme per band** (section B) — alternate light/dark/brand-tint across the document the same way the archetype examples do; don't make every band the same white.
4. **Compose each band** from its onepager component (section C) + tokens. Never drop in a web page-level component (hero-block, cards, numbers, testimonial, etc.) even reshaped — build from `components/onepager/*` and raw type-style/token classes only.
5. **Sanity-check against the DNA (A):** stacked-phrase headline in the hero; gray-vs-purple (not red/green) comparison contrast; brand-tint reserved for platform pillars; dark reserved for steps/proof-depth moments; real `.btn` on every CTA; density is the point, not restraint; length matches the content, not padding.

---

## F. Extending the brain

This doc grows as real one-pagers are built or new references appear. When given a new example (or a correction):

1. **Inspect it visually** (render to an image, don't infer from extracted text).
2. **Extract, in order:** background/theme per band, the band sequence (does it match an existing archetype or suggest a new one?), which onepager components were used and how they were configured, any token usage worth calling out, anything genuinely new.
3. **Fold it in:** refine a recipe in C, add a new archetype to D if the sequence doesn't fit the existing three, or adjust A/B only if the example reveals a genuine invariant, not a one-off. Log it below.

### Changelog
- Initial version — derived from visual inspection of 8 real Smartcat one-pagers in `references/one-pagers/` (Reviewer Agents, Content Review Agents, Website Translation, Articulate Storyline Translation, Image Translation Launch × 2, L&D - Manufacturing, Marketing - CPG/Retail): design DNA, background/theme axes, the 12-component onepager tier, three document archetypes, decision procedure.
- Test-driven fix — building the first full example (`output/onepagers/reviewer-agents.html`, archetype 1) surfaced that composing a section heading from the bare `.text-h1` utility class renders with no color at all (that class carries font metrics only). Added `.op-heading`/`.op-heading-intro` to `base/onepagers-layout.css` and made `.op-band` a flex column with a fixed heading→content gap (`--spacing-8`) — both fixed before any component shipped with the bug baked in.
- Verified by rendering two full test compositions (archetype 1 in full, archetype 3's benefit-cards/quote-with-stats/stat-band/rating-tiles/soft-closing fragments in a second pass): band stacking, the brand-band content-token repointing, the conic-gradient rating-tiles ring, and the soft-closing exception all render correctly with no further fixes needed.
