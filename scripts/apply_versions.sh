#!/usr/bin/env bash
# Creates the Assignment 2 git history (branches, commits, version tags) on top of the existing repo.
# Run once from the repo root on a clean `main`:  DOCKERHUB_USER=<user> bash scripts/apply_versions.sh
set -euo pipefail
: "${DOCKERHUB_USER:?set DOCKERHUB_USER}"
[ "$(git rev-parse --abbrev-ref HEAD)" = "main" ] || { echo "run on main"; exit 1; }
grep -q 'APP_VERSION = "1.0.1"' app.py || { echo "expected APP_VERSION 1.0.1 on main"; exit 1; }
echo "a2-stages/" >> .git/info/exclude
sed -i "s/DOCKERHUB_USER/$DOCKERHUB_USER/g" k8s/*.yaml Jenkinsfile a2-stages/README-A2.md
printf '.scannerwork/\nsonar-report.txt\n' >> .gitignore

merge() { git checkout -q main; git merge --no-ff -q "$1" -m "$2"; }

git tag -a v1.0.1 -m "ACEest Fitness v1.0.1 (Assignment 1 baseline)"

git checkout -q -b ci/sonarqube
git add .gitignore sonar-project.properties scripts/sonar_gate.sh
git commit -q -m "ci: add SonarQube project config and quality gate script"
merge ci/sonarqube "Merge branch 'ci/sonarqube'"

git checkout -q -b build/docker-access-log
git add Dockerfile
git commit -q -m "build: enable gunicorn access log for traffic verification in Kubernetes"
merge build/docker-access-log "Merge branch 'build/docker-access-log'"

git checkout -q -b infra/k8s-manifests
git add k8s/ scripts/setup_minikube.sh scripts/deploy_with_rollback.sh scripts/k8s_demo.sh
git commit -q -m "feat(k8s): add manifests for rolling, blue-green, canary, shadow and A/B deployments with rollback"
merge infra/k8s-manifests "Merge branch 'infra/k8s-manifests'"

git checkout -q -b ci/jenkins-docker-hub
git add Jenkinsfile scripts/build_push_versions.sh
git commit -q -m "ci: extend Jenkins pipeline with SonarQube gate, Docker Hub push and build artifacts"
merge ci/jenkins-docker-hub "Merge branch 'ci/jenkins-docker-hub'"

git checkout -q -b feature/client-summary
cp a2-stages/v1.1.0/app.py app.py; cp a2-stages/v1.1.0/tests/*.py tests/
git add app.py tests/test_summary.py
git commit -q -m "feat: add client summary endpoint (BMI, calories, adherence, workout totals)"
merge feature/client-summary "Merge branch 'feature/client-summary' (release v1.1.0)"
git tag -a v1.1.0 -m "ACEest Fitness v1.1.0 - client summary"

git checkout -q -b feature/stats-endpoint
cp a2-stages/v1.2.0/app.py app.py; cp a2-stages/v1.2.0/tests/*.py tests/
git add app.py tests/test_stats.py tests/test_summary.py
git commit -q -m "feat: add aggregate statistics endpoint"
merge feature/stats-endpoint "Merge branch 'feature/stats-endpoint' (release v1.2.0)"
git tag -a v1.2.0 -m "ACEest Fitness v1.2.0 - statistics endpoint"

git checkout -q -b docs/assignment2
cat a2-stages/README-A2.md >> README.md
git add README.md scripts/apply_versions.sh
git commit -q -m "docs: document Assignment 2 CI/CD architecture, versions and deployment strategies"
merge docs/assignment2 "Merge branch 'docs/assignment2'"

git status --short
git log --oneline --graph -n 25
echo; echo "Done. Next: publish all branches and tags to origin (see runbook)."
