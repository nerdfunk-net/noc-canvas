from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .core.config import settings
from .core.cache import cache_service
from .core.db_init import full_database_setup
from .api import (
    auth,
    nautobot,
    checkmk,
    settings as settings_api,
    jobs,
    canvas,
)
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting NOC Canvas application...")

    # Check database configuration
    logger.info("Checking database configuration...")
    try:
        from .core.yaml_config import load_database_config, validate_database_config

        config = load_database_config()

        if not config or not validate_database_config(config):
            error_msg = (
                "❌ CRITICAL: No valid database configuration found!\n"
                "Database is required to run this application.\n"
                "Please configure database settings using one of these methods:\n"
                "1. Environment variables: NOC_DATABASE, NOC_USERNAME, NOC_PASSWORD\n"
                "2. YAML file: ./data/settings/database.yaml\n"
                "3. Use the settings page in the application"
            )
            logger.error(error_msg)
            raise RuntimeError("Database configuration required")

        logger.info("✅ Database configuration found and valid")

        # Initialize database
        logger.info("Initializing database...")
        success = full_database_setup()
        if success:
            logger.info("✅ Database initialization completed successfully")
        else:
            logger.error(
                "❌ Database initialization failed - application may not work correctly"
            )
            raise RuntimeError("Database initialization failed")

    except Exception as e:
        logger.error(f"❌ Database setup error: {e}")
        raise

    # Connect to cache
    await cache_service.connect()
    logger.info("✅ Application startup completed")

    yield

    # Shutdown
    logger.info("Shutting down NOC Canvas application...")
    await cache_service.disconnect()
    logger.info("✅ Application shutdown completed")


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
app.include_router(canvas.router, prefix="/api/canvas", tags=["canvas"])
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
            "canvas": "/api/canvas",
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
