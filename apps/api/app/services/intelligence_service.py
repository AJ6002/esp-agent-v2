"""Deterministic closed-loop from telemetry to prediction, maintenance strategy, work orders, and knowledge capture."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.ai.knowledge_search import search_articles
from app.core.metrics import get_metrics
from app.core.otel import traced_span
from app.core.trace import current_trace_id, start_trace
from app.gateways.equipment import TelemetrySnapshot
from app.gateways.notifications import notification_gateway
from app.models.base import (
    EquipmentStatusEnum,
    KnowledgeCategoryEnum,
    PriorityEnum,
    RiskLevelEnum,
    RoleEnum,
    WorkOrderStatusEnum,
    WorkOrderTypeEnum,
)
from app.models.equipment import Equipment, SparePart
from app.models.intelligence import (
    AgentRun,
    AnomalyEvent,
    EquipmentSensor,
    FaultDiagnosis,
    MaintenanceRecommendation,
    MaintenanceVerification,
    OperationApproval,
    RiskPrediction,
    SparePartReservation,
    TelemetryRecord,
    ToolInvocation,
)
from app.models.knowledge import KnowledgeArticle
from app.models.user import TechnicianProfile, User
from app.models.workorder import (
    WorkOrder,
    WorkOrderAssignment,
    WorkOrderChecklistItem,
    WorkOrderStatusHistory,
)
from app.services.work_order_codes import generate_work_order_code


@dataclass(slots=True)
class TelemetryAssessment:
    is_anomaly: bool
    health_score: float
    risk_level: RiskLevelEnum
    fault_type: str | None
    title: str | None
    diagnosis: str | None
    confidence: float
    anomaly_metrics: list[str]
    evidence: dict[str, Any]


@dataclass(slots=True)
class IngestionResult:
    telemetry: TelemetryRecord
    anomaly: AnomalyEvent | None
    prediction: RiskPrediction | None
    recommendation: MaintenanceRecommendation | None
    work_order: WorkOrder | None


SCENARIO_FAULT_MAP = {
    "temperature_rise": ("bearing_overheat", "Continuous Bearing Temperature Rise"),
    "vibration_spike": ("rotor_unbalance", "Vibration Spike, Suspected Rotor Unbalance"),
    "current_overload": ("motor_overload", "Continuous Motor Overload"),
    "bearing_wear": ("bearing_wear", "Bearing Wear Trend"),
    "voltage_fluctuation": ("voltage_abnormal", "Supply Voltage Fluctuation"),
    "sensor_disconnect": ("sensor_abnormal", "Equipment Sensor Data Disruption"),
    "composite_anomaly": ("unknown_anomaly", "Composite Multi-Metric Anomaly"),
}

FAULT_GUIDANCE = {
    "bearing_wear": (
        "Simultaneous deterioration in vibration and temperature trends; prioritize checking bearing clearance, raceway wear, and lubrication status.",
        "Plan shutdown to inspect bearings; retest vibration spectrum, replace bearings if necessary, and adjust lubrication.",
        ["Mechanical Maintenance", "Instrumentation & Calibration"],
        ["Bearing", "Gearbox Oil"],
    ),
    "bearing_overheat": (
        "Bearing temperature exceeds operating threshold; may be caused by insufficient lubrication, overtight installation, or bearing wear.",
        "Reduce load and schedule maintenance window; inspect lubrication, bearing clearance, and cooling conditions.",
        ["Mechanical Maintenance"],
        ["Bearing", "Gearbox Oil"],
    ),
    "motor_overload": (
        "Load ratio or current continuously exceeds limits; risk of winding overheating and protective tripping.",
        "Verify process load and transmission resistance; check three-phase current balance and clear mechanical jams before restart.",
        ["Electrical Maintenance", "Mechanical Maintenance"],
        ["Contactor", "Bearing"],
    ),
    "rotor_unbalance": (
        "Sudden increase in vibration RMS while speed remains stable; consistent with rotor unbalance or loose components.",
        "Stop machine and check fasteners, impellers, and couplings; perform dynamic balancing followed by no-load and load validation.",
        ["Mechanical Maintenance", "Instrumentation & Calibration"],
        ["Bearing"],
    ),
    "shaft_misalignment": (
        "Simultaneous rise in vibration and current; investigate coupling and shaft misalignment.",
        "Execute LOTO, check soft foot and coupling alignment, correct, and retest vibration.",
        ["Mechanical Maintenance", "Instrumentation & Calibration"],
        ["Coupling"],
    ),
    "insufficient_lubrication": (
        "Bearing temperature rise accompanied by moderate vibration; high probability of insufficient lubrication.",
        "Confirm grease type, replenishment interval, and oil line condition; replenish or replace per equipment manual.",
        ["Mechanical Maintenance"],
        ["Gearbox Oil"],
    ),
    "voltage_abnormal": (
        "Motor terminal voltage outside allowable fluctuation range; may cause current anomalies and insulation degradation.",
        "Licensed electrician must check power supply, wiring, and inverter output; resume operation after voltage stabilizes.",
        ["Electrical Maintenance", "Instrumentation & Calibration"],
        ["Contactor", "Inverter"],
    ),
    "sensor_abnormal": (
        "Telemetry quality is zero or key metrics are missing; equipment health cannot be reliably determined.",
        "Check sensor power supply, wiring, and gateway; use manual inspection rounds until resolved.",
        ["Instrumentation & Calibration", "Electrical Maintenance"],
        ["Proximity Switch"],
    ),
    "unknown_anomaly": (
        "Multiple metrics out of limits simultaneously; rule model cannot uniquely determine root cause.",
        "Enter controlled shutdown and manual diagnostic procedure; troubleshoot against manuals, spectra, and historical cases.",
        ["Mechanical Maintenance", "Electrical Maintenance", "Instrumentation & Calibration"],
        ["Bearing", "Proximity Switch"],
    ),
}

SENSOR_DEFINITIONS = {
    "vibration_rms": ("Vibration RMS", "mm/s", None, 4.5, None, 7.1),
    "bearing_temperature": ("Bearing Temperature", "°C", None, 75.0, None, 90.0),
    "motor_current": ("Motor Current", "A", None, 27.0, None, 32.0),
    "motor_voltage": ("Motor Voltage", "V", 342.0, 418.0, 320.0, 440.0),
    "rotational_speed": ("Rotational Speed", "rpm", 1350.0, 1550.0, 1200.0, 1650.0),
    "load_ratio": ("Load Ratio", "%", None, 100.0, None, 115.0),
    "ambient_temperature": ("Ambient Temperature", "°C", None, 40.0, None, 50.0),
    "cumulative_runtime_hours": ("Cumulative Runtime Hours", "h", None, None, None, None),
}


def assess_snapshot(snapshot: TelemetrySnapshot) -> TelemetryAssessment:
    values = {
        "Vibration RMS": snapshot.vibration_rms,
        "Bearing Temperature": snapshot.bearing_temperature,
        "Motor Current": snapshot.motor_current,
        "Motor Voltage": snapshot.motor_voltage,
        "Load Ratio": snapshot.load_ratio,
    }
    anomaly_metrics: list[str] = []
    deductions = 0.0

    if snapshot.quality <= 0 or any(value is None for value in values.values()):
        anomaly_metrics.append("Telemetry Quality")
        sensor_fault_type, sensor_title = SCENARIO_FAULT_MAP["sensor_disconnect"]
        return TelemetryAssessment(
            True,
            42.0,
            RiskLevelEnum.high,
            sensor_fault_type,
            sensor_title,
            FAULT_GUIDANCE[sensor_fault_type][0],
            0.99,
            anomaly_metrics,
            {"quality": snapshot.quality, **values},
        )

    assert snapshot.vibration_rms is not None
    assert snapshot.bearing_temperature is not None
    assert snapshot.motor_current is not None
    assert snapshot.motor_voltage is not None
    assert snapshot.load_ratio is not None

    if snapshot.vibration_rms > 4.5:
        anomaly_metrics.append("Vibration RMS")
        deductions += min((snapshot.vibration_rms - 4.5) * 6, 32)
    if snapshot.bearing_temperature > 75:
        anomaly_metrics.append("Bearing Temperature")
        deductions += min((snapshot.bearing_temperature - 75) * 2, 32)
    if snapshot.motor_current > 27:
        anomaly_metrics.append("Motor Current")
        deductions += min((snapshot.motor_current - 27) * 2.5, 25)
    if snapshot.load_ratio > 100:
        anomaly_metrics.append("Load Ratio")
        deductions += min((snapshot.load_ratio - 100) * 1.4, 25)
    if snapshot.motor_voltage < 342 or snapshot.motor_voltage > 418:
        anomaly_metrics.append("Motor Voltage")
        deductions += min(abs(snapshot.motor_voltage - 380) * 0.8, 28)

    scenario_fault = SCENARIO_FAULT_MAP.get(snapshot.scenario)
    is_anomaly = bool(anomaly_metrics)
    fault_type: str | None = None
    title: str | None = None
    if is_anomaly and scenario_fault:
        fault_type, title = scenario_fault
    elif is_anomaly:
        if snapshot.motor_current > 27 or snapshot.load_ratio > 100:
            fault_type, title = "motor_overload", "Motor Load & Current Anomaly"
        elif snapshot.bearing_temperature > 75 and snapshot.vibration_rms > 4.5:
            fault_type, title = "bearing_wear", "Bearing Temperature & Vibration Trend Anomaly"
        elif snapshot.bearing_temperature > 75:
            fault_type, title = "bearing_overheat", "Bearing Temperature Anomaly"
        elif snapshot.vibration_rms > 4.5:
            fault_type, title = "rotor_unbalance", "Motor Vibration Anomaly"
        else:
            fault_type, title = "voltage_abnormal", "Motor Voltage Anomaly"

    critical = (
        snapshot.bearing_temperature >= 90
        or snapshot.load_ratio >= 115
        or snapshot.motor_voltage <= 320
        or snapshot.motor_voltage >= 440
        or len(anomaly_metrics) >= 4
    )
    health_score = round(max(18.0, 100.0 - deductions), 1)
    if critical:
        risk = RiskLevelEnum.critical
    elif is_anomaly and (
        health_score < 70 or len(anomaly_metrics) >= 2 or snapshot.vibration_rms >= 7.1
    ):
        risk = RiskLevelEnum.high
    elif is_anomaly:
        risk = RiskLevelEnum.medium
    else:
        risk = RiskLevelEnum.low

    return TelemetryAssessment(
        is_anomaly,
        health_score,
        risk,
        fault_type,
        title,
        FAULT_GUIDANCE.get(fault_type or "", ("", "", [], []))[0] or None,
        0.9 if scenario_fault else 0.78,
        anomaly_metrics,
        values,
    )


@traced_span("telemetry.ingest")
def ingest_snapshot(
    db: Session,
    equipment: Equipment,
    snapshot: TelemetrySnapshot,
    *,
    auto_create_work_orders: bool = True,
) -> IngestionResult:
    # Industrial event entry: start new trace if none exists (gateway sync/subscription flush already bound,
    # fallback here covers manual telemetry ingestion and direct calls).
    if current_trace_id() is None:
        start_trace("manual-telemetry-ingest")
    _metrics = get_metrics()
    _ingest_started = time.perf_counter()

    def _finish_ingest(result: IngestionResult) -> IngestionResult:
        """Unified observability outlet: telemetry ingest latency and counter."""
        _metrics.telemetry_ingest_latency_seconds.observe(
            time.perf_counter() - _ingest_started
        )
        _metrics.telemetry_ingest_total.labels(status="accepted").inc()
        return result

    assessment = assess_snapshot(snapshot)
    telemetry = TelemetryRecord(
        equipment_id=equipment.id,
        collected_at=snapshot.collected_at,
        vibration_rms=snapshot.vibration_rms,
        bearing_temperature=snapshot.bearing_temperature,
        motor_current=snapshot.motor_current,
        motor_voltage=snapshot.motor_voltage,
        rotational_speed=snapshot.rotational_speed,
        load_ratio=snapshot.load_ratio,
        ambient_temperature=snapshot.ambient_temperature,
        cumulative_runtime_hours=snapshot.cumulative_runtime_hours,
        scenario=snapshot.scenario,
        quality=snapshot.quality,
        is_anomaly=assessment.is_anomaly,
        anomaly_metrics=assessment.anomaly_metrics,
        trace_id=current_trace_id(),
    )
    db.add(telemetry)
    db.flush()

    equipment.cumulative_runtime_hours = snapshot.cumulative_runtime_hours
    equipment.health_score = assessment.health_score
    equipment.risk_level = assessment.risk_level
    if snapshot.quality <= 0:
        equipment.status = EquipmentStatusEnum.offline
    elif assessment.risk_level == RiskLevelEnum.critical:
        equipment.status = EquipmentStatusEnum.fault
    elif assessment.is_anomaly:
        equipment.status = EquipmentStatusEnum.warning
    elif equipment.status not in {
        EquipmentStatusEnum.maintenance,
        EquipmentStatusEnum.under_repair,
        EquipmentStatusEnum.scrapped,
    }:
        equipment.status = EquipmentStatusEnum.running

    _update_sensors(db, equipment, snapshot)
    if not assessment.is_anomaly or not assessment.fault_type:
        db.commit()
        db.refresh(telemetry)
        return _finish_ingest(IngestionResult(telemetry, None, None, None, None))

    existing = (
        db.query(AnomalyEvent)
        .filter(
            AnomalyEvent.equipment_id == equipment.id,
            AnomalyEvent.fault_type == assessment.fault_type,
            AnomalyEvent.status.in_(["open", "acknowledged"]),
        )
        .first()
    )
    if existing:
        existing.telemetry_id = telemetry.id
        existing.evidence = assessment.evidence
        existing.severity = assessment.risk_level
        existing.diagnosis_summary = assessment.diagnosis
        existing.confidence = assessment.confidence
        existing_work_order_id = (
            db.query(MaintenanceRecommendation.auto_work_order_id)
            .join(
                RiskPrediction,
                MaintenanceRecommendation.prediction_id == RiskPrediction.id,
            )
            .filter(
                RiskPrediction.anomaly_event_id == existing.id,
                MaintenanceRecommendation.auto_work_order_id.is_not(None),
            )
            .scalar()
        )
        if (
            auto_create_work_orders
            and not existing_work_order_id
            and assessment.risk_level in {RiskLevelEnum.high, RiskLevelEnum.critical}
        ):
            escalation_run = AgentRun(
                equipment_id=equipment.id,
                anomaly_event_id=existing.id,
                goal="Generate predictive maintenance work order upon risk escalation",
                status="running",
                provider="deterministic-mock",
                input={
                    "telemetry_id": telemetry.id,
                    "fault_type": assessment.fault_type,
                    "risk_level": assessment.risk_level.value,
                },
                confidence=assessment.confidence,
                requires_human_review=assessment.confidence < 0.8,
                started_at=datetime.now(UTC),
                trace_id=current_trace_id(),
            )
            get_metrics().agent_runs_total.labels(
                agent_name="predictive-maintenance", status="running"
            ).inc()
            db.add(escalation_run)
            db.flush()
            diagnosis = (
                db.query(FaultDiagnosis)
                .filter(FaultDiagnosis.anomaly_event_id == existing.id)
                .first()
            )
            if diagnosis:
                diagnosis.evidence = assessment.evidence
                diagnosis.confidence = assessment.confidence
                diagnosis.requires_human_review = assessment.confidence < 0.8
            prediction = _create_prediction(db, equipment, existing, assessment)
            recommendation = _create_recommendation(
                db, equipment, prediction, assessment
            )
            escalation_work_order = _create_predictive_work_order(
                db, equipment, existing, recommendation, assessment
            )
            recommendation.auto_work_order_id = escalation_work_order.id
            recommendation.status = "work_order_created"
            _reserve_parts(db, recommendation, escalation_work_order)
            _create_operation_approval(
                db, equipment, escalation_work_order, recommendation, assessment
            )
            _record_tool(
                db,
                escalation_run,
                "work_order_creator",
                {"anomaly_event_id": existing.id, "risk_escalation": True},
                {"work_order_id": escalation_work_order.id},
            )
            escalation_run.status = "completed"
            escalation_run.output = {
                "prediction_id": prediction.id,
                "recommendation_id": recommendation.id,
                "work_order_id": escalation_work_order.id,
            }
            escalation_run.finished_at = datetime.now(UTC)
            get_metrics().agent_run_latency_seconds.labels(
                agent_name="predictive-maintenance"
            ).observe(
                (escalation_run.finished_at - escalation_run.started_at).total_seconds()
            )
            db.commit()
            for entity in (
                telemetry,
                existing,
                prediction,
                recommendation,
                escalation_work_order,
            ):
                db.refresh(entity)
            return _finish_ingest(
                IngestionResult(
                    telemetry,
                    existing,
                    prediction,
                    recommendation,
                    escalation_work_order,
                )
            )
        db.commit()
        db.refresh(telemetry)
        return _finish_ingest(IngestionResult(telemetry, existing, None, None, None))

    anomaly = AnomalyEvent(
        equipment_id=equipment.id,
        telemetry_id=telemetry.id,
        fault_type=assessment.fault_type,
        title=assessment.title or "Equipment Anomaly",
        severity=assessment.risk_level,
        evidence=assessment.evidence,
        diagnosis_summary=assessment.diagnosis,
        confidence=assessment.confidence,
        detected_at=snapshot.collected_at,
        trace_id=current_trace_id(),
    )
    db.add(anomaly)
    db.flush()

    agent_run = AgentRun(
        equipment_id=equipment.id,
        anomaly_event_id=anomaly.id,
        goal="Diagnose equipment anomaly and generate predictive maintenance strategy",
        status="running",
        provider="deterministic-mock",
        input={
            "telemetry_id": telemetry.id,
            "fault_type": assessment.fault_type,
            "evidence": assessment.evidence,
        },
        confidence=assessment.confidence,
        requires_human_review=assessment.confidence < 0.8,
        started_at=datetime.now(UTC),
        trace_id=current_trace_id(),
    )
    get_metrics().agent_runs_total.labels(
        agent_name="predictive-maintenance", status="running"
    ).inc()
    db.add(agent_run)
    db.flush()
    _record_tool(
        db,
        agent_run,
        "anomaly_detector",
        {"telemetry_id": telemetry.id},
        {
            "is_anomaly": True,
            "fault_type": assessment.fault_type,
            "health_score": assessment.health_score,
        },
    )
    diagnosis = _create_diagnosis(db, equipment, anomaly, assessment, agent_run)
    prediction = _create_prediction(db, equipment, anomaly, assessment)
    _record_tool(
        db,
        agent_run,
        "risk_predictor",
        {"anomaly_event_id": anomaly.id},
        {
            "risk_level": prediction.risk_level.value,
            "probability": prediction.probability,
            "remaining_useful_life_hours": prediction.remaining_useful_life_hours,
        },
    )
    recommendation = _create_recommendation(db, equipment, prediction, assessment)
    _record_tool(
        db,
        agent_run,
        "maintenance_strategy",
        {"prediction_id": prediction.id},
        {
            "recommendation_id": recommendation.id,
            "priority": recommendation.priority,
        },
    )
    work_order = None
    if auto_create_work_orders and assessment.risk_level in {
        RiskLevelEnum.high,
        RiskLevelEnum.critical,
    }:
        work_order = _create_predictive_work_order(
            db, equipment, anomaly, recommendation, assessment
        )
        recommendation.auto_work_order_id = work_order.id
        recommendation.status = "work_order_created"
        _reserve_parts(db, recommendation, work_order)
        _create_operation_approval(
            db, equipment, work_order, recommendation, assessment
        )
        _record_tool(
            db,
            agent_run,
            "work_order_creator",
            {"recommendation_id": recommendation.id},
            {"work_order_id": work_order.id, "status": work_order.status.value},
        )

    agent_run.status = "completed"
    agent_run.output = {
        "diagnosis_id": diagnosis.id,
        "prediction_id": prediction.id,
        "recommendation_id": recommendation.id,
        "work_order_id": work_order.id if work_order else None,
    }
    agent_run.finished_at = datetime.now(UTC)
    get_metrics().agent_run_latency_seconds.labels(
        agent_name="predictive-maintenance"
    ).observe((agent_run.finished_at - agent_run.started_at).total_seconds())

    for supervisor in (
        db.query(User)
        .filter(
            User.role.in_([RoleEnum.supervisor, RoleEnum.admin]),
            User.is_active.is_(True),
        )
        .all()
    ):
        notification_gateway.send(
            db,
            user_id=supervisor.id,
            title=f"{equipment.name} detected {anomaly.title}",
            content=f"Risk Level: {assessment.risk_level.value}; Health Score: {assessment.health_score}",
            level="warning",
            link=f"/equipment/{equipment.id}",
        )

    db.commit()
    for entity in (telemetry, anomaly, prediction, recommendation):
        db.refresh(entity)
    if work_order:
        db.refresh(work_order)
    return _finish_ingest(
        IngestionResult(telemetry, anomaly, prediction, recommendation, work_order)
    )


def verify_maintenance(
    db: Session,
    work_order: WorkOrder,
    *,
    verified_by: int | None,
    notes: str | None,
    create_knowledge_case: bool,
) -> MaintenanceVerification:
    if not work_order.equipment_id:
        raise ValueError("Work order not linked to equipment")
    latest = (
        db.query(TelemetryRecord)
        .filter(TelemetryRecord.equipment_id == work_order.equipment_id)
        .order_by(TelemetryRecord.collected_at.desc())
        .first()
    )
    before = (
        db.query(TelemetryRecord)
        .join(AnomalyEvent, AnomalyEvent.telemetry_id == TelemetryRecord.id)
        .filter(
            AnomalyEvent.equipment_id == work_order.equipment_id,
        )
        .order_by(AnomalyEvent.detected_at.desc())
        .first()
    )
    equipment = db.get(Equipment, work_order.equipment_id)
    if not equipment or not latest:
        raise ValueError("Missing equipment or post-maintenance telemetry data")

    before_score = _record_health_score(before) if before else 50.0
    after_score = _record_health_score(latest)
    result = "passed" if after_score >= 80 and not latest.is_anomaly else "failed"
    previous_status = work_order.status
    now = datetime.now(UTC)
    verification = MaintenanceVerification(
        work_order_id=work_order.id,
        equipment_id=equipment.id,
        health_score_before=before_score,
        health_score_after=after_score,
        telemetry_before=_telemetry_dict(before),
        telemetry_after=_telemetry_dict(latest),
        result=result,
        notes=notes,
        verified_by=verified_by,
        verified_at=now,
    )
    db.add(verification)
    if result == "passed":
        equipment.health_score = after_score
        equipment.risk_level = RiskLevelEnum.low
        equipment.status = EquipmentStatusEnum.running
        equipment.last_maintenance_at = now.date()
        equipment.next_maintenance_at = (now + timedelta(days=90)).date()
        work_order.status = WorkOrderStatusEnum.completed
        work_order.actual_end_at = now
        work_order.needs_observation = False
        for event in (
            db.query(AnomalyEvent)
            .filter(
                AnomalyEvent.equipment_id == equipment.id,
                AnomalyEvent.status.in_(["open", "acknowledged"]),
            )
            .all()
        ):
            event.status = "resolved"
            event.resolved_at = now
    else:
        work_order.status = WorkOrderStatusEnum.returned
        work_order.actual_end_at = None
        work_order.needs_observation = True
        work_order.rejection_reason = (
            "Post-maintenance telemetry still abnormal or health score below 80; automatically returned for rework."
        )

    if work_order.status != previous_status:
        db.add(
            WorkOrderStatusHistory(
                work_order_id=work_order.id,
                from_status=previous_status.value,
                to_status=work_order.status.value,
                changed_by=verified_by,
                changed_at=now,
                remark="Maintenance verification passed, work order automatically closed"
                if result == "passed"
                else "Maintenance verification failed, work order automatically reopened",
            )
        )

    if create_knowledge_case:
        article = KnowledgeArticle(
            title=f"[Pending Review] {equipment.name} {work_order.title} Maintenance Verification Case",
            category=KnowledgeCategoryEnum.case,
            content=(
                f"Work order {work_order.code}. Root cause: {work_order.root_cause or 'Pending'}."
                f"Actions: {work_order.action_taken or 'Executed per order'}."
                f"Health score changed from {before_score} to {after_score}, verification result: {result}."
            ),
            summary=f"Maintenance verification: {before_score} -> {after_score}",
            tags=["Predictive Maintenance", "Maintenance Verification", "Pending Human Review", equipment.code],
            equipment_type_id=equipment.equipment_type_id,
            source="Generated automatically by maintenance closed loop, requires human review",
            author_id=verified_by,
            status="draft",
            created_by=str(verified_by) if verified_by else "system",
        )
        db.add(article)
        db.flush()
        verification.knowledge_article_id = article.id
    db.commit()
    db.refresh(verification)
    return verification


def _create_diagnosis(
    db: Session,
    equipment: Equipment,
    anomaly: AnomalyEvent,
    assessment: TelemetryAssessment,
    agent_run: AgentRun,
) -> FaultDiagnosis:
    query = " ".join(
        filter(
            None,
            [
                equipment.name,
                assessment.title,
                assessment.diagnosis,
                " ".join(assessment.anomaly_metrics),
            ],
        )
    )
    results = search_articles(
        db,
        query,
        equipment_type_id=equipment.equipment_type_id,
        limit=3,
    )
    citations = [
        {
            "article_id": item["article_id"],
            "title": item["title"],
            "source": item["source"],
            "score": item["score"],
        }
        for item in results
    ]
    _record_tool(
        db,
        agent_run,
        "knowledge_search",
        {"query": query, "limit": 3},
        {"citations": citations},
    )
    guidance = FAULT_GUIDANCE.get(
        assessment.fault_type or "unknown_anomaly",
        FAULT_GUIDANCE["unknown_anomaly"],
    )
    diagnosis = FaultDiagnosis(
        equipment_id=equipment.id,
        anomaly_event_id=anomaly.id,
        fault_type=assessment.fault_type or "unknown_anomaly",
        summary=assessment.diagnosis or guidance[0],
        possible_causes=_possible_causes(assessment.fault_type),
        evidence=assessment.evidence,
        rag_citations=citations,
        confidence=assessment.confidence,
        requires_human_review=assessment.confidence < 0.8,
        generated_at=datetime.now(UTC),
    )
    db.add(diagnosis)
    db.flush()
    return diagnosis


def _possible_causes(fault_type: str | None) -> list[str]:
    return {
        "bearing_wear": ["Raceway or rolling element wear", "Lubrication degradation", "Bearing clearance anomaly"],
        "bearing_overheat": ["Insufficient lubrication", "Overtight installation", "Deteriorated cooling conditions"],
        "motor_overload": ["Excessive process load", "Transmission blockage", "Three-phase current unbalance"],
        "rotor_unbalance": ["Rotor fouling or damage", "Loose fasteners", "Dynamic balancing failure"],
        "shaft_misalignment": ["Coupling offset", "Soft foot", "Foundation looseness"],
        "insufficient_lubrication": ["Overdue replenishment cycle", "Oil line blockage", "Incompatible lubricant grade"],
        "voltage_abnormal": ["Power supply fluctuation", "Loose terminal wiring", "Abnormal inverter output"],
        "sensor_abnormal": ["Sensor power loss", "Gateway disconnection", "Signal line fault"],
        "unknown_anomaly": ["Composite mechanical failure", "Coupled electrical and load anomaly", "Data quality anomaly"],
    }.get(fault_type or "unknown_anomaly", ["Requires further manual investigation"])


def _record_tool(
    db: Session,
    agent_run: AgentRun,
    tool_name: str,
    request: dict[str, Any],
    response: dict[str, Any],
) -> None:
    db.add(
        ToolInvocation(
            agent_run_id=agent_run.id,
            tool_name=tool_name,
            provider="local",
            status="success",
            request=request,
            response=response,
            duration_ms=0,
        )
    )


def _update_sensors(
    db: Session, equipment: Equipment, snapshot: TelemetrySnapshot
) -> None:
    for metric, definition in SENSOR_DEFINITIONS.items():
        name, unit, warning_min, warning_max, critical_min, critical_max = definition
        sensor = (
            db.query(EquipmentSensor)
            .filter(
                EquipmentSensor.equipment_id == equipment.id,
                EquipmentSensor.metric_type == metric,
            )
            .first()
        )
        if not sensor:
            sensor = EquipmentSensor(
                equipment_id=equipment.id,
                code=f"{equipment.code}-{metric.upper()}",
                name=name,
                metric_type=metric,
                unit=unit,
                warning_min=warning_min,
                warning_max=warning_max,
                critical_min=critical_min,
                critical_max=critical_max,
            )
            db.add(sensor)
        sensor.latest_value = getattr(snapshot, metric)
        sensor.status = "offline" if snapshot.quality <= 0 else "online"
        sensor.last_seen_at = snapshot.collected_at


@traced_span("prediction.infer", {"ml.model_family": "deterministic-rules"})
def _create_prediction(
    db: Session,
    equipment: Equipment,
    anomaly: AnomalyEvent,
    assessment: TelemetryAssessment,
) -> RiskPrediction:
    now = datetime.now(UTC)
    probability = {
        RiskLevelEnum.critical: 0.94,
        RiskLevelEnum.high: 0.82,
        RiskLevelEnum.medium: 0.58,
        RiskLevelEnum.low: 0.2,
    }[assessment.risk_level]
    remaining_hours = {
        RiskLevelEnum.critical: 8.0,
        RiskLevelEnum.high: 36.0,
        RiskLevelEnum.medium: 168.0,
        RiskLevelEnum.low: 720.0,
    }[assessment.risk_level]
    maintenance_window_end = now + timedelta(hours=max(2.0, remaining_hours * 0.5))
    _metrics = get_metrics()
    _model_family = "deterministic-rules"
    _infer_started = time.perf_counter()
    try:
        prediction = RiskPrediction(
            equipment_id=equipment.id,
            anomaly_event_id=anomaly.id,
            risk_level=assessment.risk_level,
            failure_mode=assessment.fault_type or "unknown_anomaly",
            probability=probability,
            remaining_useful_life_hours=remaining_hours,
            predicted_failure_at=now + timedelta(hours=remaining_hours),
            maintenance_window_start=now,
            maintenance_window_end=maintenance_window_end,
            factors=assessment.anomaly_metrics,
            is_mock=True,
            model_version="deterministic-rules-v1",
            trace_id=current_trace_id(),
        )
        equipment.next_maintenance_at = maintenance_window_end.date()
        db.add(prediction)
        db.flush()
    except Exception:
        _metrics.ml_inference_errors_total.labels(model_family=_model_family).inc()
        raise
    finally:
        _metrics.ml_inference_latency_seconds.labels(
            model_family=_model_family
        ).observe(time.perf_counter() - _infer_started)
    _metrics.ml_inference_total.labels(
        model_family=_model_family, status="success"
    ).inc()
    return prediction


def _create_recommendation(
    db: Session,
    equipment: Equipment,
    prediction: RiskPrediction,
    assessment: TelemetryAssessment,
) -> MaintenanceRecommendation:
    _, strategy, required_skills, required_parts = FAULT_GUIDANCE.get(
        assessment.fault_type or "unknown_anomaly",
        FAULT_GUIDANCE["unknown_anomaly"],
    )
    priority = {
        RiskLevelEnum.critical: "P1",
        RiskLevelEnum.high: "P2",
        RiskLevelEnum.medium: "P3",
        RiskLevelEnum.low: "P4",
    }[assessment.risk_level]
    dispatch = _dispatch_suggestion(db, required_skills, required_parts)
    recommendation = MaintenanceRecommendation(
        equipment_id=equipment.id,
        prediction_id=prediction.id,
        title=f"{equipment.name}：{assessment.title}",
        strategy=strategy,
        priority=priority,
        required_skills=required_skills,
        required_parts=dispatch["parts"],
        risk_operations=["shutdown", "reset_alarm", "restart"],
        dispatch_suggestion=dispatch,
        generated_at=datetime.now(UTC),
        trace_id=current_trace_id(),
    )
    db.add(recommendation)
    db.flush()
    return recommendation


def _dispatch_suggestion(
    db: Session, required_skills: list[str], required_parts: list[str]
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    for profile in db.query(TechnicianProfile).all():
        user = db.get(User, profile.user_id)
        if not user or not user.is_active:
            continue
        skills = [skill.name for skill in profile.skills]
        active_orders = (
            db.query(WorkOrder)
            .filter(
                WorkOrder.assignee_id == user.id,
                WorkOrder.status.notin_(
                    [WorkOrderStatusEnum.completed, WorkOrderStatusEnum.cancelled]
                ),
            )
            .count()
        )
        match_count = len(set(skills) & set(required_skills))
        candidates.append(
            {
                "user_id": user.id,
                "name": user.full_name,
                "availability": profile.availability,
                "active_orders": active_orders,
                "matched_skills": match_count,
                "score": match_count * 20 - active_orders * 3,
            }
        )
    candidates.sort(key=lambda item: item["score"], reverse=True)

    parts: list[dict[str, Any]] = []
    for keyword in required_parts:
        part = db.query(SparePart).filter(SparePart.name.contains(keyword)).first()
        parts.append(
            {
                "name": keyword,
                "spare_part_id": part.id if part else None,
                "stock_qty": part.stock_qty if part else 0,
                "available": bool(part and part.stock_qty > 0),
            }
        )
    return {
        "technicians": candidates[:3],
        "recommended_technician_id": candidates[0]["user_id"] if candidates else None,
        "parts": parts,
    }


def _reserve_parts(
    db: Session,
    recommendation: MaintenanceRecommendation,
    work_order: WorkOrder,
) -> None:
    reservation_summaries: list[dict[str, Any]] = []
    for required in recommendation.required_parts or []:
        spare_part_id = required.get("spare_part_id")
        part = db.get(SparePart, spare_part_id) if spare_part_id else None
        already_reserved = 0
        if part:
            already_reserved = int(
                db.query(func.coalesce(func.sum(SparePartReservation.reserved_qty), 0))
                .filter(
                    SparePartReservation.spare_part_id == part.id,
                    SparePartReservation.status == "reserved",
                )
                .scalar()
                or 0
            )
        available_qty = max((part.stock_qty if part else 0) - already_reserved, 0)
        reserved_qty = min(available_qty, 1)
        shortage_qty = 1 - reserved_qty
        status = (
            "reserved" if reserved_qty == 1 else ("shortage" if part else "unavailable")
        )
        reservation = SparePartReservation(
            recommendation_id=recommendation.id,
            work_order_id=work_order.id,
            spare_part_id=part.id if part else None,
            requested_name=str(required["name"]),
            requested_qty=1,
            reserved_qty=reserved_qty,
            shortage_qty=shortage_qty,
            status=status,
            reserved_at=datetime.now(UTC) if reserved_qty else None,
        )
        db.add(reservation)
        reservation_summaries.append(
            {
                **required,
                "requested_qty": 1,
                "reserved_qty": reserved_qty,
                "shortage_qty": shortage_qty,
                "reservation_status": status,
            }
        )
    recommendation.required_parts = reservation_summaries
    dispatch = dict(recommendation.dispatch_suggestion or {})
    dispatch["parts"] = reservation_summaries
    dispatch["parts_ready"] = all(
        item["reservation_status"] == "reserved" for item in reservation_summaries
    )
    recommendation.dispatch_suggestion = dispatch


@traced_span("work_order.create", {"work_order.source": "predictive"})
def _create_predictive_work_order(
    db: Session,
    equipment: Equipment,
    anomaly: AnomalyEvent,
    recommendation: MaintenanceRecommendation,
    assessment: TelemetryAssessment,
) -> WorkOrder:
    assignee_id = (recommendation.dispatch_suggestion or {}).get(
        "recommended_technician_id"
    )
    priority = PriorityEnum(recommendation.priority)
    status = (
        WorkOrderStatusEnum.assigned
        if assignee_id
        else WorkOrderStatusEnum.pending_dispatch
    )
    prediction = (
        db.get(RiskPrediction, recommendation.prediction_id)
        if recommendation.prediction_id
        else None
    )
    planned_end_at = (
        prediction.maintenance_window_end
        if prediction and prediction.maintenance_window_end
        else datetime.now(UTC) + timedelta(hours=8)
    )
    work_order = WorkOrder(
        code=generate_work_order_code(),
        title=f"[Predictive Maintenance] {anomaly.title}",
        equipment_id=equipment.id,
        fault_description=(
            f"Automatically created by system from telemetry anomaly. Diagnosis: {assessment.diagnosis}; "
            f"Evidence: {', '.join(assessment.anomaly_metrics)}."
        ),
        order_type=WorkOrderTypeEnum.preventive,
        priority=priority,
        status=status,
        assignee_id=assignee_id,
        planned_start_at=datetime.now(UTC),
        planned_end_at=planned_end_at,
        safety_risk="Involves rotating machinery and electrical energy; shutdown, de-energization, verification, and LOTO must be executed.",
        ai_diagnosis_summary=assessment.diagnosis,
        maintenance_steps=[
            "Confirm equipment status and anomalous telemetry",
            "Execute shutdown, de-energization, verification, and LOTO",
            recommendation.strategy,
            "Complete no-load and load testing",
            "Acquire post-maintenance telemetry and verify health score",
        ],
        acceptance_criteria="Anomalous metrics return within thresholds, health score >= 80, no-load and load testing passed.",
        created_by="maintenance-agent",
        trace_id=current_trace_id(),
    )
    get_metrics().work_orders_created_total.labels(source="predictive").inc()
    db.add(work_order)
    db.flush()

    db.add(
        WorkOrderStatusHistory(
            work_order_id=work_order.id,
            from_status=None,
            to_status=status.value,
            changed_by=None,
            changed_at=datetime.now(UTC),
            remark=f"Automatically created from anomaly event #{anomaly.id}",
        )
    )
    if assignee_id:
        db.add(
            WorkOrderAssignment(
                work_order_id=work_order.id,
                assignee_id=assignee_id,
                assigned_by=None,
                assigned_at=datetime.now(UTC),
                is_current=True,
            )
        )
    checklist = [
        ("safety", "Equipment shut down and LOTO executed", 1),
        ("diagnosis", "Verify telemetry anomaly and fault diagnosis", 2),
        ("repair", recommendation.strategy, 3),
        ("testing", "Acquire post-maintenance telemetry and verify health score", 4),
    ]
    for category, content, order in checklist:
        db.add(
            WorkOrderChecklistItem(
                work_order_id=work_order.id,
                category=category,
                content=content,
                order=order,
                is_required=True,
                created_by="maintenance-agent",
            )
        )
    return work_order


def _create_operation_approval(
    db: Session,
    equipment: Equipment,
    work_order: WorkOrder,
    recommendation: MaintenanceRecommendation,
    assessment: TelemetryAssessment,
) -> None:
    db.add(
        OperationApproval(
            equipment_id=equipment.id,
            work_order_id=work_order.id,
            recommendation_id=recommendation.id,
            command_type="shutdown",
            command_payload={"reason": anomaly_reason(assessment)},
            risk_level=assessment.risk_level,
            risk_reason="Equipment shutdown affects production line and involves rotating machinery and electrical energy isolation; supervisor manual approval required.",
            status="pending",
            requested_by=None,
            requested_at=datetime.now(UTC),
            trace_id=current_trace_id(),
        )
    )
    get_metrics().operation_approval_total.labels(
        status="pending", risk_level=assessment.risk_level.value
    ).inc()


def anomaly_reason(assessment: TelemetryAssessment) -> str:
    return f"{assessment.title or 'Equipment Anomaly'}: {', '.join(assessment.anomaly_metrics)}"


def _record_health_score(record: TelemetryRecord | None) -> float:
    if not record:
        return 50.0
    snapshot = TelemetrySnapshot(
        equipment_id=__import__("uuid").UUID(int=record.equipment_id),
        collected_at=record.collected_at,
        vibration_rms=record.vibration_rms,
        bearing_temperature=record.bearing_temperature,
        motor_current=record.motor_current,
        motor_voltage=record.motor_voltage,
        rotational_speed=record.rotational_speed,
        load_ratio=record.load_ratio,
        ambient_temperature=record.ambient_temperature,
        cumulative_runtime_hours=record.cumulative_runtime_hours,
        scenario=record.scenario,
        quality=record.quality,
    )
    return assess_snapshot(snapshot).health_score


def _telemetry_dict(record: TelemetryRecord | None) -> dict[str, Any] | None:
    if not record:
        return None
    return {
        "id": record.id,
        "collected_at": record.collected_at.isoformat(),
        "vibration_rms": record.vibration_rms,
        "bearing_temperature": record.bearing_temperature,
        "motor_current": record.motor_current,
        "motor_voltage": record.motor_voltage,
        "rotational_speed": record.rotational_speed,
        "load_ratio": record.load_ratio,
        "ambient_temperature": record.ambient_temperature,
        "quality": record.quality,
        "is_anomaly": record.is_anomaly,
    }
