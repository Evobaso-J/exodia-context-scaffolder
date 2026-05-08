# `exodia.config.yaml` schema

Optional throwaway config file at the target repo root. Drives layout customization for `/exodia` when the default 5-categories-under-one-root shape is not enough.

- **Opt-in.** Absent → today's interactive flow runs unchanged.
- **One-shot.** Consumed exactly once at the first scaffold run (Fresh or Merge mode). Incremental re-runs ignore it.
- **Throwaway.** After the first run, the AGENTS.md router table (wrapped in `<!-- exodia:router:start -->` / `<!-- exodia:router:end -->`) is the sole persistent source of truth. Delete or `.gitignore` the file once you have committed the scaffolded tree.
- **Sparse + defaults.** Encode only the diff from the canonical layout. Anything you do not declare keeps its default.

## Schema

```yaml
context_dir: docs/project          # default root for canonical categories without explicit path
categories:
  domain:    { drop: true }        # remove canonical category
  operations: { drop: true }
  glossary:                        # custom category (name not in canonical set)
    path: docs/domain/glossary     # repo-rooted, may escape context_dir
    custom: true
    l3: [glossary.yaml]            # optional; filenames only, schema inferred from name
```

### Field reference

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `context_dir` | string | `context` | Default prefix for canonical categories that omit `path`. |
| `categories` | map | `{}` | Map keyed by category name. |
| `categories.<name>.path` | string | `<context_dir>/<name>` | Repo-rooted path. Required for custom categories outside `context_dir`. |
| `categories.<name>.drop` | bool | `false` | Exclude a canonical category. Mutually exclusive with `path`/`custom`/`l3`. |
| `categories.<name>.custom` | bool | `false` | Required for non-canonical names. Signals "model drafts L2 + infers L3 if `l3:` absent". |
| `categories.<name>.l3` | list[string] | absent | Override model's L3 inference. Each entry is a filename matching `^[a-z][a-z0-9_-]*\.(yaml\|jsonl)$`. Schema inferred via canonical-name lookup when the filename matches a known ledger; otherwise model writes the schema. |

### Canonical category names

The set of names that are recognized as canonical (no `custom: true` required):

- `architecture`
- `patterns`
- `domain`
- `operations`
- `debugging`
- `mobile`
- `workspace`
- `data`
- `infra`

Any other name in `categories` requires `custom: true` or it is rejected at parse time.

### Path semantics

- Repo-rooted absolute (relative to `$TARGET`).
- Regex: `^[a-z._-][a-z0-9._/-]*$`.
- No `..` segments, no leading `/`, no trailing `/`.
- Two categories may not share a path.
- One category's path may not be a strict prefix of another's.

### Validation rules

`scripts/parse_config.py` rejects (with line-numbered errors on stderr, exit 65):

1. Path violates the regex above or contains `..` / leading `/` / trailing `/`.
2. Two categories share `path`.
3. One category's `path` is a prefix of another's.
4. Non-canonical name without `custom: true`.
5. `drop: true` combined with any other field.
6. `l3` filename with an extension other than `.yaml` or `.jsonl`.

## Worked example: weroad case

The headline use case is a repo that wants the canonical set under `docs/project/` *and* a `glossary` category at `docs/domain/glossary/`, while preserving sibling user-owned dirs like `docs/domain/handbook/` and `docs/domain/tech/`:

```yaml
context_dir: docs/project
categories:
  domain:     { drop: true }
  operations: { drop: true }
  glossary:
    path: docs/domain/glossary
    custom: true
    l3: [glossary.yaml]
```

Resolved layout:

| Category | Path | Kind |
| --- | --- | --- |
| `architecture` | `docs/project/architecture` | canonical |
| `patterns` | `docs/project/patterns` | canonical |
| `debugging` | `docs/project/debugging` | canonical |
| `glossary` | `docs/domain/glossary` | custom |

`docs/domain/handbook/` and `docs/domain/tech/` are untouched. The wrap-up step prints a sibling notice naming them so the user sees they are not managed.

## Out of scope

- No schema versioning (`version:`) field. The file is throwaway.
- No multi-root abstraction. Per-category `path` is enough.
- No auto-emit. The interactive flow does not produce a config.
- No polymorphic L2 (multi-file or L3-only categories). Deferred to a later workflow.
