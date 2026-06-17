# Renogy BLE Connection Stability

Renogy devices currently use two different connection patterns in this integration.

Most devices use active polling. Home Assistant watches advertisements, opens a BLE connection when the polling interval is due, reads Modbus data through `renogy-ble`, then releases the connection. In the Home Assistant Bluetooth visualization this can look like frequent connect and disconnect behavior even when polling is working as designed.

Smart Shunt devices can use a sustained notification listener. In `sustained` or `auto` shunt mode, the integration opens a GATT connection, subscribes to notifications, and keeps that connection alive until it fails or the entry unloads. This is closer to the solid connection line shown by apps that keep an ECOWORTHY device connected continuously.

## Practical Path

The safest path is to make connection behavior explicit per device type instead of forcing every Renogy device into a permanent connection.

1. Keep polling as the default for controllers, DCC chargers, and inverters.
2. Use the existing Smart Shunt `auto` mode when sustained notifications are available.
3. Use diagnostics before changing defaults: last successful poll, consecutive poll failures, last BLE error, connection mode, Bluetooth source, and reconnect count.
4. Add an experimental sustained connection mode for non-shunt devices only after confirming the device exposes a notification or read strategy that benefits from a held GATT connection.
5. Fall back automatically to polling after repeated sustained connection failures, matching the current Smart Shunt `auto` behavior.

## Why Not Always Stay Connected

A permanent BLE connection can improve update freshness, but it can also prevent the vendor app or another integration from connecting, expose adapter/BlueZ instability, and increase battery or radio load. Some Renogy BT modules may not send useful notifications for all data, so holding a connection may not improve data quality unless the integration still performs reads over that connection.

## Next Implementation Step

The next code change should add a shared connection-mode option, modeled after the Smart Shunt modes:

- `polling`: connect only for scheduled reads.
- `sustained`: keep a connection open when the device type has a supported notification/read loop.
- `auto`: try sustained first, then fall back to polling after repeated failures.

For controllers, DCC chargers, and inverters, the first useful milestone is not sustained mode itself. It is better diagnostics around why a poll failed and whether failures correlate with RSSI, adapter path, or concurrent connections. That data will tell us whether the issue is range/interference, polling cadence, adapter contention, or the lack of a sustained connection path.

## Health Sensor Diagnostics

The per-device `Device Health` sensor exposes these attributes for troubleshooting:

- `connection_mode`
- `poll_attempts`
- `successful_poll_count`
- `failed_poll_count`
- `consecutive_poll_failures`
- `last_poll_started`
- `last_poll_finished`
- `last_successful_poll`
- `last_ble_error`
- `last_ble_source`
- `reconnect_count`

Watch these alongside `rssi` and `rssi_status`. If RSSI is healthy but `consecutive_poll_failures` rises, the next place to look is adapter contention or the read strategy. If failures rise only when RSSI is weak, placement or antenna changes are more likely to help than sustained mode.
