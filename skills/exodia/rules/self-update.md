The context files must stay up to date with what the team learns. After completing a task, check whether anything you discovered or were told should be captured. **Do not ask the user for permission — just do it.** The user can always revert via git.

### When to update

| Signal during conversation | Target file | What to write |
| -------------------------- | ----------- | ------------- |
| User corrects a wrong assumption about the codebase | L2 `.md` file for that area | Update the incorrect section |
| You discover a non-obvious bug root cause | `debugging/playbooks.jsonl` | New playbook entry |
| User warns "don't do X" or "watch out for Y" | `debugging/gotchas.jsonl` | New gotcha entry |
| A new architecture/design decision is made | `architecture/decisions.jsonl` | New ADR entry |
| A PR review surfaces a new check (broke in prod, near-miss) | `patterns/reviews.jsonl` | New review entry |
| An API contract changes or is deprecated | `patterns/reviews.jsonl` | New entry tagged `migration` with `old_pattern` / `new_pattern` |
| A new variant-specific behavior is discovered | `operations/variants.yaml` | New entry under the relevant variant |
| A domain term is clarified or a new entity appears | `domain/glossary.yaml` | New or updated term |

### How to update

1. **Read the target file first** — check for duplicates or entries that should be updated instead of duplicated.
2. **Branch-scoped dedup.** Check the current branch (`git branch --show-current`). If an entry on the same topic was added on the **current branch** (check with `git diff <default-branch> -- <file>`), **replace it in-place** instead of appending. A branch is a unit of work — it should produce one entry per topic, not one per iteration or conversation. Once an entry is merged, it is settled and should not be overwritten — only superseded by a new entry on a new branch if the understanding changes.
3. **Use the existing schema** — every `.jsonl` file has a `_schema` line. Match it exactly. Do not invent fields.
4. **Generate the ID** — format: `{type}_{YYYYMMDD}_{HHMMSS}_{4hex}` using the current date/time. When replacing an entry per rule 2, keep the original ID.
5. **Append, don't rewrite** — add new lines at the end of `.jsonl` files. For `.md` and `.yaml` files, edit the relevant section. Exception: see rule 2 — entries added on the current branch are mutable until merged.
6. **Keep entries atomic** — one insight per entry. Don't bundle multiple gotchas into one.
7. **Be concise** — write for a developer who will read this months later without the conversation context.
8. **Point, don't hardcode** — never copy values that already live in source files (versions, ports, config). Reference the file instead.

### What NOT to capture

- Anything already in the context files (check first).
- Ephemeral debugging steps that only apply to this session.
- User preferences about agent behavior (those belong in `.claude/` or equivalent settings, not here).
- Information that can be derived from reading the code or git history.
