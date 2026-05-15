<!-- purpose: Code conventions, idioms, and shared utilities. Read this before introducing new patterns. -->
# Design Patterns

<!-- exodia:section:intro -->
> **Progressive disclosure:** this file holds short guardrails only (do/don't, 2-3 lines per topic). Detailed explanations live in `./docs/`. Drafted sections cite files and link to deep dives when a topic warrants more than ~3 lines.

<!-- exodia:section:body -->
## Handler shape (`api/routes/`)

- One pydantic request model per endpoint, defined inline at the top of the route file.
- Return pydantic response models, never raw dicts. FastAPI relies on the model for response-schema docs.
- Do: `async def` with explicit `await`. Don't: block on sync DB calls.

## Worker tasks (`worker/tasks/`)

- Each task module defines exactly one `@celery_app.task` function. Helpers go private (`_underscore_prefix`).
- Tasks are idempotent: receiving the same `job_id` twice must not double-write.

## Error handling

Two distinct paths: expected business errors raise typed exceptions caught by the FastAPI exception handler; unexpected errors propagate to a global handler that maps to 500 and logs structured.

See [docs/error-handling.md](docs/error-handling.md) for full details.

## Imports

- Absolute imports only. `from packages.contracts import RunRequest`, not `from ..contracts`.
- `api/` may not import `worker/`. Enforced by `tools/import_linter.cfg`.

## Testing

- pytest with `pytest-asyncio` for async tests; markers: `@pytest.mark.unit`, `@pytest.mark.integration`.
- Never mock the database (see `reviews.jsonl#review_20260322_091557_e2a1`). Use the `db` fixture which runs against a real Postgres container.

## L3 Data

<!-- exodia:section:l3 -->
- `reviews.jsonl`: PR review checks, migrations, anti-patterns.
