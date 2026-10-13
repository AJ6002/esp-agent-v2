"""Observability API: Trace Explorer and system operational health overview.

Security boundaries:

- Read-only router: zero PLC write, device command, approval, or work order creation endpoints;
- All endpoints require authenticated users;
- Responses sanitized (no tokens / secret keys / raw credentials).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import func, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user
from app.db.session import SessionLocal, get_db
from app.industrial_gateway.models import (
    GATEWAY_STATUS_CONNECTED,
    AlarmAnalysisRecord,
    GatewayConnection,
    IndustrialAlarm,
)
from app.models.intelligence import AgentRun, TelemetryRecord
from app.models.user import User
from app.models.workorder import WorkOrder, WorkOrderStatusEnum
from app.services.observability_service import MAX_LIMIT, get_trace, search_traces

router = APIRouter(prefix="/observability", tags=["observability"])


@router.get("/traces/{trace_id}")
def get_trace_detail(
    trace_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Reconstruct industrial event chain timeline by trace_id (real domain object aggregation)."""
    detail = get_trace(db, trace_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="No trace records found for this trace_id")
    return detail


@router.get("/traces")
def search_trace_list(
    trace_id: str | None = None,
    equipment_id: int | None = None,
    status: str | None = None,
    occurred_from: datetime | None = None,
    occurred_to: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Search industrial event traces with pagination (defaults descending by last active)."""
    return search_traces(
        db,
        trace_id=trace_id,
        equipment_id=equipment_id,
        status=status,
        occurred_from=occurred_from,
        occurred_to=occurred_to,
        limit=limit,
        offset=offset,
    )


@router.get("/metrics-summary")
def metrics_summary(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Core runtime metrics JSON summary (for frontend overview; Prometheus text via /metrics)."""

    def _count(model, *filters):  # type: ignore[no-untyped-def]
        query = db.query(func.count(model.id))
        for condition in filters:
            query = query.filter(condition)
        return int(query.scalar() or 0)

    try:
        telemetry_events = _count(TelemetryRecord)
        alarms_total = _count(IndustrialAlarm)
        alarms_active = _count(IndustrialAlarm, IndustrialAlarm.cleared_at.is_(None))
        work_orders_total = _count(WorkOrder)
        work_orders_open = _count(
            WorkOrder,
            WorkOrder.status.notin_(
                [
                    WorkOrderStatusEnum.completed,
                    WorkOrderStatusEnum.cancelled,
                ]
            ),
        )
        waiting_review = _count(
            AlarmAnalysisRecord,
            AlarmAnalysisRecord.analysis_status == "WAITING_REVIEW",
        )
        agent_runs = _count(AgentRun)

        latencies = (
            db.query(AgentRun.started_at, AgentRun.finished_at)
            .filter(
                AgentRun.started_at.is_not(None),
                AgentRun.finished_at.is_not(None),
            )
            .limit(500)
            .all()
        )
        durations = [
            (finished - started).total_seconds() * 1000
            for started, finished in latencies
            if finished and started
        ]
        agent_avg_latency_ms = (
            round(sum(durations) / len(durations), 1) if durations else None
        )

        trace_rows = (
            db.query(func.count(func.distinct(TelemetryRecord.trace_id)))
            .filter(TelemetryRecord.trace_id.is_not(None))
            .scalar()
        )
        traces_tracked = int(trace_rows or 0)

        return {
            "telemetry_events": telemetry_events,
            "alarms_total": alarms_total,
            "alarms_active": alarms_active,
            "work_orders_total": work_orders_total,
            "work_orders_open": work_orders_open,
            "analyses_waiting_review": waiting_review,
            "agent_runs_total": agent_runs,
            "agent_avg_latency_ms": agent_avg_latency_ms,
            "traces_tracked": traces_tracked,
        }
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503, detail=f"Database temporarily unavailable: {exc.__class__.__name__}"
        ) from exc


@router.get("/health")
def observability_health(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Platform operational health overview.

    Complements ``/health`` (liveness) and ``/ready`` (readiness);
    reports components with verifiable probe evidence only; marks untestable components as unknown.
    """
    components: dict[str, dict[str, Any]] = {}

    # Database: execute lightweight query.
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        components["database"] = {"status": "healthy"}
    except SQLAlchemyError as exc:
        components["database"] = {
            "status": "unavailable",
            "error_type": type(exc).__name__,
        }

    # Redis: probe only if configured; marked as unknown otherwise.
    if settings.REDIS_URL:
        try:
            Redis.from_url(settings.REDIS_URL).ping()
            components["redis"] = {"status": "healthy"}
        except RedisError as exc:
            components["redis"] = {
                "status": "unavailable",
                "error_type": type(exc).__name__,
            }
    else:
        components["redis"] = {"status": "unknown", "detail": "not_configured"}

    # Gateway: read connection status row. Probe = real DB status.
    row = db.query(GatewayConnection).first()
    if not settings.GATEWAY_ENABLED:
        gateway_status: Literal["healthy", "degraded", "unavailable", "unknown"] = (
            "unknown"
        )
        gateway_detail = "disabled"
    elif row is None:
        gateway_status = "unknown"
        gateway_detail = "no_connection_record"
    else:
        gateway_status = {
            GATEWAY_STATUS_CONNECTED: "healthy",
            "disconnected": "degraded",
            "error": "unavailable",
        }.get(row.status, "unknown")
        gateway_detail = f"status={row.status};mode={row.mode}"
    components["gateway"] = {"status": gateway_status, "detail": gateway_detail}

    # Worker / Scheduler: Redis heartbeat freshness (aligned with app.runtime keys).
    if settings.REDIS_URL:
        now = datetime.now().astimezone()
        for role in ("worker", "scheduler"):
            key = f"intelligent-maintenance:{role}:heartbeat"
            try:
                value = Redis.from_url(settings.REDIS_URL).get(key)
            except RedisError as exc:
                components[role] = {
                    "status": "unavailable",
                    "error_type": type(exc).__name__,
                }
                continue
            if not isinstance(value, str):
                components[role] = {"status": "unavailable", "detail": "no_heartbeat"}
                continue
            heartbeat = datetime.fromisoformat(value)
            age_seconds = abs((now - heartbeat).total_seconds())
            components[role] = {
                "status": "healthy" if age_seconds < 60 else "degraded",
                "heartbeat_age_seconds": round(age_seconds, 1),
            }
    else:
        components["worker"] = {"status": "unknown", "detail": "not_configured"}
        components["scheduler"] = {"status": "unknown", "detail": "not_configured"}

    # ML inference / RAG retrieval: reports verifiable facts only, never fabricates health state.
    components["ml_inference"] = {
        "status": "unknown",
        "detail": (
            "ai_provider_mock"
            if not settings.ai_actually_enabled
            else "provider_configured"
        ),
    }
    components["rag"] = {
        "status": "healthy"
        if components["database"]["status"] == "healthy"
        else "unavailable",
        "detail": "keyword_baseline_over_knowledge_base",
    }
    components["opentelemetry"] = {
        "status": "unknown" if not settings.OTEL_ENABLED else "healthy",
        "detail": "exporter_disabled"
        if not settings.OTEL_ENABLED
        else "otlp_configured",
        "sample_rate": settings.OTEL_TRACE_SAMPLE_RATE,
    }

    overall = "healthy"
    statuses = [value["status"] for value in components.values()]
    if any(status == "unavailable" for status in statuses) or any(
        status == "degraded" for status in statuses
    ):
        overall = "degraded"

    return {
        "status": overall,
        "checked_at": datetime.now().astimezone().isoformat(),
        "components": components,
    }
