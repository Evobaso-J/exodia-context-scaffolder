#!/usr/bin/env bash
# install_hook.sh — install the Claude Code Stop hook that reinforces the Self-Update Rules.
#
# Usage:
#   install_hook.sh <target-dir>
#
# Idempotent. Creates .claude/hooks/exodia-stop-reminder.sh and registers it in
# .claude/settings.json under hooks.Stop.

set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <target-dir>" >&2
  exit 64
fi

TARGET="$1"
SKILL_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
HOOK_SRC="$SKILL_DIR/hooks/stop-reminder.sh"

if [[ ! -f "$HOOK_SRC" ]]; then
  echo "error: source hook not found at $HOOK_SRC" >&2
  exit 66
fi

mkdir -p "$TARGET/.claude/hooks"
HOOK_DEST="$TARGET/.claude/hooks/exodia-stop-reminder.sh"
cp "$HOOK_SRC" "$HOOK_DEST"
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
