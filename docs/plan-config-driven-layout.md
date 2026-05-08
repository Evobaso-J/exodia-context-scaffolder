# Plan: config-driven layout customization for `/exodia`

Status: design locked, ready to implement. Handoff document for the implementing agent.

## Problem

Today `/exodia` scaffolds canonical 5 categories (`architecture`, `patterns`, `domain`, `operations`, `debugging`) under a single top-level `$CONTEXT_DIR` (default `context/`). Path validation regex `^[a-z._-][a-z0-9._-]*$` rejects slashes; every category lives directly under that one root.

Real-world repos need richer layouts. Concrete trigger: a target repo wants the canonical set under `docs/project/` *and* a `glossary` category at `docs/domain/glossary/` (sibling-level dirs `docs/domain/handbook/`, `docs/domain/tech/` are user-owned and must remain untouched). Today's scaffolder cannot express this.

Goal: let users describe arbitrary per-category paths via an opt-in throwaway config file, while keeping the default flow (no config) unchanged.

## Design decisions (locked)

Each row records a question that was grilled and the locked answer.

| # | Decision | Locked |
|---|---|---|
| Q1 | Customization mechanism | Generic config file (not company preset) |
| Q2 | Layout shape | Per-category path mapping (no "roots" abstraction) |
| Q3 | Category internal shape | Unchanged: folder + L2.md + L3 ledgers. Polymorphic kinds (multi-file L2, L3-only) deferred to a separate workflow |
| Q4 | When config consumed | Hybrid: config present → drive layout. Absent → today's interactive flow. Config is throwaway, one-shot, consumed only at first run |
| Q5 | Persistent layout manifest after config consumed | AGENTS.md router table, wrapped in `<!-- exodia:router:start -->` / `<!-- exodia:router:end -->` markers. Sole truth on incremental re-runs |
| Q6 | Config schema style | Sparse + defaults. Config encodes only the diff from canonical layout |
| Q7 | L3-only categories (no L2 .md) | Deferred (image not authoritative for file shapes) |
| Q8 | Scan-driven recommendations on top of config | Hybrid (Q8-D): scan still runs; for detected categories not in config and not dropped, prompt user to add. L2/L3 content drafted silently inside declared categories |
| Q9 | Path semantics | Repo-rooted absolute. Regex `^[a-z._-][a-z0-9._/-]*$`. No `..`, no leading `/`, no trailing `/` |
| Q10 | Collision rules | B+C. Per-target-path strict (only target itself checked, parent siblings ignored) + sibling notice in preflight summary + overlap detection (reject two categories sharing path or in prefix relation) |
| Q11 | Config filename + location | `exodia.config.yaml` at repo root |
| Q12 | L3 ledger declaration | Optional in config. If `l3: [filename, ...]` present, use those filenames; schema inferred from filename (canonical-name lookup). If absent, model infers both filenames and schemas in Step 6 |
| Q13 | L3 inference flow when config silent | Pure model inference (Q13-B), surfaced inline during Step 6 drafting and reviewed in Step 7 |
| Q14 | Merge mode + config interaction | Config-A. Config wins on layout. `parse_existing.py` extracts headings; section-map.md routes to config-declared category set. Unmappable headings → `_unsorted` |
| Q15 | Self-update rules with arbitrary paths | A+C. Bake resolved paths at scaffold time via `{{path:<ledger>}}` placeholders; drop rows for absent ledgers. Custom-category rows generated on-the-fly |

## Final design summary

### Trigger and scope

- Optional `exodia.config.yaml` at repo root.
- Present → layout-driven scaffold.
- Absent → today's interactive flow unchanged (no regression).
- Consumed exactly once at first run (Fresh OR Merge mode). Incremental re-runs ignore config entirely.
- Sole persistent source of truth post-scaffold = AGENTS.md router table inside bracket markers.

### Schema

```yaml
context_dir: docs/project          # default root for canonical categories without explicit `path`
categories:
  domain:    { drop: true }        # remove canonical category
  operations: { drop: true }
  glossary:                        # custom category (name not in canonical set)
    path: docs/domain/glossary     # repo-rooted, escapes context_dir
    custom: true
    l3: [glossary.yaml]            # OPTIONAL. Filenames only; schema inferred from name
```

Field reference:

- `context_dir` (string, optional, default `context`): default prefix for canonical categories that omit `path`.
- `categories` (map, optional): keyed by category name.
  - `path` (string, optional): repo-rooted path. If omitted for a canonical category, defaults to `<context_dir>/<name>`.
  - `drop` (bool, optional, default `false`): exclude canonical category. Mutually exclusive with `path`/`custom`/`l3`.
  - `custom` (bool, optional, default `false`): required for non-canonical names. Signals "this is novel; model drafts L2 + infers L3 if `l3:` absent".
  - `l3` (list of strings, optional): override model's L3 inference. Each entry is a filename matching `^[a-z][a-z0-9_-]*\.(yaml|jsonl)$`. Schema for each inferred from filename via canonical-name lookup.

Validation rules (rejected at parse time):

1. `path` matches `^[a-z._-][a-z0-9._/-]*$`, no `..`, no leading `/`, no trailing `/`.
2. No two categories share `path`.
3. No category path is prefix of another's path.
4. Custom category (non-canonical name) without `custom: true` → reject with helpful error.
5. `drop: true` combined with any other field → reject.
6. `l3` filename regex above; reject unknown extensions.

### Behavioral effects

Step-by-step deltas vs. current `SKILL.md` protocol:

- **Step 0**: also resolve `$CONFIG_PATH` = `$TARGET/exodia.config.yaml` if present.
- **Step 1 (preflight)**: if `$CONFIG_PATH` present, parse + validate before mode classification. On validation error, abort with line-numbered errors. Mode classification unchanged otherwise.
- **Step 1 (incremental discovery)**: parse AGENTS.md router region between bracket markers for category→path map. If markers absent (older scaffold pre-feature), fall back to today's marker grep + lazy-add bracket markers on next emit.
- **Step 2 (scan)**: unchanged.
- **Step 3 (categories)**: when config present, skip the category-set proposal. Run detector heuristics; for each detected optional category not in config and not dropped, AskUserQuestion to add. Accepted categories merged into resolved layout map.
- **Step 3a (dir name)**: when config present, skip entirely. Paths come from config.
- **Step 4 (Merge mode)**: parse existing AGENTS.md/CLAUDE.md, route headings via `section-map.md` against the config-declared category set (canonical + custom). Unmappable headings → `_unsorted`. Same confirmation table flow.
- **Step 5 (init structure)**: pass resolved `name=path` pairs to refactored `init_structure.sh`.
- **Step 6 (L2 drafts)**: for custom categories without templates, model drafts L2 sections from category name + scan signals + optional purpose hint. For categories with `l3:` in config, draft around those filenames (resolve schemas via canonical-name lookup; novel filenames → model writes schema). For categories without `l3:`, model proposes both filenames and schemas.
- **Step 7 (review)**: unchanged shape. Operates over expanded category set.
- **Step 8 (router emit)**:
  - Wrap `## Context Router` table in `<!-- exodia:router:start -->` / `<!-- exodia:router:end -->`.
  - Resolve all `{{path:<ledger>}}` placeholders in `rules/self-update.md` against the layout map.
  - Drop self-update rows whose ledger is not in the final set.
  - Append rows for custom-category ledgers (rule body reused from canonical schema if name matches; model-written one-liner otherwise).
  - Render `## Context Structure` tree grouped by common path prefix (so multi-root layouts read cleanly).
- **Step 9 (L3 seeding)**: extend the seed table with custom ledgers using the inferred schema and scan-source determined in Step 6.
- **Step 10 (wrap-up)**: print sibling-notice summary (any unmanaged dirs at parents shared with managed paths). Remind user `exodia.config.yaml` is throwaway and may be deleted or `.gitignore`-d.

## Implementation phases

### Phase 1: Config infrastructure

1. **Schema documentation.** Add a `## Config` section to `SKILL.md` (or a dedicated `docs/config-schema.md` referenced from SKILL.md) covering the schema above, validation rules, and worked examples. The headline example is the weroad case (`docs/project` + `docs/domain/glossary`).
2. **`scripts/parse_config.py`.** Reads `exodia.config.yaml`, validates per the rules above (regex, overlap detection per Q10-C, drop-vs-other mutual exclusion). Emits JSON of shape:

   ```json
   {
     "context_dir": "docs/project",
     "categories": [
       {"name": "architecture", "path": "docs/project/architecture", "kind": "canonical", "l3_override": null, "drop": false},
       {"name": "domain", "path": null, "kind": "canonical", "l3_override": null, "drop": true},
       {"name": "glossary", "path": "docs/domain/glossary", "kind": "custom", "l3_override": ["glossary.yaml"], "drop": false}
     ]
   }
   ```

   On validation failure, exit non-zero with line-numbered errors on stderr. Use stdlib only (`yaml` via `pyyaml` is acceptable since other helper scripts already use Python 3; verify `pyyaml` availability and document the dep).

3. **`scripts/resolve_layout.py`.** Merges parsed config with canonical defaults. Output: ordered list `[{name, path, kind: canonical|custom, l2_template_path, l3_specs}]`. `l3_specs` is `null` when config is silent and model must infer; populated when config provides `l3:` (each entry is `{filename, schema_name_or_null, schema_template_path_or_null}` post canonical-name lookup). This is the single layout map every downstream step consumes.

### Phase 2: Step protocol modifications

Edit `SKILL.md` to add the conditional branches described in the "Behavioral effects" section above. Keep the no-config flow byte-identical to today; all new logic gated on `$CONFIG_PATH` presence.

4. Update **Step 0** to set `$CONFIG_PATH`.
5. Update **Step 1** preflight + incremental-discovery logic (parse router-region brackets first, fall back to marker grep).
6. Update **Step 3 / 3a** with skip conditions and scan-recommendation flow.
7. Update **Step 4** Merge-mode wording to use config-declared category set when config present.

### Phase 3: Scaffold writers

8. **`scripts/init_structure.sh` refactor.** Change signature from `init_structure.sh <target> <context_dir> <category...>` to `init_structure.sh <target> <name=path>...`. Each pair creates the path with `mkdir -p`, copies templates by canonical name (skip if no template dir for the canonical name → empty L2 stub for custom). Existing destination files left untouched (today's behavior preserved). Update Step 5 invocation.
9. **Step 6 drafting (model logic).** For each category in the resolved map:
   - Canonical with template: read template, draft per current rules.
   - Custom or template-less: model invents L2 sections (default skeleton: `## Purpose`, `## Key Files`, `## L3 Data`, plus extras model deems appropriate from scan).
   - L3 specs:
     - `l3_specs` populated → write headers with those filenames; resolve schema by canonical-name lookup, else propose schema body inline.
     - `l3_specs` null → model proposes filenames + schemas inline (Q13-B).
   - Both surface in Step 7 review.

### Phase 4: Router + rules emission

10. **`templates/AGENTS.md.tmpl` update.** Add `<!-- exodia:router:start -->` and `<!-- exodia:router:end -->` markers around the router table. Document them as exodia-managed; user-edited content outside the markers preserved across re-runs.
11. **`rules/self-update.md` rewrite.** Replace literal paths with `{{path:<ledger_canonical_name>}}` placeholders. Examples: `domain/glossary.yaml` → `{{path:glossary}}`. The placeholder key is the ledger's canonical name (e.g. `glossary`, `variants`, `decisions`, `gotchas`, `playbooks`, `reviews`, `runbooks`, `experiments`, `datasets`, `mgotcha`, `mrel`, `wsmig`).
12. **Step 8 emit logic.**
    - Build map `ledger_canonical_name → resolved_full_path` from layout map + each category's L3 specs.
    - Substitute every `{{path:<key>}}` in the composed AGENTS.md against the map. Unresolved keys → drop the containing table row (today's drop-row behavior, generalized).
    - Append generated rows for custom-category ledgers: if the ledger's schema is a known canonical name, reuse the canonical row's "When to update" prose (look up by schema in the original `self-update.md`); else generate one line from the category purpose using the model.
    - Render `## Context Structure` tree by grouping resolved paths by longest common prefix per group.

### Phase 5: Step 9 + cleanup

13. **Step 9 L3 seeding.** Extend the seed table with rows for custom ledgers. For each custom ledger:
    - If schema canonical-name lookup succeeded, reuse the canonical scan-source from the existing Step 9 table.
    - Else use the scan source the model proposed in Step 6 (carried through the layout map).
14. **Step 10 wrap-up.** Print:
    - Counts (L2 files, L3 files).
    - Sibling-notice summary (unmanaged dirs detected at any parent shared with a managed path).
    - One-line reminder: "Delete or gitignore `exodia.config.yaml`. Re-runs read AGENTS.md, not config."

### Phase 6: Tests + docs

15. **Fixture configs** under `tests/fixtures/configs/`:
    - `weroad.yaml` (the headline image case).
    - `drop-only.yaml` (drop two canonicals, no customs).
    - `custom-only.yaml` (no canonicals, two customs).
    - `invalid-overlap.yaml` (two categories share path).
    - `invalid-prefix.yaml` (one path is prefix of another).
    - `invalid-traversal.yaml` (`..` in path).
    - `invalid-regex.yaml` (uppercase/special chars).
16. **Validation harness.** Tiny Python or bash harness that runs `parse_config.py` against each fixture and asserts exit code + error pattern.
17. **README + TROUBLESHOOTING updates.** New section "Customizing the layout" with the weroad example. Update TROUBLESHOOTING with config validation errors, the "config ignored on incremental re-run" gotcha, and the lazy-migration behavior for old trees lacking router brackets.
18. **CHANGELOG.** Add `## Unreleased` entry under `### Features`. release-please will pick up on next release.

## Open implementation-only items

These have no design impact; resolve during implementation.

- **Canonical schema-name registry.** Currently implicit in `templates/<canonical-cat>/<schema>.{yaml,jsonl}.tmpl`. Document the lookup order for filename-to-schema resolution (e.g. iterate canonical categories, first match wins). Edge case: schema name collision (e.g. multiple canonical categories ship `decisions.jsonl`)? Currently `architecture/decisions.jsonl` and `infra/decisions.jsonl` both use schema `adr`. Define a tiebreaker: prefer the canonical category whose name matches the L2 the ledger lives next to; else first-match.
- **Sibling-notice phrasing.** Decide whether the preflight summary is one-line per sibling or grouped per parent dir. Suggested: grouped, e.g. `Note: docs/domain/ has 2 unmanaged sibling dirs (handbook/, tech/) — left untouched.`
- **Lazy-migration UX.** When incremental re-run finds an old tree without router brackets, do we (a) silently inject markers and proceed, or (b) prompt user once? Suggested: silent + one-line note in wrap-up, since the marker injection is non-destructive to user content.
- **Custom-category L2 template stub.** For template-less customs, agree on a default section skeleton (suggestion: `## Purpose`, `## Key Files`, `## L3 Data`). Embed in `init_structure.sh` so custom L2 files are not literally empty.
- **Config presence + Incremental mode warning.** If user accidentally re-runs `/exodia` after first scaffold with `exodia.config.yaml` still present, scaffolder ignores it per design but should print a one-line warning ("Config detected but tree exists; ignoring. Delete the file to silence this warning.").

## Out of scope (defer)

- Polymorphic category shapes (multi-file L2, L3-only categories, file-only categories). Image's `rules/{code-style.md, testing.md, ...}` and `design-patterns/{auth.md, api.md}` weirdness deferred to a separate workflow per user direction.
- Auto-emitting an `exodia.config.yaml` from interactive runs (config is consumer-only; interactive flow does not produce one).
- Schema versioning of `exodia.config.yaml` (no `version:` field for now; throwaway nature limits compat burden).
- Multiple-roots abstraction (Q2-B). Per-category path is enough.

## Acceptance criteria

The feature is done when:

1. `exodia.config.yaml` matching the headline weroad shape produces:
   - `docs/project/architecture/ARCHITECTURE.md` + `decisions.jsonl`.
   - `docs/project/patterns/PATTERNS.md` + `reviews.jsonl`.
   - `docs/project/debugging/DEBUGGING.md` + `gotchas.jsonl` + `playbooks.jsonl`.
   - `docs/domain/glossary/GLOSSARY.md` + `glossary.yaml`.
   - No `docs/project/domain/`, no `docs/project/operations/`.
   - `docs/domain/handbook/` and `docs/domain/tech/` untouched.
   - `AGENTS.md` at repo root with router region in bracket markers, listing the four resolved paths.
   - `rules/self-update.md` content baked into AGENTS.md with all `{{path:...}}` placeholders resolved.
2. Running `/exodia` with no config in a fresh repo produces today's behavior byte-identically.
3. Running `/exodia` a second time on a config-scaffolded repo (config still present or deleted) is incremental: ignores config, parses router region, only updates auto-filled L2 sections per today's incremental rules.
4. All seven invalid-config fixtures fail parse with line-numbered errors.
5. Overlap detection rejects nested category paths (`docs/project` + `docs/project/architecture` as two declared categories) with a clear message.
6. Sibling-notice summary appears in wrap-up when managed paths share a parent with unmanaged content.
