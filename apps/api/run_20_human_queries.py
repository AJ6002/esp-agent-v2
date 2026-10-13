import json
import time
import os
import sys
from app.db.session import SessionLocal
from app.ai.copilot import ask as ai_ask

# 20 Mixed Real-World Human Queries:
# 1-5: Naive / Beginner queries
# 6-10: Typos & Grammatical errors
# 11-15: Field Operator jargon & shorthand
# 16-20: Complex multi-parameter & operational constraints

mixed_human_queries = [
    # Category 1: Naive / Beginner Inquiries (5 queries)
    {
        "idx": 1,
        "category": "Naive / Beginner Inquiries",
        "query": "why did pump stop?",
        "intent_expectation": "Tier 0.E HITL Clarification (Missing asset context)",
    },
    {
        "idx": 2,
        "category": "Naive / Beginner Inquiries",
        "query": "is well 17 bad?",
        "intent_expectation": "Informal asset syntax ('well 17' without prefix)",
    },
    {
        "idx": 3,
        "category": "Naive / Beginner Inquiries",
        "query": "what mean pip and pdp in esp",
        "intent_expectation": "Knowledge Base RAG (Acronym definition & physics role)",
    },
    {
        "idx": 4,
        "category": "Naive / Beginner Inquiries",
        "query": "how do i know if motor is burn",
        "intent_expectation": "Knowledge Base RAG (Colloquial motor burn / insulation failure)",
    },
    {
        "idx": 5,
        "category": "Naive / Beginner Inquiries",
        "query": "can esp run when no oil in well?",
        "intent_expectation": "Knowledge Base RAG (Colloquial dry-well / pump-off condition)",
    },

    # Category 2: Typos & Grammatical Errors (5 queries)
    {
        "idx": 6,
        "category": "Typos & Grammatical Errors",
        "query": "diafnose event EV-20261012-101438-FS-017-571 plz",
        "intent_expectation": "Event Diagnosis (Typo in 'diafnose', trailing slang 'plz')",
    },
    {
        "idx": 7,
        "category": "Typos & Grammatical Errors",
        "query": "chk helth and vibraiton for wel FS-040",
        "intent_expectation": "Well Health (Typos: 'chk', 'helth', 'vibraiton', 'wel')",
    },
    {
        "idx": 8,
        "category": "Typos & Grammatical Errors",
        "query": "whut caused the shutdonw of FS-017 yestarday",
        "intent_expectation": "Historical/Event Diagnosis (Typos: 'whut', 'shutdonw', 'yestarday')",
    },
    {
        "idx": 9,
        "category": "Typos & Grammatical Errors",
        "query": "how to fix gas lok in esp acording to api standard",
        "intent_expectation": "Knowledge Base RAG (Typos: 'lok', 'acording')",
    },
    {
        "idx": 10,
        "category": "Typos & Grammatical Errors",
        "query": "how much bbls per day fs018 make right nw",
        "intent_expectation": "Production Telemetry (Missing hyphen 'fs018', slang 'right nw')",
    },

    # Category 3: Field Operator Jargon & Shorthand (5 queries)
    {
        "idx": 11,
        "category": "Field Operator Jargon & Shorthand",
        "query": "FS-017 tripped on ol solids check loto and megger readings",
        "intent_expectation": "Event Diagnosis & SOP (Operator jargon: 'ol solids', 'loto', 'megger')",
    },
    {
        "idx": 12,
        "category": "Field Operator Jargon & Shorthand",
        "query": "show me gcs-15 total bpd and active well count",
        "intent_expectation": "Fleet Inventory & Cluster Rollup (Shorthand: 'gcs-15', 'bpd')",
    },
    {
        "idx": 13,
        "category": "Field Operator Jargon & Shorthand",
        "query": "check f-nw-001 drive frequency and motor amp draw",
        "intent_expectation": "Well Telemetry/Health (Nonstandard hyphenation 'f-nw-001')",
    },
    {
        "idx": 14,
        "category": "Field Operator Jargon & Shorthand",
        "query": "run historical reliability check on well fs_020 past failures",
        "intent_expectation": "Historical Failure Audit (Underscore well ID 'fs_020')",
    },
    {
        "idx": 15,
        "category": "Field Operator Jargon & Shorthand",
        "query": "what is the baseline amp and temp envelope for well FS040",
        "intent_expectation": "Well Health Baseline Envelope (No-hyphen asset 'FS040')",
    },

    # Category 4: Complex Operational & Threshold Queries (5 queries)
    {
        "idx": 16,
        "category": "Complex Operational Queries",
        "query": "FS-017 tripped with Vx > 3.0g and PDP collapse under 500 psi what is the mechanical root cause?",
        "intent_expectation": "Physics/Event Root Cause (Threshold inequalities: 'Vx > 3.0g', 'under 500 psi')",
    },
    {
        "idx": 17,
        "category": "Complex Operational Queries",
        "query": "For well FS-040 if motor temp reaches 125C while running at 55Hz is it approaching insulation thermal limit?",
        "intent_expectation": "Thermal Limit Assessment (Multi-condition: '125C', '55Hz', insulation limit)",
    },
    {
        "idx": 18,
        "category": "Complex Operational Queries",
        "query": "Diagnose latest trip on well FS-017 and provide step-by-step restart procedure with mandatory electrical checks",
        "intent_expectation": "Comprehensive Diagnostic & Restart SOP (Trip diagnosis + step-by-step signoffs)",
    },
    {
        "idx": 19,
        "category": "Complex Operational Queries",
        "query": "Well FS-029 is showing erratic motor current fluctuating +/- 6A with low PIP is this gas interference or pump off?",
        "intent_expectation": "Differential Diagnosis RAG (Discriminating gas lock vs dry well pump-off)",
    },
    {
        "idx": 20,
        "category": "Complex Operational Queries",
        "query": "Explain lockout tagout LOTO sequence and 1000V megger phase-to-ground test before pulling well FS-040",
        "intent_expectation": "Mandatory Safety Procedure & Workover Governance (LOTO + Megger threshold)",
    },
]

output_dir = r"C:\Users\Tas\.gemini\antigravity\brain\95701d07-c705-4176-86e5-96b4ef9cc944"
output_md = os.path.join(output_dir, "HUMAN_QUERIES_VERIFICATION_REPORT.md")
ckpt_json = os.path.join(output_dir, "human_queries_checkpoint.json")

records = []
if os.path.exists(ckpt_json):
    try:
        with open(ckpt_json, "r", encoding="utf-8") as f:
            records = json.load(f)
        print(f"Loaded {len(records)} existing checkpoint records.")
    except Exception:
        records = []

completed_indices = {r["idx"] for r in records}

header = """# [VERIFICATION REPORT] Real-World Human & Operator Queries Robustness Audit

**Test Execution Date**: 2026-10-12
**Database**: PostgreSQL Server 184 (`esp_apm_db:5433` - Strict Read-Only)
**Local LLM**: Qwen 2.5 Coder 3B (`http://192.168.1.188:8080/v1`)
**Target System**: Industrial Maintenance Copilot Master Agent (`apps/api/app/ai/copilot.py`)
**Evaluation Standard**: `/verified-code-practices` (Zero False Passes, Verifiable Empirical Data)

---

## 1. Executive Summary & Objective

In practical industrial operations, field technicians and petroleum engineers rarely submit syntactically pristine queries. Real-world operator interactions are characterized by:
1. **Grammatical errors, typos, and shorthand** (e.g. typing on rugged field tablets or mobile devices).
2. **Naive / informal inquiries** (vague questions without asset identifiers or colloquial terminology).
3. **Field acronyms and operator slang** (e.g. `LOTO`, `megger`, `bpd`, `bbls`, `ol solids`).
4. **Complex multi-parameter operational prompts** (sensor thresholds like `Vx > 3.0g`, differential diagnostic comparisons, electrical safety constraints).

This audit rigorously evaluates the Master Agent across **20 mixed real-world queries** distributed across these 4 distinct operational categories.

---

## 2. Test Execution Matrix (20 Live Ground-Truth Queries)

| # | Category | Human / Operator Query | Status | Latency | Confidence | Citations | Clarification Triggered | Primary Handled Route |
|---|---|---|---|---|---|---|---|---|
"""

def flush_markdown():
    sorted_recs = sorted(records, key=lambda x: x["idx"])
    rows = [
        f"| {r['idx']} | **{r['category']}** | `{r['query']}` | `{r['status']}` | `{r['latency_ms']} ms` | `{r['confidence']}` | `{r['citations_count']}` | `{'YES (HITL)' if r['needs_clarification'] else 'NO'}` | {r['top_source']} |"
        for r in sorted_recs
    ]
    sections = [
        f"""### Test Case {r['idx']}: [{r['category']}]
- **Operator Query**: `{r['query']}`
- **Expected Operational Behavior**: {r['intent_expectation']}
- **Actual Status**: `{r['status']}`
- **Latency**: `{r['latency_ms']} ms`
- **Confidence Score**: `{r['confidence']}`
- **Citations Attached**: `{r['citations_count']}`
- **HITL Clarification Triggered**: `{r['needs_clarification']}`
- **Top Source / Handled Entity**: {r['top_source']}

#### Verbatim Agent Response:
{r['answer']}

#### Citation JSON Metadata:
```json
{json.dumps(r['citations'], indent=2)}
```

---
"""
        for r in sorted_recs
    ]
    full_doc = header + "\n".join(rows) + "\n\n---\n\n## 3. Detailed Raw Test Case Outputs\n\n" + "\n".join(sections)
    with open(output_md, "w", encoding="utf-8") as f:
        f.write(full_doc)
    with open(ckpt_json, "w", encoding="utf-8") as f:
        json.dump(sorted_recs, f, indent=2)

print(f"Beginning 20 human-like queries execution. Total: {len(mixed_human_queries)}. Completed: {len(completed_indices)}.")

db = SessionLocal()

for item in mixed_human_queries:
    idx = item["idx"]
    category = item["category"]
    q = item["query"]
    expectation = item["intent_expectation"]

    if idx in completed_indices:
        continue

    t0 = time.time()
    try:
        res = ai_ask(db, q)
        dt = round((time.time() - t0) * 1000, 1)
        top_src = res.citations[0].title if res.citations else ("HITL Clarification Required" if res.needs_clarification else "Internal Synthesis")

        rec = {
            "idx": idx,
            "category": category,
            "query": q,
            "intent_expectation": expectation,
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
        print(f"[{idx:02d}/20] [{category}] OK ({dt}ms) -> Conf: {res.confidence} | Clarify: {res.needs_clarification} | {top_src[:45]}")
    except Exception as e:
        dt = round((time.time() - t0) * 1000, 1)
        rec = {
            "idx": idx,
            "category": category,
            "query": q,
            "intent_expectation": expectation,
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
        print(f"[{idx:02d}/20] [{category}] FAILED ({dt}ms): {e}")

    flush_markdown()

db.close()
print(f"\nExecution finished! All {len(records)} test cases executed and documented.")
