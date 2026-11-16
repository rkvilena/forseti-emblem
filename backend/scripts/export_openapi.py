"""Export the FastAPI OpenAPI schema to JSON without a server or database.

The schema is derived from the local FastAPI app object in-process, so this
works offline: no uvicorn process, no HTTP request, and no database connection.
Creating the SQLAlchemy engine is lazy, but importing the app still requires a
``DATABASE_URL``; when it is unset this script supplies a harmless placeholder.

Usage (from the repository root):

    python backend/scripts/export_openapi.py --output openapi.json

Use ``--output -`` (the default) to write the schema to stdout.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

# Importing the app builds a SQLAlchemy engine, which needs a URL but does not
# connect, so a placeholder keeps generation possible without a database.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/forsetiemblem",
)


def build_schema() -> dict:
    """Return the OpenAPI schema for the local FastAPI application."""

    from app.main import app

    return app.openapi()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export the local FastAPI OpenAPI schema as JSON."
    )
    parser.add_argument(
        "--output",
        "-o",
        default="-",
        help="Destination file, or '-' to write to stdout (default).",
    )
    args = parser.parse_args()

    text = json.dumps(build_schema(), indent=2, sort_keys=True) + "\n"

    if args.output == "-":
        sys.stdout.write(text)
    else:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
