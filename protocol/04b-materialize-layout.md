# Step 4b: Materialize `$LAYOUT_MAP`

Applies in all modes. Finalizes `$LAYOUT_MAP` as the single in-memory artifact every later step consumes. Shape contract: `$SKILL_DIR/heuristics/layout-map.md`.

After this step, Steps 5 to 9 do not branch on mode for path resolution; they read `$LAYOUT_MAP` directly.

## Mode branches

### Config-driven

`$LAYOUT_MAP` was produced in Step 1 by `parse_config.py | resolve_layout.py`. Nothing to synthesize. Print the JSON back to the user for visual confirmation under a `### Layout map` heading inside a fenced ` ```json ` block. Continue.

### Incremental

`$LAYOUT_MAP` was reconstructed in Step 1 from the router region of the existing `AGENTS.md`. Each router-table row becomes a category object; `l2_template_path` is resolved against `$SKILL_DIR/templates/<name>/<NAME>.md.tmpl` (or `null` if the directory is absent); `l3_specs` is populated by listing existing `*.jsonl` and `*.yaml` files in the host path on disk, with `schema_name` resolved against `heuristics/ledgers.yaml` and `schema_template_path` set to the matching `.tmpl` under templates (or `null` if model-inferred originally). Print the JSON back to the user as above. Continue.

### Fresh and Merge (interactive)

Synthesize from the confirmed inputs:

- Categories list from Step 3 (the core five defaults plus any non-core categories the user accepted, whether model-proposed or user-added custom).
- `$CONTEXT_DIR` from Step 3a.
- Merge mapping from Step 4 if Merge mode (does not change the layout map shape; consumed in Step 6 as seed content, not here).
- Custom-category L3 derivations produced by Step 3's interview deferral to Step 6 schema inference: leave `l3_specs: null` for custom categories the user added interactively; Step 6 inference fills the field.

For each confirmed category, build one object matching `heuristics/layout-map.md`:

- `name`: as confirmed.
- `path`: `$CONTEXT_DIR/<name>`. Interactive Fresh/Merge does not collect an explicit path from the user; the default is always used.
- `kind`: `canonical` if `name` is in the canonical set, else `custom`.
- `l2_template_path`: `<SKILL_DIR>/templates/<name>/<NAME>.md.tmpl` if the file exists, else `null`.
- `l3_specs`: for canonicals with a template dir, list every `*.jsonl.tmpl` / `*.yaml.tmpl` under `<SKILL_DIR>/templates/<name>/` and resolve `schema_name` via `heuristics/ledgers.yaml`. For customs, `null` (deferred; Step 6 fills the slot).

Apply all five validation rules from `heuristics/layout-map.md`. On any failure, abort with a clear single-line message naming the offending category and rule number, e.g. `Step 4b: category 'releases' violates rule 3 (path 'docs' is a strict prefix of 'docs/releases')`. The user must fix inputs by re-running and adjusting answers.

On success, print the JSON to the user under a `### Layout map` heading inside a fenced ` ```json ` block. Continue to Step 5.

## Output

A JSON array conforming to `heuristics/layout-map.md`, held in memory as `$LAYOUT_MAP`. No file is written to disk; the artifact is ephemeral. Shape and category set are finalized here; interactively-added custom categories carry `l3_specs: null` and Step 6 fills those slots in place. After Step 6, the map is immutable. Steps 5, 6, 7, 8, 9, and 10 read it.
