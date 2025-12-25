# Backend Dockerfile (FastAPI)
# Build context should be the repo root, so we can copy the ./backend folder.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code

# Install Python dependencies first (better layer caching)
COPY backend/requirements.txt /code/backend/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r /code/backend/requirements.txt

# Copy backend source
COPY backend /code/backend

EXPOSE 8000

# Cloud Run provides $PORT
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
