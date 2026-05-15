#!/usr/bin/env python3
"""Parse and validate `exodia.config.yaml`.

Reads the throwaway opt-in config that drives layout customization for the
`/exodia` scaffolder. Emits a JSON document on stdout describing the resolved
shape; emits line-numbered errors on stderr and exits non-zero on validation
failure.

Schema (see README "Customizing the layout" section for the full reference):

    context_dir: docs/project          # default root for canonical categories
    categories:
      operations: { drop: true }       # remove canonical category
      releases:                        # custom category (non-canonical name)
        path: docs/releases
        custom: true
        description: "Release notes per published version"  # optional one-line purpose
        l3: [release_notes.jsonl, runbook.md]  # optional override; jsonl/yaml outside canonical registry -> model writes schema; .md -> prose deep-dive

Validation rules:
  1. `path` matches `^[a-z._-][a-z0-9._/-]*$`, no `..`, no leading or trailing `/`.
  2. No two categories share `path`.
  3. No category path is a prefix of another's path.
  4. Custom category (non-canonical name) without `custom: true` -> reject.
  5. `drop: true` combined with any other field -> reject.
  6. `l3` filename matches `^[a-z][a-z0-9_-]*\\.(yaml|jsonl|md)$`; reject other extensions.
     `.md` entries are standalone markdown deep-dives (no schema header, no Step 9 seeding),
     populated as prose during Step 6 alongside the L2 draft.
  7. `description` is a single-line non-empty string of length <= 200.

Stdlib-only: parses a deliberately small YAML subset (mappings, scalar
strings/bools, inline `{}` and `[]` collections, comments). Sufficient for
the config schema above.

Usage:
    parse_config.py <path-to-exodia.config.yaml>
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

# scripts/yaml_subset.py is the shared YAML reader used by both this
# validator and `resolve_layout.py`. Both run as scripts from the `scripts/`
# directory, so Python adds that directory to `sys.path` automatically.
from yaml_subset import ConfigError, parse_yaml_subset

# Core canonical set: the five curated categories the scaffolder ships
# templates and ledger schemas for. Tuple order drives L2 draft order in
# protocol/06-draft-l2.md and the auto-add set when a config is present.
# This is the canonical recognized set, period: any name outside it requires
# `custom: true` in `exodia.config.yaml`.
DEFAULT_CATEGORIES = ("architecture", "design-patterns", "glossary", "operations", "debugging")


# Parse-time validation set: category names that do not require `custom: true`.
RECOGNIZED_CATEGORIES = set(DEFAULT_CATEGORIES)

PATH_RE = re.compile(r"^[a-z._-][a-z0-9._/-]*$")
L3_FILENAME_RE = re.compile(r"^[a-z][a-z0-9_-]*\.(yaml|jsonl|md)$")
CATEGORY_NAME_RE = re.compile(r"^[a-z][a-z0-9_-]*$")
DESCRIPTION_MAX_LEN = 200


# ---------- validation ----------


def _validate_path(path: str, line: int) -> None:
    if path.startswith("/"):
        raise ConfigError(f"path must not start with '/': '{path}'", line)
    if path.endswith("/"):
        raise ConfigError(f"path must not end with '/': '{path}'", line)
    if ".." in path.split("/"):
        raise ConfigError(f"path must not contain '..': '{path}'", line)
    if not PATH_RE.match(path):
        raise ConfigError(f"path must match {PATH_RE.pattern}: '{path}'", line)


def _validate_l3_filename(name: str, line: int) -> None:
    if not L3_FILENAME_RE.match(name):
        raise ConfigError(f"l3 filename must match {L3_FILENAME_RE.pattern}: '{name}'", line)


def _validate_description(text: object, line: int) -> None:
    if not isinstance(text, str):
        raise ConfigError(f"description must be a string, got {type(text).__name__}", line)
    if not text:
        raise ConfigError("description must not be empty", line)
    if "\n" in text or "\r" in text:
        raise ConfigError("description must be a single line (no newlines)", line)
    if len(text) > DESCRIPTION_MAX_LEN:
        raise ConfigError(
            f"description must be <= {DESCRIPTION_MAX_LEN} chars (got {len(text)})", line
        )


def validate(parsed: dict[str, Any]) -> dict[str, Any]:
    errors: list[ConfigError] = []
    for key in parsed:
        if key not in ("context_dir", "categories"):
            errors.append(ConfigError(f"unknown top-level key: '{key}'"))

    context_dir = parsed.get("context_dir", "context")
    if not isinstance(context_dir, str) or not context_dir:
        errors.append(ConfigError(f"context_dir must be a non-empty string, got {context_dir!r}"))
        context_dir = "context"
    else:
        try:
            _validate_path(context_dir, line=0)
        except ConfigError as e:
            errors.append(e)

    raw_categories = parsed.get("categories") or {}
    if not isinstance(raw_categories, dict):
        errors.append(ConfigError("categories must be a mapping"))
        raw_categories = {}

    resolved: list[dict[str, Any]] = []
    for name, body in raw_categories.items():
        if not CATEGORY_NAME_RE.match(name):
            errors.append(ConfigError(f"invalid category name: '{name}' (must match {CATEGORY_NAME_RE.pattern})"))
            continue
        body = body or {}
        if not isinstance(body, dict):
            errors.append(ConfigError(f"category '{name}' body must be a mapping"))
            continue
        for k in body:
            if k not in ("path", "drop", "custom", "l3", "description"):
                errors.append(ConfigError(f"category '{name}': unknown field '{k}'"))

        drop = bool(body.get("drop", False))
        custom_flag = bool(body.get("custom", False))
        path = body.get("path")
        l3 = body.get("l3")
        description = body.get("description")

        if drop and (
            path is not None or custom_flag or l3 is not None or description is not None
        ):
            errors.append(ConfigError(f"category '{name}': 'drop: true' is mutually exclusive with other fields"))
            continue

        is_canonical = name in RECOGNIZED_CATEGORIES
        if not is_canonical and not custom_flag and not drop:
            errors.append(
                ConfigError(
                    f"category '{name}': non-canonical name requires 'custom: true' "
                    f"(canonical set: {sorted(RECOGNIZED_CATEGORIES)})"
                )
            )
            continue

        if path is not None:
            if not isinstance(path, str):
                errors.append(ConfigError(f"category '{name}': 'path' must be a string"))
                continue
            try:
                _validate_path(path, line=0)
            except ConfigError as e:
                errors.append(ConfigError(f"category '{name}': {e}"))
                continue

        if l3 is not None:
            if not isinstance(l3, list) or not all(isinstance(x, str) for x in l3):
                errors.append(ConfigError(f"category '{name}': 'l3' must be a list of filename strings"))
                continue
            for fname in l3:
                try:
                    _validate_l3_filename(fname, line=0)
                except ConfigError as e:
                    errors.append(ConfigError(f"category '{name}': {e}"))

        if description is not None:
            try:
                _validate_description(description, line=0)
            except ConfigError as e:
                errors.append(ConfigError(f"category '{name}': {e}"))
                continue

        if drop:
            resolved.append(
                {
                    "name": name,
                    "path": None,
                    "kind": "canonical",
                    "l3_override": None,
                    "description": None,
                    "drop": True,
                }
            )
            continue

        resolved_path = path if path is not None else f"{context_dir}/{name}"
        kind = "custom" if custom_flag else "canonical"
        resolved.append(
            {
                "name": name,
                "path": resolved_path,
                "kind": kind,
                "l3_override": list(l3) if l3 is not None else None,
                "description": description if description is not None else None,
                "drop": False,
            }
        )

    declared = {c["name"] for c in resolved}
    for default_name in DEFAULT_CATEGORIES:
        if default_name not in declared:
            resolved.append(
                {
                    "name": default_name,
                    "path": f"{context_dir}/{default_name}",
                    "kind": "canonical",
                    "l3_override": None,
                    "description": None,
                    "drop": False,
                }
            )

    active = [c for c in resolved if not c["drop"]]
    seen: dict[str, str] = {}
    for cat in active:
        p = cat["path"]
        if p in seen:
            errors.append(ConfigError(f"categories '{seen[p]}' and '{cat['name']}' share path '{p}'"))
        else:
            seen[p] = cat["name"]

    sorted_active = sorted(active, key=lambda c: c["path"])
    for i, cat in enumerate(sorted_active):
        for other in sorted_active[i + 1 :]:
            if other["path"] == cat["path"]:
                continue
            if other["path"].startswith(cat["path"] + "/"):
                errors.append(
                    ConfigError(
                        f"category '{cat['name']}' path '{cat['path']}' is a prefix of "
                        f"category '{other['name']}' path '{other['path']}'"
                    )
                )

    if errors:
        raise ConfigErrorList(errors)

    return {"context_dir": context_dir, "categories": resolved}


class ConfigErrorList(Exception):
    def __init__(self, errors: list[ConfigError]) -> None:
        self.errors = errors
        super().__init__(f"{len(errors)} validation error(s)")


# ---------- entrypoint ----------


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: parse_config.py <path>", file=sys.stderr)
        return 64

    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"error: not a file: {path}", file=sys.stderr)
        return 66

    text = path.read_text(encoding="utf-8")
    try:
        parsed = parse_yaml_subset(text)
        resolved = validate(parsed)
    except ConfigError as e:
        prefix = f"{path}:{e.line}: " if e.line else f"{path}: "
        print(f"{prefix}{e}", file=sys.stderr)
        return 65
    except ConfigErrorList as bundle:
        for e in bundle.errors:
            prefix = f"{path}:{e.line}: " if e.line else f"{path}: "
            print(f"{prefix}{e}", file=sys.stderr)
        return 65

    json.dump(resolved, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
