# exodia-scaffolder

<p align="center">
  <img src="assets/exodia.webp" alt="Exodia, the Forbidden One" width="420">
</p>

<p align="center"><em>5 pieces. 5 modules of progressive disclosure. All we need to <strong>OBLITERATE</strong> token consumption.</em></p>

> One-shot scaffolder that bootstraps durable, self-maintaining agent context for any codebase.

`exodia` generates an `AGENTS.md` router and a `context/` tree tailored to your repo. The output is **agent-agnostic** — compatible with Claude Code, Cursor, Codex, Windsurf, and any tool that respects the [agents.md](https://agents.md) convention.

## Why

A single `CLAUDE.md` / `AGENTS.md` file grows into an unreadable pile. `/exodia` splits context across five narrative modules with append-only data logs behind them:

```
AGENTS.md                          # router + rules + quick action table
CLAUDE.md → AGENTS.md              # symlink for Claude Code
context/
  architecture/   ARCHITECTURE.md + decisions.jsonl
  patterns/       PATTERNS.md     + reviews.jsonl
  domain/         DOMAIN.md       + glossary.yaml
  operations/     OPERATIONS.md   + variants.yaml
  debugging/      DEBUGGING.md    + gotchas.jsonl + playbooks.jsonl
```

Agents load the router, pick the right module, and optionally read the data file. Max two hops. The router carries **self-update rules** that tell agents when to append new gotchas, ADRs, or review lessons — so the context grows as the team works.

## What you get

- **Interactive scaffolder** — `/exodia` scans your repo, proposes categories, drafts narrative modules, and walks you through them section-by-section.
- **Fixed-5 + detected extras** — five canonical categories, plus optional `mobile/`, `workspace/`, `data/`, `infra/` when the skill detects them.
- **Agent-agnostic output** — canonical `AGENTS.md`; symlinks or pointer files for Claude Code (`CLAUDE.md`), Cursor (`.cursorrules`), Windsurf (`.windsurfrules`), and Copilot (`.github/copilot-instructions.md`) as detected.
- **Self-update reinforcement** — embedded prose rules + optional Claude Code `Stop` hook that reminds agents to capture new signals at turn end.
- **Safe re-runs** — running `/exodia` again on a repo that already has the setup does an incremental diff and proposes additions only, never overwriting user-edited prose.
- **Existing-file merge** — if your repo already has `CLAUDE.md` or `AGENTS.md`, the skill parses it, maps sections to categories, and backs up the original.

## Install

```bash
git clone https://github.com/Evobaso-J/exodia-scaffolder ~/projects/exodia-scaffolder
mkdir -p ~/.claude/skills
ln -s ~/projects/exodia-scaffolder/skills/exodia ~/.claude/skills/exodia
```

Run `/exodia` in any repo. The skill takes over from there.

> Plugin-marketplace distribution is planned. For now, the symlink install is the supported path.

## Usage

```
cd ~/your-repo
# Open Claude Code, then:
/exodia
```

You'll be interviewed about:

1. **Categories** — accept the default five, drop ones that don't fit, or add detected extras.
2. **Existing content** (if any) — review the proposed section-to-category mapping.
3. **Per-category drafts** — for each `##` heading, accept / edit / reject.
4. **L3 seeding** — optionally seed `gotchas.jsonl` from `TODO`/`FIXME` comments and `decisions.jsonl` from any detected ADRs.
5. **Agent symlinks** — which agent pointer files to emit.
6. **Self-update hook** — (Claude Code only) optionally install a `Stop` hook that reinforces the self-update rules.

## Layout

```
exodia-scaffolder/
├── .claude-plugin/          # plugin metadata
├── AGENTS.md                # plugin root
├── README.md                # you are here
├── LICENSE                  # MIT
└── skills/
    └── exodia/
        ├── SKILL.md         # main interview protocol
        ├── templates/       # L2/L3 stubs copied into target repo
        ├── rules/           # rule snippets composed into AGENTS.md
        ├── heuristics/      # detector + section-mapping tables
        ├── hooks/           # optional Stop hook for Claude Code
        └── scripts/         # mechanical helpers (bash + python)
```

## Roadmap

- Cursor / Windsurf native skill wrappers
- Claude Code plugin marketplace submission
- `npx exodia` CLI wrapper for CI / zero-dep invocation
- Auto-diff of context/ against code on PR

## Credits

Shoulders of giants. This project is directly inspired by **[muratcankoylan/Agent-Skills-for-Context-Engineering — digital-brain-skill](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering/tree/main/examples/digital-brain-skill)**, which pioneered the progressive-disclosure approach to agent context. `exodia-scaffolder` adapts those ideas into a one-shot, agent-agnostic scaffolder centered on five canonical modules.

## License

MIT. See [LICENSE](LICENSE).
