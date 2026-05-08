# L3 file format strategy

When scaffolding L3 data files for any module (canonical, optional, or user-defined), pick the format from this table. The rule comes from the original digital-brain-skill source ([github.com/muratcankoylan/Agent-Skills-for-Context-Engineering, examples/digital-brain-skill/SKILL.md](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering/blob/main/examples/digital-brain-skill/SKILL.md) § "File Format Strategy").

| Format | Use when the data is | Examples |
|--------|----------------------|----------|
| `.jsonl` | An append-only list of dated records, OR an id-keyed record list mutated by id-rewrite. One self-contained record per line. | events, decisions (ADRs), gotchas, playbooks, reviews, runbooks, migrations, experiments, releases, contacts |
| `.yaml` | A named, structured tree describing the *shape* of something stable. Mutated by editing nodes in place. | glossary of terms, variant matrix, dataset registry, value system, relationship circles, goals tree |
| `.md` | Long-form narrative: prose the agent reads top to bottom. The L2 module file is always `.md`; additional `.md` files are rare at L3. | voice guide, calendar, todos, runbook walkthrough |

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

## YAML stub

Top-level key + a comment block showing one example entry. Mirror `templates/operations/variants.yaml.tmpl` and `templates/domain/glossary.yaml.tmpl`.

## ID format

JSONL entry IDs follow `{type}_{YYYYMMDD}_{HHMMSS}_{4hex}`. The `{type}` prefix is the file's `_schema` value, verbatim. Each schema's prefix lives only in its `.jsonl` template; keep them unique across the tree.

## Layout file

The opt-in `.exodia.yaml` at the target repo root nests canonical and custom categories under user-named parent groups. The file is authoritative when present; absent file = today's flat tree.

Schema (full example):

```yaml
context_dir: context        # optional; default "context"
structure:
  engineering:
    - architecture
    - patterns
    - debugging
    - operations
    - perf:                 # custom category
        purpose: "Performance work and benchmarks"
        ledgers:
          - file: bench.jsonl
            schema: bench
            scan_hint: "TODO comments under src/jobs/"
  product:
    - domain
```

Convention: under any key, a **list value** holds leaves (categories), a **map value** holds subgroups. List items are either bare strings (canonical category names) or single-key maps with a custom-category body (`purpose` + optional `ledgers`).

Validation rules (all errors fatal at file load):

1. `context_dir` matches `^[a-z._-][a-z0-9._-]*$` and is not `.` or `..`.
2. Every group name and category name (canonical or custom) matches `^[a-z][a-z0-9_-]*$`.
3. Group-name set and category-leaf set are disjoint.
4. Each leaf appears at most once anywhere in the tree.
5. Custom-category map: `purpose` is a non-empty string. `ledgers` optional; each ledger entry needs `file` + `schema`, `scan_hint` optional.
6. Tree depth has no hard cap.

Adding a new ledger to a custom category later: append to the `ledgers:` list with `file`, `schema`, optional `scan_hint`. Pick the file format from the table above; ID prefix conventions apply.
