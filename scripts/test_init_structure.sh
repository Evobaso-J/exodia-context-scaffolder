#!/usr/bin/env bash
# test_init_structure.sh: smoke tests for scripts/init_structure.sh.
#
# Run from anywhere. Exits 0 on pass, non-zero with the first failing
# assertion echoed to stderr. No external test framework needed.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
INIT="$SCRIPT_DIR/init_structure.sh"

if [[ ! -x "$INIT" && ! -f "$INIT" ]]; then
  echo "FAIL: cannot find $INIT" >&2
  exit 1
fi

pass=0
fail=0

assert_file () {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    echo "FAIL: missing file $path" >&2
    fail=$((fail + 1))
    return 1
  fi
  pass=$((pass + 1))
}

assert_dir () {
  local path="$1"
  if [[ ! -d "$path" ]]; then
    echo "FAIL: missing dir $path" >&2
    fail=$((fail + 1))
    return 1
  fi
  pass=$((pass + 1))
}

assert_exit_code () {
  local expected="$1"
  local actual="$2"
  local label="$3"
  if [[ "$expected" -ne "$actual" ]]; then
    echo "FAIL: $label expected exit $expected, got $actual" >&2
    fail=$((fail + 1))
    return 1
  fi
  pass=$((pass + 1))
}

# Test 1: bare names (backwards compat).
TMP=$(mktemp -d)
bash "$INIT" "$TMP" context architecture patterns >/dev/null
assert_file "$TMP/context/architecture/ARCHITECTURE.md"
assert_file "$TMP/context/architecture/decisions.jsonl"
assert_file "$TMP/context/patterns/PATTERNS.md"
assert_file "$TMP/context/patterns/reviews.jsonl"
rm -rf "$TMP"

# Test 2: multi-segment paths (canonical leaves under groups).
TMP=$(mktemp -d)
bash "$INIT" "$TMP" context engineering/architecture engineering/patterns product/domain >/dev/null
assert_file "$TMP/context/engineering/architecture/ARCHITECTURE.md"
assert_file "$TMP/context/engineering/architecture/decisions.jsonl"
assert_file "$TMP/context/engineering/patterns/PATTERNS.md"
assert_file "$TMP/context/engineering/patterns/reviews.jsonl"
assert_file "$TMP/context/product/domain/DOMAIN.md"
assert_file "$TMP/context/product/domain/glossary.yaml"
rm -rf "$TMP"

# Test 3: deep nesting (three levels) with canonical leaf.
TMP=$(mktemp -d)
bash "$INIT" "$TMP" context engineering/backend/services/architecture >/dev/null
assert_file "$TMP/context/engineering/backend/services/architecture/ARCHITECTURE.md"
assert_file "$TMP/context/engineering/backend/services/architecture/decisions.jsonl"
rm -rf "$TMP"

# Test 4: custom (no template) under a group falls back to stub L2 only.
TMP=$(mktemp -d)
bash "$INIT" "$TMP" context engineering/perf >/dev/null
assert_file "$TMP/context/engineering/perf/PERF.md"
if ls "$TMP/context/engineering/perf/"*.jsonl 2>/dev/null | grep -q .; then
  echo "FAIL: custom category should not auto-seed L3 jsonl files" >&2
  fail=$((fail + 1))
else
  pass=$((pass + 1))
fi
rm -rf "$TMP"

# Test 5: optional categories resolve via templates/optional/<leaf>.
TMP=$(mktemp -d)
bash "$INIT" "$TMP" context platform/infra >/dev/null
assert_file "$TMP/context/platform/infra/INFRA.md"
assert_file "$TMP/context/platform/infra/decisions.jsonl"
assert_file "$TMP/context/platform/infra/runbooks.jsonl"
rm -rf "$TMP"

# Test 6: invalid path segments are rejected.
TMP=$(mktemp -d)
set +e
bash "$INIT" "$TMP" context "Foo/bar" >/dev/null 2>&1
rc=$?
set -e
assert_exit_code 65 "$rc" "uppercase segment rejected"

set +e
bash "$INIT" "$TMP" context "../etc" >/dev/null 2>&1
rc=$?
set -e
assert_exit_code 65 "$rc" "'..' rejected"

set +e
bash "$INIT" "$TMP" context "/abs" >/dev/null 2>&1
rc=$?
set -e
assert_exit_code 65 "$rc" "absolute path rejected"

set +e
bash "$INIT" "$TMP" context "foo//bar" >/dev/null 2>&1
rc=$?
set -e
assert_exit_code 65 "$rc" "empty segment rejected"
rm -rf "$TMP"

echo "pass=$pass fail=$fail"
[[ "$fail" -eq 0 ]]
