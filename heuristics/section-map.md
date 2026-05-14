# Section → category mapping

When merging an existing `CLAUDE.md` / `AGENTS.md`, `/exodia` splits it by `##` heading and routes each section to one of the confirmed categories.

## Match order

Apply rules top-to-bottom. First match wins. If no rule matches, route to `_unsorted.md`.

| Heading keywords (case-insensitive, substring match) | Category |
| ---------------------------------------------------- | -------- |
| `architecture`, `routing`, `router`, `module`, `ssr`, `csr`, `bundle`, `chunk`, `state management`, `store`, `runtime`, `entry point`, `build pipeline` | `architecture` |
| `pattern`, `convention`, `component`, `composable`, `hook`, `utility`, `helper`, `api call`, `client`, `auth pattern`, `tracking pattern`, `telemetry pattern`, `accessibility`, `a11y`, `testing pattern`, `style guide` | `design-patterns` |
| `domain`, `entity`, `entities`, `glossary`, `terminology`, `user journey`, `business logic`, `model` (only if clearly business-model, not ML) | `glossary` |
| `environment`, `env var`, `variant`, `market`, `tenant`, `locale`, `i18n`, `translation`, `deploy`, `release`, `config`, `feature flag` | `operations` |
| `debug`, `troubleshoot`, `common issue`, `gotcha`, `playbook`, `error`, `fix`, `known issue`, `pitfall`, `setup` (only if followed by *local*, *dev*, *environment*) | `debugging` |

Non-core categories (mobile, infra, data, workspace, ...) are repo-bespoke under A2; when one is part of the confirmed category set, the user may reassign sections to it manually during the merge mapping review.

## Special rules

- **Project overview / about / README-like lede** → maps to `overview` placeholder in the generated `AGENTS.md`, not to any category.
- **Commands / Scripts** → maps to `commands` placeholder in `AGENTS.md`.
- **Quick Action Table / How to work here / For developers** → maps to `quick-actions` placeholder in `AGENTS.md`. If the table format matches closely, pass the rows through verbatim.
- **Anything under 40 characters of body** → route to `_unsorted`, likely too thin to place confidently.
- **Module section with usage-surface body** → if a heading matches the `architecture` keyword `module` (e.g. `## Modules`, `## Local Modules`) but the body is dominated by composable names, plugin/method APIs, or call-site recipes, route to `design-patterns` instead. The architecture↔patterns seam (see `templates/architecture/ARCHITECTURE.md.tmpl` and `templates/design-patterns/DESIGN-PATTERNS.md.tmpl` top comments) places module catalogues in architecture and module APIs in design-patterns. Heading match alone cannot tell them apart; inspect the body before routing.

## User override

Always show the computed mapping to the user before proceeding. The user may reassign any section to any category. Re-route silently; do not lecture.

## `_unsorted.md` format

When sections can't be placed, write them to `context/_unsorted.md` with their original heading and body preserved. Top of the file:

```markdown
# Unsorted sections

The following sections from the previous `CLAUDE.md` / `AGENTS.md` couldn't be auto-routed. Move them into the right category file when you get a moment, then delete this file.
```

Then the original sections verbatim. The self-update rules will nudge future sessions to clean this up.
