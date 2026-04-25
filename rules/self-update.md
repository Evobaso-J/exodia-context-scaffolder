The context files are **shared, living documentation** about the codebase — not personal memory. After completing a task, check whether any codebase fact, decision, or pattern — discovered or taught — should be logged for future sessions. Write in objective, third-person terms (the team decided X because Y), not first-person recollection (I learned X). **Do not ask the user for permission — just do it.** The user can always revert via git.

### When to update

All target-file paths below are relative to the context directory (`{{CONTEXT_DIR}}/`).

| Signal during conversation | Target file | What to write |
| -------------------------- | ----------- | ------------- |
| Codebase assumption corrected by user or by evidence | L2 `.md` file for that area | Update the incorrect section |
| Bug pattern identified with non-obvious root cause | `debugging/playbooks.jsonl` | New playbook entry |
| Pitfall or footgun confirmed ("don't do X" / "watch out for Y") | `debugging/gotchas.jsonl` | New gotcha entry |
| Architecture or design decision taken by the team | `architecture/decisions.jsonl` | New ADR entry |
| PR review surfaces new check (prod break, near-miss) | `patterns/reviews.jsonl` | New review entry |
| API contract changes or deprecated | `patterns/reviews.jsonl` | New entry tagged `migration` with `old_pattern` / `new_pattern` |
| Variant-specific behavior confirmed | `operations/variants.yaml` | New entry under the relevant variant |
| Domain term clarified or new entity appears | `domain/glossary.yaml` | New or updated term |
| Infra ADR taken (cloud, IaC, network, observability) | `infra/decisions.jsonl` | New ADR entry |
| Infra event response procedure defined (scale, failover, cert rotation) | `infra/runbooks.jsonl` | New runbook entry |
| Workspace graph change (package move, scope rename, tooling swap) | `workspace/migrations.jsonl` | New migration entry |
| ML experiment run with outcome | `data/experiments.jsonl` | New experiment entry |
| New dataset registered or refresh cadence change | `data/datasets.yaml` | New or updated dataset |
| Platform-specific mobile footgun confirmed | `mobile/gotchas.jsonl` | New gotcha entry tagged with `platform` |
| Mobile store rollout (version, phase) | `mobile/releases.jsonl` | New rollout entry |

### How to update

1. **Read the target file first** — check for duplicates or entries that should be updated instead of duplicated.
2. **Branch-scoped dedup.** Check the current branch (`git branch --show-current`). If an entry on the same topic was added on the **current branch** (check with `git diff <default-branch> -- <file>`), **replace it in-place** instead of appending. A branch is a unit of work — it should produce one entry per topic, not one per iteration or conversation. Once an entry is merged, it is settled and should not be overwritten — only superseded by a new entry on a new branch if the understanding changes.
3. **Use the existing schema** — every `.jsonl` file starts with a `_schema` line (JSON object with `_schema`, `_version`, `_description`, `_fields`). Read `_fields` to know which keys an entry must carry. Match field names exactly. Do not invent fields. If the schema must evolve, bump `_version` in the first line before adding entries with the new shape.
4. **Generate the ID** — format: `{type}_{YYYYMMDD}_{HHMMSS}_{4hex}` using the current date/time. When replacing an entry per rule 2, keep the original ID.
5. **Append, don't rewrite** — add new lines at the end of `.jsonl` files. For `.md` and `.yaml` files, edit the relevant section. Exception: see rule 2 — entries added on the current branch are mutable until merged.
6. **Archive, don't delete.** When a `.jsonl` entry becomes obsolete (gotcha no longer applies, runbook replaced, experiment failed), set `status: archived` on the entry instead of removing the line. Preserves history for retrospectives. The `status` field is part of every appendable schema's `_fields` (ADR schemas use `status: superseded` for the same purpose, with `supersedes: <id>` pointing at the replacement).
7. **Keep entries atomic** — one insight per entry. Don't bundle multiple gotchas into one.
8. **Be concise** — write for a developer who will read this months later without the conversation context.
9. **Point, don't hardcode** — never copy values that already live in source files (versions, ports, config). Reference the file instead.

### What NOT to capture

- Anything already in the context files (check first).
- Ephemeral debugging steps that only apply to this session.
- User preferences about agent behavior (those belong in `.claude/` or equivalent settings, not here).
- Information that can be derived from reading the code or git history.

### What NOT to capture (codebase-specific)

These rot fast — pointer only, never hardcode:

- Dependency versions, ports, env-var values, API endpoints, hostnames — reference the source file (`see package.json`, `defined in .env.example`).
- Function signatures, type definitions, class hierarchies, DB schemas — derivable by reading code.
- Git-derivable facts (commit author, date, PR number, blame line) — use `git log` / `git blame`.
- Patterns already obvious from `package.json` / lockfile / `pyproject.toml` dependencies ("we use Redux" when `redux` is in deps).
- Test names, file counts, directory listings — rerun the command.
- One-session workarounds that will be gone next branch — unless the fix teaches a durable rule.

### When adding a new L3 file

If a recurring signal does not fit any target file in the table above, a new L3 file may be justified. Pick its format from the **File Format Strategy** table embedded above (or in `heuristics/format-strategy.md` at scaffolder time). Add a row to the signal-target table at the same time so future sessions route to it.

### File Format Strategy

| Format | Use when the data is | Examples |
| ------ | -------------------- | -------- |
| `.jsonl` | Append-only list of dated records, OR id-keyed record list mutated by id-rewrite. One self-contained record per line. | decisions, gotchas, playbooks, reviews, runbooks, migrations, experiments, releases |
| `.yaml` | Named, structured tree describing the *shape* of something stable. Mutated by editing nodes in place. | glossary, variants, datasets registry |
| `.md` | Long-form narrative — prose read top to bottom. The L2 module file is always `.md`; additional `.md` files at L3 are rare. | walkthroughs, calendars |

If two formats fit, prefer `.jsonl` — agents handle line-delimited records more reliably than nested YAML, and append-only is safer for long-running context. JSONL files always start with a single-line schema header: `{"_schema": "<type>", "_version": "1.0", "_description": "...", "_fields": [...]}`.
