from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.config import DEFAULT_DB_PATH, ROOT_DIR
from backend.database import Database
from backend.routes import devices, network, scans, settings
from backend.scanner.coordinator import ScanCoordinator


logging.basicConfig(level=os.getenv("NETSCOPE_LOG_LEVEL", "INFO"))


def create_app(db_path: str | Path | None = None) -> FastAPI:
    database_path = Path(db_path or os.getenv("NETSCOPE_DB", DEFAULT_DB_PATH))

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        database = Database(database_path)
        database.initialize()
        app.state.database = database
        app.state.scanner = ScanCoordinator(database, ROOT_DIR / "data" / "oui.csv")
        yield
        database.close()

    app = FastAPI(
        title="NetScope",
        description="Local network discovery and device monitoring",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(network.router)
    app.include_router(devices.router)
    app.include_router(scans.router)
    app.include_router(settings.router)

    @app.get("/health", include_in_schema=False)
    def health() -> dict[str, str]:
        return {"status": "ok"}

    frontend_dist = ROOT_DIR / "frontend" / "dist"
    assets = frontend_dist / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    if (frontend_dist / "index.html").exists():
        @app.get("/{path:path}", include_in_schema=False)
        def frontend(path: str) -> FileResponse:
            if path.startswith("api/"):
                raise HTTPException(status_code=404, detail="API endpoint not found")
            return FileResponse(frontend_dist / "index.html")

    return app


app = create_app()
