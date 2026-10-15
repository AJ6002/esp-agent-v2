# ESP APM Dashboard Frontend Integration Guide (Agent Service V2)

This document specifies the exact requirements, payloads, and components needed on the dashboard frontend (`esp-insight-suite`) to integrate the upgraded standalone **Agent Service V2** microservice.

---

## 1. Network & Port Configuration

### Default Service Port
Agent Service V2 runs on **Port 8092** by default to prevent port conflicts with legacy V1 services (which ran on `8091`).

### Frontend `.env` Configuration
In your dashboard application project, configure the agent base URL:

```ini
# Development (.env or .env.local)
VITE_AGENT_BASE_URL="http://127.0.0.1:8092"

# Production (.env.production on Server 184)
VITE_AGENT_BASE_URL="http://192.168.1.184:8092"
```

> **Zero-Frontend-Change Fallback**:
> If your dashboard build cannot easily be recompiled and must remain on port `8091`, simply open `agent_service_v2/.env` and change `PORT=8092` to `PORT=8091` before starting the service.

---

## 2. API Endpoints & Contract Specifications

### 2.1 Streaming NDJSON Endpoint (`POST /query`)
This is the primary endpoint consumed by the `<AgentDock />` chat interface.

- **URL**: `POST ${VITE_AGENT_BASE_URL}/query`
- **Headers**:
  ```http
  Content-Type: application/json
  Accept: application/x-ndjson, text/plain, */*
  ```

#### Request Payload Structure
The endpoint accepts both `message` and `question` keys interchangeably:

```typescript
interface AgentQueryRequest {
  session_id?: string;               // e.g. "sess-operator-101"
  message?: string;                  // User query string (e.g. "Why did well FNW-001 trip?")
  question?: string;                 // Dual-compatibility alias for message
  well_id?: string;                  // Active well context (e.g. "FNW-001")
  asset_id?: string;                 // Asset identifier alias
  page_route?: string;               // Current browser route (e.g. "/wells/FS-004")
  time_range?: string;               // e.g. "last_24h"
  conversation_history?: Array<{    // Enables multi-turn pronoun & antecedent resolution
    role: "user" | "assistant";
    content: string;
  }>;
}
```

#### NDJSON Response Stream Frames
Responses are streamed as newline-delimited JSON objects (`\n`). The frontend stream parser should handle the following 4 frame types:

1. **`status` Frame** (Updates progress indicators and status pills):
   ```json
   {
     "type": "status",
     "stage": "ROUTING" | "DIAGNOSING" | "SYNTHESIS",
     "progress": 0.15 | 0.50 | 0.85,
     "message": "Querying Server 184 SCADA telemetry & physics baseline models..."
   }
   ```

2. **`text_delta` Frame** (Progressive markdown chunks for real-time typing effect):
   ```json
   {
     "type": "text_delta",
     "delta": "# [ESP APM] Fleet Real-Time Operational Status\n\n- Active..."
   }
   ```

3. **`advisory` Frame** (Structured diagnostic and safety payload for native cards):
   ```json
   {
     "type": "advisory",
     "advisory": {
       "event_id": "EV-20261012-103435-FNW-001-878",
       "well_id": "FNW-001",
       "trip_cause": "HIGH_VIBRATION",
       "severity": "CRITICAL",
       "confidence": 0.94,
       "hypotheses": [
         {
           "name": "Bearing Degradation",
           "confidence_pct": 92,
           "evidence": "Peak radial vibration surged to 4.28g prior to trip"
         }
       ],
       "deviations": [
         {
           "signal": "Vibration",
           "baseline_val": 2.0,
           "pre_trip_val": 4.28,
           "status": "VIOLATION"
         }
       ],
       "next_steps": [
         "[CRITICAL] MANDATORY LOTO: De-energize VSD switchboard.",
         "[CRITICAL] ZERO-ENERGY VERIFICATION: Test with 1000V multimeter."
       ]
     }
   }
   ```

4. **`done` Frame** (End-of-stream sentinel):
   ```json
   {
     "type": "done",
     "status": "COMPLETED" | "FAILED"
   }
   ```

---

### 2.2 REST Endpoints (`POST /ask` & `POST /api/v1/esp/ask`)
For non-streaming components, modal dialogs, or fallback REST queries:

- **URL**: `POST ${VITE_AGENT_BASE_URL}/ask` OR `POST ${VITE_AGENT_BASE_URL}/api/v1/esp/ask`
- **Request Body**: `{"question": "what is the current status of the fleet?"}`
- **Response (`200 OK`)**:
  ```json
  {
    "answer": "# [ESP APM] Fleet Real-Time Operational Status...\n",
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

## 3. New Capability Features & How Frontend Should Display Them

### 3.1 Rich Markdown Tables & Reports (Formatting Requirement)
- **Problem**: If the frontend renders message text inside a plain `<p style={{ whiteSpace: "pre-wrap" }}>`, markdown tables (`|---|`), bold text, and headers render as raw unstyled characters.
- **Frontend Fix**: In your message component (e.g. `src/agent-dock/components/MessageBubble.tsx`), use `react-markdown` with `remark-gfm`:
  ```tsx
  import ReactMarkdown from "react-markdown";
  import remarkGfm from "remark-gfm";

  export const MessageBubble = ({ text }: { text: string }) => (
    <div className="agent-bubble-container">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {text}
      </ReactMarkdown>
    </div>
  );
  ```

---

### 3.2 Domain 9: Deep-Link UI Navigation
When users ask navigational questions (e.g., *"Where can I see the electrical data for FS-004?"* or *"Where is the scenario simulator?"*):
- The agent returns `intent: "UI_NAVIGATION"`.
- The `structured_data` includes:
  ```json
  {
    "route_id": "route.well_detail",
    "resolved_path": "/wells/FS-004",
    "title": "Well Monitor & Downhole Detail",
    "suggested_options": ["Open /wells/FS-004", "Well Working Status"]
  }
  ```
- **Frontend Action**:
  Detect `resolved_path` in `structured_data` or parse suggested options starting with `Open /...`. Render a clickable navigation button:
  ```tsx
  {message.structured_data?.resolved_path && (
    <button 
      onClick={() => navigate(message.structured_data.resolved_path)}
      className="btn-navigate-screen"
    >
      Go to {message.structured_data.title || message.structured_data.resolved_path}
    </button>
  )}
  ```

---

### 3.3 Autonomous Work Order Dispatch & Safety LOTO Cards
When a user asks to *"dispatch a work order for FS-004 to replace mechanical seal"*:
- The agent generates a formal staged work order: `WO-ESP-FS-004-AUTO`.
- The stream emits an `advisory` frame with `severity: "P1"` and an 8-item `loto_checklist`.
- **Frontend Action**:
  Render the checklist items as an interactive compliance checklist where operators must check off each safety verification step (LOTO de-energize, 1000V Megger test, zero-energy verification) before final sign-off.

---

### 3.4 Multi-Turn Conversational Memory (Pronoun Resolution)
The backend now resolves antecedents across turns:
- **Turn 1**: *"Let's inspect well FS-004"*
- **Turn 2**: *"What is its motor temperature?"* (resolves `"its"` to `FS-004`)
- **Frontend Action**:
  Ensure the `<AgentDock />` sends the previous messages in the request payload:
  ```typescript
  const payload = {
    message: currentInput,
    conversation_history: messages.slice(-6).map(m => ({
      role: m.sender === "user" ? "user" : "assistant",
      content: m.text
    }))
  };
  ```

---

### 3.5 Domain 10: Safety Boundaries & Actuation Refusals
When an operator asks the agent to physically actuate hardware (e.g., *"Turn off pump FS-004"* or *"Restart well"*):
- The agent strictly enforces its `[READ-ONLY DECISION SUPPORT]` boundary.
- It returns an explicit refusal message explaining that direct SCADA actuation is prohibited for safety reasons, providing manual supervisory steps instead.
- **Frontend Action**:
  Display a warning / safety badge when `intent === "SELF_BOUNDARIES"`.

---

## 4. Frontend Integration Verification Checklist

Before shipping the dashboard build, verify the following interactions in `<AgentDock />`:

| Interaction / Query | Expected Frontend Experience |
| :--- | :--- |
| **Fleet Inventory**: `"what is the current status of the fleet?"` | Displays formatted markdown table with 10 wells (running vs tripped counts). |
| **Production Rollup**: `"how much oil are we producing across the fleet?"` | Displays Gross Liquid BPD and Net Oil BOPD with deferment loss figures. |
| **Trip Diagnosis**: `"Why did well FNW-001 trip?"` | Streams text + renders `<StructuredAdvisory />` card with 92% confidence badge. |
| **Multi-Well Compare**: `"compare well FS-004 vs FS-006"` | Side-by-side comparison table of electrical, hydraulic, and thermal signals. |
| **UI Navigation**: `"where is the scenario simulator?"` | Navigates or presents direct link to `/custom-testing`. |
| **Safety Refusal**: `"can you turn off pump FS-004?"` | Refuses actuation with read-only safety boundary explanation. |
| **LOTO Work Order**: `"dispatch work order for FS-004"` | Generates staged work order card with mandatory 8-step safety checklist. |
| **Pronoun Follow-up**: *"check FS-004"* followed by *"what is its motor temp?"* | Retains `FS-004` context without re-prompting for the well ID. |
