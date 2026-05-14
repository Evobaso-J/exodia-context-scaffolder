#!/usr/bin/env python3
"""Build the curated-category registry from `$SKILL_DIR/templates/`.

Lists every subdirectory of `templates/` that contains an `<UPPERNAME>.md.tmpl`
file, extracts the one-line purpose from the leading `<!-- purpose: ... -->`
comment, and emits a JSON object mapping `name -> purpose` on stdout.

Consumed by `protocol/01-preflight.md` to produce `$REGISTRY`. Step 3 reads
`$REGISTRY` alongside `$SCAN` so the model can judge fit between any proposed
category name and the curated set, regardless of whether the proposal came
from scan evidence or from custom-category interview.

Schema rule: every `<UPPERNAME>.md.tmpl` MUST start with a single-line HTML
comment of the form `<!-- purpose: ... -->`. If the comment is missing, the
template is skipped and a warning is emitted on stderr (the script does not
fail; missing purpose only excludes the category from `$REGISTRY`).

Usage:
    load_registry.py --skill-dir <path>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PURPOSE_RE = re.compile(r"^<!--\s*purpose:\s*(.+?)\s*-->\s*$")


def load_registry(skill_dir: Path) -> dict[str, str]:
    """Return `{name: purpose}` for every category template that declares one."""
    templates_dir = skill_dir / "templates"
    if not templates_dir.is_dir():
        return {}

    registry: dict[str, str] = {}
    for entry in sorted(templates_dir.iterdir()):
        if not entry.is_dir():
            continue
        l2_template = entry / f"{entry.name.upper()}.md.tmpl"
        if not l2_template.is_file():
            continue
        try:
            first_line = l2_template.read_text(encoding="utf-8").splitlines()[0]
        except (OSError, IndexError):
            print(f"warning: cannot read first line of {l2_template}", file=sys.stderr)
            continue
        match = PURPOSE_RE.match(first_line)
        if not match:
            print(
                f"warning: {l2_template} missing leading '<!-- purpose: ... -->' comment; "
                f"excluding '{entry.name}' from registry",
                file=sys.stderr,
            )
            continue
        registry[entry.name] = match.group(1)
    return registry


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill-dir", required=True, help="path to the exodia skill dir")
    args = ap.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    if not skill_dir.is_dir():
        print(f"error: skill dir not found: {skill_dir}", file=sys.stderr)
        return 66

    registry = load_registry(skill_dir)
    json.dump(registry, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
