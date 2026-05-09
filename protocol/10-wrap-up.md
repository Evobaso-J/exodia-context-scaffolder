# Step 10: Wrap up

Applies in all modes (with mode-specific lines noted).

Print a short summary:

- What was created (counts: L2 files, L3 files).
- **Sibling notice (config-driven only).** For each parent directory shared by two or more managed paths (e.g. `docs/domain/` is parent to a managed `glossary/` plus user-owned `handbook/` and `tech/`), list the unmanaged sibling dirs grouped per parent: `Note: docs/domain/ has 2 unmanaged sibling dirs (handbook/, tech/) — left untouched.`. Use `:` or `;` instead of `—` if the surrounding doc style avoids em-dashes.
- **Throwaway-config reminder (config-driven only).** "Delete or gitignore `exodia.config.yaml`. Re-runs read AGENTS.md, not config."
- **Lazy-migration note (Incremental, pre-feature scaffold).** When Step 1 had to inject the router brackets because they were missing, mention it in one line: "Injected `<!-- exodia:router:start/end -->` markers around the router table for future incremental discovery."
- Next steps for the user (how to iterate: just edit the files; the self-update rules handle growth).
- Reminder: running `/exodia` again triggers incremental re-run, not a fresh scaffold.
