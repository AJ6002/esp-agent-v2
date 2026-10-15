# ESP APM Agent Service V2 — Complete Service Architecture & Integration Guide

## 1. Executive Summary & Architecture
`agent_service_v2` is a standalone, containerized AI Diagnostic & SCADA Analytics microservice for the ESP Artificial Lift Platform. It runs decoupled from legacy services on **Port 8092** (`http://localhost:8092`) to guarantee zero port collisions with legacy V1 services (which ran on `8091`).

### System Topology
```
┌────────────────────────────────────────────────────────┐
│ Target Dashboard (esp-insight-suite)                   │
│ Vite / React 18 (Port 5173 / 3000)                     │
│ <AgentDock /> Component (Streaming NDJSON or REST)     │
└──────────────────────────┬─────────────────────────────┘
                           │ POST /query (NDJSON) or POST /ask (REST)
                           ▼
┌────────────────────────────────────────────────────────┐
│ agent_service_v2 (Docker Container, Port 8092)         │
│ FastAPI + Deterministic Physics Engine + Intent Router │
└─────────────┬────────────────────────────┬─────────────┘
              │ Read-Only SQL              │ OpenAI-Compatible API
              ▼                            ▼
┌───────────────────────────┐ ┌──────────────────────────┐
│ PostgreSQL Server 184     │ │ LLM Inference Server 134 │
│ (192.168.1.184:5433)      │ │ (192.168.1.134:8080/v1)  │
│ db: esp_apm_db            │ │ Qwen 2.5 Coder 3B        │
└───────────────────────────┘ └──────────────────────────┘
```

---

## 2. Quick Start & Execution

### Method A: Native Python (Development Mode)
```bash
cd agent_service_v2

# 1. Install dependencies
pip install -r requirements.txt

# 2. Run standalone service on port 8092
python main.py
```

### Method B: Docker Compose (Production Deployment)
```bash
cd agent_service_v2

# Build and start in background
docker compose up -d --build

# Inspect logs
docker compose logs -f

# Stop service
docker compose down
```

### Method C: Running Empirical Verification Suite
The service includes an exhaustive, zero-mock regression test suite verifying all 15 operational domains, remote PostgreSQL 184 telemetry, and Server 134 LLM inference:
```bash
python test_service.py
```
Expected output: `ALL 15 VERIFICATION SUITES PASSED GREEN (100% SUCCESS)!`

---

## 3. Supported Capability Domains (Complete Feature Matrix)

Not a single feature or domain is left behind. `agent_service_v2` provides complete parity with the core API engine:

| Domain | Capability / Intent | Example User Queries | Key Output / Payload |
| :--- | :--- | :--- | :--- |
| **Domain 1.1** | `FLEET_INVENTORY` | *"What is the current status of the fleet?"* | 10 monitored wells, running vs tripped counts, cluster grouping |
| **Domain 1.2** | `EVENT_DIAGNOSE` | *"Why did well FNW-001 trip and what are the recommended actions?"* | Physics root cause, 14-fault classification, sensor deviations, corrective actions |
| **Domain 1.3** | `FLEET_PRODUCTION` | *"How much oil are we producing across the fleet?"* | Gross liquid rate (BPD), net oil (BOPD), deferred production, water cut |
| **Domain 1.4** | `FLEET_TRIAGE` | *"Triage highest risk wells in the fleet"* | Urgent intervention queue, risk severity ranking, deferment impact |
| **Domain 1.5** | `FLEET_EXECUTIVE` | *"Executive morning briefing"* / *"Management summary"* | High-level executive briefing, availability factor, supervisory mandates |
| **Domain 1.6** | `FLEET_ANOMALY` | *"Which wells are exhibiting anomalous behavior?"* | Sub-trip drift detection, degrading running assets, early warning alerts |
| **Domain 1.7** | `FLEET_TIMELINE` | *"Show fleet alarm timeline"* | Chronological incident clusters, trip density across gathering stations |
| **Domain 2.1** | `MULTI_WELL_COMPARE` | *"Compare well FS-004 vs FS-006"* | Side-by-side electrical, thermal, hydraulic metrics & delta analysis |
| **Domain 2.2** | `CLUSTER_COMPARE` | *"Compare cluster 15 vs cluster 4"* | Gathering center aggregation, water cut comparison, uptime benchmarking |
| **Domain 2.3** | `HISTORICAL_COMPARE` | *"Is FS-004 operating within historical baseline limits?"* | Calibrated P50 baseline envelope, z-score deviations, operating range |
| **Domain 2.4** | `PEER_BENCHMARK` | *"Benchmark well FS-017 against its peers"* | Cluster percentile rankings, relative motor temperature & current efficiency |
| **Domain 2.5** | `FLEET_RANKING` | *"Rank wells by vibration"* / *"Rank wells by water cut"* | Fleet leaderboard sorted descending by selected SCADA metric |
| **Domain 9** | `UI_NAVIGATION` | *"Where can I see electrical data for FS-004?"* / *"Where is the scenario simulator?"* | Platform route resolution (`/wells/FS-004`, `/custom-testing`, `/reports`) |
| **Domain 10.1** | `SELF_IDENTITY` | *"Who are you and what is your role?"* | Autonomous Industrial AI Copilot specification, read-only decision badge |
| **Domain 10.2** | `SELF_CAPABILITIES` | *"What can you do?"* | Manifest of all 10 operational domains and supported analytical tasks |
| **Domain 10.3** | `SELF_BOUNDARIES` | *"Can you turn off pump FS-004?"* / *"Restart pump"* | Actuation refusal, strict read-only boundary enforcement, safety notice |
| **Domain 10.4** | `SELF_FLEET_SCOPE` | *"Which wells do you monitor?"* | Monitored asset boundaries (10 wells across GCS-15, GCS-3, GCS-4) |
| **Domain 10.5** | `SELF_LIMITATIONS` | *"What are your operational limitations?"* | Sensor sampling disclosures, human engineering oversight requirements |
| **Safety / Ops** | `WORK_ORDER_DISPATCH` | *"Dispatch work order for FS-004 to replace mechanical seal"* | Autonomous staged work order, mandatory 8-step Lockout/Tagout (LOTO) checklist |
| **Multi-Turn** | Antecedent Resolution | Turn 1: *"Inspect FS-004"* → Turn 2: *"What is its motor temperature?"* | Resolves pronouns (`it`, `its`, `that well`) across conversation turns |
| **Knowledge** | `KNOWLEDGE` | *"What causes gas locking in an ESP?"* | SOP / engineering standards retrieval & Server 134 LLM synthesis |

---

## 4. API & Protocol Specifications

### 4.1 Health Check
- **Endpoint:** `GET http://localhost:8092/health`
- **Response (`200 OK`):**
  ```json
  {
    "status": "HEALTHY",
    "service": "esp-agent-service-v2",
    "port": 8092,
    "database_connected": true,
    "llm_api_base": "http://192.168.1.134:8080/v1"
  }
  ```

### 4.2 Streaming NDJSON Endpoint (`POST /query`)
Primary endpoint for the React `<AgentDock />` component:
- **Endpoint:** `POST http://localhost:8092/query`
- **Headers:**
  - `Content-Type: application/json`
  - `Accept: application/x-ndjson, text/plain, */*`
- **Request Body (supports both `message` and `question` keys):**
  ```json
  {
    "session_id": "sess-operator-01",
    "message": "Why did well FNW-001 trip and what are the recommended actions?",
    "well_id": "FNW-001",
    "asset_id": "FNW-001",
    "page_route": "/wells/FNW-001",
    "conversation_history": [
      {"role": "user", "content": "Let's check well FNW-001"},
      {"role": "assistant", "content": "FNW-001 is currently tripped on HIGH_VIBRATION."}
    ]
  }
  ```
- **Stream Frame Sequence (NDJSON):**
  1. `status` frames (ROUTING, DIAGNOSING, SYNTHESIS)
  2. `text_delta` frames (progressive markdown text chunks for typing animation)
  3. `advisory` frame (emitted for `EVENT_DIAGNOSE` and `WORK_ORDER_DISPATCH` containing structured metadata and LOTO checklists)
  4. `done` frame (`{"type": "done", "status": "COMPLETED"}`)

### 4.3 REST Endpoints (`POST /ask` and `POST /api/v1/esp/ask`)
For non-streaming callers, batch verification scripts, and automated regression runners:
- **Endpoints:** `POST http://localhost:8092/ask` and `POST http://localhost:8092/api/v1/esp/ask`
- **Request Body:**
  ```json
  {
    "question": "What is the current status of the fleet?"
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "answer": "# [ESP APM] Fleet Real-Time Operational Status...",
    "intent": "FLEET_INVENTORY",
    "confidence": 0.98,
    "structured_data": {
      "total_wells": 10,
      "running_wells_count": 4,
      "tripped_wells_count": 6,
      "running_wells": ["FS-004", "FS-006", "FS-023", "FWS-001"],
      "tripped_wells": ["FNW-001", "FS-013", "FS-016", "FS-017", "FS-040", "FS-047"]
    },
    "needs_clarification": false,
    "suggested_options": ["FNW-001 Health", "FS-017 History", "Cluster 15"]
  }
  ```

---

## 5. Dashboard Frontend Configuration (`esp-insight-suite`)

In your frontend application (`esp-insight-suite`):

### 1. Environment Variable Configuration (`.env`)
```ini
# .env (Local Development)
VITE_AGENT_BASE_URL="http://127.0.0.1:8092"

# .env.production (Production Server 184 Deployment)
VITE_AGENT_BASE_URL="http://192.168.1.184:8092"
```

### 2. Verify `<AgentDock />` Props
In `src/agent-dock/AgentDock.tsx`:
```tsx
export const AgentDock: React.FC<AgentDockProps> = ({
  baseUrl = import.meta.env?.VITE_AGENT_BASE_URL || "http://127.0.0.1:8092",
}) => {
  // Uses streaming POST /query with progressive rendering
};
```

### 3. Rendering Markdown in `<MessageBubble />`
To render full rich markdown (tables, bold headings, code blocks) rather than raw plaintext, install:
```bash
npm install react-markdown remark-gfm
```
In `src/agent-dock/components/MessageBubble.tsx`:
```tsx
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

// In your JSX:
<div className={styles.agentBubble}>
  <ReactMarkdown remarkPlugins={[remarkGfm]}>
    {message.text}
  </ReactMarkdown>
</div>
```

---

## 6. Verification and Acceptance Guarantee

All code in `agent_service_v2` is completely self-contained:
- All imports are local to `app/`.
- UI routing uses `app/data/ui_map.yaml`.
- Telemetry queries bypass PostgreSQL temporary disk sorts with indexed per-well lookups (`ORDER BY timestamp DESC LIMIT 1`).
- The 15 verification suites in `test_service.py` pass 100% green against live Server 184 and Server 134.
