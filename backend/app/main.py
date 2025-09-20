from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .core.database import engine, Base
from .core.config import settings
from .core.cache import cache_service
from .api import auth, devices, nautobot, checkmk, settings_local as settings_api, jobs

# Create database tables
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await cache_service.connect()
    yield
    # Shutdown
    await cache_service.disconnect()


app = FastAPI(
    title="NOC Canvas API",
    version="1.0.0",
    description="NOC Canvas - Network Operations Center Canvas API with Nautobot and CheckMK integration",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(devices.router, prefix="/api/devices", tags=["devices"])
app.include_router(nautobot.router, prefix="/api/nautobot", tags=["nautobot"])
app.include_router(checkmk.router, prefix="/api/checkmk", tags=["checkmk"])
app.include_router(settings_api.router, prefix="/api/settings", tags=["settings"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["background-jobs"])


@app.get("/")
async def root():
    return {
        "message": "NOC Canvas API",
        "version": "1.0.0",
        "description": "Network Operations Center Canvas with Nautobot and CheckMK integration",
        "endpoints": {
            "auth": "/api/auth",
            "devices": "/api/devices",
            "nautobot": "/api/nautobot",
            "checkmk": "/api/checkmk",
            "settings": "/api/settings",
            "jobs": "/api/jobs",
            "docs": "/docs",
            "openapi": "/openapi.json",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "NOC Canvas API is running",
        "cache_connected": cache_service.redis is not None,
    }