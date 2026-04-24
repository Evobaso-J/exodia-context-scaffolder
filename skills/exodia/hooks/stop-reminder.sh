#!/usr/bin/env bash
# exodia-stop-reminder.sh — Claude Code Stop hook.
#
# Emits a short reminder at turn end so the agent applies the Self-Update Rules
# before handing control back. This reinforces (does not replace) the prose
# rules already embedded in AGENTS.md.
#
# The hook writes a non-blocking advisory message to stderr, which Claude Code
# surfaces to the agent as context for the current stop event.

set -euo pipefail

cat >&2 <<'EOF'
[exodia] Before ending: walk AGENTS.md §Self-Update Rules.
If the turn produced any of these signals, append an entry NOW:
  • new bug root cause        → {{CONTEXT_DIR}}/debugging/playbooks.jsonl
  • new gotcha / footgun       → {{CONTEXT_DIR}}/debugging/gotchas.jsonl
  • new architecture decision  → {{CONTEXT_DIR}}/architecture/decisions.jsonl
  • new PR review lesson       → {{CONTEXT_DIR}}/patterns/reviews.jsonl
  • clarified domain term      → {{CONTEXT_DIR}}/domain/glossary.yaml
  • new variant behavior       → {{CONTEXT_DIR}}/operations/variants.yaml
Branch-scoped dedup: if an entry on the same topic was added on the current branch,
replace in-place (same ID). Do not ask permission — the user can revert via git.
If nothing qualifies: skip.
EOF

exit 0
