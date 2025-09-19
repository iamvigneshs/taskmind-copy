# Copyright (c) 2025 Acarin Inc. All rights reserved.
# Proprietary and confidential.
from __future__ import annotations

from fastapi import FastAPI

from .database import init_db
from .routers import tasks

app = FastAPI(title="MissionMind MCP API", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


app.include_router(tasks.router)


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
