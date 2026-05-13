# Step 4: Existing-file merge

Merge mode only. Skip in Fresh and Incremental modes.

The user already granted permission in Step 1.

This step does not change the `$LAYOUT_MAP` shape. The accepted mapping is carried into Step 6 as seed content for category drafts. Step 4b runs immediately after.

1. Pick the parse source:
   - If `AGENTS.md` exists (with or without `CLAUDE.md`), it is the source.
   - If only `CLAUDE.md` exists, parse that.
2. Read the source file with the `Read` tool and split it inline on `^## ` headings (H2 only, not H3 or deeper). For each H2, capture the heading text and the body lines that follow up to the next H2. Content before the first H2 becomes a section with heading `__lede__`. Drop the lede section only when its body is empty; keep every other section even if its body is empty. The result is an in-memory list of `{heading, body}` entries, ordered as they appear in the file.
3. For each heading, apply `$SKILL_DIR/heuristics/section-map.md` keyword rules to pick a target category. Restrict the candidate set to the categories present in `$LAYOUT_MAP` when config-driven (canonical + custom); otherwise use the interactively confirmed set from Step 3. Unmappable headings → `_unsorted` bucket.
4. Render the mapping as a markdown table:

   ```
   | # | Heading           | →  | Proposed category |
   |---|-------------------|----|-------------------|
   | 1 | Architecture      | →  | architecture      |
   | 2 | Local dev         | →  | operations        |
   ```

   Then `AskUserQuestion`:
   - **Question**: "Mapping look right?"
   - **Options**: "Accept all", "Reassign rows", "Drop rows", "Edit table".

   If the table is too long for the four-option bound, fall back to a numbered prompt: ask the user to type row reassignments (`3→glossary, 5→drop`).
5. Carry the accepted mapping into Step 6 as **seed content** for each category draft. The parsed content is being *moved*, not copied; the original file is replaced by Step 8 (router). No `.bak` file is written: the user consented in Step 1, and the content is preserved (split across modules under `$CONTEXT_DIR/`) rather than destroyed.
