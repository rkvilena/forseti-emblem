FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code

COPY backend/requirements.txt /code/backend/requirements.txt
# No BuildKit cache mount here: Cloud Build's `gcr.io/cloud-builders/docker` step runs the
# legacy builder, where `RUN --mount=type=cache` fails with "the --mount option requires
# BuildKit". The install already passes --no-cache-dir, so there was nothing to cache anyway.
RUN pip install --no-cache-dir -r /code/backend/requirements.txt

COPY backend /code/backend

EXPOSE 8080

CMD ["bash", "/code/backend/entrypoint.sh"]
