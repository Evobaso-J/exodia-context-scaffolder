# exodia-context-scaffolder

<p><strong>AGENTS.md scaffolder for context engineering: one-shot generator of a durable, agent-agnostic context tree (Claude Code, Cursor, Codex, Windsurf, Gemini CLI).</strong></p>

<p align="center">
  <img src="assets/exodia.png" alt="Exodia, the Forbidden One" width="420">
</p>

<p align="center"><em>"I have assembled all 5 special modules, all 5 pieces of the puzzle! Exodia! <strong>OBLITERATE</strong> token consumption!"</em></p>

## 🧩 Why

A single `CLAUDE.md` / `AGENTS.md` grows into an unreadable pile that the agent reloads in full every turn. `/exodia` splits the same knowledge into a thin router plus five narrative modules, each backed by a directory of one-file-per-entry data. The router loads every turn; modules and logs load only when the task touches them. Max two hops to any fact.

## 🧠 Mental model: L1 / L2 / L3

`exodia` borrows Anthropic's Agent Skills loading pattern and applies it to per-repo context:

| Tier | What it is                                   | Example                                       | Loaded |
|------|----------------------------------------------|-----------------------------------------------|--------|
| L1   | The router. Small. Always loaded.            | `AGENTS.md`                                   | Every turn |
| L2   | A module's narrative. Mid-size. Human-edited.| `context/architecture/ARCHITECTURE.md`        | When the task touches that module |
| L3   | One file per entry. Grepped, then read selectively. | `decisions/`, `glossary.yaml`           | When a specific entry is needed |

**Two-hop rule**: from L1, every fact is at most two more reads away. The router points to a module; the module narrative either contains the answer (L2) or names the ledger that does (L3).

## 🃏 What it looks like

After `/exodia` runs, your repo gets one router at the root and a five-module tree underneath.

**L1 / router**

The router (`AGENTS.md`) holds the routing tables. Abbreviated:

```markdown
# AGENTS.md

<!-- exodia:section:overview -->
{one-paragraph project overview from the scan}

## Context Router

<!-- exodia:section:router -->
<!-- exodia:router:start -->
Route by task type. Read the relevant L2 module, then load L3 data (entry directories / `.yaml`) only when needed. **Max 2 hops.** An entry directory is searched, never read whole: `rg -l '<term>' <dir>/`, then read the matches.

| Task type                       | Load                                                |
| ------------------------------- | --------------------------------------------------- |
| System shape, boundaries        | `context/architecture/ARCHITECTURE.md`              |
| Conventions, code review rules  | `context/design-patterns/DESIGN-PATTERNS.md`        |
| Domain vocabulary               | `context/glossary/GLOSSARY.md`                      |
| Run / build / test / deploy     | `context/operations/OPERATIONS.md`                  |
| Footguns, known pitfalls        | `context/debugging/DEBUGGING.md`                    |
<!-- exodia:router:end -->

## Self-Update Rules

<!-- exodia:section:self-update -->
| Signal during conversation                                       | Target file                            | What to write |
| ---------------------------------------------------------------- | -------------------------------------- | ------------- |
| Codebase assumption corrected by user or by evidence             | L2 `.md` file for that area            | Update the incorrect section |
<!-- exodia:self-update:rows:start -->
| Architecture or design decision taken by the team                | `context/architecture/decisions/` | New ADR file |
| PR review surfaces new check (prod break, near-miss)             | `context/design-patterns/reviews/`| New review file |
| API contract changes or deprecated                               | `context/design-patterns/reviews/`| New file tagged `migration` with `old_pattern` / `new_pattern` |
| Domain term clarified or new entity appears                      | `context/glossary/glossary.yaml`       | New or updated term |
| Variant-specific behavior confirmed                              | `context/operations/variants.yaml`     | New entry under the relevant variant |
| Reproducible behaviour worth a future debugger's time            | `context/debugging/playbooks/`    | New playbook file |
<!-- exodia:self-update:rows:end -->
```

**L2 / narrative**

A narrative L2 (`context/architecture/ARCHITECTURE.md`) reads like a focused module README, not a wiki dump:

```markdown
## Overview

<!-- exodia:section:overview -->
Two-service split: `api/` (FastAPI) handles request routing and auth;
`worker/` (Celery) owns long-running ingest. Shared schema in `packages/contracts/`.

## Boundaries

<!-- exodia:section:boundaries -->
- `api/` never imports from `worker/`. Communication is queue-only.
- Database access from `api/` is read-mostly; writes go through the worker.
```

**L3 / ledger**

An L3 ledger is a directory with one Markdown file per entry, conforming to the directory's `_schema.md`. The filename repeats the id plus a slug of the title, so listing the directory gives a title index; grepping it (`rg -l '<term>' <dir>/`) searches the bodies too, and that is the retrieval path every emitted `_schema.md` prescribes:

```markdown
<!-- context/architecture/decisions/adr_20260514_103211_a4f2__move-auth-to-gateway.md -->
---
id: "adr_20260514_103211_a4f2"
title: "Move auth to gateway"
status: "active"
supersedes: null
date: "2026-05-14"
---

## Context

Per-service JWT validation was duplicated across 4 services.

## Decision

Validate at the gateway only; downstream services trust the gateway-injected user header.
```

One file per entry is not cosmetic: two branches that each add an entry create two distinct paths, so they can never conflict on merge. A shared append-only file makes every branch write the same tail line, which is what turns one merge into a conflict on every other open PR.

## 📚 The 5 modules

### `architecture/` : what the system *is*
The shape of the codebase: services, boundaries, data flow, build topology. L2 prose answers "what's where and why". The ledger `decisions/` is ADR-lite: one file per architectural decision, capturing the *why* so future sessions don't relitigate it.

### `design-patterns/` : how to write code here
Conventions and review rules. The L2 `DESIGN-PATTERNS.md` holds only short guardrails (2-3 lines per topic); detailed explanations live in `design-patterns/docs/<slug>.md` and are linked from the L2. Section headings inside the L2 are model-derived from the scan, not a fixed list. The ledger `reviews/` logs lessons surfaced in code review: "this PR almost shipped X, the fix is Y".

### `glossary/` : the words you have to know
Domain terms, abbreviations, and the names this codebase uses for things that have other names elsewhere. `glossary.yaml` is the source of truth; the L2 narrative explains the high-trust ones in context.

### `operations/` : how to run / build / test / deploy
Commands, environment knobs, gotchas in the dev loop. `variants.yaml` captures behavior that differs across environments or feature flags, so the agent knows "in staging this flag is off" without you re-explaining each time.

### `debugging/` : what bites you
Known pitfalls, fragile spots, recurring bug shapes. `playbooks/` holds one file per root cause, with the smell, the diagnosis, and the fix.

## 🔁 Trees scaffolded before entry directories

Older trees kept each ledger in a single append-only `.jsonl`. Re-running `/exodia` on such a tree detects them in Step 1 and, with your consent, converts each one into a directory of `{id}__{slug}.md` files (ids preserved, `.jsonl` removed) before the incremental re-run starts.

## ⚡ Install

`exodia` is a single Claude Code skill. Clone it at the [latest release tag](https://github.com/Evobaso-J/exodia-context-scaffolder/releases/latest) into your personal skills dir:

```bash
LATEST=$(git ls-remote --tags --sort=-v:refname https://github.com/Evobaso-J/exodia-context-scaffolder 'v*' | head -1 | sed 's@.*refs/tags/@@')
git clone --depth 1 --branch "$LATEST" https://github.com/Evobaso-J/exodia-context-scaffolder ~/.claude/skills/exodia
```

Restart Claude Code (or open a new session). Run `/exodia` in any repo. The directory name (`exodia`) must match the skill name in `SKILL.md` frontmatter; do not rename it.

**Runtime requirement:** Node.js (current LTS). The skill's CLI helpers are authored in `src/` (TypeScript) and ship pre-built to `dist/`, so no `npm install` is needed to run the skill.

## 🎯 Usage

```bash
cd ~/your-repo
# Open Claude Code, then:
/exodia
```

The skill scans the repo, proposes a category set, drafts each module section by section with accept / edit / reject on every `##` heading, and emits the router. Re-running on an already-scaffolded repo automatically enters incremental mode. Full interview protocol: [`SKILL.md`](SKILL.md).

## 🔁 Modes: Fresh / Merge / Incremental

Preflight classifies the target repo and picks the flow:

- **Fresh**: no existing `AGENTS.md`, `CLAUDE.md`, or context tree. Full scaffold from scratch.
- **Merge**: a monolithic `AGENTS.md` or `CLAUDE.md` exists. With explicit consent, exodia splits it on `##`, routes each heading into a category by keyword match, and replaces the original with a thin router. Content moves, not deleted.
- **Incremental**: any top-level dir containing `<!-- exodia:section:` markers is detected as an existing exodia tree. Diffs only touch auto-filled sections; user-edited prose is preserved.

## 📓 Self-update

Every emitted `AGENTS.md` ships with a routing table that tells future sessions where to log new knowledge (bug root causes, footguns, architecture decisions, PR review lessons, domain terms, variant behavior). Each entry gets an ID of the form `{type}_{YYYYMMDD}_{HHMMSS}_{4hex}`. On the current branch, a new insight on the same topic replaces the entry the same branch added earlier (checked via `git diff <default-branch>`), so one branch produces one entry per topic. Once merged, the entry is settled: only a later branch can supersede it. Agents append without asking, and the user can always revert via git.

Full signal-to-file mapping and write rules: [`rules/self-update.md`](rules/self-update.md).

## 🛠 Customizing the layout

The default layout (canonical 5 modules under `context/`) covers most repos. For richer setups, like a canonical set under `docs/project/` plus a sibling handbook category at `docs/handbook/glossary/`, drop an opt-in `exodia.config.yaml` at the repo root before the `/exodia` run. The file is sparse (encode only the diff from defaults), one-shot (consumed at first run, ignored on re-runs), and throwaway (delete once the scaffolded tree is committed). However, you can always create an `exodia.config.yaml` after the first run to reshape your current structure.

```yaml
context_dir: docs/project
categories:
  operations: { drop: true }
  releases:
    path: docs/releases
    custom: true
    description: "Release notes per published version"
    l3: [release_notes/]
```

Copy-pasteable: [`examples/exodia.config.yaml`](examples/exodia.config.yaml) (full monorepo example) or [`examples/exodia.config.minimal.yaml`](examples/exodia.config.minimal.yaml) (smallest useful override). Full schema, canonical category names, path semantics, and validation rules: [`docs/config.md`](docs/config.md).

## 🧱 Core principles

Inherited from [`digital-brain-skill`](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering/tree/main/examples/digital-brain-skill), adapted to per-repo agent context:

1. **Progressive disclosure**. An agent pays for every token it loads, every turn. A monolithic `AGENTS.md` forces the model to reread the whole thing even when the task only touches one corner of the codebase. Exodia tiers the context so cost matches relevance: the router loads every turn (cheap, always-on map of the repo), a module's narrative loads only when the task touches that module, and a ledger directory is listed and only the entry that matters is read. The payoff is a context budget that scales with task scope, not with repo size.

2. **One file per entry, never deleted**. Ledgers (`decisions/`, `reviews/`, `playbooks/`, etc.) keep every entry as its own file. When an entry becomes obsolete, its `status` flips to `archived` (or, for ADRs, `superseded` with a `supersedes: <id>` pointer to the replacement) and a new file is added. Within a single branch, an entry on the same topic is replaced in-place so one branch produces one entry per topic; once that branch merges, the entry is settled and a later branch can only supersede it with a new file. The history of how the team's understanding evolved is the artifact: you can read the ledger and see *why* the current answer is the current answer, not just *that* it is.

3. **Module separation**. The five modules (`architecture`, `design-patterns`, `glossary`, `operations`, `debugging`) are chosen so each answers a different question and they do not overlap: "what the system is", "how to write code here", "what the words mean", "how to run it", "what bites you". An architectural decision lives in `architecture/decisions/`, not smeared across a debugging playbook; a runbook gotcha lives in `operations/`, not in a glossary entry. The payoff is that an agent loading one module gets a coherent slice of context, not a grab bag, and edits in one module never silently drift the meaning of another.

4. **Platform agnostic**. The output follows the agents.md convention: a root `AGENTS.md` plus a plain-Markdown `context/` tree, no proprietary frontmatter, no tool-specific directives. Claude Code, Cursor, Codex, Windsurf, Gemini CLI, and anything else that respects the convention read the same files with no adapter. The payoff is no lock-in: switching agents (or running several side by side) does not require regenerating the context tree.

5. **Two-hop rule** (exodia-specific). From the router (L1), any fact in the tree is at most two more file reads away: read the module narrative (L2), and if the answer is not in the prose, the prose names the ledger (L3) that has it. This is a hard ceiling on lookup depth, which keeps both humans and agents from rabbit-holing through chains of cross-references. If you find yourself wanting a third hop, that is a signal to flatten: either promote the fact into the module narrative or split the module.

## 🙏 Credits

Inspired by **[muratcankoylan/Agent-Skills-for-Context-Engineering: digital-brain-skill](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering/tree/main/examples/digital-brain-skill)**, which applies progressive disclosure (Anthropic's Agent Skills loading pattern) to personal-knowledge context. `exodia-context-scaffolder` ports the same L1/L2/L3 lazy-load idea to per-repo agent context, packaged as a one-shot scaffolder centered on five canonical modules.

## 📜 License

MIT. See [LICENSE](LICENSE).
