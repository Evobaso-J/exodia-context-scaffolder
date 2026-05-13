# Step 8: Emit the AGENTS.md router

Applies in Fresh and Merge modes. (Incremental re-runs only patch `AGENTS.md`; see `protocol/incremental-rerun.md`.)

Compose `$TARGET/AGENTS.md` from:

- `$SKILL_DIR/rules/universal.md` (always included)
- `$SKILL_DIR/rules/self-update.md` (always, near the top).

Then append the following conditional bullets to the Behavioral Rules section verbatim (no extra files to load):

- **If `operations/` is in the final category set**, append this bullet:
  `- **Operations awareness.** Check {{CONTEXT_DIR}}/operations/OPERATIONS.md before touching user-visible text, env variables, routing, deploy config, or anything that differs by environment/tenant/variant. When in doubt, open the file.`
- **If the scan detected any lint/test/typecheck scripts**, append this bullet:
  `- **Do not run lint, test, or typecheck unless explicitly asked.** CI and pre-commit hooks own these gates. Detected commands in this repo: {{LINT_COMMANDS}}. Running them ad-hoc wastes wall time and muddies terminal output.`

Resolve `{{CONTEXT_DIR}}` and `{{LINT_COMMANDS}}` at emit time per the Placeholders section below.

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
3. Context Router table (one row per confirmed category, linking to the resolved `<path>/<CATEGORY>.md`). Wrap the table in `<!-- exodia:router:start -->` / `<!-- exodia:router:end -->` markers (the template already does this); incremental re-runs parse this region for the category → path map, so do not move the markers or add prose between them and the table.
4. Behavioral Rules (universal + conditional)
5. Self-Update Rules (full block, after placeholder substitution + custom-row append)
6. Quick Action Table (common dev phrases → file to read)
7. Context Structure (tree diagram). Group resolved paths by their longest common prefix and render one tree per group, so multi-root layouts (e.g. `docs/project/...` and `docs/handbook/...`) read cleanly.

## Placeholders

Rule snippets carry a small, fixed set of substitution tokens; resolve all of them at emit time:

- `{{CONTEXT_DIR}}`: replace with `$CONTEXT_DIR` for interactive runs, or with `context_dir` from the config for config-driven runs. It is only the default prefix; per-category paths are resolved separately via `$LAYOUT_MAP`, not via a placeholder.
- `{{LEDGER_ROWS}}`: replace with the rows rendered above from `heuristics/ledgers.yaml`. Each row's host path is resolved per-row from `$LAYOUT_MAP`; there is no separate path token.
- `{{LINT_COMMANDS}}`: replace with the detected lint/test/typecheck commands from the scan.
- `{{FORMAT_STRATEGY}}`: replace with the content between `<!-- exodia:format-strategy:start -->` and `<!-- exodia:format-strategy:end -->` in `$SKILL_DIR/heuristics/format-strategy.md`. That file is the single source for the runtime "File Format Strategy" guidance; do not inline a duplicate copy in this step or in `rules/self-update.md`.
