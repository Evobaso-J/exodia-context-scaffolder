# decisions: entry schema

One file per entry: `{id}__{slug}.md`. Architectural decision records: routing, state management, build pipeline, major library choices, cross-cutting refactors. Supersede with a new entry instead of editing a settled one.

**A new entry is always a new file.** Never append to, or edit, an entry someone
else wrote: two branches adding entries then create two distinct paths, which is
what keeps them from ever conflicting on merge. Retire an entry with
`status: archived`; do not delete it.

## Filename

`{id}__{slug}.md`: `{id}` is `adr_{YYYYMMDD}_{HHMMSS}_{4hex}`, `{slug}` is the
title lowercased with non-alphanumerics collapsed to `-`. The listing of this
directory is therefore a title index.

## Retrieval

Grep this directory, never read it whole: `rg -l '<term>' <dir>/` searches the entry
bodies, which the filename does not carry. Frontmatter is greppable too, so a field
filter is `rg -l '^status: "superseded"' <dir>/`. Read only the files that match; the
listing is the fallback when the task has no term worth searching for.

## Frontmatter

- `id`
- `title`
- `status`
- `supersedes`
- `date`

## Body

- `## Context`: the situation that forced a decision
- `## Decision`: what was decided, in one or two sentences
- `## Rationale`: why this option won
- `## Positive consequences`: bullet list
- `## Negative consequences`: bullet list
