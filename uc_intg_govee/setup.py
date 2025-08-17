"""
Setup flow for Govee integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any, Dict, Callable, Coroutine

import ucapi.api_definitions as uc
from uc_intg_govee.client import GoveeClient, GoveeAPIError
from uc_intg_govee.config import GoveeConfig

_LOG = logging.getLogger(__name__)


class GoveeSetup:
    """Setup handler for Govee integration."""

    def __init__(self, config: GoveeConfig, client: GoveeClient, setup_complete_callback: Callable[[], Coroutine[Any, Any, None]]):
        self.config = config
        self.client = client
        self._setup_complete_callback = setup_complete_callback

    async def setup_handler(self, msg: uc.SetupDriver) -> uc.SetupAction:
        _LOG.info("Setup handler called with: %s", type(msg).__name__)

        if isinstance(msg, uc.DriverSetupRequest):
            return await self._handle_driver_setup_request(msg)
        elif isinstance(msg, uc.UserDataResponse):
            return await self._handle_user_data_response(msg)
        elif isinstance(msg, uc.UserConfirmationResponse):
            return await self._handle_user_confirmation_response(msg)
        elif isinstance(msg, uc.AbortDriverSetup):
            return await self._handle_abort_setup(msg)
        
        return uc.SetupError(uc.IntegrationSetupError.OTHER)

    async def _handle_driver_setup_request(self, msg: uc.DriverSetupRequest) -> uc.SetupAction:
        _LOG.debug("Handling driver setup request.")

        if self.config.is_configured() and not msg.reconfigure:
            _LOG.info("Already configured, checking if working...")
            
            if await self._test_existing_config():
                _LOG.info("Existing configuration works, proceeding to completion")
                await self._setup_complete_callback()
                return uc.SetupComplete()
            else:
                _LOG.warning("Existing configuration failed - need to reconfigure")

        if msg.setup_data:
            api_key = msg.setup_data.get("api_key", "").strip()
            
            if api_key:
                _LOG.info("API key provided, testing connection...")
                return await self._test_govee_connection(api_key)
            else:
                _LOG.error("No API key provided in setup data")
                return uc.SetupError(uc.IntegrationSetupError.OTHER)
        
        _LOG.warning("No setup data provided")
        return uc.SetupError(uc.IntegrationSetupError.OTHER)

    async def _test_existing_config(self) -> bool:
        try:
            if not self.config.api_key:
                return False
            
            self.client._api_key = self.config.api_key
            self.client._headers["Govee-API-Key"] = self.config.api_key
            
            return await self.client.test_connection()
        except Exception as e:
            _LOG.error(f"Error testing existing config: {e}")
            return False

    async def _test_govee_connection(self, api_key: str) -> uc.SetupAction:
        _LOG.info("Testing connection to Govee API")

        try:
            self.client._api_key = api_key
            self.client._headers["Govee-API-Key"] = api_key

            if not await self.client.test_connection():
                _LOG.error("Failed to connect to Govee API")
                return uc.SetupError(uc.IntegrationSetupError.CONNECTION_REFUSED)

            _LOG.info("Discovering user's Govee devices...")
            devices = await self.client.get_devices()
            
            if not devices:
                _LOG.warning("No devices found in user's Govee account")
                self.config.api_key = api_key
                self.config.devices = {}
                self.config.save()
                
                await self._setup_complete_callback()
                return uc.SetupComplete()

            return await self._discover_and_complete_setup(api_key, devices)

        except GoveeAPIError as e:
            _LOG.error(f"Govee API error during setup: {e}")
            if e.code == 401:
                return uc.SetupError(uc.IntegrationSetupError.AUTHORIZATION_ERROR)
            elif e.code == 429:
                return uc.SetupError(uc.IntegrationSetupError.OTHER)
            else:
                return uc.SetupError(uc.IntegrationSetupError.CONNECTION_REFUSED)
        
        except Exception as e:
            _LOG.error(f"Unexpected error during setup: {e}")
            return uc.SetupError(uc.IntegrationSetupError.OTHER)

    async def _discover_and_complete_setup(self, api_key: str, devices: list) -> uc.SetupAction:
        try:
            device_count = len(devices)
            _LOG.info(f"Discovered {device_count} Govee devices")

            discovered_devices = {}
            for device in devices:
                device_id = device.device_id
                
                capabilities_summary = device.get_all_capabilities_summary()
                
                discovered_devices[device_id] = {
                    "name": device.device_name,
                    "type": device.device_type,
                    "api_type": device.api_type,
                    "sku": device.sku,
                    "capabilities": device.capabilities,
                    "supports_power": capabilities_summary["supports_power"],
                    "supports_brightness": capabilities_summary["supports_brightness"],
                    "supports_color": capabilities_summary["supports_color"],
                    "supports_color_temp": capabilities_summary["supports_color_temp"],
                    "supports_scenes": capabilities_summary["supports_scenes"],
                    "supports_music": capabilities_summary["supports_music"],
                    "supports_temperature": capabilities_summary["supports_temperature"],
                    "supports_work_mode": capabilities_summary["supports_work_mode"],
                    "supports_timer": capabilities_summary["supports_timer"],
                    "supports_humidity": capabilities_summary["supports_humidity"],
                    "supports_fan_mode": capabilities_summary["supports_fan_mode"],
                    "brightness_range": capabilities_summary["brightness_range"],
                    "color_temp_range": capabilities_summary["color_temp_range"],
                    "temperature_range": capabilities_summary["temperature_range"],
                    "work_modes": capabilities_summary["work_modes"],
                    "scenes": capabilities_summary["scenes"]
                }
                
                _LOG.info(f"Device: {device.device_name} ({device.device_type}/{device.api_type}) - SKU: {device.sku}")
                _LOG.debug(f"  Capabilities: Power={capabilities_summary['supports_power']}, "
                          f"Brightness={capabilities_summary['supports_brightness']}, "
                          f"Color={capabilities_summary['supports_color']}, "
                          f"Temperature={capabilities_summary['supports_temperature']}, "
                          f"WorkMode={capabilities_summary['supports_work_mode']}")

            self.config.api_key = api_key
            self.config.devices = discovered_devices
            self.config.save()
            
            _LOG.info(f"Saved {len(discovered_devices)} devices to configuration")
            _LOG.info("Successfully connected to Govee API and discovered devices")
            
            await self._setup_complete_callback()
            return uc.SetupComplete()

        except Exception as e:
            _LOG.error(f"Error during device discovery: {e}")
            return uc.SetupError(uc.IntegrationSetupError.OTHER)

    async def _handle_user_data_response(self, msg: uc.UserDataResponse) -> uc.SetupAction:
        _LOG.debug("Handling user data response")
        
        api_key = msg.input_values.get("api_key", "").strip()
        
        if api_key:
            return await self._test_govee_connection(api_key)
        else:
            _LOG.error("No API key provided")
            return uc.SetupError(uc.IntegrationSetupError.OTHER)

    async def _handle_user_confirmation_response(self, msg: uc.UserConfirmationResponse) -> uc.SetupAction:
        _LOG.debug(f"Handling user confirmation response: {msg.confirm}")
        
        if msg.confirm:
            _LOG.info("User confirmed, completing setup")
            return uc.SetupComplete()
        else:
            _LOG.info("User cancelled confirmation")
            return uc.SetupError(uc.IntegrationSetupError.OTHER)

    async def _handle_abort_setup(self, msg: uc.AbortDriverSetup) -> uc.SetupAction:
        _LOG.info(f"Setup aborted: {msg.error}")
        self.config.clear()
        return uc.SetupError(msg.error)