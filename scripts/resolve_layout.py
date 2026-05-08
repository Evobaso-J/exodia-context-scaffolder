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
        "path": "docs/domain/glossary",
        "kind": "custom",
        "l2_template_path": null,
        "l3_specs": [
          {"filename": "glossary.yaml", "schema_name": "glossary",
           "schema_template_path": "<SKILL_DIR>/templates/domain/glossary.yaml.tmpl"}
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

# Canonical filename -> ordered list of (category-name, schema-name).
# Tiebreaker for shared filenames (decisions.jsonl, gotchas.jsonl): prefer
# the category whose name matches the L2 the ledger lives next to; else
# first-match. The values below are listed in canonical-first-match order.
CANONICAL_LEDGERS: dict[str, list[tuple[str, str]]] = {
    "decisions.jsonl": [("architecture", "adr"), ("infra", "adr")],
    "reviews.jsonl": [("patterns", "rv")],
    "glossary.yaml": [("domain", "glossary")],
    "variants.yaml": [("operations", "variants")],
    "gotchas.jsonl": [("debugging", "gotcha"), ("mobile", "mgotcha")],
    "playbooks.jsonl": [("debugging", "pb")],
    "runbooks.jsonl": [("infra", "rb")],
    "experiments.jsonl": [("data", "exp")],
    "datasets.yaml": [("data", "datasets")],
    "releases.jsonl": [("mobile", "mrel")],
    "migrations.jsonl": [("workspace", "wsmig")],
}


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


def _lookup_canonical_ledger(filename: str, host_category: str) -> tuple[str | None, str | None]:
    """Return (schema_name, source_category) for a known L3 filename.

    Tiebreaker: prefer the category whose name matches `host_category`; else
    first-match. Returns (None, None) for unknown filenames.
    """
    candidates = CANONICAL_LEDGERS.get(filename)
    if not candidates:
        return None, None
    for cat, schema in candidates:
        if cat == host_category:
            return schema, cat
    cat, schema = candidates[0]
    return schema, cat


def _default_l3_specs(skill_dir: Path, category: str) -> list[dict] | None:
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
        schema_name, _src_cat = _lookup_canonical_ledger(base, category)
        specs.append(
            {
                "filename": base,
                "schema_name": schema_name,
                "schema_template_path": str(tmpl),
            }
        )
    return specs


def resolve(parsed: dict, skill_dir: Path) -> list[dict]:
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
                schema_name, src_cat = _lookup_canonical_ledger(fname, name)
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
            l3_specs = _default_l3_specs(skill_dir, name)
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
