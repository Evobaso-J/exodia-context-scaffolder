# exodia-scaffolder

<p align="center">
  <img src="assets/exodia.png" alt="Exodia, the Forbidden One" width="420">
</p>

<p align="center"><em>"I have assembled all 5 special modules, all 5 pieces of the puzzle! Exodia! <strong>OBLITERATE</strong> token consumption!"</em></p>

> One-shot scaffolder that bootstraps durable, self-maintaining agent context for any codebase.

`exodia` generates an `AGENTS.md` router and a `context/` tree tailored to your repo. Output is **agent-agnostic**: works with Claude Code, Cursor, Codex, Windsurf, and any tool that respects the [agents.md](https://agents.md) convention.

## 🧩 Why

A single `CLAUDE.md` / `AGENTS.md` grows into an unreadable pile. Every turn, the agent reloads the whole thing, the rules you wrote on line 12 fight with the gotchas you logged on line 487, and nobody (human or model) can find anything.

`/exodia` splits that same knowledge into a thin router plus five narrative modules, each backed by append-only data logs. The router is small enough that the agent loads it on every turn. The modules and logs are only loaded when the task actually touches them. Max two hops to any fact.

The result is a context tree that:

- **Stays cheap to load.** Routine work touches the router and maybe one module, not 800 lines of mixed concerns.
- **Self-heals.** Every emitted `AGENTS.md` ships with rules telling future sessions where to log new bug root causes, footguns, decisions, and review lessons. Knowledge accumulates instead of evaporating between sessions.
- **Survives re-runs.** Edit the prose by hand; `/exodia` won't clobber it. Re-running diffs only the auto-filled sections.

## 🃏 What it looks like

After `/exodia` runs, your repo gets one router at the root and a five-module tree underneath.

The router (`AGENTS.md`) holds the loading rules, the quick action table, and a `<!-- exodia:router:start -->` block that tells future sessions where to log new knowledge:

```markdown
# AGENTS.md

## How to load context
1. Read this file (the router).
2. Open the L2 narrative for the relevant module.
3. Only load L3 data files (.jsonl / .yaml) when the task needs specific entries.

## Quick reference
| Need                          | Read                                                |
|-------------------------------|-----------------------------------------------------|
| System shape, boundaries      | `context/architecture/ARCHITECTURE.md`              |
| Conventions, code review rules| `context/design-patterns/DESIGN-PATTERNS.md`        |
| Domain vocabulary             | `context/glossary/GLOSSARY.md`                      |
| Run / build / test / deploy   | `context/operations/OPERATIONS.md`                  |
| Footguns, known pitfalls      | `context/debugging/DEBUGGING.md`                    |

<!-- exodia:router:start -->
| Signal type     | Append to                                           |
|-----------------|-----------------------------------------------------|
| `decision`      | `context/architecture/decisions.jsonl`              |
| `review`        | `context/design-patterns/reviews.jsonl`             |
| `term`          | `context/glossary/glossary.yaml`                    |
| `variant`       | `context/operations/variants.yaml`                  |
| `playbook`      | `context/debugging/playbooks.jsonl`                 |
<!-- exodia:router:end -->
```

A narrative L2 (`context/architecture/ARCHITECTURE.md`) reads like a focused module README, not a wiki dump:

```markdown
<!-- exodia:section:overview -->
## Overview
Two-service split: `api/` (FastAPI) handles request routing and auth;
`worker/` (Celery) owns long-running ingest. Shared schema in `packages/contracts/`.

<!-- exodia:section:boundaries -->
## Boundaries
- `api/` never imports from `worker/`. Communication is queue-only.
- Database access from `api/` is read-mostly; writes go through the worker.
```

The L3 ledger (`context/architecture/decisions.jsonl`) is one append-only line per entry:

```jsonl
{"id":"decision_20260514_103211_a4f2","date":"2026-05-14","title":"Move auth to gateway","why":"Per-service JWT validation was duplicated across 4 services; centralizing cut latency variance and unblocked rate limiting.","status":"merged"}
```

That's the whole shape: **router, narrative, ledger**. Five modules, same pattern.

Full hand-authored snapshot: [`examples/scaffolded-tree/`](examples/scaffolded-tree/).

## 🧠 Mental model: L1 / L2 / L3

`exodia` borrows Anthropic's Agent Skills loading pattern (also used by `digital-brain-skill`, see Credits) and applies it to per-repo context:

| Tier | What it is                                   | Example                                       | Loaded |
|------|----------------------------------------------|-----------------------------------------------|--------|
| L1   | The router. Small. Always loaded.            | `AGENTS.md`                                   | Every turn |
| L2   | A module's narrative. Mid-size. Human-edited.| `context/architecture/ARCHITECTURE.md`        | When the task touches that module |
| L3   | Append-only data. Grepped, not read whole.   | `decisions.jsonl`, `glossary.yaml`            | When a specific entry is needed |

The **two-hop rule**: from L1, you reach any fact in at most two more reads. Router points to the module; module narrative either contains the answer (L2) or names the ledger that does (L3). The agent never reads the whole tree to answer one question.

This matters because the alternative, a single big `CLAUDE.md`, costs the full file in input tokens *every turn*, even when the task only needs three lines from it. Splitting trades one cheap read for one targeted read, and the savings compound across a session.

## 📚 The 5 modules

The canonical set is fixed at five. The scaffolder may also propose repo-bespoke categories on top when the scan warrants it (see [`SKILL.md`](SKILL.md)), but every scaffolded repo starts with these.

### `architecture/` : what the system *is*
The shape of the codebase: services, boundaries, data flow, build topology. L2 prose answers "what's where and why". The ledger `decisions.jsonl` is ADR-lite: one append-only entry per architectural decision, capturing the *why* so future sessions don't relitigate it.

### `design-patterns/` : how to write code here
Conventions and review rules. Uses **progressive disclosure**: `DESIGN-PATTERNS.md` holds only short guardrails (2-3 lines per topic); detailed explanations are spun out to `design-patterns/docs/<slug>.md` and linked from the L2. Section headings inside the L2 are model-derived from the scan, not a fixed list. The ledger `reviews.jsonl` logs lessons surfaced in code review: "this PR almost shipped X, the fix is Y".

### `glossary/` : the words you have to know
Domain terms, abbreviations, and the names this codebase uses for things that have other names elsewhere. `glossary.yaml` is the source of truth; the L2 narrative explains the high-trust ones in context.

### `operations/` : how to run / build / test / deploy
Commands, environment knobs, gotchas in the dev loop. `variants.yaml` captures behavior that differs across environments or feature flags, so the agent knows "in staging this flag is off" without you re-explaining each time.

### `debugging/` : what bites you
Known pitfalls, fragile spots, recurring bug shapes. `playbooks.jsonl` is append-only: one entry per root cause, with the smell, the diagnosis, and the fix. This is the module that grows fastest in real use; it's also the one that pays back loudest.

## ⚡ Install

`exodia` is a single Claude Code skill. Clone it into your personal skills dir:

```bash
git clone https://github.com/Evobaso-J/exodia-scaffolder ~/.claude/skills/exodia
```

Restart Claude Code (or open a new session). Run `/exodia` in any repo. The directory name (`exodia`) must match the skill name in `SKILL.md` frontmatter; do not rename it.

## 🎯 Usage

```bash
cd ~/your-repo
# Open Claude Code, then:
/exodia
```

That's it. The skill scans the repo, proposes a category set, drafts each module section by section with accept / edit / reject on every `##` heading, and emits the router. The first run is interactive; expect to review and steer.

Re-running `/exodia` on an already-scaffolded repo automatically enters incremental mode. No flag needed. Full interview protocol lives in [`SKILL.md`](SKILL.md).

## 🔁 Modes: Fresh / Merge / Incremental

Preflight classifies the target repo and picks the flow:

- **Fresh**: no existing `AGENTS.md`, `CLAUDE.md`, or context tree. Full scaffold from scratch.
- **Merge**: a monolithic `AGENTS.md` or `CLAUDE.md` exists. With explicit consent, exodia splits it on `##`, routes each heading into a category by keyword match, and replaces the original with a thin router. Content moves, not deleted.
- **Incremental**: any top-level dir containing `<!-- exodia:section:` markers is detected as an existing exodia tree. Diffs only touch auto-filled sections; user-edited prose is preserved.

## 📓 Self-update

Every emitted `AGENTS.md` ships with a routing table that tells future sessions where to log new knowledge (bug root causes, footguns, architecture decisions, PR review lessons, domain terms, variant behavior). Each entry gets an ID of the form `{type}_{YYYYMMDD}_{HHMMSS}_{4hex}`. While a branch is in flight, a new insight on the same topic overwrites the earlier entry in place instead of stacking duplicates. Once the branch merges, the entry is settled: only a later branch can supersede it. Agents append without asking, and the user can always revert via git.

Full signal-to-file mapping and write rules: [`rules/self-update.md`](rules/self-update.md).

## 🛠 Customizing the layout

The default layout (canonical 5 modules under `context/`) covers most repos. For richer setups, like a canonical set under `docs/project/` plus a sibling handbook category at `docs/handbook/glossary/`, drop an opt-in `exodia.config.yaml` at the repo root **before** the first `/exodia` run. The file is sparse (encode only the diff from defaults), one-shot (consumed at first run, ignored on re-runs), and throwaway (delete once the scaffolded tree is committed).

```yaml
context_dir: docs/project
categories:
  operations: { drop: true }
  releases:
    path: docs/releases
    custom: true
    description: "Release notes per published version"
    l3: [release_notes.jsonl]
```

Copy-pasteable: [`examples/exodia.config.yaml`](examples/exodia.config.yaml) (full monorepo example) or [`examples/exodia.config.minimal.yaml`](examples/exodia.config.minimal.yaml) (smallest useful override). Full schema, canonical category names, path semantics, and validation rules: [`docs/config.md`](docs/config.md).

## 🙏 Credits

Inspired by **[muratcankoylan/Agent-Skills-for-Context-Engineering: digital-brain-skill](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering/tree/main/examples/digital-brain-skill)**, which applies progressive disclosure (Anthropic's Agent Skills loading pattern) to personal-knowledge context. `exodia-scaffolder` ports the same L1/L2/L3 lazy-load idea to per-repo agent context, packaged as a one-shot scaffolder centered on five canonical modules.

## 📜 License

MIT. See [LICENSE](LICENSE).
