#!/usr/bin/env bash
# init_structure.sh: create context tree and copy templates into the target repo.
#
# Two invocation shapes:
#
#   1. Legacy (no config): public, hand-invokable. All categories live under
#      a single context dir.
#        init_structure.sh <target-dir> <context-dir> <category1> [category2 ...]
#
#   2. Config-driven: scaffolder-internal, signalled by `--pairs`. Intended
#      to be invoked by the /exodia scaffolder pipeline, not by hand. The
#      scaffolder always runs `parse_config.py` first, which is the single
#      source of truth for path-shape rules (regex, no "..", no leading or
#      trailing "/", no shared paths, no prefix nesting). This mode trusts
#      its caller and performs only the structural `name=path` check.
#        init_structure.sh <target-dir> --pairs <name1>=<path1> [<name2>=<path2> ...]
#
#      <pathN> is repo-rooted relative to <target-dir>. Each path is created
#      with `mkdir -p`. Templates from $SKILL_DIR/templates/<name>/ are copied
#      in by canonical name. Names not matching any canonical template dir
#      produce an empty L2 stub with the default skeleton (## Purpose, ## Key
#      Files, ## L3 Data).
#
# In both shapes, existing destination files are left untouched.
#
# Validation:
#   - context-dir name (legacy): ^[a-z._-][a-z0-9._-]*$, not "." or "..".
#   - category name (legacy):    ^[a-z][a-z0-9_-]*$.
#   - --pairs (config-driven):   delegated to `parse_config.py`. See that
#                                file for path/name/L3 regexes and the
#                                shared-path / prefix-nesting invariants.

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <target-dir> <context-dir> <category> [...]" >&2
  echo "       $0 <target-dir> --pairs <name>=<path> [...]" >&2
  exit 64
fi

TARGET="$1"
shift

SKILL_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATES="$SKILL_DIR/templates"

if [[ ! -d "$TARGET" ]]; then
  echo "error: target dir does not exist: $TARGET" >&2
  exit 66
fi

# Locate the source template dir for a canonical category. Returns empty
# string for custom categories (no templates).
template_dir_for () {
  local cat="$1"
  if [[ -d "$TEMPLATES/$cat" ]]; then
    printf '%s' "$TEMPLATES/$cat"
    return
  fi
  printf ''
}

# Materialize one category at a given absolute path.
copy_category_to () {
  local cat="$1" abs_dest="$2"
  local src_dir
  src_dir="$(template_dir_for "$cat")"

  mkdir -p "$abs_dest"

  if [[ -z "$src_dir" ]]; then
    # Custom category: write a default L2 stub if it does not yet exist.
    local upper
    upper="$(printf '%s' "$cat" | tr '[:lower:]' '[:upper:]')"
    local stub="$abs_dest/${upper}.md"
    if [[ -e "$stub" ]]; then
      echo "skip (exists): $stub"
    else
      cat > "$stub" <<EOF
# ${upper}

<!-- exodia:section:intro -->
TODO: describe what this module covers.

<!-- exodia:section:purpose -->
## Purpose

TODO

<!-- exodia:section:key-files -->
## Key Files

TODO

<!-- exodia:section:l3 -->
## L3 Data

TODO
EOF
      echo "wrote: $stub"
    fi
    return
  fi

  while IFS= read -r -d '' tmpl; do
    local base dest
    base="$(basename "$tmpl" .tmpl)"
    dest="$abs_dest/$base"
    if [[ -e "$dest" ]]; then
      echo "skip (exists): $dest"
      continue
    fi
    cp "$tmpl" "$dest"
    echo "wrote: $dest"
  done < <(find "$src_dir" -maxdepth 1 -type f -name '*.tmpl' -print0)

  # Mirror template subdirs (e.g. design-patterns/docs/ for progressive
  # disclosure). Created at init time so the empty subdir is committable;
  # contents are populated later by Step 6 draft. Inner files that are not
  # .tmpl (e.g. .gitkeep) are copied verbatim and never overwritten.
  while IFS= read -r -d '' subdir; do
    local rel destsub
    rel="${subdir#$src_dir/}"
    destsub="$abs_dest/$rel"
    mkdir -p "$destsub"
    while IFS= read -r -d '' f; do
      local fdest
      fdest="$destsub/$(basename "$f")"
      if [[ -e "$fdest" ]]; then
        echo "skip (exists): $fdest"
        continue
      fi
      cp "$f" "$fdest"
      echo "wrote: $fdest"
    done < <(find "$subdir" -maxdepth 1 -type f ! -name '*.tmpl' -print0)
  done < <(find "$src_dir" -mindepth 1 -maxdepth 1 -type d -print0)
}

# ---------- dispatch ----------

if [[ "${1:-}" == "--pairs" ]]; then
  shift
  if [[ $# -lt 1 ]]; then
    echo "error: --pairs requires at least one <name>=<path> pair" >&2
    exit 64
  fi
  # Path/name shape (regex, "..", leading/trailing "/", shared paths,
  # prefix nesting) is enforced upstream by parse_config.py. This mode
  # is scaffolder-internal; trust the caller and do only the structural
  # `name=path` parse check.
  for pair in "$@"; do
    if [[ "$pair" != *=* ]]; then
      echo "error: malformed pair (expected name=path): '$pair'" >&2
      exit 65
    fi
    name="${pair%%=*}"
    path="${pair#*=}"
    if [[ -z "$name" || -z "$path" ]]; then
      echo "error: malformed pair (empty name or path): '$pair'" >&2
      exit 65
    fi
    copy_category_to "$name" "$TARGET/$path"
  done
  echo "done. $# categor$([[ $# -eq 1 ]] && echo y || echo ies) materialized at config-declared paths"
  exit 0
fi

# Legacy positional shape: <target> <context-dir> <category...>
CONTEXT_DIR="$1"
shift
CATEGORIES=("$@")

if [[ ${#CATEGORIES[@]} -lt 1 ]]; then
  echo "usage: $0 <target-dir> <context-dir> <category> [category ...]" >&2
  exit 64
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

category_re='^[a-z][a-z0-9_-]*$'
for c in "${CATEGORIES[@]}"; do
  if [[ ! "$c" =~ $category_re ]]; then
    echo "error: invalid category name: '$c' (must match $category_re)" >&2
    exit 65
  fi
done

mkdir -p "$TARGET/$CONTEXT_DIR"

for cat in "${CATEGORIES[@]}"; do
  copy_category_to "$cat" "$TARGET/$CONTEXT_DIR/$cat"
done

echo "done. $CONTEXT_DIR/ initialized at $TARGET/$CONTEXT_DIR"
