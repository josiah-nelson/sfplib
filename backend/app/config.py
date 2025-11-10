"""Application configuration with environment variable support."""

import json
import os
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra env vars from Docker
    )

    # Database - default to persistent HA config path
    database_url: str = "sqlite+aiosqlite:////config/sfplib/sfp_library.db"
    database_echo: bool = False

    # API
    api_v1_prefix: str = "/api/v1"
    project_name: str = "SFPLiberate API"
    version: str = Field(default_factory=lambda: os.getenv("ADDON_VERSION", "0.1.0"))

    # CORS
    cors_origins: list[str] = ["*"]

    # Submissions - default to persistent HA config path
    submissions_dir: str = "/config/sfplib/submissions"

    # Logging
    log_level: str = "INFO"
    log_json: bool = True

    # Home Assistant Integration
    ha_api_url: str = "http://supervisor/core/api"
    ha_ws_url: str = "ws://supervisor/core/websocket"
    supervisor_token: str = Field(default_factory=lambda: os.getenv("SUPERVISOR_TOKEN", ""))
    device_name_patterns: list[str] = ["SFP", "Wizard"]
    auto_discover: bool = True
    connection_timeout: int = 30
    device_expiry_seconds: int = 300

    @field_validator('device_name_patterns', mode='before')
    @classmethod
    def parse_patterns(cls, v):
        """Parse device_name_patterns from JSON string if needed."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return ["SFP", "Wizard"]
        return v

    # SFP Wizard BLE Service UUIDs (firmware v1.0.10)
    sfp_service_uuid: str = "8E60F02E-F699-4865-B83F-F40501752184"
    sfp_write_char_uuid: str = "9280F26C-A56F-43EA-B769-D5D732E1AC67"
    sfp_notify_char_uuid: str = "DC272A22-43F2-416B-8FA5-63A071542FAC"

    # Bluetooth Configuration
    scan_interval: int = 5  # Bluetooth scan interval in seconds
    rssi_threshold: int = -80  # Minimum RSSI (dBm) to show devices
    max_devices: int = 50  # Maximum number of devices to track
    bluetooth_adapter: str = "default"  # Bluetooth adapter (default/hci0/hci1/etc)

    # Performance & Monitoring
    enable_metrics: bool = False  # Collect performance metrics
    enable_debug_ble: bool = False  # Verbose BLE debugging
    ble_trace_logging: bool = False  # Comprehensive BLE trace logging
    enable_debug_tools: bool = True  # Enable debug API endpoints

    # Database Backup
    database_backup_enabled: bool = True
    database_backup_interval: int = 24  # Backup interval in hours
    database_backup_max_count: int = 7  # Maximum number of backups to keep
    database_backup_path: str = "/config/sfplib/backups"  # Backup directory


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
