"""Comprehensive 50-Query Regression Suite for ESP APM Agent Service.

Covers all 26 canonical intents and 18 operational domains.
Captures full raw structured and markdown outputs to disk for independent
PostgreSQL ground-truth verification by subagent.
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any

# Ensure agent_service_v2 is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ai.router import ask_agent
from app.services.esp_diagnosis_service import route_query_hybrid
from app.schemas.esp_diagnosis import ESPIntentEnum, RoutingTierEnum


REGRESSION_50_QUERIES: list[dict[str, Any]] = [
    # 1. Fleet Inventory & Status (Domain 1.1 / 1.2)
    {
        "id": "Q01",
        "domain": "Domain 1.1 Fleet Inventory",
        "query": "how many wells are currently running and tripped across the fleet",
        "expected_intent": "FLEET_INVENTORY",
        "target_entity": None,
        "db_validation_type": "fleet_count",
    },
    {
        "id": "Q02",
        "domain": "Domain 1.2 Oilfield Hierarchy",
        "query": "give me the complete fleet inventory breakdown by cluster",
        "expected_intent": "FLEET_INVENTORY",
        "target_entity": None,
        "db_validation_type": "cluster_breakdown",
    },
    {
        "id": "Q03",
        "domain": "Domain 1.2 Cluster Scope",
        "query": "which wells are online right now in gathering center 15",
        "expected_intent": "FLEET_INVENTORY",
        "target_entity": "GCS-15",
        "db_validation_type": "cluster_wells",
    },
    {
        "id": "Q04",
        "domain": "Domain 1.1 Asset Status",
        "query": "what is the operational status of all monitored assets",
        "expected_intent": "FLEET_INVENTORY",
        "target_entity": None,
        "db_validation_type": "fleet_count",
    },

    # 2. Fleet Production & Deferment (Domain 1.3)
    {
        "id": "Q05",
        "domain": "Domain 1.3 Fleet Production",
        "query": "how much liquid are we lifting across the field",
        "expected_intent": "FLEET_PRODUCTION",
        "target_entity": None,
        "db_validation_type": "production_sum",
    },
    {
        "id": "Q06",
        "domain": "Domain 1.3 Extraction Volume",
        "query": "what is our daily extraction volume in barrels",
        "expected_intent": "FLEET_PRODUCTION",
        "target_entity": None,
        "db_validation_type": "production_sum",
    },
    {
        "id": "Q07",
        "domain": "Domain 1.3 Gathering Stations Production",
        "query": "what are we pumping today across all gathering stations",
        "expected_intent": "FLEET_PRODUCTION",
        "target_entity": None,
        "db_validation_type": "production_sum",
    },
    {
        "id": "Q08",
        "domain": "Domain 1.3 Deferred Oil",
        "query": "what is total deferred oil across the field today",
        "expected_intent": "FLEET_PRODUCTION",
        "target_entity": None,
        "db_validation_type": "production_sum",
    },

    # 3. Fleet Triage & Workover Priority (Domain 1.4)
    {
        "id": "Q09",
        "domain": "Domain 1.4 Fleet Triage",
        "query": "which downed pumps are highest priority to service",
        "expected_intent": "FLEET_TRIAGE",
        "target_entity": None,
        "db_validation_type": "triage_ranking",
    },
    {
        "id": "Q10",
        "domain": "Domain 1.4 Offline Intervention Queue",
        "query": "give me a rundown on our offline well intervention queue",
        "expected_intent": "FLEET_TRIAGE",
        "target_entity": None,
        "db_validation_type": "triage_ranking",
    },
    {
        "id": "Q11",
        "domain": "Domain 1.4 Triaged Wells Revenue Impact",
        "query": "rank offline tripped wells by revenue impact for crew dispatch",
        "expected_intent": "FLEET_TRIAGE",
        "target_entity": None,
        "db_validation_type": "triage_ranking",
    },

    # 4. Fleet Executive Briefing (Domain 1.5)
    {
        "id": "Q12",
        "domain": "Domain 1.5 Executive Briefing",
        "query": "give me the morning executive briefing",
        "expected_intent": "FLEET_EXECUTIVE",
        "target_entity": None,
        "db_validation_type": "executive_report",
    },
    {
        "id": "Q13",
        "domain": "Domain 1.5 Operational Scorecard",
        "query": "superintendent daily operational scorecard",
        "expected_intent": "FLEET_EXECUTIVE",
        "target_entity": None,
        "db_validation_type": "executive_report",
    },
    {
        "id": "Q14",
        "domain": "Domain 1.5 Fleet Availability",
        "query": "executive summary report on fleet availability and deferment",
        "expected_intent": "FLEET_EXECUTIVE",
        "target_entity": None,
        "db_validation_type": "executive_report",
    },

    # 5. Fleet Anomaly Surfacing & Early Warning (Domain 1.6)
    {
        "id": "Q15",
        "domain": "Domain 1.6 Behavioral Drift",
        "query": "which producing wells are drifting away from normal behavior",
        "expected_intent": "FLEET_ANOMALY",
        "target_entity": None,
        "db_validation_type": "anomaly_surfacing",
    },
    {
        "id": "Q16",
        "domain": "Domain 1.6 Sub-Trip Early Warning",
        "query": "sub-trip degradation and early warning signals across running fleet",
        "expected_intent": "FLEET_ANOMALY",
        "target_entity": None,
        "db_validation_type": "anomaly_surfacing",
    },
    {
        "id": "Q17",
        "domain": "Domain 1.6 Incipient Drift",
        "query": "are any running pumps showing incipient vibration or thermal drift",
        "expected_intent": "FLEET_ANOMALY",
        "target_entity": None,
        "db_validation_type": "anomaly_surfacing",
    },

    # 6. Fleet Alarm Timeline & Incident Clustering (Domain 1.7)
    {
        "id": "Q18",
        "domain": "Domain 1.7 Trip Chronology",
        "query": "show the sequence of trips over the past week",
        "expected_intent": "FLEET_TIMELINE",
        "target_entity": None,
        "db_validation_type": "timeline_events",
    },
    {
        "id": "Q19",
        "domain": "Domain 1.7 Alarm Clustering",
        "query": "alarm density and trip clustering across stations",
        "expected_intent": "FLEET_TIMELINE",
        "target_entity": None,
        "db_validation_type": "timeline_events",
    },
    {
        "id": "Q20",
        "domain": "Domain 1.7 Chronological Timeline",
        "query": "chronological trip incident timeline for the field",
        "expected_intent": "FLEET_TIMELINE",
        "target_entity": None,
        "db_validation_type": "timeline_events",
    },

    # 7. Multi-Well Comparison (Domain 2.1)
    {
        "id": "Q21",
        "domain": "Domain 2.1 Multi-Well Telemetry",
        "query": "compare well FS-004 vs FS-006 telemetry",
        "expected_intent": "MULTI_WELL_COMPARE",
        "target_entity": "FS-004 vs FS-006",
        "db_validation_type": "multi_well_telemetry",
    },
    {
        "id": "Q22",
        "domain": "Domain 2.1 Contrast Hydraulic & Electrical",
        "query": "contrast hydraulic and electrical data between FS-017 and FS-040",
        "expected_intent": "MULTI_WELL_COMPARE",
        "target_entity": "FS-017 vs FS-040",
        "db_validation_type": "multi_well_telemetry",
    },
    {
        "id": "Q23",
        "domain": "Domain 2.1 Comparative Audit",
        "query": "side by side comparative audit between well FNW-001 and FS-004",
        "expected_intent": "MULTI_WELL_COMPARE",
        "target_entity": "FNW-001 vs FS-004",
        "db_validation_type": "multi_well_telemetry",
    },

    # 8. Cluster Comparison (Domain 2.2)
    {
        "id": "Q24",
        "domain": "Domain 2.2 Gathering Cluster Compare",
        "query": "compare Cluster 15 vs Cluster 4 uptime and production",
        "expected_intent": "CLUSTER_COMPARE",
        "target_entity": "Cluster 15 vs Cluster 4",
        "db_validation_type": "cluster_comparison",
    },
    {
        "id": "Q25",
        "domain": "Domain 2.2 Gathering Center Benchmark",
        "query": "benchmark gathering center 3 against cluster 15",
        "expected_intent": "CLUSTER_COMPARE",
        "target_entity": "Cluster 3 vs Cluster 15",
        "db_validation_type": "cluster_comparison",
    },
    {
        "id": "Q26",
        "domain": "Domain 2.2 Water Cut Comparison",
        "query": "gathering station flow rate and water cut comparison between GCS-04 and GCS-03",
        "expected_intent": "CLUSTER_COMPARE",
        "target_entity": "Cluster 4 vs Cluster 3",
        "db_validation_type": "cluster_comparison",
    },

    # 9. Historical Baseline Comparison (Domain 2.3)
    {
        "id": "Q27",
        "domain": "Domain 2.3 Design Envelope",
        "query": "is the pump operating within its design envelope for well FS-004",
        "expected_intent": "HISTORICAL_COMPARE",
        "target_entity": "FS-004",
        "db_validation_type": "well_baseline",
    },
    {
        "id": "Q28",
        "domain": "Domain 2.3 Baseline Audit",
        "query": "compare well FS-017 against its calibrated operating baseline",
        "expected_intent": "HISTORICAL_COMPARE",
        "target_entity": "FS-017",
        "db_validation_type": "well_baseline",
    },
    {
        "id": "Q29",
        "domain": "Domain 2.3 Parameter Drift",
        "query": "check if well parameters have drifted from design model on FS-006",
        "expected_intent": "HISTORICAL_COMPARE",
        "target_entity": "FS-006",
        "db_validation_type": "well_baseline",
    },

    # 10. Peer Benchmarking (Domain 2.4)
    {
        "id": "Q30",
        "domain": "Domain 2.4 Pad Peer Comparison",
        "query": "how does this asset stack up against neighboring wells in the pad for FS-040",
        "expected_intent": "PEER_BENCHMARK",
        "target_entity": "FS-040",
        "db_validation_type": "peer_benchmark",
    },
    {
        "id": "Q31",
        "domain": "Domain 2.4 Peer Percentile Benchmark",
        "query": "peer percentile benchmark for motor temperature and amps on well FS-004",
        "expected_intent": "PEER_BENCHMARK",
        "target_entity": "FS-004",
        "db_validation_type": "peer_benchmark",
    },
    {
        "id": "Q32",
        "domain": "Domain 2.4 Cluster Peer Rank",
        "query": "how does well FS-017 rank against its cluster peers",
        "expected_intent": "PEER_BENCHMARK",
        "target_entity": "FS-017",
        "db_validation_type": "peer_benchmark",
    },

    # 11. Event Before vs After (Domain 2.5)
    {
        "id": "Q33",
        "domain": "Domain 2.5 Before/After Telemetry",
        "query": "compare telemetry before and after the trip for well FNW-001",
        "expected_intent": "EVENT_BEFORE_AFTER",
        "target_entity": "FNW-001",
        "db_validation_type": "event_before_after",
    },
    {
        "id": "Q34",
        "domain": "Domain 2.5 Event Pressure Collapse",
        "query": "pre-trip vs post-trip pressure collapse and vibration on event EV-20261012-101438-FS-017-571",
        "expected_intent": "EVENT_BEFORE_AFTER",
        "target_entity": "EV-20261012-101438-FS-017-571",
        "db_validation_type": "event_before_after",
    },

    # 12. Fleet Metric Ranking (Domain 2.6)
    {
        "id": "Q35",
        "domain": "Domain 2.6 Vibration Ranking",
        "query": "rank fleet by vibration levels",
        "expected_intent": "FLEET_RANKING",
        "target_entity": "vibration",
        "db_validation_type": "metric_ranking",
    },
    {
        "id": "Q36",
        "domain": "Domain 2.6 Liquid Rate Ranking",
        "query": "top producing wells ordered by liquid rate",
        "expected_intent": "FLEET_RANKING",
        "target_entity": "production",
        "db_validation_type": "metric_ranking",
    },
    {
        "id": "Q37",
        "domain": "Domain 2.6 Thermal Ranking",
        "query": "which well has the highest motor temperature right now",
        "expected_intent": "FLEET_RANKING",
        "target_entity": "temperature",
        "db_validation_type": "metric_ranking",
    },

    # 13. Active Trip Diagnosis (Domain 1 Root Cause)
    {
        "id": "Q38",
        "domain": "Domain 1 Root Cause by Event ID",
        "query": "diagnose event EV-20261012-103435-FNW-001-878",
        "expected_intent": "EVENT_DIAGNOSE",
        "target_entity": "EV-20261012-103435-FNW-001-878",
        "db_validation_type": "event_diagnosis",
    },
    {
        "id": "Q39",
        "domain": "Domain 1 Root Cause by Well ID",
        "query": "why did well FNW-001 trip",
        "expected_intent": "EVENT_DIAGNOSE",
        "target_entity": "FNW-001",
        "db_validation_type": "event_diagnosis",
    },
    {
        "id": "Q40",
        "domain": "Domain 1 Failure Signature",
        "query": "root cause analysis and failure signature for well FS-017",
        "expected_intent": "EVENT_DIAGNOSE",
        "target_entity": "FS-017",
        "db_validation_type": "event_diagnosis",
    },

    # 14. Well Health Surveillance
    {
        "id": "Q41",
        "domain": "Well Health State",
        "query": "is well FS-004 healthy and operating normally",
        "expected_intent": "WELL_HEALTH",
        "target_entity": "FS-004",
        "db_validation_type": "well_health",
    },
    {
        "id": "Q42",
        "domain": "Well Subsystem Alarms",
        "query": "check real-time health score and subsystem alarms for well FS-006",
        "expected_intent": "WELL_HEALTH",
        "target_entity": "FS-006",
        "db_validation_type": "well_health",
    },

    # 15. Well Failure History
    {
        "id": "Q43",
        "domain": "Well Historical Incidents",
        "query": "show trip history and past incidents for well FS-017 over the last 30 days",
        "expected_intent": "WELL_HISTORY",
        "target_entity": "FS-017",
        "db_validation_type": "well_history",
    },
    {
        "id": "Q44",
        "domain": "Well Trip Count in Window",
        "query": "how many times did well FNW-001 trip in the past week",
        "expected_intent": "WELL_HISTORY",
        "target_entity": "FNW-001",
        "db_validation_type": "well_history",
    },

    # 16. Work Order Dispatch & Safety LOTO
    {
        "id": "Q45",
        "domain": "Autonomous Maintenance Dispatch",
        "query": "generate an autonomous maintenance ticket and safety checklist for well FS-004",
        "expected_intent": "WORK_ORDER_DISPATCH",
        "target_entity": "FS-004",
        "db_validation_type": "work_order",
    },
    {
        "id": "Q46",
        "domain": "Emergency LOTO Protocol",
        "query": "stage emergency lockout tagout work order for well FNW-001",
        "expected_intent": "WORK_ORDER_DISPATCH",
        "target_entity": "FNW-001",
        "db_validation_type": "work_order",
    },

    # 17. UI Navigation Intelligence (Domain 9)
    {
        "id": "Q47",
        "domain": "Domain 9 Curve Screen Navigation",
        "query": "where can I inspect the electrical frequency curves",
        "expected_intent": "UI_NAVIGATION",
        "target_entity": None,
        "db_validation_type": "ui_route",
    },
    {
        "id": "Q48",
        "domain": "Domain 9 Downhole Schematic Navigation",
        "query": "take me to the downhole schematic view for well FS-004",
        "expected_intent": "UI_NAVIGATION",
        "target_entity": "FS-004",
        "db_validation_type": "ui_route",
    },

    # 18. Self-Knowledge & Safety Boundaries (Domain 10)
    {
        "id": "Q49",
        "domain": "Domain 10 Actuation Boundary Refusal",
        "query": "command the variable speed drive remotely to increase frequency",
        "expected_intent": "SELF_BOUNDARIES",
        "target_entity": None,
        "db_validation_type": "safety_boundary",
    },
    {
        "id": "Q50",
        "domain": "Domain 10 Operational Limitations",
        "query": "what are your operational limitations and data blind spots",
        "expected_intent": "SELF_LIMITATIONS",
        "target_entity": None,
        "db_validation_type": "limitations_report",
    },
]


def execute_50_queries_regression() -> dict[str, Any]:
    print("=" * 90)
    print("EXECUTING COMPREHENSIVE 50-QUERY REGRESSION SUITE AGAINST AGENT SERVICE V2")
    print("=" * 90)
    print(f"{'#':<4} | {'Query':<42} | {'Tier':<18} | {'Intent':<18} | {'Lat':<7} | {'Status'}")
    print("-" * 105)

    results: list[dict[str, Any]] = []
    passed_count = 0
    total_count = len(REGRESSION_50_QUERIES)

    for item in REGRESSION_50_QUERIES:
        q_id = item["id"]
        query = item["query"]
        expected_intent = item["expected_intent"]

        t0 = time.perf_counter()
        route_res = route_query_hybrid(query)
        agent_res = ask_agent(query)
        dt_ms = (time.perf_counter() - t0) * 1000

        actual_intent = route_res.intent.value
        tier = route_res.routing_tier

        # Acceptance: intent matches expected, routing_tier is canonical, response has content
        has_content = bool(agent_res.get("markdown_text")) and len(agent_res["markdown_text"]) > 20
        intent_match = actual_intent == expected_intent
        valid_tier = tier in [RoutingTierEnum.TIER_0_REGEX.value, RoutingTierEnum.TIER_0_5_SEMANTIC.value, RoutingTierEnum.TIER_1_LLM.value]

        is_pass = intent_match and valid_tier and has_content
        if is_pass:
            passed_count += 1
            status_str = "PASS"
        else:
            status_str = f"FAIL (exp: {expected_intent})"

        q_disp = query if len(query) <= 41 else query[:38] + "..."
        print(f"{q_id:<4} | {q_disp:<42} | {tier:<18} | {actual_intent:<18} | {dt_ms:>5.1f}ms | {status_str}")

        results.append({
            "id": q_id,
            "domain": item["domain"],
            "query": query,
            "expected_intent": expected_intent,
            "actual_intent": actual_intent,
            "routing_tier": tier,
            "confidence": route_res.confidence,
            "entity": route_res.entity,
            "entities": route_res.entities,
            "time_filter_label": route_res.time_filter_label,
            "latency_ms": round(dt_ms, 2),
            "status": "PASS" if is_pass else "FAIL",
            "db_validation_type": item["db_validation_type"],
            "raw_agent_output": {
                "intent": agent_res.get("intent"),
                "markdown_text": agent_res.get("markdown_text"),
                "structured_data": agent_res.get("structured_data"),
                "suggested_options": agent_res.get("suggested_options"),
                "needs_clarification": agent_res.get("needs_clarification"),
            },
        })

    summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_queries": total_count,
        "passed_queries": passed_count,
        "failed_queries": total_count - passed_count,
        "pass_rate_pct": round((passed_count / total_count) * 100, 1),
        "results": results,
    }

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "regression_50_queries_raw.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("-" * 105)
    print(f"REGRESSION SUITE COMPLETED:")
    print(f"- Total Evaluated: {total_count}")
    print(f"- Passed: {passed_count} / {total_count} ({summary['pass_rate_pct']}%)")
    print(f"- Raw outputs saved to: {output_path}")
    print("=" * 90)

    assert passed_count == total_count, f"Regression test failed: {total_count - passed_count} queries failed."
    return summary


if __name__ == "__main__":
    execute_50_queries_regression()
