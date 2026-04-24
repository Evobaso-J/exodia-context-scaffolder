#!/usr/bin/env python3
"""Split an existing CLAUDE.md / AGENTS.md by ## headings.

Emits JSON on stdout:
    [{"heading": "Architecture", "body": "..."}, ...]

H1 content (anything before the first ##) is emitted as:
    {"heading": "__lede__", "body": "..."}

Usage:
    parse_existing.py <path-to-file>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def split(text: str) -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []
    current_heading = "__lede__"
    current_lines: list[str] = []

    for raw_line in text.splitlines():
        stripped = raw_line.lstrip()
        if stripped.startswith("## ") and not stripped.startswith("### "):
            # Flush previous section.
            body = "\n".join(current_lines).strip()
            if body or current_heading != "__lede__":
                sections.append({"heading": current_heading, "body": body})
            current_heading = stripped[3:].strip()
            current_lines = []
        else:
            current_lines.append(raw_line)

    body = "\n".join(current_lines).strip()
    if body or current_heading != "__lede__":
        sections.append({"heading": current_heading, "body": body})

    return sections


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: parse_existing.py <path>", file=sys.stderr)
        return 64

    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"error: not a file: {path}", file=sys.stderr)
        return 66

    text = path.read_text(encoding="utf-8")
    sections = split(text)
    json.dump(sections, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
