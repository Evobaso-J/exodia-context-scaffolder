# Step 3: Propose categories

Mode-split. Read only the branch matching the current mode.

This step contributes the **category set** to `$LAYOUT_MAP`. Step 4b finalizes the map from these confirmed categories plus the context-dir name from Step 3a and the merge mapping from Step 4 (Merge mode only).

## Config-driven branch

If `$LAYOUT_MAP` is set (config present), skip the category-set proposal entirely. Use the resolved categories from `$LAYOUT_MAP` as the confirmed set. Still run the detector heuristics in `$SKILL_DIR/heuristics/detectors.md`: for each detected optional canonical (`mobile`, `workspace`, `data`, `infra`) **not already in `$LAYOUT_MAP`** and not declared with `drop: true`, present one focused `AskUserQuestion` per detected category to add it under `<context_dir>/<name>/` (using `context_dir` from the config). Accepted additions are merged into `$LAYOUT_MAP`. Then jump to Step 4. The custom-category interview below does not run; custom categories come exclusively from the config.

## Interactive branch

When no config is present, the **default** starter set is the five canonical categories:

- `architecture/`
- `design-patterns/`
- `glossary/`
- `operations/`
- `debugging/`

Then, based on `$SCAN` and `$SKILL_DIR/heuristics/detectors.md`, compute optional adds:

| Trigger in scan | Add |
|---|---|
| Mobile stack detected | `mobile/` |
| Monorepo manager detected | `workspace/` |
| ML/data stack detected | `data/` |
| Infra-as-code detected | `infra/` |

First render the proposed set as a markdown bulleted list (one category per line, with the one-line purpose) so the user can scan it. Then use `AskUserQuestion`:

- **Question**: "Use this category set?"
- **Options**:
  - "Accept set"
  - "Drop categories": list which to drop in the follow-up.
  - "Add custom": provide name + one-line purpose in the follow-up.

Iterate until the user confirms.

When the user adds a **custom category**, ask one follow-up: a one-line purpose statement. Do not ask the user to enumerate L3 ledgers or scan hints. Instead, derive both yourself from the purpose statement and `$SCAN`:

- Decide whether the category warrants any L3 files at all (many custom categories are L2-only).
- For each ledger you propose, pick a filename, a `_schema` prefix, and a format (`.jsonl` for append-only / id-keyed records, `.yaml` for named taxonomies) per `$SKILL_DIR/heuristics/format-strategy.md`.
- For each ledger, derive a one-line **scan hint** that Step 9 will run to seed it (e.g. "scan TODO comments under `src/jobs/`", "parse `docs/playbooks/`", "git log matching `^perf:`"). If no useful seed source exists, set the hint to `none` and Step 9 will leave the file empty.

Carry the proposed `(filename, schema, format, scan_hint)` tuples into Step 6 alongside the L2 draft. `init_structure.sh` will scaffold an empty L2 stub for any category without a template dir; the L3 stubs you propose are drafted in Step 6 and seeded in Step 9.

The target repo picks the shape. Users may drop any canonical category that does not apply: a pure library may have no `operations/`, a data pipeline may have no `design-patterns/`, a CLI tool may have no `glossary/`. `init_structure.sh` accepts any subset of category names matching `^[a-z][a-z0-9_-]*$`; the core set is a default, not an enforced minimum.
