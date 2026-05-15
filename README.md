# exodia-scaffolder

<p align="center">
  <img src="assets/exodia.png" alt="Exodia, the Forbidden One" width="420">
</p>

<p align="center"><em>"I have assembled all 5 special modules, all 5 pieces of the puzzle! Exodia! <strong>OBLITERATE</strong> token consumption!"</em></p>

> One-shot scaffolder that bootstraps durable, self-maintaining agent context for any codebase.

`exodia` generates an `AGENTS.md` router and a `context/` tree tailored to your repo. Output is **agent-agnostic**: works with Claude Code, Cursor, Codex, Windsurf, and any tool that respects the [agents.md](https://agents.md) convention.

## 🧩 Why

A single `CLAUDE.md` / `AGENTS.md` grows into an unreadable pile that agents reload in full every turn. `/exodia` splits the same knowledge into a thin router plus five narrative modules, each backed by append-only data logs. Max two hops to any fact.

```
AGENTS.md                          # router + rules + quick action table
context/
  architecture/   ARCHITECTURE.md + decisions.jsonl
  design-patterns/ DESIGN-PATTERNS.md + reviews.jsonl + docs/<slug>.md (deep dives)
  glossary/        GLOSSARY.md        + glossary.yaml
  operations/     OPERATIONS.md   + variants.yaml
  debugging/      DEBUGGING.md    + playbooks.jsonl
```

`design-patterns` uses **progressive disclosure**: `DESIGN-PATTERNS.md` holds short guardrails only (2-3 lines per topic); detailed explanations are spun out to `design-patterns/docs/<slug>.md` and linked from the L2. Section headings inside the L2 are model-derived from the scan, not a fixed list.

## ⚡ Install

`exodia` is a single Claude Code skill. Clone it into your personal skills dir:

```bash
git clone https://github.com/Evobaso-J/exodia-scaffolder ~/.claude/skills/exodia
```

Restart Claude Code (or open a new session). Run `/exodia` in any repo. The directory name (`exodia`) must match the skill name in `SKILL.md` frontmatter; do not rename it.

## 🃏 What it does

- **Interactive scaffold**: scans the repo, proposes categories, drafts each module section by section with accept / edit / reject on every `##` heading.
- **Fixed-5 core + model-proposed adds**: five canonical modules by default; the scaffolder reads the scan and proposes additional repo-bespoke categories when evidence warrants. Non-core categories flow through a single model-derivation path (filename, schema, format, scan_hint derived from purpose plus scan).
- **Safe re-runs**: running `/exodia` again diffs incrementally, preserves user-edited prose via `<!-- exodia:section:<id> -->` markers, and never overwrites the emitted `AGENTS.md`.
- **Existing-file merge**: a pre-existing `CLAUDE.md` / `AGENTS.md` is parsed, split by `##`, and routed into the right modules.

Customization knobs (custom context-dir name, dropping canonical modules, custom categories): see [`SKILL.md`](SKILL.md).

## 🛠 Customizing the layout (config-driven)

For richer layouts (canonical set under `docs/project/`, plus a sibling category at `docs/handbook/glossary/`, etc.), drop an opt-in `exodia.config.yaml` at the repo root **before** running `/exodia` for the first time. Categories can be relocated, dropped, or added with arbitrary repo-rooted paths.

- **Opt-in.** Absent → the interactive flow runs unchanged.
- **One-shot.** Consumed exactly once at the first scaffold run (Fresh or Merge mode). Incremental re-runs ignore it.
- **Throwaway.** After the first run, the AGENTS.md router table (wrapped in `<!-- exodia:router:start -->` / `<!-- exodia:router:end -->`) is the sole persistent source of truth. Delete or `.gitignore` the file once the scaffolded tree is committed.
- **Sparse + defaults.** Encode only the diff from the canonical layout. Anything not declared keeps its default.

### Schema

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
| `categories.<name>.l3` | list[string] | absent | Override model's L3 inference. Each entry is a filename matching `^[a-z][a-z0-9_-]*\.(yaml\|jsonl)$`. Schema inferred via canonical-name lookup when the filename matches a known ledger; otherwise model writes the schema. |

### Canonical category names

Recognized as canonical (no `custom: true` required):

`architecture`, `design-patterns`, `glossary`, `operations`, `debugging`.

Any other name in `categories` requires `custom: true` or it is rejected at parse time. Cross-repo consistency for non-core categories (e.g. sharing the same `mobile` / `infra` shape across several services) is a user responsibility: share an `exodia.config.yaml` snippet between repos.

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
7. `description` that is empty, multiline, or longer than 200 characters.

## 🎯 Usage

```
cd ~/your-repo
# Open Claude Code, then:
/exodia
```

Re-running `/exodia` on an already-scaffolded repo automatically enters incremental mode. No flag needed. Full interview protocol lives in [`SKILL.md`](SKILL.md).

## 🔁 Modes: Fresh / Merge / Incremental

Preflight classifies the target repo and picks the flow:

- **Fresh**: no existing `AGENTS.md`, `CLAUDE.md`, or context tree. Full scaffold from scratch.
- **Merge**: a monolithic `AGENTS.md` or `CLAUDE.md` exists. With explicit consent, exodia splits it on `##`, routes each heading into a category by keyword match, and replaces the original with a thin router. Content moves, not deleted.
- **Incremental**: any top-level dir containing `<!-- exodia:section:` markers is detected as an existing exodia tree. Diffs only touch auto-filled sections; user-edited prose is preserved.

## 📓 Self-update

Every emitted `AGENTS.md` ships with a routing table that tells future sessions where to log new knowledge (bug root causes, footguns, architecture decisions, PR review lessons, domain terms, variant behavior). Each entry gets an ID of the form `{type}_{YYYYMMDD}_{HHMMSS}_{4hex}`. While a branch is in flight, a new insight on the same topic overwrites the earlier entry in place instead of stacking duplicates. Once the branch merges, the entry is settled: only a later branch can supersede it. Agents append without asking, and the user can always revert via git.

Full signal-to-file mapping and write rules: [`rules/self-update.md`](rules/self-update.md).

## 🙏 Credits

Inspired by **[muratcankoylan/Agent-Skills-for-Context-Engineering: digital-brain-skill](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering/tree/main/examples/digital-brain-skill)**, which applies progressive disclosure (Anthropic's Agent Skills loading pattern) to personal-knowledge context. `exodia-scaffolder` ports the same L1/L2/L3 lazy-load idea to per-repo agent context, packaged as a one-shot scaffolder centered on five canonical modules.

## 📜 License

MIT. See [LICENSE](LICENSE).
