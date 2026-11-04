# reviews: entry schema

One file per entry: `{id}__{slug}.md`. Review checks learned the hard way: what a reviewer must verify because getting it wrong broke something. Includes migration rules, with the old and the new pattern.

**A new entry is always a new file.** Never append to, or edit, an entry someone
else wrote: two branches adding entries then create two distinct paths, which is
what keeps them from ever conflicting on merge. Retire an entry with
`status: archived`; do not delete it.

## Filename

`{id}__{slug}.md`: `{id}` is `rv_{YYYYMMDD}_{HHMMSS}_{4hex}`, `{slug}` is the
title lowercased with non-alphanumerics collapsed to `-`. The listing of this
directory is therefore a title index.

## Retrieval

Grep this directory, never read it whole: `rg -l '<term>' <dir>/` searches the entry
bodies, which the filename does not carry. Frontmatter is greppable too, so a field
filter is `rg -l '^type: "migration"' <dir>/`. Read only the files that match; the
listing is the fallback when the task has no term worth searching for.

## Frontmatter

- `id`
- `title`
- `category`
- `type`
- `severity`
- `tags`
- `status`
- `created`

## Body

- `## Old pattern` (migration entries only): the shape being retired
- `## New pattern` (migration entries only): the shape that replaces it
