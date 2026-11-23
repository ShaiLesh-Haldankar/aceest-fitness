#!/usr/bin/env bash
# Rolling-update a deployment to a new image tag; if the rollout does not become healthy in time, roll back automatically.
# Usage: bash scripts/deploy_with_rollback.sh <deployment> <image:tag> [timeout-seconds]
set -uo pipefail
DEPLOY="$1"; IMAGE="$2"; TIMEOUT="${3:-60}"
echo ">>> updating $DEPLOY to $IMAGE"
kubectl set image "deployment/$DEPLOY" app="$IMAGE"
if kubectl rollout status "deployment/$DEPLOY" --timeout="${TIMEOUT}s"; then
  echo ">>> rollout of $IMAGE succeeded"
else
  echo ">>> rollout FAILED - rolling back to the last stable revision"
  kubectl rollout undo "deployment/$DEPLOY"
  kubectl rollout status "deployment/$DEPLOY" --timeout=120s
  echo ">>> rollback complete; running image: $(kubectl get deployment/$DEPLOY -o jsonpath='{.spec.template.spec.containers[0].image}')"
  exit 1
fi
