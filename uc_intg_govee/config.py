"""
Configuration management for Govee integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import json
import logging
from typing import Any, Dict, Optional

_LOG = logging.getLogger(__name__)


class GoveeConfig:
    """Configuration management for Govee integration."""
    
    def __init__(self, config_file_path: str):
        self._config_file_path = config_file_path
        self._config_data: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        try:
            with open(self._config_file_path, 'r', encoding='utf-8') as f:
                self._config_data = json.load(f)
            _LOG.debug("Configuration loaded successfully")
        except FileNotFoundError:
            _LOG.debug("Configuration file not found, starting with empty config")
            self._config_data = {}
        except json.JSONDecodeError as e:
            _LOG.error("Error parsing configuration file: %s", e)
            self._config_data = {}
        except Exception as e:
            _LOG.error("Error loading configuration: %s", e)
            self._config_data = {}
    
    def _save_config(self) -> bool:
        try:
            with open(self._config_file_path, 'w', encoding='utf-8') as f:
                json.dump(self._config_data, f, indent=2, ensure_ascii=False)
            _LOG.debug("Configuration saved successfully")
            return True
        except Exception as e:
            _LOG.error("Error saving configuration: %s", e)
            return False
    
    def is_configured(self) -> bool:
        api_key = self.api_key
        return api_key is not None and api_key.strip() != ""
    
    @property
    def api_key(self) -> Optional[str]:
        return self._config_data.get("api_key")

    @api_key.setter
    def api_key(self, value: str) -> None:
        self._config_data["api_key"] = value.strip()
        self._save_config()

    @property
    def devices(self) -> Dict[str, Any]:
        return self._config_data.get("devices", {})

    @devices.setter
    def devices(self, value: Dict[str, Any]) -> None:
        self._config_data["devices"] = value
        self._save_config()

    def get_device_config(self, device_id: str) -> Dict[str, Any]:
        return self.devices.get(device_id, {})

    def set_device_config(self, device_id: str, config: Dict[str, Any]) -> None:
        devices = self.devices.copy()
        devices[device_id] = config
        self.devices = devices

    def get_polling_interval(self) -> int:
        return self._config_data.get("polling_interval", 30)
    
    def set_polling_interval(self, interval: int) -> bool:
        try:
            self._config_data["polling_interval"] = max(10, min(300, interval))
            return self._save_config()
        except Exception as e:
            _LOG.error("Error setting polling interval: %s", e)
            return False

    def get_all_config(self) -> Dict[str, Any]:
        safe_config = self._config_data.copy()
        if "api_key" in safe_config:
            safe_config["api_key"] = "***HIDDEN***"
        return safe_config

    def clear(self) -> None:
        self._config_data = {}
        self._save_config()

    def save(self) -> None:
        self._save_config()