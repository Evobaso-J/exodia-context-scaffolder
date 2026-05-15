# Error handling

Spun out from `DESIGN-PATTERNS.md` because the topic needs more than 3 lines.

## Two paths

`ingest-service` splits errors into two paths:

1. **Expected business errors** raise a typed exception from `packages/contracts/errors.py` (e.g. `RunNotFound`, `IdempotencyConflict`). The FastAPI exception handler in `api/main.py` maps each to a stable HTTP status and a JSON body with `error_code` + `message`.
2. **Unexpected errors** propagate to a global handler that returns HTTP 500, logs the full traceback as structured JSON (loguru), and emits a `error.unhandled` metric to Prometheus.

## Rules

- Never `raise HTTPException` from inside `worker/`. Workers run outside the request lifecycle; raise a typed exception and let the caller (or the retry policy) deal with it.
- Never catch `Exception` broadly inside `api/routes/`. The global handler is the only place that does. Catching swallows the metric and the log.
- Business exceptions must subclass `packages.contracts.errors.AppError` so the handler picks them up.

## Adding a new business error

1. Add the class to `packages/contracts/errors.py` with a `status_code` class attribute and an `error_code` string.
2. Add a row to the OpenAPI examples in `api/main.py:_register_error_responses()`.
3. If the worker can also raise it, add a test in `tests/integration/test_error_propagation.py`.

## See also

- `packages/contracts/errors.py`: the typed hierarchy.
- `api/main.py:register_exception_handlers()`: where mapping happens.
- `reviews.jsonl#review_20260322_091557_e2a1`: related testing rule.
