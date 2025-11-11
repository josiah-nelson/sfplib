"""FastAPI application with modern patterns."""

from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.config import get_settings
from app.core.database import init_db
from app.core.logging import setup_logging

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager (replaces deprecated on_event).

    Handles startup and shutdown logic.
    """
    # Startup
    setup_logging(settings.log_level, settings.log_json)
    logger = structlog.get_logger()
    logger.info(
        "application_startup",
        version=settings.version,
    )

    # Initialize BLE tracer if enabled
    if settings.ble_trace_logging:
        from app.services.ha_bluetooth.ble_tracer import init_tracer
        init_tracer(enabled=True)
        logger.info("ble_tracer_enabled")

    await init_db()
    logger.info("database_initialized")

    # Initialize Bluetooth service (HA add-on only)
    bluetooth_service = None
    backup_service = None

    # Home Assistant Add-On mode: Use HA Bluetooth API
    try:
        from app.api.v1.ha_bluetooth import set_ha_bluetooth_client
        from app.services.ha_bluetooth import HomeAssistantBluetoothClient

        bluetooth_service = HomeAssistantBluetoothClient(
            ha_api_url=settings.ha_api_url,
            ha_ws_url=settings.ha_ws_url,
            supervisor_token=settings.supervisor_token,
            device_patterns=settings.device_name_patterns,
        )
        await bluetooth_service.start()
        set_ha_bluetooth_client(bluetooth_service)
        logger.info("ha_bluetooth_client_started", patterns=settings.device_name_patterns)

    except Exception as e:
        logger.error("ha_bluetooth_client_startup_failed", error=str(e), exc_info=True)
        raise  # Don't start if Bluetooth is essential

    # Start database backup service
    try:
        from app.services.backup_service import DatabaseBackupService
        backup_service = DatabaseBackupService(max_backups=settings.database_backup_max_count)
        await backup_service.start()
    except Exception as e:
        logger.error("backup_service_startup_failed", error=str(e), exc_info=True)

    yield

    # Shutdown
    if backup_service:
        try:
            await backup_service.stop()
            logger.info("backup_service_stopped")
        except Exception as e:
            logger.error("backup_service_shutdown_failed", error=str(e))

    if bluetooth_service:
        try:
            await bluetooth_service.stop()
            logger.info("bluetooth_service_stopped")
        except Exception as e:
            logger.error("bluetooth_service_shutdown_failed", error=str(e))

    # Close BLE tracer if enabled
    if settings.ble_trace_logging:
        from app.services.ha_bluetooth.ble_tracer import get_tracer
        get_tracer().close()

    logger.info("application_shutdown")


app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    lifespan=lifespan,
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    docs_url=f"{settings.api_v1_prefix}/docs",
    redoc_url=f"{settings.api_v1_prefix}/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(api_router, prefix=settings.api_v1_prefix)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Root health check."""
    return {"status": "healthy", "version": settings.version}


# Backward compatibility: Keep legacy /api routes
@app.get("/api/modules")
async def legacy_get_modules():
    """Legacy endpoint - redirects to v1."""
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url=f"{settings.api_v1_prefix}/modules")


# Serve static UI files for Home Assistant add-on ingress
from fastapi.responses import FileResponse

static_ui_path = Path("/usr/share/sfplib/ui")

@app.get("/app.js")
async def serve_app_js():
    """Serve app.js."""
    if not static_ui_path.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="UI not available")
    return FileResponse(static_ui_path / "app.js", media_type="application/javascript")

@app.get("/logo.svg")
async def serve_logo():
    """Serve logo.svg."""
    if not static_ui_path.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="UI not available")
    return FileResponse(static_ui_path / "logo.svg", media_type="image/svg+xml")

@app.get("/")
async def serve_ui():
    """Serve the UI index.html at root path."""
    if not static_ui_path.exists():
        return {
            "name": settings.project_name,
            "version": settings.version,
            "docs_url": f"{settings.api_v1_prefix}/docs",
        }
    return FileResponse(static_ui_path / "index.html")

logger = structlog.get_logger()
if static_ui_path.exists():
    logger.info("static_ui_available", path=str(static_ui_path))
else:
    logger.warning("static_ui_not_found", path=str(static_ui_path))
