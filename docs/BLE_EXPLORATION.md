# BLE Protocol Exploration Guide

Complete guide to using the BLE exploration tools for systematically reverse engineering and validating the SFP Wizard BLE protocol.

---

## Overview

The BLE exploration suite helps you:
1. **Discover** services and characteristics
2. **Test** command patterns to understand protocol
3. **Monitor** notifications during physical operations
4. **Analyze** logs with LLM assistance (Claude)
5. **Validate** implementation with hardware tests

---

## Quick Start (Via Debug UI)

### Prerequisites
- HA add-on installed and running
- SFP Wizard device powered on
- Bluetooth connection working

### Basic Workflow

1. **Open Debug UI**
   - Go to HA → Add-ons → SFPLiberate → OPEN WEB UI
   - Click "🔧 Debug Tools" tab

2. **Select Device**
   - Choose SFP Wizard from dropdown
   - Device must be discovered first

3. **Run Exploration**
   ```
   Step 1: Discover Services
   → Enumerates all BLE characteristics
   → Validates UUIDs match expected firmware

   Step 2: Run Write Tests
   → Tests 100+ command patterns
   → Takes 2-3 minutes
   → Logs all responses

   Step 3: Start Monitoring
   → Captures notifications for 60s
   → ACTION REQUIRED: Insert/remove SFP module during this time
   → Logs all state changes

   Step 4: Download Logs
   → Downloads JSONL file
   → Feed to Claude for analysis
   ```

4. **Analyze Results**
   ```bash
   # Generate analysis prompt
   python -m backend.tools.ble_exploration.analyzer reports/ha_debug.jsonl

   # Send to Claude
   claude code < reports/ha_debug_analysis.txt
   ```

---

## Exploration Tools

### 1. Service Discovery (`backend/tools/ble_exploration/explorer.py`)

**Purpose:** Enumerate all BLE services and characteristics

**What it does:**
- Connects to device
- Lists all GATT services
- Enumerates characteristics per service
- Records properties (read, write, notify)
- Logs all descriptors

**Output:**
```jsonl
{"timestamp": "2025-01-10T10:00:00", "event_type": "service_discovered", "data": {
  "uuid": "8E60F02E-F699-4865-B83F-F40501752184",
  "description": "Unknown Service",
  "characteristics": [
    {
      "uuid": "9280F26C-A56F-43EA-B769-D5D732E1AC67",
      "properties": ["write", "write-without-response"],
      "descriptors": []
    },
    {
      "uuid": "DC272A22-43F2-416B-8FA5-63A071542FAC",
      "properties": ["notify", "read"],
      "descriptors": ["00002902-0000-1000-8000-00805f9b34fb"]
    }
  ]
}}
```

**Use case:**
- Verify firmware version has expected UUIDs
- Detect characteristic property changes
- Discover new characteristics in firmware updates

---

### 2. Write Pattern Testing (`backend/tools/ble_exploration/test_patterns.py`)

**Purpose:** Systematically test command formats to understand protocol

**What it tests:**
```python
# Category 1: Known working endpoints
"GET /api/1.0/version"
"GET /stats"
"POST /sif/start"
"POST /sif/stop"
"POST /sif/erase"
"POST /sif/write"

# Category 2: HTTP method variations
"GET /api/1.0/version"
"POST /api/1.0/version"
"PUT /api/1.0/version"
"DELETE /api/1.0/version"
"PATCH /api/1.0/version"

# Category 3: Path enumeration
"GET /api"
"GET /api/1.0"
"GET /api/1.0/"
"GET /api/2.0/version"
"GET /sif"

# Category 4: Parameter testing
"GET /stats?refresh=true"
"POST /sif/start?verify=true"
"GET /api/1.0/version?format=json"

# Category 5: Edge cases
""                              # Empty command
"X" * 512                       # Oversized payload
"\x00" * 20                     # Null bytes
"GET /nonexistent"              # 404 test

# Category 6: Malformed requests
"INVALID REQUEST"               # Invalid syntax
"GET"                           # Missing path
"GET /api HTTP/1.1\r\n"         # Full HTTP headers

# Category 7: Write operation variants
"POST /sif/write\n\n[binary data]"
"PUT /sif/data"
"WRITE EEPROM"

# Category 8: Binary/special characters
"\x01\x02\x03\x04"              # Binary start
"GET /\x00\x00"                 # Embedded nulls
"命令"                           # Unicode
```

**Output:**
```jsonl
{"event_type": "write_test", "data": {
  "pattern_index": 0,
  "pattern_hex": "474554202f6170692f312e302f76657273696f6e",
  "pattern_ascii": "GET /api/1.0/version",
  "response_hex": "76312e302e3130",
  "response_ascii": "v1.0.10",
  "success": true
}}
```

**Use case:**
- Discover new endpoints
- Understand parameter syntax
- Map error responses
- Find edge case behavior

---

### 3. Notification Monitoring

**Purpose:** Capture real-time notifications during physical operations

**What to do:**
1. Start monitoring (60s window)
2. **Insert SFP module** into Wizard
3. Wait 5 seconds
4. **Remove SFP module**
5. Wait for monitoring to complete

**Output:**
```jsonl
{"event_type": "monitoring_complete", "data": {
  "total_notifications": 15,
  "notifications": [
    {
      "timestamp": "2025-01-10T10:00:05",
      "data_hex": "6d6f64756c655f696e7365727465643a74727565",
      "data_ascii": "module_inserted:true"
    },
    {
      "timestamp": "2025-01-10T10:00:10",
      "data_hex": "6d6f64756c655f72656d6f7665643a74727565",
      "data_ascii": "module_removed:true"
    }
  ]
}}
```

**Use case:**
- Understand state change notifications
- Detect module insertion/removal events
- Map notification format to protocol
- Identify timing patterns

---

## Hardware Testing (`backend/tools/ble_exploration/hardware_tests.py`)

### Purpose
Automated pytest suite for validating BLE operations with physical hardware.

### Setup

1. **Update Device Addresses**
   ```python
   # Edit hardware_tests.py
   DEVICE_001 = "AA:BB:CC:DD:EE:01"  # Your device MAC
   DEVICE_002 = "AA:BB:CC:DD:EE:02"  # Optional: second device
   DEVICE_003 = "AA:BB:CC:DD:EE:03"  # Optional: third device
   ```

2. **Install Dependencies**
   ```bash
   cd backend
   poetry install
   poetry run pytest --version
   ```

### Running Tests

```bash
# Run all hardware tests
poetry run pytest tools/ble_exploration/hardware_tests.py -v --hardware

# Run specific test
poetry run pytest tools/ble_exploration/hardware_tests.py::test_read_version_consistent -v

# Generate HTML report
poetry run pytest tools/ble_exploration/hardware_tests.py --html=test_report.html --self-contained-html
```

### Test Categories

**Discovery Tests** (no module required):
- `test_all_devices_discoverable` - Verify devices are found
- `test_device_has_sfp_service` - Check expected UUIDs exist

**Version Tests** (no module required):
- `test_read_version_consistent` - Version reads are identical

**Status Tests** (no module required):
- `test_read_status` - Device status endpoint responds

**Read Tests** (module required):
- `test_read_eeprom_idempotent` - Multiple reads return same data

**Cross-Device Tests** (multiple devices + module required):
- `test_cross_device_consistency` - Same module on different devices

**Stability Tests**:
- `test_repeated_connections` - Connect/disconnect 10 times

### Expected Results

**✅ Success Criteria:**
- All discovery tests pass
- Version reads are identical
- EEPROM reads are idempotent (same data)
- Connection success rate > 90%
- Cross-device reads match (if multiple devices)

**❌ If Tests Fail:**
1. Check device MAC addresses in test file
2. Verify module is inserted for EEPROM tests
3. Check Bluetooth adapter is working
4. Ensure devices are powered and in range
5. Review debug UI logs for BLE errors

---

## LLM Analysis (`backend/tools/ble_exploration/analyzer.py`)

### Purpose
Generate comprehensive prompts for Claude to analyze exploration logs and produce protocol specifications.

### Usage

```bash
# Generate analysis prompt from logs
python -m backend.tools.ble_exploration.analyzer reports/ha_debug.jsonl

# Output: reports/ha_debug_analysis.txt

# View summary without generating prompt
python -m backend.tools.ble_exploration.analyzer reports/ha_debug.jsonl --summary

# Specify custom output file
python -m backend.tools.ble_exploration.analyzer reports/ha_debug.jsonl -o my_analysis.txt
```

### Analysis Prompt Includes

1. **Session Overview**
   - Log file metadata
   - Event counts by type
   - Devices tested
   - Time range

2. **Full Log Data**
   - Complete JSONL logs
   - Formatted for LLM analysis

3. **Analysis Requirements**
   - Command structure analysis
   - Response pattern detection
   - State machine mapping
   - Data transfer protocol
   - Edge case identification
   - Performance characteristics

4. **Output Requirements**
   - YAML protocol specification
   - Python client implementation
   - Unit tests
   - Integration test scenarios
   - Implementation recommendations

### Feeding to Claude

```bash
# Method 1: Pipe to Claude Code
claude code < reports/ha_debug_analysis.txt

# Method 2: Copy-paste in Claude chat
# Open file and paste contents into chat

# Method 3: Use Claude Code file upload
# Upload analysis.txt in Claude Code UI
```

### Expected Claude Output

1. **Protocol Specification (YAML)**
   ```yaml
   protocol:
     name: "SFP Wizard BLE Protocol"
     version: "1.0.10"
     commands:
       - name: "read_eeprom"
         request: "POST /sif/start"
         response_type: "binary"
         chunk_size: 20
   ```

2. **Python Implementation**
   ```python
   class SFPWizardProtocol:
       async def read_eeprom(self) -> bytes:
           # Implementation based on analysis
   ```

3. **Test Cases**
   ```python
   async def test_read_returns_256_bytes():
       # Generated test
   ```

4. **Recommendations**
   - Optimal timeouts
   - Retry strategies
   - Error handling patterns

---

## Best Practices

### 1. Systematic Exploration

```
Day 1: Initial Discovery
- Run service discovery
- Verify UUIDs match expected
- Test known commands

Day 2: Write Testing
- Run all 100+ test patterns
- Identify new endpoints
- Map error responses

Day 3: Notification Monitoring
- Capture module insertion
- Capture module removal
- Map state transitions

Day 4: Analysis
- Generate LLM prompts
- Feed to Claude
- Review protocol spec

Day 5: Validation
- Update implementation
- Run hardware tests
- Verify 100% success rate
```

### 2. Multiple Devices

Test with 3 devices to catch:
- Firmware inconsistencies
- Hardware-specific quirks
- Timing variations
- Cross-device compatibility

### 3. Multiple Modules

Test with diverse modules:
- Different vendors (Cisco, Ubiquiti, Generic)
- Different types (1G, 10G, BiDi)
- Different conditions (new, used, suspected bad)

### 4. Log Everything

Keep comprehensive logs:
```
reports/
├── device_001_discovery.jsonl
├── device_001_write_tests.jsonl
├── device_001_monitoring.jsonl
├── device_002_discovery.jsonl
├── device_003_discovery.jsonl
├── ha_debug.jsonl                    # From UI
└── analysis_prompts/
    ├── combined_analysis.txt
    └── claude_response.md
```

---

## Troubleshooting

### "Device not found"
- Check device is powered on
- Verify Bluetooth is enabled in HA
- Run `hcitool scan` to verify visibility
- Check device name patterns in config

### "Connection timeout"
- Move closer to device (BLE range ~10m)
- Check for Bluetooth interference
- Restart device
- Restart HA Bluetooth integration

### "No response to command"
- Verify characteristic UUIDs are correct
- Check notification handler is running
- Increase timeout duration
- Review debug UI logs

### "Inconsistent reads"
- Module may be loose in socket
- Clean module contacts
- Try different module
- Check device firmware version

### "Write test hangs"
- Some patterns may cause device to hang
- Power cycle device
- Skip problematic patterns
- Update test_patterns.py

---

## Integration with Production Code

### After Exploration

1. **Update Protocol Constants**
   ```python
   # backend/app/services/ble_operations.py
   SERVICE_UUID = "..."  # Verified via discovery
   WRITE_CHAR_UUID = "..."
   NOTIFY_CHAR_UUID = "..."
   ```

2. **Refine Command Format**
   ```python
   # Based on analysis results
   async def _send_command(self, command: str):
       # Use discovered format
       await self._client.write_gatt_char(
           self.WRITE_CHAR_UUID,
           command.encode("utf-8")
       )
   ```

3. **Implement Response Parsing**
   ```python
   # Based on notification analysis
   async def _read_response(self, timeout: float):
       # Implement proper framing/chunking
       pass
   ```

4. **Add Error Handling**
   ```python
   # Based on discovered error codes
   if response.startswith(b"ERROR"):
       raise DeviceError(response.decode())
   ```

5. **Validate with Hardware Tests**
   ```bash
   pytest tools/ble_exploration/hardware_tests.py -v
   ```

---

## Success Metrics

### Exploration Complete When:
- ✅ All 3 test types run (discovery, write tests, monitoring)
- ✅ Logs contain responses for 90%+ of test patterns
- ✅ Claude analysis produces valid protocol spec
- ✅ Hardware tests pass with 100% success rate
- ✅ Implementation matches protocol spec
- ✅ Read/write operations work reliably

### Ready for Users When:
- ✅ 100 consecutive reads return identical data
- ✅ 50 write→verify cycles succeed
- ✅ Works with modules from 3+ vendors
- ✅ Error messages are clear and actionable
- ✅ Operations complete in reasonable time
- ✅ Documentation is complete

---

## Future Enhancements

### Planned Features:
- Automated firmware version detection
- Protocol diff between firmware versions
- Performance benchmarking suite
- Automated regression testing
- Multi-device concurrent testing

### Contributing:
If you discover new endpoints or protocol features:
1. Document in logs
2. Run full exploration suite
3. Generate analysis prompt
4. Update test_patterns.py
5. Submit PR with findings

---

## Resources

- **BLE API Specification**: `docs/BLE_API_SPECIFICATION.md`
- **Hardware Testing Plan**: `docs/TESTING_PLAN.md`
- **Issue Tracker**: `docs/ISSUE_4_IMPLEMENTATION.md`
- **SFF-8472 Spec**: https://members.snia.org/document/dl/25916

---

**Last Updated:** 2025-01-10
**Status:** Active Development (Pre-Alpha)
