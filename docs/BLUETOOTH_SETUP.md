# Bluetooth Device Setup

## Adding Your SFP Wizard Device to Home Assistant

The SFPLiberate addon currently requires your SFP Wizard device to be added as a Bluetooth entity in Home Assistant before it can be discovered.

### Why is this needed?

Home Assistant's Bluetooth proxies receive BLE advertisements from your SFP Wizard, but these raw advertisements are not exposed via the Supervisor API that addons can access. The advertisements are visible in **Developer Tools → Bluetooth → Advertisement Monitor**, but addons cannot query this data directly.

By adding the device to the Bluetooth integration, Home Assistant creates an entity that the addon can discover and connect to.

### Setup Steps

1. **Find Your Device's MAC Address**
   - The BLE MAC address is printed on your SFP Wizard device
   - Example: `1C:6A:1B:05:F7:FE`
   - Alternatively, check **Developer Tools → Bluetooth → Advertisement Monitor** for devices with service UUID `8e60f02e-f699-4865-b83f-f40501752184`

2. **Add Device to Bluetooth Integration**
   - Navigate to **Settings → Devices & Services → Bluetooth**
   - Click **"+ Add Device"** or **"Configure"**
   - Select your SFP Wizard from the discovered devices list
   - If it doesn't appear in the list:
     - Ensure your device is powered on and nearby
     - Make sure you have at least one Bluetooth proxy or adapter configured
     - The device should be advertising (check Advertisement Monitor)

3. **Verify the Device Was Added**
   - After adding, you should see a new device or entity in the Bluetooth integration
   - The device should appear with its MAC address or a generated name
   - You can rename it to something more descriptive like "SFP Wizard"

4. **Use the Addon**
   - Open the SFPLiberate addon UI
   - Click **"Discover Devices"**
   - Your SFP Wizard should now appear in the device list
   - You can select it and perform read/write operations

### Troubleshooting

**Device not discovered in addon after adding to HA:**
- Check that the device is still showing in **Settings → Devices & Services → Bluetooth**
- Verify the addon has restarted since adding the device
- Check addon logs for discovery errors

**Device not appearing in Bluetooth integration:**
- Ensure your Bluetooth proxies are online and functioning
- Check **Developer Tools → Bluetooth → Advertisement Monitor** - the device should be listed there
- Make sure the device is powered on and advertising
- Try restarting the Bluetooth integration

**Connection fails after discovery:**
- Ensure the device is in range of a Bluetooth proxy
- Check that no other apps/integrations are connected to the device
- The SFP Wizard can only maintain one connection at a time

### Alternative: Direct MAC Address Entry

If you cannot add the device through the Bluetooth integration UI, you can manually specify the MAC address when connecting:

1. Find your device's MAC address from the physical label or Advertisement Monitor
2. In the SFPLiberate addon, you can directly enter the MAC address `1C:6A:1B:05:F7:FE` when prompted
3. The addon will attempt to connect directly using that MAC address

**Note:** Direct MAC address entry bypasses device discovery and assumes the device is in range of your Bluetooth proxies.

### Future Improvements

We are investigating ways to access raw BLE advertisement data directly from Home Assistant's Bluetooth proxies without requiring manual device addition. This would allow automatic discovery of SFP Wizard devices based on their service UUID.
