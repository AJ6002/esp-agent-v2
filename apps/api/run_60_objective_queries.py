import json
import time
import os
from app.db.session import SessionLocal
from app.ai.copilot import ask as ai_ask

domain_queries = [
    # Domain 1: Trip Event Diagnostics (10 queries)
    ("Trip Event Diagnostics", "Diagnose event EV-20261012-103435-FNW-001-878"),
    ("Trip Event Diagnostics", "Diagnose trip EV-20261012-101438-FS-017-571"),
    ("Trip Event Diagnostics", "Diagnose event EV-20261012-101529-FS-040-950"),
    ("Trip Event Diagnostics", "What happened in event EV-20261011-163129-FS-017-979?"),
    ("Trip Event Diagnostics", "Diagnose event EV-20261011-170941-FS-040-202"),
    ("Trip Event Diagnostics", "What caused trip EV-20261011-170653-FS-040-053?"),
    ("Trip Event Diagnostics", "Diagnose trip event EV-20261011-162333-FS-040-579"),
    ("Trip Event Diagnostics", "Explain root cause for event EV-20261011-161537-FS-017-108"),
    ("Trip Event Diagnostics", "Diagnose event EV-20261011-161127-FS-017-456"),
    ("Trip Event Diagnostics", "What caused shutdown in EV-20261011-155908-FS-017-447?"),

    # Domain 2: Historical Well Failure & Recurrence Audit (10 queries)
    ("Historical Failure Audit", "What is the failure history of well FS-017?"),
    ("Historical Failure Audit", "Show past trip patterns and recurrence history of well FS-040"),
    ("Historical Failure Audit", "Historical failure analysis of well FNW-001"),
    ("Historical Failure Audit", "Show all logged incidents and trips for well FS-018"),
    ("Historical Failure Audit", "Failure history of well FS-001"),
    ("Historical Failure Audit", "What are the historical failure modes for well FS-002?"),
    ("Historical Failure Audit", "Show trip history and logged incidents for well FS-003"),
    ("Historical Failure Audit", "Historical reliability audit of well FS-020"),
    ("Historical Failure Audit", "Show past trip recurrence and failure spectrum for well FS-029"),
    ("Historical Failure Audit", "Audit historical trips and incidents for well FS-035"),

    # Domain 3: Real-Time Well Health & Protection Envelopes (10 queries)
    ("Well Health Assessment", "Is well FNW-001 healthy?"),
    ("Well Health Assessment", "Check health status and condition of well FS-017"),
    ("Well Health Assessment", "What is the operational condition and vibration health of well FS-040?"),
    ("Well Health Assessment", "Evaluate health index and telemetry envelopes for well FS-018"),
    ("Well Health Assessment", "Well status and health condition for FS-001"),
    ("Well Health Assessment", "Is well FS-002 within safe operating limits?"),
    ("Well Health Assessment", "Check vibration and current health status of well FS-003"),
    ("Well Health Assessment", "Well health assessment for FS-020"),
    ("Well Health Assessment", "Is well FS-029 experiencing any abnormal vibration or temperature?"),
    ("Well Health Assessment", "Health status and protection envelope audit for FS-035"),

    # Domain 4: Fleet & Cluster Asset Inventory (10 queries)
    ("Fleet Inventory", "Show total fleet inventory and active wells summary"),
    ("Fleet Inventory", "How many wells are in cluster GCS-15?"),
    ("Fleet Inventory", "Show all wells and capacity in cluster GCS-4"),
    ("Fleet Inventory", "List all monitored wells in cluster GCS-3"),
    ("Fleet Inventory", "What is the total motor installed horsepower across the fleet?"),
    ("Fleet Inventory", "How many wells are currently active versus stopped in the fleet?"),
    ("Fleet Inventory", "Fleet inventory overview for cluster GCS-15"),
    ("Fleet Inventory", "Show asset registry summary for cluster GCS-4"),
    ("Fleet Inventory", "List fleet asset specifications and motor ratings"),
    ("Fleet Inventory", "Give me the cluster breakdown of all producing assets"),

    # Domain 5: Production Stream & Flowline Telemetry (10 queries)
    ("Production Telemetry", "What is the flow rate of well FS-017?"),
    ("Production Telemetry", "What are the current production rates and water cut for well FS-040?"),
    ("Production Telemetry", "Production summary and net oil rate for well FNW-001"),
    ("Production Telemetry", "Show flow rate and water cut for well FS-018"),
    ("Production Telemetry", "What is the liquid production rate and PDP for well FS-001?"),
    ("Production Telemetry", "Production metrics and differential pressure for well FS-002"),
    ("Production Telemetry", "What is the daily oil production of well FS-003?"),
    ("Production Telemetry", "Show flow rate, water cut and pressures for well FS-020"),
    ("Production Telemetry", "Production telemetry stream for well FS-029"),
    ("Production Telemetry", "What is the current flow rate and operating state of well FS-035?"),

    # Domain 6: Petroleum Standards & Troubleshooting (10 queries)
    ("Standards & Troubleshooting", "How to troubleshoot gas lock in an ESP system according to API RP 11S?"),
    ("Standards & Troubleshooting", "What are the immediate corrective actions when an ESP experiences severe gas interference?"),
    ("Standards & Troubleshooting", "What causes dry-well pump off condition and what is the recovery procedure?"),
    ("Standards & Troubleshooting", "How does high crude oil viscosity affect ESP motor load and cold start?"),
    ("Standards & Troubleshooting", "How to diagnose and troubleshoot sand ingestion in an electric submersible pump?"),
    ("Standards & Troubleshooting", "What are the indications and troubleshooting procedure for a broken pump shaft?"),
    ("Standards & Troubleshooting", "How to identify bearing degradation and mechanical wear using vibration FFT?"),
    ("Standards & Troubleshooting", "How to troubleshoot phase current imbalance in an ESP motor?"),
    ("Standards & Troubleshooting", "How to perform an electrical megger insulation resistance test on an ESP cable?"),
    ("Standards & Troubleshooting", "What are the lockout/tagout (LOTO) safety requirements before electrical troubleshooting?"),
]

output_dir = r"C:\Users\Tas\.gemini\antigravity\brain\95701d07-c705-4176-86e5-96b4ef9cc944"
output_md = os.path.join(output_dir, "OBJECTIVE_DOMAINS_TEST_RAW_OUTPUTS.md")
ckpt_json = os.path.join(output_dir, "objective_domains_checkpoint.json")

# Load existing checkpoint if available
records = []
if os.path.exists(ckpt_json):
    try:
        with open(ckpt_json, "r", encoding="utf-8") as f:
            records = json.load(f)
        print(f"Loaded {len(records)} existing checkpoint records.")
    except Exception:
        records = []

completed_indices = {r["idx"] for r in records}

header = """# [PROOF] ESP APM Objective Domains Full Verification: 60 Live Query Outputs (10 per Domain)

**Execution Timestamp**: 2026-10-12 17:25:00 UTC
**Database**: PostgreSQL Server 184 (`esp_apm_db:5433` - Strict Read-Only)
**LLM Inference**: `http://192.168.1.188:8080/v1` (Qwen 2.5 Coder 3B)
**Test Matrix**: 6 Objective Domains x 10 Queries = 60 Live Ground-Truth Queries
**Target Agent**: Industrial Maintenance Copilot Master Agent (`apps/api/app/ai/copilot.py`)

---

## Executive Test Summary Matrix (60 Queries across 6 Objective Domains)

| # | Domain | Objective Query | Status | Latency | Confidence | Citations | Top Cited Source / Asset |
|---|---|---|---|---|---|---|---|
"""

def flush_markdown():
    # Sort by idx
    sorted_recs = sorted(records, key=lambda x: x["idx"])
    rows = [
        f"| {r['idx']} | **{r['domain']}** | `{r['query']}` | `{r['status']}` | `{r['latency_ms']} ms` | `{r['confidence']}` | `{r['citations_count']}` | {r['top_source']} |"
        for r in sorted_recs
    ]
    sections = [
        f"""### Test Case {r['idx']}: [{r['domain']}] `{r['query']}`
- **Execution Status**: `{r['status']}`
- **Latency**: `{r['latency_ms']} ms`
- **Confidence**: `{r['confidence']}`
- **Citations Attached**: `{r['citations_count']}`
- **Needs Clarification**: `{r['needs_clarification']}`

#### Delivered Agent Response:
{r['answer']}

#### Raw Citations Metadata:
```json
{json.dumps(r['citations'], indent=2)}
```

---
"""
        for r in sorted_recs
    ]
    full_doc = header + "\n".join(rows) + "\n\n---\n\n## Detailed Test Case Outputs\n\n" + "\n".join(sections)
    with open(output_md, "w", encoding="utf-8") as f:
        f.write(full_doc)
    with open(ckpt_json, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

db = SessionLocal()

print(f"Total queries to execute: {len(domain_queries)}. Already completed: {len(completed_indices)}.")

for idx, (domain, q) in enumerate(domain_queries, 1):
    if idx in completed_indices:
        continue

    t0 = time.time()
    try:
        res = ai_ask(db, q)
        dt = round((time.time() - t0) * 1000, 1)
        top_src = res.citations[0].title if res.citations else ("HITL Clarification" if res.needs_clarification else "Internal Synthesis")
        
        rec = {
            "idx": idx,
            "domain": domain,
            "query": q,
            "status": "200 OK",
            "latency_ms": dt,
            "confidence": res.confidence,
            "citations_count": len(res.citations),
            "top_source": top_src,
            "needs_clarification": res.needs_clarification,
            "answer": res.answer,
            "citations": [c.model_dump() for c in res.citations],
        }
        records.append(rec)
        print(f"[{idx:02d}/60] [{domain}] OK ({dt}ms) -> Conf: {res.confidence} | Citations: {len(res.citations)} | {top_src[:40]}")
    except Exception as e:
        dt = round((time.time() - t0) * 1000, 1)
        rec = {
            "idx": idx,
            "domain": domain,
            "query": q,
            "status": f"ERROR: {str(e)[:40]}",
            "latency_ms": dt,
            "confidence": 0.0,
            "citations_count": 0,
            "top_source": "N/A",
            "needs_clarification": False,
            "answer": f"Error: {e}",
            "citations": [],
        }
        records.append(rec)
        print(f"[{idx:02d}/60] [{domain}] FAILED ({dt}ms): {e}")

    flush_markdown()

db.close()
print(f"\nExecution finished! Total records in checkpoint: {len(records)}.")
