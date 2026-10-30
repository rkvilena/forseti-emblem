# Infrastructure

Layout of the build and hosting assets for Forsetiemblem.

- **Region**: `asia-northeast1` (GCP project `rkvilena`)
- **Postgres**: Supabase (external, not managed here)
- **Redis**: Upstash (external, not managed here)

Deployment details (pipelines, triggers, secrets, rollback) are intentionally not documented
here yet; see [`documentation/deployment-audit.md`](../documentation/deployment-audit.md)
for the current findings and open work.

## Layout

```text
infrastructure/
├── cloudbuild/
│   ├── build.sh                 # build + smoke-test an image locally
│   ├── backend/
│   │   ├── cloudbuild.yaml      # backend build pipeline
│   │   ├── Dockerfile           # production backend image
│   │   └── .env.example         # local template (real .env is gitignored)
│   └── frontend/
│       ├── cloudbuild.yaml      # frontend build pipeline
│       ├── Dockerfile           # production frontend image
│       └── .env.example         # local template (real .env is gitignored)
└── compose/
    ├── local.dev.yml            # local Postgres (api/web services are unused)
    └── vm.db.yml                # standalone Postgres/pgvector for a VM
```

## Local development

See the root [`README.md`](../README.md). The Compose file's `api`/`web` services are
broken (they reference a missing `backend/Dockerfile.dev`), so the supported local path is
running backend and frontend natively with Docker only for Postgres and Redis.

Building and smoke-testing an image locally:

```bash
bash infrastructure/cloudbuild/build.sh \
  infrastructure/cloudbuild/backend/Dockerfile 8080 infrastructure/cloudbuild/backend/.env

bash infrastructure/cloudbuild/build.sh \
  infrastructure/cloudbuild/frontend/Dockerfile 3000 infrastructure/cloudbuild/frontend/.env
```
