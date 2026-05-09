# Troubleshooting

Runtime failure modes for the `/exodia` scaffolder. Read this only when one of the listed conditions is hit during a run.

- **User aborts mid-interview**: leave the repo in whatever partial state exists. No need to roll back. Running `/exodia` again resumes from preflight.
- **Explore scan times out / returns garbage**: fall back to asking the user to confirm the stack and architecture directly, then continue.
- **Target repo has committed secrets or `.env` with real values**: never echo these in drafts. If you must reference env vars, name them only.
- **No agent integration, no lint scripts**: skill still works; just emits the minimal universal rules.
- **`exodia.config.yaml` validation error**: `parse_config.py` exits 65 with line-numbered errors on stderr. Fix the offending line and re-run; the scaffolder will not proceed with an invalid config. Common causes: path uppercase or contains `..`, two categories share a path, a non-canonical category name without `custom: true`, `drop: true` combined with another field.
- **Config ignored on incremental re-run**: by design. Once the first scaffold has emitted AGENTS.md with the router region wrapped in `<!-- exodia:router:start/end -->`, that table is the sole truth. Re-runs print a warning and skip the file. Delete `exodia.config.yaml` to silence the warning.
- **Old scaffold without router brackets**: incremental re-runs fall back to a `<!-- exodia:section:` grep across the existing context dir, then lazily inject the bracket markers around the router table on the next emit. The wrap-up summary mentions the migration; user-edited prose outside the router region is preserved.

## Router region invariants

Step 1 (preflight) and the incremental re-run flow read the router region of `$TARGET/AGENTS.md` to recover the category to path map. There is no parser script: the agent reads the region directly. The cost of that choice is that the format below is a load-bearing contract. Do not evolve it without updating every reader.

The contract:

1. **Markers.** The region is delimited by exactly `<!-- exodia:router:start -->` and `<!-- exodia:router:end -->`, each on its own line, in that order, with a single matching pair per file. Step 8 emits them; Step 1 falls back to a `<!-- exodia:section:` grep when they are absent and re-injects them on the next emit.
2. **Body.** Between the markers: a single intro paragraph (the "Route by task type" line, kept as prose) followed by exactly one GitHub-flavored Markdown table. No additional tables, lists, headings, or block quotes inside the region.
3. **Table shape.** Two columns. Header row: `| Task type | Load |`. Separator row: `| --------- | ---- |`. One data row per confirmed category. Extra columns, footnotes, or merged cells break the parse.
4. **Data row shape.** First cell: the task-type label (free prose). Second cell: a Markdown link of the form `[<category-name>](<resolved-path>/<CATEGORY>.md)`. The `<resolved-path>` is what `$LAYOUT_MAP` produced at scaffold time and is the value the agent recovers on re-run. A category MUST appear at most once; duplicate links are ambiguous and the reader cannot break the tie.
5. **Source of truth alignment.** During a fresh or merge run, paths come from `$LAYOUT_MAP` (built by `scripts/parse_config.py | scripts/resolve_layout.py` in config-driven mode, or synthesized from the user-confirmed categories in interactive mode). On incremental re-run, the router region is the source of truth and `$LAYOUT_MAP` is reconstructed from it. The `kind`, `l2_template_path`, and `l3_specs` fields are NOT recoverable from the router region; they are recomputed by re-walking `$SKILL_DIR/templates/` and `$SKILL_DIR/heuristics/ledgers.yaml` against the names recovered from the table. That asymmetry is intentional: the router is a runtime artifact for agents, not a serialized config.

If a future change needs to carry more than `(name, path)` across re-runs (for example per-category kind or L3 specs), do not widen the router table. Add a sibling region with its own marker pair, or persist a machine-readable sidecar inside `$CONTEXT_DIR/`. Keep the router agent-readable.
