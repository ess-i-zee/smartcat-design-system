# Loading the design system without a shell

Use this when `sync.sh` cannot run — claude.ai on the web, a sandbox with no git,
or a shell that has no network. Everything else about the job is unchanged: read
the index, read one format's rules, read only the components you need.

## The URL pattern

The repo is public, so no auth is needed:

```
https://raw.githubusercontent.com/ess-i-zee/smartcat-design-system/main/<path>
```

`<path>` is exactly the repo-relative path — `tokens/colors.css`,
`components/onepager/flow/flow.css`, `docs/deck-design-brain.md`. Fetch with
WebFetch (or any HTTP fetch available). Each file is one request, ~0.2s.

Pin to a commit instead of `main` when you need the system to hold still across a
long build — swap `main` for the SHA:

```
https://raw.githubusercontent.com/ess-i-zee/smartcat-design-system/19ebbe9/tokens/colors.css
```

## Order

1. **`INDEX.md`** — always first.
   `https://raw.githubusercontent.com/ess-i-zee/smartcat-design-system/main/INDEX.md`
2. **`CLAUDE.md`** — one section, but note the caveat below.
3. **The design brain** for your format, from `docs/`.
4. **The three to five component files** `INDEX.md` pointed you at.

## The one real difference: you cannot grep

With a shell you read a slice of a file. Over HTTP you get the whole thing, so
`CLAUDE.md` costs its full ~19k tokens rather than the ~2k a single section costs.

That makes `INDEX.md` more valuable here, not less — its component table, root
classes and property lists often answer the question outright, with no component
file needed. Lean on it before fetching anything large.

If you only need a rule confirmed rather than the whole section, prefer the
design-brain doc for your format (`docs/*-design-brain.md`, ~4–7k tokens each)
over `CLAUDE.md`.

## Budget

The full corpus is ~116k tokens. A normal build should cost well under 30k:

| Fetch | ~tokens |
|---|---|
| `INDEX.md` | 5,000 |
| One design-brain doc | 4,000–7,000 |
| `CLAUDE.md` (whole — only if you truly need the rules verbatim) | 19,000 |
| Each component `.css` | 300–2,300 |
| Each token file | 1,500–4,000 |

## Reference examples

`references/` (finished screenshots and PDFs — see SKILL.md Step 5) works the
same way, one file at a time:

```
https://raw.githubusercontent.com/ess-i-zee/smartcat-design-system/main/references/decks/light/agenda.jpg
```

`INDEX.md`'s "Reference examples" table lists every pullable path with its file
count, size, and a few example filenames — read that first so you fetch one
named file rather than guessing. There's no directory listing over plain HTTP,
so a path you haven't confirmed in that table is a guess, not a lookup.
`references/mockups/` isn't in that table — leave it to `smartcat-mockup`,
which already builds its own raw URLs for that tree.

## Report back

Say that you used the raw-URL path and which ref you pinned to:

> Design system `main` via raw URLs (no shell) · one-pager rules + flow,
> numbered-cards, cta-band.

That flags to the reader that you fetched whole files rather than slices, and
that nothing was cached.
