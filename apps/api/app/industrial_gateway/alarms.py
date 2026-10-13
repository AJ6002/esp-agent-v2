"""Industrial Alarm event pipeline.

Converts OPC UA DataChange / Alarm signals into platform industrial alarm records:

- State machine: NORMAL -> WARNING -> CRITICAL (reverts to NORMAL when cleared);
- Produced/cleared **on state transitions only**, preventing high-frequency event spam;
- Thresholds aligned with platform ``SENSOR_DEFINITIONS`` warning thresholds;
- Boolean ``Alarm`` node being active is immediately judged as CRITICAL (emergency stop/alarm bit semantics).

Read-only constraint: this module only produces platform alarm records and writes nothing to devices.
"""

from __future__ import annotations

from typing import Final

ALARM_STATE_NORMAL: Final = "NORMAL"
ALARM_STATE_WARNING: Final = "WARNING"
ALARM_STATE_CRITICAL: Final = "CRITICAL"
ALARM_STATES: Final[frozenset[str]] = frozenset(
    {ALARM_STATE_NORMAL, ALARM_STATE_WARNING, ALARM_STATE_CRITICAL}
)

# Aligned with intelligence_service.SENSOR_DEFINITIONS warning thresholds.
_WARNING_THRESHOLDS: Final[dict[str, tuple[bool, float]]] = {
    # field: (is_upper_bound, threshold)
    "bearing_temperature": (True, 75.0),
    "vibration_rms": (True, 4.5),
    "motor_current": (True, 27.0),
    "load_ratio": (True, 100.0),
}
VOLTAGE_LOWER: Final = 342.0
VOLTAGE_UPPER: Final = 418.0


def evaluate_alarm_state(
    snapshot_fields: dict[str, float | bool | None],
    *,
    alarm_active: bool,
) -> str:
    """Evaluate current alarm state based on snapshot metrics and Alarm bit.

    ``snapshot_fields`` uses platform telemetry field names (bearing_temperature, etc.).
    """
    if alarm_active:
        return ALARM_STATE_CRITICAL
    for field_name, (is_upper, threshold) in _WARNING_THRESHOLDS.items():
        value = snapshot_fields.get(field_name)
        if isinstance(value, bool) or value is None:
            continue
        if is_upper and value > threshold:
            return ALARM_STATE_WARNING
    voltage = snapshot_fields.get("motor_voltage")
    if isinstance(voltage, (int, float)) and not (
        VOLTAGE_LOWER <= float(voltage) <= VOLTAGE_UPPER
    ):
        return ALARM_STATE_WARNING
    return ALARM_STATE_NORMAL


def build_alarm_message(
    state: str,
    snapshot_fields: dict[str, float | bool | None],
    *,
    alarm_active: bool,
) -> str:
    """Generate alarm message in English, including detailed breach metrics."""
    if state == ALARM_STATE_CRITICAL:
        detail = "Device alarm bit (Alarm) active" if alarm_active else "Metrics entered critical range"
        return f"Industrial alarm escalated to CRITICAL: {detail}"
    if state == ALARM_STATE_WARNING:
        offenders: list[str] = []
        label_by_field = {
            "bearing_temperature": "Bearing Temperature",
            "vibration_rms": "Vibration RMS",
            "motor_current": "Motor Current",
            "load_ratio": "Load Ratio",
        }
        for field_name, (is_upper, threshold) in _WARNING_THRESHOLDS.items():
            value = snapshot_fields.get(field_name)
            if (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
                and is_upper
                and float(value) > threshold
            ):
                offenders.append(f"{label_by_field[field_name]}={float(value):.1f}")
        voltage = snapshot_fields.get("motor_voltage")
        if (
            isinstance(voltage, (int, float))
            and not isinstance(voltage, bool)
            and not (VOLTAGE_LOWER <= float(voltage) <= VOLTAGE_UPPER)
        ):
            offenders.append(f"Motor Voltage={float(voltage):.1f}V")
        detail = ", ".join(offenders) or "Multiple metrics breached"
        return f"Industrial alarm escalated to WARNING: {detail}"
    return "Industrial alarm cleared: metrics restored to normal range"
