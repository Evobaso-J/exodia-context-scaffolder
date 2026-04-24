#!/usr/bin/env bash
# install_hook.sh — install the Claude Code Stop hook that reinforces the Self-Update Rules.
#
# Usage:
#   install_hook.sh <target-dir> <context-dir>
#
# <context-dir> is the name of the context directory the scaffold used
# (e.g. "context", "docs", ".agents"). The hook source contains
# {{CONTEXT_DIR}} placeholders that are substituted with this value
# at install time so the reminder text points to the right paths.
#
# Idempotent. Creates .claude/hooks/exodia-stop-reminder.sh and registers
# it in .claude/settings.json under hooks.Stop.

set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 <target-dir> <context-dir>" >&2
  exit 64
fi

TARGET="$1"
CONTEXT_DIR="$2"
SKILL_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
HOOK_SRC="$SKILL_DIR/hooks/stop-reminder.sh"

if [[ ! -f "$HOOK_SRC" ]]; then
  echo "error: source hook not found at $HOOK_SRC" >&2
  exit 66
fi

if [[ -z "$CONTEXT_DIR" || "$CONTEXT_DIR" == "." || "$CONTEXT_DIR" == ".." ]]; then
  echo "error: invalid context dir name: '$CONTEXT_DIR'" >&2
  exit 65
fi
context_dir_re='^[a-z._-][a-z0-9._-]*$'
if [[ ! "$CONTEXT_DIR" =~ $context_dir_re ]]; then
  echo "error: invalid context dir name: '$CONTEXT_DIR' (must match $context_dir_re)" >&2
  exit 65
fi

mkdir -p "$TARGET/.claude/hooks"
HOOK_DEST="$TARGET/.claude/hooks/exodia-stop-reminder.sh"
cp "$HOOK_SRC" "$HOOK_DEST"
# Substitute {{CONTEXT_DIR}} placeholder with the chosen value.
# -i.bak is used for cross-platform (macOS + GNU) compatibility;
# the backup is removed right after.
sed -i.bak "s|{{CONTEXT_DIR}}|${CONTEXT_DIR}|g" "$HOOK_DEST"
rm -f "${HOOK_DEST}.bak"
chmod +x "$HOOK_DEST"
echo "installed: $HOOK_DEST"

SETTINGS="$TARGET/.claude/settings.json"
if [[ ! -f "$SETTINGS" ]]; then
  cat > "$SETTINGS" <<'EOF'
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": ".claude/hooks/exodia-stop-reminder.sh" }
        ]
      }
    ]
  }
}
EOF
  echo "created: $SETTINGS"
  exit 0
fi

# Use python to merge into existing settings.json to avoid destroying other hooks.
python3 - "$SETTINGS" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))

if not isinstance(data, dict):
    print(
        f"error: {path} top level is {type(data).__name__}, expected object. "
        "Refusing to merge.",
        file=sys.stderr,
    )
    sys.exit(65)

hooks = data.setdefault("hooks", {})
if not isinstance(hooks, dict):
    print(
        f"error: {path} 'hooks' is {type(hooks).__name__}, expected object. "
        "Refusing to merge — fix the settings shape manually.",
        file=sys.stderr,
    )
    sys.exit(65)

stop_entries = hooks.get("Stop")
if stop_entries is None:
    stop_entries = []
    hooks["Stop"] = stop_entries
elif not isinstance(stop_entries, list):
    print(
        f"error: {path} 'hooks.Stop' is {type(stop_entries).__name__}, "
        "expected list. Refusing to merge — the Claude Code settings schema "
        "requires an array here. Fix manually and re-run.",
        file=sys.stderr,
    )
    sys.exit(65)

command = ".claude/hooks/exodia-stop-reminder.sh"

def already_registered(entries):
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        for h in entry.get("hooks", []):
            if isinstance(h, dict) and h.get("command") == command:
                return True
    return False

if not already_registered(stop_entries):
    stop_entries.append({
        "matcher": "",
        "hooks": [{"type": "command", "command": command}],
    })
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"updated: {path}")
else:
    print(f"already registered in: {path}")
PY
