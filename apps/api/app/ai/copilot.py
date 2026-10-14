"""Copilot high-level capabilities: fault parsing, diagnosis, polishing, reports, Q&A, historical summaries."""

from __future__ import annotations

import re

from datetime import UTC, datetime
from sqlalchemy.orm import Session

from app.ai.client import llm_client, record_ai_interaction
from app.ai.knowledge_search import find_similar_work_orders, search_articles
from app.models.base import PriorityEnum, UrgencyEnum, WorkOrderStatusEnum, WorkOrderTypeEnum
from app.models.equipment import Equipment
from app.models.workorder import WorkOrder, WorkOrderChecklistItem, WorkOrderStatusHistory
from app.services.work_order_codes import generate_work_order_code
from app.schemas.fault import ParseFaultResult
from app.schemas.knowledge import (
    AskResult,
    Citation,
    DiagnoseResult,
    HistorySummary,
    MaintenanceReport,
    ReportSection,
    RewriteLogResult,
    SimilarCase,
)

DISCLAIMER = "AI suggestions are for assistance only. Maintenance technicians must make judgments based on on-site conditions, equipment manuals, and safety specifications."


# ---------------- 1. Natural Language Fault Parsing ----------------


def parse_fault(db: Session, text: str, user_id: int | None = None) -> ParseFaultResult:
    result = ParseFaultResult(description=text, raw={"text": text})

    if llm_client.enabled:
        prompt = _build_parse_prompt(db, text)
        resp = llm_client.chat(prompt, json_mode=True)
        if resp["content"]:
            data = llm_client.parse_json(resp["content"])
            if data:
                result = _coerce_parse(data, text)
                record_ai_interaction(
                    db,
                    user_id,
                    "parse_fault",
                    text,
                    resp["content"],
                    resp["is_mock"],
                    resp["model"],
                    resp.get("latency_ms", 0),
                    resp["error"],
                )
                return result
        # Fallback to rule-based parse if AI fails
        record_ai_interaction(
            db,
            user_id,
            "parse_fault",
            text,
            None,
            True,
            resp["model"],
            0,
            resp["error"],
        )

    # Rule-based parsing (Mock / Fallback)
    parsed = _rule_based_parse(db, text)
    record_ai_interaction(
        db, user_id, "parse_fault", text, str(parsed.dict()), True, "mock"
    )
    return parsed


def _build_parse_prompt(db: Session, text: str) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "You are an industrial equipment fault parsing assistant. Extract structured fault information from user natural language input, "
                "returning JSON with fields: title, description, equipment_keyword, phenomenon, "
                "fault_code, is_downtime(bool), affects_production(bool), has_safety_risk(bool), "
                "urgency(low/medium/high/critical), suggested_priority(P1-P4), confidence(0-1). "
                "Return only JSON with no extra explanation."
            ),
        },
        {"role": "user", "content": text},
    ]


def _coerce_parse(data: dict, text: str) -> ParseFaultResult:
    urgency = data.get("urgency", "medium")
    try:
        urgency = UrgencyEnum(urgency)
    except ValueError:
        urgency = UrgencyEnum.medium
    return ParseFaultResult(
        title=data.get("title"),
        description=data.get("description", text),
        equipment_keyword=data.get("equipment_keyword"),
        phenomenon=data.get("phenomenon"),
        fault_code=data.get("fault_code"),
        is_downtime=bool(data.get("is_downtime", False)),
        affects_production=bool(data.get("affects_production", False)),
        has_safety_risk=bool(data.get("has_safety_risk", False)),
        urgency=urgency,
        suggested_priority=data.get("suggested_priority"),
        confidence=float(data.get("confidence", 0.5)),
        raw=data,
    )


def _rule_based_parse(db: Session, text: str) -> ParseFaultResult:
    # Fault code pattern E1xx / E2xx / M1xx
    fc_match = re.search(r"[EeMm](\d{2,4})", text)
    fault_code = f"E{fc_match.group(1)}" if fc_match else None
    # Downtime detection
    is_downtime = any(
        k in text.lower() for k in ["downtime", "shutdown", "stopped", "unable to run", "cannot start", "halt"]
    )
    affects_production = any(
        k in text.lower() for k in ["entire line", "production line", "affects production", "stoppage", "line"]
    )
    has_safety_risk = any(
        k in text.lower() for k in ["noise", "smoke", "leakage", "spark", "high temp", "explosion", "abnormal sound", "overheat"]
    )
    urgency = (
        UrgencyEnum.critical
        if (is_downtime and affects_production)
        else UrgencyEnum.high
        if has_safety_risk
        else UrgencyEnum.medium
    )
    priority = (
        "P1"
        if urgency == UrgencyEnum.critical
        else "P2"
        if urgency == UrgencyEnum.high
        else "P3"
    )
    # Equipment keyword detection
    eq_keyword = None
    for kw in [
        "packaging machine",
        "air compressor",
        "cnc machine",
        "cnc",
        "conveyor",
        "robot",
        "press",
        "injection molding",
        "motor",
        "control cabinet",
    ]:
        if kw in text.lower():
            eq_keyword = kw
            break
    title = f"{eq_keyword.title() if eq_keyword else 'Equipment'} Fault" + (
        f"-E{fc_match.group(1)}" if fc_match else ""
    )
    return ParseFaultResult(
        title=title,
        description=text,
        equipment_keyword=eq_keyword,
        phenomenon=(eq_keyword.title() + " Abnormality") if eq_keyword else "Equipment Fault",
        fault_code=fault_code,
        is_downtime=is_downtime,
        affects_production=affects_production,
        has_safety_risk=has_safety_risk,
        urgency=urgency,
        suggested_priority=priority,
        confidence=0.6,
        raw={"method": "rule"},
    )


# ---------------- 2. AI Assisted Diagnostics ----------------


def diagnose(
    db: Session,
    fault_description: str,
    equipment_id: int | None,
    fault_code: str | None,
    wo: WorkOrder | None,
    user_id: int | None = None,
) -> DiagnoseResult:
    # Similar historical work orders
    similar: list[SimilarCase] = []
    if wo:
        for c, score in find_similar_work_orders(db, wo, limit=3):
            similar.append(
                SimilarCase(
                    work_order_id=c.id,
                    code=c.code,
                    title=c.title,
                    similarity=round(score, 2),
                    root_cause=c.root_cause,
                    action_taken=c.action_taken,
                )
            )

    if llm_client.enabled:
        prompt = _build_diagnose_prompt(
            db, fault_description, equipment_id, fault_code, similar
        )
        resp = llm_client.chat(prompt, json_mode=True)
        if resp["content"]:
            data = llm_client.parse_json(resp["content"])
            if data:
                result = DiagnoseResult(
                    possible_causes=data.get("possible_causes", []),
                    inspection_order=data.get("inspection_order", []),
                    safety_notes=data.get("safety_notes", []),
                    recommended_tools=data.get("recommended_tools", []),
                    recommended_parts=data.get("recommended_parts", []),
                    similar_cases=similar,
                    is_mock=False,
                )
                record_ai_interaction(
                    db,
                    user_id,
                    "diagnose",
                    fault_description,
                    resp["content"],
                    False,
                    resp["model"],
                    resp.get("latency_ms", 0),
                )
                return result
        record_ai_interaction(
            db,
            user_id,
            "diagnose",
            fault_description,
            None,
            True,
            resp["model"],
            0,
            resp["error"],
        )

    # Mock rule-based diagnosis
    result = _mock_diagnose(fault_description, fault_code, similar)
    record_ai_interaction(
        db,
        user_id,
        "diagnose",
        fault_description,
        result.model_dump_json(),
        True,
        "mock",
    )
    return result


def _build_diagnose_prompt(
    db, fault_description, equipment_id, fault_code, similar
) -> list[dict]:
    eq_info = ""
    if equipment_id:
        eq = db.get(Equipment, equipment_id)
        if eq:
            eq_info = f"Equipment: {eq.name}({eq.code}), Manufacturer: {eq.manufacturer}, Model: {eq.model}"
    return [
        {
            "role": "system",
            "content": (
                "You are an industrial equipment maintenance and diagnostics expert. Based on the fault description, return structured JSON: "
                "possible_causes (array of objects with cause and confidence), inspection_order (string array), "
                "safety_notes (string array), recommended_tools (string array), recommended_parts (string array). "
                "Strictly prohibit recommending bypassing safety devices, live disassembly, or bypassing interlocks. Return only JSON."
            ),
        },
        {
            "role": "user",
            "content": f"{eq_info}\nFault Code: {fault_code or 'Unknown'}\nFault Description: {fault_description}",
        },
    ]


def _mock_diagnose(
    fault_description: str, fault_code: str | None, similar: list[SimilarCase]
) -> DiagnoseResult:
    text = (fault_description or "").lower()
    causes = []
    if fault_code:
        causes.append(
            {"cause": f"Sensor or driver anomaly related to fault code {fault_code}", "confidence": 0.7}
        )
    if "noise" in text or "sound" in text or "abnormal" in text:
        causes.append({"cause": "Mechanical looseness or bearing wear causing abnormal noise", "confidence": 0.65})
    if "temperature" in text or "temp" in text or "overheat" in text:
        causes.append({"cause": "Poor heat dissipation or overload causing temperature rise", "confidence": 0.6})
    if "pressure" in text or "pneumatic" in text:
        causes.append({"cause": "Pneumatic leakage or filter blockage causing insufficient pressure", "confidence": 0.6})
    if "misalign" in text or "drift" in text or "belt" in text:
        causes.append({"cause": "Uneven belt tension or guide roller wear causing misalignment", "confidence": 0.7})
    if not causes:
        causes.append({"cause": "Control signal anomaly or sensor fault", "confidence": 0.5})
    safety = [
        "De-energization and Lockout/Tagout (LOTO) must be executed before servicing",
        "Verify residual energy has been dissipated",
        "Wear appropriate personal protective equipment (PPE)",
    ]
    if "electric" in text or "cabinet" in text or "voltage" in text:
        safety.append("Electrical work must be performed by certified electricians using insulated tools")
    if "temperature" in text or "heat" in text or "hot" in text:
        safety.append("Allow equipment to cool down before contact to prevent burn injuries")
    return DiagnoseResult(
        possible_causes=causes,
        inspection_order=[
            "Confirm equipment is stopped and de-energized",
            "Execute Lockout/Tagout (LOTO)",
            "Read and record fault codes",
            "Inspect relevant sensors and wiring",
            "Inspect mechanical connections and lubrication",
            "Replace components if necessary",
            "Restore power and perform verification test",
        ],
        safety_notes=safety,
        recommended_tools=["Multimeter", "Insulated Gloves", "Torque Wrench", "Hex Key Set"],
        recommended_parts=["Proximity Switch", "Fuse", "Relay"],
        similar_cases=similar,
        is_mock=True,
    )


# ---------------- 3. Maintenance Record Normalization ----------------


def rewrite_log(
    db: Session, content: str, user_id: int | None = None
) -> RewriteLogResult:
    if llm_client.enabled:
        prompt = [
            {
                "role": "system",
                "content": "You are a maintenance record normalization assistant. Rewrite colloquial maintenance logs into standardized, professional, and objective records, retaining key facts without hallucinating unverified assumptions. Output only the rewritten text.",
            },
            {"role": "user", "content": content},
        ]
        resp = llm_client.chat(prompt)
        if resp["content"]:
            record_ai_interaction(
                db,
                user_id,
                "rewrite_log",
                content,
                resp["content"],
                False,
                resp["model"],
                resp.get("latency_ms", 0),
            )
            return RewriteLogResult(
                original=content, polished=resp["content"], is_mock=False
            )
        record_ai_interaction(
            db,
            user_id,
            "rewrite_log",
            content,
            None,
            True,
            resp["model"],
            0,
            resp["error"],
        )
    polished = _mock_rewrite(content)
    record_ai_interaction(db, user_id, "rewrite_log", content, polished, True, "mock")
    return RewriteLogResult(original=content, polished=polished, is_mock=True)


def _mock_rewrite(content: str) -> str:
    c = content.strip()
    prefix = "Upon inspection, " if not c.lower().startswith("upon inspection") else ""
    suffix = "" if c.endswith(".") else "."
    return f"{prefix}{c}{suffix}"


# ---------------- 4. Automated Completion Report ----------------


def generate_report(
    db: Session,
    wo_id: int,
    user_id: int | None = None,
    force_template: bool = False,
) -> MaintenanceReport:
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        return MaintenanceReport(
            work_order_id=wo_id, work_order_code="", summary="Work order does not exist", is_mock=True
        )
    eq_name = ""
    if wo.equipment_id:
        eq = db.get(Equipment, wo.equipment_id)
        if eq:
            eq_name = f"{eq.name}({eq.code})"

    sections = [
        ReportSection(
            title="Fault Overview",
            content=f"{wo.title}. {wo.fault_description or ''}".strip(),
        ),
        ReportSection(
            title="Impact Scope",
            content=f"Equipment: {eq_name}. Downtime impact: {'Yes' if wo.safety_risk else 'No'}.",
        ),
        ReportSection(title="Root Cause", content=wo.root_cause or "Not recorded"),
        ReportSection(title="Corrective Action", content=wo.action_taken or "Not recorded"),
        ReportSection(title="Replaced Parts", content=wo.replaced_parts or "None"),
        ReportSection(title="Test Result", content=wo.test_result or "Not recorded"),
        ReportSection(
            title="Safety Measures", content=wo.safety_risk or "De-energization and LOTO executed"
        ),
        ReportSection(
            title="Follow-up Recommendations", content=wo.follow_up_advice or "Continue monitoring equipment operating condition"
        ),
    ]
    summary = f"Work order {wo.code} completed. Equipment {eq_name} fault root cause was '{wo.root_cause or 'Unknown'}'; executed '{wo.action_taken or 'Repair'}'; test result: {wo.test_result or 'Normal'}."

    if llm_client.enabled and not force_template:
        prompt = _build_report_prompt(wo, eq_name, sections)
        resp = llm_client.chat(prompt, json_mode=True)
        if resp["content"]:
            data = llm_client.parse_json(resp["content"])
            if data and "sections" in data:
                sections = [
                    ReportSection(
                        title=s.get("title", ""), content=s.get("content", "")
                    )
                    for s in data["sections"]
                ]
                summary = data.get("summary", summary)
                record_ai_interaction(
                    db,
                    user_id,
                    "generate_report",
                    str(wo_id),
                    resp["content"],
                    False,
                    resp["model"],
                    resp.get("latency_ms", 0),
                )
                return MaintenanceReport(
                    work_order_id=wo.id,
                    work_order_code=wo.code,
                    sections=sections,
                    summary=summary,
                    is_mock=False,
                )
        record_ai_interaction(
            db,
            user_id,
            "generate_report",
            str(wo_id),
            None,
            True,
            resp["model"],
            0,
            resp["error"],
        )

    record_ai_interaction(
        db, user_id, "generate_report", str(wo_id), summary, True, "mock"
    )
    return MaintenanceReport(
        work_order_id=wo.id,
        work_order_code=wo.code,
        sections=sections,
        summary=summary,
        is_mock=True,
    )


def _build_report_prompt(wo, eq_name, sections) -> list[dict]:
    base = "\n".join(f"{s.title}: {s.content}" for s in sections)
    return [
        {
            "role": "system",
            "content": "You are a maintenance report generation assistant. Generate structured maintenance report JSON from work order data, containing sections (array of objects with title and content) and summary fields. Objective and rigorous, do not invent data. Return only JSON.",
        },
        {
            "role": "user",
            "content": f"Work order: {wo.code}\nEquipment: {eq_name}\nBase data:\n{base}",
        },
    ]


# ---------------- 5. Knowledge Base Q&A ----------------


def ask(
    db: Session,
    question: str,
    equipment_type_id: int | None = None,
    fault_code: str | None = None,
    user_id: int | None = None,
    conversation_history: list[dict[str, Any]] | None = None,
) -> AskResult:
    """Enterprise Hybrid Copilot Ask: Routes across Event Diagnosis, Well History, Well Health, Multi-Well Comparison, Fleet Inventory, Production, and Petroleum Standards RAG."""
    import logging
    logger = logging.getLogger("app.copilot")

    from app.services.esp_diagnosis_service import (
        route_query_hybrid,
        diagnose_esp_event,
        get_well_historical_analysis,
        get_well_health_status,
        get_fleet_inventory_status,
        get_fleet_production_summary,
        get_fleet_triage_ranking,
        get_fleet_executive_report,
        get_fleet_anomaly_surfacing,
        get_fleet_alarm_timeline,
        get_well_production_metrics,
        search_petroleum_kb,
        compare_multiple_wells,
        compare_gathering_clusters,
        compare_well_historical,
        benchmark_well_against_peers,
        compare_event_before_after,
        rank_fleet_by_metric,
    )
    from app.schemas.esp_diagnosis import DiagnoseEventRequest, ESPIntentEnum

    route = route_query_hybrid(question, conversation_history=conversation_history)

    # 1. HITL Clarification Needed (Missing Well/Event entity on ambiguous diagnostic question)
    if route.needs_clarification:
        return AskResult(
            answer=(
                f"### [ESP APM] Operational Clarification Required\n\n"
                f"{route.clarification_question or 'Please specify which well or event you want to inspect.'}\n\n"
                f"Select an asset below or type the Well ID directly:"
            ),
            confidence=route.confidence,
            citations=[],
            warnings=["Operational Context Ambiguous: Please choose an asset option to focus the diagnostic engine."],
            needs_clarification=True,
            clarification_question=route.clarification_question,
            suggested_options=route.suggested_options,
            is_mock=False,
        )

    # 2. Conversational Chit-Chat
    if route.intent == ESPIntentEnum.CHAT:
        chat_reply = None
        if llm_client.enabled:
            try:
                system_prompt = (
                    "You are the ESP APM Industrial Maintenance Copilot connected to PostgreSQL `esp_apm_db` on Server 184. "
                    "You assist petroleum engineers and field operators with ESP diagnostics, trip root cause analysis, "
                    "fleet health surveillance, and petroleum engineering standards. "
                    "Respond naturally, warmly, and concisely (1-3 sentences) to the user's greeting or conversational query. "
                    "Always maintain your professional persona and briefly invite them to explore well diagnostics, "
                    "fleet status, or engineering standards."
                )
                messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
                if conversation_history:
                    for m in conversation_history[-4:]:
                        role = m.get("role") or ("user" if m.get("sender") == "user" else "assistant")
                        c = m.get("content") or m.get("text") or ""
                        if c:
                            messages.append({"role": role, "content": c})
                messages.append({"role": "user", "content": question})
                resp = llm_client.chat(messages)
                chat_reply = resp.get("content") if resp else None
            except Exception as e:
                logger.warning(f"Dynamic LLM chat synthesis failed: {e}")

        if not chat_reply:
            chat_reply = (
                "Hello! I am your **ESP APM Industrial Maintenance Copilot** connected to PostgreSQL `esp_apm_db` on Server 184.\n\n"
                "I can assist you with:\n"
                "- **Trip Event Diagnostics**: Paste an Event ID (e.g. `EV-20261012-103435-FNW-001-878`) or choose from the dropdown.\n"
                "- **Well Failure History**: Ask *'Show history of well FS-017 in last 7 days'* or `FS-040`.\n"
                "- **Multi-Well Comparative Analysis**: Ask *'Compare well FS-017 vs FS-040'*.\n"
                "- **Real-time Well Health**: Ask *'Is well FNW-001 healthy?'*.\n"
                "- **Fleet & Cluster Inventory**: Ask *'Show fleet inventory'* or *'GCS-15 cluster wells'*.\n"
                "- **Production Rates**: Ask *'What is flow rate of FS-017?'*.\n"
                "- **Petroleum Engineering Standards**: Ask *'What causes gas locking in an ESP?'* or *'How to prevent bearing wear?'*."
            )
        return AskResult(
            answer=chat_reply,
            confidence=1.0,
            citations=[],
            warnings=[],
            needs_clarification=False,
            suggested_options=["Compare FS-017 vs FS-040", "Check FNW-001 Health", "Audit FS-017 History", "Fleet Inventory"],
            is_mock=False,
        )

    # 2.5. Automated Work Order Dispatch (Gap 6)
    if route.intent == ESPIntentEnum.WORK_ORDER_DISPATCH:
        try:
            target_well = route.entity or "FNW-001"
            esp_res = diagnose_esp_event(DiagnoseEventRequest(well_id=target_well))
            p_fault = esp_res.structured_data.get("signature", {}).get("fault_name") or esp_res.trip_cause or "ESP Shutdown"
            ev_id = esp_res.event_id

            wo_code = generate_work_order_code()
            title = f"EMERGENCY LOTO REPAIR: Well {target_well} - {p_fault}"
            safety_risk = "MANDATORY LOTO & ELECTRICAL ISOLATION: De-energize Variable Speed Drive (VSD) and surface switchgear; verify zero-voltage state with calibrated multimeter. Depressurize wellhead flowlines before inspection."
            diag_summary = (
                f"Automated AI Copilot Dispatch for Well {target_well} (Event: {ev_id}).\n"
                f"Primary Root Cause: {p_fault} ({esp_res.structured_data.get('signature', {}).get('citation', '')}).\n"
                f"Telemetry Inflection: Peak vibration {esp_res.structured_data.get('deviations', [{}])[0].get('pre_trip_val', 'N/A')}g, "
                f"Peak motor current {esp_res.structured_data.get('deviations', [{}])[1].get('pre_trip_val', 'N/A')}A."
            )
            acceptance = (
                "1. Verified zero-energy state via multimeter test.\n"
                "2. Motor insulation resistance > 10 MΩ via 1000V Megger.\n"
                "3. Free manual drive rotation with turning tool.\n"
                "4. Dynamic fluid level verified via echometer.\n"
                "5. Petroleum Production Engineer and Electrical Supervisor signed approval."
            )

            wo = WorkOrder(
                code=wo_code,
                title=title,
                order_type=WorkOrderTypeEnum.fault_repair,
                priority=PriorityEnum.P1,
                status=WorkOrderStatusEnum.pending_dispatch,
                safety_risk=safety_risk,
                ai_diagnosis_summary=diag_summary,
                acceptance_criteria=acceptance,
                created_by_id=user_id or 1,
                created_by=str(user_id or 1),
            )
            db.add(wo)
            db.flush()

            db.add(
                WorkOrderStatusHistory(
                    work_order_id=wo.id,
                    from_status=None,
                    to_status=WorkOrderStatusEnum.pending_dispatch.value,
                    changed_by=user_id or 1,
                    changed_at=datetime.now(UTC),
                    remark="Automated Copilot Work Order Dispatch with Mandatory LOTO Enforced",
                )
            )

            loto_items = [
                ("safety", "MANDATORY LOTO: De-energize and Lockout/Tagout VSD surface switchboard and main feeder", True),
                ("safety", "ZERO-ENERGY VERIFICATION: Test all incoming and motor leads with 1000V calibrated multimeter", True),
                ("safety", "HYDRAULIC ISOLATION: Close wing valve, master valve, and dissipate wellhead flowline trapped pressure", True),
                ("diagnosis", f"VSD FAULT LOG AUDIT: Extract VSD memory fault codes and trip event logs for {target_well}", True),
                ("repair", "ELECTRICAL MEGGER TEST: Measure Phase-to-Phase and Phase-to-Ground resistance (min 10 MΩ)", True),
                ("repair", "MECHANICAL FREE ROTATION: Rotate shaft with drive turning tool; verify zero drag or impeller seizure", True),
                ("repair", "WELLHEAD INTEGRITY: Inspect surface sand desander trap and measure BS&W solids cut", False),
                ("testing", "PRE-RESTART SIGN-OFF: Review echometer fluid level and obtain Petroleum Production Engineer sign-off", True),
            ]
            for idx, (cat, content, req) in enumerate(loto_items):
                db.add(
                    WorkOrderChecklistItem(
                        work_order_id=wo.id,
                        category=cat,
                        content=content,
                        order=idx,
                        is_required=req,
                    )
                )
            db.commit()
            db.refresh(wo)

            md_reply = (
                f"# [ESP APM] Work Order Successfully Dispatched\n\n"
                f"**Work Order Code**: `{wo.code}` | **Work Order ID**: `#{wo.id}`\n\n"
                f"### Work Order Details\n"
                f"- **Target Asset**: Well `{target_well}`\n"
                f"- **Priority**: `P1 - Critical Emergency Dispatch`\n"
                f"- **Status**: `{wo.status.value}` (Pending Supervisor Assignment)\n"
                f"- **Primary Root Cause**: `{p_fault}`\n"
                f"- **Associated Event**: `{ev_id}`\n\n"
                f"### Mandatory Safety & LOTO Governance\n"
                f"> **Safety Alert**: *{safety_risk}*\n\n"
                f"### Assigned Checklist ({len(loto_items)} Steps):\n"
                + "\n".join([f"{i+1}. **[{c[0].upper()}]** {c[1]}" + (" *(Mandatory)*" if c[2] else "") for i, c in enumerate(loto_items)])
                + f"\n\n---\n*The work order has been created in the local maintenance database and queued for execution.*"
            )

            citations = [
                Citation(
                    source_type="work_order_database",
                    source_id=wo.id,
                    title=f"Work Order {wo.code} (Well {target_well})",
                    excerpt=f"Priority P1 work order created with {len(loto_items)} mandatory LOTO and diagnostic items",
                    relevance_score=1.0,
                    url=None,
                )
            ]

            record_ai_interaction(
                db, user_id, "esp_dispatch_work_order", question, md_reply, False, llm_client.model, 0
            )

            return AskResult(
                answer=md_reply,
                confidence=1.0,
                citations=citations,
                warnings=[f"Work order {wo.code} dispatched for Well {target_well}. Zero-voltage multimeter test required."],
                needs_clarification=False,
                suggested_options=[f"Diagnose {target_well}", f"Well {target_well} Health", f"Well {target_well} History", "Fleet Inventory"],
                is_mock=False,
                structured_data={
                    "work_order_id": wo.id,
                    "work_order_code": wo.code,
                    "well_id": target_well,
                    "priority": "P1",
                    "status": wo.status.value,
                    "checklist_count": len(loto_items),
                },
            )
        except Exception as e:
            logger.warning(f"Work order dispatch failed: {e}")
            db.rollback()

    # 3. Trip Event Diagnosis (with Telemetry Waveform Vector, Gap 4)
    if route.intent == ESPIntentEnum.EVENT_DIAGNOSE:
        try:
            ev_id = route.entity if (route.entity and route.entity.startswith("EV-")) else None
            w_id = route.entity if (route.entity and not route.entity.startswith("EV-")) else None
            esp_res = diagnose_esp_event(DiagnoseEventRequest(event_id=ev_id, well_id=w_id))
            citations = [
                Citation(
                    source_type="esp_fault_taxonomy",
                    source_id=1,
                    title=f"Taxonomy: {esp_res.structured_data['signature']['fault_name']}",
                    excerpt=esp_res.structured_data["signature"]["citation"],
                    relevance_score=0.96,
                    url=None,
                )
            ]
            record_ai_interaction(
                db, user_id, "esp_diagnose_ask", question, esp_res.markdown_report, False, llm_client.model, 0
            )
            return AskResult(
                answer=esp_res.markdown_report,
                confidence=round(esp_res.mathematical_confidence_pct / 100.0, 2),
                citations=citations,
                warnings=[
                    f"Active Telemetry Diagnosis: Well {esp_res.well_id} tripped with {esp_res.trip_cause}. Mandatory LOTO required before inspection."
                ],
                needs_clarification=False,
                suggested_options=[
                    f"Dispatch Work Order for {esp_res.well_id}",
                    f"Well {esp_res.well_id} History",
                    f"Well {esp_res.well_id} Health",
                    "Fleet Inventory",
                ],
                is_mock=False,
                structured_data=esp_res.structured_data,
            )
        except Exception as e:
            logger.warning(f"Diagnosis dispatch failed: {e}")

    # 3.5. Multi-Well Comparative Analysis (Gap 1)
    if route.intent == ESPIntentEnum.MULTI_WELL_COMPARE and route.entities:
        try:
            comp_report = compare_multiple_wells(route.entities)
            citations = [
                Citation(
                    source_type="postgresql_multi_well",
                    source_id=1,
                    title=f"Multi-Well Comparative Surveillance: {' vs '.join(route.entities)}",
                    excerpt=f"Side-by-side telemetry and baseline audit across {len(route.entities)} assets in Server 184 PostgreSQL",
                    relevance_score=0.98,
                    url=None,
                )
            ]
            record_ai_interaction(
                db, user_id, "esp_multi_well_compare", question, comp_report, False, llm_client.model, 0
            )
            return AskResult(
                answer=comp_report,
                confidence=0.98,
                citations=citations,
                warnings=[
                    f"Cross-Asset Analysis: Evaluated live telemetry across {len(route.entities)} wells ({', '.join(route.entities)})."
                ],
                needs_clarification=False,
                suggested_options=[f"Diagnose {w}" for w in route.entities] + ["Fleet Inventory"],
                is_mock=False,
            )
        except Exception as e:
            logger.warning(f"Multi-well comparison dispatch failed: {e}")

    # 3.6. Gathering Cluster Comparison (Domain 2.2)
    if route.intent == ESPIntentEnum.CLUSTER_COMPARE and route.entities and len(route.entities) >= 2:
        try:
            cl_res = compare_gathering_clusters(route.entities[0], route.entities[1])
            citations = [
                Citation(
                    source_type="postgresql_cluster_telemetry",
                    source_id=1,
                    title=f"Gathering Cluster Comparative Scorecard: {cl_res.cluster_a} vs {cl_res.cluster_b}",
                    excerpt=f"Comparative availability and production rollup between {cl_res.cluster_a} and {cl_res.cluster_b}",
                    relevance_score=0.99,
                    url=None,
                )
            ]
            record_ai_interaction(
                db, user_id, "esp_cluster_compare", question, cl_res.markdown_report, False, llm_client.model, 0
            )
            return AskResult(
                answer=cl_res.markdown_report,
                confidence=0.98,
                citations=citations,
                warnings=[],
                needs_clarification=False,
                suggested_options=["Fleet Production Summary", "Fleet Triage Ranking", "Compare FS-017 vs FS-040"],
                is_mock=False,
                structured_data=cl_res.dict(),
            )
        except Exception as e:
            logger.warning(f"Cluster comparison dispatch failed: {e}")

    # 3.7. Historical Baseline Comparison (Domain 2.3)
    if route.intent == ESPIntentEnum.HISTORICAL_COMPARE and route.entity:
        try:
            hist_comp = compare_well_historical(route.entity)
            citations = [
                Citation(
                    source_type="postgresql_historical_telemetry",
                    source_id=1,
                    title=f"Historical Baseline Audit: Well {route.entity}",
                    excerpt=f"24h current sensor average compared against baseline for {route.entity}",
                    relevance_score=0.98,
                    url=None,
                )
            ]
            record_ai_interaction(
                db, user_id, "esp_historical_compare", question, hist_comp.markdown_report, False, llm_client.model, 0
            )
            return AskResult(
                answer=hist_comp.markdown_report,
                confidence=0.98,
                citations=citations,
                warnings=[],
                needs_clarification=False,
                suggested_options=[f"Well {route.entity} Health", f"Benchmark {route.entity} vs Peers", f"History of {route.entity}"],
                is_mock=False,
                structured_data=hist_comp.dict(),
            )
        except Exception as e:
            logger.warning(f"Historical comparison dispatch failed: {e}")

    # 3.8. Peer Group Benchmarking (Domain 2.4)
    if route.intent == ESPIntentEnum.PEER_BENCHMARK and route.entity:
        try:
            peer_res = benchmark_well_against_peers(route.entity)
            citations = [
                Citation(
                    source_type="postgresql_peer_telemetry",
                    source_id=1,
                    title=f"Peer Group Benchmarking: Well {route.entity}",
                    excerpt=f"Target well telemetry evaluated against {peer_res.peer_count} cluster peers",
                    relevance_score=0.98,
                    url=None,
                )
            ]
            record_ai_interaction(
                db, user_id, "esp_peer_benchmark", question, peer_res.markdown_report, False, llm_client.model, 0
            )
            return AskResult(
                answer=peer_res.markdown_report,
                confidence=0.98,
                citations=citations,
                warnings=[],
                needs_clarification=False,
                suggested_options=[f"Well {route.entity} Health", f"Historical Baseline for {route.entity}", "Fleet Ranking by Vibration"],
                is_mock=False,
                structured_data=peer_res.dict(),
            )
        except Exception as e:
            logger.warning(f"Peer benchmarking dispatch failed: {e}")

    # 3.9. Before vs After Event Comparison (Domain 2.5)
    if route.intent == ESPIntentEnum.EVENT_BEFORE_AFTER:
        try:
            ev_id = route.entity if (route.entity and route.entity.startswith("EV-")) else None
            w_id = route.entity if (route.entity and not route.entity.startswith("EV-")) else None
            ba_res = compare_event_before_after(event_id=ev_id, well_id=w_id)
            citations = [
                Citation(
                    source_type="postgresql_event_telemetry",
                    source_id=1,
                    title=f"Before/After Event Inflection: {ba_res.event_id}",
                    excerpt=f"2h pre-event vs post-event sensor delta for well {ba_res.well_id}",
                    relevance_score=0.98,
                    url=None,
                )
            ]
            record_ai_interaction(
                db, user_id, "esp_event_before_after", question, ba_res.markdown_report, False, llm_client.model, 0
            )
            return AskResult(
                answer=ba_res.markdown_report,
                confidence=0.98,
                citations=citations,
                warnings=[],
                needs_clarification=False,
                suggested_options=[f"Diagnose Event {ba_res.event_id}", f"Dispatch Work Order for {ba_res.well_id}", "Fleet Triage Ranking"],
                is_mock=False,
                structured_data=ba_res.dict(),
            )
        except Exception as e:
            logger.warning(f"Before/After event comparison dispatch failed: {e}")

    # 3.10. Fleet Metric Ranking & Leaderboard (Domain 2.6)
    if route.intent == ESPIntentEnum.FLEET_RANKING:
        try:
            metric_target = route.entity or "vibration"
            rank_res = rank_fleet_by_metric(metric=metric_target)
            citations = [
                Citation(
                    source_type="postgresql_fleet_telemetry",
                    source_id=1,
                    title=f"Fleet Metric Leaderboard: {rank_res.ranking_metric}",
                    excerpt=f"10-well ranking by {rank_res.ranking_metric} relative to fleet median",
                    relevance_score=0.99,
                    url=None,
                )
            ]
            record_ai_interaction(
                db, user_id, "esp_fleet_ranking", question, rank_res.markdown_report, False, llm_client.model, 0
            )
            return AskResult(
                answer=rank_res.markdown_report,
                confidence=0.98,
                citations=citations,
                warnings=[],
                needs_clarification=False,
                suggested_options=["Rank Wells by Temperature", "Rank Wells by Production", "Fleet Production Summary", "Fleet Triage Ranking"],
                is_mock=False,
                structured_data=rank_res.dict(),
            )
        except Exception as e:
            logger.warning(f"Fleet ranking dispatch failed: {e}")

    # 4. Well Failure History (with Temporal Window Filter, Gap 2)
    if route.intent == ESPIntentEnum.WELL_HISTORY and route.entity:
        try:
            t_days = 7 if (route.time_filter_label and "7" in route.time_filter_label) else (30 if (route.time_filter_label and "30" in route.time_filter_label) else (1 if (route.time_filter_label and "24" in route.time_filter_label) else None))
            hist_res = get_well_historical_analysis(route.entity, time_window_days=t_days, time_window_label=route.time_filter_label)
            window_suffix = f" ({route.time_filter_label})" if route.time_filter_label else ""
            citations = [
                Citation(
                    source_type="postgresql_esp_history",
                    source_id=1,
                    title=f"PostgreSQL Historical Audit: Well {route.entity}{window_suffix}",
                    excerpt=f"Total events: {hist_res['total_events']}, confirmed trips: {hist_res['total_trips']} in esp_apm_db",
                    relevance_score=0.98,
                    url=None,
                )
            ]
            record_ai_interaction(
                db, user_id, "esp_history_ask", question, hist_res["markdown_report"], False, llm_client.model, 0
            )
            return AskResult(
                answer=hist_res["markdown_report"],
                confidence=0.95,
                citations=citations,
                warnings=[
                    f"Historical Records from Server 184: Well {route.entity} has {hist_res['total_trips']} confirmed trips logged."
                ],
                needs_clarification=False,
                suggested_options=[f"Check {route.entity} Health", f"Diagnose {route.entity} Trip", "Fleet Inventory"],
                is_mock=False,
            )
        except Exception as e:
            logger.warning(f"History dispatch failed: {e}")

    # 5. Well Health Assessment
    if route.intent == ESPIntentEnum.WELL_HEALTH and route.entity:
        try:
            health_res = get_well_health_status(route.entity)
            citations = [
                Citation(
                    source_type="postgresql_asset_registry",
                    source_id=1,
                    title=f"Baseline Envelope: Well {route.entity}",
                    excerpt=f"Rated Amps: {health_res.rated_amps}A | Max Vibration: {health_res.max_vibration_g}g",
                    relevance_score=0.95,
                    url=None,
                )
            ]
            record_ai_interaction(
                db, user_id, "esp_health_ask", question, health_res.markdown_report, False, llm_client.model, 0
            )
            return AskResult(
                answer=health_res.markdown_report,
                confidence=round(health_res.health_index_pct / 100.0, 2),
                citations=citations,
                warnings=health_res.alerts,
                needs_clarification=False,
                suggested_options=[f"Well {route.entity} History", f"Well {route.entity} Production", "Fleet Inventory"],
                is_mock=False,
            )
        except Exception as e:
            logger.warning(f"Health dispatch failed: {e}")

    # 6. Fleet Inventory
    if route.intent == ESPIntentEnum.FLEET_INVENTORY:
        try:
            fleet_res = get_fleet_inventory_status(cluster=route.entity)
            citations = [
                Citation(
                    source_type="postgresql_telemetry",
                    source_id=1,
                    title="Live Telemetry: Operational Fleet Status",
                    excerpt=f"Running wells: {fleet_res.running_wells_count}, Tripped/Stopped: {fleet_res.tripped_wells_count}, Unmonitored: {fleet_res.unmonitored_wells_count}",
                    relevance_score=0.99,
                    url=None,
                ),
                Citation(
                    source_type="postgresql_asset_registry",
                    source_id=2,
                    title="Asset Registry: Fleet Summary",
                    excerpt=f"Total registered wells: {fleet_res.total_wells}, Total installed power: {fleet_res.total_motor_hp:.1f} HP",
                    relevance_score=0.95,
                    url=None,
                ),
            ]
            record_ai_interaction(
                db, user_id, "esp_fleet_ask", question, fleet_res.markdown_report, False, llm_client.model, 0
            )
            return AskResult(
                answer=fleet_res.markdown_report,
                confidence=0.95,
                citations=citations,
                warnings=[],
                needs_clarification=False,
                suggested_options=["FNW-001 Health", "FS-017 History", "Cluster GCS-15", "Cluster GCS-4"],
                is_mock=False,
            )
        except Exception as e:
            logger.warning(f"Fleet inventory dispatch failed: {e}")

    # 6.1 Fleet Production & Deferment Summary (Domain 1.3)
    if route.intent == ESPIntentEnum.FLEET_PRODUCTION:
        try:
            prod_res = get_fleet_production_summary()
            citations = [
                Citation(
                    source_type="postgresql_telemetry",
                    source_id=1,
                    title="Live Fleet Production & Deferment Audit",
                    excerpt=f"Active Oil: {prod_res.current_net_oil_bpd:.1f} BOPD, Deferred Loss: {prod_res.deferred_net_oil_bpd:.1f} BOPD across {prod_res.total_wells} wells",
                    relevance_score=0.99,
                    url=None,
                )
            ]
            record_ai_interaction(
                db, user_id, "esp_fleet_production_ask", question, prod_res.markdown_report, False, llm_client.model, 0
            )
            return AskResult(
                answer=prod_res.markdown_report,
                confidence=0.98,
                citations=citations,
                warnings=[f"Fleet Deferment: {prod_res.deferred_net_oil_bpd:.1f} BOPD currently shut in across {prod_res.tripped_wells_count} offline wells."],
                needs_clarification=False,
                suggested_options=["Fleet Triage Ranking", "Executive Summary", "Fleet Anomalies", "Fleet Status"],
                is_mock=False,
                structured_data=prod_res.dict(),
            )
        except Exception as e:
            logger.warning(f"Fleet production dispatch failed: {e}")

    # 6.2 Fleet Triage & Priority Ranking (Domain 1.4)
    if route.intent == ESPIntentEnum.FLEET_TRIAGE:
        try:
            triage_res = get_fleet_triage_ranking()
            citations = [
                Citation(
                    source_type="postgresql_events",
                    source_id=1,
                    title="Fleet Maintenance Triage Matrix",
                    excerpt=f"Triaged {triage_res.total_assets_triaged} offline assets: {triage_res.critical_count} Critical, {triage_res.warning_count} Warning",
                    relevance_score=0.99,
                    url=None,
                )
            ]
            record_ai_interaction(
                db, user_id, "esp_fleet_triage_ask", question, triage_res.markdown_report, False, llm_client.model, 0
            )
            return AskResult(
                answer=triage_res.markdown_report,
                confidence=0.98,
                citations=citations,
                warnings=[f"Action Priority: {triage_res.critical_count} critical tripped wells require Immediate LOTO and root-cause clearance."],
                needs_clarification=False,
                suggested_options=["Executive Summary", "Fleet Production Summary", "Diagnose FNW-001", "Fleet Status"],
                is_mock=False,
                structured_data=triage_res.dict(),
            )
        except Exception as e:
            logger.warning(f"Fleet triage dispatch failed: {e}")

    # 6.3 Fleet Executive Briefing & KPI Reporting (Domain 1.5)
    if route.intent == ESPIntentEnum.FLEET_EXECUTIVE:
        try:
            exec_res = get_fleet_executive_report()
            citations = [
                Citation(
                    source_type="postgresql_executive_rollup",
                    source_id=1,
                    title="Executive Operations KPI Scorecard",
                    excerpt=f"Fleet Availability: {exec_res.fleet_availability_pct}% | Active Oil: {exec_res.current_bopd:.1f} BOPD",
                    relevance_score=0.99,
                    url=None,
                )
            ]
            record_ai_interaction(
                db, user_id, "esp_fleet_executive_ask", question, exec_res.markdown_report, False, llm_client.model, 0
            )
            return AskResult(
                answer=exec_res.markdown_report,
                confidence=0.98,
                citations=citations,
                warnings=[],
                needs_clarification=False,
                suggested_options=["Fleet Triage Ranking", "Fleet Production Summary", "Fleet Anomalies", "Fleet Status"],
                is_mock=False,
                structured_data=exec_res.dict(),
            )
        except Exception as e:
            logger.warning(f"Fleet executive dispatch failed: {e}")

    # 6.4 Fleet Anomaly Surfacing & Early Warning (Domain 1.6)
    if route.intent == ESPIntentEnum.FLEET_ANOMALY:
        try:
            anomaly_res = get_fleet_anomaly_surfacing()
            citations = [
                Citation(
                    source_type="postgresql_telemetry_envelope",
                    source_id=1,
                    title="Fleet Sensor Drift & Anomaly Surveillance",
                    excerpt=f"Audited {anomaly_res.running_wells_audited} running assets: {anomaly_res.anomalous_running_count} sub-trip deviations detected",
                    relevance_score=0.98,
                    url=None,
                )
            ]
            record_ai_interaction(
                db, user_id, "esp_fleet_anomaly_ask", question, anomaly_res.markdown_report, False, llm_client.model, 0
            )
            return AskResult(
                answer=anomaly_res.markdown_report,
                confidence=0.98,
                citations=citations,
                warnings=[f"Early Warning: {anomaly_res.anomalous_running_count} running wells displaying continuous baseline drift."],
                needs_clarification=False,
                suggested_options=["Fleet Status", "Fleet Triage Ranking", "Executive Summary"],
                is_mock=False,
                structured_data=anomaly_res.dict(),
            )
        except Exception as e:
            logger.warning(f"Fleet anomaly dispatch failed: {e}")

    # 6.5 Fleet Alarm Timeline & Incident Clustering (Domain 1.7)
    if route.intent == ESPIntentEnum.FLEET_TIMELINE:
        try:
            timeline_res = get_fleet_alarm_timeline()
            citations = [
                Citation(
                    source_type="postgresql_events_density",
                    source_id=1,
                    title="Fleet Trip Event Frequency & Clustering",
                    excerpt=f"Historical total trips: {timeline_res.total_trip_events} | Dominant cause: {timeline_res.dominant_fleet_trip_cause}",
                    relevance_score=0.98,
                    url=None,
                )
            ]
            record_ai_interaction(
                db, user_id, "esp_fleet_timeline_ask", question, timeline_res.markdown_report, False, llm_client.model, 0
            )
            return AskResult(
                answer=timeline_res.markdown_report,
                confidence=0.98,
                citations=citations,
                warnings=[],
                needs_clarification=False,
                suggested_options=["Fleet Triage Ranking", "Executive Summary", "Fleet Status"],
                is_mock=False,
                structured_data=timeline_res.dict(),
            )
        except Exception as e:
            logger.warning(f"Fleet timeline dispatch failed: {e}")

    # 7. Production Telemetry
    if route.intent == ESPIntentEnum.PRODUCTION and route.entity:
        try:
            prod_res = get_well_production_metrics(route.entity)
            citations = [
                Citation(
                    source_type="postgresql_telemetry",
                    source_id=1,
                    title=f"Telemetry Production Stream: Well {route.entity}",
                    excerpt=f"Flow Rate: {prod_res.flow_rate_bpd:.1f} BPD | Water Cut: {prod_res.water_cut_pct:.1f}%",
                    relevance_score=0.95,
                    url=None,
                )
            ]
            record_ai_interaction(
                db, user_id, "esp_prod_ask", question, prod_res.markdown_report, False, llm_client.model, 0
            )
            return AskResult(
                answer=prod_res.markdown_report,
                confidence=0.95,
                citations=citations,
                warnings=[],
                needs_clarification=False,
                suggested_options=[f"Well {route.entity} Health", f"Well {route.entity} History", "Fleet Inventory"],
                is_mock=False,
            )
        except Exception as e:
            logger.warning(f"Production dispatch failed: {e}")

    # 8. Knowledge Base (Petroleum Standards RAG against 7,856 chunks in kb_chunks)
    kb_chunks = search_petroleum_kb(question, limit=4)
    if kb_chunks:
        citations = [
            Citation(
                source_type="petroleum_standard_manual",
                source_id=idx + 1,
                title=f"{c.doc_title}{f' — {c.section_title}' if c.section_title else ''}",
                excerpt=c.content[:280] + ("..." if len(c.content) > 280 else ""),
                relevance_score=round(c.relevance_score, 2),
                url=None,
            )
            for idx, c in enumerate(kb_chunks)
        ]
        context_str = "\n\n".join([
            f"[{c.doc_title} | {c.section_title or 'Section'}]\n{c.content[:900]}"
            for c in kb_chunks
        ])

        answer = None
        if llm_client.enabled:
            prompt = [
                {
                    "role": "system",
                    "content": (
                        "You are an authoritative Petroleum Artificial Lift Engineer specializing in Electric Submersible Pumps (ESPs). "
                        "Answer the technical question based strictly on the provided technical manual references from API RP 11S, ChampionX, Weatherford, and field engineering standards. "
                        "Provide a structured, rigorous engineering troubleshooting explanation with operational diagnostics, warning signs, and corrective SOP maintenance procedures (under 250 words). "
                        "Never recommend bypassing safety interlocks or live electrical work."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Technical References:\n{context_str}\n\nQuestion: {question}",
                },
            ]
            resp = llm_client.chat(prompt, max_tokens=350)
            if resp.get("content") and not resp.get("error"):
                answer = resp["content"].strip()

        if not answer:
            top = kb_chunks[0]
            answer = (
                f"# [ESP Technical Knowledge] {top.doc_title}\n\n"
                f"**Section**: {top.section_title or 'Standard Operating Procedures'}\n\n"
                f"{top.content}\n\n"
                f"---\n"
                f"> *Retrieved from PostgreSQL `kb_chunks` repository on Server 184.*"
            )

        record_ai_interaction(
            db, user_id, "esp_kb_ask", question, answer, False, llm_client.model, 0
        )
        return AskResult(
            answer=answer,
            confidence=round(kb_chunks[0].relevance_score, 2),
            citations=citations,
            warnings=_build_safety_warnings(question),
            needs_clarification=False,
            suggested_options=["Gas Lock Prevention", "Bearing Wear Teardown", "Motor Overload Causes", "Fleet Inventory"],
            is_mock=False,
        )

    # 9. Fallback: Attempt dynamic LLM synthesis before returning generic refusal
    if llm_client.enabled:
        try:
            llm_reply = llm_client.chat([
                {
                    "role": "system",
                    "content": (
                        "You are an expert Petroleum Artificial Lift Engineer and Industrial Maintenance Copilot for Electric Submersible Pumps (ESPs) connected to PostgreSQL Server 184. "
                        "Answer the user query accurately, concisely, and professionally. "
                        "If the user is asking a conversational or general question, respond helpfully and invite them to explore well diagnostics, fleet status, or equipment health."
                    ),
                },
                {"role": "user", "content": question},
            ])
            if llm_reply.get("content"):
                return AskResult(
                    answer=llm_reply["content"].strip(),
                    confidence=0.75,
                    citations=[],
                    warnings=[],
                    needs_clarification=False,
                    suggested_options=["Fleet Overview", "Well FNW-001 Health", "Well FS-017 History", "Diagnose Trip"],
                    is_mock=False,
                )
        except Exception as e:
            logger.warning(f"LLM fallback synthesis failed: {e}")

    return AskResult(
        answer="No directly relevant technical manual or telemetry record was found for this query in the ESP APM repository. Please verify the Well ID or rephrase with standard petroleum terminology.",
        confidence=0.3,
        citations=[],
        warnings=["No matching domain records found."],
        needs_clarification=True,
        clarification_question="What would you like to investigate?",
        suggested_options=["Fleet Overview", "Recent Trip Diagnostics", "Well FNW-001 Health", "Well FS-017 History"],
        is_mock=True,
    )



def _build_safety_warnings(question: str) -> list[str]:
    """Detect safety risks based on question content and return a warning list."""
    warnings: list[str] = []
    risk_keywords = {
        "electrical": "Electrical maintenance carries shock risks; ensure power is isolated and LOTO is applied.",
        "live": "Never work on live equipment! Cut power and apply Lockout/Tagout (LOTO) before maintenance.",
        "high voltage": "High voltage equipment maintenance has severe safety risks; must be performed by certified personnel.",
        "high temperature": "High temperature equipment poses burn risks; wait for cooldown and wear thermal PPE.",
        "hydraulic": "Hydraulic systems pose high-pressure fluid injection risks; release system pressure first.",
        "pneumatic": "Pneumatic systems have pressure release risks; purge airlines first.",
        "rotating": "Rotating machinery poses entanglement risks; ensure complete stoppage and lock.",
        "interlock": "Never bypass safety interlocks; this may cause catastrophic accidents.",
        "lockout": "Stop, de-energize, and lock out/tag out (LOTO) before servicing.",
        "tagout": "Stop, de-energize, and lock out/tag out (LOTO) before servicing.",
        "disassemble": "Confirm equipment is fully stopped and secured before disassembly.",
        "bypass": "Do not bypass any safety device or protection circuit; follow standard operating procedures.",
    }
    lower_q = question.lower()
    for kw, msg in risk_keywords.items():
        if (kw in question or kw in lower_q) and msg not in warnings:
            warnings.append(msg)
    return warnings


# ---------------- 6. Historical Work Order Summary ----------------


def history_summary(db: Session, equipment_id: int) -> HistorySummary:
    eq = db.get(Equipment, equipment_id)
    if not eq:
        return HistorySummary(
            equipment_id=equipment_id,
            equipment_name="",
            total_work_orders=0,
            is_mock=True,
        )
    wos = (
        db.query(WorkOrder)
        .filter(WorkOrder.equipment_id == equipment_id)
        .order_by(WorkOrder.created_at.desc())
        .all()
    )
    total = len(wos)
    # High-frequency faults
    fault_count: dict[str, int] = {}
    for w in wos:
        key = w.fault_description or w.title
        fault_count[key] = fault_count.get(key, 0) + 1
    frequent = [
        {"fault": k, "count": v}
        for k, v in sorted(fault_count.items(), key=lambda x: -x[1])[:5]
    ]
    recent = [
        {
            "code": w.code,
            "title": w.title,
            "status": w.status.value,
            "created_at": w.created_at.isoformat() if w.created_at else None,
        }
        for w in wos[:5]
    ]
    repeated = [{"fault": k, "count": v} for k, v in fault_count.items() if v >= 2][:3]
    # Common replaced parts
    parts: dict[str, int] = {}
    hours_list = []
    for w in wos:
        if w.replaced_parts:
            for p in re.split(r"[,;\n]+", w.replaced_parts):
                p = p.strip()
                if p:
                    parts[p] = parts.get(p, 0) + 1
        if w.actual_start_at and w.actual_end_at:
            delta = (w.actual_end_at - w.actual_start_at).total_seconds() / 3600
            if delta > 0:
                hours_list.append(delta)
    common_parts = [
        {"part": k, "count": v}
        for k, v in sorted(parts.items(), key=lambda x: -x[1])[:5]
    ]
    avg_hours = round(sum(hours_list) / len(hours_list), 1) if hours_list else None
    return HistorySummary(
        equipment_id=equipment_id,
        equipment_name=f"{eq.name}({eq.code})",
        total_work_orders=total,
        frequent_faults=frequent,
        recent_faults=recent,
        repeated_faults=repeated,
        common_parts=common_parts,
        avg_repair_hours=avg_hours,
        is_mock=True,
    )
