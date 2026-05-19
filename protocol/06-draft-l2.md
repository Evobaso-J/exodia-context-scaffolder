# Step 6: Draft and finalize L2 content

Applies in Fresh and Merge modes. (Incremental re-runs use the diff flow in `protocol/incremental-rerun.md`.)

> **Schema inference (custom ledgers).** Whenever this step says "model writes the schema body inline," apply one unified rule. Inputs available: `{purpose, filename-if-given, scan-hints}` (any subset; missing pieces are derived from `$SCAN` and the category's purpose statement). `{purpose}` sources from `$LAYOUT_MAP[category].description` when non-null (config-driven runs); otherwise from the one-line purpose collected interactively in Step 3. Output is the tuple `{filename, schema, format, scan_hint}`; `format` and any per-format header come from `$SKILL_DIR/heuristics/format-strategy.md` (the `schema` slot is null for `.md`). Result lives in the in-memory `l3_specs` for the category and is referenced by Step 8 (AGENTS.md emit) and Step 9 (seeding). The three sub-cases below are entry points into this single rule, not separate procedures.

For each confirmed category, in order (architecture, design-patterns, glossary, operations, debugging, then any non-core categories the user confirmed):

1. **Choose the section skeleton.** If the category has an `l2_template_path` (canonical with template), read it and lock the voice (terse, factual, table- and bullet-heavy, inline file citations, no marketing prose). For custom categories with no template (`l2_template_path: null`), use the default skeleton already written by `init-structure.mjs` (`## Purpose`, `## Key Files`, `## L3 Data`) plus any extra `##` sections you deem useful from the scan. When `$LAYOUT_MAP[category].description` is non-null, seed the `## Purpose` section with it verbatim before expanding from `$SCAN`.
2. Using `$SCAN` (and any merge-seeded content from Step 4), fill each `##` section with a short, factual draft. Cite files. No speculation. Keep each section under ~150 words.
3. Preserve the `<!-- exodia:section:<id> -->` markers; they drive incremental re-runs.
4. **Never duplicate data that already lives in the repo.** Versions, ports, env names, paths, commands, config values, dependency lists, script names; all must be *referenced*, not copied. Write `see \`package.json\` \`engines.node\`` or `defined in \`.env.example\``, never the literal value. Duplicated data rots; pointers survive edits.
5. **`## L3 Data` section.** Drive this section from `l3_specs` in `$LAYOUT_MAP` (finalized in Step 4b per `$SKILL_DIR/heuristics/layout-map.md`). When the L2 template has a `<!-- exodia:section:l3 -->` block, list the L3 files that ship with the module. For custom categories where `l3_specs` is `null` (Step 4b deferred inference here), apply *Schema inference* above with `{purpose}` as input to derive the full tuple and write the inferred entries back into `$LAYOUT_MAP`. For categories whose `l3_specs` are populated (canonical defaults or config-declared overrides), list those entries; copy the schema template to the destination if `schema_template_path` is non-null and the destination does not yet exist; otherwise apply *Schema inference* with `{purpose, filename}` as input to fill `schema_name`. Each line in the L3 section reads `` - `<file>`: <one-line purpose>. `` Entries whose `filename` ends in `.md` are handled by the "Markdown L3 deep-dives" subsection below (no schema-template copy, no schema inference): still list them in the `## L3 Data` block.

## Design-patterns: progressive disclosure

The `design-patterns` L2 has no fixed section list. The template ships only an intro note, a single `<!-- exodia:section:body -->` region, and the L3 footer (see `$SKILL_DIR/templates/design-patterns/DESIGN-PATTERNS.md.tmpl`).

1. **Derive sections from `$SCAN`.** Propose one `##` heading per repo-specific concern the scan turned up: components, modals, composables, imports, API client, auth, tracking, testing, icons, accessibility, i18n, and so on. Skip concerns with no evidence. Order from highest-touch to lowest.
2. **Guardrail voice.** Each section body is 2-3 lines max: do / don't, plus one inline file citation. No prose, no rationale, no examples in the L2. Match the voice in `$SKILL_DIR/templates/design-patterns/DESIGN-PATTERNS.md.tmpl`.
3. **Spin-out rule.** When a topic carries enough material to exceed ~3 lines (auth flow, type system, testing harness, migration spec), write a `./docs/<slug>.md` deep dive alongside the L2 and replace the section body with a single line: `See [docs/<slug>.md](docs/<slug>.md) for full details.` `<slug>` is lower-kebab-case of the section heading. The `docs/` directory already exists from Step 5; deep dives live there.
4. **Deep-dive shape is free-form.** No template. Title, prose, tables, code blocks: whatever the topic demands. Cite files. Keep under ~400 lines; if longer, split by sub-topic.
5. **Interactive review still applies (next section), but the section unit is the H2 slug, not a `section-id` marker.** Treat each proposed `##` heading as the review unit. For deep dives, render the full proposed `docs/<slug>.md` content in the same accept/edit/skip loop.

## Markdown L3 deep-dives

For each `l3_specs[]` entry in `$LAYOUT_MAP` whose `filename` ends in `.md` (config-declared entries, plus any `.md` filenames the model proposed during schema inference for custom categories):

1. **Derive the heading.** From `$LAYOUT_MAP[category].description` (the category's purpose) combined with the filename's semantic role in the category, pick a `# H1` heading appropriate to the deep-dive's scope. Examples: under category `rules` with description "engineering guardrails", `code-style.md` → `# Code Style Guardrails`; under `glossary` with description "domain vocabulary", `terms.md` → `# Domain Term Definitions`. When `description` is `null`, fall back to a Title-Cased rendering of the filename slug (`code-style.md` → `# Code Style`). Nested `<filename>`: derive slug from `basename` only (`rules/style/imports.md` → `# Imports`).
2. **Draft the body.** Free-form prose, tables, bullet lists. Cite repo files. Keep under ~400 lines; split into multiple `.md` L3 files if longer. No template, no schema header.
3. **Wrap the body in a single `<!-- exodia:section:body -->` marker** so incremental re-runs can diff the auto-filled region. Matches the design-patterns deep-dive convention.
4. **Interactive review.** Render each `.md` L3 draft as its own review unit using anchor `` ### `<category>/<filename>` `` with the standard Accept / Edit / Skip loop (same shape as the section-level loop below). After acceptance, `Write` to `$TARGET/$CONTEXT_DIR/<category-path>/<filename>`. If nested, `mkdir -p "$(dirname "$TARGET/$CONTEXT_DIR/<category-path>/<filename>")"` before `Write`.

Schema inference (for custom categories where `l3_specs` is `null`) may propose `.md` filenames when the purpose is prose-friendly (glossary entries, rule docs, runbooks). The output tuple's `schema` slot stays `null`; `format` is `md`.

## Interactive review and write

Walk each L2 draft section-by-section with the user. For each `##` section:

- Render the draft inside a fenced markdown block, prefaced by an H3 anchor: `` ### `<category>/<CATEGORY>.md` § <section-id> `` (for `design-patterns`, where sections have no fixed `<section-id>`, use the H2 slug: `` ### `<category>/<CATEGORY>.md` § <h2-slug> ``).
- Then `AskUserQuestion`:
  - **Question**: "Accept this section?"
  - **Options**: "Accept", "Edit", "Skip" (leave empty for later).
- If edit: let the user dictate changes, re-draft (still inside the fenced block), loop until accepted.

For `design-patterns` deep dives, each `docs/<slug>.md` is its own review unit, presented with anchor `` ### `<category>/docs/<slug>.md` `` and the same accept/edit/skip loop.

After all sections in a category are accepted, `Write` the finalized L2 file to `$TARGET/$CONTEXT_DIR/<category>/<CATEGORY>.md`. For `design-patterns`, also `Write` each accepted deep dive to `$TARGET/$CONTEXT_DIR/design-patterns/docs/<slug>.md`.
