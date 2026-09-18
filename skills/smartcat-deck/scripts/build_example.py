"""build_example.py — a worked example exercising every core slide role in
deck_pptx.py. Run it to sanity-check the module after any change:

    python build_example.py out.pptx

Not a template to copy verbatim into a real deck — read deck_pptx.py's own
function signatures and docstrings, and docs/deck-design-brain.md for when
to reach for which role.
"""
import sys
import deck_pptx as dp


def build(out_path: str):
    prs = dp.new_deck()

    # Client business-case cover — logo lockup (Smartcat + client
    # placeholder, since we don't have Acme's real logo file), title in the
    # lower-middle band, and the bottom two-column prepared-by/for metadata
    # (deck-design-brain.md "Cover" — the other two metadata styles are
    # "top_right" and "footer"; see add_cover's docstring).
    dp.add_cover(
        prs, "Your global translation operating model",
        client_name="Acme Corp",
        metadata={
            "style": "bottom_columns",
            "prepared_by": ["Smartcat Account Team", "Alex Rivera · Priya Nandakumar"],
            "prepared_for": ["Soumen Das, VP Marketing Excellence", "Covadonga Fernández, Procurement"],
        },
    )
    dp.add_section_divider(prs, "Why it matters.", theme="dark")
    dp.add_heading_paragraph(
        prs, "The problem today",
        "Manual translation review does not scale past a handful of languages. "
        "Teams either slow down launches or ship content nobody checked.",
        theme="light",
    )
    dp.add_flow_chain(
        prs, "How it works",
        [
            {"icon": "upload-to-cloud", "label": "Tell it what you need", "caption": "Plain language, no setup."},
            {"icon": "workspace", "label": "It sets up the workspace", "caption": "Configured automatically."},
            {"icon": "integration", "label": "It routes the work", "caption": "To the right coworker or tool."},
            {"icon": "check-in-circle", "label": "You review and approve", "caption": "Nothing ships unchecked."},
        ],
        theme="light",  # default style="cards" — icon-bearing cards connected by arrows
    )
    dp.add_cards(prs, "Built for enterprise trust", [
        {"icon": "security", "heading": "SOC 2 compliant", "paragraph": "Infrastructure audited annually against SOC 2 Type II controls."},
        {"icon": "lock-closed", "heading": "Role-based access", "paragraph": "Every workspace enforces least-privilege permissions."},
        {"icon": "key", "heading": "SSO & identity", "paragraph": "Integrates with your existing identity provider."},
        {"icon": "check-in-circle", "heading": "Audit trails", "paragraph": "Every AI interaction is logged and reviewable."},
    ], theme="light")
    dp.add_stats(prs, "The numbers", [
        {"value": "70%", "label": "Faster review"},
        {"value": "280+", "label": "Languages supported"},
        {"value": "$1.2M", "label": "Saved annually"},
    ], theme="dark")
    dp.add_split(
        prs, "Where the time goes",
        left={"kind": "text",
              "paragraph": "Most localization teams spend the bulk of their week on "
                           "review, not translation itself.",
              "bullets": ["Manual spot-checks on every language", "No visibility into reviewer backlog"]},
        right={"kind": "cards", "items": [
            {"icon": "clock", "heading": "Review", "paragraph": "62% of team time."},
            {"icon": "translation", "heading": "Translate", "paragraph": "23% of team time."},
            {"icon": "rocket", "heading": "Ship", "paragraph": "15% of team time."},
        ]},
        ratio=(5, 7), theme="light",
    )

    # Grouped tiles + placeholders — categorized tool list as labeled tiles
    # instead of a nested bullet list; missing logos get a labeled
    # placeholder instead of being dropped (deck-design-brain.md Design DNA).
    tools_slide = dp.add_heading_paragraph(
        prs, "Learns your workflow. Fits your stack.",
        "Your AI Chief of Staff learns your role and preferences as you work "
        "together, so each session builds on the last.",
        theme="light",
    )
    right_x = dp.PAGE_PADDING_PX + (dp.SLIDE_W_PX - 2 * dp.PAGE_PADDING_PX) // 2 + 24
    tile_top = dp.PAGE_PADDING_PX + dp.HEADING_GAP_PX
    tile_w, tile_h, tile_gap = 150, 90, 8
    for i, tool in enumerate(["Adobe AEM", "Contentful", "Sitecore", "WordPress", "Google Drive", "Figma"]):
        col, row = i % 3, i // 3
        left = right_x + col * (tile_w + tile_gap)
        top = tile_top + row * (tile_h + tile_gap)
        dp.add_placeholder(tools_slide, left, top, tile_w, tile_h, f"Logo: {tool}", theme="light")
    dp.add_table(
        prs, "Plan comparison", ["Plan", "Languages", "Reviewers", "Price"],
        [["Starter", "10", "2", "$400/mo"], ["Growth", "50", "8", "$1,200/mo"],
         ["Total (enterprise)", "280+", "Unlimited", "$4,800/mo"]],
        theme="light", highlight_last_row=True, highlight_first_col=True,
    )
    dp.add_flow_chain(
        prs, "Compliance checkpoints",
        ["Draft", "Legal review", "Redline", "Sign-off", "Archive"],
        theme="light", style="pills",  # compact form, paired with the detail row it indexes into
        detail_cards=[
            {"icon": "globe", "heading": "Data residency", "paragraph": "EU content never leaves the region."},
            {"icon": "document-1", "heading": "Audit trail", "paragraph": "Every edit is timestamped and attributed."},
            {"icon": "lock-closed", "heading": "Access control", "paragraph": "Role-based, reviewed quarterly."},
        ],
    )
    # Quote-with-embedded-stats split — the quote's own wording names two
    # metrics ("50%" twice), so they're pulled into stat cards beside it
    # instead of standing alone as prose (deck-design-brain.md "Testimonial").
    dp.add_split(
        prs, "What Expondo says",
        left={"kind": "quote",
              "text": "We’ve been able to increase our productivity by 50% while "
                      "reducing our outsourcing costs by 50%.",
              "attribution": "Expondo"},
        right={"kind": "stats", "items": [
            {"value": "50%", "label": "Productivity increase", "desc": "Boosted operational efficiency across teams."},
            {"value": "50%", "label": "Cost reduction", "desc": "Direct savings on external outsourcing expenses."},
        ]},
        ratio=(6, 6), theme="light",
    )
    dp.add_quote(
        prs,
        "We don’t remove humans from the process. We reposition them "
        "where their judgment matters most.",
        "Alex Rivera", "VP Localization", "Acme Corp",
        theme="dark",
    )
    dp.add_closing(prs, "Questions? Thank you.", [
        "alex@smartcat.ai", "smartcat.ai/demo",
    ], theme="dark")

    problems = dp.check_overflow(prs)
    if problems:
        print("OVERFLOW DETECTED:")
        for p in problems:
            print(f"  slide {p['slide']}: {p['name']} at ({p['left_px']}, {p['top_px']})px")
    else:
        print(f"No shape-bounds overflow across {len(prs.slides)} slides.")

    prs.save(out_path)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "example-deck.pptx")
