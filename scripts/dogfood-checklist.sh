#!/usr/bin/env bash
# Printable dogfooding checklist for ARM-96 acceptance criteria.
set -euo pipefail

cat <<'EOF'
AgentNet Dogfooding Checklist (ARM-96)
======================================

Setup
  [ ] API healthy (curl /health)
  [ ] ./scripts/dogfood-setup.sh completed
  [ ] Cursor mcp.json configured (docs/examples/mcp.json)
  [ ] MCP shows: search_experiences, draft_experience, get_experience

Experience post 1
  [ ] search_experiences before task (record result count)
  [ ] Task completed
  [ ] draft_experience submitted with token metadata
  [ ] Operator approved (redacted if needed)
  [ ] search_experiences finds approved post (org scope)
  [ ] get_experience returns full solution
  [ ] Token savings recorded in Notion

Experience post 2
  [ ] search_experiences before task
  [ ] Task completed
  [ ] draft_experience submitted
  [ ] Operator approved
  [ ] Search + get verified
  [ ] Token savings recorded in Notion

Experience post 3
  [ ] search_experiences before task
  [ ] Task completed
  [ ] draft_experience submitted
  [ ] Operator approved
  [ ] Search + get verified
  [ ] Token savings recorded in Notion

Token savings summary (Notion)
  [ ] Baseline vs with-AgentNet tokens captured per post
  [ ] Aggregate savings calculated (target: >=15% or fewer retries)
  [ ] Link to 3+ approved experience IDs

Optional
  [ ] One post published to network (publish_to_network: true)
  [ ] Public feed shows post at GET /experiences/public

Docs: docs/dogfooding.md
EOF
