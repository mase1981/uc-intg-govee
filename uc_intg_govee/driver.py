#!/usr/bin/env python3
"""
Govee integration driver for Unfolded Circle Remote.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""
import asyncio
import logging
import os
import signal
from typing import Optional

import ucapi

from uc_intg_govee.client import GoveeClient
from uc_intg_govee.config import GoveeConfig
from uc_intg_govee.remote import GoveeRemote
from uc_intg_govee.setup import GoveeSetup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)8s | %(name)s | %(message)s"
)
logging.getLogger("aiohttp").setLevel(logging.WARNING)

_LOG = logging.getLogger(__name__)

loop = asyncio.get_event_loop()
api: Optional[ucapi.IntegrationAPI] = None
govee_client: Optional[GoveeClient] = None
govee_config: Optional[GoveeConfig] = None
remote: Optional[GoveeRemote] = None

async def create_entities_from_config():
    global remote, entities_initialized
    
    async with initialization_lock:
        if entities_initialized:
            _LOG.debug("Entities already initialized, skipping duplicate creation")
            return
        
        if not govee_config or not govee_config.is_configured():
            _LOG.debug("Integration not configured, skipping entity creation")
            return
        
        discovered_devices = govee_config.devices
        if not discovered_devices:
            _LOG.warning("No devices found in configuration")
            return
        
        try:
            _LOG.info(f"PRE-CREATING entities for {len(discovered_devices)} devices to prevent race condition")
            
            for device_id, device_info in discovered_devices.items():
                _LOG.debug(f"Device {device_id}: {device_info.get('name')} ({device_info.get('type')}) - SKU: {device_info.get('sku')}")
            
            # Create remote entity IMMEDIATELY - don't wait for connection test
            remote = GoveeRemote(api, govee_client, govee_config)
            api.available_entities.add(remote.entity)
            _LOG.info(f"Pre-created remote entity: {remote.entity.id}")
            
            # Mark entities as initialized BEFORE setting state
            entities_initialized = True
            _LOG.info("Entities initialized and ready for subscription")
            
        except Exception as e:
            _LOG.error(f"Error pre-creating entities: {e}", exc_info=True)
            entities_initialized = False

async def verify_and_set_connection_state():
    """Verify Govee API connection and set appropriate device state.
    
    This runs AFTER entities are created to update connection status.
    Uses retry logic to handle network timing issues during boot.
    """
    if not govee_config or not govee_config.is_configured():
        _LOG.warning("Integration is not configured")
        await api.set_device_state(ucapi.DeviceStates.ERROR)
        return
    
    govee_client._api_key = govee_config.api_key
    govee_client._headers["Govee-API-Key"] = govee_config.api_key
    
    # Retry logic for connection verification
    max_retries = 5
    retry_delays = [2, 4, 8, 16, 32]
    connection_successful = False
    
    for attempt in range(max_retries):
        if attempt > 0:
            delay = retry_delays[attempt - 1]
            _LOG.warning(f"Connection attempt {attempt + 1}/{max_retries} - waiting {delay}s for network stabilization...")
            await asyncio.sleep(delay)
        else:
            _LOG.info(f"Connection attempt {attempt + 1}/{max_retries}")
        
        try:
            if await govee_client.test_connection():
                _LOG.info(f"Govee connection successful on attempt {attempt + 1}/{max_retries}")
                connection_successful = True
                break
            else:
                _LOG.warning(f"Govee connection failed on attempt {attempt + 1}/{max_retries}")
                
        except Exception as e:
            _LOG.warning(f"Connection attempt {attempt + 1}/{max_retries} raised exception: {e}")
    
    # Set device state based on connection result
    if connection_successful:
        _LOG.info("Govee API connection verified. Setting state to CONNECTED.")
        await api.set_device_state(ucapi.DeviceStates.CONNECTED)
    else:
        _LOG.error(f"Cannot connect to Govee API after {max_retries} attempts")
        _LOG.error("Entities are available but connection to Govee API failed")
        await api.set_device_state(ucapi.DeviceStates.ERROR)

async def on_setup_complete():
    """Callback executed when driver setup is complete.
    
    This is called after INITIAL setup (not on reboot).
    For reboots, entities are pre-created in main() to avoid race conditions.
    """
    global entities_initialized
    
    _LOG.info("Setup complete. Creating entities...")
    
    if not api or not govee_client:
        _LOG.error("Cannot create entities: API or client not initialized.")
        await api.set_device_state(ucapi.DeviceStates.ERROR)
        return
    
    # Use the same entity creation logic
    await create_entities_from_config()
    
    if entities_initialized:
        # Verify connection after entities are created
        await verify_and_set_connection_state()
    else:
        await api.set_device_state(ucapi.DeviceStates.ERROR)

async def on_r2_connect():
    """Handle Remote connection."""
    global entities_initialized
    
    _LOG.info("Remote connected.")
    
    # Ensure entities are created before UC Remote tries to use them
    if govee_config and govee_config.is_configured():
        if not entities_initialized:
            _LOG.warning("RACE CONDITION DETECTED: Remote connected before entities initialized!")
            await create_entities_from_config()
        
        # Verify connection if entities are ready
        if entities_initialized and govee_client:
            if await govee_client.test_connection():
                _LOG.info("Govee connection verified. Setting state to CONNECTED.")
                await api.set_device_state(ucapi.DeviceStates.CONNECTED)
            else:
                _LOG.warning("Govee connection failed. Setting state to ERROR.")
                await api.set_device_state(ucapi.DeviceStates.ERROR)
    else:
        _LOG.info("Integration not configured yet.")

async def on_disconnect():
    """Handle Remote disconnection."""
    _LOG.info("Remote disconnected.")

async def on_subscribe_entities(entity_ids: list[str]):
    """Handle entity subscription."""
    global entities_initialized
    
    _LOG.info(f"Entities subscribed: {entity_ids}. Pushing initial state.")
    
    # Guard against race condition - ensure entities exist before subscription
    if not entities_initialized:
        _LOG.warning("RACE CONDITION DETECTED: Subscription requested before entities ready!")
        await create_entities_from_config()
    
    if remote and govee_client and govee_config.is_configured():
        _LOG.info("Ensuring remote entity has configured Govee client...")
        
        connection_ok = await govee_client.test_connection()
        _LOG.info(f"Govee client connection test: {'OK' if connection_ok else 'FAILED'}")
        
        if not connection_ok:
            _LOG.error("Govee client connection failed during entity subscription")
            await api.set_device_state(ucapi.DeviceStates.ERROR)
            return
    
    if remote and remote.entity.id in entity_ids:
        _LOG.info("Remote entity subscribed - pushing initial state")
        await remote.push_initial_state()
        _LOG.info("Remote entity fully initialized and ready for commands")

async def on_unsubscribe_entities(entity_ids: list[str]):
    """Handle entity unsubscription from Remote."""
    _LOG.info(f"Remote unsubscribed from entities: {entity_ids}")
    
    if remote and remote.entity.id in entity_ids:
        _LOG.info("Remote entity unsubscribed")

async def init_integration():
    """Initialize the integration objects and API."""
    global api, govee_client, govee_config
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    driver_json_path = os.path.join(project_root, "driver.json")
    
    if not os.path.exists(driver_json_path):
        driver_json_path = "driver.json"
        if not os.path.exists(driver_json_path):
            _LOG.error(f"Cannot find driver.json at {driver_json_path}")
            raise FileNotFoundError("driver.json not found")
    
    _LOG.info(f"Using driver.json from: {driver_json_path}")

    api = ucapi.IntegrationAPI(loop)

    config_path = os.path.join(api.config_dir_path, "config.json")
    _LOG.info(f"Using config file: {config_path}")
    govee_config = GoveeConfig(config_path)
    
    govee_client = GoveeClient("")
    govee_client._config = govee_config

    setup_handler = GoveeSetup(govee_config, govee_client, on_setup_complete)
    
    await api.init(driver_json_path, setup_handler.setup_handler)
    
    api.add_listener(ucapi.Events.CONNECT, on_r2_connect)
    api.add_listener(ucapi.Events.DISCONNECT, on_disconnect)
    api.add_listener(ucapi.Events.SUBSCRIBE_ENTITIES, on_subscribe_entities)
    api.add_listener(ucapi.Events.UNSUBSCRIBE_ENTITIES, on_unsubscribe_entities)
    
    _LOG.info("Integration API initialized successfully")
    
async def main():
    """Main entry point."""
    _LOG.info("Starting Govee Integration Driver")
    
    try:
        await init_integration()
        if govee_config and govee_config.is_configured():
            _LOG.info("Integration is already configured - pre-creating entities")
            
            # Step 1: Create entities IMMEDIATELY from saved config
            await create_entities_from_config()
            
            if entities_initialized:
                _LOG.info("Entities created successfully - now safe for UC Remote subscription")
                
                # Step 2: Verify connection in background (doesn't block entity availability)
                loop.create_task(verify_and_set_connection_state())
            else:
                _LOG.error("Failed to create entities from configuration")
                await api.set_device_state(ucapi.DeviceStates.ERROR)
        else:
            _LOG.warning("Integration is not configured. Waiting for setup...")
            await api.set_device_state(ucapi.DeviceStates.ERROR)

        _LOG.info("Integration is running. Press Ctrl+C to stop.")
        
    except Exception as e:
        _LOG.error(f"Failed to start integration: {e}", exc_info=True)
        if api:
            await api.set_device_state(ucapi.DeviceStates.ERROR)
        raise
    
def shutdown_handler(signum, frame):
    """Handle termination signals for graceful shutdown."""
    _LOG.warning(f"Received signal {signum}. Shutting down...")
    
    async def cleanup():
        try:
            if govee_client:
                _LOG.info("Closing Govee client...")
                await govee_client.disconnect()
            
            _LOG.info("Cancelling remaining tasks...")
            tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            [task.cancel() for task in tasks]
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            _LOG.error(f"Error during cleanup: {e}")
        finally:
            _LOG.info("Stopping event loop...")
            loop.stop()

    loop.create_task(cleanup())

if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    try:
        loop.run_until_complete(main())
        loop.run_forever()
    except (KeyboardInterrupt, asyncio.CancelledError):
        _LOG.info("Driver stopped.")
    except Exception as e:
        _LOG.error(f"Driver failed: {e}", exc_info=True)
    finally:
        if loop and not loop.is_closed():
            _LOG.info("Closing event loop...")
            loop.close()