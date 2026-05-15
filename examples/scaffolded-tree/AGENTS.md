<!--
  Hand-authored snapshot of what `/exodia` emits for a fictional FastAPI +
  Celery monorepo named "ingest-service". Illustrative, not generated.
  See ../../README.md for the project overview.
-->
# AGENTS.md

<!-- exodia:section:overview -->
`ingest-service` is a two-process monorepo: a FastAPI `api/` handles request routing, auth, and short-lived reads; a Celery `worker/` owns long-running ingest jobs. Shared contracts live in `packages/contracts/`. Deployed as two containers behind a single gateway.

## Commands

<!-- exodia:section:commands -->
Check `pyproject.toml` for scripts. Common entry points:

- `make api` runs the FastAPI server (uvicorn, reload mode).
- `make worker` runs the Celery worker against the local Redis broker.
- `make test` runs pytest across `api/`, `worker/`, and `packages/`.

## Context Router

<!-- exodia:section:router -->
<!-- exodia:router:start -->
Route by task type. Read the relevant L2 module, then load L3 data (`.jsonl` / `.yaml`) only when needed. **Max 2 hops.**

| Task type | Load |
| --------- | ---- |
| Understanding system shape, service boundaries, data flow | `context/architecture/ARCHITECTURE.md` |
| Logging or recalling an architectural decision | `context/architecture/decisions.jsonl` |
| Writing new code: conventions, idioms, shared utilities | `context/design-patterns/DESIGN-PATTERNS.md` |
| Reviewing or logging a PR-review check / migration | `context/design-patterns/reviews.jsonl` |
| Looking up domain terms or entity definitions | `context/glossary/GLOSSARY.md` then `context/glossary/glossary.yaml` |
| Build, test, deploy, env vars, variant-specific behavior | `context/operations/OPERATIONS.md` |
| Per-variant override or feature-flag cohort detail | `context/operations/variants.yaml` |
| Diagnosing a broken state or recurring footgun | `context/debugging/DEBUGGING.md` then `context/debugging/playbooks.jsonl` |
<!-- exodia:router:end -->

## Behavioral Rules

<!-- exodia:section:rules -->
- Read L2 narrative once per task; only load the matching L3 file when a specific entry is needed.
- Edit prose between `<!-- exodia:section:<id> -->` markers freely. Do not delete the markers.
- Append-only ledgers are append-only: never rewrite a settled row, supersede with a new entry.
- `api/` never imports from `worker/`. Communication is queue-only through `packages/contracts/`.

## Self-Update Rules

<!-- exodia:section:self-update -->
When a session learns something worth saving, append to the ledger matching the signal:

| Signal | Append to |
| ------ | --------- |
| Architecture or design decision taken by the team | `context/architecture/decisions.jsonl` |
| PR review surfaces new check (prod near-miss, deprecation, contract change) | `context/design-patterns/reviews.jsonl` |
| Domain term clarified or new entity appears | `context/glossary/glossary.yaml` |
| Variant-specific behavior confirmed | `context/operations/variants.yaml` |
| Reproducible bug worth a future debugger's time (symptom, root cause, fix) | `context/debugging/playbooks.jsonl` |

Each entry uses an ID of the form `{type}_{YYYYMMDD}_{HHMMSS}_{4hex}`. While a branch is in flight, overwrite an earlier same-topic entry in place; once merged, it is settled and only a later branch can supersede it.

## Quick Action Table

<!-- exodia:section:quick-actions -->
| Developer says | Action sequence |
| -------------- | --------------- |
| "Add a new endpoint" | Load `architecture/ARCHITECTURE.md` (Entry Points), `design-patterns/DESIGN-PATTERNS.md` (Handler shape). Implement in `api/routes/`. |
| "Worker job times out" | Load `debugging/DEBUGGING.md`, grep `debugging/playbooks.jsonl` for `worker_timeout`. |
| "Why was X chosen over Y?" | Grep `architecture/decisions.jsonl` for X. |
| "What is a `Run`?" | Open `glossary/glossary.yaml`, then `glossary/GLOSSARY.md` for context. |

## Context Structure

<!-- exodia:section:structure -->
```text
AGENTS.md
context/
  architecture/
    ARCHITECTURE.md
    decisions.jsonl
  design-patterns/
    DESIGN-PATTERNS.md
    reviews.jsonl
    docs/
      error-handling.md
  glossary/
    GLOSSARY.md
    glossary.yaml
  operations/
    OPERATIONS.md
    variants.yaml
  debugging/
    DEBUGGING.md
    playbooks.jsonl
```
