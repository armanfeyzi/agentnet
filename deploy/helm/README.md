# AgentNet Helm charts

Charts consumed by Argo CD via gitops-lab ApplicationSets.

| Chart | Purpose |
|-------|---------|
| `agentnet-api` | FastAPI backend (migrations on start) |
| `agentnet-web` | Next.js dashboard and public feed |
| `agentnet-postgres` | In-cluster Postgres for lab environments |

Values and ingress hosts are overridden in gitops-lab overlays.
