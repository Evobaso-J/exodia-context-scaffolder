# Step 8: Emit the AGENTS.md router

Applies in Fresh and Merge modes. (Incremental re-runs only patch `AGENTS.md`; see `protocol/incremental-rerun.md`.)

Compose `$TARGET/AGENTS.md` from:

- `$SKILL_DIR/rules/universal.md` (always included)
- `$SKILL_DIR/rules/conditional/operations-awareness.md` *only if `operations/` is in the final category set*
- `$SKILL_DIR/rules/conditional/lint-check.md` if scan detected any lint/test/typecheck scripts; substitute the detected commands into the snippet
- `$SKILL_DIR/rules/self-update.md` (always, near the top).

## Ledger row generation

`self-update.md` ships with a `<!-- exodia:self-update:rows:start -->` / `<!-- exodia:self-update:rows:end -->` marker pair around a `{{LEDGER_ROWS}}` token. Render rows from the canonical ledger registry at `$SKILL_DIR/heuristics/ledgers.yaml`; that file is the single source of truth for filename, host, schema, signal, action, and scan source. Do not duplicate ledger data here.

For each ledger entry in `ledgers.yaml`:

1. Resolve the host's path from `$LAYOUT_MAP` (interactive runs construct the equivalent map by joining `$CONTEXT_DIR` with each canonical category name).
2. **Drop the ledger** if the host category is dropped or absent from the final set, or the ledger's `filename` is not in the host category's `l3_specs`.
3. Otherwise emit one Markdown table row **per `signals` entry** (some ledgers, e.g. `reviews`, declare multiple signals): `\| <signal> \| \`<host_path>/<filename>\` \| <action> \|`.

Then append generated rows for **custom-category ledgers** (categories with `kind: custom` in `$LAYOUT_MAP` whose `l3_specs` is non-empty, plus any interactively proposed custom ledgers from Step 3). For each `(category, ledger)` pair: if the ledger's `schema_name` matches a row in `ledgers.yaml`, reuse that row's signals/actions with the custom category's resolved path. Otherwise write a one-line "When to update" hint from the category's purpose statement.

Substitute `{{LEDGER_ROWS}}` with the rendered rows joined by newlines.

The `File Format Strategy` § at the bottom of `self-update.md` is always retained; it guides future agents adding new ledgers.

## Final shape

Follow the shape in `$SKILL_DIR/templates/AGENTS.md.tmpl`:

1. Project overview (one paragraph from scan)
2. Commands (point to the detected package manifest file)
3. Context Router table (one row per confirmed category, linking to the resolved `<path>/<CATEGORY>.md`). Wrap the table in `<!-- exodia:router:start -->` / `<!-- exodia:router:end -->` markers (the template already does this); incremental re-runs parse this region for the category → path map, so do not move the markers or add prose between them and the table. The full format contract (header row, column count, link-cell shape, single-occurrence rule) lives in `$SKILL_DIR/TROUBLESHOOTING.md` § "Router region invariants"; emit must conform to it.
4. Behavioral Rules (universal + conditional)
5. Self-Update Rules (full block, after placeholder substitution + custom-row append)
6. Quick Action Table (common dev phrases → file to read)
7. Context Structure (tree diagram). Group resolved paths by their longest common prefix and render one tree per group, so multi-root layouts (e.g. `docs/project/...` and `docs/domain/...`) read cleanly.

## Placeholders

Rule snippets (`universal.md`, `conditional/operations-awareness.md`, `self-update.md`, and the `{{CONTEXT_TREE}}` diagram) contain `{{CONTEXT_DIR}}` placeholders. Substitute every `{{CONTEXT_DIR}}` with `$CONTEXT_DIR` for interactive runs. For config-driven runs, `{{CONTEXT_DIR}}` is replaced by `context_dir` from the config (the default prefix), and `{{path:<key>}}` placeholders carry the per-category specifics.
