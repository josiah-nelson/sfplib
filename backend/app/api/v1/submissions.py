"""API endpoints for community submissions."""

import asyncio
import base64
import hashlib
import json
import os
import uuid
from datetime import datetime

import structlog
from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.schemas.submission import SubmissionCreate, SubmissionResponse

router = APIRouter()
logger = structlog.get_logger()
settings = get_settings()


@router.post("/submissions", response_model=SubmissionResponse)
async def submit_to_community(payload: SubmissionCreate) -> SubmissionResponse:
    """
    Accept a community submission without GitHub sign-in.

    Submissions are stored in an inbox for maintainers to review and publish.
    
    Note: Uses asyncio.to_thread for file I/O to avoid blocking the event loop.
    """
    try:
        eeprom = base64.b64decode(payload.eeprom_data_base64)
    except Exception as e:
        logger.warning("invalid_submission_base64", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid Base64 data") from e

    sha = hashlib.sha256(eeprom).hexdigest()
    inbox_root = settings.submissions_dir
    
    # Run blocking I/O operations in thread pool
    await asyncio.to_thread(os.makedirs, inbox_root, exist_ok=True)

    inbox_id = str(uuid.uuid4())
    target_dir = os.path.join(inbox_root, inbox_id)
    await asyncio.to_thread(os.makedirs, target_dir, exist_ok=True)

    # Write EEPROM binary
    eeprom_path = os.path.join(target_dir, "eeprom.bin")
    await asyncio.to_thread(_write_binary_file, eeprom_path, eeprom)

    # Write metadata JSON
    metadata = {
        "name": payload.name,
        "vendor": payload.vendor,
        "model": payload.model,
        "serial": payload.serial,
        "sha256": sha,
        "notes": payload.notes,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    metadata_path = os.path.join(target_dir, "metadata.json")
    await asyncio.to_thread(_write_json_file, metadata_path, metadata)

    logger.info("submission_queued", inbox_id=inbox_id, sha256=sha[:16] + "...")

    return SubmissionResponse(
        status="queued",
        message="Submission stored for review.",
        inbox_id=inbox_id,
        sha256=sha,
    )


def _write_binary_file(path: str, data: bytes) -> None:
    """Helper to write binary file (runs in thread pool)."""
    with open(path, "wb") as f:
        f.write(data)


def _write_json_file(path: str, data: dict) -> None:
    """Helper to write JSON file (runs in thread pool)."""
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
