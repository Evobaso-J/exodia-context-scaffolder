# Exodia Scaffolder: Workflow Map

```
                      /exodia trigger
                            │
                            ▼
            ┌───────────────────────────────────────────────┐
            │ Step 1: preflight                              │
            │   classify mode (Fresh/Merge/Incremental)      │
            │   classify shape (interactive/config-driven)   │
            │ Utilities:                                     │
            │   - scripts/parse_config.py  (validate config) │
            │   - scripts/resolve_layout.py                  │
            │     (config-driven: produces $LAYOUT_MAP)      │
            │   - Bash probes (ls AGENTS.md/CLAUDE.md;       │
            │     grep `exodia:section:` markers;            │
            │     parse `exodia:router:start/end` region;    │
            │     incremental: produces $LAYOUT_MAP)         │
            │   - heuristics/layout-map.md (shape contract)  │
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
                    ▼                          │
        ┌────────────────────────────────┐    │
        │ Step 3: categories             │    │
        │ Utilities:                     │    │
        │  - $REGISTRY (built Step 1)    │    │
        │  - $SCAN (built Step 2)        │    │
        │  - heuristics/format-strategy  │    │
        │    .md (custom ledger picks)   │    │
        │  - AskUserQuestion             │    │
        │ Branches:                      │    │
        │  - config-driven → JUMP to     │    │
        │    Step 4 (skip Step 3a)       │    │
        │  - interactive → fall through  │    │
        └──────────┬─────────────────────┘    │
                   │                          │
                   ▼  (interactive only)      │
        ┌────────────────────────────────┐    │
        │ Step 3a: $CONTEXT_DIR          │    │
        │   Fresh/Merge interactive only │    │
        │   (skipped when $LAYOUT_MAP    │    │
        │    set: config-driven)         │    │
        │ Utilities:                     │    │
        │  - AskUserQuestion             │    │
        │  - scripts/init_structure.sh   │    │
        │    (property ref only;         │    │
        │     skip-existing guarantee)   │    │
        └──────────┬─────────────────────┘    │
                   ▼                          │
        ┌────────────────────────────────┐    │
        │ Step 4: merge (Merge only)     │    │
        │ Utilities:                     │    │
        │  - Read (source file)          │    │
        │  - inline H2 split             │    │
        │  - heuristics/section-map.md   │    │
        │  - heuristics/prompt-format.md │    │
        │    (mapping table render)      │    │
        │  - AskUserQuestion             │    │
        └──────────┬─────────────────────┘    │
                   │                          │
                   └─────────────┬────────────┘
                                 ▼
            ┌───────────────────────────────────────────────┐
            │ Step 4b: materialize $LAYOUT_MAP (ALL MODES)   │
            │   Fresh/Merge: synthesize in memory from       │
            │     Step 3 + 3a + 4 inputs; validate           │
            │   Config-driven: confirm Step 1 output         │
            │   Incremental: confirm router-parsed map       │
            │   Print JSON back for user visual confirmation │
            │ Utilities:                                     │
            │  - heuristics/layout-map.md (schema + rules)   │
            └───────┬──────────────────────────┬────────────┘
                    │                          │
            Fresh / Merge                 Incremental
                    │                          │
                    ▼                          ▼
        ┌────────────────────────────────┐  ┌──────────────────────────────┐
        │ Step 5: init structure         │  │ protocol/incremental-rerun.md│
        │ Utilities:                     │  │   (replaces Steps 3 to 8)    │
        │  - scripts/init_structure.sh   │  │ Utilities:                   │
        │    (legacy positional /        │  │  - `exodia:section:` markers │
        │     --pairs form)              │  │  - section-id baseline diff  │
        │  - templates/<canonical>/*.tmpl│  │  - AskUserQuestion (per diff)│
        │    (architecture, design-      │  │  - reuses Step 9 for L3      │
        │     patterns, glossary,        │  └─────────────┬────────────────┘
        │     operations, debugging,     │                │
        │     mobile, workspace, data,   │                │
        │     infra)                     │                │
        └──────────┬─────────────────────┘                │
                   ▼                                      │
        ┌────────────────────────────────┐                │
        │ Step 6: draft + finalize L2    │                │
        │   (draft each section, then    │                │
        │    interactively review and    │                │
        │    write L2 + L3 stubs for     │                │
        │    interactive custom cats)    │                │
        │ Utilities:                     │                │
        │  - templates/<cat>/<CAT>.md    │                │
        │    .tmpl (L2 skeleton + voice) │                │
        │  - templates/<cat>/*.tmpl      │                │
        │    (L3 schema templates via    │                │
        │     l3_specs.schema_template)  │                │
        │  - heuristics/format-strategy  │                │
        │    .md (schema/format/ID rule) │                │
        │  - heuristics/prompt-format.md │                │
        │    (section review render)    │                │
        │  - $SCAN data                  │                │
        │  - Step 4 merge-seeded content │                │
        │    (Merge mode only)           │                │
        │  - $LAYOUT_MAP.l3_specs        │                │
        │  - AskUserQuestion             │                │
        │  - Write (L2 files + L3 stubs  │                │
        │    for interactive custom cats)│                │
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
        │  - heuristics/ledgers.yaml     │                │
        │    (ledger row source)         │                │
        │  - heuristics/format-strategy  │                │
        │    .md (format-strategy        │                │
        │    kernel between markers)     │                │
        │  - Write (emit AGENTS.md)      │                │
        └──────────┬─────────────────────┘                │
                   │                                      │
                   └─────────────┬────────────────────────┘
                                 ▼
            ┌───────────────────────────────────────────────┐
            │ Step 9: seed L3 (.jsonl + .yaml)               │
            │ Utilities:                                     │
            │  - heuristics/ledgers.yaml                     │
            │    (format / scan_source /                     │
            │     skeleton_source / skeleton_shape)          │
            │  - heuristics/prompt-format.md                 │
            │  - heuristics/format-strategy.md (ID format)   │
            │  - AskUserQuestion (per ledger candidates)     │
            │  - Bash / Explore (scan_source execution)      │
            └───────────────────┬───────────────────────────┘
                                ▼
            ┌───────────────────────────────────────────────┐
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
| script | `scripts/load_registry.py` | Step 1 (builds `$REGISTRY` from `templates/*/`) |
| script | `scripts/init_structure.sh` | Step 3a (property ref), Step 5 |
| script | `scripts/yaml_subset.py` | imported by `parse_config.py` / `resolve_layout.py` |
| heuristic | `heuristics/lint-detectors.md` | Step 2 (scan target list), Step 8 (lint/test/typecheck rule emission) |
| heuristic | `heuristics/section-map.md` | Step 4 |
| heuristic | `heuristics/format-strategy.md` | Step 3, Step 6, Step 8 (kernel substitution for `{{FORMAT_STRATEGY}}`), Step 9 |
| heuristic | `heuristics/ledgers.yaml` | Step 8, Step 9 |
| heuristic | `heuristics/layout-map.md` | Step 1 (shape contract), Step 4b (synthesize + validate), Step 5, Step 6, Step 8, Step 9, incremental-rerun |
| heuristic | `heuristics/prompt-format.md` | Step 4 mapping table, Step 6 draft review, Step 9 candidate list |
| template | `templates/AGENTS.md.tmpl` | Step 8 |
| template | `templates/<canonical>/*.tmpl` | Step 5, Step 6 |
| rule | `rules/universal.md` | Step 8 |
| rule | `rules/self-update.md` | Step 8 |
| docs | `README.md` | config schema reference (linked from Glossary in `SKILL.md`) |

## Tool inventory (non-file)

| Tool | Used by |
|---|---|
| `AskUserQuestion` | Step 1 (Merge consent), Step 3, Step 3a, Step 4, Step 6, Step 9, incremental-rerun |
| `Explore` subagent | Step 2 (initial scan), Step 9 (scan_source execution) |
| `Bash` | Step 1 (config validate + layout resolve via `python3`, plus `ls` / `grep` probes), Step 5 (`init_structure.sh`), Step 9 (scan_source execution) |
| `Write` / `Edit` | Step 6 (L2 files + L3 stubs for interactive custom categories), Step 8 (AGENTS.md), Step 9 (L3 append) |

## Key splits

- **Mode** (Fresh / Merge / Incremental) decides which steps run. Step 2 and Step 4b run in ALL modes.
- **Shape** (interactive vs config-driven, via `$CONFIG_PATH = exodia.config.yaml`) is orthogonal to mode, except Incremental always ignores config. Shape affects:
  - Step 3 (config-driven branch skips the custom-category interview and jumps to Step 4)
  - Step 3a (skipped entirely in config-driven runs; `context_dir` baked into resolved paths)
  - Step 4b (Fresh/Merge synthesizes `$LAYOUT_MAP` in memory; config-driven and Incremental confirm the map produced by Step 1)
  - Step 5 (legacy positional vs `--pairs` form of `init_structure.sh`)
- `$LAYOUT_MAP` is finalized once, at Step 4b, in every mode. Path resolution in Steps 5, 6, 8, 9, and incremental-rerun reads from it directly without mode branching. Shape contract: `heuristics/layout-map.md`.
- Steps 3, 4, 5, 6, 8 replaced by `incremental-rerun.md` when re-running. Step 2, Step 4b, and Step 9 still execute. The incremental flow forks from Fresh/Merge twice: at Step 2 (Incremental skips Steps 3 to 4 and goes straight to Step 4b) and at Step 4b (Incremental enters the rerun body while Fresh/Merge enters Steps 5 to 8). Both flows reconverge at Step 9.
- L3 seeding (Step 9) and wrap-up (Step 10) run in every mode.
