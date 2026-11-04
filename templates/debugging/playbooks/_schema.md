# playbooks: entry schema

One file per entry: `{id}__{slug}.md`. Reproducible behaviour worth a future debugger's time: symptoms seen, root cause found, fix applied. Includes recurring footguns: the footgun IS the symptom.

**A new entry is always a new file.** Never append to, or edit, an entry someone
else wrote: two branches adding entries then create two distinct paths, which is
what keeps them from ever conflicting on merge. Retire an entry with
`status: archived`; do not delete it.

## Filename

`{id}__{slug}.md`: `{id}` is `pb_{YYYYMMDD}_{HHMMSS}_{4hex}`, `{slug}` is the
title lowercased with non-alphanumerics collapsed to `-`. The listing of this
directory is therefore a title index.

## Retrieval

Grep this directory, never read it whole: `rg -l '<symptom>' <dir>/` searches the entry
bodies, which the filename does not carry, and a debugger arrives with the symptom, not
the title someone gave it. Frontmatter is greppable too, so a field filter is
`rg -l '^tags: .*hydration' <dir>/`. Read only the files that match; the listing is the
fallback when the task has no term worth searching for.

## Frontmatter

- `id`
- `title`
- `files`
- `tags`
- `status`
- `created`

## Body

- `## Symptoms`: bullet list of what the developer observes
- `## Root cause`: why it happens
- `## Fix`: what to do about it
