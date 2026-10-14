"""Domain 2 Curl API Test Execution Script.
Executes real curl.exe commands against http://localhost:8000/api/v1/copilot/ask
and generates DOMAIN_2_CURL_API_TEST_RESULTS.txt with complete request/response traces.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time

# Ensure apps/api is in sys.path to obtain authentic security token
sys.path.insert(0, os.path.abspath("apps/api"))
from app.core.security import create_access_token

token = create_access_token(
    subject=1,
    extra={"role": "admin", "name": "Lead Test Engineer"}
)

URL = "http://localhost:8000/api/v1/copilot/ask"

test_cases = [
    {
        "id": "CURL-DOM2-01",
        "capability": "2.1 Well-to-Well Comparison",
        "description": "Side-by-side comparative telemetry and limit envelope across two specific assets",
        "query": "Compare well FS-017 vs FS-040",
    },
    {
        "id": "CURL-DOM2-02",
        "capability": "2.2 Gathering Cluster Comparison",
        "description": "Aggregation and mathematical delta comparison between gathering stations GCS-15 and GCS-4",
        "query": "Compare Cluster 15 vs Cluster 4",
    },
    {
        "id": "CURL-DOM2-03",
        "capability": "2.2 HITL Ambiguous Cluster Disambiguation",
        "description": "Open-ended cluster comparison prompt triggering interactive option selection",
        "query": "Compare the clusters",
    },
    {
        "id": "CURL-DOM2-04",
        "capability": "2.3 Historical Baseline Comparison",
        "description": "Rolling 24-hour current sensor average vs prior baseline window for target well",
        "query": "Show historical baseline comparison for well FS-004",
    },
    {
        "id": "CURL-DOM2-05",
        "capability": "2.4 Cluster Peer Benchmarking",
        "description": "Evaluates target asset against median of all other peer wells in its gathering cluster",
        "query": "Benchmark well FS-017 against its cluster peers",
    },
    {
        "id": "CURL-DOM2-06",
        "capability": "2.5 Before/After Event Telemetry",
        "description": "Sensor delta evaluation 2 hours prior to trip event vs 2 hours post-event",
        "query": "Compare telemetry before and after trip for event EV-20261012-101438-FS-017-571",
    },
    {
        "id": "CURL-DOM2-07",
        "capability": "2.6 Fleet Ranking: Vibration",
        "description": "Objective 10-well vibration leaderboard (#1 to #10) with deviation vs fleet median",
        "query": "Rank wells by vibration",
    },
    {
        "id": "CURL-DOM2-08",
        "capability": "2.6 Fleet Ranking: Production",
        "description": "Objective 10-well gross liquid production leaderboard (#1 to #10)",
        "query": "Top producing wells across the fleet",
    },
    {
        "id": "CURL-DOM2-09",
        "capability": "2.6 Fleet Ranking: Temperature",
        "description": "Objective 10-well motor temperature ranking (#1 to #10)",
        "query": "Rank wells by motor temperature",
    },
    {
        "id": "CURL-DOM2-10",
        "capability": "2.6 Fleet Ranking: Lifetime Trips",
        "description": "Objective 10-well ranking by historical trip frequency from events table",
        "query": "Rank wells by lifetime trips",
    },
    {
        "id": "CURL-DOM2-11",
        "capability": "2.1 HITL Ambiguous Single-Well Compare",
        "description": "Comparative query with single well missing comparison target triggering clarification",
        "query": "Compare well FS-017",
    },
]

output_lines = [
    "=" * 100,
    "ESP APM INDUSTRIAL COPILOT — DOMAIN 2 (FLEET COMPARISON) CURL API TEST REPORT",
    "=" * 100,
    f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}",
    f"Target Endpoint: {URL}",
    f"Data Source: PostgreSQL Server 184 (esp_apm_db) [Read-Only]",
    f"LLM Engine: Local Server 134 (http://192.168.1.134:8080/v1)",
    "=" * 100,
    "",
]

summary_records = []

for idx, tc in enumerate(test_cases, 1):
    print(f"[{idx}/{len(test_cases)}] Executing curl for: {tc['id']} - {tc['capability']}...", flush=True)
    payload = json.dumps({"question": tc["query"]})

    # Write payload to a temporary JSON file to avoid shell escaping issues on Windows
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as tf:
        tf.write(payload)
        temp_payload_path = tf.name

    curl_cmd = [
        "curl.exe",
        "-s",
        "-X", "POST",
        URL,
        "-H", "Content-Type: application/json",
        "-H", f"Authorization: Bearer {token}",
        "-d", f"@{temp_payload_path}",
        "-w", "\n__METRICS__\nHTTP_STATUS:%{http_code}\nTIME_TOTAL:%{time_total}",
    ]

    human_curl_display = (
        f'curl -X POST "{URL}" \\\n'
        f'  -H "Content-Type: application/json" \\\n'
        f'  -H "Authorization: Bearer {token[:16]}...[TRUNCATED_JWT]...{token[-16:]}" \\\n'
        f'  -d \'{payload}\''
    )

    t0 = time.time()
    try:
        proc = subprocess.run(
            curl_cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=45,
        )
        elapsed = time.time() - t0
        raw_output = proc.stdout
        
        # Parse metrics
        http_status = "UNKNOWN"
        time_total = f"{elapsed:.2f}"
        body_content = raw_output

        if "__METRICS__" in raw_output:
            parts = raw_output.split("__METRICS__")
            body_content = parts[0].strip()
            metrics_block = parts[1].strip()
            for line in metrics_block.splitlines():
                if line.startswith("HTTP_STATUS:"):
                    http_status = line.split(":", 1)[1].strip()
                elif line.startswith("TIME_TOTAL:"):
                    time_total = line.split(":", 1)[1].strip()

        # Parse JSON response body
        parsed_json = None
        ans_text = ""
        needs_clar = False
        suggested = []
        try:
            parsed_json = json.loads(body_content)
            ans_text = parsed_json.get("answer", "")
            needs_clar = parsed_json.get("needs_clarification", False)
            suggested = parsed_json.get("suggested_options", [])
        except Exception:
            ans_text = body_content

        status_flag = "PASS" if http_status == "200" and len(ans_text) > 50 else "FAIL"

        summary_records.append({
            "id": tc["id"],
            "capability": tc["capability"],
            "status": status_flag,
            "http_code": http_status,
            "time_total": time_total,
            "response_len": len(ans_text),
        })

        output_lines.extend([
            "-" * 100,
            f"TEST CASE: [{tc['id']}] {tc['capability']}",
            f"Description: {tc['description']}",
            f"Status: {status_flag} | HTTP Code: {http_status} | Elapsed: {time_total}s",
            "-" * 100,
            "CURL COMMAND:",
            human_curl_display,
            "",
            "REQUEST BODY JSON:",
            json.dumps({"question": tc["query"]}, indent=2),
            "",
            f"RESPONSE METADATA:",
            f"- HTTP Status Code: {http_status}",
            f"- Response Latency: {time_total} seconds",
            f"- Needs Clarification: {needs_clar}",
            f"- Suggested Options: {suggested}",
            "",
            "RESPONSE BODY (FULL ANSWER TEXT / MARKDOWN REPORT):",
            ans_text,
            "",
            "RAW JSON RESPONSE (TRUNCATED PREVIEW):",
            json.dumps(parsed_json, indent=2)[:600] + ("\n... [TRUNCATED FOR READABILITY] ..." if parsed_json and len(json.dumps(parsed_json)) > 600 else ""),
            "",
            "",
        ])
        print(f"   -> {status_flag} (HTTP {http_status}) in {time_total}s | Answer length: {len(ans_text)} chars", flush=True)

    except Exception as exc:
        summary_records.append({
            "id": tc["id"],
            "capability": tc["capability"],
            "status": f"ERROR: {exc}",
            "http_code": "ERR",
            "time_total": "0",
            "response_len": 0,
        })
        output_lines.extend([
            "-" * 100,
            f"TEST CASE: [{tc['id']}] {tc['capability']}",
            f"Status: ERROR ({exc})",
            "-" * 100,
            "",
        ])
        print(f"   -> ERROR: {exc}", flush=True)
    finally:
        if os.path.exists(temp_payload_path):
            try:
                os.remove(temp_payload_path)
            except OSError:
                pass

output_lines.extend([
    "=" * 100,
    "DOMAIN 2 CURL API TEST SUMMARY SCORECARD",
    "=" * 100,
    f"{'Test ID':<16} | {'Capability':<38} | {'Status':<6} | {'HTTP':<5} | {'Latency':<8} | {'Length'}",
    "-" * 100,
])

all_passed = True
for sr in summary_records:
    if sr["status"] != "PASS":
        all_passed = False
    output_lines.append(
        f"{sr['id']:<16} | {sr['capability']:<38} | {sr['status']:<6} | {sr['http_code']:<5} | {sr['time_total']}s | {sr['response_len']} chars"
    )

output_lines.extend([
    "=" * 100,
    f"FINAL VERDICT: {'ALL 11/11 DOMAIN 2 CURL API TESTS PASSED (100% SUCCESS RATE)' if all_passed else 'SOME TESTS FAILED'}",
    "=" * 100,
])

report_text = "\n".join(output_lines)
report_path = os.path.abspath("DOMAIN_2_CURL_API_TEST_RESULTS.txt")
with open(report_path, "w", encoding="utf-8") as rf:
    rf.write(report_text)

print(f"\n[DONE] Test report successfully written to: {report_path}", flush=True)
