"""
Govee API client implementation.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
import ssl
from typing import Any, Dict, List, Optional

import aiohttp
from asyncio_throttle import Throttler

_LOG = logging.getLogger(__name__)


class GoveeAPIError(Exception):
    """Custom exception for Govee API errors."""

    def __init__(self, message: str, code: int = None) -> None:
        super().__init__(message)
        self.code = code


class GoveeDevice:
    """Represents a Govee device with its capabilities."""

    def __init__(self, data: Dict[str, Any]) -> None:
        self.sku = data.get("sku", "")
        self.device_id = data.get("device", "")
        self.device_name = data.get("deviceName", f"Govee {self.sku}")
        self.capabilities = data.get("capabilities", [])
        
        self.api_type = data.get("type", "")
        
        # FIX: Set all capability attributes BEFORE determining device type
        # _determine_device_type() depends on these attributes being set first
        # Previously this caused AttributeError: 'GoveeDevice' object has no attribute 'supports_color'
        self.supports_power = self._has_capability("devices.capabilities.on_off")
        self.supports_brightness = self._has_capability("devices.capabilities.range", "brightness")
        self.supports_color = self._has_capability("devices.capabilities.color_setting", "colorRgb")
        self.supports_color_temp = self._has_capability("devices.capabilities.color_setting", "colorTemperatureK")
        self.supports_scenes = self._has_capability("devices.capabilities.dynamic_scene")
        self.supports_music = self._has_capability("devices.capabilities.music_setting")
        self.supports_temperature = self._has_capability("devices.capabilities.temperature_setting") or self._has_capability("devices.capabilities.range", "temperature")
        self.supports_work_mode = self._has_capability("devices.capabilities.work_mode")
        self.supports_timer = self._has_capability("devices.capabilities.timer")
        self.supports_humidity = self._has_capability("devices.capabilities.range", "humidity")
        self.supports_fan_mode = self._has_capability("devices.capabilities.work_mode", "fanMode")
        self.supports_gradient = self._has_capability("devices.capabilities.toggle", "gradientToggle")
        self.supports_dreamview = self._has_capability("devices.capabilities.toggle", "dreamViewToggle")
        self.supports_segmented = self._has_capability("devices.capabilities.segment_color_setting")
        
        # NOW determine device type after all capabilities are set
        self.device_type = self._determine_device_type()

    def _determine_device_type(self) -> str:
        if self.sku in ["H6603", "H6604", "H8604"]:
            return "sync_box"
        
        if self.api_type:
            type_mapping = {
                "devices.types.light": "light",
                "devices.types.switch": "switch", 
                "devices.types.socket": "socket",
                "devices.types.kettle": "kettle",
                "devices.types.humidifier": "humidifier",
                "devices.types.air_purifier": "air_purifier",
                "devices.types.heater": "heater",
                "devices.types.thermometer": "thermometer",
                "devices.types.air_quality_monitor": "sensor",
                "devices.types.fan": "fan",
                "devices.types.dehumidifier": "dehumidifier",
                "devices.types.ice_maker": "ice_maker",
                "devices.types.aroma_diffuser": "aroma_diffuser"
            }
            mapped_type = type_mapping.get(self.api_type)
            if mapped_type:
                _LOG.debug(f"Device type from API: {self.api_type} -> {mapped_type}")
                return mapped_type
        
        if self.supports_color or self.supports_brightness:
            return "light"
        elif self.supports_work_mode or self.supports_temperature:
            return "appliance"
        elif self.supports_power:
            return "switch"
        else:
            return "sensor"

    def _has_capability(self, capability_type: str, instance: Optional[str] = None) -> bool:
        for cap in self.capabilities:
            if cap.get("type") == capability_type:
                if instance is None or cap.get("instance") == instance:
                    return True
        return False

    def get_capability(self, capability_type: str, instance: str) -> Optional[Dict[str, Any]]:
        for cap in self.capabilities:
            if cap.get("type") == capability_type and cap.get("instance") == instance:
                return cap
        return None

    def get_brightness_range(self) -> tuple[int, int]:
        cap = self.get_capability("devices.capabilities.range", "brightness")
        if cap and "parameters" in cap:
            range_info = cap["parameters"].get("range", {})
            return (range_info.get("min", 1), range_info.get("max", 100))
        return (1, 100)

    def get_color_temp_range(self) -> tuple[int, int]:
        cap = self.get_capability("devices.capabilities.color_setting", "colorTemperatureK")
        if cap and "parameters" in cap:
            range_info = cap["parameters"].get("range", {})
            return (range_info.get("min", 2000), range_info.get("max", 9000))
        return (2000, 9000)

    def get_temperature_range(self) -> tuple[int, int]:
        cap = self.get_capability("devices.capabilities.temperature_setting", "sliderTemperature")
        if cap and "parameters" in cap and "fields" in cap["parameters"]:
            for field in cap["parameters"]["fields"]:
                if field.get("fieldName") == "temperature" and "range" in field:
                    range_info = field["range"]
                    return (range_info.get("min", 20), range_info.get("max", 100))
        
        cap = self.get_capability("devices.capabilities.range", "temperature")
        if cap and "parameters" in cap:
            range_info = cap["parameters"].get("range", {})
            return (range_info.get("min", 20), range_info.get("max", 100))
        
        return (20, 100)

    def get_work_modes(self) -> List[Dict[str, Any]]:
        modes = []
        for cap in self.capabilities:
            if cap.get("type") == "devices.capabilities.work_mode":
                params = cap.get("parameters", {})
                if "fields" in params:
                    for field in params["fields"]:
                        if field.get("fieldName") == "workMode" and "options" in field:
                            for option in field["options"]:
                                modes.append({
                                    "instance": cap.get("instance", ""),
                                    "name": option.get("name"),
                                    "value": option.get("value")
                                })
        return modes

    def get_music_modes(self) -> List[Dict[str, Any]]:
        modes = []
        cap = self.get_capability("devices.capabilities.music_setting", "musicMode")
        if cap and "parameters" in cap and "fields" in cap["parameters"]:
            for field in cap["parameters"]["fields"]:
                if field.get("fieldName") == "musicMode" and "options" in field:
                    for option in field["options"]:
                        modes.append({
                            "name": option.get("name"),
                            "value": option.get("value")
                        })
        return modes

    def get_scene_options(self) -> List[Dict[str, Any]]:
        scenes = []
        for cap in self.capabilities:
            if cap.get("type") == "devices.capabilities.dynamic_scene":
                params = cap.get("parameters", {})
                if "options" in params:
                    instance = cap.get("instance", "")
                    for option in params["options"]:
                        scenes.append({
                            "instance": instance,
                            "name": option.get("name"),
                            "value": option.get("value")
                        })
        return scenes

    def get_all_capabilities_summary(self) -> Dict[str, Any]:
        return {
            "device_type": self.device_type,
            "api_type": self.api_type,
            "supports_power": self.supports_power,
            "supports_brightness": self.supports_brightness,
            "supports_color": self.supports_color,
            "supports_color_temp": self.supports_color_temp,
            "supports_scenes": self.supports_scenes,
            "supports_music": self.supports_music,
            "supports_temperature": self.supports_temperature,
            "supports_work_mode": self.supports_work_mode,
            "supports_timer": self.supports_timer,
            "supports_humidity": self.supports_humidity,
            "supports_fan_mode": self.supports_fan_mode,
            "supports_gradient": self.supports_gradient,
            "supports_dreamview": self.supports_dreamview,
            "supports_segmented": self.supports_segmented,
            "brightness_range": self.get_brightness_range() if self.supports_brightness else None,
            "color_temp_range": self.get_color_temp_range() if self.supports_color_temp else None,
            "temperature_range": self.get_temperature_range() if self.supports_temperature else None,
            "work_modes": self.get_work_modes(),
            "music_modes": self.get_music_modes(),
            "scenes": self.get_scene_options()
        }

    def __str__(self) -> str:
        return f"GoveeDevice(sku={self.sku}, device_id={self.device_id}, name={self.device_name}, type={self.device_type}, api_type={self.api_type})"


class GoveeClient:
    """Govee API client with rate limiting and error handling."""

    BASE_URL = "https://openapi.api.govee.com"
    
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self._api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        
        self.throttler = Throttler(rate_limit=10, period=60)
        
        self._headers = {
            "Content-Type": "application/json",
            "Govee-API-Key": self.api_key
        }
        
        self._config = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    async def connect(self) -> None:
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
        if self.session:
            await self.session.close()
            self.session = None

    def is_configured(self) -> bool:
        return self._api_key is not None and self._api_key.strip() != ""

    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.session:
            await self.connect()

        url = f"{self.BASE_URL}{endpoint}"
        
        async with self.throttler:
            try:
                async with self.session.request(method, url, json=data) as response:
                    response_data = await response.json()
                    
                    if response.status == 200:
                        if response_data.get("code") == 200:
                            return response_data
                        else:
                            raise GoveeAPIError(
                                f"API error: {response_data.get('message', 'Unknown error')}",
                                response_data.get("code")
                            )
                    elif response.status == 401:
                        raise GoveeAPIError("Unauthorized - check your API key", 401)
                    elif response.status == 429:
                        raise GoveeAPIError("Rate limit exceeded - too many requests", 429)
                    else:
                        raise GoveeAPIError(f"HTTP {response.status}: {response_data}", response.status)
                        
            except ssl.SSLError as e:
                _LOG.error(f"SSL Error connecting to Govee API: {e}")
                await self._reconnect_with_fallback_ssl()
                try:
                    async with self.session.request(method, url, json=data) as response:
                        response_data = await response.json()
                        
                        if response.status == 200 and response_data.get("code") == 200:
                            return response_data
                        else:
                            raise GoveeAPIError(f"API error after SSL fallback: {response_data.get('message', 'Unknown error')}")
                            
                except Exception as retry_e:
                    raise GoveeAPIError(f"SSL connection failed even with fallback: {str(retry_e)}")
                    
            except aiohttp.ClientError as e:
                raise GoveeAPIError(f"Network error: {str(e)}")
            except Exception as e:
                raise GoveeAPIError(f"Unexpected error: {str(e)}")

    async def _reconnect_with_fallback_ssl(self) -> None:
        if self.session:
            await self.session.close()
            
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        _LOG.warning("Using fallback SSL settings due to certificate verification issues")
        
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

    async def get_devices(self) -> List[GoveeDevice]:
        _LOG.info("Fetching devices from Govee API")
        
        try:
            response = await self._make_request("GET", "/router/api/v1/user/devices")
            devices_data = response.get("data", [])
            
            devices = []
            for device_data in devices_data:
                device = GoveeDevice(device_data)
                devices.append(device)
                _LOG.debug(f"Found device: {device}")
                _LOG.debug(f"Device capabilities: {device.get_all_capabilities_summary()}")
            
            _LOG.info(f"Successfully discovered {len(devices)} Govee devices")
            return devices
            
        except GoveeAPIError as e:
            _LOG.error(f"Failed to get devices: {e}")
            raise
        except Exception as e:
            _LOG.error(f"Unexpected error getting devices: {e}")
            raise GoveeAPIError(f"Failed to get devices: {str(e)}")

    async def get_device_state(self, device: GoveeDevice) -> Dict[str, Any]:
        _LOG.debug(f"Getting state for device: {device.device_id}")
        
        try:
            params = {
                "sku": device.sku,
                "device": device.device_id
            }
            
            response = await self._make_request("GET", "/router/api/v1/device/state", params)
            return response.get("data", {})
            
        except GoveeAPIError as e:
            _LOG.error(f"Failed to get device state for {device.device_id}: {e}")
            raise
        except Exception as e:
            _LOG.error(f"Unexpected error getting device state: {e}")
            raise GoveeAPIError(f"Failed to get device state: {str(e)}")

    async def control_device(self, device: GoveeDevice, capability_type: str, instance: str, value: Any) -> bool:
        _LOG.debug(f"Controlling device {device.device_id}: {capability_type}.{instance} = {value}")
        
        try:
            command_data = {
                "requestId": "uc_integration_request",
                "payload": {
                    "sku": device.sku,
                    "device": device.device_id,
                    "capability": {
                        "type": capability_type,
                        "instance": instance,
                        "value": value
                    }
                }
            }
            
            _LOG.debug(f"Sending command: {command_data}")
            await self._make_request("POST", "/router/api/v1/device/control", command_data)
            _LOG.debug(f"Successfully sent command to {device.device_id}")
            return True
            
        except GoveeAPIError as e:
            _LOG.error(f"Failed to control device {device.device_id}: {e}")
            return False
        except Exception as e:
            _LOG.error(f"Unexpected error controlling device: {e}")
            return False

    async def turn_on(self, device: GoveeDevice) -> bool:
        return await self.control_device(device, "devices.capabilities.on_off", "powerSwitch", 1)

    async def turn_off(self, device: GoveeDevice) -> bool:
        return await self.control_device(device, "devices.capabilities.on_off", "powerSwitch", 0)

    async def set_brightness(self, device: GoveeDevice, brightness: int) -> bool:
        min_val, max_val = device.get_brightness_range()
        brightness = max(min_val, min(max_val, brightness))
        return await self.control_device(device, "devices.capabilities.range", "brightness", brightness)

    async def set_color_rgb(self, device: GoveeDevice, rgb: int) -> bool:
        rgb = max(0, min(16777215, rgb))
        return await self.control_device(device, "devices.capabilities.color_setting", "colorRgb", rgb)

    async def set_color_temperature(self, device: GoveeDevice, kelvin: int) -> bool:
        min_val, max_val = device.get_color_temp_range()
        kelvin = max(min_val, min(max_val, kelvin))
        return await self.control_device(device, "devices.capabilities.color_setting", "colorTemperatureK", kelvin)

    async def set_temperature(self, device: GoveeDevice, temperature: int) -> bool:
        min_val, max_val = device.get_temperature_range()
        temperature = max(min_val, min(max_val, temperature))
        
        return await self.control_device(
            device, 
            "devices.capabilities.temperature_setting", 
            "sliderTemperature", 
            {"temperature": temperature, "unit": "Celsius"}
        )

    async def set_work_mode(self, device: GoveeDevice, instance: str, mode_value: int) -> bool:
        return await self.control_device(device, "devices.capabilities.work_mode", instance, {"workMode": mode_value})

    async def set_scene(self, device: GoveeDevice, instance: str, scene_value: int) -> bool:
        return await self.control_device(device, "devices.capabilities.dynamic_scene", instance, scene_value)

    async def set_gradient(self, device: GoveeDevice, enabled: bool) -> bool:
        return await self.control_device(device, "devices.capabilities.toggle", "gradientToggle", 1 if enabled else 0)

    async def set_dreamview(self, device: GoveeDevice, enabled: bool) -> bool:
        return await self.control_device(device, "devices.capabilities.toggle", "dreamViewToggle", 1 if enabled else 0)

    async def set_music_mode(self, device: GoveeDevice, mode: int, sensitivity: int) -> bool:
        return await self.control_device(
            device,
            "devices.capabilities.music_setting",
            "musicMode",
            {"musicMode": mode, "sensitivity": sensitivity, "autoColor": 1}
        )

    async def test_connection(self) -> bool:
        try:
            response = await self._make_request("GET", "/router/api/v1/user/devices")
            return True
        except GoveeAPIError as e:
            _LOG.error(f"Connection test failed: {e}")
            return False
        except Exception as e:
            _LOG.error(f"Unexpected error in connection test: {e}")
            return False