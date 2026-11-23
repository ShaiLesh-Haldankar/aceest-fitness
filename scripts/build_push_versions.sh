#!/usr/bin/env bash
# Builds one Docker image per released git tag and pushes them all to Docker Hub.
# Usage: DOCKERHUB_USER=<user> bash scripts/build_push_versions.sh   (run `docker login` first)
set -euo pipefail
: "${DOCKERHUB_USER:?set DOCKERHUB_USER}"
IMAGE="$DOCKERHUB_USER/aceest-fitness"
TAGS="v1.0.1 v1.1.0 v1.2.0"
for t in $TAGS; do
  v="${t#v}"
  dir=$(mktemp -d)
  git worktree add -f "$dir" "$t" >/dev/null 2>&1
  echo ">>> building $IMAGE:$v from git tag $t"
  docker build --target runtime -t "$IMAGE:$v" "$dir" >/dev/null
  docker push "$IMAGE:$v"
  git worktree remove --force "$dir"
done
docker tag "$IMAGE:1.2.0" "$IMAGE:latest" && docker push "$IMAGE:latest"
echo; echo "Versions now on Docker Hub:"; docker images "$IMAGE"
