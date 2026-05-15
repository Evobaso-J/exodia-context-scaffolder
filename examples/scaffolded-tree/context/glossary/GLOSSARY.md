<!-- purpose: Business language, entities, and how they relate. Read when a task involves business logic, models, or user-facing concepts. -->
# Glossary

<!-- exodia:section:intro -->
Business language, entities, and how they relate. Read this when a task involves business logic, models, or user-facing concepts.

## Entities

<!-- exodia:section:entities -->
- **Run**: a single execution of an ingest pipeline for one tenant. Source of truth: `packages/contracts/run.py:Run`.
- **Source**: an upstream data origin (S3 bucket, HTTP feed, manual upload). Source of truth: `packages/contracts/source.py:Source`.
- **Tenant**: a logical isolation boundary; all `Run`s and `Source`s belong to exactly one. Source of truth: `packages/contracts/tenant.py:Tenant`.
- **Artifact**: a file produced by a successful `Run`. Source of truth: `packages/contracts/artifact.py:Artifact`.

## Relationships

<!-- exodia:section:relationships -->
- `Tenant` 1:n `Source`
- `Source` 1:n `Run`
- `Run` 1:n `Artifact`
- A `Run` always has exactly one `Source`; an `Artifact` always belongs to exactly one `Run`.

## User Journey

<!-- exodia:section:journey -->
1. Tenant registers a `Source` (one-time).
2. Tenant `POST /v1/ingest` with the `Source` ID. The api creates a `Run` in `pending` and enqueues it.
3. Worker picks up the `Run`, transitions it through `running` -> `succeeded` / `failed`.
4. On success, worker writes one or more `Artifact`s; tenant fetches them via `GET /v1/runs/{id}/artifacts`.

## Type System

<!-- exodia:section:types -->
Types live in `packages/contracts/`, hand-written as pydantic v2 models. Import via `from packages.contracts import Run, Source, Tenant, Artifact`. No code generation step.

## L3 Data

<!-- exodia:section:l3 -->
- `glossary.yaml`: extended terminology and synonyms.
