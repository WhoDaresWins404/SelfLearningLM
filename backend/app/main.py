from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.app.config import settings
from backend.app.database import init_main_db, init_lake_db
from backend.app.routers import containers, crawls, dashboard, dead_letter, proxies, records
from backend.app.seed import seed_if_empty

app = FastAPI(title=settings.project_name, version="0.1.0")

app.include_router(containers.router)
app.include_router(crawls.router)
app.include_router(dashboard.router)
app.include_router(dead_letter.router)
app.include_router(proxies.router)
app.include_router(records.router)


@app.on_event("startup")
def startup():
    for d in [settings.unstructured_dir, settings.structured_dir, settings.dead_letter_dir]:
        d.mkdir(parents=True, exist_ok=True)
    init_main_db()
    init_lake_db()
    seed_if_empty()

    static_dir = settings.frontend_dist
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="frontend")


@app.get("/api/health")
def health():
    return {"status": "ok"}
