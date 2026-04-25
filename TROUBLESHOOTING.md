# Troubleshooting

Runtime failure modes for the `/exodia` scaffolder. Read this only when one of the listed conditions is hit during a run.

- **User aborts mid-interview**: leave the repo in whatever partial state exists. No need to roll back. Running `/exodia` again resumes from preflight.
- **Explore scan times out / returns garbage**: fall back to asking the user to confirm the stack and architecture directly, then continue.
- **Target repo has committed secrets or `.env` with real values**: never echo these in drafts. If you must reference env vars, name them only.
- **No git, no agent integration, no lint scripts**: skill still works; just emits the minimal universal rules.
