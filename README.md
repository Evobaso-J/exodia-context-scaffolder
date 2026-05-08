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
  patterns/       PATTERNS.md     + reviews.jsonl
  domain/         DOMAIN.md       + glossary.yaml
  operations/     OPERATIONS.md   + variants.yaml
  debugging/      DEBUGGING.md    + gotchas.jsonl + playbooks.jsonl
```

## ⚡ Install

`exodia` is a single Claude Code skill. Clone it into your personal skills dir:

```bash
git clone https://github.com/Evobaso-J/exodia-scaffolder ~/.claude/skills/exodia
```

Restart Claude Code (or open a new session). Run `/exodia` in any repo. The directory name (`exodia`) must match the skill name in `SKILL.md` frontmatter; do not rename it.

## 🃏 What it does

- **Interactive scaffold**: scans the repo, proposes categories, drafts each module section by section with accept / edit / reject on every `##` heading.
- **Fixed-5 core + detected optionals**: five canonical modules by default; `mobile/`, `workspace/`, `data/`, `infra/` auto-proposed when repo signals fire.
- **Safe re-runs**: running `/exodia` again diffs incrementally, preserves user-edited prose via `<!-- exodia:section:<id> -->` markers, and never overwrites the emitted `AGENTS.md`.
- **Existing-file merge**: a pre-existing `CLAUDE.md` / `AGENTS.md` is parsed, split by `##`, and routed into the right modules.

Customization knobs (custom context-dir name, dropping canonical modules, custom categories, optional auto-add detectors): see [`SKILL.md`](SKILL.md).

### Custom layout (`.exodia.yaml`)

For repos that want to nest categories under user-named parent groups, drop a `.exodia.yaml` at the repo root before running `/exodia`:

```yaml
context_dir: context
structure:
  engineering:
    - architecture
    - patterns
    - debugging
    - operations
  product:
    - domain
```

The file is opt-in and **authoritative when present**: leaves of `structure:` are the final category set, and the on-disk tree mirrors the nesting (`context/engineering/architecture/...`, `context/product/domain/...`). Custom categories may appear inline as single-key maps with `purpose:` and optional `ledgers:`. Validation runs at file load (regex on names, group/leaf disjointness, no leaf duplicated across paths). Re-running `/exodia` after editing the file reconciles file-vs-disk drift with per-move and per-orphan prompts. Absent file = the flat layout that previous releases shipped. Schema details in [`heuristics/format-strategy.md`](heuristics/format-strategy.md) § Layout file.

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
