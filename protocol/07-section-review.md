# Step 7: Section-by-section review

Applies in Fresh and Merge modes.

Walk each L2 draft with the user. For each `##` section:

- Show the drafted prose.
- Render the draft inside a fenced markdown block, prefaced by an H3 anchor: `### \`<category>/<CATEGORY>.md\` § <section-id>`.
- Then `AskUserQuestion`:
  - **Question**: "Accept this section?"
  - **Options**: "Accept", "Edit", "Skip" (leave empty for later).
- If edit: let the user dictate changes, re-draft (still inside the fenced block), loop until accepted.

Then `Write` the finalized L2 file to `$TARGET/$CONTEXT_DIR/<category>/<CATEGORY>.md`.
