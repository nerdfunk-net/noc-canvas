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
    devices,
    credentials,
    shapes,
    cache,
    topology,
)
# Removed old routers that were causing duplicate endpoints:
# from .routers import (
#     nautobot_devices,
#     nautobot_metadata,
#     nautobot_jobs,
#     nautobot_network,
# )
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

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

    # Clean expired cache on startup if configured
    try:
        from .core.database import get_db
        from .services.device_cache_service import DeviceCacheService
        from .models.settings import AppSettings
        import json

        db = next(get_db())
        try:
            # Get cache settings from database (stored as key-value)
            cache_settings = db.query(AppSettings).filter(
                AppSettings.key == "cache_settings"
            ).first()

            if cache_settings and cache_settings.value:
                settings_data = json.loads(cache_settings.value)
                if settings_data.get("cleanExpiredOnStartup", True):  # Default to True
                    logger.info("🧹 Cleaning expired cache on startup...")
                    count = DeviceCacheService.clean_expired_cache(db, None)
                    logger.info(f"✅ Cleaned {count} expired cache entries on startup")
                else:
                    logger.info("ℹ️ Clean expired cache on startup is disabled")
            else:
                # Default behavior: clean on startup
                logger.info("🧹 Cleaning expired cache on startup (default)...")
                count = DeviceCacheService.clean_expired_cache(db, None)
                logger.info(f"✅ Cleaned {count} expired cache entries on startup")
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"⚠️ Could not clean expired cache on startup: {e}")

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

# Nautobot routers - using GraphQL-based implementation
# Note: nautobot.router contains all device endpoints using GraphQL
app.include_router(nautobot.router, prefix="/api/nautobot", tags=["nautobot"])
# Removed old REST-based routers to avoid duplicates:
# - nautobot_devices.router (replaced by nautobot.router with GraphQL)
# - nautobot_metadata.router, nautobot_jobs.router, nautobot_network.router
# All functionality now consolidated in nautobot.router

app.include_router(devices.router, prefix="/api/devices", tags=["devices"])
app.include_router(credentials.router, prefix="/api/credentials", tags=["credentials"])
app.include_router(checkmk.router, prefix="/api/checkmk", tags=["checkmk"])
app.include_router(settings_api.router, prefix="/api/settings", tags=["settings"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["background-jobs"])
app.include_router(shapes.router, prefix="/api", tags=["shapes"])
app.include_router(cache.router, prefix="/api", tags=["cache"])
app.include_router(topology.router, prefix="/api", tags=["topology"])


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
            "nautobot_devices": "/api/nautobot/devices",
            "nautobot_metadata": "/api/nautobot/locations (and other metadata)",
            "nautobot_jobs": "/api/nautobot/devices/onboard (and sync)",
            "nautobot_network": "/api/nautobot/test (and check-ip)",
            "devices": "/api/devices",
            "credentials": "/api/credentials",
            "checkmk": "/api/checkmk",
            "settings": "/api/settings",
            "jobs": "/api/jobs",
            "shapes": "/api/shapes",
            "cache": "/api/cache",
            "topology": "/api/topology",
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
