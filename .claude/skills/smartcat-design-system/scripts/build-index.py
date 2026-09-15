#!/usr/bin/env python3
"""Regenerate INDEX.md — the component manifest the loader skill reads first.

Every component CSS file opens with a spec comment (see CLAUDE.md, "Component
file structure"). This script parses those comments into a compact table so a
skill can pick the right component without opening all 60 of them.

Run from the repo root:
  python .claude/skills/smartcat-design-system/scripts/build-index.py
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

# tier key -> (heading, directory, blurb)
TIERS = [
    ("atomic", "Atomic components", "components/atomic",
     "Small self-contained elements. Always embedded inside a larger component; "
     "never own a page row. No media queries — they respond through tokens alone."),
    ("page-level", "Page-level components (web)", "components/page-level",
     "Full-width page rows stacked to form a web page. Web only — never reused by "
     "one-pagers or documents."),
    ("onepager", "One-pager components", "components/onepager",
     "The one-pager tier. Never reuse web page-level components here, not even as "
     "a starting point."),
    ("document", "Document components", "components/document",
     "The document tier. Same reuse boundary as the one-pager tier."),
]

# Lines that end the prose description and begin a structured block.
BLOCK_START = re.compile(
    r"^(Figma|Properties|Component properties|Card properties|Visual variant|"
    r"Elements|Element presence|Content toggles|Content toggle|CSS-driven|State|"
    r"States|Structure|Nesting|Layout|Usage|Variants|Notes?|Sub-components?)\b",
    re.I,
)
DATA_ATTR = re.compile(r"^(data-[a-z0-9-]+)\s*(?:on\s+\.[a-z0-9_-]+\s*)?:\s*(.+)$", re.I)
NAME_LINE = re.compile(r"^/\*\s*[─\-—]*\s*(.+?)\s*[─\-—]{2,}")


def spec_comment(css: str) -> list[str]:
    """Return the lines of the leading /* ... */ spec comment, dedented."""
    if not css.lstrip().startswith("/*"):
        return []
    end = css.find("*/")
    if end == -1:
        return []
    block = css[: end]
    return [ln.rstrip() for ln in block.splitlines()]


def parse(path: Path) -> dict | None:
    try:
        css = path.read_text(encoding="utf-8-sig")
    except OSError:
        return None
    lines = spec_comment(css)
    if not lines:
        return None

    m = NAME_LINE.match(lines[0])
    name = m.group(1).strip() if m else path.stem

    prose: list[str] = []
    props: list[str] = []
    in_props = False

    for raw in lines[1:]:
        ln = raw.strip()
        if not ln:
            if prose:
                in_props = in_props or False
            continue
        if ln.startswith("Figma:") or (not prose and ln.startswith("Figma")):
            continue
        # A structured block begins: stop collecting prose.
        if BLOCK_START.match(ln):
            in_props = bool(re.match(r"^(Properties|Component|Card|Visual)", ln, re.I))
            continue
        am = DATA_ATTR.match(ln)
        if am:
            values = re.split(r"\s+[—–-]\s+", am.group(2))[0].strip()
            values = re.sub(r"\s+", " ", values)[:52]
            # "|" separates markdown table columns — escape it so a value list
            # like "2 | 3 | 4" stays inside its own cell.
            values = values.replace("|", "\\|")
            entry = f"`{am.group(1)}` {values}"
            if entry not in props:
                props.append(entry)
            in_props = True
            continue
        if in_props:
            # continuation line inside a properties block — skip
            continue
        if not BLOCK_START.match(ln):
            prose.append(ln)

    purpose = re.sub(r"\s+", " ", " ".join(prose)).strip()
    # Trim to the first sentence(s) that fit a compact cell.
    if len(purpose) > 165:
        cut = purpose[:165]
        dot = max(cut.rfind(". "), cut.rfind("; "))
        purpose = (cut[: dot + 1] if dot > 70 else cut.rstrip() + "…")
    purpose = purpose.replace("|", "\\|")

    root_class = ""
    for cm in re.finditer(r"^\s*(\.[a-z][a-z0-9_-]*)", css[css.find("*/") + 2 :], re.M):
        root_class = cm.group(1)
        break

    return {
        "name": name,
        "class": root_class,
        "props": props[:3],
        "purpose": purpose,
        "path": path.relative_to(ROOT).as_posix(),
        "dir": path.parent.name,
        "bytes": path.stat().st_size,
    }


def approx_tokens(n_bytes: int) -> int:
    return round(n_bytes / 4)


def table(rows: list[dict]) -> list[str]:
    out = ["| Component | Root class | Properties | Purpose | ~tok |",
           "|---|---|---|---|---|"]
    for r in rows:
        props = "<br>".join(r["props"]) if r["props"] else "—"
        out.append(
            f"| **{r['dir']}** | `{r['class']}` | {props} | {r['purpose']} "
            f"| {approx_tokens(r['bytes'])} |"
        )
    return out


def flat_files(rel_dir: str, exts=(".css", ".md")) -> list[dict]:
    d = ROOT / rel_dir
    rows = []
    for p in sorted(d.glob("*")):
        if p.suffix in exts and p.is_file():
            rows.append({
                "path": p.relative_to(ROOT).as_posix(),
                "bytes": p.stat().st_size,
                "purpose": first_line_purpose(p),
            })
    return rows


def first_line_purpose(p: Path) -> str:
    try:
        text = p.read_text(encoding="utf-8-sig")
    except OSError:
        return ""
    if p.suffix == ".md":
        for ln in text.splitlines():
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                return re.sub(r"\s+", " ", ln)[:150].replace("|", "\\|")
        return ""
    lines = spec_comment(text)
    prose = []
    for raw in lines[1:]:
        ln = raw.strip()
        if not ln or ln.startswith("Figma"):
            continue
        if BLOCK_START.match(ln):
            break
        prose.append(ln)
    return re.sub(r"\s+", " ", " ".join(prose))[:150].replace("|", "\\|")


def main() -> None:
    out: list[str] = []
    add = out.append

    add("# Smartcat design system — index")
    add("")
    add("The manifest the `smartcat-design-system` loader skill reads **first**, so it "
        "can open only the few files a task actually needs.")
    add("")
    add("> Generated by `.claude/skills/smartcat-design-system/scripts/build-index.py`. "
        "Do not edit by hand — re-run the script after adding or changing a component.")
    add("")

    total = sum(p.stat().st_size for p in ROOT.glob("components/**/*.css"))
    total += sum(p.stat().st_size for p in ROOT.glob("tokens/*.css"))
    total += sum(p.stat().st_size for p in ROOT.glob("base/*.css"))
    total += sum(p.stat().st_size for p in ROOT.glob("docs/*.md"))
    total += (ROOT / "CLAUDE.md").stat().st_size

    # Deliberately no commit SHA here: a stamp written before the commit that
    # contains it is always one behind. sync.sh reports the real DS_COMMIT.
    add(f"Full corpus ≈ {approx_tokens(total):,} tokens — **never read it all.** "
        f"`sync.sh` reports the commit you are actually on.")
    add("")

    add("## Reading order")
    add("")
    add("1. This file.")
    add("2. The rules for the ONE output format in play (see the table below) — not all five.")
    add("3. `tokens/` only when you need a specific token value; the format rules name the ones that matter.")
    add("4. The 3–5 component files the task actually calls for.")
    add("")

    # ---- Format rules -----------------------------------------------------
    add("## Output formats — read the rules for the one you are building")
    add("")
    add("Every format shares the same tokens. Only layout and component reuse differ.")
    add("")
    add("| Format | Canvas | Rules to read | Component source | ~tok |")
    add("|---|---|---|---|---|")
    fmt_rows = [
        ("Web page", "responsive, 2 breakpoints", "`CLAUDE.md` → sections up to “Component file structure”",
         "`components/page-level/` + `components/atomic/`", ROOT / "CLAUDE.md"),
        ("Deck", "1280×720 fixed", "`CLAUDE.md` → “Presentation decks” + `docs/deck-design-brain.md`",
         "compose freely from atomics; reshape page-level as a starting point",
         ROOT / "docs/deck-design-brain.md"),
        ("One-pager", "1280 wide, auto height", "`CLAUDE.md` → “One-pagers” + `docs/onepagers-design-brain.md`",
         "`components/onepager/` only", ROOT / "docs/onepagers-design-brain.md"),
        ("Document", "1290×1670 paginated", "`CLAUDE.md` → “Documents” + `docs/document-design-brain.md`",
         "`components/document/` only", ROOT / "docs/document-design-brain.md"),
        ("Social", "1080² / 1080×1350 / 1200×675", "`CLAUDE.md` → “Social assets” + `base/social-layout.css`",
         "compose freely from atomics; no social tier", ROOT / "base/social-layout.css"),
    ]
    for label, canvas, rules, source, sized in fmt_rows:
        tok = approx_tokens(sized.stat().st_size) if sized.exists() else 0
        add(f"| {label} | {canvas} | {rules} | {source} | {tok:,} |")
    add("")
    add("`CLAUDE.md` is ~19k tokens covering all five formats. Read the section you need, "
        "not the file — the shared rules (icons, logo, casing, punctuation, tokens-only CSS) "
        "sit above “Presentation decks”.")
    add("")

    # ---- Tokens & base ----------------------------------------------------
    for heading, rel in (("Tokens", "tokens"), ("Base layers", "base")):
        add(f"## {heading} (`{rel}/`)")
        add("")
        add("| File | Purpose | ~tok |")
        add("|---|---|---|")
        for r in flat_files(rel):
            add(f"| `{Path(r['path']).name}` | {r['purpose']} | {approx_tokens(r['bytes'])} |")
        add("")

    # ---- Component tiers --------------------------------------------------
    grand = 0
    for _key, heading, rel, blurb in TIERS:
        d = ROOT / rel
        if not d.is_dir():
            continue
        rows = []
        for css in sorted(d.glob("*/*.css")):
            parsed = parse(css)
            if parsed:
                rows.append(parsed)
        if not rows:
            continue
        tier_tokens = sum(approx_tokens(r["bytes"]) for r in rows)
        grand += tier_tokens
        add(f"## {heading} (`{rel}/`)")
        add("")
        add(blurb)
        add("")
        add(f"Files: `{rel}/<component>/<component>.css` and `.html` "
            f"(the `.html` is a reference template showing full anatomy, not an include). "
            f"{len(rows)} components, ≈{tier_tokens:,} tokens if read whole.")
        add("")
        out.extend(table(rows))
        add("")

    add("## Design-brain docs (`docs/`)")
    add("")
    add("How to *decide* what to build for a format — read alongside that format's rules.")
    add("")
    add("| File | Purpose | ~tok |")
    add("|---|---|---|")
    for r in flat_files("docs"):
        add(f"| `{Path(r['path']).name}` | {r['purpose']} | {approx_tokens(r['bytes'])} |")
    add("")

    (ROOT / "INDEX.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    size = len("\n".join(out))
    print(f"INDEX.md written - {size/1024:.1f} KB, ~{approx_tokens(size)} tokens")


if __name__ == "__main__":
    main()
