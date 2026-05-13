# `$LAYOUT_MAP` schema

`$LAYOUT_MAP` is the single in-memory artifact that drives Steps 5 to 9. Every mode (Fresh, Merge, Incremental, config-driven) shape-locks it at Step 4b and consumers read it without branching on mode. This file is the contract.

Output is a JSON array of category objects. Order is preserved and drives L2 draft order in Step 6.

**Deferred fields.** For custom categories added interactively (`kind: custom`, no config-declared `l3:`), Step 4b leaves `l3_specs` as `null`. Step 6 fills those slots in place once it has the category's purpose statement and can run schema inference (per `heuristics/format-strategy.md`). The shape and category set are finalized at 4b; only `null` `l3_specs` slots remain mutable, and only Step 6 mutates them. After Step 6, the map is fully immutable.

## Example

```json
[
  {
    "name": "architecture",
    "path": "docs/project/architecture",
    "kind": "canonical",
    "l2_template_path": "<SKILL_DIR>/templates/architecture/ARCHITECTURE.md.tmpl",
    "l3_specs": [
      {
        "filename": "decisions.jsonl",
        "schema_name": "adr",
        "schema_template_path": "<SKILL_DIR>/templates/architecture/decisions.jsonl.tmpl"
      }
    ]
  },
  {
    "name": "releases",
    "path": "docs/releases",
    "kind": "custom",
    "l2_template_path": null,
    "l3_specs": [
      {
        "filename": "release_notes.jsonl",
        "schema_name": null,
        "schema_template_path": null
      }
    ]
  }
]
```

## Fields

| Field | Type | Meaning |
|---|---|---|
| `name` | string | Category identifier, `^[a-z][a-z0-9_-]*$`. Canonical names: `architecture`, `design-patterns`, `glossary`, `operations`, `debugging`, `mobile`, `workspace`, `data`, `infra`. Anything else is `kind: custom`. |
| `path` | string | Repo-rooted destination under `$TARGET`. Same regex as config: `^[a-z._-][a-z0-9._/-]*$`. |
| `kind` | `"canonical"` or `"custom"` | Drives L2 template lookup and Step 6 schema-inference branching. |
| `l2_template_path` | string or `null` | Absolute path to the L2 `.md.tmpl` under `$SKILL_DIR/templates/<name>/`. `null` for custom categories without a template; Step 6 falls back to the default stub written by `init_structure.sh`. |
| `l3_specs` | array or `null` | Ordered list of L3 file specs. `null` means "Step 6 must infer L3 specs inline" (custom category without a config-declared `l3:`). Empty array means "L2-only category". |
| `l3_specs[].filename` | string | Matches `^[a-z][a-z0-9_-]*\.(yaml\|jsonl)$`. |
| `l3_specs[].schema_name` | string or `null` | Canonical schema name (e.g. `adr`, `glossary`, `gotcha`). `null` when the filename is outside `heuristics/ledgers.yaml`; Step 6 writes the schema body inline. |
| `l3_specs[].schema_template_path` | string or `null` | Absolute path to the L3 `.tmpl` if one ships in the templates tree. `null` when the schema is model-inferred. |

## Validation rules

Step 4b applies these in all modes. Any rule violation aborts the run with a clear message naming the offending category and rule number; the user fixes inputs and re-runs.

1. `path` matches `^[a-z._-][a-z0-9._/-]*$`. No `..` segments, no leading `/`, no trailing `/`.
2. No two categories share `path`.
3. No category's `path` is a strict prefix of another's (e.g. `docs/project` cannot coexist with `docs/project/architecture`).
4. `name` outside the canonical set requires `kind: custom`. Names violating `^[a-z][a-z0-9_-]*$` are rejected.
5. Each `l3_specs[].filename` matches `^[a-z][a-z0-9_-]*\.(yaml|jsonl)$`.

These are the rules `scripts/parse_config.py` enforces at config-parse time; Step 4b confirms but does not re-run those checks for config-driven mode. The interactive adapter (Step 4b Fresh/Merge branch) and the router-parse adapter (Step 4b Incremental branch) must apply all five.

## Producers

Three adapters land on this shape:

- **Config-driven (Step 1)**: `scripts/parse_config.py | scripts/resolve_layout.py` emits the JSON. Step 4b prints it back for visual confirmation.
- **Interactive Fresh/Merge (Step 4b)**: synthesized from confirmed categories (Step 3), context-dir name (Step 3a), and merge mapping (Step 4 when present). Built in memory by the scaffolder.
- **Incremental (Step 1, finalized at Step 4b)**: parsed from the `<!-- exodia:router:start -->` / `<!-- exodia:router:end -->` region of the existing `AGENTS.md`. Each router-table row becomes a category object; `l2_template_path` and `l3_specs` are resolved by walking the existing tree.
