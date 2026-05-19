# Step 3a: Name the context directory

Fresh and Merge modes only (interactive). Skip in Incremental mode (already detected in Step 1). Skip entirely when `$LAYOUT_MAP` was produced from a config in Step 1: paths come from the config, and `context_dir` is the default prefix already baked into each canonical category's resolved path.

This step contributes `$CONTEXT_DIR` to Step 4b, which uses it as the path prefix for every canonical category (`$CONTEXT_DIR/<name>`).

`AskUserQuestion`:

- **Question**: "Context directory name? (default: `context/`)"
- **Description**: "Pick any path-safe single-segment name: `context`, `docs`, `knowledge`, `.agents`, `ai`, whatever matches the repo's conventions."

Accept any value matching `^[a-z._-][a-z0-9._-]*$` (single safe filesystem segment, no slashes, no `..`, no `.` alone). Store as `$CONTEXT_DIR`. Default to `context` if the user accepts the default. Validate the answer before continuing.

## Collision check

A directory with a common name like `docs/`, `knowledge/`, or `ai/` may already exist in the target repo for reasons unrelated to exodia (user-authored docs, generated artifacts, unrelated tooling). After the user picks a name, check `$TARGET/$CONTEXT_DIR`:

- If the directory does not exist, or exists and is empty: proceed.
- If it exists with files that already carry `<!-- exodia:section:` markers: Step 1 misclassified the mode. Switch to Incremental treatment of that directory and skip the rest of Fresh/Merge scaffolding.
- If it exists with files but none carry exodia markers (pre-existing non-exodia content): list the first 5 to 10 existing top-level entries as a markdown bulleted list, then `AskUserQuestion`:
  - **Question**: "`$CONTEXT_DIR/` already has unrelated content. How to proceed?"
  - **Options**:
    - "Share directory": exodia adds `<category>/...` subdirectories alongside existing content; templates only land on fresh paths, existing files are left untouched.
    - "Pick different name": re-ask the Step 3a question.
    - "Abort scaffold": stop the skill cleanly.

The scaffolder never overwrites existing files (`init-structure.mjs` skips any destination that already exists), but a shared top-level directory still entangles the exodia tree with unrelated content. The consent step makes that entanglement explicit.
