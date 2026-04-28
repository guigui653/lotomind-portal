"""
LotoMind Enterprise — Python Intelligence Service
FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.redis_client import redis_manager
from app.core.scheduler import start_scheduler, shutdown_scheduler
from app.core.migrations import run_migrations
from app.routers import analysis_router, health_router, sync_router, prediction_router, consultant_router


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Manage application startup and shutdown events."""
    # 1. Database Migrations
    await run_migrations()
    
    # 2. Start Scheduler
    start_scheduler()
    
    # 3. Connect Redis
    await redis_manager.connect()
    
    yield
    
    # Shutdown
    await redis_manager.disconnect()
    shutdown_scheduler()


app = FastAPI(
    title="LotoMind Intelligence",
    description="Serviço de Data Science para análise estatística da Lotofácil",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────
app.include_router(health_router.router, prefix="/api/v1", tags=["Health"])
app.include_router(analysis_router.router, prefix="/api/v1/analysis", tags=["Analysis"])
app.include_router(sync_router.router, prefix="/api/v1", tags=["Sync"])
app.include_router(prediction_router.router, prefix="/api/v1", tags=["Prediction"])
app.include_router(consultant_router.router, prefix="/api/v1/analysis", tags=["Consultant"])
