"""FastAPI entrypoint for the lean copilot backend."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.core.settings import settings
from api.routes.copilot import router as copilot_router

app = FastAPI(title="Babel Copilot API")

frontend_origins = [origin.strip() for origin in settings.FRONTEND_ORIGIN.split(",") if origin.strip()]
if not frontend_origins:
    frontend_origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=list({*frontend_origins}),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(copilot_router)


@app.get("/")
async def root():
    return {"ok": True, "name": "babel-copilot"}


@app.get("/status")
async def status():
    return {"status": "healthy"}
