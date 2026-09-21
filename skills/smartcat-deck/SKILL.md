---
name: smartcat-deck
description: >-
  Build a Smartcat-branded presentation deck and deliver it as an editable
  Google Slides file. Use whenever someone wants a Smartcat deck, slides, a
  presentation, a pitch, a QBR or a customer-facing walkthrough: "make a
  deck", "turn this into slides", "build a presentation for X", "put this in
  Smartcat style as a deck". Covers cover, section divider, heading+
  paragraph, bullets, N-cards, stats, quote, closing, a back cover, an
  asymmetric two-panel split, a data table, and a straight-line flow chain
  — all built as native,
  editable shapes. Anything outside that set (charts, gantt, timelines with
  alternating milestones, organic/branching flow diagrams, comparison
  matrices with chevrons) is not yet portable to Slides and should be
  flagged rather than attempted. Not for one-pagers, printed documents or
  social graphics; those have their own skills.
---

# Smartcat deck

A deck is a sequence of **fixed 1280×720px slides**, delivered as an
**editable Google Slides file** — real shapes and text a person can open and
change, not a picture of a slide. That requirement is why this skill builds
with `python-pptx` and uploads for Drive to convert, rather than rendering
HTML: Slides has no way to import arbitrary CSS as editable objects, so the
deck is authored as native shapes from the start.

**Scope, by explicit decision (2026-09-15, extended 2026-09-18 twice — see
docs/deck-design-brain.md section E's changelog for the second pass's full
writeup): a defined set of slide roles, not the full catalog.**
`scripts/deck_pptx.py` covers cover, section divider, heading+paragraph,
bullet list (a supporting element inside another slide, never a whole slide
alone — see Step 2), N-cards (`add_cards` — icon- or number-badge-anchored,
height follows content, row centers when it leaves extra room), stats,
quote, closing, an **asymmetric split** (`add_split` — two panels at an
uneven ratio, e.g. narrative + card grid, or a highlighted stat + a table),
a **table** (`add_table` — native, editable cells, with an optional
highlighted key column and/or bold total row), and a **flow chain**
(`add_flow_chain` — icon-bearing cards connected by arrows by default
(`style="cards"`), or a compact pill-node chain (`style="pills"`) paired
with a supporting `detail_cards` row underneath), and a **back cover**
(`add_back_cover` — the cover's bookend, which every deck ends with).
All compose from the same tokens as everything else — no new colors, sizes, or canvas geometry were
introduced to build them.

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

## Step 1 — load the design system

Use the **smartcat-design-system** skill first. It syncs the repo and gives
you `DS_ROOT`. Then read, in this order:

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
  no screenshot in hand.** Use `draw_image_slot` (a split `{"kind": "image"}`
  panel, `add_image_banner`, or `image` on a card) wherever a specific
  feature is named, not on every slide. **Not having the real screenshot at
  build time is the normal case, never a reason to skip the slot** — that is
  the whole point of reserving one prospectively. Never redraw product UI
  from atomics; that is the social tier's rule. `add_placeholder` is a
  different thing: an asset we meant to have and is missing, not a
  prospective slot.
- **Reserve first, match second — never skip the reservation.** `draw_image_slot`
  is always the first call for a slide about a product surface, even when you
  already expect a match in `images/promo-ui-mockups/` (AI chief of staff,
  content translator coworker, reviewer coworker, SCORM studio — see CLAUDE.md
  "Promo UI mockups" for the folder layout and the
  `<description> -- <tag> - <tag>` filename convention). The lookup and swap
  happen afterward, as their own pass in Step 5, via `fill_image_slot` — that
  ordering is required so a slide never loses its slot just because the
  lookup pass gets missed or the folder turns out not to have a match after
  all.
- **No drop shadows.** Not on cards, panels, icon tiles, arrows or tables.
  PowerPoint adds them by default to anything that does not opt out, so
  call `dp.strip_shadows(prs)` before saving as a final sweep.
- **No gradient blobs, orbs, or glows.** No soft-edged blurred circle,
  especially bleeding off a slide corner as a decorative cover object. Every
  brand gradient in `deck_pptx.py` is a flat fill with a sharp edge — see the
  deck brain's Design DNA → Color for the sanctioned forms.

## Step 2 — plan the deck before building any slide

Work out the full slide list first — one line per slide, each naming its
**role** (cover, agenda, section divider, stat, comparison, process, quote,
closing) and its theme. Section D of the deck brain is the decision
procedure; section C is the role catalog.

Then check the arc:

- **Read or presented?** A sent deck (business case, proposal, leave-behind)
  carries real paragraphs; a live-presented one runs to ~25 words a slide.
  Ask if it isn't obvious — it sets the copy density for every slide.
- **The headline test.** Read the slide titles in order, and nothing else.
  They have to make the argument on their own. Fix the headlines before
  building anything — see the deck brain's section D, "Pass 0".
- **Open on a hook, not the agenda** — a change in the world, a shared
  frustration, an unexpected number, a question.
- **Light sandwich.** Content slides light; cover, section dividers and the
  closing slide dark or brand-purple. A deck that is all one treatment reads
  flat.
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
`add_heading_paragraph`, `add_bullet_list`, `add_cards`, `add_stats`,
`add_split`, `add_table`, `add_flow_chain`, `add_quote`, `add_closing`,
`add_back_cover`). **Every deck ends with `add_back_cover`** — the cover's
bookend (cover gradient, a Display sign-off, the metadata line, the
wordmark bottom-right). It follows the closing slide, which makes the ask.
Reach for `add_split`/`add_table`/`add_flow_chain` deliberately, the same way
you'd reach for `add_cards` — not by default, but not as a last resort
either. A run of slides that are all "heading + a row of cards" reads as
flat even when each individual slide is fine; an asymmetric split or a table
in the mix is often the more honest shape for the content anyway (a
narrative next to supporting detail is rarely two equal halves).

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

**Reserving an image slot:** call `dp.draw_image_slot(slide, left, top, width,
height, caption)` for every slide about a product surface, every time — this
is step one of the two-step sequence from Step 1's bullet. Do not look up
`images/promo-ui-mockups/` yet and do not call `draw_product_image` here; the
lookup and fill happen in their own pass, in Step 5, after every slide is
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

**1. Fill matched image slots — the second half of the reserve-then-fill
sequence, and do it before the checks below:**

```python
for entry in dp.image_slots(prs):
    if entry["filled"]:
        continue
    match = ...  # your own lookup: best filename match in images/promo-ui-mockups/
                 # for entry["caption"] (see CLAUDE.md "Promo UI mockups")
    if match:
        slide = prs.slides[entry["slide"] - 1]
        dp.fill_image_slot(slide, entry["slot_index"], match)
```

Every slot was reserved with `draw_image_slot` back in Step 4, regardless of
whether a match was expected — this is where the lookup actually happens, on
the full, final slot list. Leave a slot exactly as `draw_image_slot` drew it
when nothing in the folder genuinely matches; don't force a weak match just
to clear the list.

**2. Check for shape-bounds overflow:**

```python
problems = dp.check_overflow(prs)
```

An empty list is a pass. This catches a shape placed or sized past the
slide edges — it does **not** catch text overflowing its own text box
(pptx can autosize or clip that silently); that is exactly why stat/label
length matters more here than in the HTML skills.

**3. Check for a missed image slot — required, not optional:**

```python
missed = dp.check_missing_image_slots(prs)
```

Call this on the **same `prs`, before saving** — it relies on a runtime
attribute the saved `.pptx` doesn't carry, so it must run here, not on a
reloaded file (see its docstring). This exists because a deck shipped with
zero reserved slots despite a flow-chain step captioned "Side by side, per
language" sitting right next to a slide about reviewing content — the rule
("a slide about a product surface reserves room for it") was known and
still never got checked while planning. Don't rely on remembering to look;
run this and look at what it flags. A hit is not automatically wrong (the
phrase can turn up without describing an actual screen), but every one
must be resolved one way or the other — add the slot, or decide out loud
why this one doesn't need it. Silently clearing the list without deciding
either way is the same failure this check exists to catch.

**4. Sanity-check the actual content**, not just the geometry — re-open the
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
them.** `dp.image_slots(prs)` returns every slot with its slide number,
caption, and a `filled` flag (`True` + `source` when `draw_product_image`
placed a real file from `images/promo-ui-mockups/`, `False` when it's still a
`draw_image_slot` reservation with the required size). Hand over the
`filled=False` ones as a shot list and say plainly that the deck is not
finished until they are filled; mention the `filled=True` ones too, naming
which real file went where, so the reader knows a picture already there is
deliberate and not a placeholder that slipped through. The obligation is
disclosure, not avoidance: reserving a slot for a slide about a product
feature, with no screenshot yet in hand, is exactly what this mechanism is
for. Shipping a slot without mentioning it is the failure — not adding the
slot.

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
the theme arc, and the Drive/Slides link. Flag any slide role you had to
recast or leave out because it isn't in the covered set yet, and anything
you couldn't visually confirm (since there's no local render — say plainly
that you're relying on the programmatic checks plus the Drive conversion
having reported the right MIME type, not an eyeballed screenshot).
