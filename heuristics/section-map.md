# Section → category mapping

When merging an existing `CLAUDE.md` / `AGENTS.md`, `/exodia` splits it by `##` heading and routes each section to one of the confirmed categories.

## Match order

Apply rules top-to-bottom. First match wins. If no rule matches, route to `_unsorted.md`.

| Heading keywords (case-insensitive, substring match) | Category |
| ---------------------------------------------------- | -------- |
| `architecture`, `routing`, `router`, `module`, `ssr`, `csr`, `bundle`, `chunk`, `state management`, `store`, `runtime`, `entry point`, `build pipeline` | `architecture` |
| `pattern`, `convention`, `component`, `composable`, `hook`, `utility`, `helper`, `api call`, `client`, `auth pattern`, `tracking pattern`, `telemetry pattern`, `accessibility`, `a11y`, `testing pattern`, `style guide` | `patterns` |
| `domain`, `entity`, `entities`, `glossary`, `terminology`, `user journey`, `business logic`, `model` (only if clearly business-model, not ML) | `domain` |
| `environment`, `env var`, `variant`, `market`, `tenant`, `locale`, `i18n`, `translation`, `deploy`, `release`, `config`, `feature flag` | `operations` |
| `debug`, `troubleshoot`, `common issue`, `gotcha`, `playbook`, `error`, `fix`, `known issue`, `pitfall`, `setup` (only if followed by *local*, *dev*, *environment*) | `debugging` |
| `mobile`, `ios`, `android`, `react native`, `expo`, `flutter` | `mobile` (if present) |
| `workspace`, `monorepo`, `package graph`, `turbo`, `nx`, `pnpm workspace` | `workspace` (if present) |
| `notebook`, `pipeline`, `ml`, `training`, `model` (when clearly ML-context), `dataset`, `etl` | `data` (if present) |
| `infra`, `terraform`, `kubernetes`, `helm`, `cloudformation`, `provisioning`, `cdk`, `pulumi`, `observability`, `oncall`, `monitoring` | `infra` (if present) |

## Special rules

- **Project overview / about / README-like lede** → maps to `overview` placeholder in the generated `AGENTS.md`, not to any category.
- **Commands / Scripts** → maps to `commands` placeholder in `AGENTS.md`.
- **Quick Action Table / How to work here / For developers** → maps to `quick-actions` placeholder in `AGENTS.md`. If the table format matches closely, pass the rows through verbatim.
- **Anything under 40 characters of body** → route to `_unsorted`, likely too thin to place confidently.

## User override

Always show the computed mapping to the user before proceeding. The user may reassign any section to any category. Re-route silently — do not lecture.

## `_unsorted.md` format

When sections can't be placed, write them to `context/_unsorted.md` with their original heading and body preserved. Top of the file:

```markdown
# Unsorted sections

The following sections from the previous `CLAUDE.md` / `AGENTS.md` couldn't be auto-routed. Move them into the right category file when you get a moment, then delete this file.
```

Then the original sections verbatim. The self-update rules will nudge future sessions to clean this up.
