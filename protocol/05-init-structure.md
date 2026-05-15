# Step 5: Initialize structure

Reads `$LAYOUT_MAP` (finalized in Step 4b per `$SKILL_DIR/heuristics/layout-map.md`) and creates the directory tree. Two invocation shapes for the helper; pick by mode.

## Interactive (Fresh/Merge synthesized in Step 4b)

```bash
bash "$SKILL_DIR/scripts/init_structure.sh" "$TARGET" "$CONTEXT_DIR" <space-separated-category-names>
```

Category names come from `$LAYOUT_MAP[*].name`.

## Config-driven (Step 1 produced `$LAYOUT_MAP`)

Pass each category's resolved path via the `--pairs` form, one `name=path` per category in `$LAYOUT_MAP`. `--pairs` is scaffolder-internal: it trusts paths already validated by `parse_config.py` (regex, no `..`, no leading or trailing `/`, no shared paths, no prefix nesting) and skips re-validation. Hand-invocation should use the legacy positional shape instead.

```bash
bash "$SKILL_DIR/scripts/init_structure.sh" "$TARGET" --pairs \
  architecture=docs/project/architecture \
  design-patterns=docs/project/design-patterns \
  operations=docs/project/operations \
  debugging=docs/project/debugging \
  glossary=docs/handbook/glossary
```

## Helper behavior (both shapes)

The helper creates the destination dirs with `mkdir -p`, copies `.tmpl` files from `$SKILL_DIR/templates/<canonical-name>/` when the category name matches a template dir, and writes a default L2 stub (`## Purpose`, `## Key Files`, `## L3 Data`) for custom categories with no template. Template subdirectories are mirrored at the destination (e.g. `templates/design-patterns/docs/` becomes `<category-path>/docs/`); non-`.tmpl` files inside them (such as `.gitkeep`) are copied verbatim so the empty subdir is committable. Existing destination files are never overwritten. L3 files declared in `$LAYOUT_MAP[*].l3_specs` but not auto-copied by `init_structure.sh` (because the host category has no template dir) are written by Step 6 from the schema template resolved in `$LAYOUT_MAP[*].l3_specs[].schema_template_path`.
