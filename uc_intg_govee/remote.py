"""
Govee remote entity for Unfolded Circle integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import ucapi
from ucapi.remote import Commands, Features, States
from ucapi.ui import Buttons, Size, create_btn_mapping, create_ui_text, UiPage

from uc_intg_govee.client import GoveeClient

_LOG = logging.getLogger(__name__)


class GoveeRemote:
    """Govee remote entity with scalable SKU-based UI organization."""
    
    def __init__(self, api: ucapi.IntegrationAPI, client: GoveeClient, config: 'GoveeConfig'):
        self._api = api
        self._client = client
        self._config = config
        self._device_throttle = {}
        self._global_throttle = 0
        self._device_states = {}
        
        self._discovered_devices = self._config.devices
        _LOG.info(f"Creating remote with {len(self._discovered_devices)} discovered devices")
        
        features = [Features.ON_OFF, Features.SEND_CMD]
        simple_commands = self._generate_simple_commands()
        button_mapping = self._generate_button_mapping()
        ui_pages = self._create_scalable_ui_pages()
        
        self.entity = ucapi.Remote(
            identifier="govee_remote_main",
            name={"en": "Govee Remote"},
            features=features,
            attributes={"state": States.ON},
            simple_commands=simple_commands,
            button_mapping=button_mapping,
            ui_pages=ui_pages,
            cmd_handler=self.cmd_handler
        )
        
        _LOG.info(f"Govee remote entity created with {len(simple_commands)} commands and {len(ui_pages)} UI pages")
    
    def _generate_simple_commands(self) -> List[str]:
        commands = []
        
        if not self._discovered_devices:
            return ["NO_DEVICES"]
        
        for device_id, device_info in self._discovered_devices.items():
            device_name = device_info.get("name", f"Device_{device_id}")
            clean_name = self._clean_command_name(device_name)
            
            if device_info.get("supports_power"):
                commands.extend([f"{clean_name}_ON", f"{clean_name}_OFF", f"{clean_name}_TOGGLE"])
            
            if device_info.get("type") == "sync_box":
                if device_info.get("supports_dreamview"):
                    commands.extend([f"{clean_name}_DREAMVIEW_ON", f"{clean_name}_DREAMVIEW_OFF"])
                if device_info.get("supports_gradient"):
                    commands.extend([f"{clean_name}_GRADIENT_ON", f"{clean_name}_GRADIENT_OFF"])
                if device_info.get("supports_music"):
                    music_modes = device_info.get("music_modes", [])
                    for mode in music_modes:
                        mode_name = mode.get("name", "").upper().replace(" ", "_")
                        commands.append(f"{clean_name}_MUSIC_{mode_name}")
                    commands.extend([f"{clean_name}_SENSITIVITY_UP", f"{clean_name}_SENSITIVITY_DOWN"])
            
            if device_info.get("supports_brightness"):
                commands.extend([f"{clean_name}_BRIGHTNESS_UP", f"{clean_name}_BRIGHTNESS_DOWN", 
                               f"{clean_name}_BRIGHTNESS_25", f"{clean_name}_BRIGHTNESS_50", 
                               f"{clean_name}_BRIGHTNESS_75", f"{clean_name}_BRIGHTNESS_100"])
            
            if device_info.get("supports_color"):
                commands.extend([f"{clean_name}_COLOR_RED", f"{clean_name}_COLOR_GREEN", 
                               f"{clean_name}_COLOR_BLUE", f"{clean_name}_COLOR_WHITE",
                               f"{clean_name}_COLOR_WARM", f"{clean_name}_COLOR_COOL"])
            
            if device_info.get("supports_temperature"):
                commands.extend([f"{clean_name}_TEMP_UP", f"{clean_name}_TEMP_DOWN",
                               f"{clean_name}_TEMP_60", f"{clean_name}_TEMP_70",
                               f"{clean_name}_TEMP_80", f"{clean_name}_TEMP_90", f"{clean_name}_TEMP_100"])
            
            if device_info.get("supports_work_mode"):
                work_modes = device_info.get("work_modes", [])
                for mode in work_modes[:5]:
                    mode_name = mode.get("name", "").upper().replace(" ", "_")
                    if mode_name:
                        commands.append(f"{clean_name}_MODE_{mode_name}")
            
            if device_info.get("supports_scenes"):
                scenes = device_info.get("scenes", [])
                for scene in scenes[:10]:
                    scene_name = scene.get("name", "").upper().replace(" ", "_").replace("'", "")
                    if scene_name:
                        commands.append(f"{clean_name}_SCENE_{scene_name}")
        
        if len(self._discovered_devices) > 1:
            commands.extend(["ALL_ON", "ALL_OFF", "ALL_TOGGLE"])
        
        return sorted(list(set(commands)))
    
    def _clean_command_name(self, name: str) -> str:
        cleaned = "".join(c if c.isalnum() else "_" for c in name.upper())
        while "__" in cleaned:
            cleaned = cleaned.replace("__", "_")
        return cleaned.strip("_")
    
    def _generate_button_mapping(self) -> List[dict]:
        mappings = []
        
        if not self._discovered_devices:
            return mappings
        
        primary_device = self._find_primary_device()
        if primary_device:
            device_name = self._clean_command_name(primary_device.get("name", "Device"))
            mappings.append(create_btn_mapping(Buttons.POWER, f"{device_name}_TOGGLE"))
        
        control_device = self._find_device_with_capability("supports_brightness") or self._find_device_with_capability("supports_temperature")
        if control_device:
            device_name = self._clean_command_name(control_device.get("name", "Device"))
            if control_device.get("supports_brightness"):
                mappings.append(create_btn_mapping(Buttons.VOLUME_UP, f"{device_name}_BRIGHTNESS_UP"))
                mappings.append(create_btn_mapping(Buttons.VOLUME_DOWN, f"{device_name}_BRIGHTNESS_DOWN"))
            elif control_device.get("supports_temperature"):
                mappings.append(create_btn_mapping(Buttons.VOLUME_UP, f"{device_name}_TEMP_UP"))
                mappings.append(create_btn_mapping(Buttons.VOLUME_DOWN, f"{device_name}_TEMP_DOWN"))
        
        return mappings
    
    def _find_primary_device(self) -> Dict[str, Any]:
        priority_types = ["sync_box", "light", "kettle", "humidifier", "heater", "switch", "socket", "sensor"]
        
        for device_type in priority_types:
            for device_info in self._discovered_devices.values():
                if device_info.get("type") == device_type:
                    return device_info
        
        return next(iter(self._discovered_devices.values())) if self._discovered_devices else {}
    
    def _find_device_with_capability(self, capability: str) -> Dict[str, Any]:
        for device_info in self._discovered_devices.values():
            if device_info.get(capability, False):
                return device_info
        return {}
    
    def _create_scalable_ui_pages(self) -> List[UiPage]:
        pages = []
        
        if not self._discovered_devices:
            main_page = UiPage(page_id="main", name="No Devices", grid=Size(4, 6))
            main_page.add(create_ui_text("No devices found", 0, 0, Size(4, 1)))
            pages.append(main_page)
            return pages
        
        device_directory = self._create_device_directory_page()
        pages.append(device_directory)
        
        sku_pages = self._create_sku_control_pages()
        pages.extend(sku_pages)
        
        _LOG.info(f"Created scalable UI: 1 directory + {len(sku_pages)} SKU pages = {len(pages)} total pages")
        return pages
    
    def _create_device_directory_page(self) -> UiPage:
        directory_page = UiPage(page_id="main", name="Govee Devices", grid=Size(4, 6))
        directory_page.add(create_ui_text("Govee Devices", 0, 0, Size(4, 1)))
        
        sku_groups = self._group_devices_by_sku()
        x, y = 0, 1
        
        for sku, devices in sku_groups.items():
            if y >= 6:
                break
            
            device_type_name = self._get_sku_display_name(sku, devices)
            directory_page.add(create_ui_text(f"{device_type_name}:", 0, y, Size(4, 1)))
            y += 1
            
            for device_id, device_info in devices.items():
                if y >= 6:
                    break
                    
                device_name = device_info.get("name", f"Device {device_id}")
                display_name = device_name[:18] if len(device_name) > 18 else device_name
                directory_page.add(create_ui_text(f"â€¢ {display_name}", 0, y, Size(4, 1)))
                y += 1
            
            y += 1 if y < 6 else 0
        
        if len(self._discovered_devices) > 1 and y < 5:
            directory_page.add(create_ui_text("All On", 0, 5, Size(2, 1), "ALL_ON"))
            directory_page.add(create_ui_text("All Off", 2, 5, Size(2, 1), "ALL_OFF"))
        
        return directory_page
    
    def _group_devices_by_sku(self) -> Dict[str, Dict[str, Any]]:
        sku_groups = {}
        
        for device_id, device_info in self._discovered_devices.items():
            sku = device_info.get("sku", "Unknown")
            
            if sku not in sku_groups:
                sku_groups[sku] = {}
            
            sku_groups[sku][device_id] = device_info
        
        return sku_groups
    
    def _get_sku_display_name(self, sku: str, devices: Dict[str, Any]) -> str:
        first_device = next(iter(devices.values()))
        device_type = first_device.get("type", "")
        
        type_names = {
            "sync_box": "Sync Boxes",
            "kettle": "Kettles", 
            "light": "Lights", 
            "humidifier": "Humidifiers",
            "heater": "Heaters", 
            "switch": "Switches", 
            "socket": "Smart Plugs",
            "sensor": "Sensors", 
            "thermometer": "Thermometers"
        }
        
        friendly_name = type_names.get(device_type, "Devices")
        device_count = len(devices)
        
        if device_count > 1:
            return f"{friendly_name} ({sku}) - {device_count} devices"
        else:
            return f"{friendly_name} ({sku})"
    
    def _create_sku_control_pages(self) -> List[UiPage]:
        sku_groups = self._group_devices_by_sku()
        pages = []
        
        for sku, devices in sku_groups.items():
            page = self._create_sku_page(sku, devices)
            if page:
                pages.append(page)
        
        return pages
    
    def _create_sku_page(self, sku: str, devices: Dict[str, Any]) -> UiPage:
        page_name = self._get_sku_display_name(sku, devices)
        page_id = f"sku_{sku.replace('-', '_').lower()}"
        page = UiPage(page_id=page_id, name=page_name, grid=Size(4, 6))
        page.add(create_ui_text(page_name, 0, 0, Size(4, 1)))
        
        y = 1
        
        first_device = next(iter(devices.values()))
        if first_device.get("type") == "sync_box":
            device_id, device_info = next(iter(devices.items()))
            y = self._add_sync_box_controls(page, device_id, device_info, start_y=y)
        elif len(devices) == 1:
            device_id, device_info = next(iter(devices.items()))
            y = self._add_device_controls_to_page(page, device_id, device_info, start_y=y)
        else:
            y = self._add_multi_device_controls_to_page(page, devices, start_y=y)
        
        _LOG.info(f"Created SKU page for {sku}: {len(devices)} devices, {y} rows used")
        return page
    
    def _add_sync_box_controls(self, page: UiPage, device_id: str, device_info: Dict[str, Any], start_y: int) -> int:
        device_name = device_info.get("name", f"Device {device_id}")
        clean_name = self._clean_command_name(device_name)
        x, y = 0, start_y
        
        if device_info.get("supports_power"):
            page.add(create_ui_text("On", x, y, Size(1, 1), f"{clean_name}_ON"))
            page.add(create_ui_text("Off", x + 1, y, Size(1, 1), f"{clean_name}_OFF"))
            page.add(create_ui_text("Toggle", x + 2, y, Size(2, 1), f"{clean_name}_TOGGLE"))
            y += 1
        
        if device_info.get("supports_dreamview"):
            page.add(create_ui_text("DreamView", 0, y, Size(2, 1), f"{clean_name}_DREAMVIEW_ON"))
            page.add(create_ui_text("DV Off", 2, y, Size(2, 1), f"{clean_name}_DREAMVIEW_OFF"))
            y += 1
        
        if device_info.get("supports_gradient"):
            page.add(create_ui_text("Gradient", 0, y, Size(2, 1), f"{clean_name}_GRADIENT_ON"))
            page.add(create_ui_text("Grad Off", 2, y, Size(2, 1), f"{clean_name}_GRADIENT_OFF"))
            y += 1
        
        if device_info.get("supports_music"):
            music_modes = device_info.get("music_modes", [])
            for i, mode in enumerate(music_modes[:4]):
                if y >= 6:
                    break
                mode_name = mode.get("name", f"Mode{i+1}")
                display_name = mode_name[:7]
                cmd = f"{clean_name}_MUSIC_{mode_name.upper().replace(' ', '_')}"
                page.add(create_ui_text(display_name, i % 4, y, Size(1, 1), cmd))
            y += 1
            
            if y < 6:
                page.add(create_ui_text("Sens -", 0, y, Size(2, 1), f"{clean_name}_SENSITIVITY_DOWN"))
                page.add(create_ui_text("Sens +", 2, y, Size(2, 1), f"{clean_name}_SENSITIVITY_UP"))
                y += 1
        
        if device_info.get("supports_brightness") and y < 5:
            page.add(create_ui_text("25%", 0, y, Size(1, 1), f"{clean_name}_BRIGHTNESS_25"))
            page.add(create_ui_text("50%", 1, y, Size(1, 1), f"{clean_name}_BRIGHTNESS_50"))
            page.add(create_ui_text("75%", 2, y, Size(1, 1), f"{clean_name}_BRIGHTNESS_75"))
            page.add(create_ui_text("100%", 3, y, Size(1, 1), f"{clean_name}_BRIGHTNESS_100"))
            y += 1
        
        if device_info.get("supports_color") and y < 5:
            page.add(create_ui_text("Red", 0, y, Size(1, 1), f"{clean_name}_COLOR_RED"))
            page.add(create_ui_text("Green", 1, y, Size(1, 1), f"{clean_name}_COLOR_GREEN"))
            page.add(create_ui_text("Blue", 2, y, Size(1, 1), f"{clean_name}_COLOR_BLUE"))
            page.add(create_ui_text("White", 3, y, Size(1, 1), f"{clean_name}_COLOR_WHITE"))
            y += 1
        
        return y
    
    def _add_device_controls_to_page(self, page: UiPage, device_id: str, device_info: Dict[str, Any], start_y: int) -> int:
        device_name = device_info.get("name", f"Device {device_id}")
        clean_name = self._clean_command_name(device_name)
        x, y = 0, start_y
        
        if device_info.get("supports_power"):
            page.add(create_ui_text("On", x, y, Size(1, 1), f"{clean_name}_ON"))
            page.add(create_ui_text("Off", x + 1, y, Size(1, 1), f"{clean_name}_OFF"))
            page.add(create_ui_text("Toggle", x + 2, y, Size(2, 1), f"{clean_name}_TOGGLE"))
            y += 1
        
        if device_info.get("supports_temperature"):
            temp_range = device_info.get("temperature_range", (20, 100))
            min_temp, max_temp = temp_range
            
            if max_temp >= 100:
                temps = [60, 70, 80, 90]
                for i, temp in enumerate(temps):
                    page.add(create_ui_text(f"{temp}Â°", i, y, Size(1, 1), f"{clean_name}_TEMP_{temp}"))
                y += 1
                
                page.add(create_ui_text("Temp -", 0, y, Size(2, 1), f"{clean_name}_TEMP_DOWN"))
                page.add(create_ui_text("Temp +", 2, y, Size(2, 1), f"{clean_name}_TEMP_UP"))
                y += 1
            
            elif max_temp >= 40:
                temps = [20, 25, 30, 35]
                for i, temp in enumerate(temps):
                    page.add(create_ui_text(f"{temp}Â°", i, y, Size(1, 1), f"{clean_name}_TEMP_{temp}"))
                y += 1
        
        if device_info.get("supports_work_mode"):
            work_modes = device_info.get("work_modes", [])
            
            for i, mode in enumerate(work_modes[:4]):
                if y >= 6:
                    break
                mode_name = mode.get("name", f"Mode{i+1}")
                display_name = mode_name[:6]
                cmd = f"{clean_name}_MODE_{mode_name.upper().replace(' ', '_')}"
                
                page.add(create_ui_text(display_name, i % 4, y, Size(1, 1), cmd))
                
                if (i + 1) % 4 == 0:
                    y += 1
            
            if len(work_modes) % 4 != 0:
                y += 1
        
        elif device_info.get("supports_brightness") and y < 5:
            page.add(create_ui_text("25%", 0, y, Size(1, 1), f"{clean_name}_BRIGHTNESS_25"))
            page.add(create_ui_text("50%", 1, y, Size(1, 1), f"{clean_name}_BRIGHTNESS_50"))
            page.add(create_ui_text("75%", 2, y, Size(1, 1), f"{clean_name}_BRIGHTNESS_75"))
            page.add(create_ui_text("100%", 3, y, Size(1, 1), f"{clean_name}_BRIGHTNESS_100"))
            y += 1
            
            if y < 6:
                page.add(create_ui_text("Bright -", 0, y, Size(2, 1), f"{clean_name}_BRIGHTNESS_DOWN"))
                page.add(create_ui_text("Bright +", 2, y, Size(2, 1), f"{clean_name}_BRIGHTNESS_UP"))
                y += 1
        
        if device_info.get("supports_color") and y < 5:
            page.add(create_ui_text("Red", 0, y, Size(1, 1), f"{clean_name}_COLOR_RED"))
            page.add(create_ui_text("Green", 1, y, Size(1, 1), f"{clean_name}_COLOR_GREEN"))
            page.add(create_ui_text("Blue", 2, y, Size(1, 1), f"{clean_name}_COLOR_BLUE"))
            page.add(create_ui_text("White", 3, y, Size(1, 1), f"{clean_name}_COLOR_WHITE"))
            y += 1
            
            if y < 6:
                page.add(create_ui_text("Warm", 0, y, Size(2, 1), f"{clean_name}_COLOR_WARM"))
                page.add(create_ui_text("Cool", 2, y, Size(2, 1), f"{clean_name}_COLOR_COOL"))
                y += 1
        
        return y
    
    def _add_multi_device_controls_to_page(self, page: UiPage, devices: Dict[str, Any], start_y: int) -> int:
        x, y = 0, start_y
        
        for device_id, device_info in devices.items():
            if y >= 5:
                break
                
            device_name = device_info.get("name", f"Device {device_id}")
            clean_name = self._clean_command_name(device_name)
            
            display_name = device_name[:12] if len(device_name) > 12 else device_name
            page.add(create_ui_text(display_name, 0, y, Size(2, 1)))
            page.add(create_ui_text("Toggle", 2, y, Size(2, 1), f"{clean_name}_TOGGLE"))
            y += 1
        
        if y < 6:
            first_device = next(iter(devices.values()))
            
            if first_device.get("supports_power"):
                page.add(create_ui_text("All On", 0, 5, Size(2, 1), "ALL_ON"))
                page.add(create_ui_text("All Off", 2, 5, Size(2, 1), "ALL_OFF"))
        
        return y
    
    async def push_initial_state(self):
        _LOG.info("Setting initial remote entity state")
        
        if not self._api.configured_entities.contains(self.entity.id):
            _LOG.warning(f"Entity {self.entity.id} not in configured entities yet")
            return
        
        initial_state = States.ON
        initial_attributes = {"state": initial_state}
        self._api.configured_entities.update_attributes(self.entity.id, initial_attributes)
        _LOG.info(f"Initial state set successfully - remote entity is {initial_state}")

    async def _get_device_state(self, device_id: str) -> bool:
        try:
            device_info = self._discovered_devices.get(device_id)
            if not device_info:
                return False
        
            from uc_intg_govee.client import GoveeDevice
        
            device_data = {
                "sku": device_info.get("sku", ""),
                "device": device_id,
                "deviceName": device_info.get("name", ""),
                "type": device_info.get("api_type", ""),
                "capabilities": device_info.get("capabilities", [])
            }
        
            device = GoveeDevice(device_data)
            state_data = await self._client.get_device_state(device)
        
            if state_data and 'capabilities' in state_data:
                for capability in state_data['capabilities']:
                    if capability.get('type') == 'devices.capabilities.on_off' and capability.get('instance') == 'powerSwitch':
                        value = capability.get('state', {}).get('value', 0)
                        is_on = bool(value)
                        self._device_states[device_id] = is_on
                        _LOG.debug(f"Device {device_id} state from API: {is_on}")
                        return is_on
        
            cached_state = self._device_states.get(device_id, False)
            _LOG.debug(f"Device {device_id} using cached state: {cached_state}")
            return cached_state
        
        except Exception as e:
            _LOG.warning(f"Failed to get state for device {device_id}: {e}")
            return self._device_states.get(device_id, False)
        
    async def _check_throttle(self, device_id: str) -> bool:
        import time
        
        current_time = time.time()
        
        if current_time - self._global_throttle < 0.1:
            return False
        
        last_time = self._device_throttle.get(device_id, 0)
        if current_time - last_time < 0.3:
            return False
        
        self._global_throttle = current_time
        self._device_throttle[device_id] = current_time
        return True

    async def cmd_handler(self, entity: ucapi.Entity, cmd_id: str, params: dict[str, Any] | None) -> ucapi.StatusCodes:
        _LOG.info("Remote command: %s %s", cmd_id, params)
        
        if not self._client or not self._client.is_configured():
            return ucapi.StatusCodes.SERVICE_UNAVAILABLE
        
        try:
            if cmd_id == Commands.ON:
                return await self._handle_on()
            elif cmd_id == Commands.OFF:
                return await self._handle_off()
            elif cmd_id == Commands.SEND_CMD:
                return await self._handle_send_cmd(params)
            else:
                return ucapi.StatusCodes.NOT_IMPLEMENTED
                
        except Exception as e:
            _LOG.error("Error handling remote command %s: %s", cmd_id, e, exc_info=True)
            return ucapi.StatusCodes.SERVER_ERROR
    
    async def _handle_on(self) -> ucapi.StatusCodes:
        self._api.configured_entities.update_attributes(self.entity.id, {"state": States.ON})
        return ucapi.StatusCodes.OK
    
    async def _handle_off(self) -> ucapi.StatusCodes:
        self._api.configured_entities.update_attributes(self.entity.id, {"state": States.OFF})
        return ucapi.StatusCodes.OK
    
    async def _handle_send_cmd(self, params: dict[str, Any] | None) -> ucapi.StatusCodes:
        if not params or "command" not in params:
            return ucapi.StatusCodes.BAD_REQUEST
        
        command = params["command"]
        success = await self._execute_govee_command(command)
        return ucapi.StatusCodes.OK if success else ucapi.StatusCodes.SERVER_ERROR
    
    async def _execute_govee_command(self, command: str) -> bool:
        try:
            if not self._discovered_devices or command == "NO_DEVICES":
                return False
            
            if command.startswith("ALL_"):
                return await self._execute_global_command(command)
            
            return await self._execute_device_command(command)
            
        except Exception as e:
            _LOG.error(f"Error executing Govee command {command}: {e}")
            return False
    
    async def _execute_global_command(self, command: str) -> bool:
        tasks = []
        
        for device_id, device_info in self._discovered_devices.items():
            if device_info.get("supports_power", True):
                if command == "ALL_ON":
                    task = self._execute_device_action_safe(device_id, "turn_on", device_info.get('name'))
                elif command == "ALL_OFF":
                    task = self._execute_device_action_safe(device_id, "turn_off", device_info.get('name'))
                elif command == "ALL_TOGGLE":
                    task = self._execute_device_action_safe(device_id, "toggle", device_info.get('name'))
                else:
                    continue
                tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for result in results if result is True)
            return success_count > 0
        
        return False
    
    async def _execute_device_action_safe(self, device_id: str, action: str, device_name: str) -> bool:
        try:
            if not await self._check_throttle(device_id):
                return True
            
            device_info = self._discovered_devices.get(device_id)
            if not device_info:
                return False
            
            from uc_intg_govee.client import GoveeDevice
            
            device_data = {
                "sku": device_info.get("sku", ""),
                "device": device_id,
                "deviceName": device_name,
                "type": device_info.get("api_type", ""),
                "capabilities": device_info.get("capabilities", [])
            }
            
            device = GoveeDevice(device_data)
            
            if action == "turn_on":
                result = await self._client.turn_on(device)
                if result:
                    self._device_states[device_id] = True
                return result
            elif action == "turn_off":
                result = await self._client.turn_off(device)
                if result:
                    self._device_states[device_id] = False
                return result
            elif action == "toggle":
                # OPTIMIZED: Use cached state instead of slow API query
                cached_state = self._device_states.get(device_id, False)
                _LOG.info(f"Toggle for {device_name}: cached state is {'ON' if cached_state else 'OFF'}, will turn {'OFF' if cached_state else 'ON'}")
                
                if cached_state:
                    # Currently ON -> Turn OFF
                    result = await self._client.turn_off(device)
                    if result:
                        self._device_states[device_id] = False
                        _LOG.info(f"Toggled {device_name} OFF")
                else:
                    # Currently OFF -> Turn ON  
                    result = await self._client.turn_on(device)
                    if result:
                        self._device_states[device_id] = True
                        _LOG.info(f"Toggled {device_name} ON")
                
                return result
            else:
                return False
                
        except Exception as e:
            _LOG.error(f"Error executing {action} on device {device_name}: {e}")
            return False
    
    async def _execute_device_command(self, command: str) -> bool:
        for device_id, device_info in self._discovered_devices.items():
            device_name = device_info.get("name", f"Device_{device_id}")
            device_prefix = self._clean_command_name(device_name)
            
            if command.startswith(device_prefix + "_"):
                if not await self._check_throttle(device_id):
                    return True
                
                action_part = command[len(device_prefix)+1:]
                govee_action_result = self._map_ui_action_to_govee_action(action_part, device_info)
                
                if govee_action_result:
                    try:
                        from uc_intg_govee.client import GoveeDevice
                        
                        device_data = {
                            "sku": device_info.get("sku", ""),
                            "device": device_id,
                            "deviceName": device_name,
                            "type": device_info.get("api_type", ""),
                            "capabilities": device_info.get("capabilities", [])
                        }
                        
                        device = GoveeDevice(device_data)
                        return await self._execute_mapped_action(device, govee_action_result, device_info, device_id)
                        
                    except Exception as e:
                        _LOG.error(f"Exception executing action on device {device_name}: {e}")
                        return False
                
                return False
        
        return False
    
    async def _execute_mapped_action(self, device: 'GoveeDevice', action: str, device_info: Dict[str, Any], device_id: str = None) -> bool:
        try:
            if action == "turn_on":
                result = await self._client.turn_on(device)
                if result and device_id:
                    self._device_states[device_id] = True
                return result
            elif action == "turn_off":
                result = await self._client.turn_off(device)
                if result and device_id:
                    self._device_states[device_id] = False
                return result
            elif action == "toggle":
                if device_id:
                    # OPTIMIZED: Use cached state instead of slow API query
                    # Toggle based on last known state (inverted logic for toggle)
                    cached_state = self._device_states.get(device_id, False)
                    _LOG.info(f"Toggle for {device.device_name}: cached state is {'ON' if cached_state else 'OFF'}, will turn {'OFF' if cached_state else 'ON'}")
                    
                    if cached_state:
                        # Currently ON -> Turn OFF
                        result = await self._client.turn_off(device)
                        if result:
                            self._device_states[device_id] = False
                            _LOG.info(f"Toggled {device.device_name} OFF")
                    else:
                        # Currently OFF -> Turn ON
                        result = await self._client.turn_on(device)
                        if result:
                            self._device_states[device_id] = True
                            _LOG.info(f"Toggled {device.device_name} ON")
                    
                    return result
                else:
                    return await self._client.turn_on(device)
            elif action == "dreamview_on":
                return await self._client.set_dreamview(device, True)
            elif action == "dreamview_off":
                return await self._client.set_dreamview(device, False)
            elif action == "gradient_on":
                return await self._client.set_gradient(device, True)
            elif action == "gradient_off":
                return await self._client.set_gradient(device, False)
            elif action.startswith("music_"):
                mode_name = action.replace("music_", "").replace("_", " ").title()
                music_modes = device_info.get("music_modes", [])
                for mode in music_modes:
                    if mode.get("name", "").lower() == mode_name.lower():
                        return await self._client.set_music_mode(device, mode.get("value", 1), 50)
                return False
            elif action == "sensitivity_up":
                return await self._client.set_music_mode(device, 1, 75)
            elif action == "sensitivity_down":
                return await self._client.set_music_mode(device, 1, 25)
            elif action.startswith("brightness_"):
                if "up" in action:
                    brightness = 100
                elif "down" in action:
                    brightness = 20
                else:
                    parts = action.split("_")
                    brightness = 50
                    for part in parts:
                        if part.isdigit():
                            brightness = int(part)
                            break
                return await self._client.set_brightness(device, brightness)
            elif action.startswith("color_"):
                color_map = {
                    "red": 16711680, "green": 65280, "blue": 255, "white": 16777215,
                    "warm": 16753920, "cool": 11593983
                }
                color_name = action.replace("color_", "")
                rgb_value = color_map.get(color_name, 16777215)
                return await self._client.set_color_rgb(device, rgb_value)
            elif action.startswith("temp_"):
                if "up" in action:
                    temp_range = device_info.get("temperature_range", (20, 100))
                    temperature = min(temp_range[1], 90)
                elif "down" in action:
                    temp_range = device_info.get("temperature_range", (20, 100))
                    temperature = max(temp_range[0], 40)
                else:
                    parts = action.split("_")
                    temperature = 80
                    for part in parts:
                        if part.isdigit():
                            temperature = int(part)
                            break
                return await self._client.set_temperature(device, temperature)
            elif action.startswith("mode_"):
                mode_name = action.replace("mode_", "").replace("_", " ").title()
                work_modes = device_info.get("work_modes", [])
                
                for mode in work_modes:
                    if mode.get("name", "").lower() == mode_name.lower():
                        return await self._client.set_work_mode(device, mode.get("instance", ""), mode.get("value", 1))
                
                kettle_mode_map = {"diy": 1, "tea": 2, "coffee": 3, "boiling": 4}
                mode_value = kettle_mode_map.get(mode_name.lower())
                if mode_value:
                    return await self._client.set_work_mode(device, "workMode", mode_value)
                    
                return False
            elif action.startswith("scene_"):
                scene_name = action.replace("scene_", "").replace("_", " ").title()
                scenes = device_info.get("scenes", [])
                for scene in scenes:
                    if scene.get("name", "").lower() == scene_name.lower():
                        return await self._client.set_scene(device, scene.get("instance", ""), scene.get("value", 1))
                return False
            else:
                return False
                
        except Exception as e:
            _LOG.error(f"Error executing mapped action {action}: {e}")
            return False

    def _map_ui_action_to_govee_action(self, ui_action: str, device_info: Dict[str, Any]) -> Optional[str]:
        if ui_action == "ON":
            return "turn_on" if device_info.get("supports_power") else None
        elif ui_action == "OFF":
            return "turn_off" if device_info.get("supports_power") else None
        elif ui_action == "TOGGLE":
            return "toggle" if device_info.get("supports_power") else None
        elif ui_action == "DREAMVIEW_ON":
            return "dreamview_on" if device_info.get("supports_dreamview") else None
        elif ui_action == "DREAMVIEW_OFF":
            return "dreamview_off" if device_info.get("supports_dreamview") else None
        elif ui_action == "GRADIENT_ON":
            return "gradient_on" if device_info.get("supports_gradient") else None
        elif ui_action == "GRADIENT_OFF":
            return "gradient_off" if device_info.get("supports_gradient") else None
        elif ui_action.startswith("MUSIC_"):
            return ui_action.lower() if device_info.get("supports_music") else None
        elif ui_action in ["SENSITIVITY_UP", "SENSITIVITY_DOWN"]:
            return ui_action.lower() if device_info.get("supports_music") else None
        elif ui_action.startswith("BRIGHTNESS_"):
            if not device_info.get("supports_brightness"):
                return None
            
            if ui_action == "BRIGHTNESS_UP":
                return "brightness_up"
            elif ui_action == "BRIGHTNESS_DOWN":
                return "brightness_down"
            elif ui_action in ["BRIGHTNESS_25", "BRIGHTNESS_50", "BRIGHTNESS_75", "BRIGHTNESS_100"]:
                return ui_action.lower()
        elif ui_action.startswith("COLOR_"):
            if not device_info.get("supports_color"):
                return None
            return ui_action.lower()
        elif ui_action.startswith("TEMP_"):
            if not device_info.get("supports_temperature"):
                return None
            
            if ui_action == "TEMP_UP":
                return "temp_up"
            elif ui_action == "TEMP_DOWN":
                return "temp_down"
            else:
                return ui_action.lower()
        elif ui_action.startswith("MODE_"):
            if not device_info.get("supports_work_mode"):
                return None
            return ui_action.lower()
        elif ui_action.startswith("SCENE_"):
            if not device_info.get("supports_scenes"):
                return None
            return ui_action.lower()
        
        return None