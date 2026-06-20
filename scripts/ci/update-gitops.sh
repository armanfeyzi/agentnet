#!/usr/bin/env bash
set -euo pipefail

# Bump pinned image tags (and optional chart revision) in gitops-lab.
#
# Required env:
#   GITOPS_TOKEN   - PAT with write access to gitops-lab
#   IMAGE_TAG      - tag applied to api and web images
#
# Optional env:
#   CHART_REVISION - agentnet git ref for ApplicationSet targetRevision (e.g. v0.1.0 or main)
#   GITOPS_REPO    - default armanfeyzi/gitops-lab

GITOPS_REPO="${GITOPS_REPO:-armanfeyzi/gitops-lab}"
CHART_REVISION="${CHART_REVISION:-HEAD}"

workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT

git clone --depth 1 "https://x-access-token:${GITOPS_TOKEN}@github.com/${GITOPS_REPO}.git" "$workdir/repo"
cd "$workdir/repo"

API_VALUES="apps/backend/agentnet-api/overlays/prod/values.yaml"
WEB_VALUES="apps/frontend/agentnet-web/overlays/prod/values.yaml"
API_APPSET="apps/backend/agentnet-api/base/applicationset.yaml"
WEB_APPSET="apps/frontend/agentnet-web/base/applicationset.yaml"
PG_APPSET="apps/backend/agentnet-postgres/base/applicationset.yaml"

for file in "$API_VALUES" "$WEB_VALUES" "$API_APPSET" "$WEB_APPSET" "$PG_APPSET"; do
  if [[ ! -f "$file" ]]; then
    echo "missing expected gitops file: $file" >&2
    exit 1
  fi
done

yq -i ".image.tag = \"${IMAGE_TAG}\"" "$API_VALUES"
yq -i ".image.tag = \"${IMAGE_TAG}\"" "$WEB_VALUES"
yq -i ".spec.template.spec.sources[0].targetRevision = \"${CHART_REVISION}\"" "$API_APPSET"
yq -i ".spec.template.spec.sources[0].targetRevision = \"${CHART_REVISION}\"" "$WEB_APPSET"
yq -i ".spec.template.spec.sources[0].targetRevision = \"${CHART_REVISION}\"" "$PG_APPSET"

if git diff --quiet; then
  echo "gitops-lab already at image.tag=${IMAGE_TAG}"
  exit 0
fi

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git add "$API_VALUES" "$WEB_VALUES" "$API_APPSET" "$WEB_APPSET" "$PG_APPSET"
git commit -m "chore(agentnet): bump images to ${IMAGE_TAG}"
git push origin HEAD
