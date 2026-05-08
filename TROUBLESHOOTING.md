# Troubleshooting

Runtime failure modes for the `/exodia` scaffolder. Read this only when one of the listed conditions is hit during a run.

- **User aborts mid-interview**: leave the repo in whatever partial state exists. No need to roll back. Running `/exodia` again resumes from preflight.
- **Explore scan times out / returns garbage**: fall back to asking the user to confirm the stack and architecture directly, then continue.
- **Target repo has committed secrets or `.env` with real values**: never echo these in drafts. If you must reference env vars, name them only.
- **No git, no agent integration, no lint scripts**: skill still works; just emits the minimal universal rules.
- **`.exodia.yaml` fails to parse / unknown keys**: stop the run and quote the offending line. Do not fall back silently to flat mode; the user wrote the file expecting it to apply, so a silent fallback hides the bug. Print the rule that failed (1-6 in `SKILL.md` § Step 0a).
- **Group / category name collision**: a name like `engineering` cannot appear as both a group and a category leaf. Validation rule 3 rejects it; ask the user to rename one.
- **Leaf duplicated across paths** (e.g. `architecture` listed under `engineering/` and `product/`): rejected by rule 4; categories are uniquely placed.
- **Drift detected**: `.exodia.yaml` lists a leaf at one path but disk has it elsewhere. Surface a per-move prompt; never auto-move. If the user skips a move, leave the file/disk mismatch in place and warn — `AGENTS.md` re-emit will reflect the file's intent and break router links until the move is applied.
- **Orphan on disk**: a directory under `$CONTEXT_DIR/` carries `<!-- exodia:section:` markers but the leaf is not in `.exodia.yaml`. Prompt with `Keep in place` / `Move to root` / `Delete`. The delete branch always requires a second confirmation prompt before any `rm -rf`.
- **Missing `purpose` in custom-category map**: rule 5 fails. Ask the user to add a non-empty `purpose:` string before re-running.
