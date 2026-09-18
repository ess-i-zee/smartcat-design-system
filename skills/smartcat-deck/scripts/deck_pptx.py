"""deck_pptx.py — build a Smartcat-branded .pptx from the SAME tokens the HTML
design system uses, translated once here into pptx-native units (EMU, points,
RGBColor) so a deck built with this module lands in Google Slides as real,
editable shapes and text — not a picture of a slide.

Covers the CORE slide roles only (by explicit scope decision, 2026-09-15,
extended 2026-09-18 twice — see docs/deck-design-brain.md section E's
changelog for the full writeup of each): cover, section divider,
heading+paragraph, bullet list (a supporting element, never a whole slide
alone), N-cards (icon- or number-anchored, height follows content), stats,
quote, closing, an asymmetric split, a table, and a flow chain (icon-cards
connected by arrows by default; a compact pill-chain variant for when it's
paired with a supporting detail-card row). Also provides a labeled
placeholder primitive for a missing image/logo asset. Anything else in
docs/deck-design-brain.md's full recipe catalog (charts, gantt, timeline,
comparison matrix, organic/branching flow diagrams) is NOT covered — build
those as an HTML deck via smartcat-deck's original path instead, or extend
this module following the same pattern.

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
    BRAND_TINT = RGBColor(0xF3, 0xF1, 0xFB)     # --color-non-semantic-purple-10 == --background-static-brand-layer-1 (light)
    PINK = RGBColor(0xC3, 0x26, 0xED)           # --color-non-semantic-pink-70 — the cover gradient's bottom-edge stop

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


def panel_fill(theme: str) -> RGBColor:
    # Light -> solid gray layer-1 panel. Dark -> a step lighter than the
    # slide bg, standing in for the CSS frosted-alpha panel (pptx has no
    # true backdrop blur) — see deck-design-brain.md Design DNA -> Surfaces.
    return C.LIGHT_BG[1] if theme == "light" else RGBColor(0x2B, 0x29, 0x37)


# ── Type — desktop tier, tokens/typography.css, px->pt at 96dpi (x0.75) ──
FONT_HEADING = "Plus Jakarta Sans"
FONT_BODY = "Inter"
WEIGHT_BOLD, WEIGHT_SEMIBOLD, WEIGHT_REGULAR = 700, 600, 400

SIZE_DISPLAY = Pt(48)   # 64px
SIZE_H1 = Pt(36)        # 48px — the deck's slide-title scale
SIZE_H2 = Pt(24)        # 32px
SIZE_H3 = Pt(18)        # 24px
SIZE_PARAGRAPH = Pt(13.5)  # 18px
SIZE_CAPTION = Pt(10.5)    # 14px

# px equivalents of the sizes above, for the card-height content estimate
# below (_text_lines / _measure_card_row_height) — kept in sync with the
# comments on the Pt() constants themselves.
SIZE_H3_PX = 24
SIZE_PARAGRAPH_PX = 18
SIZE_CAPTION_PX = 14
SIZE_DISPLAY_PX = 64

ANCHOR_SIZE = 40  # every card's icon/number-badge anchor — see deck-design-brain.md Design DNA "Surfaces"


def new_deck() -> Presentation:
    prs = Presentation()
    prs.slide_width = px(SLIDE_W_PX)
    prs.slide_height = px(SLIDE_H_PX)
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


def _draw_card_anchor(slide, kind: str, value, left: float, top: float, theme: str):
    """Every content card's required visual anchor (see deck-design-brain.md
    Design DNA "Surfaces") — a filled circle holding either a numbered badge
    (`kind="number"`, `value` an int) or a design-system icon
    (`kind="icon"`, `value` an icon name). The numbered badge is solid brand
    purple + white numeral in both themes, matching the stat figures'
    theme-independent brand-purple treatment. The icon tile is a light
    brand-tint circle + purple icon on light surfaces, and a solid brand
    circle + white icon on dark surfaces, for reliable contrast either way."""
    size = ANCHOR_SIZE
    circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, px(left), px(top), px(size), px(size))
    circ.line.fill.background()
    circ.shadow.inherit = False
    if kind == "number":
        circ.fill.solid()
        circ.fill.fore_color.rgb = C.BRAND
        tf = circ.text_frame
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        _set_run(p.add_run(), str(value), SIZE_H3, True, C.WHITE, FONT_HEADING)
    else:
        circ.fill.solid()
        circ.fill.fore_color.rgb = C.BRAND_TINT if theme == "light" else C.BRAND
        icon_color = C.BRAND if theme == "light" else C.WHITE
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


def _measure_card_row_height(cards: list[dict], width: float, pad: float = 24) -> float:
    """The natural height of a row of cards at `width`px total — the tallest
    card's content (anchor + heading + optional paragraph) plus padding."""
    gutter = 8
    n = len(cards)
    card_w = (width - gutter * (n - 1)) / n
    inner_w = card_w - 2 * pad
    tallest = 0.0
    for card in cards:
        h = ANCHOR_SIZE + 14
        h += _text_lines(card["heading"], inner_w, SIZE_H3_PX, avg_char_ratio=0.58) * SIZE_H3_PX * 1.3
        if card.get("paragraph"):
            h += 8 + _text_lines(card["paragraph"], inner_w, SIZE_CAPTION_PX, avg_char_ratio=0.5) * SIZE_CAPTION_PX * 1.45
        h += 2 * pad
        tallest = max(tallest, h)
    return tallest


def _measure_stat_row_height(stats: list[dict], width: float, pad: float = 24) -> float:
    """The natural height of a row of stat cards — see
    `_measure_card_row_height`'s docstring for why this exists. Stat cards
    are exempt from the icon/number-badge anchor (the figure itself is the
    anchor) but not from this — see deck-design-brain.md 'Numbers / stats'."""
    gutter = 8
    n = len(stats)
    card_w = (width - gutter * (n - 1)) / n
    inner_w = card_w - 2 * pad
    tallest = 0.0
    for stat in stats:
        h = _text_lines(stat["value"], inner_w, SIZE_DISPLAY_PX, avg_char_ratio=0.55) * SIZE_DISPLAY_PX * 1.15
        h += 8 + _text_lines(stat["label"], inner_w, SIZE_CAPTION_PX, avg_char_ratio=0.58) * SIZE_CAPTION_PX * 1.3
        if stat.get("desc"):
            h += 4 + _text_lines(stat["desc"], inner_w, SIZE_CAPTION_PX, avg_char_ratio=0.5) * SIZE_CAPTION_PX * 1.45
        h += 2 * pad
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
        conn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, px(left), px(y), px(left + block_w), px(y))
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
        conn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, px(left), px(top), px(left + col_w), px(top))
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
    muted_color = C.DARK_SECONDARY

    # Cover gradient — deck-design-brain.md Design DNA -> Color, "Cover
    # gradient": flat dark to ~48% down, through brand purple, to pink at
    # the bottom edge. Stops pixel-sampled from references/decks/cover/
    # (2026-09-18), identical across all three reference covers.
    bg_rect = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(0), px(0), px(SLIDE_W_PX), px(SLIDE_H_PX))
    bg_rect.line.fill.background()
    bg_rect.shadow.inherit = False
    _set_vertical_gradient(bg_rect, [
        (0.0, C.DARK_BG[0]), (0.48, C.DARK_BG[0]), (0.78, C.BRAND), (1.0, C.PINK),
    ])

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
        p2 = tf.add_paragraph()
        p2.space_before = Pt(12)
        _set_run(p2.add_run(), subtitle, SIZE_PARAGRAPH, False, muted_color)

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
    return slide


def add_section_divider(prs, title: str, theme: str = "dark"):
    slide = add_blank_slide(prs, theme=theme, layer=0)
    _, tf = _textbox(slide, PAGE_PADDING_PX, PAGE_PADDING_PX,
                      SLIDE_W_PX - 2 * PAGE_PADDING_PX, SLIDE_H_PX - 2 * PAGE_PADDING_PX)
    p = tf.paragraphs[0]
    _set_run(p.add_run(), title, SIZE_DISPLAY, True, primary(theme), FONT_HEADING)
    return slide


def _add_slide_title(slide, title: str):
    theme = slide._smartcat_theme
    _, tf = _textbox(slide, PAGE_PADDING_PX, PAGE_PADDING_PX,
                      SLIDE_W_PX - 2 * PAGE_PADDING_PX, 60)
    p = tf.paragraphs[0]
    _set_run(p.add_run(), title, SIZE_H1, True, _content_color(slide), FONT_HEADING)


def add_heading_paragraph(prs, title: str, paragraph: str, theme: str = "light"):
    slide = add_blank_slide(prs, theme=theme)
    _add_slide_title(slide, title)
    top = PAGE_PADDING_PX + HEADING_GAP_PX
    _, tf = _textbox(slide, PAGE_PADDING_PX, top,
                      (SLIDE_W_PX - 2 * PAGE_PADDING_PX) // 2, SLIDE_H_PX - top - PAGE_PADDING_PX)
    p = tf.paragraphs[0]
    _set_run(p.add_run(), paragraph, SIZE_PARAGRAPH, False, secondary(theme))
    return slide


def add_bullet_list(prs, title: str, bullets: list[str], theme: str = "light"):
    slide = add_blank_slide(prs, theme=theme)
    _add_slide_title(slide, title)
    top = PAGE_PADDING_PX + HEADING_GAP_PX
    _, tf = _textbox(slide, PAGE_PADDING_PX, top,
                      (SLIDE_W_PX - 2 * PAGE_PADDING_PX) // 2, SLIDE_H_PX - top - PAGE_PADDING_PX)
    for i, item in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(10)
        _set_run(p.add_run(), f"•  {item}", SIZE_PARAGRAPH, False, primary(theme))
    return slide


def _draw_card_row(slide, cards: list[dict], left0: float, top: float, width: float,
                    height: float, theme: str, pad: float = 24):
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
    for i, card in enumerate(cards):
        left = left0 + i * (card_w + gutter)
        _rounded_rect(slide, left, top, card_w, height, panel_fill(theme))
        icon = card.get("icon")
        _draw_card_anchor(slide, "icon" if icon else "number", icon or (i + 1), left + pad, top + pad, theme)
        text_top = top + pad + ANCHOR_SIZE + 14
        _, tf = _textbox(slide, left + pad, text_top, card_w - 2 * pad, height - (text_top - top) - pad)
        p = tf.paragraphs[0]
        _set_run(p.add_run(), card["heading"], SIZE_H3, True, primary(theme), FONT_HEADING)
        if card.get("paragraph"):
            p2 = tf.add_paragraph()
            p2.space_before = Pt(8)
            _set_run(p2.add_run(), card["paragraph"], SIZE_CAPTION, False, secondary(theme))


def _draw_stat_row(slide, stats: list[dict], left0: float, top: float, width: float,
                    height: float, theme: str, pad: float = 24):
    """Shared by add_stats and add_split's 'stat' panel (a single highlighted
    stat filling one side of an asymmetric split, e.g. math-savings.jpg) —
    see deck-design-brain.md 'Quantitative & proof -> Numbers / stats'.
    Each stat may include an optional `desc` line under the label."""
    gutter = 8
    n = len(stats)
    card_w = (width - gutter * (n - 1)) / n
    for i, stat in enumerate(stats):
        left = left0 + i * (card_w + gutter)
        _rounded_rect(slide, left, top, card_w, height, panel_fill(theme))
        _, tf = _textbox(slide, left + pad, top + pad, card_w - 2 * pad, height - 2 * pad)
        p = tf.paragraphs[0]
        _set_run(p.add_run(), stat["value"], SIZE_DISPLAY, True, C.BRAND, FONT_HEADING)
        p2 = tf.add_paragraph()
        p2.space_before = Pt(8)
        _set_run(p2.add_run(), stat["label"], SIZE_CAPTION, True, primary(theme))
        if stat.get("desc"):
            p3 = tf.add_paragraph()
            p3.space_before = Pt(4)
            _set_run(p3.add_run(), stat["desc"], SIZE_CAPTION, False, secondary(theme))


def add_cards(prs, title: str, cards: list[dict], theme: str = "light"):
    """cards: [{heading, paragraph, icon}], 2-4 items — see
    docs/deck-design-brain.md 'Enumerated content -> N cards'. `icon` is
    optional per card (a deck_icons.ICONS key); omit it for an automatic
    numbered badge. The row's height follows its own content (see
    `_measure_card_row_height`) and is vertically centered in the space below
    the title when that leaves extra room, rather than stretching cards to
    fill the slide — see Design DNA "Surfaces"."""
    assert 2 <= len(cards) <= 4, "N-cards recipe is 2-4 items"
    slide = add_blank_slide(prs, theme=theme)
    _add_slide_title(slide, title)
    top = PAGE_PADDING_PX + HEADING_GAP_PX
    content_w = SLIDE_W_PX - 2 * PAGE_PADDING_PX
    avail_h = SLIDE_H_PX - top - PAGE_PADDING_PX
    card_h = min(_measure_card_row_height(cards, content_w), avail_h)
    row_top = top + max(0, (avail_h - card_h) / 2)
    _draw_card_row(slide, cards, PAGE_PADDING_PX, row_top, content_w, card_h, theme)
    return slide


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


def add_stats(prs, title: str, stats: list[dict], theme: str = "light"):
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
    _add_slide_title(slide, title)
    top = PAGE_PADDING_PX + HEADING_GAP_PX
    content_w = SLIDE_W_PX - 2 * PAGE_PADDING_PX
    avail_h = SLIDE_H_PX - top - PAGE_PADDING_PX
    card_h = min(_measure_stat_row_height(stats, content_w), avail_h)
    row_top = top + max(0, (avail_h - card_h) / 2)
    _draw_stat_row(slide, stats, PAGE_PADDING_PX, row_top, content_w, card_h, theme)
    return slide


# ── Asymmetric split, table, flow-chain ────────────────────────────────────
# Added 2026-09-18 after visually inspecting references/decks/ — real decks
# rarely divide a slide 50/50 or default to a plain card row; see
# docs/deck-design-brain.md section E's changelog entry for the full writeup.
# These three compose from the SAME tokens/helpers as everything above (no
# new geometry, no new colors) — they just place them less evenly, and add
# two shape kinds (native table, connector line) the module didn't use yet.

_SPLIT_SURFACE_KINDS = {"cards", "stat", "stats", "table"}


def _render_split_panel(slide, spec: dict, left: float, top: float, width: float,
                         height: float, theme: str):
    """Render one side of add_split. `spec['kind']` selects the panel type —
    see add_split's docstring for the shape each kind expects."""
    kind = spec["kind"]
    if kind == "text":
        _, tf = _textbox(slide, left, top, width, height)
        wrote_first = False
        if spec.get("paragraph"):
            p = tf.paragraphs[0]
            _set_run(p.add_run(), spec["paragraph"], SIZE_PARAGRAPH, False, secondary(theme))
            wrote_first = True
        for bullet in spec.get("bullets", []):
            p = tf.paragraphs[0] if not wrote_first else tf.add_paragraph()
            wrote_first = True
            p.space_after = Pt(10)
            _set_run(p.add_run(), f"•  {bullet}", SIZE_PARAGRAPH, False, primary(theme))
    elif kind == "quote":
        # A quote panel whose own wording carries a metric worth pulling into
        # a neighboring 'stat'/'stats' panel — see deck-design-brain.md
        # "Testimonial." Bold pull-quote text, no gradient panel (the split
        # itself, plus the extracted stat card(s), carries the visual
        # weight); optional brand-purple attribution below.
        _, tf = _textbox(slide, left, top, width, height)
        p = tf.paragraphs[0]
        _set_run(p.add_run(), f"“{spec['text']}”", SIZE_H2, True, primary(theme), FONT_HEADING)
        if spec.get("attribution"):
            p2 = tf.add_paragraph()
            p2.space_before = Pt(16)
            _set_run(p2.add_run(), spec["attribution"], SIZE_PARAGRAPH, True, C.BRAND)
    elif kind == "cards":
        items = spec["items"]
        assert 2 <= len(items) <= 4, "split 'cards' panel is 2-4 items"
        row_h = min(_measure_card_row_height(items, width, pad=20), height)
        row_top = top + max(0, (height - row_h) / 2)
        _draw_card_row(slide, items, left, row_top, width, row_h, theme, pad=20)
    elif kind in ("stat", "stats"):
        items = [spec] if kind == "stat" else spec["items"]
        if kind == "stats":
            assert 2 <= len(items) <= 4, "split 'stats' panel is 2-4 items"
        row_h = min(_measure_stat_row_height(items, width, pad=20), height)
        row_top = top + max(0, (height - row_h) / 2)
        _draw_stat_row(slide, items, left, row_top, width, row_h, theme, pad=20)
    elif kind == "table":
        _draw_table(slide, left, top, width, height, spec["headers"], spec["rows"], theme=theme,
                    highlight_last_row=spec.get("highlight_last_row", False),
                    highlight_first_col=spec.get("highlight_first_col", False))
    else:
        raise ValueError(f"add_split: unknown panel kind {kind!r}")


def add_split(prs, title: str, left: dict, right: dict, ratio: tuple[int, int] = (5, 7),
              theme: str = "light"):
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

    `ratio` is the (left, right) column share, e.g. (5, 7) or (4, 8) — need
    not sum to 12, only the proportion matters. Per Design DNA 'Gutter vs.
    slide padding': the two panels sit 8px apart when BOTH carry their own
    surface (cards/stat/stats/table), else 48px (the slide's own padding)
    when either side is bare text or a quote — so a text+cards or quote+stats
    split reads as text sitting in the slide's whitespace next to a panel,
    not glued to it.
    """
    assert len(ratio) == 2 and ratio[0] > 0 and ratio[1] > 0
    slide = add_blank_slide(prs, theme=theme)
    _add_slide_title(slide, title)
    top = PAGE_PADDING_PX + HEADING_GAP_PX
    content_w = SLIDE_W_PX - 2 * PAGE_PADDING_PX
    content_h = SLIDE_H_PX - top - PAGE_PADDING_PX
    both_surfaced = left["kind"] in _SPLIT_SURFACE_KINDS and right["kind"] in _SPLIT_SURFACE_KINDS
    gap = 8 if both_surfaced else PAGE_PADDING_PX
    left_share = ratio[0] / (ratio[0] + ratio[1])
    left_w = content_w * left_share - gap / 2
    right_left = PAGE_PADDING_PX + left_w + gap
    right_w = SLIDE_W_PX - PAGE_PADDING_PX - right_left
    _render_split_panel(slide, left, PAGE_PADDING_PX, top, left_w, content_h, theme)
    _render_split_panel(slide, right, right_left, top, right_w, content_h, theme)
    return slide


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
    gframe = slide.shapes.add_table(n_rows, n_cols, px(left), px(top), px(width), px(height))
    tbl = gframe.table
    tbl.first_row = False
    tbl.horz_banding = False
    col_w = width / n_cols
    for c in range(n_cols):
        tbl.columns[c].width = px(col_w)
    header_h = min(height / n_rows, 40)
    body_h = (height - header_h) / max(len(rows), 1)
    for r in range(n_rows):
        tbl.rows[r].height = px(header_h if r == 0 else body_h)

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
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.RIGHT
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
    _add_slide_title(slide, title)
    top = PAGE_PADDING_PX + HEADING_GAP_PX
    content_w = SLIDE_W_PX - 2 * PAGE_PADDING_PX
    content_h = SLIDE_H_PX - top - PAGE_PADDING_PX
    _draw_table(slide, PAGE_PADDING_PX, top, content_w, content_h, headers, rows, theme=theme,
                highlight_last_row=highlight_last_row, highlight_first_col=highlight_first_col)
    return slide


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
    _add_slide_title(slide, title)
    top = PAGE_PADDING_PX + HEADING_GAP_PX
    content_w = SLIDE_W_PX - 2 * PAGE_PADDING_PX
    # Node-to-node spacing is deliberately wider than the 8px panel gutter:
    # that value is for two surfaces meeting at a seam, but here the gap
    # carries a routed connector + arrowhead, which needs room to read as an
    # arrow rather than a hairline between touching shapes.
    node_gap = 32
    n = len(nodes)
    node_w = (content_w - node_gap * (n - 1)) / n
    avail_h = SLIDE_H_PX - top - PAGE_PADDING_PX

    if style == "cards":
        pad = 20
        inner_w = node_w - 2 * pad
        node_h = ANCHOR_SIZE + 14
        node_h += max(_text_lines(nd["label"], inner_w, SIZE_PARAGRAPH_PX, avg_char_ratio=0.58)
                      for nd in nodes) * SIZE_PARAGRAPH_PX * 1.3
        if any(nd.get("caption") for nd in nodes):
            node_h += 8 + max(_text_lines(nd.get("caption", ""), inner_w, SIZE_CAPTION_PX, avg_char_ratio=0.5)
                               for nd in nodes) * SIZE_CAPTION_PX * 1.45
        node_h += 2 * pad
        node_h = min(node_h, avail_h)
        row_top = top + max(0, (avail_h - node_h) / 2)
        spans = []
        for i, nd in enumerate(nodes):
            left = PAGE_PADDING_PX + i * (node_w + node_gap)
            _rounded_rect(slide, left, row_top, node_w, node_h, panel_fill(theme))
            icon = nd.get("icon")
            _draw_card_anchor(slide, "icon" if icon else "number", icon or (i + 1), left + pad, row_top + pad, theme)
            text_top = row_top + pad + ANCHOR_SIZE + 14
            _, tf = _textbox(slide, left + pad, text_top, inner_w, node_h - (text_top - row_top) - pad)
            p = tf.paragraphs[0]
            _set_run(p.add_run(), nd["label"], SIZE_PARAGRAPH, True, primary(theme), FONT_HEADING)
            if nd.get("caption"):
                p2 = tf.add_paragraph()
                p2.space_before = Pt(6)
                _set_run(p2.add_run(), nd["caption"], SIZE_CAPTION, False, secondary(theme))
            spans.append((left, left + node_w))
        arrow_y = px(row_top + node_h / 2)
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
        connector = slide.shapes.add_connector(
            MSO_CONNECTOR.STRAIGHT, px(spans[i][1]), arrow_y, px(spans[i + 1][0]), arrow_y
        )
        connector.line.color.rgb = secondary(theme)
        connector.line.width = Pt(1.5)
        _add_arrowhead(connector, end="tail")

    if style == "pills" and detail_cards:
        assert 2 <= len(detail_cards) <= 4, "flow-chain detail row is 2-4 cards"
        cards_top = top + node_h + 8
        cards_avail_h = SLIDE_H_PX - cards_top - PAGE_PADDING_PX
        cards_h = min(_measure_card_row_height(detail_cards, content_w), cards_avail_h)
        _draw_card_row(slide, detail_cards, PAGE_PADDING_PX, cards_top, content_w, cards_h, theme)
    return slide


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
    return slide


def add_closing(prs, title: str, contact_lines: list[str] | None = None, theme: str = "dark"):
    """No .btn anywhere — a deck is presented, not clicked. Contact info is
    plain text, matching the HTML deck's own rule."""
    slide = add_blank_slide(prs, theme=theme)
    color = primary(theme)
    box_h = 160 if contact_lines else 80
    _, tf = _textbox(slide, PAGE_PADDING_PX, PAGE_PADDING_PX,
                      SLIDE_W_PX - 2 * PAGE_PADDING_PX, box_h)
    p = tf.paragraphs[0]
    _set_run(p.add_run(), title, SIZE_DISPLAY, True, color, FONT_HEADING)
    if contact_lines:
        for line in contact_lines:
            p2 = tf.add_paragraph()
            p2.space_before = Pt(6)
            _set_run(p2.add_run(), line, SIZE_PARAGRAPH, False, secondary(theme))
    return slide


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
