#!/usr/bin/env bash
# symlink_agents.sh — create pointer files that point to AGENTS.md.
#
# Usage:
#   symlink_agents.sh <target-dir> <pointer-path> [pointer-path ...]
#
# Each pointer-path is a repo-relative path (e.g. CLAUDE.md, .cursorrules,
# .github/copilot-instructions.md, or any custom filename your agent
# runtime expects). A symlink back to AGENTS.md is created at each path.
# On filesystems without symlink support (Windows FAT, some WSL mounts),
# or when FORCE_POINTER=1 is set, a one-line pointer file is written
# instead.
#
# Paths must not contain '..' segments and must not be absolute. This
# script does not assume any particular agent runtime — the caller picks.

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <target-dir> <pointer-path> [pointer-path ...]" >&2
  exit 64
fi

TARGET="$1"
shift
POINTERS=("$@")

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

for ptr in "${POINTERS[@]}"; do
  if [[ -z "$ptr" ]]; then
    echo "warn: skipping empty pointer path" >&2
    continue
  fi
  if [[ "$ptr" == /* ]]; then
    echo "warn: skipping absolute pointer path: '$ptr'" >&2
    continue
  fi
  case "$ptr" in
    *'..'*)
      echo "warn: skipping pointer path with '..' segment: '$ptr'" >&2
      continue
      ;;
  esac
  emit_pointer "$ptr"
done

echo "done."
