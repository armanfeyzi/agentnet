#!/usr/bin/env bash
# Bootstrap operator, API key, and agent for AgentNet dogfooding.
# Requires API running with AUTH_DEV_MODE=true.
set -euo pipefail

API_URL="${AGENTNET_API_URL:-http://localhost:8000}"
GITHUB_ID="${DOGFOOD_GITHUB_ID:-dogfood-$(date +%s)}"
OPERATOR_NAME="${DOGFOOD_OPERATOR_NAME:-Dogfood Operator}"
OPERATOR_EMAIL="${DOGFOOD_OPERATOR_EMAIL:-dogfood@example.com}"
AGENT_NAME="${DOGFOOD_AGENT_NAME:-Cursor Dogfood Agent}"

if ! command -v jq >/dev/null 2>&1; then
  echo "error: jq is required" >&2
  exit 1
fi

echo "==> Checking API at $API_URL"
if ! curl -sf "$API_URL/health" >/dev/null; then
  echo "error: API not reachable. Start with: docker compose up -d" >&2
  echo "       For dev auth: AUTH_DEV_MODE=true uv run --package agentnet-api uvicorn agentnet_api.main:app --port 8000" >&2
  exit 1
fi

echo "==> Registering operator ($GITHUB_ID)"
REGISTER=$(curl -sf -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"github_id\":\"$GITHUB_ID\",\"name\":\"$OPERATOR_NAME\",\"email\":\"$OPERATOR_EMAIL\"}" \
  2>/dev/null) || true

if [ -z "${REGISTER:-}" ]; then
  echo "==> Register failed, trying login (operator may already exist)"
  REGISTER=$(curl -sf -X POST "$API_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"github_id\":\"$GITHUB_ID\",\"name\":\"$OPERATOR_NAME\",\"email\":\"$OPERATOR_EMAIL\"}")
fi

TOKEN=$(echo "$REGISTER" | jq -r '.access_token')
if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
  echo "error: could not obtain operator token. Is AUTH_DEV_MODE=true?" >&2
  exit 1
fi

echo "==> Creating API key"
KEY_RESP=$(curl -sf -X POST "$API_URL/operators/me/api-keys" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"cursor-dogfood"}')
API_KEY=$(echo "$KEY_RESP" | jq -r '.api_key')

echo "==> Creating agent"
AGENT_RESP=$(curl -sf -X POST "$API_URL/agents" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"$AGENT_NAME\",\"model_family\":\"claude-sonnet\",\"capability_tags\":[\"dogfood\",\"mcp\"]}")
AGENT_ID=$(echo "$AGENT_RESP" | jq -r '.id')

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cat <<EOF

AgentNet dogfood credentials
============================
AGENTNET_API_KEY=$API_KEY
AGENTNET_AGENT_ID=$AGENT_ID
AGENTNET_API_URL=$API_URL

Operator JWT (dashboard / curl):
$TOKEN

Next steps
----------
1. Copy docs/examples/mcp.json to ~/.cursor/mcp.json
2. Replace REPO_ROOT with: $REPO_ROOT
3. Paste AGENTNET_API_KEY and AGENTNET_AGENT_ID into the env block
4. Restart Cursor MCP servers
5. Run: ./scripts/dogfood-checklist.sh
6. See: docs/dogfooding.md

EOF
