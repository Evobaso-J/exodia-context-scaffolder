#!/usr/bin/env bash
# init_structure.sh: create context tree and copy templates into the target repo.
#
# Usage:
#   init_structure.sh <target-dir> <context-dir> <path1> [path2 ...]
#
# <context-dir> is the directory name inside <target-dir> that will hold the
# tree (e.g. "context", "docs", "knowledge", ".agents", "ai"). Must match
# ^[a-z._-][a-z0-9._-]*$ and must not be "." or "..".
#
# <pathN> is a relative path under <context-dir> (e.g. "architecture",
# "engineering/architecture", "product/domain/glossary-area"). Each "/"-
# separated segment must match ^[a-z][a-z0-9_-]*$. Bare names (one segment)
# behave exactly like the previous bare-category form. The leaf (last
# segment) is treated as the canonical category name for template lookup;
# parent segments are user-named groups and have no template semantics.

set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "usage: $0 <target-dir> <context-dir> <path> [path ...]" >&2
  exit 64
fi

TARGET="$1"
CONTEXT_DIR="$2"
shift 2
PATHS=("$@")

SKILL_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATES="$SKILL_DIR/templates"

if [[ ! -d "$TARGET" ]]; then
  echo "error: target dir does not exist: $TARGET" >&2
  exit 66
fi

# Validate context-dir: single safe filesystem segment.
if [[ -z "$CONTEXT_DIR" || "$CONTEXT_DIR" == "." || "$CONTEXT_DIR" == ".." ]]; then
  echo "error: invalid context dir name: '$CONTEXT_DIR'" >&2
  exit 65
fi
context_dir_re='^[a-z._-][a-z0-9._-]*$'
if [[ ! "$CONTEXT_DIR" =~ $context_dir_re ]]; then
  echo "error: invalid context dir name: '$CONTEXT_DIR' (must match $context_dir_re)" >&2
  exit 65
fi

# Per-segment regex. Same shape as the old category_re; applied to every
# slash-separated segment of the path (groups + leaf).
segment_re='^[a-z][a-z0-9_-]*$'
for p in "${PATHS[@]}"; do
  if [[ -z "$p" || "$p" == /* || "$p" == */ || "$p" == *//* ]]; then
    echo "error: invalid path: '$p' (no leading/trailing slashes, no empty segments)" >&2
    exit 65
  fi
  if [[ "$p" == *..* ]]; then
    case "/$p/" in
      */../*) echo "error: invalid path: '$p' (no '..' segments)" >&2; exit 65 ;;
    esac
  fi
  IFS='/' read -r -a _segs <<< "$p"
  for seg in "${_segs[@]}"; do
    if [[ ! "$seg" =~ $segment_re ]]; then
      echo "error: invalid path segment: '$seg' in '$p' (each segment must match $segment_re)" >&2
      exit 65
    fi
  done
done

mkdir -p "$TARGET/$CONTEXT_DIR"

copy_path () {
  local rel="$1"
  local leaf="${rel##*/}"
  local src_dir="$TEMPLATES/$leaf"
  local dest_dir="$TARGET/$CONTEXT_DIR/$rel"

  # Optional categories live under templates/optional/<leaf>
  if [[ ! -d "$src_dir" && -d "$TEMPLATES/optional/$leaf" ]]; then
    src_dir="$TEMPLATES/optional/$leaf"
  fi

  if [[ ! -d "$src_dir" ]]; then
    # Custom category: create an empty L2 stub at the resolved path and no L3 data.
    mkdir -p "$dest_dir"
    local upper
    upper="$(printf '%s' "$leaf" | tr '[:lower:]' '[:upper:]')"
    cat > "$dest_dir/${upper}.md" <<EOF
# ${upper}

<!-- exodia:section:intro -->
TODO: describe what this module covers.
EOF
    echo "created custom category: $rel"
    return
  fi

  mkdir -p "$dest_dir"
  while IFS= read -r -d '' tmpl; do
    local base
    base="$(basename "$tmpl" .tmpl)"
    local dest="$dest_dir/$base"
    if [[ -e "$dest" ]]; then
      echo "skip (exists): $dest"
      continue
    fi
    cp "$tmpl" "$dest"
    echo "wrote: $dest"
  done < <(find "$src_dir" -maxdepth 1 -type f -name '*.tmpl' -print0)
}

for p in "${PATHS[@]}"; do
  copy_path "$p"
done

echo "done. $CONTEXT_DIR/ initialized at $TARGET/$CONTEXT_DIR"
