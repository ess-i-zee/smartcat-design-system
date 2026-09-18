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
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml import parse_xml
from pptx.oxml.ns import qn, nsdecls

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


def _draw_card_row(slide, cards: list[dict], left0: float, top: float, width: float,
                    height: float, theme: str, pad: float = 24):
    """Shared by add_cards and any composition that needs a card grid inside
    a sub-region of the slide (add_split's 'cards' panel, add_flow_chain's
    detail row) — see docs/deck-design-brain.md 'Enumerated content -> N
    cards'. `width`/`height` are the full row's box; cards divide it evenly
    with the 8px gutter, per Design DNA 'Gutter vs. slide padding'."""
    gutter = 8
    n = len(cards)
    card_w = (width - gutter * (n - 1)) / n
    for i, card in enumerate(cards):
        left = left0 + i * (card_w + gutter)
        _rounded_rect(slide, left, top, card_w, height, panel_fill(theme))
        _, tf = _textbox(slide, left + pad, top + pad, card_w - 2 * pad, height - 2 * pad)
        p = tf.paragraphs[0]
        _set_run(p.add_run(), card["heading"], SIZE_H3, True, primary(theme), FONT_HEADING)
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
    """cards: [{heading, paragraph}], 2-4 items — see docs/deck-design-brain.md
    'Enumerated content -> N cards'."""
    assert 2 <= len(cards) <= 4, "N-cards recipe is 2-4 items"
    slide = add_blank_slide(prs, theme=theme)
    _add_slide_title(slide, title)
    top = PAGE_PADDING_PX + HEADING_GAP_PX
    content_w = SLIDE_W_PX - 2 * PAGE_PADDING_PX
    card_h = SLIDE_H_PX - top - PAGE_PADDING_PX
    _draw_card_row(slide, cards, PAGE_PADDING_PX, top, content_w, card_h, theme)
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
    content_w = SLIDE_W_PX - 2 * PAGE_PADDING_PX
    card_h = SLIDE_H_PX - top - PAGE_PADDING_PX
    _draw_stat_row(slide, stats, PAGE_PADDING_PX, top, content_w, card_h, theme)
    return slide


# ── Asymmetric split, table, flow-chain ────────────────────────────────────
# Added 2026-09-18 after visually inspecting references/decks/ — real decks
# rarely divide a slide 50/50 or default to a plain card row; see
# docs/deck-design-brain.md section E's changelog entry for the full writeup.
# These three compose from the SAME tokens/helpers as everything above (no
# new geometry, no new colors) — they just place them less evenly, and add
# two shape kinds (native table, connector line) the module didn't use yet.

_SPLIT_SURFACE_KINDS = {"cards", "stat", "table"}


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
    elif kind == "cards":
        items = spec["items"]
        assert 2 <= len(items) <= 4, "split 'cards' panel is 2-4 items"
        _draw_card_row(slide, items, left, top, width, height, theme, pad=20)
    elif kind == "stat":
        _draw_stat_row(slide, [spec], left, top, width, height, theme)
    elif kind == "table":
        _draw_table(slide, left, top, width, height, spec["headers"], spec["rows"], theme=theme,
                    highlight_last_row=spec.get("highlight_last_row", False),
                    highlight_first_col=spec.get("highlight_first_col", False))
    else:
        raise ValueError(f"add_split: unknown panel kind {kind!r}")


def add_split(prs, title: str, left: dict, right: dict, ratio: tuple[int, int] = (5, 7),
              theme: str = "light"):
    """Asymmetric two-panel slide — the composition behind exec-summary-3col.jpg
    (narrative left, card grid right) and math-savings.jpg (one highlighted
    stat left, a value table right). This is a *reshape* of the existing
    heading+paragraph / N-cards / stats / table recipes side by side at an
    uneven width, not a new component — see deck-design-brain.md section E.

    `left` and `right` each describe one panel:
      {"kind": "text",  "paragraph": str, "bullets": [str, ...]}   (either or both)
      {"kind": "cards", "items": [{"heading", "paragraph"}, ...]}  (2-4 items)
      {"kind": "stat",  "value": str, "label": str, "desc": str}   (one figure; desc optional)
      {"kind": "table", "headers": [...], "rows": [[...], ...],
                         "highlight_last_row": bool, "highlight_first_col": bool}

    `ratio` is the (left, right) column share, e.g. (5, 7) or (4, 8) — need
    not sum to 12, only the proportion matters. Per Design DNA 'Gutter vs.
    slide padding': the two panels sit 8px apart when BOTH carry their own
    surface (cards/stat/table), else 48px (the slide's own padding) when
    either side is bare text — so a text+cards split reads as text sitting in
    the slide's whitespace next to a panel, not glued to it.
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


def add_flow_chain(prs, title: str, nodes: list[str], theme: str = "light",
                    detail_cards: list[dict] | None = None):
    """Horizontal chain of pill-shaped nodes joined by arrows — the native-
    pptx take on deck-design-brain.md 'Time & structure -> Flow / graph'
    (node-diagram.jpg, operating-model.jpg). `nodes` is 3-6 short labels
    rendered brand-purple, left to right, connected by straight arrow
    connectors — real lines/shapes, not a picture.

    Pass `detail_cards` (2-4 items, same shape as add_cards) to stack a
    supporting card row underneath the chain, matching compliance-risk-
    grid.jpg's two-layer composition (flow above, detail cards below); the
    two rows sit the 8px gutter apart since both carry their own surface.
    Omit it for the chain alone, e.g. vertically centered in the slide.

    Diagrams with organic/non-rectilinear connectors (curved arrows, a
    branching tree, icons inside nodes) are NOT what this builds — those stay
    on the HTML deck path; this covers the straight-chain case only.
    """
    assert 3 <= len(nodes) <= 6, "flow-chain recipe is 3-6 nodes"
    slide = add_blank_slide(prs, theme=theme)
    _add_slide_title(slide, title)
    top = PAGE_PADDING_PX + HEADING_GAP_PX
    content_w = SLIDE_W_PX - 2 * PAGE_PADDING_PX
    gutter = 8
    # Node-to-node spacing is deliberately wider than the 8px panel gutter:
    # that value is for two surfaces meeting at a seam, but here the gap
    # carries a routed connector + arrowhead, which needs room to read as an
    # arrow rather than a hairline between touching shapes.
    node_gap = 32
    n = len(nodes)
    node_h = 64
    node_w = (content_w - node_gap * (n - 1)) / n

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

    if detail_cards:
        assert 2 <= len(detail_cards) <= 4, "flow-chain detail row is 2-4 cards"
        cards_top = top + node_h + gutter
        cards_h = SLIDE_H_PX - cards_top - PAGE_PADDING_PX
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
