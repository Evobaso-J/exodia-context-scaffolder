# Step 6: Draft L2 content

Applies in Fresh and Merge modes. (Incremental re-runs use the diff flow in `protocol/incremental-rerun.md`.)

For each confirmed category, in order (architecture, patterns, domain, operations, debugging, then optional extras and custom categories):

1. **Choose the section skeleton.** If the category has an `l2_template_path` (canonical with template), read it and lock the voice (terse, factual, table- and bullet-heavy, inline file citations, no marketing prose). For custom categories with no template (`l2_template_path: null`), use the default skeleton already written by `init_structure.sh` (`## Purpose`, `## Key Files`, `## L3 Data`) plus any extra `##` sections you deem useful from the scan.
2. Using `$SCAN` (and any merge-seeded content from Step 4), fill each `##` section with a short, factual draft. Cite files. No speculation. Keep each section under ~150 words.
3. Preserve the `<!-- exodia:section:<id> -->` markers; they drive incremental re-runs.
4. **Never duplicate data that already lives in the repo.** Versions, ports, env names, paths, commands, config values, dependency lists, script names; all must be *referenced*, not copied. Write `see \`package.json\` \`engines.node\`` or `defined in \`.env.example\``, never the literal value. Duplicated data rots; pointers survive edits.
5. **`## L3 Data` section.** Drive this section from `l3_specs` in `$LAYOUT_MAP` when config-driven. When the L2 template has a `<!-- exodia:section:l3 -->` block, list the L3 files that ship with the module. For custom categories whose `l3_specs` are populated by the config, list those files (each entry a `{filename, schema_name, schema_template_path}`); copy the schema template to the destination if `schema_template_path` is non-null and the destination does not yet exist; otherwise propose the schema body inline. For custom categories declared interactively in Step 3, use the `(filename, schema, format, scan_hint)` tuples you derived there: write each L3 stub to disk with a one-line header comment naming its `_schema`, and propose the schema body inline. Each line in the L3 section reads `` - `<file>`: <one-line purpose>. ``

Do **not** write the file to disk yet. Hold the draft in memory.
