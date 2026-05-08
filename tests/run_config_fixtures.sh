#!/usr/bin/env bash
# Validation harness: runs scripts/parse_config.py against every fixture in
# tests/fixtures/configs/ and asserts the expected exit code and (for
# invalid- fixtures) error pattern.
#
# Usage:
#   tests/run_config_fixtures.sh            # exit non-zero on any failure
#   tests/run_config_fixtures.sh --verbose  # print pass/fail per fixture

set -u

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
FIXTURES="$SCRIPT_DIR/fixtures/configs"
PARSE="$REPO_DIR/scripts/parse_config.py"

VERBOSE="${1:-}"
FAIL=0
PASS=0

run_case () {
  local fixture="$1"
  local expected_code="$2"
  local expected_pattern="${3:-}"

  local stderr_file
  stderr_file="$(mktemp)"
  python3 "$PARSE" "$fixture" >/dev/null 2>"$stderr_file"
  local actual_code=$?

  local label
  label="$(basename "$fixture")"

  if [[ "$actual_code" -ne "$expected_code" ]]; then
    echo "FAIL: $label expected exit $expected_code, got $actual_code" >&2
    cat "$stderr_file" >&2
    rm -f "$stderr_file"
    FAIL=$((FAIL + 1))
    return
  fi

  if [[ -n "$expected_pattern" ]]; then
    if ! grep -q -- "$expected_pattern" "$stderr_file"; then
      echo "FAIL: $label expected stderr to match '$expected_pattern'" >&2
      cat "$stderr_file" >&2
      rm -f "$stderr_file"
      FAIL=$((FAIL + 1))
      return
    fi
  fi

  rm -f "$stderr_file"
  PASS=$((PASS + 1))
  if [[ "$VERBOSE" == "--verbose" ]]; then
    echo "ok: $label"
  fi
}

# Valid fixtures: exit 0.
run_case "$FIXTURES/weroad.yaml"      0
run_case "$FIXTURES/drop-only.yaml"   0
run_case "$FIXTURES/custom-only.yaml" 0

# Invalid fixtures: exit 65, with a discriminating error line.
run_case "$FIXTURES/invalid-overlap.yaml"   65 "share path"
run_case "$FIXTURES/invalid-prefix.yaml"    65 "prefix of"
run_case "$FIXTURES/invalid-traversal.yaml" 65 "must not contain '..'"
run_case "$FIXTURES/invalid-regex.yaml"     65 "must match"

echo "passed: $PASS  failed: $FAIL"
exit "$FAIL"
