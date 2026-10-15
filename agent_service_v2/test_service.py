"""Empirical verification & regression test suite for standalone Agent Service V2.

Strict adherence to /verified-code-practices:
- Zero false-pass reporting.
- Truthful validation of live Server 184 database telemetry and Server 134 LLM inference.
- Full domain coverage (Domains 1, 2, 9, 10, Work Orders, Multi-turn Antecedents, Streaming NDJSON, REST).
"""

from __future__ import annotations

import json
import logging
from fastapi.testclient import TestClient

from main import app
from app.ai.router import ask_agent

client = TestClient(app)
logger = logging.getLogger("agent.test_suite")


def test_health_endpoint():
    print("\n--- [TEST 1] GET /health Verification ---")
    res = client.get("/health")
    assert res.status_code == 200, f"Expected 200 OK, got {res.status_code}"
    data = res.json()
    print("Health response:", data)
    assert data["status"] == "HEALTHY", f"Expected HEALTHY status, got {data['status']}"
    assert data["port"] == 8092, f"Expected port 8092, got {data['port']}"
    assert data["database_connected"] is True, "Database on Server 184 must be connected"
    assert "192.168.1.134:8080" in data["llm_api_base"], "LLM Gateway must point to Server 134"
    print("PASSED: Health endpoint and remote connections verified.")


def test_domain_1_fleet_inventory():
    print("\n--- [TEST 2] Domain 1: Fleet Inventory ---")
    res = ask_agent("what is the current status of the fleet?")
    assert res["intent"] == "FLEET_INVENTORY", f"Expected FLEET_INVENTORY, got {res['intent']}"
    s_data = res["structured_data"]
    assert s_data is not None, "structured_data must not be None"
    assert s_data["total_wells"] == 10, f"Expected 10 total wells, got {s_data['total_wells']}"
    assert s_data["running_wells_count"] + s_data["tripped_wells_count"] == 10, (
        f"Sum of running ({s_data['running_wells_count']}) + tripped ({s_data['tripped_wells_count']}) must equal 10"
    )
    assert len(s_data["running_wells"]) + len(s_data["tripped_wells"]) == 10
    assert "Fleet Real-Time Operational Status" in res["markdown_text"] or "LIVE FLEET OPERATIONAL STATE" in res["markdown_text"]
    print(f"PASSED: Fleet Inventory verified. Running: {s_data['running_wells_count']}, Tripped: {s_data['tripped_wells_count']}.")


def test_domain_1_production_summary():
    print("\n--- [TEST 3] Domain 1: Fleet Production Summary ---")
    res = ask_agent("how much oil are we producing across the fleet?")
    assert res["intent"] == "FLEET_PRODUCTION", f"Expected FLEET_PRODUCTION, got {res['intent']}"
    s_data = res["structured_data"]
    assert s_data is not None
    assert "current_liquid_rate_bpd" in s_data
    assert "current_net_oil_bpd" in s_data
    assert s_data["current_liquid_rate_bpd"] > 0
    print(f"PASSED: Production summary verified: Gross Liquid = {s_data['current_liquid_rate_bpd']} BPD, Oil = {s_data['current_net_oil_bpd']} BOPD.")


def test_domain_1_triage_ranking():
    print("\n--- [TEST 4] Domain 1: Fleet Triage Ranking ---")
    res = ask_agent("triage highest risk wells in the fleet")
    assert res["intent"] == "FLEET_TRIAGE", f"Expected FLEET_TRIAGE, got {res['intent']}"
    s_data = res["structured_data"]
    assert s_data is not None
    assert "triaged_wells" in s_data
    assert len(s_data["triaged_wells"]) > 0
    print(f"PASSED: Fleet Triage verified with {len(s_data['triaged_wells'])} triaged assets.")


def test_domain_1_event_diagnose():
    print("\n--- [TEST 5] Domain 1: Event Diagnosis & Root Cause ---")
    res = ask_agent("Why did well FNW-001 trip and what are the recommended actions?")
    assert res["intent"] == "EVENT_DIAGNOSE", f"Expected EVENT_DIAGNOSE, got {res['intent']}"
    assert "FNW-001" in res["markdown_text"]
    assert "HIGH_VIBRATION" in res["markdown_text"] or "MECHANICAL" in res["markdown_text"]
    s_data = res["structured_data"]
    assert s_data is not None
    assert s_data["well_id"] == "FNW-001"
    print("PASSED: Event Diagnosis verified for well FNW-001.")


def test_domain_2_multi_well_compare():
    print("\n--- [TEST 6] Domain 2: Multi-Well Comparison ---")
    res = ask_agent("compare well FS-004 vs FS-006")
    assert res["intent"] == "MULTI_WELL_COMPARE", f"Expected MULTI_WELL_COMPARE, got {res['intent']}"
    assert "FS-004" in res["markdown_text"]
    assert "FS-006" in res["markdown_text"]
    print("PASSED: Multi-well comparison verified for FS-004 and FS-006.")


def test_domain_2_cluster_compare():
    print("\n--- [TEST 7] Domain 2: Gathering Cluster Comparison ---")
    res = ask_agent("compare cluster 15 vs cluster 4")
    assert res["intent"] == "CLUSTER_COMPARE", f"Expected CLUSTER_COMPARE, got {res['intent']}"
    s_data = res["structured_data"]
    assert s_data is not None
    assert "cluster_a" in s_data and "cluster_b" in s_data
    print(f"PASSED: Cluster comparison verified between {s_data['cluster_a']} and {s_data['cluster_b']}.")


def test_domain_2_baseline_audit():
    print("\n--- [TEST 8] Domain 2: Baseline Historical Audit ---")
    res = ask_agent("is FS-004 operating within historical baseline limits?")
    assert res["intent"] == "HISTORICAL_COMPARE", f"Expected HISTORICAL_COMPARE, got {res['intent']}"
    assert "FS-004" in res["markdown_text"]
    print("PASSED: Baseline comparison verified for FS-004.")


def test_domain_2_fleet_ranking():
    print("\n--- [TEST 9] Domain 2: Fleet Metric Ranking ---")
    res = ask_agent("rank wells by vibration")
    assert res["intent"] == "FLEET_RANKING", f"Expected FLEET_RANKING, got {res['intent']}"
    assert "Vibration" in res["markdown_text"] or "vibration" in res["markdown_text"]
    print("PASSED: Fleet ranking by vibration verified.")


def test_domain_9_ui_navigation():
    print("\n--- [TEST 10] Domain 9: UI Navigation & Route Resolution ---")
    # 1. Telemetry / tab route resolution
    res1 = ask_agent("where can I see the electrical data for FS-004?")
    assert res1["intent"] == "UI_NAVIGATION", f"Expected UI_NAVIGATION, got {res1['intent']}"
    s_data1 = res1["structured_data"]
    assert s_data1 is not None
    assert "resolved_path" in s_data1
    assert "/wells/FS-004" in s_data1["resolved_path"]
    print(f"PASSED: Electrical navigation route resolved: {s_data1['resolved_path']}")

    # 2. General route resolution
    res2 = ask_agent("where is the reports hub?")
    assert res2["intent"] == "UI_NAVIGATION"
    s_data2 = res2["structured_data"]
    assert "/reports" in s_data2["resolved_path"]
    print(f"PASSED: Report export navigation route resolved: {s_data2['resolved_path']}")

    # 3. Component / simulator route lookup
    res3 = ask_agent("where is the scenario simulator?")
    assert res3["intent"] == "UI_NAVIGATION"
    s_data3 = res3["structured_data"]
    assert "/custom-testing" in s_data3["resolved_path"]
    print(f"PASSED: Scenario simulator route resolved: {s_data3['resolved_path']}")


def test_petroleum_knowledge_rag():
    print("\n--- [TEST 10.B] Petroleum Engineering Knowledge RAG ---")
    res = ask_agent("what causes gas locking in an ESP?")
    assert res["intent"] == "KNOWLEDGE"
    assert "gas" in res["markdown_text"].lower()
    print("PASSED: Petroleum Engineering Knowledge verified.")


def test_domain_10_self_knowledge():
    print("\n--- [TEST 11] Domain 10: Agent Self-Knowledge & Safety Boundaries ---")
    # 1. Identity
    res_id = ask_agent("who are you and what is your role?")
    assert res_id["intent"] == "SELF_IDENTITY", f"Expected SELF_IDENTITY, got {res_id['intent']}"
    assert "Industrial AI Copilot" in res_id["markdown_text"] or "Industrial Maintenance Copilot" in res_id["markdown_text"]
    print("PASSED: Self-Identity verified.")

    # 2. Capabilities
    res_cap = ask_agent("what can you do?")
    assert res_cap["intent"] == "SELF_CAPABILITIES", f"Expected SELF_CAPABILITIES, got {res_cap['intent']}"
    assert "System Capabilities Manifest" in res_cap["markdown_text"]
    print("PASSED: Self-Capabilities verified.")

    # 3. Safety boundary & Actuation refusal
    res_ref = ask_agent("can you turn off pump FS-004?")
    assert res_ref["intent"] == "SELF_BOUNDARIES", f"Expected SELF_BOUNDARIES, got {res_ref['intent']}"
    assert "READ_ONLY" in res_ref["markdown_text"] or "No Physical Actuation" in res_ref["markdown_text"]
    print("PASSED: Safety refusal & Actuation boundary verified.")

    # 4. Fleet Scope
    res_scp = ask_agent("which wells do you monitor?")
    assert res_scp["intent"] == "SELF_FLEET_SCOPE", f"Expected SELF_FLEET_SCOPE, got {res_scp['intent']}"
    assert "Monitored Fleet Scope" in res_scp["markdown_text"]
    assert "10 Monitored Assets" in res_scp["markdown_text"]
    print("PASSED: Fleet Scope verified.")

    # 5. Limitations
    res_lim = ask_agent("what are your operational limitations?")
    assert res_lim["intent"] == "SELF_LIMITATIONS", f"Expected SELF_LIMITATIONS, got {res_lim['intent']}"
    assert "System Limitations & Known Disclosures" in res_lim["markdown_text"]
    print("PASSED: Operational limitations verified.")


def test_work_order_dispatch_safety():
    print("\n--- [TEST 12] Work Order Dispatch & Safety Protocol ---")
    res = ask_agent("dispatch work order for FS-004 to replace mechanical seal")
    assert res["intent"] == "WORK_ORDER_DISPATCH", f"Expected WORK_ORDER_DISPATCH, got {res['intent']}"
    s_data = res["structured_data"]
    assert s_data is not None
    assert s_data["work_order_code"] == "WO-ESP-FS-004-AUTO"
    assert s_data["well_id"] == "FS-004"
    assert len(s_data["loto_checklist"]) >= 5
    # Verify mandatory safety checks
    checklist_str = " ".join(s_data["loto_checklist"])
    assert "MANDATORY LOTO" in checklist_str
    assert "ZERO-ENERGY VERIFICATION" in checklist_str
    assert "ELECTRICAL MEGGER TEST" in checklist_str
    print("PASSED: Autonomous Work Order Dispatch verified with full LOTO checklist.")


def test_multi_turn_antecedent_resolution():
    print("\n--- [TEST 13] Multi-turn Pronoun & Antecedent Resolution ---")
    history = [
        {"role": "user", "content": "Let's inspect well FS-004"},
        {"role": "assistant", "content": "Well FS-004 is currently RUNNING with motor temp at 85 C."},
    ]
    res = ask_agent("what is its motor temperature and is it normal?", conversation_history=history)
    # The antecedent "its" should resolve to FS-004
    assert res["intent"] in ["WELL_HEALTH", "HISTORICAL_COMPARE", "PRODUCTION"]
    assert "FS-004" in res["markdown_text"]
    print("PASSED: Multi-turn antecedent 'its' resolved to well FS-004 successfully.")


def test_streaming_ndjson_protocol():
    print("\n--- [TEST 14] Streaming NDJSON Protocol (/query) ---")
    # Test 1: Message payload with Event Diagnosis
    res = client.post("/query", json={"message": "Why did well FNW-001 trip?"})
    assert res.status_code == 200
    assert "application/x-ndjson" in res.headers["content-type"]
    lines = [line.strip() for line in res.text.split("\n") if line.strip()]
    assert len(lines) >= 4, f"Expected at least 4 NDJSON frames, got {len(lines)}"

    frame_types = []
    for line in lines:
        parsed = json.loads(line)
        frame_types.append(parsed.get("type"))

    print("Observed frame sequence (FNW-001 diagnosis):", frame_types)
    assert "status" in frame_types
    assert "text_delta" in frame_types
    assert "advisory" in frame_types, "Event diagnosis must emit advisory frame for <AgentDock />"
    assert "done" in frame_types
    last_frame = json.loads(lines[-1])
    assert last_frame["type"] == "done"
    assert last_frame["status"] == "COMPLETED"

    # Test 2: Backward compatibility with 'question' field
    res_compat = client.post("/query", json={"question": "what is the current status of the fleet?"})
    assert res_compat.status_code == 200
    compat_lines = [line.strip() for line in res_compat.text.split("\n") if line.strip()]
    compat_last = json.loads(compat_lines[-1])
    assert compat_last["type"] == "done"
    assert compat_last["status"] == "COMPLETED"

    # Test 3: Work Order Dispatch advisory emission
    res_wo = client.post("/query", json={"message": "dispatch work order for FS-004"})
    assert res_wo.status_code == 200
    wo_lines = [line.strip() for line in res_wo.text.split("\n") if line.strip()]
    wo_types = [json.loads(l).get("type") for l in wo_lines]
    assert "advisory" in wo_types, "Work order dispatch must emit advisory frame"
    print("PASSED: Streaming NDJSON protocol verified across all frame types and payloads.")


def test_rest_ask_endpoints():
    print("\n--- [TEST 15] REST Endpoints (/ask and /api/v1/esp/ask) ---")
    # 1. POST /ask
    res1 = client.post("/ask", json={"question": "what is the current status of the fleet?"})
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["intent"] == "FLEET_INVENTORY"
    assert "answer" in data1 and len(data1["answer"]) > 0
    assert data1["structured_data"]["total_wells"] == 10
    print("PASSED: POST /ask returned valid JSON response.")

    # 2. POST /api/v1/esp/ask
    res2 = client.post("/api/v1/esp/ask", json={"message": "who are you?"})
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["intent"] == "SELF_IDENTITY"
    assert "Industrial AI Copilot" in data2["answer"] or "Industrial Maintenance Copilot" in data2["answer"]
    print("PASSED: POST /api/v1/esp/ask returned valid JSON response.")


if __name__ == "__main__":
    print("=" * 70)
    print("STARTING EXHAUSTIVE VERIFICATION FOR AGENT SERVICE V2")
    print("=" * 70)

    test_health_endpoint()
    test_domain_1_fleet_inventory()
    test_domain_1_production_summary()
    test_domain_1_triage_ranking()
    test_domain_1_event_diagnose()
    test_domain_2_multi_well_compare()
    test_domain_2_cluster_compare()
    test_domain_2_baseline_audit()
    test_domain_2_fleet_ranking()
    test_domain_9_ui_navigation()
    test_petroleum_knowledge_rag()
    test_domain_10_self_knowledge()
    test_work_order_dispatch_safety()
    test_multi_turn_antecedent_resolution()
    test_streaming_ndjson_protocol()
    test_rest_ask_endpoints()

    print("\n" + "=" * 70)
    print("ALL 15 VERIFICATION SUITES PASSED GREEN (100% SUCCESS)!")
    print("AGENT SERVICE V2 IS HARDENED, COMPLETE, AND READY FOR HANDOFF.")
    print("=" * 70)
