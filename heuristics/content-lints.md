# Context-tree content lints

Content-level consistency checks for the emitted `context/` tree. Distinct from `heuristics/lint-detectors.md`, which discovers lint/test/typecheck commands in the **target repo's** toolchain. These checks scan the **scaffolded context tree itself** for cross-file consistency violations.

The scaffolder does not automate these at draft time; treat each row as a manual lint pass that a maintainer (or a future automation hook) can run against an existing context tree. The rules they enforce are baked into the runtime self-update rules (`rules/self-update.md`) and the L2 template top comments.

## Checks

| Check | Detect by | Action when matched |
| ----- | --------- | ------------------- |
| Duplicate entity definition | Term keyed under `entities:` or `concepts:` in `glossary.yaml` appears as a heading (`##`, `###`, `####`) or bold lead (`**Term**:` at the start of a line) in any L2 `.md` file other than the glossary L2 | Replace the duplicate definition with a name-only reference. If the L2 file needs to elaborate context, point at the glossary entry rather than restating its definition. Rule source: `templates/glossary/GLOSSARY.md.tmpl` `<!-- glossary: -->` comment and the `<!-- glossary: -->` comments in the four non-glossary L2 templates. |
| Module dossier in architecture | An entry under `## Modules & Boundaries` in `architecture/ARCHITECTURE.md` lists composable names, plugin methods, helper functions, or call-site recipes instead of (or in addition to) a `Usage docs` pointer into `design-patterns/DESIGN-PATTERNS.md` | Strip the API details from the architecture entry; move them into the relevant section of `design-patterns/DESIGN-PATTERNS.md`. Replace with a one-line purpose plus the `see [<Section>](...)` link. Rule source: `templates/architecture/ARCHITECTURE.md.tmpl` `<!-- seam: -->` comment. |

## Implementation hints

A minimal `grep` / `jq` pipeline is enough for the duplicate-entity check:

1. Parse `<context_dir>/glossary/glossary.yaml`; collect the union of `entities:` and `concepts:` keys.
2. For each key, grep the other L2 `.md` files for `^##+\s+<key>` (heading match, case-insensitive) and `^\*\*<key>\*\*:` (bold-lead match).
3. Emit a warning per match with the L2 file and the offending line.

The module-dossier check is harder to mechanize because "looks like an API" is fuzzy. A practical proxy: count fenced code blocks, backtick-wrapped identifiers, and lines starting with `-` inside the `## Modules & Boundaries` section; if any threshold is exceeded, flag for manual review.

Neither check is wired into the scaffolder protocol today. If automation is added later, the natural entry point is `protocol/06-draft-l2.md` (post-draft validation) for the duplicate-entity check and `protocol/04-merge.md` (mapping-review prompt) for the module-dossier check.
