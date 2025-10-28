# Machi Quest — Alpha 

## Purpose
Machi Quest is a gamified productivity platform that connects user data sources (starting with GitHub) to a persistent virtual pet and garden. This repository is a scaffold implementing an end-to-end MVP vertical slice: user auth, GitHub OAuth + webhook ingestion, canonical event normalization, scoring → pet state updates, a React + Phaser frontend, and basic observability and IaC skeletons.

---

## Contents
- `backend/` — FastAPI application, DB models, normalization and scoring services.
- `backend/worker/` — Background worker to process normalization and scoring jobs.
- `frontend/` — Next.js (or create-react-app) prototype with Phaser scene for the pet.
- `charts/machi-quest/` — Helm chart skeleton for Kubernetes deployment (Week 5 target).
- `infra/terraform/` — Terraform skeleton for cloud provisioning (RDS, S3, cluster placeholders).
- `.github/workflows/ci.yml` — CI pipeline for lint/test/build.
- `docker-compose.yml` — Local development compose file.

---

## Quickstart — Local development (Day 1)

**Prerequisites**
- Docker & Docker Compose
- Python 3.11+ (for local venv testing)
- Node 18+ (if working on frontend components locally)
- `ngrok` or `localhost.run` for exposing local webhooks to GitHub

**1. Copy example env**
```bash
cp .env.example .env
# Edit .env to set DATABASE_URL, REDIS_URL, LOCAL_HOST etc.

2. Start services
docker-compose up --build

Backend: http://localhost:8000


Frontend: http://localhost:3000


Postgres: inside container, link to DATABASE_URL


3. Apply migrations
# inside backend container or local venv
alembic upgrade head

4. Create a test user
python scripts/db_seed.py --create-user

5. Register & test GitHub Webhooks
Create a GitHub OAuth app (set callback to http://<tunnel-host>/api/v1/auth/github/callback)


Configure webhook delivery to http://<tunnel-host>/api/v1/webhooks/github and generate a webhook secret


Use the frontend to connect GitHub, or trigger a webhook manually via GitHub repo settings




Running tests
# backend
pytest backend/tests
# frontend
cd frontend && npm test


Development workflow
Branch per feature: feature/<ticket-short-title>


Small PRs, CI runs on each PR


Merge to main triggers CI to build & push containers (see .github/workflows/ci.yml)



Architecture (short)
See docs/architecture.md for a full diagram. At a high level:
Webhooks & OAuth integrations → webhook receiver → publish to queue → normalizer workers → scoring engine → update pet state in Postgres and Redis → frontend listens via WebSocket for state changes.
