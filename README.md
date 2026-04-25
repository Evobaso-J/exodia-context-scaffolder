# exodia-scaffolder

<p align="center">
  <img src="assets/exodia.webp" alt="Exodia, the Forbidden One" width="420">
</p>

<p align="center"><em>"I have assembled all 5 special modules, all 5 pieces of the puzzle! Exodia! <strong>OBLITERATE</strong> token consumption!"</em></p>

> One-shot scaffolder that bootstraps durable, self-maintaining agent context for any codebase.

`exodia` generates an `AGENTS.md` router and a `context/` tree tailored to your repo. The output is **agent-agnostic**: compatible with Claude Code, Cursor, Codex, Windsurf, and any tool that respects the [agents.md](https://agents.md) convention.

## Why

A single `CLAUDE.md` / `AGENTS.md` grows into an unreadable pile that agents load in full on every turn. `/exodia` splits the same knowledge into a thin router plus five narrative modules, each backed by append-only data logs:

```
AGENTS.md                          # router + rules + quick action table
context/
  architecture/   ARCHITECTURE.md + decisions.jsonl
  patterns/       PATTERNS.md     + reviews.jsonl
  domain/         DOMAIN.md       + glossary.yaml
  operations/     OPERATIONS.md   + variants.yaml
  debugging/      DEBUGGING.md    + gotchas.jsonl + playbooks.jsonl
```

Agents read the router, pick the right module, and optionally load one data file. Max two hops. The router carries **self-update rules** that nudge future sessions to capture new gotchas, ADRs, and review lessons as the team works, so the context grows with the codebase instead of against it.

## Install

`exodia` is a single Claude Code skill. Symlink it into your personal skills dir:

```bash
git clone https://github.com/Evobaso-J/exodia-scaffolder ~/projects/exodia-scaffolder
mkdir -p ~/.claude/skills
ln -s ~/projects/exodia-scaffolder/skills/exodia ~/.claude/skills/exodia
```

Run `/exodia` in any repo. The skill takes over from there.

## What you get

- **Interactive scaffolder**: `/exodia` scans your repo, proposes categories, drafts each module section-by-section, and walks you through accept / edit / reject on every `##` heading.
- **Fixed-5 core + detected optionals**: five canonical modules by default, plus `mobile/`, `workspace/`, `data/`, `infra/` auto-proposed when repo signals fire.
- **Agent-agnostic output**: canonical `AGENTS.md` that any [agents.md](https://agents.md)-aware tool can consume.
- **Configurable shape**: custom context-dir name, custom categories, drop any canonical module that doesn't fit.
- **Self-update rules baked in**: emitted `AGENTS.md` carries a signal → target-file table so future sessions append entries automatically.
- **Optional Claude Code `Stop` hook**: per-turn reminder that reinforces the self-update rules without blocking work.
- **Safe re-runs**: running `/exodia` again on a scaffolded repo diffs incrementally and never overwrites user-edited prose.
- **Existing-file merge**: pre-existing `CLAUDE.md` / `AGENTS.md` is parsed, split by `##`, and routed into the right modules; the original file becomes a thin router.

## How it works

The emitted tree is organized around a **max two-hop** load rule: L1 router → L2 narrative → (optional) L3 data. Nothing is loaded eagerly.

- **L1 Router** (`AGENTS.md`): project overview, commands pointer, Context Router task-type table, behavioral rules, self-update rules, quick-action table, and a tree diagram. Small enough to stay in context every turn.
- **L2 narratives** (`<CATEGORY>.md` per module): human-readable prose for each domain area. Every section carries a `<!-- exodia:section:<id> -->` marker. The markers drive incremental re-runs: auto-filled sections can be refreshed; user-edited sections are left alone.
- **L3 data files** (`.jsonl` / `.yaml` per module): append-only logs. Each `.jsonl` opens with a `_schema` line declaring `_schema`, `_version`, `_fields`. Entries must match the declared shape.
- **Pointer, don't hardcode**: drafts reference source files (`see package.json engines.node`, `defined in .env.example`) rather than copying values. Duplicated data rots; pointers survive edits.

Deep-divers can read `skills/exodia/SKILL.md` for the full protocol.

## Usage

```
cd ~/your-repo
# Open Claude Code, then:
/exodia
```

The interview walks you through:

1. **Preflight classification**: Fresh, Merge, or Incremental (auto-detected; see below).
2. **Categories**: accept the canonical five, drop any that don't fit, or add detected / custom ones.
3. **Context-dir name**: default `context/`; pick any path-safe single segment.
4. **Existing-file mapping** (Merge only): review which `##` section lands in which module.
5. **Per-section drafts**: accept / edit / reject every `##` heading across the L2 files.
6. **L3 seeding**: optionally seed `gotchas.jsonl` from `TODO`/`FIXME` comments and `decisions.jsonl` from any detected ADRs.
7. **Stop hook** (Claude Code only): optional per-turn reminder install.

Re-running `/exodia` on an already-scaffolded repo automatically enters incremental mode. No flag needed.

## Modes: Fresh / Merge / Incremental

Preflight classifies the target repo and picks the right flow.

- **Fresh**: no `AGENTS.md`, no `CLAUDE.md`, no existing context tree. Full scaffold: scan, propose categories, draft L2s section-by-section, seed L3s, emit the router.
- **Merge**: a monolithic `AGENTS.md` or `CLAUDE.md` exists, but no context tree yet. exodia asks explicit consent (the old file will be replaced by a thin router), then `scripts/parse_existing.py` splits it on `##` and `heuristics/section-map.md` routes each heading to a category by keyword match. Unmappable sections land in `_unsorted.md` for later triage. The parsed content is *moved*, not deleted. It survives inside the new modules.
- **Incremental**: any top-level directory containing `<!-- exodia:section:` markers counts as an existing exodia tree (the directory name isn't hardcoded). `/exodia` re-runs the scan, proposes diffs only on auto-filled sections, and never overwrites the emitted `AGENTS.md`. User-edited prose is detected via the section markers and preserved.

## Customization knobs

- **Context-dir name**: default `context/`, but any single safe segment matching `^[a-z._-][a-z0-9._-]*$` works (`docs`, `knowledge`, `.agents`, `ai`, or whatever fits your repo's conventions). Enforced by `scripts/init_structure.sh`.
- **Drop canonical modules**: the core five are a default, not a minimum. A pure library may have no `operations/`; a CLI tool may have no `domain/`; a data pipeline may skip `patterns/`. Keep only what fits.
- **Custom categories**: add any lowercase name matching `^[a-z][a-z0-9_-]*$`. exodia scaffolds an empty L2 stub; you describe what the module covers.
- **Optional auto-adds**: the scanner proposes `mobile/` (React Native, Expo, iOS/Android dirs), `workspace/` (`pnpm-workspace.yaml`, `turbo.json`, `nx.json`, `lerna.json`), `data/` (`torch` / `tensorflow` / `jax` / notebooks / `dvc.yaml`), and `infra/` (`terraform/`, `helm/`, `k8s/`, `cdk.json`, `pulumi.yaml`) when the relevant signals fire. Full trigger list lives in `skills/exodia/heuristics/detectors.md`.

## Self-update + Stop hook

The emitted `AGENTS.md` ships with two layers of reinforcement so the context keeps growing without per-change prompting.

**Self-update rules** (always embedded)

Every emitted `AGENTS.md` carries a signal-to-target-file table so future sessions know where new knowledge goes:

| Signal during a turn | Append to |
| -------------------- | --------- |
| Bug root cause | `debugging/playbooks.jsonl` |
| Footgun / pitfall | `debugging/gotchas.jsonl` |
| Architecture decision | `architecture/decisions.jsonl` |
| PR review lesson | `patterns/reviews.jsonl` |
| Clarified domain term | `domain/glossary.yaml` |
| Variant-specific behavior | `operations/variants.yaml` |

Entries use the canonical ID format `{type}_{YYYYMMDD}_{HHMMSS}_{4hex}` (sortable, collision-free). **Branch-scoped dedup**: a same-topic entry added on the current branch is replaced in-place rather than duplicated; once merged, entries are settled and only superseded by a new entry on a new branch. Agents don't ask permission; the user can always revert via git.

**Optional Stop hook** (Claude Code only)

The prose self-update rules above work on their own. The hook exists because prose rules are easy to forget mid-task: agents finish a bug fix, hand back to the user, and the gotcha never gets logged. A `Stop` hook fires on every turn end and gives the agent one last nudge before it yields.

What happens when the hook is installed:

1. **Trigger**: Claude Code runs the hook every time the agent finishes a turn (stops and returns control to the user).
2. **Action**: the hook script writes a short reminder to stderr listing each self-update signal and its target file (gotcha, playbook, ADR, review, glossary, variant).
3. **Effect on the agent**: Claude Code forwards that stderr text back to the agent as stop-event context. The agent re-reads §Self-Update Rules in `AGENTS.md` and, if the turn actually produced a signal, appends the corresponding entry before yielding.
4. **Guarantees**: the hook `exit 0`s unconditionally. It cannot fail a turn, cancel in-flight work, edit files, or make network calls. Its only side effect is the stderr message.

Installed files:

- `.claude/hooks/exodia-stop-reminder.sh`: the 25-line reminder script, with `{{CONTEXT_DIR}}` substituted to your chosen directory name.
- `.claude/settings.json`: the hook is registered under `hooks.Stop`. exodia merges into an existing file rather than replacing, and refuses to touch a malformed settings shape.

To disable: delete the hook script and remove the matching entry from `settings.json`.

## Credits

Inspired by **[muratcankoylan/Agent-Skills-for-Context-Engineering: digital-brain-skill](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering/tree/main/examples/digital-brain-skill)**, which applies progressive disclosure (Anthropic's Agent Skills loading pattern) to personal-knowledge context. `exodia-scaffolder` ports the same L1/L2/L3 lazy-load idea to per-repo agent context, packaged as a one-shot scaffolder centered on five canonical modules.

## License

MIT. See [LICENSE](LICENSE).
