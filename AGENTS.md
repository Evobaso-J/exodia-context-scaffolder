# exodia-scaffolder

Plugin root. This plugin ships a single skill, `/exodia`, which scaffolds a durable, agent-agnostic context tree (`AGENTS.md` + `context/`) into any target repo.

## Skills

@./skills/exodia/SKILL.md

## Philosophy

A single monolithic `CLAUDE.md` becomes a dumping ground. `/exodia` instead emits:

- a thin **router** (`AGENTS.md`) that points agents to the right module by task type
- five narrative modules (L2 `.md`) — architecture, patterns, domain, operations, debugging
- append-only data files (L3 `.jsonl` / `.yaml`) — ADRs, PR review checks, gotchas, playbooks, glossaries, variants
- embedded **self-update rules** that future agent sessions follow to keep the context alive

Max 2 hops to any piece of information. Context grows with the codebase, not against it.

## Install

```bash
git clone https://github.com/Evobaso-J/exodia-scaffolder ~/projects/exodia-scaffolder
mkdir -p ~/.claude/skills
ln -s ~/projects/exodia-scaffolder/skills/exodia ~/.claude/skills/exodia
```

Then run `/exodia` from any repo.
