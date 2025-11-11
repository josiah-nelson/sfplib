"""
Bluetooth API using direct Bleak scanner

Uses Bleak's BleakScanner to directly scan for BLE devices via host Bluetooth adapter.
Filters by SFP Wizard service UUID: 8e60f02e-f699-4865-b83f-f40501752184
"""

import base64
import hashlib
import structlog
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Any, List
from bleak import BleakScanner

from app.services.ble_operations import BLEOperationsService
from app.services.sfp_parser import parse_sfp_data
from app.repositories.module_repository import ModuleRepository
from app.core.database import get_db
from app.config import get_settings

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/bluetooth", tags=["bluetooth"])
settings = get_settings()


# ====================================================================
# Constants
# ====================================================================

# SFP Wizard service UUID (firmware v1.0.10)
SFP_SERVICE_UUID = "8e60f02e-f699-4865-b83f-f40501752184"


# ====================================================================
# Request/Response Models
# ====================================================================

class DiscoverResponse(BaseModel):
    devices: List[dict]


class ReadRequest(BaseModel):
    device_address: str
    name: str


class WriteRequest(BaseModel):
    device_address: str
    module_id: int
    verify: bool = True


# ====================================================================
# Endpoints
# ====================================================================

@router.get("/discover")
async def discover_devices() -> DiscoverResponse:
    """
    Discover SFP Wizard devices via direct BLE scanning.

    Uses Bleak's BleakScanner to scan for devices advertising the SFP Wizard
    service UUID: 8e60f02e-f699-4865-b83f-f40501752184

    Returns:
        List of discovered devices with MAC, name, and RSSI
    """
    try:
        logger.info("ble_scan_start", service_uuid=SFP_SERVICE_UUID)

        # Scan for 10 seconds
        discovered_devices = await BleakScanner.discover(
            timeout=10.0,
            return_adv=True  # Return advertisement data
        )

        # Filter by service UUID
        devices = []
        for address, (device, advertisement_data) in discovered_devices.items():
            # Check if device advertises our service UUID
            service_uuids = advertisement_data.service_uuids or []

            if SFP_SERVICE_UUID.lower() in [str(uuid).lower() for uuid in service_uuids]:
                devices.append({
                    "address": address,
                    "name": device.name or address,  # Fallback to MAC if no name
                    "rssi": advertisement_data.rssi,
                    "source": "direct_scan",
                    "last_seen": None
                })
                logger.info(
                    "sfp_wizard_discovered",
                    address=address,
                    name=device.name,
                    rssi=advertisement_data.rssi
                )

        logger.info("ble_scan_complete", devices_found=len(devices))
        return DiscoverResponse(devices=devices)

    except Exception as e:
        logger.error("ble_scan_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to discover devices: {str(e)}"
        )


@router.post("/read")
async def read_module(request: ReadRequest) -> dict[str, Any]:
    """
    Read EEPROM from SFP module via SFP Wizard.

    Full read flow:
    1. Connect to device via Bluetooth
    2. Send POST /sif/start command
    3. Read 256 bytes of EEPROM data
    4. Parse SFF-8472 data (vendor, model, serial)
    5. Save to database
    6. Return module details

    Args:
        device_address: MAC address of SFP Wizard
        name: User-provided name for module

    Returns:
        Module ID, metadata, and parsed fields
    """
    logger.info("read_module_start", device=request.device_address, name=request.name)

    try:
        # Step 1: Connect and read EEPROM
        async with BLEOperationsService(request.device_address) as ble:
            eeprom_data = await ble.read_eeprom()

        # Step 2: Parse SFF-8472 data
        parsed = parse_sfp_data(eeprom_data)
        logger.info("module_parsed", vendor=parsed.get("vendor"), model=parsed.get("model"))

        # Step 3: Calculate SHA256 hash
        sha256 = hashlib.sha256(eeprom_data).hexdigest()

        # Step 4: Save to database
        async for db in get_db():
            repo = ModuleRepository(db)

            # Check for duplicates
            existing = await repo.get_by_sha256(sha256)
            if existing:
                logger.warning("duplicate_module_detected", existing_id=existing.id, sha256=sha256[:16])
                raise HTTPException(
                    status_code=409,
                    detail=f"Module already exists in library (ID: {existing.id}). "
                    f"This exact EEPROM data was previously saved."
                )

            # Create module
            module = await repo.create(
                name=request.name,
                vendor=parsed["vendor"],
                model=parsed["model"],
                serial=parsed["serial"],
                eeprom_data=base64.b64encode(eeprom_data).decode("utf-8"),
                sha256=sha256,
            )

            logger.info("module_saved", module_id=module.id, name=module.name)

            return {
                "id": module.id,
                "name": module.name,
                "vendor": module.vendor,
                "model": module.model,
                "serial": module.serial,
                "sha256": module.sha256,
                "created_at": module.created_at.isoformat() if module.created_at else None,
            }

    except HTTPException:
        raise
    except ConnectionError as e:
        logger.error("read_connection_failed", device=request.device_address, error=str(e))
        raise HTTPException(status_code=503, detail=f"Connection failed: {str(e)}")
    except TimeoutError as e:
        logger.error("read_timeout", device=request.device_address, error=str(e))
        raise HTTPException(status_code=504, detail=f"Operation timed out: {str(e)}")
    except Exception as e:
        logger.error("read_operation_failed", device=request.device_address, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Read failed: {str(e)}")


@router.post("/write")
async def write_module(request: WriteRequest) -> dict[str, Any]:
    """
    Write EEPROM to SFP module via SFP Wizard.

    Full write flow:
    1. Retrieve module data from database
    2. Connect to device via Bluetooth
    3. Send POST /sif/write command
    4. Send EEPROM data in 20-byte chunks
    5. Wait for write complete
    6. If verify=True, read back and compare byte-by-byte
    7. Return status and verification result

    Args:
        device_address: MAC address of SFP Wizard
        module_id: ID of module to write
        verify: Whether to read back and verify after write (RECOMMENDED)

    Returns:
        Write success status, verification result, and any differences
    """
    logger.info(
        "write_module_start",
        module_id=request.module_id,
        device=request.device_address,
        verify=request.verify,
    )

    try:
        # Step 1: Get module from database
        async for db in get_db():
            repo = ModuleRepository(db)
            module = await repo.get_by_id(request.module_id)

            if not module:
                raise HTTPException(
                    status_code=404, detail=f"Module {request.module_id} not found"
                )

            # Decode EEPROM data
            eeprom_data = base64.b64decode(module.eeprom_data)

            if len(eeprom_data) != 256:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid EEPROM data length: {len(eeprom_data)} bytes "
                    "(expected 256)",
                )

            logger.info(
                "write_module_details",
                vendor=module.vendor,
                model=module.model,
                serial=module.serial,
            )

            # Step 2: Connect and write
            async with BLEOperationsService(request.device_address) as ble:
                # Write with built-in verification if requested
                success = await ble.write_eeprom(eeprom_data, verify=request.verify)

            result = {
                "success": success,
                "module_id": module.id,
                "module_name": module.name,
                "vendor": module.vendor,
                "model": module.model,
                "serial": module.serial,
                "verified": request.verify,
            }

            if request.verify:
                result["verification_status"] = "passed"
                logger.info("write_verified", module_id=module.id)
            else:
                result["verification_status"] = "skipped"
                logger.warning(
                    "write_unverified",
                    module_id=module.id,
                    message="Write completed without verification",
                )

            return result

    except HTTPException:
        raise
    except ConnectionError as e:
        logger.error("write_connection_failed", device=request.device_address, error=str(e))
        raise HTTPException(status_code=503, detail=f"Connection failed: {str(e)}")
    except TimeoutError as e:
        logger.error("write_timeout", device=request.device_address, error=str(e))
        raise HTTPException(status_code=504, detail=f"Operation timed out: {str(e)}")
    except RuntimeError as e:
        # Verification failure
        logger.error("write_verification_failed", device=request.device_address, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Write verification failed: {str(e)}. "
            "Module may be corrupted! Do NOT use this module.",
        )
    except Exception as e:
        logger.error("write_operation_failed", device=request.device_address, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Write failed: {str(e)}")
