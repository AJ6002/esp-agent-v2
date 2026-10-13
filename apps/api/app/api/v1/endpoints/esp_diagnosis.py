"""ESP APM Event Diagnosis API Endpoints.

Provides read-only access to Server 184 for real-time ESP fault diagnosis,
telemetry extraction, and Explainable AI (XAI) reports.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.esp_db import check_esp_db_health
from app.ai.client import llm_client
from app.ai.copilot import ask as ai_ask
from app.schemas.knowledge import AskRequest, AskResult
from app.schemas.esp_diagnosis import (
    ActiveWellSummary,
    DiagnoseEventRequest,
    ESPDiagnosisResponse,
    FleetInventoryReport,
    HybridRouteResult,
    PetroleumChunk,
    RecentEventSummary,
    WellHealthReport,
    WellProductionSummary,
)
from app.services.esp_diagnosis_service import (
    diagnose_esp_event,
    get_active_wells,
    get_fleet_inventory_status,
    get_recent_events,
    get_well_health_status,
    get_well_production_metrics,
    route_query_hybrid,
    search_petroleum_kb,
)

router = APIRouter(prefix="/esp", tags=["esp-apm-diagnosis"])


@router.post("/diagnose-event", response_model=ESPDiagnosisResponse)
def diagnose_event_endpoint(payload: DiagnoseEventRequest):
    """Diagnose an ESP trip event using deterministic math and domain knowledge."""
    try:
        return diagnose_esp_event(payload)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ESP Diagnosis failed: {str(e)}",
        )


@router.get("/recent-events", response_model=list[RecentEventSummary])
def recent_events_endpoint(limit: int = Query(default=20, ge=1, le=100)):
    """Retrieve recent tripped events from Server 184 PostgreSQL."""
    try:
        return get_recent_events(limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch recent events: {str(e)}",
        )


@router.get("/wells", response_model=list[ActiveWellSummary])
def active_wells_endpoint():
    """Retrieve list of active ESP wells and baseline profiles from Server 184."""
    try:
        return get_active_wells()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch active wells: {str(e)}",
        )


@router.get("/health")
def esp_service_health():
    """Check connectivity to PostgreSQL Server 184 and local Qwen 3B LLM."""
    db_ok = check_esp_db_health()
    return {
        "status": "healthy" if db_ok else "degraded",
        "esp_apm_db_connected": db_ok,
        "esp_apm_db_readonly": True,
        "llm_enabled": llm_client.enabled,
        "llm_model": llm_client.model,
        "llm_base": llm_client.api_base,
    }


@router.get("/kb/search", response_model=list[PetroleumChunk])
def kb_search_endpoint(query: str = Query(..., min_length=2), limit: int = Query(default=5, ge=1, le=20)):
    """Search 7,856 domain knowledge chunks from Server 184 PostgreSQL."""
    try:
        return search_petroleum_kb(query, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KB search failed: {str(e)}")


@router.get("/wells/{well_id}/health", response_model=WellHealthReport)
def well_health_endpoint(well_id: str):
    """Calculate deterministic health index and telemetry envelope status for a well."""
    try:
        return get_well_health_status(well_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Well health calculation failed: {str(e)}")


@router.get("/wells/{well_id}/production", response_model=WellProductionSummary)
def well_production_endpoint(well_id: str):
    """Retrieve production flow rates, water cut, and pressures for a well."""
    try:
        return get_well_production_metrics(well_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Well production retrieval failed: {str(e)}")


@router.get("/fleet/inventory", response_model=FleetInventoryReport)
def fleet_inventory_endpoint(cluster: str | None = Query(default=None)):
    """Retrieve fleet asset inventory and cluster breakdown from asset_registry."""
    try:
        return get_fleet_inventory_status(cluster=cluster)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fleet inventory retrieval failed: {str(e)}")


@router.get("/route-intent", response_model=HybridRouteResult)
def route_intent_endpoint(question: str = Query(..., min_length=1)):
    """Preview intent routing decision for a given maintenance query."""
    try:
        return route_query_hybrid(question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Routing decision failed: {str(e)}")


@router.post("/ask", response_model=AskResult)
def esp_ask_endpoint(payload: AskRequest, db: Session = Depends(get_db)):
    """Execute enterprise hybrid copilot ask query across Server 184 database and Qwen 3B synthesis."""
    try:
        return ai_ask(
            db,
            payload.question,
            payload.equipment_type_id,
            payload.fault_code,
            conversation_history=payload.conversation_history,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Copilot ask failed: {str(e)}")


