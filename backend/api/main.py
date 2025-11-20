"""FastAPI entrypoint for the lean copilot backend."""
import asyncio
from contextlib import suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.core.settings import settings
from api.routes.copilot import router as copilot_router
from api.routes.upload import router as upload_router
from api.routes.documents import router as documents_router
from api.routes.clauses import router as clauses_router
from api.workers.runner import run_worker_loop

app = FastAPI(title="Babel Copilot API")

default_frontend_origins = {
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
}
frontend_origins = {
    origin.strip()
    for origin in settings.FRONTEND_ORIGIN.split(",")
    if origin.strip()
}
if not frontend_origins:
    frontend_origins = default_frontend_origins
else:
    frontend_origins |= default_frontend_origins

from api.core.logging import logger
logger.info("CORS allowed origins: %s", sorted(frontend_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(frontend_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(copilot_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(clauses_router, prefix="/api")


@app.on_event("startup")
async def _start_worker() -> None:
    if settings.AUTO_START_WORKER:
        app.state.worker_task = asyncio.create_task(run_worker_loop())


@app.on_event("shutdown")
async def _stop_worker() -> None:
    task = getattr(app.state, "worker_task", None)
    if task:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


@app.get("/")
async def root():
    return {"ok": True, "name": "babel-copilot"}


@app.get("/status")
async def status():
    return {"status": "healthy"}
