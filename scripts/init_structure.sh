#!/usr/bin/env bash
# init_structure.sh: create context tree and copy templates into the target repo.
#
# Usage:
#   init_structure.sh <target-dir> <context-dir> <category1> [category2 ...]
#
# <context-dir> is the directory name inside <target-dir> that will hold the
# tree (e.g. "context", "docs", "knowledge", ".agents", "ai"). Must match
# ^[a-z._-][a-z0-9._-]*$ and must not be "." or "..".
#
# <categoryN> names each match ^[a-z][a-z0-9_-]*$ (lowercase, safe filesystem
# segment). The canonical five (architecture, patterns, domain, operations,
# debugging) are the default starter set but not enforced; the target repo
# picks its own shape. Additional documented categories (mobile, workspace,
# data, infra) and any custom names are accepted on the same regex.

set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "usage: $0 <target-dir> <context-dir> <category> [category ...]" >&2
  exit 64
fi

TARGET="$1"
CONTEXT_DIR="$2"
shift 2
CATEGORIES=("$@")

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

# Reject category names that could escape the context dir or otherwise
# produce surprising paths. Allow: lowercase letters, digits, dashes,
# underscores. Must start with a letter. Refuses "../etc", "/abs/path",
# "foo/bar", "", and whitespace.
category_re='^[a-z][a-z0-9_-]*$'
for c in "${CATEGORIES[@]}"; do
  if [[ ! "$c" =~ $category_re ]]; then
    echo "error: invalid category name: '$c' (must match $category_re)" >&2
    exit 65
  fi
done

mkdir -p "$TARGET/$CONTEXT_DIR"

copy_category () {
  local cat="$1"
  local src_dir="$TEMPLATES/$cat"

  # Optional categories live under templates/optional/<cat>
  if [[ ! -d "$src_dir" && -d "$TEMPLATES/optional/$cat" ]]; then
    src_dir="$TEMPLATES/optional/$cat"
  fi

  if [[ ! -d "$src_dir" ]]; then
    # Custom category: create an empty L2 stub and no L3 data.
    mkdir -p "$TARGET/$CONTEXT_DIR/$cat"
    local upper
    upper="$(printf '%s' "$cat" | tr '[:lower:]' '[:upper:]')"
    cat > "$TARGET/$CONTEXT_DIR/$cat/${upper}.md" <<EOF
# ${upper}

<!-- exodia:section:intro -->
TODO: describe what this module covers.
EOF
    echo "created custom category: $cat"
    return
  fi

  mkdir -p "$TARGET/$CONTEXT_DIR/$cat"
  while IFS= read -r -d '' tmpl; do
    local base
    base="$(basename "$tmpl" .tmpl)"
    local dest="$TARGET/$CONTEXT_DIR/$cat/$base"
    if [[ -e "$dest" ]]; then
      echo "skip (exists): $dest"
      continue
    fi
    cp "$tmpl" "$dest"
    echo "wrote: $dest"
  done < <(find "$src_dir" -maxdepth 1 -type f -name '*.tmpl' -print0)
}

for cat in "${CATEGORIES[@]}"; do
  copy_category "$cat"
done

echo "done. $CONTEXT_DIR/ initialized at $TARGET/$CONTEXT_DIR"
