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

### Step 0a: Load `.exodia.yaml`

If `$TARGET/.exodia.yaml` exists, parse it via `Read` and validate. The file is **authoritative when present**: a populated `structure:` defines the final category set and their on-disk grouping. Absent file = today's flat behavior.

**Schema** (see also `$SKILL_DIR/heuristics/format-strategy.md` § "Layout file"):

```yaml
context_dir: context        # optional; default "context"
structure:
  engineering:
    - architecture
    - patterns
    - debugging
    - operations
    - perf:                 # custom category (map form)
        purpose: "Performance work and benchmarks"
        ledgers:
          - file: bench.jsonl
            schema: bench
            scan_hint: "TODO comments under src/jobs/"
  product:
    - domain
```

Convention: under any key, a list value holds **leaves** (categories), a map value holds **subgroups**. List items are either bare strings (canonical category names) or single-key maps with a custom-category body (`purpose` + optional `ledgers`).

**Validation rules** (all errors fatal at file load; cite the offending rule and stop):

1. `context_dir` (if present) matches `^[a-z._-][a-z0-9._-]*$` and is not `.` or `..`.
2. Every group name and category name (canonical or custom) matches `^[a-z][a-z0-9_-]*$`.
3. The set of group names and the set of category leaf names are disjoint (no name appears as both a group and a leaf).
4. Every leaf appears at most once anywhere in the tree (a category cannot be mirrored across paths).
5. Custom-category map: `purpose` is a non-empty string. `ledgers` is optional; each ledger entry needs `file` and `schema`, `scan_hint` is optional.
6. Tree depth has no hard cap (arbitrary nesting allowed).

**Derived structures** (hold for the rest of the run):

- `$LAYOUT`: ordered map `<leaf-category-name> → <relative-path-under-$CONTEXT_DIR>`. Examples: flat layout maps `architecture → architecture`; nested layout maps `architecture → engineering/architecture`. In flat mode (no file), `$LAYOUT` is empty (sentinel for downstream gates).
- `$CATEGORIES`: ordered list of leaf names from `structure:` (the final category set).
- `$CUSTOM_LEDGERS`: for each custom-category map, capture `(category, file, schema, scan_hint)` tuples. Used in Step 9.
- If `context_dir:` is present in the file, set `$CONTEXT_DIR` to that value and skip Step 3a (collision check still runs).

**Behavior gating** in subsequent steps:

- `$LAYOUT` non-empty: Step 3 set-prompt is skipped; Step 5 passes full relative paths; Step 6 destinations follow `$LAYOUT`; Step 7 H3 anchors use the resolved path; Step 8 path-rewrites rule snippets and table rows; Step 9 resolves canonical keys via `$LAYOUT`; Incremental re-run runs the drift-reconciliation flow.
- `$LAYOUT` empty: every step behaves exactly as before (flat tree, full prompts).

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
- **Incremental**: `$EXISTING_CONTEXT_DIR` is non-empty. Set `$CONTEXT_DIR=$EXISTING_CONTEXT_DIR` and jump to the *Incremental re-run* section at the bottom; do not ask the dir-name question again. If `.exodia.yaml` was loaded in Step 0a and a context tree exists, this is also Incremental: the file may have moved categories since the previous run, and the re-run flow reconciles file vs. on-disk tree.

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

**`.exodia.yaml` shortcut.** If `$LAYOUT` is non-empty (Step 0a loaded a file), skip the proposal flow entirely. The file is authoritative; the leaves of `structure:` are the final category set. Render the resolved set as a confirmation block (no question), shaped like:

```
Layout from .exodia.yaml:
  engineering/
    architecture/
    patterns/
    debugging/
    operations/
    perf/         (custom: "Performance work and benchmarks")
  product/
    domain/
```

Then proceed to Step 3a. Custom categories declared in the file do **not** retrigger the per-category L3 follow-ups below; their `purpose` and `ledgers` are taken verbatim from the file.

The **default** starter set (used only when `$LAYOUT` is empty) is the five canonical categories:

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

Fresh and Merge modes only. Skip in Incremental mode (already detected in Step 1). Also skip the question when `.exodia.yaml` declared `context_dir:` (Step 0a already set `$CONTEXT_DIR`); the collision check below still runs against that value.

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

Run the scaffolder helper. Pass **full relative paths** (under `$CONTEXT_DIR`), not bare category names:

```bash
bash "$SKILL_DIR/scripts/init_structure.sh" "$TARGET" "$CONTEXT_DIR" <space-separated-paths>
```

- `$LAYOUT` empty (flat mode): paths are bare category names, e.g. `architecture patterns domain operations debugging`. Backwards-compatible with previous behavior.
- `$LAYOUT` non-empty: paths are `$LAYOUT[<category>]` for every leaf in `$CATEGORIES`, e.g. `engineering/architecture engineering/patterns engineering/debugging engineering/operations product/domain`.

For each path, `init_structure.sh` creates `$TARGET/$CONTEXT_DIR/<path>/`, looks up the template by the **last segment** (so `engineering/architecture` resolves to `templates/architecture/`), copies `.tmpl` files (writing the `_schema` line into each `.jsonl`), and writes a stub L2 for unknown leaves. YAML stubs ship with their top-level key + a comment block.

### Step 6: Draft L2 content

For each confirmed category, in order (architecture, patterns, domain, operations, debugging, then optional extras):

1. Read `$SKILL_DIR/templates/<category>/<CATEGORY>.md.tmpl` to see the section skeleton and lock the voice (terse, factual, table- and bullet-heavy, inline file citations, no marketing prose). Lookup uses the bare category name (the leaf), independent of where it sits in `$LAYOUT`.
2. Using `$SCAN` (and any merge-seeded content from Step 4), fill each `##` section with a short, factual draft. Cite files. No speculation. Keep each section under ~150 words. For custom categories declared in `.exodia.yaml` with a `purpose:` field, use that string as the seed for section-1 (intro) before any scan-driven prose.
3. Preserve the `<!-- exodia:section:<id> -->` markers; they drive incremental re-runs.
4. **Never duplicate data that already lives in the repo.** Versions, ports, env names, paths, commands, config values, dependency lists, script names; all must be *referenced*, not copied. Write `see \`package.json\` \`engines.node\`` or `defined in \`.env.example\``, never the literal value. Duplicated data rots; pointers survive edits.
5. **`## L3 Data` section.** When the L2 template has a `<!-- exodia:section:l3 -->` block, list the L3 files that ship with the module. For custom categories with no template, draft this section from the L3 ledgers requested in Step 3 (or declared in `.exodia.yaml` for layout-mode customs), picking formats per `$SKILL_DIR/heuristics/format-strategy.md`. Each line: `` - `<file>`: <one-line purpose>. ``
6. **Destination path.** The file is written to `$TARGET/$CONTEXT_DIR/<destination>/<CATEGORY>.md` where `<destination>` = `$LAYOUT[<category>]` if `$LAYOUT` is non-empty, else the bare category name (flat mode).

Do **not** write the file to disk yet. Hold the draft in memory.

### Step 7: Section-by-section review

Walk each L2 draft with the user. For each `##` section:

- Show the drafted prose.
- Render the draft inside a fenced markdown block, prefaced by an H3 anchor: `### \`<destination>/<CATEGORY>.md\` § <section-id>`, where `<destination>` is the resolved path (`$LAYOUT[<category>]` if non-empty, else the bare category name). Example: `### \`engineering/architecture/ARCHITECTURE.md\` § overview`.
- Then `AskUserQuestion`:
  - **Question**: "Accept this section?"
  - **Options**: "Accept", "Edit", "Skip" (leave empty for later).
- If edit: let the user dictate changes, re-draft (still inside the fenced block), loop until accepted.

Then `Write` the finalized L2 file to `$TARGET/$CONTEXT_DIR/<destination>/<CATEGORY>.md` (see Step 6 § 6 for destination resolution).

### Step 8: Emit the AGENTS.md router

Compose `$TARGET/AGENTS.md` from:

- `$SKILL_DIR/rules/universal.md` (always included)
- `$SKILL_DIR/rules/conditional/operations-awareness.md` *only if `operations/` is in the final category set*
- `$SKILL_DIR/rules/conditional/lint-check.md` if scan detected any lint/test/typecheck scripts; substitute the detected commands into the snippet
- `$SKILL_DIR/rules/self-update.md` (always, near the top). When composing the Self-Update Rules block, drop table rows whose target path is not in the final category set. This applies to both core and optional rows (e.g. drop the `operations/variants.yaml` row if `operations/` was dropped, drop the `domain/glossary.yaml` row if `domain/` was dropped, drop both `infra/*` rows if `infra/` was dropped). The `File Format Strategy` § at the bottom of `self-update.md` is always retained; it guides future agents adding new ledgers.

Follow the shape in `$SKILL_DIR/templates/AGENTS.md.tmpl`:

1. Project overview (one paragraph from scan)
2. Commands (point to the detected package manifest file)
3. Context Router table (one row per confirmed category, linking to `$CONTEXT_DIR/<destination>/<CATEGORY>.md` where `<destination>` is the path resolved via `$LAYOUT`)
4. Behavioral Rules (universal + conditional)
5. Self-Update Rules (full block)
6. Quick Action Table (common dev phrases → file to read, using resolved paths)
7. Context Structure (tree diagram, rooted at `$CONTEXT_DIR/`, rendered dynamically from `$LAYOUT`)

**Substitution order.** Apply these passes in order before writing the emitted `AGENTS.md`. Each pass operates on the already-composed text from the previous pass:

1. **Path-rewrite pass on self-update table.** After dropping rows whose category is not in the final set, walk each retained row and rewrite the **target-file** column. The retained-row target cell starts with `<category>/...`; if `$LAYOUT` is non-empty, replace the leading `<category>/` with `$LAYOUT[<category>]/`. In flat mode (`$LAYOUT` empty), leave the cell unchanged. The phrase "All target-file paths below are relative to the context directory (`{{CONTEXT_DIR}}/`)" in `self-update.md` stays accurate either way.
2. **`{{PATH_OF_<CATEGORY>}}` substitution.** For each leaf in `$CATEGORIES`, compose `{{PATH_OF_<UPPER>}}` where `<UPPER>` is the category name uppercased and dashes/underscores stripped (e.g. `patterns → PATTERNS`, `operations → OPERATIONS`, `mobile → MOBILE`). Replace each occurrence with `{{CONTEXT_DIR}}/<resolved-path>` where `<resolved-path>` = `$LAYOUT[<category>]` if non-empty, else the bare category name. This generalizes any future rule snippet that uses the convention.
3. **`{{CONTEXT_TREE}}` rendering.** Render the tree from `$LAYOUT` rather than from a baked literal. Walk the nested `structure:` (or the flat list in flat mode); for each leaf, list every L3 file shipped by the matching template directory (read `templates/<leaf>/` or `templates/optional/<leaf>/`, plus any custom-category ledgers from `$CUSTOM_LEDGERS`). Indent groups two spaces per level.
4. **`{{ROUTER_ROWS}}` and `{{QUICK_ACTION_ROWS}}`.** Each row's `Load` cell uses the resolved path: `Read \`<resolved-path>/<CATEGORY>.md\``. Quick-action rows get the same treatment for any cell pointing at a category file.
5. **`{{CONTEXT_DIR}}` substitution.** Last pass: replace every remaining `{{CONTEXT_DIR}}` token with the actual value of `$CONTEXT_DIR`.

### Step 9: L3 seeding prompt

For each L3 file in the final category set, apply the matching seed clause below. Skip any clause whose target file does not exist (the user may have dropped that category in Step 3, or the file may live under a nested layout path). JSONL clauses scan candidates and let the user approve a subset via `AskUserQuestion`; YAML clauses propose a skeleton (named keys with empty body fields) for the user to accept, edit, or skip.

The lookup tables below use **canonical** keys (e.g. `architecture/decisions.jsonl`). Resolve each key via `$LAYOUT` before reading or writing: the on-disk path is `$TARGET/$CONTEXT_DIR/<resolved-path>/<file>` where `<resolved-path>` = `$LAYOUT[<category>]` if non-empty, else the bare category name. In flat mode the canonical key is the on-disk path verbatim.

Append JSONL entries using the canonical ID format `{type}_{YYYYMMDD}_{HHMMSS}_{4hex}`. The `{type}` prefix is the target file's `_schema` value, verbatim (read the first line of the `.jsonl`). See `$SKILL_DIR/heuristics/format-strategy.md` § ID format.

**JSONL clauses.** One row per shipped `.jsonl`. Run only if the file exists.

| File | `_schema` | Scan source |
|---|---|---|
| `architecture/decisions.jsonl` | `adr` | `docs/adr/`, `docs/decisions/`, `ARCHITECTURE.md` headings with decision language |
| `patterns/reviews.jsonl` | `rv` | ESLint/Biome custom rules, `@deprecated` JSDoc / Python `DeprecationWarning`, CHANGELOG sections matching `BREAKING` / `Deprecated` |
| `debugging/gotchas.jsonl` | `gotcha` | `TODO`, `FIXME`, `HACK`, `XXX`, `WARNING` comments grouped by directory/area |
| `debugging/playbooks.jsonl` | `pb` | `docs/postmortems/`, `POSTMORTEM*.md`, rich `^fix:` commits (commit body longer than ~200 chars) |
| `infra/decisions.jsonl` | `adr` | infra-scoped commits in `terraform/`, `helm/`, `k8s/`; `infra/CHANGES.md` |
| `infra/runbooks.jsonl` | `rb` | `RUNBOOK*.md`, `docs/runbooks/`, `ops/`, `runbooks/` |
| `data/experiments.jsonl` | `exp` | `experiments/`, `notebooks/`, `runs/` directories; `RESULTS.md` |
| `mobile/gotchas.jsonl` | `mgotcha` | TODO/FIXME inside `ios/`, `android/`, `*.swift`, `*.kt`; tag each entry `platform: ios | android | both` |
| `mobile/releases.jsonl` | `mrel` | store-config files, `fastlane/` metadata, git tags matching version patterns |
| `workspace/migrations.jsonl` | `wsmig` | git log touching `pnpm-workspace.yaml`, `turbo.json`, `nx.json`, `lerna.json`, root `package.json` `workspaces` field |

For each JSONL clause: run the scan, render the candidate list per `$SKILL_DIR/heuristics/prompt-format.md`, then `AskUserQuestion` to approve a subset. Append approved entries with canonical IDs.

**YAML clauses (skeleton-from-scan).** Run only if the file exists.

| File | Skeleton source | Skeleton shape |
|---|---|---|
| `domain/glossary.yaml` | `$SCAN` §3 (top-level entities / models named in the repo) | `entities:` map, one key per entity, body `definition: ""` and `relationship: "see <file>"` |
| `operations/variants.yaml` | i18n locales, env files, feature-flag tool from `$SCAN` §4 | `variants:` map with a `default:` key and one key per detected variant, each body `notes: ""` |
| `data/datasets.yaml` | DB migrations, schema files, contents of `data/` | `datasets:` map, one key per dataset, body `source: "<file>"`, `schema: ""`, `refresh: ""`, `notes: ""` |

For each YAML clause: render the proposed skeleton inside a fenced ` ```yaml ` block prefaced by `### \`<file>\` § skeleton`, then `AskUserQuestion`:

- **Question**: "Accept this skeleton?"
- **Options**: "Accept", "Edit", "Skip" (leave the existing empty stub).

On accept or after edit, overwrite the YAML stub with the populated skeleton.

**Custom L3 clause.** Iterate every user-declared custom ledger from either source: (a) Step 3 interactive declarations (flat mode), (b) `$CUSTOM_LEDGERS` parsed from `.exodia.yaml` in Step 0a. Each ledger carries `(category, file, schema, scan_hint)`. Resolve the on-disk path via `$LAYOUT`: `$TARGET/$CONTEXT_DIR/$LAYOUT[<category>]/<file>` (or `<category>/<file>` in flat mode). If `scan_hint` is non-empty, run it as a Bash/Explore query, present candidates the same way as built-in JSONL clauses, and append approved entries using the ledger's own `schema` value as the ID prefix. If the hint is "none" or absent, skip seeding for that ledger.

### Step 10: Wrap up

Print a short summary:

- What was created (counts: L2 files, L3 files)
- Next steps for the user (how to iterate: just edit the files; the self-update rules handle growth)
- Reminder: running `/exodia` again triggers incremental re-run, not a fresh scaffold

---

## Incremental re-run

When preflight detects an existing exodia setup:

0. Trust the `$CONTEXT_DIR` already detected in Step 1. Do not ask the user to rename it; preserving the existing directory name keeps router paths consistent. If `.exodia.yaml` declared a different `context_dir:`, the file wins for the *target* layout but the existing tree is reconciled against it (see step 2 below).
1. Re-run Step 2 (scan).
2. **Layout reconciliation** (`.exodia.yaml` present + tree exists). The file wins; the on-disk tree is migrated to match. Walk it as follows:
   1. Step 0a already loaded and validated the file.
   2. Walk `$TARGET/$CONTEXT_DIR/`. For each L2 file matching `<UPPER>.md` carrying `<!-- exodia:section:` markers, record `<lowercase-leaf> → <found-relative-path>` into `$ON_DISK`.
   3. Compute three sets:
      - **Moves**: leaves present in both `$LAYOUT` and `$ON_DISK` with different paths. For each: render a fenced ` ```diff ` block showing old → new path, then `AskUserQuestion`:
        - **Question**: "Apply this move?"
        - **Options**: "Apply move", "Skip".
        - On accept, run `git mv "$TARGET/$CONTEXT_DIR/<old>" "$TARGET/$CONTEXT_DIR/<new>"` if `$TARGET` is a git repo; otherwise `mv -n` (no overwrite). Create parent dirs first if needed.
      - **New**: leaves in `$LAYOUT` but not in `$ON_DISK`. Scaffold each by invoking `init_structure.sh` with **just the new path(s)** — existing paths are left untouched (the script skips destinations that already exist).
      - **Orphans**: leaves on disk not in `$LAYOUT` (or directories with `<!-- exodia:section:` markers under no recognized leaf). For each, `AskUserQuestion`:
        - **Question**: "Orphan `<path>` not in `.exodia.yaml`. How to proceed?"
        - **Options**: "Keep in place", "Move to root", "Delete".
        - "Move to root": `git mv "$TARGET/$CONTEXT_DIR/<path>" "$TARGET/$CONTEXT_DIR/<leaf>"` (or `mv -n`).
        - "Delete": **second-step confirmation required** before destructive action. Render the path and contained file count, then a second `AskUserQuestion` with options "Confirm delete", "Cancel". Only on "Confirm delete" run `rm -rf` on the directory.
   4. After path reconciliation, refresh `$ON_DISK` (paths may have moved) and continue.
3. For each L2 file under `$TARGET/$CONTEXT_DIR/<resolved-path>/`, read it and locate `<!-- exodia:section:<id> -->` markers. Fresh-draft *new* facts from the scan. Diff against existing auto-filled content.
4. Propose updates only to sections where the auto-filled block has not been user-edited (detect with the section-id marker; if the content after the marker differs from a reconstructible baseline, treat it as user-edited and do not touch).
5. Render each proposed diff as a fenced ` ```diff ` code block, prefaced by `### \`<resolved-path>/<file>\` § <section-id>`. Then per section, `AskUserQuestion`:
   - **Question**: "Apply this update?"
   - **Options**: "Accept", "Skip".
6. Append to L3 files from the scan using the same Step 9 logic (canonical keys resolved via `$LAYOUT`).
7. **Re-emit `AGENTS.md`** if `$LAYOUT` differs from the previous on-disk tree (paths moved, leaves added/removed, or `context_dir` changed). The router-path columns must reflect the current layout. In flat mode with no layout change, retain the previous behavior: do not overwrite `AGENTS.md`; only add missing rule snippets if conditions now apply (e.g. an `operations/` category added after initial scaffold).

---

## Failure modes to watch

See `$SKILL_DIR/TROUBLESHOOTING.md` for handling: user aborts mid-interview, Explore scan timeouts, secrets in the target repo, missing git/agent/lint toolchain.

---

## User-facing prompt format

See `$SKILL_DIR/heuristics/prompt-format.md` for the rules every `AskUserQuestion` call site, Step 7 draft review, Step 4 mapping table, and Step 9 candidate list must follow: question text, option labels, list/table rendering, and multi-section H3 anchoring.
