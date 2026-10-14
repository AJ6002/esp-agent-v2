"""ESP APM Event Diagnosis Schemas (Strict Read-Only)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class PriorityEnum(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class DiagnoseEventRequest(BaseModel):
    event_id: str | None = Field(default=None, description="Event ID, e.g. EV-20261012-103435-FNW-001-878")
    well_id: str | None = Field(default=None, description="Well ID, e.g. FNW-001")
    timestamp: datetime | None = Field(default=None, description="Optional custom timestamp if event_id is omitted")


class PhysicalDeviation(BaseModel):
    signal: str = Field(description="Signal name (e.g. Motor Current, Vibration, PIP)")
    baseline_val: float = Field(description="Calibrated baseline or safety envelope from asset registry")
    pre_trip_val: float = Field(description="Observed value leading up to trip")
    post_trip_val: float | None = Field(default=None, description="Observed value after trip")
    delta: float = Field(description="Absolute deviation (pre_trip_val - baseline_val)")
    pct_change: float = Field(description="Percentage change from baseline")
    rate_of_change: str = Field(description="Slope or rate of change, e.g. +1.8 g/min, -16.3 PSI/hr")
    unit: str = Field(description="Engineering unit, e.g. A, PSI, g, °C")
    status: str = Field(description="NORMAL, WARNING, or VIOLATION")


class HypothesisItem(BaseModel):
    rank: int = Field(description="Priority rank (1, 2, 3...)")
    fault_id: str = Field(description="Taxonomy fault code, e.g. BEARING_WEAR")
    name: str = Field(description="Human-readable fault name")
    confidence_pct: int = Field(description="Confidence percentage (0-100)")
    evidence: str = Field(description="Specific physical evidence supporting this hypothesis")
    confirmation_test: str = Field(description="Empirical field test to verify or rule out this hypothesis")


class ImpactMetrics(BaseModel):
    deferred_bbl_per_hour: float = Field(description="Estimated deferred production in barrels per hour")
    thermal_margin_c: float = Field(description="Remaining motor temperature margin below trip limit in °C")
    mechanical_margin: str = Field(description="Vibration & load envelope status vs rated limits")
    escalation_condition: str = Field(description="Specific threshold condition triggering supervisory escalation")


class NextStepItem(BaseModel):
    step_number: int = Field(description="Sequential step order")
    action: str = Field(description="Specific operational or diagnostic action")
    category: str = Field(description="SAFETY_LOTO, ELECTRICAL, MECHANICAL, or PROCESS")
    requires_human_signoff: bool = Field(default=True, description="Whether human engineer sign-off is mandatory")


class ESPDiagnosisResponse(BaseModel):
    event_id: str
    well_id: str
    event_timestamp: str
    trip_cause: str
    severity: str
    scenario: str | None = None
    operating_state: str | None = None
    mathematical_confidence_pct: int
    markdown_report: str
    structured_data: dict[str, Any]
    disclaimer: str = (
        "AI suggestions are for advisory assistance only. Maintenance technicians and petroleum engineers "
        "must exercise professional judgment based on on-site conditions, equipment manuals, and safety standards."
    )


class RecentEventSummary(BaseModel):
    event_id: str
    well_id: str
    timestamp: str
    trip_cause: str
    severity: str
    scenario: str | None = None
    operating_state: str | None = None


class ActiveWellSummary(BaseModel):
    well_id: str
    cluster: str | None = None
    pump_type: str | None = None
    motor_hp: float | None = None
    rated_amp_a: float | None = None
    max_vibration_g: float | None = None
    is_active: bool = True


class ESPIntentEnum(str, Enum):
    EVENT_DIAGNOSE = "EVENT_DIAGNOSE"
    WELL_HISTORY = "WELL_HISTORY"
    WELL_HEALTH = "WELL_HEALTH"
    MULTI_WELL_COMPARE = "MULTI_WELL_COMPARE"
    FLEET_INVENTORY = "FLEET_INVENTORY"
    FLEET_PRODUCTION = "FLEET_PRODUCTION"
    FLEET_TRIAGE = "FLEET_TRIAGE"
    FLEET_EXECUTIVE = "FLEET_EXECUTIVE"
    FLEET_ANOMALY = "FLEET_ANOMALY"
    FLEET_TIMELINE = "FLEET_TIMELINE"
    CLUSTER_COMPARE = "CLUSTER_COMPARE"
    HISTORICAL_COMPARE = "HISTORICAL_COMPARE"
    PEER_BENCHMARK = "PEER_BENCHMARK"
    EVENT_BEFORE_AFTER = "EVENT_BEFORE_AFTER"
    FLEET_RANKING = "FLEET_RANKING"
    PRODUCTION = "PRODUCTION"
    KNOWLEDGE = "KNOWLEDGE"
    WORK_ORDER_DISPATCH = "WORK_ORDER_DISPATCH"
    CHAT = "CHAT"


class HybridRouteResult(BaseModel):
    intent: ESPIntentEnum
    entity: str | None = None
    entities: list[str] = Field(default_factory=list, description="Multiple entities for comparison queries")
    time_filter_label: str | None = None
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    routing_tier: str = "TIER_0_REGEX"
    needs_clarification: bool = False
    clarification_question: str | None = None
    suggested_options: list[str] = []


class PetroleumChunk(BaseModel):
    chunk_id: str
    doc_title: str
    section_title: str | None = None
    content: str
    relevance_score: float


class WellHealthReport(BaseModel):
    well_id: str
    health_index_pct: float
    operating_state: str
    current_amps: float
    rated_amps: float
    current_status: str
    vibration_g: float
    max_vibration_g: float
    vibration_status: str
    intake_pressure_psi: float
    discharge_pressure_psi: float
    motor_temperature_c: float
    alerts: list[str] = []
    markdown_report: str
    llm_recommendation: str | None = None


class FleetInventoryReport(BaseModel):
    total_wells: int
    active_wells: int
    total_motor_hp: float
    clusters: list[dict[str, Any]]
    markdown_report: str
    running_wells_count: int = 0
    tripped_wells_count: int = 0
    unmonitored_wells_count: int = 0
    running_wells: list[str] = []
    tripped_wells: list[dict[str, Any]] = []


class WellProductionSummary(BaseModel):
    well_id: str
    flow_rate_bpd: float
    water_cut_pct: float
    operating_state: str
    intake_pressure_psi: float
    discharge_pressure_psi: float
    gas_flow_mscfd: float | None = None
    markdown_report: str


class DispatchWorkOrderRequest(BaseModel):
    well_id: str = Field(description="Target well identifier (e.g. FNW-001, FS-017)")
    event_id: str | None = Field(default=None, description="Optional associated trip event ID")
    trip_cause: str | None = Field(default=None, description="Trip cause triggering maintenance")
    severity: str | None = Field(default=None, description="Severity level, e.g. CRITICAL or HIGH")
    primary_fault: str | None = Field(default=None, description="Diagnosed root cause hypothesis")
    recommended_actions: list[str] = Field(default_factory=list, description="Recommended maintenance and inspection steps")
    priority: PriorityEnum = Field(default=PriorityEnum.P1, description="Work order priority (P1-P4)")


class DispatchWorkOrderResponse(BaseModel):
    success: bool
    work_order_id: int
    work_order_code: str
    title: str
    status: str
    priority: str
    assigned_checklist_count: int
    mandatory_loto_enforced: bool
    message: str


# =========================================================================
# DOMAIN 1: FLEET ANALYSIS EXPANDED SCHEMAS
# =========================================================================

class FleetProductionSummary(BaseModel):
    total_wells: int
    running_wells_count: int
    tripped_wells_count: int
    availability_factor_pct: float
    current_liquid_rate_bpd: float
    current_net_oil_bpd: float
    average_water_cut_pct: float
    deferred_liquid_rate_bpd: float
    deferred_net_oil_bpd: float
    fleet_production_efficiency_pct: float
    cluster_production_breakdown: list[dict[str, Any]] = []
    markdown_report: str


class TriageWellItem(BaseModel):
    rank: int
    well_id: str
    operating_state: str
    severity: str
    dominant_issue: str
    peak_vibration_g: float | None = None
    motor_current_a: float | None = None
    deferred_oil_bpd: float = 0.0
    recommended_urgency: str


class FleetTriageReport(BaseModel):
    total_assets_triaged: int
    critical_count: int
    warning_count: int
    triaged_wells: list[TriageWellItem] = []
    markdown_report: str


class FleetExecutiveReport(BaseModel):
    generated_at: str
    fleet_availability_pct: float
    online_wells_ratio: str
    current_bopd: float
    deferred_bopd: float
    top_deferment_asset: str
    fleet_health_index_avg: float
    supervisory_mandates: list[str] = []
    markdown_report: str


class AnomalyWellItem(BaseModel):
    well_id: str
    anomaly_category: str
    current_val: float
    baseline_p50: float
    threshold_p90: float
    deviation_pct: float


class FleetAnomalyReport(BaseModel):
    running_wells_audited: int
    anomalous_running_count: int
    anomalies: list[AnomalyWellItem] = []
    markdown_report: str


class AlarmTimeBucket(BaseModel):
    time_bucket: str
    trip_count: int
    dominant_cause: str


class FleetAlarmTimelineReport(BaseModel):
    time_window_days: int
    total_trip_events: int
    dominant_fleet_trip_cause: str
    cluster_clustering: dict[str, int] = {}
    daily_density: list[AlarmTimeBucket] = []
    markdown_report: str


# =========================================================================
# DOMAIN 2: FLEET COMPARISON EXPANDED SCHEMAS
# =========================================================================

class WellComparisonReport(BaseModel):
    wells: list[str]
    parameters: list[dict[str, Any]]
    markdown_report: str


class ClusterComparisonReport(BaseModel):
    cluster_a: str
    cluster_b: str
    cluster_a_metrics: dict[str, Any]
    cluster_b_metrics: dict[str, Any]
    deltas: dict[str, Any]
    markdown_report: str


class HistoricalComparisonReport(BaseModel):
    well_id: str
    current_window_label: str
    baseline_window_label: str
    comparison_table: list[dict[str, Any]]
    markdown_report: str


class PeerBenchmarkReport(BaseModel):
    well_id: str
    cluster: str
    peer_count: int
    benchmark_table: list[dict[str, Any]]
    markdown_report: str


class EventBeforeAfterReport(BaseModel):
    well_id: str
    event_id: str
    event_timestamp: str
    trip_cause: str
    metrics_comparison: list[dict[str, Any]]
    markdown_report: str


class FleetRankItem(BaseModel):
    rank: int
    well_id: str
    cluster: str
    metric_name: str
    metric_value: float
    operating_state: str
    deviation_vs_median_pct: float


class FleetRankingReport(BaseModel):
    ranking_metric: str
    sort_order: str
    fleet_median: float
    leaderboard: list[FleetRankItem]
    markdown_report: str

