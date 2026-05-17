# Step 9: L3 seeding prompt

Applies in Fresh and Merge modes. Incremental re-runs reuse this step via `protocol/incremental-rerun.md`.

For each L3 file in the final category set, apply the matching seed clause below. The "target file" is resolved against `$LAYOUT_MAP` (finalized in Step 4b per `$SKILL_DIR/heuristics/layout-map.md`): `<host_path>/<filename>`. Skip any clause whose target file does not exist (the user may have dropped that category in Step 3). JSONL clauses scan candidates and let the user approve a subset via `AskUserQuestion`; YAML clauses propose a skeleton (named keys with empty body fields) for the user to accept, edit, or skip. When `<filename>` contains `/`, run `mkdir -p "$(dirname "<host_path>/<filename>")"` immediately before appending or writing so the intermediate directory exists.

**Driven by `$SKILL_DIR/heuristics/ledgers.yaml`.** That file is the single source for `format` (jsonl vs yaml), `scan_source` (jsonl), and `skeleton_source` / `skeleton_shape` (yaml) for every ledger the scaffolder ships. Do not duplicate this data in this step.

For each entry in `ledgers.yaml`: locate the host category in `$LAYOUT_MAP` and resolve the target file `<host_path>/<filename>`. Skip if the host category is absent from `$LAYOUT_MAP`, or the filename is absent from the host's `l3_specs`, or the target file does not exist on disk.

For **custom-category ledgers** (categories with `kind: custom` whose `l3_specs` is non-empty in `$LAYOUT_MAP`), extend this step with one extra clause per `(category, ledger)` pair. If the ledger's `schema_name` matches a row in `ledgers.yaml`, reuse that row's `scan_source` (jsonl) or `skeleton_source` / `skeleton_shape` (yaml) verbatim. Otherwise use the scan source the model proposed alongside the schema in Step 6 (carried through `$LAYOUT_MAP`). Append entries the same way as built-in clauses, using the ledger's own `_schema` prefix (canonical or model-invented).

Append JSONL entries using the canonical ID format `{type}_{YYYYMMDD}_{HHMMSS}_{4hex}`. The `{type}` prefix is the target file's `_schema` value, verbatim (read the first line of the `.jsonl`). See `$SKILL_DIR/heuristics/format-strategy.md` § ID format.

## Markdown clauses

For any `l3_specs[]` entry whose `filename` ends in `.md`, skip Step 9. These files are populated as prose deep-dives during Step 6 (see `protocol/06-draft-l2.md` § "Markdown L3 deep-dives"), analogous to the `design-patterns/docs/<slug>.md` flow. The JSONL and YAML clauses below iterate `ledgers.yaml` rows (which only contain jsonl/yaml entries), so `.md` files naturally fall out: this clause documents the intent.

## JSONL clauses

Iterate `ledgers.yaml` rows where `format: jsonl`. For each row: run the registry-declared `scan_source`, render the candidate list per `$SKILL_DIR/heuristics/prompt-format.md`, then `AskUserQuestion` to approve a subset. Append approved entries with canonical IDs.

## YAML clauses (skeleton-from-scan)

Iterate `ledgers.yaml` rows where `format: yaml`. For each row: render the proposed skeleton (per `skeleton_shape`, sourced from `skeleton_source`) inside a fenced ` ```yaml ` block prefaced by `### \`<file>\` § skeleton`, then `AskUserQuestion`:

- **Question**: "Accept this skeleton?"
- **Options**: "Accept", "Edit", "Skip" (leave the existing empty stub).

On accept or after edit, overwrite the YAML stub with the populated skeleton.

## Custom L3 clause

For each model-proposed custom ledger from Step 3 (or config-declared custom ledger), use the scan hint the model derived alongside the schema. If the hint is non-empty, run it as a Bash/Explore query, present candidates the same way as built-in JSONL clauses, and append approved entries (using the ledger's own `_schema` prefix). If the hint is `none`, skip seeding and leave the file empty. When candidate filtering is ambiguous and `$LAYOUT_MAP[category].description` is non-null, use that purpose statement to disambiguate which candidates fit.
