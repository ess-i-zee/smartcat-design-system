---
name: smartcat-deck
description: >-
  Build a Smartcat-branded presentation deck and deliver it as an editable
  Google Slides file. Use whenever someone wants a Smartcat deck, slides, a
  presentation, a pitch, a QBR or a customer-facing walkthrough: "make a
  deck", "turn this into slides", "build a presentation for X". Builds
  covers, dividers, statements, card grids, stats, numbered rows, splits,
  stacks, tables, flow chains, image slots for product screenshots, rosters
  and mosaics as native editable shapes, with layout-variety and fit checks.
  Charts, gantt, timelines and branching diagrams are not yet supported and
  are flagged. Not for one-pagers, documents or social graphics.
---

# Smartcat deck

A deck is a sequence of **fixed 1280×720px slides**, delivered as an
**editable Google Slides file** — real shapes and text a person can open and
change, not a picture of a slide. That requirement is why this skill builds
with `python-pptx` and uploads for Drive to convert, rather than rendering
HTML: Slides has no way to import arbitrary CSS as editable objects, so the
deck is authored as native shapes from the start.

**Scope, by explicit decision (2026-09-15, extended 2026-09-18 twice and
2026-09-21 — see docs/deck-design-brain.md section E's changelog): a defined
set of slide roles, not the full catalog.** `scripts/deck_pptx.py` covers:

- **Furniture:** `add_cover`, `add_section_divider` (plain, or with a
  chapter `number`, a ruled `items` list — strings, or `{"label", "icon"}`
  for an icon-led row — and/or a full-height `image_caption` slot),
  `add_closing`, `add_back_cover` (the cover's bookend, which every deck
  ends with).
- **Text-forward:** `add_statement` (the argument set large — bold H2 lead
  + one or more aside paragraphs, optional hairline `divider`; the
  opening-hook shape), `add_manifesto` (a Display statement that IS the
  slide, two narrow body columns under it), `add_heading_paragraph` (the
  quieter sibling), `add_bullet_list` (a supporting element inside another
  slide, never a whole slide alone — see Step 2).
- **Enumerated:** `add_cards` (2–6 cards — one row, or a 2×2 / 2×3 grid via
  `columns`; stacked or horizontal `layout`; icon- or number-anchored; one
  optional `featured` card), `add_numbered_rows` (3–8 short claims with a
  line of detail, in one or two columns; `style` panel / ruled / bare, per
  item `meta` for a page number or duration — agenda, contents, trust list).
- **Proof:** `add_stats` (cards, or `style="rule"` — bare figures beside a
  brand rule), `add_quote`, `add_table` (native editable cells, optional
  highlighted key column / bold total row).
- **People & imagery:** `add_roster` (portrait + name + role grid),
  `add_image_mosaic` (2–4 square image slots as one object: `1+2`, `2x2`,
  `row`).
- **Compositions:** `add_split` (two panels at an uneven ratio — text
  with `lead` / paragraphs / `features`, cards, stats, rule quote, table,
  rows, facts, image; any panel may carry its own `heading`; hairline
  `divider` between bare columns), `add_image_split` (a product-UI
  slot sized to the image's aspect filling the full height, copy beside it —
  the default for any slide about a product surface; when the copy is just a
  paragraph, the title joins it in the left column and the shot runs the
  whole slide height), `add_stack` (two
  components under one title: stats over a quote bar, a flow over cards or
  an image, rows over stats…), `add_flow_chain` (icon-cards joined by
  arrows, or a compact pill chain over `detail_cards`), `add_image_banner`
  (a 2:1-or-wider screenshot as the whole argument — it delegates to the
  image-led split for anything narrower).

All compose from the same tokens as everything else — no new colors, sizes,
or canvas geometry were introduced to build them. **Every builder stamps its
slide with a silhouette and sizes its content block to at least half the room
under the title**; `run_all_checks` (Step 5) reads those back. The rules
behind them live in the deck brain's Design DNA ("Silhouette variety is a
rule with numbers", "A content block earns the canvas or changes shape").

**Icons render as native pptx vector shapes, not raster pictures.**
`draw_icon()` parses a curated subset of the design system's icon SVGs
(`scripts/deck_icons.py`) into real custom-geometry shapes — genuinely
editable in Slides, matching this module's whole premise. Every card anchor
(`add_cards`, the split `cards` panel, flow-chain nodes) takes an optional
`icon` key from that curated set; omit it for an automatic numbered circle
badge. `deck_icons.py` documents how to add another icon to the set.
**`add_placeholder()`** renders a labeled placeholder (dashed panel + the
`placeholder` icon + a caption naming the asset) for a missing customer
logo, screenshot, or icon tile — call it from inside another slide's layout
code wherever a real asset belongs but isn't available yet.

**The Smartcat wordmark is the one visual embedded as a picture, not a
native shape** — `draw_logo()` places `assets/smartcat-logo-{white,black}.png`,
rendered once from the real SVG via an actual browser (two of the
wordmark's letterforms need `fill-rule="evenodd"` to render their counters
correctly, which pptx's custom-geometry has no per-path equivalent for —
reconstructing it as a vector shape risked silently filling those counters
in solid, a real correctness problem for a brand asset). `add_cover()` calls
it automatically; nothing else needs to.

Still not covered, because it doesn't reduce to rectangles, straight
connectors, and native table cells: charts (donut/bar), Gantt charts,
timelines with alternating above/below milestones, comparison v1/v2 and
alignment-matrix layouts (brand-gradient hero panels + chevrons), and any
flow/graph diagram with curved or branching connectors rather than a single
straight chain. `docs/deck-design-brain.md`'s full recipe catalog documents
all of these — if a plan calls for one, say so plainly rather than
approximating it with the wrong shape.

## Installing this skill elsewhere

The skill is packaged as one file, `skills/packages/smartcat-deck.skill` (a
zip whose root is the `smartcat-deck/` folder). In another Claude Code
workspace, unzip it into `~/.claude/skills/`; on claude.ai, upload the file
in Settings → Capabilities → Skills. It is self-sufficient: the engine
(`scripts/deck_pptx.py`, `scripts/deck_icons.py`), the logo assets and a
copy of the design-system sync script (`scripts/ds_sync.sh`) all travel
inside it. The design-system rules themselves are still fetched live from
GitHub at run time (Step 1), so they are only as current as the last push —
push the design-system repo after changing the brain or CLAUDE.md, or other
workspaces build against the previous rules. Rebuild the package after any
change to this folder (`skills/README.md` has the one-liner).

## Step 1 — load the design system

Use the **smartcat-design-system** skill first. It syncs the repo and gives
you `DS_ROOT`. **If that skill is not installed in this workspace**, run this
skill's own copy of its sync script instead — same output, same resolution
order (an explicit `$SMARTCAT_DS_ROOT`, the repo you are standing in, else a
sparse clone cached under `~/.cache/smartcat-design-system`):

```bash
eval "$(bash "<this skill's folder>/scripts/ds_sync.sh")"
```

With no shell at all, `reference/no-shell.md` gives the raw-URL fallback.
Then read, in this order:

- `INDEX.md` — the component manifest
- **the shared rules** — icons, logo, the promo-UI-mockups asset folder, page
  assembly, text casing, punctuation, section-background rules, CSS
  conventions. **Read this every time; it is not optional.** It's where the
  eyebrow-text ban and the gradient-blob ban live — a deck has shipped with
  both, in a build that skipped straight to the format section below and
  never saw them. It's also where "Promo UI mockups" lives — check it before
  reserving an empty image slot for one of the four covered products (see the
  bullet below).
- `CLAUDE.md` → the "Presentation decks" section
- `docs/deck-design-brain.md` — how to decide what each slide should be
  (still the right reasoning layer — it governs *what* a slide is, which is
  independent of *how* it gets rendered)

```bash
sed -n '/^## Icons/,/^## Component file structure/p' "$DS_ROOT/CLAUDE.md" | sed '$d'
sed -n '/^## Presentation decks/,/^## One-pagers/p' "$DS_ROOT/CLAUDE.md"
```

Three rules worth restating here because a deck's freedom to invent layouts
makes them easy to reinvent by accident:

- **No eyebrow text.** No label line above or beside a slide title or a
  heading inside a panel — not all-caps, not tracked out, and not a plain
  sentence-case one in brand purple either. A couple of reference slides
  carry one; they predate the ban. Do not reproduce it.
- **No chrome.** No page numbers, running heads, per-slide logos, section
  rails, tab strips or progress indicators. Every reference slide is bare;
  the section dividers and the light/dark banding carry the navigation.
  The only footer in `deck_pptx.py` is the cover's optional metadata line.
- **Reserve a slot where the slide is about a product surface — even with
  no screenshot in hand.** Use `add_image_split` (the default), a split or
  stack `{"kind": "image"}` panel, `image` on a card, or `add_image_banner`
  for a wide shot, wherever a specific feature is named — not on every slide. **Not having the real screenshot at
  build time is the normal case, never a reason to skip the slot** — that is
  the whole point of reserving one prospectively. Never redraw product UI
  from atomics; that is the social tier's rule. `add_placeholder` is a
  different thing: an asset we meant to have and is missing, not a
  prospective slot.
- **Reserve first, match second — never skip the reservation.** A slot is
  always reserved first for a slide about a product surface, even when you
  already expect a match in `images/promo-ui-mockups/` (AI chief of staff,
  content translator coworker, reviewer coworker, SCORM studio — see CLAUDE.md
  "Promo UI mockups" for the folder layout and the
  `<description> -- <tag> - <tag>` filename convention). The lookup and swap
  happen afterward, in Step 5, through **one call — `dp.run_all_checks(prs,
  PROMO_ROOT, product=…)`**, which runs `fill_matched_slots` over every
  reserved slot. That ordering is required so a slide never loses its slot
  just because the lookup gets missed or the folder has no match after all.
- **The promo shots are square — host them in `add_image_split`.** All 17
  files in `images/promo-ui-mockups/` are 1080×1080. A square dropped into a
  3:2 side box or a full-width banner covers barely half the slot and leaves
  dead flanks (the report flags it as a poor fit). `add_image_split` sizes the
  slot to the image — a full-height square with the copy beside it — and is
  the default shape for a product-surface slide. Write the slot caption in
  the folder's own vocabulary (product name + the surface, in the words the
  filenames use) so the match is exact.
- **Tone on dark slides.** Headings and key captions full white; every run
  of body copy — including bullets that continue a paragraph — the secondary
  shade. Text never leaves its box; `run_all_checks` flags an overrun.
- **Closing links.** Any closing line containing "book a demo" or "start a
  free trial" is hyperlinked automatically to the standard URLs
  (`dp.CLOSING_LINKS`) — link-coloured, underlined text, never a button.
- **No drop shadows.** Not on cards, panels, icon tiles, arrows or tables.
  PowerPoint adds them by default to anything that does not opt out, so
  call `dp.strip_shadows(prs)` before saving as a final sweep.
- **No gradient blobs, orbs, or glows.** No soft-edged blurred circle,
  especially bleeding off a slide corner as a decorative cover object. Every
  brand gradient in `deck_pptx.py` is a flat fill with a sharp edge — see the
  deck brain's Design DNA → Color for the sanctioned forms.

## Step 2 — plan the deck before building any slide

Work out the full slide list first — one line per slide, in three columns:
the **headline**, the **silhouette** (statement · prose · row · grid · rows ·
split · stack · banner · mosaic · roster · flow · table · quote — the deck
brain's step 3 table maps content to these), and the **theme**. Every
text-led slide opens with a **lead** line (the thesis, H3) before its body
copy, and body copy sits in reading-measure columns, never full width —
see the deck brain's Design DNA, "Five levels of type." Section D of the deck brain is the
decision procedure; section C is the role catalog.

**Pick each slide's shape from its parts, not from the nearest builder.**
Before assigning a silhouette, list what the slide's content actually
consists of — a claim, a paragraph, N items and how much copy each carries, a
number, a quote, a sequence, a product surface — and choose the shape that
holds *all* of them. A paragraph plus a screenshot is `add_image_split`, not a
paragraph with a picture dropped beside it; three stats plus the quote that
proves them is `add_stack`; a five-step process plus what each step delivers
is a flow over cards. The builders are primitives, and the panel specs on
`add_split` / `add_image_split` / `add_stack` are how a slide gets tailored to
its content.

**If the deck is about a covered product, print the shot catalog first:**

```python
for img in dp.list_promo_images(PROMO_ROOT, product="scorm"):   # or "chief", "translat", "reviewer"
    print(img["description"], "|", img["tags"])
```

Each shot is a candidate slide — the surface it shows is a claim the deck can
make with the product visible. Mark on the slide list which slide carries
which shot; a shot with no slide is a slide you have not thought of yet. The
build report names any shot left unused.

Then check the arc:

- **Read or presented?** A sent deck (business case, proposal, leave-behind)
  carries real paragraphs; a live-presented one runs to ~25 words a slide.
  Ask if it isn't obvious — it sets the copy density for every slide.
- **The headline test.** Read the slide titles in order, and nothing else.
  They have to make the argument on their own. Fix the headlines before
  building anything — see the deck brain's section D, "Pass 0".
- **Open on a hook, not the agenda** — a change in the world, a shared
  frustration, an unexpected number, a question.
- **Themes in bands, roughly even.** Decide the theme per band of 2–4 related
  slides and flip at section dividers; aim for about half the content slides
  dark. Hook and proof bands lean dark, tables and trust/compliance bands
  lean light. Content slides are *not* light by default — the reference decks
  are majority dark on content slides, and an all-light body with only the
  cover and dividers dark reads flat (the "light sandwich" this skill used to
  prescribe did exactly that). `check_theme_banding` flags any theme over
  80% of the content slides.
- **Read the silhouette column alone.** No two adjacent slides share a
  silhouette; no silhouette carries more than a third of the content slides;
  a deck of eight or more content slides uses at least four. Fix it here, on
  the list — `check_layout_variety` in Step 5 only confirms it.
- **One idea per slide.** If a slide needs two headlines, it is two slides.
- **And the reverse: one idea across two slides is one slide.** A stats row
  and a customer quote that both prove the same claim ("customers get the
  results they came to Smartcat for") ARE one idea, not two — merge them
  into one `add_split` (quote one side, the figures it backs on the other)
  rather than spending two slides on a single claim. "They're different
  content types" and "it blurs one-idea-per-slide pacing" are not reasons
  to keep them apart; the test is whether they share a claim, not whether
  they're the same content type — see deck-design-brain.md's decision
  procedure, step 1.
- **Does every slide earn its canvas?** A title + one short sentence with
  nothing else is not a slide — fold it into a neighbor under one shared
  idea. See deck-design-brain.md's decision procedure, step 1.
- **Which slides show the product?** Go down the slide list and ask this
  for each one, including each step of a flow chain — don't leave it for
  a review pass afterward. Does its copy name a specific product surface:
  a UI view, a conversation, a before/after, a dashboard? If so, it
  reserves an image slot now, as part of planning this slide, regardless
  of whether the screenshot exists yet (Design DNA, "A slide about a
  product surface reserves room for it"). A flow-chain step naming a real
  UI moment ("review in context," "side by side") may be significant
  enough to earn its own slide — an `add_image_banner` right after the
  chain — rather than staying folded into a node caption; decide that
  here. Step 5's `check_missing_image_slots` is the backstop for this
  question, not a substitute for asking it now.
- **A divider every 3–5 content slides** on anything longer than ~10 slides.

Show the user the slide list before building if the deck is longer than
about six slides — restructuring costs nothing at this stage and a lot
later.

## Step 3 — check every planned slide against the covered role set

Before writing any code, match each line in the slide list to one of
`deck_pptx.py`'s slide-role functions (`add_cover`, `add_section_divider`,
`add_statement`, `add_manifesto`, `add_heading_paragraph`, `add_bullet_list`,
`add_cards`, `add_numbered_rows`, `add_stats`, `add_split`, `add_image_split`,
`add_stack`, `add_table`, `add_flow_chain`, `add_image_banner`,
`add_image_mosaic`, `add_roster`, `add_quote`, `add_closing`,
`add_back_cover`). **Every deck ends with `add_back_cover`** —
the cover's bookend (cover gradient, a Display sign-off, the metadata line,
the wordmark bottom-right). It follows the closing slide, which makes the ask.

The silhouette you assigned in Step 2 already names the builder (see the
table in the deck brain's step 3). Three habits to break while matching:
**four cards with real paragraphs are a 2×2 grid** (`columns=2`), not a
4-up row of caption-size copy; **two or three cards beside a screenshot
stack vertically as full-width cards**, never side by side as tall empty
columns (the engine does this by default; go horizontal only when the stack
would not fit); **a stats row and the quote that proves it are one
`add_stack`**, not two slides; **a process chain and a feature list
are two slides, never one stack** — a chain stacks only over the screenshot
of one of its steps, or over cards that quantify those same steps.

**`add_bullet_list` is not a whole-slide default.** Reach for it only as a
short supporting list you place alongside other content (e.g. inside an
`add_split` text panel) — a genuinely enumerable, parallel set of 3+ items
is always `add_cards` instead, per deck-design-brain.md's "Enumerated
content." If a planned slide is just a title and a short list of several
peer items, recast it as cards before building it.

**If a slide doesn't fit one of these**, don't force it into the nearest
available shape (e.g. faking a timeline out of N-cards misrepresents the
content). Instead:
- Recast the slide as a covered role if the content genuinely supports it
  (a simple 3-step process often IS a bullet list or 3 cards), or
- Tell the user this slide role isn't built yet and ask whether to simplify
  it, add it to the deck manually in Slides afterward, or extend
  `deck_pptx.py` with a new builder function following the existing pattern
  (tokens in, a shape-placement function out).

## Step 4 — build each slide

Import the module and call one function per slide:

```python
import sys
sys.path.insert(0, "<path to this skill's scripts/ folder>")
import deck_pptx as dp

prs = dp.new_deck()
dp.add_cover(prs, "Smartcat platform overview", "Q4 2026 · Customer walkthrough")
dp.add_stats(prs, "The numbers", [
    {"value": "70%", "label": "Faster review"},
    {"value": "280+", "label": "Languages supported"},
    {"value": "$1.2M", "label": "Saved annually"},
], theme="light")
# ... one call per planned slide ...
prs.save("<deck-name>.pptx")
```

`scripts/build_example.py` is a full worked example exercising every core
role — copy its structure, not its content.

**Reserving an image slot:** every slide about a product surface reserves
one as part of being built — `add_image_split` (the default; square slot for
the promo shots, `aspect=1.5` or `16/10` for a landscape screenshot), an
`{"kind": "image", "caption": …}` panel in `add_split` / `add_stack`, an
`image` card in a row, or `add_image_banner` for a wide shot. This is step
one of the two-step sequence from Step 1's bullet. Do not look up
`images/promo-ui-mockups/` yet and do not call `draw_product_image` here; the
lookup and fill happen in Step 5's `run_all_checks`, after every slide is
built and every slot exists.

**Every value, color, and size in `deck_pptx.py` already comes from the
design tokens** (resolved snapshots from `tokens/*.css`, documented at the
top of the module) — this is what keeps a generated deck on-brand without
re-deriving colors by hand. Do not pass raw hex or point sizes into a
builder call; if a slide genuinely needs something the module doesn't
expose, extend the module (a new keyword on an existing function, or a new
function following the same pattern), not a one-off override at the call
site.

**Keep stat values and labels short.** `add_stats` does not re-check for
overflow the way the old HTML path's verify step did — a value like
`"$1,200,000"` will visually run past its panel edge with no warning.
Abbreviate before calling it: `$1,200,000` → `$1.2M`, `500,000` → `500K`.

## Step 5 — verify

**Check whether this environment can render a `.pptx` to an image before
assuming it can't.** Two paths, in order of fidelity:

**On Windows with PowerPoint installed** (check
`HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\POWERPNT.EXE`
or `$env:ProgramFiles\Microsoft Office\root\Office16\POWERPNT.EXE`) — this
is the highest-fidelity option, since it is the same renderer the deck will
be viewed in. It exports every slide at native 1280×720 in one call:

```powershell
$ppt = New-Object -ComObject PowerPoint.Application
$pres = $ppt.Presentations.Open("<deck>.pptx", -1, 0, 0)   # ReadOnly, not Untitled, no window
$pres.Export("<outdir>", "PNG", 1280, 720)
$pres.Close(); $ppt.Quit()
```

**Otherwise, LibreOffice** — `which libreoffice soffice` and `which pdftoppm`.
When both are present:

```bash
soffice --headless --convert-to pdf --outdir <dir> <deck-name>.pptx
pdftoppm -png -r 110 <dir>/<deck-name>.pdf <dir>/slide
```

(`--convert-to png` only exports slide 1 — always go through `pdf` +
`pdftoppm` for a real per-slide set.) Look at every slide this produces,
the same way you would review a screenshot of an HTML deck — this is what
actually catches a cramped table, an arrow with an invisible arrowhead, or a
split ratio that reads wrong, none of which `check_overflow` can see. Only
when neither tool is available does verification fall back to programmatic-
only, with a real spot-check once the deck lands in Slides (step 6).

**1. Run every mechanical check in one call — required, on the same `prs`,
before saving:**

```python
PROMO_ROOT = f"{DS_ROOT}/images/promo-ui-mockups"
report = dp.run_all_checks(prs, PROMO_ROOT, product="translat")   # product: a folder-name substring, or None
```

It does, in order: **fills every reserved slot** that matches a promo shot
(`fill_matched_slots` — each shot used once, weak matches left as slots),
then **overflow** (a shape past the slide edge), **text overflow**
(`check_text_fit` — text estimated to run past its own box; a hit is a
hard defect: shorten the copy, use a horizontal card, fewer items, or split
the slide — never shrink the type),
**missed image slots** (screenshot-inviting language on a slide with no
slot), **layout variety** (adjacent repeats, a silhouette over a third,
too few shapes), **theme banding** (one theme over 80% of content slides)
and **canvas fill** (a content block under 40% of the room beneath the
title), then prints the silhouette/theme line for the whole deck, the fill
report with any **poor fit** (an image covering under 75% of its slot), and
the product shots left **unused**.

Every check relies on runtime attributes the saved `.pptx` doesn't carry, so
this must run here, not on a reloaded file. Read what it prints and resolve
every line: a variety or fill hit means reshaping that slide (the message
says how); a missed-slot hit is not automatically wrong (the phrase can turn
up without describing an actual screen) but must be decided out loud — add
the slot, or say why this one doesn't need it; a poor fit means the slot's
shape doesn't suit the image — switch to `add_image_split` or set `aspect`;
an unused shot is a slide to consider adding. Silently clearing the list is
the failure these checks exist to catch. The variety and fill checks are
here because two rounds of written guidance did not stop generated decks
coming out as a title over one strip of boxes on every slide.

**2. Sanity-check the actual content**, not just the geometry — re-open the
saved file and print what's really in it, since a wrong keyword argument
fails silently rather than raising:

```python
from pptx import Presentation
prs2 = Presentation("<deck-name>.pptx")
for i, slide in enumerate(prs2.slides):
    print(f"slide {i+1}: bg=#{slide.background.fill.fore_color.rgb}")
    for shp in slide.shapes:
        if shp.has_text_frame:
            print("   ", shp.text_frame.text[:60])
```

Read the printed text back and confirm it matches the plan — this is also
where you'd catch punctuation-rule violations (straight quotes, hyphen-
as-dash) before they ship, same as any other format.

**If you print text with special characters (curly quotes, em dashes) to a
Windows terminal for a manual check, set `PYTHONUTF8=1` first** — without it
the console can mangle the display even though the file itself is correct.
Confirmed empirically this session: a middle dot and an em dash both printed
as `�` under the default console encoding, while the saved `.pptx` had the
right characters the whole time. Don't "fix" a mis-rendered console readout
by touching the file.

**Report the image slots — filled and unfilled alike — don't avoid creating
them.** `run_all_checks` already printed the fill report (`report["promo_fills"]`
holds it): which real file went into which slide, and which slots are still
reservations with their required size. Hand over the unfilled ones as a shot
list and say plainly that the deck is not finished until they are filled;
name the filled ones too, so the reader knows a picture already there is
deliberate and not a placeholder that slipped through; and list the product
shots left unused (`report["unused_promo"]`) so leaving them out is a
decision the reader can overrule. The obligation is disclosure, not
avoidance: reserving a slot for a slide about a product feature, with no
screenshot yet in hand, is exactly what this mechanism is for. Shipping a
slot without mentioning it is the failure — not adding the slot.

## Step 6 — upload and convert to Google Slides

**1. Save the `.pptx` locally**, then find whichever Drive-capable tool or
connector is available in this session — do not assume a specific tool
name, since it varies by installation.

**2. Base64-encode the file and upload it with NO `disableConversionToGoogleType`
flag** (or explicitly `false`) — this is the opposite of the PDF skills'
rule, and it's the whole point here:

- `contentMimeType: application/vnd.openxmlformats-officedocument.presentationml.presentation`
- leave `disableConversionToGoogleType` unset — Drive's default behavior
  converts a supported upload into its native Google format, which for a
  `.pptx` is an editable Google Slides file. This is documented tool
  behavior, not a guess.

**3. Confirm the result is actually Slides**, not a stored PowerPoint file —
the response's `mimeType` should read `application/vnd.google-apps.presentation`.
If it still says a PowerPoint MIME type, the conversion didn't happen; check
that `disableConversionToGoogleType` was truly omitted.

**If no Drive connector is available in this session**, say so plainly and
hand over the local `.pptx` instead — do not silently skip the upload, and
`.pptx` still opens in Slides via manual upload, so it is not a dead end.

**A `.pptx`'s base64 form is large even for a short deck** — the format
carries theme/layout XML overhead regardless of slide count (an 8-slide deck
in testing was ~37KB as a file, ~49KB base64). If moving the file through
your own context to construct the upload call is impractical, read it in
manageable chunks or use whatever direct file-upload path your environment
offers instead of round-tripping the whole payload through chat.

The upload response includes the file's Drive link — that link is the
deliverable to hand back.

## Step 7 — report

Say which commit of the design system you built against, how many slides,
the silhouette and theme arc (the one line `run_all_checks` prints is
enough), which product shots were placed where and which were left unused,
and the Drive/Slides link. Flag any slide role you had to recast or leave
out because it isn't in the covered set yet, and anything you couldn't
visually confirm (if there was no local render, say plainly that you're
relying on the programmatic checks plus the Drive conversion having
reported the right MIME type, not an eyeballed screenshot).
