# SFPLiberate

**Home Assistant add-on for the Ubiquiti SFP Wizard.**

SFPLiberate is a companion application for the **Ubiquiti SFP Wizard (UACC-SFP-Wizard)**, enabling you to capture, store, and manage unlimited SFP/SFP+ module EEPROM profiles through Home Assistant.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Add--on-blue.svg)](https://www.home-assistant.io/)

---

## Quick Start

### Installation

1. **Add the repository to Home Assistant:**
   - Go to **Settings** → **Add-ons** → **Add-on Store** (⋮ menu) → **Repositories**
   - Add: `https://github.com/josiah-nelson/SFPLiberate`

2. **Install the add-on:**
   - Find "SFPLiberate" in the add-on store
   - Click **Install**

3. **Start the add-on:**
   - Click **Start**
   - Open the Web UI from the add-on page

That's it! The add-on stores data locally in Home Assistant's config directory with a SQLite database.

---

## What Problem Does This Solve?

The Ubiquiti SFP Wizard is a powerful standalone device, but has limitations:

- **Can only store ONE module profile at a time** for writing
- **No way to "copy" a module** unless you physically have one to read
- **No persistent library** of your SFP configurations

**SFPLiberate solves this** by providing:

✅ **Unlimited Storage** - Save as many module profiles as you want  
✅ **Clone Without Originals** - Write profiles you've saved previously  
✅ **Native Bluetooth** - Works with Home Assistant's Bluetooth integration  
✅ **Full Control** - Self-hosted, all data stays in your Home Assistant instance

---

## Architecture

### Frontend
- **Alpine.js** single-page application (lightweight, no build step)
- **Tailwind CSS** for styling (CDN-loaded)
- Served directly from FastAPI backend at `/ui`

### Backend
- **FastAPI** with Python 3.12
- **SQLAlchemy 2.0** with SQLite database
- **Home Assistant Bluetooth API** for native device communication
- **structlog** for structured logging
- **BLE exploration tools** for protocol reverse-engineering

### Deployment

**Home Assistant Add-On (Primary)** 🏠

[![Add to Home Assistant](https://my.home-assistant.io/badges/supervisor_addon.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fjosiah-nelson%2FSFPLiberate)

- ✅ **One-click installation** - No Docker knowledge required
- ✅ **Automatic Bluetooth discovery** - Leverages HA's native Bluetooth integration
- ✅ **Built-in backup** - Included in HA backups automatically
- ✅ **Web UI via Ingress** - No port conflicts or reverse proxy needed
- ✅ **Debug tools** - Integrated BLE protocol exploration for reverse-engineering

**Requirements:**
- Home Assistant OS or Supervised
- Bluetooth adapter (built-in or USB dongle)
- SFP Wizard firmware v1.0.10+

See [sfplib/README.md](sfplib/README.md) for complete add-on documentation.

---

## Browser Compatibility

The add-on's Web UI works in all modern browsers (Alpine.js-based, no special APIs required).

**Note:** Previous standalone Docker deployments using Web Bluetooth have been archived. HA add-on with native Bluetooth is now the only supported deployment method.

---

---

## Features

### Current Features ✅

- **Device Connection** - Connect to SFP Wizard via Home Assistant Bluetooth
- **Live Status** - Real-time BLE connection and module presence detection
- **EEPROM Capture** - Read full module EEPROM (256+ bytes)
- **SFP Parsing** - Extract vendor, model, serial from SFF-8472 spec
- **Module Library** - Save, view, delete modules in local database
- **Duplicate Detection** - SHA-256 checksum prevents duplicate saves
- **Write Support** - Write saved profiles back to blank modules (experimental)
- **Debug Tools** - Integrated BLE exploration suite for protocol reverse-engineering
- **Automatic Backups** - Database backups included in Home Assistant snapshots

### Coming Soon 🚧

- **Write Verification** - Automatic read-back and comparison after writes
- **Export/Import** - ZIP backup/restore for module library
- **Module Notes/Tags** - Organize modules with custom metadata
- **Module Comparison** - Side-by-side hex diff view
- **Community Repository** - Share and download profiles (if demand exists)

---

## API Endpoints

### Module Management

```
GET    /api/v1/modules              List all modules
POST   /api/v1/modules              Save new module
GET    /api/v1/modules/{id}         Get module details
GET    /api/v1/modules/{id}/eeprom  Get raw EEPROM binary
DELETE /api/v1/modules/{id}         Delete module
```

### Bluetooth Operations (HA Add-on)

```
GET    /api/v1/bluetooth/discover   Discover SFP Wizard devices
POST   /api/v1/bluetooth/read       Read EEPROM from device
POST   /api/v1/bluetooth/write      Write EEPROM to device
```

### Debug Tools (HA Add-on)

```
POST   /api/v1/debug/discover-services      Enumerate BLE characteristics
POST   /api/v1/debug/test-writes            Test command patterns
POST   /api/v1/debug/monitor-notifications  Capture 60s of BLE notifications
GET    /api/v1/debug/export-logs            Download JSONL exploration logs
```

API documentation available at `/api/docs` when running.

---

## Configuration

### Add-on Configuration

Configure via Home Assistant UI (Settings → Add-ons → SFPLiberate → Configuration):

```yaml
log_level: info                      # debug, info, warning, error
auto_discover: true                  # Auto-discover SFP Wizard devices
device_name_patterns:                # BLE device name filters
  - "SFP"
  - "Wizard"
connection_timeout: 30               # BLE connection timeout (seconds)
bluetooth_adapter: "default"         # Bluetooth adapter to use
database_backup_enabled: true        # Auto-backup database
database_backup_interval: 24         # Backup interval (hours)
enable_debug_ble: false              # Enable debug tools tab
ble_trace_logging: false             # Log all BLE operations (verbose)
```

See [sfplib/README.md](sfplib/README.md) for complete configuration reference.

---

## Development

### Prerequisites

- **Home Assistant OS** or **Supervised** (for testing add-on)
- **Python** 3.12+ and **Poetry** 1.8+ (for backend development)
- **SFP Wizard** device (for hardware testing)

### Backend Development

```bash
cd backend
poetry install
poetry run pytest                    # Run tests
poetry run uvicorn app.main:app --reload
```

### Add-on Local Testing

```bash
# Build locally for testing
docker build -t sfplib-addon-amd64 \
  --build-arg BUILD_FROM=ghcr.io/home-assistant/amd64-base:3.22 \
  -f sfplib/Dockerfile .

# Or use HA CLI if installed
ha addons reload
ha addons logs sfplib
```

### BLE Protocol Exploration

The add-on includes integrated debug tools for reverse-engineering:

```bash
# Access via Web UI: "🔧 Debug Tools" tab
# 1. Discover Services → enumerates all BLE characteristics
# 2. Run Write Tests → tests 100+ command patterns
# 3. Start Monitoring → captures notifications during physical operations
# 4. Export Logs → downloads JSONL for LLM analysis
```

See [docs/BLE_EXPLORATION.md](docs/BLE_EXPLORATION.md) for complete guide.

---

## Documentation

Comprehensive documentation is available in `/docs`:

**Core Documentation:**
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Deployment guide for all modes
- [BLUETOOTH.md](docs/BLUETOOTH.md) - BLE connection guide

**Technical Documentation:**

---

## How It Works

### BLE Protocol

SFPLiberate uses the **Web Bluetooth API** to communicate with the SFP Wizard over BLE.

**Discovered Protocol (firmware v1.0.10):**

| Endpoint | Purpose |
|----------|---------|
| `GET /api/1.0/version` | Get firmware version |
| `GET /stats` | Get device status (battery, SFP presence) |
| `POST /sif/start` | Read SFP EEPROM |
| `POST /sif/write` | Write SFP EEPROM (binary data in chunks) |
| `POST /sif/erase` | Erase SFP EEPROM |
| `POST /sif/stop` | Stop current operation |

**BLE Characteristics:**

- **Service:** `8E60F02E-F699-4865-B83F-F40501752184`
- **Write:** `9280F26C-A56F-43EA-B769-D5D732E1AC67`
- **Notify:** `DC272A22-43F2-416B-8FA5-63A071542FAC`


### Data Flow

**Standalone Mode (Web Bluetooth):**
```
Browser ←--BLE--→ SFP Wizard
   ↕ HTTP
Next.js Server
   ↕ Proxy
FastAPI Backend
   ↕
SQLite Database
```

**ESPHome Proxy Mode:**
```
Browser ←--WebSocket--→ FastAPI Backend ←--ESPHome API--→ ESPHome Proxy ←--BLE--→ SFP Wizard
```

---

## Security & Privacy

- **Self-hosted by default** - All data stays on your machine

---

## Testing

### Backend Tests

```bash
cd backend
poetry run pytest                     # Run all tests
poetry run pytest --cov=app           # With coverage
poetry run pytest -v                  # Verbose output
```

### Frontend Tests

```bash
cd frontend
npm run test                          # Run all tests
npm run test:watch                    # Watch mode
```

---

## Troubleshooting

### "No device found"
- Ensure SFP Wizard is powered on and in range
- Check that Bluetooth is enabled on your device
- Try the "Scan (Open Chooser)" button for manual selection
- For iOS/Safari: Enable ESPHome proxy mode

### "Connection failed"
- Reset the SFP Wizard by power cycling
- Clear browser cache and reload
- Check browser console for error messages
- Verify UUIDs match your firmware version

### "ESPHome proxy not found"
- Check that ESPHome device is on same network
- Verify mDNS is enabled on your network
- Try manual configuration in .env (ESPHOME_PROXY_HOST)
- Check ESPHome logs: `docker-compose logs -f backend | grep esphome`

### Docker build fails
- Ensure Docker has enough resources (4GB+ RAM recommended)
- Clear Docker cache: `docker system prune -a`
- Check Docker logs: `docker-compose logs`

---

## Contributing

Contributions are highly encouraged!

**Priority areas:**
- Testing on different SFP modules
- Additional firmware version support
- UI/UX improvements
- Documentation improvements
- Bug reports and fixes

Please open an issue before submitting large PRs to discuss the approach.

---

## License

This project is licensed under the MIT License - see LICENSE file for details.

---

## Disclaimer

This project is an independent, community-driven effort and is **not affiliated with, endorsed by, or supported by Ubiquiti**. The SFP Wizard's firmware and BLE behavior may change at any time; this tool may stop working without notice if a firmware update alters the observed interfaces. Use at your own risk.

---

## Acknowledgments

- **Ubiquiti** for creating the SFP Wizard hardware
- **ESPHome** team for the excellent Bluetooth proxy implementation
- **shadcn/ui** for the beautiful component library
- **Contributors** who helped reverse-engineer the BLE protocol

---

**Built with ❤️ by the SFPLiberate community**
