# Context-tree content lints

Content-level consistency checks for the emitted `context/` tree. Distinct from `heuristics/lint-detectors.md`, which discovers lint/test/typecheck commands in the **target repo's** toolchain. These checks scan the **scaffolded context tree itself** for cross-file consistency violations.

The scaffolder does not automate these at draft time; treat each row as a manual lint pass that a maintainer (or a future automation hook) can run against an existing context tree. The rules they enforce are baked into the runtime self-update rules (`rules/self-update.md`) and the L2 template top comments.

## Checks

| Check | Detect by | Action when matched |
| ----- | --------- | ------------------- |
| Module dossier in architecture | An entry under `## Modules & Boundaries` in `architecture/ARCHITECTURE.md` lists composable names, plugin methods, helper functions, or call-site recipes instead of (or in addition to) a `Usage docs` pointer into `design-patterns/DESIGN-PATTERNS.md` | Strip the API details from the architecture entry; move them into the relevant section of `design-patterns/DESIGN-PATTERNS.md`. Replace with a one-line purpose plus the `see [<Section>](...)` link. Rule source: `templates/architecture/ARCHITECTURE.md.tmpl` `<!-- seam: -->` comment. |

## Implementation hints

The module-dossier check is hard to mechanize because "looks like an API" is fuzzy. A practical proxy: count fenced code blocks, backtick-wrapped identifiers, and lines starting with `-` inside the `## Modules & Boundaries` section; if any threshold is exceeded, flag for manual review.

The check is not wired into the scaffolder protocol today. If automation is added later, the natural entry point is `protocol/04-merge.md` (mapping-review prompt) so that incoming CLAUDE.md sections that match the architecture keyword `module` but carry usage-surface bodies are routed to `design-patterns` before drafting begins.
