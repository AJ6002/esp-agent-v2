# Co-Pilot Agent Service: Architectural Contract & Requirements Specification

**Target Audience:** Agent Engineering Team, AI/ML Engineers, Gateway Integrators  
**Client Interface:** ESP Insight Suite (`AgentDock`)  
**Workspace:** `a:\TAS-AI\esp-insight-suite`  
**Related Repository:** `A:\TAS-AI\ESP\agent_service`  
**Classification:** Deep Codebase Reality — Production Handoff Contract  

---

## Executive Summary

This document defines the definitive operational, architectural, and interface specifications for developing a **new AI Agent Service** for the **Co-Pilot Dock (`AgentDock`)**, assuming the existing frontend suite remains in place.

The Co-Pilot Dock is not a general-purpose chat interface. It is a mission-critical **Operations Diagnostic Copilot** designed for petroleum engineers, production technicians, and field dispatchers managing electrical submersible pumps (ESPs).

```
+----------------------------------------------------------------------------------------------------+
|                                    ESP INSIGHT SUITE (FRONTEND)                                     |
|  +-----------------------------------------------------------------------------------------------+  |
|  |                                  AgentDock (React 18 / Vite)                                  |  |
|  |  +---------------------------+  +-------------------------------+  +-----------------------+  |  |
|  |  |      Message Stream       |  |     Structured Advisory       |  |   Rich Visual Cards   |  |  |
|  |  | (text_delta, status pills)|  |  (7-step XAI, SOP, Evidence)  |  | (Health, Defer, Proof)|  |  |
|  |  +---------------------------+  +-------------------------------+  +-----------------------+  |  |
|  +-----------------------------------------------------------------------------------------------+  |
+--------------------------------------------------+-------------------------------------------------+
                                                   | HTTP POST /query
                                                   | Accept: application/x-ndjson
                                                   v
+----------------------------------------------------------------------------------------------------+
|                                     AGENT SERVICE (TARGET BUILD)                                   |
|  +--------------------------+  +----------------------------+  +--------------------------------+  |
|  |    FastAPI NDJSON Bus    |  |     XAI Reasoning Core     |  |       Analytics & Adapters     |  |
|  | (port 8091, stream heart)|  | (Tripped / Running Engine) |  |   (DB, Baselines, Rest APIs)   |  |
|  +--------------------------+  +----------------------------+  +--------------------------------+  |
+--------------------------------------------------+-------------------------------------------------+
                                                   | Read-Only Query & Governed Baselines
                                                   v
+----------------------------------------------------------------------------------------------------+
|                                 DASHBOARD SERVICES & DATA PLATFORM                                 |
|  +------------------------+  +----------------------------+  +----------------------------------+  |
|  | Governed Baselines YAML|  |  PostgreSQL (esp_apm_db)   |  | Dashboard Backend (port 8000)    |  |
|  | (config/baselines/)    |  |  (port 5433, telemetry/ev) |  | (REST live / historian / curves) |  |
|  +------------------------+  +----------------------------+  +----------------------------------+  |
+----------------------------------------------------------------------------------------------------+
```

---

## 1. Conceptual Responsibilities of the Agent Team

The Agent Team is responsible for building a deterministic, physics-informed, and explainable multi-agent reasoning engine. The engine must model the operational reality of oilfield ESP systems.

### 1.1 Core Diagnostic Responsibilities
1. **Multi-Domain Physics Analysis:**
   - ESP failures never occur in isolation. The agent must cross-correlate four operational domains:
     - **Electrical:** Motor current ($I_{RMS}$), frequency ($f$), power factor ($\cos\phi$), voltage imbalance, and leakage current.
     - **Hydraulic:** Intake pressure ($P_{int}$), discharge pressure ($P_{dis}$), differential head ($\Delta P$), and flow rate ($Q$).
     - **Thermal:** Motor winding temperature ($T_{mot}$), downhole fluid temperature ($T_{fluid}$), and cooling velocity across the motor jacket.
     - **Mechanical:** X/Y/Z vibration (G-RMS), baseline shifts ($0.18\text{G}$ nominal), and thrust bearing wear.
2. **State-Differentiated Diagnostics:**
   - **Tripped State ($N_0$):** Immediate post-mortem forensic analysis. Determine the primary trip code (e.g., Underload `4130`, Overcurrent `4110`, High Vibration `4200`), distinguish root causes from secondary protective trips, and estimate deferment.
   - **Running Degradation State ($N_1$):** Incipient anomaly detection. Identify subtle trend drift (e.g., progressive gas locking, solids abrasion, emulsion loading, scaling) before protective trips occur.
3. **The Strict Zero-Fabrication Rule:**
   - The Agent **MUST NEVER hallucinate or fabricate** telemetry values, pump performance curves, timestamps, or operating states.
   - If a sensor tag is unreadable or absent, the Agent must explicitly state that the source is degraded or missing.
   - If a well is offline or not part of the active live fleet (such as `FS-014`, `FS-044`, `FS-116`, `FWS-004`), the Agent must return the exact governed message:
     > *"Well `<well_id>` is a known asset in the registry but is currently offline/unmonitored. Telemetry and live diagnostics are unavailable."*
4. **Deterministic Telemetry Citation:**
   - Every diagnostic claim made in natural language or structured output must be grounded in an auditable evidence citation tag (e.g., `FS-017_PIP_PSI@2026-10-12T04:15:00Z = 342.1 psi`).
5. **Streaming Liveness Guarantee:**
   - LLM reasoning and chain-of-thought processing can take time. The Agent must continuously stream keepalive status frames so the UI watchdog never terminates the connection.

---

## 2. Query API & What the Dock Expects

The Agent Dock communicates exclusively via an **NDJSON (Newline-Delimited JSON)** streaming protocol over HTTP.

### 2.1 Endpoint Specification
- **URL:** `http://127.0.0.1:8091/query` (configurable in Dock)
- **Method:** `POST`
- **Headers:**
  ```http
  Content-Type: application/json
  Accept: application/x-ndjson, text/plain, */*
  ```

### 2.2 Inbound Request Payload (What the Dock Sends)

The Dock sends the following JSON payload on user query submission:

```json
{
  "session_id": "sess-673e4b89-a210-4821",
  "message": "Why did well FS-017 trip at 04:15 and what should we do?",
  "well_id": "FS-017",
  "asset_id": "FS-017",
  "page_route": "/wells/FS-017",
  "time_range": "last_24h",
  "ui_context": {
    "selected_route": "/wells/FS-017",
    "active_tab": "diagnostics",
    "viewport": "desktop",
    "current_kpi": {
      "intake_pressure": 342.1,
      "motor_temperature": 198.4
    }
  }
}
```

#### Field Rules:
- `session_id` *(string, required)*: Unique identifier for conversation continuity and multi-turn state.
- `message` *(string, required)*: Raw user input text.
- `well_id` *(string | null)*: Pre-selected well from the UI context (e.g., `FS-017`). Can be null if the user asks a fleet-wide question.
- `asset_id` *(string | null)*: Asset identifier (matches `well_id` in single-well contexts).
- `page_route` *(string | null)*: Active frontend route (e.g., `/`, `/fleet`, `/wells/FS-017`, `/analytics`).
- `time_range` *(string | null)*: Active time selector (e.g., `last_1h`, `last_24h`, `last_7d`).
- `ui_context` *(object | null)*: Ephemeral UI state payload.

---

### 2.3 NDJSON Streaming Protocol & Timing Constraints

1. **Safety Watchdog Ceiling (65 Seconds):**
   - The frontend maintains a strict 65-second client-side watchdog (`agentClient.ts:19`).
   - If **no chunk** is received within 65,000 ms, the frontend terminates the request, displays a `TIMEOUT_ERROR`, and unlocks the UI input.
   - **Agent Requirement:** The Agent MUST emit an initial frame within **5 seconds** of receiving the request and stream progressive status or text frames at intervals not exceeding **10 seconds**.
2. **Chunk Framing:**
   - Every frame must be a single-line valid JSON object terminated by a newline character (`\n`).
   - The stream terminates when a `done` frame or an `error` frame is emitted.

---

### 2.4 Complete Frame Schema Specification (Expected Frame Types)

The Dock's state reducer (`AgentDock.tsx:65-92`) handles eight distinct frame types:

```typescript
export type AgentFrame =
  | StatusFrame
  | TextDeltaFrame
  | AdvisoryFrame
  | VisualFrame
  | ClarificationFrame
  | InterruptFrame
  | ErrorFrame
  | DoneFrame;
```

#### Frame 1: `status` (Progress & Activity Indicator)
Informs the user of internal pipeline progression. Renders a pulsing spinner and status message in the chat bubble.
```json
{
  "type": "status",
  "run_id": "run-98a72f10",
  "stage": "telemetry_fetch",
  "progress": 0.25,
  "message": "Querying historian for FS-017 72-hour pressure & vibration telemetry..."
}
```

#### Frame 2: `text_delta` (Streaming Natural Language)
Streams conversational or executive summary text token-by-token or phrase-by-phrase into the chat bubble.
```json
{
  "type": "text_delta",
  "run_id": "run-98a72f10",
  "delta": "Forensic analysis of well **FS-017** indicates an underload trip triggered at 04:15:22 UTC. "
}
```

#### Frame 3: `advisory` (Structured Diagnostic Output)
Provides the formal structured diagnostic contract. Renders an interactive, audit-ready diagnostic report inside the chat bubble.
```json
{
  "type": "advisory",
  "run_id": "run-98a72f10",
  "advisory": {
    "objective_id": "DIAG_FS-017_20261012_0415",
    "assessment": "Underload trip triggered by acute gas interference causing vapor lock in stages 12-24.",
    "hypotheses": [
      "Gas Interference / Vapor Lock (Primary - 85% probability)",
      "Severe Pump-Off / Inflow Depletion (Secondary - 12% probability)",
      "Drive Shaft Sheared / Mechanical Decoupling (Ruled Out - 3% probability)"
    ],
    "recommendation": "Perform casing head vent blowdown, verify separator backpressure, and execute soft-restart at 45 Hz with 15-minute gas-purge ramp.",
    "troubleshooting_steps": [
      "Inspect casing-tubing annulus pressure transmitter PT-102.",
      "Check separator gas backpressure valve position.",
      "Review acoustic fluid level sounding shot."
    ],
    "verification_steps": [
      "Confirm motor current stabilizes between 42A and 48A upon restart.",
      "Verify intake pressure recovers above 450 psi bubble-point threshold.",
      "Inspect vibration G-RMS remains below 0.22G."
    ],
    "cited_evidence_ids": [
      "FS-017_PIP_DROP_420_TO_180_PSI",
      "FS-017_CURRENT_FLUCTUATION_AMPS",
      "FS-017_VIBRATION_SPIKE_0.38G"
    ],
    "confidence": 0.88,
    "provenance_warnings": [
      "Discharge temperature sensor TT-104 responded with 4-minute telemetry lag."
    ],
    "degraded_sources": [],
    "recommended_cards": [
      "fleet-health-table",
      "proof-overlay-chart"
    ]
  },
  "source_refs": ["well_baselines.yaml", "opg_well_telemetry"]
}
```

#### Frame 4: `visual` (Interactive Rich Cards & Widgets)
Renders rich interactive visual cards or launcher badges directly in the message bubble.
```json
{
  "type": "visual",
  "run_id": "run-98a72f10",
  "card_ids": ["fleet-health-table", "proof-overlay-chart"],
  "visualization": {
    "widget_id": "fleet_overview_widget",
    "card_ids": ["fleet-health-table", "proof-overlay-chart"],
    "data": {
      "fleet-health-table": {
        "totalWells": 10,
        "healthyCount": 7,
        "degradedCount": 2,
        "criticalCount": 1,
        "wells": [
          {
            "wellId": "FS-017",
            "healthScore": 15.0,
            "healthBand": "CRITICAL",
            "operatingState": "TRIPPED",
            "topSignal": "Underload Trip (Gas Lock)",
            "grossRateBpd": 0.0,
            "lastEvent": "Trip 4130 Underload"
          },
          {
            "wellId": "FS-004",
            "healthScore": 88.5,
            "healthBand": "HEALTHY",
            "operatingState": "RUNNING",
            "topSignal": "Nominal Operation",
            "grossRateBpd": 1420.0
          }
        ]
      },
      "proof-overlay-chart": {
        "channels": [
          {
            "channel_id": "current_amps",
            "name": "Motor Current (A)",
            "unit": "A",
            "series": [
              { "timestamp": "2026-10-12T04:00:00Z", "value": 46.2 },
              { "timestamp": "2026-10-12T04:14:00Z", "value": 24.1 },
              { "timestamp": "2026-10-12T04:15:22Z", "value": 0.0 }
            ]
          }
        ]
      }
    }
  }
}
```

#### Frame 5: `clarification` (Interactive Disambiguation)
Prompts the user with structured choice buttons when the request is ambiguous (e.g., user asks "Analyze the tripped well" when two wells are tripped).
```json
{
  "type": "clarification",
  "run_id": "run-98a72f10",
  "question": "Two wells currently exhibit trip alerts. Which well would you like me to diagnose?",
  "options": ["FS-017 (Underload Trip)", "FS-023 (Overcurrent Alarm)"],
  "slot": "target_well_id"
}
```

#### Frame 6: `interrupt` (Human-in-the-Loop Confirmation)
Halts execution when an action requires explicit field engineer approval (e.g., recommending a choke change or automated frequency step).
```json
{
  "type": "interrupt",
  "run_id": "run-98a72f10",
  "reason": "Recommending VSD operating frequency change from 50 Hz to 45 Hz on well FS-017.",
  "options": ["Approve SOP Recommendation", "Decline Recommendation"]
}
```

#### Frame 7: `error` (Structured Failure Notification)
Emitted when reasoning fails, external services are down, or invalid parameters are received.
```json
{
  "type": "error",
  "run_id": "run-98a72f10",
  "code": "DB_TELEMETRY_UNAVAILABLE",
  "message": "Unable to connect to PostgreSQL historian on port 5433 to retrieve sensor timeseries."
}
```

#### Frame 8: `done` (Stream Termination Sentinel)
Signals successful completion of the stream. Re-enables the chat input bar and removes progress spinners.
```json
{
  "type": "done",
  "run_id": "run-98a72f10",
  "status": "completed"
}
```

---

## 3. What the Dashboard Suite Provides to the Agent Team Now

The Dashboard repository provides all physical, mathematical, and telemetry foundations. The Agent Team does not need to reinvent baselines or invent database schemas.

### 3.1 Authoritative Governed Baselines (`config/baselines/`)
The Dashboard repository owns and governs 7 baseline files. These are synchronized automatically to the Agent Service via `python scripts/sync_baselines_to_agent.py`:

| Baseline File | Source Location in Dashboard | Usage in Agent Reasoning |
| :--- | :--- | :--- |
| `provisioned_wells.json` | [`config/baselines/provisioned_wells.json`](file:///a:/TAS-AI/esp-insight-suite/config/baselines/provisioned_wells.json) | **Single Source of Truth for Fleet Roster**: Defines 10 active live wells, 4 offline wells, asset IDs, and aliases. |
| `well_baselines.yaml` | [`config/baselines/well_baselines.yaml`](file:///a:/TAS-AI/esp-insight-suite/config/baselines/well_baselines.yaml) | **30-day running observed medians**: Baseline intake pressure, motor temp, vibration, motor current, frequency, liquid rate, and water cut for each active well. |
| `impact_thresholds.yaml` | [`config/baselines/impact_thresholds.yaml`](file:///a:/TAS-AI/esp-insight-suite/config/baselines/impact_thresholds.yaml) | **Engineering limits & rated capacity**: Fleet-wide safety limits plus `per_well_rated` nameplate capacities for deferment calculations. |
| `per_well_thresholds.yaml` | [`config/baselines/per_well_thresholds.yaml`](file:///a:/TAS-AI/esp-insight-suite/config/baselines/per_well_thresholds.yaml) | **Noise floors & sensitivities**: Rate-of-change limits and sensor variance thresholds per individual well. |
| `differential_hypotheses.yaml` | [`config/baselines/differential_hypotheses.yaml`](file:///a:/TAS-AI/esp-insight-suite/config/baselines/differential_hypotheses.yaml) | **Differential failure catalog**: Rule matrices for distinguishing vapor lock vs pump-off vs shaft shear vs emulsion. |
| `pattern_taxonomy_mapping.yaml` | [`config/baselines/pattern_taxonomy_mapping.yaml`](file:///a:/TAS-AI/esp-insight-suite/config/baselines/pattern_taxonomy_mapping.yaml) | **14 standard ESP fault signatures**: Taxonomy codes, standard severity scales, and tag signatures. |
| `per_well_hdq.yaml` | [`config/baselines/per_well_hdq.yaml`](file:///a:/TAS-AI/esp-insight-suite/config/baselines/per_well_hdq.yaml) | **Head-Flow (H-Q) Envelopes**: Operating envelopes and quadratic coefficients for pump performance assessment. |

---

### 3.2 Live Backend REST Endpoints (Port 8000)
The Dashboard backend service runs on `http://127.0.0.1:8000` (FastAPI) and provides read-only operational APIs:

1. `GET /api/esp/wells/live`
   - Returns instantaneous telemetry, calculated health scores, operating state (`RUNNING`, `TRIPPED`, `STOPPED`), and active alarms for all live fleet wells.
2. `GET /api/esp/wells/{well_id}/telemetry?hours=72`
   - Returns 72-hour historical time-series data for downhole and surface tags ($P_{int}$, $P_{dis}$, $I_{RMS}$, $T_{mot}$, $V_{vib}$, $Q$).
3. `GET /api/esp/events`
   - Returns historical and active alarm/trip event logs, SCADA alarm codes, and event durations.
4. `GET /api/esp/assets/{asset_id}/pump-curve`
   - Returns digitized manufacturer bench curves (`vendor_import`) or BEP affinity curves. If no digitized catalog curve exists, it returns `status: "UNAVAILABLE"` under the Zero-Fabrication rule.

---

### 3.3 Production PostgreSQL Telemetry Historian (`esp_apm_db`)
- **Host / Port:** `127.0.0.1:5433` (Dockerized or local cluster)
- **Database:** `esp_apm_db`
- **Key Tables:**
  - `opg_well_telemetry`: Raw and downsampled 1-minute to 10-minute sensor telemetry. Well IDs are formatted in canonical zero-padded form (e.g., `FS-017`).
  - `esp_events`: Historian trip records, alarm codes, and operator acknowledgement states.
  - `asset_registry`: Physical equipment metadata (casing ID, tubing OD, pump depth, motor type).

---

### 3.4 Automated Sync Utility
The repository includes an automated baseline synchronization script:
```bash
python scripts/sync_baselines_to_agent.py
```
This script computes SHA-256 hashes of all baseline files and synchronizes them idempotently into `agent_service/config/baselines/`, ensuring zero configuration drift between the Dashboard and the Agent.

---

## 4. Requirements from the Agent & What It Must Deliver

To deliver a production-grade user experience in the Co-Pilot Dock, the Agent Service must satisfy four non-negotiable requirements:

### 4.1 The 7-Step Explainable AI (XAI) Diagnostic Narrative
Every diagnostic response generated for an individual well must strictly adhere to the **7-Step XAI Diagnostic Structure**:

```
[Step 1: Observation & Operating State Summary]
   └── Operating state (RUNNING / TRIPPED), active alarms, current vs baseline delta.

[Step 2: Anomaly Signature & Domain Identification]
   └── Dominant domain (Electrical, Hydraulic, Thermal, Mechanical) & signature pattern.

[Step 3: Ranked Differential Hypotheses]
   └── Ranked failure modes with explicit probabilities; ruled-in and ruled-out rationales.

[Step 4: Root Cause Physics Determination]
   └── Definite physical mechanism (e.g., vapor pressure exceeded intake head causing gas lock).

[Step 5: Field Verification & Troubleshooting SOP]
   └── Step-by-step physical actions for field technicians before equipment restart or workover.

[Step 6: Operational Recommendations & Setpoint Tuning]
   └── Precise parameter adjustments (frequency Hz, choke %, purge time) and deferment mitigation.

[Step 7: Evidence Citations & Provenance Audit]
   └── Timestamped tag references and confidence score calculation.
```

---

### 4.2 Rich Visual Card Delivery
The Dock's `VisualCardPlaceholder` component natively renders rich interactive cards when payloads are provided in the `visual` frame. The Agent Service must format card payloads to match these exact TypeScript contracts:

#### Card 1: `fleet-health-table` (Fleet Overview & Status)
- **Component:** `FleetHealthTableCard.tsx`
- **Payload Contract:**
  ```json
  {
    "totalWells": 10,
    "healthyCount": 8,
    "degradedCount": 1,
    "criticalCount": 1,
    "wells": [
      {
        "wellId": "FS-017",
        "healthScore": 15.0,
        "healthBand": "CRITICAL",
        "operatingState": "TRIPPED",
        "topSignal": "Underload Trip (Gas Lock)",
        "grossRateBpd": 0.0,
        "lastEvent": "Trip 4130 Underload"
      }
    ]
  }
  ```

#### Card 2: `fleet-opportunity-view` (Production Optimization & Deferment)
- **Component:** `FleetOpportunityViewCard.tsx`
- **Payload Contract:**
  ```json
  {
    "totalOpportunityBpd": 840.0,
    "candidateCount": 2,
    "rankedWells": [
      {
        "rank": 1,
        "wellId": "FS-017",
        "opportunityType": "Unscheduled Deferment",
        "deferredProductionBpd": 520.0,
        "healthScore": 15.0,
        "anomalyScore": 0.94,
        "recommendedAction": "Clear gas lock and soft-restart at 45 Hz"
      }
    ]
  }
  ```

#### Card 3: `fleet-production-summary` (Operational KPI Ribbon)
- **Component:** `FleetProductionSummaryCard.tsx`
- **Payload Contract:**
  ```json
  {
    "totalGrossLiquidBpd": 11450.0,
    "totalNetOilBopd": 3820.0,
    "averageWaterCutPct": 66.6,
    "totalGasRateMscfd": 1840.0,
    "activeWells": 9,
    "downWells": 1,
    "fleetAvailabilityPct": 90.0,
    "totalDefermentBpd": 520.0
  }
  ```

#### Card 4: `proof-overlay-chart` (Multi-Channel Diagnostic Evidence)
- **Component:** `ProofOverlayChartCard.tsx`
- **Payload Contract:**
  ```json
  {
    "channels": [
      {
        "channel_id": "pip_psi",
        "name": "Intake Pressure",
        "unit": "psi",
        "series": [
          { "timestamp": "2026-10-12T04:00:00Z", "value": 410.0 },
          { "timestamp": "2026-10-12T04:15:00Z", "value": 182.0 }
        ]
      }
    ]
  }
  ```

> [!NOTE]
> For other card IDs (e.g., `subsystem-equalizer`, `smart-fault-card`, `vfm-ribbon`), the Dock currently renders a **Recommended Visual Widget Badge** with a custom icon and label. If the Agent team wishes to display rich UI for these cards, they must coordinate component development as described in Section 5.

---

### 4.3 Pump Curve Zero-Fabrication Rule (Omit in v1)
Under [`handoff/H6_PUMP_CURVES_AVAILABILITY_AND_PROVENANCE.md`](file:///a:/TAS-AI/esp-insight-suite/handoff/H6_PUMP_CURVES_AVAILABILITY_AND_PROVENANCE.md):
- When catalog digitized pump curves are unavailable, the Agent **MUST NOT** synthesize or invent an H-Q curve.
- The Agent **MUST OMIT** the `pump-curve` card ID in v1 rather than showing a misleading placeholder or fake curve.

---

## 5. Code Modification Boundaries: Allowed vs. Strictly Prohibited

To maintain stability, avoid merge conflicts, and protect critical real-time SCADA infrastructure, strict boundaries are enforced regarding what the Agent Team may and may not modify in the Dashboard repository (`esp-insight-suite`).

```
+----------------------------------------------------------------------------------------------------+
|                                    CODE MODIFICATION MATRIX                                       |
+---------------------------------------------------+------------------------------------------------+
|          ALLOWED (COORDINATED COLLABORATION)       |          STRICTLY PROHIBITED (CORE BREACH)     |
+---------------------------------------------------+------------------------------------------------+
| [x] New Visual Card TSX components in Dock        | [!] SCADA Ingestion & OPC-UA Gateways          |
| [x] Card type definitions in types/fleetCards.ts  | [!] Production PostgreSQL Telemetry Schema     |
| [x] Scoped CSS styles in AgentDock.module.css     | [!] Non-Dock Frontend Views (Fleet, Twins, VFM)|
| [x] Adding baseline YAMLs to config/baselines/    | [!] NDJSON Protocol & 65s Watchdog Removal     |
| [x] Updating sync_baselines_to_agent.py manifest  | [!] Direct Writes to Database or Telemetry Bus |
+---------------------------------------------------+------------------------------------------------+
```

### 5.1 What the Agent Team IS ALLOWED to Change in Dashboard Suite Code

1. **New Visual Card Components:**
   - **Path:** `esp-insight-suite/src/agent-dock/components/cards/`
   - The Agent Team may author new React TSX components to render rich visual cards (e.g., `SubsystemEqualizerCard.tsx`, `SmartFaultCard.tsx`).
   - Must export new cards from `src/agent-dock/components/cards/index.ts`.
2. **Card Type Definitions & Reducer Routing:**
   - **Paths:**
     - `esp-insight-suite/src/agent-dock/types/fleetCards.ts` (Add interface definitions for card data payloads).
     - `esp-insight-suite/src/agent-dock/components/VisualCardPlaceholder.tsx` (Route new card IDs to their rich component).
3. **Agent Dock Styling Refinements:**
   - **Path:** `esp-insight-suite/src/agent-dock/AgentDock.module.css`
   - Adjust styling, animations, bubble widths, or badge appearances, provided all rules remain scoped strictly to `.dock*` or local CSS module classes.
4. **Governed Baseline Files & Sync Manifest:**
   - **Paths:**
     - `config/baselines/*.yaml`
     - `scripts/sync_baselines_to_agent.py` (`SYNC_FILES` list)
   - When introducing new governed thresholds or failure taxonomy patterns, the Agent Team may add new YAML files to `config/baselines/` and register them in the sync script.

---

### 5.2 What the Agent Team IS STRICTLY PROHIBITED from Changing

1. **SCADA Ingestion & Protocol Gateways:**
   - **Paths:** `cced_esp/backend/services/opcua_gateway_service.py`, `cced_esp/backend/services/mqtt_service.py`, `bin/` simulator binaries.
   - **Rule:** The Agent team must NEVER alter SCADA polling intervals, OPC-UA node IDs, MQTT subscriptions, or simulated device topologies.
2. **Production Telemetry Database & Schemas:**
   - **Target:** PostgreSQL `esp_apm_db:5433` (`opg_well_telemetry`, `esp_events`).
   - **Rule:** The Agent service has **READ-ONLY** access. Executing write queries (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`) against telemetry or event tables is strictly prohibited.
3. **Non-Dock Dashboard Views & Core UI Layout:**
   - **Paths:** `src/components/`, `src/views/`, `src/pages/` (outside `src/agent-dock/`).
   - **Rule:** The Agent team must not touch the main navigation bar, 3D digital twin canvas (`WellboreViewer3D`), VFM ribbon calculations, alarm banner, or standard chart components.
4. **Bypassing the NDJSON Streaming Protocol & Watchdog:**
   - **Paths:** `src/agent-dock/services/ndjsonStream.ts`, `src/agent-dock/services/agentClient.ts`.
   - **Rule:** The 65-second safety watchdog, UTF-8 chunk buffering, and NDJSON line-parsing contracts must remain intact. Responses must not be converted into blocking single-payload JSON endpoints.
5. **Hardcoding Mock Data in Dashboard UI:**
   - **Rule:** The Agent team must not introduce hardcoded fake telemetry values or synthetic test responses into the frontend codebase. All dynamic data must arrive over the query stream.

---

## 6. Verification & Compliance Checklist for Agent Team

Before releasing any build of the new Agent Service, the Agent Team must verify and satisfy the following checklist:

- [ ] **Port & Route Compliance:** Service listens on port `8091` and responds to `POST /query`.
- [ ] **NDJSON Framing:** Every message frame is terminated with `\n` and conforms to `types/frames.ts`.
- [ ] **Heartbeat Latency:** Initial frame emits within 5s; no inter-frame delay exceeds 10s.
- [ ] **Stream Termination:** Every successful stream terminates with `{"type": "done", "status": "completed"}`.
- [ ] **Zero-Fabrication:** Offline wells (`FS-014`, `FS-044`, `FS-116`, `FWS-004`) receive standard offline notices with 0 fabricated telemetry points.
- [ ] **Missing Pump Curves:** Unverified pump curve cards are omitted in v1 rather than rendered with synthetic data.
- [ ] **7-Step XAI Narrative:** All single-well diagnostics contain all 7 structured explanation steps.
- [ ] **Evidence Citations:** Natural language assertions cite concrete sensor tags and timestamps.
- [ ] **Card Payload Conformity:** Visual cards validate against the TypeScript interfaces in `types/fleetCards.ts`.
- [ ] **Baseline Synchronization:** Agent baselines match SHA-256 hashes generated by `scripts/sync_baselines_to_agent.py`.
