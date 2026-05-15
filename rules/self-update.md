The context files are **shared, living documentation** about the codebase, not personal memory. After completing a task, check whether any codebase fact, decision, or pattern (discovered or taught) should be logged for future sessions. Write in objective, third-person terms (the team decided X because Y), not first-person recollection (I learned X). **Do not ask the user for permission; just do it.** The user can always revert via git.

### When to update

Target-file paths below are absolute, repo-rooted: a config-driven scaffold may place categories anywhere (e.g. `docs/project/architecture/`, `docs/handbook/glossary/`). Without a config, the canonical layout has every category under `{{CONTEXT_DIR}}/`. The scaffolder substitutes the resolved paths into this table at emit time; do not re-derive them.

| Signal during conversation | Target file | What to write |
| -------------------------- | ----------- | ------------- |
| Codebase assumption corrected by user or by evidence | L2 `.md` file for that area | Update the incorrect section |
<!-- exodia:self-update:rows:start -->
{{LEDGER_ROWS}}
<!-- exodia:self-update:rows:end -->

### How to update

1. **Read the target file first**: check for duplicates or entries that should be updated instead of duplicated.
2. **Branch-scoped dedup.** Check the current branch (`git branch --show-current`). If an entry on the same topic was added on the **current branch** (check with `git diff <default-branch> -- <file>`), **replace it in-place** instead of appending. A branch is a unit of work; it should produce one entry per topic, not one per iteration or conversation. Once an entry is merged, it is settled and should not be overwritten; only superseded by a new entry on a new branch if the understanding changes.
3. **Use the existing schema**: every `.jsonl` file starts with a `_schema` line (JSON object with `_schema`, `_version`, `_description`, `_fields`). Read `_fields` to know which keys an entry must carry. Match field names exactly. Do not invent fields. If the schema must evolve, bump `_version` in the first line before adding entries with the new shape.
4. **Generate the ID**: format `{type}_{YYYYMMDD}_{HHMMSS}_{4hex}` using the current date/time. When replacing an entry per rule 2, keep the original ID.
5. **Append, don't rewrite**: add new lines at the end of `.jsonl` files. For `.md` and `.yaml` files, edit the relevant section. Exception: see rule 2; entries added on the current branch are mutable until merged.
6. **Archive, don't delete.** When a `.jsonl` entry becomes obsolete (playbook fix no longer applies, runbook replaced, experiment failed), set `status: archived` on the entry instead of removing the line. Preserves history for retrospectives. The `status` field is part of every appendable schema's `_fields` (ADR schemas use `status: superseded` for the same purpose, with `supersedes: <id>` pointing at the replacement).
7. **Keep entries atomic**: one insight per entry. Don't bundle multiple findings into one.
8. **Be concise**: write for a developer who will read this months later without the conversation context.
9. **Point, don't hardcode**: never copy values that already live in source files (versions, ports, config). Reference the file instead.

### What NOT to capture

- Anything already in the context files (check first).
- Ephemeral debugging steps that only apply to this session.
- User preferences about agent behavior (those belong in `.claude/` or equivalent settings, not here).
- Information that can be derived from reading the code or git history.
- Entity or concept definitions outside `glossary/glossary.yaml` (or the equivalent glossary L3 under the resolved category path). The glossary L3 is the single source of truth; reference entities by name from other L2 files, do not redefine them.
  - If a term is missing from the glossary, add it there first, then reference it from the L2 file.

### What NOT to capture (codebase-specific)

These rot fast; pointer only, never hardcode:

- Dependency versions, ports, env-var values, API endpoints, hostnames: reference the source file (`see package.json`, `defined in .env.example`).
- Function signatures, type definitions, class hierarchies, DB schemas: derivable by reading code.
- Git-derivable facts (commit author, date, PR number, blame line): use `git log` / `git blame`.
- Patterns already obvious from `package.json` / lockfile / `pyproject.toml` dependencies ("we use Redux" when `redux` is in deps).
- Test names, file counts, directory listings: rerun the command.
- One-session workarounds that will be gone next branch, unless the fix teaches a durable rule.

### When adding a new L3 file

If a recurring signal does not fit any target file in the table above, a new L3 file may be justified. Pick its format from the **File Format Strategy** table embedded above (or in `heuristics/format-strategy.md` at scaffolder time). Add a row to the signal-target table at the same time so future sessions route to it.

### File Format Strategy

<!-- exodia:format-strategy:start -->
{{FORMAT_STRATEGY}}
<!-- exodia:format-strategy:end -->
