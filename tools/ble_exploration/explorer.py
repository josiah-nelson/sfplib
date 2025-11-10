"""
BLE Explorer - Protocol exploration tools for SFP Wizard.

This module provides tools for reverse engineering the BLE protocol
used by the SFP Wizard device.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, List, Dict

from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic

logger = logging.getLogger(__name__)


class BLEExplorer:
    """BLE exploration and protocol analysis tool."""

    def __init__(self, device_address: str, log_file: str):
        """
        Initialize BLE explorer.

        Args:
            device_address: MAC address of target device
            log_file: Path to JSONL log file for results
        """
        self.device_address = device_address
        self.log_file = Path(log_file)
        self.log_handle = open(self.log_file, 'a')
        self._client: BleakClient | None = None

    def _log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Log an event to the JSONL file."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "device": self.device_address,
            "data": data
        }
        self.log_handle.write(json.dumps(entry) + "\n")
        self.log_handle.flush()

    async def connect(self, timeout: float = 30.0) -> None:
        """Connect to the BLE device."""
        logger.info(f"Connecting to {self.device_address}...")
        self._client = BleakClient(self.device_address, timeout=timeout)
        await self._client.connect()
        self._log_event("connected", {"success": True})
        logger.info("Connected successfully")

    async def disconnect(self) -> None:
        """Disconnect from the BLE device."""
        if self._client and self._client.is_connected:
            await self._client.disconnect()
            self._log_event("disconnected", {})
            logger.info("Disconnected")

    async def discover_services(self) -> List[Dict[str, Any]]:
        """
        Discover all GATT services and characteristics.

        Returns:
            List of service dictionaries with characteristics
        """
        if not self._client or not self._client.is_connected:
            await self.connect()

        logger.info("Discovering services...")
        services = []

        for service in self._client.services:
            service_data = {
                "uuid": service.uuid,
                "description": service.description,
                "characteristics": []
            }

            for char in service.characteristics:
                char_data = {
                    "uuid": char.uuid,
                    "description": char.description,
                    "properties": char.properties,
                    "handle": char.handle
                }
                service_data["characteristics"].append(char_data)

                # Log each characteristic
                self._log_event("characteristic_discovered", char_data)

            services.append(service_data)
            self._log_event("service_discovered", service_data)

        logger.info(f"Discovered {len(services)} services")
        return services

    async def test_write_patterns(self, patterns: List[Dict[str, Any]]) -> None:
        """
        Test multiple write patterns to discover protocol commands.

        Args:
            patterns: List of test patterns to try
        """
        if not self._client or not self._client.is_connected:
            await self.connect()

        logger.info(f"Testing {len(patterns)} write patterns...")

        for i, pattern in enumerate(patterns):
            try:
                # Find writable characteristic
                write_char = None
                for service in self._client.services:
                    for char in service.characteristics:
                        if "write" in char.properties:
                            write_char = char
                            break
                    if write_char:
                        break

                if not write_char:
                    self._log_event("write_test", {
                        "pattern_index": i,
                        "pattern": pattern,
                        "success": False,
                        "error": "No writable characteristic found"
                    })
                    continue

                # Write pattern
                data = pattern.get("data", b"")
                await self._client.write_gatt_char(write_char, data)

                # Wait for response
                await asyncio.sleep(0.1)

                self._log_event("write_test", {
                    "pattern_index": i,
                    "pattern": pattern,
                    "success": True,
                    "characteristic": write_char.uuid
                })

            except Exception as e:
                self._log_event("write_test", {
                    "pattern_index": i,
                    "pattern": pattern,
                    "success": False,
                    "error": str(e)
                })

            # Rate limiting
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{len(patterns)}")
                await asyncio.sleep(0.5)

        logger.info("Write pattern testing complete")

    async def monitor_notifications(self, duration: int = 60) -> List[Dict[str, Any]]:
        """
        Monitor BLE notifications for a specified duration.

        Args:
            duration: Monitoring duration in seconds

        Returns:
            List of captured notifications
        """
        if not self._client or not self._client.is_connected:
            await self.connect()

        logger.info(f"Monitoring notifications for {duration}s...")
        notifications = []

        def notification_handler(sender: BleakGATTCharacteristic, data: bytearray) -> None:
            """Handle incoming notifications."""
            notification = {
                "timestamp": datetime.utcnow().isoformat(),
                "characteristic": str(sender.uuid),
                "data_hex": data.hex(),
                "data_ascii": data.decode('utf-8', errors='replace'),
                "length": len(data)
            }
            notifications.append(notification)
            self._log_event("notification_received", notification)

        # Start notifications on all notify-capable characteristics
        notify_chars = []
        for service in self._client.services:
            for char in service.characteristics:
                if "notify" in char.properties:
                    await self._client.start_notify(char, notification_handler)
                    notify_chars.append(char)
                    logger.info(f"Started notifications on {char.uuid}")

        # Monitor for specified duration
        await asyncio.sleep(duration)

        # Stop notifications
        for char in notify_chars:
            await self._client.stop_notify(char)

        self._log_event("monitoring_complete", {
            "duration": duration,
            "notification_count": len(notifications),
            "notifications": notifications
        })

        logger.info(f"Captured {len(notifications)} notifications")
        return notifications

    def close(self) -> None:
        """Close the log file handle."""
        if self.log_handle:
            self.log_handle.close()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
        self.close()
