# Step 3: Propose categories

Mode-split. Read only the branch matching the current mode.

This step contributes the **category set** to `$LAYOUT_MAP`. Step 4b finalizes the map from these confirmed categories plus the context-dir name from Step 3a and the merge mapping from Step 4 (Merge mode only).

## Config-driven branch

If `$LAYOUT_MAP` is set (config present), skip the category-set proposal entirely. Use the resolved categories from `$LAYOUT_MAP` as the confirmed set. Each custom category carries an optional `description` field; treat it as the authoritative purpose statement for that category in Steps 6 and 9 (no need to re-elicit purpose from the user).

Still surface "did you forget X?" proposals: in one model turn, read `$SCAN` and propose any categories that are **not already in `$LAYOUT_MAP`** and not declared with `drop: true`. Each proposal carries `(name, rationale_citing_scan_evidence)` plus the derived `(filename, schema, format, scan_hint)` tuples for any L3 ledgers, all produced in the same response per `$SKILL_DIR/heuristics/format-strategy.md`. Present one focused `AskUserQuestion` per proposal to add it under `<context_dir>/<name>/` (using `context_dir` from the config). Accepted additions are merged into `$LAYOUT_MAP` (their `description` slot stays `null`; the rationale travels in conversation). Then jump to Step 4.

## Interactive branch

When no config is present, the **default** starter set is the five canonical categories:

- `architecture/`
- `design-patterns/`
- `glossary/`
- `operations/`
- `debugging/`

Then, based on `$SCAN`, make one model call that proposes any additional categories beyond the core five that earn their keep on this repo. In the same turn, for each proposal derive the `(filename, schema, format, scan_hint)` tuples for any L3 ledgers per `$SKILL_DIR/heuristics/format-strategy.md`. Each proposal is `(name, rationale_citing_scan_evidence)` plus those ledger tuples.

First render the proposed set as a markdown bulleted list (one category per line, with the one-line purpose and rationale) so the user can scan it. Then use `AskUserQuestion`:

- **Question**: "Use this category set?"
- **Options**:
  - "Accept set"
  - "Drop categories": list which to drop in the follow-up.
  - "Add custom": provide name + one-line purpose in the follow-up.

Iterate until the user confirms.

The derivation rules below apply to **every non-core category** (model-proposed additions and user-added custom categories alike). Do not ask the user to enumerate L3 ledgers or scan hints. Derive both yourself from the purpose statement and `$SCAN`:

- Decide whether the category warrants any L3 files at all (many non-core categories are L2-only).
- For each ledger you propose, pick a filename, a `_schema` prefix, and a format (`.jsonl` for append-only / id-keyed records, `.yaml` for named taxonomies) per `$SKILL_DIR/heuristics/format-strategy.md`. When constructing the JSONL schema header `_fields` array, follow the "Baseline `_fields` for derived JSONL ledgers" rule in `$SKILL_DIR/heuristics/format-strategy.md`.
- For each ledger, derive a one-line **scan hint** that Step 9 will run to seed it (e.g. "scan TODO comments under `src/jobs/`", "parse `docs/playbooks/`", "git log matching `^perf:`"). If no useful seed source exists, set the hint to `none` and Step 9 will leave the file empty.

Carry the proposed `(filename, schema, format, scan_hint)` tuples into Step 6 alongside the L2 draft. `init-structure.mjs` will scaffold an empty L2 stub for any category without a template dir; the L3 stubs you propose are drafted in Step 6 and seeded in Step 9.

The target repo picks the shape. Users may drop any canonical category that does not apply: a pure library may have no `operations/`, a data pipeline may have no `design-patterns/`, a CLI tool may have no `glossary/`. `init-structure.mjs` accepts any subset of category names matching `^[a-z][a-z0-9_-]*$`; the core set is a default, not an enforced minimum.
