#!/usr/bin/env bash
# symlink_agents.sh — create agent pointer files for AGENTS.md.
#
# Usage:
#   symlink_agents.sh <target-dir> <agent1> [agent2 ...]
#
# Supported agents: claude cursor windsurf copilot
#
# On filesystems that don't support symlinks (Windows FAT, some WSL mounts),
# or when FORCE_POINTER=1 is set, write a one-line pointer file instead.

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <target-dir> <agent> [agent ...]" >&2
  exit 64
fi

TARGET="$1"
shift
AGENTS=("$@")

if [[ ! -f "$TARGET/AGENTS.md" ]]; then
  echo "error: $TARGET/AGENTS.md not found. Run /exodia from a repo after the router is written." >&2
  exit 66
fi

supports_symlinks () {
  [[ "${FORCE_POINTER:-0}" != "1" ]] || return 1
  local probe_dir
  probe_dir="$(mktemp -d "$TARGET/.exodia-symlink-probe.XXXXXX")" || return 1
  local rc=1
  if ln -s AGENTS.md "$probe_dir/link" 2>/dev/null; then
    rc=0
  fi
  rm -rf "$probe_dir"
  return $rc
}

emit_pointer () {
  # $1 = relative path to write, pointing to AGENTS.md at the repo root.
  local rel="$1"
  local dir
  dir="$(dirname "$rel")"
  local target_rel
  # Number of "../" hops needed to reach the repo root from $dir.
  if [[ "$dir" == "." ]]; then
    target_rel="AGENTS.md"
  else
    local hops
    hops="$(tr '/' '\n' <<< "$dir" | grep -c . || true)"
    target_rel=""
    for ((i=0; i<hops; i++)); do target_rel+="../"; done
    target_rel+="AGENTS.md"
  fi

  mkdir -p "$TARGET/$dir"
  local path="$TARGET/$rel"
  if [[ -e "$path" || -L "$path" ]]; then
    echo "skip (exists): $path"
    return
  fi

  if supports_symlinks; then
    ( cd "$TARGET/$dir" && ln -s "$target_rel" "$(basename "$rel")" )
    echo "symlinked: $path -> $target_rel"
  else
    printf 'See %s for the canonical instructions.\n' "$target_rel" > "$path"
    echo "pointer: $path"
  fi
}

for agent in "${AGENTS[@]}"; do
  case "$agent" in
    claude)   emit_pointer "CLAUDE.md" ;;
    cursor)   emit_pointer ".cursorrules" ;;
    windsurf) emit_pointer ".windsurfrules" ;;
    copilot)  emit_pointer ".github/copilot-instructions.md" ;;
    *)        echo "warn: unknown agent '$agent' — skipping" >&2 ;;
  esac
done

echo "done."
