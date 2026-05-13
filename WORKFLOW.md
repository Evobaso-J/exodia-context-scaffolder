# Exodia Scaffolder: Workflow Map

```
                      /exodia trigger
                            │
                            ▼
            ┌───────────────────────────────────────────────┐
            │ Step 0: resolve context                        │
            │   $SKILL_DIR, $TARGET, $CONFIG_PATH            │
            │ Utilities:                                     │
            │   - SKILL.md frontmatter                       │
            │   - README.md (config schema reference)        │
            └───────────────────┬───────────────────────────┘
                                ▼
            ┌───────────────────────────────────────────────┐
            │ Step 1: preflight                              │
            │   classify mode (Fresh/Merge/Incremental)      │
            │   classify shape (interactive/config-driven)   │
            │ Utilities:                                     │
            │   - scripts/parse_config.py  (validate config) │
            │   - scripts/resolve_layout.py → $LAYOUT_MAP    │
            │   - Bash probes (ls AGENTS.md/CLAUDE.md;       │
            │     grep `exodia:section:` markers;            │
            │     parse `exodia:router:start/end` region)    │
            │   - AskUserQuestion (Merge consent)            │
            └───────────────────┬───────────────────────────┘
                                ▼
            ┌───────────────────────────────────────────────┐
            │ Step 2: scan  (ALL MODES)                      │
            │ Utilities:                                     │
            │  - Explore subagent (medium; --deep upgrade)   │
            │  - $SCAN report                                │
            └───────┬──────────────────────────┬────────────┘
                    │                          │
            Fresh / Merge                 Incremental
                    │                          │
                    ▼                          ▼
        ┌────────────────────────────────┐  ┌──────────────────────────────┐
        │ Step 3: categories             │  │ protocol/incremental-rerun.md│
        │ Utilities:                     │  │ Utilities:                    │
        │  - heuristics/detectors.md     │  │  - `exodia:section:` markers  │
        │  - heuristics/format-strategy  │  │  - `exodia:router:start/end`  │
        │    .md (custom ledger picks)   │  │    region (category→path map) │
        │  - AskUserQuestion             │  │  - section-id baseline diff   │
        │ Branches:                      │  │  - AskUserQuestion (per diff) │
        │  - config-driven → JUMP to     │  │  - reuses Step 9 for L3       │
        │    Step 4 (skip Step 3a)       │  └─────────────┬────────────────┘
        │  - interactive → fall through  │                │
        └──────────┬─────────────────────┘                │
                   │                                      │
                   ▼  (interactive only)                  │
        ┌────────────────────────────────┐                │
        │ Step 3a: $CONTEXT_DIR          │                │
        │   Fresh/Merge interactive only │                │
        │   (skipped when $LAYOUT_MAP    │                │
        │    set: config-driven)         │                │
        │ Utilities:                     │                │
        │  - AskUserQuestion             │                │
        │  - scripts/init_structure.sh   │                │
        │    (property ref only;         │                │
        │     skip-existing guarantee)   │                │
        └──────────┬─────────────────────┘                │
                   ▼                                      │
        ┌────────────────────────────────┐                │
        │ Step 4: merge (Merge only)     │                │
        │ Utilities:                     │                │
        │  - scripts/parse_existing.py   │                │
        │  - heuristics/section-map.md   │                │
        │  - heuristics/prompt-format.md │                │
        │    (mapping table render)      │                │
        │  - AskUserQuestion             │                │
        └──────────┬─────────────────────┘                │
                   ▼                                      │
        ┌────────────────────────────────┐                │
        │ Step 5: init structure         │                │
        │ Utilities:                     │                │
        │  - scripts/init_structure.sh   │                │
        │    (legacy positional /        │                │
        │     --pairs form)              │                │
        │  - templates/<canonical>/*.tmpl│                │
        │    (architecture, design-      │                │
        │     patterns, glossary,        │                │
        │     operations, debugging,     │                │
        │     mobile, workspace, data,   │                │
        │     infra)                     │                │
        └──────────┬─────────────────────┘                │
                   ▼                                      │
        ┌────────────────────────────────┐                │
        │ Step 6: draft L2 sections      │                │
        │   (+ write L3 stubs for        │                │
        │    interactive custom cats)    │                │
        │ Utilities:                     │                │
        │  - templates/<cat>/<CAT>.md    │                │
        │    .tmpl (L2 skeleton + voice) │                │
        │  - templates/<cat>/*.tmpl      │                │
        │    (L3 schema templates via    │                │
        │     l3_specs.schema_template)  │                │
        │  - heuristics/format-strategy  │                │
        │    .md (schema/format/ID rule) │                │
        │  - $SCAN data                  │                │
        │  - Step 4 merge-seeded content │                │
        │    (Merge mode only)           │                │
        │  - $LAYOUT_MAP.l3_specs        │                │
        │  - Write (L3 stubs for         │                │
        │    interactive custom cats)    │                │
        └──────────┬─────────────────────┘                │
                   ▼                                      │
        ┌────────────────────────────────┐                │
        │ Step 7: section review         │                │
        │ Utilities:                     │                │
        │  - AskUserQuestion             │                │
        │  - heuristics/prompt-format.md │                │
        │  - Write (emit L2 to disk)     │                │
        └──────────┬─────────────────────┘                │
                   ▼                                      │
        ┌────────────────────────────────┐                │
        │ Step 8: emit AGENTS.md         │                │
        │ Utilities:                     │                │
        │  - templates/AGENTS.md.tmpl    │                │
        │  - rules/universal.md          │                │
        │  - rules/self-update.md        │                │
        │    (+ {{LEDGER_ROWS}},         │                │
        │     {{FORMAT_STRATEGY}} tokens)│                │
        │  - rules/conditional/          │                │
        │    operations-awareness.md     │                │
        │  - rules/conditional/          │                │
        │    lint-check.md               │                │
        │  - heuristics/ledgers.yaml     │                │
        │    (ledger row source)         │                │
        │  - heuristics/format-strategy  │                │
        │    .md (format-strategy        │                │
        │    kernel between markers)     │                │
        │  - Write (emit AGENTS.md)      │                │
        └──────────┬─────────────────────┘                │
                   ▼                                      ▼
        ┌────────────────────────────────────────────────┐
        │ Step 9: seed L3 (.jsonl + .yaml)               │
        │ Utilities:                                     │
        │  - heuristics/ledgers.yaml                     │
        │    (format / scan_source /                     │
        │     skeleton_source / skeleton_shape)          │
        │  - heuristics/prompt-format.md                 │
        │  - heuristics/format-strategy.md (ID format)   │
        │  - AskUserQuestion (per ledger candidates)     │
        │  - Bash / Explore (scan_source execution)      │
        └──────────────────┬─────────────────────────────┘
                           ▼
        ┌────────────────────────────────────────────────┐
        │ Step 10: wrap-up                               │
        │ Utilities:                                     │
        │  - summary text only                           │
        │  - sibling notice (config-driven only;         │
        │    per shared parent dir, list unmanaged       │
        │    sibling dirs left untouched)                │
        │  - throwaway-config reminder text              │
        │    (no automatic cleanup; user deletes         │
        │     `exodia.config.yaml`)                      │
        │  - lazy-migration note (Incremental, when      │
        │    router markers injected)                    │
        └────────────────────────────────────────────────┘
```

## Utility inventory

| Kind | Path | Used by |
|---|---|---|
| script | `scripts/parse_config.py` | Step 1 |
| script | `scripts/resolve_layout.py` | Step 1 |
| script | `scripts/parse_existing.py` | Step 4 |
| script | `scripts/init_structure.sh` | Step 3a (property ref), Step 5 |
| script | `scripts/yaml_subset.py` | imported by `parse_config.py` / `resolve_layout.py` |
| heuristic | `heuristics/detectors.md` | Step 3 |
| heuristic | `heuristics/section-map.md` | Step 4 |
| heuristic | `heuristics/format-strategy.md` | Step 3, Step 6, Step 8 (kernel substitution for `{{FORMAT_STRATEGY}}`), Step 9 |
| heuristic | `heuristics/ledgers.yaml` | Step 8, Step 9 |
| heuristic | `heuristics/prompt-format.md` | Step 4 mapping table, Step 7 draft review, Step 9 candidate list |
| template | `templates/AGENTS.md.tmpl` | Step 8 |
| template | `templates/<canonical>/*.tmpl` | Step 5, Step 6 |
| rule | `rules/universal.md` | Step 8 |
| rule | `rules/self-update.md` | Step 8 |
| rule | `rules/conditional/operations-awareness.md` | Step 8 (if `operations/` present) |
| rule | `rules/conditional/lint-check.md` | Step 8 (if lint/test detected) |
| docs | `README.md` | Step 0 (config schema reference) |

## Tool inventory (non-file)

| Tool | Used by |
|---|---|
| `AskUserQuestion` | Step 1 (Merge consent), Step 3, Step 3a, Step 4, Step 7, Step 9, incremental-rerun |
| `Explore` subagent | Step 2 (initial scan), Step 9 (scan_source execution) |
| `Bash` | Step 1 (config validate + layout resolve via `python3`, plus `ls` / `grep` probes), Step 5 (`init_structure.sh`), Step 9 (scan_source execution) |
| `Write` / `Edit` | Step 6 (L3 stubs for interactive custom categories), Step 7 (L2 files), Step 8 (AGENTS.md), Step 9 (L3 append) |

## Key splits

- **Mode** (Fresh / Merge / Incremental) decides which steps run. Step 2 runs in ALL modes.
- **Shape** (interactive vs config-driven, via `$CONFIG_PATH = exodia.config.yaml`) is orthogonal to mode, except Incremental always ignores config. Shape affects:
  - Step 3 (config-driven branch skips the custom-category interview and jumps to Step 4)
  - Step 3a (skipped entirely in config-driven runs; `context_dir` baked into resolved paths)
  - Step 5 (legacy positional vs `--pairs` form of `init_structure.sh`)
  - Step 8 and Step 9 (per-row path resolution from `$LAYOUT_MAP`; interactive runs synthesize an equivalent in-memory map)
- Steps 3 to 8 replaced by `incremental-rerun.md` when re-running. Step 2 and Step 9 still execute.
- L3 seeding (Step 9) and wrap-up (Step 10) run in every mode.
