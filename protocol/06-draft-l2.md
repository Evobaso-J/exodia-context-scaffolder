# Step 6: Draft L2 content

Applies in Fresh and Merge modes. (Incremental re-runs use the diff flow in `protocol/incremental-rerun.md`.)

> **Schema inference (custom ledgers).** Whenever this step says "model writes the schema body inline," apply one unified rule. Inputs available: `{purpose, filename-if-given, scan-hints}` (any subset; missing pieces are derived from `$SCAN` and the category's purpose statement). Output is the tuple `{filename, schema, format, scan_hint}`; `format` and any per-format header come from `$SKILL_DIR/heuristics/format-strategy.md` (the `schema` slot is null for `.md`). Result lives in the in-memory `l3_specs` for the category and is referenced by Step 8 (AGENTS.md emit) and Step 9 (seeding). The three sub-cases below are entry points into this single rule, not separate procedures.

For each confirmed category, in order (architecture, design-patterns, glossary, operations, debugging, then optional extras and custom categories):

1. **Choose the section skeleton.** If the category has an `l2_template_path` (canonical with template), read it and lock the voice (terse, factual, table- and bullet-heavy, inline file citations, no marketing prose). For custom categories with no template (`l2_template_path: null`), use the default skeleton already written by `init_structure.sh` (`## Purpose`, `## Key Files`, `## L3 Data`) plus any extra `##` sections you deem useful from the scan.
2. Using `$SCAN` (and any merge-seeded content from Step 4), fill each `##` section with a short, factual draft. Cite files. No speculation. Keep each section under ~150 words.
3. Preserve the `<!-- exodia:section:<id> -->` markers; they drive incremental re-runs.
4. **Never duplicate data that already lives in the repo.** Versions, ports, env names, paths, commands, config values, dependency lists, script names; all must be *referenced*, not copied. Write `see \`package.json\` \`engines.node\`` or `defined in \`.env.example\``, never the literal value. Duplicated data rots; pointers survive edits.
5. **`## L3 Data` section.** Drive this section from `l3_specs` in `$LAYOUT_MAP` (finalized in Step 4b per `$SKILL_DIR/heuristics/layout-map.md`). When the L2 template has a `<!-- exodia:section:l3 -->` block, list the L3 files that ship with the module. For custom categories where `l3_specs` is `null` (Step 4b deferred inference here), apply *Schema inference* above with `{purpose}` as input to derive the full tuple and write the inferred entries back into `$LAYOUT_MAP`. For categories whose `l3_specs` are populated (canonical defaults or config-declared overrides), list those entries; copy the schema template to the destination if `schema_template_path` is non-null and the destination does not yet exist; otherwise apply *Schema inference* with `{purpose, filename}` as input to fill `schema_name`. Each line in the L3 section reads `` - `<file>`: <one-line purpose>. ``

Do **not** write the file to disk yet. Hold the draft in memory.
