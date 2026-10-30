# Forsetiemblem Backend

FastAPI backend for the Fire Emblem RAG application. It ingests chapter data from the Fire Emblem wiki, stores it in Postgres with pgvector embeddings, and serves the chat and ingestion APIs used by the frontend.

> For architecture, data flows, the full API reference, and design decisions, see [documentation/backend.md](../documentation/backend.md).

## Prerequisites

- **Python 3.11+**
- **Postgres with pgvector** (e.g. the `pgvector/pgvector:pg16` Docker image)
- **Redis** (e.g. `redis:7`) — required for chat endpoints
- **An OpenAI API key**
- Bash (Git Bash on Windows, or WSL) for the helper scripts

## 1. Start Postgres and Redis

If they aren't already running (the root README Quick Start also covers this):

```bash
docker run -d --name forsetiemblem-db \
  -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=forsetiemblem \
  -p 5432:5432 pgvector/pgvector:pg16

docker run -d --name forsetiemblem-redis -p 6379:6379 redis:7
```

## 2. Create the environment file

```bash
cd backend
cp .env.example .env
```

Edit `backend/.env`:

| Variable | Must change? | Notes |
| -------- | ------------ | ----- |
| `OPENAI_API_KEY` | **Yes** | Required for embeddings and chat |
| `DATABASE_URL` | Only for a non-local DB | Default points at the local Docker Postgres |
| `REDIS_URL` | Only for a non-local Redis | Default `redis://localhost:6379/0` |
| `CORS_ALLOWED_ORIGIN` | Only for a different frontend origin | Default `http://localhost:3000` |
| `TURNSTILE_SECRET_KEY` | Optional | Set `TURNSTILE_ENABLED=false` if you don't have a key |

`.env.example` is fully annotated (rate limits, cost controls, docs auth). `config.py` always loads `backend/.env` regardless of the working directory; the legacy `DATABASE_HOST`/`DATABASE_PORT`/… variables are ignored — `DATABASE_URL` wins.

## 3. Create the virtual environment

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash
# source .venv/bin/activate     # Linux / macOS
pip install -r requirements.txt
```

## 4. Apply migrations

The schema is managed by Alembic (`alembic.ini`, `alembic/`):

```bash
alembic -c alembic.ini upgrade head
```

`backend/start.sh` runs this automatically on every start.

## 5. Start the server

```bash
bash start.sh
```

This loads `.env`, applies migrations, and starts the FastAPI dev server at **http://localhost:8000** (reload enabled in local mode).

## Verify the Backend

```bash
curl http://localhost:8000/health   # status, environment, DB, pgvector
curl http://localhost:8000/config   # non-sensitive configuration
```

Interactive API docs live at `/docs` and `/redoc`. They are protected when `DOCS_AUTH_ENABLED=true` or automatically in production when `DOCS_USERNAME`/`DOCS_PASSWORD` are set (session mode uses a signed cookie via `/docs-login`).

## Ingest Initial Data

The chat has nothing to answer until at least one chapter is ingested. Ingest by wiki page title (URL-encoded):

```bash
curl -X POST "http://localhost:8000/wiki/page/Prologue%20(Blazing%20Blade)/ingest?generate_embeddings=true"
```

Verify with `GET /chapters`, or open http://localhost:3000/chapters in the frontend. More ingestion options (`/reingest`, category listing, wikitext parsing) are described in [documentation/backend.md](../documentation/backend.md#wiki-and-ingestion).

## Development Commands

All commands run from `backend/` with the venv activated.

| Command | Description |
| ------- | ----------- |
| `bash start.sh` | Load `.env`, apply migrations, start the dev server |
| `pytest` | Run unit tests (`test/unit/`) |
| `bash format.sh` | Format code (Ruff format + Ruff check) |
| `bash format.sh --check` | Check formatting without changing files |
| `bash format.sh --typecheck` | Run Ruff check + mypy |
| `ruff check .` | Lint only |
| `mypy app` | Type checking only |
| `alembic -c alembic.ini upgrade head` | Apply migrations |
| `alembic -c alembic.ini revision --autogenerate -m "message"` | Create a new migration |

## Database Operations

```bash
# Show current migration state
alembic -c alembic.ini current

# Apply all pending migrations
alembic -c alembic.ini upgrade head
```

To wipe the database, use the repo-root script (requires the Postgres container to be running):

```bash
bash ../resetdb.sh
```

> **Warning:** this drops and recreates the database. All ingested chapters are lost. Afterwards, restart the backend so migrations recreate the tables, and re-ingest chapters.

## Production Container

`backend/entrypoint.sh` runs Alembic migrations, then starts uvicorn on `$PORT` (default 8080). Deployment notes are not documented in `infrastructure/README.md` yet; current findings live in [`documentation/deployment-audit.md`](../documentation/deployment-audit.md).

## Troubleshooting

| Symptom | Cause and fix |
| ------- | ------------- |
| Chat endpoints return 500 | Redis unreachable — check `REDIS_URL` and that the Redis container is running. Non-chat endpoints (e.g. `/chapters`, `/health`) still work without Redis |
| `/health` reports pgvector unavailable | Postgres lacks the `vector` extension — use the `pgvector/pgvector` image; `init_db()` attempts `CREATE EXTENSION vector` on startup |
| 500 on chat with "API key" errors | `OPENAI_API_KEY` missing or invalid in `backend/.env` |
| Frontend CORS errors | `CORS_ALLOWED_ORIGIN` doesn't match the frontend origin (default `http://localhost:3000`) |
| Chat returns 400 about Turnstile | `TURNSTILE_ENABLED=true` but no valid secret key — set `TURNSTILE_ENABLED=false` for local development |
| Migrations fail to connect | `DATABASE_URL` points at a database that isn't running, or wrong credentials |
| `docker compose` API build fails | The Compose `api` service references `backend/Dockerfile.dev`, which doesn't currently exist in this repository — use the local setup above instead |

## Related Documentation

- [Architecture and API reference](../documentation/backend.md) — how the backend works internally
- [Frontend guide](../frontend/README.md) — frontend setup
- [Root README](../README.md) — whole-project overview and quick start
