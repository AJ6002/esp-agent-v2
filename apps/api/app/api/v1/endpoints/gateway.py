"""Industrial protocol gateway API: connection status, node lists, connection testing, and manual sync.

All endpoints are read-only or trigger read-only ingestion; zero PLC write interfaces.
``/sync`` and ``/mappings/reload`` persist platform telemetry / mappings and are restricted to supervisor/admin.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, supervisor_or_admin
from app.db.session import get_db
from app.industrial_gateway.models import GatewaySubscription
from app.industrial_gateway.opcua.service import get_gateway_runtime
from app.industrial_gateway.schemas import (
    GatewayConnectionOut,
    GatewayNodesOut,
    GatewayStatusOut,
    GatewaySubscriptionRowOut,
    GatewaySyncOut,
    MappingReloadOut,
    SubscriptionActionOut,
    SubscriptionStatusOut,
    TestConnectOut,
)
from app.models.user import User

router = APIRouter(prefix="/gateway", tags=["industrial-gateway"])


@router.get("/status", response_model=GatewayStatusOut)
def gateway_status(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> GatewayStatusOut:
    """Gateway connection status: connection status / OPC UA server / last sync time."""
    from app.core.config import settings

    runtime = get_gateway_runtime()
    runtime.ensure_seed(db)
    connection = runtime.ensure_connection_row(db)
    return GatewayStatusOut(
        connection=GatewayConnectionOut.model_validate(connection),
        runtime=runtime.status(),
        enabled=settings.GATEWAY_ENABLED,
        read_only=True,
        seed_error=runtime.seed_error,
    )


@router.get("/nodes", response_model=GatewayNodesOut)
def gateway_nodes(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> GatewayNodesOut:
    """All currently mapped equipment nodes with latest reads and quality status."""
    runtime = get_gateway_runtime()
    runtime.ensure_seed(db)
    return GatewayNodesOut(
        nodes=runtime.node_entries(db),
        read_only=True,
    )


@router.post("/test-connect", response_model=TestConnectOut)
async def test_connect(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> TestConnectOut:
    """Test connection with OPC UA Server (read-only probe, no persistence)."""
    runtime = get_gateway_runtime()
    result = await runtime.test_connection(db)
    return TestConnectOut(**result)


@router.post("/sync", response_model=GatewaySyncOut)
async def gateway_sync(
    db: Session = Depends(get_db),
    _user: User = Depends(supervisor_or_admin),
) -> GatewaySyncOut:
    """Manually execute a read -> quality check -> telemetry ingestion sync."""
    runtime = get_gateway_runtime()
    runtime.ensure_seed(db)
    result = await runtime.sync_once(db)
    return GatewaySyncOut(**result.to_dict())


@router.post("/mappings/reload", response_model=MappingReloadOut)
def reload_mappings(
    db: Session = Depends(get_db),
    _user: User = Depends(supervisor_or_admin),
) -> MappingReloadOut:
    """Reload node mappings from YAML config (idempotent upsert by node_id)."""
    runtime = get_gateway_runtime()
    return MappingReloadOut(**runtime.reload_mappings(db))


@router.get("/subscriptions", response_model=SubscriptionStatusOut)
def subscription_status(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> SubscriptionStatusOut:
    """View DataChange subscription status: active nodes / sampling interval / event counts."""
    runtime = get_gateway_runtime()
    runtime.ensure_seed(db)
    status = runtime.subscription_status()
    connection = runtime.ensure_connection_row(db)
    rows = (
        db.query(GatewaySubscription)
        .filter(GatewaySubscription.gateway_id == connection.id)
        .order_by(GatewaySubscription.node_id)
        .all()
    )
    return SubscriptionStatusOut(
        ok=True,
        status=status["subscription_status"],
        rows=[GatewaySubscriptionRowOut.model_validate(row) for row in rows],
        **status,
    )


@router.post("/subscriptions/start", response_model=SubscriptionActionOut)
async def start_subscriptions(
    db: Session = Depends(get_db),
    _user: User = Depends(supervisor_or_admin),
) -> SubscriptionActionOut:
    """Start DataChange subscription (event-driven ingestion, read-only)."""
    runtime = get_gateway_runtime()
    result = await runtime.start_subscription(db)
    detail = {
        k: v
        for k, v in result.items()
        if k not in {"ok", "status", "already_active", "error"}
    }
    return SubscriptionActionOut(
        ok=result["ok"],
        status=result["status"],
        already_active=result.get("already_active", False),
        error=result.get("error"),
        detail=detail,
    )


@router.post("/subscriptions/stop", response_model=SubscriptionActionOut)
async def stop_subscriptions(
    db: Session = Depends(get_db),
    _user: User = Depends(supervisor_or_admin),
) -> SubscriptionActionOut:
    """Stop DataChange subscription (polling capability remains available)."""
    runtime = get_gateway_runtime()
    result = await runtime.stop_subscription(db)
    return SubscriptionActionOut(ok=result["ok"], status=result["status"])
