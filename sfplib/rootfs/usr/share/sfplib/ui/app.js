/**
 * SFP Liberate - Alpine.js Application
 *
 * Simple reactive UI for HA add-on with integrated debug tools
 */

function sfpApp() {
    return {
        // State
        currentTab: 'library',
        modules: [],
        devices: [],
        selectedDevice: '',
        moduleName: '',
        loading: false,
        debugRunning: false,
        debugLog: [],
        monitoringCountdown: 0,

        // Configuration
        config: {
            version: '',
            device_name_patterns: [],
            auto_discover: true,
            enable_debug_ble: false,
            ble_trace_logging: false,
            scan_interval: 5,
            rssi_threshold: -80,
            connection_timeout: 30,
            sfp_service_uuid: '',
            sfp_write_char_uuid: '',
            sfp_notify_char_uuid: '',
        },

        // Status notifications
        statusMessage: '',
        statusType: 'info', // 'info', 'success', 'error'

        // ====================================================================
        // Initialization
        // ====================================================================

        async init() {
            console.log('SFP Liberate initialized');
            await this.loadConfig();
            await this.loadModules();
        },

        // ====================================================================
        // Configuration
        // ====================================================================

        async loadConfig() {
            try {
                const response = await fetch('/api/v1/config');
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                
                this.config = await response.json();
                console.log('Configuration loaded:', this.config);
                
                // Log BLE debug status
                if (this.config.ble_trace_logging) {
                    console.log('🔍 BLE Trace Logging: ENABLED');
                }
                if (this.config.enable_debug_ble) {
                    console.log('🐛 Debug BLE: ENABLED');
                }
            } catch (error) {
                console.error('Failed to load configuration:', error);
                // Continue with defaults
            }
        },

        // ====================================================================
        // Status Management
        // ====================================================================

        showStatus(message, type = 'info') {
            this.statusMessage = message;
            this.statusType = type;

            // Auto-dismiss success messages
            if (type === 'success') {
                setTimeout(() => {
                    this.statusMessage = '';
                }, 5000);
            }
        },

        addDebugLog(message) {
            const timestamp = new Date().toLocaleTimeString();
            this.debugLog.push(`[${timestamp}] ${message}`);

            // Keep only last 100 lines
            if (this.debugLog.length > 100) {
                this.debugLog.shift();
            }
        },

        // ====================================================================
        // Module Library
        // ====================================================================

        async loadModules() {
            this.loading = true;
            try {
                const response = await fetch('/api/v1/modules');
                if (!response.ok) throw new Error(`HTTP ${response.status}`);

                this.modules = await response.json();
                console.log(`Loaded ${this.modules.length} modules`);
            } catch (error) {
                console.error('Failed to load modules:', error);
                this.showStatus(`Failed to load modules: ${error.message}`, 'error');
            } finally {
                this.loading = false;
            }
        },

        async deleteModule(moduleId) {
            if (!confirm(`Delete module #${moduleId}? This cannot be undone.`)) {
                return;
            }

            try {
                const response = await fetch(`/api/v1/modules/${moduleId}`, {
                    method: 'DELETE'
                });

                if (!response.ok) throw new Error(`HTTP ${response.status}`);

                this.showStatus(`Module #${moduleId} deleted`, 'success');
                await this.loadModules();
            } catch (error) {
                this.showStatus(`Delete failed: ${error.message}`, 'error');
            }
        },

        // ====================================================================
        // Device Operations
        // ====================================================================

        async discoverDevices() {
            this.showStatus('Discovering devices...', 'info');

            try {
                const response = await fetch('/api/v1/bluetooth/discover');
                if (!response.ok) throw new Error(`HTTP ${response.status}`);

                const data = await response.json();
                this.devices = data.devices || [];

                if (this.devices.length === 0) {
                    this.showStatus('No SFP Wizard devices found. Make sure devices are powered on.', 'error');
                } else {
                    this.showStatus(`Found ${this.devices.length} device(s)`, 'success');

                    // Auto-select first device
                    if (this.devices.length === 1) {
                        this.selectedDevice = this.devices[0].address;
                    }
                }
            } catch (error) {
                this.showStatus(`Discovery failed: ${error.message}`, 'error');
            }
        },

        async readFromDevice() {
            if (!this.selectedDevice) {
                this.showStatus('Please select a device first', 'error');
                return;
            }

            if (!this.moduleName.trim()) {
                this.showStatus('Please enter a module name', 'error');
                return;
            }

            this.loading = true;
            this.showStatus('Reading EEPROM from device...', 'info');

            try {
                const response = await fetch('/api/v1/bluetooth/read', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        device_address: this.selectedDevice,
                        name: this.moduleName
                    })
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || `HTTP ${response.status}`);
                }

                const result = await response.json();
                this.showStatus(`Module saved as #${result.id}`, 'success');

                // Reset form and reload library
                this.moduleName = '';
                await this.loadModules();

                // Switch to library tab
                this.currentTab = 'library';
            } catch (error) {
                this.showStatus(`Read failed: ${error.message}`, 'error');
            } finally {
                this.loading = false;
            }
        },

        async writeModule(moduleId) {
            if (!this.selectedDevice) {
                this.showStatus('Please discover and select a device first', 'error');
                this.currentTab = 'device';
                return;
            }

            if (!confirm(`Write module #${moduleId} to device?\n\nWARNING: This will overwrite the SFP module's EEPROM. Make sure you have the correct module selected!`)) {
                return;
            }

            this.loading = true;
            this.showStatus('Writing EEPROM to device...', 'info');

            try {
                const response = await fetch('/api/v1/bluetooth/write', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        device_address: this.selectedDevice,
                        module_id: moduleId,
                        verify: true
                    })
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || `HTTP ${response.status}`);
                }

                const result = await response.json();

                if (result.verified) {
                    this.showStatus('Write successful and verified!', 'success');
                } else {
                    this.showStatus('Write completed but verification failed', 'error');
                }
            } catch (error) {
                this.showStatus(`Write failed: ${error.message}`, 'error');
            } finally {
                this.loading = false;
            }
        },

        // ====================================================================
        // Debug Tools
        // ====================================================================

        async runServiceDiscovery() {
            if (!this.selectedDevice) {
                this.showStatus('Please select a device first', 'error');
                return;
            }

            this.debugRunning = true;
            this.addDebugLog('Starting service discovery...');
            this.showStatus('Discovering BLE services...', 'info');

            try {
                const response = await fetch('/api/v1/debug/discover-services', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        device_address: this.selectedDevice
                    })
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || `HTTP ${response.status}`);
                }

                const result = await response.json();
                this.addDebugLog(`Discovered ${result.service_count} services`);

                result.services.forEach(service => {
                    this.addDebugLog(`Service: ${service.uuid}`);
                    service.characteristics.forEach(char => {
                        this.addDebugLog(`  └─ Char: ${char.uuid} (${char.properties.join(', ')})`);
                    });
                });

                this.showStatus('Service discovery complete', 'success');
            } catch (error) {
                this.addDebugLog(`ERROR: ${error.message}`);
                this.showStatus(`Discovery failed: ${error.message}`, 'error');
            } finally {
                this.debugRunning = false;
            }
        },

        async runWriteTests() {
            if (!this.selectedDevice) {
                this.showStatus('Please select a device first', 'error');
                return;
            }

            this.debugRunning = true;
            this.addDebugLog('Starting write pattern tests (100+ patterns)...');
            this.showStatus('Testing write patterns (this may take 2-3 minutes)...', 'info');

            try {
                const response = await fetch('/api/v1/debug/test-writes', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        device_address: this.selectedDevice
                    })
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || `HTTP ${response.status}`);
                }

                const result = await response.json();
                this.addDebugLog(`Tested ${result.total_patterns} patterns`);
                this.addDebugLog(`Successful: ${result.successful}, Failed: ${result.failed}`);

                this.showStatus(`Write tests complete: ${result.successful}/${result.total_patterns} succeeded`, 'success');
            } catch (error) {
                this.addDebugLog(`ERROR: ${error.message}`);
                this.showStatus(`Write tests failed: ${error.message}`, 'error');
            } finally {
                this.debugRunning = false;
            }
        },

        async runNotificationMonitoring() {
            if (!this.selectedDevice) {
                this.showStatus('Please select a device first', 'error');
                return;
            }

            this.debugRunning = true;
            this.monitoringCountdown = 60;
            this.addDebugLog('Starting notification monitoring (60s)...');
            this.addDebugLog('ACTION REQUIRED: Insert and remove SFP module now!');
            this.showStatus('Monitoring notifications for 60s - insert/remove module now!', 'info');

            // Countdown timer
            const countdownInterval = setInterval(() => {
                this.monitoringCountdown--;
                if (this.monitoringCountdown <= 0) {
                    clearInterval(countdownInterval);
                }
            }, 1000);

            try {
                const response = await fetch('/api/v1/debug/monitor-notifications', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        device_address: this.selectedDevice,
                        duration: 60
                    })
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || `HTTP ${response.status}`);
                }

                const result = await response.json();
                this.addDebugLog(`Captured ${result.notification_count} notifications`);

                // Show first few notifications
                result.notifications.slice(0, 10).forEach(notif => {
                    this.addDebugLog(`  ${notif.timestamp}: ${notif.data_ascii.substring(0, 60)}`);
                });

                if (result.notification_count > 10) {
                    this.addDebugLog(`  ... and ${result.notification_count - 10} more`);
                }

                this.showStatus(`Monitoring complete: ${result.notification_count} notifications captured`, 'success');
            } catch (error) {
                this.addDebugLog(`ERROR: ${error.message}`);
                this.showStatus(`Monitoring failed: ${error.message}`, 'error');
            } finally {
                this.debugRunning = false;
                this.monitoringCountdown = 0;
                clearInterval(countdownInterval);
            }
        },

        async exportLogs() {
            this.showStatus('Downloading logs...', 'info');

            try {
                const response = await fetch('/api/v1/debug/export-logs');
                if (!response.ok) throw new Error(`HTTP ${response.status}`);

                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `ble-exploration-${new Date().toISOString().split('T')[0]}.jsonl`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);

                this.showStatus('Logs downloaded successfully', 'success');
            } catch (error) {
                this.showStatus(`Export failed: ${error.message}`, 'error');
            }
        }
    };
}
