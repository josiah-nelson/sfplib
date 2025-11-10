"""Home Assistant Bluetooth API endpoints."""

import structlog
from fastapi import APIRouter, Depends, HTTPException

from app.services.ha_bluetooth import (
    HABluetoothDevice,
    HADeviceConnectionRequest,
    HADeviceConnectionResponse,
    HomeAssistantBluetoothClient,
)
from app.services.ha_bluetooth.schemas import HABluetoothStatus

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/ha-bluetooth", tags=["Home Assistant Bluetooth"])

# Global client instance (initialized in main.py lifespan)
_ha_bluetooth_client: HomeAssistantBluetoothClient | None = None


def set_ha_bluetooth_client(client: HomeAssistantBluetoothClient) -> None:
    """Set the global HA Bluetooth client instance."""
    global _ha_bluetooth_client
    _ha_bluetooth_client = client


def get_ha_bluetooth_client() -> HomeAssistantBluetoothClient:
    """Dependency to get the HA Bluetooth client."""
    if _ha_bluetooth_client is None:
        raise HTTPException(
            status_code=503,
            detail="HA Bluetooth client not initialized. "
            "This endpoint is only available when running as a Home Assistant add-on."
        )
    return _ha_bluetooth_client


@router.get("/status", response_model=HABluetoothStatus)
async def get_status(
    client: HomeAssistantBluetoothClient = Depends(get_ha_bluetooth_client)
) -> HABluetoothStatus:
    """
    Get status of Home Assistant Bluetooth integration.

    Returns information about the connection to HA and discovered devices.
    """
    try:
        devices = await client.get_bluetooth_devices()

        return HABluetoothStatus(
            enabled=True,
            devices_discovered=len(devices),
            ha_api_url=client.ha_api_url,
            connected=client.is_connected,
        )
    except Exception as e:
        logger.error("ha_bluetooth_status_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/devices", response_model=list[HABluetoothDevice])
async def get_devices(
    client: HomeAssistantBluetoothClient = Depends(get_ha_bluetooth_client)
) -> list[HABluetoothDevice]:
    """
    Get auto-discovered Bluetooth devices from Home Assistant.

    Returns devices matching configured patterns ("SFP", "Wizard", etc.).
    This endpoint replaces ESPHome mDNS device discovery when running as an add-on.

    The device list is automatically filtered based on the device_name_patterns
    configuration option in the add-on settings.
    """
    try:
        devices = await client.get_bluetooth_devices()
        logger.debug("devices_retrieved", count=len(devices))
        return devices

    except Exception as e:
        logger.error("devices_get_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get devices: {e}") from e


@router.post("/connect", response_model=HADeviceConnectionResponse)
async def connect_device(
    request: HADeviceConnectionRequest,
    client: HomeAssistantBluetoothClient = Depends(get_ha_bluetooth_client)
) -> HADeviceConnectionResponse:
    """
    Connect to a BLE device via Home Assistant and retrieve UUIDs.

    This endpoint:
    1. Verifies the device is discovered
    2. Returns cached UUIDs for SFP Wizard (or connects via HA Bluetooth API)
    3. Returns service UUID, notify UUID, and write UUID

    The returned UUIDs should be cached by the frontend for future operations.

    Args:
        request: Connection request with device MAC address

    Returns:
        Connection response with GATT service/characteristic UUIDs

    Raises:
        404: Device not found or not advertising
        500: Connection failed
    """
    try:
        result = await client.connect_to_device(request.mac_address)
        logger.info(
            "device_connected",
            mac=request.mac_address,
            service_uuid=result.service_uuid,
        )
        return result

    except ValueError as e:
        logger.warning("device_connection_not_found", mac=request.mac_address, error=str(e))
        raise HTTPException(status_code=404, detail=str(e)) from e

    except RuntimeError as e:
        logger.error("device_connection_runtime_error", mac=request.mac_address, error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e

    except Exception as e:
        logger.error("device_connection_unexpected_error", mac=request.mac_address, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Connection failed: {e}") from e
