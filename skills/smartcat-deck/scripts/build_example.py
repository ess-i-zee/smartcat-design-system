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

    dp.add_cover(prs, "Smartcat platform overview", "Q4 2026 · Customer walkthrough", theme="dark")
    dp.add_section_divider(prs, "Why it matters.", theme="dark")
    dp.add_heading_paragraph(
        prs, "The problem today",
        "Manual translation review does not scale past a handful of languages. "
        "Teams either slow down launches or ship content nobody checked.",
        theme="light",
    )
    dp.add_bullet_list(prs, "What changes", [
        "AI pre-reviews every translation before a human sees it",
        "Only genuinely uncertain segments reach a reviewer",
        "Review time drops without lowering the bar",
    ], theme="light")
    dp.add_cards(prs, "How it works", [
        {"heading": "Ingest", "paragraph": "Content arrives from any connected source — CMS, file, or API."},
        {"heading": "Review", "paragraph": "The agent flags only what a human should look at."},
        {"heading": "Ship", "paragraph": "Approved content publishes automatically."},
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
            {"heading": "Review", "paragraph": "62% of team time."},
            {"heading": "Translate", "paragraph": "23% of team time."},
            {"heading": "Ship", "paragraph": "15% of team time."},
        ]},
        ratio=(5, 7), theme="light",
    )
    dp.add_table(
        prs, "Plan comparison", ["Plan", "Languages", "Reviewers", "Price"],
        [["Starter", "10", "2", "$400/mo"], ["Growth", "50", "8", "$1,200/mo"],
         ["Total (enterprise)", "280+", "Unlimited", "$4,800/mo"]],
        theme="light", highlight_last_row=True, highlight_first_col=True,
    )
    dp.add_flow_chain(
        prs, "Compliance checkpoints",
        ["Draft", "Legal review", "Redline", "Sign-off", "Archive"],
        theme="light",
        detail_cards=[
            {"heading": "Data residency", "paragraph": "EU content never leaves the region."},
            {"heading": "Audit trail", "paragraph": "Every edit is timestamped and attributed."},
            {"heading": "Access control", "paragraph": "Role-based, reviewed quarterly."},
        ],
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
