# Step 1: Preflight

Treat the SKILL.md Glossary as authoritative for `$TARGET`, `$SKILL_DIR`, `$CONTEXT_DIR`, and `$CONFIG_PATH`.

Mode classification. Applies in all modes.

If the user aborts mid-interview, leave the repo in whatever partial state exists. Running `/exodia` again resumes from preflight.

## Build `$REGISTRY`

Before mode classification, build `$REGISTRY` as the curated-category index. It is a JSON object mapping `name -> one-line purpose`, derived by listing `$SKILL_DIR/templates/*/` and reading each L2 template's leading `<!-- purpose: ... -->` comment:

```bash
REGISTRY="$(python3 "$SKILL_DIR/scripts/load_registry.py" --skill-dir "$SKILL_DIR")"
```

Step 3 reads `$REGISTRY` alongside `$SCAN` to judge fit between any proposed category name and the curated set. Adding a new curated category (e.g. a fifth canonical default) means creating a new `templates/<name>/<NAME>.md.tmpl` with a leading `<!-- purpose: ... -->` line plus the relevant ledger entries; no Python, scan, or detector edits required.

## Config validation (when `$CONFIG_PATH` is present)

If `$CONFIG_PATH` is present, parse and validate it **before** mode classification:

```bash
python3 "$SKILL_DIR/scripts/parse_config.py" "$CONFIG_PATH"
```

On non-zero exit, abort the run and surface the line-numbered errors from stderr verbatim. Do not attempt to proceed without the config; the user must fix it. On success, pipe the JSON output through `resolve_layout.py` and store the result as `$LAYOUT_MAP`:

```bash
python3 "$SKILL_DIR/scripts/parse_config.py" "$CONFIG_PATH" \
  | python3 "$SKILL_DIR/scripts/resolve_layout.py" --skill-dir "$SKILL_DIR"
```

The output conforms to `$SKILL_DIR/heuristics/layout-map.md`. Step 4b will print it back for visual confirmation before any disk writes; downstream steps read it as the only path-resolution source.

## Detect what already exists

```bash
ls -la "$TARGET/AGENTS.md" "$TARGET/CLAUDE.md" 2>/dev/null
```

Probe for an existing exodia context tree. The directory name is no longer hardcoded; any top-level dir whose markdown files contain `<!-- exodia:section:` markers is an exodia context tree. Cheap probe first, fallback scan second:

```bash
# Cheap: try common names.
EXISTING_CONTEXT_DIR=""
for candidate in context docs knowledge .agents ai; do
  if [[ -d "$TARGET/$candidate" ]] && grep -lr 'exodia:section:' "$TARGET/$candidate" --include='*.md' 2>/dev/null | head -1 >/dev/null; then
    EXISTING_CONTEXT_DIR="$candidate"
    break
  fi
done
# Fallback: any top-level dir at all.
if [[ -z "$EXISTING_CONTEXT_DIR" ]]; then
  for d in "$TARGET"/*/; do
    if grep -lr 'exodia:section:' "$d" --include='*.md' 2>/dev/null | head -1 >/dev/null; then
      EXISTING_CONTEXT_DIR="$(basename "$d")"
      break
    fi
  done
fi
```

## Classify mode

Classify into one of three modes:

- **Fresh**: no `AGENTS.md`, no `CLAUDE.md`, no `$EXISTING_CONTEXT_DIR`. Go to Step 2.
- **Merge**: `AGENTS.md` or `CLAUDE.md` (or both) exists, but no existing context tree. Before doing anything else, **ask the user for explicit permission** to consume the existing file(s). Use `AskUserQuestion`:
  - **Question**: "Split existing `AGENTS.md` / `CLAUDE.md` into per-module sections?"
  - **Options**:
    - "Yes, split now": parse the existing file, route each section into the right module, replace the root file with a thin router. Original content is preserved across modules, not destroyed. A monolithic root file is reloaded on every task; splitting is the long-term fix.
    - "No, stop": exit without changes. You can revisit later by re-running `/exodia`.

  If the user declines, stop the skill here and do not scaffold anything. If they accept, continue to Step 2 normally; Step 4 handles the split. If both files exist, `AGENTS.md` is the parse source.
- **Incremental**: `$EXISTING_CONTEXT_DIR` is non-empty. Set `$CONTEXT_DIR=$EXISTING_CONTEXT_DIR` and jump to `protocol/incremental-rerun.md`; do not ask the dir-name question again. If `$CONFIG_PATH` is also present, ignore it and print one warning line: `Config detected but tree exists; ignoring. Delete \`exodia.config.yaml\` to silence this warning.`

When entering the incremental re-run flow, parse the **router region** of `$TARGET/AGENTS.md` for the canonical category → path map. The region is wrapped in `<!-- exodia:router:start -->` / `<!-- exodia:router:end -->` markers around the `## Context Router` table. Materialize the result as `$LAYOUT_MAP` matching `$SKILL_DIR/heuristics/layout-map.md`: each router row becomes a category object, `l2_template_path` is resolved against `$SKILL_DIR/templates/<name>/<NAME>.md.tmpl` (or `null`), and `l3_specs` is populated by listing existing `*.jsonl` and `*.yaml` files on disk under the host path with `schema_name` resolved via `heuristics/ledgers.yaml`. Step 4b will print it back for confirmation.

If the markers are absent (the scaffold pre-dates this feature), fall back to a plain `<!-- exodia:section:` grep across `$TARGET/$EXISTING_CONTEXT_DIR/`, then lazily inject the markers around the router table on the next emit and note the migration in the wrap-up summary.
