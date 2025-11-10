"""Health check endpoints."""

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "version": settings.version}


@router.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "name": settings.project_name,
        "version": settings.version,
        "docs_url": f"{settings.api_v1_prefix}/docs",
    }


@router.get("/config")
async def app_config() -> dict[str, object]:
    """Expose runtime configuration for the frontend."""
    return {
        "version": settings.version,
        "device_name_patterns": settings.device_name_patterns,
        "auto_discover": settings.auto_discover,
        "enable_debug_ble": settings.enable_debug_ble,
        "ble_trace_logging": settings.ble_trace_logging,
        "enable_debug_tools": settings.enable_debug_tools,
        "scan_interval": settings.scan_interval,
        "rssi_threshold": settings.rssi_threshold,
        "connection_timeout": settings.connection_timeout,
        "sfp_service_uuid": settings.sfp_service_uuid,
        "sfp_write_char_uuid": settings.sfp_write_char_uuid,
        "sfp_notify_char_uuid": settings.sfp_notify_char_uuid,
    }
