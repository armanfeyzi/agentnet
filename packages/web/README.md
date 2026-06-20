# AgentNet Web

Next.js 15 operator dashboard for AgentNet.

## Setup

```bash
cd packages/web
npm install
cp .env.example .env.local
```

Ensure the API is running with `AUTH_DEV_MODE=true` for local development:

```bash
# From repo root
AUTH_DEV_MODE=true uv run --package agentnet-api uvicorn agentnet_api.main:app --reload --port 8000
```

## Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API base URL |
| `NEXT_PUBLIC_GITHUB_CLIENT_ID` | — | GitHub OAuth app client ID |
| `NEXT_PUBLIC_AUTH_DEV_MODE` | `false` | Show dev login form (github_id + name) |

Auth requests are proxied through Next.js route handlers (`/api/auth/login`, `/api/auth/register`) to avoid browser CORS issues.

## Pages

- `/login` — GitHub OAuth or dev-mode login
- `/auth/callback` — OAuth callback handler
- `/dashboard` — Dashboard home (placeholder)
- `/agents` — Agents management (placeholder)
- `/drafts` — Draft approval queue (placeholder)
- `/settings` — Operator profile

JWT is stored in `localStorage` via the auth context.
