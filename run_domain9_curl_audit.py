"""Audit runner for Domain 9: UI / Navigation Awareness."""

import urllib.request
import urllib.parse
import json
import time
from datetime import datetime

QUERIES = [
    # 1. Primary Routes
    ("9.1 Route", "what is the Working Status page?"),
    ("9.1 Route", "explain the Working Status screen"),
    ("9.1 Route", "what is the Fleet Cockpit page?"),
    ("9.1 Route", "where is the fleet cockpit?"),
    ("9.1 Route", "what is the Well Monitor screen?"),
    ("9.1 Route", "explain the single well monitor screen"),
    ("9.1 Route", "what is the Live Calculations page?"),
    ("9.1 Route", "how do I navigate to live calculations?"),
    ("9.1 Route", "what is the Event Intelligence page?"),
    ("9.1 Route", "where do I find trip forensics?"),
    ("9.1 Route", "what is the Reports Hub page?"),
    ("9.1 Route", "where are operational reports?"),
    ("9.1 Route", "what is the Scenario Simulator page?"),
    ("9.1 Route", "how do I get to custom testing bench?"),
    ("9.1 Navigation", "show all screens in operations workspace"),
    ("9.1 Navigation", "list all available routes"),

    # 2. Components
    ("9.2 Component", "where can I find the 2D ESP string visualizer?"),
    ("9.2 Component", "what does the 4-subsystem equalizer display?"),
    ("9.2 Component", "where are live pump performance curves?"),
    ("9.2 Component", "what does the FleetTable display?"),
    ("9.2 Component", "where is the Top KPI strip located?"),
    ("9.2 Component", "what displays in the Working Status diagnostic queue?"),
    ("9.2 Component", "what is the Fleet KPI Formulas Editor?"),
    ("9.2 Component", "where can I find the Scenario Configuration Bench?"),

    # 3. Concepts
    ("9.3 Concept", "what is the 14-fault classifier spectrum?"),
    ("9.3 Concept", "what is virtual flow metering (VFM)?"),
    ("9.3 Concept", "what are affinity laws in the platform?"),
    ("9.3 Concept", "what is the zero fabrication data readiness gate?"),
    ("9.3 Concept", "what is the recommended operating range (ROR)?"),

    # 4. Parametric Entity Binding
    ("9.4 Parametric Binding", "where can I find pump curves for FS-017?"),
    ("9.4 Parametric Binding", "show well detail for FNW-001"),

    # 5. Out of Scope / Missing
    ("9.5 Out of Scope", "where is the pizza ordering screen?"),
    ("9.5 Out of Scope", "what is the 3D seismic voxel viewer page?"),
]

BASE_URL = "http://127.0.0.1:8000/api/v1"

def run_audit():
    print(f"Starting Domain 9 cURL Audit across {len(QUERIES)} queries...")
    results = []

    md_lines = [
        "# Domain 9: UI / Navigation / Route Awareness Raw cURL Audit Log",
        "",
        f"**Audit Execution Time**: {datetime.utcnow().isoformat()}Z  ",
        "**Target Environment**: FastAPI Backend (`:8000`), Qwen 2.5 Coder 3B (`Server 188`)  ",
        f"**Total Queries Evaluated**: {len(QUERIES)}  ",
        "",
        "---",
        "",
        "## Summary Matrix",
        "",
        "| # | Category | Query | Intent | Route ID | Path / Status | End Tag Verified |",
        "|:---:|---|---|:---:|:---:|:---:|:---:|",
    ]

    for idx, (cat, q) in enumerate(QUERIES, start=1):
        # 1. Query route-intent
        intent_url = f"{BASE_URL}/esp/route-intent?question={urllib.parse.quote(q)}"
        intent_data = {}
        try:
            req = urllib.request.Request(intent_url)
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                intent_data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            intent_data = {"error": str(e)}

        # 2. Query /api/v1/esp/ask
        ask_url = f"{BASE_URL}/esp/ask"
        ask_payload = {
            "question": q,
            "conversation_history": []
        }
        ask_data = {}
        t0 = time.time()
        try:
            req = urllib.request.Request(
                ask_url,
                data=json.dumps(ask_payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=15.0) as resp:
                ask_data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            ask_data = {"error": str(e)}
        dur_ms = int((time.time() - t0) * 1000)

        structured = ask_data.get("structured_data") or {}
        route_id = structured.get("route_id") or intent_data.get("entity") or "-"
        resolved_path = structured.get("resolved_path") or "-"
        answer_text = ask_data.get("answer", "")
        end_tag_ok = "YES" if (answer_text.strip().endswith("]") or "That's not documented" in answer_text) else "NO"

        md_lines.append(
            f"| **{idx:02d}** | {cat} | *\"{q}\"* | `{intent_data.get('intent', 'ERR')}` | `{route_id}` | `{resolved_path}` | `{end_tag_ok}` |"
        )

        results.append({
            "idx": idx,
            "category": cat,
            "query": q,
            "intent_data": intent_data,
            "ask_data": ask_data,
            "latency_ms": dur_ms,
        })
        print(f"[{idx:02d}/{len(QUERIES)}] {q[:38]:<40} -> {intent_data.get('intent')} ({dur_ms}ms)")

    md_lines.extend([
        "",
        "---",
        "",
        "## Detailed Raw API Requests & Responses",
        "",
    ])

    for r in results:
        q = r["query"]
        ask = r["ask_data"]
        intent = r["intent_data"]
        md_lines.extend([
            f"### Query #{r['idx']:02d}: {q}",
            f"**Category**: `{r['category']}` | **Latency**: `{r['latency_ms']}ms`",
            "",
            "#### 1. Route Intent Preview (`GET /api/esp/route-intent`)",
            "```json",
            json.dumps(intent, indent=2),
            "```",
            "",
            "#### 2. Copilot Ask Request (`POST /api/esp/ask`)",
            "```bash",
            f"curl -X POST \"{BASE_URL}/esp/ask\" \\",
            "  -H \"Content-Type: application/json\" \\",
            f"  -d '{json.dumps({'question': q})}'",
            "```",
            "",
            "#### 3. Raw Response Payload",
            "```json",
            json.dumps(ask, indent=2),
            "```",
            "",
            "#### 4. Rendered Markdown Narrative",
            "> " + ask.get("answer", "").replace("\n", "\n> "),
            "",
            "---",
            "",
        ])

    with open("DOMAIN_9_CURL_RAW_RESPONSES.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print("\nAudit completed! Written to DOMAIN_9_CURL_RAW_RESPONSES.md")


if __name__ == "__main__":
    run_audit()
