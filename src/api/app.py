"""Wine Cellar API — FastAPI application."""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from src.api.deps import close_pool, init_pool
from src.api.routers import auth, cellar, ingest, labels, log, stats, wines, wishlist

from mees_shared.usage_tracker import init_usage_tracker, shutdown_usage_tracker, track_usage_middleware, usage_pageview_router
from mees_shared.dashboard import register_with_dashboard
from mees_shared.spa import mount_spa

STATIC_DIR = Path(_project_root) / "static"

_log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_pool()
    init_usage_tracker("wine", settings.usage_dsn)
    task = asyncio.create_task(register_with_dashboard(
        label="Wine",
        href="https://wine.mees.st",
        icon="\U0001F377",
        sort_order=3,
        registry_key=settings.dash_registry_key,
    ))
    yield
    task.cancel()
    shutdown_usage_tracker()
    close_pool()


app = FastAPI(
    title="Wine Cellar API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(track_usage_middleware)

# Mount routers
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(wines.router, prefix="/api/v1", tags=["wines"])
app.include_router(log.router, prefix="/api/v1", tags=["log"])
app.include_router(cellar.router, prefix="/api/v1", tags=["cellar"])
app.include_router(wishlist.router, prefix="/api/v1", tags=["wishlist"])
app.include_router(stats.router, prefix="/api/v1", tags=["stats"])
app.include_router(ingest.router, prefix="/api/v1", tags=["ingest"])
app.include_router(labels.router, prefix="/api/v1", tags=["labels"])
app.include_router(usage_pageview_router, prefix="/api/v1")

# SPA serving + /health endpoint
mount_spa(app, STATIC_DIR)
