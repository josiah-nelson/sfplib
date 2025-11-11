"""Home Assistant Bluetooth API client for SFPLiberate add-on."""

import asyncio
import json
import os
import structlog
from typing import Any

import aiohttp

from .ble_tracer import get_tracer
from .schemas import HABluetoothDevice, HADeviceConnectionResponse

logger = structlog.get_logger(__name__)


class HomeAssistantBluetoothClient:
    """
    Client for interacting with Home Assistant's Bluetooth integration.

    Replaces mDNS-based ESPHome discovery with direct HA API access.
    This client is only used when running as a Home Assistant add-on.
    """

    def __init__(
        self,
        ha_api_url: str | None = None,
        ha_ws_url: str | None = None,
        supervisor_token: str | None = None,
        device_patterns: list[str] | None = None,
    ):
        """
        Initialize HA Bluetooth client.

        Args:
            ha_api_url: Home Assistant REST API URL (defaults to supervisor proxy)
            ha_ws_url: Home Assistant WebSocket URL (defaults to supervisor proxy)
            supervisor_token: Supervisor token for authentication
            device_patterns: List of device name patterns to filter (case-insensitive)
        """
        self.ha_api_url = ha_api_url or os.getenv("HA_API_URL", "http://supervisor/core/api")
        self.ha_ws_url = ha_ws_url or os.getenv("HA_WS_URL", "ws://supervisor/core/websocket")
        self.supervisor_token = supervisor_token or os.getenv("SUPERVISOR_TOKEN", "")

        # Parse device patterns from env if provided as JSON array
        patterns_env = os.getenv("DEVICE_NAME_PATTERNS", '["SFP", "Wizard"]')
        try:
            default_patterns = json.loads(patterns_env)
        except (json.JSONDecodeError, TypeError):
            default_patterns = ["SFP", "Wizard"]

        self.device_patterns = [p.lower() for p in (device_patterns or default_patterns)]

        self._session: aiohttp.ClientSession | None = None
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._discovered_devices: dict[str, HABluetoothDevice] = {}
        self._ws_task: asyncio.Task | None = None
        self._connected = False

        token_len = len(self.supervisor_token or "")
        logger.info(
            "ha_bluetooth_client_initialized",
            api_url=self.ha_api_url,
            patterns=self.device_patterns,
            token_present=bool(self.supervisor_token),
            token_length=token_len,
        )

        # Log session info to tracer
        tracer = get_tracer()
        tracer.log_session_info({
            "mode": "Home Assistant Add-on",
            "api_url": self.ha_api_url,
            "ws_url": self.ha_ws_url,
            "device_patterns": self.device_patterns,
        })

    async def start(self) -> None:
        """Initialize connection to HA API and start listening for device updates."""
        if self._session:
            logger.warning("ha_bluetooth_client_already_started")
            return

        logger.info("ha_bluetooth_client_starting")

        # Create session with auth header
        headers = {"Authorization": f"Bearer {self.supervisor_token}"}
        self._session = aiohttp.ClientSession(headers=headers)

        # Initial device discovery
        await self._discover_devices()

        # Start WebSocket listener for real-time updates
        self._ws_task = asyncio.create_task(self._websocket_listener())

        self._connected = True
        logger.info("ha_bluetooth_client_started")

    async def stop(self) -> None:
        """Cleanup connections and resources."""
        logger.info("ha_bluetooth_client_stopping")

        # Cancel WebSocket listener
        if self._ws_task:
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass

        # Close WebSocket
        if self._ws:
            await self._ws.close()
            self._ws = None

        # Close session
        if self._session:
            await self._session.close()
            self._session = None

        self._connected = False
        logger.info("ha_bluetooth_client_stopped")

    async def get_bluetooth_devices(self) -> list[HABluetoothDevice]:
        """
        Get all Bluetooth devices from HA that match configured patterns.

        Returns:
            List of discovered devices matching configured patterns
        """
        # Return cached devices populated at startup and refreshed via the
        # WebSocket listener. This avoids hitting the HA API on every request.
        return list(self._discovered_devices.values())

    async def connect_to_device(self, mac_address: str) -> HADeviceConnectionResponse:
        """
        Connect to device via HA Bluetooth and retrieve GATT UUIDs.

        For SFP Wizard devices, we return the known UUIDs from firmware v1.0.10.
        For other devices, we attempt to use HA's Bluetooth integration to
        discover services via the REST API.

        Args:
            mac_address: BLE MAC address

        Returns:
            DeviceConnectionResponse with service/characteristic UUIDs

        Raises:
            ValueError: If device not found
            RuntimeError: If connection fails
        """
        logger.info("ha_bluetooth_connecting", mac=mac_address)

        # Normalize MAC
        mac_address = mac_address.upper().replace("-", ":")

        # Check if device is discovered
        device = self._discovered_devices.get(mac_address)
        if not device:
            raise ValueError(
                f"Device {mac_address} not found. "
                "Make sure the device is advertising and matches configured patterns."
            )

        # Check if this is an SFP Wizard device (matches our patterns)
        is_sfp_wizard = any(
            pattern.lower() in device.name.lower()
            for pattern in ["sfp", "wizard"]
        )

        if is_sfp_wizard:
            # Return known UUIDs for SFP Wizard firmware v1.0.10
            logger.info("ha_bluetooth_sfp_wizard_detected", device_name=device.name)

            # Known UUIDs from firmware v1.0.10
            service_uuid = "8E60F02E-F699-4865-B83F-F40501752184"
            write_char_uuid = "9280F26C-A56F-43EA-B769-D5D732E1AC67"
            notify_char_uuid = "DC272A22-43F2-416B-8FA5-63A071542FAC"

            tracer = get_tracer()
            tracer.log_connection_established(
                mac=mac_address,
                name=device.name,
                service_uuid=service_uuid,
                write_uuid=write_char_uuid,
                notify_uuid=notify_char_uuid,
            )

            return HADeviceConnectionResponse(
                mac=mac_address,
                name=device.name,
                service_uuid=service_uuid,
                write_char_uuid=write_char_uuid,
                notify_char_uuid=notify_char_uuid,
            )
        else:
            # For non-SFP Wizard devices, we cannot auto-detect UUIDs via HA API
            # HA's Bluetooth integration doesn't expose GATT service enumeration
            # Users would need to use Web Bluetooth or provide UUIDs manually
            raise RuntimeError(
                f"Device {device.name} is not recognized as an SFP Wizard. "
                "GATT service discovery is not available via Home Assistant's Bluetooth API. "
                "Please use Web Bluetooth to discover service UUIDs first."
            )

    @property
    def is_connected(self) -> bool:
        """Check if client is connected to HA API."""
        return self._connected

    async def _discover_devices(self) -> None:
        """
        Query HA for Bluetooth devices.

        Note: This currently looks for Bluetooth entities (device_tracker, etc.)
        which only exist for paired/integrated devices. Raw BLE advertisements
        visible in the Advertisement Monitor are not exposed via this API.

        For now, users should manually add their SFP Wizard device using the
        Bluetooth integration before using this addon.
        """
        if not self._session:
            logger.warning("ha_bluetooth_discover_no_session")
            return

        tracer = get_tracer()
        tracer.log_device_scan_start(
            patterns=self.device_patterns,
            filters={"source": "Home Assistant API"}
        )

        try:
            async with self._session.get(f"{self.ha_api_url}/states") as resp:
                if resp.status != 200:
                    logger.error("ha_bluetooth_states_fetch_failed", status=resp.status)
                    return

                states = await resp.json()

            # Process states to find Bluetooth devices
            discovered = {}
            for state in states:
                entity_id = state.get("entity_id", "")
                attrs = state.get("attributes", {})

                # Look for bluetooth-related entities
                # This includes device_tracker from bluetooth, sensor entities, etc.
                if not self._is_bluetooth_entity(entity_id, attrs):
                    continue

                name = attrs.get("friendly_name", "")

                # Pattern matching (case-insensitive) OR match by service UUID if present
                service_uuids = attrs.get("service_uuids", [])
                sfp_service_uuid = "8e60f02e-f699-4865-b83f-f40501752184"

                matches_pattern = any(pattern in name.lower() for pattern in self.device_patterns)
                matches_uuid = sfp_service_uuid.lower() in [str(u).lower() for u in service_uuids]

                if not (matches_pattern or matches_uuid):
                    continue

                # Extract MAC from various attribute locations
                mac = self._extract_mac(attrs, entity_id)
                if not mac:
                    continue

                # Create device object
                device = HABluetoothDevice(
                    mac=mac,
                    name=name or mac,  # Fallback to MAC if no name
                    rssi=attrs.get("rssi", -100),
                    source=attrs.get("source", "hass_bluetooth"),
                    last_seen=state.get("last_changed"),
                )
                discovered[mac] = device

                # Log discovery to tracer
                tracer.log_device_discovered(
                    mac=mac,
                    name=name or mac,
                    rssi=attrs.get("rssi", -100),
                    advertisement_data={
                        "entity_id": entity_id,
                        "source": attrs.get("source", "hass_bluetooth"),
                        "last_seen": state.get("last_changed"),
                        "service_uuids": service_uuids,
                        "attributes": attrs,
                    }
                )

            # Update cache
            self._discovered_devices = discovered
            logger.info("ha_bluetooth_devices_discovered", count=len(discovered))

            if len(discovered) == 0:
                logger.warning(
                    "no_bluetooth_devices_found",
                    message="No Bluetooth devices found. Raw BLE advertisements are not "
                    "accessible via HA API. Please add your SFP Wizard device manually in "
                    "Settings → Devices & Services → Bluetooth → Add Device, then use its MAC "
                    f"address: {self.device_patterns}"
                )

        except Exception as e:
            logger.error("ha_bluetooth_discovery_error", error=str(e), exc_info=True)
            tracer.log_error("Device Discovery", str(e))

    def _is_bluetooth_entity(self, entity_id: str, attrs: dict[str, Any]) -> bool:
        """Check if entity is Bluetooth-related."""
        # Check entity domain
        if entity_id.startswith(("device_tracker.", "sensor.")):
            # Check for bluetooth source attribute
            source = attrs.get("source", "")
            if "bluetooth" in source.lower() or "ble" in source.lower():
                return True

        # Check for bluetooth in entity ID
        if "bluetooth" in entity_id or "ble" in entity_id:
            return True

        return False

    def _extract_mac(self, attrs: dict[str, Any], entity_id: str) -> str | None:
        """Extract MAC address from entity attributes."""
        # Try common attribute names
        for key in ["address", "mac", "mac_address", "id"]:
            mac = attrs.get(key)
            if mac and ":" in str(mac):
                return str(mac).upper()

        # Try to extract from entity ID (some integrations use MAC in entity ID)
        # e.g., device_tracker.aa_bb_cc_dd_ee_ff
        parts = entity_id.split(".")
        if len(parts) == 2:
            potential_mac = parts[1].replace("_", ":")
            if potential_mac.count(":") == 5:  # Valid MAC format
                return potential_mac.upper()

        return None

    async def _websocket_listener(self) -> None:
        """Listen for Bluetooth device updates via WebSocket with auto-reconnection."""
        logger.info("ha_bluetooth_websocket_starting")
        
        retry_count = 0
        max_retries = 5
        base_delay = 1.0
        
        while retry_count < max_retries:
            try:
                # Connect to WebSocket
                self._ws = await self._session.ws_connect(self.ha_ws_url)

                # HA WS auth handshake: server sends auth_required first, then client sends auth
                # Be tolerant to message ordering and read until auth_ok or auth_invalid
                auth_ok = False
                # Read up to 3 initial messages to complete handshake
                for _ in range(3):
                    msg = await self._ws.receive_json()
                    mtype = msg.get("type")
                    if mtype == "auth_required":
                        # Send credentials
                        await self._ws.send_json({
                            "type": "auth",
                            "access_token": self.supervisor_token,
                        })
                        continue
                    if mtype == "auth_ok":
                        auth_ok = True
                        break
                    if mtype == "auth_invalid":
                        logger.error("ha_bluetooth_websocket_auth_failed", response=msg)
                        return
                    # Unknown pre-auth message; continue loop
                if not auth_ok:
                    logger.error("ha_bluetooth_websocket_auth_failed", response={"type": "no_auth_ok"})
                    return

                logger.info("ha_bluetooth_websocket_authenticated")
                retry_count = 0  # Reset retry count on successful connection

                # Subscribe to state_changed events
                await self._ws.send_json({
                    "id": 1,
                    "type": "subscribe_events",
                    "event_type": "state_changed"
                })

                # Listen for messages
                async for msg in self._ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        try:
                            data = json.loads(msg.data)
                            await self._handle_ws_message(data)
                        except Exception as e:
                            logger.error("ha_bluetooth_websocket_message_error", error=str(e), exc_info=True)
                    elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                        logger.warning("ha_bluetooth_websocket_closed", msg_type=str(msg.type))
                        break

                # Connection closed, attempt reconnection
                retry_count += 1
                if retry_count < max_retries:
                    delay = base_delay * (2 ** retry_count)  # Exponential backoff
                    logger.info("ha_bluetooth_websocket_reconnecting", retry=retry_count, delay=delay)
                    await asyncio.sleep(delay)
                    
            except asyncio.CancelledError:
                logger.info("ha_bluetooth_websocket_cancelled")
                raise
            except Exception as e:
                logger.error("ha_bluetooth_websocket_error", error=str(e), exc_info=True)
                retry_count += 1
                if retry_count < max_retries:
                    delay = base_delay * (2 ** retry_count)
                    logger.info("ha_bluetooth_websocket_reconnecting", retry=retry_count, delay=delay)
                    await asyncio.sleep(delay)
                    
        logger.error("ha_bluetooth_websocket_max_retries_exceeded")

    async def _handle_ws_message(self, data: dict[str, Any]) -> None:
        """Process WebSocket message for Bluetooth device updates."""
        # Check for state_changed event
        if (
            data.get("type") == "event"
            and data.get("event", {}).get("event_type") == "state_changed"
        ):
            event_data = data.get("event", {}).get("data", {})
            entity_id = event_data.get("entity_id", "")
            new_state = event_data.get("new_state", {})
            attrs = new_state.get("attributes", {})

            # Only process bluetooth entities
            if not self._is_bluetooth_entity(entity_id, attrs):
                return

            name = attrs.get("friendly_name", "")

            # Pattern matching
            if not any(pattern in name.lower() for pattern in self.device_patterns):
                return

            # Extract MAC
            mac = self._extract_mac(attrs, entity_id)
            if not mac:
                return

            # Update cache
            device = HABluetoothDevice(
                mac=mac,
                name=name,
                rssi=attrs.get("rssi", -100),
                source=attrs.get("source", "hass_bluetooth"),
                last_seen=new_state.get("last_changed"),
            )
            self._discovered_devices[mac] = device

            # Log to tracer
            tracer = get_tracer()
            tracer.log_device_discovered(
                mac=mac,
                name=name,
                rssi=attrs.get("rssi", -100),
                advertisement_data={
                    "entity_id": entity_id,
                    "source": attrs.get("source", "hass_bluetooth"),
                    "last_seen": new_state.get("last_changed"),
                    "update_via": "websocket",
                }
            )

            logger.debug(f"Updated device via WebSocket: {name} ({mac})")
