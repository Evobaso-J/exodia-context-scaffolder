# Incremental re-run

Replaces Steps 3, 4, 5, 6, 7, and 8 when preflight (Step 1) detects an existing exodia setup. Step 1, Step 2, and Step 4b still run (Step 4b prints the router-derived `$LAYOUT_MAP` back for confirmation, as documented in `protocol/04b-materialize-layout.md`); Step 9 logic is reused for L3 seeding; Step 10 prints the wrap-up.

Step 1 has already reconstructed `$LAYOUT_MAP` from the existing router region per `heuristics/layout-map.md`; this runbook reads it as the single source for category paths.

0. Trust the `$CONTEXT_DIR` already detected in Step 1. Do not ask the user to rename it; preserving the existing directory name keeps router paths consistent.
1. Re-run Step 2 (scan).
2. For each L2 file under `$TARGET/$CONTEXT_DIR/`, read it and locate `<!-- exodia:section:<id> -->` markers. Fresh-draft *new* facts from the scan. Diff against existing auto-filled content.
3. Propose updates only to sections where the auto-filled block has not been user-edited (detect with the section-id marker; if the content after the marker differs from a reconstructible baseline, treat it as user-edited and do not touch).
4. Render each proposed diff as a fenced ` ```diff ` code block, prefaced by `### \`<file>\` § <section-id>`. Then per section, `AskUserQuestion`:
   - **Question**: "Apply this update?"
   - **Options**: "Accept", "Skip".
5. Append to L3 files from the scan using the same Step 9 logic.
6. Never overwrite `AGENTS.md`; only add missing rule snippets if conditions now apply (e.g. an `operations/` category added after initial scaffold).
