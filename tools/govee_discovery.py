#!/usr/bin/env python3
"""
Govee API Device Discovery Script
----------------------------------
Standalone script to query Govee API and extract all device capabilities.

Usage:
    python govee_api_discovery.py

Requirements:
    pip install aiohttp

Author: Generated for Govee Integration Enhancement
Date: October 2025
"""

import asyncio
import json
import ssl
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import aiohttp
except ImportError:
    print("ERROR: aiohttp is not installed.")
    print("Please install it using: pip install aiohttp")
    exit(1)


class GoveeAPIDiscovery:
    """Govee API discovery tool to extract device capabilities."""

    BASE_URL = "https://openapi.api.govee.com"
    
    def __init__(self, api_key: str):
        self.api_key = api_key.strip()
        self.session: Optional[aiohttp.ClientSession] = None
        self._headers = {
            "Content-Type": "application/json",
            "Govee-API-Key": self.api_key
        }

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    async def connect(self) -> None:
        """Initialize aiohttp session with SSL context."""
        if self.session is None:
            ssl_context = ssl.create_default_context()
            connector = aiohttp.TCPConnector(
                ssl=ssl_context,
                ttl_dns_cache=300,
                use_dns_cache=True,
            )
            
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self.session = aiohttp.ClientSession(
                headers=self._headers,
                timeout=timeout,
                connector=connector
            )

    async def disconnect(self) -> None:
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None

    async def _make_request(self, method: str, endpoint: str) -> Dict[str, Any]:
        """Make HTTP request to Govee API."""
        if not self.session:
            await self.connect()

        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            async with self.session.request(method, url) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    if response_data.get("code") == 200:
                        return response_data
                    else:
                        error_msg = response_data.get('message', 'Unknown error')
                        raise Exception(f"API error: {error_msg} (code: {response_data.get('code')})")
                elif response.status == 401:
                    raise Exception("Unauthorized - Invalid API key")
                elif response.status == 429:
                    raise Exception("Rate limit exceeded - Too many requests")
                else:
                    raise Exception(f"HTTP {response.status}: {response_data}")
                    
        except aiohttp.ClientError as e:
            raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")

    async def test_connection(self) -> bool:
        """Test API connection."""
        try:
            response = await self._make_request("GET", "/router/api/v1/user/devices")
            return True
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False

    async def get_all_devices(self) -> List[Dict[str, Any]]:
        """Fetch all devices from Govee API."""
        print("\n🔍 Fetching devices from Govee API...")
        
        try:
            response = await self._make_request("GET", "/router/api/v1/user/devices")
            devices_data = response.get("data", [])
            
            print(f"✅ Successfully discovered {len(devices_data)} device(s)")
            return devices_data
            
        except Exception as e:
            print(f"❌ Failed to fetch devices: {e}")
            raise

    async def get_device_state(self, sku: str, device_id: str) -> Dict[str, Any]:
        """Get current state of a device."""
        try:
            # Note: This endpoint may not work for all devices
            # Govee API has limitations on state queries
            endpoint = f"/router/api/v1/device/state?sku={sku}&device={device_id}"
            response = await self._make_request("GET", endpoint)
            return response.get("data", {})
        except Exception as e:
            # State query might fail for some devices - this is normal
            return {"error": str(e), "note": "State query not supported for this device"}

    def analyze_device(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze device capabilities and structure."""
        sku = device_data.get("sku", "Unknown")
        device_id = device_data.get("device", "Unknown")
        device_name = device_data.get("deviceName", f"Govee {sku}")
        api_type = device_data.get("type", "Unknown")
        capabilities = device_data.get("capabilities", [])
        
        # Analyze capabilities
        capability_summary = {
            "power_control": False,
            "brightness_control": False,
            "color_control": False,
            "color_temperature": False,
            "temperature_setting": False,
            "work_modes": [],
            "dynamic_scenes": [],
            "music_setting": False,
            "timer_support": False,
            "range_controls": [],
            "custom_capabilities": []
        }
        
        for cap in capabilities:
            cap_type = cap.get("type", "")
            cap_instance = cap.get("instance", "")
            cap_params = cap.get("parameters", {})
            
            # Power control
            if cap_type == "devices.capabilities.on_off":
                capability_summary["power_control"] = True
            
            # Brightness
            elif cap_type == "devices.capabilities.range" and cap_instance == "brightness":
                capability_summary["brightness_control"] = True
                capability_summary["range_controls"].append({
                    "type": "brightness",
                    "range": cap_params.get("range", {}),
                    "unit": cap_params.get("unit", "")
                })
            
            # Color RGB
            elif cap_type == "devices.capabilities.color_setting" and cap_instance == "colorRgb":
                capability_summary["color_control"] = True
            
            # Color Temperature
            elif cap_type == "devices.capabilities.color_setting" and cap_instance == "colorTemperatureK":
                capability_summary["color_temperature"] = True
                capability_summary["range_controls"].append({
                    "type": "color_temperature",
                    "range": cap_params.get("range", {}),
                    "unit": "Kelvin"
                })
            
            # Temperature setting
            elif cap_type == "devices.capabilities.temperature_setting":
                capability_summary["temperature_setting"] = True
                if "fields" in cap_params:
                    for field in cap_params["fields"]:
                        if field.get("fieldName") == "temperature":
                            capability_summary["range_controls"].append({
                                "type": "temperature",
                                "range": field.get("range", {}),
                                "unit": "Celsius"
                            })
            
            # Work modes
            elif cap_type == "devices.capabilities.work_mode":
                if "fields" in cap_params:
                    for field in cap_params["fields"]:
                        if field.get("fieldName") == "workMode" and "options" in field:
                            for option in field["options"]:
                                capability_summary["work_modes"].append({
                                    "instance": cap_instance,
                                    "name": option.get("name"),
                                    "value": option.get("value")
                                })
            
            # Dynamic scenes
            elif cap_type == "devices.capabilities.dynamic_scene":
                if "options" in cap_params:
                    for option in cap_params["options"]:
                        capability_summary["dynamic_scenes"].append({
                            "instance": cap_instance,
                            "name": option.get("name"),
                            "value": option.get("value")
                        })
            
            # Music setting
            elif cap_type == "devices.capabilities.music_setting":
                capability_summary["music_setting"] = True
            
            # Timer
            elif cap_type == "devices.capabilities.timer":
                capability_summary["timer_support"] = True
            
            # Range controls (generic)
            elif cap_type == "devices.capabilities.range":
                capability_summary["range_controls"].append({
                    "type": cap_instance,
                    "range": cap_params.get("range", {}),
                    "unit": cap_params.get("unit", "")
                })
            
            # Custom/Unknown capabilities
            else:
                capability_summary["custom_capabilities"].append({
                    "type": cap_type,
                    "instance": cap_instance,
                    "parameters": cap_params
                })
        
        return {
            "sku": sku,
            "device_id": device_id,
            "device_name": device_name,
            "api_type": api_type,
            "raw_capabilities": capabilities,
            "capability_summary": capability_summary
        }

    async def discover_and_analyze(self) -> Dict[str, Any]:
        """Main discovery and analysis function."""
        print("\n" + "="*70)
        print("🔧 GOVEE API DEVICE DISCOVERY TOOL")
        print("="*70)
        
        # Test connection
        print("\n📡 Testing API connection...")
        if not await self.test_connection():
            raise Exception("Failed to connect to Govee API")
        print("✅ API connection successful")
        
        # Get all devices
        devices_data = await self.get_all_devices()
        
        if not devices_data:
            print("\n⚠️  No devices found in your Govee account")
            return {
                "timestamp": datetime.now().isoformat(),
                "total_devices": 0,
                "devices": []
            }
        
        # Analyze each device
        print("\n📊 Analyzing device capabilities...")
        analyzed_devices = []
        
        for idx, device_data in enumerate(devices_data, 1):
            device_name = device_data.get("deviceName", "Unknown")
            sku = device_data.get("sku", "Unknown")
            
            print(f"\n  [{idx}/{len(devices_data)}] {device_name} (SKU: {sku})")
            
            # Analyze device
            analysis = self.analyze_device(device_data)
            
            # Try to get device state (may fail for some devices)
            print(f"      Querying device state...", end=" ")
            state = await self.get_device_state(sku, device_data.get("device", ""))
            if "error" not in state:
                analysis["current_state"] = state
                print("✅")
            else:
                analysis["current_state"] = None
                print("⚠️  (not available)")
            
            analyzed_devices.append(analysis)
            
            # Print capability summary
            cap_summary = analysis["capability_summary"]
            print(f"      Capabilities:")
            print(f"        • Power: {cap_summary['power_control']}")
            print(f"        • Brightness: {cap_summary['brightness_control']}")
            print(f"        • Color: {cap_summary['color_control']}")
            print(f"        • Work Modes: {len(cap_summary['work_modes'])}")
            print(f"        • Scenes: {len(cap_summary['dynamic_scenes'])}")
            print(f"        • Custom: {len(cap_summary['custom_capabilities'])}")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "api_key_prefix": f"{self.api_key[:8]}...",
            "total_devices": len(analyzed_devices),
            "devices": analyzed_devices
        }


def print_banner():
    """Print welcome banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║        GOVEE API DEVICE DISCOVERY & ANALYSIS TOOL             ║
║                                                               ║
║  Purpose: Extract complete device capabilities for           ║
║           integration enhancement                            ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_instructions():
    """Print usage instructions."""
    instructions = """
📋 INSTRUCTIONS:
--------------
1. This script will query your Govee account via the API
2. It will discover all your devices and their capabilities
3. Results will be saved to 'govee_discovery_output.json'
4. Share this JSON file for integration enhancement

⚠️  IMPORTANT:
   • Your API key is stored ONLY in this script execution
   • No data is sent anywhere except Govee's official API
   • The output JSON can be safely shared (device IDs are included but not sensitive)
   • Keep your API key private - never share it publicly
"""
    print(instructions)


def get_api_key() -> str:
    """Prompt user for API key."""
    print("\n🔑 Please enter your Govee API Key:")
    print("   (Get it from Govee Home App → Profile → Settings → Apply for API Key)")
    print()
    api_key = input("   API Key: ").strip()
    
    if not api_key:
        print("\n❌ Error: API key cannot be empty")
        exit(1)
    
    if len(api_key) < 20:
        print("\n⚠️  Warning: API key seems too short. Please verify.")
        confirm = input("   Continue anyway? (y/N): ").strip().lower()
        if confirm != 'y':
            exit(1)
    
    return api_key


def save_results(results: Dict[str, Any], filename: str = "govee_discovery_output.json"):
    """Save results to JSON file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Results saved to: {filename}")
        print(f"   File size: {len(json.dumps(results, indent=2)) / 1024:.2f} KB")
        return True
    except Exception as e:
        print(f"\n❌ Failed to save results: {e}")
        return False


def print_summary(results: Dict[str, Any]):
    """Print discovery summary."""
    print("\n" + "="*70)
    print("📊 DISCOVERY SUMMARY")
    print("="*70)
    
    total = results.get("total_devices", 0)
    print(f"\n✅ Total devices discovered: {total}")
    
    if total > 0:
        print("\n📦 Devices by SKU:")
        sku_count = {}
        for device in results.get("devices", []):
            sku = device.get("sku", "Unknown")
            sku_count[sku] = sku_count.get(sku, 0) + 1
        
        for sku, count in sorted(sku_count.items()):
            print(f"   • {sku}: {count} device(s)")
        
        print("\n🔍 Special Device Types Found:")
        special_types = set()
        for device in results.get("devices", []):
            api_type = device.get("api_type", "")
            if "sync" in api_type.lower() or "hdmi" in api_type.lower():
                special_types.add(api_type)
        
        if special_types:
            for device_type in special_types:
                print(f"   • {device_type}")
        else:
            print("   • No special device types (sync boxes, etc.)")
    
    print("\n" + "="*70)


async def main():
    """Main entry point."""
    print_banner()
    print_instructions()
    
    # Get API key from user
    api_key = get_api_key()
    
    # Run discovery
    try:
        async with GoveeAPIDiscovery(api_key) as discovery:
            results = await discovery.discover_and_analyze()
        
        # Save results
        if save_results(results):
            print_summary(results)
            
            print("\n✅ SUCCESS!")
            print("   You can now share 'govee_discovery_output.json' for analysis")
            print("\n💡 Next Steps:")
            print("   1. Review the JSON output file")
            print("   2. Share it with the integration developer")
            print("   3. Wait for integration enhancement")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Discovery cancelled by user")
        exit(0)
    
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        print("\n🔧 Troubleshooting:")
        print("   • Verify your API key is correct")
        print("   • Check your internet connection")
        print("   • Ensure Govee API is accessible")
        print("   • Try again in a few minutes (rate limiting)")
        exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n\n💥 Fatal error: {e}")
        exit(1)