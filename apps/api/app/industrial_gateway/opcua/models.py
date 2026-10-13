"""OPC UA Gateway internal data structures: node read results and quality flags.

Does not depend on ``asyncua``, ensuring mock mode runs with zero extra dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

# OPC UA status code classification bits (simplified OPC 10000-4 §8.41):
#   bit31=1 -> Bad; bit30=1 -> Uncertain; otherwise Good.
_STATUS_BAD_BIT = 0x8000_0000
_STATUS_UNCERTAIN_BIT = 0x4000_0000

QUALITY_GOOD = "good"
QUALITY_UNCERTAIN = "uncertain"
QUALITY_BAD = "bad"

# Unified telemetry source flag: written to TelemetryRecord.scenario to identify OPC UA data.
TELEMETRY_SOURCE_OPCUA = "opcua"


def quality_from_status_code(status_code: int | None) -> str:
    """Classify OPC UA StatusCode into good / uncertain / bad.

    ``None`` is treated as Good: some simulation servers and mock clients do not populate status codes.
    """
    if status_code is None:
        return QUALITY_GOOD
    if status_code & _STATUS_BAD_BIT:
        return QUALITY_BAD
    if status_code & _STATUS_UNCERTAIN_BIT:
        return QUALITY_UNCERTAIN
    return QUALITY_GOOD


@dataclass(slots=True, frozen=True)
class NodeRead:
    """Raw result of a single OPC UA node read (before data quality validation)."""

    node_id: str
    value: float | bool | int | str | None
    source_timestamp: datetime | None
    status_code: int | None = None
    quality: str = QUALITY_GOOD
    unit_hint: str | None = None

    @property
    def is_bad(self) -> bool:
        return self.quality == QUALITY_BAD


@dataclass(slots=True, frozen=True)
class RejectedRead:
    """Read rejected by Data Quality Layer and the reason."""

    node_id: str
    reason: str
    detail: str = ""


@dataclass(slots=True)
class NodeSnapshotEntry:
    """Node state for API display (mapping + last read + quality conclusion)."""

    node_id: str
    equipment_code: str | None
    metric_name: str
    unit: str
    enabled: bool
    informational: bool
    last_value: float | bool | int | str | None = None
    last_quality: str | None = None
    last_timestamp: datetime | None = None
    last_error: str | None = None
