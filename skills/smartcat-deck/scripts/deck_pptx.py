"""deck_pptx.py — build a Smartcat-branded .pptx from the SAME tokens the HTML
design system uses, translated once here into pptx-native units (EMU, points,
RGBColor) so a deck built with this module lands in Google Slides as real,
editable shapes and text — not a picture of a slide.

Covers the CORE slide roles only (by explicit scope decision, 2026-09-15):
cover, section divider, heading+paragraph, bullet list, N-cards, stats,
quote, closing. Anything else in docs/deck-design-brain.md's full recipe
catalog (charts, gantt, timeline, flow/graph, comparison matrix) is NOT
covered — build those as an HTML deck via smartcat-deck's original path
instead, or extend this module following the same pattern.

Token values below are resolved snapshots from tokens/globals.css,
tokens/colors.css and tokens/typography.css (desktop tier) as of the commit
this module was built against — see the loader skill for the live values if
a design token has since changed. Do not hand-edit a color/size here without
checking it still matches the source token.

Usage — see build_example.py in this same folder for a full worked deck.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

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


# ── Core slide-role builders ──────────────────────────────────────────────
# Each mirrors a recipe in docs/deck-design-brain.md section C. Title
# placement follows Design DNA: cover = bottom-left, every other slide =
# top-left, flush at the 48px padding origin. No eyebrow text anywhere, no
# gradient blobs anywhere — both banned system-wide (CLAUDE.md).

def add_cover(prs, title: str, subtitle: str | None = None, theme: str = "dark"):
    slide = add_blank_slide(prs, theme=theme, layer=0)
    color = primary(theme)
    # Headline, bottom-left. Anchored by placing a tall box and bottom-aligning text.
    box_h = 220
    _, tf = _textbox(slide, PAGE_PADDING_PX, SLIDE_H_PX - PAGE_PADDING_PX - box_h,
                      SLIDE_W_PX - 2 * PAGE_PADDING_PX, box_h)
    tf.vertical_anchor = MSO_ANCHOR.BOTTOM
    p = tf.paragraphs[0]
    _set_run(p.add_run(), title, SIZE_DISPLAY, True, color, FONT_HEADING)
    if subtitle:
        p2 = tf.add_paragraph()
        _set_run(p2.add_run(), subtitle, SIZE_PARAGRAPH, False, secondary(theme))
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


def add_cards(prs, title: str, cards: list[dict], theme: str = "light"):
    """cards: [{heading, paragraph}], 2-4 items — see docs/deck-design-brain.md
    'Enumerated content -> N cards'."""
    assert 2 <= len(cards) <= 4, "N-cards recipe is 2-4 items"
    slide = add_blank_slide(prs, theme=theme)
    _add_slide_title(slide, title)
    top = PAGE_PADDING_PX + HEADING_GAP_PX
    gutter = 8
    n = len(cards)
    content_w = SLIDE_W_PX - 2 * PAGE_PADDING_PX
    card_w = (content_w - gutter * (n - 1)) / n
    card_h = SLIDE_H_PX - top - PAGE_PADDING_PX
    for i, card in enumerate(cards):
        left = PAGE_PADDING_PX + i * (card_w + gutter)
        _rounded_rect(slide, left, top, card_w, card_h, panel_fill(theme))
        pad = 24
        _, tf = _textbox(slide, left + pad, top + pad, card_w - 2 * pad, card_h - 2 * pad)
        p = tf.paragraphs[0]
        _set_run(p.add_run(), card["heading"], SIZE_H3, True, primary(theme), FONT_HEADING)
        p2 = tf.add_paragraph()
        p2.space_before = Pt(8)
        _set_run(p2.add_run(), card["paragraph"], SIZE_CAPTION, False, secondary(theme))
    return slide


def add_stats(prs, title: str, stats: list[dict], theme: str = "light"):
    """stats: [{value, label}], 2-4 items. Big brand-purple figure (Display
    scale) + bold caption — see deck-design-brain.md 'Quantitative & proof'.
    Keep `value` short — abbreviate large numbers ($1,200,000 -> $1.2M);
    this module does not re-check for overflow the way the HTML path's
    verify step does, so oversized values WILL visually overrun their panel."""
    assert 2 <= len(stats) <= 4, "stats recipe is 2-4 items"
    slide = add_blank_slide(prs, theme=theme)
    _add_slide_title(slide, title)
    top = PAGE_PADDING_PX + HEADING_GAP_PX
    gutter = 8
    n = len(stats)
    content_w = SLIDE_W_PX - 2 * PAGE_PADDING_PX
    card_w = (content_w - gutter * (n - 1)) / n
    card_h = SLIDE_H_PX - top - PAGE_PADDING_PX
    for i, stat in enumerate(stats):
        left = PAGE_PADDING_PX + i * (card_w + gutter)
        _rounded_rect(slide, left, top, card_w, card_h, panel_fill(theme))
        pad = 24
        _, tf = _textbox(slide, left + pad, top + pad, card_w - 2 * pad, card_h - 2 * pad)
        p = tf.paragraphs[0]
        _set_run(p.add_run(), stat["value"], SIZE_DISPLAY, True, C.BRAND, FONT_HEADING)
        p2 = tf.add_paragraph()
        p2.space_before = Pt(8)
        _set_run(p2.add_run(), stat["label"], SIZE_CAPTION, True, primary(theme))
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
