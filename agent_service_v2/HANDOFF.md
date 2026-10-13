# ESP APM Agent Service V2 — Dashboard Integration & Handoff Guide

## 1. Executive Summary & Architecture
`agent_service_v2` is a standalone, containerized AI Diagnostic & SCADA Analytics microservice for the ESP Artificial Lift Platform. It runs decoupled from legacy services on **Port 8092** (`http://localhost:8092`) to guarantee zero port collisions with legacy V1 services (which ran on `8091`).

### System Topology
```
┌────────────────────────────────────────────────────────┐
│ Target Dashboard (esp-insight-suite)                   │
│ Vite / React 18 (Port 5173 / 3000)                     │
│ <AgentDock /> Component                                │
└──────────────────────────┬─────────────────────────────┘
                           │ POST /query (NDJSON Stream)
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

## 2. Quick Start (How to Run)

### Method A: Docker Compose (Recommended)
From the `agent_service_v2/` directory:
```bash
# Build and start in background
docker compose up -d --build

# Inspect logs
docker compose logs -f

# Stop service
docker compose down
```

### Method B: Native Python (Development Mode)
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run server on port 8092
python main.py
```

### Verify Running Status
```bash
curl -s http://localhost:8092/health
# Response:
# {"status": "HEALTHY", "service": "esp-agent-service-v2", "port": 8092, "database_connected": true, "llm_api_base": "http://192.168.1.134:8080/v1"}
```

---

## 3. Dashboard Frontend Configuration

In your dashboard project (`esp-insight-suite/esp-insight-suite`):

### 1. Update Environment Variables (`.env`)
Update the agent URL in your `.env` and `.env.production` files:

```ini
# .env (Local Development)
VITE_AGENT_BASE_URL="http://127.0.0.1:8092"

# .env.production (Production Deployment)
VITE_AGENT_BASE_URL="http://192.168.1.184:8092"
```

### 2. Verify `<AgentDock />` Props
In `src/agent-dock/AgentDock.tsx`, ensure default fallback points to `8092`:
```tsx
export const AgentDock: React.FC<AgentDockProps> = ({
  baseUrl = import.meta.env?.VITE_AGENT_BASE_URL || "http://127.0.0.1:8092",
}) => {
  // ...
};
```

---

## 4. API & Protocol Specifications

### 4.1 Health Endpoint
- **URL:** `GET http://localhost:8092/health`
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

### 4.2 Query Endpoint
- **URL:** `POST http://localhost:8092/query`
- **Headers:**
  - `Content-Type: application/json`
  - `Accept: application/x-ndjson, text/plain, */*`
- **Request Body:**
  ```json
  {
    "session_id": "sess-user-01",
    "message": "Why did well FNW-001 trip and what are the recommended actions?",
    "well_id": "FNW-001",
    "asset_id": "FNW-001",
    "page_route": "/wells/FNW-001",
    "time_range": "last_24h"
  }
  ```
- **Response (`200 OK`):** Streaming `application/x-ndjson`. Sequence of newline-delimited JSON objects matching Dashboard `AgentFrame` TypeScript types:
  1. **Status Frames:**
     ```json
     {"type": "status", "stage": "ROUTING", "progress": 0.15, "message": "Analyzing query intent & identifying asset..."}
     {"type": "status", "stage": "DIAGNOSING", "progress": 0.50, "message": "Querying Server 184 SCADA telemetry & physics baseline models..."}
     ```
  2. **Text Delta Frames (Markdown chunks):**
     ```json
     {"type": "text_delta", "delta": "# [ESP APM] Event Root Cause Diagnosis\n\n**Well**: `FNW-001`..."}
     ```
  3. **Structured Advisory Frame (Native Card UI):**
     ```json
     {
       "type": "advisory",
       "advisory": {
         "event_id": "EV-20261012-103435-FNW-001-878",
         "well_id": "FNW-001",
         "trip_cause": "HIGH_VIBRATION",
         "confidence": 0.94,
         "hypotheses": [
           {"name": "Bearing Wear", "confidence_pct": 90, "evidence": "Vibration surged to 4.2783g"}
         ],
         "deviations": [
           {"signal": "Vibration", "baseline_val": 2.0, "pre_trip_val": 4.2783, "status": "VIOLATION"}
         ],
         "next_steps": [
           {"category": "SAFETY_LOTO", "action": "De-energize VSD switchboard"}
         ]
       }
     }
     ```
  4. **Done Sentinel:**
     ```json
     {"type": "done", "status": "COMPLETED"}
     ```

---

## 5. Improving Dashboard Response Presentation

### Why Markdown Text Looks Raw Currently
In `src/agent-dock/components/MessageBubble.tsx:49`:
```tsx
<div className={styles.agentBubble}>
  <p style={{ margin: 0, whiteSpace: "pre-wrap" }}>{message.text}</p>
</div>
```
Because the message is rendered inside a plain `<p style={{ whiteSpace: "pre-wrap" }}>`, headings (`###`), bold text (`**`), and tables (`|---|`) render as literal characters instead of formatted rich typography.

### Recommended Frontend Improvements
1. **Enable Markdown Parsing in `MessageBubble.tsx`:**
   Install or import a Markdown renderer (such as `react-markdown`):
   ```bash
   npm install react-markdown remark-gfm
   ```
   In `MessageBubble.tsx`:
   ```tsx
   import ReactMarkdown from "react-markdown";
   import remarkGfm from "remark-gfm";

   // Replace the plain <p> tag with:
   <div className={styles.agentBubble}>
     <ReactMarkdown remarkPlugins={[remarkGfm]}>
       {message.text}
     </ReactMarkdown>
   </div>
   ```
2. **Native Cards via `StructuredAdvisory`:**
   `agent_service_v2` automatically emits `type: "advisory"` frames for diagnostic queries. The existing `<StructuredAdvisory advisory={message.advisory} />` component in the dashboard will automatically render rich visual cards, confidence badges, and actionable checklists.

---

## 6. Verified Golden Queries for Testing

| Test Query | Target Asset | Expected Result |
| :--- | :--- | :--- |
| `"Why did well FNW-001 trip and what are the recommended actions?"` | `FNW-001` | Diagnoses `HIGH_VIBRATION` bearing degradation (peak vib `4.28g`, overload `24.34A`, PDP collapse). |
| `"what is the current status of the fleet?"` | Fleet | Exact 10 wells: **5 Running** (`FS-004`, `FS-006`, `FS-013`, `FS-023`, `FWS-001`), **5 Tripped** (`FNW-001`, `FS-016`, `FS-017`, `FS-040`, `FS-047`). |
| `"Is well FNW-001 healthy?"` | `FNW-001` | Returns health audit envelope against calibrated P50 baselines. |
| `"Compare well FS-017 vs FS-040"` | `FS-017`, `FS-040` | Side-by-side comparative analysis of overload vs broken shaft trips. |
| `"Show history of well FS-017 in last 7 days"` | `FS-017` | Filtered historical trip timeline from Server 184. |

---

## 7. Troubleshooting & Operational Support

- **Database Connectivity Issues:**
  - Verify PostgreSQL Server 184 is reachable: `Test-NetConnection -ComputerName 192.168.1.184 -Port 5433`.
  - Credentials in `.env`: `postgresql://esp_admin:EspApm2026!@192.168.1.184:5433/esp_apm_db`.
- **LLM Timeout or Refusal:**
  - Verify LLM Server 134 is active: `curl http://192.168.1.134:8080/v1/models`.
  - Service automatically falls back gracefully if the LLM server is temporarily offline.
- **Port Conflict Check:**
  - Verify port 8092 is dedicated: `Get-NetTCPConnection -LocalPort 8092`.
  - Note: V1 agent service on 8091 will not interfere with this container.
