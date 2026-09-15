# Skills

Source of truth for the Smartcat skills. Each subfolder is one skill, authored
and versioned here, then installed or uploaded from here.

| Skill | What it does |
|---|---|
| `smartcat-design-system/` | **The loader.** Fetches the current design system — tokens, rules, component specs — so the others don't carry their own copy. |
| `smartcat-deck/` | Presentation decks — a sequence of fixed 1280×720 slides. |
| `smartcat-onepager/` | One-pagers — a fixed 1280px-wide, variable-height document. |
| `smartcat-document/` | Multi-page documents — genuinely paginated 1290×1670 pages. |

The three format skills each delegate to the loader for the rules and hold only
what is specific to their format: the decision procedure, the geometry, the
failure modes and how to verify them. No skill for web pages yet.

## Why they live here and not in `.claude/skills/`

`.claude/skills/` is where Claude Code looks for skills belonging to *this*
project. These skills aren't about this project — they're about building
Smartcat assets anywhere. This folder is their home; the sections below are how
they get somewhere useful.

The trade-off: a skill sitting here is **not** auto-discovered by Claude Code.
Install it first.

## Installing one locally

Copy it into your user skills directory to make it available in every project on
this machine:

```bash
cp -r skills/smartcat-design-system ~/.claude/skills/   # one
cp -r skills/*/ ~/.claude/skills/                       # all of them
```

The format skills need the loader installed too — they delegate to it.

Re-copy after changing the skill itself. You do **not** need to re-copy when the
design system changes — that is the whole point of the loader: it fetches the
current system at run time.

## Uploading one to claude.ai

Zip the skill's folder (the folder itself, so `SKILL.md` sits at the archive
root) and upload it in Settings → Capabilities → Skills:

```bash
cd skills && zip -r smartcat-design-system.zip smartcat-design-system
```

That makes it available in Claude on the web and in the desktop app, alongside
the other `anthropic-skills:` ones.

## Writing another one

Each skill is a folder containing:

```
<skill-name>/
  SKILL.md          required — YAML frontmatter (name, description) + instructions
  scripts/          optional — anything the skill runs
  reference/        optional — docs the skill reads only when it needs them
```

The `description` in the frontmatter is what decides when the skill triggers, so
write it as a description of the *situation*, not the mechanism.

Keep `SKILL.md` short. It is loaded in full whenever the skill fires, so detail
that is only sometimes needed belongs in `reference/`, fetched on demand.

Skills that build Smartcat assets should delegate to `smartcat-design-system`
for the rules rather than restating them — a rule change is then a commit in this
repo, with no skill to re-upload.
