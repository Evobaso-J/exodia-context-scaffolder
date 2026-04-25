# User-facing prompt format

Every prompt the user sees during a `/exodia` run should be scannable. Apply these rules to every `AskUserQuestion` call site, every Step 7 draft review, every Step 4 mapping table, and every Step 9 candidate list.

## Question text

- One sentence, ≤120 characters.
- No hedging openers (`Would you like...`, `Could you...`, `Do you want me to...`). State the choice directly: `Split now?`, `Use this category set?`, `Accept this section?`.
- Inline `code` for file paths, directory names, and identifiers.

## Option labels

- ≤5 words. Action-verb start: `Accept set`, `Drop categories`, `Add custom`, `Pick different name`, `Abort scaffold`.
- Cap 4 options per call. If you need more, fall back to a numbered free-text prompt (`Type row reassignments: 3→domain, 5→drop`).
- Long rationale lives in the option `description` field, never in the question body.

## Lists, tables, and candidate sets

- Render as actual markdown (bulleted lists, real `|` tables, fenced code blocks). Not prose paragraphs.
- Group long lists by directory, category, or file. Cap visible items at ~20; offer a "show more" branch if longer.
- Truncate long paths mid-segment with `...` (e.g. `apps/web/.../routes/foo.ts`).

## Multi-section drafts (Step 7, Step 4 mapping, incremental diffs)

- Preface each block with an H3 anchor: `### \`<file>\` § <section-id>`. Lets the user scan a long review.
- Put draft prose inside a fenced markdown block. Put diffs inside a ` ```diff ` block.
- One H3 + one fenced block + one `AskUserQuestion` per section. Do not stack multiple sections under one question.
