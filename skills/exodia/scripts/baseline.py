#!/usr/bin/env python3
"""Track exodia-drafted L2 section content so incremental re-runs can
distinguish user-edited sections from sections that still hold their
original drafted content.

Each L2 file carries HTML comment markers: `<!-- exodia:section:<id> -->`.
The content between one marker and the next marker (or EOF) is a
"section body." On initial scaffold, exodia records the sha256 of every
section body into `.exodia/baselines.json`, keyed by relative path.

On an incremental re-run:
  - `current_hash == baseline_hash`  -> content is still exodia's draft,
                                        propose the updated draft.
  - `current_hash != baseline_hash`  -> user has edited, leave alone.
  - section-id absent from baseline  -> either a new section or a repo
                                        migrated from a pre-baseline
                                        install; treat as edited.

Subcommands:
    record   <context-dir>                           Write baselines.json
    compare  <context-dir> <relative-l2-path>        Emit JSON per section
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

MARKER_RE = re.compile(r"<!--\s*exodia:section:([A-Za-z0-9_.-]+)\s*-->")


def split_sections(text: str) -> list[tuple[str, str]]:
    """Return [(section_id, body), ...] in document order.

    Content before the first marker is dropped. Bodies include a
    trailing newline normalization so whitespace-only edits to the
    section boundaries do not flip the hash.
    """
    sections: list[tuple[str, str]] = []
    matches = list(MARKER_RE.finditer(text))
    for i, match in enumerate(matches):
        section_id = match.group(1)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip("\n")
        sections.append((section_id, body))
    return sections


def hash_body(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def scan_l2_files(context_dir: Path) -> dict[str, dict[str, str]]:
    """Return {relative_path: {section_id: hash}} for every `*.md` in
    context/ that contains at least one exodia section marker.
    """
    result: dict[str, dict[str, str]] = {}
    for md_path in sorted(context_dir.rglob("*.md")):
        try:
            text = md_path.read_text(encoding="utf-8")
        except OSError:
            continue
        sections = split_sections(text)
        if not sections:
            continue
        rel = md_path.relative_to(context_dir).as_posix()
        result[rel] = {sid: hash_body(body) for sid, body in sections}
    return result


def cmd_record(context_dir: Path) -> int:
    if not context_dir.is_dir():
        print(f"error: not a directory: {context_dir}", file=sys.stderr)
        return 66
    baselines = scan_l2_files(context_dir)
    out_dir = context_dir.parent / ".exodia"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "baselines.json"
    payload = {"version": 1, "files": baselines}
    out_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote: {out_path} ({sum(len(v) for v in baselines.values())} sections)")
    return 0


def cmd_compare(context_dir: Path, rel_path: str) -> int:
    l2_path = context_dir / rel_path
    if not l2_path.is_file():
        print(f"error: not a file: {l2_path}", file=sys.stderr)
        return 66
    baseline_path = context_dir.parent / ".exodia" / "baselines.json"
    if not baseline_path.is_file():
        print(
            f"error: baseline not found at {baseline_path}. Run "
            "`baseline.py record` after the initial scaffold.",
            file=sys.stderr,
        )
        return 66
    payload = json.loads(baseline_path.read_text(encoding="utf-8"))
    stored = payload.get("files", {}).get(rel_path, {})

    text = l2_path.read_text(encoding="utf-8")
    sections = split_sections(text)
    report = []
    for section_id, body in sections:
        current = hash_body(body)
        baseline = stored.get(section_id)
        if baseline is None:
            status = "no-baseline"
        elif baseline == current:
            status = "unedited"
        else:
            status = "edited"
        report.append({
            "section_id": section_id,
            "status": status,
            "current_hash": current,
            "baseline_hash": baseline,
        })
    json.dump({"file": rel_path, "sections": report}, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def main() -> int:
    if len(sys.argv) < 3:
        print(
            "usage:\n"
            "  baseline.py record  <context-dir>\n"
            "  baseline.py compare <context-dir> <relative-l2-path>",
            file=sys.stderr,
        )
        return 64
    cmd = sys.argv[1]
    context_dir = Path(sys.argv[2]).resolve()
    if cmd == "record":
        return cmd_record(context_dir)
    if cmd == "compare":
        if len(sys.argv) != 4:
            print("usage: baseline.py compare <context-dir> <relative-l2-path>", file=sys.stderr)
            return 64
        return cmd_compare(context_dir, sys.argv[3])
    print(f"error: unknown subcommand '{cmd}'", file=sys.stderr)
    return 64


if __name__ == "__main__":
    sys.exit(main())
