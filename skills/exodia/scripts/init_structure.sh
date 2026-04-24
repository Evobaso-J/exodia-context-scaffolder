#!/usr/bin/env bash
# init_structure.sh — create context/ tree and copy templates into the target repo.
#
# Usage:
#   init_structure.sh <target-dir> <category1> [category2 ...]
#
# Core categories (architecture, patterns, domain, operations, debugging) are mandatory.
# Additional categories (mobile, workspace, data, infra, or custom) are optional.

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <target-dir> <category> [category ...]" >&2
  exit 64
fi

TARGET="$1"
shift
CATEGORIES=("$@")

SKILL_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATES="$SKILL_DIR/templates"

if [[ ! -d "$TARGET" ]]; then
  echo "error: target dir does not exist: $TARGET" >&2
  exit 66
fi

mkdir -p "$TARGET/context"

core_categories=(architecture patterns domain operations debugging)

# Validate: every core category must be present in the requested list.
for core in "${core_categories[@]}"; do
  found=0
  for c in "${CATEGORIES[@]}"; do
    if [[ "$c" == "$core" ]]; then found=1; break; fi
  done
  if [[ "$found" -eq 0 ]]; then
    echo "error: core category '$core' missing from requested set" >&2
    exit 65
  fi
done

copy_category () {
  local cat="$1"
  local src_dir="$TEMPLATES/$cat"

  # Optional categories live under templates/optional/<cat>
  if [[ ! -d "$src_dir" && -d "$TEMPLATES/optional/$cat" ]]; then
    src_dir="$TEMPLATES/optional/$cat"
  fi

  if [[ ! -d "$src_dir" ]]; then
    # Custom category: create an empty L2 stub and no L3 data.
    mkdir -p "$TARGET/context/$cat"
    local upper
    upper="$(printf '%s' "$cat" | tr '[:lower:]' '[:upper:]')"
    cat > "$TARGET/context/$cat/${upper}.md" <<EOF
# ${upper}

<!-- exodia:section:intro -->
TODO: describe what this module covers.
EOF
    echo "created custom category: $cat"
    return
  fi

  mkdir -p "$TARGET/context/$cat"
  while IFS= read -r -d '' tmpl; do
    local base
    base="$(basename "$tmpl" .tmpl)"
    local dest="$TARGET/context/$cat/$base"
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

echo "done. context/ initialized at $TARGET/context"
