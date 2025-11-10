"""
Debug API Endpoints

BLE exploration tools exposed via REST API for HA add-on UI.
These endpoints wrap the BLE exploration framework for easy web access.

⚠️ REMOVE THIS FILE before releasing to users! Debug tools only.

NOTE: Requires tools directory in PYTHONPATH. The tools directory is not
included in the add-on distribution and should be mounted separately for development.
Set PYTHONPATH=/path/to/tools in the environment before starting the backend.
"""

import asyncio
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any

# Import exploration tools (requires PYTHONPATH to include tools directory)
try:
    from ble_exploration.explorer import BLEExplorer
    from ble_exploration.test_patterns import get_test_patterns
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False
    BLEExplorer = None
    get_test_patterns = None

router = APIRouter(prefix="/debug", tags=["debug"])

# Log file path
REPORTS_DIR = Path(__file__).parents[4] / "tools" / "ble_exploration" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = REPORTS_DIR / "ha_debug.jsonl"


# ====================================================================
# Request/Response Models
# ====================================================================

class DiscoverServicesRequest(BaseModel):
    device_address: str


class TestWritesRequest(BaseModel):
    device_address: str


class MonitorNotificationsRequest(BaseModel):
    device_address: str
    duration: int = 60


# ====================================================================
# Endpoints
# ====================================================================

@router.post("/discover-services")
async def discover_services(request: DiscoverServicesRequest):
    """
    Enumerate all BLE services and characteristics on the device.

    Returns:
        Service and characteristic information
    """
    if not TOOLS_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="BLE exploration tools not available. Ensure tools directory is in PYTHONPATH."
        )
    
    try:
        explorer = BLEExplorer(request.device_address, str(LOG_FILE))
        try:
            await explorer.discover_services()
        finally:
            explorer.log_handle.close()

        # Parse log to extract service info
        import json
        services = []
        service_count = 0

        with open(LOG_FILE, 'r') as f:
            for line in f:
                entry = json.loads(line)

                if entry['event_type'] == 'service_discovered':
                    services.append(entry['data'])
                    service_count += 1

        return {
            "success": True,
            "service_count": service_count,
            "services": services
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-writes")
async def test_writes(request: TestWritesRequest):
    """
    Test 100+ write patterns to reverse engineer BLE protocol.

    This may take 2-3 minutes to complete.

    Returns:
        Summary of test results
    """
    try:
        patterns = get_test_patterns()

        explorer = BLEExplorer(request.device_address, str(LOG_FILE))
        try:
            await explorer.test_write_patterns(patterns)
        finally:
            explorer.log_handle.close()

        # Parse log to count successes/failures
        import json
        successful = 0
        failed = 0

        with open(LOG_FILE, 'r') as f:
            for line in f:
                entry = json.loads(line)

                if entry['event_type'] == 'write_test':
                    if entry['data'].get('success'):
                        successful += 1
                    else:
                        failed += 1

        return {
            "success": True,
            "total_patterns": len(patterns),
            "successful": successful,
            "failed": failed
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitor-notifications")
async def monitor_notifications(request: MonitorNotificationsRequest):
    """
    Monitor BLE notifications for specified duration.

    User should insert/remove SFP modules during monitoring.

    Returns:
        Captured notifications
    """
    try:
        explorer = BLEExplorer(request.device_address, str(LOG_FILE))
        try:
            await explorer.monitor_notifications(request.duration)
        finally:
            explorer.log_handle.close()

        # Parse log to extract notifications
        import json
        notifications = []

        with open(LOG_FILE, 'r') as f:
            for line in f:
                entry = json.loads(line)

                if entry['event_type'] == 'monitoring_complete':
                    notifications = entry['data']['notifications']
                    break

        return {
            "success": True,
            "notification_count": len(notifications),
            "notifications": notifications
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export-logs")
async def export_logs():
    """
    Download exploration logs as JSONL file for LLM analysis.

    Returns:
        File download of exploration logs
    """
    if not LOG_FILE.exists():
        raise HTTPException(status_code=404, detail="No logs available")

    return FileResponse(
        path=LOG_FILE,
        filename=f"ble-exploration-{LOG_FILE.stem}.jsonl",
        media_type="application/jsonl"
    )
