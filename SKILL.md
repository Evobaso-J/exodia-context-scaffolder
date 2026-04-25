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

# /exodia: scaffold agent context for a repo

You are running the `exodia` scaffolder. Your job is to generate an `AGENTS.md` router plus a `context/` directory tree in the current working directory. You do this interactively, in a fixed protocol.

## Scaffolder vs. runtime: do not confuse the two

`/exodia` is a **scaffolder**, not a runtime context system. Two distinct roles:

- **Scaffolder instructions** (this file + `$SKILL_DIR/` assets): tell *you* how to interview the user, scan the repo, and emit files. Consumed once per run.
- **Runtime instructions** (emitted into `$TARGET/AGENTS.md` + `$TARGET/$CONTEXT_DIR/`): tell *future agent sessions* how to load context and self-update while working on the target repo. Consumed every session after scaffold.

The self-update rules in `$SKILL_DIR/rules/self-update.md` are **runtime rules for the target repo**; they get composed into the emitted `AGENTS.md`. They do not govern this scaffolder. Do not apply them to `$SKILL_DIR/` itself.

All assets you need live next to this file:

```
./
  templates/       # L2/L3 stubs you copy into target
  rules/           # snippets composed into final AGENTS.md
  heuristics/      # detector + section-map tables you follow
  scripts/         # mechanical helpers (bash + python)
```

When this doc refers to `$SKILL_DIR`, it means the directory this `SKILL.md` sits in. Resolve it at the start of the run: typically `~/.claude/skills/exodia` for an installed skill, or the directory of this file as a fallback. The target repo is the current working directory (`$TARGET` in this doc).

---

## Protocol

Execute steps in order. **Do not skip steps**. Use `AskUserQuestion` for user input, `Explore` subagent for scans, `Bash` for mechanical work, and `Write`/`Edit` for file emission.

### Step 0: Resolve context

- Confirm `$TARGET` = current working directory.
- Confirm `$SKILL_DIR` = directory of this SKILL.md. If you cannot resolve it, fall back to `~/.claude/skills/exodia`.
- Check `git rev-parse --is-inside-work-tree` in `$TARGET`. If not a git repo, continue but warn the user ("branch-scoped dedup in self-update rules will be ineffective without git").
- Hold a variable `$CONTEXT_DIR` throughout the run. It names the directory that will hold the context tree inside `$TARGET`. Default is `context`; the user may pick another name in Step 3a (Fresh / Merge) or it is auto-detected in Step 1 (Incremental).

### Step 1: Preflight

Detect what already exists:

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

Classify into one of three modes:

- **Fresh**: no `AGENTS.md`, no `CLAUDE.md`, no `$EXISTING_CONTEXT_DIR`. Go to Step 2.
- **Merge**: `AGENTS.md` or `CLAUDE.md` (or both) exists, but no existing context tree. Before doing anything else, **ask the user for explicit permission** to consume the existing file(s). Use `AskUserQuestion`:
  - **Question**: "Split existing `AGENTS.md` / `CLAUDE.md` into per-module sections?"
  - **Options**:
    - "Yes, split now": parse the existing file, route each section into the right module, replace the root file with a thin router. Original content is preserved across modules, not destroyed. A monolithic root file is reloaded on every task; splitting is the long-term fix.
    - "No, stop": exit without changes. You can revisit later by re-running `/exodia`.

  If the user declines, stop the skill here and do not scaffold anything. If they accept, continue to Step 2 normally; Step 4 handles the split. If both files exist, `AGENTS.md` is the parse source.
- **Incremental**: `$EXISTING_CONTEXT_DIR` is non-empty. Set `$CONTEXT_DIR=$EXISTING_CONTEXT_DIR` and jump to the *Incremental re-run* section at the bottom; do not ask the dir-name question again.

### Step 2: Scan the repo

Delegate the initial scan to an `Explore` subagent with **medium** thoroughness (upgrade to very thorough only if the user passes a `--deep` flag or the repo is clearly large and multi-faceted). Pass a prompt shaped like this:

> You are scanning `<TARGET>` to help bootstrap an AGENTS.md context tree. Report in under 800 words:
>
> 1. **Stack**: languages, frameworks, build tool, test tool, package manager. Cite files.
> 2. **Architecture summary**: routing style, state management, module layout, SSR/CSR split, backend/frontend divide. One paragraph.
> 3. **Domain signals**: top-level entities or models you can name. Look wherever the repo keeps its domain objects: schema files, model classes, type definitions, or a dedicated directory.
> 4. **Operations signals**: i18n tooling if any framework-specific lib is present (locale files, translation dirs), multi-env config (env files, `deploy/`, k8s, helm, terraform), multi-tenant patterns, feature-flag tools.
> 5. **Category-tweak triggers**: report presence/absence of each:
>    - i18n / multi-market
>    - mobile (React Native, Expo, Flutter, iOS/Android dirs)
>    - monorepo (`pnpm-workspace.yaml`, `turbo.json`, `nx.json`, `lerna.json`, `packages/`, `apps/`)
>    - data / ML (`notebooks/`, `models/`, `data/`, ipynb files, pytorch / tf / jax deps)
>    - infra (`terraform/`, `helm/`, `k8s/`, `.tf` files, CloudFormation)
> 6. **Lint/test/typecheck scripts** detected in `package.json`, `pyproject.toml`, `Gemfile`, `go.mod`, `Cargo.toml`, `Makefile`. Name the commands (e.g. `pnpm lint`, `pytest`).
> 7. **Existing docs**: if `AGENTS.md` / `CLAUDE.md` / `README.md` has structured sections, list the `##` headings.
>
> Output the report as a structured list. Do not speculate; cite files for everything.

Store the returned scan as your working `$SCAN`.

### Step 3: Propose categories

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

First render the proposed set as a markdown bulleted list (one category per line, with the one-line purpose) so the user can scan it. Then use `AskUserQuestion`:

- **Question**: "Use this category set?"
- **Options**:
  - "Accept set"
  - "Drop categories": list which to drop in the follow-up.
  - "Add custom": provide name + one-line purpose in the follow-up.

Iterate until the user confirms.

When the user adds a **custom category**, ask two follow-ups: (1) one-line purpose statement, (2) any L3 ledgers needed (append-only logs, structured taxonomies). Consult `$SKILL_DIR/heuristics/format-strategy.md` to pick the format for each proposed L3 file (`.jsonl` for append-only / id-keyed records, `.yaml` for named taxonomies). `init_structure.sh` will scaffold an empty L2 stub for any category without a template dir; if the user asked for L3, draft those stubs in Step 6 alongside the L2.

The target repo picks the shape. Users may drop any canonical category that does not apply: a pure library may have no `operations/`, a data pipeline may have no `patterns/`, a CLI tool may have no `domain/`. `init_structure.sh` accepts any subset of category names matching `^[a-z][a-z0-9_-]*$`; the core set is a default, not an enforced minimum.

### Step 3a: Name the context directory

Fresh and Merge modes only. Skip in Incremental mode (already detected in Step 1).

`AskUserQuestion`:

- **Question**: "Context directory name? (default: `context/`)"
- **Description**: "Pick any path-safe single-segment name: `context`, `docs`, `knowledge`, `.agents`, `ai`, whatever matches the repo's conventions."

Accept any value matching `^[a-z._-][a-z0-9._-]*$` (single safe filesystem segment, no slashes, no `..`, no `.` alone). Store as `$CONTEXT_DIR`. Default to `context` if the user accepts the default. Validate the answer before continuing.

**Collision check.** A directory with a common name like `docs/`, `knowledge/`, or `ai/` may already exist in the target repo for reasons unrelated to exodia (user-authored docs, generated artifacts, unrelated tooling). After the user picks a name, check `$TARGET/$CONTEXT_DIR`:

- If the directory does not exist, or exists and is empty: proceed.
- If it exists with files that already carry `<!-- exodia:section:` markers: Step 1 misclassified the mode. Switch to Incremental treatment of that directory and skip the rest of Fresh/Merge scaffolding.
- If it exists with files but none carry exodia markers (pre-existing non-exodia content): list the first 5 to 10 existing top-level entries as a markdown bulleted list, then `AskUserQuestion`:
  - **Question**: "`$CONTEXT_DIR/` already has unrelated content. How to proceed?"
  - **Options**:
    - "Share directory": exodia adds `<category>/...` subdirectories alongside existing content; templates only land on fresh paths, existing files are left untouched.
    - "Pick different name": re-ask the Step 3a question.
    - "Abort scaffold": stop the skill cleanly.

The scaffolder never overwrites existing files (`init_structure.sh` skips any destination that already exists), but a shared top-level directory still entangles the exodia tree with unrelated content. The consent step makes that entanglement explicit.

### Step 4: Existing-file merge (Merge mode only)

If preflight classified as Merge (the user already granted permission in Step 1):

1. Pick the parse source:
   - If `AGENTS.md` exists (with or without `CLAUDE.md`), it is the source.
   - If only `CLAUDE.md` exists, parse that.
2. Run `python3 "$SKILL_DIR/scripts/parse_existing.py" "<source-path>"`. It returns JSON of `[{heading, body}]` split by `##`.
3. For each heading, apply `$SKILL_DIR/heuristics/section-map.md` keyword rules to pick a target category. Unmappable headings → `_unsorted` bucket.
4. Render the mapping as a markdown table:

   ```
   | # | Heading           | →  | Proposed category |
   |---|-------------------|----|-------------------|
   | 1 | Architecture      | →  | architecture      |
   | 2 | Local dev         | →  | operations        |
   ```

   Then `AskUserQuestion`:
   - **Question**: "Mapping look right?"
   - **Options**: "Accept all", "Reassign rows", "Drop rows", "Edit table".

   If the table is too long for the four-option bound, fall back to a numbered prompt: ask the user to type row reassignments (`3→domain, 5→drop`).
5. Carry the accepted mapping into Step 6 as **seed content** for each category draft. The parsed content is being *moved*, not copied; the original file is replaced by Step 8 (router). No `.bak` file is written: the user consented in Step 1, and the content is preserved (split across modules under `$CONTEXT_DIR/`) rather than destroyed.

### Step 5: Initialize structure

Run the scaffolder helper:

```bash
bash "$SKILL_DIR/scripts/init_structure.sh" "$TARGET" "$CONTEXT_DIR" <space-separated-category-names>
```

`$CONTEXT_DIR` is the second positional argument. This creates `$TARGET/$CONTEXT_DIR/<category>/` for each requested category, copies `.tmpl` files from `$SKILL_DIR/templates/`, and writes the `_schema` line into each `.jsonl`. YAML stubs ship with their top-level key + a comment block.

### Step 6: Draft L2 content

For each confirmed category, in order (architecture, patterns, domain, operations, debugging, then optional extras):

1. Read `$SKILL_DIR/templates/<category>/<CATEGORY>.md.tmpl` to see the section skeleton and lock the voice (terse, factual, table- and bullet-heavy, inline file citations, no marketing prose).
2. Using `$SCAN` (and any merge-seeded content from Step 4), fill each `##` section with a short, factual draft. Cite files. No speculation. Keep each section under ~150 words.
3. Preserve the `<!-- exodia:section:<id> -->` markers; they drive incremental re-runs.
4. **Never duplicate data that already lives in the repo.** Versions, ports, env names, paths, commands, config values, dependency lists, script names; all must be *referenced*, not copied. Write `see \`package.json\` \`engines.node\`` or `defined in \`.env.example\``, never the literal value. Duplicated data rots; pointers survive edits.
5. **`## L3 Data` section.** When the L2 template has a `<!-- exodia:section:l3 -->` block, list the L3 files that ship with the module. For custom categories with no template, draft this section from the L3 ledgers requested in Step 3, picking formats per `$SKILL_DIR/heuristics/format-strategy.md`. Each line: `` - `<file>`: <one-line purpose>. ``

Do **not** write the file to disk yet. Hold the draft in memory.

### Step 7: Section-by-section review

Walk each L2 draft with the user. For each `##` section:

- Show the drafted prose.
- Render the draft inside a fenced markdown block, prefaced by an H3 anchor: `### \`<category>/<CATEGORY>.md\` § <section-id>`.
- Then `AskUserQuestion`:
  - **Question**: "Accept this section?"
  - **Options**: "Accept", "Edit", "Skip" (leave empty for later).
- If edit: let the user dictate changes, re-draft (still inside the fenced block), loop until accepted.

Then `Write` the finalized L2 file to `$TARGET/$CONTEXT_DIR/<category>/<CATEGORY>.md`.

### Step 8: Emit the AGENTS.md router

Compose `$TARGET/AGENTS.md` from:

- `$SKILL_DIR/rules/universal.md` (always included)
- `$SKILL_DIR/rules/conditional/operations-awareness.md` *only if `operations/` is in the final category set*
- `$SKILL_DIR/rules/conditional/lint-check.md` if scan detected any lint/test/typecheck scripts; substitute the detected commands into the snippet
- `$SKILL_DIR/rules/self-update.md` (always, near the top). When composing the Self-Update Rules block, drop table rows whose target path is not in the final category set. This applies to both core and optional rows (e.g. drop the `operations/variants.yaml` row if `operations/` was dropped, drop the `domain/glossary.yaml` row if `domain/` was dropped, drop both `infra/*` rows if `infra/` was dropped). The `File Format Strategy` § at the bottom of `self-update.md` is always retained; it guides future agents adding new ledgers.

Follow the shape in `$SKILL_DIR/templates/AGENTS.md.tmpl`:

1. Project overview (one paragraph from scan)
2. Commands (point to the detected package manifest file)
3. Context Router table (one row per confirmed category, linking to `$CONTEXT_DIR/<category>/<CATEGORY>.md`)
4. Behavioral Rules (universal + conditional)
5. Self-Update Rules (full block)
6. Quick Action Table (common dev phrases → file to read)
7. Context Structure (tree diagram, rooted at `$CONTEXT_DIR/`)

Rule snippets (`universal.md`, `conditional/operations-awareness.md`, `self-update.md`, and the `{{CONTEXT_TREE}}` diagram) contain `{{CONTEXT_DIR}}` placeholders. Substitute all occurrences with the actual value of `$CONTEXT_DIR` before writing the emitted `AGENTS.md`.

### Step 9: L3 seeding prompt

Ask the user whether to seed L3 files from the codebase. Tailor the prompt to the final category set:

- `debugging/gotchas.jsonl`: scan for `TODO`, `FIXME`, `HACK`, `XXX`, `WARNING` comments. Group by directory/area. Present a trimmed candidate list and let the user approve a subset.
- `architecture/decisions.jsonl`: look for `docs/adr/`, `docs/decisions/`, `ARCHITECTURE.md` headings with decision language. Present candidates.
- `infra/decisions.jsonl` (if `infra/` present): scan `terraform/`, `helm/`, `k8s/` commit messages and any `infra/CHANGES.md` for infra-scoped decisions.
- `data/experiments.jsonl` (if `data/` present): scan `experiments/`, `notebooks/`, `runs/` directories and any `RESULTS.md` for past run summaries.
- `mobile/releases.jsonl` (if `mobile/` present): scan store-config files, `fastlane/` metadata, or git tags matching version patterns for prior rollouts.

If yes, append entries using the canonical ID format `{type}_{YYYYMMDD}_{HHMMSS}_{4hex}`. The `{type}` prefix is the target file's `_schema` value, verbatim (read the first line of the `.jsonl`). See `$SKILL_DIR/heuristics/format-strategy.md` § ID format.

### Step 10: Wrap up

Print a short summary:

- What was created (counts: L2 files, L3 files)
- Next steps for the user (how to iterate: just edit the files; the self-update rules handle growth)
- Reminder: running `/exodia` again triggers incremental re-run, not a fresh scaffold

---

## Incremental re-run

When preflight detects an existing exodia setup:

0. Trust the `$CONTEXT_DIR` already detected in Step 1. Do not ask the user to rename it; preserving the existing directory name keeps router paths consistent.
1. Re-run Step 2 (scan).
2. For each L2 file under `$TARGET/$CONTEXT_DIR/`, read it and locate `<!-- exodia:section:<id> -->` markers. Fresh-draft *new* facts from the scan. Diff against existing auto-filled content.
3. Propose updates only to sections where the auto-filled block has not been user-edited (detect with the section-id marker; if the content after the marker differs from a reconstructible baseline, treat it as user-edited and do not touch).
4. Render each proposed diff as a fenced ` ```diff ` code block, prefaced by `### \`<file>\` § <section-id>`. Then per section, `AskUserQuestion`:
   - **Question**: "Apply this update?"
   - **Options**: "Accept", "Skip".
5. Append to L3 files from the scan using the same Step 9 logic.
6. Never overwrite `AGENTS.md`; only add missing rule snippets if conditions now apply (e.g. an `operations/` category added after initial scaffold).

---

## Failure modes to watch

See `$SKILL_DIR/TROUBLESHOOTING.md` for handling: user aborts mid-interview, Explore scan timeouts, secrets in the target repo, missing git/agent/lint toolchain.

---

## User-facing prompt format

Every prompt the user sees during the run should be scannable. Apply these rules to every `AskUserQuestion` call site, every Step 7 draft review, every Step 4 mapping table, and every Step 9 candidate list.

**Question text**

- One sentence, ≤120 characters.
- No hedging openers (`Would you like...`, `Could you...`, `Do you want me to...`). State the choice directly: `Split now?`, `Use this category set?`, `Accept this section?`.
- Inline `code` for file paths, directory names, and identifiers.

**Option labels**

- ≤5 words. Action-verb start: `Accept set`, `Drop categories`, `Add custom`, `Pick different name`, `Abort scaffold`.
- Cap 4 options per call. If you need more, fall back to a numbered free-text prompt (`Type row reassignments: 3→domain, 5→drop`).
- Long rationale lives in the option `description` field, never in the question body.

**Lists, tables, and candidate sets**

- Render as actual markdown (bulleted lists, real `|` tables, fenced code blocks). Not prose paragraphs.
- Group long lists by directory, category, or file. Cap visible items at ~20; offer a "show more" branch if longer.
- Truncate long paths mid-segment with `...` (e.g. `apps/web/.../routes/foo.ts`).

**Multi-section drafts (Step 7, Step 4 mapping, incremental diffs)**

- Preface each block with an H3 anchor: `### \`<file>\` § <section-id>`. Lets the user scan a long review.
- Put draft prose inside a fenced markdown block. Put diffs inside a ` ```diff ` block.
- One H3 + one fenced block + one `AskUserQuestion` per section. Do not stack multiple sections under one question.
