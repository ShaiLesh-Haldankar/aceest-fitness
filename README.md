# ACEest Fitness & Gym — Flask API with CI/CD

![CI/CD Pipeline](https://github.com/ShaiLesh-Haldankar/aceest-fitness/actions/workflows/main.yml/badge.svg)

A Flask REST service for ACEest Fitness & Gym (client management, fitness programs, BMI/calorie calculators, progress and workout tracking), shipped through an automated DevOps pipeline: **Git → Pytest → Docker → Jenkins BUILD → GitHub Actions**.

The business logic is ported from the legacy Tkinter desktop versions (`legacy/Aceestver-1.0.py` … `Aceestver-3.2.4.py`) into a modular, testable web service.

---

## Repository layout

```
.
├── app.py                  # Flask app factory + REST routes
├── fitness.py              # Pure business logic (programs, calories, BMI, validation)
├── db.py                   # SQLite persistence layer
├── templates/index.html    # Landing page
├── requirements.txt        # Runtime dependencies
├── requirements-dev.txt    # Test / lint dependencies
├── tests/                  # Pytest suite (unit + API tests)
├── Dockerfile              # Multi-stage build: builder → test → runtime
├── Jenkinsfile             # Jenkins declarative pipeline (BUILD & quality gate)
├── .github/workflows/main.yml  # GitHub Actions CI/CD
└── legacy/                 # Original Tkinter versions supplied with the assignment
```

## API overview

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Landing page with programs |
| GET | `/health` | Health check (used by Docker HEALTHCHECK & CI smoke test) |
| GET | `/api/programs`, `/api/programs/<code>` | Program catalogue (`FL`, `MG`, `BG`) |
| GET | `/api/bmi?weight=70&height=175` | BMI + category |
| GET | `/api/calories?weight=80&program=FL` | Daily calorie target |
| GET / POST | `/api/clients` | List / create clients |
| GET / DELETE | `/api/clients/<name>` | Fetch / delete a client |
| POST | `/api/clients/<name>/generate-program` | AI-style program template |
| GET / POST | `/api/clients/<name>/progress` | Weekly adherence tracking |
| GET / POST | `/api/clients/<name>/workouts` | Workout log |

Example:

```bash
curl -X POST localhost:5000/api/clients -H "Content-Type: application/json" \
     -d '{"name":"Arjun","age":28,"height":175,"weight":80,"program":"FL"}'
```

---

## 1. Local setup & execution

Prerequisites: Python 3.10+, Git, Docker.

```bash
git clone https://github.com/ShaiLesh-Haldankar/aceest-fitness.git
cd aceest-fitness
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python app.py                      # http://localhost:5000
```

### Run with Docker

```bash
docker build --target runtime -t aceest-fitness:latest .
docker run -d -p 5000:5000 --name aceest aceest-fitness:latest
curl http://localhost:5000/health
```

## 2. Running tests manually

```bash
source .venv/bin/activate
pytest                                   # all tests
pytest --cov=. --cov-report=term-missing # with coverage
flake8 .                                 # lint
```

Inside a container (same as CI):

```bash
docker build --target test -t aceest-fitness-test .
docker run --rm aceest-fitness-test
```

The suite (66 tests) covers the pure logic in `fitness.py` (calorie/BMI maths, BMI category boundaries, input validation, program generation) and every API endpoint including error paths (400/404/409). Each test runs against an isolated temporary SQLite database.

---

## 3. CI/CD integration logic

```
 developer push / PR
        │
        ▼
   ┌──────────┐      ┌───────────────────────── GitHub Actions ─────────────────────────┐
   │  GitHub  │ ───▶ │ Build & Lint ──▶ Docker Image Assembly ──▶ Pytest in container   │
   └──────────┘      └──────────────────────────────────────────────────────────────────┘
        │
        │ pollSCM / webhook
        ▼
   ┌─────────────────────────────── Jenkins BUILD ───────────────────────────────┐
   │ Checkout ─▶ Python venv ─▶ Build & Lint ─▶ Unit Tests ─▶ Docker Build ─▶ Container Tests │
   └──────────────────────────────────────────────────────────────────────────────┘
```

### GitHub Actions (`.github/workflows/main.yml`)

Triggered on **every push** and on **pull requests to `main`**. Three dependent jobs; a failure stops the pipeline:

1. **Build & Lint** — installs dependencies, `py_compile` checks for syntax errors, `flake8` enforces style.
2. **Docker Image Assembly** — builds the `runtime` image and smoke-tests `/health` on a running container.
3. **Automated Testing** — builds the `test` image and runs the Pytest suite *inside the container* with coverage.

### Jenkins (`Jenkinsfile`)

A Pipeline job configured with *Pipeline script from SCM* pointing at this GitHub repo. Jenkins polls GitHub every 5 minutes (or reacts to a webhook), pulls the latest commit into a clean workspace, and acts as a secondary quality gate: venv build → lint → Pytest (JUnit report published) → Docker build → in-container tests. Any failing stage marks the BUILD as failed.

### Docker image design

* **Multi-stage**: dependencies compiled to wheels in a `builder` stage; the `runtime` stage only copies the wheels and the three app modules — no compilers, tests or caches.
* **`python:3.12-slim`** base, `--no-cache-dir` installs, `.dockerignore` keeps the build context small.
* Runs as a **non-root** `aceest` user, served by **gunicorn**, with a `HEALTHCHECK`.
* A separate `test` target lets CI run Pytest inside a container without shipping test tools in production.

---

## Branching & commit conventions

* `main` — always releasable; protected, updated via merge.
* `feature/*`, `infra/*`, `ci/*`, `docs/*` — short-lived branches merged with `--no-ff`.
* Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `test:`, `ci:`, `build:`, `docs:`, `chore:`).
* Legacy versions are tagged `legacy-v1.0` … `legacy-v3.2.4`; releases are tagged `v1.0.0`.
