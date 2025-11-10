"""Main API v1 router."""

from fastapi import APIRouter

from app.api.v1 import bluetooth, ha_bluetooth, health, modules, submissions
from app.config import get_settings

settings = get_settings()
api_router = APIRouter()

# Include module routes
api_router.include_router(modules.router, tags=["modules"])

# Include submission routes
api_router.include_router(submissions.router, tags=["submissions"])

# Include health routes
api_router.include_router(health.router, tags=["health"])

# Include Home Assistant Bluetooth integration
api_router.include_router(ha_bluetooth.router, tags=["ha-bluetooth"])
api_router.include_router(bluetooth.router, tags=["bluetooth"])

# Conditionally include debug exploration tools
# These endpoints allow BLE protocol exploration via the HA UI
if settings.enable_debug_tools:
    from app.api.v1 import debug
    api_router.include_router(debug.router, tags=["debug"])
