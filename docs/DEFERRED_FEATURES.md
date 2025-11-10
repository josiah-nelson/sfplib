# Features Deferred Until Post-MVP

This document tracks features that have been intentionally deferred, archived, or removed during the HA-first minimal refactor. These features may be reconsidered after the MVP proves core functionality and gathers real user feedback.

---

## HIGH PRIORITY - Needed for Week 2-4

### Export/Import Functionality
**Status:** 🔴 CRITICAL - Not yet implemented
**Priority:** Must have before user release
**Reason:** Protects user data, enables backup/restore workflows

**Implementation plan:**
- **Export:** ZIP file containing:
  - SQLite database (`sfp_library.db`)
  - All EEPROM binary files
  - Manifest JSON with metadata
- **Import:** Extract ZIP, validate, merge with existing library
- **UI:** Simple "Export All" and "Import from File" buttons

**Prevents:** User data loss (critical trust issue)

**Timeline:** Week 4 (before first user release)

---

### Write Verification
**Status:** 🔴 CRITICAL - Not yet implemented
**Priority:** Safety-critical feature
**Reason:** Prevents silently bricked modules

**Implementation plan:**
- After every write operation: automatically read back EEPROM
- Byte-by-byte comparison with original data
- Alert user immediately if mismatch detected
- Option to retry write or abort

**Prevents:** Corrupted modules, user trust loss

**Timeline:** Week 4 (before first user release)

---

### Module Notes/Tags
**Status:** 🟡 High value, low complexity
**Priority:** Week 5-6

**Implementation plan:**
- Add `notes` (text) and `tags` (array) columns to SQLite
- UI: Notes textarea, tag input with autocomplete
- Filter/search by tags

**Use cases:**
- "Working spare for server rack 2"
- "Failed on 2025-01-10, suspected bad"
- Tags: "Cisco", "10G", "850nm", "BiDi"

**Benefit:** Makes library useful for organization, not just storage

**Timeline:** Week 5-6 (user feedback dependent)

---

## MEDIUM PRIORITY - After User Feedback

### Module Comparison View
**Status:** 🟡 Useful debugging aid
**Priority:** Medium (wait for user requests)

**Implementation plan:**
- Select two modules from library
- Side-by-side hex view with diff highlighting
- Decode differences (e.g., "Vendor changed from X to Y")
- Export diff report

**Use cases:**
- Understanding why clone failed
- Comparing vendor variations
- Debugging EEPROM corruption

**Timeline:** Week 6-8 (if users request it)

---

### Batch Operations
**Status:** 🟡 Power user feature
**Priority:** Medium (wait for user requests)

**Implementation plan:**
- Multi-select modules in UI
- Operations: delete, export, tag, rename
- Progress indicator for batch writes

**Use cases:**
- Reading 20 modules in sequence
- Bulk tagging by vendor
- Mass export for migration

**Timeline:** Week 7+ (if power users emerge)

---

### CLI Tool
**Status:** 🟢 Good for automation, but not essential
**Priority:** Low (physical operations limit scripting value)

**Reconsideration:** Initially proposed for scripting, but every operation requires physical module insertion/removal. Limited automation value.

**Possible future:** If users request headless operation for testing/QA workflows.

**Timeline:** Not planned unless requested

---

## ARCHIVED - Removed During Refactor

### Web Frontend (Next.js + Standalone Docker)
**Status:** ⚫ ARCHIVED
**Location:** Will be moved to `../sfpliberate-archive/frontend/`
**Reason:** Complexity, browser compatibility issues, deployment overhead

**What was removed:**
- Entire Next.js 16 frontend application
- React 19 components and hooks
- Tailwind CSS + shadcn/ui component library
- Web Bluetooth browser API integration
- Docker Compose standalone deployment
- API proxy configuration in Next.js
- Webpack/Turbopack build configuration

**Why removed:**
- Web Bluetooth limited to Chrome/Edge (Safari, Firefox unsupported)
- iOS users blocked (no Web Bluetooth in Safari)
- Complex deployment (Docker Compose, networking, CORS)
- HA add-on provides better UX with native Bluetooth

**Reconsideration criteria:**
- If HA users request standalone version
- If Web Bluetooth gains broader support
- If non-HA users emerge as significant user base

**Alternative:** HA add-on with Alpine.js UI (15KB vs 150KB+)

---

### ESPHome Bluetooth Proxy
**Status:** ⚫ ARCHIVED
**Location:** Will be moved to `../sfpliberate-archive/backend-removed/esphome/`
**Reason:** Complexity for marginal benefit, HA native Bluetooth sufficient

**What was removed:**
- mDNS device discovery service
- WebSocket bridge for BLE commands
- ESPHome Native API client
- Device manager and connection pooling
- Proxy service with RSSI-based selection
- Docker Compose ESPHome override
- All `backend/app/services/esphome/` code
- `backend/app/api/v1/esphome*.py` endpoints

**Why removed:**
- Built to work around Web Bluetooth limitations on iOS/Safari
- Added 2000+ lines of complex proxy code
- HA users already have ESPHome OR can use native integration
- Maintenance burden (two BLE paths to support)
- Network complexity (mDNS, WebSocket, multiple proxies)

**Alternative:** HA native Bluetooth integration (simpler, more reliable)

**Reconsideration criteria:** Never - HA's native solution is superior

---

### Appwrite Cloud Deployment
**Status:** ⚫ ARCHIVED
**Location:** Will be moved to `../sfpliberate-archive/frontend/lib/appwrite/`
**Reason:** Premature optimization, no users to serve yet

**What was removed:**
- Multi-tenancy support with authentication
- Role-based access control (RBAC) system
- SSR cookie bridge for auth
- JWT session handling
- Realtime subscription hooks
- Two repository implementations (Standalone + Appwrite)
- Deployment mode detection logic
- Appwrite-specific API routes
- Permission system for documents/files
- Community features (submissions, sharing)
- Approximately 40% of frontend codebase

**Why removed:**
- Zero users in pre-alpha to serve
- Auth/RBAC adds complexity with no current value
- Cloud hosting premature before product-market fit
- Most codebase complexity existed to support this
- Self-hosted Docker sufficient for target users

**Reconsideration criteria:**
- If HA add-on proves successful with 50+ users
- If users request cloud hosting option
- If revenue model established (cloud could be paid tier)

**Timeline:** Not before Q3 2025 at earliest

---

### Home Assistant Add-on (Old Multi-Mode Version)
**Status:** 🟢 KEPT but SIMPLIFIED
**What was removed:**
- ESPHome proxy configuration options
- mDNS discovery settings
- Complex device pattern matching
- Multiple Bluetooth connection modes

**What was kept:**
- Core add-on structure
- Native HA Bluetooth integration
- Ingress-based UI
- Simple configuration (log level, timeout)

**Why simplified:**
- Original version tried to support too many connection methods
- New version: HA native Bluetooth only (one path, reliable)

---

### Community Module Repository
**Status:** ⚫ ARCHIVED
**Reason:** Feature creep, premature before core CRUD proven

**What was removed:**
- Separate Appwrite collections for community modules
- Blob storage for shared EEPROM files
- Photo upload functionality
- Verification workflow (admin approval)
- Download counters and favorites system
- Permission system (alpha/admin roles)
- `lib/community.ts` and related components

**Why removed:**
- No users yet to create community
- Adds database complexity
- Requires moderation/verification workflow
- Git repo of JSON files would work better

**Alternative (future):**
- GitHub repository with JSON module files
- Users export to JSON, submit PR
- GitHub = free hosting + version control + community tools

**Reconsideration criteria:**
- After 100+ active users
- If users request sharing functionality
- If volunteer moderators available

**Timeline:** Not before Q4 2025

---

## DOCUMENTED BUT NOT IMPLEMENTED

### Features That Were Planned But Never Built

These appear in documentation or TODOs but were never implemented:

- **Multi-firmware version support:** Assumed needed, but all devices use v1.0.10
- **Mobile app:** Mentioned in long-term roadmap, never started
- **Advanced search/filtering:** Basic search sufficient for pre-alpha
- **Bulk import/export (CSV/ZIP):** Export planned for Week 4, CSV overkill
- **DDM (Digital Diagnostics Monitoring):** Interesting but not core functionality
- **Cloud sync for standalone:** Only relevant if standalone mode resurrected

---

## Decision Framework for Future Features

Before implementing any deferred feature, ask:

1. **User demand:** Have 3+ users explicitly requested this?
2. **Core functionality:** Does this improve read/write reliability?
3. **Safety:** Does this prevent data loss or module damage?
4. **Effort vs value:** Will this take < 1 week and benefit most users?

**If NO to all four:** Defer further

**Priority order:**
1. Safety features (write verification, backup)
2. Reliability improvements (error handling, retries)
3. User-requested features (based on feedback)
4. Nice-to-haves (polish, advanced features)

---

## Archive Manifest

Files/directories to be moved to `../sfpliberate-archive/`:

```
Archive structure:
../sfpliberate-archive/
├── frontend/                    # Entire Next.js app
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── ...
├── backend-removed/
│   ├── esphome/                # ESPHome proxy service
│   ├── esphome_websocket.py    # WebSocket endpoints
│   └── esphome.py              # REST endpoints
├── docker-compose-removed/
│   ├── docker-compose.yml      # Old standalone config
│   ├── docker-compose.dev.yml
│   └── docker-compose.esphome.yml
├── docs-archive/
│   ├── APPWRITE.md
│   ├── AUTH_SYSTEM.md
│   └── ESPHOME.md
└── README.md                    # Archive explanation
```

---

## Notes

- This document is a living record of architectural decisions
- Update when features are un-deferred or permanently removed
- Review quarterly as user base grows
- Success = NOT building features users don't want

**Last updated:** 2025-01-10 (HA-first refactor)
