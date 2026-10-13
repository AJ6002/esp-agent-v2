"""Equipment mapping: OPC UA NodeId <-> Platform equipment asset + metric.

Mapping is fully configurable:

- Database table ``opcua_node_mappings`` is the single runtime source of truth;
- YAML config (default ``configs/opcua-node-mapping.yaml``) is used for initialization /
  reloading demo and field mappings, persisted via :func:`seed_mappings_from_config`;
- Zero hardcoded NodeIds in business logic code.

Metric names use friendly identifiers (``temperature`` / ``vibration`` / ...),
mapped via :data:`SNAPSHOT_FIELD_BY_METRIC` to platform telemetry snapshot fields.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

import yaml
from sqlalchemy.orm import Session

from app.industrial_gateway.models import OpcUaNodeMapping
from app.models.equipment import Equipment

DEFAULT_MAPPING_CONFIG = Path("configs/opcua-node-mapping.yaml")

# Friendly metric name -> TelemetrySnapshot field. Metrics not in table are informational
# (such as running / alarm), displayed for monitoring only, excluded from telemetry snapshots.
SNAPSHOT_FIELD_BY_METRIC: Final[dict[str, str]] = {
    "temperature": "bearing_temperature",
    "vibration": "vibration_rms",
    "current": "motor_current",
    "voltage": "motor_voltage",
    "speed": "rotational_speed",
    "load": "load_ratio",
    "ambient_temperature": "ambient_temperature",
}

INFORMATIONAL_METRICS: Final[frozenset[str]] = frozenset({"running", "alarm"})


def snapshot_field_for(metric_name: str) -> str | None:
    return SNAPSHOT_FIELD_BY_METRIC.get(metric_name.strip().lower())


@dataclass(slots=True, frozen=True)
class NodeMapping:
    """A resolved node mapping (equipment exists)."""

    node_id: str
    equipment_id: int
    equipment_code: str
    metric_name: str
    unit: str
    scale: float = 1.0
    offset: float = 0.0
    enabled: bool = True
    informational: bool = False

    @property
    def snapshot_field(self) -> str | None:
        return None if self.informational else snapshot_field_for(self.metric_name)

    def apply_scaling(self, value: float) -> float:
        """Apply scale/offset linear conversion (engineering unit conversion)."""
        return value * self.scale + self.offset


@dataclass(slots=True)
class MappingSeedResult:
    created: int = 0
    updated: int = 0
    skipped: list[str] = field(default_factory=list)


def load_all_mappings(db: Session) -> list[NodeMapping]:
    """Load all mapping rows (including disabled rows) for node list display."""
    rows = (
        db.query(OpcUaNodeMapping, Equipment.code)
        .join(Equipment, Equipment.id == OpcUaNodeMapping.equipment_id)
        .order_by(OpcUaNodeMapping.node_id)
        .all()
    )
    return [_to_node_mapping(mapping, code) for mapping, code in rows]


def load_mappings(db: Session) -> list[NodeMapping]:
    """Load all enabled node mappings from database (including equipment info)."""
    rows = (
        db.query(OpcUaNodeMapping, Equipment.code)
        .join(Equipment, Equipment.id == OpcUaNodeMapping.equipment_id)
        .filter(OpcUaNodeMapping.enabled.is_(True))
        .order_by(OpcUaNodeMapping.node_id)
        .all()
    )
    return [_to_node_mapping(mapping, code) for mapping, code in rows]


def _to_node_mapping(mapping: OpcUaNodeMapping, equipment_code: str) -> NodeMapping:
    return NodeMapping(
        node_id=mapping.node_id,
        equipment_id=mapping.equipment_id,
        equipment_code=equipment_code,
        metric_name=mapping.metric_name,
        unit=mapping.unit,
        scale=mapping.scale,
        offset=mapping.offset,
        enabled=mapping.enabled,
        informational=mapping.informational,
    )


def seed_mappings_from_config(
    db: Session,
    config_path: str | Path = DEFAULT_MAPPING_CONFIG,
) -> MappingSeedResult:
    """Sync YAML mapping config into database (upsert by node_id, idempotent).

    - ``equipment_code`` must resolve to platform equipment, otherwise skipped and logged;
    - Existing node_ids have attributes updated; new ones are created;
    - Existing mappings missing from config are not deleted (field manual mappings take priority).
    """
    path = Path(config_path)
    payload: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    entries: list[dict[str, Any]] = list(payload.get("mappings") or [])
    result = MappingSeedResult()

    for entry in entries:
        node_id = str(entry.get("node_id", "")).strip()
        equipment_code = str(entry.get("equipment_code", "")).strip()
        metric = str(entry.get("metric", "")).strip().lower()
        unit = str(entry.get("unit", "")).strip()
        if not node_id or not equipment_code or not metric:
            result.skipped.append(f"{node_id or '<empty>'}: Config missing required fields")
            continue

        equipment = db.query(Equipment).filter(Equipment.code == equipment_code).first()
        if equipment is None:
            result.skipped.append(
                f"{node_id}: Equipment code {equipment_code} does not exist in platform"
            )
            continue

        informational = (
            metric in INFORMATIONAL_METRICS or snapshot_field_for(metric) is None
        )
        defaults = {
            "equipment_id": equipment.id,
            "metric_name": metric,
            "unit": unit,
            "scale": float(entry.get("scale", 1.0)),
            "offset": float(entry.get("offset", 0.0)),
            "enabled": bool(entry.get("enabled", True)),
            "informational": bool(entry.get("informational", informational)),
        }
        existing = (
            db.query(OpcUaNodeMapping)
            .filter(OpcUaNodeMapping.node_id == node_id)
            .first()
        )
        if existing is None:
            db.add(OpcUaNodeMapping(node_id=node_id, **defaults))
            result.created += 1
        else:
            for key, value in defaults.items():
                setattr(existing, key, value)
            result.updated += 1

    db.commit()
    return result
