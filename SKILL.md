---
name: exodia
description: >
  Scaffold a durable, agent-agnostic context tree for any repo: AGENTS.md router + a
  `context/` directory split into 5 narrative modules (architecture, design-patterns, glossary,
  operations, debugging) with append-only L3 data files (.jsonl + .yaml). Interactive:
  scans the repo, proposes categories, drafts each module section-by-section, and
  embeds self-update rules. One-shot. Re-runs incrementally diff existing content.
  Trigger: /exodia. Also triggers on "scaffold agent context", "initialize AGENTS.md",
  "bootstrap context tree".
---

# /exodia: scaffold agent context for a repo

You are running the `exodia` scaffolder. Your job is to generate an `AGENTS.md` router plus a `context/` directory tree in the current working directory. You do this interactively, in a fixed protocol whose per-step runbooks live under `$SKILL_DIR/protocol/`.

## Scaffolder vs. runtime: do not confuse the two

`/exodia` is a **scaffolder**, not a runtime context system. Two distinct roles:

- **Scaffolder instructions** (this file + `$SKILL_DIR/protocol/` + `$SKILL_DIR/heuristics/` + `$SKILL_DIR/templates/` + `$SKILL_DIR/rules/` + `$SKILL_DIR/scripts/`): tell *you* how to interview the user, scan the repo, and emit files. Consumed once per run.
- **Runtime instructions** (emitted into `$TARGET/AGENTS.md` + `$TARGET/$CONTEXT_DIR/`): tell *future agent sessions* how to load context and self-update while working on the target repo. Consumed every session after scaffold.

The self-update rules in `$SKILL_DIR/rules/self-update.md` are **runtime rules for the target repo**; they get composed into the emitted `AGENTS.md`. They do not govern this scaffolder. Do not apply them to `$SKILL_DIR/` itself.

## Glossary

| Symbol | Meaning |
|---|---|
| `$TARGET` | Current working directory: the repo being scaffolded. |
| `$SKILL_DIR` | Directory this `SKILL.md` sits in. Resolve at start of run; fall back to `~/.claude/skills/exodia` if unresolvable. |
| `$CONTEXT_DIR` | Single-segment directory name inside `$TARGET` that holds the context tree. Default `context`; user-named in Step 3a (Fresh / Merge); auto-detected in Step 1 (Incremental). |
| `$CONFIG_PATH` | `$TARGET/exodia.config.yaml`. Presence flips the run into config-driven mode. Throwaway, ignored by incremental re-runs. |
| `$LAYOUT_MAP` | In-memory JSON array of category objects (`name`, `path`, `kind`, `l2_template_path`, `l3_specs`). Finalized by Step 4b in all modes. Shape and validation rules: `$SKILL_DIR/heuristics/layout-map.md`. |
| `$SCAN` | Structured Explore-subagent report from Step 2. |

## Modes

The run takes one of three modes, classified in Step 1:

| Mode | Trigger | Files emitted |
|---|---|---|
| **Fresh** | No `AGENTS.md`, no `CLAUDE.md`, no existing context tree. | Full scaffold: `AGENTS.md` + L2 + L3. |
| **Merge** | `AGENTS.md` and/or `CLAUDE.md` exist; no context tree. Requires user consent in Step 1. | Splits the existing root file into per-module sections, then full scaffold. |
| **Incremental** | A directory containing `<!-- exodia:section:` markers exists. Config (if any) is ignored. | Diff-based updates to auto-filled L2 sections only; never overwrites `AGENTS.md`. |

A run is **interactive** if `$CONFIG_PATH` is absent, **config-driven** if it is present and parses cleanly. Mode (Fresh / Merge / Incremental) and shape (interactive / config-driven) are orthogonal except that Incremental always ignores config.

## Protocol

Execute steps in order. **Do not skip steps.** Use `AskUserQuestion` for user input, `Explore` subagent for scans, `Bash` for mechanical work, and `Write`/`Edit` for file emission.

| Step | File | Modes |
|---|---|---|
| 0 | [`protocol/00-resolve-context.md`](protocol/00-resolve-context.md) | all |
| 1 | [`protocol/01-preflight.md`](protocol/01-preflight.md) | all |
| 2 | [`protocol/02-scan.md`](protocol/02-scan.md) | all |
| 3 | [`protocol/03-categories.md`](protocol/03-categories.md) | Fresh, Merge |
| 3a | [`protocol/03a-context-dir.md`](protocol/03a-context-dir.md) | Fresh, Merge (interactive only) |
| 4 | [`protocol/04-merge.md`](protocol/04-merge.md) | Merge |
| 4b | [`protocol/04b-materialize-layout.md`](protocol/04b-materialize-layout.md) | all |
| 5 | [`protocol/05-init-structure.md`](protocol/05-init-structure.md) | Fresh, Merge |
| 6 | [`protocol/06-draft-l2.md`](protocol/06-draft-l2.md) | Fresh, Merge |
| 7 | [`protocol/07-section-review.md`](protocol/07-section-review.md) | Fresh, Merge |
| 8 | [`protocol/08-emit-agents-md.md`](protocol/08-emit-agents-md.md) | Fresh, Merge |
| 9 | [`protocol/09-l3-seeding.md`](protocol/09-l3-seeding.md) | Fresh, Merge, Incremental |
| 10 | [`protocol/10-wrap-up.md`](protocol/10-wrap-up.md) | all |
| re-run | [`protocol/incremental-rerun.md`](protocol/incremental-rerun.md) | Incremental (replaces Steps 3, 4, 5, 6, 7, 8; Step 4b still runs) |

## Pointers

- `AskUserQuestion` formatting (question text, option labels, list/table rendering, multi-section H3 anchoring): `$SKILL_DIR/heuristics/prompt-format.md`. Required for every Step 7 draft review, Step 4 mapping table, and Step 9 candidate list.
