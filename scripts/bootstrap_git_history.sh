#!/usr/bin/env bash
# Builds a clean, meaningful Git history for the assignment repo.
# Run ONCE from the repo root, after configuring git user.name / user.email.
set -euo pipefail

if [ -d .git ]; then
  echo "A .git directory already exists - aborting to avoid rewriting history." >&2
  exit 1
fi

git init -b main

# 1. Legacy Tkinter versions, committed in release order and tagged
git add .gitignore
git commit -m "chore: initialise repository with .gitignore"
for v in 1.0 1.1 1.1.2 2.0.1 2.1.2 2.2.1 2.2.4 3.0.1 3.1.2 3.2.4; do
  f=$(ls legacy | grep -E "Aceestver-?${v//./\\.}\.py$")
  git add "legacy/$f"
  git commit -m "chore(legacy): import ACEest Tkinter version $v"
  git tag "legacy-v$v"
done

merge() {  # merge <branch> <message>
  git checkout main
  git merge --no-ff "$1" -m "$2"
}

# 2. Flask application
git checkout -b feature/flask-app
git add fitness.py
git commit -m "feat: extract fitness business logic (programs, calories, BMI) into fitness.py"
git add db.py
git commit -m "feat: add SQLite persistence layer for clients, progress and workouts"
git add app.py templates/ requirements.txt
git commit -m "feat: add Flask REST API with client, progress and workout endpoints"
merge feature/flask-app "Merge branch 'feature/flask-app'"

# 3. Tests
git checkout -b feature/unit-tests
git add requirements-dev.txt pytest.ini .flake8 tests/conftest.py
git commit -m "test: configure pytest, flake8 and shared fixtures"
git add tests/test_fitness.py
git commit -m "test: add unit tests for fitness business logic"
git add tests/test_app.py
git commit -m "test: add API tests covering success and error paths"
merge feature/unit-tests "Merge branch 'feature/unit-tests'"

# 4. Docker
git checkout -b infra/docker
git add Dockerfile .dockerignore
git commit -m "build: add multi-stage, non-root Dockerfile with healthcheck"
merge infra/docker "Merge branch 'infra/docker'"

# 5. CI pipelines
git checkout -b ci/github-actions
git add .github/workflows/main.yml
git commit -m "ci: add GitHub Actions pipeline (lint, docker build, tests in container)"
merge ci/github-actions "Merge branch 'ci/github-actions'"

git checkout -b ci/jenkins
git add Jenkinsfile
git commit -m "ci: add Jenkins declarative pipeline for BUILD quality gate"
merge ci/jenkins "Merge branch 'ci/jenkins'"

# 6. Docs
git checkout -b docs/readme
git add README.md scripts/
git commit -m "docs: add README with setup, testing and CI/CD overview"
merge docs/readme "Merge branch 'docs/readme'"

git tag -a v1.0.0 -m "ACEest Fitness Flask API v1.0.0"
git status --short
git log --oneline --graph --all | head -40
echo
echo "Done. Next: git remote add origin https://github.com/<user>/aceest-fitness.git"
echo "      git push -u origin --all && git push origin --tags"
