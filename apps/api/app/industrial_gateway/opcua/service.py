"""OPC UA Gateway service orchestration: Read -> Quality Check -> Mapping Aggregation -> Ingestion.

Responsibilities:

- Maintain connection status and failure fallback (no business writes on failure, backoff retry);
- **Polling**: Read all mapped nodes each sync cycle, validate via :class:`DataQualityLayer`;
- **Subscription (Event-driven)**: Receive OPC UA DataChange notifications, reuse the same quality and snapshot building path after event buffering (debounce / batch / dedup);
- Aggregate validated data by equipment into ``TelemetrySnapshot``;
- Call existing ``intelligence_service.ingest_snapshot`` to enter AI pipeline,
  **without bypassing** Health Score / Anomaly Detection / Fault Prediction / Work Order Generation,
  with zero duplicate AI pipelines.

Security: This service only invokes client ``read_node`` / ``subscribe``, with zero write paths.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import math
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy.orm import Session

if TYPE_CHECKING:  # pragma: no cover - required for type checking only
    from app.industrial_gateway.simulator.generator import MotorSimulator

from app.core.metrics import get_metrics
from app.core.otel import industrial_span
from app.core.trace import current_trace_id, start_trace
from app.db.session import SessionLocal
from app.gateways.equipment import TelemetrySnapshot
from app.industrial_gateway.alarms import (
    ALARM_STATE_NORMAL,
    build_alarm_message,
    evaluate_alarm_state,
)
from app.industrial_gateway.event_buffer import EventBuffer
from app.industrial_gateway.gateway import GatewayConfig
from app.industrial_gateway.mapping import (
    NodeMapping,
    load_all_mappings,
    load_mappings,
    seed_mappings_from_config,
)
from app.industrial_gateway.models import (
    GATEWAY_STATUS_CONNECTED,
    GATEWAY_STATUS_DISCONNECTED,
    GATEWAY_STATUS_ERROR,
    GatewayConnection,
    GatewaySubscription,
    IndustrialAlarm,
)
from app.industrial_gateway.opcua.client import OpcUaClient
from app.industrial_gateway.opcua.models import (
    QUALITY_BAD,
    QUALITY_UNCERTAIN,
    TELEMETRY_SOURCE_OPCUA,
    NodeRead,
    NodeSnapshotEntry,
)
from app.industrial_gateway.opcua.subscription import (
    SUBSCRIPTION_STATUS_ACTIVE,
    SUBSCRIPTION_STATUS_ERROR,
    SUBSCRIPTION_STATUS_STOPPED,
    MockSubscriptionClient,
    NodeDataChange,
    OpcUaSubscriptionClient,
    SubscriptionHandle,
)
from app.industrial_gateway.quality import (
    REASON_BAD_QUALITY,
    REASON_MISSING_VALUE,
    REASON_NON_NUMERIC,
    DataQualityLayer,
    UnitConversionError,
    convert_value,
)
from app.models.equipment import Equipment
from app.services.intelligence_service import ingest_snapshot

logger = logging.getLogger("app.industrial_gateway")

DEFAULT_CONNECTION_NAME = "primary-opcua"

# Platform metric fields required to form a complete assessment snapshot (aligned with assess_snapshot:
# Any missing field is treated as sensor failure, so incomplete snapshots are skipped as a batch).
REQUIRED_SNAPSHOT_FIELDS: tuple[str, ...] = (
    "vibration_rms",
    "bearing_temperature",
    "motor_current",
    "motor_voltage",
    "load_ratio",
)


@dataclass(slots=True)
class GatewaySyncResult:
    """Complete outcome of a single gateway sync (read -> validate -> persist)."""

    ok: bool = False
    error: str | None = None
    reads_total: int = 0
    accepted: int = 0
    rejected: int = 0
    corrections: int = 0
    reject_reasons: dict[str, int] = field(default_factory=dict)
    snapshots_ingested: int = 0
    snapshots_skipped: int = 0
    anomalies: int = 0
    work_orders_created: int = 0
    telemetry_ids: list[int] = field(default_factory=list)
    skipped_details: list[str] = field(default_factory=list)
    duration_ms: float = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "error": self.error,
            "reads_total": self.reads_total,
            "accepted": self.accepted,
            "rejected": self.rejected,
            "corrections": self.corrections,
            "reject_reasons": self.reject_reasons,
            "snapshots_ingested": self.snapshots_ingested,
            "snapshots_skipped": self.snapshots_skipped,
            "anomalies": self.anomalies,
            "work_orders_created": self.work_orders_created,
            "telemetry_ids": self.telemetry_ids,
            "skipped_details": self.skipped_details,
            "duration_ms": self.duration_ms,
        }


class OpcUaGatewayService:
    """OPC UA Gateway runtime: polling sync and DataChange subscription coexist.

    - Polling: ``sync_once`` periodic reads (preserving existing capabilities);
    - Subscription: DataChange event-driven after ``start_subscription``,
      events enter ``ingest_snapshot`` via the same quality gate and snapshot builder.
    """

    def __init__(
        self,
        client: OpcUaClient,
        *,
        mode: str,
        poll_interval_seconds: float = 5.0,
        auto_ingest: bool = True,
        mapping_config_path: str,
        connection_name: str = DEFAULT_CONNECTION_NAME,
        before_sync: Any = None,
        subscription_client_factory: Any = None,
        subscription_sampling_ms: float = 1000.0,
        subscription_debounce_ms: float = 1000.0,
        event_source: Any = None,
        session_factory: Any = None,
    ) -> None:
        self._client = client
        self._mode = mode
        self._poll_interval_seconds = poll_interval_seconds
        self._auto_ingest = auto_ingest
        self._mapping_config_path = mapping_config_path
        self._connection_name = connection_name
        # In mock mode, used to advance deterministic simulation tick before each sync.
        self._before_sync = before_sync
        # Subscription (event-driven): default client factory provided by runtime assembly.
        self._subscription_client_factory = subscription_client_factory
        self._subscription_sampling_ms = subscription_sampling_ms
        # Mock mode event source: returns DataChange events changed since last call.
        self._event_source = event_source
        # Session factory used by background flush loop (injectable for testing).
        self._session_factory = session_factory or SessionLocal

        self._quality = DataQualityLayer()
        self._lock = asyncio.Lock()
        self._sub_lock = asyncio.Lock()
        self._task: asyncio.Task[None] | None = None
        self._running = False

        self._status = GATEWAY_STATUS_DISCONNECTED
        self._last_error: str | None = None
        self._last_connected_at: datetime | None = None
        self._last_sync_at: datetime | None = None
        self._consecutive_failures = 0
        self._seed_error: str | None = None

        self._node_entries: dict[str, NodeSnapshotEntry] = {}
        self._last_result: GatewaySyncResult | None = None
        self._totals = {
            "reads_total": 0,
            "accepted": 0,
            "rejected": 0,
            "snapshots_ingested": 0,
            "snapshots_skipped": 0,
            "anomalies": 0,
            "work_orders_created": 0,
        }

        # --- Subscription (event-driven) state ---
        self._subscription_client: OpcUaSubscriptionClient | None = None
        self._subscription_handle: SubscriptionHandle | None = None
        self._subscription_status = SUBSCRIPTION_STATUS_STOPPED
        self._subscription_error: str | None = None
        self._buffer = EventBuffer(
            debounce_seconds=max(subscription_debounce_ms, 100.0) / 1000.0
        )
        # Per-node latest value cache: updated on event, used to build complete snapshot on flush.
        self._latest_values: dict[
            str, tuple[float | bool | int | str | None, datetime]
        ] = {}
        self._mapping_by_node: dict[str, NodeMapping] = {}
        self._flush_task: asyncio.Task[None] | None = None
        self._publish_task: asyncio.Task[None] | None = None
        self._event_totals = {
            "received": 0,
            "accepted": 0,
            "duplicates_suppressed": 0,
            "rejected": 0,
            "unknown_node": 0,
            "snapshots_ingested": 0,
            "snapshots_skipped": 0,
        }
        self._last_event_at: datetime | None = None
        self._last_event_summary: str | None = None
        # Industrial alarm state machine: equipment_id -> NORMAL/WARNING/CRITICAL.
        self._alarm_states: dict[int, str] = {}

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    @property
    def client(self) -> OpcUaClient:
        return self._client

    @property
    def connection_status(self) -> str:
        return self._status

    async def _connect(self) -> None:
        await self._client.connect()
        self._status = GATEWAY_STATUS_CONNECTED
        self._last_connected_at = datetime.now(UTC)
        self._last_error = None
        self._consecutive_failures = 0
        get_metrics().gateway_connected.labels(protocol="opcua", mode=self._mode).set(1)

    async def test_connection(self, db: Session) -> dict[str, Any]:
        """Test connection: connect and probe a mapped node; disconnect after probe if originally disconnected."""
        was_connected = self._client.connected
        started = time.perf_counter()
        probe_node: str | None = None
        sample: float | bool | int | str | None = None
        try:
            if not was_connected:
                await self._client.connect()
            mappings = load_mappings(db)
            if mappings:
                probe_node = mappings[0].node_id
                read = await self._client.read_node(probe_node)
                sample = read.value
            self._status = GATEWAY_STATUS_CONNECTED
            self._last_connected_at = datetime.now(UTC)
            self._last_error = None
            self._persist_state(db)
            return {
                "ok": True,
                "endpoint": self._client.endpoint,
                "latency_ms": round((time.perf_counter() - started) * 1000, 1),
                "probe_node": probe_node,
                "sample_value": sample,
                "error": None,
            }
        except Exception as exc:
            self._status = GATEWAY_STATUS_ERROR
            self._last_error = str(exc)
            self._persist_state(db)
            return {
                "ok": False,
                "endpoint": self._client.endpoint,
                "latency_ms": round((time.perf_counter() - started) * 1000, 1),
                "probe_node": probe_node,
                "sample_value": None,
                "error": str(exc),
            }
        finally:
            if not was_connected and self._client.connected:
                await self._client.disconnect()

    # ------------------------------------------------------------------
    # Sync (read -> quality -> aggregate -> persist)
    # ------------------------------------------------------------------

    async def sync_once(self, db: Session) -> GatewaySyncResult:
        """Execute a full sync. Safe fallback on connection failure: zero business writes."""
        async with self._lock:
            # Industrial event entry: each polling cycle has a new trace (read -> quality -> ingest shares trace).
            start_trace("gateway-poll")
            started = time.perf_counter()
            result = GatewaySyncResult()
            try:
                if not self._client.connected:
                    await self._connect()
            except Exception as exc:
                return self._record_failure(db, result, exc, started)

            try:
                await self._collect(db, result)
            except Exception as exc:  # Defensive: single sync error does not terminate polling process
                db.rollback()
                return self._record_failure(db, result, exc, started)

            result.ok = True
            self._status = GATEWAY_STATUS_CONNECTED
            self._last_sync_at = datetime.now(UTC)
            self._consecutive_failures = 0
            self._last_result = result
            self._accumulate_totals(result)
            self._persist_state(db)
            result.duration_ms = round((time.perf_counter() - started) * 1000, 1)
            return result

    def _record_failure(
        self,
        db: Session,
        result: GatewaySyncResult,
        exc: Exception,
        started: float,
    ) -> GatewaySyncResult:
        """Failure fallback: record error and consecutive failures, wait for backoff retry.

        Fallback guarantee: failure cycle writes zero business data, only updates gateway connection status.
        """
        result.error = str(exc)
        result.duration_ms = round((time.perf_counter() - started) * 1000, 1)
        self._status = GATEWAY_STATUS_ERROR
        self._last_error = str(exc)
        self._consecutive_failures += 1
        self._last_result = result
        get_metrics().gateway_connected.labels(protocol="opcua", mode=self._mode).set(0)
        logger.warning("Gateway sync failed (attempt %d): %s", self._consecutive_failures, exc)
        self._persist_state(db)
        return result

    async def _collect(self, db: Session, result: GatewaySyncResult) -> None:
        self.ensure_seed(db)
        mappings = load_mappings(db)
        if not mappings:
            result.snapshots_skipped += 1
            result.skipped_details.append("no_mappings: No node mappings configured")
            return

        if self._before_sync is not None:
            self._before_sync()

        reads: list[NodeRead] = []
        metrics = get_metrics()
        for mapping in mappings:
            entry = self._entry_for(mapping)
            try:
                read = await self._client.read_node(mapping.node_id)
            except Exception as exc:
                entry.last_error = str(exc)
                result.reads_total += 1
                metrics.gateway_events_total.labels(
                    protocol="opcua", mode=self._mode, status="error"
                ).inc()
                continue
            entry.last_error = None
            entry.last_value = read.value
            entry.last_quality = read.quality
            entry.last_timestamp = read.source_timestamp
            reads.append(read)
            result.reads_total += 1
            metrics.gateway_events_total.labels(
                protocol="opcua", mode=self._mode, status="received"
            ).inc()

        report = self._quality.process(reads)
        result.accepted = len(report.accepted)
        result.rejected = len(report.rejected)
        result.corrections = len(report.corrections)
        result.reject_reasons = report.reject_reasons()
        for rejected in report.rejected:
            metrics.gateway_quality_rejected_total.labels(reason=rejected.reason).inc()
            cached = self._node_entries.get(rejected.node_id)
            if cached is not None:
                cached.last_error = f"{rejected.reason}: {rejected.detail}"

        accepted_by_node = {read.node_id: read for read in report.accepted}
        grouped: dict[int, list[tuple[NodeMapping, NodeRead]]] = {}
        for mapping in mappings:
            accepted_read = accepted_by_node.get(mapping.node_id)
            if accepted_read is not None:
                grouped.setdefault(mapping.equipment_id, []).append(
                    (mapping, accepted_read)
                )

        for equipment_id, pairs in grouped.items():
            equipment = db.get(Equipment, equipment_id)
            if equipment is None:
                result.snapshots_skipped += 1
                result.skipped_details.append(f"equipment_{equipment_id}: Equipment not found")
                continue
            snapshot, missing = self._build_snapshot(equipment, pairs)
            if snapshot is None:
                result.snapshots_skipped += 1
                result.skipped_details.append(
                    f"{equipment.code}: Incomplete snapshot, missing {sorted(set(missing))}"
                )
                continue
            if not self._auto_ingest:
                result.snapshots_skipped += 1
                result.skipped_details.append(f"{equipment.code}: AUTO_INGEST is disabled")
                continue
            ingestion = ingest_snapshot(db, equipment, snapshot)
            result.snapshots_ingested += 1
            result.anomalies += int(ingestion.anomaly is not None)
            result.work_orders_created += int(ingestion.work_order is not None)
            result.telemetry_ids.append(ingestion.telemetry.id)

    def _entry_for(self, mapping: NodeMapping) -> NodeSnapshotEntry:
        entry = self._node_entries.get(mapping.node_id)
        if entry is None:
            entry = NodeSnapshotEntry(
                node_id=mapping.node_id,
                equipment_code=mapping.equipment_code,
                metric_name=mapping.metric_name,
                unit=mapping.unit,
                enabled=mapping.enabled,
                informational=mapping.informational,
            )
            self._node_entries[mapping.node_id] = entry
        return entry

    def _build_snapshot(
        self, equipment: Equipment, pairs: list[tuple[NodeMapping, NodeRead]]
    ) -> tuple[TelemetrySnapshot | None, list[str]]:
        fields: dict[str, float] = {}
        quality_floor = 1.0
        latest_ts: datetime | None = None
        missing: list[str] = []

        for mapping, read in pairs:
            if read.source_timestamp is not None and (
                latest_ts is None or read.source_timestamp > latest_ts
            ):
                latest_ts = read.source_timestamp
            if read.quality == QUALITY_UNCERTAIN:
                quality_floor = min(quality_floor, 0.5)

            field_name = mapping.snapshot_field
            if field_name is None:
                continue  # Informational nodes (running/alarm) are for display only
            try:
                value = convert_value(
                    mapping.metric_name,
                    mapping.unit,
                    float(read.value),  # type: ignore[arg-type]
                )
            except (UnitConversionError, TypeError, ValueError):
                missing.append(f"{mapping.metric_name}(unit={mapping.unit})")
                continue
            fields[field_name] = round(mapping.apply_scaling(value), 4)

        missing_required = [
            name for name in REQUIRED_SNAPSHOT_FIELDS if name not in fields
        ]
        if missing_required:
            missing.extend(missing_required)
            return None, missing

        return (
            TelemetrySnapshot(
                equipment_id=UUID(equipment.asset_uuid),
                collected_at=latest_ts or datetime.now(UTC),
                vibration_rms=fields.get("vibration_rms"),
                bearing_temperature=fields.get("bearing_temperature"),
                motor_current=fields.get("motor_current"),
                motor_voltage=fields.get("motor_voltage"),
                rotational_speed=fields.get("rotational_speed"),
                load_ratio=fields.get("load_ratio"),
                ambient_temperature=fields.get("ambient_temperature"),
                cumulative_runtime_hours=equipment.cumulative_runtime_hours,
                scenario=TELEMETRY_SOURCE_OPCUA,
                quality=quality_floor,
            ),
            [],
        )

    # ------------------------------------------------------------------
    # Subscription (event-driven): DataChange -> buffer -> snapshot -> existing AI pipeline
    # ------------------------------------------------------------------

    def on_data_change(self, event: NodeDataChange) -> None:
        """DataChange callback (synchronous, no blocking I/O): validation and buffering only.

        Flow: Node Mapping lookup -> single-event quality gate -> dedup buffer
        -> update latest value cache. Persistence is handled by flush loop.
        """
        self._event_totals["received"] += 1
        self._last_event_at = datetime.now(UTC)
        metrics = get_metrics()
        metrics.gateway_event_buffer_size.set(self._buffer.pending_count)
        mapping = self._mapping_by_node.get(event.node_id)
        if mapping is None:
            self._event_totals["unknown_node"] += 1
            self._last_event_summary = f"Unknown node {event.node_id} (unmapped)"
            return

        reason = _event_reject_reason(event)
        if reason is not None:
            self._event_totals["rejected"] += 1
            metrics.gateway_quality_rejected_total.labels(reason=reason).inc()
            entry = self._entry_for(mapping)
            entry.last_error = reason
            self._last_event_summary = f"{event.node_id} rejected ({reason})"
            return

        outcome = self._buffer.add(event)
        if outcome == "duplicate":
            self._event_totals["duplicates_suppressed"] += 1
            metrics.gateway_events_total.labels(
                protocol="opcua", mode=self._mode, status="duplicate"
            ).inc()
            return

        self._event_totals["accepted"] += 1
        metrics.gateway_events_total.labels(
            protocol="opcua", mode=self._mode, status="accepted"
        ).inc()
        timestamp = event.source_timestamp or datetime.now(UTC)
        self._latest_values[event.node_id] = (event.value, timestamp)
        entry = self._entry_for(mapping)
        entry.last_value = event.value
        entry.last_quality = event.quality
        entry.last_timestamp = timestamp
        entry.last_error = None
        self._last_event_summary = f"{event.node_id} = {event.value}"

    async def start_subscription(
        self,
        db: Session,
        *,
        client: OpcUaSubscriptionClient | None = None,
        sampling_interval_ms: float | None = None,
    ) -> dict[str, Any]:
        """Start DataChange subscription: connect -> subscribe -> prime cache -> flush loop."""
        async with self._sub_lock:
            if (
                self._subscription_status == SUBSCRIPTION_STATUS_ACTIVE
                and self._subscription_handle is not None
            ):
                return {
                    "ok": True,
                    "status": self._subscription_status,
                    "already_active": True,
                    "error": None,
                    **self.subscription_status(),
                }

            self.ensure_seed(db)
            self._refresh_mapping_cache(db)
            factory = self._subscription_client_factory
            sub_client = (
                client if client is not None else (factory() if factory else None)
            )
            if sub_client is None:
                self._subscription_status = SUBSCRIPTION_STATUS_ERROR
                self._subscription_error = "Subscription client factory not configured"
                return {
                    "ok": False,
                    "status": self._subscription_status,
                    "already_active": False,
                    "error": self._subscription_error,
                }

            sampling = sampling_interval_ms or self._subscription_sampling_ms
            node_ids = sorted(self._mapping_by_node)
            try:
                if not sub_client.connected:
                    await sub_client.connect()
                handle = await sub_client.subscribe(
                    node_ids,
                    self.on_data_change,
                    sampling_interval_ms=sampling,
                    publishing_interval_ms=sampling,
                )
            except Exception as exc:
                # Subscription failure fallback: zero business writes; polling path remains available.
                self._subscription_status = SUBSCRIPTION_STATUS_ERROR
                self._subscription_error = str(exc)
                logger.warning("Subscription start failed: %s", exc)
                return {
                    "ok": False,
                    "status": self._subscription_status,
                    "already_active": False,
                    "error": str(exc),
                }

            self._subscription_client = sub_client
            self._subscription_handle = handle
            self._subscription_status = SUBSCRIPTION_STATUS_ACTIVE
            self._subscription_error = None
            self._persist_subscriptions(db, handle)

            # Initial value priming: ensure latest value cache is complete before event-driven snapshots begin.
            await self._prime_latest_values(sub_client, node_ids)
            self._start_flush_loop()
            self._start_publish_loop()
            logger.info(
                "OPC UA DataChange subscription started: %d nodes (sampling=%sms)",
                len(handle.node_ids),
                sampling,
            )
            return {
                "ok": True,
                "status": self._subscription_status,
                "already_active": False,
                "error": None,
                **self.subscription_status(),
            }

    async def stop_subscription(self, db: Session) -> dict[str, Any]:
        """Stop subscription: flush buffer first, then unsubscribe and mark subscription row as stopped."""
        async with self._sub_lock:
            if self._subscription_status != SUBSCRIPTION_STATUS_ACTIVE:
                return {"ok": True, "status": self._subscription_status}
            await self.flush_now(db)
            await self._stop_publish_loop()
            await self._stop_flush_loop()
            handle = self._subscription_handle
            client = self._subscription_client
            if handle is not None and client is not None:
                with contextlib.suppress(Exception):
                    await client.unsubscribe(handle)
            self._subscription_handle = None
            self._subscription_status = SUBSCRIPTION_STATUS_STOPPED
            self._mark_subscriptions(db, "inactive")
            logger.info("OPC UA DataChange subscription stopped")
            return {"ok": True, "status": self._subscription_status}

    def _refresh_mapping_cache(self, db: Session) -> None:
        mappings = load_mappings(db)
        self._mapping_by_node = {m.node_id: m for m in mappings}

    async def _prime_latest_values(
        self, client: OpcUaSubscriptionClient, node_ids: list[str]
    ) -> None:
        for node_id in node_ids:
            mapping = self._mapping_by_node.get(node_id)
            if mapping is None or mapping.snapshot_field is None:
                continue  # Informational nodes do not participate in snapshot cache
            try:
                read = await client.read_node(node_id)
            except Exception as exc:
                logger.warning("Initial value priming failed %s: %s", node_id, exc)
                continue
            if read.source_timestamp is not None and read.value is not None:
                self._latest_values[node_id] = (read.value, read.source_timestamp)

    def _start_flush_loop(self) -> None:
        if self._flush_task is None or self._flush_task.done():
            self._flush_task = asyncio.create_task(self._flush_loop())

    def _start_publish_loop(self) -> None:
        """Mock mode: publish deterministic simulation node changes as DataChange events."""
        if self._mode != "mock" or self._event_source is None:
            return
        if not isinstance(self._subscription_client, MockSubscriptionClient):
            return
        if self._publish_task is None or self._publish_task.done():
            self._publish_task = asyncio.create_task(self._mock_publish_loop())

    async def _stop_publish_loop(self) -> None:
        task = self._publish_task
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
            self._publish_task = None

    async def _mock_publish_loop(self) -> None:
        interval = max(self._subscription_sampling_ms / 1000.0, 0.05)
        client = self._subscription_client
        while self._subscription_status == SUBSCRIPTION_STATUS_ACTIVE and isinstance(
            client, MockSubscriptionClient
        ):
            await asyncio.sleep(interval)
            source = self._event_source
            events = source() if source is not None else []
            for event in events:
                client.publish(event)

    async def _stop_flush_loop(self) -> None:
        task = self._flush_task
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
            self._flush_task = None

    async def _flush_loop(self) -> None:
        interval = max(self._buffer.debounce_seconds / 2.0, 0.05)
        while self._subscription_status == SUBSCRIPTION_STATUS_ACTIVE:
            await asyncio.sleep(interval)
            db = self._session_factory()
            try:
                await self.flush_due(db)
            except Exception:  # pragma: no cover - flush internally handled
                db.rollback()
            finally:
                db.close()

    async def flush_due(self, db: Session) -> dict[str, Any]:
        """Aggregate due buffered events into snapshots and feed into existing AI pipeline."""
        events = self._buffer.drain_due()
        get_metrics().gateway_event_buffer_size.set(self._buffer.pending_count)
        if not events:
            return await self._ingest_events(db, events)
        # Industrial event entry: a single flush (a batch of DataChanges) shares the same trace.
        start_trace("gateway-subscription-flush")
        return await self._timed_ingest(db, events)

    async def flush_now(self, db: Session) -> dict[str, Any]:
        """Flush buffer immediately, ignoring debounce (before stopping subscription / manual / test)."""
        events = self._buffer.force_drain()
        get_metrics().gateway_event_buffer_size.set(self._buffer.pending_count)
        if not events:
            return await self._ingest_events(db, events)
        start_trace("gateway-subscription-flush")
        return await self._timed_ingest(db, events)

    async def _timed_ingest(
        self, db: Session, events: list[NodeDataChange]
    ) -> dict[str, Any]:
        """Flush entry with latency observability (Observability does not alter business behavior)."""
        started = time.perf_counter()
        with industrial_span(
            "gateway.buffer_flush",
            {"gateway.mode": self._mode, "gateway.event_count": len(events)},
        ):
            try:
                return await self._ingest_events(db, events)
            finally:
                get_metrics().gateway_flush_latency_seconds.observe(
                    time.perf_counter() - started
                )

    async def demo_publish_ticks(
        self, db: Session, *, ticks: int = 1
    ) -> dict[str, Any]:
        """Demo only: synchronously advance mock simulation and flush (independent of background loop).

        Only manipulates in-process software simulator and existing subscription->quality->snapshot->AI pipeline;
        Contains zero external write operations. Directly rejected in non-mock mode.
        """
        if self._mode != "mock" or self._event_source is None:
            raise RuntimeError("demo publish requires gateway mock mode")
        # Demo prerequisite: load/refresh node mappings (shared with subscription path cache).
        self.ensure_seed(db)
        self._refresh_mapping_cache(db)

        from datetime import timedelta

        from app.industrial_gateway.opcua.subscription import NodeDataChange
        from app.industrial_gateway.simulator.generator import NODE_NAMES

        simulator = get_mock_simulator()
        if simulator is None:
            raise RuntimeError("mock simulator unavailable")

        # Each sampling tick publishes ALL mapped nodes (consistent with real DataChange semantics),
        # timestamps strictly monotonically increase (base + i seconds) -- avoiding duplicate suppression in quality layer.
        base_ts = datetime.now(UTC)
        published = 0
        for index in range(1, max(1, min(ticks, 24)) + 1):
            values = simulator.advance()
            ts = base_ts + timedelta(seconds=index)
            for name in NODE_NAMES:
                node_id = f"ns=2;s={simulator.prefix}.{name}"
                if node_id not in self._mapping_by_node:
                    continue  # Unmapped nodes do not enter platform pipeline
                event = NodeDataChange(
                    node_id=node_id,
                    value=values[name],
                    source_timestamp=ts,
                    status_code=0,
                    quality="good",
                )
                self.on_data_change(event)
                published += 1

        flush = await self.flush_now(db)
        return {
            "published_events": published,
            "trace_id": current_trace_id(),
            **flush,
        }

    async def _ingest_events(
        self, db: Session, events: list[NodeDataChange]
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "events": len(events),
            "snapshots_ingested": 0,
            "snapshots_skipped": 0,
            "anomalies": 0,
            "work_orders_created": 0,
            "telemetry_ids": [],
            "skipped_details": [],
        }
        if not events:
            return result

        equipment_nodes: dict[int, list[NodeMapping]] = {}
        for mapping in self._mapping_by_node.values():
            equipment_nodes.setdefault(mapping.equipment_id, []).append(mapping)

        for equipment_id, mappings in equipment_nodes.items():
            pairs: list[tuple[NodeMapping, NodeRead]] = []
            for mapping in mappings:
                cached = self._latest_values.get(mapping.node_id)
                if cached is None:
                    continue
                value, timestamp = cached
                pairs.append(
                    (
                        mapping,
                        NodeRead(
                            node_id=mapping.node_id,
                            value=value,
                            source_timestamp=timestamp,
                            quality="good",
                        ),
                    )
                )
            if not pairs:
                continue
            equipment = db.get(Equipment, equipment_id)
            if equipment is None:
                result["snapshots_skipped"] += 1
                continue
            snapshot, missing = self._build_snapshot(equipment, pairs)
            if snapshot is None:
                result["snapshots_skipped"] += 1
                result["skipped_details"].append(
                    f"{equipment.code}: Incomplete cache, missing {sorted(set(missing))}"
                )
                continue
            ingestion = ingest_snapshot(db, equipment, snapshot)
            result["snapshots_ingested"] += 1
            result["anomalies"] += int(ingestion.anomaly is not None)
            result["work_orders_created"] += int(ingestion.work_order is not None)
            result["telemetry_ids"].append(ingestion.telemetry.id)
            self._event_totals["snapshots_ingested"] += 1
            self._evaluate_alarm(db, equipment, snapshot)
            self._mark_subscription_events(db, len(events))
        return result

    def _evaluate_alarm(
        self, db: Session, equipment: Equipment, snapshot: TelemetrySnapshot
    ) -> None:
        """Industrial alarm state machine: create/resolve alarm records only on state transitions."""
        fields: dict[str, float | bool | None] = {
            "bearing_temperature": snapshot.bearing_temperature,
            "vibration_rms": snapshot.vibration_rms,
            "motor_current": snapshot.motor_current,
            "load_ratio": snapshot.load_ratio,
            "motor_voltage": snapshot.motor_voltage,
        }
        alarm_node_id = next(
            (
                node_id
                for node_id, mapping in self._mapping_by_node.items()
                if mapping.metric_name == "alarm"
            ),
            None,
        )
        alarm_active = False
        if alarm_node_id is not None:
            cached = self._latest_values.get(alarm_node_id)
            alarm_active = bool(cached[0]) if cached is not None else False

        state = evaluate_alarm_state(fields, alarm_active=alarm_active)
        previous = self._alarm_states.get(equipment.id, ALARM_STATE_NORMAL)
        if state == previous:
            return
        if state == ALARM_STATE_NORMAL:
            db.query(IndustrialAlarm).filter(
                IndustrialAlarm.equipment_id == equipment.id,
                IndustrialAlarm.cleared_at.is_(None),
            ).update({"cleared_at": datetime.now(UTC)}, synchronize_session=False)
        else:
            with industrial_span(
                "alarm.evaluate",
                {
                    "alarm.severity": state,
                    "equipment.id": equipment.id,
                },
            ):
                db.add(
                    IndustrialAlarm(
                        equipment_id=equipment.id,
                        severity=state,
                        message=build_alarm_message(
                            state, fields, alarm_active=alarm_active
                        ),
                        source="opcua-subscription",
                        trace_id=current_trace_id(),
                    )
                )
            get_metrics().industrial_alarm_total.labels(severity=state).inc()
        self._alarm_states[equipment.id] = state

    def subscription_status(self) -> dict[str, Any]:
        """Subscription running status (consumed directly by API layer)."""
        handle = self._subscription_handle
        return {
            "subscription_status": self._subscription_status,
            "sampling_interval_ms": (
                handle.sampling_interval_ms
                if handle
                else self._subscription_sampling_ms
            ),
            "active_nodes": list(handle.node_ids) if handle else [],
            "buffer_pending": self._buffer.pending_count,
            "event_totals": dict(self._event_totals),
            "last_event_at": _iso(self._last_event_at),
            "last_event": self._last_event_summary,
            "error": self._subscription_error,
            "read_only": True,
        }

    def _persist_subscriptions(self, db: Session, handle: SubscriptionHandle) -> None:
        try:
            row = self.ensure_connection_row(db)
            for node_id in handle.node_ids:
                existing = (
                    db.query(GatewaySubscription)
                    .filter(
                        GatewaySubscription.gateway_id == row.id,
                        GatewaySubscription.node_id == node_id,
                    )
                    .first()
                )
                if existing is None:
                    db.add(
                        GatewaySubscription(
                            gateway_id=row.id,
                            node_id=node_id,
                            sampling_interval=handle.sampling_interval_ms,
                            status="active",
                        )
                    )
                else:
                    existing.sampling_interval = handle.sampling_interval_ms
                    existing.status = "active"
            db.commit()
        except Exception:  # pragma: no cover - status persistence failure does not affect ingestion
            db.rollback()
            logger.exception("Failed to save subscription status")

    def _mark_subscriptions(self, db: Session, status: str) -> None:
        try:
            row = self.ensure_connection_row(db)
            db.query(GatewaySubscription).filter(
                GatewaySubscription.gateway_id == row.id
            ).update({"status": status}, synchronize_session=False)
            db.commit()
        except Exception:  # pragma: no cover
            db.rollback()
            logger.exception("Failed to update subscription status")

    def _mark_subscription_events(self, db: Session, event_count: int) -> None:
        try:
            row = self.ensure_connection_row(db)
            now = datetime.now(UTC)
            db.query(GatewaySubscription).filter(
                GatewaySubscription.gateway_id == row.id,
                GatewaySubscription.status == "active",
            ).update(
                {
                    "event_count": GatewaySubscription.event_count + event_count,
                    "last_event_at": now,
                },
                synchronize_session=False,
            )
            db.commit()
        except Exception:  # pragma: no cover
            db.rollback()

    # ------------------------------------------------------------------
    # Background polling
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start background polling task (must be called within event loop)."""
        if self._running:
            return
        self._running = True
        if not self._task or self._task.done():
            self._task = asyncio.create_task(self._run_loop())

    def stop(self) -> None:
        self._running = False

    async def wait_stopped(self) -> None:
        task = self._task
        if task is not None:
            self._running = False
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
            self._task = None

    async def _run_loop(self) -> None:
        while self._running:
            db = SessionLocal()
            try:
                await self.sync_once(db)
            except Exception:  # pragma: no cover - sync_once internally handled
                db.rollback()
            finally:
                db.close()
            # Failure backoff: multiply retry interval by 2^n on consecutive failures, up to 16x.
            backoff = min(2 ** min(self._consecutive_failures, 4), 16)
            await asyncio.sleep(self._poll_interval_seconds * backoff)

    # ------------------------------------------------------------------
    # Status, persistence, and config loading
    # ------------------------------------------------------------------

    def ensure_seed(self, db: Session) -> None:
        """Load YAML mapping config on first use (idempotent, only executes when table is empty)."""
        from app.industrial_gateway.models import OpcUaNodeMapping

        if db.query(OpcUaNodeMapping).count() > 0:
            return
        from pathlib import Path

        path = Path(self._mapping_config_path)
        if not path.exists():
            self._seed_error = f"Mapping config file not found: {path}"
            return
        result = seed_mappings_from_config(db, path)
        logger.info(
            "Loaded node mappings from %s: created %d, updated %d, skipped %d",
            path,
            result.created,
            result.updated,
            len(result.skipped),
        )

    @property
    def seed_error(self) -> str | None:
        return self._seed_error

    def reload_mappings(self, db: Session) -> dict[str, Any]:
        from pathlib import Path

        result = seed_mappings_from_config(db, Path(self._mapping_config_path))
        return {
            "created": result.created,
            "updated": result.updated,
            "skipped": result.skipped,
        }

    def ensure_connection_row(self, db: Session) -> GatewayConnection:
        row = (
            db.query(GatewayConnection)
            .filter(GatewayConnection.name == self._connection_name)
            .first()
        )
        if row is None:
            row = GatewayConnection(
                name=self._connection_name,
                protocol="opcua",
                endpoint=self._client.endpoint,
                mode=self._mode,
                status=self._status,
                poll_interval_seconds=self._poll_interval_seconds,
            )
            db.add(row)
            db.commit()
            db.refresh(row)
        return row

    def _persist_state(self, db: Session) -> None:
        try:
            row = self.ensure_connection_row(db)
            row.endpoint = self._client.endpoint
            row.mode = self._mode
            row.status = self._status
            row.poll_interval_seconds = self._poll_interval_seconds
            row.last_connected_at = self._last_connected_at
            row.last_sync_at = self._last_sync_at
            row.last_error = self._last_error
            db.commit()
        except Exception:  # pragma: no cover - status persistence failure does not affect ingestion
            db.rollback()
            logger.exception("Failed to save gateway connection status")

    def node_entries(self, db: Session) -> list[NodeSnapshotEntry]:
        """All current mapped nodes and their latest read status (including disabled rows)."""
        entries: list[NodeSnapshotEntry] = []
        for mapping in load_all_mappings(db):
            entry = NodeSnapshotEntry(
                node_id=mapping.node_id,
                equipment_code=mapping.equipment_code,
                metric_name=mapping.metric_name,
                unit=mapping.unit,
                enabled=mapping.enabled,
                informational=mapping.informational,
            )
            cached = self._node_entries.get(mapping.node_id)
            if cached is not None:
                entry.last_value = cached.last_value
                entry.last_quality = cached.last_quality
                entry.last_timestamp = cached.last_timestamp
                entry.last_error = cached.last_error
            entries.append(entry)
        return entries

    def status(self) -> dict[str, Any]:
        return {
            "mode": self._mode,
            "endpoint": self._client.endpoint,
            "connected": self._client.connected,
            "connection_status": self._status,
            "running": self._running,
            "poll_interval_seconds": self._poll_interval_seconds,
            "auto_ingest": self._auto_ingest,
            "read_only": True,
            "last_connected_at": _iso(self._last_connected_at),
            "last_sync_at": _iso(self._last_sync_at),
            "last_error": self._last_error,
            "consecutive_failures": self._consecutive_failures,
            "totals": dict(self._totals),
            "last_sync": self._last_result.to_dict() if self._last_result else None,
        }

    def _accumulate_totals(self, result: GatewaySyncResult) -> None:
        self._totals["reads_total"] += result.reads_total
        self._totals["accepted"] += result.accepted
        self._totals["rejected"] += result.rejected
        self._totals["snapshots_ingested"] += result.snapshots_ingested
        self._totals["snapshots_skipped"] += result.snapshots_skipped
        self._totals["anomalies"] += result.anomalies
        self._totals["work_orders_created"] += result.work_orders_created


def _iso(value: datetime | None) -> str | None:
    return value.astimezone(UTC).isoformat() if value else None


def _event_reject_reason(event: NodeDataChange) -> str | None:
    """Single-event quality gate: shares the same rejection rules with snapshot path."""
    if event.quality == QUALITY_BAD:
        return REASON_BAD_QUALITY
    if event.value is None:
        return REASON_MISSING_VALUE
    if isinstance(event.value, str):
        return REASON_NON_NUMERIC
    if (
        not isinstance(event.value, bool)
        and isinstance(event.value, float)
        and not math.isfinite(event.value)
    ):
        return REASON_NON_NUMERIC
    return None


# ----------------------------------------------------------------------
# Runtime assembly (module-level singleton)
# ----------------------------------------------------------------------

_gateway_runtime: OpcUaGatewayService | None = None
# In-process simulator under mock mode (demo scenario control target; None in non-mock mode).
_demo_simulator: MotorSimulator | None = None


def get_mock_simulator() -> MotorSimulator | None:
    """Return software simulator bound to Mock gateway runtime (exists only in mock mode)."""
    return _demo_simulator


def get_gateway_runtime() -> OpcUaGatewayService:
    """Assemble gateway runtime according to Settings (lazy singleton)."""
    global _gateway_runtime, _demo_simulator
    if _gateway_runtime is not None:
        return _gateway_runtime

    from app.core.config import settings
    from app.industrial_gateway.gateway import (
        build_client,
        build_subscription_client,
    )
    from app.industrial_gateway.opcua.client import MockOpcUaClient
    from app.industrial_gateway.simulator.generator import NODE_NAMES, MotorSimulator

    config: GatewayConfig = GatewayConfig.from_settings(settings)
    client = build_client(config)
    before_sync = None
    event_source = None
    if isinstance(client, MockOpcUaClient):
        # Mock mode: connect deterministic motor simulation as in-process equipment data source.
        simulator = MotorSimulator(seed=42, scenario="normal")
        _demo_simulator = simulator
        client.set_value_provider(simulator.value_provider())
        before_sync = simulator.advance

        # DataChange event source: advances one tick per call, returning changed node events.
        node_id_by_name = {
            name: f"ns=2;s={simulator.prefix}.{name}" for name in NODE_NAMES
        }

        def event_source() -> list[NodeDataChange]:
            values = simulator.advance()
            timestamp = datetime.now(UTC)
            return [
                NodeDataChange(
                    node_id=node_id_by_name[name],
                    value=values[name],
                    source_timestamp=timestamp,
                    status_code=0,
                    quality="good",
                )
                for name in simulator.changed_nodes
                if name in node_id_by_name
            ]

    _gateway_runtime = OpcUaGatewayService(
        client,
        mode=config.mode,
        poll_interval_seconds=config.poll_interval_seconds,
        auto_ingest=config.auto_ingest,
        mapping_config_path=config.mapping_config_path,
        before_sync=before_sync,
        subscription_client_factory=lambda: build_subscription_client(config),
        subscription_sampling_ms=config.subscription_sampling_ms,
        subscription_debounce_ms=config.subscription_debounce_ms,
        event_source=event_source,
    )
    return _gateway_runtime


def reset_gateway_runtime() -> None:
    """Testing only: reset runtime singleton."""
    global _gateway_runtime, _demo_simulator
    _gateway_runtime = None
    _demo_simulator = None
