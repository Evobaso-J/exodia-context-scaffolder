# `exodia.config.yaml` reference

`exodia.config.yaml` is an **opt-in, one-shot, throwaway** config file you drop at the repo root *before* the first `/exodia` run to override the canonical layout. Opt-in (absent means the interactive flow runs unchanged); one-shot (consumed only on the first Fresh / Merge run, ignored by Incremental re-runs); throwaway (the `AGENTS.md` router table wrapped in `<!-- exodia:router:start -->` / `<!-- exodia:router:end -->` becomes the sole persistent source of truth, so the config file can be deleted or `.gitignore`d once the scaffolded tree is committed). Sparse by default: encode only the diff from the canonical layout.

## Schema

```yaml
context_dir: docs/project          # default root for canonical categories without explicit path
categories:
  operations: { drop: true }       # remove canonical category
  releases:                        # custom category (name not in canonical set)
    path: docs/releases            # repo-rooted, may escape context_dir
    custom: true
    description: "Release notes per published version"  # optional; one-line purpose passed to the model
    l3: [release_notes.jsonl]      # optional; filenames only, model writes schema when filename not in canonical ledger registry
```

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `context_dir` | string | `context` | Default prefix for canonical categories that omit `path`. |
| `categories` | map | `{}` | Map keyed by category name. |
| `categories.<name>.path` | string | `<context_dir>/<name>` | Repo-rooted path. Required for custom categories outside `context_dir`. |
| `categories.<name>.drop` | bool | `false` | Exclude a canonical category. Mutually exclusive with `path` / `custom` / `l3` / `description`. |
| `categories.<name>.custom` | bool | `false` | Required for non-canonical names. Signals "model drafts L2 + infers L3 if `l3:` absent". |
| `categories.<name>.description` | string | absent | Optional one-line purpose (single line, &le;200 chars). Passed to the model as `{purpose}` when drafting the L2 `## Purpose` section and inferring custom L3 schemas / scan hints. Most useful for custom categories whose intent is not obvious from the name. |
| `categories.<name>.l3` | list[string] | absent | Override model's L3 inference. Each entry is a filename matching `^[a-z][a-z0-9_-]*(?:/[a-z][a-z0-9_-]*)*\.(yaml\|jsonl\|md)$`. Filenames may include `/` to nest under the host category path (e.g. `style/imports.md`); each `/`-separated segment must independently match `[a-z][a-z0-9_-]*`, which blocks leading/trailing slashes, empty segments, and `..` by construction. For `.yaml` / `.jsonl`, schema is inferred via canonical-name lookup when the filename matches a known ledger; otherwise the model writes the schema. Nested entries always fall through to model-derived schema (canonical lookup is keyed on the flat filename). For `.md`, the entry is a standalone markdown deep-dive (no schema, no ledger semantics): Step 6 drafts prose alongside the L2; Step 9 skips it. |

## Canonical category names

Recognized as canonical (no `custom: true` required):

`architecture`, `design-patterns`, `glossary`, `operations`, `debugging`.

Any other name in `categories` requires `custom: true` or it is rejected at parse time. Cross-repo consistency for non-core categories (e.g. sharing the same `mobile` / `infra` shape across several services) is a user responsibility: share an `exodia.config.yaml` snippet between repos.

## Path semantics

- Repo-rooted absolute (relative to `$TARGET`).
- Regex: `^[a-z._-][a-z0-9._/-]*$`.
- No `..` segments, no leading `/`, no trailing `/`.
- Two categories may not share a path.
- One category's path may not be a strict prefix of another's.

## Validation rules

`scripts/parse_config.py` rejects (with line-numbered errors on stderr, exit 65):

1. Path violates the regex above or contains `..` / leading `/` / trailing `/`.
2. Two categories share `path`.
3. One category's `path` is a prefix of another's.
4. Non-canonical name without `custom: true`.
5. `drop: true` combined with any other field.
6. `l3` filename with an extension other than `.yaml`, `.jsonl`, or `.md`, or with a segment that does not match `[a-z][a-z0-9_-]*` (this blocks leading `/`, trailing `/`, empty segments like `//`, and `..`).
7. `description` that is empty, multiline, or longer than 200 characters.
8. Two `l3:` entries in the same category share an identical filename.

## `.md` L3 entries

`.md` filenames in `l3:` declare standalone markdown deep-dives, not ledgers. They carry no `_schema` header, no ID format, no append-only contract, and no Step 9 scan-seeding. The scaffolder treats them as a parallel mechanism to `design-patterns/docs/<slug>.md` deep dives, but located in the host category's path and registered explicitly via `l3:`. Step 6 (`protocol/06-draft-l2.md` § "Markdown L3 deep-dives") drafts each `.md` body interactively, wraps it in a single `<!-- exodia:section:body -->` marker, and writes it to `<host_path>/<filename>`. Nested filenames write to `<host_path>/<segments>/<basename>`; the scaffolder creates intermediate directories at write time. H1 heading derivation uses `basename(<filename>)` only, ignoring intermediate segments.

Use `.md` L3 entries for: per-area rule docs, glossary deep-dives, runbooks, anything prose-shaped that does not fit jsonl/yaml. For appendable logs (decisions, incidents) prefer `.jsonl`; for fixed structured trees (term registries, variant maps) prefer `.yaml`.

## Worked example: monorepo with `docs/project/` canonical set and a sibling handbook

```yaml
context_dir: docs/project
categories:
  glossary:
    path: docs/handbook/glossary    # canonical category relocated outside context_dir
  debugging: { drop: true }         # not needed for this repo
  mobile:                           # custom category
    path: docs/mobile
    custom: true
    l3: [device_quirks.jsonl, release_train.yaml, quirks/ios.md]
```

Copy-pasteable: [`../examples/exodia.config.yaml`](../examples/exodia.config.yaml). Smallest override: [`../examples/exodia.config.minimal.yaml`](../examples/exodia.config.minimal.yaml).

This produces:

- `docs/project/architecture/` (canonical, default path under `context_dir`)
- `docs/project/design-patterns/` (canonical, default path under `context_dir`)
- `docs/project/operations/` (canonical, default path under `context_dir`)
- `docs/handbook/glossary/` (canonical, explicit path)
- `docs/mobile/` (custom, model drafts L2 and writes schemas for the two declared ledgers plus a nested `quirks/ios.md` prose deep-dive at `docs/mobile/quirks/ios.md`)
