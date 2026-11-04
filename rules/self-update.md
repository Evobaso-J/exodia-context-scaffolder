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

1. **Search the target directory first**: `rg -l '<term>' <dir>/` over the entry bodies, because a near-duplicate rarely repeats the wording you would have put in the title. Filenames are `{id}__{slug}.md`, so the listing is a title index; use it as the fallback when the topic has no distinctive term. Read only the entries that match.
2. **Branch-scoped dedup.** Check the current branch (`git branch --show-current`). If an entry on the same topic was added on the **current branch** (check with `git diff <default-branch> -- <dir>`), **edit that file in place** instead of adding another. A branch is a unit of work; it should produce one entry per topic, not one per iteration or conversation. Once an entry is merged, it is settled and should not be overwritten; only superseded by a new entry on a new branch if the understanding changes.
3. **Use the existing schema**: every entry directory carries a `_schema.md` listing the frontmatter fields and the body sections. Match field names exactly. Do not invent fields. If the schema must evolve, update `_schema.md` in the same branch that introduces the new shape.
4. **Generate the ID**: format `{type}_{YYYYMMDD}_{HHMMSS}_{4hex}` using the current date/time. When replacing an entry per rule 2, keep the original ID.
5. **One file per entry, never touch another**: write a new `{id}__{slug}.md` in the target directory. Two branches adding entries create two distinct paths, which is what stops them conflicting on merge; appending to a shared file is what caused the conflicts this model replaces. For L2 `.md` modules and `.yaml` files, edit the relevant section. Exception: see rule 2; entries added on the current branch are mutable until merged.
6. **Archive, don't delete.** When an entry becomes obsolete (playbook fix no longer applies, runbook replaced, experiment failed), set `status: archived` in its frontmatter instead of removing the file. Preserves history for retrospectives. `status` is part of every entry schema (ADR schemas use `status: superseded` for the same purpose, with `supersedes: <id>` pointing at the replacement). If a repo's `_schema.md` lacks it, add it there first, otherwise nothing can ever be retired.
7. **Keep entries atomic**: one insight per entry. Don't bundle multiple findings into one.
8. **Be concise**: write for a developer who will read this months later without the conversation context.
9. **Point, don't hardcode**: never copy values that already live in source files (versions, ports, config). Reference the file instead.

### What NOT to capture

- Anything already in the context files (check first).
- Ephemeral debugging steps that only apply to this session.
- User preferences about agent behavior (those belong in `.claude/` or equivalent settings, not here).
- Information that can be derived from reading the code or git history.

### What NOT to capture (codebase-specific)

These rot fast; pointer only, never hardcode:

- Dependency versions, ports, env-var values, API endpoints, hostnames: reference the source file (`see package.json`, `defined in .env.example`).
- Function signatures, type definitions, class hierarchies, DB schemas: derivable by reading code.
- Git-derivable facts (commit author, date, PR number, blame line): use `git log` / `git blame`.
- Patterns already obvious from `package.json` / lockfile / `pyproject.toml` dependencies ("we use Redux" when `redux` is in deps).
- Test names, file counts, directory listings: rerun the command.
- One-session workarounds that will be gone next branch, unless the fix teaches a durable rule.

