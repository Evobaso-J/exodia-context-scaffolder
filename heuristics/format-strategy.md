# L3 file format strategy

When scaffolding L3 data files for any module (canonical, optional, or user-defined), pick the format from this table. The rule comes from the original digital-brain-skill source ([github.com/muratcankoylan/Agent-Skills-for-Context-Engineering, examples/digital-brain-skill/SKILL.md](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering/blob/main/examples/digital-brain-skill/SKILL.md) § "File Format Strategy").

The kernel below (between the `exodia:format-strategy` markers) is the runtime-facing version of this guidance; it is the single source for the `### File Format Strategy` block in emitted `AGENTS.md` files. Step 8 substitutes it into `rules/self-update.md`'s `{{FORMAT_STRATEGY}}` token verbatim. Keep the kernel terse and L3-focused so target repos receive runtime-appropriate examples. Anything below the kernel is scaffolder-only guidance (decision questions, JSONL header detail, ID format) and is not emitted.

<!-- exodia:format-strategy:start -->
| Format | Use when the data is | Examples |
| ------ | -------------------- | -------- |
| `.jsonl` | Append-only list of dated records, OR id-keyed record list mutated by id-rewrite. One self-contained record per line. | decisions, gotchas, playbooks, reviews, runbooks, migrations, experiments, releases |
| `.yaml` | Named, structured tree describing the *shape* of something stable. Mutated by editing nodes in place. | glossary, variants, datasets registry |
| `.md` | Long-form narrative: prose read top to bottom. The L2 module file is always `.md`; additional `.md` files at L3 are rare. | walkthroughs, calendars |

If two formats fit, prefer `.jsonl`; agents handle line-delimited records more reliably than nested YAML, and append-only is safer for long-running context. JSONL files always start with a single-line schema header: `{"_schema": "<type>", "_version": "1.0", "_description": "...", "_fields": [...]}`.
<!-- exodia:format-strategy:end -->

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

Top-level key + a comment block showing one example entry. Mirror `templates/operations/variants.yaml.tmpl` and `templates/glossary/glossary.yaml.tmpl`.

## ID format

JSONL entry IDs follow `{type}_{YYYYMMDD}_{HHMMSS}_{4hex}`. The `{type}` prefix is the file's `_schema` value, verbatim. Each schema's prefix lives only in its `.jsonl` template; keep them unique across the tree.
