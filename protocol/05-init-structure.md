# Step 5: Initialize structure

Mode-split. Read only the branch matching the current mode.

## Interactive (no config)

```bash
bash "$SKILL_DIR/scripts/init_structure.sh" "$TARGET" "$CONTEXT_DIR" <space-separated-category-names>
```

## Config-driven (`$LAYOUT_MAP` set)

Pass each category's resolved path via the `--pairs` form, one `name=path` per category in `$LAYOUT_MAP`. `--pairs` is scaffolder-internal: it trusts paths already validated by `parse_config.py` (regex, no `..`, no leading or trailing `/`, no shared paths, no prefix nesting) and skips re-validation. Hand-invocation should use the legacy positional shape instead.

```bash
bash "$SKILL_DIR/scripts/init_structure.sh" "$TARGET" --pairs \
  architecture=docs/project/architecture \
  patterns=docs/project/patterns \
  debugging=docs/project/debugging \
  glossary=docs/domain/glossary
```

## Helper behavior (both shapes)

The helper creates the destination dirs with `mkdir -p`, copies `.tmpl` files from `$SKILL_DIR/templates/<canonical-name>/` when the category name matches a template dir, and writes a default L2 stub (`## Purpose`, `## Key Files`, `## L3 Data`) for custom categories with no template. Existing destination files are never overwritten. L3 files declared via `l3:` in the config but not auto-copied by `init_structure.sh` (because the host category has no template dir) are written by Step 6 from the schema template resolved in `$LAYOUT_MAP[*].l3_specs`.
