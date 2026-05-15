<!-- purpose: How to diagnose common problems. Start here when something breaks. -->
# Debugging

<!-- exodia:section:intro -->
How to diagnose common problems. Start here when something breaks.

## Local Environment Setup

<!-- exodia:section:env-setup -->
Python 3.12 (see `pyproject.toml` `requires-python`). Use `uv` as the package manager: `uv sync` installs all packages in editable mode. Ports: `api/` on 8080, Postgres on 5432, Redis on 6379. Env: copy `.env.example` to `.env.local`, fill the database URL.

## How to use this module

<!-- exodia:section:how-to-use -->
1. Reproduce the symptom.
2. Search `playbooks.jsonl` for matching symptoms.
3. If found, follow the playbook's fix.
4. If not found, once solved, append a new playbook entry per the Self-Update Rules. Recurring footguns count: the footgun IS the symptom; name how it surfaces.

## Common Topics

<!-- exodia:section:topics -->
- **Worker timeouts**: `playbook_20260319_111234_aa01`. Usually network egress to S3.
- **api/worker schema drift**: `playbook_20260507_173021_5e88`. When `packages/contracts/` is bumped without re-deploying both services.
- **Idempotency-key collisions**: see `reviews.jsonl#review_20260429_142008_3df9` for the contract; no playbook yet because no incident has happened.

## L3 Data

<!-- exodia:section:l3 -->
- `playbooks.jsonl`: symptom to root cause to fix recipes. Includes recurring footguns (the footgun IS the symptom).
