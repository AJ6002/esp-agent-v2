"""Alarm Correlation Engine: merges related alarms into correlated event groups.

Rules (deterministic, reproducible):

- **same_equipment**: Alarms on same equipment within ``window_seconds`` chained into same group;
- **line_cascade**: Different equipment on same line (``Equipment.production_line``) with overlapping
  time windows -> merged across groups (cascade / common cause detection, e.g. voltage sag across line);
- Group ID derived via uuid5 over sorted member IDs: identical member sets always produce identical group_id.

Pure functions decoupled from database: takes alarm snapshots as input for testing and reuse.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Final

from app.industrial_gateway.models import IndustrialAlarm

CORRELATION_SAME_EQUIPMENT: Final = "same_equipment"
CORRELATION_LINE_CASCADE: Final = "line_cascade"
DEFAULT_WINDOW_SECONDS: Final = 300.0

_UUID_NAMESPACE = uuid.uuid5(
    uuid.NAMESPACE_URL, "industrial-maintenance:alarm-correlation"
)


@dataclass(slots=True, frozen=True)
class AlarmSnapshot:
    """Alarm snapshot input for correlation engine (decoupled from ORM)."""

    id: int
    equipment_id: int
    severity: str
    message: str
    created_at: datetime
    alarm_type: str | None = None


@dataclass(slots=True)
class CorrelationGroup:
    """A correlated event group (merged view of related alarms)."""

    group_id: str
    reason: str
    alarm_ids: list[int] = field(default_factory=list)
    equipment_ids: list[int] = field(default_factory=list)
    severity: str = "WARNING"
    window_start: datetime | None = None
    window_end: datetime | None = None

    @property
    def size(self) -> int:
        return len(self.alarm_ids)


def _group_id_for(alarm_ids: list[int]) -> str:
    members = ",".join(str(aid) for aid in sorted(alarm_ids))
    return uuid.uuid5(_UUID_NAMESPACE, members).hex


def _severity_rank(severity: str) -> int:
    return {"WARNING": 0, "CRITICAL": 1}.get(severity.upper(), 0)


def _snapshot_of(alarm: IndustrialAlarm) -> AlarmSnapshot:
    return AlarmSnapshot(
        id=alarm.id,
        equipment_id=alarm.equipment_id,
        severity=alarm.severity,
        message=alarm.message,
        created_at=alarm.created_at,
        alarm_type=_alarm_type_from_message(alarm.message),
    )


def _alarm_type_from_message(message: str) -> str:
    """Extract stable metric family from alarm text without introducing second classification model."""
    normalized = message.lower()
    rules = (
        (("bearing", "temperature"), "bearing_temperature"),
        (("vibration",), "vibration"),
        (("current", "load"), "motor_load"),
        (("voltage",), "voltage"),
        (("alarm bit", "alarm)"), "alarm_bit"),
    )
    for keywords, alarm_type in rules:
        if any(keyword in normalized for keyword in keywords):
            return alarm_type
    return "unknown"


def _types_are_related(left: AlarmSnapshot, right: AlarmSnapshot) -> bool:
    left_type = left.alarm_type or _alarm_type_from_message(left.message)
    right_type = right.alarm_type or _alarm_type_from_message(right.message)
    if left_type == right_type or "unknown" in {left_type, right_type}:
        return True
    # Temperature rise + vibration is a compound signal of bearing degradation; Alarm bit correlates with physical metrics.
    return {left_type, right_type} <= {
        "bearing_temperature",
        "vibration",
        "alarm_bit",
    }


def correlate_alarm_snapshots(
    snapshots: list[AlarmSnapshot],
    *,
    window_seconds: float = DEFAULT_WINDOW_SECONDS,
    line_lookup: dict[int, list[str]] | None = None,
) -> list[CorrelationGroup]:
    """Merge alarm snapshots into correlated event groups using deterministic rules.

    - Pass 1: same_equipment chained grouping (same equipment gap <= window);
    - Pass 2 (optional): line_cascade -- when ``line_lookup`` (equipment_id -> line list)
      is provided, groups on same line with overlapping time windows are merged.

    Returns groups sorted by window start; individual alarms form single-member groups.
    """
    ordered = sorted(snapshots, key=lambda item: (item.created_at, item.id))

    chains: list[list[AlarmSnapshot]] = []
    for snapshot in ordered:
        placed = False
        for chain in reversed(chains):
            tail = chain[-1]
            if tail.equipment_id != snapshot.equipment_id:
                continue
            if not _types_are_related(tail, snapshot):
                continue
            gap = (snapshot.created_at - tail.created_at).total_seconds()
            if 0 <= gap <= window_seconds:
                chain.append(snapshot)
                placed = True
                break
        if not placed:
            chains.append([snapshot])

    groups: list[CorrelationGroup] = [
        CorrelationGroup(
            group_id=_group_id_for([item.id for item in chain]),
            reason=CORRELATION_SAME_EQUIPMENT,
            alarm_ids=sorted(item.id for item in chain),
            equipment_ids=sorted({item.equipment_id for item in chain}),
            severity=max((item.severity for item in chain), key=_severity_rank),
            window_start=chain[0].created_at,
            window_end=chain[-1].created_at,
        )
        for chain in chains
    ]

    merged = _merge_line_cascades(groups, window_seconds, line_lookup or {})
    return sorted(merged, key=lambda group: (group.window_start, group.alarm_ids))


def _merge_line_cascades(
    groups: list[CorrelationGroup],
    window_seconds: float,
    line_lookup: dict[int, list[str]],
) -> list[CorrelationGroup]:
    """Merge groups by line cascade (returns unchanged if no line mapping)."""
    if not line_lookup:
        return groups

    parent = list(range(len(groups)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def lines_of(group: CorrelationGroup) -> set[str]:
        result: set[str] = set()
        for equipment_id in group.equipment_ids:
            result.update(line_lookup.get(equipment_id, []))
        return result

    for i in range(len(groups)):
        for j in range(i + 1, len(groups)):
            left, right = groups[i], groups[j]
            if not (lines_of(left) & lines_of(right)):
                continue
            assert left.window_start and left.window_end
            assert right.window_start and right.window_end
            overlap = (
                min(left.window_end, right.window_end)
                - max(left.window_start, right.window_start)
            ).total_seconds()
            if overlap >= -window_seconds:
                root_i, root_j = find(i), find(j)
                if root_i != root_j:
                    parent[max(root_i, root_j)] = min(root_i, root_j)

    buckets: dict[int, list[CorrelationGroup]] = {}
    for index, group in enumerate(groups):
        buckets.setdefault(find(index), []).append(group)

    result: list[CorrelationGroup] = []
    for members in buckets.values():
        if len(members) == 1:
            result.append(members[0])
            continue
        alarm_ids = sorted({aid for group in members for aid in group.alarm_ids})
        result.append(
            CorrelationGroup(
                group_id=_group_id_for(alarm_ids),
                reason=CORRELATION_LINE_CASCADE,
                alarm_ids=alarm_ids,
                equipment_ids=sorted(
                    {eid for group in members for eid in group.equipment_ids}
                ),
                severity=max((group.severity for group in members), key=_severity_rank),
                window_start=min(
                    (group.window_start for group in members if group.window_start),
                    default=None,
                ),
                window_end=max(
                    (group.window_end for group in members if group.window_end),
                    default=None,
                ),
            )
        )
    return result


def correlate_alarms(
    alarms: list[IndustrialAlarm],
    *,
    window_seconds: float = DEFAULT_WINDOW_SECONDS,
    production_line_by_equipment: dict[int, str | None] | None = None,
) -> list[CorrelationGroup]:
    """Convenience entry: correlate ORM alarm rows (optional equipment line mapping)."""
    lines: dict[int, list[str]] = {}
    for equipment_id, line in (production_line_by_equipment or {}).items():
        if line:
            lines.setdefault(equipment_id, []).append(line)
    snapshots = [_snapshot_of(alarm) for alarm in alarms]
    return correlate_alarm_snapshots(
        snapshots, window_seconds=window_seconds, line_lookup=lines or None
    )
