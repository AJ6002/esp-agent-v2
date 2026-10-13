"""Headless Query Router & Dispatcher for standalone Agent Service V2."""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.esp_diagnosis import (
    DiagnoseEventRequest,
    ESPIntentEnum,
    HybridRouteResult,
)
from app.services.esp_diagnosis_service import (
    compare_multiple_wells,
    diagnose_esp_event,
    get_fleet_alarm_timeline,
    get_fleet_anomaly_surfacing,
    get_fleet_executive_report,
    get_fleet_inventory_status,
    get_fleet_production_summary,
    get_fleet_triage_ranking,
    get_well_health_status,
    get_well_historical_analysis,
    get_well_production_metrics,
    route_query_hybrid,
    search_petroleum_kb,
)

from app.ai.client import llm_client

logger = logging.getLogger("agent.router")


def ask_agent(
    question: str,
    well_id: str | None = None,
    conversation_history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Execute query against deterministic physics tools & LLM synthesis.
    
    Returns:
        {
            "intent": str,
            "markdown_text": str,
            "structured_data": dict | None,
            "confidence": float,
            "needs_clarification": bool,
            "suggested_options": list[str],
        }
    """
    route: HybridRouteResult = route_query_hybrid(
        question, conversation_history=conversation_history
    )

    # 1. Clarification Needed
    if route.needs_clarification and not well_id:
        return {
            "intent": route.intent.value,
            "markdown_text": (
                f"### [ESP APM] Operational Clarification Required\n\n"
                f"{route.clarification_question or 'Please specify which well or event you want to inspect.'}\n\n"
                f"Suggested options: {', '.join(route.suggested_options)}"
            ),
            "structured_data": None,
            "confidence": route.confidence,
            "needs_clarification": True,
            "suggested_options": route.suggested_options,
        }

    # 2. Conversational Chit-Chat
    if route.intent == ESPIntentEnum.CHAT:
        msg = None
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
                msg = resp.get("content") if resp else None
            except Exception as e:
                logger.warning(f"Dynamic LLM chat synthesis failed: {e}")

        if not msg:
            msg = (
                "Hello! I am your **ESP APM Industrial Maintenance Copilot** connected to PostgreSQL `esp_apm_db` on Server 184.\n\n"
                "I can assist you with:\n"
                "- **Trip Event Diagnostics**: E.g. *'Why did well FNW-001 trip?'* or *'Diagnose event EV-20261012-103435-FNW-001-878'*\n"
                "- **Fleet Operational Status**: E.g. *'What is the current status of the fleet?'*\n"
                "- **Well Failure History**: E.g. *'Show history of well FS-017 in last 7 days'*\n"
                "- **Real-time Well Health**: E.g. *'Is well FNW-001 healthy?'*\n"
                "- **Multi-Well Comparison**: E.g. *'Compare well FS-017 vs FS-040'*\n"
                "- **Petroleum Engineering Standards**: E.g. *'What causes gas locking in an ESP?'*"
            )

        return {
            "intent": "CHAT",
            "markdown_text": msg,
            "structured_data": None,
            "confidence": 1.0,
            "needs_clarification": False,
            "suggested_options": ["Fleet Status", "Diagnose FNW-001", "Compare FS-017 vs FS-040", "FS-017 History"],
        }

    # 3. Trip Event Diagnosis
    if route.intent == ESPIntentEnum.EVENT_DIAGNOSE:
        ev_id = route.entity if (route.entity and route.entity.startswith("EV-")) else None
        target_well = route.entity if (route.entity and not route.entity.startswith("EV-")) else (well_id or "FNW-001")
        diag_res = diagnose_esp_event(DiagnoseEventRequest(event_id=ev_id, well_id=target_well))
        return {
            "intent": "EVENT_DIAGNOSE",
            "markdown_text": diag_res.markdown_report,
            "structured_data": diag_res.structured_data,
            "confidence": float(diag_res.mathematical_confidence_pct) / 100.0,
            "needs_clarification": False,
            "suggested_options": [f"Well {target_well} Health", f"Well {target_well} History", "Fleet Status"],
        }

    # 4. Fleet Inventory & Real-Time Status
    if route.intent == ESPIntentEnum.FLEET_INVENTORY:
        fleet_res = get_fleet_inventory_status(cluster=route.entity)
        return {
            "intent": "FLEET_INVENTORY",
            "markdown_text": fleet_res.markdown_report,
            "structured_data": {
                "total_wells": fleet_res.total_wells,
                "running_wells_count": fleet_res.running_wells_count,
                "tripped_wells_count": fleet_res.tripped_wells_count,
                "unmonitored_wells_count": fleet_res.unmonitored_wells_count,
                "running_wells": fleet_res.running_wells,
                "tripped_wells": fleet_res.tripped_wells,
            },
            "confidence": 0.98,
            "needs_clarification": False,
            "suggested_options": ["FNW-001 Health", "FS-017 History", "Cluster 15", "Cluster 4"],
        }

    # 4.1 Fleet Production & Deferment Summary (Domain 1.3)
    if route.intent == ESPIntentEnum.FLEET_PRODUCTION:
        prod_res = get_fleet_production_summary()
        return {
            "intent": "FLEET_PRODUCTION",
            "markdown_text": prod_res.markdown_report,
            "structured_data": prod_res.dict(),
            "confidence": 0.98,
            "needs_clarification": False,
            "suggested_options": ["Fleet Triage", "Executive Summary", "Fleet Anomalies", "Fleet Status"],
        }

    # 4.2 Fleet Triage & Priority Ranking (Domain 1.4)
    if route.intent == ESPIntentEnum.FLEET_TRIAGE:
        triage_res = get_fleet_triage_ranking()
        return {
            "intent": "FLEET_TRIAGE",
            "markdown_text": triage_res.markdown_report,
            "structured_data": triage_res.dict(),
            "confidence": 0.98,
            "needs_clarification": False,
            "suggested_options": ["Executive Summary", "Fleet Production", "Diagnose FNW-001", "Fleet Status"],
        }

    # 4.3 Fleet Executive Briefing & KPI Reporting (Domain 1.5)
    if route.intent == ESPIntentEnum.FLEET_EXECUTIVE:
        exec_res = get_fleet_executive_report()
        return {
            "intent": "FLEET_EXECUTIVE",
            "markdown_text": exec_res.markdown_report,
            "structured_data": exec_res.dict(),
            "confidence": 0.98,
            "needs_clarification": False,
            "suggested_options": ["Fleet Triage", "Fleet Production", "Fleet Anomalies", "Fleet Status"],
        }

    # 4.4 Fleet Anomaly Surfacing & Early Warning (Domain 1.6)
    if route.intent == ESPIntentEnum.FLEET_ANOMALY:
        anomaly_res = get_fleet_anomaly_surfacing()
        return {
            "intent": "FLEET_ANOMALY",
            "markdown_text": anomaly_res.markdown_report,
            "structured_data": anomaly_res.dict(),
            "confidence": 0.98,
            "needs_clarification": False,
            "suggested_options": ["Fleet Status", "Fleet Triage", "Executive Summary"],
        }

    # 4.5 Fleet Alarm Timeline & Incident Clustering (Domain 1.7)
    if route.intent == ESPIntentEnum.FLEET_TIMELINE:
        timeline_res = get_fleet_alarm_timeline()
        return {
            "intent": "FLEET_TIMELINE",
            "markdown_text": timeline_res.markdown_report,
            "structured_data": timeline_res.dict(),
            "confidence": 0.98,
            "needs_clarification": False,
            "suggested_options": ["Fleet Triage", "Executive Summary", "Fleet Status"],
        }

    # 5. Multi-Well Comparison
    if route.intent == ESPIntentEnum.MULTI_WELL_COMPARE:
        comp_report = compare_multiple_wells(route.entities)
        return {
            "intent": "MULTI_WELL_COMPARE",
            "markdown_text": comp_report,
            "structured_data": {"wells": route.entities},
            "confidence": 0.95,
            "needs_clarification": False,
            "suggested_options": [f"Diagnose {w}" for w in route.entities] + ["Fleet Status"],
        }

    # 6. Well Failure History
    if route.intent == ESPIntentEnum.WELL_HISTORY:
        target_well = route.entity or well_id or "FS-017"
        t_days = 7 if (route.time_filter_label and "7" in route.time_filter_label) else (30 if (route.time_filter_label and "30" in route.time_filter_label) else None)
        hist_res = get_well_historical_analysis(target_well, time_window_days=t_days, time_window_label=route.time_filter_label)
        return {
            "intent": "WELL_HISTORY",
            "markdown_text": hist_res["markdown_report"],
            "structured_data": hist_res,
            "confidence": 0.95,
            "needs_clarification": False,
            "suggested_options": [f"Check {target_well} Health", f"Diagnose {target_well} Trip", "Fleet Status"],
        }

    # 7. Well Health Assessment
    if route.intent == ESPIntentEnum.WELL_HEALTH:
        target_well = route.entity or well_id or "FNW-001"
        health_res = get_well_health_status(target_well)
        return {
            "intent": "WELL_HEALTH",
            "markdown_text": health_res.markdown_report,
            "structured_data": health_res.dict(),
            "confidence": 0.96,
            "needs_clarification": False,
            "suggested_options": [f"Diagnose {target_well}", f"History {target_well}", "Fleet Status"],
        }

    # 8. Production Telemetry
    if route.intent == ESPIntentEnum.PRODUCTION:
        target_well = route.entity or well_id or "FS-017"
        prod_res = get_well_production_metrics(target_well)
        return {
            "intent": "PRODUCTION",
            "markdown_text": prod_res.markdown_report,
            "structured_data": prod_res.dict(),
            "confidence": 0.95,
            "needs_clarification": False,
            "suggested_options": [f"Diagnose {target_well}", "Fleet Status"],
        }

    # 9. Petroleum Engineering Knowledge RAG
    chunks = search_petroleum_kb(question, limit=3)
    if chunks:
        context_body = "\n\n".join([f"**{c.doc_title}** ({c.section_title or 'Section'}):\n{c.content}" for c in chunks])
        kb_text = f"### [ESP Knowledge Standard & SOP]\n\n{context_body}"
    else:
        # Synthesize answer via LLM (Server 134) for natural conversational & technical queries
        if llm_client.enabled:
            try:
                llm_reply = llm_client.chat([
                    {
                        "role": "system",
                        "content": (
                            "You are an expert Petroleum Artificial Lift Engineer and Industrial Maintenance Copilot for Electric Submersible Pumps (ESPs). "
                            "Answer the user query accurately, concisely, and professionally. "
                            "If the user is asking a conversational greeting or general query, respond helpfully and invite them to explore well diagnostics or fleet status."
                        ),
                    },
                    {"role": "user", "content": question},
                ])
                kb_text = llm_reply.get("content") or "Hello! I am your ESP APM Maintenance Copilot. You can ask me to diagnose well trip events, check fleet inventory, or inspect well health baselines."
            except Exception:
                kb_text = "Hello! I am your ESP APM Maintenance Copilot. You can ask me to diagnose well trip events, check fleet inventory, or inspect well health baselines."
        else:
            kb_text = "Hello! I am your ESP APM Maintenance Copilot. You can ask me to diagnose well trip events, check fleet inventory, or inspect well health baselines."

    return {
        "intent": "KNOWLEDGE",
        "markdown_text": kb_text,
        "structured_data": {"chunks_count": len(chunks)},
        "confidence": 0.90,
        "needs_clarification": False,
        "suggested_options": ["Fleet Status", "Diagnose FNW-001", "Check FS-017 Health", "Compare FS-017 vs FS-040"],
    }
