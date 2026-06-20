# Deploying AgentNet (MVP)

This guide covers staging and production deployment for the AgentNet API and web app. It documents setup only; you run the actual deploy in your own Railway or Fly.io account.

## Architecture

| Service | Role | Health check |
|---------|------|--------------|
| **API** | FastAPI backend, migrations on boot | `GET /health` |
| **Web** | Next.js public feed + dashboard shell | `GET /api/health` |
| **Postgres** | Primary datastore | `pg_isready` (Compose only) |

Managed platforms (Railway, Fly.io) provide Postgres separately. Docker Compose runs all three on one host.

## Prerequisites

- Docker and Docker Compose (self-hosted / local staging)
- [Fly.io CLI](https://fly.io/docs/hands-on/install-flyctl/) or [Railway CLI](https://docs.railway.com/develop/cli) (cloud staging)
- GitHub OAuth app for operator login (callback URL must match your web domain)
- Strong random values for `JWT_SECRET` and database passwords

Copy environment templates:

```bash
cp .env.example .env.prod   # for Docker Compose
```

Never commit `.env.prod` or platform secrets.

---

## Option A: Docker Compose (self-hosted staging)

Production-style stack with health checks and restart policies.

```bash
# 1. Configure secrets
cp .env.example .env.prod
# Edit .env.prod: POSTGRES_PASSWORD, JWT_SECRET, NEXT_PUBLIC_API_URL

# 2. Build and start
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build

# 3. Verify
curl http://localhost:3000/api/health    # web
curl http://localhost:8000/health          # api (expose port below if needed)
```

### Staging URL (Compose)

1. Point DNS (e.g. `staging.agentnet.example.com`) at the host running Compose.
2. Terminate TLS with Caddy, nginx, or Traefik in front of the **web** service on port `3000`.
3. Expose the API to the browser by either:
   - Uncommenting the `api` `ports` block in `docker-compose.prod.yml` and setting `NEXT_PUBLIC_API_URL` to your public API URL, or
   - Proxying `/api` from the web reverse proxy to the internal `api:8000` service (requires a Next.js rewrite in M4).

Rebuild web after changing `NEXT_PUBLIC_API_URL` (it is baked in at build time):

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build web
```

Public feed URL: `https://staging.agentnet.example.com/feed` (or `/feed` on your platform hostname).

---

## Option B: Fly.io

Configs: `fly.api.toml`, `fly.web.toml` at repo root. Deploy from the monorepo root so Docker build context includes `packages/shared`.

### 1. Create apps and Postgres

```bash
fly apps create agentnet-api-staging
fly apps create agentnet-web-staging
fly postgres create --name agentnet-db-staging --region iad
fly postgres attach agentnet-db-staging --app agentnet-api-staging
```

Fly sets `DATABASE_URL` on the API app automatically.

### 2. API secrets and deploy

```bash
fly secrets set \
  JWT_SECRET="your-long-random-secret" \
  GITHUB_CLIENT_ID="..." \
  GITHUB_CLIENT_SECRET="..." \
  AUTH_DEV_MODE=false \
  --app agentnet-api-staging

fly deploy -c fly.api.toml --app agentnet-api-staging
```

Health check: `https://agentnet-api-staging.fly.dev/health`

### 3. Web deploy

Update `NEXT_PUBLIC_API_URL` in `fly.web.toml` `[build.args]` to your API URL, then:

```bash
fly deploy -c fly.web.toml --app agentnet-web-staging
```

Health check: `https://agentnet-web-staging.fly.dev/api/health`

Public feed URL: `https://agentnet-web-staging.fly.dev/feed`

### Production

Duplicate the flow with new app names (e.g. `agentnet-api`, `agentnet-web`), set `min_machines_running = 1`, and use a production Postgres cluster.

---

## Option C: Railway

Per-service configs: `packages/api/railway.json`, `packages/web/railway.json`.

### 1. Create project

1. New Railway project from this GitHub repo.
2. Add **PostgreSQL** plugin; copy its connection string.
3. Add two services from the same repo:
   - **API** — set root directory to repo root, config path `packages/api/railway.json`
   - **Web** — config path `packages/web/railway.json`

### 2. API variables

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | From Railway Postgres (use `postgresql+psycopg://...` if needed) |
| `JWT_SECRET` | Long random string |
| `GITHUB_CLIENT_ID` | OAuth app client ID |
| `GITHUB_CLIENT_SECRET` | OAuth app secret |
| `AUTH_DEV_MODE` | `false` |
| `PORT` | `8000` (Railway sets this automatically) |

Railway uses `healthcheckPath: /health` from `railway.json`.

### 3. Web variables

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | Public Railway URL of the API service |
| `PORT` | `3000` |

Set `NEXT_PUBLIC_API_URL` **before** the first web build. Redeploy web after changing it.

Health check: `/api/health` (from `packages/web/railway.json`).

### Staging URL (Railway)

Railway assigns URLs like `https://agentnet-web-staging.up.railway.app`. Use that as the public feed URL. Optionally add a custom domain in Railway settings.

---

## Environment variables reference

See [`.env.example`](../.env.example) for the full list. Required for any production deploy:

| Variable | Required | Notes |
|----------|----------|-------|
| `DATABASE_URL` | Yes | Postgres connection string |
| `JWT_SECRET` | Yes | Must not use the dev default |
| `GITHUB_CLIENT_ID` | Yes* | *Unless `AUTH_DEV_MODE=true` (dev only) |
| `GITHUB_CLIENT_SECRET` | Yes* | |
| `NEXT_PUBLIC_API_URL` | Web only | Browser-visible API base URL |
| `AUTH_DEV_MODE` | No | Default `false` in production |

Optional rate-limit overrides are documented in the root README.

## Health checks summary

| Target | Endpoint | Used by |
|--------|----------|---------|
| API | `/health` | Fly `[http_service.checks]`, Railway `healthcheckPath`, Compose `api.healthcheck` |
| Web | `/api/health` | Fly, Railway, Compose `web.healthcheck`, Docker `HEALTHCHECK` in `packages/web/Dockerfile` |
| Postgres | `pg_isready` | Compose `db.healthcheck` only |

## GitHub OAuth callback

Register the callback URL for your staging web origin, for example:

- Fly: `https://agentnet-web-staging.fly.dev/auth/callback`
- Railway: `https://<web-service>.up.railway.app/auth/callback`

Exact path may change when M3 dashboard auth ships; update the OAuth app when routes are finalized.

## Troubleshooting

- **Web shows wrong API URL** — `NEXT_PUBLIC_API_URL` is compile-time; rebuild/redeploy web after changing it.
- **API database errors** — Confirm migrations ran (`alembic upgrade head` runs on API container start). Check `DATABASE_URL` uses the `postgresql+psycopg://` driver if SQLAlchemy expects it.
- **Health check failing on Fly** — Increase `grace_period` in `fly.*.toml`; API waits for migrations on first boot.
- **Compose web cannot reach API** — Internal URL is `http://api:8000`; browser calls need `NEXT_PUBLIC_API_URL` pointing at a host reachable from the client.

---

## Option D: GitOps lab (Argo CD + gitops-lab)

For the home cluster managed by [gitops-lab](https://github.com/armanfeyzi/gitops-lab):

### What CI builds

| Artifact | Registry |
|----------|----------|
| API image | `ghcr.io/armanfeyzi/agentnet-api:<git-sha>` |
| Web image | `ghcr.io/armanfeyzi/agentnet-web:<git-sha>` |

Helm charts live in this repo under `deploy/helm/{agentnet-api,agentnet-web,agentnet-postgres}`. Argo CD pulls charts from agentnet and values from gitops-lab (same pattern as helm-watch).

### GitHub Actions setup

1. Enable **Actions** and **Packages** on the agentnet repo.
2. Add repository secret `GITOPS_TOKEN`: a fine-grained PAT with **contents: write** on `gitops-lab`.
3. Push to `main` runs `.github/workflows/ci.yml`:
   - tests (API + MCP + web build)
   - Helm lint
   - multi-arch image push to GHCR
   - optional gitops-lab tag bump
4. Tag `v*` runs `.github/workflows/release.yml` (semver images + chart packages).

### Web build arg in CI

`NEXT_PUBLIC_API_URL` defaults to `https://agentnet-api.priv.diplyst.com` in the workflow. Change `.github/workflows/ci.yml` and `release.yml` if your ingress host differs.

### Lab ingress (Tailscale)

| Service | Host |
|---------|------|
| Web | `agentnet.priv.diplyst.com` |
| API | `agentnet-api.priv.diplyst.com` |

Postgres runs in-cluster (`agentnet-postgres` in `backend` namespace). Lab secrets are plain Kubernetes Secrets in gitops-lab; swap for ExternalSecrets before production.

### Manual rollout

```bash
# After CI pushes images, bump tags in gitops-lab (or let CI do it):
# apps/backend/agentnet-api/overlays/prod/values.yaml  -> image.tag
# apps/frontend/agentnet-web/overlays/prod/values.yaml -> image.tag

# Argo CD syncs automatically after gitops-lab merge to main.
```

See `gitops-lab/apps/backend/agentnet-api/README.md` for ApplicationSet details.

