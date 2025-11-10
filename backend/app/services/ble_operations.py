"""
BLE Operations Service for SFP Wizard

Handles direct BLE communication with SFP Wizard device using bleak.
Based on discovered protocol:
- Service: 8E60F02E-F699-4865-B83F-F40501752184
- Write Char: 9280F26C-A56F-43EA-B769-D5D732E1AC67
- Notify Char: DC272A22-43F2-416B-8FA5-63A071542FAC

Protocol: HTTP-like commands over BLE notifications
- Commands sent to write characteristic
- Responses received via notify characteristic
- Binary data chunked in 20-byte packets
"""

import asyncio
import structlog
from typing import Optional
from bleak import BleakClient

logger = structlog.get_logger(__name__)


class BLEOperationsService:
    """Service for BLE operations with SFP Wizard."""

    # Known UUIDs for firmware v1.0.10
    SERVICE_UUID = "8E60F02E-F699-4865-B83F-F40501752184"
    WRITE_CHAR_UUID = "9280F26C-A56F-43EA-B769-D5D732E1AC67"
    NOTIFY_CHAR_UUID = "DC272A22-43F2-416B-8FA5-63A071542FAC"

    def __init__(self, device_address: str):
        """
        Initialize BLE operations service.

        Args:
            device_address: MAC address of SFP Wizard device
        """
        self.device_address = device_address
        self._client: Optional[BleakClient] = None
        self._notification_queue: asyncio.Queue = asyncio.Queue()
        self._response_buffer = bytearray()

    async def connect(self, timeout: float = 30.0) -> None:
        """
        Connect to SFP Wizard device.

        Args:
            timeout: Connection timeout in seconds

        Raises:
            TimeoutError: If connection times out
            ConnectionError: If connection fails
        """
        logger.info("ble_connecting", device=self.device_address)

        try:
            self._client = BleakClient(self.device_address, timeout=timeout)
            await self._client.connect()

            # Start notification handler
            await self._client.start_notify(
                self.NOTIFY_CHAR_UUID, self._notification_callback
            )

            logger.info("ble_connected", device=self.device_address)

        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Connection to {self.device_address} timed out after {timeout}s"
            )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {self.device_address}: {e}")

    async def disconnect(self) -> None:
        """Disconnect from device and cleanup."""
        if self._client and self._client.is_connected:
            try:
                await self._client.stop_notify(self.NOTIFY_CHAR_UUID)
                await self._client.disconnect()
                logger.info("ble_disconnected", device=self.device_address)
            except Exception as e:
                logger.error("ble_disconnect_error", device=self.device_address, error=str(e))
        self._client = None

    def _notification_callback(self, sender: int, data: bytearray) -> None:
        """
        Handle incoming BLE notifications.

        Args:
            sender: Characteristic handle
            data: Notification payload
        """
        self._notification_queue.put_nowait(bytes(data))

    async def _send_command(self, command: str) -> None:
        """
        Send HTTP-like command to device.

        Args:
            command: Command string (e.g., "GET /stats")

        Raises:
            ConnectionError: If not connected
        """
        if not self._client or not self._client.is_connected:
            raise ConnectionError("Not connected to device")

        logger.debug("ble_sending_command", command=command)
        await self._client.write_gatt_char(
            self.WRITE_CHAR_UUID, command.encode("utf-8")
        )

    async def _read_response(self, timeout: float = 10.0) -> bytes:
        """
        Read response from notification queue.

        Args:
            timeout: Response timeout in seconds

        Returns:
            Complete response data

        Raises:
            TimeoutError: If no response within timeout
        """
        self._response_buffer.clear()
        end_time = asyncio.get_event_loop().time() + timeout

        while True:
            remaining = end_time - asyncio.get_event_loop().time()
            if remaining <= 0:
                while True:
                    try:
                        self._notification_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break
                raise TimeoutError(f"Response timeout after {timeout}s")

            try:
                data = await asyncio.wait_for(
                    self._notification_queue.get(), timeout=remaining
                )
                self._response_buffer.extend(data)

                # Check for response terminator (implementation specific)
                # For now, assume single notification contains full response
                # TODO: Implement proper response parsing based on protocol
                return bytes(self._response_buffer)

            except asyncio.TimeoutError:
                if self._response_buffer:
                    # Got partial data, return it
                    return bytes(self._response_buffer)
                # Clear queue to prevent memory leaks
                while not self._notification_queue.empty():
                    try:
                        self._notification_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break
                raise TimeoutError(f"Response timeout after {timeout}s")

    async def read_eeprom(self) -> bytes:
        """
        Read SFP module EEPROM data.

        Returns:
            Raw EEPROM data (256 bytes)

        Raises:
            ConnectionError: If not connected
            TimeoutError: If operation times out
            RuntimeError: If read fails
        """
        logger.info("ble_reading_eeprom")

        try:
            # Send start command
            await self._send_command("POST /sif/start")

            # Read response data
            # TODO: Implement proper chunked reading based on protocol exploration
            data = await self._read_response(timeout=30.0)

            if len(data) != 256:
                raise RuntimeError(
                    f"Incorrect EEPROM data length: got {len(data)} bytes, expected 256"
                )

            logger.info("ble_read_success", bytes=len(data))
            return data

        except Exception as e:
            logger.error("ble_read_failed", error=str(e))
            raise

    async def write_eeprom(self, data: bytes, verify: bool = True) -> bool:
        """
        Write SFP module EEPROM data.

        Args:
            data: EEPROM data to write (256 bytes)
            verify: If True, read back and verify after write

        Returns:
            True if write successful (and verified if requested)

        Raises:
            ValueError: If data length invalid
            ConnectionError: If not connected
            TimeoutError: If operation times out
            RuntimeError: If write fails
        """
        if len(data) != 256:
            raise ValueError(f"EEPROM data must be 256 bytes, got {len(data)}")

        logger.info("ble_writing_eeprom", verify=verify)

        try:
            # Send write command
            await self._send_command("POST /sif/write")

            # TODO: Implement chunked writing (20-byte packets)
            # Based on BLE MTU, data must be sent in small chunks
            # FIXME: The sleep delay is currently fixed at 50ms but may need to be
            # configurable or adaptive based on device response. Ideally, implement
            # an acknowledgment mechanism if the device supports it.

            chunk_size = 20
            for i in range(0, len(data), chunk_size):
                chunk = data[i : i + chunk_size]
                await self._client.write_gatt_char(self.WRITE_CHAR_UUID, chunk)
                await asyncio.sleep(0.05)  # 50ms delay between chunks

            # Wait for write complete notification
            response = await self._read_response(timeout=60.0)
            logger.debug("ble_write_response", response=response)

            # Verify if requested
            if verify:
                logger.info("ble_verifying_write")
                readback = await self.read_eeprom()

                if readback != data:
                    # Find differences
                    diffs = sum(1 for a, b in zip(data, readback) if a != b)
                    raise RuntimeError(
                        f"Verification failed: {diffs} bytes differ. "
                        "Module may be corrupted!"
                    )

                logger.info("ble_write_verified")

            return True

        except Exception as e:
            logger.error("ble_write_failed", error=str(e))
            raise

    async def erase_eeprom(self) -> None:
        """
        Erase SFP module EEPROM.

        FIXME: This method is not currently exposed via API endpoints.
        Consider adding endpoint or removing if not needed.

        Raises:
            ConnectionError: If not connected
            TimeoutError: If operation times out
            RuntimeError: If erase fails
        """
        logger.info("ble_erasing_eeprom")

        try:
            await self._send_command("POST /sif/erase")
            response = await self._read_response(timeout=30.0)
            logger.debug("ble_erase_response", response=response)
            logger.info("ble_erase_success")

        except Exception as e:
            logger.error("ble_erase_failed", error=str(e))
            raise

    async def get_status(self) -> dict:
        """
        Get device status (battery, SFP presence, etc.).

        FIXME: This method is not currently exposed via API endpoints.
        Protocol parsing needs implementation. Consider adding endpoint or removing if not needed.

        Returns:
            Status dictionary

        Raises:
            ConnectionError: If not connected
            TimeoutError: If operation times out
        """
        try:
            await self._send_command("GET /stats")
            response = await self._read_response(timeout=5.0)

            # TODO: Parse response based on protocol
            # For now, return raw response
            return {"raw": response.decode("utf-8", errors="ignore")}

        except Exception as e:
            logger.error("ble_get_status_failed", error=str(e))
            raise

    async def get_version(self) -> str:
        """
        Get firmware version.

        FIXME: This method is not currently exposed via API endpoints.
        Consider adding endpoint or removing if not needed.

        Returns:
            Firmware version string

        Raises:
            ConnectionError: If not connected
            TimeoutError: If operation times out
        """
        try:
            await self._send_command("GET /api/1.0/version")
            response = await self._read_response(timeout=5.0)
            version = response.decode("utf-8", errors="ignore").strip()
            logger.info("ble_firmware_version", version=version)
            return version

        except Exception as e:
            logger.error("ble_get_version_failed", error=str(e))
            raise

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
