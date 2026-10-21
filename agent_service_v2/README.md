# ESP APM Agent Service V2

**Standalone Industrial Diagnostic Microservice for Electric Submersible Pump (ESP) Artificial Lift & Asset Performance Management (APM).**

`agent_service_v2` is a lightweight, decoupled FastAPI microservice designed to run independently from the monolithic backend. It connects directly to live SCADA telemetry, runs deterministic physics algorithms, evaluates equipment envelopes, queries API RP 11S petroleum standards, and streams Explainable AI (XAI) diagnostic reports over Newline-Delimited JSON (NDJSON).

---

## Key Features

- **Port 8092 Microservice**: Runs independently with zero dependency on SQLAlchemy ORM, Alembic migrations, or Redis workers.
- **Dual-Mode Diagnostic Engine**:
  - **Mode A (Post-Trip Forensics)**: Anchored to $T_{trip}$ with a 15-minute pre-trip / 5-minute post-trip SCADA telemetry window.
  - **Mode B (Live Running Degradation RCA)**: Analyzes uncommanded drift, thermal margins, and early degradation on live running wells.
- **Evidence Identification & Reconciliation (EIR)**: 7-section structured diagnostic reports detailing observations, physics discrepancies, and confidence calibration.
- **Streaming NDJSON (`POST /query`)**: Progressive frame streaming (`ROUTING` $\rightarrow$ `DIAGNOSING` $\rightarrow$ `EVIDENCE` $\rightarrow$ `REPORT`) for instant operator feedback in `<AgentDock />` and dashboard UI panels.
- **Safety & Refusal Engine**:
  - Intercepts false-premise queries on healthy assets without fabricating failures.
  - Blocks physical actuation commands (strictly advisory-only).
  - Re-anchors out-of-scope prompts back to ESP field operations.
  - Enforces Data Readiness Gates when telemetry channels are missing or degraded.

---

## Required Environment Variables (`.env`)

To run `agent_service_v2`, create a `.env` file in the `agent_service_v2/` directory:

```bash
# Copy example configuration
cp .env.example .env
```

### Environment Variable Reference

| Variable | Description | Required | Example / Recommended Value |
|---|---|:---:|---|
| `HOST` | Microservice bind host | Yes | `0.0.0.0` |
| `PORT` | Microservice listening port | Yes | `8092` |
| `ESP_APM_DB_URL` | PostgreSQL read-only connection string to Server 184 (`esp_apm_db`) | Yes | `postgresql://esp_admin:EspApm2026!@192.168.1.184:5433/esp_apm_db` |
| `AI_ENABLED` | Enable local LLM synthesis for narrative report generation | Yes | `true` (or `false` for deterministic-only mode) |
| `LLM_API_BASE` | OpenAI-compatible endpoint for local LLM inference server | Yes | `http://192.168.1.188:8080/v1` (or `http://192.168.1.134:8080/v1`) |
| `LLM_MODEL` | Local LLM model identifier | Yes | `Qwen2.5-Coder-3B-Instruct-Q4_K_M` |
| `LLM_TIMEOUT` | Timeout in seconds for LLM generation requests | No | `60` |

### Complete `.env` Template for `agent_service_v2`

```ini
# Server Networking
HOST=0.0.0.0
PORT=8092

# PostgreSQL SCADA & Knowledge Base (Server 184, Read-Only)
ESP_APM_DB_URL=postgresql://esp_admin:EspApm2026!@192.168.1.184:5433/esp_apm_db

# Local Inference Gateway (Server 188 / 134 Qwen 2.5 Coder 3B)
AI_ENABLED=true
LLM_API_BASE=http://192.168.1.188:8080/v1
LLM_MODEL=Qwen2.5-Coder-3B-Instruct-Q4_K_M
LLM_TIMEOUT=60
```

---

## API Endpoints

### 1. Healthcheck (`GET /health`)
Verifies read-only connectivity to Server 184 PostgreSQL and the local LLM endpoint.
```bash
curl http://localhost:8092/health
```
```json
{
  "status": "HEALTHY",
  "service": "esp-agent-service-v2",
  "port": 8092,
  "database_connected": true,
  "llm_api_base": "http://192.168.1.188:8080/v1"
}
```

### 2. Streaming Query (`POST /query`)
Primary endpoint for chat widgets (`<AgentDock />`) and dashboard integrations. Streams newline-delimited JSON (`x-ndjson`).

**Request Payload**:
```json
{
  "session_id": "sess-op-001",
  "question": "Why did well FNW-001 trip?",
  "well_id": "FNW-001",
  "page_route": "/wells/FNW-001"
}
```

**Stream Frames**:
```jsonl
{"type": "status", "stage": "ROUTING", "progress": 0.15, "message": "Analyzing query intent & identifying asset..."}
{"type": "status", "stage": "DIAGNOSING", "progress": 0.50, "message": "Querying Server 184 SCADA telemetry & physics baseline models..."}
{"type": "evidence", "confidence": 0.96, "intent": "EVENT_DIAGNOSE", "entity": "FNW-001", "event_id": "EV-20261012-103435-FNW-001-878"}
{"type": "report", "markdown_text": "# ESP Diagnostic Report ..."}
{"type": "completion", "status": "COMPLETED", "progress": 1.0}
```

---

## Running the Service

### Option A: Local Python Virtual Environment

```bash
# Navigate to service directory
cd agent_service_v2

# Install dependencies
py -3.11 -m pip install -r requirements.txt

# Start FastAPI server
py -3.11 -m uvicorn main:app --host 0.0.0.0 --port 8092 --reload
```

### Option B: Docker Container

```bash
cd agent_service_v2
docker compose up --build -d
```

---

## Verification & Test Suites

The service contains rigorous test suites verifying all operational domains against live PostgreSQL data:

```bash
# Domain 3: 15-min Pre-trip / 5-min Post-trip Forensics & Disambiguation
py -3.11 -m pytest test_domain3_forensics.py -v

# Domain 4: Well-Level Diagnosis (Dual-Mode Engine)
py -3.11 -m pytest test_domain4_diagnosis.py -v

# Domain 11: Multi-turn Session & Pronoun Resolution
py -3.11 -m pytest test_domain11_conversational.py -v

# Domain 12: Safety & Refusal Engine
py -3.11 -m pytest test_domain12_safety.py -v

# Run Full 60-Query Benchmark across all 12 Domains
py -3.11 run_60_all_domains_benchmark.py
```
