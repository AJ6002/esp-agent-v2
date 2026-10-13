"""Industrial gateway database models: connection configs, node mappings, subscriptions, and alarm analysis.

Tables:

- ``gateway_connections``: Gateway connection (protocol, endpoint, status, last connect time).
- ``opcua_node_mappings``: OPC UA NodeId -> Platform equipment asset + metric mapping.
- ``gateway_subscriptions``: DataChange subscription (event-driven ingestion, read-only).
- ``industrial_alarms``: Industrial alarm (OPC UA Alarm semantics).
- ``alarm_analysis_records``: Alarm intelligence analysis findings (advisory only, no execution).

All models are additive; no existing business tables are modified.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin
from app.models.equipment import Equipment

PROTOCOL_OPCUA = "opcua"

# Gateway state machine: disconnected -> connected -> error (connection failure fallback)
GATEWAY_STATUS_DISCONNECTED = "disconnected"
GATEWAY_STATUS_CONNECTED = "connected"
GATEWAY_STATUS_ERROR = "error"


class GatewayConnection(TimestampMixin, Base):
    """Industrial protocol gateway connection config and operational status."""

    __tablename__ = "gateway_connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    protocol: Mapped[str] = mapped_column(
        String(24), default=PROTOCOL_OPCUA, index=True
    )
    endpoint: Mapped[str] = mapped_column(String(255))
    mode: Mapped[str] = mapped_column(String(16), default="mock")
    status: Mapped[str] = mapped_column(
        String(24), default=GATEWAY_STATUS_DISCONNECTED, index=True
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    poll_interval_seconds: Mapped[float] = mapped_column(Float, default=5.0)
    last_connected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)


class OpcUaNodeMapping(TimestampMixin, Base):
    """OPC UA node to platform equipment asset mapping (configurable, zero hardcoding)."""

    __tablename__ = "opcua_node_mappings"
    __table_args__ = (
        UniqueConstraint(
            "equipment_id",
            "metric_name",
            name="uq_opcua_node_mapping_equipment_metric",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    node_id: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipment.id", ondelete="CASCADE"), index=True
    )
    metric_name: Mapped[str] = mapped_column(String(64), index=True)
    unit: Mapped[str] = mapped_column(String(24), default="")
    scale: Mapped[float] = mapped_column(Float, default=1.0)
    offset: Mapped[float] = mapped_column(Float, default=0.0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    # Informational nodes (such as RunningState/Alarm) for display only, excluded from telemetry snapshots.
    informational: Mapped[bool] = mapped_column(Boolean, default=False)

    equipment: Mapped[Equipment] = relationship()


class GatewaySubscription(TimestampMixin, Base):
    """OPC UA DataChange subscription (event-driven ingestion, read-only)."""

    __tablename__ = "gateway_subscriptions"
    __table_args__ = (
        UniqueConstraint(
            "gateway_id",
            "node_id",
            name="uq_gateway_subscription_gateway_node",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    gateway_id: Mapped[int] = mapped_column(
        ForeignKey("gateway_connections.id", ondelete="CASCADE"), index=True
    )
    node_id: Mapped[str] = mapped_column(String(160), index=True)
    sampling_interval: Mapped[float] = mapped_column(Float, default=1000.0)
    status: Mapped[str] = mapped_column(String(24), default="inactive", index=True)
    last_event_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    event_count: Mapped[int] = mapped_column(Integer, default=0)


class IndustrialAlarm(TimestampMixin, Base):
    """Industrial alarm (platform record with OPC UA Alarm semantics).

    Lifecycle: Created (created_at) -> Acknowledged (acknowledged) -> Cleared (cleared_at).
    Created/cleared only on alarm state transitions, avoiding duplicate spam on high-frequency events.
    """

    __tablename__ = "industrial_alarms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipment.id", ondelete="CASCADE"), index=True
    )
    severity: Mapped[str] = mapped_column(String(16), index=True)  # WARNING/CRITICAL
    message: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(64), default="opcua", index=True)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    acknowledged_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    cleared_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    # Industrial event trace context: inherited from telemetry/subscription trace (NULL for legacy data).
    trace_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    equipment: Mapped[Equipment] = relationship()


class AlarmAnalysisRecord(TimestampMixin, Base):
    """Alarm Intelligence analysis record (1:1 attached to IndustrialAlarm).

    Positioning: Persisted findings of AI-assisted industrial alarm analysis --
    Understanding summary, root cause hypothesis, evidence chain, and maintenance recommendations. **Advisory only**:
    Any equipment operation must follow existing work orders and Human Approval workflows.
    """

    __tablename__ = "alarm_analysis_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alarm_id: Mapped[int] = mapped_column(
        ForeignKey("industrial_alarms.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    correlation_group_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )
    summary: Mapped[str] = mapped_column(Text)
    root_cause_hypothesis: Mapped[str] = mapped_column(Text)
    contributing_factors: Mapped[list[str]] = mapped_column(JSON, default=list)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    citations: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    recommended_actions: Mapped[list[str]] = mapped_column(JSON, default=list)
    suggested_priority: Mapped[str] = mapped_column(String(8), default="P3")
    related_work_order_id: Mapped[int | None] = mapped_column(
        ForeignKey("work_orders.id", ondelete="SET NULL"), nullable=True
    )
    created_work_order_id: Mapped[int | None] = mapped_column(
        ForeignKey("work_orders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    risk_level: Mapped[str] = mapped_column(String(16), default="MEDIUM", index=True)
    analysis_status: Mapped[str] = mapped_column(String(32), default="NEW", index=True)
    review_status: Mapped[str | None] = mapped_column(
        String(32), nullable=True, index=True
    )
    reviewed_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    requires_human_review: Mapped[bool] = mapped_column(Boolean, default=True)
    model_version: Mapped[str] = mapped_column(
        String(48), default="deterministic-rules-v1"
    )
    is_mock: Mapped[bool] = mapped_column(Boolean, default=True)
    # Industrial event trace context: inherited from parent IndustrialAlarm (NULL for legacy data).
    trace_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
