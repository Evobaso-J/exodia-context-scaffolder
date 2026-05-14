#!/usr/bin/env python3
"""Merge parsed `exodia.config.yaml` with canonical defaults.

Reads the JSON output of `parse_config.py` from stdin (or `--config <file>`),
and emits the layout map every downstream step consumes:

    [
      {
        "name": "architecture",
        "path": "docs/project/architecture",
        "kind": "canonical",
        "l2_template_path": "<SKILL_DIR>/templates/architecture/ARCHITECTURE.md.tmpl",
        "l3_specs": [
          {"filename": "decisions.jsonl", "schema_name": "adr",
           "schema_template_path": "<SKILL_DIR>/templates/architecture/decisions.jsonl.tmpl"}
        ]
      },
      {
        "name": "glossary",
        "path": "docs/project/glossary",
        "kind": "canonical",
        "l2_template_path": "<SKILL_DIR>/templates/glossary/GLOSSARY.md.tmpl",
        "l3_specs": [
          {"filename": "glossary.yaml", "schema_name": "glossary",
           "schema_template_path": "<SKILL_DIR>/templates/glossary/glossary.yaml.tmpl"}
        ]
      }
    ]

`l3_specs` is `null` when the config did not declare `l3` and the model must
infer filenames + schemas in Step 6. When `l3` is declared, each entry is
resolved against the canonical-name registry built from the templates tree;
unknown filenames return `schema_name: null` and `schema_template_path: null`
(model fills the schema body inline).

Usage:
    parse_config.py exodia.config.yaml | resolve_layout.py --skill-dir <path>
    resolve_layout.py --skill-dir <path> --config exodia.config.yaml
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from yaml_subset import parse_yaml_subset

# Canonical-ledger registry is loaded from heuristics/ledgers.yaml. That file
# is the single source of truth for filename -> (host, schema) and is also
# consumed by SKILL.md (Step 8 path-resolution, Step 9 seed scans) and by
# rules/self-update.md row generation. Do not duplicate ledger data here.


def _load_canonical_ledgers(skill_dir: Path) -> dict[str, list[tuple[str, str]]]:
    """Build filename -> ordered [(host, schema)] map from the registry.

    Tiebreaker for shared filenames: preserve registry insertion order so
    callers that pass a matching `host_category` win, else first-match.
    """
    registry_path = skill_dir / "heuristics" / "ledgers.yaml"
    parsed = parse_yaml_subset(registry_path.read_text(encoding="utf-8"))
    out: dict[str, list[tuple[str, str]]] = {}
    for row in parsed["ledgers"].values():
        out.setdefault(row["filename"], []).append((row["host"], row["schema"]))
    return out


def _category_template_dir(skill_dir: Path, name: str) -> Path | None:
    candidate = skill_dir / "templates" / name
    return candidate if candidate.is_dir() else None


def _l2_template_path(skill_dir: Path, name: str) -> Path | None:
    src = _category_template_dir(skill_dir, name)
    if src is None:
        return None
    candidate = src / f"{name.upper()}.md.tmpl"
    return candidate if candidate.is_file() else None


def _l3_template_path(skill_dir: Path, category: str, filename: str) -> Path | None:
    src = _category_template_dir(skill_dir, category)
    if src is None:
        return None
    candidate = src / f"{filename}.tmpl"
    return candidate if candidate.is_file() else None


def _lookup_canonical_ledger(
    ledgers: dict[str, list[tuple[str, str]]],
    filename: str,
    host_category: str,
) -> tuple[str | None, str | None]:
    """Return (schema_name, source_category) for a known L3 filename.

    Tiebreaker: prefer the category whose name matches `host_category`; else
    first-match. Returns (None, None) for unknown filenames.
    """
    candidates = ledgers.get(filename)
    if not candidates:
        return None, None
    for cat, schema in candidates:
        if cat == host_category:
            return schema, cat
    cat, schema = candidates[0]
    return schema, cat


def _default_l3_specs(
    skill_dir: Path,
    ledgers: dict[str, list[tuple[str, str]]],
    category: str,
) -> list[dict] | None:
    """Default L3 specs for a canonical category: every `.tmpl` next to the L2.

    Mirrors today's `init_structure.sh` behavior of copying every `.tmpl` in
    the category's template dir.
    """
    src = _category_template_dir(skill_dir, category)
    if src is None:
        return None
    specs: list[dict] = []
    for tmpl in sorted(src.glob("*.tmpl")):
        base = tmpl.name[: -len(".tmpl")]
        if base.endswith(".md"):
            continue
        if not (base.endswith(".jsonl") or base.endswith(".yaml")):
            continue
        schema_name, _src_cat = _lookup_canonical_ledger(ledgers, base, category)
        specs.append(
            {
                "filename": base,
                "schema_name": schema_name,
                "schema_template_path": str(tmpl),
            }
        )
    return specs


def resolve(parsed: dict, skill_dir: Path) -> list[dict]:
    ledgers = _load_canonical_ledgers(skill_dir)
    out: list[dict] = []
    for cat in parsed["categories"]:
        if cat["drop"]:
            continue
        name = cat["name"]
        kind = cat["kind"]
        l3_override = cat["l3_override"]

        l2_path = _l2_template_path(skill_dir, name) if kind == "canonical" else None

        if l3_override is not None:
            l3_specs: list[dict] | None = []
            for fname in l3_override:
                schema_name, src_cat = _lookup_canonical_ledger(ledgers, fname, name)
                tmpl_path: str | None = None
                if src_cat is not None:
                    p = _l3_template_path(skill_dir, src_cat, fname)
                    tmpl_path = str(p) if p is not None else None
                l3_specs.append(
                    {
                        "filename": fname,
                        "schema_name": schema_name,
                        "schema_template_path": tmpl_path,
                    }
                )
        elif kind == "canonical":
            l3_specs = _default_l3_specs(skill_dir, ledgers, name)
        else:
            l3_specs = None  # custom + no override -> Step 6 model infers

        out.append(
            {
                "name": name,
                "path": cat["path"],
                "kind": kind,
                "l2_template_path": str(l2_path) if l2_path else None,
                "l3_specs": l3_specs,
            }
        )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill-dir", required=True, help="path to the exodia skill dir")
    ap.add_argument("--config", help="JSON output of parse_config.py (default: stdin)")
    args = ap.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    if not skill_dir.is_dir():
        print(f"error: skill dir not found: {skill_dir}", file=sys.stderr)
        return 66

    if args.config:
        text = Path(args.config).read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()
    parsed = json.loads(text)

    resolved = resolve(parsed, skill_dir)
    json.dump(resolved, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
