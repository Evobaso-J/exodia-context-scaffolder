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
- Resolve `$CONFIG_PATH = $TARGET/exodia.config.yaml`. If the file exists, the run is **config-driven**: layout comes from the config rather than from interactive prompts. If absent, the interactive flow runs unchanged. Config is throwaway and only consumed at first scaffold (Fresh or Merge); incremental re-runs ignore it. Schema reference: see the "Customizing the layout" section in `$SKILL_DIR/README.md`.

### Step 1: Preflight

If `$CONFIG_PATH` is present, parse and validate it **before** mode classification:

```bash
python3 "$SKILL_DIR/scripts/parse_config.py" "$CONFIG_PATH"
```

On non-zero exit, abort the run and surface the line-numbered errors from stderr verbatim. Do not attempt to proceed without the config; the user must fix it. On success, pipe the JSON output through `resolve_layout.py` and store the result as `$LAYOUT_MAP`:

```bash
python3 "$SKILL_DIR/scripts/parse_config.py" "$CONFIG_PATH" \
  | python3 "$SKILL_DIR/scripts/resolve_layout.py" --skill-dir "$SKILL_DIR"
```

`$LAYOUT_MAP` is the single source of truth for `name → path`, kind, L2 template, and L3 specs that every later step consumes.

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
- **Incremental**: `$EXISTING_CONTEXT_DIR` is non-empty. Set `$CONTEXT_DIR=$EXISTING_CONTEXT_DIR` and jump to the *Incremental re-run* section at the bottom; do not ask the dir-name question again. If `$CONFIG_PATH` is also present, ignore it and print one warning line: `Config detected but tree exists; ignoring. Delete \`exodia.config.yaml\` to silence this warning.`

When entering the *Incremental re-run* section, parse the **router region** of `$TARGET/AGENTS.md` for the canonical category → path map. The region is wrapped in `<!-- exodia:router:start -->` / `<!-- exodia:router:end -->` markers around the `## Context Router` table. If the markers are absent (the scaffold pre-dates this feature), fall back to a plain `<!-- exodia:section:` grep across `$TARGET/$EXISTING_CONTEXT_DIR/`, then lazily inject the markers around the router table on the next emit and note the migration in the wrap-up summary.

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

**Config-driven branch.** If `$LAYOUT_MAP` is set (config present), skip the category-set proposal entirely. Use the resolved categories from `$LAYOUT_MAP` as the confirmed set. Still run the detector heuristics in `$SKILL_DIR/heuristics/detectors.md`: for each detected optional canonical (`mobile`, `workspace`, `data`, `infra`) **not already in `$LAYOUT_MAP`** and not declared with `drop: true`, present one focused `AskUserQuestion` per detected category to add it under `<context_dir>/<name>/` (using `context_dir` from the config). Accepted additions are merged into `$LAYOUT_MAP`. Then jump to Step 4. The custom-category interview below does not run; custom categories come exclusively from the config.

**Interactive branch.** When no config is present, the **default** starter set is the five canonical categories:

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

When the user adds a **custom category**, ask three follow-ups: (1) one-line purpose statement, (2) any L3 ledgers needed (append-only logs, structured taxonomies), (3) for each declared L3 ledger, a one-line **scan hint** that Step 9 will use to seed it (e.g. "scan TODO comments under `src/jobs/`", "parse `docs/playbooks/`", "git log matching `^perf:`"). Accept "none" to skip seeding for that ledger. Consult `$SKILL_DIR/heuristics/format-strategy.md` to pick the format for each proposed L3 file (`.jsonl` for append-only / id-keyed records, `.yaml` for named taxonomies). `init_structure.sh` will scaffold an empty L2 stub for any category without a template dir; if the user asked for L3, draft those stubs in Step 6 alongside the L2 and carry the scan hints into Step 9.

The target repo picks the shape. Users may drop any canonical category that does not apply: a pure library may have no `operations/`, a data pipeline may have no `patterns/`, a CLI tool may have no `domain/`. `init_structure.sh` accepts any subset of category names matching `^[a-z][a-z0-9_-]*$`; the core set is a default, not an enforced minimum.

### Step 3a: Name the context directory

Fresh and Merge modes only. Skip in Incremental mode (already detected in Step 1). Skip entirely when `$LAYOUT_MAP` is set: paths come from the config, and `context_dir` is the default prefix already baked into each canonical category's resolved path.

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
3. For each heading, apply `$SKILL_DIR/heuristics/section-map.md` keyword rules to pick a target category. Restrict the candidate set to the categories present in `$LAYOUT_MAP` when config-driven (canonical + custom); otherwise use the interactively confirmed set from Step 3. Unmappable headings → `_unsorted` bucket.
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

Run the scaffolder helper.

**Interactive (no config):**

```bash
bash "$SKILL_DIR/scripts/init_structure.sh" "$TARGET" "$CONTEXT_DIR" <space-separated-category-names>
```

**Config-driven (`$LAYOUT_MAP` set):** pass each category's resolved path via the `--pairs` form, one `name=path` per category in `$LAYOUT_MAP`:

```bash
bash "$SKILL_DIR/scripts/init_structure.sh" "$TARGET" --pairs \
  architecture=docs/project/architecture \
  patterns=docs/project/patterns \
  debugging=docs/project/debugging \
  glossary=docs/domain/glossary
```

In both shapes the helper creates the destination dirs with `mkdir -p`, copies `.tmpl` files from `$SKILL_DIR/templates/<canonical-name>/` when the category name matches a template dir, and writes a default L2 stub (`## Purpose`, `## Key Files`, `## L3 Data`) for custom categories with no template. Existing destination files are never overwritten. L3 files declared via `l3:` in the config but not auto-copied by `init_structure.sh` (because the host category has no template dir) are written by Step 6 from the schema template resolved in `$LAYOUT_MAP[*].l3_specs`.

### Step 6: Draft L2 content

For each confirmed category, in order (architecture, patterns, domain, operations, debugging, then optional extras and custom categories):

1. **Choose the section skeleton.** If the category has an `l2_template_path` (canonical with template), read it and lock the voice (terse, factual, table- and bullet-heavy, inline file citations, no marketing prose). For custom categories with no template (`l2_template_path: null`), use the default skeleton already written by `init_structure.sh` (`## Purpose`, `## Key Files`, `## L3 Data`) plus any extra `##` sections you deem useful from the scan.
2. Using `$SCAN` (and any merge-seeded content from Step 4), fill each `##` section with a short, factual draft. Cite files. No speculation. Keep each section under ~150 words.
3. Preserve the `<!-- exodia:section:<id> -->` markers; they drive incremental re-runs.
4. **Never duplicate data that already lives in the repo.** Versions, ports, env names, paths, commands, config values, dependency lists, script names; all must be *referenced*, not copied. Write `see \`package.json\` \`engines.node\`` or `defined in \`.env.example\``, never the literal value. Duplicated data rots; pointers survive edits.
5. **`## L3 Data` section.** Drive this section from `l3_specs` in `$LAYOUT_MAP` when config-driven. When the L2 template has a `<!-- exodia:section:l3 -->` block, list the L3 files that ship with the module. For custom categories whose `l3_specs` are populated by the config, list those files (each entry a `{filename, schema_name, schema_template_path}`); copy the schema template to the destination if `schema_template_path` is non-null and the destination does not yet exist; otherwise propose the schema body inline. For custom categories where `l3_specs` is `null`, propose filenames + schemas yourself (Q13-B), picking formats per `$SKILL_DIR/heuristics/format-strategy.md`. Each line in the L3 section reads `` - `<file>`: <one-line purpose>. ``

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
- `$SKILL_DIR/rules/self-update.md` (always, near the top).

**Ledger row generation.** `self-update.md` ships with a `<!-- exodia:self-update:rows:start -->` / `<!-- exodia:self-update:rows:end -->` marker pair around a `{{LEDGER_ROWS}}` token. Render rows from the canonical ledger registry at `$SKILL_DIR/heuristics/ledgers.yaml`; that file is the single source of truth for filename, host, schema, signal, action, and scan source. Do not duplicate ledger data in this step.

For each ledger entry in `ledgers.yaml`:

1. Resolve the host's path from `$LAYOUT_MAP` (interactive runs construct the equivalent map by joining `$CONTEXT_DIR` with each canonical category name).
2. **Drop the ledger** if the host category is dropped or absent from the final set, or the ledger's `filename` is not in the host category's `l3_specs`.
3. Otherwise emit one Markdown table row **per `signals` entry** (some ledgers, e.g. `reviews`, declare multiple signals): `\| <signal> \| \`<host_path>/<filename>\` \| <action> \|`.

Then append generated rows for **custom-category ledgers** (categories with `kind: custom` in `$LAYOUT_MAP` whose `l3_specs` is non-empty). For each `(category, ledger)` pair: if the ledger's `schema_name` matches a row in `ledgers.yaml`, reuse that row's signals/actions with the custom category's resolved path. Otherwise write a one-line "When to update" hint from the category's purpose statement.

Substitute `{{LEDGER_ROWS}}` with the rendered rows joined by newlines.

The `File Format Strategy` § at the bottom of `self-update.md` is always retained; it guides future agents adding new ledgers.

Follow the shape in `$SKILL_DIR/templates/AGENTS.md.tmpl`:

1. Project overview (one paragraph from scan)
2. Commands (point to the detected package manifest file)
3. Context Router table (one row per confirmed category, linking to the resolved `<path>/<CATEGORY>.md`). Wrap the table in `<!-- exodia:router:start -->` / `<!-- exodia:router:end -->` markers (the template already does this); incremental re-runs parse this region for the category → path map, so do not move the markers or add prose between them and the table.
4. Behavioral Rules (universal + conditional)
5. Self-Update Rules (full block, after placeholder substitution + custom-row append)
6. Quick Action Table (common dev phrases → file to read)
7. Context Structure (tree diagram). Group resolved paths by their longest common prefix and render one tree per group, so multi-root layouts (e.g. `docs/project/...` and `docs/domain/...`) read cleanly.

Rule snippets (`universal.md`, `conditional/operations-awareness.md`, `self-update.md`, and the `{{CONTEXT_TREE}}` diagram) contain `{{CONTEXT_DIR}}` placeholders. Substitute every `{{CONTEXT_DIR}}` with `$CONTEXT_DIR` for interactive runs. For config-driven runs, `{{CONTEXT_DIR}}` is replaced by `context_dir` from the config (the default prefix), and `{{path:<key>}}` placeholders carry the per-category specifics.

### Step 9: L3 seeding prompt

For each L3 file in the final category set, apply the matching seed clause below. The "target file" is now resolved against `$LAYOUT_MAP` (config-driven) or `$TARGET/$CONTEXT_DIR/<category>/<file>` (interactive). Skip any clause whose target file does not exist (the user may have dropped that category in Step 3). JSONL clauses scan candidates and let the user approve a subset via `AskUserQuestion`; YAML clauses propose a skeleton (named keys with empty body fields) for the user to accept, edit, or skip.

**Driven by `$SKILL_DIR/heuristics/ledgers.yaml`.** That file is the single source for `format` (jsonl vs yaml), `scan_source` (jsonl), and `skeleton_source` / `skeleton_shape` (yaml) for every ledger the scaffolder ships. Do not duplicate this data in this step.

For each entry in `ledgers.yaml`: locate the host category in `$LAYOUT_MAP` and resolve the target file `<host_path>/<filename>`. Skip if the host category is dropped, or the filename is absent from the host's `l3_specs`, or the target file does not exist on disk.

For **custom-category ledgers** declared in the config, extend this step with one extra clause per `(category, ledger)` pair from `$LAYOUT_MAP`. If the ledger's `schema_name` matches a row in `ledgers.yaml`, reuse that row's `scan_source` (jsonl) or `skeleton_source` / `skeleton_shape` (yaml) verbatim. Otherwise use the scan source the model proposed alongside the schema in Step 6 (carry it through the layout map). Append entries the same way as built-in clauses, using the ledger's own `_schema` prefix (canonical or model-invented).

Append JSONL entries using the canonical ID format `{type}_{YYYYMMDD}_{HHMMSS}_{4hex}`. The `{type}` prefix is the target file's `_schema` value, verbatim (read the first line of the `.jsonl`). See `$SKILL_DIR/heuristics/format-strategy.md` § ID format.

**JSONL clauses.** Iterate `ledgers.yaml` rows where `format: jsonl`. For each row: run the registry-declared `scan_source`, render the candidate list per `$SKILL_DIR/heuristics/prompt-format.md`, then `AskUserQuestion` to approve a subset. Append approved entries with canonical IDs.

**YAML clauses (skeleton-from-scan).** Iterate `ledgers.yaml` rows where `format: yaml`. For each row: render the proposed skeleton (per `skeleton_shape`, sourced from `skeleton_source`) inside a fenced ` ```yaml ` block prefaced by `### \`<file>\` § skeleton`, then `AskUserQuestion`:

- **Question**: "Accept this skeleton?"
- **Options**: "Accept", "Edit", "Skip" (leave the existing empty stub).

On accept or after edit, overwrite the YAML stub with the populated skeleton.

**Custom L3 clause.** For each user-declared custom ledger from Step 3, look up the scan hint captured at declaration time. If the hint is non-empty, run it as a Bash/Explore query, present candidates the same way as built-in JSONL clauses, and append approved entries (using the ledger's own `_schema` prefix). If the hint is "none", skip.

### Step 10: Wrap up

Print a short summary:

- What was created (counts: L2 files, L3 files).
- **Sibling notice (config-driven only).** For each parent directory shared by two or more managed paths (e.g. `docs/domain/` is parent to a managed `glossary/` plus user-owned `handbook/` and `tech/`), list the unmanaged sibling dirs grouped per parent: `Note: docs/domain/ has 2 unmanaged sibling dirs (handbook/, tech/) — left untouched.`. Use `:` or `;` instead of `—` if the surrounding doc style avoids em-dashes.
- **Throwaway-config reminder (config-driven only).** "Delete or gitignore `exodia.config.yaml`. Re-runs read AGENTS.md, not config."
- **Lazy-migration note (Incremental, pre-feature scaffold).** When Step 1 had to inject the router brackets because they were missing, mention it in one line: "Injected `<!-- exodia:router:start/end -->` markers around the router table for future incremental discovery."
- Next steps for the user (how to iterate: just edit the files; the self-update rules handle growth).
- Reminder: running `/exodia` again triggers incremental re-run, not a fresh scaffold.

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

See `$SKILL_DIR/heuristics/prompt-format.md` for the rules every `AskUserQuestion` call site, Step 7 draft review, Step 4 mapping table, and Step 9 candidate list must follow: question text, option labels, list/table rendering, and multi-section H3 anchoring.
