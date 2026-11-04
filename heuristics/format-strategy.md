# L3 file format strategy

When scaffolding L3 data files for any module (core canonical or user-defined), pick the format from this table. The rule comes from the original digital-brain-skill source ([github.com/muratcankoylan/Agent-Skills-for-Context-Engineering, examples/digital-brain-skill/SKILL.md](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering/blob/main/examples/digital-brain-skill/SKILL.md) § "File Format Strategy").

| Format | Use when the data is | Examples |
| ------ | -------------------- | -------- |
| entry directory (`<name>/`) | Growing list of dated records: one Markdown file per entry, frontmatter + prose body. | decisions, playbooks, reviews |
| `.yaml` | Named, structured tree describing the *shape* of something stable. Mutated by editing nodes in place. | glossary, variants, datasets registry |
| `.md` | Long-form narrative: prose read top to bottom. The L2 module file is always `.md`; additional `.md` files at L3 are rare. | walkthroughs, calendars |

If two formats fit, prefer the entry directory. A single append-only file makes every branch write to the same tail line, so parallel work conflicts on every merge; one file per entry gives each branch its own path and nothing to merge. Each directory carries a `_schema.md` describing the frontmatter fields and body sections.

## Decision questions (top-down)

1. Is each entry self-contained and timestamped, with new entries added over time? → entry directory.
2. Is it a fixed set of named buckets that gets edited (not appended)? → `.yaml`.
3. Is it prose meant to be read sequentially? → `.md` (rarely needed at L3).

If two formats fit, prefer the entry directory: it is the only shape that cannot conflict when two branches add entries at the same time.

## Entry-directory schema

Every entry directory carries a `_schema.md` that lists the frontmatter fields, the body sections, and the filename rule `{id}__{slug}.md`. Each entry file looks like:

```markdown
---
id: "pb_20260814_101500_a1b2"
title: "Google OAuth fails in dev/QA"
status: "active"
---

## Root cause

...
```

The field list in `_schema.md` is the contract: it gives future sessions an explicit set to validate an entry against, and it is what an agent reads before writing one.

Every `_schema.md` also carries a `## Retrieval` section, and it is not boilerplate. One file per entry only pays off if entries are *searched*: `rg -l '<term>' <dir>/` matches the bodies and the frontmatter, so an agent reads two entries instead of all 114. A directory listing is a weaker index: it carries the title and nothing else, so a task whose trigger word never made it into someone's title finds nothing. Emit the retrieval instruction next to the schema, because "read the ledger" is the habit it has to displace.

## Baseline fields for derived ledgers

When deriving the field list for a new ledger (custom category, or any non-core category under A2), every entry schema MUST include:

- `id`: canonical ID format `{schema}_{YYYYMMDD}_{HHMMSS}_{4hex}`.
- `title`: one-line label for the entry.
- `status`: lifecycle marker (`active`, `archived`, schema-specific values welcome). Never omit it: a schema without `status` makes retirement impossible, and the entries pile up forever.
- timestamp: `created` for growing logs, `date` for event records (pick one based on schema semantics).

Two more SHOULD be included when applicable:

- `files`: citation list pointing at relevant files in the repo.
- `tags`: cross-cutting filters (free-form, schema-specific).

Schema-specific fields follow these. Place them in semantic order: cause-before-effect for incident-style schemas, before / after for change-style schemas, and so on.

This baseline is not emitted into the runtime kernel: once a ledger is scaffolded, its `_schema.md` IS the contract for future agents writing entries into it. The prescription only applies at scaffolding time.

## YAML stub

Top-level key + a comment block showing one example entry. Mirror `templates/operations/variants.yaml.tmpl` and `templates/glossary/glossary.yaml.tmpl`.

## ID format

Entry IDs follow `{type}_{YYYYMMDD}_{HHMMSS}_{4hex}`, and the file is named `{id}__{slug}.md`. The `{type}` prefix is declared in the directory's `_schema.md`; keep the prefixes unique across the tree.
