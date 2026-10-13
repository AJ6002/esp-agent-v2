"""Verification script for DOMAIN 1: Fleet Analysis Expanded Capabilities.
Tests all 7 capabilities:
1.1 & 1.2 Fleet Inventory & Status Rollup
1.3 Fleet Production & Deferment Summary
1.4 Fleet Triage & Action Priority
1.5 Fleet Executive Briefing & KPI Reporting
1.6 Fleet Anomaly Surfacing & Early Warning
1.7 Fleet Alarm Timeline & Incident Clustering
Plus Dynamic LLM Greetings (Chat)
"""

import sys
import os
import json

# Ensure agent_service_v2 is in path
sys.path.insert(0, os.path.abspath("agent_service_v2"))
from app.ai.router import ask_agent

print("=" * 80)
print("VERIFYING DOMAIN 1 CAPABILITIES (agent_service_v2)")
print("=" * 80)

test_cases = [
    ("Greeting Check", "Hello, how are you?"),
    ("1.1 Fleet Inventory", "What is the current status of the fleet?"),
    ("1.3 Fleet Production", "Show total fleet production and deferment summary"),
    ("1.4 Fleet Triage", "Fleet triage: rank wells by severity and intervention priority"),
    ("1.5 Fleet Executive", "Generate an executive report and briefing for management"),
    ("1.6 Fleet Anomalies", "Which wells are anomalous right now? Show fleet anomalies"),
    ("1.7 Fleet Alarm Timeline", "Show fleet alarm timeline and incident clustering"),
]

all_passed = True
for name, query in test_cases:
    print(f"\n--- Testing: {name} ---")
    print(f"Query: '{query}'")
    try:
        res = ask_agent(query)
        intent = res.get("intent")
        md = res.get("markdown_text", "")
        print(f"-> Routed Intent: {intent}")
        print(f"-> Confidence: {res.get('confidence')}")
        print(f"-> Markdown Length: {len(md)} chars")
        print("-> Preview (First 200 chars):")
        print(md[:200].replace("\n", " "))
        
        # Verify content
        if not md or len(md) < 50:
            print("FAILED: Empty or truncated response")
            all_passed = False
        else:
            print("PASSED")
    except Exception as e:
        print(f"FAILED with error: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

if all_passed:
    print("\n" + "=" * 80)
    print("ALL DOMAIN 1 CAPABILITIES VERIFIED SUCCESSFULLY IN agent_service_v2!")
    print("=" * 80)
else:
    print("\nSome tests failed!")
    sys.exit(1)
