"""Tests for Renogy BLE coordinator error handling."""

import asyncio
import sys
import types
from enum import Enum
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock


def _install_module_stubs() -> None:
    """Install minimal module stubs to import the BLE coordinator."""
    from tests.mocks import ha_bluetooth, ha_coordinator

    bleak_module = cast(Any, types.ModuleType("bleak"))

    class BleakError(Exception):
        """Stub BleakError for testing."""

    class BleakClient:
        """Stub BleakClient for sustained shunt tests."""

        def set_disconnected_callback(self, _callback) -> None:
            """Store disconnect callback."""

        async def start_notify(self, *_args, **_kwargs) -> None:
            """Start notifications."""

        async def stop_notify(self, *_args, **_kwargs) -> None:
            """Stop notifications."""

        async def disconnect(self) -> None:
            """Disconnect the client."""

    bleak_module.BleakError = BleakError
    bleak_module.BleakClient = BleakClient
    sys.modules["bleak"] = bleak_module
    bleak_characteristic_module = cast(
        Any, types.ModuleType("bleak.backends.characteristic")
    )
    bleak_characteristic_module.BleakGATTCharacteristic = object
    sys.modules["bleak.backends.characteristic"] = bleak_characteristic_module
    retry_connector_module = cast(Any, types.ModuleType("bleak_retry_connector"))
    retry_connector_module.establish_connection = AsyncMock(return_value=BleakClient())
    sys.modules["bleak_retry_connector"] = retry_connector_module

    core_module = cast(Any, types.ModuleType("homeassistant.core"))

    class CoreState(str, Enum):
        """Stub CoreState enum for testing."""

        running = "running"

    def callback(func):
        """Return the function unchanged for testing."""
        return func

    core_module.CoreState = CoreState
    core_module.HomeAssistant = object
    core_module.callback = callback

    helpers_event_module = cast(Any, types.ModuleType("homeassistant.helpers.event"))
    helpers_event_module.async_track_time_interval = MagicMock()

    bluetooth_module = cast(Any, types.ModuleType("homeassistant.components.bluetooth"))
    bluetooth_module.BluetoothChange = ha_bluetooth.BluetoothChange
    bluetooth_module.BluetoothScanningMode = ha_bluetooth.BluetoothScanningMode
    bluetooth_module.BluetoothServiceInfoBleak = ha_bluetooth.BluetoothServiceInfoBleak
    bluetooth_module.async_get_scanner = MagicMock(return_value=MagicMock())
    bluetooth_module.async_last_service_info = MagicMock()
    bluetooth_module.async_ble_device_from_address = MagicMock()
    bluetooth_module.async_register_callback = MagicMock()

    components_module = cast(Any, types.ModuleType("homeassistant.components"))
    components_module.bluetooth = bluetooth_module

    homeassistant_module = cast(Any, types.ModuleType("homeassistant"))
    sys.modules["homeassistant"] = homeassistant_module
    sys.modules["homeassistant.components"] = components_module
    sys.modules["homeassistant.components.bluetooth"] = bluetooth_module
    sys.modules["homeassistant.components.bluetooth.active_update_coordinator"] = (
        ha_coordinator
    )
    sys.modules["homeassistant.core"] = core_module
    sys.modules["homeassistant.helpers.event"] = helpers_event_module
    config_entries_module = cast(Any, types.ModuleType("homeassistant.config_entries"))
    config_entries_module.ConfigEntry = object
    sys.modules["homeassistant.config_entries"] = config_entries_module
    helpers_module = cast(Any, types.ModuleType("homeassistant.helpers"))
    device_registry_module = cast(
        Any, types.ModuleType("homeassistant.helpers.device_registry")
    )
    device_registry_module.async_get = MagicMock()
    sys.modules["homeassistant.helpers"] = helpers_module
    sys.modules["homeassistant.helpers.device_registry"] = device_registry_module
    const_module = cast(Any, types.ModuleType("homeassistant.const"))
    const_module.CONF_ADDRESS = "address"

    class Platform(str, Enum):
        """Stub Platform enum for testing."""

        BINARY_SENSOR = "binary_sensor"
        SENSOR = "sensor"
        NUMBER = "number"
        SELECT = "select"
        SWITCH = "switch"

    const_module.Platform = Platform
    sys.modules["homeassistant.const"] = const_module

    renogy_ble_module = cast(Any, types.ModuleType("renogy_ble"))
    renogy_ble_ble_module = cast(Any, types.ModuleType("renogy_ble.ble"))
    renogy_ble_shunt_module = cast(Any, types.ModuleType("renogy_ble.shunt"))

    class RenogyBleClient:
        """Stub RenogyBleClient for testing."""

        def __init__(self, scanner):
            self.scanner = scanner

        async def read_device(self, device):
            return MagicMock(success=True, error=None)

    class RenogyBLEDevice:
        """Stub RenogyBLEDevice for testing."""

        def __init__(self, ble_device, advertisement_rssi, device_type=None):
            self.ble_device = ble_device
            self.address = ble_device.address
            self.name = ble_device.name or "Unknown Renogy Device"
            self.rssi = advertisement_rssi
            self.device_type = device_type
            self.parsed_data = {}
            self.update_availability = MagicMock()

    def clean_device_name(name: str) -> str:
        """Return a cleaned device name for testing."""
        return name.strip()

    class RenogyBleReadResult:
        """Stub read result matching the real library interface."""

        def __init__(self, success: bool, parsed_data: dict[str, Any], error=None):
            self.success = success
            self.parsed_data = parsed_data
            self.error = error

    renogy_ble_ble_module.RenogyBleClient = RenogyBleClient
    renogy_ble_ble_module.RenogyBLEDevice = RenogyBLEDevice
    renogy_ble_ble_module.RenogyBleReadResult = RenogyBleReadResult
    renogy_ble_ble_module.clean_device_name = clean_device_name
    renogy_ble_ble_module.LOAD_CONTROL_REGISTER = 0x010A

    class ShuntBleClient:
        """Stub shunt client matching the library interface."""

        def _integrate_energy_totals(
            self, *, device_address: str, power_w: float | None, now_ts: float
        ) -> tuple[float, float]:
            """Return deterministic energy totals for testing."""
            return (0.0, 0.0)

        async def read_device(self, device):
            return RenogyBleReadResult(True, getattr(device, "parsed_data", {}), None)

    renogy_ble_shunt_module.ShuntBleClient = ShuntBleClient
    renogy_ble_shunt_module.SHUNT_EXPECTED_PAYLOAD_LENGTH = 110
    renogy_ble_shunt_module.SHUNT_NOTIFY_CHAR_UUID = (
        "0000c411-0000-1000-8000-00805f9b34fb"
    )
    renogy_ble_shunt_module._find_valid_payload_window = MagicMock(return_value=None)

    sys.modules["renogy_ble"] = renogy_ble_module
    sys.modules["renogy_ble.ble"] = renogy_ble_ble_module
    sys.modules["renogy_ble.shunt"] = renogy_ble_shunt_module


def _load_ble_module():
    """Load the BLE module with stubs in place."""
    _install_module_stubs()
    sys.modules.pop("custom_components.renogy.ble", None)
    sys.modules.pop("custom_components.renogy", None)

    import importlib

    return importlib.import_module("custom_components.renogy.ble")


def test_read_device_data_handles_ble_errors():
    """Ensure BLE read exceptions update availability and return False."""
    ble_module = _load_ble_module()
    hass = MagicMock()
    logger = MagicMock()
    coordinator = ble_module.RenogyActiveBluetoothCoordinator(
        hass=hass,
        logger=logger,
        address="AA:BB:CC:DD:EE:FF",
        scan_interval=30,
        device_type="controller",
    )

    service_info = ble_module.BluetoothServiceInfoBleak(
        address="AA:BB:CC:DD:EE:FF",
        name="BT-TH-12345",
        rssi=-60,
    )

    coordinator._ble_client.read_device = AsyncMock(
        side_effect=ble_module.BleakError("read failed")
    )

    success = asyncio.run(coordinator._read_device_data(service_info))

    assert success is False
    assert coordinator.last_update_success is False
    assert coordinator.poll_attempts == 1
    assert coordinator.failed_poll_count == 1
    assert coordinator.successful_poll_count == 0
    assert coordinator.consecutive_poll_failures == 1
    assert "read failed" in coordinator.last_ble_error
    assert coordinator.last_poll_started is not None
    assert coordinator.last_poll_finished is not None
    coordinator.device.update_availability.assert_called_once()
    call_args = coordinator.device.update_availability.call_args[0]
    assert call_args[0] is False
    assert "read failed" in str(call_args[1])


def test_read_device_data_records_success_diagnostics():
    """Ensure successful BLE reads reset failure diagnostics."""
    ble_module = _load_ble_module()
    hass = MagicMock()
    logger = MagicMock()
    coordinator = ble_module.RenogyActiveBluetoothCoordinator(
        hass=hass,
        logger=logger,
        address="AA:BB:CC:DD:EE:FF",
        scan_interval=30,
        device_type="controller",
    )
    coordinator.consecutive_poll_failures = 2
    coordinator.last_ble_error = "previous failure"

    service_info = ble_module.BluetoothServiceInfoBleak(
        address="AA:BB:CC:DD:EE:FF",
        name="BT-TH-12345",
        rssi=-60,
    )

    success = asyncio.run(coordinator._read_device_data(service_info))

    assert success is True
    assert coordinator.poll_attempts == 1
    assert coordinator.successful_poll_count == 1
    assert coordinator.failed_poll_count == 0
    assert coordinator.consecutive_poll_failures == 0
    assert coordinator.last_ble_error is None
    assert coordinator.last_successful_poll is not None


def test_read_device_data_retries_missing_characteristic_once():
    """Ensure missing GATT characteristic errors rebuild the client and retry once."""
    ble_module = _load_ble_module()
    hass = MagicMock()
    logger = MagicMock()
    coordinator = ble_module.RenogyActiveBluetoothCoordinator(
        hass=hass,
        logger=logger,
        address="AA:BB:CC:DD:EE:FF",
        scan_interval=30,
        device_type="controller",
    )

    service_info = ble_module.BluetoothServiceInfoBleak(
        address="AA:BB:CC:DD:EE:FF",
        name="BT-TH-12345",
        rssi=-60,
    )

    first_client = coordinator._ble_client
    first_client.read_device = AsyncMock(
        return_value=ble_module.renogy_ble_ble.RenogyBleReadResult(
            False,
            {},
            ble_module.BleakError(
                "Characteristic 0000fff1-0000-1000-8000-00805f9b34fb was not found!"
            ),
        )
    )
    second_client = ble_module.RenogyBleClient(scanner=MagicMock())
    second_client.read_device = AsyncMock(
        return_value=ble_module.renogy_ble_ble.RenogyBleReadResult(True, {}, None)
    )
    coordinator._build_ble_client_for_type = MagicMock(return_value=second_client)
    original_sleep = ble_module.asyncio.sleep
    ble_module.asyncio.sleep = AsyncMock()

    try:
        success = asyncio.run(coordinator._read_device_data(service_info))
    finally:
        ble_module.asyncio.sleep = original_sleep

    assert success is True
    assert coordinator.characteristic_not_found_count == 1
    assert coordinator.characteristic_retry_count == 1
    assert coordinator.characteristic_retry_success_count == 1
    assert coordinator.reconnect_count == 1
    assert coordinator.last_characteristic_error is None
    assert coordinator.successful_poll_count == 1
    assert coordinator.failed_poll_count == 0
    first_client.read_device.assert_awaited_once()
    second_client.read_device.assert_awaited_once()


def test_read_device_data_soft_fails_repeated_missing_characteristic():
    """Ensure repeated missing characteristics preserve availability."""
    ble_module = _load_ble_module()
    hass = MagicMock()
    logger = MagicMock()
    coordinator = ble_module.RenogyActiveBluetoothCoordinator(
        hass=hass,
        logger=logger,
        address="AA:BB:CC:DD:EE:FF",
        scan_interval=30,
        device_type="controller",
    )

    service_info = ble_module.BluetoothServiceInfoBleak(
        address="AA:BB:CC:DD:EE:FF",
        name="BT-TH-12345",
        rssi=-60,
    )
    error = ble_module.BleakError(
        "Characteristic 0000fff1-0000-1000-8000-00805f9b34fb was not found!"
    )
    coordinator._ble_client.read_device = AsyncMock(
        return_value=ble_module.renogy_ble_ble.RenogyBleReadResult(False, {}, error)
    )
    retry_client = ble_module.RenogyBleClient(scanner=MagicMock())
    retry_client.read_device = AsyncMock(
        return_value=ble_module.renogy_ble_ble.RenogyBleReadResult(False, {}, error)
    )
    coordinator._build_ble_client_for_type = MagicMock(return_value=retry_client)
    original_sleep = ble_module.asyncio.sleep
    ble_module.asyncio.sleep = AsyncMock()

    try:
        success = asyncio.run(coordinator._read_device_data(service_info))
    finally:
        ble_module.asyncio.sleep = original_sleep

    assert success is True
    assert coordinator.characteristic_not_found_count == 2
    assert coordinator.characteristic_retry_count == 1
    assert coordinator.characteristic_retry_success_count == 0
    assert coordinator.failed_poll_count == 0
    assert coordinator.consecutive_poll_failures == 0
    assert coordinator.last_update_success is True
    assert coordinator.stale_gatt_soft_failure_count == 1
    assert "Characteristic 0000fff1" in coordinator.last_characteristic_error
    assert "Characteristic 0000fff1" in coordinator.last_stale_gatt_error
    coordinator.device.update_availability.assert_called_once_with(True, None)


def test_startup_warmup_skips_refresh_requests():
    """Ensure startup warmup avoids active reads while adapters settle."""
    ble_module = _load_ble_module()
    hass = MagicMock()
    hass.loop.time = MagicMock(return_value=10.0)
    logger = MagicMock()
    coordinator = ble_module.RenogyActiveBluetoothCoordinator(
        hass=hass,
        logger=logger,
        address="AA:BB:CC:DD:EE:FF",
        scan_interval=30,
        device_type="controller",
    )
    coordinator._startup_started_at = 0.0
    coordinator._async_poll_device = AsyncMock()

    asyncio.run(coordinator.async_request_refresh())

    coordinator._async_poll_device.assert_not_awaited()
    assert coordinator.startup_refresh_skip_count == 1
    assert coordinator.last_update_success is True


def test_startup_warmup_skips_advertisement_poll():
    """Ensure advertisement-triggered polling waits for startup warmup."""
    ble_module = _load_ble_module()
    hass = MagicMock()
    hass.loop.time = MagicMock(return_value=10.0)
    hass.state = ble_module.CoreState.running
    logger = MagicMock()
    coordinator = ble_module.RenogyActiveBluetoothCoordinator(
        hass=hass,
        logger=logger,
        address="AA:BB:CC:DD:EE:FF",
        scan_interval=30,
        device_type="controller",
    )
    coordinator._startup_started_at = 0.0
    service_info = ble_module.BluetoothServiceInfoBleak(
        address="AA:BB:CC:DD:EE:FF",
        name="BT-TH-12345",
        rssi=-60,
    )

    assert coordinator._needs_poll(service_info, None) is False
    assert coordinator.startup_refresh_skip_count == 1


def test_startup_characteristic_failure_preserves_availability():
    """Ensure warmup characteristic misses do not mark the device unavailable."""
    ble_module = _load_ble_module()
    hass = MagicMock()
    hass.loop.time = MagicMock(return_value=10.0)
    logger = MagicMock()
    coordinator = ble_module.RenogyActiveBluetoothCoordinator(
        hass=hass,
        logger=logger,
        address="AA:BB:CC:DD:EE:FF",
        scan_interval=30,
        device_type="controller",
    )
    coordinator._startup_started_at = 0.0
    error = ble_module.BleakError(
        "Characteristic 0000fff1-0000-1000-8000-00805f9b34fb was not found!"
    )
    coordinator._read_device_with_characteristic_recovery = AsyncMock(
        return_value=(False, error)
    )

    service_info = ble_module.BluetoothServiceInfoBleak(
        address="AA:BB:CC:DD:EE:FF",
        name="BT-TH-12345",
        rssi=-60,
    )

    success = asyncio.run(coordinator._read_device_data(service_info))

    assert success is True
    assert coordinator.last_update_success is True
    assert coordinator.failed_poll_count == 0
    assert coordinator.consecutive_poll_failures == 0
    assert coordinator.startup_characteristic_suppressed_count == 1
    assert coordinator.stale_gatt_soft_failure_count == 1
    assert "Characteristic 0000fff1" in coordinator.last_startup_characteristic_error
    coordinator.device.update_availability.assert_called_once_with(True, None)


def test_sustained_shunt_device_defaults_to_generic_client():
    """Ensure sustained SHUNT300 mode avoids the library shunt read client."""
    ble_module = _load_ble_module()
    coordinator = ble_module.RenogyActiveBluetoothCoordinator(
        hass=MagicMock(),
        logger=MagicMock(),
        address="AA:BB:CC:DD:EE:FF",
        scan_interval=30,
        device_type="shunt300",
        shunt_connection_mode="sustained",
    )

    assert coordinator._ble_client.__class__.__name__ == "RenogyBleClient"


def test_intermittent_shunt_device_uses_library_shunt_client():
    """Ensure intermittent SHUNT300 mode keeps using the library shunt client."""
    ble_module = _load_ble_module()
    coordinator = ble_module.RenogyActiveBluetoothCoordinator(
        hass=MagicMock(),
        logger=MagicMock(),
        address="AA:BB:CC:DD:EE:FF",
        scan_interval=30,
        device_type="shunt300",
        shunt_connection_mode="intermittent",
    )

    assert coordinator._ble_client.__class__.__name__ == "ShuntBleClient"


def test_auto_shunt_device_starts_with_sustained_listener():
    """Ensure auto SHUNT300 mode starts with sustained listener behavior."""
    ble_module = _load_ble_module()
    coordinator = ble_module.RenogyActiveBluetoothCoordinator(
        hass=MagicMock(),
        logger=MagicMock(),
        address="AA:BB:CC:DD:EE:FF",
        scan_interval=30,
        device_type="shunt300",
        shunt_connection_mode="auto",
    )

    assert coordinator._ble_client.__class__.__name__ == "RenogyBleClient"
    assert coordinator._uses_sustained_shunt_listener() is True


def test_auto_shunt_fallback_switches_to_polling_client():
    """Ensure auto mode falls back to polling after repeated failures."""
    ble_module = _load_ble_module()
    coordinator = ble_module.RenogyActiveBluetoothCoordinator(
        hass=MagicMock(),
        logger=MagicMock(),
        address="AA:BB:CC:DD:EE:FF",
        scan_interval=30,
        device_type="shunt300",
        shunt_connection_mode="auto",
    )

    for _ in range(ble_module.SHUNT_AUTO_FALLBACK_FAILURES):
        coordinator._handle_shunt_listener_failure(RuntimeError("boom"))

    assert coordinator._shunt_auto_fallback_active is True
    assert coordinator._uses_sustained_shunt_listener() is False
    assert coordinator._ble_client.__class__.__name__ == "ShuntBleClient"


def test_sustained_shunt_refresh_does_not_poll():
    """Ensure sustained SHUNT300 refresh requests do not open a competing read."""
    ble_module = _load_ble_module()
    coordinator = ble_module.RenogyActiveBluetoothCoordinator(
        hass=MagicMock(),
        logger=MagicMock(),
        address="AA:BB:CC:DD:EE:FF",
        scan_interval=30,
        device_type="shunt300",
        shunt_connection_mode="sustained",
    )
    coordinator._async_poll_device = AsyncMock()

    asyncio.run(coordinator.async_request_refresh())

    coordinator._async_poll_device.assert_not_awaited()


def test_detected_sustained_shunt_poll_does_not_read():
    """Ensure BLE-detected sustained shunts do not use the polling read path."""
    ble_module = _load_ble_module()
    coordinator = ble_module.RenogyActiveBluetoothCoordinator(
        hass=MagicMock(),
        logger=MagicMock(),
        address="AA:BB:CC:DD:EE:FF",
        scan_interval=30,
        device_type="controller",
        shunt_connection_mode="sustained",
    )
    coordinator._ble_client.read_device = AsyncMock()
    service_info = MagicMock()
    service_info.name = "RTMShunt30046000655"
    service_info.address = "AA:BB:CC:DD:EE:FF"

    result = asyncio.run(coordinator._async_poll_device(service_info))

    assert result == {}
    coordinator._ble_client.read_device.assert_not_awaited()
    assert coordinator.sustained_shunt_read_skip_count == 0


def test_sustained_shunt_read_guard_records_skip():
    """Ensure direct sustained shunt reads are skipped and counted."""
    ble_module = _load_ble_module()
    coordinator = ble_module.RenogyActiveBluetoothCoordinator(
        hass=MagicMock(),
        logger=MagicMock(),
        address="AA:BB:CC:DD:EE:FF",
        scan_interval=30,
        device_type="shunt300",
        shunt_connection_mode="sustained",
    )
    coordinator._ble_client.read_device = AsyncMock()
    service_info = ble_module.BluetoothServiceInfoBleak(
        address="AA:BB:CC:DD:EE:FF",
        name="RTMShunt300A1B2",
        rssi=-60,
    )

    result = asyncio.run(coordinator._read_device_data(service_info))

    assert result is True
    coordinator._ble_client.read_device.assert_not_awaited()
    assert coordinator.sustained_shunt_read_skip_count == 1


def test_sustained_shunt_notification_ignores_duplicate_payloads():
    """Ensure identical sustained shunt payloads do not spam listeners."""
    ble_module = _load_ble_module()
    hass = MagicMock()
    hass.loop.time = MagicMock(side_effect=[100.0, 110.0])
    hass.loop.call_soon_threadsafe = lambda callback: callback()
    coordinator = ble_module.RenogyActiveBluetoothCoordinator(
        hass=hass,
        logger=MagicMock(),
        address="AA:BB:CC:DD:EE:FF",
        scan_interval=30,
        device_type="shunt300",
        shunt_connection_mode="sustained",
    )
    coordinator.device = MagicMock(parsed_data={})
    listener = MagicMock()
    coordinator.async_add_listener(listener)

    payload = (
        b"\x01\x02",
        {
            "shunt_voltage": 13.2,
            "shunt_current": 1.5,
            "shunt_power": 19.8,
            "shunt_soc": 85.0,
        },
    )
    ble_module.shunt_find_valid_payload_window = MagicMock(return_value=payload)

    coordinator._process_sustained_shunt_notification(b"first")
    coordinator._process_sustained_shunt_notification(b"second")

    assert coordinator.data["shunt_voltage"] == 13.2
    assert listener.call_count == 1


def test_sustained_shunt_notification_recovers_from_duplicate_payload_after_error():
    """Ensure duplicate payloads still restore availability after listener errors."""
    ble_module = _load_ble_module()
    hass = MagicMock()
    hass.loop.time = MagicMock(side_effect=[100.0, 110.0])
    hass.loop.call_soon_threadsafe = lambda callback: callback()
    coordinator = ble_module.RenogyActiveBluetoothCoordinator(
        hass=hass,
        logger=MagicMock(),
        address="AA:BB:CC:DD:EE:FF",
        scan_interval=30,
        device_type="shunt300",
        shunt_connection_mode="sustained",
    )
    coordinator.device = MagicMock(parsed_data={})
    listener = MagicMock()
    coordinator.async_add_listener(listener)

    payload = (
        b"\x01\x02",
        {
            "shunt_voltage": 13.2,
            "shunt_current": 1.5,
            "shunt_power": 19.8,
            "shunt_soc": 85.0,
        },
    )
    ble_module.shunt_find_valid_payload_window = MagicMock(return_value=payload)

    coordinator._process_sustained_shunt_notification(b"first")
    coordinator.last_update_success = False
    coordinator._process_sustained_shunt_notification(b"second")

    assert coordinator.last_update_success is True
    assert listener.call_count == 2
    assert coordinator.device.update_availability.call_args_list[-1][0] == (True, None)


def test_sustained_shunt_listener_error_notifies_entities():
    """Ensure sustained listener errors notify listeners about availability changes."""
    ble_module = _load_ble_module()
    hass = MagicMock()
    hass.loop.call_soon_threadsafe = lambda callback: callback()
    logger = MagicMock()
    coordinator = ble_module.RenogyActiveBluetoothCoordinator(
        hass=hass,
        logger=logger,
        address="AA:BB:CC:DD:EE:FF",
        scan_interval=30,
        device_type="shunt300",
        shunt_connection_mode="sustained",
    )
    listener = MagicMock()
    coordinator.async_add_listener(listener)
    service_info = ble_module.BluetoothServiceInfoBleak(
        address="AA:BB:CC:DD:EE:FF",
        name="RTMShunt300A1B2",
        rssi=-60,
    )
    ble_module.bluetooth.async_last_service_info.return_value = service_info
    client = MagicMock()
    client.start_notify = AsyncMock(side_effect=RuntimeError("notify failed"))
    client.stop_notify = AsyncMock()
    client.disconnect = AsyncMock()
    ble_module.establish_connection = AsyncMock(return_value=client)
    original_sleep = ble_module.asyncio.sleep
    ble_module.asyncio.sleep = AsyncMock(side_effect=asyncio.CancelledError())

    try:
        try:
            asyncio.run(coordinator._shunt_notification_loop())
        except asyncio.CancelledError:
            pass
    finally:
        ble_module.asyncio.sleep = original_sleep

    assert coordinator.last_update_success is False
    assert coordinator.reconnect_count == 1
    assert "notify failed" in coordinator.last_ble_error
    coordinator.device.update_availability.assert_called_with(
        False, client.start_notify.side_effect
    )
    assert listener.call_count == 1


def test_sustained_shunt_listener_detects_stale_connection():
    """Ensure sustained shunt listeners become stale without valid notifications."""
    ble_module = _load_ble_module()
    coordinator = ble_module.RenogyActiveBluetoothCoordinator(
        hass=MagicMock(),
        logger=MagicMock(),
        address="AA:BB:CC:DD:EE:FF",
        scan_interval=30,
        device_type="shunt300",
        shunt_connection_mode="sustained",
    )
    coordinator._shunt_listener_started_at = 100.0

    assert coordinator._sustained_shunt_listener_is_stale(279.0) is False
    assert coordinator._sustained_shunt_listener_is_stale(280.0) is True


def test_sustained_shunt_listener_restarts_when_stale():
    """Ensure stale sustained shunt listeners restart the BLE connection."""
    ble_module = _load_ble_module()
    hass = MagicMock()
    hass.loop.time = MagicMock(side_effect=[100.0, 280.0])
    hass.loop.call_soon_threadsafe = lambda callback: callback()
    logger = MagicMock()
    coordinator = ble_module.RenogyActiveBluetoothCoordinator(
        hass=hass,
        logger=logger,
        address="AA:BB:CC:DD:EE:FF",
        scan_interval=30,
        device_type="shunt300",
        shunt_connection_mode="sustained",
    )
    listener = MagicMock()
    coordinator.async_add_listener(listener)
    service_info = ble_module.BluetoothServiceInfoBleak(
        address="AA:BB:CC:DD:EE:FF",
        name="RTMShunt300A1B2",
        rssi=-60,
    )
    ble_module.bluetooth.async_last_service_info.return_value = service_info
    client = MagicMock()
    client.is_connected = True
    client.start_notify = AsyncMock()
    client.stop_notify = AsyncMock()
    client.disconnect = AsyncMock()
    ble_module.establish_connection = AsyncMock(return_value=client)
    original_sleep = ble_module.asyncio.sleep
    ble_module.asyncio.sleep = AsyncMock(side_effect=[None, asyncio.CancelledError()])

    try:
        try:
            asyncio.run(coordinator._shunt_notification_loop())
        except asyncio.CancelledError:
            pass
    finally:
        ble_module.asyncio.sleep = original_sleep

    assert coordinator.shunt_listener_restart_count == 1
    assert coordinator.reconnect_count == 1
    assert coordinator.shunt_listener_last_stale_restart is not None
    assert "listener stale" in coordinator.last_ble_error
    client.disconnect.assert_awaited()
    assert listener.call_count == 1


def test_shunt_poll_keeps_last_good_data_when_library_read_fails():
    """Ensure HA preserves the last good shunt snapshot on library read failure."""
    ble_module = _load_ble_module()
    hass = MagicMock()
    logger = MagicMock()
    coordinator = ble_module.RenogyActiveBluetoothCoordinator(
        hass=hass,
        logger=logger,
        address="AA:BB:CC:DD:EE:FF",
        scan_interval=30,
        device_type="shunt300",
        shunt_connection_mode="intermittent",
    )
    cached_data = {"shunt_voltage": 13.2, "reading_verified": True}
    failed_read_data = {"shunt_voltage": 15.7, "reading_verified": False}
    coordinator.data = dict(cached_data)

    service_info = ble_module.BluetoothServiceInfoBleak(
        address="AA:BB:CC:DD:EE:FF",
        name="RTMShunt300A1B2",
        rssi=-60,
    )

    coordinator._ble_client.read_device = AsyncMock(
        return_value=MagicMock(
            success=False,
            parsed_data=failed_read_data,
            error=RuntimeError("history-only payload"),
        )
    )

    result = asyncio.run(coordinator._async_poll_device(service_info))

    assert result == cached_data
    assert coordinator.data == cached_data
    assert coordinator.last_update_success is False
    coordinator.device.update_availability.assert_called_once()
    call_args = coordinator.device.update_availability.call_args[0]
    assert call_args[0] is False
    assert "history-only payload" in str(call_args[1])
