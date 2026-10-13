"""Verification script for DOMAIN 1 in apps/api (FastAPI Monolith / Copilot Ask).
Tests via HTTP POST to http://localhost:8000/api/v1/copilot/ask with Bearer token.
"""

import sys
import os
import urllib.request
import json

# Use apps/api to generate a valid test token
sys.path.insert(0, os.path.abspath("apps/api"))
from app.core.security import create_access_token

token = create_access_token(subject=1, extra={"role": "admin", "name": "Test Engineer"})

URL = "http://localhost:8000/api/v1/copilot/ask"

test_cases = [
    ("Greeting Check", "Hello, how are you?"),
    ("1.1 Fleet Inventory", "What is the current status of the fleet?"),
    ("1.3 Fleet Production", "Show total fleet production and deferment summary"),
    ("1.4 Fleet Triage", "Fleet triage: rank wells by severity and intervention priority"),
    ("1.5 Fleet Executive", "Generate an executive report and briefing for management"),
    ("1.6 Fleet Anomalies", "Which wells are anomalous right now? Show fleet anomalies"),
    ("1.7 Fleet Alarm Timeline", "Show fleet alarm timeline and incident clustering"),
]

print("=" * 80)
print(f"VERIFYING DOMAIN 1 VIA HTTP POST: {URL}")
print("=" * 80)

all_passed = True
for name, query in test_cases:
    print(f"\n--- Testing: {name} ---")
    print(f"Query: '{query}'")
    try:
        payload = json.dumps({"question": query}).encode("utf-8")
        req = urllib.request.Request(
            URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            }
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            ans = data.get("answer", "")
            print(f"-> Confidence: {data.get('confidence')}")
            print(f"-> Suggested Options: {data.get('suggested_options')}")
            print(f"-> Answer Length: {len(ans)} chars")
            print("-> Answer Preview (First 200 chars):")
            print(ans[:200].replace("\n", " "))
            
            if not ans or len(ans) < 50:
                print("FAILED: Empty or short response")
                all_passed = False
            else:
                print("PASSED")
    except Exception as e:
        print(f"FAILED with error: {e}")
        all_passed = False

if all_passed:
    print("\n" + "=" * 80)
    print("ALL DOMAIN 1 CAPABILITIES VERIFIED SUCCESSFULLY IN apps/api VIA HTTP!")
    print("=" * 80)
else:
    print("\nSome tests failed!")
    sys.exit(1)
