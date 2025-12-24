from fastapi import FastAPI

from .routes import wiki


app = FastAPI(title="Fire Emblem RAG Backend")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(wiki.router)


