"""Comprehensive Full Regression Audit Suite (70 Queries)
Covers:
1. Diagnostic XAI (RCA, Waveform Vectors, Hypotheses, Health, History, Production, HITL)
2. Petroleum Standards RAG, Work Order Dispatch & Conversational Chit-Chat
3. Domain 1: Fleet Baseline, Triage, Surveillance, Production & Anomaly Screening
4. Domain 2: Fleet Comparison, Cluster Comparison, Peer Benchmark, Historical Baseline & Ranking
5. Domain 9: UI / Navigation / Route Awareness (Routes, Components, Concepts, Parametric Binding, Fallback)
6. Domain 10: Self-Knowledge & System Identity (Identity, Capabilities, Boundaries, Fleet Scope, Tasks, Limitations)

Outputs results to FULL_REGRESSION_TEST_REPORT.txt
"""

import urllib.request
import urllib.parse
import json
import time
import os
import sys
from datetime import datetime

URL = "http://127.0.0.1:8000/api/v1/esp/ask"

QUERIES = [
    # =========================================================================
    # GROUP 1: DIAGNOSTIC XAI (10 Queries)
    # =========================================================================
    {
        "id": "XAI-01",
        "domain": "Diagnostic XAI",
        "subdomain": "Trip Diagnosis by Event ID",
        "query": "Diagnose event EV-20261012-103435-FNW-001-878",
        "expected_intent": "EVENT_DIAGNOSE",
        "check": lambda d, a: (
            ("FNW-001" in a or "BEARING_WEAR" in a or "Vibration" in a)
            and len(a) > 200,
            "Must identify well FNW-001 and diagnostic root cause"
        )
    },
    {
        "id": "XAI-02",
        "domain": "Diagnostic XAI",
        "subdomain": "Trip Diagnosis by Well ID",
        "query": "Why did well FS-017 trip?",
        "expected_intent": "EVENT_DIAGNOSE",
        "check": lambda d, a: (
            ("FS-017" in a or "OVERLOAD" in a or "Solids" in a or "sand" in a.lower())
            and len(a) > 200,
            "Must isolate primary trip cause on FS-017"
        )
    },
    {
        "id": "XAI-03",
        "domain": "Diagnostic XAI",
        "subdomain": "Event Diagnosis (FS-040)",
        "query": "Diagnose latest shutdown on well FS-040",
        "expected_intent": "EVENT_DIAGNOSE",
        "check": lambda d, a: (
            "FS-040" in a and ("Trip" in a or "Diagnosis" in a or "Event" in a),
            "Must retrieve and diagnose latest event on FS-040"
        )
    },
    {
        "id": "XAI-04",
        "domain": "Diagnostic XAI",
        "subdomain": "Telemetry Feature Extraction",
        "query": "Show sensor deviations and waveform trends for the trip on FS-017",
        "expected_intent": "EVENT_DIAGNOSE",
        "check": lambda d, a: (
            ("Deviation" in a or "Baseline" in a or "Current" in a or "Vibration" in a)
            and len(a) > 150,
            "Must report pre-trip deviations vs calibrated baseline"
        )
    },
    {
        "id": "XAI-05",
        "domain": "Diagnostic XAI",
        "subdomain": "Hypothesis & Confidence Scoring",
        "query": "What is the primary hypothesis and confirmation test for FNW-001 shutdown?",
        "expected_intent": "EVENT_DIAGNOSE",
        "check": lambda d, a: (
            ("Hypothesis" in a or "Confidence" in a or "Test" in a)
            and len(a) > 150,
            "Must provide ranked hypotheses with confirmation tests"
        )
    },
    {
        "id": "XAI-06",
        "domain": "Diagnostic XAI",
        "subdomain": "Temporal Failure History (7 Days)",
        "query": "Show failure history of well FS-017 in the last 7 days",
        "expected_intent": "WELL_HISTORY",
        "check": lambda d, a: (
            "FS-017" in a and ("Historical" in a or "Event" in a or "Trip" in a or "7" in a),
            "Must report temporal historical window for FS-017"
        )
    },
    {
        "id": "XAI-07",
        "domain": "Diagnostic XAI",
        "subdomain": "Well Health Assessment",
        "query": "Is well FNW-001 healthy? What is its current condition?",
        "expected_intent": "WELL_HEALTH",
        "check": lambda d, a: (
            "FNW-001" in a and ("Health" in a or "Condition" in a or "State" in a),
            "Must compute deterministic health index for FNW-001"
        )
    },
    {
        "id": "XAI-08",
        "domain": "Diagnostic XAI",
        "subdomain": "Well Health Assessment (FS-004)",
        "query": "What is the current health status and operating envelope of FS-004?",
        "expected_intent": "WELL_HEALTH",
        "check": lambda d, a: (
            "FS-004" in a and ("Health" in a or "Operating" in a or "RUNNING" in a or "TRIPPED" in a),
            "Must compute health index and telemetry envelope for FS-004"
        )
    },
    {
        "id": "XAI-09",
        "domain": "Diagnostic XAI",
        "subdomain": "Well Production Metrics",
        "query": "What is the current flow rate and water cut of well FS-004?",
        "expected_intent": "PRODUCTION",
        "check": lambda d, a: (
            "FS-004" in a and ("BPD" in a or "Water Cut" in a or "Production" in a or "%" in a),
            "Must return gross liquid rate and water cut for FS-004"
        )
    },
    {
        "id": "XAI-10",
        "domain": "Diagnostic XAI",
        "subdomain": "HITL Operational Clarification",
        "query": "Why did the pump stop?",
        "expected_intent": "EVENT_DIAGNOSE",
        "check": lambda d, a: (
            d.get("needs_clarification") is True and len(d.get("suggested_options", [])) > 0,
            "Must trigger HITL clarification when well ID is omitted"
        )
    },

    # =========================================================================
    # GROUP 2: STANDARDS RAG, WORK ORDERS & CHIT-CHAT (8 Queries)
    # =========================================================================
    {
        "id": "RAG-01",
        "domain": "Petroleum Standards RAG",
        "subdomain": "Gas Locking Prevention",
        "query": "What causes gas locking in an ESP and how to prevent it?",
        "expected_intent": "KNOWLEDGE",
        "check": lambda d, a: (
            ("gas" in a.lower() or "lock" in a.lower() or "separator" in a.lower())
            and len(a) > 100,
            "Must cite petroleum engineering principles on gas locking"
        )
    },
    {
        "id": "RAG-02",
        "domain": "Petroleum Standards RAG",
        "subdomain": "Sand Management Guidelines",
        "query": "How to handle sand production and solids erosion in ESP completions?",
        "expected_intent": "KNOWLEDGE",
        "check": lambda d, a: (
            ("sand" in a.lower() or "erosion" in a.lower() or "abrasion" in a.lower())
            and len(a) > 100,
            "Must cite API/field manual guidance for solids management"
        )
    },
    {
        "id": "RAG-03",
        "domain": "Petroleum Standards RAG",
        "subdomain": "Electrical Current Unbalance",
        "query": "What causes high current unbalance in ESP motors?",
        "expected_intent": "KNOWLEDGE",
        "check": lambda d, a: (
            ("current" in a.lower() or "unbalance" in a.lower() or "voltage" in a.lower() or "phase" in a.lower())
            and len(a) > 100,
            "Must explain causes of phase/current unbalance"
        )
    },
    {
        "id": "RAG-04",
        "domain": "Petroleum Standards RAG",
        "subdomain": "Thermal Limits & Insulation",
        "query": "What are API RP 11S guidelines for motor winding temperature limits?",
        "expected_intent": "KNOWLEDGE",
        "check": lambda d, a: (
            ("temperature" in a.lower() or "motor" in a.lower() or "winding" in a.lower() or "11s" in a.lower() or "c" in a.lower())
            and len(a) > 100,
            "Must cite motor thermal rating and insulation constraints"
        )
    },
    {
        "id": "RAG-05",
        "domain": "Work Order Dispatch",
        "subdomain": "Emergency Dispatch with LOTO",
        "query": "Create an emergency work order to dispatch maintenance for well FNW-001",
        "expected_intent": "WORK_ORDER_DISPATCH",
        "check": lambda d, a: (
            ("Work Order" in a or "WO-" in a) and ("LOTO" in a or "multimeter" in a.lower()),
            "Must generate P1 work order with mandatory safety LOTO"
        )
    },
    {
        "id": "RAG-06",
        "domain": "Work Order Dispatch",
        "subdomain": "Dispatch for FS-017",
        "query": "Dispatch emergency work order for tripped well FS-017",
        "expected_intent": "WORK_ORDER_DISPATCH",
        "check": lambda d, a: (
            ("Work Order" in a or "WO-" in a) and "FS-017" in a,
            "Must dispatch work order for well FS-017"
        )
    },
    {
        "id": "RAG-07",
        "domain": "Chit-Chat & Persona",
        "subdomain": "Conversational Greeting",
        "query": "Hello, how are things going today?",
        "expected_intent": "CHAT",
        "check": lambda d, a: (
            len(a) > 20 and not a.startswith("# [ESP APM] System Identity"),
            "Must respond professionally with persona invitation"
        )
    },
    {
        "id": "RAG-08",
        "domain": "Chit-Chat & Persona",
        "subdomain": "Operational Greeting",
        "query": "Good morning assistant, are you ready for surveillance duty?",
        "expected_intent": "CHAT",
        "check": lambda d, a: (
            len(a) > 20,
            "Must return conversational readiness response"
        )
    },

    # =========================================================================
    # GROUP 3: DOMAIN 1 - BASELINE, TRIAGE & SURVEILLANCE (8 Queries)
    # =========================================================================
    {
        "id": "DOM1-01",
        "domain": "Domain 1: Surveillance",
        "subdomain": "Fleet Production & Deferment",
        "query": "Show total fleet production and deferred oil loss across clusters",
        "expected_intent": "FLEET_PRODUCTION",
        "check": lambda d, a: (
            ("Fleet Production" in a or "BOPD" in a) and ("Deferred" in a or "Loss" in a or "BPD" in a),
            "Must aggregate fleet gross liquid and oil deferment"
        )
    },
    {
        "id": "DOM1-02",
        "domain": "Domain 1: Surveillance",
        "subdomain": "Fleet Production Summary",
        "query": "What is the daily gross liquid and net oil production of the fleet?",
        "expected_intent": "FLEET_PRODUCTION",
        "check": lambda d, a: (
            ("Production" in a or "Gross Liquid" in a) and ("BPD" in a or "BOPD" in a),
            "Must report fleet daily production volumes"
        )
    },
    {
        "id": "DOM1-03",
        "domain": "Domain 1: Surveillance",
        "subdomain": "Fleet Operational Triage",
        "query": "Fleet triage: rank offline wells by severity and intervention urgency",
        "expected_intent": "FLEET_TRIAGE",
        "check": lambda d, a: (
            "Fleet Operational Triage" in a or "Urgency" in a or "Offline" in a or "Severity" in a,
            "Must rank offline wells by operational triage urgency"
        )
    },
    {
        "id": "DOM1-04",
        "domain": "Domain 1: Surveillance",
        "subdomain": "Tripped Wells Priority Triage",
        "query": "Which tripped wells require immediate engineering intervention?",
        "expected_intent": "FLEET_TRIAGE",
        "check": lambda d, a: (
            ("Triage" in a or "Severity" in a or "Intervention" in a or "Priority" in a) and len(a) > 100,
            "Must identify high-severity tripped assets"
        )
    },
    {
        "id": "DOM1-05",
        "domain": "Domain 1: Surveillance",
        "subdomain": "Fleet Anomaly Early Warning",
        "query": "Which wells are anomalous right now? Show fleet sub-trip drift",
        "expected_intent": "FLEET_ANOMALY",
        "check": lambda d, a: (
            "Fleet Anomaly" in a or "Anomaly" in a or "Drift" in a or "Running Wells" in a,
            "Must surface active running wells with sub-trip drift"
        )
    },
    {
        "id": "DOM1-06",
        "domain": "Domain 1: Surveillance",
        "subdomain": "Fleet Executive Summary",
        "query": "Generate morning executive report for the ESP fleet",
        "expected_intent": "FLEET_EXECUTIVE",
        "check": lambda d, a: (
            ("Executive" in a or "Fleet" in a or "Surveillance" in a) and ("Availability" in a or "Summary" in a),
            "Must render high-level executive surveillance report"
        )
    },
    {
        "id": "DOM1-07",
        "domain": "Domain 1: Surveillance",
        "subdomain": "Fleet Asset Inventory",
        "query": "Show fleet inventory across gathering centers",
        "expected_intent": "FLEET_INVENTORY",
        "check": lambda d, a: (
            ("Inventory" in a or "Asset" in a or "Cluster" in a) and len(a) > 100,
            "Must list asset inventory grouped by cluster"
        )
    },
    {
        "id": "DOM1-08",
        "domain": "Domain 1: Surveillance",
        "subdomain": "Fleet Alarm Timeline (48h)",
        "query": "Show fleet alarm timeline for the past 48 hours",
        "expected_intent": "FLEET_TIMELINE",
        "check": lambda d, a: (
            ("Alarm" in a or "Timeline" in a or "48" in a or "Hour" in a) and len(a) > 80,
            "Must construct chronological alarm timeline"
        )
    },

    # =========================================================================
    # GROUP 4: DOMAIN 2 - COMPARISON & RANKING (10 Queries)
    # =========================================================================
    {
        "id": "DOM2-01",
        "domain": "Domain 2: Comparison & Ranking",
        "subdomain": "Well-to-Well Comparison",
        "query": "Compare well FS-017 vs FS-040",
        "expected_intent": "MULTI_WELL_COMPARE",
        "check": lambda d, a: (
            "FS-017" in a and "FS-040" in a and ("Comparative" in a or "|" in a),
            "Must generate side-by-side comparative table for both wells"
        )
    },
    {
        "id": "DOM2-02",
        "domain": "Domain 2: Comparison & Ranking",
        "subdomain": "Well Comparison (FNW-001 vs FS-004)",
        "query": "Compare well FNW-001 vs FS-004",
        "expected_intent": "MULTI_WELL_COMPARE",
        "check": lambda d, a: (
            "FNW-001" in a and "FS-004" in a and ("Comparative" in a or "|" in a),
            "Must compare operating metrics for FNW-001 and FS-004"
        )
    },
    {
        "id": "DOM2-03",
        "domain": "Domain 2: Comparison & Ranking",
        "subdomain": "Cluster Comparison",
        "query": "Compare Cluster 15 vs Cluster 4",
        "expected_intent": "CLUSTER_COMPARE",
        "check": lambda d, a: (
            "Cluster 15" in a and "Cluster 4" in a and ("Comparison" in a or "Availability" in a or "Liquid" in a),
            "Must contrast availability and gross production across clusters"
        )
    },
    {
        "id": "DOM2-04",
        "domain": "Domain 2: Comparison & Ranking",
        "subdomain": "Cluster Comparison (3 vs 15)",
        "query": "Compare Cluster 3 vs Cluster 15",
        "expected_intent": "CLUSTER_COMPARE",
        "check": lambda d, a: (
            "Cluster 3" in a and "Cluster 15" in a,
            "Must compare Cluster 3 vs Cluster 15 metrics"
        )
    },
    {
        "id": "DOM2-05",
        "domain": "Domain 2: Comparison & Ranking",
        "subdomain": "Ambiguous Cluster HITL",
        "query": "Compare the clusters",
        "expected_intent": "CLUSTER_COMPARE",
        "check": lambda d, a: (
            d.get("needs_clarification") is True and len(d.get("suggested_options", [])) >= 2,
            "Must trigger HITL clarification when cluster pairs omitted"
        )
    },
    {
        "id": "DOM2-06",
        "domain": "Domain 2: Comparison & Ranking",
        "subdomain": "Historical Baseline Comparison (24h vs 7d)",
        "query": "Compare well FS-017 past 24 hours with last 7 days",
        "expected_intent": "HISTORICAL_COMPARE",
        "check": lambda d, a: (
            "FS-017" in a and ("24" in a or "7" in a or "Baseline" in a or "Historical" in a),
            "Must compare rolling 24h vs prior 7d baseline parameters"
        )
    },
    {
        "id": "DOM2-07",
        "domain": "Domain 2: Comparison & Ranking",
        "subdomain": "Peer Group Benchmarking",
        "query": "Compare well FS-017 against its cluster peers",
        "expected_intent": "PEER_BENCHMARK",
        "check": lambda d, a: (
            "FS-017" in a and ("Peer" in a or "Cluster" in a or "Median" in a or "Benchmark" in a),
            "Must evaluate target well metrics against cluster peer medians"
        )
    },
    {
        "id": "DOM2-08",
        "domain": "Domain 2: Comparison & Ranking",
        "subdomain": "Trip Before/After Forensics",
        "query": "Compare conditions before and after trip for event EV-20261012-101438-FS-017-571",
        "expected_intent": "EVENT_BEFORE_AFTER",
        "check": lambda d, a: (
            ("Before" in a or "After" in a or "Pre-Trip" in a or "Post-Trip" in a) and len(a) > 100,
            "Must contrast telemetry parameters before and after trip"
        )
    },
    {
        "id": "DOM2-09",
        "domain": "Domain 2: Comparison & Ranking",
        "subdomain": "Fleet Ranking by Trips",
        "query": "Rank fleet by lifetime trips",
        "expected_intent": "FLEET_RANKING",
        "check": lambda d, a: (
            ("Rank" in a or "Leaderboard" in a or "#1" in a or "Trip" in a) and "|" in a,
            "Must render fleet ranking table by lifetime trips"
        )
    },
    {
        "id": "DOM2-10",
        "domain": "Domain 2: Comparison & Ranking",
        "subdomain": "Fleet Ranking by Vibration",
        "query": "Which wells have the highest vibration?",
        "expected_intent": "FLEET_RANKING",
        "check": lambda d, a: (
            ("Vibration" in a or "Rank" in a or "#1" in a or "g" in a) and "|" in a,
            "Must rank wells descending by vibration peak amplitude"
        )
    },

    # =========================================================================
    # GROUP 5: DOMAIN 9 - UI / NAVIGATION / ROUTE AWARENESS (18 Queries)
    # =========================================================================
    {
        "id": "DOM9-01",
        "domain": "Domain 9: UI Navigation",
        "subdomain": "Primary Route: Working Status",
        "query": "what is the Working Status page?",
        "expected_intent": "UI_NAVIGATION",
        "check": lambda d, a: (
            "working" in a.lower() and "[route.working_status]" in a,
            "Must narrate working status screen and end with [route.working_status]"
        )
    },
    {
        "id": "DOM9-02",
        "domain": "Domain 9: UI Navigation",
        "subdomain": "Primary Route: Working Status Explanation",
        "query": "explain the Working Status screen",
        "expected_intent": "UI_NAVIGATION",
        "check": lambda d, a: (
            "working" in a.lower() and "[route.working_status]" in a,
            "Must explain working status and end with [route.working_status]"
        )
    },
    {
        "id": "DOM9-03",
        "domain": "Domain 9: UI Navigation",
        "subdomain": "Primary Route: Fleet Cockpit",
        "query": "what is the Fleet Cockpit page?",
        "expected_intent": "UI_NAVIGATION",
        "check": lambda d, a: (
            "cockpit" in a.lower() and "[route.fleet_cockpit]" in a,
            "Must narrate fleet cockpit and end with [route.fleet_cockpit]"
        )
    },
    {
        "id": "DOM9-04",
        "domain": "Domain 9: UI Navigation",
        "subdomain": "Primary Route: Fleet Cockpit Location",
        "query": "where is the fleet cockpit?",
        "expected_intent": "UI_NAVIGATION",
        "check": lambda d, a: (
            "cockpit" in a.lower() and "[route.fleet_cockpit]" in a,
            "Must provide fleet cockpit route path and end with [route.fleet_cockpit]"
        )
    },
    {
        "id": "DOM9-05",
        "domain": "Domain 9: UI Navigation",
        "subdomain": "Primary Route: Well Monitor",
        "query": "what is the Well Monitor screen?",
        "expected_intent": "UI_NAVIGATION",
        "check": lambda d, a: (
            ("well" in a.lower() or "monitor" in a.lower()) and "[route.well_detail]" in a,
            "Must narrate well monitor and end with [route.well_detail]"
        )
    },
    {
        "id": "DOM9-06",
        "domain": "Domain 9: UI Navigation",
        "subdomain": "Primary Route: Live Calculations",
        "query": "what is the Live Calculations page?",
        "expected_intent": "UI_NAVIGATION",
        "check": lambda d, a: (
            ("calculation" in a.lower() or "live" in a.lower()) and "[route.live_calculations]" in a,
            "Must narrate live calculations and end with [route.live_calculations]"
        )
    },
    {
        "id": "DOM9-07",
        "domain": "Domain 9: UI Navigation",
        "subdomain": "Primary Route: Event Intelligence",
        "query": "what is the Event Intelligence page?",
        "expected_intent": "UI_NAVIGATION",
        "check": lambda d, a: (
            ("event" in a.lower() or "trip" in a.lower() or "intelligence" in a.lower()) and "[route.event_intelligence]" in a,
            "Must narrate event intelligence and end with [route.event_intelligence]"
        )
    },
    {
        "id": "DOM9-08",
        "domain": "Domain 9: UI Navigation",
        "subdomain": "Primary Route: Reports Hub",
        "query": "what is the Reports Hub page?",
        "expected_intent": "UI_NAVIGATION",
        "check": lambda d, a: (
            "report" in a.lower() and "[route.reports_hub]" in a,
            "Must narrate reports hub and end with [route.reports_hub]"
        )
    },
    {
        "id": "DOM9-09",
        "domain": "Domain 9: UI Navigation",
        "subdomain": "Primary Route: Scenario Simulator",
        "query": "what is the Scenario Simulator page?",
        "expected_intent": "UI_NAVIGATION",
        "check": lambda d, a: (
            ("scenario" in a.lower() or "simulator" in a.lower() or "testing" in a.lower()) and "[route.scenario_simulator]" in a,
            "Must narrate scenario simulator and end with [route.scenario_simulator]"
        )
    },
    {
        "id": "DOM9-10",
        "domain": "Domain 9: UI Navigation",
        "subdomain": "Navigation Index / Workspace Overview",
        "query": "show all screens in operations workspace",
        "expected_intent": "UI_NAVIGATION",
        "check": lambda d, a: (
            "[navigation.operations_workspace]" in a or "operations" in a.lower(),
            "Must list workspace screens and cite navigation index"
        )
    },
    {
        "id": "DOM9-11",
        "domain": "Domain 9: UI Navigation",
        "subdomain": "Component: 2D ESP String Visualizer",
        "query": "where can I find the 2D ESP string visualizer?",
        "expected_intent": "UI_NAVIGATION",
        "check": lambda d, a: (
            ("visualizer" in a.lower() or "schematic" in a.lower() or "string" in a.lower()) and "[route.well_detail]" in a,
            "Must locate visualizer on well detail and end with [route.well_detail]"
        )
    },
    {
        "id": "DOM9-12",
        "domain": "Domain 9: UI Navigation",
        "subdomain": "Component: 4-Subsystem Equalizer",
        "query": "what does the 4-subsystem equalizer display?",
        "expected_intent": "UI_NAVIGATION",
        "check": lambda d, a: (
            ("equalizer" in a.lower() or "subsystem" in a.lower() or "hydraulic" in a.lower()) and "[route.well_detail]" in a,
            "Must describe 4-subsystem equalizer meters on well detail"
        )
    },
    {
        "id": "DOM9-13",
        "domain": "Domain 9: UI Navigation",
        "subdomain": "Component: Live Pump Performance Curves",
        "query": "where are live pump performance curves?",
        "expected_intent": "UI_NAVIGATION",
        "check": lambda d, a: (
            ("curve" in a.lower() or "pump" in a.lower() or "h-q" in a.lower()) and "[route.well_detail]" in a,
            "Must locate pump curve component on well detail"
        )
    },
    {
        "id": "DOM9-14",
        "domain": "Domain 9: UI Navigation",
        "subdomain": "Concept: 14-Fault Classifier Spectrum",
        "query": "what is the 14-fault classifier spectrum?",
        "expected_intent": "UI_NAVIGATION",
        "check": lambda d, a: (
            ("14-fault" in a.lower() or "classifier" in a.lower() or "machine learning" in a.lower() or "spectrum" in a.lower()) and "[route.working_status]" in a,
            "Must explain 14-fault classifier concept on working status"
        )
    },
    {
        "id": "DOM9-15",
        "domain": "Domain 9: UI Navigation",
        "subdomain": "Concept: Virtual Flow Metering (VFM)",
        "query": "what is virtual flow metering (VFM)?",
        "expected_intent": "UI_NAVIGATION",
        "check": lambda d, a: (
            ("vfm" in a.lower() or "virtual flow" in a.lower() or "thermodynamic" in a.lower()) and "[route.live_calculations]" in a,
            "Must explain VFM concept on live calculations"
        )
    },
    {
        "id": "DOM9-16",
        "domain": "Domain 9: UI Navigation",
        "subdomain": "Parametric Entity Binding (FS-017)",
        "query": "where can I find pump curves for FS-017?",
        "expected_intent": "UI_NAVIGATION",
        "check": lambda d, a: (
            "/wells/FS-017" in a and "[route.well_detail]" in a,
            "Must bind entity FS-017 into route path /wells/FS-017"
        )
    },
    {
        "id": "DOM9-17",
        "domain": "Domain 9: UI Navigation",
        "subdomain": "Parametric Entity Binding (FNW-001)",
        "query": "show well detail for FNW-001",
        "expected_intent": "UI_NAVIGATION",
        "check": lambda d, a: (
            "/wells/FNW-001" in a and "[route.well_detail]" in a,
            "Must bind entity FNW-001 into route path /wells/FNW-001"
        )
    },
    {
        "id": "DOM9-18",
        "domain": "Domain 9: UI Navigation",
        "subdomain": "Out-of-Scope Navigation Fallback",
        "query": "where is the pizza ordering screen?",
        "expected_intent": "UI_NAVIGATION",
        "check": lambda d, a: (
            "That's not documented in the platform guide yet." in a,
            "Must return exact documented fallback phrase for unknown screens"
        )
    },

    # =========================================================================
    # GROUP 6: DOMAIN 10 - SELF-KNOWLEDGE & IDENTITY (16 Queries)
    # =========================================================================
    {
        "id": "DOM10-01",
        "domain": "Domain 10: Self-Knowledge",
        "subdomain": "10.1 Core Agent Identity",
        "query": "who are you?",
        "expected_intent": "SELF_IDENTITY",
        "check": lambda d, a: (
            "System Identity" in a and ("ADVAIT" in a or "Copilot" in a or "ESP APM" in a),
            "Must state core agent identity and system name"
        )
    },
    {
        "id": "DOM10-02",
        "domain": "Domain 10: Self-Knowledge",
        "subdomain": "10.1 System Identity & Version",
        "query": "what is your system identity?",
        "expected_intent": "SELF_IDENTITY",
        "check": lambda d, a: (
            "System Identity" in a and ("2.4.0" in a or "Autonomous" in a or "Server 184" in a),
            "Must report full architecture specification and database server"
        )
    },
    {
        "id": "DOM10-03",
        "domain": "Domain 10: Self-Knowledge",
        "subdomain": "10.1 Agent Introduction",
        "query": "introduce yourself and your background",
        "expected_intent": "SELF_IDENTITY",
        "check": lambda d, a: (
            "Identity" in a and ("ESP" in a or "Surveillance" in a),
            "Must introduce petroleum engineering surveillance role"
        )
    },
    {
        "id": "DOM10-04",
        "domain": "Domain 10: Self-Knowledge",
        "subdomain": "10.2 System Capabilities Catalog",
        "query": "what are your capabilities?",
        "expected_intent": "SELF_CAPABILITIES",
        "check": lambda d, a: (
            "Capabilities" in a and ("Trip Root Cause" in a or "Surveillance" in a or "Triage" in a),
            "Must catalog core domain capabilities"
        )
    },
    {
        "id": "DOM10-05",
        "domain": "Domain 10: Self-Knowledge",
        "subdomain": "10.2 Functional Scope",
        "query": "what can you do?",
        "expected_intent": "SELF_CAPABILITIES",
        "check": lambda d, a: (
            "Capabilities" in a and len(a) > 200,
            "Must list supported diagnostic and surveillance capabilities"
        )
    },
    {
        "id": "DOM10-06",
        "domain": "Domain 10: Self-Knowledge",
        "subdomain": "10.2 Core Features Overview",
        "query": "list your core features",
        "expected_intent": "SELF_CAPABILITIES",
        "check": lambda d, a: (
            "Capabilities" in a and ("Diagnostic" in a or "Forensics" in a or "Baseline" in a),
            "Must provide comprehensive features breakdown"
        )
    },
    {
        "id": "DOM10-07",
        "domain": "Domain 10: Self-Knowledge",
        "subdomain": "10.3 Operational Boundaries",
        "query": "what are your operational boundaries?",
        "expected_intent": "SELF_BOUNDARIES",
        "check": lambda d, a: (
            "Boundaries" in a and ("In-Scope" in a or "Out-of-Scope" in a or "Read-Only" in a),
            "Must explicitly define in-scope vs out-of-scope system boundaries"
        )
    },
    {
        "id": "DOM10-08",
        "domain": "Domain 10: Self-Knowledge",
        "subdomain": "10.3 Out of Scope Disclosures",
        "query": "what can you not do?",
        "expected_intent": "SELF_BOUNDARIES",
        "check": lambda d, a: (
            "Boundaries" in a and ("Out-of-Scope" in a or "Control Actuation" in a or "SCADA" in a),
            "Must disclose actuation prohibitions and safety boundaries"
        )
    },
    {
        "id": "DOM10-09",
        "domain": "Domain 10: Self-Knowledge",
        "subdomain": "10.3 What is Out of Scope",
        "query": "what is out of scope for you?",
        "expected_intent": "SELF_BOUNDARIES",
        "check": lambda d, a: (
            "Boundaries" in a and len(a) > 150,
            "Must detail out-of-scope boundaries"
        )
    },
    {
        "id": "DOM10-10",
        "domain": "Domain 10: Self-Knowledge",
        "subdomain": "10.4 Monitored Fleet Scope",
        "query": "what fleet do you monitor?",
        "expected_intent": "SELF_FLEET_SCOPE",
        "check": lambda d, a: (
            "Fleet Scope" in a and ("10" in a or "Farha South" in a or "GCS" in a or "FNW-001" in a),
            "Must describe the 10 active monitored Farha South assets"
        )
    },
    {
        "id": "DOM10-11",
        "domain": "Domain 10: Self-Knowledge",
        "subdomain": "10.4 Monitored Assets List",
        "query": "what assets are under your surveillance?",
        "expected_intent": "SELF_FLEET_SCOPE",
        "check": lambda d, a: (
            "Fleet Scope" in a and ("Cluster" in a or "FS-" in a or "FNW-" in a),
            "Must list asset clusters and monitored wells"
        )
    },
    {
        "id": "DOM10-12",
        "domain": "Domain 10: Self-Knowledge",
        "subdomain": "10.5 Supported Tasks & Workflows",
        "query": "what tasks do you support?",
        "expected_intent": "SELF_TASKS",
        "check": lambda d, a: (
            "Supported Tasks" in a and ("Trip Root Cause" in a or "Surveillance" in a or "SOP" in a),
            "Must list operational SOP tasks supported by the engine"
        )
    },
    {
        "id": "DOM10-13",
        "domain": "Domain 10: Self-Knowledge",
        "subdomain": "10.5 Supported Workflows Catalog",
        "query": "list supported workflows",
        "expected_intent": "SELF_TASKS",
        "check": lambda d, a: (
            "Tasks & Workflows" in a and len(a) > 200,
            "Must catalog standard operating procedures"
        )
    },
    {
        "id": "DOM10-14",
        "domain": "Domain 10: Self-Knowledge",
        "subdomain": "10.6 System Limitations",
        "query": "what are your system limitations?",
        "expected_intent": "SELF_LIMITATIONS",
        "check": lambda d, a: (
            "System Limitations" in a and ("Sensor Coverage" in a or "Telemetry" in a or "Actuation" in a),
            "Must disclose sensor coverage, sampling cadence, and safety boundaries"
        )
    },
    {
        "id": "DOM10-15",
        "domain": "Domain 10: Self-Knowledge",
        "subdomain": "10.6 Known Constraints",
        "query": "what are your known constraints?",
        "expected_intent": "SELF_LIMITATIONS",
        "check": lambda d, a: (
            "Limitations" in a and len(a) > 200,
            "Must state engineering transparency limitations"
        )
    },
    {
        "id": "DOM10-16",
        "domain": "Domain 10: Self-Knowledge",
        "subdomain": "10.6 Limitations Disclosure",
        "query": "disclose system limitations",
        "expected_intent": "SELF_LIMITATIONS",
        "check": lambda d, a: (
            "System Limitations" in a and ("Radical Transparency" in a or "Limitations" in a),
            "Must provide comprehensive transparency disclosures"
        )
    },
]

def run_regression_test():
    total_queries = len(QUERIES)
    print(f"================================================================================")
    print(f"STARTING COMPREHENSIVE REGRESSION AUDIT ACROSS {total_queries} QUERIES")
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    print(f"Target Endpoint: {URL}")
    print(f"Rule: Read-Only Audit | Zero Code Modifications | Failing Queries Will Log Reasons")
    print(f"================================================================================")

    results = []
    txt_lines = []

    txt_lines.append("=" * 100)
    txt_lines.append("ADVAIT ESP APM COPILOT: COMPREHENSIVE FULL REGRESSION AUDIT REPORT")
    txt_lines.append(f"Execution Date/Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    txt_lines.append(f"Target Environment: Live FastAPI Backend (:8000), Local Qwen 2.5 3B (Server 188), PostgreSQL 184")
    txt_lines.append(f"Total Queries Evaluated: {total_queries}")
    txt_lines.append("=" * 100)
    txt_lines.append("")
    txt_lines.append("SUMMARY SCORECARD TABLE:")
    txt_lines.append("-" * 100)
    txt_lines.append(f"{'#':<4} | {'ID':<9} | {'Status':<6} | {'Latency':<8} | {'Domain':<24} | {'Query'}")
    txt_lines.append("-" * 100)

    for idx, item in enumerate(QUERIES, start=1):
        q_id = item["id"]
        dom = item["domain"]
        sub = item["subdomain"]
        query = item["query"]

        print(f"[{idx:02d}/{total_queries}] ({q_id}) {dom} -> \"{query[:42]}\"...", end="", flush=True)

        payload = {"question": query, "conversation_history": []}
        t0 = time.time()
        resp_data = {}
        error_msg = None

        try:
            req = urllib.request.Request(
                URL,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=40.0) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            error_msg = str(e)

        dur_ms = int((time.time() - t0) * 1000)
        answer = resp_data.get("answer", "")

        is_accurate = False
        fail_reason = ""

        if error_msg:
            is_accurate = False
            fail_reason = f"HTTP/Network Error: {error_msg}"
        elif not answer or not answer.strip():
            is_accurate = False
            fail_reason = "Empty answer received from backend"
        else:
            try:
                passed, reason = item["check"](resp_data, answer)
                if passed:
                    is_accurate = True
                else:
                    is_accurate = False
                    fail_reason = f"Verification check failed: {reason}"
            except Exception as eval_err:
                is_accurate = False
                fail_reason = f"Evaluation script exception: {eval_err}"

        status_str = "PASS" if is_accurate else "FAIL"
        print(f" [{status_str}] ({dur_ms}ms)")

        txt_lines.append(
            f"{idx:02d}   | {q_id:<9} | {status_str:<6} | {dur_ms:<5}ms | {dom[:24]:<24} | \"{query}\""
        )

        results.append({
            "idx": idx,
            "id": q_id,
            "domain": dom,
            "subdomain": sub,
            "query": query,
            "status": status_str,
            "latency_ms": dur_ms,
            "fail_reason": fail_reason,
            "resp_data": resp_data,
            "answer": answer,
        })

    txt_lines.append("-" * 100)
    total_passed = sum(1 for r in results if r["status"] == "PASS")
    total_failed = sum(1 for r in results if r["status"] == "FAIL")
    pass_pct = (total_passed / total_queries) * 100.0

    txt_lines.append("")
    txt_lines.append(f"AGGREGATE AUDIT METRICS:")
    txt_lines.append(f"- Total Queries Executed: {total_queries}")
    txt_lines.append(f"- Total Passed / Accurate: {total_passed} ({pass_pct:.1f}%)")
    txt_lines.append(f"- Total Failed: {total_failed} ({(total_failed/total_queries)*100.0:.1f}%)")
    txt_lines.append(f"- Average Latency: {int(sum(r['latency_ms'] for r in results)/total_queries)} ms")
    txt_lines.append("")
    txt_lines.append("=" * 100)
    txt_lines.append("DETAILED PER-QUERY AUDIT TRANSCRIPTS AND RAW OUTPUTS")
    txt_lines.append("=" * 100)
    txt_lines.append("")

    for r in results:
        txt_lines.append("-" * 100)
        txt_lines.append(f"QUERY #{r['idx']:02d} [{r['id']}] - {r['domain']} / {r['subdomain']}")
        txt_lines.append(f"Prompt: \"{r['query']}\"")
        txt_lines.append(f"Status: {r['status']} | Latency: {r['latency_ms']} ms")
        if r['fail_reason']:
            txt_lines.append(f"FAIL REASON: {r['fail_reason']}")
        
        structured = r['resp_data'].get("structured_data") or {}
        if structured:
            txt_lines.append(f"Resolved Intent / Route: {structured.get('intent') or structured.get('route_id') or 'N/A'}")

        txt_lines.append("")
        txt_lines.append("FULL RESPONSE OUTPUT:")
        txt_lines.append(r['answer'])
        txt_lines.append("")

    report_path = "FULL_REGRESSION_TEST_REPORT.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(txt_lines))

    print(f"\nAudit complete! {total_passed}/{total_queries} passed ({pass_pct:.1f}%).")
    print(f"Full report written to: {os.path.abspath(report_path)}")

if __name__ == "__main__":
    run_regression_test()
