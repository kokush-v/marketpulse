# Kubernetes manifests

These manifests are a Git-tracked base for local Kubernetes deployment.

## What is included

- `Namespace`
- `ConfigMap`
- `Deployment`
- `CronJob`
- `Service`
- `PersistentVolumeClaim` for PostgreSQL and Redis

## What is intentionally not committed

- Kubernetes `Secret` objects
- raw `.env` files with sensitive values
- ingress and TLS configuration

## Apply order

Create the namespace first:

```bash
kubectl apply -f k8s/namespace.yaml
```

Create local secret env files that are **not committed**:

```bash
mkdir -p k8s/secrets
cp backend/.env k8s/secrets/backend.env
cp market-data-api/.env k8s/secrets/market-data-api.env
```

Expected local files:

```bash
k8s/secrets/postgres.env
k8s/secrets/backend.env
k8s/secrets/market-data-api.env
```

## Build images

Build all local development images:

```bash
sh k8s/scripts/build-images.sh
```

This builds only the application images:

- `marketpulse-backend:dev`
- `marketpulse-frontend:dev`
- `marketpulse-market-data-api:dev`
- `marketpulse-cron:dev`

Optional overrides:

```bash
IMAGE_TAG=dev REGISTRY=ghcr.io/your-org IMAGE_PREFIX=marketpulse sh k8s/scripts/build-images.sh
```

The backend image includes Alembic files so the same image can run database migrations in Kubernetes.
The frontend build reads `NEXT_PUBLIC_*` values from `k8s/frontend/configmap.yaml` and passes them into `next build` as Docker build arguments.

## Restart deployments

If you rebuild and reuse the same image tag, sync secrets, apply manifests, and request a rollout restart:

```bash
sh k8s/scripts/restart-deployments.sh
```

This flow also runs the backend database migrations before restarting the application deployments.
The migration script waits for the PostgreSQL deployment to become available and retries the migration job on startup races.

You can run the migration job separately:

```bash
sh k8s/scripts/run-migrations.sh
```

Optional migration overrides:

```bash
NAMESPACE=marketpulse POSTGRES_DEPLOYMENT=marketpulse-postgres WAIT_TIMEOUT=180s MAX_ATTEMPTS=3 sh k8s/scripts/run-migrations.sh
```

Example manual restart:

```bash
kubectl rollout restart deployment/marketpulse-market-data-api -n marketpulse
```

Optional namespace override:

```bash
NAMESPACE=marketpulse sh k8s/scripts/restart-deployments.sh
```

Optional secret directory override:

```bash
SECRETS_DIR=/absolute/path/to/k8s-secrets sh k8s/scripts/restart-deployments.sh
```

## Expected secret keys

### `k8s/secrets/postgres.env`

```env
POSTGRES_PASSWORD=change-me
```

### `k8s/secrets/backend.env`

```env
DATABASE_URL=postgresql+asyncpg://marketpulse:change-me@marketpulse-postgres:5432/marketpulse
SUPABASE_ANON_KEY=replace-me
SUPABASE_SECRET_KEY=replace-me
TELEGRAM_BOT_TOKEN=replace-me
TELEGRAM_WEBHOOK_SECRET=
```

Optional keys:

```env
TEST_DATABASE_URL=postgresql+asyncpg://marketpulse:change-me@marketpulse-postgres:5432/marketpulse_test
```

### `k8s/secrets/market-data-api.env`

```env
COINGECKO_API_KEY=
NEWS_API_KEY=replace-me
SECRET_KEY_BASE=replace-me-or-let-the-script-generate-it
```

## Notes

- All services are `ClusterIP` for now.
- `postgres` and `redis` Kubernetes resources can use official upstream images directly and do not need local builds.
- `postgres` keeps `POSTGRES_USER` and `POSTGRES_DB` in the deployment manifest and uses a secret only for `POSTGRES_PASSWORD`.
- `frontend` and `backend` are exposed through one host, `http://marketpulse.test`, via Kubernetes Ingress.
- frontend uses `http://marketpulse.test/`
- backend public API uses `http://marketpulse.test/api`
- `frontend` config uses placeholder public URLs and should be updated before browser-based access.
- `NEXT_PUBLIC_*` frontend values are build-time values for Next.js in this setup, so after changing `k8s/frontend/configmap.yaml` you should rebuild the frontend image.
- `backend` talks to `market-data-api`, `postgres`, and `redis` over cluster-internal service names.
- `cron` image is reused by two Kubernetes `CronJob` resources for `price` and `news` alert evaluation.
- `restart-deployments.sh` first upserts Kubernetes secrets from `k8s/secrets/*.env`, applies non-cron manifests, executes the backend Alembic migration job, then applies cron manifests and restarts the application deployments.
- If `k8s/secrets/market-data-api.env` does not contain `SECRET_KEY_BASE`, `restart-deployments.sh` generates one automatically before applying the Kubernetes secret.

## Ingress

This setup expects an NGINX Ingress controller.

For local development, add this host entry:

```text
127.0.0.1 marketpulse.test
```

Then access the app at:

```text
http://marketpulse.test
```
