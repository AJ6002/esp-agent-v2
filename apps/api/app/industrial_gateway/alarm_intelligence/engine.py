"""Alarm Understanding and Root Cause Analysis (deterministic rules + existing knowledge retrieval).

Positioning: **AI-assisted industrial alarm analysis**.

- Understanding: Summarizes threshold alarm messages into structured semantics (breached metrics, triggered rules, severity);
- Root Cause Analysis: Combines latest telemetry evidence, existing platform troubleshooting knowledge (``FAULT_GUIDANCE``,
  reused read-only), and knowledge base search (``search_articles``, RAG baseline) to provide **root cause hypothesis** and evidence chain;
- Purely deterministic rules, preserving all ML models and Agent decision logic;
- Output is analytical findings only, performing zero operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Final

from sqlalchemy.orm import Session

from app.ai.knowledge_search import search_articles
from app.models.base import RiskLevelEnum
from app.models.intelligence import TelemetryRecord
from app.services.intelligence_service import FAULT_GUIDANCE

MODEL_VERSION: Final = "deterministic-rules-v1"

# Platform warning thresholds (aligned with intelligence_service.SENSOR_DEFINITIONS / alarms.py).
WARNING_THRESHOLDS: Final[dict[str, float]] = {
    "bearing_temperature": 75.0,
    "vibration_rms": 4.5,
    "motor_current": 27.0,
    "load_ratio": 100.0,
}
VOLTAGE_RANGE: Final[tuple[float, float]] = (342.0, 418.0)

METRIC_LABELS: Final[dict[str, str]] = {
    "bearing_temperature": "Bearing Temperature",
    "vibration_rms": "Vibration RMS",
    "motor_current": "Motor Current",
    "motor_voltage": "Motor Voltage",
    "load_ratio": "Load Ratio",
}

# Metric -> root cause hypothesis (read-only reference to FAULT_GUIDANCE troubleshooting knowledge).
METRIC_FAULT_HYPOTHESIS: Final[dict[str, str]] = {
    "bearing_temperature": "bearing_overheat",
    "vibration_rms": "rotor_unbalance",
    "motor_current": "motor_overload",
    "load_ratio": "motor_overload",
    "motor_voltage": "voltage_abnormal",
}


def latest_telemetry_fields(
    db: Session, equipment_id: int
) -> tuple[dict[str, float | bool | None], int | None]:
    """Read latest telemetry assessment fields for equipment (for evidence chain)."""
    record = (
        db.query(TelemetryRecord)
        .filter(TelemetryRecord.equipment_id == equipment_id)
        .order_by(TelemetryRecord.collected_at.desc())
        .first()
    )
    if record is None:
        return {}, None
    fields: dict[str, float | bool | None] = {
        "bearing_temperature": record.bearing_temperature,
        "vibration_rms": record.vibration_rms,
        "motor_current": record.motor_current,
        "motor_voltage": record.motor_voltage,
        "load_ratio": record.load_ratio,
    }
    return fields, record.id


def _abnormal_metrics(
    telemetry_fields: dict[str, float | bool | None],
) -> list[dict[str, Any]]:
    """Return breached metric details (sorted descending by ratio)."""
    result: list[dict[str, Any]] = []
    for metric, threshold in WARNING_THRESHOLDS.items():
        value = telemetry_fields.get(metric)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        if float(value) > threshold:
            result.append(
                {
                    "metric": metric,
                    "label": METRIC_LABELS[metric],
                    "value": round(float(value), 2),
                    "threshold": threshold,
                    "ratio": round(float(value) / threshold, 3),
                    "state": "above_upper",
                }
            )
    voltage = telemetry_fields.get("motor_voltage")
    if isinstance(voltage, (int, float)) and not isinstance(voltage, bool):
        low, high = VOLTAGE_RANGE
        if not (low <= float(voltage) <= high):
            result.append(
                {
                    "metric": "motor_voltage",
                    "label": METRIC_LABELS["motor_voltage"],
                    "value": round(float(voltage), 2),
                    "threshold": f"{low}-{high}",
                    "ratio": round(float(voltage) / high, 3),
                    "state": "voltage_out_of_range",
                }
            )
    result.sort(key=lambda item: item["ratio"], reverse=True)
    return result


@dataclass(slots=True)
class AlarmUnderstanding:
    """Alarm understanding outcome: structured semantic summary."""

    summary: str
    severity: str
    abnormal_metrics: list[dict[str, Any]] = field(default_factory=list)
    triggered_rules: list[str] = field(default_factory=list)


def understand_alarm(
    *,
    severity: str,
    message: str,
    telemetry_fields: dict[str, float | bool | None],
) -> AlarmUnderstanding:
    """Summarize alarm and telemetry evidence into structured understanding."""
    abnormal = _abnormal_metrics(telemetry_fields)
    rules = [f"{item['label']}>{item['threshold']}" for item in abnormal]
    if severity == "CRITICAL":
        rules.insert(0, "Alarm bit is active")
    parts = [f"{item['label']}={item['value']}" for item in abnormal]
    summary = (
        f"{severity} Industrial Alarm: "
        + (", ".join(parts) if parts else "No significant metric breach observed (possibly triggered by alarm bit or transient)")
        + f". Raw message: {message}"
    )
    return AlarmUnderstanding(
        summary=summary,
        severity=severity,
        abnormal_metrics=abnormal,
        triggered_rules=rules,
    )


@dataclass(slots=True)
class RootCauseAnalysisResult:
    """Root cause analysis result: hypothesis + evidence chain + knowledge citations."""

    hypothesis: str
    fault_type: str | None
    contributing_factors: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    citations: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.5
    confidence_factors: list[str] = field(default_factory=list)
    evidence_conflicts: list[str] = field(default_factory=list)


def analyze_root_cause(
    db: Session,
    *,
    severity: str,
    message: str,
    telemetry_fields: dict[str, float | bool | None],
    telemetry_record_id: int | None,
    equipment_name: str,
    equipment_type_id: int | None = None,
    prediction_context: dict[str, Any] | None = None,
    anomaly_context: dict[str, Any] | None = None,
    equipment_context: dict[str, Any] | None = None,
) -> RootCauseAnalysisResult:
    """Produce root cause hypothesis and evidence chain (deterministic rules + read-only knowledge retrieval)."""
    abnormal = _abnormal_metrics(telemetry_fields)
    contributing = [
        f"{item['label']}={item['value']} (Threshold {item['threshold']})"
        for item in abnormal
    ]
    contributing.append(f"Alarm message: {message}")

    fault_type: str | None = None
    if abnormal:
        fault_type = METRIC_FAULT_HYPOTHESIS.get(abnormal[0]["metric"])
    elif severity == "CRITICAL":
        fault_type = None

    guidance = FAULT_GUIDANCE.get(fault_type or "", None)
    if guidance and fault_type:
        cause_text = guidance[0]
        hypothesis = f"Root cause hypothesis ({fault_type}): {cause_text}"
    elif abnormal:
        hypothesis = (
            "Root cause hypothesis: multi-signal composite or transient trigger; rule layer cannot uniquely identify root cause. "
            "Recommend spectrum/trend analysis and on-site inspection for confirmation."
        )
    else:
        hypothesis = (
            "insufficient_evidence / manual_review_required: Currently no verifiable "
            "telemetry breach or knowledge evidence; cannot provide high-confidence root cause."
        )

    evidence: dict[str, Any] = {
        "severity": severity,
        "equipment": equipment_name,
        "telemetry_record_id": telemetry_record_id,
        "telemetry_fields": {key: value for key, value in telemetry_fields.items()},
        "abnormal_metrics": abnormal,
        "prediction_context": prediction_context,
        "anomaly_context": anomaly_context,
        "equipment_context": equipment_context,
    }

    citations: list[dict[str, Any]] = []
    query_parts = [equipment_name]
    if fault_type:
        query_parts.append(fault_type.replace("_", " "))
    if anomaly_context and anomaly_context.get("fault_type"):
        query_parts.append(str(anomaly_context["fault_type"]).replace("_", " "))
    for item in abnormal:
        query_parts.append(str(item["label"]))
    try:
        articles = search_articles(
            db,
            query=" ".join(query_parts),
            equipment_type_id=equipment_type_id,
            limit=3,
        )
    except Exception:  # pragma: no cover - degrade to empty citations if KB unavailable
        articles = []
    for article in articles:
        content = str(article.get("summary") or article.get("content") or "")
        citations.append(
            {
                "article_id": article.get("article_id"),
                "document_id": article.get("article_id"),
                "title": article.get("title"),
                "source": article.get("source") or article.get("category"),
                "section": None,
                "snippet": content[:240],
                "score": article.get("score"),
            }
        )

    confidence = 0.0
    confidence_factors: list[str] = []
    conflicts: list[str] = []
    if abnormal:
        confidence += 0.35
        confidence_factors.append("telemetry_threshold_evidence:+0.35")
    if len(abnormal) >= 2:
        confidence += 0.1
        confidence_factors.append("multiple_consistent_signals:+0.10")
    if fault_type is not None and guidance:
        confidence += 0.2
        confidence_factors.append("deterministic_guidance_match:+0.20")
    if citations:
        confidence += 0.15
        confidence_factors.append("rag_evidence:+0.15")
    if prediction_context:
        predicted_mode = str(prediction_context.get("failure_mode") or "")
        probability = float(prediction_context.get("probability") or 0.0)
        if fault_type and predicted_mode and fault_type not in predicted_mode:
            confidence -= 0.2
            conflicts.append(
                f"Predicted failure mode {predicted_mode} conflicts with rule root cause {fault_type}"
            )
            confidence_factors.append("conflicting_prediction:-0.20")
        elif probability >= 0.5:
            confidence += 0.15
            confidence_factors.append("fault_prediction_support:+0.15")
    if severity == "CRITICAL":
        confidence += 0.05
        confidence_factors.append("critical_alarm_signal:+0.05")
    if not citations:
        confidence_factors.append("rag_evidence_absent:+0.00")
    confidence = max(confidence, 0.1)
    confidence = min(confidence, 0.85)
    evidence["confidence_factors"] = confidence_factors
    evidence["evidence_conflicts"] = conflicts

    return RootCauseAnalysisResult(
        hypothesis=hypothesis,
        fault_type=fault_type,
        contributing_factors=contributing,
        evidence=evidence,
        citations=citations,
        confidence=round(confidence, 2),
        confidence_factors=confidence_factors,
        evidence_conflicts=conflicts,
    )


@dataclass(slots=True, frozen=True)
class RiskAssessmentResult:
    """Transparent alarm risk rule output."""

    risk_level: str
    reasons: list[str]
    inputs: dict[str, Any]


def assess_alarm_risk(
    *,
    severity: str,
    confidence: float,
    correlated_alarm_count: int,
    equipment_health_score: float | None,
    equipment_risk_level: RiskLevelEnum | str | None,
    fault_probability: float | None,
) -> RiskAssessmentResult:
    """Assess risk level using interpretable rules synthesizing alarm, prediction, and equipment status."""
    level = "LOW"
    reasons: list[str] = []
    normalized_equipment_risk = (
        equipment_risk_level.value
        if isinstance(equipment_risk_level, RiskLevelEnum)
        else str(equipment_risk_level or "").lower()
    )
    if severity.upper() == "WARNING":
        level = "MEDIUM"
        reasons.append("industrial_alarm=WARNING")
    if severity.upper() == "CRITICAL":
        level = "HIGH"
        reasons.append("industrial_alarm=CRITICAL")
    strong_support = False
    if fault_probability is not None and fault_probability >= 0.7:
        strong_support = True
        reasons.append("fault_probability>=0.70")
    if equipment_health_score is not None and equipment_health_score <= 50:
        strong_support = True
        reasons.append("health_score<=50")
    if correlated_alarm_count >= 3:
        strong_support = True
        reasons.append("correlated_alarm_count>=3")
    if normalized_equipment_risk in {"high", "critical"}:
        reasons.append(f"equipment_risk={normalized_equipment_risk}")
        if normalized_equipment_risk == "critical":
            strong_support = True
        if level == "MEDIUM":
            level = "HIGH"
    if severity.upper() == "CRITICAL" and strong_support:
        level = "CRITICAL"
    elif level == "MEDIUM" and strong_support:
        level = "HIGH"
    if confidence < 0.5:
        reasons.append("diagnosis_confidence<0.50_requires_review")
    return RiskAssessmentResult(
        risk_level=level,
        reasons=reasons,
        inputs={
            "alarm_severity": severity.upper(),
            "diagnosis_confidence": confidence,
            "correlated_alarm_count": correlated_alarm_count,
            "equipment_health_score": equipment_health_score,
            "equipment_risk_level": normalized_equipment_risk or None,
            "fault_probability": fault_probability,
        },
    )


# ----------------------------------------------------------------------
# Maintenance Decision Support (Advisory only, no execution)
# ----------------------------------------------------------------------

HUMAN_APPROVAL_DISCLAIMER: Final = (
    "The above is AI-assisted analysis recommendation for human reference only; "
    "any equipment operation must be executed via smart work orders and the Human Approval (OperationApproval) workflow. "
    "This analysis will not automatically create or execute any control."
)


@dataclass(slots=True)
class DecisionSupportResult:
    """Maintenance decision support: recommended actions + priority suggestion + related work orders."""

    recommended_actions: list[str] = field(default_factory=list)
    suggested_priority: str = "P3"
    related_work_orders: list[dict[str, Any]] = field(default_factory=list)
    requires_human_review: bool = True
    disclaimer: str = HUMAN_APPROVAL_DISCLAIMER


def build_decision_support(
    db: Session,
    *,
    severity: str,
    fault_type: str | None,
    confidence: float,
    equipment_id: int,
) -> DecisionSupportResult:
    """Transform root cause hypothesis into maintenance action suggestions (read-only query, creates no objects)."""
    from app.models.base import WorkOrderStatusEnum
    from app.models.workorder import WorkOrder

    guidance = FAULT_GUIDANCE.get(fault_type or "", None)
    if guidance and fault_type:
        actions = [item.strip() for item in str(guidance[1]).replace("；", ";").split(";") if item.strip()]
        skills = ", ".join(guidance[2]) if guidance[2] else ""
        parts = ", ".join(
            part.get("name") if isinstance(part, dict) else str(part)
            for part in (guidance[3] or [])
        )
        if skills:
            actions.append(f"Recommended skill configuration: {skills}")
        if parts:
            actions.append(f"Recommended spare parts pre-check: {parts}")
    else:
        actions = [
            "Schedule on-site inspection and record spectrum/trend data",
            "Review root cause against historical work orders and knowledge base cases",
        ]
    actions.append("Confirm on-site safety conditions (LOTO) prior to handling")

    if severity == "CRITICAL":
        suggested_priority = "P1" if confidence >= 0.7 else "P2"
    elif severity == "WARNING":
        suggested_priority = "P3"
    else:
        suggested_priority = "P4"

    open_statuses = [
        WorkOrderStatusEnum.pending_dispatch,
        WorkOrderStatusEnum.assigned,
        WorkOrderStatusEnum.accepted,
        WorkOrderStatusEnum.in_progress,
        WorkOrderStatusEnum.paused,
    ]
    related_rows = (
        db.query(WorkOrder)
        .filter(
            WorkOrder.equipment_id == equipment_id,
            WorkOrder.status.in_(open_statuses),
        )
        .order_by(WorkOrder.created_at.desc())
        .limit(3)
        .all()
    )
    related = [
        {
            "work_order_id": row.id,
            "code": row.code,
            "title": row.title,
            "status": row.status.value if row.status else None,
        }
        for row in related_rows
    ]

    return DecisionSupportResult(
        recommended_actions=actions,
        suggested_priority=suggested_priority,
        related_work_orders=related,
        requires_human_review=True,
        disclaimer=HUMAN_APPROVAL_DISCLAIMER,
    )
