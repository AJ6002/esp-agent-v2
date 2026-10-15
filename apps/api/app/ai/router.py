"""Headless Query Router & Dispatcher for standalone Agent Service V2."""

from __future__ import annotations

import logging
import re
from typing import Any

from app.core.session import session_manager
from app.schemas.esp_diagnosis import (
    DiagnoseEventRequest,
    ESPIntentEnum,
    HybridRouteResult,
)
from app.services.esp_diagnosis_service import (
    compare_multiple_wells,
    compare_gathering_clusters,
    compare_well_historical,
    benchmark_well_against_peers,
    compare_event_before_after,
    rank_fleet_by_metric,
    diagnose_esp_event,
    diagnose_running_well_degradation,
    get_fleet_alarm_timeline,
    get_fleet_anomaly_surfacing,
    get_fleet_executive_report,
    get_fleet_inventory_status,
    get_fleet_production_summary,
    get_fleet_triage_ranking,
    get_self_identity,
    get_self_capabilities,
    get_self_boundaries,
    get_self_fleet_scope,
    get_self_tasks,
    get_self_limitations,
    get_ui_navigation_narrative,
    get_well_health_status,
    get_well_historical_analysis,
    get_well_production_metrics,
    route_query_hybrid,
    search_petroleum_kb,
    get_evidence_inquiry_report,
    get_follow_up_justification_report,
    get_graph_explanation_report,
    get_well_subsystem_reframe_report,
    check_well_is_running_nominally,
    check_well_telemetry_readiness,
    get_false_premise_refusal_report,
    get_data_readiness_refusal_report,
    get_unknown_asset_refusal_report,
    get_out_of_scope_refusal_report,
    get_well_recent_events,
    VALID_FLEET_WELLS,
)

from app.ai.client import llm_client

logger = logging.getLogger("agent.router")


def ask_agent(
    question: str,
    well_id: str | None = None,
    conversation_history: list[dict[str, Any]] | None = None,
    session_id: str | None = None,
    page_route: str | None = None,
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
            "session_id": str,
            "routing_tier": str,
        }
    """
    session, _ = session_manager.get_or_create(session_id)
    if page_route:
        session.active_page_route = page_route

    route: HybridRouteResult = route_query_hybrid(
        question,
        conversation_history=conversation_history,
        session_id=session.session_id,
        page_route=page_route or session.active_page_route,
    )

    if route.deferred_intent:
        session_manager.queue_deferred_intent(
            session.session_id,
            query=route.deferred_intent["query"],
        )

    def finalize_response(resp: dict[str, Any]) -> dict[str, Any]:
        resp["session_id"] = session.session_id
        resp["routing_tier"] = route.routing_tier
        next_deferred = session_manager.peek_deferred_intent(session.session_id)
        if next_deferred:
            chip = f"[Continue: {next_deferred['query']}]"
            suggested = resp.get("suggested_options") or []
            if chip not in suggested:
                resp["suggested_options"] = [chip] + suggested
            if "Queued Follow-Up" not in resp.get("markdown_text", ""):
                resp["markdown_text"] = (
                    resp.get("markdown_text", "")
                    + f"\n\n---\n> **Queued Follow-Up**: *'{next_deferred['query']}'* is queued in session memory. "
                    f"Click **[Continue: {next_deferred['query']}]** or type `continue` to execute next."
                )
        return resp

    # 1. Clarification Needed
    if route.needs_clarification and not well_id:
        return finalize_response({
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
        })

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

        return finalize_response({
            "intent": "CHAT",
            "markdown_text": msg,
            "structured_data": None,
            "confidence": 1.0,
            "needs_clarification": False,
            "suggested_options": ["Fleet Status", "Diagnose FNW-001", "Compare FS-017 vs FS-040", "FS-017 History"],
        })

    # Domain 11.2: Evidence Inquiry ("What data did you use?")
    if route.intent == ESPIntentEnum.EVIDENCE_INQUIRY:
        ev_res = get_evidence_inquiry_report(session.session_id)
        return finalize_response({
            "intent": "EVIDENCE_INQUIRY",
            "markdown_text": ev_res["markdown_report"],
            "structured_data": ev_res["structured_data"],
            "confidence": 0.99,
            "needs_clarification": False,
            "suggested_options": ev_res["suggested_options"],
        })

    # Domain 11.1: Follow-up on Prior Answer ("Why did you say X?")
    if route.intent == ESPIntentEnum.FOLLOW_UP_JUSTIFY:
        just_res = get_follow_up_justification_report(session.session_id, question)
        return finalize_response({
            "intent": "FOLLOW_UP_JUSTIFY",
            "markdown_text": just_res["markdown_report"],
            "structured_data": just_res["structured_data"],
            "confidence": 0.98,
            "needs_clarification": False,
            "suggested_options": just_res["suggested_options"],
        })

    # Domain 11.3: Graph Explanation ("What does that chart mean?")
    if route.intent == ESPIntentEnum.GRAPH_EXPLAIN:
        graph_res = get_graph_explanation_report(page_route=page_route or session.active_page_route, question=question)
        return finalize_response({
            "intent": "GRAPH_EXPLAIN",
            "markdown_text": graph_res["markdown_report"],
            "structured_data": graph_res["structured_data"],
            "confidence": 0.98,
            "needs_clarification": graph_res.get("needs_clarification", False),
            "suggested_options": graph_res.get("suggested_options", []),
        })

    # Domain 12.4: Out-of-Scope Query Refusal
    if route.intent == ESPIntentEnum.SAFETY_REFUSAL_OUT_OF_SCOPE:
        scope_res = get_out_of_scope_refusal_report(question)
        return finalize_response({
            "intent": "SAFETY_REFUSAL_OUT_OF_SCOPE",
            "markdown_text": scope_res["markdown_report"],
            "structured_data": scope_res["structured_data"],
            "confidence": 0.99,
            "needs_clarification": False,
            "suggested_options": scope_res["suggested_options"],
        })

    # Domain 12.5: Unknown Asset Refusal & Fuzzy Disambiguation
    if route.intent == ESPIntentEnum.SAFETY_REFUSAL_UNKNOWN_ASSET:
        asset_res = get_unknown_asset_refusal_report(route.entity or question)
        return finalize_response({
            "intent": "SAFETY_REFUSAL_UNKNOWN_ASSET",
            "markdown_text": asset_res["markdown_report"],
            "structured_data": asset_res["structured_data"],
            "confidence": route.confidence,
            "needs_clarification": route.needs_clarification,
            "suggested_options": route.suggested_options or asset_res["suggested_options"],
        })

    # Domain 12.2: Insufficient Evidence Refusal
    if route.intent == ESPIntentEnum.SAFETY_REFUSAL_INSUFFICIENT_EVIDENCE:
        evidence_res = get_data_readiness_refusal_report(route.entity or "FNW-001", "Missing live sensor channels")
        return finalize_response({
            "intent": "SAFETY_REFUSAL_INSUFFICIENT_EVIDENCE",
            "markdown_text": evidence_res["markdown_report"],
            "structured_data": evidence_res["structured_data"],
            "confidence": 0.99,
            "needs_clarification": False,
            "suggested_options": evidence_res["suggested_options"],
        })

    # 3. Trip Event Diagnosis
    if route.intent == ESPIntentEnum.EVENT_DIAGNOSE:
        ev_id = route.entity if (route.entity and route.entity.startswith("EV-")) else None
        target_well = route.entity if (route.entity and not route.entity.startswith("EV-")) else (well_id or "FNW-001")

        # Domain 4 / 12.1: False-Premise Refusal vs Live Running Well Degradation Diagnosis
        if not ev_id and target_well:
            is_running, snapshot = check_well_is_running_nominally(target_well)
            q_lower = question.lower()
            is_trip_query = any(w in q_lower for w in ["trip", "shutdown", "stopped", "failed", "offline", "cause of trip", "why did it stop"])
            is_anomaly_or_health_query = any(w in q_lower for w in [
                "declin", "drop", "drift", "anomaly", "health", "early warning", 
                "about to fail", "vibrat", "reconcil", "wear", "overload", "status", "degrad"
            ])

            # If user asks why it tripped/stopped, but it's currently RUNNING nominally -> False-Premise Refusal
            if is_running and is_trip_query and not is_anomaly_or_health_query:
                fp_res = get_false_premise_refusal_report(target_well, snapshot)
                return finalize_response({
                    "intent": "SAFETY_REFUSAL_FALSE_PREMISE",
                    "markdown_text": fp_res["markdown_report"],
                    "structured_data": fp_res["structured_data"],
                    "confidence": 0.99,
                    "needs_clarification": False,
                    "suggested_options": fp_res["suggested_options"],
                })

            # If well is running and the user wants a diagnosis or anomaly analysis (not a trip) -> Mode B (Live Running Degradation)
            if is_running and (is_anomaly_or_health_query or "diagnos" in q_lower):
                diag_res = diagnose_running_well_degradation(target_well, query=question)
                session_manager.record_execution(
                    session_id=session.session_id,
                    intent="EVENT_DIAGNOSE",
                    entity=target_well,
                    event_id=diag_res.event_id,
                    evidence=diag_res.structured_data,
                    diagnosis=diag_res.structured_data,
                    markdown_report=diag_res.markdown_report,
                    page_route=page_route or session.active_page_route,
                )
                return finalize_response({
                    "intent": "EVENT_DIAGNOSE",
                    "markdown_text": diag_res.markdown_report,
                    "structured_data": diag_res.structured_data,
                    "confidence": float(diag_res.mathematical_confidence_pct) / 100.0,
                    "needs_clarification": False,
                    "suggested_options": [
                        f"Well {target_well} Equalizer",
                        f"Open Well View (/well-view/{target_well})",
                        f"Dispatch Inspection Work Order for {target_well}",
                        "What data did you use?",
                        "What are the next diagnostic steps?",
                    ],
                })

        # Domain 12.2: Insufficient Evidence Check via Data Readiness Gate
        if target_well and not ev_id:
            is_ready, gate_reason = check_well_telemetry_readiness(target_well)
            if not is_ready:
                dr_res = get_data_readiness_refusal_report(target_well, gate_reason)
                return finalize_response({
                    "intent": "SAFETY_REFUSAL_INSUFFICIENT_EVIDENCE",
                    "markdown_text": dr_res["markdown_report"],
                    "structured_data": dr_res["structured_data"],
                    "confidence": 0.99,
                    "needs_clarification": False,
                    "suggested_options": dr_res["suggested_options"],
                })

        # Domain 3: Multi-Event Disambiguation (if multiple historical events exist and no specific event specified)
        if target_well and not ev_id:
            is_explicit_latest = any(w in question.lower() for w in ["latest", "most recent", "last trip", "current trip", "newest", "diagnose latest", "diagnose well", "diagnose "])
            recent_events = get_well_recent_events(target_well, limit=5)
            if len(recent_events) > 1 and not is_explicit_latest:
                options = []
                for idx, ev in enumerate(recent_events[:3]):
                    ts_label = ev["timestamp"].strftime("%Y-%m-%d %H:%M UTC") if hasattr(ev["timestamp"], "strftime") else str(ev["timestamp"])
                    prefix = "(Recommended) " if idx == 0 else ""
                    options.append(f"{prefix}Diagnose {ev['event_id']} ({ts_label} - {ev['trip_cause']})")
                options.append(f"Show Reliability History for {target_well}")

                clarification_md = (
                    f"### [ESP APM] Multiple Trip Incidents Detected: `{target_well}`\n\n"
                    f"Well `{target_well}` has **{len(recent_events)}** recorded trip incidents in the operational event store. "
                    f"Please select which incident you would like to analyze:\n\n"
                    + "\n".join([f"- **{opt}**" for opt in options])
                    + f"\n\n*Tip: Click an option chip below or type `latest` to diagnose the most recent event.*"
                )
                session_manager.record_execution(
                    session_id=session.session_id,
                    intent="EVENT_DIAGNOSE",
                    entity=target_well,
                    markdown_report=clarification_md,
                    page_route=page_route or session.active_page_route,
                )
                return finalize_response({
                    "intent": "EVENT_DIAGNOSE",
                    "markdown_text": clarification_md,
                    "structured_data": {
                        "well_id": target_well,
                        "available_events": [
                            {
                                "event_id": e["event_id"],
                                "timestamp": e["timestamp"].isoformat() if hasattr(e["timestamp"], "isoformat") else str(e["timestamp"]),
                                "trip_cause": e["trip_cause"],
                                "severity": e["severity"],
                            }
                            for e in recent_events
                        ],
                        "needs_clarification": True,
                    },
                    "confidence": 0.85,
                    "needs_clarification": True,
                    "suggested_options": options,
                })

        diag_res = diagnose_esp_event(DiagnoseEventRequest(event_id=ev_id, well_id=target_well))

        # Record execution snapshot in session
        session_manager.record_execution(
            session_id=session.session_id,
            intent="EVENT_DIAGNOSE",
            entity=target_well,
            event_id=ev_id or diag_res.event_id,
            evidence=diag_res.structured_data,
            diagnosis=diag_res.structured_data,
            markdown_report=diag_res.markdown_report,
            page_route=page_route or session.active_page_route,
        )

        effective_event_id = ev_id or diag_res.event_id
        return finalize_response({
            "intent": "EVENT_DIAGNOSE",
            "markdown_text": diag_res.markdown_report,
            "structured_data": diag_res.structured_data,
            "confidence": float(diag_res.mathematical_confidence_pct) / 100.0,
            "needs_clarification": False,
            "suggested_options": [
                f"Open Forensics Workspace (/events/{effective_event_id})",
                f"Dispatch Work Order for {target_well}",
                f"Well {target_well} Equalizer",
                "What data did you use?",
                "Why was it diagnosed?",
            ],
        })

    # 4. Fleet Inventory & Real-Time Status
    if route.intent == ESPIntentEnum.FLEET_INVENTORY:
        fleet_res = get_fleet_inventory_status(cluster=route.entity)
        session_manager.record_execution(
            session_id=session.session_id,
            intent="FLEET_INVENTORY",
            entity=route.entity,
            page_route=page_route or session.active_page_route,
        )
        return finalize_response({
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
        })

    # 4.1 Fleet Production & Deferment Summary (Domain 1.3)
    if route.intent == ESPIntentEnum.FLEET_PRODUCTION:
        prod_res = get_fleet_production_summary()
        session_manager.record_execution(
            session_id=session.session_id,
            intent="FLEET_PRODUCTION",
            page_route=page_route or session.active_page_route,
        )
        return finalize_response({
            "intent": "FLEET_PRODUCTION",
            "markdown_text": prod_res.markdown_report,
            "structured_data": prod_res.dict(),
            "confidence": 0.98,
            "needs_clarification": False,
            "suggested_options": ["Fleet Triage", "Executive Summary", "Fleet Anomalies", "Fleet Status"],
        })

    # 4.2 Fleet Triage & Priority Ranking (Domain 1.4)
    if route.intent == ESPIntentEnum.FLEET_TRIAGE:
        triage_res = get_fleet_triage_ranking()
        session_manager.record_execution(
            session_id=session.session_id,
            intent="FLEET_TRIAGE",
            page_route=page_route or session.active_page_route,
        )
        return finalize_response({
            "intent": "FLEET_TRIAGE",
            "markdown_text": triage_res.markdown_report,
            "structured_data": triage_res.dict(),
            "confidence": 0.98,
            "needs_clarification": False,
            "suggested_options": ["Executive Summary", "Fleet Production", "Diagnose FNW-001", "Fleet Status"],
        })

    # 4.3 Fleet Executive Briefing & KPI Reporting (Domain 1.5)
    if route.intent == ESPIntentEnum.FLEET_EXECUTIVE:
        exec_res = get_fleet_executive_report()
        session_manager.record_execution(
            session_id=session.session_id,
            intent="FLEET_EXECUTIVE",
            page_route=page_route or session.active_page_route,
        )
        return finalize_response({
            "intent": "FLEET_EXECUTIVE",
            "markdown_text": exec_res.markdown_report,
            "structured_data": exec_res.dict(),
            "confidence": 0.98,
            "needs_clarification": False,
            "suggested_options": ["Fleet Triage", "Fleet Production", "Fleet Anomalies", "Fleet Status"],
        })

    # 4.4 Fleet Anomaly Surfacing & Early Warning (Domain 1.6)
    if route.intent == ESPIntentEnum.FLEET_ANOMALY:
        anomaly_res = get_fleet_anomaly_surfacing()
        session_manager.record_execution(
            session_id=session.session_id,
            intent="FLEET_ANOMALY",
            page_route=page_route or session.active_page_route,
        )
        return finalize_response({
            "intent": "FLEET_ANOMALY",
            "markdown_text": anomaly_res.markdown_report,
            "structured_data": anomaly_res.dict(),
            "confidence": 0.98,
            "needs_clarification": False,
            "suggested_options": ["Fleet Status", "Fleet Triage", "Executive Summary"],
        })

    # 4.5 Fleet Alarm Timeline & Incident Clustering (Domain 1.7)
    if route.intent == ESPIntentEnum.FLEET_TIMELINE:
        timeline_res = get_fleet_alarm_timeline()
        session_manager.record_execution(
            session_id=session.session_id,
            intent="FLEET_TIMELINE",
            page_route=page_route or session.active_page_route,
        )
        return finalize_response({
            "intent": "FLEET_TIMELINE",
            "markdown_text": timeline_res.markdown_report,
            "structured_data": timeline_res.dict(),
            "confidence": 0.98,
            "needs_clarification": False,
            "suggested_options": ["Fleet Triage", "Executive Summary", "Fleet Status"],
        })

    # 5. Multi-Well Comparison
    if route.intent == ESPIntentEnum.MULTI_WELL_COMPARE:
        comp_report = compare_multiple_wells(route.entities)
        session_manager.record_execution(
            session_id=session.session_id,
            intent="MULTI_WELL_COMPARE",
            entities=route.entities,
            entity=route.entities[0] if route.entities else None,
            markdown_report=comp_report,
            page_route=page_route or session.active_page_route,
        )
        return finalize_response({
            "intent": "MULTI_WELL_COMPARE",
            "markdown_text": comp_report,
            "structured_data": {"wells": route.entities},
            "confidence": 0.95,
            "needs_clarification": False,
            "suggested_options": [f"Diagnose {w}" for w in route.entities] + ["Fleet Status"],
        })

    # 6. Well Failure History
    if route.intent == ESPIntentEnum.WELL_HISTORY:
        target_well = route.entity or well_id or "FS-017"
        t_days = 7 if (route.time_filter_label and "7" in route.time_filter_label) else (30 if (route.time_filter_label and "30" in route.time_filter_label) else None)
        hist_res = get_well_historical_analysis(target_well, time_window_days=t_days, time_window_label=route.time_filter_label)
        session_manager.record_execution(
            session_id=session.session_id,
            intent="WELL_HISTORY",
            entity=target_well,
            evidence=hist_res,
            markdown_report=hist_res["markdown_report"],
            page_route=page_route or session.active_page_route,
        )
        return finalize_response({
            "intent": "WELL_HISTORY",
            "markdown_text": hist_res["markdown_report"],
            "structured_data": hist_res,
            "confidence": 0.95,
            "needs_clarification": False,
            "suggested_options": [f"Check {target_well} Health", f"Diagnose {target_well} Trip", "Fleet Status"],
        })

    # 7. Well Health Assessment & Reframing Subsystems
    if route.intent == ESPIntentEnum.WELL_HEALTH:
        target_well = route.entity or well_id or "FNW-001"
        is_reframe = any(p in question.lower() for p in ["what about", "how about", "check", "tell me about", "what is the"]) and any(
            s in question.lower() for s in ["temp", "thermal", "heat", "vib", "shake", "current", "amp", "pip", "pressure", "flow"]
        )
        if is_reframe:
            reframe_res = get_well_subsystem_reframe_report(target_well, question)
            session_manager.record_execution(
                session_id=session.session_id,
                intent="WELL_HEALTH",
                entity=target_well,
                evidence=reframe_res["structured_data"],
                markdown_report=reframe_res["markdown_report"],
                page_route=page_route or session.active_page_route,
            )
            return finalize_response({
                "intent": "WELL_HEALTH",
                "markdown_text": reframe_res["markdown_report"],
                "structured_data": reframe_res["structured_data"],
                "confidence": 0.96,
                "needs_clarification": False,
                "suggested_options": reframe_res["suggested_options"],
            })

        health_res = get_well_health_status(target_well)
        session_manager.record_execution(
            session_id=session.session_id,
            intent="WELL_HEALTH",
            entity=target_well,
            evidence=health_res.dict(),
            markdown_report=health_res.markdown_report,
            page_route=page_route or session.active_page_route,
        )
        return finalize_response({
            "intent": "WELL_HEALTH",
            "markdown_text": health_res.markdown_report,
            "structured_data": health_res.dict(),
            "confidence": 0.96,
            "needs_clarification": False,
            "suggested_options": [f"Diagnose {target_well}", f"History {target_well}", "What about temperature?", "Fleet Status"],
        })

    # 8. Production Telemetry
    if route.intent == ESPIntentEnum.PRODUCTION:
        target_well = route.entity or well_id or "FS-017"
        prod_res = get_well_production_metrics(target_well)
        session_manager.record_execution(
            session_id=session.session_id,
            intent="PRODUCTION",
            entity=target_well,
            evidence=prod_res.dict(),
            markdown_report=prod_res.markdown_report,
            page_route=page_route or session.active_page_route,
        )
        return finalize_response({
            "intent": "PRODUCTION",
            "markdown_text": prod_res.markdown_report,
            "structured_data": prod_res.dict(),
            "confidence": 0.95,
            "needs_clarification": False,
            "suggested_options": [f"Diagnose {target_well}", "Fleet Status"],
        })

    # 8.1 Gathering Cluster Comparison (Domain 2)
    if route.intent == ESPIntentEnum.CLUSTER_COMPARE:
        c1 = route.entities[0] if len(route.entities) > 0 else "15"
        c2 = route.entities[1] if len(route.entities) > 1 else "4"
        comp_res = compare_gathering_clusters(c1, c2)
        session_manager.record_execution(
            session_id=session.session_id,
            intent="CLUSTER_COMPARE",
            entities=route.entities,
            evidence=comp_res.dict(),
            markdown_report=comp_res.markdown_report,
            page_route=page_route or session.active_page_route,
        )
        return finalize_response({
            "intent": "CLUSTER_COMPARE",
            "markdown_text": comp_res.markdown_report,
            "structured_data": comp_res.dict(),
            "confidence": 0.98,
            "needs_clarification": False,
            "suggested_options": ["Compare Cluster 15 vs Cluster 3", "Show total fleet production", "Fleet Status"],
        })

    # 8.2 Historical Baseline Comparison (Domain 2)
    if route.intent == ESPIntentEnum.HISTORICAL_COMPARE:
        target_well = route.entity or well_id or "FS-004"
        b_res = compare_well_historical(target_well)
        session_manager.record_execution(
            session_id=session.session_id,
            intent="HISTORICAL_COMPARE",
            entity=target_well,
            evidence=b_res.dict(),
            markdown_report=b_res.markdown_report,
            page_route=page_route or session.active_page_route,
        )
        return finalize_response({
            "intent": "HISTORICAL_COMPARE",
            "markdown_text": b_res.markdown_report,
            "structured_data": b_res.dict(),
            "confidence": 0.98,
            "needs_clarification": False,
            "suggested_options": [f"Diagnose {target_well}", f"Benchmark {target_well} vs peers", "Fleet Status"],
        })

    # 8.3 Cluster Peer Benchmarking (Domain 2)
    if route.intent == ESPIntentEnum.PEER_BENCHMARK:
        target_well = route.entity or well_id or "FS-017"
        peer_res = benchmark_well_against_peers(target_well)
        session_manager.record_execution(
            session_id=session.session_id,
            intent="PEER_BENCHMARK",
            entity=target_well,
            evidence=peer_res.dict(),
            markdown_report=peer_res.markdown_report,
            page_route=page_route or session.active_page_route,
        )
        return finalize_response({
            "intent": "PEER_BENCHMARK",
            "markdown_text": peer_res.markdown_report,
            "structured_data": peer_res.dict(),
            "confidence": 0.98,
            "needs_clarification": False,
            "suggested_options": [f"Diagnose {target_well}", f"Show baseline for {target_well}", "Rank wells by vibration"],
        })

    # 8.4 Event Telemetry Comparison (Domain 2)
    if route.intent == ESPIntentEnum.EVENT_BEFORE_AFTER:
        ev_id = route.entity or "EV-20261012-101438-FS-017-571"
        ev_res = compare_event_before_after(ev_id)
        session_manager.record_execution(
            session_id=session.session_id,
            intent="EVENT_BEFORE_AFTER",
            entity=ev_id,
            evidence=ev_res.dict(),
            markdown_report=ev_res.markdown_report,
            page_route=page_route or session.active_page_route,
        )
        return finalize_response({
            "intent": "EVENT_BEFORE_AFTER",
            "markdown_text": ev_res.markdown_report,
            "structured_data": ev_res.dict(),
            "confidence": 0.98,
            "needs_clarification": False,
            "suggested_options": [f"Diagnose event {ev_id}", "Fleet Status"],
        })

    # 8.5 Fleet Leaderboards & Metric Ranking (Domain 2)
    if route.intent == ESPIntentEnum.FLEET_RANKING:
        metric = route.entity or "vibration"
        rank_res = rank_fleet_by_metric(metric)
        session_manager.record_execution(
            session_id=session.session_id,
            intent="FLEET_RANKING",
            entity=metric,
            page_route=page_route or session.active_page_route,
        )
        return finalize_response({
            "intent": "FLEET_RANKING",
            "markdown_text": rank_res.markdown_report,
            "structured_data": rank_res.dict(),
            "confidence": 0.98,
            "needs_clarification": False,
            "suggested_options": ["Rank wells by water cut", "Rank wells by motor current", "Fleet Triage"],
        })

    # 8.6 Domain 10: Self-Knowledge & Identity Dispatches
    if route.intent == ESPIntentEnum.SELF_IDENTITY:
        id_res = get_self_identity()
        return finalize_response({
            "intent": "SELF_IDENTITY",
            "markdown_text": id_res.markdown_report,
            "structured_data": id_res.dict(),
            "confidence": 1.0,
            "needs_clarification": False,
            "suggested_options": ["What can you do?", "What can't you do?", "Which wells do you know about?"],
        })

    if route.intent == ESPIntentEnum.SELF_CAPABILITIES:
        cap_res = get_self_capabilities()
        return finalize_response({
            "intent": "SELF_CAPABILITIES",
            "markdown_text": cap_res.markdown_report,
            "structured_data": cap_res.dict(),
            "confidence": 1.0,
            "needs_clarification": False,
            "suggested_options": ["Show fleet inventory", "Compare Cluster 15 vs Cluster 4", "What can't you do?"],
        })

    if route.intent == ESPIntentEnum.SELF_BOUNDARIES:
        bnd_res = get_self_boundaries()
        return finalize_response({
            "intent": "SELF_BOUNDARIES",
            "markdown_text": bnd_res.markdown_report,
            "structured_data": bnd_res.dict(),
            "confidence": 1.0,
            "needs_clarification": False,
            "suggested_options": ["What can you do?", "What are your limitations?", "Which wells do you know about?"],
        })

    if route.intent == ESPIntentEnum.SELF_FLEET_SCOPE:
        scope_res = get_self_fleet_scope()
        return finalize_response({
            "intent": "SELF_FLEET_SCOPE",
            "markdown_text": scope_res.markdown_report,
            "structured_data": scope_res.dict(),
            "confidence": 1.0,
            "needs_clarification": False,
            "suggested_options": ["Show total fleet production", "Fleet triage ranking", "Compare Cluster 15 vs Cluster 4"],
        })

    if route.intent == ESPIntentEnum.SELF_TASKS:
        tasks_res = get_self_tasks()
        return finalize_response({
            "intent": "SELF_TASKS",
            "markdown_text": tasks_res.markdown_report,
            "structured_data": tasks_res.dict(),
            "confidence": 1.0,
            "needs_clarification": False,
            "suggested_options": ["Executive morning briefing", "Fleet triage ranking", "What can't you do?"],
        })

    if route.intent == ESPIntentEnum.SELF_LIMITATIONS:
        lim_res = get_self_limitations()
        return finalize_response({
            "intent": "SELF_LIMITATIONS",
            "markdown_text": lim_res.markdown_report,
            "structured_data": lim_res.dict(),
            "confidence": 1.0,
            "needs_clarification": False,
            "suggested_options": ["What can you do?", "What are your boundaries?", "Which wells do you know about?"],
        })

    # 3.9 UI Navigation & Platform Route Intelligence (Domain 9)
    if route.intent == ESPIntentEnum.UI_NAVIGATION:
        ev_match = re.search(r"(EV-[\w\-]+)", question, re.IGNORECASE)
        event_id = ev_match.group(1) if ev_match else None
        nav_res = get_ui_navigation_narrative(question, entity=route.entity, event_id=event_id)
        return finalize_response({
            "intent": "UI_NAVIGATION",
            "markdown_text": nav_res.markdown_report,
            "structured_data": nav_res.dict(),
            "confidence": 0.99,
            "needs_clarification": False,
            "suggested_options": nav_res.suggested_options,
        })

    # 3.10 Work Order Dispatch & Autonomous Safety Preparation
    if route.intent == ESPIntentEnum.WORK_ORDER_DISPATCH:
        target_well = route.entity or well_id or "FNW-001"
        esp_res = diagnose_esp_event(DiagnoseEventRequest(well_id=target_well))
        p_fault = esp_res.structured_data.get("signature", {}).get("fault_name") or esp_res.trip_cause or "ESP Shutdown"
        ev_id = esp_res.event_id
        wo_code = f"WO-ESP-{target_well}-AUTO"

        loto_checklist = [
            "[CRITICAL] MANDATORY LOTO: De-energize and Lockout/Tagout VSD surface switchboard and main feeder.",
            "[CRITICAL] ZERO-ENERGY VERIFICATION: Test all incoming and motor leads with 1000V calibrated multimeter.",
            "[CRITICAL] HYDRAULIC ISOLATION: Close wing valve, master valve, and dissipate wellhead flowline trapped pressure.",
            "[DIAGNOSIS] VSD FAULT LOG AUDIT: Extract VSD memory fault codes and trip event logs for target well.",
            "[ELECTRICAL] ELECTRICAL MEGGER TEST: Measure Phase-to-Phase and Phase-to-Ground resistance (min 10 MΩ).",
            "[MECHANICAL] MECHANICAL FREE ROTATION: Rotate shaft with drive turning tool; verify zero drag or impeller seizure.",
            "[OPERATIONS] WELLHEAD INTEGRITY: Inspect surface sand desander trap and measure BS&W solids cut.",
            "[SAFETY SIGN-OFF] PRE-RESTART APPROVAL: Review echometer fluid level and obtain Petroleum Production Engineer sign-off."
        ]

        md = (
            f"# [ESP APM] Autonomous Work Order Dispatch\n\n"
            f"**Work Order Code**: `{wo_code}` | **Priority**: `P1 - CRITICAL` | **Status**: `STAGED_PENDING_APPROVAL`\n\n"
            f"### Target Asset\n"
            f"- **Well Identifier**: `{target_well}`\n"
            f"- **Associated Event**: `{ev_id}`\n"
            f"- **Diagnosed Root Cause**: `{p_fault}`\n\n"
            f"### 🛡️ Human Approval Gating (Phase 6 Write Path)\n"
            f"- **Gated Action**: Physical Dispatch & LOTO Execution\n"
            f"- **Approval State**: 🟡 `STAGED_PENDING_APPROVAL` (Zero autonomous field write)\n"
            f"- **Required Sign-Off**: Petroleum Production Engineer & Electrical Maintenance Supervisor\n\n"
            f"### ⚠️ Mandatory Lockout/Tagout (LOTO) Safety Protocol\n"
            + "\n".join([f"- {item}" for item in loto_checklist]) + "\n\n"
            f"### Acceptance & Sign-off Criteria\n"
            f"1. Verified zero-energy state via multimeter test.\n"
            f"2. Motor insulation resistance > 10 MΩ via 1000V Megger.\n"
            f"3. Free manual drive rotation with turning tool.\n"
            f"4. Petroleum Production Engineer and Electrical Supervisor signed approval.\n\n"
            f"---\n"
            f"> *Safety Notice: Work order is staged in read-only advisory decision-support mode. Physical dispatch requires field engineer authorization.*\n"
        )

        return finalize_response({
            "intent": "WORK_ORDER_DISPATCH",
            "markdown_text": md,
            "structured_data": {
                "work_order_code": wo_code,
                "priority": "P1",
                "well_id": target_well,
                "event_id": ev_id,
                "diagnosed_fault": p_fault,
                "loto_checklist": loto_checklist,
                "approval_status": "STAGED_PENDING_APPROVAL",
                "requires_human_signoff": True,
                "authorized_roles": ["PETROLEUM_PRODUCTION_ENGINEER", "ELECTRICAL_MAINTENANCE_SUPERVISOR"],
                "action_type": "PHYSICAL_FIELD_DISPATCH",
                "is_advisory_only": True,
            },
            "confidence": 0.99,
            "needs_clarification": False,
            "suggested_options": [f"Diagnose {target_well}", f"Check {target_well} Health", "Fleet Status"],
        })

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

    return finalize_response({
        "intent": "KNOWLEDGE",
        "markdown_text": kb_text,
        "structured_data": {"chunks_count": len(chunks)},
        "confidence": 0.90,
        "needs_clarification": False,
        "suggested_options": ["Fleet Status", "Diagnose FNW-001", "Check FS-017 Health", "Compare FS-017 vs FS-040"],
    })
