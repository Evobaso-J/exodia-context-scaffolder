# Step 2: Scan the repo

Applies in Fresh, Merge, and Incremental modes.

Delegate the initial scan to an `Explore` subagent with **medium** thoroughness (upgrade to very thorough only if the user passes a `--deep` flag or the repo is clearly large and multi-faceted). Pass a prompt shaped like this:

> You are scanning `<TARGET>` to help bootstrap an AGENTS.md context tree. Report in under 800 words:
>
> 1. **Stack**: languages, frameworks, build tool, test tool, package manager. Cite files.
> 2. **Architecture summary**: routing style, state management, module layout, SSR/CSR split, backend/frontend divide. One paragraph.
> 3. **Glossary signals**: top-level entities or models you can name. Look wherever the repo keeps its domain objects: schema files, model classes, type definitions, or a dedicated directory.
> 4. **Operations signals**: i18n tooling if any framework-specific lib is present (locale files, translation dirs), multi-env config (env files, `deploy/`, k8s, helm, terraform), multi-tenant patterns, feature-flag tools.
> 5. **Category-tweak triggers**: report presence/absence of each:
>    - i18n / multi-market
>    - mobile (React Native, Expo, Flutter, iOS/Android dirs)
>    - monorepo (`pnpm-workspace.yaml`, `turbo.json`, `nx.json`, `lerna.json`, `packages/`, `apps/`)
>    - data / ML (`notebooks/`, `models/`, `data/`, ipynb files, pytorch / tf / jax deps)
>    - infra (`terraform/`, `helm/`, `k8s/`, `.tf` files, CloudFormation)
> 6. **Lint/test/typecheck scripts** detected in `package.json`, `pyproject.toml`, `Gemfile`, `go.mod`, `Cargo.toml`, `Makefile`. Name the commands (e.g. `pnpm lint`, `pytest`).
> 7. **Existing docs**: if `AGENTS.md` / `CLAUDE.md` / `README.md` has structured sections, list the `##` headings.
>
> Output the report as a structured list. Do not speculate; cite files for everything.

Store the returned scan as your working `$SCAN`.

## Fallback

If the Explore subagent times out or returns unusable data, fall back to asking the user to confirm the stack and architecture directly, then continue.
