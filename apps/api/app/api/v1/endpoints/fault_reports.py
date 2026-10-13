"""Fault report endpoints."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.ai.copilot import parse_fault as ai_parse_fault
from app.core.deps import get_current_user, supervisor_or_admin
from app.core.exceptions import bad_request, not_found, paginate
from app.db.session import get_db
from app.models.base import (
    FaultReportStatusEnum,
    PriorityEnum,
    UrgencyEnum,
    WorkOrderStatusEnum,
    WorkOrderTypeEnum,
)
from app.models.fault import FaultReport
from app.models.workorder import (
    WorkOrder,
    WorkOrderChecklistItem,
    WorkOrderStatusHistory,
)
from app.schemas.common import PageOut
from app.schemas.fault import (
    ConvertToWorkOrderRequest,
    ConvertToWorkOrderResponse,
    FaultReportCreate,
    FaultReportDetail,
    FaultReportOut,
    ParseFaultRequest,
    ParseFaultResult,
)
from app.services.work_order_codes import generate_work_order_code

router = APIRouter(prefix="/fault-reports", tags=["fault-reports"])

DEFAULT_CHECKLIST: list[dict] = [
    {"category": "safety", "content": "Confirm equipment powered off", "is_required": True},
    {"category": "safety", "content": "Execute power cutoff", "is_required": True},
    {"category": "safety", "content": "Execute Lockout/Tagout (LOTO)", "is_required": True},
    {"category": "safety", "content": "Confirm residual energy dissipated", "is_required": True},
    {"category": "diagnosis", "content": "Read and record fault code", "is_required": True},
    {"category": "diagnosis", "content": "Check relevant component status", "is_required": True},
    {"category": "repair", "content": "Execute repair or replacement", "is_required": True},
    {"category": "repair", "content": "Restore power supply", "is_required": True},
    {"category": "testing", "content": "No-load test", "is_required": False},
    {"category": "testing", "content": "Load test", "is_required": True},
    {"category": "testing", "content": "Confirm equipment restored to normal", "is_required": True},
]

_HIGH_RISK_KEYWORDS = ["high voltage", "electrical", "hydraulic", "pneumatic", "high temperature", "rotating"]


def _urgency_to_priority(urgency: UrgencyEnum) -> PriorityEnum:
    mapping = {
        UrgencyEnum.critical: PriorityEnum.P1,
        UrgencyEnum.high: PriorityEnum.P2,
        UrgencyEnum.medium: PriorityEnum.P3,
        UrgencyEnum.low: PriorityEnum.P4,
    }
    return mapping.get(urgency, PriorityEnum.P3)


def _enforce_minimum_priority(
    requested: PriorityEnum, fault_report: FaultReport
) -> PriorityEnum:
    """Safety rule: must not be lower than priority required by business rules."""
    if fault_report.has_safety_risk:
        priority_order = {
            PriorityEnum.P1: 1,
            PriorityEnum.P2: 2,
            PriorityEnum.P3: 3,
            PriorityEnum.P4: 4,
        }
        if priority_order.get(requested, 3) > 2:
            return PriorityEnum.P2
    if fault_report.is_downtime and fault_report.affects_production:
        priority_order = {
            PriorityEnum.P1: 1,
            PriorityEnum.P2: 2,
            PriorityEnum.P3: 3,
            PriorityEnum.P4: 4,
        }
        if priority_order.get(requested, 3) > 2:
            return PriorityEnum.P2
    return requested


def _to_out(
    fr: FaultReport, related_work_order_id: int | None = None
) -> FaultReportOut:
    return FaultReportOut(
        id=fr.id,
        equipment_id=fr.equipment_id,
        equipment_name=fr.equipment.name if fr.equipment else None,
        equipment_code=fr.equipment.code if fr.equipment else None,
        title=fr.title,
        description=fr.description,
        occurred_at=fr.occurred_at,
        phenomenon=fr.phenomenon,
        is_downtime=fr.is_downtime,
        affects_production=fr.affects_production,
        has_safety_risk=fr.has_safety_risk,
        photos=fr.photos,
        reporter_name=fr.reporter_name,
        contact=fr.contact,
        urgency=fr.urgency,
        status=fr.status,
        raw_text=fr.raw_text,
        parsed_fields=fr.parsed_fields,
        fault_code_id=fr.fault_code_id,
        created_at=fr.created_at,
        related_work_order_id=related_work_order_id,
    )


def _to_detail(db: Session, fr: FaultReport) -> FaultReportDetail:
    related_work_order = (
        db.query(WorkOrder).filter(WorkOrder.fault_report_id == fr.id).first()
    )
    out = _to_out(fr, related_work_order.id if related_work_order is not None else None)
    return FaultReportDetail(
        id=out.id,
        equipment_id=out.equipment_id,
        equipment_name=out.equipment_name,
        equipment_code=out.equipment_code,
        title=out.title,
        description=out.description,
        occurred_at=out.occurred_at,
        phenomenon=out.phenomenon,
        is_downtime=out.is_downtime,
        affects_production=out.affects_production,
        has_safety_risk=out.has_safety_risk,
        photos=out.photos,
        reporter_name=out.reporter_name,
        contact=out.contact,
        urgency=out.urgency,
        status=out.status,
        raw_text=out.raw_text,
        parsed_fields=out.parsed_fields,
        fault_code_id=out.fault_code_id,
        created_at=out.created_at,
        related_work_order_id=out.related_work_order_id,
        related_work_order_code=(
            related_work_order.code if related_work_order is not None else None
        ),
        related_work_order_status=(
            related_work_order.status.value
            if related_work_order is not None and related_work_order.status
            else None
        ),
    )


@router.get("", response_model=PageOut[FaultReportOut])
def list_reports(
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(FaultReport).options(joinedload(FaultReport.equipment))
    if status:
        q = q.filter(FaultReport.status == status)
    q = q.order_by(FaultReport.created_at.desc())
    items, total = paginate(q, page, page_size)
    related_work_order_ids: dict[int, int] = {}
    if items:
        for fault_report_id, work_order_id in (
            db.query(WorkOrder.fault_report_id, WorkOrder.id)
            .filter(WorkOrder.fault_report_id.in_([item.id for item in items]))
            .order_by(WorkOrder.id)
            .all()
        ):
            if fault_report_id is not None:
                related_work_order_ids.setdefault(fault_report_id, work_order_id)
    return PageOut(
        items=[_to_out(f, related_work_order_ids.get(f.id)) for f in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=FaultReportOut)
def create_report(
    payload: FaultReportCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    fr = FaultReport(
        **payload.model_dump(exclude={"occurred_at", "reporter_name"}),
        occurred_at=payload.occurred_at or datetime.now(UTC),
        reporter_name=payload.reporter_name or user.full_name,
        created_by=str(user.id),
    )
    db.add(fr)
    db.commit()
    db.refresh(fr)
    return _to_out(fr)


@router.get("/{fr_id}", response_model=FaultReportDetail)
def get_report(fr_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    fr = db.get(FaultReport, fr_id)
    if not fr:
        raise not_found("Fault report does not exist")
    return _to_detail(db, fr)


@router.post("/parse", response_model=ParseFaultResult)
def parse_fault(
    payload: ParseFaultRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Parse natural language into structured fault fields (requires user confirmation before saving)."""
    return ai_parse_fault(db, payload.text, user.id)


@router.post(
    "/{fr_id}/convert-to-work-order", response_model=ConvertToWorkOrderResponse
)
def convert_to_work_order(
    fr_id: int,
    payload: ConvertToWorkOrderRequest = ConvertToWorkOrderRequest(),
    db: Session = Depends(get_db),
    user=Depends(supervisor_or_admin),
):
    """Convert fault report to maintenance work order within transaction."""
    # 1. Query fault report
    fr = db.get(FaultReport, fr_id)
    if not fr:
        raise not_found("Fault report does not exist")

    # 2. Permission validated in Depends (supervisor_or_admin)

    # 3. Check whether associated work order already exists
    existing = db.query(WorkOrder).filter(WorkOrder.fault_report_id == fr_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "FAULT_REPORT_ALREADY_CONVERTED",
                "message": "Maintenance work order already created for this fault report",
                "work_order_id": existing.id,
            },
        )

    # 4. Check whether status allows conversion
    if fr.status == FaultReportStatusEnum.closed:
        raise bad_request("Closed fault report cannot be converted to work order")

    # 5. Priority mapping (defaults, user override, and safety enforcement)
    priority = payload.priority or _urgency_to_priority(UrgencyEnum(fr.urgency))
    priority = _enforce_minimum_priority(priority, fr)

    # 6. Create work order in transaction
    try:
        wo = WorkOrder(
            code=generate_work_order_code(),
            title=fr.title,
            equipment_id=fr.equipment_id,
            fault_report_id=fr.id,
            fault_description=fr.description,
            fault_code_id=fr.fault_code_id,
            order_type=WorkOrderTypeEnum.fault_repair,
            priority=priority,
            status=WorkOrderStatusEnum.pending_dispatch,
            created_by_id=user.id,
            created_by=str(user.id),
            planned_start_at=payload.planned_start_at,
            planned_end_at=payload.planned_end_at,
        )

        # Safety risk identification
        risk_parts = []
        if fr.has_safety_risk:
            risk_parts.append("Fault report flagged with safety risk")
        if any(k in (fr.description or "").lower() for k in _HIGH_RISK_KEYWORDS):
            risk_parts.append("Caution: Involves high-risk hazards; safety measures must be confirmed prior to maintenance")
        if risk_parts:
            wo.safety_risk = "; ".join(risk_parts)

        db.add(wo)
        db.flush()

        # Generate default checklist
        for i, item in enumerate(DEFAULT_CHECKLIST):
            db.add(
                WorkOrderChecklistItem(
                    work_order_id=wo.id,
                    category=item["category"],
                    content=item["content"],
                    order=i,
                    is_required=item["is_required"],
                )
            )

        # Write work order status history
        now = datetime.now(UTC)
        db.add(
            WorkOrderStatusHistory(
                work_order_id=wo.id,
                from_status=None,
                to_status=WorkOrderStatusEnum.pending_dispatch.value,
                changed_by=user.id,
                changed_at=now,
                remark=payload.notes or "Created from fault report conversion",
            )
        )

        # 7. Update fault report status
        fr.status = FaultReportStatusEnum.converted
        fr.updated_by = str(user.id)

        db.commit()
        db.refresh(wo)

    except Exception:
        db.rollback()
        raise

    return ConvertToWorkOrderResponse(
        fault_report_id=fr.id,
        work_order_id=wo.id,
        work_order_code=wo.code,
        priority=wo.priority.value if wo.priority else "P3",
        status=wo.status.value if wo.status else "pending_dispatch",
    )
