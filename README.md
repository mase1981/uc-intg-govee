# Govee Smart Home Integration for Unfolded Circle Remote Two/3

[![GitHub Release](https://img.shields.io/github/release/mase1981/uc-intg-govee.svg)](https://github.com/mase1981/uc-intg-govee/releases)
[![GitHub License](https://img.shields.io/github/license/mase1981/uc-intg-govee.svg)](https://github.com/mase1981/uc-intg-govee/blob/main/LICENSE)

Transform your Unfolded Circle Remote Two/3 into a powerful Govee smart home command center. Control all your Govee devices with intelligent organization, dynamic UI generation, and comprehensive device support.

**NOTE:** This integration requires a Govee Developer API Key (free) obtained through the Govee Home app.

## 🏠 Features

### Universal Device Support
- **Smart Lights**: RGB control, brightness, color temperature, dynamic scenes
- **Smart Kettles**: Temperature control (40-100°C), work modes (DIY, Tea, Coffee, Boiling)
- **Smart Plugs/Switches**: Power control and status monitoring
- **Environmental Devices**: Sensors, thermometers, air purifiers, humidifiers
- **Appliances**: Heaters, aroma diffusers, ice makers, dehumidifiers

### Intelligent Remote Interface
- **Scalable UI Architecture**: Adapts from 1 device to 1000+ devices elegantly
- **SKU-Based Organization**: Groups devices by model for clean interface
- **Dynamic Page Generation**: Creates appropriate controls based on actual device capabilities
- **Device Directory**: Overview page with organized device listing
- **Control Pages**: Dedicated pages per device type with full controls

### Advanced Features
- **Automatic Device Discovery**: Finds all your Govee devices via Cloud API
- **Dynamic Entity Creation**: Creates entities based on actual device capabilities (no hardcoding)
- **Rate Limiting Protection**: Respects Govee API limits with intelligent throttling
- **Real-time Control**: Instant device response with comprehensive error handling
- **Physical Button Mapping**: Remote Two/3 hardware buttons mapped to device controls

## 📋 Prerequisites

### Hardware Requirements
- **Govee Smart Devices**: Any Govee devices with API support
- **Remote Two/3**: Unfolded Circle Remote Two/3
- **Network**: Both devices connected to internet
- **Govee Account**: Active account with devices configured in Govee Home app

### Software Requirements

#### Required Setup
1. **Govee Home App** (Mobile)
   - Download: iOS App Store / Google Play Store
   - Required: All devices must be working in Govee Home app first

2. **Govee Developer API Key** (Free)
   - Source: Govee Home app → Profile → Settings → Apply for API Key
   - Limitations: One key per account

#### Network Requirements
- **Internet Access**: Both Remote and Govee Cloud API
- **Stable Connection**: Reliable internet for real-time control
- **No Port Forwarding**: Uses secure HTTPS to Govee Cloud
- **No Local Network Setup**: Devices communicate through Govee Cloud (To be able to control all devices, not just lights)

## 🚀 Quick Start

### Step 1: Prepare Your Govee Account

#### Setup Govee Devices
1. **Download Govee Home App** on your smartphone
2. **Create Account** and log in
3. **Add All Devices** to your Govee account following app instructions
4. **Test Functionality**: Ensure all devices work properly in the app
5. **Note Device Names**: Remember names for easier identification in Remote

#### Obtain API Key
1. **Open Govee Home App**
2. **Navigate to Profile**:
   - Tap profile icon (👤) at bottom right
   - Tap settings icon (⚙️) at top right
3. **Apply for API Key**:
   - Select "Apply for API Key"
   - **Name**: Your name
   - **Reason**: "Smart home automation integration" or "Third-party remote control"
4. **Accept Terms**: Read and accept Developer API Terms
5. **Submit Application**: Click "Submit"
6. **Receive API Key**: Check email (usually arrives within minutes)

**⚠️ Important Notes**:
- **One key per account**: Each new application invalidates previous keys
- **Store securely**: You'll need this key during integration setup
- **Don't share**: Keep your API key private

### Step 2: Install Integration on Remote

#### Via Remote Two/3 Web Interface
1. **Access Web Configurator**
   ```
   http://YOUR_REMOTE_IP/configurator
   ```

2. **Install Integration**
   - Navigate to: **Integrations** → **Add New** / **Install Custom**
   - Upload: **uc-intg-govee-***.tar.gz
   - Click: **Upload**

3. **Configure Integration**
   - Enter your **Govee API Key** when prompted
   - Click: **Continue**
   - Wait for automatic device discovery (~6 seconds)
   - Complete setup

4. **Add Entity**
   - **Govee Remote** (Remote Entity) - for comprehensive device control
   - Add to your desired activities

## 🎮 Using the Integration

### Scalable Remote Interface

The integration creates an intelligent remote interface that automatically adapts to your devices:

#### Single Device Setup:
- **Page 1**: "Govee Devices" - Device overview
- **Page 2**: "Device Controls" - Full control interface for your device

#### Multiple Device Setup:
- **Page 1**: "Govee Devices" - Device directory organized by SKU
- **Page 2+**: SKU-specific control pages (e.g., "Kettles (H7173)", "Lights (H6601)")

#### Example Layouts:

**5 Devices, 3 SKUs**:
```
Page 1: Device Directory
Page 2: Kettles (H7173) - 2 devices
Page 3: Lights (H6601) - 2 devices  
Page 4: Plugs (H5085) - 1 device
```

**50 Devices, 8 SKUs**:
```
Page 1: Device Directory (overview)
Page 2: Kettles (H7173) - 12 devices
Page 3: Living Room Lights (H6601) - 8 devices
Page 4: Bedroom Lights (H6159) - 6 devices
Page 5: Smart Plugs (H5085) - 10 devices
Page 6: Outdoor Lights (H7021) - 4 devices
Page 7: Sensors (H5179) - 6 devices
Page 8: Humidifiers (H7141) - 2 devices
Page 9: Air Purifiers (H7122) - 2 devices
```

### Device Controls by Type

#### Smart Kettle Controls:
- **Power**: On/Off/Toggle buttons
- **Temperature Presets**: 60°, 70°, 80°, 90°, 100° quick select
- **Work Modes**: DIY, Tea, Coffee, Boiling
- **Fine Control**: Temp +/- buttons for precise adjustment

#### Smart Light Controls:
- **Power**: On/Off/Toggle buttons
- **Brightness Presets**: 25%, 50%, 75%, 100% quick select
- **Color Presets**: Red, Green, Blue, White, Warm, Cool
- **Fine Control**: Brightness +/- buttons
- **Scenes**: Dynamic scenes based on device capabilities

#### Smart Plug/Switch Controls:
- **Power**: On/Off/Toggle buttons
- **Status Display**: Real-time state indication
- **Group Control**: "All On/Off" for multiple devices

#### Environmental Device Controls:
- **Power**: On/Off/Toggle for controllable devices
- **Work Modes**: Multiple modes based on device type
- **Speed/Intensity**: Variable control where supported

### Global Controls

#### Multi-Device Commands:
- **ALL_ON**: Turn on all compatible devices
- **ALL_OFF**: Turn off all compatible devices  
- **ALL_TOGGLE**: Toggle all compatible devices

#### Physical Remote Buttons:
The integration maps physical Remote Two/3 buttons:
- **Power Button**: Toggle primary device (prioritized by device type)
- **Volume Up/Down**: 
  - Brightness control (for lights)
  - Temperature control (for kettles/heaters)


## 🔧 Configuration

### Integration Settings

Located at: `config.json` in integration directory

```json
{
  "api_key": "your_govee_api_key_here",
  "devices": {
    "device_id_1": {
      "sku": "H7173",
      "name": "Kitchen Kettle",
      "type": "kettle",
      "supports_temperature": true,
      "supports_work_mode": true,
      "temperature_range": [40, 100],
      "work_modes": [
        {"name": "DIY", "value": 1},
        {"name": "Tea", "value": 2},
        {"name": "Coffee", "value": 3},
        {"name": "Boiling", "value": 4}
      ]
    },
    "device_id_2": {
      "sku": "H6601",
      "name": "Living Room Light",
      "type": "light",
      "supports_brightness": true,
      "supports_color": true,
      "brightness_range": [1, 100],
      "scenes": [
        {"name": "Party", "value": 1},
        {"name": "Romance", "value": 2}
      ]
    }
  }
}
```

### Environment Variables (Optional)

| Variable | Description | Default |
|----------|-------------|---------|
| `UC_INTEGRATION_HTTP_PORT` | Integration HTTP port | `9090` |
| `UC_INTEGRATION_INTERFACE` | Bind interface | `0.0.0.0` |
| `UC_CONFIG_HOME` | Configuration directory | `./` |

### Rate Limiting Settings

The integration includes built-in API protection:
- **Rate Limit**: 10 requests per minute
- **Global Throttle**: 100ms between any commands
- **Device Throttle**: 300ms between commands to same device
- **Retry Logic**: Automatic retry for temporary failures

## 🛠️ Troubleshooting

### Setup Issues

**Problem**: Integration setup fails with "Invalid API Key"

**Solutions**:
1. **Verify API Key**:
   - Copy key exactly from Govee email
   - No extra spaces or characters
   - Key should be 32+ characters long
2. **Generate New Key**:
   - Each application invalidates previous keys
   - Apply for new key if needed
3. **Check Account Status**:
   - Ensure Govee account is active
   - Verify devices work in Govee Home app

**Problem**: "No Devices Found" during setup

**Solutions**:
1. **Verify Device Compatibility**:
   - Ensure devices support Govee API
   - Check devices work in Govee Home app
   - Some older devices lack API support
2. **Check Account Setup**:
   - All devices must be added to your Govee account
   - Devices must be online and responsive
3. **API Permissions**:
   - Ensure API key has device access permissions
   - Some devices may require specific API access

**Problem**: Setup takes too long or times out

**Solutions**:
1. **Check Internet Connection**:
   - Verify Remote has internet access
   - Test: `ping api.govee.com`
2. **Firewall/Network**:
   - Ensure HTTPS (port 443) is allowed
   - Check corporate/school network restrictions
3. **API Service Status**:
   - Verify Govee API is operational
   - Check Govee's status page or forums

### Runtime Issues

**Problem**: Device commands not working

**Solutions**:
1. **Check Device Status**:
   - Verify devices are online in Govee Home app
   - Test manual control through app
2. **API Rate Limits**:
   - Integration includes rate limiting
   - Wait if "Rate Limit Exceeded" appears
3. **Network Connectivity**:
   - Ensure stable internet connection
   - Check if other integrations work
4. **Device Capability**:
   - Some commands may not be supported by specific devices
   - Check device manual for supported features

**Problem**: "Connection Error" displayed

**Solutions**:
1. **Internet Connectivity**:
   ```bash
   # Test internet connection
   ping google.com
   ping api.govee.com
   ```
2. **API Key Status**:
   - Verify API key hasn't been revoked
   - Check if new key was generated
3. **Service Status**:
   - Check Govee Cloud API status
   - Verify other cloud services work
4. **Restart Integration**:
   - Restart Remote Two/3
   - Re-install integration if persistent

**Problem**: Some devices missing from interface

**Solutions**:
1. **Device Compatibility**:
   - Not all Govee devices support the API
   - Check device manual for API support
2. **Account Sync**:
   - Ensure all devices are in your Govee account
   - Try removing and re-adding device to account
3. **Reconfigure Integration**:
   - Delete and re-setup integration
   - New devices will be discovered
4. **API Limitations**:
   - Some device types may have limited API access
   - Check Govee documentation for device support

### Debug Information

**Check Integration Logs**:
```bash
# Via web configurator
http://YOUR_REMOTE_IP/configurator → settings → development → Logs → choose Govee logs
```

**Test API Access**:
```bash
# Test API connectivity
curl -H "Govee-API-Key: YOUR_API_KEY" \
  "https://openapi.api.govee.com/router/api/v1/user/devices"

# Expected: JSON response with device list
```

**Verify Device Response**:
```bash
# Test device control (replace with your details)
curl -X POST "https://openapi.api.govee.com/router/api/v1/device/control" \
  -H "Govee-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "requestId": "test_request",
    "payload": {
      "sku": "H7173",
      "device": "your_device_id",
      "capability": {
        "type": "devices.capabilities.on_off",
        "instance": "powerSwitch",
        "value": 1
      }
    }
  }'
```

### Common Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| "Invalid API Key" | Authentication failed | Verify API key correctness |
| "Rate Limit Exceeded" | Too many requests | Wait 1 minute, built-in throttling will resume |
| "Device Not Found" | Device not in account | Add device to Govee Home app |
| "Connection Refused" | Network/Internet issue | Check internet connectivity |
| "Capability Not Supported" | Device limitation | Check device manual for supported features |

## 🗃️ Advanced Setup

### API Key Management

**Security Best Practices**:
- Store API key securely
- Don't share API key publicly
- Generate new key if compromised
- Use only on trusted networks

**Multiple Accounts**:
- Each Govee account needs separate API key
- Can't combine devices from multiple accounts
- Consider using primary account for all devices

### Device Organization Tips

**Naming Strategy**:
```bash
# Use descriptive names in Govee Home app
"Living Room Main Light"     # Better than "Light 1"
"Kitchen Smart Kettle"       # Better than "Kettle"
"Bedroom Reading Light"      # Better than "Desk Light"
```

**Grouping Strategy**:
- Group by room in Govee Home app
- Similar device types get organized automatically by integration
- Use consistent naming for easier voice control

### Performance Optimization

**Network Optimization**:
- Use stable, high-speed internet connection
- Consider QoS prioritization for smart home traffic
- Monitor for network congestion during peak usage

**Device Management**:
- Keep device firmware updated through Govee Home app
- Regularly test device responsiveness
- Remove unused devices from account

## 🤝 Contributing

### Development Setup

```bash
# Clone repository
git clone https://github.com/mase1981/uc-intg-govee.git
cd uc-intg-govee

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Testing

```bash
# Run integration directly
python -m uc_intg_govee.driver

# Test with debug logging
UC_INTEGRATION_HTTP_PORT=9090 python uc_intg_govee/driver.py

# Test specific functionality
python -c "
from uc_intg_govee.client import GoveeClient
import asyncio

async def test():
    client = GoveeClient('YOUR_API_KEY')
    devices = await client.get_devices()
    print(f'Found {len(devices)} devices')

asyncio.run(test())
"
```

### Building Release Package

```bash
# Create distribution package
tar -czf uc-intg-govee-v1.0.0.tar.gz \
  --exclude-vcs \
  --exclude='.github' \
  --exclude='tests' \
  --exclude='*.pyc' \
  --exclude='__pycache__' \
  --exclude='dist' \
  --exclude='build' \
  .
```

### Code Structure

```
uc_intg_govee/
├── __init__.py          # Package initialization
├── client.py            # Govee API client with rate limiting
├── config.py            # Configuration management
├── driver.py            # Main integration driver
├── remote.py            # Scalable remote entity with SKU-based UI
└── setup.py             # Integration setup flow with device discovery
```

## 📄 License

This project is licensed under the MPL-2.0 License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Community Resources

- **GitHub Issues**: [Report bugs and request features](https://github.com/mase1981/uc-intg-govee/issues)
- **UC Community Forum**: [General discussion and support](https://unfolded.community/)
- **Govee Support**: [Official Govee device support](https://govee.com/support)



### Frequently Asked Questions

**Q: How many devices can the integration handle?**
A: The integration scales from 1 to 1000+ devices with intelligent UI organization.

**Q: Do I need to pay for the Govee API?**
A: No, the Govee Developer API is free for personal use.

**Q: Can I control devices when away from home?**
A: Yes, as long as your Remote Two/3 has internet access and devices are online.

**Q: What happens if my internet goes down?**
A: Device control requires internet connectivity. Local device states are maintained when possible.

**Q: Can I use multiple Govee accounts?**
A: Each integration instance supports one Govee account. Use the account with all your devices.

---

**Made with ❤️ for the Unfolded Circle Community**

**Author**: Meir Miyara