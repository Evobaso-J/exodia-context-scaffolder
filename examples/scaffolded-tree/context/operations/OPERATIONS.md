<!-- purpose: Environments, configuration, deploys, and any per-variant behavior. Read when touching env vars, build config, or anything that differs between environments or variants. -->
# Operations

<!-- exodia:section:intro -->
Environments, configuration, deploys, and any per-variant behavior the codebase supports (environments, tenants, feature-flag cohorts, deployment targets, whatever applies). Read this when touching env vars, build config, or anything that differs between environments or variants.

## Environments

<!-- exodia:section:environments -->
- `local`: docker-compose stack (api + worker + postgres + redis). Config from `.env.local`.
- `staging`: shared cluster, single tenant set, low-traffic. Config from Kubernetes secrets, key `ingest-service-staging`.
- `production`: multi-region (`eu-west-1`, `us-east-1`), tenant-sharded. Config from Kubernetes secrets, key `ingest-service-prod`.

`.env.example` documents every variable. Loader: `pydantic-settings` via `api/config.py:Settings` and `worker/config.py:WorkerSettings`.

## Variants

<!-- exodia:section:variants -->
Two axes: environment (above) and tenant tier (`free`, `pro`, `enterprise`). Tier affects rate limits, retention, and feature flags only; never schema or contract. The matrix lives in `variants.yaml`.

## Configuration System

<!-- exodia:section:config -->
All config is read once at startup into the typed `Settings` object. No runtime mutation. Feature flags use LaunchDarkly via the `packages/flags/` wrapper; flag keys are typed in `packages/flags/keys.py`.

## Deploy

<!-- exodia:section:deploy -->
CI: GitHub Actions. On `main`, builds two container images (`api`, `worker`), pushes to ECR, and triggers an ArgoCD sync to staging. Production sync requires a manual approval step. Rollback: ArgoCD revision rollback (`make rollback ENV=prod`).

## Localization / i18n (if applicable)

<!-- exodia:section:i18n -->
N/A. The api emits English-only error messages; user-facing localization happens in the consumer apps, not here.

## L3 Data

<!-- exodia:section:l3 -->
- `variants.yaml`: per-variant behavioral differences (any axis the codebase varies along).
