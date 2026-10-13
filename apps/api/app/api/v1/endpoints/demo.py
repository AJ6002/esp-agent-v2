"""Demo orchestration endpoints (software simulator only; Simulation only).

Security boundaries:

- Scenario control affects in-process ``MotorSimulator`` only (Mock gateway data source);
- Refuses requests when ``GATEWAY_MODE=opcua`` (real OPC UA connection);
- Zero calls to ``EquipmentGateway.execute_command`` / ``write_node``;
- ``/demo/state`` is a read-only aggregation.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, supervisor_or_admin
from app.db.session import get_db
from app.industrial_gateway.simulator.generator import SUPPORTED_SCENARIOS
from app.models.user import User
from app.services.demo_service import get_demo_state

router = APIRouter(prefix="/demo", tags=["demo"])


class DemoScenarioRequest(BaseModel):
    scenario: str = Field(max_length=32)
    ticks: int = Field(default=0, ge=1, le=24)
    equipment_code: str = Field(default="Motor001", max_length=64)


def _require_mock_gateway() -> Any:
    """Validate Mock software gateway; real OPC UA mode refuses Demo orchestration."""
    from app.industrial_gateway.opcua.service import (
        get_gateway_runtime,
        get_mock_simulator,
    )

    # Security boundary: requires Mock mode only; real OPC UA mode is strictly refused.
    runtime = get_gateway_runtime()
    current_mode = runtime.status().get("mode")
    if current_mode != "mock":
        raise HTTPException(
            status_code=409,
            detail=(
                f"Demo simulator refused: gateway mode is '{current_mode}'. "
                "Scenario control is simulation-only and never targets real OPC UA servers."
            ),
        )
    simulator = get_mock_simulator()
    if simulator is None:
        raise HTTPException(status_code=409, detail="Mock simulator unavailable")
    return runtime


def _default_ticks(scenario: str) -> int:
    # Ticks required to deterministically cross warning thresholds (aligned with generator curves):
    # fault requires elapsed>=7 (+warmup 3), warning requires elapsed>=13 (+warmup 5).
    return {"normal": 2, "warning": 20, "fault": 14}[scenario]


@router.get("/state")
def demo_state(
    equipment_code: str = Query(default="Motor001", max_length=64),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Aggregate all real state required for a demo (read-only read model)."""
    return get_demo_state(db, equipment_code=equipment_code)


@router.post("/simulator/scenario")
async def set_demo_scenario(
    payload: DemoScenarioRequest,
    db: Session = Depends(get_db),
    _user: User = Depends(supervisor_or_admin),
) -> dict[str, Any]:
    """Switch simulator scenario and synchronously publish/flush DataChanges.

    Simulation only: advances in-process deterministic simulator, reusing subscription -> quality -> snapshot -> AI pipeline;
    zero PLC / device writes.
    """
    if payload.scenario not in SUPPORTED_SCENARIOS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported simulation scenario: {payload.scenario} (supported: {sorted(SUPPORTED_SCENARIOS)})",
        )
    runtime = _require_mock_gateway()

    from app.industrial_gateway.opcua.service import get_mock_simulator

    simulator = get_mock_simulator()
    assert simulator is not None  # _require_mock_gateway guarantees this
    try:
        simulator.set_scenario(payload.scenario)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    ticks = payload.ticks or _default_ticks(payload.scenario)
    result = await runtime.demo_publish_ticks(db, ticks=ticks)
    return {
        "scenario": payload.scenario,
        "ticks": ticks,
        "simulation_only": True,
        **result,
    }
