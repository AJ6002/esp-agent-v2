"""Domain 2 Fleet Comparison Verification Test Suite.
Tests all 6 Domain 2 capabilities + HITL ambiguity triggers + regression checks
against live FastAPI backend connected to PostgreSQL Server 184 and local LLM on Server 134.
"""

from __future__ import annotations

import sys
import os
import json
import time
import urllib.request

sys.path.insert(0, os.path.abspath("apps/api"))
from app.core.security import create_access_token

token = create_access_token(subject=1, extra={"role": "admin", "name": "Lead Test Engineer"})
URL = "http://localhost:8000/api/v1/copilot/ask"

tests = [
    # 1. Capability 2.1: Well-to-Well Comparison
    {
        "id": "DOM2-01",
        "category": "2.1 Well-to-Well Comparison",
        "query": "Compare well FS-017 vs FS-040",
        "check": lambda ans, data: (
            "Comparative Well Analysis" in ans
            and "FS-017" in ans
            and "FS-040" in ans
            and "Operating State" in ans
            and "Motor Current" in ans
            and "Vibration" in ans
        ),
    },

    # 2. Capability 2.2: Cluster Comparison
    {
        "id": "DOM2-02",
        "category": "2.2 Gathering Cluster Comparison",
        "query": "Compare Cluster 15 vs Cluster 4",
        "check": lambda ans, data: (
            "Gathering Cluster Comparison" in ans
            and "Cluster 15" in ans
            and "Cluster 4" in ans
            and "Active Availability" in ans
            and "Gross Liquid Output" in ans
            and "Delta" in ans
        ),
    },

    # 3. Capability 2.2 HITL: Ambiguous Cluster Comparison
    {
        "id": "DOM2-03",
        "category": "2.2 HITL: Ambiguous Cluster Prompt",
        "query": "Compare the clusters",
        "check": lambda ans, data: (
            data.get("needs_clarification") is True
            and any("Cluster 15" in opt for opt in data.get("suggested_options", []))
        ),
    },

    # 4. Capability 2.3: Historical Baseline Comparison
    {
        "id": "DOM2-04",
        "category": "2.3 Historical Baseline Comparison",
        "query": "Show historical baseline comparison for well FS-004",
        "check": lambda ans, data: (
            "Historical Baseline Comparison" in ans
            and "FS-004" in ans
            and "Current (24h Avg)" in ans
            and "Baseline" in ans
            and "Absolute Delta" in ans
        ),
    },

    # 5. Capability 2.4: Peer Benchmarking
    {
        "id": "DOM2-05",
        "category": "2.4 Cluster Peer Benchmarking",
        "query": "Benchmark well FS-017 against its cluster peers",
        "check": lambda ans, data: (
            "Cluster Peer Benchmark" in ans
            and "FS-017" in ans
            and "Peer Group Median" in ans
            and "Deviation vs Peers" in ans
            and ("ELEVATED" in ans or "NOMINAL" in ans or "SUB-NOMINAL" in ans)
        ),
    },

    # 6. Capability 2.5: Before / After Event Comparison
    {
        "id": "DOM2-06",
        "category": "2.5 Before/After Event Telemetry",
        "query": "Compare telemetry before and after trip for event EV-20261012-101438-FS-017-571",
        "check": lambda ans, data: (
            "Event Telemetry Comparison" in ans
            and "EV-20261012-101438-FS-017-571" in ans
            and "Pre-Event (2h" in ans
            and "Post-Event" in ans
            and "Delta" in ans
        ),
    },

    # 7. Capability 2.6: Fleet Ranking by Vibration
    {
        "id": "DOM2-07",
        "category": "2.6 Fleet Ranking (Vibration)",
        "query": "Rank wells by vibration",
        "check": lambda ans, data: (
            "Fleet Ranking: Vibration" in ans
            and "Fleet Median" in ans
            and "#1" in ans
            and "#10" in ans
            and "Deviation vs Median" in ans
        ),
    },

    # 8. Capability 2.6: Fleet Ranking by Production
    {
        "id": "DOM2-08",
        "category": "2.6 Fleet Ranking (Production)",
        "query": "Top producing wells across the fleet",
        "check": lambda ans, data: (
            "Fleet Ranking: Gross Liquid Rate" in ans
            and "BPD" in ans
            and "#1" in ans
            and "Deviation vs Median" in ans
        ),
    },

    # 9. Ambiguity HITL: Single Well Comparison
    {
        "id": "DOM2-09",
        "category": "2.1 HITL: Ambiguous Single-Well Compare",
        "query": "Compare well FS-017",
        "check": lambda ans, data: (
            data.get("needs_clarification") is True
            and len(data.get("suggested_options", [])) > 0
        ),
    },

    # 10. Regression: Event Diagnosis
    {
        "id": "REG-01",
        "category": "Regression: Event Diagnosis",
        "query": "Diagnose event EV-20261012-103435-FNW-001-878",
        "check": lambda ans, data: "Event Root Cause Diagnosis" in ans and "FNW-001" in ans,
    },

    # 11. Regression: Domain 1 Fleet Production
    {
        "id": "REG-02",
        "category": "Regression: Domain 1 Fleet Production",
        "query": "Show total fleet production and deferred oil loss across clusters",
        "check": lambda ans, data: "Fleet Production & Deferment" in ans and "BOPD" in ans,
    },

    # 12. Regression: Domain 1 Fleet Triage
    {
        "id": "REG-03",
        "category": "Regression: Domain 1 Fleet Triage",
        "query": "Fleet triage: rank offline wells by severity and intervention urgency",
        "check": lambda ans, data: "Fleet Operational Triage" in ans and "IMMEDIATE_LOTO" in ans,
    },

    # 13. Regression: HITL Operational Clarification
    {
        "id": "REG-04",
        "category": "Regression: Ambiguous Pump Stop Clarification",
        "query": "Why did the pump stop?",
        "check": lambda ans, data: data.get("needs_clarification") is True,
    },
]

print("=" * 90, flush=True)
print("STARTING DOMAIN 2 FLEET COMPARISON VERIFICATION SUITE", flush=True)
print("TARGET: FastAPI Backend (http://localhost:8000/api/v1/copilot/ask)", flush=True)
print("=" * 90, flush=True)

results = []
all_passed = True

for t in tests:
    print(f"\n[{t['id']}] {t['category']}", flush=True)
    print(f"Query: \"{t['query']}\"", flush=True)
    t0 = time.time()
    try:
        payload = json.dumps({"question": t["query"]}).encode("utf-8")
        req = urllib.request.Request(
            URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            }
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            elapsed = time.time() - t0
            data = json.loads(resp.read().decode("utf-8"))
            ans = data.get("answer", "")
            passed = t["check"](ans, data)
            
            status_str = "PASS" if passed else "FAIL"
            if not passed:
                all_passed = False
            
            results.append({
                "id": t["id"],
                "category": t["category"],
                "status": status_str,
                "elapsed": round(elapsed, 2),
                "answer_len": len(ans),
                "preview": ans[:140].replace("\n", " "),
            })
            print(f"-> Result: {status_str} in {elapsed:.2f}s | Length: {len(ans)} chars", flush=True)
            print(f"-> Preview: {ans[:140].replace(chr(10), ' ')}...", flush=True)
    except Exception as e:
        all_passed = False
        print(f"-> Result: ERROR ({e})", flush=True)
        results.append({
            "id": t["id"],
            "category": t["category"],
            "status": f"ERROR: {e}",
            "elapsed": round(time.time() - t0, 2),
            "answer_len": 0,
            "preview": "N/A",
        })

print("\n" + "=" * 90, flush=True)
print("DOMAIN 2 VERIFICATION SUMMARY SCORECARD", flush=True)
print("=" * 90, flush=True)
for r in results:
    print(f"[{r['id']}] {r['category']:<45} | {r['status']:<6} | {r['elapsed']}s | {r['answer_len']} chars", flush=True)
print("=" * 90, flush=True)

if all_passed:
    print("ALL TESTS PASSED PERFECTLY (100% SUCCESS RATE)!", flush=True)
else:
    print("SOME TESTS FAILED! REVIEW OUTPUT ABOVE.", flush=True)
