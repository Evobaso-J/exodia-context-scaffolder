<!-- purpose: System shape, entry points, and module layout. Read this first to understand how the codebase is organized. -->
# Architecture

<!-- exodia:section:intro -->
Two-process split: FastAPI `api/` handles request routing, auth, and short-lived reads; Celery `worker/` owns long-running ingest jobs. The two communicate only via a Redis-backed queue, never directly.

## Entry Points & Routing

<!-- exodia:section:routing -->
Routing is file-based under `api/routes/`. Each `*.py` file in that directory is auto-mounted at startup via the convention `api/routes/<name>.py` to `/<name>`. The router wiring lives in `api/main.py`.

### Key Files

- `api/main.py`: app factory, route auto-mount, middleware stack.
- `api/routes/`: one file per top-level endpoint family.
- `worker/celery_app.py`: Celery app factory, task auto-discovery from `worker/tasks/`.

## Modules & Boundaries

<!-- exodia:section:modules -->
- `api/`: HTTP layer. May read from the database; must enqueue all writes through `packages/contracts/queue.py`.
- `worker/`: job execution. Owns all database writes. Imports `packages/contracts/` but never `api/`.
- `packages/contracts/`: pydantic models shared between `api/` and `worker/`. No business logic, no I/O.
- `packages/storage/`: thin async SQLAlchemy wrapper. Used by both.

The `api/ -> worker/` import boundary is enforced by `tools/import_linter.cfg`.

## State Management

<!-- exodia:section:state -->
Database is Postgres (single primary, read replicas not used as of 2026-05). All state of record lives there; Redis is broker-only and treated as ephemeral. Sessions are stateless JWT, validated at the gateway (see `decisions.jsonl#decision_20260514_103211_a4f2`).

## Build

<!-- exodia:section:build -->
No bundler. Python 3.12, `pyproject.toml` defines packages, dependencies, and entry-point scripts. `make build` runs `pip install -e .` per package.

## Runtime Model

<!-- exodia:section:runtime -->
Request flow: gateway -> `api/` -> validate -> enqueue job to Redis -> `worker/` picks up -> writes to Postgres -> publishes completion event. Polling endpoints on `api/` read job status from Postgres directly.

## L3 Data

<!-- exodia:section:l3 -->
- `decisions.jsonl`: Architecture Decision Records for non-obvious choices.
