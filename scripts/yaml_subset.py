"""Minimal stdlib-only YAML subset parser shared across scaffolder scripts.

Supports the deliberately small dialect used by `exodia.config.yaml` and
`heuristics/ledgers.yaml`: mappings, scalar strings/bools/ints/null, inline
`{}` and `[]` collections, and `#` comments. Tabs in indentation are rejected.

Public API:
  - `parse_yaml_subset(text) -> dict`
  - `ConfigError` (raised on parse errors; carries optional 1-based line)

Helpers (`_strip_comment`, `_split_top_level`, `_scan_scalar`, `_indent_of`,
`_parse_inline`) are internal implementation details.
"""

from __future__ import annotations

import re
from typing import Any


class ConfigError(Exception):
    def __init__(self, message: str, line: int | None = None) -> None:
        super().__init__(message)
        self.line = line


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
