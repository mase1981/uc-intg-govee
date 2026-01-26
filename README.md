# Govee Smart Home Integration for Unfolded Circle Remote Two/3

[![Discord](https://badgen.net/discord/online-members/zGVYf58)](https://discord.gg/zGVYf58)
![GitHub Release](https://img.shields.io/github/v/release/mase1981/uc-intg-govee)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/mase1981/uc-intg-govee/total)
![License](https://img.shields.io/badge/license-MPL--2.0-blue)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA)](https://github.com/sponsors/mase1981/button)


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


## Credits

- **Developer**: Meir Miyara
- **Govee**: Smart home device platform and API
- **Unfolded Circle**: Remote 2/3 integration framework (ucapi)
- **Community**: Testing and feedback from UC community

## License

This project is licensed under the Mozilla Public License 2.0 (MPL-2.0) - see LICENSE file for details.

## Support & Community

- **GitHub Issues**: [Report bugs and request features](https://github.com/mase1981/uc-intg-govee/issues)
- **UC Community Forum**: [General discussion and support](https://unfolded.community/)
- **Developer**: [Meir Miyara](https://www.linkedin.com/in/meirmiyara)
- **Govee Support**: [Official Govee Support](https://govee.com/support)

---

**Made with ❤️ for the Unfolded Circle Community**

**Thank You**: Meir Miyara
