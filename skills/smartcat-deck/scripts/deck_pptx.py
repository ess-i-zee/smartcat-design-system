"""deck_pptx.py — build a Smartcat-branded .pptx from the SAME tokens the HTML
design system uses, translated once here into pptx-native units (EMU, points,
RGBColor) so a deck built with this module lands in Google Slides as real,
editable shapes and text — not a picture of a slide.

Covers the CORE slide roles only (by explicit scope decision, 2026-09-15,
extended 2026-09-18 twice and 2026-09-21 — see docs/deck-design-brain.md
section E's changelog for the full writeup of each): cover, section
divider, heading+paragraph, statement (lead paragraph + aside), bullet list
(a supporting element, never a whole slide alone), N-cards (icon- or
number-anchored, one row or a 2×2 / 2×3 grid, optional featured card),
stats, numbered rows (agenda / row-per-item), quote, closing, back cover,
an asymmetric split, an IMAGE-LED split (the slot sized to the image, the
copy beside it), a stack (two components under one title — stats over a
quote bar, a flow over cards or an image…), a table, an image banner, and
a flow chain (icon-cards connected by arrows by default; a compact
pill-chain variant for when it's paired with a supporting detail-card
row). Also provides a labeled placeholder primitive for a missing
image/logo asset, reserved product-UI image slots with a one-call promo
image lookup (`fill_matched_slots`), and `run_all_checks` — overflow,
missed slots, layout variety, theme banding and canvas fill in one pass.
Anything else in docs/deck-design-brain.md's full recipe catalog (charts,
gantt, timeline, comparison matrix, organic/branching flow diagrams) is
NOT covered — build those as an HTML deck via smartcat-deck's original
path instead, or extend this module following the same pattern.

Every builder stamps its slide with a SILHOUETTE (see `SILHOUETTES`) and
sizes its content block to at least MIN_CONTENT_FILL of the room under the
title. Both exist because two rounds of written guidance did not stop
generated decks coming out as eleven light slides each carrying a title
over one squat strip of boxes; the checks make the rules bite at build time.

Icons render as NATIVE pptx vector shapes (custom geometry, stroke-only) —
not raster pictures — from a curated subset of the design system's icon set
resolved into deck_icons.py. See that module for which icons are available
and how to add another one.

Token values below are resolved snapshots from tokens/globals.css,
tokens/colors.css and tokens/typography.css (desktop tier) as of the commit
this module was built against — see the loader skill for the live values if
a design token has since changed. Do not hand-edit a color/size here without
checking it still matches the source token.

Usage — see build_example.py in this same folder for a full worked deck.
"""

from __future__ import annotations

import os
import re
from math import ceil

from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml import parse_xml
from pptx.oxml.ns import qn, nsdecls

import deck_icons as dicon

# ── Canvas ──────────────────────────────────────────────────────────────
# 1280x720px at 96dpi == the standard PowerPoint/Slides 16:9 widescreen size.
EMU_PER_PX = 914400 / 96  # 9525
SLIDE_W_PX, SLIDE_H_PX = 1280, 720
PAGE_PADDING_PX = 48       # --spacing-9, the deck's fixed page padding
HEADING_GAP_PX = 80        # heading -> content gap, every slide type
SIZE_H1_PX = 48            # --size-h1 (desktop)
H1_LINE_PX = 58            # --line-height-h1 (desktop)
TITLE_CLEARANCE_PX = 24    # minimum air between a title's last line and the content
                           # below it. The reference slides sit at ~25-35px here;
                           # HEADING_GAP_PX is measured from the title's ORIGIN, so a
                           # one-line title lands in that range on its own and only a
                           # title that wraps needs the content pushed down.


def px(n: float) -> Emu:
    return Emu(round(n * EMU_PER_PX))


# ── Colors — resolved from tokens/globals.css + tokens/colors.css ────────
# (light mode / dark mode). A gradient blob/orb is banned system-wide
# (CLAUDE.md -> "Section backgrounds beyond the gray layers") — nothing here
# builds one; the "brand" background is a flat fill, matching every other
# sanctioned use of the brand color in this system.
class C:
    WHITE = RGBColor(0xFF, 0xFF, 0xFF)
    BRAND = RGBColor(0x73, 0x1E, 0xF2)          # --color-non-semantic-purple-70
    BRAND_50 = RGBColor(0x8A, 0x59, 0xFC)       # --color-non-semantic-purple-50
    BRAND_TINT = RGBColor(0xF3, 0xF1, 0xFB)     # --color-non-semantic-purple-10 == --background-static-brand-layer-1 (light)
    PINK = RGBColor(0xC3, 0x26, 0xED)           # --color-non-semantic-pink-70 — the cover gradient's bottom-edge stop
    PINK_40 = RGBColor(0xED, 0xB7, 0xFB)        # --color-non-semantic-pink-40 — cover/back-cover metadata line
    PURPLE_40 = RGBColor(0xC5, 0xB3, 0xFC)      # --color-non-semantic-purple-40 — cover subtitle

    LIGHT_BG = {0: RGBColor(0xFF, 0xFF, 0xFF), 1: RGBColor(0xF4, 0xF5, 0xF8),
                2: RGBColor(0xF0, 0xF1, 0xF4), 3: RGBColor(0xE5, 0xE5, 0xEA)}
    DARK_BG = {0: RGBColor(0x1A, 0x18, 0x24), 1: RGBColor(0x1F, 0x1D, 0x2A),
               2: RGBColor(0x2B, 0x29, 0x37), 3: RGBColor(0x52, 0x4F, 0x64)}

    LIGHT_PRIMARY = RGBColor(0x13, 0x10, 0x1C)     # near-black, matches deck-brain's #13101C
    LIGHT_SECONDARY = RGBColor(0x53, 0x50, 0x65)   # gray-alpha-60 flattened over white
    DARK_PRIMARY = RGBColor(0xFF, 0xFF, 0xFF)
    DARK_SECONDARY = RGBColor(0xB3, 0xB1, 0xBC)    # white-alpha-50 flattened over dark bg

    # background-static-brand-inverted: purple-70 in light mode, purple-30 in dark.
    # Paired 1:1 with content-static-inverted (white in light mode, near-black
    # in dark) — see base/deck-layout.css's own note on this pairing.
    BRAND_INVERTED_BG = {"light": RGBColor(0x73, 0x1E, 0xF2), "dark": RGBColor(0xE2, 0xDB, 0xFC)}
    BRAND_INVERTED_CONTENT = {"light": RGBColor(0xFF, 0xFF, 0xFF), "dark": RGBColor(0x13, 0x10, 0x1C)}


def primary(theme: str) -> RGBColor:
    return C.DARK_PRIMARY if theme == "dark" else C.LIGHT_PRIMARY


def secondary(theme: str) -> RGBColor:
    return C.DARK_SECONDARY if theme == "dark" else C.LIGHT_SECONDARY


def bg(theme: str, layer: int) -> RGBColor:
    return (C.DARK_BG if theme == "dark" else C.LIGHT_BG)[layer]


def brand_content(theme: str) -> RGBColor:
    """--content-static-brand: purple-70 in light mode, purple-50 in dark.
    Any brand-coloured TEXT or figure goes through this — purple-70 on a
    near-black slide is too dark to read, which is exactly why the token
    has a dark-mode value. Brand-coloured FILLS (the numbered badge, a pill)
    keep C.BRAND in both themes, since they carry white on top."""
    return C.BRAND_50 if theme == "dark" else C.BRAND


def panel_fill(theme: str) -> RGBColor:
    # Light -> solid gray layer-1 panel. Dark -> gray-80 (#1F1D2A), one step
    # off the slide's own gray-90 ground: the flat stand-in for the CSS
    # frosted-alpha panel, since pptx has no backdrop blur. A lighter step
    # than this reads as a grey box floating on the slide rather than a
    # panel sunk into it — see deck-design-brain.md Design DNA -> Surfaces.
    return C.LIGHT_BG[1] if theme == "light" else C.DARK_BG[1]


# ── Type — desktop tier, tokens/typography.css, px->pt at 96dpi (x0.75) ──
FONT_HEADING = "Plus Jakarta Sans"
FONT_BODY = "Inter"
WEIGHT_BOLD, WEIGHT_SEMIBOLD, WEIGHT_REGULAR = 700, 600, 400

SIZE_DISPLAY = Pt(48)   # 64px
SIZE_H1 = Pt(36)        # 48px — the deck's slide-title scale
SIZE_H2 = Pt(24)        # 32px
SIZE_H3 = Pt(18)        # 24px
SIZE_H4 = Pt(13.5)      # 18px — card heading on a narrow card
SIZE_PARAGRAPH = Pt(13.5)  # 18px
SIZE_CAPTION = Pt(10.5)    # 14px

# px equivalents of the sizes above, for the card-height content estimate
# below (_text_lines / _measure_card_row_height) — kept in sync with the
# comments on the Pt() constants themselves.
SIZE_H3_PX = 24
SIZE_H4_PX = 18
SIZE_PARAGRAPH_PX = 18
SIZE_CAPTION_PX = 14
SIZE_DISPLAY_PX = 64

ANCHOR_SIZE = 40        # numbered-badge anchor
ICON_ANCHOR_SIZE = 56   # icon anchor — deliberately larger than the numbered badge:
                        # an icon has to read as a glyph, a numeral only as a digit
ANCHOR_TEXT_GAP = 24    # anchor -> heading. Applies to BOTH anchor kinds
SMALL_CARD_W = 260      # at or below this width a card takes the H4 heading (see _card_heading_size)
BODY_LINE_SPACING = 1.15  # every run of body copy — never pptx's "single"
STAT_NO_DESC_PAD = 16   # extra bottom padding on a stat card with no description line
SPLIT_BARE_GAP = 64     # --spacing-11, the gap between a bare text panel and a surfaced one
WIDE_CARD_W = 360       # at or above this width a card's paragraph sets at body size (18px),
                        # not caption — the reference cards (stat-cards.jpg, exec-summary-3col.jpg)
                        # carry 18px copy; caption-size copy on a wide card reads as a footnote
MIN_CONTENT_FILL = 0.5  # a content block occupies at least this share of the area below the
                        # title. "Size to content" was added to stop cards stretching to the
                        # slide floor; without a floor it produced the opposite defect — a
                        # 120px strip of squat cards floating in 500px of empty canvas, on
                        # slide after slide. The reference decks fill ~50–70%. Below this the
                        # shape is wrong for the content (go to two rows, a split, or merge
                        # slides), so the builders pad up to the floor and check_canvas_fill
                        # flags anything that still lands under it.
STAT_BOTTOM_EXTRA = 48  # stat cards take triple the bottom padding (24 + 48 = 72px) so the
                        # caption never sits on the card's floor — user correction 2026-09-21
CARD_H_TEXT_GAP = 20    # horizontal card: gap between the anchor and the text column
FLOW_MIN_FILL = 0.4     # a chain on its own floors its nodes at this share of the room, top-aligned

# Real hyperlinks on the closing slide — plain link-styled text, never a
# button. Any closing line containing one of these phrases is linked
# automatically (add_closing's default `links`). Set by the user 2026-09-21.
CLOSING_LINKS = {
    "book a demo": "https://www.smartcat.com/book-a-demo/",
    "start a free trial": "https://smartcat.com/sign-up",
}

# Editorial devices adopted from the external reference set (2026-09-21,
# docs/deck-design-brain.md section F). All on-token: the lead level is H3
# in the heading face; rules and dividers are existing colour snapshots.
LEAD_SIZE, LEAD_PX = SIZE_H3, SIZE_H3_PX   # the "lead" paragraph level — thesis before body copy
ACCENT_RULE_W = 3        # brand-purple vertical rule beside a bare stat or a rule quote
DIVIDER_W_PT = 0.75      # hairline dividers between ruled rows / split columns
FEATURE_ICON = 20        # icon size in a text panel's feature mini-grid
FEATURE_ROW_H = 36
PANEL_HEADING_GAP = 20   # gap under a panel's own H3 heading


def divider_color(theme: str) -> RGBColor:
    """--border-divider-default, flattened: the existing gray-layer-3 snapshots."""
    return C.LIGHT_BG[3] if theme == "light" else C.DARK_BG[3]


def _hairline(slide, x0: float, y0: float, x1: float, y1: float, theme: str):
    ln = _no_shadow(slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, px(x0), px(y0), px(x1), px(y1)))
    ln.line.color.rgb = divider_color(theme)
    ln.line.width = Pt(DIVIDER_W_PT)
    return ln


def _accent_rule(slide, x: float, top: float, height: float):
    """A short solid brand-purple vertical bar (a shape, not a line, so it
    keeps its width at any zoom) — the stat-rule and rule-quote device."""
    bar = _no_shadow(slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(x), px(top), px(ACCENT_RULE_W), px(height)))
    bar.fill.solid()
    bar.fill.fore_color.rgb = C.BRAND
    bar.line.fill.background()
    return bar


STACK_GAP_SURFACED = 8  # two surfaced panels stacked vertically meet at the grid gutter…
STACK_GAP_BARE = 32     # …a bare panel over/under a surfaced one takes --spacing-7

# Every builder stamps the slide with its SILHOUETTE — the shape a viewer
# sees at thumbnail scale before reading a word. check_layout_variety reads
# these back: two adjacent content slides with the same silhouette, or one
# silhouette carrying most of a deck, is the "every slide is a title over a
# strip of boxes" failure that wording alone never fixed.
SILHOUETTES = (
    "cover", "back-cover", "divider", "closing",      # furniture — not content
    "statement",   # one big statement / lead paragraph + aside
    "prose",       # heading + paragraph
    "list",        # heading + bullet list (supporting-only; flagged if whole slide)
    "row",         # one row of equal cards or stats
    "grid",        # two or more rows of cards
    "rows",        # numbered / icon rows, 1–2 columns (agenda, row-per-item)
    "split",       # asymmetric two-panel
    "stack",       # two different components stacked vertically
    "banner",      # full-width image slot
    "mosaic",      # two to four image slots as one composed object
    "roster",      # people grid — portrait + name + role
    "flow",        # process chain
    "table",
    "quote",
)
_CONTENT_SILHOUETTES = tuple(s for s in SILHOUETTES if s not in ("cover", "back-cover", "divider", "closing"))
# Deliberately sparse shapes — a statement or a stand-alone quote is meant to
# leave most of the canvas empty, so the fill floor does not apply to them.
_FILL_EXEMPT = ("cover", "back-cover", "divider", "closing", "statement", "quote", "prose")


def _mark(slide, silhouette: str):
    assert silhouette in SILHOUETTES, silhouette
    slide._smartcat_silhouette = silhouette
    return slide


LINK_HEX = "8A59FC"   # --content-link-default (dark) = purple-50; the theme hyperlink colour


def _set_theme_link_color(prs, hex_rgb: str = LINK_HEX):
    """PowerPoint and Google Slides paint hyperlinked text with the THEME's
    hyperlink colour and ignore the run's own colour — which is why the
    closing slide's links came out Office-blue despite being set to brand
    purple. The fix is at the source: rewrite the theme's `hlink` and
    `folHlink` scheme colours to purple-50 (#8A59FC, --content-link-default
    on dark) so every link in the deck is brand-coloured by default.
    User correction 2026-09-21."""
    from pptx.opc.constants import RELATIONSHIP_TYPE as RT
    from lxml import etree
    theme_part = prs.slide_master.part.part_related_by(RT.THEME)
    root = etree.fromstring(theme_part.blob)
    for tag in ("hlink", "folHlink"):
        el = root.find(f".//{qn('a:' + tag)}")
        if el is None:
            continue
        for child in list(el):
            el.remove(child)
        el.append(parse_xml(f'<a:srgbClr {nsdecls("a")} val="{hex_rgb}"/>'))
    theme_part._blob = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def new_deck() -> Presentation:
    prs = Presentation()
    prs.slide_width = px(SLIDE_W_PX)
    prs.slide_height = px(SLIDE_H_PX)
    _set_theme_link_color(prs)
    return prs


def add_blank_slide(prs: Presentation, theme: str = "light", layer: int = 0,
                     brand_bg: bool = False):
    """A slide with no placeholders — every shape on it is one we add
    ourselves. brand_bg=True uses background-static-brand-inverted, paired
    with brand-inverted content color (see base/deck-layout.css's note: never
    combine this with a theme flip to "get" white text — the pairing is
    already self-contained per theme)."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # layout 6 = blank
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = C.BRAND_INVERTED_BG[theme] if brand_bg else bg(theme, layer)
    slide._smartcat_theme = theme
    slide._smartcat_brand_bg = brand_bg
    return slide


def _content_color(slide) -> RGBColor:
    if getattr(slide, "_smartcat_brand_bg", False):
        return C.BRAND_INVERTED_CONTENT[slide._smartcat_theme]
    return primary(slide._smartcat_theme)


def _secondary_color(slide) -> RGBColor:
    if getattr(slide, "_smartcat_brand_bg", False):
        return C.BRAND_INVERTED_CONTENT[slide._smartcat_theme]
    return secondary(slide._smartcat_theme)


def _textbox(slide, left, top, width, height):
    tb = slide.shapes.add_textbox(px(left), px(top), px(width), px(height))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    return tb, tf


def _body(p):
    """Every paragraph of body copy goes through this. pptx defaults to
    "single" line spacing, which sets 18px body copy far too tight for a
    slide read at a distance; 1.15 is the deck's leading for any flowing
    text (paragraphs, card copy, captions, bullets, table cells). Headings
    and display figures keep their own tight default."""
    p.line_spacing = BODY_LINE_SPACING
    return p


def _no_shadow(shp):
    """No element in this system carries a drop shadow. PowerPoint applies
    the theme's default shape effects to anything that does not explicitly
    opt out — which is how the flow-chain arrows shipped with a shadow
    nobody asked for. Call this on every shape the module creates."""
    try:
        shp.shadow.inherit = False
    except (AttributeError, NotImplementedError):
        pass
    return shp


def strip_shadows(prs):
    """Belt-and-braces sweep: clear inherited effects from every shape on
    every slide. The per-shape calls above are the real fix; this catches
    anything a future builder forgets. Safe to call more than once."""
    for slide in prs.slides:
        for shp in slide.shapes:
            _no_shadow(shp)
    return prs


def _set_run(run, text, size, bold, color, font=FONT_BODY):
    run.text = text
    run.font.size = size
    run.font.bold = bold
    run.font.name = font
    run.font.color.rgb = color


def _rounded_rect(slide, left, top, width, height, fill_color, radius_ratio=0.06):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px(left), px(top), px(width), px(height))
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill_color
    shp.line.fill.background()
    shp.shadow.inherit = False
    try:
        shp.adjustments[0] = radius_ratio
    except (IndexError, ValueError):
        pass
    return shp


def _set_line_dash(line_format, val: str = "dash"):
    """Raw-XML dash style, the same pattern as `_add_arrowhead`/
    `_set_cell_border` below — python-pptx 1.0.2 exposes `dash_style` but no
    public enum to assign it from in this version, so this writes the
    <a:prstDash> child directly, inserted right after any existing fill
    child per ECMA-376's required element order."""
    ln = line_format._get_or_add_ln()
    el = parse_xml(f'<a:prstDash {nsdecls("a")} val="{val}"/>')
    fill_el = None
    for child in ln:
        if child.tag.split("}")[-1] in ("noFill", "solidFill", "gradFill", "pattFill"):
            fill_el = child
    if fill_el is not None:
        fill_el.addnext(el)
    else:
        ln.insert(0, el)


def _set_vertical_gradient(shape, stops: list[tuple]):
    """Raw-XML multi-stop linear gradient, top-to-bottom — python-pptx's
    `fill.gradient()` only gives 2 stops with no public way to add more, so
    this builds <a:gradFill> directly (same raw-OOXML pattern as this
    module's other helpers). `stops` is [(position 0..1, RGBColor), ...] in
    top-to-bottom order. Used for the cover gradient — see
    deck-design-brain.md Design DNA -> Color, "Cover gradient"."""
    spPr = shape._element.spPr
    for tag in ("a:noFill", "a:solidFill", "a:gradFill", "a:blipFill", "a:pattFill", "a:grpFill"):
        el = spPr.find(qn(tag))
        if el is not None:
            spPr.remove(el)
    gs_xml = "".join(
        f'<a:gs pos="{round(pos * 100000)}"><a:srgbClr val="%02X%02X%02X"/></a:gs>' % (c[0], c[1], c[2])
        for pos, c in stops
    )
    grad_xml = (
        f'<a:gradFill {nsdecls("a")} rotWithShape="1">'
        f"<a:gsLst>{gs_xml}</a:gsLst>"
        f'<a:lin ang="5400000" scaled="1"/>'  # 5400000 = 90deg (60,000ths of a degree) = top-to-bottom
        f"</a:gradFill>"
    )
    grad_el = parse_xml(grad_xml)
    ln_el = spPr.find(qn("a:ln"))
    if ln_el is not None:
        ln_el.addprevious(grad_el)
    else:
        spPr.append(grad_el)


# ── Icons — native vector shapes from a curated SVG-path snapshot ─────────
# See deck_icons.py for the data and its provenance. Icons are stroke-only
# custom geometry (matching the source: stroke="currentColor", fill="none"),
# built as raw OOXML because python-pptx's freeform builder only supports
# straight line segments, not the cubic beziers real icon paths use.

_SVG_TOKEN_RE = re.compile(r"([MLHVCZmlhvcz])|(-?\d*\.?\d+(?:[eE][-+]?\d+)?)")
_SHAPE_ID_COUNTER = [10000]
_PATH_UNITS = 24000  # icon path coordinate space: viewBox units x1000 for sub-pixel precision


def _next_shape_id() -> int:
    _SHAPE_ID_COUNTER[0] += 1
    return _SHAPE_ID_COUNTER[0]


def _parse_svg_path(d: str) -> list[list[tuple]]:
    """Parse an SVG path `d` string into a list of subpaths, each a list of
    segment tuples: ('moveTo', (x,y)) / ('lnTo', (x,y)) /
    ('cubicBezTo', p1, p2, p3) / ('close',). Supports M/L/H/V/C/Z, absolute
    or relative, implicit lineto-after-moveto and implicit command
    repetition — everything deck_icons.py's curated set actually uses. Raises
    ValueError on any other command (e.g. arcs); see that module's note on
    what to do about an icon that needs one."""
    tokens: list = []
    for m in _SVG_TOKEN_RE.finditer(d):
        if m.group(1):
            tokens.append(m.group(1))
        elif m.group(2) is not None:
            tokens.append(float(m.group(2)))
    i, n = 0, len(tokens)
    subpaths: list[list[tuple]] = []
    cur = None
    cx = cy = start_x = start_y = 0.0
    cmd = None

    def take():
        nonlocal i
        v = tokens[i]
        i += 1
        return v

    while i < n:
        if isinstance(tokens[i], str):
            cmd = tokens[i]
            i += 1
        if cmd in ("M", "m"):
            x, y = take(), take()
            if cmd == "m":
                x += cx
                y += cy
            cx, cy = x, y
            start_x, start_y = x, y
            cur = [("moveTo", (x, y))]
            subpaths.append(cur)
            cmd = "L" if cmd == "M" else "l"  # further coordinate pairs are implicit lineto
        elif cmd in ("L", "l"):
            x, y = take(), take()
            if cmd == "l":
                x += cx
                y += cy
            cx, cy = x, y
            cur.append(("lnTo", (x, y)))
        elif cmd in ("H", "h"):
            x = take()
            if cmd == "h":
                x += cx
            cx = x
            cur.append(("lnTo", (cx, cy)))
        elif cmd in ("V", "v"):
            y = take()
            if cmd == "v":
                y += cy
            cy = y
            cur.append(("lnTo", (cx, cy)))
        elif cmd in ("C", "c"):
            x1, y1, x2, y2, x, y = take(), take(), take(), take(), take(), take()
            if cmd == "c":
                x1 += cx; y1 += cy; x2 += cx; y2 += cy; x += cx; y += cy
            cur.append(("cubicBezTo", (x1, y1), (x2, y2), (x, y)))
            cx, cy = x, y
        elif cmd in ("Z", "z"):
            cur.append(("close",))
            cx, cy = start_x, start_y
        else:
            raise ValueError(f"unsupported SVG path command {cmd!r} — see deck_icons.py")
    return subpaths


def _custgeom_xml(subpaths: list) -> str:
    scale = _PATH_UNITS / dicon.ICON_VIEWBOX

    def pt(x, y):
        return f'<a:pt x="{round(x * scale)}" y="{round(y * scale)}"/>'

    parts = []
    for sp in subpaths:
        for seg in sp:
            kind = seg[0]
            if kind == "moveTo":
                parts.append(f"<a:moveTo>{pt(*seg[1])}</a:moveTo>")
            elif kind == "lnTo":
                parts.append(f"<a:lnTo>{pt(*seg[1])}</a:lnTo>")
            elif kind == "cubicBezTo":
                parts.append(f"<a:cubicBezTo>{pt(*seg[1])}{pt(*seg[2])}{pt(*seg[3])}</a:cubicBezTo>")
            elif kind == "close":
                parts.append("<a:close/>")
    body = "".join(parts)
    return (
        f'<a:custGeom {nsdecls("a")}><a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/>'
        f'<a:rect l="0" t="0" r="0" b="0"/>'
        f'<a:pathLst><a:path w="{_PATH_UNITS}" h="{_PATH_UNITS}" fill="none" stroke="1">{body}</a:path></a:pathLst>'
        f"</a:custGeom>"
    )


def draw_icon(slide, icon_name: str, left: float, top: float, size: float, color: RGBColor):
    """Draw a design-system icon as a NATIVE pptx vector shape (custom
    geometry, stroke-only, no fill) — not a raster picture — `size`px square,
    top-left at (left, top) in slide px. `color` sets the stroke, matching
    the source icon's stroke="currentColor". Raises KeyError if `icon_name`
    isn't in deck_icons.ICONS' curated set — see that module to add one, or
    fall back to a numbered badge for that card instead."""
    if icon_name not in dicon.ICONS:
        raise KeyError(
            f"icon {icon_name!r} is not in deck_icons.ICONS' curated set "
            f"({sorted(dicon.ICONS)}). Add it there (see that module's "
            f"docstring) or use a numbered badge instead."
        )
    subpaths = []
    for d in dicon.ICONS[icon_name]:
        subpaths.extend(_parse_svg_path(d))
    geom_xml = _custgeom_xml(subpaths)
    stroke_w_px = size * (dicon.ICON_STROKE_WIDTH / dicon.ICON_VIEWBOX)
    shape_id = _next_shape_id()
    hex_color = "%02X%02X%02X" % (color[0], color[1], color[2])
    sp_xml = (
        f'<p:sp {nsdecls("p", "a")}>'
        f'<p:nvSpPr><p:cNvPr id="{shape_id}" name="icon-{icon_name}-{shape_id}"/>'
        f"<p:cNvSpPr/><p:nvPr/></p:nvSpPr>"
        f"<p:spPr>"
        f'<a:xfrm><a:off x="{int(px(left))}" y="{int(px(top))}"/>'
        f'<a:ext cx="{int(px(size))}" cy="{int(px(size))}"/></a:xfrm>'
        f"{geom_xml}"
        f"<a:noFill/>"
        f'<a:ln w="{int(px(stroke_w_px))}" cap="rnd"><a:solidFill><a:srgbClr val="{hex_color}"/></a:solidFill><a:round/></a:ln>'
        f"<a:effectLst/>"   # explicit empty effect list == no drop shadow
        f"</p:spPr>"
        f"<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody>"
        f"</p:sp>"
    )
    sp_element = parse_xml(sp_xml)
    slide.shapes._spTree.append(sp_element)
    return sp_element


# ── Logo — the real wordmark, embedded as a picture ────────────────────────
# Unlike icons, the wordmark is NOT reconstructed as native vector geometry:
# two of its letterforms ("a") are exported with fill-rule="evenodd" to
# render their counters (holes) correctly, and OOXML custGeom has no
# per-path fill-rule choice (always nonzero winding) — reproducing it as a
# custGeom risks silently filling those counters in solid, which is a real
# correctness problem for a brand asset, unlike an icon's approximate line
# art. The safer choice is embedding the REAL logo file, rendered once to a
# transparent PNG via an actual browser (perfect fidelity, evenodd handled
# natively) — see CLAUDE.md "Logo": "Always use the real logo asset."

_ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
_LOGO_ASPECT = 1200 / 208  # smartcat-logo-{white,black}.png's actual (cropped) pixel aspect ratio


def draw_logo(slide, variant: str, left: float, top: float, height: float):
    """Place the Smartcat wordmark, `height`px tall, width computed from its
    real aspect ratio (`_LOGO_ASPECT`) so it's never stretched. `variant` is
    "white" (dark backgrounds — every cover) or "black" (light backgrounds).
    Returns (shape, width_px) since callers laying out a logo lockup (e.g. a
    cover's Smartcat + client logo pair) need the actual width placed."""
    assert variant in ("white", "black"), "variant must be 'white' or 'black'"
    path = os.path.join(_ASSETS_DIR, f"smartcat-logo-{variant}.png")
    width = height * _LOGO_ASPECT
    pic = slide.shapes.add_picture(path, px(left), px(top), px(width), px(height))
    return pic, width


def _draw_card_anchor(slide, kind: str, value, left: float, top: float, theme: str,
                       surface: RGBColor | None = None):
    """Every content card's required visual anchor (see deck-design-brain.md
    Design DNA "Surfaces") — a filled circle holding either a numbered badge
    (`kind="number"`, `value` an int) or a design-system icon
    (`kind="icon"`, `value` an icon name). The numbered badge is solid brand
    purple + white numeral in both themes, matching the stat figures'
    theme-independent brand-purple treatment.

    The icon tile reads against the SURFACE it sits on, not the theme:
    `surface` is the card's own fill, and whenever that is anything other
    than pure white the tile is white with a brand-purple glyph. A white
    disc is what separates the icon from the card in both themes — on a
    light gray card and on a dark gray-80 one alike. Only on a genuinely
    white surface does the tile fall back to the brand tint, since a white
    disc on white would be invisible. Pass `surface=None` when the anchor
    is not sitting on a card."""
    size = ICON_ANCHOR_SIZE if kind == "icon" else ANCHOR_SIZE
    circ = _no_shadow(slide.shapes.add_shape(MSO_SHAPE.OVAL, px(left), px(top), px(size), px(size)))
    circ.line.fill.background()
    on_brand = surface is not None and tuple(surface) == tuple(C.BRAND)
    if kind == "number":
        # On a featured (brand-filled) card the badge inverts — white disc,
        # brand numeral — since a brand badge on a brand card would vanish.
        circ.fill.solid()
        circ.fill.fore_color.rgb = C.WHITE if on_brand else C.BRAND
        tf = circ.text_frame
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        _set_run(p.add_run(), str(value), SIZE_H3, True, C.BRAND if on_brand else C.WHITE, FONT_HEADING)
    else:
        on_white = surface is not None and tuple(surface) == tuple(C.WHITE)
        circ.fill.solid()
        circ.fill.fore_color.rgb = C.BRAND_TINT if on_white else C.WHITE
        icon_color = C.BRAND
        icon_size = size * 0.5
        draw_icon(slide, value, left + (size - icon_size) / 2, top + (size - icon_size) / 2, icon_size, icon_color)
    return size


# ── Card content-height estimate — cards size to content, not the slide ───
# See deck-design-brain.md Design DNA "Surfaces": a card's height follows its
# own content, and a row that leaves extra vertical room centers instead of
# stretching. pptx has no equivalent of CSS's own text-measurement/autosize
# for our purpose here (autosize only shrinks text to fit a fixed box, the
# opposite of what we want), so this is a deliberate char-count heuristic —
# close enough to size a card sensibly, not a typesetting-accurate measure.

def _text_lines(text: str, avail_width_px: float, font_px: float, avg_char_ratio: float = 0.55) -> int:
    if not text:
        return 0
    chars_per_line = max(1, int(avail_width_px / (font_px * avg_char_ratio)))
    return max(1, ceil(len(text) / chars_per_line))


def _card_heading_size(card_w: float):
    """A card narrower than SMALL_CARD_W — a split's card panel, a 4-up row —
    takes the H4 heading. H3 on a ~220px card wraps a three-word heading onto
    three lines and swamps the copy under it."""
    return (SIZE_H4, SIZE_H4_PX) if card_w <= SMALL_CARD_W else (SIZE_H3, SIZE_H3_PX)


def _card_body_size(card_w: float):
    """Card copy sets at body size (18px) on a wide card and caption (14px)
    on a narrow one. The reference cards all carry 18px copy — a 2×2 grid
    or a 3-up row at caption size reads as a row of footnotes, and it is the
    single biggest reason a generated card row looked thin next to the
    references."""
    return (SIZE_PARAGRAPH, SIZE_PARAGRAPH_PX) if card_w >= WIDE_CARD_W else (SIZE_CAPTION, SIZE_CAPTION_PX)


def _card_text_height(card: dict, text_w: float, head_px: float, body_px: float) -> float:
    h = _text_lines(card["heading"], text_w, head_px, avg_char_ratio=0.58) * head_px * 1.3
    if card.get("paragraph"):
        h += 8 + _text_lines(card["paragraph"], text_w, body_px, avg_char_ratio=0.5) * body_px * 1.45
    return h


def _measure_card_row_height(cards: list[dict], width: float, pad: float = 24,
                             layout: str = "stacked") -> float:
    """The natural height of a row of cards at `width`px total — the tallest
    card's content plus padding. `layout="stacked"` is anchor over text (the
    reference card); `"horizontal"` is anchor left, text right — about half
    the height, for a single column of cards beside an image."""
    gutter = 8
    n = len(cards)
    card_w = (width - gutter * (n - 1)) / n
    head_size, head_px = _card_heading_size(card_w)
    body_size, body_px = _card_body_size(card_w)
    tallest = 0.0
    for card in cards:
        if card.get("image"):
            continue        # an image cell takes the row's height, it doesn't set it
        anchor = ICON_ANCHOR_SIZE if card.get("icon") else ANCHOR_SIZE
        if layout == "horizontal":
            text_w = card_w - 2 * pad - anchor - CARD_H_TEXT_GAP
            h = max(anchor, _card_text_height(card, text_w, head_px, body_px))
        else:
            h = anchor + ANCHOR_TEXT_GAP + _card_text_height(card, card_w - 2 * pad, head_px, body_px)
        tallest = max(tallest, h + 2 * pad)
    return tallest


def _grid_rows(cards: list, columns: int) -> list[list]:
    return [cards[i:i + columns] for i in range(0, len(cards), columns)]


def _default_columns(n: int) -> int:
    """How a card set divides by default: up to 4 on one row (a 4-up row is
    the reference's own gtm-dept-cards shape), 5–6 as two rows of three
    (benefit-cards.jpg, compliance-risk-grid.jpg). Pass `columns` explicitly
    for a 2×2 (exec-summary-3col.jpg's right panel) or a 2×3."""
    return n if n <= 4 else 3


def _measure_card_grid_height(cards: list[dict], width: float, columns: int, pad: float = 24,
                              layout: str = "stacked") -> tuple[float, int]:
    """(total height, uniform row height) for a card grid — every row takes
    the tallest row's height so the grid reads as one object."""
    rows = _grid_rows(cards, columns)
    # measure each row at a full row's width so partial last rows don't widen
    filler = [{"heading": "", "paragraph": ""}]
    row_h = max(_measure_card_row_height((r + filler * (columns - len(r))), width, pad, layout) for r in rows)
    return row_h * len(rows) + 8 * (len(rows) - 1), row_h


def _default_card_layout(columns: int, layout: str | None) -> str:
    """Cards are stacked (anchor over text) unless asked otherwise; the
    renderers switch a set to horizontal (anchor left, text right) only when
    the stacked form would not fit its room — user corrections 2026-09-21/22:
    spare room → stack the cards vertically as full-width cards; overflow →
    go horizontal. Never squeeze, never leave tall empty columns."""
    return layout or "stacked"


def _stat_figure_size(card_w: float):
    """A Display figure needs room: "400%" sets about 170px wide at 64px, so
    on a stat card narrower than SMALL_CARD_W (a stats panel inside a split,
    a 4-up row) it wraps its last glyph onto a second line and shoves the
    caption out of the card. Step the figure down one token — H1 — rather
    than letting it overflow. It is still by far the largest thing on the
    card, so it still reads as the anchor."""
    return (SIZE_H1, 48) if card_w <= SMALL_CARD_W else (SIZE_DISPLAY, SIZE_DISPLAY_PX)


def _measure_stat_row_height(stats: list[dict], width: float, pad: float = 24,
                             style: str = "card") -> float:
    """The natural height of a row of stat cards — see
    `_measure_card_row_height`'s docstring for why this exists. Stat cards
    are exempt from the icon/number-badge anchor (the figure itself is the
    anchor) but not from this — see deck-design-brain.md 'Numbers / stats'.
    `style="rule"` measures the bare, stacked form: one figure under another,
    each beside a brand rule, no card and no side padding."""
    if style == "rule":
        inner_w = width - ACCENT_RULE_W - 20
        total = 0.0
        for stat in stats:
            h = _text_lines(stat["value"], inner_w, SIZE_DISPLAY_PX, avg_char_ratio=0.68) * SIZE_DISPLAY_PX * 1.1
            h += 4 + _text_lines(stat["label"], inner_w, SIZE_PARAGRAPH_PX, avg_char_ratio=0.5) * SIZE_PARAGRAPH_PX * 1.3
            if stat.get("desc"):
                h += 2 + _text_lines(stat["desc"], inner_w, SIZE_CAPTION_PX, avg_char_ratio=0.5) * SIZE_CAPTION_PX * 1.45
            total += h + RULE_STAT_GAP
        return total - RULE_STAT_GAP
    gutter = 8
    n = len(stats)
    card_w = (width - gutter * (n - 1)) / n
    inner_w = card_w - 2 * pad
    fig_size, fig_px = _stat_figure_size(card_w)
    tallest = 0.0
    for stat in stats:
        # 0.68, not the body text's 0.55: bold display digits and especially
        # "%" are much wider per character than running text.
        h = _text_lines(stat["value"], inner_w, fig_px, avg_char_ratio=0.68) * fig_px * 1.15
        h += 8 + _text_lines(stat["label"], inner_w, SIZE_CAPTION_PX, avg_char_ratio=0.58) * SIZE_CAPTION_PX * 1.3
        if stat.get("desc"):
            h += 4 + _text_lines(stat["desc"], inner_w, SIZE_CAPTION_PX, avg_char_ratio=0.5) * SIZE_CAPTION_PX * 1.45
        else:
            # Figure + caption only: the caption is a short line sitting right
            # under a 64px figure, and equal padding leaves it looking dropped
            # against the card's bottom edge. Deepen the floor instead.
            h += STAT_NO_DESC_PAD
        h += 2 * pad + STAT_BOTTOM_EXTRA     # triple bottom padding — see the constant
        tallest = max(tallest, h)
    return tallest


# ── Core slide-role builders ──────────────────────────────────────────────
# Each mirrors a recipe in docs/deck-design-brain.md section C. Title
# placement follows Design DNA: cover = bottom-left, every other slide =
# top-left, flush at the 48px padding origin. No eyebrow text anywhere, no
# gradient blobs anywhere — both banned system-wide (CLAUDE.md).

def _add_cover_top_right_metadata(slide, metadata: dict, muted_color: RGBColor):
    """`{"framing": str, "prepared_for": str}` — a thin divider, a framing
    line, another divider, then "Prepared for: ...", right-aligned. See
    Cover01 in references/decks/cover/."""
    block_w = 320
    left = SLIDE_W_PX - PAGE_PADDING_PX - block_w
    y = PAGE_PADDING_PX

    def divider(y):
        conn = _no_shadow(slide.shapes.add_connector(
            MSO_CONNECTOR.STRAIGHT, px(left), px(y), px(left + block_w), px(y)))
        conn.line.color.rgb = muted_color
        conn.line.width = Pt(0.75)

    divider(y)
    y += 10
    _, tf = _textbox(slide, left, y, block_w, 34)
    tf.paragraphs[0].alignment = PP_ALIGN.RIGHT
    _set_run(tf.paragraphs[0].add_run(), metadata["framing"], SIZE_CAPTION, False, muted_color)
    y += 40
    divider(y)
    y += 10
    _, tf2 = _textbox(slide, left, y, block_w, 60)
    tf2.paragraphs[0].alignment = PP_ALIGN.RIGHT
    _set_run(tf2.paragraphs[0].add_run(), f"Prepared for: {metadata['prepared_for']}", SIZE_CAPTION, False, muted_color)


def _add_cover_bottom_columns(slide, metadata: dict, content_color: RGBColor, muted_color: RGBColor):
    """`{"prepared_by": [...], "prepared_for": [...], "prepared_by_label",
    "prepared_for_label"}` — two columns near the bottom edge, each a thin
    divider over a small label, names below (the first "prepared_by" line
    bold, matching Cover03 in references/decks/cover/)."""
    content_w = SLIDE_W_PX - 2 * PAGE_PADDING_PX
    gap = 48
    col_w = (content_w - gap) / 2
    top = SLIDE_H_PX - PAGE_PADDING_PX - 130
    columns = [
        (metadata.get("prepared_by_label", "Prepared by"), metadata["prepared_by"], True),
        (metadata.get("prepared_for_label", "Prepared for"), metadata["prepared_for"], False),
    ]
    for i, (label, names, bold_first) in enumerate(columns):
        left = PAGE_PADDING_PX + i * (col_w + gap)
        conn = _no_shadow(slide.shapes.add_connector(
            MSO_CONNECTOR.STRAIGHT, px(left), px(top), px(left + col_w), px(top)))
        conn.line.color.rgb = muted_color
        conn.line.width = Pt(0.75)
        _, tf = _textbox(slide, left, top + 10, col_w, 20)
        _set_run(tf.paragraphs[0].add_run(), label, SIZE_CAPTION, False, muted_color)
        _, tf2 = _textbox(slide, left, top + 36, col_w, 80)
        for j, name in enumerate(names):
            p = tf2.paragraphs[0] if j == 0 else tf2.add_paragraph()
            if j > 0:
                p.space_before = Pt(4)
            _set_run(p.add_run(), name, SIZE_PARAGRAPH, bold_first and j == 0, content_color)


def _draw_cover_gradient(slide):
    """The cover gradient — deck-design-brain.md Design DNA -> Color: flat
    dark to ~48% down, through brand purple, to pink at the bottom edge.
    Stops pixel-sampled from references/decks/cover/ (2026-09-18), identical
    across all three reference covers. Shared by the cover and the back
    cover, which are the only two places it is allowed."""
    rect = _no_shadow(slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, px(0), px(0), px(SLIDE_W_PX), px(SLIDE_H_PX)))
    rect.line.fill.background()
    _set_vertical_gradient(rect, [
        (0.0, C.DARK_BG[0]), (0.48, C.DARK_BG[0]), (0.78, C.BRAND), (1.0, C.PINK),
    ])
    return rect


def add_cover(prs, title: str, subtitle: str | None = None,
              client_name: str | None = None, client_logo_path: str | None = None,
              metadata: dict | None = None):
    """The deck's opening slide — see deck-design-brain.md "Cover," grounded
    in three real reference covers (references/decks/cover/). Always the
    cover gradient, dark theme, white text — this recipe takes no `theme`
    parameter because the background is fixed.

    `client_name` / `client_logo_path`: pass `client_name` when the deck is
    for a specific named account — the logo lockup then pairs the Smartcat
    wordmark with the client's own logo. Pass `client_logo_path` (a local
    image file) to embed the real client logo; omit it and a labeled
    placeholder stands in instead (deck-design-brain.md Design DNA, "A
    missing image or logo asset gets a placeholder"). Omit `client_name`
    entirely for a generic, non-client cover — Smartcat's logo alone.

    `metadata` is optional, and at most one of:
      {"style": "top_right", "framing": str, "prepared_for": str}
      {"style": "bottom_columns", "prepared_by": [str, ...], "prepared_for": [str, ...],
       "prepared_by_label": str, "prepared_for_label": str}   (labels optional)
      {"style": "footer", "text": str}
    Omit it for the simplest generic cover — logo + title + optional subtitle.
    """
    slide = add_blank_slide(prs, theme="dark", layer=0)
    content_color = C.DARK_PRIMARY
    muted_color = C.PINK_40      # the cover's small metadata type — pink-40
    _draw_cover_gradient(slide)

    # Logo lockup, top-left — always present.
    logo_h = 24
    _, logo_w = draw_logo(slide, "white", PAGE_PADDING_PX, PAGE_PADDING_PX, logo_h)
    if client_name:
        client_left = PAGE_PADDING_PX + logo_w + 20
        if client_logo_path:
            slide.shapes.add_picture(client_logo_path, px(client_left), px(PAGE_PADDING_PX), height=px(logo_h))
        else:
            add_placeholder(slide, client_left, PAGE_PADDING_PX - 4, 160, logo_h + 8,
                             f"Logo: {client_name}", theme="dark")

    # Title + optional subtitle — lower-middle band (Design DNA "Title
    # placement"). Sits higher when a bottom_columns metadata block needs
    # room below it, lower when the cover is otherwise bare.
    title_top = 210 if (metadata and metadata.get("style") == "bottom_columns") else 320
    _, tf = _textbox(slide, PAGE_PADDING_PX, title_top, SLIDE_W_PX - 2 * PAGE_PADDING_PX, 220)
    p = tf.paragraphs[0]
    _set_run(p.add_run(), title, SIZE_DISPLAY, True, content_color, FONT_HEADING)
    if subtitle:
        p2 = _body(tf.add_paragraph())
        p2.space_before = Pt(12)
        # purple-40, a step cooler and lighter than the pink-40 metadata line,
        # so the two small lines on the cover stay distinguishable.
        _set_run(p2.add_run(), subtitle, SIZE_PARAGRAPH, False, C.PURPLE_40)

    if metadata:
        style = metadata["style"]
        if style == "top_right":
            _add_cover_top_right_metadata(slide, metadata, muted_color)
        elif style == "bottom_columns":
            _add_cover_bottom_columns(slide, metadata, content_color, muted_color)
        elif style == "footer":
            _, tf3 = _textbox(slide, PAGE_PADDING_PX, SLIDE_H_PX - PAGE_PADDING_PX - 20,
                               SLIDE_W_PX - 2 * PAGE_PADDING_PX, 20)
            _set_run(tf3.paragraphs[0].add_run(), metadata["text"], SIZE_CAPTION, False, muted_color)
        else:
            raise ValueError(f"add_cover: unknown metadata style {style!r}")
    return _mark(slide, "cover")


def add_back_cover(prs, title: str = "Thank you!", metadata_text: str | None = None):
    """The deck's last slide — the cover's bookend. Same cover gradient, the
    sign-off top-left at Display scale, the cover's metadata line repeated
    bottom-left, and the Smartcat wordmark bottom-right (the only slide
    besides the cover that carries the wordmark — see deck-design-brain.md
    Design DNA, "No chrome"). Takes no `theme`: like the cover, the
    background is fixed."""
    slide = add_blank_slide(prs, theme="dark", layer=0)
    _draw_cover_gradient(slide)

    _, tf = _textbox(slide, PAGE_PADDING_PX, PAGE_PADDING_PX,
                      SLIDE_W_PX - 2 * PAGE_PADDING_PX, 100)
    _set_run(tf.paragraphs[0].add_run(), title, SIZE_DISPLAY, True, C.DARK_PRIMARY, FONT_HEADING)

    logo_h = 24
    _, logo_w = draw_logo(slide, "white", 0, SLIDE_H_PX - PAGE_PADDING_PX - logo_h, logo_h)
    # draw_logo places from the left, so reposition to the right margin now
    # that its rendered width is known.
    for shp in slide.shapes:
        if shp.shape_type == 13 and shp.top == px(SLIDE_H_PX - PAGE_PADDING_PX - logo_h):
            shp.left = px(SLIDE_W_PX - PAGE_PADDING_PX - logo_w)

    if metadata_text:
        _, tf2 = _textbox(slide, PAGE_PADDING_PX, SLIDE_H_PX - PAGE_PADDING_PX - 20,
                           SLIDE_W_PX - 2 * PAGE_PADDING_PX - logo_w - 40, 20)
        _body(tf2.paragraphs[0])
        _set_run(tf2.paragraphs[0].add_run(), metadata_text, SIZE_CAPTION, False, C.PINK_40)
    return _mark(slide, "back-cover")


def add_section_divider(prs, title: str, theme: str = "dark", number: str | None = None,
                        items: list[str] | None = None, image_caption: str | None = None):
    """A chapter opener. Plain form: one Display title top-left, nothing else.

    Three optional devices from the reference set, combinable. Everything
    stays anchored at the TOP — a chapter numeral, then the title under it,
    then the list under that. The reference "title in the lower band" form
    was tried and rejected by the user (2026-09-21): only the cover and back
    cover place their content low; every other slide reads from the top-left.
    - `number` ("01", "2.0"): a Display-scale chapter numeral in brand purple
      at the top-left origin, the title directly below it.
    - `items`: 2–6 short lines listing what the chapter covers, as a ruled
      list under the title — body size, secondary, one roomy row each,
      bracketed by a rule above the first and under the last. An item is a
      plain string, or `{"label": str, "icon": str}` to lead the row with a
      design-system icon (a deck_icons.ICONS key) in the same muted tone as
      the text; a divider's one accent is its title, so the icons stay
      quiet rather than brand-purple.
    - `image_caption`: a reserved product-UI slot filling the right ~45% at
      full height, square (the promo shots' shape) and inside the padding —
      a chapter opener that shows the surface the chapter is about. Nothing
      bleeds off the edge; the 48px frame holds.
    """
    slide = add_blank_slide(prs, theme=theme, layer=0)
    content_w = SLIDE_W_PX - 2 * PAGE_PADDING_PX
    content_h = SLIDE_H_PX - 2 * PAGE_PADDING_PX
    text_w = content_w * 0.5 if image_caption else content_w
    title_top = PAGE_PADDING_PX
    if number:
        _, tfn = _textbox(slide, PAGE_PADDING_PX, PAGE_PADDING_PX, text_w, 77)
        _set_run(tfn.paragraphs[0].add_run(), number, SIZE_DISPLAY, True, brand_content(theme), FONT_HEADING)
        title_top = PAGE_PADDING_PX + 77 + 24        # numeral, then the title right under it
    title_lines = _text_lines(title, text_w, 64, avg_char_ratio=0.55)
    title_h = title_lines * 77
    _, tf = _textbox(slide, PAGE_PADDING_PX, title_top, text_w, title_h)
    _set_run(tf.paragraphs[0].add_run(), title, SIZE_DISPLAY, True, primary(theme), FONT_HEADING)
    if items:
        # A ruled list is BRACKETED — a rule above the first row and under
        # every row, including the last — with rows at DIVIDER_ITEM_ROW_H and
        # an optional icon per line. Rules between rows alone, at a tight
        # line pitch, read as underlined text rather than a list
        # (user correction 2026-09-22).
        list_w = text_w * 0.8
        y = title_top + title_h + DIVIDER_LIST_TOP_GAP
        _hairline(slide, PAGE_PADDING_PX, y, PAGE_PADDING_PX + list_w, y, theme)
        for it in items:
            label = it["label"] if isinstance(it, dict) else it
            icon = it.get("icon") if isinstance(it, dict) else None
            text_left = PAGE_PADDING_PX
            if icon:
                draw_icon(slide, icon, PAGE_PADDING_PX,
                          y + (DIVIDER_ITEM_ROW_H - DIVIDER_ITEM_ICON) / 2,
                          DIVIDER_ITEM_ICON, secondary(theme))
                text_left = PAGE_PADDING_PX + DIVIDER_ITEM_ICON + DIVIDER_ITEM_TEXT_GAP
            _, tfi = _textbox(slide, text_left, y, PAGE_PADDING_PX + list_w - text_left,
                              DIVIDER_ITEM_ROW_H)
            tfi.vertical_anchor = MSO_ANCHOR.MIDDLE
            _set_run(tfi.paragraphs[0].add_run(), label, SIZE_PARAGRAPH, False, secondary(theme))
            y += DIVIDER_ITEM_ROW_H
            _hairline(slide, PAGE_PADDING_PX, y, PAGE_PADDING_PX + list_w, y, theme)
    if image_caption:
        img_h = content_h
        img_w = min(img_h, content_w * 0.45)
        draw_image_slot(slide, SLIDE_W_PX - PAGE_PADDING_PX - img_w, PAGE_PADDING_PX + (content_h - img_h) / 2,
                        img_w, img_h, image_caption, theme, align="right")
    return _mark(slide, "divider")


def _add_slide_title(slide, title: str) -> float:
    """Place the slide title and return the y where content may start.

    A title is not always one line — several reference slides run to two
    (exec-summary-3col.jpg). The content top is therefore measured from the
    title's LAST line, not from a fixed offset: with a one-line title this
    returns the usual PAGE_PADDING + HEADING_GAP, and a wrapped title pushes
    content down instead of letting it slide under the second line. Every
    builder below uses the returned value rather than recomputing the
    constant, so this holds for every slide type.
    """
    theme = slide._smartcat_theme
    width = SLIDE_W_PX - 2 * PAGE_PADDING_PX
    lines = _text_lines(title, width, SIZE_H1_PX, avg_char_ratio=0.52)
    box_h = max(60.0, lines * H1_LINE_PX)
    tb, tf = _textbox(slide, PAGE_PADDING_PX, PAGE_PADDING_PX, width, box_h)
    p = tf.paragraphs[0]
    _set_run(p.add_run(), title, SIZE_H1, True, _content_color(slide), FONT_HEADING)
    top = max(PAGE_PADDING_PX + HEADING_GAP_PX,
              PAGE_PADDING_PX + lines * H1_LINE_PX + TITLE_CLEARANCE_PX)
    slide._smartcat_content_top = top      # read back by check_canvas_fill
    slide._smartcat_title_shape = tb
    return top


def add_heading_paragraph(prs, title: str, paragraph: str, theme: str = "light"):
    slide = add_blank_slide(prs, theme=theme)
    top = _add_slide_title(slide, title)
    _, tf = _textbox(slide, PAGE_PADDING_PX, top,
                      (SLIDE_W_PX - 2 * PAGE_PADDING_PX) // 2, SLIDE_H_PX - top - PAGE_PADDING_PX)
    p = _body(tf.paragraphs[0])
    _set_run(p.add_run(), paragraph, SIZE_PARAGRAPH, False, secondary(theme))
    return _mark(slide, "prose")


def add_bullet_list(prs, title: str, bullets: list[str], theme: str = "light"):
    slide = add_blank_slide(prs, theme=theme)
    top = _add_slide_title(slide, title)
    _, tf = _textbox(slide, PAGE_PADDING_PX, top,
                      (SLIDE_W_PX - 2 * PAGE_PADDING_PX) // 2, SLIDE_H_PX - top - PAGE_PADDING_PX)
    for i, item in enumerate(bullets):
        p = _body(tf.paragraphs[0] if i == 0 else tf.add_paragraph())
        p.space_after = Pt(10)
        _set_run(p.add_run(), f"•  {item}", SIZE_PARAGRAPH, False, secondary(theme))   # body copy = secondary
    return _mark(slide, "list")


def _draw_card_row(slide, cards: list[dict], left0: float, top: float, width: float,
                    height: float, theme: str, pad: float = 24, number_offset: int = 0,
                    layout: str = "stacked"):
    """Shared by add_cards and any composition that needs a card grid inside
    a sub-region of the slide (add_split's 'cards' panel, add_flow_chain's
    detail row) — see docs/deck-design-brain.md 'Enumerated content -> N
    cards'. `width`/`height` are the row's actual box — callers size `height`
    to the content via `_measure_card_row_height` and center the row when it
    leaves extra room, rather than stretching cards to fill the slide (see
    Design DNA "Surfaces"). Cards divide `width` evenly with the 8px gutter,
    per Design DNA 'Gutter vs. slide padding'.

    Each card carries a visual anchor (Design DNA "Surfaces") — pass
    `card["icon"]` (a deck_icons.ICONS key) for a specific icon, or omit it
    for an automatic numbered circle badge (1-based, in row order)."""
    gutter = 8
    n = len(cards)
    card_w = (width - gutter * (n - 1)) / n
    head_size, _ = _card_heading_size(card_w)
    body_size, _ = _card_body_size(card_w)
    for i, card in enumerate(cards):
        left = left0 + i * (card_w + gutter)
        if card.get("image"):
            # One (or more) cells of the row given over to a product shot,
            # at exactly the card's own size, radius and gutter — the
            # image-cell pattern from the reference decks. The row still
            # reads as one object because nothing but the fill changes.
            draw_image_slot(slide, left, top, card_w, height, card["image"], theme)
            continue
        # A featured card — the one promoted option among peers (Design DNA,
        # "Hierarchy within a repeated component") — takes the solid brand
        # fill with white text; everything else about it stays identical.
        featured = bool(card.get("featured"))
        surface = C.BRAND if featured else panel_fill(theme)
        text_primary = C.WHITE if featured else primary(theme)
        text_secondary = C.PURPLE_40 if featured else secondary(theme)
        _rounded_rect(slide, left, top, card_w, height, surface)
        icon = card.get("icon")
        anchor_h = _draw_card_anchor(slide, "icon" if icon else "number", icon or (number_offset + i + 1),
                                      left + pad, top + pad, theme, surface=surface)
        if layout == "horizontal":
            # Anchor left, text right, both top-aligned at the padding.
            text_left = left + pad + anchor_h + CARD_H_TEXT_GAP
            _, tf = _textbox(slide, text_left, top + pad, left + card_w - pad - text_left, height - 2 * pad)
        else:
            text_top = top + pad + anchor_h + ANCHOR_TEXT_GAP
            _, tf = _textbox(slide, left + pad, text_top, card_w - 2 * pad, height - (text_top - top) - pad)
        p = tf.paragraphs[0]
        _set_run(p.add_run(), card["heading"], head_size, True, text_primary, FONT_HEADING)
        if card.get("paragraph"):
            p2 = _body(tf.add_paragraph())
            p2.space_before = Pt(8)
            _set_run(p2.add_run(), card["paragraph"], body_size, False, text_secondary)


def _draw_card_grid(slide, cards: list[dict], left0: float, top: float, width: float,
                     columns: int, row_h: float, theme: str, pad: float = 24, layout: str = "stacked"):
    """A grid of cards, `columns` per row, every row `row_h` tall — the 2×2 /
    2×3 shapes from exec-summary-3col.jpg, benefit-cards.jpg and
    compliance-risk-grid.jpg. A partial last row keeps the full grid's card
    width (benefit-cards.jpg's 3+2), so cards never widen to fill the row.
    Numbered badges run on across rows."""
    rows = _grid_rows(cards, columns)
    gutter = 8
    card_w = (width - gutter * (columns - 1)) / columns
    y = top
    count = 0
    for r in rows:
        row_w = card_w * len(r) + gutter * (len(r) - 1)
        _draw_card_row(slide, r, left0, y, row_w, row_h, theme, pad=pad, number_offset=count, layout=layout)
        count += len(r)
        y += row_h + gutter


def _draw_stat_row(slide, stats: list[dict], left0: float, top: float, width: float,
                    height: float, theme: str, pad: float = 24, style: str = "card"):
    """Shared by add_stats and add_split's 'stat' panel (a single highlighted
    stat filling one side of an asymmetric split, e.g. math-savings.jpg) —
    see deck-design-brain.md 'Quantitative & proof -> Numbers / stats'.
    Each stat may include an optional `desc` line under the label.

    `style="rule"` — the bare form from the reference set: no card; each
    figure stacked under the previous with a solid brand-purple vertical
    rule at its left, the label in body type and an optional desc line.
    Reads as editorial evidence beside a paragraph rather than a KPI row."""
    if style == "rule":
        inner_w = width - ACCENT_RULE_W - 20
        y = top
        for stat in stats:
            h = _measure_stat_row_height([stat], width, pad, style="rule")
            _accent_rule(slide, left0, y, h)
            _, tf = _textbox(slide, left0 + ACCENT_RULE_W + 20, y, inner_w, h)
            p = tf.paragraphs[0]
            _set_run(p.add_run(), stat["value"], SIZE_DISPLAY, True, brand_content(theme), FONT_HEADING)
            p2 = _body(tf.add_paragraph())
            p2.space_before = Pt(3)
            _set_run(p2.add_run(), stat["label"], SIZE_PARAGRAPH, False, primary(theme))
            if stat.get("desc"):
                p3 = _body(tf.add_paragraph())
                _set_run(p3.add_run(), stat["desc"], SIZE_CAPTION, False, secondary(theme))
            y += h + RULE_STAT_GAP
        return
    gutter = 8
    n = len(stats)
    card_w = (width - gutter * (n - 1)) / n
    fig_size, _ = _stat_figure_size(card_w)
    for i, stat in enumerate(stats):
        left = left0 + i * (card_w + gutter)
        _rounded_rect(slide, left, top, card_w, height, panel_fill(theme))
        _, tf = _textbox(slide, left + pad, top + pad, card_w - 2 * pad,
                          max(20.0, height - 2 * pad - STAT_BOTTOM_EXTRA))
        p = tf.paragraphs[0]
        _set_run(p.add_run(), stat["value"], fig_size, True, brand_content(theme), FONT_HEADING)
        p2 = _body(tf.add_paragraph())
        p2.space_before = Pt(8)
        _set_run(p2.add_run(), stat["label"], SIZE_CAPTION, True, primary(theme))
        if stat.get("desc"):
            p3 = _body(tf.add_paragraph())
            p3.space_before = Pt(4)
            _set_run(p3.add_run(), stat["desc"], SIZE_CAPTION, False, secondary(theme))


def add_cards(prs, title: str, cards: list[dict], theme: str = "light", columns: int | None = None,
              layout: str | None = None):
    """cards: [{heading, paragraph, icon, featured, image}], 2–6 items — see
    docs/deck-design-brain.md 'Enumerated content -> N cards'. `icon` is
    optional per card (a deck_icons.ICONS key); omit it for an automatic
    numbered badge. `featured: True` on at most one card promotes it with the
    solid brand fill (Design DNA, "Hierarchy within a repeated component").

    `columns` picks the grid: default one row for 2–4 cards, two rows of
    three for 5–6. Pass `columns=2` on four cards for the 2×2 grid
    (exec-summary-3col.jpg), which is the better shape whenever each card
    carries a real paragraph — a 4-up row forces caption-size copy.

    Height: the grid sizes to its own content (`_measure_card_grid_height`)
    but never below MIN_CONTENT_FILL of the space under the title, and it is
    vertically centered in that space. The floor is what stops a two-line
    card row rendering as a squat strip in an empty slide; if the floor is
    doing most of the work, the content is too thin for this shape — use two
    rows, a split, or merge slides (see the brain's Design DNA "Surfaces")."""
    assert 2 <= len(cards) <= 6, "N-cards recipe is 2-6 items"
    columns = columns or _default_columns(len(cards))
    assert 1 <= columns <= 4 and columns <= len(cards)
    assert sum(1 for c in cards if c.get("featured")) <= 1, "at most one featured card"
    slide = add_blank_slide(prs, theme=theme)
    top = _add_slide_title(slide, title)
    content_w = SLIDE_W_PX - 2 * PAGE_PADDING_PX
    avail_h = SLIDE_H_PX - top - PAGE_PADDING_PX
    n_rows = len(_grid_rows(cards, columns))
    layout = _default_card_layout(columns, layout)
    total_h, row_h = _measure_card_grid_height(cards, content_w, columns, layout=layout)
    if total_h > avail_h and layout == "stacked":
        # Too tall for the room: never squeeze the text — go horizontal, which
        # roughly halves each card. If that still doesn't fit, check_text_fit
        # will flag it and the content wants two slides.
        layout = "horizontal"
        total_h, row_h = _measure_card_grid_height(cards, content_w, columns, layout=layout)
    floor = MIN_CONTENT_FILL * avail_h
    if total_h < floor:
        row_h = (floor - 8 * (n_rows - 1)) / n_rows
        total_h = floor
    if total_h > avail_h:
        row_h = (avail_h - 8 * (n_rows - 1)) / n_rows
        total_h = avail_h
    grid_top = top + max(0, (avail_h - total_h) / 2)
    _draw_card_grid(slide, cards, PAGE_PADDING_PX, grid_top, content_w, columns, row_h, theme, layout=layout)
    return _mark(slide, "grid" if n_rows > 1 else "row")


def add_placeholder(slide, left: float, top: float, width: float, height: float,
                     label: str, theme: str = "light"):
    """A labeled placeholder for a missing image/logo asset (a customer logo,
    a screenshot, a partner icon tile) — a dashed-border panel holding the
    design system's `placeholder` icon centered, with a caption naming
    exactly what belongs there. Use wherever a real asset would go but isn't
    available at build time — see deck-design-brain.md Design DNA, "A
    missing image or logo asset gets a placeholder, not a gap." Not a
    standalone slide role — call it from within another slide's layout code
    (a card's image slot, a logo-wall tile, a split panel)."""
    rect = _rounded_rect(slide, left, top, width, height, panel_fill(theme), radius_ratio=0.08)
    rect.line.fill.solid()
    rect.line.color.rgb = secondary(theme)
    rect.line.width = Pt(1)
    _set_line_dash(rect.line)
    icon_size = min(28, height * 0.3)
    label_h = 20
    icon_top = top + (height - icon_size - label_h - 6) / 2
    draw_icon(slide, "placeholder", left + (width - icon_size) / 2, icon_top, icon_size, secondary(theme))
    _, tf = _textbox(slide, left + 8, icon_top + icon_size + 6, width - 16, label_h)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    _set_run(p.add_run(), label, SIZE_CAPTION, False, secondary(theme))
    return rect


def draw_image_slot(slide, left: float, top: float, width: float, height: float,
                     caption: str, theme: str = "light", align: str = "center"):
    """A RESERVED slot for a product-UI screenshot. Draws the exact rectangle
    the image must fill, and labels it with what belongs there plus the size
    and aspect ratio to export at.

    **Always call this first, for every slide about a product surface — even
    when you already expect a match in `images/promo-ui-mockups/`.** Reserve
    now, look up and fill later with `fill_image_slot` (see below). Never
    skip this call because a real file seems likely; the two steps are
    required in that order (CLAUDE.md "Promo UI mockups") so a slide never
    silently loses its slot just because the lookup pass gets missed.

    This is not `add_placeholder`. That one covers an asset we meant to have
    and didn't (a customer logo, a partner tile) and is a build-time gap.
    This is a deliberate composition decision: the slide argues about a
    product surface, so the layout holds room for it. The two look different
    on purpose — this one is brand-purple and states its dimensions, because
    somebody has to go and produce an image of exactly that shape.

    Stating the pixel size and ratio is the whole point. A slot that only
    says "screenshot here" gets filled with whatever crop is to hand, and
    the layout breaks when it lands.
    """
    start_idx = len(slide.shapes)
    slot = _rounded_rect(slide, left, top, width, height, panel_fill(theme), radius_ratio=0.04)
    slot.line.fill.solid()
    slot.line.color.rgb = brand_content(theme)
    slot.line.width = Pt(1.25)
    _set_line_dash(slot.line)

    ratio = _aspect_label(width, height)
    icon_size = min(32, height * 0.22)
    cap_h, dim_h, gapv = 20, 18, 8
    block_h = icon_size + gapv + cap_h + dim_h
    icon_top = top + (height - block_h) / 2
    draw_icon(slide, "image", left + (width - icon_size) / 2, icon_top, icon_size,
              brand_content(theme))

    _, tf = _textbox(slide, left + 16, icon_top + icon_size + gapv, width - 32, cap_h)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    _set_run(p.add_run(), caption, SIZE_CAPTION, True, primary(theme))

    _, tf2 = _textbox(slide, left + 16, icon_top + icon_size + gapv + cap_h, width - 32, dim_h)
    p2 = tf2.paragraphs[0]
    p2.alignment = PP_ALIGN.CENTER
    _set_run(p2.add_run(), f"{round(width)} \u00d7 {round(height)} px \u00b7 {ratio}",
             SIZE_CAPTION, False, C.LIGHT_SECONDARY if theme == "light" else C.DARK_SECONDARY)
    shapes = list(slide.shapes)[start_idx:]
    slide._smartcat_image_slots = getattr(slide, "_smartcat_image_slots", []) + [
        {"caption": caption, "filled": False, "left": left, "top": top,
         "width": width, "height": height, "theme": theme, "shapes": shapes, "align": align}
    ]
    return slot


def draw_product_image(slide, image_path: str, left: float, top: float, width: float,
                        height: float, caption: str | None = None, align: str = "center"):
    """Embed a REAL product screenshot into the given box. This is the
    low-level primitive `fill_image_slot` uses \u2014 call it directly only when
    there is no reserved slot to replace (the normal path is: reserve with
    `draw_image_slot` first, then call `fill_image_slot`, not this).

    The usual source is `images/promo-ui-mockups/`, matched by filename to
    what the slide is about \u2014 see CLAUDE.md "Promo UI mockups" for the folder
    layout and the `<description> -- <tag> - <tag>` naming convention to
    match against.

    Contain-fit, never stretched or cropped: placed at native size first to
    read the file's real aspect ratio (no Pillow dependency needed \u2014 pptx's
    own picture object exposes it), then scaled down to the largest size that
    fits inside (width, height) and centered in that box.

    Still recorded on `_smartcat_image_slots` (with `filled=True`) so
    `check_missing_image_slots` treats the slide as handled and
    `image_slots()` can tell a filled slide from one still holding an empty
    reserved slot in the handoff report."""
    pic = slide.shapes.add_picture(image_path, px(left), px(top))
    native_w, native_h = pic.width, pic.height
    scale = min(px(width) / native_w, px(height) / native_h)
    new_w, new_h = round(native_w * scale), round(native_h * scale)
    pic.width, pic.height = new_w, new_h
    slack = px(width) - new_w
    # Horizontal slack: a side-panel slot aligns the picture toward the copy
    # it illustrates ("left"/"right"); a banner or stack panel centres it.
    pic.left = px(left) + (0 if align == "left" else slack if align == "right" else round(slack / 2))
    pic.top = px(top) + round((px(height) - new_h) / 2)
    _no_shadow(pic)
    label = caption or os.path.basename(image_path)
    # How much of the reserved box the picture actually covers. A square
    # promo shot dropped into a 3:2 or banner slot covers 40–65% and leaves
    # dead flanks — fill_matched_slots reports anything under FIT_WARN so the
    # slide can be reshaped (add_image_split sizes the slot to the image).
    fit = (new_w * new_h) / max(px(width) * px(height), 1)
    slide._smartcat_image_slots = getattr(slide, "_smartcat_image_slots", []) + [
        {"caption": label, "filled": True, "source": image_path, "fit": round(fit, 2),
         "image_aspect": round(native_w / native_h, 2)}
    ]
    return pic


FIT_WARN = 0.75   # a filled image covering less than this share of its slot gets a report line


def fill_image_slot(slide, slot_index: int, image_path: str):
    """The SECOND PASS of the required reserve-then-fill sequence (CLAUDE.md
    "Promo UI mockups"): once a real file has been matched in
    `images/promo-ui-mockups/` for a slot `draw_image_slot` already reserved,
    call this to swap the dashed placeholder for the real picture in the
    exact same box. `slot_index` is that slot's position within
    `slide._smartcat_image_slots` — get it from `image_slots(prs)`'s
    `slot_index` field, matched by that entry's `slide` number.

    Removes the placeholder's rectangle, icon and caption text boxes, then
    draws the real image via `draw_product_image` at the slot's stored
    geometry, and replaces the slot's tracking entry in place — slide order
    and any other slot's index on the same slide are unaffected. Raises if
    the slot is already filled; check `entry["filled"]` first when iterating
    `image_slots(prs)`."""
    slot = slide._smartcat_image_slots[slot_index]
    if slot.get("filled"):
        raise ValueError(f"slot {slot_index} on this slide is already filled")
    for shp in slot["shapes"]:
        shp._element.getparent().remove(shp._element)
    pic = draw_product_image(slide, image_path, slot["left"], slot["top"],
                              slot["width"], slot["height"], caption=slot["caption"],
                              align=slot.get("align", "center"))
    # draw_product_image reassigns slide._smartcat_image_slots to a NEW list
    # (it appends via `+`, not in place) — re-fetch it before popping/indexing,
    # rather than reusing a `slots` reference captured before that call.
    new_entry = slide._smartcat_image_slots.pop()
    slide._smartcat_image_slots[slot_index] = new_entry
    return pic


def _aspect_label(width: float, height: float) -> str:
    """The slot's ratio, as a target someone can export to. Snaps to a
    familiar ratio only when it genuinely is one — within 4%. Otherwise it
    prints the real number, because a banner labelled "16:9" when it is
    actually 3.9:1 sends the exporter after the wrong crop, which is the one
    failure this label exists to prevent."""
    r = width / height
    known = [(16/9, "16:9"), (3/2, "3:2"), (4/3, "4:3"), (1.0, "1:1"),
             (3/4, "3:4"), (2/3, "2:3"), (9/16, "9:16")]
    best, label = min(known, key=lambda k: abs(k[0] - r))
    if abs(best - r) / r <= 0.04:
        return label
    return f"{r:.2f}:1" if r >= 1 else f"1:{1 / r:.2f}"


def image_slots(prs) -> list[dict]:
    """Every reserved or filled image slot in the deck, in slide order —
    `{"slide", "slot_index", "caption", "filled", "source"}` (`source` only
    present when filled; unfilled entries also carry `left/top/width/height`,
    the box `fill_image_slot` will need). A deck must never be handed over
    without reporting the UNFILLED ones — a dashed purple box reaching a
    customer is worse than a slide with no image at all. Use it to produce
    the shot list on handoff, and — before that — to drive the second pass:
    for each unfilled entry, check `images/promo-ui-mockups/` for a match and
    call `fill_image_slot(prs.slides[entry["slide"] - 1], entry["slot_index"],
    matched_path)` when one exists (see CLAUDE.md "Promo UI mockups").
    `slot_index` is the slide-relative position to pass to `fill_image_slot`;
    the internal `shapes` list is omitted here since it isn't serializable."""
    found = []
    for i, slide in enumerate(prs.slides, start=1):
        for idx, slot in enumerate(getattr(slide, "_smartcat_image_slots", [])):
            public = {k: v for k, v in slot.items() if k != "shapes"}
            found.append({"slide": i, "slot_index": idx, **public})
    return found


def add_stats(prs, title: str, stats: list[dict], theme: str = "light", style: str = "card"):
    """stats: [{value, label}], 2-4 items. Big brand-purple figure (Display
    scale) + bold caption — see deck-design-brain.md 'Quantitative & proof'.
    Keep `value` short — abbreviate large numbers ($1,200,000 -> $1.2M);
    this module does not re-check for overflow the way the HTML path's
    verify step does, so oversized values WILL visually overrun their panel.
    Stat cards are exempt from the icon/number-badge anchor rule (the figure
    is the anchor) but not from the height rule — the row sizes to its own
    content and centers when that leaves extra vertical room, same as
    add_cards."""
    assert 2 <= len(stats) <= 4, "stats recipe is 2-4 items"
    slide = add_blank_slide(prs, theme=theme)
    top = _add_slide_title(slide, title)
    content_w = SLIDE_W_PX - 2 * PAGE_PADDING_PX
    avail_h = SLIDE_H_PX - top - PAGE_PADDING_PX
    # Softer floor than cards (0.4, not 0.5): a stat card is figure + label +
    # an optional line, and a very tall one reads as an empty box with a
    # number in the corner. Give stats a `desc` line, or stack the row over
    # a quote bar (add_stack) — that is the reference shape for stats anyway.
    if style == "rule":
        # Bare rule stats as a whole slide read as a ladder down the left
        # ~45% (the reference stacks two or three under a heading).
        col_w = content_w * 0.45
        h = min(_measure_stat_row_height(stats, col_w, style="rule"), avail_h)
        _draw_stat_row(slide, stats, PAGE_PADDING_PX, top, col_w, h, theme, style="rule")
        return _mark(slide, "statement")
    card_h = min(max(_measure_stat_row_height(stats, content_w), 0.4 * avail_h), avail_h)
    row_top = top + max(0, (avail_h - card_h) / 2)
    _draw_stat_row(slide, stats, PAGE_PADDING_PX, row_top, content_w, card_h, theme)
    return _mark(slide, "row")


# ── Asymmetric split, table, flow-chain ────────────────────────────────────
# Added 2026-09-18 after visually inspecting references/decks/ — real decks
# rarely divide a slide 50/50 or default to a plain card row; see
# docs/deck-design-brain.md section E's changelog entry for the full writeup.
# These three compose from the SAME tokens/helpers as everything above (no
# new geometry, no new colors) — they just place them less evenly, and add
# two shape kinds (native table, connector line) the module didn't use yet.

# An image slot carries its own surface, so it takes the tight 8px gutter
# against another panel and the wide 64px gap against bare copy.
_SPLIT_SURFACE_KINDS = {"cards", "stat", "stats", "table", "image", "rows", "quote-bar", "flow"}


def _panel_heading_height(spec: dict, width: float) -> float:
    """Any panel may carry its own `heading` (H3, heading face, primary) —
    the reference pattern of a split whose right half has a sub-headline
    over its stats ("Multimodal AI is on a rapid growth trajectory")."""
    if not spec.get("heading"):
        return 0.0
    return _text_lines(spec["heading"], width, SIZE_H3_PX, avg_char_ratio=0.52) * SIZE_H3_PX * 1.3 + PANEL_HEADING_GAP


def _split_panel_height(spec: dict, width: float) -> float:
    """A panel's natural height: its optional heading plus its body."""
    return _panel_heading_height(spec, width) + _panel_body_height(spec, width)


def _panel_body_height(spec: dict, width: float) -> float:
    """A panel's natural content height. Card and stat rows measure exactly;
    flowing text, a quote and a table are estimated from the same char-count
    heuristic the cards use. Every kind returns a number so add_split can
    always centre the pair as one block — see its docstring."""
    kind = spec["kind"]
    if kind == "cards":
        cols = spec.get("columns") or _default_columns(len(spec["items"]))
        layout = _default_card_layout(cols, spec.get("layout"))
        return _measure_card_grid_height(spec["items"], width, cols, pad=20, layout=layout)[0]
    if kind == "rows":
        return _measure_numbered_rows_height(spec["items"], width, spec.get("columns", 1))
    if kind == "quote-bar":
        return _measure_quote_bar_height(spec, width)
    if kind == "flow":
        return _measure_flow_height(spec["nodes"], width)
    if kind == "stat":
        return _measure_stat_row_height([spec], width, pad=20, style=spec.get("style", "card"))
    if kind == "stats":
        return _measure_stat_row_height(spec["items"], width, pad=20, style=spec.get("style", "card"))
    if kind == "text":
        h = 0.0
        if spec.get("lead"):
            h += _text_lines(spec["lead"], width, LEAD_PX, avg_char_ratio=0.52) * LEAD_PX * 1.3 + 16
        for para in _as_list(spec.get("paragraph")):
            h += _text_lines(para, width, SIZE_PARAGRAPH_PX, avg_char_ratio=0.5) \
                 * SIZE_PARAGRAPH_PX * BODY_LINE_SPACING * 1.25 + 13
        for b in spec.get("bullets", []):
            h += _text_lines(b, width, SIZE_PARAGRAPH_PX, avg_char_ratio=0.5) \
                 * SIZE_PARAGRAPH_PX * BODY_LINE_SPACING * 1.25 + 13
        if spec.get("features"):
            h += 20 + ceil(len(spec["features"]) / 2) * FEATURE_ROW_H
        return h
    if kind == "facts":
        cols = spec.get("columns", 1)
        return ceil(len(spec["items"]) / cols) * FACT_ROW_H
    if kind == "quote":
        text_w = width - ACCENT_RULE_W - 24
        h = _text_lines(spec["text"], text_w, 32, avg_char_ratio=0.5) * 32 * 1.3
        if spec.get("attribution"):
            h += 21 + SIZE_PARAGRAPH_PX * 1.4
        return h
    if kind == "image":
        # A slot with no explicit height takes a 3:2 landscape shape, the
        # commonest product-screenshot proportion in the reference decks.
        # `aspect` (w/h, e.g. 16/10) overrides that; `height` overrides both.
        return spec.get("height") or width / spec.get("aspect", 1.5)
    if kind == "table":
        return 40.0 + sum(
            max(48.0, max(_text_lines(str(cell), width / len(spec["headers"]) - 32,
                                       SIZE_PARAGRAPH_PX, avg_char_ratio=0.5)
                          for cell in row) * SIZE_PARAGRAPH_PX * 1.5 + 16)
            for row in spec["rows"])
    raise ValueError(f"add_split: unknown panel kind {spec['kind']!r}")


def _render_split_panel(slide, spec: dict, left: float, top: float, width: float,
                         height: float, theme: str, block_h: float | None = None):
    """Render one panel of add_split / add_stack, anchored at `top`.
    `spec['kind']` selects the panel type — see add_split's docstring for the
    shape each kind expects. `height` is the room available; `block_h` is the
    height the composition settled on for the block the panel belongs to —
    surfaced panels (cards, stats, image) grow to it so the two sides of a
    split share a bottom edge as well as a top one (exec-summary-3col.jpg's
    card grid runs the full height of the text panel beside it). No panel
    re-centers itself vertically: the caller positions the block as a unit."""
    kind = spec["kind"]
    fill_h = min(block_h or 0, height)
    if spec.get("heading"):
        # The panel's own sub-headline (H3) sits at the panel's top edge; the
        # body below it shrinks by the same amount so the block still lines up.
        hh = _panel_heading_height(spec, width)
        _, tfh = _textbox(slide, left, top, width, hh - PANEL_HEADING_GAP)
        _set_run(tfh.paragraphs[0].add_run(), spec["heading"], SIZE_H3, True, primary(theme), FONT_HEADING)
        top += hh
        height -= hh
        fill_h = max(0.0, fill_h - hh)
    if kind == "text":
        # `valign: "middle"` centres a short bare-text panel on the block —
        # used by add_image_split, where a paragraph pinned to the top edge of
        # a full-height screenshot leaves dead space under it. "bottom" sinks
        # it to the block's floor (the staggered-quotes pairing).
        _, tf = _textbox(slide, left, top, width, fill_h or height)
        if spec.get("valign") == "middle":
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        elif spec.get("valign") == "bottom":
            tf.vertical_anchor = MSO_ANCHOR.BOTTOM
        wrote_first = False
        if spec.get("lead"):
            # The LEAD level: the thesis, H3 in the heading face, primary
            # colour, before the body copy — the editorial pattern the
            # reference set uses on nearly every text slide.
            p = tf.paragraphs[0]
            p.space_after = Pt(12)
            _set_run(p.add_run(), spec["lead"], LEAD_SIZE, True, primary(theme), FONT_HEADING)
            wrote_first = True
        for para in _as_list(spec.get("paragraph")):
            p = _body(tf.paragraphs[0] if not wrote_first else tf.add_paragraph())
            p.space_after = Pt(10)
            _set_run(p.add_run(), para, SIZE_PARAGRAPH, False, secondary(theme))
            wrote_first = True
        for bullet in spec.get("bullets", []):
            # Bullets continue the paragraph, so they take its colour — body
            # copy is the secondary shade; only headings and important
            # captions are full primary (user correction 2026-09-21).
            p = _body(tf.paragraphs[0] if not wrote_first else tf.add_paragraph())
            wrote_first = True
            p.space_after = Pt(10)
            _set_run(p.add_run(), f"•  {bullet}", SIZE_PARAGRAPH, False, secondary(theme))
        if spec.get("features"):
            # A compact icon + label mini-grid under the copy (two columns) —
            # the reference "Issue tracking · Project management" row. Labels
            # are caption scale, primary; icons brand-coloured, 20px.
            n_text_h = _panel_body_height({**spec, "features": None}, width)
            grid_top = top + (0 if spec.get("valign") else n_text_h) + 20
            if spec.get("valign"):
                grid_top = top + (fill_h or height) - ceil(len(spec["features"]) / 2) * FEATURE_ROW_H
            col_w = width / 2
            for i, feat in enumerate(spec["features"]):
                r, c = divmod(i, 2)
                fx, fy = left + c * col_w, grid_top + r * FEATURE_ROW_H
                if feat.get("icon"):
                    draw_icon(slide, feat["icon"], fx, fy + 2, FEATURE_ICON, brand_content(theme))
                _, tff = _textbox(slide, fx + FEATURE_ICON + 12, fy, col_w - FEATURE_ICON - 20, FEATURE_ROW_H - 8)
                _set_run(tff.paragraphs[0].add_run(), feat["label"], SIZE_CAPTION, True, primary(theme))
    elif kind == "quote":
        # A pull-quote with a solid brand-purple vertical rule at its left
        # (the reference "rule quote"), bold heading-face text, optional
        # brand attribution below. No gradient panel — the split itself, plus
        # whatever it is paired with (stat cards, icon rows), carries the
        # weight. `valign: "bottom"` sinks it for a staggered quote pair.
        text_left = left + ACCENT_RULE_W + 24
        _, tf = _textbox(slide, text_left, top, width - ACCENT_RULE_W - 24, fill_h or height)
        if spec.get("valign") == "middle":
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        elif spec.get("valign") == "bottom":
            tf.vertical_anchor = MSO_ANCHOR.BOTTOM
        p = tf.paragraphs[0]
        _set_run(p.add_run(), f"“{spec['text']}”", SIZE_H2, True, primary(theme), FONT_HEADING)
        if spec.get("attribution"):
            p2 = tf.add_paragraph()
            p2.space_before = Pt(16)
            _set_run(p2.add_run(), spec["attribution"], SIZE_PARAGRAPH, True, brand_content(theme))
        q_h = _panel_body_height(spec, width)
        rule_top = top if spec.get("valign") != "bottom" else top + max(0, (fill_h or height) - q_h)
        if spec.get("valign") == "middle":
            rule_top = top + max(0, ((fill_h or height) - q_h) / 2)
        _accent_rule(slide, left, rule_top, min(q_h, height))
    elif kind == "facts":
        _draw_facts(slide, spec["items"], left, top, width, spec.get("columns", 1), theme)
    elif kind == "cards":
        items = spec["items"]
        assert 2 <= len(items) <= 6, "split 'cards' panel is 2-6 items"
        cols = spec.get("columns") or _default_columns(len(items))
        layout = _default_card_layout(cols, spec.get("layout"))
        if spec.get("columns") is None and len(items) <= 3 and cols > 1:
            # Two or three cards beside a tall neighbour (a full-height
            # screenshot): side by side, each becomes a narrow column with two
            # lines of copy at the top and a floor of empty gray. When the
            # block is much taller than the cards need, stack them vertically
            # as full-width cards instead (user correction 2026-09-22).
            side_by_side_h = _measure_card_grid_height(items, width, cols, pad=20, layout=layout)[0]
            if fill_h > 1.5 * side_by_side_h:
                cols = 1
        n_rows = len(_grid_rows(items, cols))
        total_h, row_h = _measure_card_grid_height(items, width, cols, pad=20, layout=layout)
        if total_h > height and layout == "stacked":
            layout = "horizontal"       # never squeeze text — reshape the card instead
            total_h, row_h = _measure_card_grid_height(items, width, cols, pad=20, layout=layout)
        total_h = min(max(total_h, fill_h), height)
        row_h = (total_h - 8 * (n_rows - 1)) / n_rows
        _draw_card_grid(slide, items, left, top, width, cols, row_h, theme, pad=20, layout=layout)
    elif kind == "rows":
        _draw_numbered_rows(slide, spec["items"], left, top, width, spec.get("columns", 1), theme,
                            min_total_h=fill_h, style=spec.get("style", "panel"))
    elif kind == "flow":
        # A chain does not grow to the block: tall nodes with one label each
        # read as empty boxes. It keeps its natural height, top-aligned.
        _draw_flow_row(slide, spec["nodes"], left, top, width,
                       min(_measure_flow_height(spec["nodes"], width), height), theme)
    elif kind == "quote-bar":
        _draw_quote_bar(slide, spec, left, top, width, max(_measure_quote_bar_height(spec, width), fill_h), theme)
    elif kind in ("stat", "stats"):
        items = [spec] if kind == "stat" else spec["items"]
        if kind == "stats":
            assert 2 <= len(items) <= 4, "split 'stats' panel is 2-4 items"
        style = spec.get("style", "card")
        natural = _measure_stat_row_height(items, width, pad=20, style=style)
        # Rule-style stats are bare (no card), so they keep their natural
        # height and stack like text rather than growing to the block.
        row_h = min(natural if style == "rule" else max(natural, fill_h), height)
        _draw_stat_row(slide, items, left, top, width, row_h, theme, pad=20, style=style)
    elif kind == "image":
        # The slot never drops below its declared proportion (3:2 by default,
        # or `aspect`), but it DOES grow to the block's height when the
        # neighbouring panel is taller — a screenshot beside a full-height
        # text panel should fill that height, not sit as a small box in the
        # middle of it (the reference side-panel shots run panel-height).
        # An explicit `height` pins it. The label always states the drawn
        # size, so the exporter is never sent after the wrong crop.
        natural = spec.get("height") or width / spec.get("aspect", 1.5)
        h = natural if spec.get("height") else max(natural, fill_h)
        draw_image_slot(slide, left, top, width, min(h, height), spec["caption"], theme,
                        align=spec.get("align", "center"))
    elif kind == "table":
        _draw_table(slide, left, top, width, height, spec["headers"], spec["rows"], theme=theme,
                    highlight_last_row=spec.get("highlight_last_row", False),
                    highlight_first_col=spec.get("highlight_first_col", False))
    else:
        raise ValueError(f"add_split: unknown panel kind {kind!r}")


def add_split(prs, title: str, left: dict, right: dict, ratio: tuple[int, int] = (5, 7),
              theme: str = "light", divider: bool = False):
    """Asymmetric two-panel slide — the composition behind exec-summary-3col.jpg
    (narrative left, card grid right), math-savings.jpg (one highlighted
    stat left, a value table right), and a quote whose own wording carries a
    metric (quote left, the metric(s) it named as stat cards right — see
    deck-design-brain.md "Testimonial"). This is a *reshape* of the existing
    heading+paragraph / quote / N-cards / stats / table recipes side by side
    at an uneven width, not a new component — see deck-design-brain.md
    section E.

    `left` and `right` each describe one panel:
      {"kind": "text",  "paragraph": str, "bullets": [str, ...]}   (either or both)
      {"kind": "quote", "text": str, "attribution": str}           (attribution optional)
      {"kind": "cards", "items": [{"heading", "paragraph"}, ...]}  (2-4 items)
      {"kind": "stat",  "value": str, "label": str, "desc": str}   (one figure; desc optional)
      {"kind": "stats", "items": [{"value", "label", "desc"}, ...]} (2-4 figures)
      {"kind": "table", "headers": [...], "rows": [[...], ...],
                         "highlight_last_row": bool, "highlight_first_col": bool}
      {"kind": "image", "caption": str, "height": float (optional)}
                         — a reserved product-UI slot; see draw_image_slot

    `ratio` is the (left, right) column share, e.g. (5, 7) or (4, 8) — need
    not sum to 12, only the proportion matters. Per Design DNA 'Gutter vs.
    slide padding': the two panels sit 8px apart when BOTH carry their own
    surface (cards/stat/stats/table), else 48px (the slide's own padding)
    when either side is bare text or a quote — so a text+cards or quote+stats
    split reads as text sitting in the slide's whitespace next to a panel,
    not glued to it.
    """
    assert len(ratio) == 2 and ratio[0] > 0 and ratio[1] > 0
    # `divider=True` draws a hairline down the middle of the gap — only
    # meaningful when neither side carries its own surface (text | text,
    # text | quote, text | rule-stats): the reference "two-column editorial"
    # slides separate their columns with a rule, not with panels.
    # An image panel aligns its picture toward the copy on the other side.
    if left["kind"] == "image":
        left = {"align": "right", **left}
    if right["kind"] == "image":
        right = {"align": "left", **right}
    slide = add_blank_slide(prs, theme=theme)
    top = _add_slide_title(slide, title)
    content_w = SLIDE_W_PX - 2 * PAGE_PADDING_PX
    content_h = SLIDE_H_PX - top - PAGE_PADDING_PX
    both_surfaced = left["kind"] in _SPLIT_SURFACE_KINDS and right["kind"] in _SPLIT_SURFACE_KINDS
    gap = 8 if both_surfaced else SPLIT_BARE_GAP
    left_share = ratio[0] / (ratio[0] + ratio[1])
    left_w = content_w * left_share - gap / 2
    right_left = PAGE_PADDING_PX + left_w + gap
    right_w = SLIDE_W_PX - PAGE_PADDING_PX - right_left
    # Both panels share one top edge. When BOTH are measurable rows (cards /
    # stats), the pair is centered in the space below the title as a single
    # block — the same "center the row, don't stretch it" rule a standalone
    # card row follows. When either side is flowing text (text/quote/table)
    # there is nothing reliable to measure, so the pair anchors at the title
    # gap. Either way the two sides line up, which they did not when each
    # panel decided its own vertical position.
    # The block never drops below the canvas-fill floor: a split whose two
    # panels are each two lines tall is a strip in an empty slide, and the
    # surfaced side(s) grow to the block height so both edges line up.
    block_h = min(max(_split_panel_height(left, left_w),
                       _split_panel_height(right, right_w),
                       MIN_CONTENT_FILL * content_h), content_h)
    panel_top = top + max(0, (content_h - block_h) / 2)
    panel_h = content_h - (panel_top - top)
    _render_split_panel(slide, left, PAGE_PADDING_PX, panel_top, left_w, panel_h, theme, block_h=block_h)
    _render_split_panel(slide, right, right_left, panel_top, right_w, panel_h, theme, block_h=block_h)
    if divider and not both_surfaced:
        x = PAGE_PADDING_PX + left_w + gap / 2
        _hairline(slide, x, panel_top, x, panel_top + block_h, theme)
    return _mark(slide, "split")


_TCPR_LINE_ORDER = ("a:lnL", "a:lnR", "a:lnT", "a:lnB")


def _set_cell_border(cell, edges: list[str], color: RGBColor, width_pt: float = 0.75):
    """Add a thin solid rule to one or more edges ('lnT'/'lnB'/'lnL'/'lnR') of
    a table cell. python-pptx has no friendly API for cell borders (see
    pptx/oxml/table.py's CT_TableCellProperties — it models only fill and
    margins), so this inserts the raw <a:lnB>-style OOXML element directly,
    at the position ECMA-376 requires within <a:tcPr> (line elements, in
    lnL/lnR/lnT/lnB order, before any fill)."""
    tcPr = cell._tc.get_or_add_tcPr()
    w = int(width_pt * 12700)  # EMU per point
    for edge in edges:
        tag = f"a:{edge}"
        existing = tcPr.find(qn(tag))
        if existing is not None:
            tcPr.remove(existing)
        ln_el = parse_xml(
            f'<{tag} {nsdecls("a")} w="{w}" cap="flat" cmpd="sng" algn="ctr">'
            f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
            f'<a:prstDash val="solid"/>'
            f"</{tag}>"
        )
        insert_rank = _TCPR_LINE_ORDER.index(tag)
        pos = 0
        for i, child in enumerate(tcPr):
            child_tag = "a:" + child.tag.split("}")[-1]
            if child_tag in _TCPR_LINE_ORDER and _TCPR_LINE_ORDER.index(child_tag) < insert_rank:
                pos = i + 1
            else:
                break
        tcPr.insert(pos, ln_el)


def _draw_table(slide, left: float, top: float, width: float, height: float,
                 headers: list[str], rows: list[list[str]], theme: str = "light",
                 highlight_last_row: bool = False, highlight_first_col: bool = False):
    """Native, editable pptx table — shared by add_table and add_split's
    'table' panel. See deck-design-brain.md 'Tabular -> Table': bold headers,
    thin row dividers, muted values, an optional gray-filled key column
    (pricing-table.jpg) and/or a bold brand-purple total row (math-savings.jpg)."""
    n_rows, n_cols = len(rows) + 1, len(headers)
    col_w = width / n_cols
    # Rows size to their own content, capped by the space available — a table
    # stretched to fill the slide balloons every row and reads as a form, not
    # the compact reference table (pricing-table.jpg). Same "size to content,
    # don't stretch" rule the card and stat rows follow.
    header_h = 40.0
    natural = []
    for row in rows:
        lines = max(_text_lines(str(cell), col_w - 32, SIZE_PARAGRAPH_PX, avg_char_ratio=0.5)
                    for cell in row)
        natural.append(max(48.0, lines * SIZE_PARAGRAPH_PX * 1.5 + 16))
    total = header_h + sum(natural)
    if total > height:                      # too tall — fall back to even fill
        scale = (height - header_h) / max(sum(natural), 1)
        natural = [h * scale for h in natural]
        total = height
    gframe = slide.shapes.add_table(n_rows, n_cols, px(left), px(top), px(width), px(total))
    tbl = gframe.table
    tbl.first_row = False
    tbl.horz_banding = False
    for c in range(n_cols):
        tbl.columns[c].width = px(col_w)
    tbl.rows[0].height = px(header_h)
    for r, h in enumerate(natural, start=1):
        tbl.rows[r].height = px(h)

    divider_color = C.LIGHT_BG[3] if theme == "light" else C.DARK_BG[3]
    for r in range(n_rows):
        is_header = r == 0
        is_total = highlight_last_row and r == n_rows - 1
        for c in range(n_cols):
            cell = tbl.cell(r, c)
            is_key_col = highlight_first_col and c == 0 and not is_header and not is_total
            cell.margin_left = cell.margin_right = px(16)
            cell.margin_top = cell.margin_bottom = px(8)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            if is_total:
                cell.fill.fore_color.rgb = C.BRAND
            elif is_header or is_key_col:
                cell.fill.fore_color.rgb = panel_fill(theme)
            else:
                cell.fill.fore_color.rgb = bg(theme, 0)

            text = headers[c] if is_header else str(rows[r - 1][c])
            tf = cell.text_frame
            tf.word_wrap = True
            p = _body(tf.paragraphs[0])
            # Every column is left-aligned, matching pricing-table.jpg — its
            # value columns (words, cost per word, cost) all start at their
            # own left edge. Right-aligning them ragged-lefts any wrapped
            # text cell and breaks the column's reading edge.
            p.alignment = PP_ALIGN.LEFT
            bold = is_total or is_header or is_key_col
            if is_total:
                color = C.WHITE
            elif is_header or is_key_col:
                color = primary(theme)
            else:
                color = secondary(theme)
            size = SIZE_CAPTION if is_header else SIZE_PARAGRAPH
            _set_run(p.add_run(), text, size, bold, color)

            if r < n_rows - 1 and not is_total:
                _set_cell_border(cell, ["lnB"], divider_color)
    return gframe


def add_table(prs, title: str, headers: list[str], rows: list[list[str]], theme: str = "light",
              highlight_last_row: bool = False, highlight_first_col: bool = False):
    """Full-width data table — see deck-design-brain.md 'Tabular -> Table'
    (pricing-table.jpg, math-savings.jpg). `rows` are data rows, each the
    same length as `headers`. `highlight_last_row` renders the final row as
    a bold brand-purple summary/total (e.g. a pricing table's total line);
    `highlight_first_col` shades the label column gray to key it out."""
    assert rows and all(len(r) == len(headers) for r in rows), "every row must match headers' length"
    slide = add_blank_slide(prs, theme=theme)
    top = _add_slide_title(slide, title)
    content_w = SLIDE_W_PX - 2 * PAGE_PADDING_PX
    content_h = SLIDE_H_PX - top - PAGE_PADDING_PX
    gframe = _draw_table(slide, PAGE_PADDING_PX, top, content_w, content_h, headers, rows,
                          theme=theme, highlight_last_row=highlight_last_row,
                          highlight_first_col=highlight_first_col)
    # Center the finished table in the space below the title when it is
    # shorter than that space, same as a card row.
    used = sum(r.height for r in gframe.table.rows) / EMU_PER_PX
    gframe.top = px(top + max(0, (content_h - used) / 2))
    return _mark(slide, "table")


def _add_arrowhead(connector, end: str = "tail", size: str = "med"):
    """Add a native triangular arrowhead to one end of a connector line.
    python-pptx exposes no friendly API for <a:headEnd>/<a:tailEnd> (see
    pptx/oxml/shapes/shared.py's CT_LineProperties — headEnd/tailEnd are in
    its element sequence but have no ZeroOrOne accessor), so this appends the
    raw element directly. It is safe to just append: by the time this is
    called `line.color` has already added a bare <a:solidFill>, so headEnd/
    tailEnd land in their correct schema slot (after the fill, before the
    absent extLst) without needing to reason about the general case."""
    ln = connector.line._get_or_add_ln()
    tag = f"a:{'headEnd' if end == 'head' else 'tailEnd'}"
    existing = ln.find(qn(tag))
    if existing is not None:
        ln.remove(existing)
    el = parse_xml(f'<{tag} {nsdecls("a")} type="triangle" w="{size}" len="{size}"/>')
    extLst = ln.find(qn("a:extLst"))
    if extLst is not None:
        extLst.addprevious(el)
    else:
        ln.append(el)


# Node-to-node spacing is deliberately wider than the 8px panel gutter: that
# value is for two surfaces meeting at a seam, but here the gap carries a
# routed connector + arrowhead, which needs room to read as an arrow rather
# than a hairline between touching shapes.
FLOW_NODE_GAP = 32


def _measure_flow_height(nodes: list[dict], width: float, pad: float = 20) -> float:
    n = len(nodes)
    node_w = (width - FLOW_NODE_GAP * (n - 1)) / n
    inner_w = node_w - 2 * pad
    h = ANCHOR_SIZE + 14
    h += max(_text_lines(nd["label"], inner_w, SIZE_PARAGRAPH_PX, avg_char_ratio=0.58)
             for nd in nodes) * SIZE_PARAGRAPH_PX * 1.3
    if any(nd.get("caption") for nd in nodes):
        h += 8 + max(_text_lines(nd.get("caption", ""), inner_w, SIZE_CAPTION_PX, avg_char_ratio=0.5)
                     for nd in nodes) * SIZE_CAPTION_PX * 1.45
    return h + 2 * pad


def _draw_flow_row(slide, nodes: list[dict], left0: float, top: float, width: float,
                   height: float, theme: str, pad: float = 20):
    """The icon-card chain: a row of anchored cards joined by arrow
    connectors. Shared by add_flow_chain (style="cards") and the `flow`
    panel kind in add_stack / add_split — a chain over the detail cards or
    the screenshot that backs it is the reference shape (workflow-steps.jpg),
    and on its own a chain rarely earns the canvas."""
    n = len(nodes)
    node_w = (width - FLOW_NODE_GAP * (n - 1)) / n
    inner_w = node_w - 2 * pad
    spans = []
    for i, nd in enumerate(nodes):
        left = left0 + i * (node_w + FLOW_NODE_GAP)
        _rounded_rect(slide, left, top, node_w, height, panel_fill(theme))
        icon = nd.get("icon")
        _draw_card_anchor(slide, "icon" if icon else "number", icon or (i + 1), left + pad, top + pad, theme,
                          surface=panel_fill(theme))
        text_top = top + pad + (ICON_ANCHOR_SIZE if icon else ANCHOR_SIZE) + 14
        _, tf = _textbox(slide, left + pad, text_top, inner_w, height - (text_top - top) - pad)
        p = tf.paragraphs[0]
        _set_run(p.add_run(), nd["label"], SIZE_PARAGRAPH, True, primary(theme), FONT_HEADING)
        if nd.get("caption"):
            p2 = tf.add_paragraph()
            p2.space_before = Pt(6)
            _body(p2)
            _set_run(p2.add_run(), nd["caption"], SIZE_CAPTION, False, secondary(theme))
        spans.append((left, left + node_w))
    arrow_y = px(top + height / 2)
    for i in range(n - 1):
        _draw_flow_connector(slide, spans[i][1], spans[i + 1][0], arrow_y, theme)


def _draw_flow_connector(slide, x0: float, x1: float, y_emu, theme: str):
    """A dotted connector with an arrowhead — every connector in the reference
    decks is dotted (user correction 2026-09-21). Dash is written before the
    arrowhead so the line's XML children stay in schema order."""
    connector = _no_shadow(slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, px(x0), y_emu, px(x1), y_emu))
    connector.line.color.rgb = secondary(theme)
    connector.line.width = Pt(1.5)
    _set_line_dash(connector.line, "sysDot")
    _add_arrowhead(connector, end="tail")
    return connector


def add_flow_chain(prs, title: str, nodes: list, theme: str = "light", style: str = "cards",
                    detail_cards: list[dict] | None = None):
    """Horizontal process flow connected by native arrow connectors — the
    pptx take on deck-design-brain.md 'Time & structure -> Flow / graph'.
    Real lines/shapes throughout, not a picture. 3-6 nodes.

    `style="cards"` (default) — each node is an icon-bearing card. Use this
    when the flow IS the slide's whole content (e.g. "How it works" in N
    steps): every step carries real visual weight instead of a thin row of
    pills over an empty slide. `nodes` is a list of dicts:
    {"label": str, "icon": str (optional, a deck_icons.ICONS key — omit for
    an automatic numbered badge), "caption": str (optional, one short line)}.

    `style="pills"` — the compact brand-purple pill-node chain. Reserve this
    for when the flow is paired with a supporting `detail_cards` row
    underneath it (compliance-risk-grid.jpg's two-layer composition): the
    pills then read as a compact index into the cards below, not the slide's
    only content. `nodes` is a list of short strings; `detail_cards` (2-4
    items, same shape as add_cards) is required with this style.

    Diagrams with organic/non-rectilinear connectors (curved arrows, a
    branching tree) are NOT what this builds — those stay on the HTML deck
    path; this covers the straight-chain case only.
    """
    assert 3 <= len(nodes) <= 6, "flow-chain recipe is 3-6 nodes"
    assert style in ("cards", "pills"), "style must be 'cards' or 'pills'"
    slide = add_blank_slide(prs, theme=theme)
    top = _add_slide_title(slide, title)
    content_w = SLIDE_W_PX - 2 * PAGE_PADDING_PX
    node_gap = FLOW_NODE_GAP
    n = len(nodes)
    node_w = (content_w - node_gap * (n - 1)) / n
    avail_h = SLIDE_H_PX - top - PAGE_PADDING_PX

    if style == "cards":
        # A chain that is the whole slide (a process and a feature list are
        # two slides, never one stack — user correction 2026-09-21) floors
        # its nodes at FLOW_MIN_FILL of the room so it earns the canvas;
        # text stays top-aligned inside the taller node.
        node_h = min(max(_measure_flow_height(nodes, content_w), FLOW_MIN_FILL * avail_h), avail_h)
        row_top = top + max(0, (avail_h - node_h) / 2)
        _draw_flow_row(slide, nodes, PAGE_PADDING_PX, row_top, content_w, node_h, theme)
        return _mark(slide, "flow")
    else:
        assert detail_cards, "style='pills' is reserved for a flow paired with a detail_cards row — see docstring"
        node_h = 64
        spans = []
        for i, label in enumerate(nodes):
            node_left = PAGE_PADDING_PX + i * (node_w + node_gap)
            shp = _rounded_rect(slide, node_left, top, node_w, node_h, C.BRAND, radius_ratio=0.5)
            tf = shp.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_right = px(12)
            tf.margin_top = tf.margin_bottom = px(4)
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            _set_run(p.add_run(), label, SIZE_CAPTION, True, C.WHITE)
            spans.append((node_left, node_left + node_w))
        arrow_y = px(top + node_h / 2)

    for i in range(n - 1):
        _draw_flow_connector(slide, spans[i][1], spans[i + 1][0], arrow_y, theme)

    if style == "pills" and detail_cards:
        assert 2 <= len(detail_cards) <= 4, "flow-chain detail row is 2-4 cards"
        cards_top = top + node_h + 8
        cards_avail_h = SLIDE_H_PX - cards_top - PAGE_PADDING_PX
        cards_h = min(max(_measure_card_row_height(detail_cards, content_w),
                          MIN_CONTENT_FILL * avail_h - node_h - 8), cards_avail_h)
        _draw_card_row(slide, detail_cards, PAGE_PADDING_PX, cards_top, content_w, cards_h, theme)
    return _mark(slide, "stack")


def add_image_banner(prs, title: str, caption: str, paragraph: str | None = None,
                      theme: str = "light", height: float | None = None,
                      aspect: float | None = None, force_banner: bool = False):
    """A reserved product-UI slot running the full content width, under the
    title and an optional line of copy — for a slide whose whole point is one
    WIDE product surface (a dashboard, a timeline view, a before/after strip).

    **A title, a paragraph and a screenshot is a horizontal split, not a
    banner** (user correction 2026-09-22). Under a full-width title, a slot
    that fills the rest of the slide is a wide flat box — a square or 4:3
    shot covers a third of it and the slide reads as empty. So unless the
    screenshot is genuinely wide (`aspect >= 2`), this delegates to
    `add_image_split(title_column=True)`: title and copy in the left column,
    the shot at full height on the right. Pass `force_banner=True` to insist.

    `aspect` (w/h) sizes the slot to the shot it will hold; without it the
    slot takes all the height left, and a real image dropped in later is
    contain-fit and centred. `height` pins a specific export shape."""
    if not force_banner and (aspect is None or aspect < 2.0):
        return add_image_split(
            prs, title,
            copy={"kind": "text", "paragraph": paragraph} if paragraph else {"kind": "text"},
            caption=caption, aspect=aspect or 1.0, theme=theme, title_column=True)
    slide = add_blank_slide(prs, theme=theme)
    top = _add_slide_title(slide, title)
    content_w = SLIDE_W_PX - 2 * PAGE_PADDING_PX
    if paragraph:
        _, tf = _textbox(slide, PAGE_PADDING_PX, top, content_w * 0.6, 60)
        _body(tf.paragraphs[0])
        _set_run(tf.paragraphs[0].add_run(), paragraph, SIZE_PARAGRAPH, False, secondary(theme))
        top += 76
    avail = SLIDE_H_PX - top - PAGE_PADDING_PX
    # A declared aspect sizes the slot to the shot it will hold; without one
    # the slot takes all the height left.
    h = min(height or (content_w / aspect if aspect else avail), avail)
    draw_image_slot(slide, PAGE_PADDING_PX, top + max(0, (avail - h) / 2),
                    content_w, h, caption, theme)
    return _mark(slide, "banner")


TITLE_COLUMN_GAP = 40   # --spacing-8: title's last line -> the copy under it, inside a column.
                        # The 80px HEADING_GAP is measured from a full-width title's origin and
                        # is far too much once the title wraps to two or three lines in a column.


def add_image_split(prs, title: str, copy: dict, caption: str, image_side: str = "right",
                    aspect: float = 1.0, theme: str = "light", max_image_share: float = 0.55,
                    title_column: bool | None = None):
    """The IMAGE-LED split: a reserved product-UI slot that fills the full
    height at its own aspect ratio, with the copy panel taking whatever width
    is left. This is the default shape for a slide about a product surface,
    and the right one for the finished promo shots in
    images/promo-ui-mockups/ — all of which are SQUARE (1080×1080). A square
    dropped into a 3:2 side box or a full-width banner covers barely half the
    slot and leaves dead flanks; here the slot is sized to the image, so the
    fill is exact.

    `copy` is any add_split panel spec (text, cards, stats, rows, quote…) —
    a paragraph beside the shot, or two or three stacked cards keyed to what
    the screenshot shows. `image_side` is "right" (default) or "left"; the
    picture aligns toward the copy. `aspect` is the image's w/h (1.0 for the
    promo set; 1.5 or 16/10 for a landscape screenshot); the image width is
    capped at `max_image_share` of the content width so the copy keeps room.

    `title_column` puts the SLIDE TITLE inside the copy column — title at H1
    over its paragraph on the left, the shot running the full slide height on
    the right, from the top padding down. **It defaults on for a bare text
    copy panel** — a slide that is just a title, a paragraph and a screenshot
    — because a full-width title there strands the image at half height and
    leaves a band of dead space (user correction 2026-09-22). It defaults off
    for a surfaced panel (cards, stats), where the full-width title reads
    correctly over the column. The title still sits top-left at the padding
    origin either way; it is simply measured to the column, not the slide."""
    assert image_side in ("left", "right")
    if title_column is None:
        title_column = copy["kind"] == "text"
    if copy["kind"] == "text" and not title_column:
        copy = {"valign": "middle", **copy}
    slide = add_blank_slide(prs, theme=theme)
    content_w = SLIDE_W_PX - 2 * PAGE_PADDING_PX
    if title_column:
        top = PAGE_PADDING_PX
        content_h = SLIDE_H_PX - 2 * PAGE_PADDING_PX
        slide._smartcat_content_top = top
    else:
        top = _add_slide_title(slide, title)
        content_h = SLIDE_H_PX - top - PAGE_PADDING_PX
    img_w = min(content_h * aspect, content_w * max_image_share)
    img_h = img_w / aspect
    gap = 8 if copy["kind"] in _SPLIT_SURFACE_KINDS else SPLIT_BARE_GAP
    copy_w = content_w - img_w - gap
    if image_side == "right":
        copy_left, img_left, align = PAGE_PADDING_PX, PAGE_PADDING_PX + copy_w + gap, "left"
    else:
        img_left, copy_left, align = PAGE_PADDING_PX, PAGE_PADDING_PX + img_w + gap, "right"

    if title_column:
        t_lines = _text_lines(title, copy_w, SIZE_H1_PX, avg_char_ratio=0.52)
        t_h = t_lines * H1_LINE_PX
        tb, tf = _textbox(slide, copy_left, top, copy_w, t_h)
        _set_run(tf.paragraphs[0].add_run(), title, SIZE_H1, True, _content_color(slide), FONT_HEADING)
        slide._smartcat_title_shape = tb
        copy_top = top + t_h + TITLE_COLUMN_GAP
        copy_h = SLIDE_H_PX - PAGE_PADDING_PX - copy_top
        _render_split_panel(slide, copy, copy_left, copy_top, copy_w, copy_h, theme, block_h=copy_h)
        slot_top = top + max(0, (content_h - img_h) / 2)
        draw_image_slot(slide, img_left, slot_top, img_w, img_h, caption, theme, align=align)
        return _mark(slide, "split")

    block_h = min(max(_split_panel_height(copy, copy_w), img_h, MIN_CONTENT_FILL * content_h), content_h)
    block_top = top + max(0, (content_h - block_h) / 2)
    _render_split_panel(slide, copy, copy_left, block_top, copy_w, content_h - (block_top - top), theme,
                        block_h=block_h)
    # The slot keeps the image's own proportion (that is the point of this
    # builder) and is vertically centred on the copy block.
    slot_top = block_top + max(0, (block_h - img_h) / 2)
    draw_image_slot(slide, img_left, slot_top, img_w, img_h, caption, theme, align=align)
    return _mark(slide, "split")


# ── Stacked, rows and statement compositions ──────────────────────────────

def _measure_quote_bar_height(spec: dict, width: float, pad: float = 28) -> float:
    quote_w = width * 0.62 - 2 * pad
    h = _text_lines(spec["text"], quote_w, SIZE_H3_PX, avg_char_ratio=0.5) * SIZE_H3_PX * 1.3
    attr_h = SIZE_PARAGRAPH_PX * 1.3 + (SIZE_CAPTION_PX * 1.4 if spec.get("role") else 0)
    return max(h, attr_h) + 2 * pad


def _draw_quote_bar(slide, spec: dict, left: float, top: float, width: float, height: float,
                    theme: str, pad: float = 28):
    """The quote BAR from stat-cards-quote.jpg: one full-width panel, the
    quote in bold heading type on the left ~60%, a hairline divider, then the
    attribution (name bold, role muted) on the right. The stacked companion
    to a stats row — the qualitative half of one claim under its quantitative
    half. `spec`: {"kind": "quote-bar", "text", "name", "role" (optional)}."""
    _rounded_rect(slide, left, top, width, height, panel_fill(theme))
    quote_w = width * 0.62 - 2 * pad
    _, tf = _textbox(slide, left + pad, top + pad, quote_w, height - 2 * pad)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    _set_run(p.add_run(), f"“{spec['text']}”", SIZE_H3, True, primary(theme), FONT_HEADING)
    div_x = left + width * 0.62 + pad / 2
    div = _no_shadow(slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, px(div_x), px(top + pad),
                                                px(div_x), px(top + height - pad)))
    div.line.color.rgb = C.LIGHT_BG[3] if theme == "light" else C.DARK_BG[3]
    div.line.width = Pt(1)
    attr_left = div_x + pad
    _, tf2 = _textbox(slide, attr_left, top + pad, left + width - pad - attr_left, height - 2 * pad)
    tf2.vertical_anchor = MSO_ANCHOR.MIDDLE
    p2 = tf2.paragraphs[0]
    _set_run(p2.add_run(), spec["name"], SIZE_PARAGRAPH, True, primary(theme))
    if spec.get("role"):
        p3 = _body(tf2.add_paragraph())
        p3.space_before = Pt(4)
        _set_run(p3.add_run(), spec["role"], SIZE_CAPTION, False, secondary(theme))


ROW_PAD = 20
ROW_GAP = 8
# A section divider's ruled item list — see add_section_divider.
DIVIDER_ITEM_ROW_H = 56
DIVIDER_ITEM_ICON = 20
DIVIDER_ITEM_TEXT_GAP = 20
DIVIDER_LIST_TOP_GAP = 32
ROW_NUMERAL_W = 52      # "01." at H3 bold needs ~46px; a narrower box wraps the period onto its own line


def _measure_numbered_rows_height(items: list[dict], width: float, columns: int = 1) -> float:
    gutter = 8
    col_w = (width - gutter * (columns - 1)) / columns
    text_w = col_w - 2 * ROW_PAD - ROW_NUMERAL_W - 12
    heights = []
    for it in items:
        h = _text_lines(it["heading"], text_w, SIZE_PARAGRAPH_PX, avg_char_ratio=0.58) * SIZE_PARAGRAPH_PX * 1.3
        if it.get("detail"):
            h += 6 + _text_lines(it["detail"], text_w, SIZE_CAPTION_PX, avg_char_ratio=0.5) * SIZE_CAPTION_PX * 1.45
        heights.append(max(h, ANCHOR_SIZE) + 2 * ROW_PAD)
    row_h = max(heights)                      # uniform rows, like agenda.jpg
    n_rows = ceil(len(items) / columns)
    return row_h * n_rows + ROW_GAP * (n_rows - 1)


def _draw_numbered_rows(slide, items: list[dict], left0: float, top: float, width: float,
                        columns: int, theme: str, min_total_h: float = 0, style: str = "panel") -> float:
    """agenda.jpg / row-per-item: one row per item, a brand numeral (or a
    design-system icon) at the left, heading + muted detail beside it; rows
    fill down the first column, then the second. Returns the height used.

    `style`: "panel" (default — each row on a gray surface), "ruled" (no
    surface; the list bracketed by a hairline above the first row and under
    every row — the contents-page pattern in the reference set), or "bare"
    (no surface, no rule — icon rows beside a quote). Each item may carry `meta`, a short right-aligned
    caption (a page number, a duration, an owner) on the heading line."""
    gutter = 8 if style == "panel" else 48
    col_w = (width - gutter * (columns - 1)) / columns
    n_rows = ceil(len(items) / columns)
    natural = _measure_numbered_rows_height(items, width, columns)
    total = max(natural, min_total_h)
    row_h = (total - ROW_GAP * (n_rows - 1)) / n_rows
    for i, it in enumerate(items):
        col, row = divmod(i, n_rows)
        x = left0 + col * (col_w + gutter)
        y = top + row * (row_h + ROW_GAP)
        if style == "panel":
            _rounded_rect(slide, x, y, col_w, row_h, panel_fill(theme), radius_ratio=0.12)
        elif style == "ruled":
            # Bracketed, like the divider's list: a rule above the column's
            # first row and under every row.
            if row == 0:
                _hairline(slide, x, y - ROW_GAP / 2, x + col_w, y - ROW_GAP / 2, theme)
            _hairline(slide, x, y + row_h + ROW_GAP / 2, x + col_w, y + row_h + ROW_GAP / 2, theme)
        if it.get("meta"):
            _, tfm = _textbox(slide, x + col_w - ROW_PAD - 120, y + ROW_PAD + 2, 120, 20)
            pm = tfm.paragraphs[0]
            pm.alignment = PP_ALIGN.RIGHT
            _set_run(pm.add_run(), it["meta"], SIZE_CAPTION, False, secondary(theme))
        badge_top = y + ROW_PAD
        if it.get("icon"):
            draw_icon(slide, it["icon"], x + ROW_PAD + 4, badge_top + 2, 24, brand_content(theme))
        else:
            _, tfn = _textbox(slide, x + ROW_PAD, badge_top, ROW_NUMERAL_W, ANCHOR_SIZE)
            tfn.word_wrap = False
            pn = tfn.paragraphs[0]
            _set_run(pn.add_run(), f"{i + 1:02d}.", SIZE_H3, True, brand_content(theme), FONT_HEADING)
        text_left = x + ROW_PAD + ROW_NUMERAL_W + 12
        text_w = x + col_w - ROW_PAD - text_left - (130 if it.get("meta") else 0)
        _, tf = _textbox(slide, text_left, badge_top, text_w, row_h - 2 * ROW_PAD)
        p = tf.paragraphs[0]
        _set_run(p.add_run(), it["heading"], SIZE_PARAGRAPH, True, primary(theme), FONT_HEADING)
        if it.get("detail"):
            p2 = _body(tf.add_paragraph())
            p2.space_before = Pt(6)
            _set_run(p2.add_run(), it["detail"], SIZE_CAPTION, False, secondary(theme))
    return total


def add_numbered_rows(prs, title: str, items: list[dict], theme: str = "light",
                      columns: int | None = None, style: str = "panel"):
    """Numbered (or icon) rows — the agenda.jpg shape and the brain's
    "row-per-item": 3–8 items, each `{"heading", "detail" (optional),
    "icon" (optional)}`, one panel per item with a brand numeral at the left.
    `columns` defaults to 2 for five or more items, else 1. Use it for an
    agenda, a list of updates, an at-a-glance summary — anywhere the items
    are short claims with a line of detail, which a card grid would puff up
    and a bullet list would flatten."""
    assert 3 <= len(items) <= 8, "numbered rows: 3-8 items"
    columns = columns or (2 if len(items) >= 5 else 1)
    slide = add_blank_slide(prs, theme=theme)
    top = _add_slide_title(slide, title)
    content_w = SLIDE_W_PX - 2 * PAGE_PADDING_PX
    avail_h = SLIDE_H_PX - top - PAGE_PADDING_PX
    natural = _measure_numbered_rows_height(items, content_w, columns)
    total = min(max(natural, MIN_CONTENT_FILL * avail_h), avail_h)
    block_top = top + max(0, (avail_h - total) / 2)
    _draw_numbered_rows(slide, items, PAGE_PADDING_PX, block_top, content_w, columns, theme,
                        min_total_h=total, style=style)
    return _mark(slide, "rows")


def add_stack(prs, title: str, top: dict, bottom: dict, theme: str = "light"):
    """Two different components stacked vertically under one title — the
    brain's "Stacked composition": a stats row over a quote bar
    (stat-cards-quote.jpg), a card row over a full-width image slot, an
    image banner over a row of three captions, numbered rows over a stat
    row. `top` and `bottom` take the same panel specs as add_split, plus:
      {"kind": "quote-bar", "text": str, "name": str, "role": str}
      {"kind": "rows", "items": [{"heading", "detail", "icon"}], "columns": 1|2}

    Both panels run the full content width. The block sizes to content, is
    floored at MIN_CONTENT_FILL of the room under the title (extra room is
    shared in proportion to each panel's natural height), and is centered.
    The gap is the 8px gutter when both panels carry a surface, 32px when
    either is bare text."""
    slide = add_blank_slide(prs, theme=theme)
    y0 = _add_slide_title(slide, title)
    content_w = SLIDE_W_PX - 2 * PAGE_PADDING_PX
    content_h = SLIDE_H_PX - y0 - PAGE_PADDING_PX
    both_surfaced = top["kind"] in _SPLIT_SURFACE_KINDS and bottom["kind"] in _SPLIT_SURFACE_KINDS
    gap = STACK_GAP_SURFACED if both_surfaced else STACK_GAP_BARE
    h_top = _split_panel_height(top, content_w)
    h_bot = _split_panel_height(bottom, content_w)
    natural = h_top + gap + h_bot
    target = min(max(natural, MIN_CONTENT_FILL * content_h), content_h)
    scale = (target - gap) / max(h_top + h_bot, 1)
    h_top, h_bot = h_top * scale, h_bot * scale
    block_top = y0 + max(0, (content_h - target) / 2)
    _render_split_panel(slide, top, PAGE_PADDING_PX, block_top, content_w, h_top, theme, block_h=h_top)
    _render_split_panel(slide, bottom, PAGE_PADDING_PX, block_top + h_top + gap, content_w, h_bot, theme,
                        block_h=h_bot)
    return _mark(slide, "stack")


def _as_list(v) -> list:
    if not v:
        return []
    return list(v) if isinstance(v, (list, tuple)) else [v]


def add_statement(prs, title: str, lead: str, aside: str | list[str] | None = None,
                  theme: str = "dark", divider: bool = False, ratio: tuple[int, int] = (6, 6)):
    """statement-body.jpg and the reference two-column editorial slide: the
    title, then the argument itself set LARGE — the lead paragraph in bold H2
    heading type, primary colour, on the left — with the supporting copy on
    the right: `aside` is one paragraph or a list of paragraphs in body type,
    secondary colour, starting on the same top line. `ratio` splits the two
    columns (6:6 default; 5:7 when the aside carries the detail, 7:5 when the
    lead is the point). `divider=True` draws the hairline between them that
    the references use instead of a wider gap. This is the slide for landing
    one idea in prose without a diagram; add_heading_paragraph is its
    smaller, quieter sibling for a paragraph that merely introduces what
    follows."""
    slide = add_blank_slide(prs, theme=theme)
    top = _add_slide_title(slide, title)
    content_w = SLIDE_W_PX - 2 * PAGE_PADDING_PX
    avail_h = SLIDE_H_PX - top - PAGE_PADDING_PX
    share = ratio[0] / (ratio[0] + ratio[1])
    lead_w = content_w * share - SPLIT_BARE_GAP / 2
    _, tf = _textbox(slide, PAGE_PADDING_PX, top, lead_w, avail_h)
    p = tf.paragraphs[0]
    _set_run(p.add_run(), lead, SIZE_H2, True, primary(theme), FONT_HEADING)
    paras = _as_list(aside)
    if paras:
        aside_left = PAGE_PADDING_PX + lead_w + SPLIT_BARE_GAP
        _, tf2 = _textbox(slide, aside_left, top + 8, SLIDE_W_PX - PAGE_PADDING_PX - aside_left, avail_h)
        for i, para in enumerate(paras):
            p2 = _body(tf2.paragraphs[0] if i == 0 else tf2.add_paragraph())
            p2.space_after = Pt(10)
            _set_run(p2.add_run(), para, SIZE_PARAGRAPH, False, secondary(theme))
        if divider:
            x = PAGE_PADDING_PX + lead_w + SPLIT_BARE_GAP / 2
            lead_h = _text_lines(lead, lead_w, 32, avg_char_ratio=0.52) * 32 * 1.3
            aside_h = sum(_text_lines(t, SLIDE_W_PX - PAGE_PADDING_PX - aside_left, SIZE_PARAGRAPH_PX,
                                      avg_char_ratio=0.5) * SIZE_PARAGRAPH_PX * 1.45 + 13 for t in paras)
            _hairline(slide, x, top, x, top + min(max(lead_h, aside_h), avail_h), theme)
    return _mark(slide, "statement")


def add_manifesto(prs, statement: str, columns: list[str] | None = None, theme: str = "light",
                  footnote: str | None = None):
    """The reference "headline as content" slide: no separate title — one
    Display-scale statement across the top ~two-thirds of the width IS the
    slide, with one or two narrow body columns beneath it (the detail behind
    the claim) and an optional caption-scale footnote bottom-left. Use it
    for an opening thesis or a chapter's one-paragraph argument; never for
    a slide that also needs a diagram. `columns` holds 0–2 paragraphs."""
    slide = add_blank_slide(prs, theme=theme)
    content_w = SLIDE_W_PX - 2 * PAGE_PADDING_PX
    stmt_w = content_w * 0.85
    lines = _text_lines(statement, stmt_w, 64, avg_char_ratio=0.55)
    stmt_h = lines * 77          # a little over the 72px Display leading, so the box never clips
    _, tf = _textbox(slide, PAGE_PADDING_PX, PAGE_PADDING_PX, stmt_w, stmt_h)
    _set_run(tf.paragraphs[0].add_run(), statement, SIZE_DISPLAY, True, primary(theme), FONT_HEADING)
    slide._smartcat_content_top = PAGE_PADDING_PX + stmt_h + HEADING_GAP_PX
    cols = _as_list(columns)[:2]
    if cols:
        # Body columns take a reading measure of ~60 characters (content_w/2
        # minus the gap), never the full slide width.
        col_w = (content_w - SPLIT_BARE_GAP) / 2
        y = PAGE_PADDING_PX + stmt_h + HEADING_GAP_PX
        col_h = SLIDE_H_PX - PAGE_PADDING_PX - y - (40 if footnote else 0)
        for i, para in enumerate(cols):
            _, tfc = _textbox(slide, PAGE_PADDING_PX + i * (col_w + SPLIT_BARE_GAP), y, col_w, col_h)
            pc = _body(tfc.paragraphs[0])
            _set_run(pc.add_run(), para, SIZE_PARAGRAPH, False, secondary(theme))
    if footnote:
        _, tff = _textbox(slide, PAGE_PADDING_PX, SLIDE_H_PX - PAGE_PADDING_PX - 24, content_w, 24)
        _set_run(tff.paragraphs[0].add_run(), footnote, SIZE_CAPTION, False, secondary(theme))
    return _mark(slide, "statement")


FACT_ROW_H = 34
RULE_STAT_GAP = 28


def _draw_facts(slide, items: list[dict], left: float, top: float, width: float, columns: int, theme: str):
    """A fact ladder: many small figures, each `value` bold in the heading
    face and primary colour with its `label` inline after it in secondary —
    "11 238 athletes", "306 events" — in one or two columns. The reference
    device for 6–12 supporting numbers that are evidence, not headlines."""
    gutter = 40
    col_w = (width - gutter * (columns - 1)) / columns
    n_rows = ceil(len(items) / columns)
    for i, it in enumerate(items):
        col, row = divmod(i, n_rows)
        x = left + col * (col_w + gutter)
        y = top + row * FACT_ROW_H
        _, tf = _textbox(slide, x, y, col_w, FACT_ROW_H - 6)
        p = tf.paragraphs[0]
        _set_run(p.add_run(), f"{it['value']} ", SIZE_PARAGRAPH, True, primary(theme), FONT_HEADING)
        _set_run(p.add_run(), it["label"], SIZE_PARAGRAPH, False, secondary(theme))


def add_roster(prs, title: str, people: list[dict], theme: str = "light", columns: int = 3,
               aside: str | None = None):
    """A people grid — the reference "thought leaders" / team slide: a
    circle-crop portrait (a labelled placeholder until the photo lands),
    name in bold, role in secondary, in `columns` columns, with the title in
    a left column and an optional aside under it. `people`:
    [{"name", "role", "photo" (optional path)}], 3–12 items."""
    assert 3 <= len(people) <= 12
    slide = add_blank_slide(prs, theme=theme)
    top = _add_slide_title(slide, title)
    content_w = SLIDE_W_PX - 2 * PAGE_PADDING_PX
    avail_h = SLIDE_H_PX - top - PAGE_PADDING_PX
    if aside:
        _, tfa = _textbox(slide, PAGE_PADDING_PX, top, content_w * 0.25, avail_h)
        pa = _body(tfa.paragraphs[0])
        _set_run(pa.add_run(), aside, SIZE_PARAGRAPH, False, secondary(theme))
        grid_left = PAGE_PADDING_PX + content_w * 0.25 + SPLIT_BARE_GAP
    else:
        grid_left = PAGE_PADDING_PX
    grid_w = SLIDE_W_PX - PAGE_PADDING_PX - grid_left
    n_rows = ceil(len(people) / columns)
    col_w = (grid_w - 24 * (columns - 1)) / columns
    row_h = min(96.0, (avail_h - 16 * (n_rows - 1)) / n_rows)
    portrait = min(64.0, row_h - 8)
    total = row_h * n_rows + 16 * (n_rows - 1)
    y0 = top + max(0, (avail_h - total) / 2)
    for i, person in enumerate(people):
        r, c = divmod(i, columns)
        x = grid_left + c * (col_w + 24)
        y = y0 + r * (row_h + 16)
        if person.get("photo"):
            pic = slide.shapes.add_picture(person["photo"], px(x), px(y), px(portrait), px(portrait))
            _no_shadow(pic)
        else:
            circ = _no_shadow(slide.shapes.add_shape(MSO_SHAPE.OVAL, px(x), px(y), px(portrait), px(portrait)))
            circ.fill.solid()
            circ.fill.fore_color.rgb = panel_fill(theme)
            circ.line.color.rgb = secondary(theme)
            circ.line.width = Pt(1)
            _set_line_dash(circ.line)
            draw_icon(slide, "user", x + portrait * 0.3, y + portrait * 0.3, portrait * 0.4, secondary(theme))
        _, tf = _textbox(slide, x + portrait + 16, y + 4, col_w - portrait - 16, row_h - 4)
        p = tf.paragraphs[0]
        _set_run(p.add_run(), person["name"], SIZE_PARAGRAPH, True, primary(theme))
        p2 = _body(tf.add_paragraph())
        _set_run(p2.add_run(), person.get("role", ""), SIZE_CAPTION, False, secondary(theme))
    return _mark(slide, "roster")


def add_image_mosaic(prs, title: str, captions: list[str], theme: str = "light", layout: str = "1+2",
                     paragraph: str | None = None):
    """Two to four reserved image slots composed as one object — same radius,
    same gutter, so the set reads as a single mosaic (the reference
    portfolio and photo-grid slides). Layouts, all inside the padding:
      "1+2"  — one large square left, two smaller squares stacked right (3 captions)
      "2x2"  — four equal squares (4 captions)
      "row"  — two or three equal squares in a row (2–3 captions)
    The promo shots are square, so every cell is square. An optional
    `paragraph` takes the room left beside the mosaic (1+2 and row)."""
    slide = add_blank_slide(prs, theme=theme)
    top = _add_slide_title(slide, title)
    content_w = SLIDE_W_PX - 2 * PAGE_PADDING_PX
    avail_h = SLIDE_H_PX - top - PAGE_PADDING_PX
    g = 8
    cells = []
    if layout == "1+2":
        assert len(captions) == 3
        big = avail_h
        small = (big - g) / 2
        x0 = PAGE_PADDING_PX
        cells = [(x0, top, big, big), (x0 + big + g, top, small, small), (x0 + big + g, top + small + g, small, small)]
        used_w = big + g + small
    elif layout == "2x2":
        assert len(captions) == 4
        s = (avail_h - g) / 2
        x0 = PAGE_PADDING_PX
        cells = [(x0, top, s, s), (x0 + s + g, top, s, s), (x0, top + s + g, s, s), (x0 + s + g, top + s + g, s, s)]
        used_w = 2 * s + g
    elif layout == "row":
        assert 2 <= len(captions) <= 3
        n = len(captions)
        s = min(avail_h, (content_w - g * (n - 1)) / n)
        x0 = PAGE_PADDING_PX
        cells = [(x0 + i * (s + g), top + (avail_h - s) / 2, s, s) for i in range(n)]
        used_w = n * s + g * (n - 1)
    else:
        raise ValueError(layout)
    for (x, y, w, h), cap in zip(cells, captions):
        draw_image_slot(slide, x, y, w, h, cap, theme)
    if paragraph and used_w < content_w - 200:
        px_left = PAGE_PADDING_PX + used_w + SPLIT_BARE_GAP
        _, tf = _textbox(slide, px_left, top, SLIDE_W_PX - PAGE_PADDING_PX - px_left, avail_h)
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        _set_run(_body(tf.paragraphs[0]).add_run(), paragraph, SIZE_PARAGRAPH, False, secondary(theme))
    return _mark(slide, "mosaic")


def add_quote(prs, quote_text: str, author_name: str, author_title: str = "",
              company: str = "", theme: str = "dark"):
    slide = add_blank_slide(prs, theme=theme, brand_bg=True)
    color = _content_color(slide)
    _, tf = _textbox(slide, PAGE_PADDING_PX, PAGE_PADDING_PX + 40,
                      SLIDE_W_PX - 2 * PAGE_PADDING_PX, 340)
    p = tf.paragraphs[0]
    _set_run(p.add_run(), quote_text, SIZE_H2, True, color, FONT_HEADING)
    attribution = author_name
    if author_title:
        attribution += f", {author_title}"
    if company:
        attribution += f" — {company}"
    _, tf2 = _textbox(slide, PAGE_PADDING_PX, SLIDE_H_PX - PAGE_PADDING_PX - 40,
                       SLIDE_W_PX - 2 * PAGE_PADDING_PX, 30)
    p2 = tf2.paragraphs[0]
    _set_run(p2.add_run(), attribution, SIZE_CAPTION, False, color)
    return _mark(slide, "quote")


def _add_linked_runs(p, line: str, size, color, link_color, links: dict[str, str]):
    """Write `line` as runs, turning every occurrence of a `links` phrase
    (case-insensitive) into a real hyperlink run in the link colour,
    underlined — underline means "link" in this system and nothing else."""
    if not links:
        _set_run(p.add_run(), line, size, False, color)
        return
    pattern = re.compile("|".join(re.escape(k) for k in sorted(links, key=len, reverse=True)), re.IGNORECASE)
    pos = 0
    for m in pattern.finditer(line):
        if m.start() > pos:
            _set_run(p.add_run(), line[pos:m.start()], size, False, color)
        run = p.add_run()
        _set_run(run, m.group(0), size, False, link_color)
        run.font.underline = True
        run.hyperlink.address = links[next(k for k in links if k.lower() == m.group(0).lower())]
        pos = m.end()
    if pos < len(line):
        _set_run(p.add_run(), line[pos:], size, False, color)


def add_closing(prs, title: str, contact_lines: list[str] | None = None, theme: str = "dark",
                links: dict[str, str] | None = None):
    """No .btn anywhere — a deck is presented, not clicked. Contact info is
    plain text with REAL hyperlinks on the call-to-action phrases: `links`
    maps a phrase to a URL and defaults to CLOSING_LINKS ("book a demo",
    "start a free trial"), so any closing line that says either gets linked
    automatically. Link text takes --content-link-default (brand purple,
    theme-aware) and an underline. Pass `links={}` to disable."""
    links = CLOSING_LINKS if links is None else links
    slide = add_blank_slide(prs, theme=theme)
    color = primary(theme)
    # Room for a two-line Display title plus the contact block; the box is
    # top-anchored so extra height is harmless, too little clips the lines.
    box_h = 2 * 77 + 40 + 40 * len(contact_lines or [])
    _, tf = _textbox(slide, PAGE_PADDING_PX, PAGE_PADDING_PX,
                      SLIDE_W_PX - 2 * PAGE_PADDING_PX, box_h)
    p = tf.paragraphs[0]
    _set_run(p.add_run(), title, SIZE_DISPLAY, True, color, FONT_HEADING)
    if contact_lines:
        for i, line in enumerate(contact_lines):
            p2 = tf.add_paragraph()
            # A Display-scale headline needs real air beneath it before the
            # contact lines — 40px (--spacing-8) off the title, then the lines
            # sit together as one block.
            p2.space_before = Pt(30) if i == 0 else Pt(6)
            _body(p2)
            _add_linked_runs(p2, line, SIZE_PARAGRAPH, secondary(theme), brand_content(theme), links)
    return _mark(slide, "closing")


# ── Verification ───────────────────────────────────────────────────────────

def check_overflow(prs: Presentation) -> list[dict]:
    """The pptx equivalent of the HTML skills' bounding-box overflow check:
    flag any shape whose box extends past the slide edges. This does NOT
    catch text that overflows ITS OWN shape (pptx autosize can hide that
    silently) — inspect long values/labels by eye in addition to this."""
    problems = []
    sw, sh = prs.slide_width, prs.slide_height
    for i, slide in enumerate(prs.slides):
        for shape in slide.shapes:
            if shape.left is None:
                continue
            if shape.left < 0 or shape.top < 0 or \
               shape.left + shape.width > sw + Emu(1000) or \
               shape.top + shape.height > sh + Emu(1000):
                problems.append({
                    "slide": i + 1,
                    "shape": shape.shape_type,
                    "name": shape.name,
                    "left_px": round(shape.left / EMU_PER_PX, 1),
                    "top_px": round(shape.top / EMU_PER_PX, 1),
                })
    return problems


# Screenshot-inviting language — see deck-design-brain.md Design DNA, "A slide
# about a product surface reserves room for it." This is a MECHANICAL BACKSTOP
# for that rule, added after a deck shipped with zero image slots despite a
# flow-chain step captioned "Side by side, per language" sitting right next to
# a slide claiming "review in context." The rule was correctly known and still
# never got applied at plan time — a purely written rule wasn't enough, so this
# gives the same rule a code-level trigger that runs regardless of how the deck
# was planned. A hit here is not automatically wrong (the phrase can appear
# without describing an actual screen), but it must be looked at and either
# resolved (add a slot) or consciously dismissed — never silently passed over.
_SCREENSHOT_TRIGGER_PHRASES = (
    "side by side", "before and after", "before/after", "in context",
    "see before", "see it", "see the", "review view", "the dashboard",
    "the interface", "the screen", "your workspace", "the conversation",
    "drop in a file", "drop a file",
)


def check_missing_image_slots(prs) -> list[dict]:
    """Flag every slide whose own text contains screenshot-inviting language
    (see `_SCREENSHOT_TRIGGER_PHRASES`) but carries no reserved image slot.
    Run this alongside `check_overflow` on every build, before reporting the
    shot list from `image_slots()` — it catches exactly the case that
    passive reporting cannot: a slide that should have reserved a slot and
    didn't, which `image_slots()` has no way to notice since it only lists
    slots that already exist.

    MUST be called on the same in-memory `prs` you just built, before
    saving — not on a `Presentation(...)` re-opened from the saved file.
    `_smartcat_image_slots` is a plain Python attribute set on the slide
    object during the build; it is never written into the .pptx XML, so a
    reloaded presentation has no way to know which slides already have a
    slot and this would flag every slide with matching language, slotted
    or not. (Step 5's own text-dump check re-opens the saved file for a
    different reason — do not reuse that reloaded object here.)"""
    flagged = []
    for i, slide in enumerate(prs.slides, start=1):
        if getattr(slide, "_smartcat_image_slots", None):
            continue   # already has a slot; not a miss
        text = " ".join(
            shp.text_frame.text.lower()
            for shp in slide.shapes
            if shp.has_text_frame and shp.text_frame.text
        )
        hits = [p for p in _SCREENSHOT_TRIGGER_PHRASES if p in text]
        if hits:
            flagged.append({"slide": i, "matched_phrases": hits})
    return flagged


# ── Layout variety, theme rhythm and canvas fill — mechanical backstops ────
# These exist for the same reason check_missing_image_slots does: the rules
# ("vary the silhouette", "alternate themes in bands", "a slide has to earn
# its canvas") were all written down, twice, and generated decks still came
# out as eleven light slides each carrying a title over one squat strip of
# boxes. A written rule that nothing asks about at build time is not a rule.

VARIETY_MAX_SHARE = 1 / 3      # no one silhouette carries more than a third of the content slides
VARIETY_MIN_DISTINCT = 4       # …and a deck of 8+ content slides uses at least four different ones
THEME_MAX_SHARE = 0.8          # no theme carries more than 80% of the content slides
FILL_MIN = 0.4                 # check threshold — a little under the builders' own 0.5 floor


def _content_slides(prs) -> list[tuple[int, str]]:
    out = []
    for i, slide in enumerate(prs.slides, start=1):
        sil = getattr(slide, "_smartcat_silhouette", None)
        if sil in _CONTENT_SILHOUETTES:
            out.append((i, sil))
    return out


def check_layout_variety(prs) -> list[dict]:
    """Flag the repetition a viewer sees at thumbnail scale. Three rules:
    (1) two directly adjacent slides never share a silhouette;
    (2) with 6+ content slides, no silhouette exceeds a third of them;
    (3) with 8+ content slides, at least four distinct silhouettes are used.
    A `list` silhouette (a bullet list as a whole slide) is flagged outright.
    Each hit says which rule and which slides, so it can be resolved by
    reshaping a slide — not by rotating templates for variety's sake.
    Run on the in-memory `prs` (silhouettes are runtime attributes)."""
    flagged = []
    content = _content_slides(prs)
    all_sils = [(i, getattr(s, "_smartcat_silhouette", None)) for i, s in enumerate(prs.slides, start=1)]
    for (i, a), (j, b) in zip(all_sils, all_sils[1:]):
        if a and a == b and a in _CONTENT_SILHOUETTES:
            flagged.append({"rule": "adjacent", "slides": [i, j], "silhouette": a,
                            "fix": "reshape one of the two — a split, a stack, a grid, a statement — "
                                   "or merge them if they make one point"})
    for i, sil in content:
        if sil == "list":
            flagged.append({"rule": "list-as-slide", "slides": [i], "silhouette": sil,
                            "fix": "a bullet list is a supporting element; recast as cards, rows, or a split"})
    n = len(content)
    if n >= 6:
        counts = {}
        for _, sil in content:
            counts[sil] = counts.get(sil, 0) + 1
        for sil, c in counts.items():
            if c / n > VARIETY_MAX_SHARE:
                flagged.append({"rule": "share", "slides": [i for i, s in content if s == sil],
                                "silhouette": sil, "count": c, "of": n,
                                "fix": f"{c} of {n} content slides are '{sil}' — convert some to a "
                                       "2x2 grid, a split with the copy beside it, a stack, or numbered rows"})
    if n >= 8 and len({s for _, s in content}) < VARIETY_MIN_DISTINCT:
        flagged.append({"rule": "distinct", "slides": [i for i, _ in content],
                        "silhouette": None, "count": len({s for _, s in content}), "of": n,
                        "fix": "the deck uses too few shapes overall — see the silhouette table in the deck brain"})
    return flagged


def check_theme_banding(prs) -> list[dict]:
    """Flag a deck whose content slides are (almost) all one theme. The
    reference decks are majority DARK on content slides, alternating in bands
    of 2–4; a deck that is light everywhere except the cover and dividers
    reads flat. Rule: no theme exceeds 80% of the content slides (5+ content
    slides)."""
    content = _content_slides(prs)
    if len(content) < 5:
        return []
    themes = [getattr(prs.slides[i - 1], "_smartcat_theme", "light") for i, _ in content]
    flagged = []
    for t in ("light", "dark"):
        share = themes.count(t) / len(themes)
        if share > THEME_MAX_SHARE:
            flagged.append({"rule": "theme-share", "theme": t, "share": round(share, 2),
                            "fix": f"{themes.count(t)} of {len(themes)} content slides are {t} — flip whole "
                                   "bands of 2–4 related slides to the other theme, not single slides"})
    return flagged


def _estimate_text_height(tf, box_w: float) -> float:
    """Estimated rendered height of a text frame, with the same char-count
    heuristic the builders size cards by. Not typesetting-accurate — close
    enough to catch a paragraph running past its card."""
    total = 0.0
    for p in tf.paragraphs:
        text = "".join(r.text for r in p.runs)
        if not text.strip():
            continue
        run = p.runs[0]
        size_px = (run.font.size.pt if run.font.size else SIZE_PARAGRAPH.pt) / 0.75
        heading = run.font.name == FONT_HEADING
        # Plus Jakarta Sans Bold averages ~0.52em per character at title
        # sizes (the same ratio _add_slide_title sizes its box with); Inter
        # body ~0.5em. Wider guesses here flagged one-line titles as two.
        ratio = 0.55 if (heading and size_px >= 60) else 0.52 if heading else 0.5
        leading = p.line_spacing if isinstance(p.line_spacing, float) else 1.2
        lines = _text_lines(text, box_w, size_px, avg_char_ratio=ratio)
        total += lines * size_px * leading
        total += (p.space_before.pt / 0.75 if p.space_before else 0) + (p.space_after.pt / 0.75 if p.space_after else 0)
    return total


def check_text_fit(prs, tolerance: float = 6) -> list[dict]:
    """Flag any text box whose estimated text height exceeds the box it was
    given — a paragraph running out of the bottom of its card, a caption
    wrapping out of a stat card. check_overflow only sees shapes past the
    slide edge; this is the text-inside-its-own-box counterpart the user
    asked for (2026-09-21: "watch out for text overflows and don't allow
    them"). Word-wrap-off boxes (numerals) and table cells are skipped."""
    flagged = []
    for i, slide in enumerate(prs.slides, start=1):
        for shp in slide.shapes:
            if not shp.has_text_frame or not shp.text_frame.text.strip() or shp.width is None:
                continue
            tf = shp.text_frame
            if tf.word_wrap is False:
                continue
            box_w = shp.width / EMU_PER_PX - (tf.margin_left + tf.margin_right) / EMU_PER_PX
            box_h = shp.height / EMU_PER_PX - (tf.margin_top + tf.margin_bottom) / EMU_PER_PX
            est = _estimate_text_height(tf, box_w)
            if est > box_h + tolerance:
                flagged.append({"slide": i, "text": tf.text[:60].replace("\n", " / "),
                                "estimated": round(est), "box": round(box_h),
                                "fix": "the text does not fit its box — shorten the copy, use a horizontal card, "
                                       "fewer items, or split the slide; never let it run past the card"})
    return flagged


def check_canvas_fill(prs) -> list[dict]:
    """Flag a content slide whose content occupies under FILL_MIN of the
    height available below the title — the squat-strip failure. Measures the
    vertical extent of every shape except the title. Deliberately sparse
    shapes (statement, quote, prose, furniture) are exempt. Run on the
    in-memory `prs`."""
    flagged = []
    for i, slide in enumerate(prs.slides, start=1):
        sil = getattr(slide, "_smartcat_silhouette", None)
        top = getattr(slide, "_smartcat_content_top", None)
        if sil is None or sil in _FILL_EXEMPT or top is None:
            continue
        title = getattr(slide, "_smartcat_title_shape", None)
        boxes = [(s.top / EMU_PER_PX, (s.top + s.height) / EMU_PER_PX)
                 for s in slide.shapes if s is not title and s.top is not None and s.height]
        if not boxes:
            continue
        extent = max(b for _, b in boxes) - min(t for t, _ in boxes)
        avail = SLIDE_H_PX - PAGE_PADDING_PX - top
        ratio = extent / avail
        if ratio < FILL_MIN:
            flagged.append({"slide": i, "silhouette": sil, "fill": round(ratio, 2),
                            "fix": "content is a strip in an empty canvas — two rows, a split with the copy "
                                   "beside it, a stack with the detail underneath, or merge with a neighbour"})
    return flagged


# ── Promo UI mockups — the second pass of reserve-then-fill ───────────────
# `images/promo-ui-mockups/<NN-product>/<description> -- <tag> - <tag>.<ext>`
# (CLAUDE.md "Promo UI mockups"). Reserve every slot first with
# draw_image_slot; then ONE call to fill_matched_slots does the whole lookup
# pass. It used to be left to the builder ("your own lookup") and it got
# skipped — a deck about the Content Translator Coworker shipped with two
# empty slots while four finished shots of exactly that product sat in the
# folder.

_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")
_PROMO_STOPWORDS = {
    "a", "an", "the", "of", "in", "on", "at", "to", "for", "and", "or", "is", "are", "with",
    "your", "our", "its", "it", "this", "that", "into", "from", "by", "as", "be", "you",
    "screenshot", "screen", "shot", "view", "image", "picture", "product", "showing", "shows",
    "slot", "here", "one", "using", "used", "use", "before", "after", "through", "going",
}
_PROMO_SYNONYMS = {"overview": "default", "generic": "default", "hero": "default", "homepage": "home",
                   "screenshots": "default", "interface": "ui", "editor": "editor", "settings": "settings",
                   "configure": "configuring", "configured": "configuring", "configuration": "configuring",
                   "personalise": "personalization", "personalize": "personalization",
                   "translating": "translate", "translation": "translate", "translated": "translate",
                   "localization": "localize", "localise": "localize", "localizing": "localize",
                   "reviewing": "review", "reviewer": "reviewer", "reviewed": "review",
                   "assign": "assigning", "assigned": "assigning", "assignment": "assignments",
                   "courses": "course", "docs": "pdf", "document": "pdf", "documents": "pdf",
                   "glossary": "glossaries", "memories": "memory", "l&d": "l&d", "learning": "learning"}


def _promo_tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9&]+", text.lower())
    out = set()
    for w in words:
        if w in _PROMO_STOPWORDS or len(w) < 2:
            continue
        w = _PROMO_SYNONYMS.get(w, w)
        out.add(w)
        if len(w) > 3 and w.endswith("s"):
            out.add(w[:-1])          # crude plural fold: files -> file
    return out


def list_promo_images(root: str, product: str | None = None) -> list[dict]:
    """The catalog: every image under `root`, parsed from its filename into
    {path, file, product, description, tags, tokens}. `product` (a substring
    of the folder name, e.g. "scorm" or "chief of staff") restricts it to
    one product folder. Print this at PLAN time when the deck is about one
    of the covered products, so slides are planned around the shots that
    exist rather than the lookup being an afterthought."""
    items = []
    if not root or not os.path.isdir(root):
        return items
    for dirpath, _, files in os.walk(root):
        folder = os.path.basename(dirpath)
        prod = re.sub(r"^\d+-", "", folder).replace("-", " ").strip()
        if product and product.lower().replace("-", " ") not in prod.lower():
            continue
        for fn in sorted(files):
            stem, ext = os.path.splitext(fn)
            if ext.lower() not in _IMAGE_EXTS:
                continue
            if " -- " in stem:
                desc, tagstr = stem.split(" -- ", 1)
                tags = [t.strip() for t in re.split(r"\s+-\s*|\s*-\s+", tagstr) if t.strip()]
            else:
                desc, tags = stem, []
            tokens = _promo_tokens(desc) | set().union(*(_promo_tokens(t) for t in tags)) if tags else _promo_tokens(desc)
            items.append({"path": os.path.join(dirpath, fn), "file": fn, "product": prod,
                          "description": desc.strip(), "tags": tags,
                          "tokens": tokens, "product_tokens": _promo_tokens(prod)})
    return items


def match_promo_image(caption: str, root: str, product: str | None = None,
                      exclude: set[str] | None = None, min_specific: int = 1) -> dict | None:
    """Best filename match for a slot caption, or None when nothing genuinely
    matches. Scoring: the caption must share at least `min_specific` token
    with the image's OWN description/tags (beyond the product name — every
    shot of a product mentions the product), plus one point when the caption
    names the product or `product` pins the folder. Ties go to the more
    specific image (fewer tokens). Images in `exclude` (already used) lose."""
    cap = _promo_tokens(caption)
    exclude = exclude or set()
    best = None
    for img in list_promo_images(root, product):
        specific = cap & (img["tokens"] - img["product_tokens"])
        product_hit = bool(cap & img["product_tokens"]) or product is not None
        # Three or more specific hits ("glossaries, translation memory,
        # profiles") identify the shot on their own; otherwise the caption
        # must also name the product, or the product folder must be pinned.
        if len(specific) < min_specific or (not product_hit and len(specific) < 3):
            continue
        score = len(specific) + (1 if product_hit else 0)
        key = (img["path"] not in exclude, score, -len(img["tokens"]))
        if best is None or key > best[0]:
            best = (key, img, sorted(specific))
    if best is None or best[0][1] < 2:
        return None
    _, img, matched = best
    return {**img, "score": best[0][1], "matched": matched, "reused": img["path"] in exclude}


def fill_matched_slots(prs, root: str, product: str | None = None) -> list[dict]:
    """THE lookup pass. For every still-empty reserved slot, find the best
    promo image and swap it in with fill_image_slot; each image is used once
    before any is reused. Returns one entry per slot — filled or not — so the
    handoff report can list what went where and which slots still need a
    shot. Leaves a slot untouched when nothing genuinely matches; never
    forces a weak match."""
    used: set[str] = set()
    report = []
    for entry in image_slots(prs):
        if entry["filled"]:
            used.add(entry.get("source", ""))
            report.append({"slide": entry["slide"], "caption": entry["caption"],
                           "source": entry.get("source"), "matched": "pre-filled"})
            continue
        m = match_promo_image(entry["caption"], root, product, exclude=used)
        if m:
            slide = prs.slides[entry["slide"] - 1]
            fill_image_slot(slide, entry["slot_index"], m["path"])
            used.add(m["path"])
            filled = slide._smartcat_image_slots[entry["slot_index"]]
            report.append({"slide": entry["slide"], "caption": entry["caption"], "source": m["file"],
                           "score": m["score"], "matched": m["matched"], "reused": m["reused"],
                           "fit": filled.get("fit"), "image_aspect": filled.get("image_aspect"),
                           "poor_fit": (filled.get("fit") or 1) < FIT_WARN})
        else:
            report.append({"slide": entry["slide"], "caption": entry["caption"], "source": None,
                           "size": f'{round(entry["width"])}×{round(entry["height"])} px'})
    return report


def unused_promo_images(prs, root: str, product: str | None = None) -> list[dict]:
    """Finished shots of `product` that no slot in the deck uses. A deck about
    a product that leaves most of its shots on the shelf is under-showing
    the product — each of these is a candidate slide (a banner, or the image
    side of a split) the plan should have considered."""
    used = {e.get("source") for e in image_slots(prs) if e.get("filled")}
    return [img for img in list_promo_images(root, product) if img["path"] not in used]


def run_all_checks(prs, promo_root: str | None = None, product: str | None = None,
                   verbose: bool = True) -> dict:
    """Every mechanical check in one call, in the right order, on the
    in-memory `prs` BEFORE saving. Fills matched promo slots first when
    `promo_root` is given, then runs overflow, missing-slot, variety, theme
    and fill checks, and lists the image slots and any unused product shots.
    Prints a plain report and returns the same as a dict. SKILL.md Step 5
    requires this call; do not cherry-pick individual checks instead."""
    result = {}
    if promo_root:
        result["promo_fills"] = fill_matched_slots(prs, promo_root, product)
        result["unused_promo"] = [i["file"] for i in unused_promo_images(prs, promo_root, product)]
    result["overflow"] = check_overflow(prs)
    result["text_overflow"] = check_text_fit(prs)
    result["missing_image_slots"] = check_missing_image_slots(prs)
    result["layout_variety"] = check_layout_variety(prs)
    result["theme_banding"] = check_theme_banding(prs)
    result["canvas_fill"] = check_canvas_fill(prs)
    result["image_slots"] = image_slots(prs)
    result["silhouettes"] = [(i, getattr(s, "_smartcat_silhouette", "?"), getattr(s, "_smartcat_theme", "?"))
                             for i, s in enumerate(prs.slides, start=1)]
    if verbose:
        print("slides:", " ".join(f"{i}:{sil}/{th[0]}" for i, sil, th in result["silhouettes"]))
        for key in ("overflow", "text_overflow", "missing_image_slots", "layout_variety", "theme_banding", "canvas_fill"):
            hits = result[key]
            print(f"{key}: {'ok' if not hits else ''}")
            for h in hits:
                print("   ", h)
        if promo_root:
            print("promo fills:")
            for r in result["promo_fills"]:
                line = f"slide {r['slide']}: {r['source'] or 'UNFILLED — ' + r.get('size', '')} <- {r['caption']}"
                if r.get("poor_fit"):
                    line += (f"   ** POOR FIT: image covers {int(r['fit'] * 100)}% of its slot "
                             f"(image aspect {r['image_aspect']}) — reshape with add_image_split / aspect **")
                print("   ", line)
            if result["unused_promo"]:
                print("unused product shots:", *result["unused_promo"], sep="\n    ")
        else:
            unfilled = [s for s in result["image_slots"] if not s["filled"]]
            print(f"image slots: {len(result['image_slots'])} total, {len(unfilled)} unfilled (no promo_root given)")
    return result
