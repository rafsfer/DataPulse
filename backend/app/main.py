from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router
from app.api.platform import router as platform_router
from app.core.config import get_settings
from app.core.logging import configure_logging

configure_logging()
app = FastAPI(
    title="DataPulse",
    description="Data Reliability & Intelligence Platform for Atlas Commerce.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)
app.include_router(router)

app.include_router(platform_router)
