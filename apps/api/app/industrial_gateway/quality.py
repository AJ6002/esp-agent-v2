"""Data Quality Layer: the sole gateway before raw OPC UA reads enter business logic.

Processing:

- missing value          -> reject ``missing_value``
- invalid timestamp      -> substitute reception time when missing (correction);
                           future / expired timestamp -> reject
- bad quality flag       -> OPC UA StatusCode Bad -> reject ``bad_quality``
- unit conversion        -> convert declared unit to platform canonical unit
- duplicate timestamp    -> identical source timestamp on same node -> reject ``duplicate_timestamp``

Rejected data is NEVER written to business tables; equipment snapshots failing validation are skipped entirely.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Final

from app.industrial_gateway.opcua.models import (
    QUALITY_BAD,
    NodeRead,
    RejectedRead,
)

REASON_MISSING_VALUE = "missing_value"
REASON_NON_NUMERIC = "non_numeric"
REASON_BAD_QUALITY = "bad_quality"
REASON_FUTURE_TIMESTAMP = "future_timestamp"
REASON_STALE_TIMESTAMP = "stale_timestamp"
REASON_DUPLICATE_TIMESTAMP = "duplicate_timestamp"
REASON_UNKNOWN_UNIT = "unknown_unit"
REASON_CONVERSION_FAILED = "conversion_failed"


class UnitConversionError(ValueError):
    """Unit cannot be converted to platform canonical unit."""

    def __init__(self, metric: str, unit: str) -> None:
        self.metric = metric
        self.unit = unit
        super().__init__(f"Metric {metric} does not support unit {unit!r}")


# Platform canonical units (aligned with intelligence_service.SENSOR_DEFINITIONS).
CANONICAL_UNITS: Final[dict[str, str]] = {
    "temperature": "celsius",
    "vibration": "mm/s",
    "current": "a",
    "voltage": "v",
    "speed": "rpm",
    "load": "%",
    "ambient_temperature": "celsius",
}

_UNIT_ALIASES: Final[dict[str, str]] = {
    "c": "celsius",
    "°c": "celsius",
    "℃": "celsius",
    "celsius": "celsius",
    "f": "fahrenheit",
    "°f": "fahrenheit",
    "fahrenheit": "fahrenheit",
    "k": "kelvin",
    "kelvin": "kelvin",
    "mm/s": "mm/s",
    "mms": "mm/s",
    "mm_s": "mm/s",
    "a": "a",
    "amp": "a",
    "ampere": "a",
    "v": "v",
    "volt": "v",
    "rpm": "rpm",
    "r/min": "rpm",
    "%": "%",
    "percent": "%",
}


def normalize_unit(unit: str) -> str:
    return _UNIT_ALIASES.get(unit.strip().lower(), unit.strip().lower())


def convert_value(metric: str, unit: str, value: float) -> float:
    """Convert ``value`` from ``unit`` to platform canonical unit for the metric.

    Temperature supports celsius / fahrenheit / kelvin; other metrics accept canonical units only
    (including case variations and common aliases). Raises :class:`UnitConversionError` on failure.
    """
    canonical = CANONICAL_UNITS.get(metric)
    if canonical is None:
        raise UnitConversionError(metric, unit)
    normalized = normalize_unit(unit)
    if metric in {"temperature", "ambient_temperature"}:
        if normalized == "celsius":
            return value
        if normalized == "fahrenheit":
            return (value - 32.0) * 5.0 / 9.0
        if normalized == "kelvin":
            return value - 273.15
        raise UnitConversionError(metric, unit)
    if normalized != canonical:
        raise UnitConversionError(metric, unit)
    return value


@dataclass(slots=True)
class QualityReport:
    """Complete outcome of a single data quality validation."""

    accepted: list[NodeRead] = field(default_factory=list)
    rejected: list[RejectedRead] = field(default_factory=list)
    corrections: list[str] = field(default_factory=list)

    @property
    def rejected_count(self) -> int:
        return len(self.rejected)

    def reject_reasons(self) -> dict[str, int]:
        reasons: dict[str, int] = {}
        for item in self.rejected:
            reasons[item.reason] = reasons.get(item.reason, 0) + 1
        return reasons


class DataQualityLayer:
    """Stateful node read validator (tracks latest timestamp per node for dedup)."""

    def __init__(
        self,
        *,
        max_age_seconds: float = 300.0,
        future_tolerance_seconds: float = 30.0,
    ) -> None:
        self._max_age_seconds = max_age_seconds
        self._future_tolerance_seconds = future_tolerance_seconds
        self._last_timestamps: dict[str, datetime] = {}

    def reset(self) -> None:
        self._last_timestamps.clear()

    def process(
        self,
        reads: list[NodeRead],
        *,
        received_at: datetime | None = None,
    ) -> QualityReport:
        """Validate a batch of reads, returning accepted / rejected / corrected outcomes."""
        received = (received_at or datetime.now(UTC)).astimezone(UTC)
        report = QualityReport()
        for read in reads:
            outcome = self._check(read, received)
            if isinstance(outcome, RejectedRead):
                report.rejected.append(outcome)
                continue
            accepted_read, correction = outcome
            if correction:
                report.corrections.append(correction)
            report.accepted.append(accepted_read)
        return report

    def _check(
        self, read: NodeRead, received: datetime
    ) -> RejectedRead | tuple[NodeRead, str | None]:
        # 1. Bad quality flag: OPC UA StatusCode Bad rejected directly.
        if read.quality == QUALITY_BAD:
            return RejectedRead(
                node_id=read.node_id,
                reason=REASON_BAD_QUALITY,
                detail=f"status_code={read.status_code}",
            )
        # 2. Missing value.
        if read.value is None:
            return RejectedRead(node_id=read.node_id, reason=REASON_MISSING_VALUE)
        # 3. Non-numeric value (NaN / Inf / unparseable type).
        if (
            not isinstance(read.value, bool)
            and isinstance(read.value, float)
            and not math.isfinite(read.value)
        ):
            return RejectedRead(
                node_id=read.node_id,
                reason=REASON_NON_NUMERIC,
                detail=f"value={read.value}",
            )
        if isinstance(read.value, str):
            return RejectedRead(
                node_id=read.node_id,
                reason=REASON_NON_NUMERIC,
                detail=f"value={read.value!r}",
            )
        # 4. Timestamp validity.
        correction: str | None = None
        timestamp = read.source_timestamp
        if timestamp is None:
            timestamp = received
            correction = f"{read.node_id}: source_timestamp missing, substituted with reception time"
        else:
            timestamp = timestamp.astimezone(UTC)
            if timestamp > received + timedelta(seconds=self._future_tolerance_seconds):
                return RejectedRead(
                    node_id=read.node_id,
                    reason=REASON_FUTURE_TIMESTAMP,
                    detail=f"source_timestamp={timestamp.isoformat()}",
                )
            if received - timestamp > timedelta(seconds=self._max_age_seconds):
                return RejectedRead(
                    node_id=read.node_id,
                    reason=REASON_STALE_TIMESTAMP,
                    detail=f"source_timestamp={timestamp.isoformat()}",
                )
        # 5. Duplicate timestamp: identical to last accepted timestamp for node -> reject.
        last = self._last_timestamps.get(read.node_id)
        if last is not None and timestamp <= last:
            return RejectedRead(
                node_id=read.node_id,
                reason=REASON_DUPLICATE_TIMESTAMP,
                detail=f"source_timestamp={timestamp.isoformat()}",
            )
        self._last_timestamps[read.node_id] = timestamp
        accepted = NodeRead(
            node_id=read.node_id,
            value=read.value,
            source_timestamp=timestamp,
            status_code=read.status_code,
            quality=read.quality,
            unit_hint=read.unit_hint,
        )
        return accepted, correction
