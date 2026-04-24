---
name: exodia
description: >
  Scaffold a durable, agent-agnostic context tree for any repo: AGENTS.md router + a
  `context/` directory split into 5 narrative modules (architecture, patterns, domain,
  operations, debugging) with append-only L3 data files (.jsonl + .yaml). Interactive:
  scans the repo, proposes categories, drafts each module section-by-section, and
  embeds self-update rules. One-shot. Re-runs incrementally diff existing content.
  Trigger: /exodia. Also triggers on "scaffold agent context", "initialize AGENTS.md",
  "bootstrap context tree".
---

# /exodia — scaffold agent context for a repo

You are running the `exodia` scaffolder. Your job is to generate an `AGENTS.md` router plus a `context/` directory tree in the current working directory. You do this interactively, in a fixed protocol.

## Scaffolder vs. runtime — do not confuse the two

`/exodia` is a **scaffolder**, not a runtime context system. Two distinct roles:

- **Scaffolder instructions** (this file + `$SKILL_DIR/` assets) — tell *you* how to interview the user, scan the repo, and emit files. Consumed once per run.
- **Runtime instructions** (emitted into `$TARGET/AGENTS.md` + `$TARGET/context/`) — tell *future agent sessions* how to load context and self-update while working on the target repo. Consumed every session after scaffold.

The self-update rules in `$SKILL_DIR/rules/self-update.md` are **runtime rules for the target repo** — they get composed into the emitted `AGENTS.md`. They do not govern this scaffolder. Do not apply them to `$SKILL_DIR/` itself.

All assets you need live next to this file:

```
skills/exodia/
  templates/       # L2/L3 stubs you copy into target
  rules/           # snippets composed into final AGENTS.md
  heuristics/      # detector + section-map tables you follow
  hooks/           # optional Claude Code Stop hook
  scripts/         # mechanical helpers (bash + python)
```

When this doc refers to `$SKILL_DIR`, it means the directory this `SKILL.md` sits in. Resolve it at the start of the run: the symlink target of `~/.claude/skills/exodia`, or — if invoked from the plugin cache — the directory of this file. The target repo is the current working directory (`$TARGET` in this doc).

---

## Protocol

Execute steps in order. **Do not skip steps**. Use `AskUserQuestion` for user input, `Explore` subagent for scans, `Bash` for mechanical work, and `Write`/`Edit` for file emission.

### Step 0 — Resolve context

- Confirm `$TARGET` = current working directory.
- Confirm `$SKILL_DIR` = directory of this SKILL.md. If you cannot resolve it, fall back to `~/.claude/skills/exodia`.
- Check `git rev-parse --is-inside-work-tree` in `$TARGET`. If not a git repo, continue but warn the user ("branch-scoped dedup in self-update rules will be ineffective without git").

### Step 1 — Preflight

Detect what already exists:

```bash
ls -la "$TARGET/AGENTS.md" "$TARGET/CLAUDE.md" 2>/dev/null
ls -d "$TARGET/context" 2>/dev/null
```

Classify into one of three modes:

- **Fresh** — none of the above exist. Go to Step 2.
- **Merge** — `AGENTS.md` or `CLAUDE.md` (or both) exists, but no `context/`. Before doing anything else, **ask the user for explicit permission** to consume the existing file(s). Use `AskUserQuestion` with the rationale: *"A monolithic `AGENTS.md` / `CLAUDE.md` hurts agent inference — the whole file is dumped into context on every task. exodia will parse the existing content, split it by `##` sections, and move each section into the appropriate module under `context/`. The original file at the repo root will be replaced by a thin router that points agents to the right module per task. Proceed?"* Options: *proceed*, *abort*. On abort, stop the skill here — do not scaffold anything. On proceed, continue to Step 2 normally; Step 4 handles the split. If both files exist, `AGENTS.md` is the parse source (`CLAUDE.md` becomes a pointer in Step 10 regardless).
- **Incremental** — `context/` already exists with exodia markers. Jump to the *Incremental re-run* section at the bottom.

### Step 2 — Scan the repo

Delegate the initial scan to an `Explore` subagent with **medium** thoroughness (upgrade to very thorough only if the user passes a `--deep` flag or the repo is clearly large and multi-faceted). Pass a prompt shaped like this:

> You are scanning `<TARGET>` to help bootstrap an AGENTS.md context tree. Report in under 800 words:
>
> 1. **Stack**: languages, frameworks, build tool, test tool, package manager. Cite files.
> 2. **Architecture summary**: routing style, state management, module layout, SSR/CSR split, backend/frontend divide. One paragraph.
> 3. **Domain signals**: top-level entities or models you can name (from `models/`, `entities/`, `schemas/`, `prisma/`, `openapi`, etc.).
> 4. **Operations signals**: i18n presence (i18n dirs, vue-i18n / next-intl / react-i18next / i18next deps, locale files), multi-env config (env files, `deploy/`, k8s, helm, terraform), multi-tenant patterns, feature-flag tools.
> 5. **Category-tweak triggers** — report presence/absence of each:
>    - i18n / multi-market
>    - mobile (React Native, Expo, Flutter, iOS/Android dirs)
>    - monorepo (`pnpm-workspace.yaml`, `turbo.json`, `nx.json`, `lerna.json`, `packages/`, `apps/`)
>    - data / ML (`notebooks/`, `models/`, `data/`, ipynb files, pytorch / tf / jax deps)
>    - infra (`terraform/`, `helm/`, `k8s/`, `.tf` files, CloudFormation)
> 6. **Agent integrations present**: `.claude/`, `.cursor/`, `.cursorrules`, `.windsurfrules`, `.github/copilot-instructions.md`.
> 7. **Lint/test/typecheck scripts** detected in `package.json`, `pyproject.toml`, `Gemfile`, `go.mod`, `Cargo.toml`, `Makefile`. Name the commands (e.g. `pnpm lint`, `pytest`).
> 8. **Existing docs** — if `AGENTS.md` / `CLAUDE.md` / `README.md` has structured sections, list the `##` headings.
>
> Output the report as a structured list. Do not speculate — cite files for everything.

Store the returned scan as your working `$SCAN`.

### Step 3 — Propose categories

The **default** starter set is the five canonical categories:

- `architecture/`
- `patterns/`
- `domain/`
- `operations/`
- `debugging/`

Then, based on `$SCAN` and `$SKILL_DIR/heuristics/detectors.md`, compute optional adds:

| Trigger in scan | Add |
|---|---|
| Mobile stack detected | `mobile/` |
| Monorepo manager detected | `workspace/` |
| ML/data stack detected | `data/` |
| Infra-as-code detected | `infra/` |

Use `AskUserQuestion`: "Here's the proposed category set: [list]. OK to proceed?" Offer options: *accept*, *drop any (core or optional)*, *add custom*. If the user wants changes, iterate until they confirm.

The target repo picks the shape. Users may drop any canonical category that does not apply: a pure library may have no `operations/`, a data pipeline may have no `patterns/`, a CLI tool may have no `domain/`. `init_structure.sh` accepts any subset of category names matching `^[a-z][a-z0-9_-]*$` — the core set is a default, not an enforced minimum.

### Step 4 — Existing-file merge (Merge mode only)

If preflight classified as Merge (the user already granted permission in Step 1):

1. Pick the parse source:
   - If `AGENTS.md` exists (with or without `CLAUDE.md`), it is the source.
   - If only `CLAUDE.md` exists, parse that.
2. Run `python3 "$SKILL_DIR/scripts/parse_existing.py" "<source-path>"`. It returns JSON of `[{heading, body}]` split by `##`.
3. For each heading, apply `$SKILL_DIR/heuristics/section-map.md` keyword rules to pick a target category. Unmappable headings → `_unsorted` bucket.
4. Present the mapping table via `AskUserQuestion` (or a numbered prompt if too many rows for four options). Let the user reassign rows.
5. Carry the accepted mapping into Step 6 as **seed content** for each category draft. The parsed content is being *moved*, not copied — the original file will be replaced by Step 8 (router) and, if it was `CLAUDE.md`, by a pointer at Step 10. No `.bak` file is written: the user consented in Step 1, and the content is preserved (split across modules under `context/`) rather than destroyed.

### Step 5 — Initialize structure

Run the scaffolder helper:

```bash
bash "$SKILL_DIR/scripts/init_structure.sh" "$TARGET" <space-separated-category-names>
```

This creates the directory tree, copies `.tmpl` files from `$SKILL_DIR/templates/`, and writes the `_schema` line into each `.jsonl`. YAML stubs ship with their top-level key + a comment block.

### Step 6 — Draft L2 content

For each confirmed category, in order (architecture, patterns, domain, operations, debugging, then optional extras):

1. Read `$SKILL_DIR/templates/<category>/<CATEGORY>.md.tmpl` to see the section skeleton.
2. Using `$SCAN` (and any merge-seeded content from Step 4), fill each `##` section with a short, factual draft. Cite files. No speculation. Keep each section under ~150 words.
3. Preserve the `<!-- exodia:section:<id> -->` markers — they drive incremental re-runs.
4. **Never duplicate data that already lives in the repo.** Versions, ports, env names, paths, commands, config values, dependency lists, script names — all must be *referenced*, not copied. Write `see \`package.json\` \`engines.node\`` or `defined in \`.env.example\``, never the literal value. Duplicated data rots; pointers survive edits.

Do **not** write the file to disk yet. Hold the draft in memory.

### Step 7 — Section-by-section review

Walk each L2 draft with the user. For each `##` section:

- Show the drafted prose.
- `AskUserQuestion` with options: *accept*, *edit*, *reject (leave empty for later)*.
- If edit: let the user dictate changes, re-draft, loop until accepted.

Then `Write` the finalized L2 file to `$TARGET/context/<category>/<CATEGORY>.md`.

### Step 8 — Emit the AGENTS.md router

Compose `$TARGET/AGENTS.md` from:

- `$SKILL_DIR/rules/universal.md` (always included)
- `$SKILL_DIR/rules/conditional/operations-awareness.md` *only if `operations/` is in the final category set*
- `$SKILL_DIR/rules/conditional/lint-check.md` if scan detected any lint/test/typecheck scripts — substitute the detected commands into the snippet
- `$SKILL_DIR/rules/self-update.md` (always — near the top). When composing the Self-Update Rules block, drop table rows whose target path is not in the final category set (e.g. drop the `operations/variants.yaml` row if `operations/` was dropped, drop the `domain/glossary.yaml` row if `domain/` was dropped).

Follow the shape in `$SKILL_DIR/templates/AGENTS.md.tmpl`:

1. Project overview (one paragraph from scan)
2. Commands (point to the detected package manifest file)
3. Context Router table (one row per confirmed category)
4. Behavioral Rules (universal + conditional)
5. Self-Update Rules (full block)
6. Quick Action Table (common dev phrases → file to read)
7. Context Structure (tree diagram)

### Step 9 — L3 seeding prompt

Ask the user whether to seed L3 files from the codebase:

- `gotchas.jsonl`: scan for `TODO`, `FIXME`, `HACK`, `XXX`, `WARNING` comments. Group by directory/area. Present a trimmed candidate list and let the user approve a subset.
- `decisions.jsonl`: look for `docs/adr/`, `docs/decisions/`, `ARCHITECTURE.md` headings with decision language. Present candidates.

If yes, append entries using the canonical ID format `{type}_{YYYYMMDD}_{HHMMSS}_{4hex}` where `{type}` is `gotcha`, `pb`, `adr`, or `rv`.

### Step 10 — Emit agent pointer files

Every agent runtime has its own conventions for where top-level instructions live (`CLAUDE.md`, `.cursorrules`, `.windsurfrules`, `.github/copilot-instructions.md`, something custom, or nothing at all). The scaffolder does not ship a hardcoded list — the target repo picks.

Flow:

1. From `$SCAN`, note any agent-integration files already present (`.claude/`, `.cursor/`, `.cursorrules`, `.windsurfrules`, `.github/copilot-instructions.md`, etc.). Mention them in the question prose as *hints only*.
2. `AskUserQuestion`: *"Which pointer files should point to `AGENTS.md`? Provide one or more repo-relative paths (e.g. `CLAUDE.md`, `.cursorrules`, `.github/copilot-instructions.md`, or any custom path). Leave empty to skip this step."* Do not preselect a known-runtime list — the user knows their own setup.
3. For each path the user supplies, run:

   ```bash
   bash "$SKILL_DIR/scripts/symlink_agents.sh" "$TARGET" "<pointer-path>" [<pointer-path> ...]
   ```

   The script accepts one or more literal paths. Each becomes a symlink back to `AGENTS.md` (or a one-line pointer file on filesystems without symlink support). Paths must not contain `..` segments and must not be absolute.
4. If the user provides no paths, skip this step entirely.

### Step 11 — Optional Stop hook install

If the user is on Claude Code (detect via `$TARGET/.claude/` presence or ask), offer:

> "Install a Claude Code `Stop` hook that reminds the agent to apply Self-Update Rules at turn end? It only augments the prose rules already in AGENTS.md."

If yes:

```bash
bash "$SKILL_DIR/scripts/install_hook.sh" "$TARGET"
```

This writes `$SKILL_DIR/hooks/stop-reminder.sh` into `$TARGET/.claude/hooks/exodia-stop-reminder.sh` and registers it in `$TARGET/.claude/settings.json` under `"hooks.Stop"`. The installer is idempotent.

### Step 12 — Wrap up

Print a short summary:

- What was created (counts: L2 files, L3 files, pointer files, hook yes/no)
- Next steps for the user (how to iterate: just edit the files; the self-update rules handle growth)
- Reminder: running `/exodia` again triggers incremental re-run, not a fresh scaffold

---

## Incremental re-run

When preflight detects an existing exodia setup:

1. Re-run Step 2 (scan).
2. For each L2 file, read it and locate `<!-- exodia:section:<id> -->` markers. Fresh-draft *new* facts from the scan. Diff against existing auto-filled content.
3. Propose updates only to sections where the auto-filled block has not been user-edited (detect with the section-id marker — if the content after the marker differs from a reconstructible baseline, treat it as user-edited and do not touch).
4. Show the proposed diffs via `AskUserQuestion` (accept / skip per section).
5. Append to L3 files from the scan using the same Step 9 logic.
6. Never overwrite `AGENTS.md` — only add missing rule snippets if conditions now apply (e.g. a Stop hook was added after initial scaffold).

---

## Failure modes to watch

- **User aborts mid-interview** — leave the repo in whatever partial state exists. No need to roll back. Running `/exodia` again resumes from preflight.
- **Explore scan times out / returns garbage** — fall back to asking the user to confirm the stack and architecture directly, then continue.
- **Target repo has committed secrets or `.env` with real values** — never echo these in drafts. If you must reference env vars, name them only.
- **No git, no agent integration, no lint scripts** — skill still works; just emits the minimal universal rules.

---

## Tone for drafts

Drafts must be terse, factual, table- and bullet-heavy, with inline file citations and no marketing prose. Read `$SKILL_DIR/templates/*/*.tmpl` before drafting to lock the voice.
