## [1.0.0] - 2026-04-25

Initial release of the `/exodia` skill scaffolder for Claude Code.

### Added

- Interactive scaffolder: scans a target repo, proposes categories, drafts each module section-by-section, and embeds self-update rules.
- Emits an `AGENTS.md` router plus a `context/` directory split into 5 narrative modules: architecture, patterns, domain, operations, debugging.
- Append-only L3 data files in each module (`.jsonl` + `.yaml`) with a `_schema` header line.
- Optional L3 ledgers for `infra` (decisions, runbooks), `workspace` (migrations), `data` (experiments, datasets), and `mobile` (gotchas, releases).
- File-format strategy heuristic (`heuristics/format-strategy.md`) so custom modules pick `.jsonl` / `.yaml` / `.md` consistently.
- Re-run support: incremental diff against existing content with interactive merge mode (consent up front, no `.bak` files).
- One-shot install as a Claude Code skill (single `SKILL.md` at `~/.claude/skills/exodia`, no plugin wrapper).
- Triggers: `/exodia`, "scaffold agent context", "initialize AGENTS.md", "bootstrap context tree".
- Heuristics, templates, and runtime self-update rules bundled alongside `SKILL.md`.
