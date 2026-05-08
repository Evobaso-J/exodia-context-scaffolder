#!/usr/bin/env python3
"""Parse and validate `exodia.config.yaml`.

Reads the throwaway opt-in config that drives layout customization for the
`/exodia` scaffolder. Emits a JSON document on stdout describing the resolved
shape; emits line-numbered errors on stderr and exits non-zero on validation
failure.

Schema (locked design, see docs/plan-config-driven-layout.md):

    context_dir: docs/project          # default root for canonical categories
    categories:
      domain:     { drop: true }       # remove canonical category
      operations: { drop: true }
      glossary:                        # custom category
        path: docs/domain/glossary
        custom: true
        l3: [glossary.yaml]            # optional override

Validation rules:
  1. `path` matches `^[a-z._-][a-z0-9._/-]*$`, no `..`, no leading or trailing `/`.
  2. No two categories share `path`.
  3. No category path is a prefix of another's path.
  4. Custom category (non-canonical name) without `custom: true` -> reject.
  5. `drop: true` combined with any other field -> reject.
  6. `l3` filename matches `^[a-z][a-z0-9_-]*\\.(yaml|jsonl)$`; reject other extensions.

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

CANONICAL_CATEGORIES = {
    "architecture",
    "patterns",
    "domain",
    "operations",
    "debugging",
    "mobile",
    "workspace",
    "data",
    "infra",
}

# Default-in set when a config is present. Optional canonicals (mobile,
# workspace, data, infra) only enter via Step 3 scan detection or explicit
# config declaration; the canonical five are the baseline.
CANONICAL_FIVE = ("architecture", "patterns", "domain", "operations", "debugging")

PATH_RE = re.compile(r"^[a-z._-][a-z0-9._/-]*$")
L3_FILENAME_RE = re.compile(r"^[a-z][a-z0-9_-]*\.(yaml|jsonl)$")
CATEGORY_NAME_RE = re.compile(r"^[a-z][a-z0-9_-]*$")


class ConfigError(Exception):
    def __init__(self, message: str, line: int | None = None) -> None:
        super().__init__(message)
        self.line = line


# ---------- minimal YAML subset parser ----------


def _strip_comment(line: str) -> str:
    out = []
    in_single = False
    in_double = False
    for ch in line:
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            break
        out.append(ch)
    return "".join(out).rstrip()


def _scan_scalar(s: str) -> Any:
    s = s.strip()
    if s == "":
        return None
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    low = s.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if low in ("null", "~"):
        return None
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    return s


def _split_top_level(s: str, sep: str) -> list[str]:
    """Split on `sep` at top brace/bracket depth, respecting quotes."""
    parts: list[str] = []
    buf: list[str] = []
    depth_curly = 0
    depth_square = 0
    in_single = False
    in_double = False
    for ch in s:
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        if not in_single and not in_double:
            if ch == "{":
                depth_curly += 1
            elif ch == "}":
                depth_curly -= 1
            elif ch == "[":
                depth_square += 1
            elif ch == "]":
                depth_square -= 1
            elif ch == sep and depth_curly == 0 and depth_square == 0:
                parts.append("".join(buf))
                buf = []
                continue
        buf.append(ch)
    parts.append("".join(buf))
    return parts


def _parse_inline(value: str, line: int) -> Any:
    value = value.strip()
    if value.startswith("{") and value.endswith("}"):
        body = value[1:-1].strip()
        if not body:
            return {}
        out: dict[str, Any] = {}
        for item in _split_top_level(body, ","):
            item = item.strip()
            if not item:
                continue
            if ":" not in item:
                raise ConfigError(f"inline mapping entry missing ':': '{item}'", line)
            k, _, v = item.partition(":")
            out[k.strip()] = _parse_inline(v, line) if v.strip().startswith(("{", "[")) else _scan_scalar(v)
        return out
    if value.startswith("[") and value.endswith("]"):
        body = value[1:-1].strip()
        if not body:
            return []
        return [
            _parse_inline(item, line) if item.strip().startswith(("{", "[")) else _scan_scalar(item)
            for item in _split_top_level(body, ",")
            if item.strip()
        ]
    return _scan_scalar(value)


def _indent_of(line: str) -> int:
    n = 0
    for ch in line:
        if ch == " ":
            n += 1
        elif ch == "\t":
            raise ConfigError("tabs not allowed for indentation; use spaces")
        else:
            break
    return n


def parse_yaml_subset(text: str) -> dict[str, Any]:
    """Parse the minimal YAML subset used by exodia.config.yaml."""
    raw_lines = text.splitlines()
    lines: list[tuple[int, int, str]] = []
    for idx, raw in enumerate(raw_lines, start=1):
        stripped_full = _strip_comment(raw)
        if not stripped_full.strip():
            continue
        try:
            indent = _indent_of(stripped_full)
        except ConfigError as e:
            e.line = idx
            raise
        content = stripped_full[indent:]
        lines.append((idx, indent, content))

    pos = 0

    def parse_block(min_indent: int) -> tuple[Any, int]:
        nonlocal pos
        if pos >= len(lines):
            return None, pos
        line_no, indent, content = lines[pos]
        if indent < min_indent:
            return None, pos
        if content.startswith("- "):
            return parse_list(indent)
        return parse_map(indent)

    def parse_map(target_indent: int) -> tuple[dict[str, Any], int]:
        nonlocal pos
        out: dict[str, Any] = {}
        while pos < len(lines):
            line_no, indent, content = lines[pos]
            if indent < target_indent:
                break
            if indent > target_indent:
                raise ConfigError(f"unexpected indentation (got {indent}, expected {target_indent})", line_no)
            if ":" not in content:
                raise ConfigError(f"mapping entry missing ':': '{content}'", line_no)
            key, _, rest = content.partition(":")
            key = key.strip()
            rest = rest.strip()
            pos += 1
            if rest:
                out[key] = _parse_inline(rest, line_no)
            else:
                if pos < len(lines) and lines[pos][1] > target_indent:
                    child_indent = lines[pos][1]
                    child_content = lines[pos][2]
                    if child_content.startswith("- "):
                        value, _ = parse_list(child_indent)
                    else:
                        value, _ = parse_map(child_indent)
                    out[key] = value
                else:
                    out[key] = None
        return out, pos

    def parse_list(target_indent: int) -> tuple[list[Any], int]:
        nonlocal pos
        out: list[Any] = []
        while pos < len(lines):
            line_no, indent, content = lines[pos]
            if indent < target_indent or not content.startswith("- "):
                break
            item_text = content[2:].strip()
            pos += 1
            if item_text:
                out.append(_parse_inline(item_text, line_no))
            else:
                value, _ = parse_block(target_indent + 2)
                out.append(value)
        return out, pos

    if not lines:
        return {}
    first_indent = lines[0][1]
    if first_indent != 0:
        raise ConfigError("top-level keys must start at column 0", lines[0][0])
    result, _ = parse_map(0)
    if not isinstance(result, dict):
        raise ConfigError("top-level document must be a mapping", 1)
    return result


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
            if k not in ("path", "drop", "custom", "l3"):
                errors.append(ConfigError(f"category '{name}': unknown field '{k}'"))

        drop = bool(body.get("drop", False))
        custom_flag = bool(body.get("custom", False))
        path = body.get("path")
        l3 = body.get("l3")

        if drop and (path is not None or custom_flag or l3 is not None):
            errors.append(ConfigError(f"category '{name}': 'drop: true' is mutually exclusive with other fields"))
            continue

        is_canonical = name in CANONICAL_CATEGORIES
        if not is_canonical and not custom_flag and not drop:
            errors.append(
                ConfigError(
                    f"category '{name}': non-canonical name requires 'custom: true' "
                    f"(canonical set: {sorted(CANONICAL_CATEGORIES)})"
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

        if drop:
            resolved.append(
                {"name": name, "path": None, "kind": "canonical", "l3_override": None, "drop": True}
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
                "drop": False,
            }
        )

    declared = {c["name"] for c in resolved}
    for default_name in CANONICAL_FIVE:
        if default_name not in declared:
            resolved.append(
                {
                    "name": default_name,
                    "path": f"{context_dir}/{default_name}",
                    "kind": "canonical",
                    "l3_override": None,
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
