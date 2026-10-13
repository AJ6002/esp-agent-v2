"""Work order management endpoints: status transitions, checklists, logs, labor, spare parts, acceptance, reports."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload

from app.ai.copilot import generate_report as ai_generate_report
from app.core.deps import get_current_user, supervisor_or_admin, technician_or_above
from app.core.exceptions import bad_request, conflict, not_found, paginate
from app.db.session import get_db
from app.models.base import (
    EquipmentStatusEnum,
    FaultReportStatusEnum,
    KnowledgeCategoryEnum,
    WorkOrderStatusEnum,
)
from app.models.equipment import Equipment, FaultCode, SparePart
from app.models.knowledge import AcceptanceRecord, KnowledgeArticle
from app.models.maintenance import (
    Attachment,
    LaborEntry,
    MaintenanceLog,
    WorkOrderReport,
    WorkOrderSparePart,
)
from app.models.user import User
from app.models.workorder import (
    WorkOrder,
    WorkOrderAssignment,
    WorkOrderChecklistItem,
    WorkOrderStatusHistory,
)
from app.schemas.common import OkResponse, PageOut
from app.schemas.workorder import (
    AcceptRequest,
    AssignRequest,
    ChecklistItemOut,
    ChecklistItemUpdate,
    CompletionValidationError,
    LaborEntryCreate,
    LaborEntryOut,
    LaborEntryUpdate,
    MaintenanceLogCreate,
    MaintenanceLogOut,
    MaintenanceLogUpdate,
    RejectRequest,
    ReportGenerateResponse,
    ReportSectionOut,
    SafetyConfirmationRequest,
    SparePartUsageCreate,
    SparePartUsageOut,
    SparePartUsageUpdate,
    SubmitRequest,
    WorkOrderCreate,
    WorkOrderDetail,
    WorkOrderOut,
    WorkOrderUpdate,
)
from app.services.work_order_codes import generate_work_order_code
from app.services.workorder_service import change_status
from app.storage.backend import get_storage

router = APIRouter(prefix="/work-orders", tags=["work-orders"])

# Default checklist -- grouped by category
DEFAULT_CHECKLIST: list[dict] = [
    {"category": "safety", "content": "Equipment powered off", "is_required": True},
    {"category": "safety", "content": "Associated power sources disconnected", "is_required": True},
    {"category": "safety", "content": "Lockout/Tagout (LOTO) executed", "is_required": True},
    {"category": "safety", "content": "Residual energy dissipated", "is_required": True},
    {"category": "safety", "content": "Safety interlocks verified", "is_required": True},
    {"category": "safety", "content": "Site warning signs placed", "is_required": True},
    {"category": "safety", "content": "PPE worn", "is_required": True},
    {"category": "diagnosis", "content": "Read and record fault code", "is_required": True},
    {"category": "diagnosis", "content": "Check relevant component status", "is_required": True},
    {"category": "repair", "content": "Execute repair or replacement", "is_required": True},
    {"category": "repair", "content": "Restore power supply", "is_required": True},
    {"category": "testing", "content": "No-load test", "is_required": False},
    {"category": "testing", "content": "Load test", "is_required": True},
    {"category": "testing", "content": "Confirm equipment restored to normal", "is_required": True},
]

_HIGH_RISK_KEYWORDS = [
    "high voltage",
    "electrical",
    "hydraulic",
    "pneumatic",
    "high temperature",
    "rotating",
    "live circuit",
    "jumper",
    "short circuit",
    "bypass",
    "interlock",
]

# Prohibited hazardous operations hints
_PROHIBITED_KEYWORDS = ["live circuit", "jumper", "short circuit", "bypass"]

_EXECUTION_EDITABLE_STATUSES = {
    WorkOrderStatusEnum.accepted,
    WorkOrderStatusEnum.in_progress,
    WorkOrderStatusEnum.paused,
    WorkOrderStatusEnum.returned,
}


def _require_assignee(wo: WorkOrder, user: User) -> None:
    if wo.assignee_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the assigned engineer can perform this operation",
        )


def _require_execution_access(wo: WorkOrder, user: User) -> None:
    _require_assignee(wo, user)
    if wo.status not in _EXECUTION_EDITABLE_STATUSES:
        raise bad_request("Current work order status does not allow editing maintenance execution records")


def _is_high_risk(wo: WorkOrder) -> bool:
    risk_text = f"{wo.safety_risk or ''} {wo.fault_description or ''}".lower()
    return bool((wo.safety_risk or "").strip()) or any(
        keyword in risk_text for keyword in _HIGH_RISK_KEYWORDS
    )


def _require_safety_confirmation(
    wo: WorkOrder, payload: SafetyConfirmationRequest | None
) -> str | None:
    if not _is_high_risk(wo):
        return None

    if payload is None or not payload.confirmed or len(payload.note.strip()) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "HIGH_RISK_SAFETY_CONFIRMATION_REQUIRED",
                "message": "Safety measures must be confirmed with at least 8 characters of notes before starting high-risk work order",
            },
        )

    required_items = [
        item
        for item in wo.checklist_items
        if item.category == "safety" and item.is_required
    ]
    incomplete_items = [
        item.content
        for item in required_items
        if not item.is_completed or not item.completed_by or not item.completed_at
    ]
    if not required_items or incomplete_items:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "HIGH_RISK_SAFETY_CHECKLIST_INCOMPLETE",
                "message": "Required safety checklist items for high-risk work order are not all completed",
                "missing_items": incomplete_items or ["Safety checklist not configured"],
            },
        )

    return f"High-risk operation safety confirmation: {payload.note.strip()}"


def _safety_text(wo: WorkOrder) -> str | None:
    base = wo.safety_risk or ""
    if wo.equipment_id:
        eq = db_get_eq_risk(wo.equipment_id)
        if eq:
            base = (base + "；" if base else "") + eq
    return base or None


def db_get_eq_risk(eq_id: int) -> str | None:
    # Independent helper avoiding circular imports
    return None


def _to_out(wo: WorkOrder) -> WorkOrderOut:
    eq_name = eq_code = None
    if wo.equipment_id:
        eq = wo.equipment
        if eq:
            eq_name, eq_code = eq.name, eq.code
    fault_code = None
    creator_name = wo.creator.full_name if wo.creator else None
    assignee_name = wo.assignee.full_name if wo.assignee else None
    return WorkOrderOut(
        id=wo.id,
        code=wo.code,
        title=wo.title,
        equipment_id=wo.equipment_id,
        equipment_name=eq_name,
        equipment_code=eq_code,
        fault_report_id=wo.fault_report_id,
        fault_description=wo.fault_description,
        fault_code_id=wo.fault_code_id,
        fault_code=fault_code,
        order_type=wo.order_type,
        priority=wo.priority,
        status=wo.status,
        created_by_id=wo.created_by_id,
        creator_name=creator_name,
        assignee_id=wo.assignee_id,
        assignee_name=assignee_name,
        planned_start_at=wo.planned_start_at,
        planned_end_at=wo.planned_end_at,
        actual_start_at=wo.actual_start_at,
        actual_end_at=wo.actual_end_at,
        safety_risk=wo.safety_risk,
        requires_safety_confirmation=_is_high_risk(wo),
        ai_diagnosis_summary=wo.ai_diagnosis_summary,
        maintenance_steps=wo.maintenance_steps,
        acceptance_criteria=wo.acceptance_criteria,
        root_cause=wo.root_cause,
        action_taken=wo.action_taken,
        replaced_parts=wo.replaced_parts,
        test_result=wo.test_result,
        equipment_status_after=wo.equipment_status_after,
        follow_up_advice=wo.follow_up_advice,
        needs_observation=wo.needs_observation,
        completion_photos=wo.completion_photos,
        rejection_reason=wo.rejection_reason,
        submitted_at=wo.submitted_at,
        created_at=wo.created_at,
        updated_at=wo.updated_at,
    )


def _to_detail(db: Session, wo: WorkOrder) -> WorkOrderDetail:
    base = _to_out(wo).model_dump()
    fc = None
    if wo.fault_code_id:
        f = db.get(FaultCode, wo.fault_code_id)
        fc = f.code if f else None
    base["fault_code"] = fc
    base["checklist_items"] = [
        ChecklistItemOut.model_validate(c) for c in wo.checklist_items
    ]
    base["logs"] = [MaintenanceLogOut.model_validate(log) for log in wo.logs]
    base["labor_entries"] = [LaborEntryOut.model_validate(e) for e in wo.labor_entries]
    base["spare_parts"] = [SparePartUsageOut.model_validate(s) for s in wo.spare_parts]
    base["status_history"] = [
        {
            "id": h.id,
            "from_status": h.from_status,
            "to_status": h.to_status,
            "changed_by": h.changed_by,
            "changed_at": h.changed_at.isoformat() if h.changed_at else None,
            "remark": h.remark,
        }
        for h in wo.status_history
    ]
    return WorkOrderDetail(**base)


@router.get("", response_model=PageOut[WorkOrderOut])
def list_work_orders(
    status_filter: str | None = None,
    priority: str | None = None,
    assignee_id: int | None = None,
    equipment_id: int | None = None,
    keyword: str | None = None,
    mine: bool = False,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    q = db.query(WorkOrder).options(
        joinedload(WorkOrder.equipment),
        joinedload(WorkOrder.creator),
        joinedload(WorkOrder.assignee),
    )
    if status_filter:
        q = q.filter(WorkOrder.status == status_filter)
    if priority:
        q = q.filter(WorkOrder.priority == priority)
    if assignee_id:
        q = q.filter(WorkOrder.assignee_id == assignee_id)
    if equipment_id:
        q = q.filter(WorkOrder.equipment_id == equipment_id)
    if mine:
        q = q.filter(WorkOrder.assignee_id == user.id)
    if keyword:
        q = q.filter(
            WorkOrder.title.contains(keyword) | WorkOrder.code.contains(keyword)
        )
    q = q.order_by(WorkOrder.created_at.desc())
    items, total = paginate(q, page, page_size)
    return PageOut(
        items=[_to_out(w) for w in items], total=total, page=page, page_size=page_size
    )


@router.post("", response_model=WorkOrderDetail)
def create_work_order(
    payload: WorkOrderCreate,
    db: Session = Depends(get_db),
    user=Depends(supervisor_or_admin),
):
    wo = WorkOrder(
        code=generate_work_order_code(),
        **payload.model_dump(),
        status=WorkOrderStatusEnum.pending_dispatch,
        created_by_id=user.id,
        created_by=str(user.id),
    )
    # Safety risk identification
    risk_text = (payload.fault_description or "") + (payload.safety_risk or "")
    if any(k in risk_text for k in _HIGH_RISK_KEYWORDS):
        wo.safety_risk = (
            wo.safety_risk or ""
        ) + " (Caution: Involves high-risk hazards; safety measures must be confirmed prior to maintenance)"
    db.add(wo)
    db.flush()
    db.add(
        WorkOrderStatusHistory(
            work_order_id=wo.id,
            from_status=None,
            to_status=WorkOrderStatusEnum.pending_dispatch.value,
            changed_by=user.id,
            changed_at=datetime.now(UTC),
            remark="Manually created work order",
        )
    )
    # Generate default checklist by category
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
    db.commit()
    db.refresh(wo)
    return _to_detail(db, wo)


@router.get("/{wo_id}", response_model=WorkOrderDetail)
def get_work_order(
    wo_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)
):
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise not_found("Work order does not exist")
    return _to_detail(db, wo)


@router.put("/{wo_id}", response_model=WorkOrderDetail)
def update_work_order(
    wo_id: int,
    payload: WorkOrderUpdate,
    db: Session = Depends(get_db),
    user=Depends(supervisor_or_admin),
):
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise not_found("Work order does not exist")
    # Completed work orders cannot edit business fields
    if wo.status == WorkOrderStatusEnum.completed:
        raise bad_request("Completed work orders cannot be edited")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(wo, k, v)
    wo.updated_by = str(user.id)
    db.commit()
    db.refresh(wo)
    return _to_detail(db, wo)


@router.post("/{wo_id}/assign", response_model=WorkOrderDetail)
def assign(
    wo_id: int,
    payload: AssignRequest,
    db: Session = Depends(get_db),
    user=Depends(supervisor_or_admin),
):
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise not_found("Work order does not exist")
    tech = db.get(User, payload.assignee_id)
    if not tech or tech.role.value != "technician":
        raise bad_request("Can only assign to maintenance engineers")
    if wo.status not in {
        WorkOrderStatusEnum.pending_dispatch,
        WorkOrderStatusEnum.assigned,
    }:
        raise bad_request("Can only assign work orders in pending_dispatch or assigned status")
    if wo.status == WorkOrderStatusEnum.pending_dispatch:
        change_status(
            db,
            wo,
            WorkOrderStatusEnum.assigned,
            user.id,
            remark=f"Assigned to {tech.full_name}",
        )
    else:
        wo.updated_by = str(user.id)
    wo.assignee_id = payload.assignee_id
    if payload.priority:
        wo.priority = payload.priority
    if payload.planned_end_at:
        wo.planned_end_at = payload.planned_end_at
    # Mark old assignment as non-current
    db.query(WorkOrderAssignment).filter(
        WorkOrderAssignment.work_order_id == wo.id,
        WorkOrderAssignment.is_current.is_(True),
    ).update({WorkOrderAssignment.is_current: False})
    # Record assignment history
    db.add(
        WorkOrderAssignment(
            work_order_id=wo.id,
            assignee_id=payload.assignee_id,
            assigned_by=user.id,
            assigned_at=datetime.now(UTC),
            is_current=True,
        )
    )
    db.flush()
    db.commit()
    db.refresh(wo)
    return _to_detail(db, wo)


@router.post("/{wo_id}/accept", response_model=WorkOrderDetail)
def accept(
    wo_id: int, db: Session = Depends(get_db), user=Depends(technician_or_above)
):
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise not_found("Work order does not exist")
    _require_assignee(wo, user)
    change_status(db, wo, WorkOrderStatusEnum.accepted, user.id)
    db.commit()
    db.refresh(wo)
    return _to_detail(db, wo)


@router.post("/{wo_id}/start", response_model=WorkOrderDetail)
def start(
    wo_id: int,
    payload: SafetyConfirmationRequest | None = None,
    db: Session = Depends(get_db),
    user=Depends(technician_or_above),
):
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise not_found("Work order does not exist")
    _require_assignee(wo, user)
    safety_remark = _require_safety_confirmation(wo, payload)
    change_status(
        db,
        wo,
        WorkOrderStatusEnum.in_progress,
        user.id,
        remark=safety_remark,
    )
    db.commit()
    db.refresh(wo)
    return _to_detail(db, wo)


@router.post("/{wo_id}/pause", response_model=WorkOrderDetail)
def pause(wo_id: int, db: Session = Depends(get_db), user=Depends(technician_or_above)):
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise not_found("Work order does not exist")
    _require_assignee(wo, user)
    change_status(db, wo, WorkOrderStatusEnum.paused, user.id)
    db.commit()
    db.refresh(wo)
    return _to_detail(db, wo)


@router.post("/{wo_id}/resume", response_model=WorkOrderDetail)
def resume(
    wo_id: int,
    payload: SafetyConfirmationRequest | None = None,
    db: Session = Depends(get_db),
    user=Depends(technician_or_above),
):
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise not_found("Work order does not exist")
    _require_assignee(wo, user)
    safety_remark = _require_safety_confirmation(wo, payload)
    change_status(
        db,
        wo,
        WorkOrderStatusEnum.in_progress,
        user.id,
        remark=safety_remark,
    )
    db.commit()
    db.refresh(wo)
    return _to_detail(db, wo)


def _validate_completion(
    wo: WorkOrder, payload: SubmitRequest, db: Session
) -> list[str]:
    """Validate completion conditions, returning list of missing items."""
    missing: list[str] = []

    if not payload.root_cause or not payload.root_cause.strip():
        missing.append("root_cause")
    if not payload.action_taken or not payload.action_taken.strip():
        missing.append("action_taken")
    if not payload.test_result or not payload.test_result.strip():
        missing.append("test_result")

    # Required checklist items
    required_items = [c for c in wo.checklist_items if c.is_required]
    unfinished = [c.content for c in required_items if not c.is_completed]
    if unfinished:
        missing.append("required_checklist_items")

    # At least one maintenance log
    if not wo.logs:
        missing.append("maintenance_log")

    # At least one labor hour record
    if not wo.labor_entries:
        missing.append("labor_entry")

    # At least one testing checklist item completed
    test_items = [c for c in wo.checklist_items if c.category == "testing"]
    if not test_items or not any(c.is_completed for c in test_items):
        missing.append("test_step")

    # At least one photo for high-risk work order
    if _is_high_risk(wo):
        photos = payload.completion_photos or wo.completion_photos or []
        # Also check photos from maintenance logs
        log_photos: list[str] = []
        for log in wo.logs:
            if log.photos:
                log_photos.extend(log.photos)
        if not photos and not log_photos:
            missing.append("completion_photo")

    return missing


@router.post("/{wo_id}/submit", response_model=WorkOrderDetail)
def submit(
    wo_id: int,
    payload: SubmitRequest,
    db: Session = Depends(get_db),
    user=Depends(technician_or_above),
):
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise not_found("Work order does not exist")
    if wo.status == WorkOrderStatusEnum.pending_acceptance:
        raise conflict("Work order already submitted, awaiting acceptance")
    if wo.assignee_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only assigned engineer can submit completion"
        )
    # Completion validation
    missing = _validate_completion(wo, payload, db)
    if missing:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=CompletionValidationError(
                missing_requirements=missing
            ).model_dump(),
        )
    wo.root_cause = payload.root_cause
    wo.action_taken = payload.action_taken
    wo.replaced_parts = payload.replaced_parts
    wo.test_result = payload.test_result
    wo.equipment_status_after = payload.equipment_status_after
    wo.follow_up_advice = payload.follow_up_advice
    wo.needs_observation = payload.needs_observation
    if payload.completion_photos is not None:
        wo.completion_photos = payload.completion_photos
    change_status(db, wo, WorkOrderStatusEnum.pending_acceptance, user.id)
    # Fault report status kept as converted (in progress)
    if wo.fault_report_id:
        _sync_fault_report_status(db, wo.fault_report_id, "converted")
    db.commit()
    db.refresh(wo)
    return _to_detail(db, wo)


def _sync_fault_report_status(db: Session, fault_report_id: int, status: str) -> None:
    """Sync fault report status."""
    from app.models.fault import FaultReport

    fr = db.get(FaultReport, fault_report_id)
    if fr:
        fr.status = FaultReportStatusEnum(status)


def _create_knowledge_candidate(db: Session, wo: WorkOrder) -> None:
    """Auto-generate knowledge base candidate entry after acceptance."""
    # Prevent duplicate generation
    existing = (
        db.query(KnowledgeArticle)
        .filter(
            KnowledgeArticle.source == f"work_order_{wo.id}",
        )
        .first()
    )
    if existing:
        return
    eq_name = ""
    if wo.equipment_id:
        eq = db.get(Equipment, wo.equipment_id)
        if eq:
            eq_name = eq.name
    fault_code_str = None
    if wo.fault_code_id:
        fc = db.get(FaultCode, wo.fault_code_id)
        if fc:
            fault_code_str = fc.code
    title = f"[{eq_name or 'Equipment'}] {wo.title}"
    if fault_code_str:
        title += f" ({fault_code_str})"
    content_parts = [
        f"## Fault Symptoms\n{wo.fault_description or 'None recorded'}",
        f"## Fault Code\n{fault_code_str or 'None'}",
        f"## Root Cause\n{wo.root_cause or 'None recorded'}",
        f"## Actions Taken\n{wo.action_taken or 'None recorded'}",
        f"## Spare Parts Used\n{wo.replaced_parts or 'None'}",
        f"## Test Method\n{wo.test_result or 'None recorded'}",
        f"## Follow-up Recommendations\n{wo.follow_up_advice or 'Continuously observe equipment operational status'}",
    ]
    # Sanitize contact info and sensitive data
    import re

    cleaned = "\n\n".join(content_parts)
    cleaned = re.sub(r"1[3-9]\d{9}", "***", cleaned)
    cleaned = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "***", cleaned)
    article = KnowledgeArticle(
        title=title[:255],
        category=KnowledgeCategoryEnum.case,
        content=cleaned,
        summary=f"Maintenance case derived from work order {wo.code}. {wo.root_cause or ''}"[:500],
        source=f"work_order_{wo.id}",
        equipment_type_id=wo.equipment.equipment_type_id if wo.equipment else None,
        fault_code_id=wo.fault_code_id,
        status="draft",
    )
    db.add(article)


@router.post("/{wo_id}/approve", response_model=WorkOrderDetail)
def approve(
    wo_id: int,
    payload: AcceptRequest = AcceptRequest(),
    db: Session = Depends(get_db),
    user=Depends(supervisor_or_admin),
):
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise not_found("Work order does not exist")
    # Idempotent protection: completed work order returns conflict
    if wo.status == WorkOrderStatusEnum.completed:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "code": "WORK_ORDER_ALREADY_ACCEPTED",
                "message": "This work order has already completed acceptance",
                "work_order_id": wo_id,
            },
        )
    if wo.status != WorkOrderStatusEnum.pending_acceptance:
        raise bad_request("Can only accept work orders in pending_acceptance status")
    change_status(
        db,
        wo,
        WorkOrderStatusEnum.completed,
        user.id,
        remark=payload.acceptance_notes or "Acceptance approved",
    )
    # Equipment status sync
    if wo.equipment_id:
        eq = db.get(Equipment, wo.equipment_id)
        if eq:
            eq.status = EquipmentStatusEnum.running
            eq.last_maintenance_at = datetime.now(UTC).date()
    # Acceptance record
    db.add(
        AcceptanceRecord(
            work_order_id=wo.id,
            result="approved",
            reviewer_id=user.id,
            remark=payload.acceptance_notes or "Acceptance approved",
        )
    )
    # Fault report status sync
    if wo.fault_report_id:
        _sync_fault_report_status(db, wo.fault_report_id, "closed")
    # Generate maintenance report (AI version + template fallback)
    db.flush()
    try:
        report = ai_generate_report(db, wo_id, user.id)
        generation_method = "template" if report.is_mock else "ai"
    except Exception:
        report = ai_generate_report(db, wo_id, user.id, force_template=True)
        generation_method = "template"
    # Persist report
    # Mark old version as non-current
    db.query(WorkOrderReport).filter(
        WorkOrderReport.work_order_id == wo_id,
        WorkOrderReport.is_current == True,  # noqa: E712
    ).update({WorkOrderReport.is_current: False})
    persisted = WorkOrderReport(
        work_order_id=wo_id,
        version=_next_report_version(db, wo_id),
        generation_method=generation_method,
        summary=report.summary,
        sections=[s.model_dump() for s in report.sections] if report.sections else None,
        is_current=True,
        generated_by=user.id,
    )
    db.add(persisted)
    # Knowledge base candidate entry
    _create_knowledge_candidate(db, wo)
    db.commit()
    db.refresh(wo)
    return _to_detail(db, wo)


def _next_report_version(db: Session, wo_id: int) -> int:
    max_v = (
        db.query(WorkOrderReport).filter(WorkOrderReport.work_order_id == wo_id).count()
    )
    return max_v + 1


@router.post("/{wo_id}/reject", response_model=WorkOrderDetail)
def reject(
    wo_id: int,
    payload: RejectRequest,
    db: Session = Depends(get_db),
    user=Depends(supervisor_or_admin),
):
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise not_found("Work order does not exist")
    if wo.status == WorkOrderStatusEnum.completed:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "code": "WORK_ORDER_ALREADY_ACCEPTED",
                "message": "This work order has already completed acceptance",
                "work_order_id": wo_id,
            },
        )
    if not payload.remark or not payload.remark.strip():
        raise bad_request("Rejection reason cannot be empty")
    change_status(
        db,
        wo,
        WorkOrderStatusEnum.returned,
        user.id,
        remark=f"Acceptance rejected: {payload.remark}",
    )
    wo.rejection_reason = payload.remark
    db.add(
        AcceptanceRecord(
            work_order_id=wo.id,
            result="rejected",
            reviewer_id=user.id,
            remark=payload.remark,
        )
    )
    # Fault report status kept as in progress
    if wo.fault_report_id:
        _sync_fault_report_status(db, wo.fault_report_id, "converted")
    db.commit()
    db.refresh(wo)
    return _to_detail(db, wo)


@router.post("/{wo_id}/cancel", response_model=WorkOrderDetail)
def cancel(
    wo_id: int, db: Session = Depends(get_db), user=Depends(supervisor_or_admin)
):
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise not_found("Work order does not exist")
    change_status(db, wo, WorkOrderStatusEnum.cancelled, user.id)
    db.commit()
    db.refresh(wo)
    return _to_detail(db, wo)


# ---------- Checklist ----------


@router.put("/{wo_id}/checklist/{item_id}", response_model=WorkOrderDetail)
def update_checklist_item(
    wo_id: int,
    item_id: int,
    payload: ChecklistItemUpdate,
    db: Session = Depends(get_db),
    user=Depends(technician_or_above),
):
    item = db.get(WorkOrderChecklistItem, item_id)
    if not item or item.work_order_id != wo_id:
        raise not_found("Checklist item does not exist")
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise not_found("Work order does not exist")
    _require_execution_access(wo, user)
    if payload.is_completed is not None:
        item.is_completed = payload.is_completed
        item.completed_at = datetime.now(UTC) if payload.is_completed else None
        item.completed_by = user.id if payload.is_completed else None
    if payload.remark is not None:
        item.remark = payload.remark
    db.commit()
    return _to_detail(db, wo)


# ---------- Maintenance Logs ----------


@router.post("/{wo_id}/logs", response_model=MaintenanceLogOut)
def add_log(
    wo_id: int,
    payload: MaintenanceLogCreate,
    db: Session = Depends(get_db),
    user=Depends(technician_or_above),
):
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise not_found("Work order does not exist")
    _require_execution_access(wo, user)
    log = MaintenanceLog(
        work_order_id=wo_id,
        log_type=payload.log_type,
        content=payload.content,
        raw_content=payload.raw_content or payload.content,
        photos=payload.photos,
        operator_id=user.id,
        operator_name=user.full_name,
        logged_at=payload.logged_at or datetime.now(UTC),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return MaintenanceLogOut.model_validate(log)


@router.put("/{wo_id}/logs/{log_id}", response_model=MaintenanceLogOut)
def update_log(
    wo_id: int,
    log_id: int,
    payload: MaintenanceLogUpdate,
    db: Session = Depends(get_db),
    user=Depends(technician_or_above),
):
    log = db.get(MaintenanceLog, log_id)
    if not log or log.work_order_id != wo_id:
        raise not_found("Maintenance log does not exist")
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise not_found("Work order does not exist")
    _require_execution_access(wo, user)
    if payload.content is not None:
        log.content = payload.content
    if payload.log_type is not None:
        log.log_type = payload.log_type
    if payload.photos is not None:
        log.photos = payload.photos
    if payload.logged_at is not None:
        log.logged_at = payload.logged_at
    db.commit()
    db.refresh(log)
    return MaintenanceLogOut.model_validate(log)


# ---------- Labor Hours ----------


@router.post("/{wo_id}/labor", response_model=LaborEntryOut)
def add_labor(
    wo_id: int,
    payload: LaborEntryCreate,
    db: Session = Depends(get_db),
    user=Depends(technician_or_above),
):
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise not_found("Work order does not exist")
    _require_execution_access(wo, user)
    # Labor hour validation
    if payload.hours is not None and payload.hours <= 0:
        raise bad_request("Labor hours must be greater than 0")
    if (
        payload.started_at
        and payload.ended_at
        and payload.ended_at <= payload.started_at
    ):
        raise bad_request("End time cannot be earlier than start time")
    entry = LaborEntry(
        work_order_id=wo_id,
        started_at=payload.started_at,
        ended_at=payload.ended_at,
        hours=payload.hours,
        is_downtime=payload.is_downtime,
        operator_id=user.id,
        operator_name=payload.operator_name or user.full_name,
        remark=payload.remark,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return LaborEntryOut.model_validate(entry)


@router.put("/{wo_id}/labor/{entry_id}", response_model=LaborEntryOut)
def update_labor(
    wo_id: int,
    entry_id: int,
    payload: LaborEntryUpdate,
    db: Session = Depends(get_db),
    user=Depends(technician_or_above),
):
    entry = db.get(LaborEntry, entry_id)
    if not entry or entry.work_order_id != wo_id:
        raise not_found("Labor entry does not exist")
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise not_found("Work order does not exist")
    _require_execution_access(wo, user)
    if payload.started_at is not None:
        entry.started_at = payload.started_at
    if payload.ended_at is not None:
        entry.ended_at = payload.ended_at
    if payload.hours is not None:
        if payload.hours <= 0:
            raise bad_request("Labor hours must be greater than 0")
        entry.hours = payload.hours
    if payload.is_downtime is not None:
        entry.is_downtime = payload.is_downtime
    if payload.remark is not None:
        entry.remark = payload.remark
    # Cross validation
    if entry.started_at and entry.ended_at and entry.ended_at <= entry.started_at:
        raise bad_request("End time cannot be earlier than start time")
    db.commit()
    db.refresh(entry)
    return LaborEntryOut.model_validate(entry)


@router.delete("/{wo_id}/labor/{entry_id}", response_model=OkResponse)
def delete_labor(
    wo_id: int,
    entry_id: int,
    db: Session = Depends(get_db),
    user=Depends(technician_or_above),
):
    entry = db.get(LaborEntry, entry_id)
    if not entry or entry.work_order_id != wo_id:
        raise not_found("Labor entry does not exist")
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise not_found("Work order does not exist")
    _require_execution_access(wo, user)
    db.delete(entry)
    db.commit()
    return OkResponse(message="Labor entry deleted")


# ---------- Spare Parts ----------


@router.post("/{wo_id}/spare-parts", response_model=SparePartUsageOut)
def add_spare_part(
    wo_id: int,
    payload: SparePartUsageCreate,
    db: Session = Depends(get_db),
    user=Depends(technician_or_above),
):
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise not_found("Work order does not exist")
    _require_execution_access(wo, user)
    if payload.quantity <= 0:
        raise bad_request("Spare part quantity must be greater than 0")
    code = name = None
    if payload.spare_part_id:
        sp = db.get(SparePart, payload.spare_part_id)
        if sp:
            code, name = sp.code, sp.name
    usage = WorkOrderSparePart(
        work_order_id=wo_id,
        spare_part_id=payload.spare_part_id,
        spare_part_code=payload.spare_part_code or code,
        spare_part_name=payload.spare_part_name or name,
        quantity=payload.quantity,
        unit=payload.unit,
        remark=payload.remark,
    )
    db.add(usage)
    db.commit()
    db.refresh(usage)
    return SparePartUsageOut.model_validate(usage)


@router.put("/{wo_id}/spare-parts/{record_id}", response_model=SparePartUsageOut)
def update_spare_part(
    wo_id: int,
    record_id: int,
    payload: SparePartUsageUpdate,
    db: Session = Depends(get_db),
    user=Depends(technician_or_above),
):
    record = db.get(WorkOrderSparePart, record_id)
    if not record or record.work_order_id != wo_id:
        raise not_found("Spare part record does not exist")
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise not_found("Work order does not exist")
    _require_execution_access(wo, user)
    if payload.spare_part_id is not None:
        record.spare_part_id = payload.spare_part_id
    if payload.spare_part_code is not None:
        record.spare_part_code = payload.spare_part_code
    if payload.spare_part_name is not None:
        record.spare_part_name = payload.spare_part_name
    if payload.quantity is not None:
        if payload.quantity <= 0:
            raise bad_request("Spare part quantity must be greater than 0")
        record.quantity = payload.quantity
    if payload.unit is not None:
        record.unit = payload.unit
    if payload.remark is not None:
        record.remark = payload.remark
    db.commit()
    db.refresh(record)
    return SparePartUsageOut.model_validate(record)


@router.delete("/{wo_id}/spare-parts/{record_id}", response_model=OkResponse)
def delete_spare_part(
    wo_id: int,
    record_id: int,
    db: Session = Depends(get_db),
    user=Depends(technician_or_above),
):
    record = db.get(WorkOrderSparePart, record_id)
    if not record or record.work_order_id != wo_id:
        raise not_found("Spare part record does not exist")
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise not_found("Work order does not exist")
    _require_execution_access(wo, user)
    db.delete(record)
    db.commit()
    return OkResponse(message="Spare part record deleted")


# ---------- Attachments ----------


@router.post("/{wo_id}/attachments")
def upload_attachment(
    wo_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(technician_or_above),
):
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise not_found("Work order does not exist")
    _require_execution_access(wo, user)
    storage = get_storage()
    try:
        rel_path, url, size, ftype = storage.save(file, subdir=f"workorders/{wo_id}")
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
    att = Attachment(
        work_order_id=wo_id,
        file_name=file.filename,
        file_path=rel_path,
        file_url=url,
        file_type=ftype,
        file_size=size,
        uploaded_by=user.id,
    )
    db.add(att)
    db.commit()
    db.refresh(att)
    return {"id": att.id, "url": att.file_url, "file_name": att.file_name}


# ---------- Maintenance Report ----------


@router.get("/{wo_id}/report", response_model=ReportGenerateResponse)
def get_report(wo_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise not_found("Work order does not exist")
    report = (
        db.query(WorkOrderReport)
        .filter(
            WorkOrderReport.work_order_id == wo_id,
            WorkOrderReport.is_current == True,  # noqa: E712
        )
        .order_by(WorkOrderReport.created_at.desc())
        .first()
    )
    if not report:
        # If no persisted report exists, generate on the fly
        try:
            result = ai_generate_report(db, wo_id)
            return ReportGenerateResponse(
                work_order_id=wo.id,
                work_order_code=wo.code,
                summary=result.summary,
                sections=[
                    ReportSectionOut(title=s.title, content=s.content)
                    for s in result.sections
                ],
                generation_method="template" if result.is_mock else "ai",
                version=1,
                is_mock=result.is_mock,
            )
        except Exception:
            raise not_found("No report exists for this work order; please complete acceptance first") from None
    sections_out = [
        ReportSectionOut(title=s.get("title", ""), content=s.get("content", ""))
        for s in (report.sections or [])
    ]
    return ReportGenerateResponse(
        work_order_id=wo.id,
        work_order_code=wo.code,
        summary=report.summary,
        sections=sections_out,
        generation_method=report.generation_method,
        version=report.version,
        is_mock=report.generation_method == "template",
    )


@router.post("/{wo_id}/report/regenerate", response_model=ReportGenerateResponse)
def regenerate_report(
    wo_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise not_found("Work order does not exist")
    # Regeneration does not modify existing business data, only creates new report version
    try:
        result = ai_generate_report(db, wo_id, user.id)
        gen_method = "template" if result.is_mock else "ai"
    except Exception:
        result = ai_generate_report(db, wo_id, user.id, force_template=True)
        gen_method = "template"
    # Mark old version as non-current
    db.query(WorkOrderReport).filter(
        WorkOrderReport.work_order_id == wo_id,
        WorkOrderReport.is_current == True,  # noqa: E712
    ).update({WorkOrderReport.is_current: False})
    version = _next_report_version(db, wo_id)
    persisted = WorkOrderReport(
        work_order_id=wo_id,
        version=version,
        generation_method=gen_method,
        summary=result.summary,
        sections=[s.model_dump() for s in result.sections] if result.sections else None,
        is_current=True,
        generated_by=user.id,
    )
    db.add(persisted)
    db.commit()
    sections_out = [
        ReportSectionOut(title=s.title, content=s.content) for s in result.sections
    ]
    return ReportGenerateResponse(
        work_order_id=wo.id,
        work_order_code=wo.code,
        summary=result.summary,
        sections=sections_out,
        generation_method=gen_method,
        version=version,
        is_mock=result.is_mock,
    )
