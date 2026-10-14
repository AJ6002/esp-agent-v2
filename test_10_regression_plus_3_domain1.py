"""Comprehensive Verification Test Suite:
- 10 Earlier Implementation Regression Queries
- 3 Domain 1 Wrapping-Up Queries
Executed against FastAPI Backend (http://localhost:8000)
"""

import sys
import os
import urllib.request
import json
import time

sys.path.insert(0, os.path.abspath("apps/api"))
from app.core.security import create_access_token

token = create_access_token(subject=1, extra={"role": "admin", "name": "Lead Test Engineer"})
URL = "http://localhost:8000/api/v1/copilot/ask"

tests = [
    # --- 10 Regression Queries ---
    {
        "id": "REG-01",
        "category": "Event Diagnosis (by Event ID)",
        "query": "Diagnose event EV-20261012-103435-FNW-001-878",
        "expected_intent": "EVENT_DIAGNOSE",
        "check": lambda ans, data: "FNW-001" in ans and ("HIGH_VIBRATION" in ans or "bearing" in ans.lower() or "vibration" in ans.lower()),
    },
    {
        "id": "REG-02",
        "category": "Event Diagnosis (by Well ID)",
        "query": "Why did well FS-017 trip?",
        "expected_intent": "EVENT_DIAGNOSE",
        "check": lambda ans, data: "FS-017" in ans and ("OVERLOAD" in ans or "solids" in ans.lower() or "sand" in ans.lower()),
    },
    {
        "id": "REG-03",
        "category": "Well Health Assessment",
        "query": "Is well FNW-001 healthy? What is its current condition?",
        "expected_intent": "WELL_HEALTH",
        "check": lambda ans, data: "FNW-001" in ans and ("Health Index" in ans or "health" in ans.lower()),
    },
    {
        "id": "REG-04",
        "category": "Well Failure History (Temporal Window)",
        "query": "Show failure history of well FS-017 in the last 7 days",
        "expected_intent": "WELL_HISTORY",
        "check": lambda ans, data: "FS-017" in ans and ("Historical" in ans or "trip" in ans.lower() or "events" in ans.lower()),
    },
    {
        "id": "REG-05",
        "category": "Multi-Well Comparison",
        "query": "Compare well FS-017 vs FS-040",
        "expected_intent": "MULTI_WELL_COMPARE",
        "check": lambda ans, data: "FS-017" in ans and "FS-040" in ans and "|" in ans,
    },
    {
        "id": "REG-06",
        "category": "Well Production Metrics",
        "query": "What is the current flow rate and water cut of well FS-004?",
        "expected_intent": "PRODUCTION",
        "check": lambda ans, data: "FS-004" in ans and ("BPD" in ans or "Water Cut" in ans or "Liquid Rate" in ans),
    },
    {
        "id": "REG-07",
        "category": "Petroleum Engineering Standards RAG",
        "query": "What causes gas locking in an ESP and how to prevent it?",
        "expected_intent": "KNOWLEDGE",
        "check": lambda ans, data: len(ans) > 100 and ("gas" in ans.lower() or "esp" in ans.lower()),
    },
    {
        "id": "REG-08",
        "category": "HITL Operational Clarification",
        "query": "Why did the pump stop?",
        "expected_intent": "EVENT_DIAGNOSE",
        "check": lambda ans, data: data.get("needs_clarification") is True and len(data.get("suggested_options", [])) > 0,
    },
    {
        "id": "REG-09",
        "category": "Dynamic Conversational Chit-Chat",
        "query": "Hello, how are things going today?",
        "expected_intent": "CHAT",
        "check": lambda ans, data: len(ans) > 20 and not ans.startswith("# [ESP APM]"),
    },
    {
        "id": "REG-10",
        "category": "Emergency Work Order Dispatch",
        "query": "Create an emergency work order to dispatch maintenance for well FNW-001",
        "expected_intent": "WORK_ORDER_DISPATCH",
        "check": lambda ans, data: "Work Order" in ans and "LOTO" in ans,
    },

    # --- 3 Domain 1 Wrapping-Up Queries ---
    {
        "id": "DOM1-01",
        "category": "1.3 Fleet Production & Deferment Summary",
        "query": "Show total fleet production and deferred oil loss across clusters",
        "expected_intent": "FLEET_PRODUCTION",
        "check": lambda ans, data: "Fleet Production" in ans and "BOPD" in ans and "Deferred" in ans,
    },
    {
        "id": "DOM1-02",
        "category": "1.4 Fleet Operational Triage & Priority",
        "query": "Fleet triage: rank offline wells by severity and intervention urgency",
        "expected_intent": "FLEET_TRIAGE",
        "check": lambda ans, data: "Fleet Operational Triage" in ans and "IMMEDIATE_LOTO" in ans,
    },
    {
        "id": "DOM1-03",
        "category": "1.6 Fleet Anomaly Early Warning (Verified Active Assets)",
        "query": "Which wells are anomalous right now? Show fleet sub-trip drift",
        "expected_intent": "FLEET_ANOMALY",
        "check": lambda ans, data: "Fleet Anomaly" in ans and ("Active Running Wells Audited: 4" in ans or "4 Assets" in ans),
    },
]

print("=" * 90, flush=True)
print("STARTING 10 REGRESSION + 3 DOMAIN 1 VERIFICATION SUITE", flush=True)
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
            "elapsed": 0,
            "answer_len": 0,
            "preview": "",
        })

print("\n" + "=" * 90)
print("TEST SUMMARY SCORECARD")
print("=" * 90)
for r in results:
    print(f"[{r['id']}] {r['category']:<45} | {r['status']:<6} | {r['elapsed']}s | {r['answer_len']} chars")

print("=" * 90)
if all_passed:
    print("ALL 13/13 TESTS PASSED PERFECTLY (100% SUCCESS RATE)!")
else:
    print("SOME TESTS FAILED! REVIEW ABOVE LOG.")
    sys.exit(1)
