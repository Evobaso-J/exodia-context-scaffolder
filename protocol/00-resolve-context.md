# Step 0: Resolve context

Applies in all modes.

- Confirm `$TARGET` = current working directory.
- Confirm `$SKILL_DIR` = directory of `SKILL.md`. If you cannot resolve it, fall back to `~/.claude/skills/exodia`.
- Hold a variable `$CONTEXT_DIR` throughout the run. It names the directory that will hold the context tree inside `$TARGET`. Default is `context`; the user may pick another name in Step 3a (Fresh / Merge) or it is auto-detected in Step 1 (Incremental).
- Resolve `$CONFIG_PATH = $TARGET/exodia.config.yaml`. If the file exists, the run is **config-driven**: layout comes from the config rather than from interactive prompts. If absent, the interactive flow runs unchanged. Config is throwaway and only consumed at first scaffold (Fresh or Merge); incremental re-runs ignore it. Schema reference: see the "Customizing the layout" section in `$SKILL_DIR/README.md`.
