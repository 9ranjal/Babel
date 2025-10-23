# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.core.settings import settings
from api.routes.negotiate import router as negotiate_router
from api.routes.personas import router as personas_router
from api.routes.copilot import router as copilot_router
from api.routes.copilot_v2 import router as copilot_v2_router
from api.routes.transactions import router as transactions_router
from api.routes.migrate import router as migrate_router

app = FastAPI(title="Termcraft API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(personas_router)
app.include_router(negotiate_router)
app.include_router(copilot_router)  # Legacy copilot routes
app.include_router(copilot_v2_router)  # New modular copilot routes
app.include_router(transactions_router)
app.include_router(migrate_router)

@app.get("/")
def root():
    return {"ok": True, "name": "termcraft-api"}

@app.get("/status")
def status():
    return {"status": "healthy"}



