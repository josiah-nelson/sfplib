# Hardware Testing Plan

Comprehensive testing strategy for SFPLiberate HA add-on before user release.

**Target:** 100% success rate for read/write operations

---

## Test Equipment

### Required Hardware

**SFP Wizard Devices:**
- ✅ Minimum: 1 device for basic testing
- 🎯 Recommended: 3 devices for consistency validation
- 📋 Note firmware versions for each device

**SFP/SFP+ Modules:**
- ✅ Minimum: 3 modules (1 known good, 1 blank, 1 test)
- 🎯 Recommended: 12+ modules covering diversity:

| Category | Examples | Purpose |
|----------|----------|---------|
| **Vendors** | Cisco, Ubiquiti, Finisar, Generic | Cross-vendor compatibility |
| **Types** | 1000BASE-SX, 1000BASE-LX, 10GBASE-SR | Different EEPROM layouts |
| **Special** | BiDi, DWDM, CWDM | Edge case testing |
| **Condition** | New, Used, Suspected Bad | Reliability testing |

**Host Environment:**
- Home Assistant OS/Supervised instance
- Bluetooth adapter (built-in or USB)
- OR ESPHome Bluetooth proxy

---

## Testing Phases

### Phase 1: Baseline Validation (Day 1)

**Goal:** Verify basic functionality works

#### 1.1 Installation Test
```
1. Install add-on from repository
2. Start add-on
3. Check logs for successful startup
4. Open Web UI → verify UI loads

Expected: Clean startup, UI accessible in <30s
```

#### 1.2 Device Discovery Test
```
1. Power on SFP Wizard
2. Wait for discovery (max 30s)
3. Verify device appears in dropdown
4. Check MAC address and RSSI

Expected: Device discovered automatically
```

#### 1.3 Debug Tools Test
```
1. Open "🔧 Debug Tools" tab
2. Run "Discover Services"
3. Verify UUIDs match expected:
   - Service: 8E60F02E-F699-4865-B83F-F40501752184
   - Write: 9280F26C-A56F-43EA-B769-D5D732E1AC67
   - Notify: DC272A22-43F2-416B-8FA5-63A071542FAC

Expected: All UUIDs present and correct
```

---

### Phase 2: Read Operation Validation (Day 2)

**Goal:** 100% read success rate

#### 2.1 Single Read Test
```
1. Insert known-good SFP module
2. Click "Read Module"
3. Enter name: "Test Module 001"
4. Verify parsed data:
   - Vendor name populated
   - Model number populated
   - Serial number populated
5. Check database entry created

Expected: Read completes in <10s, data parsed correctly
```

#### 2.2 Repeated Read Test
```
1. Same module from 2.1
2. Read 10 times consecutively
3. Compare EEPROM data (should be identical)
4. Note: Will create duplicates (expected)

Expected: All 10 reads return identical data
```

#### 2.3 Read Reliability Test
```
1. Insert module
2. Read 100 times
3. Log success/failure rate
4. Calculate: (successes / 100) * 100%

Expected: 100% success rate
Target: 100 consecutive successful reads
```

#### 2.4 Multi-Module Test
```
1. Test with 10 different modules
2. Read each module once
3. Verify all parse successfully
4. Check for parsing errors

Expected: All modules parse, no "Unknown" fields
```

#### 2.5 Edge Case - No Module
```
1. Empty socket (no module)
2. Attempt read
3. Verify error message is clear

Expected: User-friendly error, no crash
```

#### 2.6 Edge Case - Module Mid-Operation
```
1. Start read
2. Remove module after 2 seconds
3. Verify error handling

Expected: Graceful failure, clear error message
```

---

### Phase 3: Write Operation Validation (Day 3-4)

**Goal:** 100% write+verify success rate

#### 3.1 Single Write Test
```
1. Read module A → save as "Original"
2. Insert blank module B
3. Write "Original" to module B
4. Verify enabled (default)
5. Wait for completion

Expected: Write completes, verification passes
```

#### 3.2 Write-Read-Verify Cycle
```
1. Read module A
2. Write to blank module B
3. Remove module B, insert module C
4. Read module C
5. Compare: A's data == C's data

Expected: Data matches byte-for-byte
```

#### 3.3 Write Reliability Test
```
1. Read one module → save as "Test Profile"
2. Use 10 blank modules
3. Write "Test Profile" to each
4. Read back each module
5. Compare all read-backs to original

Expected: All 10 writes verify successfully
```

#### 3.4 Write+Verify 50-Cycle Test
```
1. Module A (known good data)
2. Blank module B
3. Loop 50 times:
   a. Write A's data to B
   b. Read B
   c. Verify matches A
   d. Erase B (optional)
4. Log any failures

Expected: 50/50 cycles pass verification
```

#### 3.5 Write Without Verification Test
```
1. Disable verification
2. Write to module
3. Manually read back
4. Check if write actually succeeded

Expected: Write completes (but use with caution)
```

#### 3.6 Edge Case - Write Protected Module
```
1. Use write-protected module (if available)
2. Attempt write
3. Verify error handling

Expected: Clear error message about write failure
```

---

### Phase 4: Cross-Device Consistency (Day 5)

**Goal:** Same module reads identically on all devices

**Requires:** Multiple SFP Wizard devices

#### 4.1 Cross-Device Read Test
```
1. Insert module in Device 1
2. Read EEPROM
3. Move module to Device 2
4. Read EEPROM
5. Move module to Device 3
6. Read EEPROM
7. Compare all 3 reads

Expected: All reads return identical data
```

#### 4.2 Cross-Device Write Test
```
1. Device 1: Read module A
2. Device 2: Write A's data to blank module B
3. Device 3: Read module B
4. Compare: A's original data == B's readback from Device 3

Expected: Data matches across devices
```

#### 4.3 Firmware Version Check
```
1. For each device:
   a. Open debug tools
   b. Check firmware version
2. Document versions
3. Flag if inconsistent

Expected: All devices on same firmware (ideally)
```

---

### Phase 5: Performance & Timing (Day 6)

**Goal:** Operations complete in reasonable time

#### 5.1 Read Performance Test
```
1. Time 10 read operations
2. Calculate:
   - Average time
   - Min time
   - Max time
   - Standard deviation

Target: Average < 5 seconds
```

#### 5.2 Write Performance Test
```
1. Time 10 write+verify operations
2. Calculate statistics

Target: Average < 30 seconds (includes verification)
```

#### 5.3 Connection Establishment Test
```
1. Time from "Connect" click to "Connected" state
2. Repeat 10 times

Target: Average < 3 seconds
```

#### 5.4 UI Responsiveness Test
```
1. During long operation (write)
2. Check UI remains responsive
3. Verify progress indicators work

Expected: UI doesn't freeze, user can cancel
```

---

### Phase 6: Error Handling & Recovery (Day 7)

**Goal:** All error conditions handled gracefully

#### 6.1 Connection Loss Test
```
1. Start read operation
2. Power off device mid-operation
3. Verify error message
4. Attempt reconnect

Expected: Clear error, successful reconnect
```

#### 6.2 Timeout Test
```
1. Device powered but unresponsive
2. Attempt operation
3. Verify timeout occurs
4. Check timeout value is reasonable

Expected: Timeout after 30s, clear error message
```

#### 6.3 Corrupt Data Test
```
1. Module with corrupted EEPROM (if available)
2. Attempt read
3. Check parsing behavior

Expected: Graceful parsing failure, no crash
```

#### 6.4 Database Corruption Test
```
1. Manually corrupt SQLite database
2. Restart add-on
3. Verify recovery or clear error

Expected: Database recreated or clear migration error
```

---

### Phase 7: User Scenarios (Day 8-9)

**Goal:** Real-world workflows succeed

#### 7.1 Scenario: Clone Working Module
```
User Story: "I have a working Cisco module, want to clone it to a blank"

1. Insert working module → Read → "Cisco GLC-SX-MMD"
2. Insert blank → Write "Cisco GLC-SX-MMD"
3. Verification passes
4. Test cloned module in network equipment

Expected: Cloned module works identically to original
```

#### 7.2 Scenario: Backup and Restore
```
User Story: "Backup module before testing"

1. Read module → "Production Module Backup"
2. Test module (may corrupt)
3. If corrupted: Write "Production Module Backup"
4. Verify restoration

Expected: Module restored to original state
```

#### 7.3 Scenario: Build Module Library
```
User Story: "Read 20 modules into library for future use"

1. Read module 1 → "Office Switch Port 1"
2. Read module 2 → "Office Switch Port 2"
   ...
3. Read module 20 → "Lab Test Module"
4. Browse library
5. Search/filter modules

Expected: All 20 modules in library, searchable
```

#### 7.4 Scenario: Mass Cloning
```
User Story: "Clone 1 module to 10 blanks"

1. Read original → "Standard Config"
2. For each of 10 blank modules:
   a. Insert blank
   b. Write "Standard Config"
   c. Verify
3. Check all 10 match original

Expected: All 10 clones identical
```

---

## Automated Testing

### Hardware Test Suite

```bash
# Run all automated hardware tests
cd backend
poetry run pytest tools/ble_exploration/hardware_tests.py -v --hardware

# Generate HTML report
poetry run pytest tools/ble_exploration/hardware_tests.py \
  --html=test_report.html \
  --self-contained-html
```

**Tests Included:**
- `test_all_devices_discoverable` - Discovery works
- `test_device_has_sfp_service` - UUIDs present
- `test_read_version_consistent` - Firmware version stable
- `test_read_status` - Status endpoint responds
- `test_read_eeprom_idempotent` - Reads are consistent
- `test_cross_device_consistency` - Same data across devices
- `test_repeated_connections` - Connection stability

---

## Success Criteria

### Must Pass Before User Release:

**Reliability:**
- ✅ 100 consecutive reads succeed (100%)
- ✅ 50 write+verify cycles succeed (100%)
- ✅ Connection success rate > 95%
- ✅ No crashes or hangs during testing

**Functionality:**
- ✅ Reads parse all module types correctly
- ✅ Writes with verification never silently fail
- ✅ Cross-device reads are identical
- ✅ All user scenarios complete successfully

**Performance:**
- ✅ Read operation < 10 seconds
- ✅ Write+verify operation < 60 seconds
- ✅ UI responsive during operations
- ✅ Connection established < 5 seconds

**User Experience:**
- ✅ Clear error messages (no "unknown error")
- ✅ Progress indicators work
- ✅ Operations can be cancelled
- ✅ Documentation is complete

**Safety:**
- ✅ Write verification prevents corruption
- ✅ Destructive operations require confirmation
- ✅ Duplicate detection works
- ✅ Database backups functional

---

## Test Matrix

| Test Category | Tests | Pass Criteria | Status |
|---------------|-------|---------------|---------|
| Installation | 3 | All pass | 🔴 Not started |
| Device Discovery | 1 | Auto-discovery works | 🔴 Not started |
| Read Operations | 6 | 100% success rate | 🔴 Not started |
| Write Operations | 6 | 100% success rate | 🔴 Not started |
| Cross-Device | 3 | Consistent data | 🔴 Not started |
| Performance | 4 | Meets targets | 🔴 Not started |
| Error Handling | 4 | Graceful failures | 🔴 Not started |
| User Scenarios | 4 | All complete | 🔴 Not started |
| **TOTAL** | **31** | **All pass** | **0% complete** |

---

## Issue Tracking

### Issue Template

```markdown
**Test:** [Test name]
**Phase:** [Phase number]
**Severity:** [Critical/High/Medium/Low]

**Issue Description:**
[What went wrong]

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happened]

**Reproduction Steps:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Environment:**
- Device MAC: [XX:XX:XX:XX:XX:XX]
- Firmware: [version]
- Module: [vendor/model]

**Logs:**
```
[Paste relevant logs]
```

**Resolution:**
[How it was fixed]
```

---

## Timeline

### Week 1: Foundation
- Day 1: Phase 1 (Baseline)
- Day 2: Phase 2 (Read operations)
- Day 3-4: Phase 3 (Write operations)
- Day 5: Phase 4 (Cross-device)
- Day 6: Phase 5 (Performance)
- Day 7: Phase 6 (Error handling)

### Week 2: Validation
- Day 8-9: Phase 7 (User scenarios)
- Day 10: Fix issues from Week 1
- Day 11: Regression testing
- Day 12: Performance optimization
- Day 13: Documentation review
- Day 14: Final validation

### Week 3: Pre-Release
- Day 15-17: Bug fixes
- Day 18: Export/import implementation
- Day 19: Final testing
- Day 20: Documentation
- Day 21: Release preparation

---

## Sign-off Checklist

Before releasing to users:

- [ ] All 31 manual tests pass
- [ ] All automated tests pass
- [ ] 100 consecutive reads succeed
- [ ] 50 write+verify cycles succeed
- [ ] Tested with 10+ different modules
- [ ] Tested with 3+ different vendors
- [ ] Cross-device consistency validated
- [ ] Performance targets met
- [ ] Error messages reviewed and improved
- [ ] Documentation complete
- [ ] Export/import functionality working
- [ ] Database backups tested
- [ ] Recovery procedures documented
- [ ] Known issues documented
- [ ] User guide reviewed
- [ ] Installation guide reviewed

**Release Approved By:** _______________
**Date:** _______________

---

**Last Updated:** 2025-01-10
**Status:** Ready for testing (implementation complete)
