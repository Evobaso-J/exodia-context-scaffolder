# L3 file format strategy

When scaffolding L3 data files for any module (core canonical or user-defined), pick the format from this table. The rule comes from the original digital-brain-skill source ([github.com/muratcankoylan/Agent-Skills-for-Context-Engineering, examples/digital-brain-skill/SKILL.md](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering/blob/main/examples/digital-brain-skill/SKILL.md) § "File Format Strategy").

| Format | Use when the data is | Examples |
| ------ | -------------------- | -------- |
| `.jsonl` | Append-only list of dated records, OR id-keyed record list mutated by id-rewrite. One self-contained record per line. | decisions, playbooks, reviews |
| `.yaml` | Named, structured tree describing the *shape* of something stable. Mutated by editing nodes in place. | glossary, variants, datasets registry |
| `.md` | Long-form narrative: prose read top to bottom. The L2 module file is always `.md`; additional `.md` files at L3 are rare. | walkthroughs, calendars |

If two formats fit, prefer `.jsonl`; agents handle line-delimited records more reliably than nested YAML, and append-only is safer for long-running context. JSONL files always start with a single-line schema header: `{"_schema": "<type>", "_version": "1.0", "_description": "...", "_fields": [...]}`.

## Decision questions (top-down)

1. Is each entry self-contained and timestamped, with new entries added over time? → `.jsonl`.
2. Is it a fixed set of named buckets that gets edited (not appended)? → `.yaml`.
3. Is it prose meant to be read sequentially? → `.md` (rarely needed at L3).

If two formats fit, prefer `.jsonl`: agents handle line-delimited records more reliably than nested YAML, and append-only is safer for long-running context.

## JSONL schema header

Every `.jsonl` file's first line is a schema descriptor:

```json
{"_schema": "<type>", "_version": "1.0", "_description": "...", "_fields": ["id", ...]}
```

`_fields` is exodia-specific (the source skill uses only `_schema` / `_version` / `_description`). Keep it: it gives future sessions an explicit field list to validate against.

## Baseline `_fields` for derived JSONL ledgers

When deriving `_fields` for a new ledger (custom category, or any non-core category under A2), every `_fields` array MUST include:

- `id`: canonical ID format `{schema}_{YYYYMMDD}_{HHMMSS}_{4hex}`.
- `title`: one-line label for the entry.
- `status`: lifecycle marker (`active`, `archived`, schema-specific values welcome).
- timestamp: `created` for append-only logs, `date` for event records (pick one based on schema semantics).

Two more SHOULD be included when applicable:

- `files`: citation list pointing at relevant files in the repo.
- `tags`: cross-cutting filters (free-form, schema-specific).

Schema-specific fields follow these. Place them in semantic order: cause-before-effect for incident-style schemas, before / after for change-style schemas, and so on.

This baseline is not emitted into the runtime kernel: once a ledger is scaffolded, its `_fields` header IS the contract for future agents appending to it. The prescription only applies at scaffolding time.

## YAML stub

Top-level key + a comment block showing one example entry. Mirror `templates/operations/variants.yaml.tmpl` and `templates/glossary/glossary.yaml.tmpl`.

## ID format

JSONL entry IDs follow `{type}_{YYYYMMDD}_{HHMMSS}_{4hex}`. The `{type}` prefix is the file's `_schema` value, verbatim. Each schema's prefix lives only in its `.jsonl` template; keep them unique across the tree.
