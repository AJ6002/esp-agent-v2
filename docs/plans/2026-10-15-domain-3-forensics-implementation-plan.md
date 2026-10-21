# Domain 3 Implementation Plan: Trip Root-Cause Diagnostics & Physics Classification

**Status**: Planned & Aligned with Dashboard Specifications  
**Branch**: `dev-domain`  
**Target Systems**: `agent_service_v2` & `apps/api`  
**Database**: PostgreSQL Server 184 (`esp_apm_db`)  
**LLM Gateway**: Server 188 (`Qwen2.5-Coder-3B-Instruct-Q4_K_M`)  

---

## 1. Architectural Overview & Design Decisions

Based on the `/grill-me` alignment and Dashboard Team specifications:
1. **Single Source of Truth**: All event metadata (`events`), telemetry streams (`opg_well_telemetry`), and asset parameters (`asset_registry`) reside exclusively in PostgreSQL on Server 184. No SQLite or local flat-files are involved.
2. **15-Min / 5-Min Telemetry Forensics Window**: The telemetry window queried around the trip event is expanded to 900s pre-trip ($T_{-900s}$) and 300s post-trip ($T_{+300s}$) to perfectly match the time series viewed by operators in the `/events/$eventId` workspace.
3. **Disambiguation for Multi-Event Assets**:
   - When a specific `event_id` is supplied (e.g., `EV-20261012-103435-FNW-001-878`), diagnosis is executed immediately.
   - When only a `well_id` is supplied (e.g., "Why did well FNW-001 trip?") and multiple trip events exist in the database, the Copilot surfaces an interactive clarification prompt displaying recent trip timestamps with the latest event marked `(Recommended)` alongside prior events.
   - When only 1 event exists, it diagnoses directly.
4. **Dashboard-Ready Structured Payload**: Emits `pre_trip_window_start`, `trip_timestamp`, `post_trip_window_end`, `resolved_path: "/events/" + event_id`, and full `deviations` array for direct binding with `<EventInvestigationWorkspace />`.
5. **7-Pillar Forensic Markdown Report**: Renders Executive Summary, Baseline Deviation Table, Co-Inflection Window, Ranked Hypotheses with API RP 11S citations, Field Confirmation Tests, Deep-Link button, and Next Steps.

---

## 2. Technical Implementation Breakdown

### Task 1: Telemetry Window Expansion in `esp_diagnosis_service.py`
- Modify `get_telemetry_window`:
  - `pre_window_sec = 900` (15 minutes)
  - `post_window_sec = 300` (5 minutes)
  - Extract sensor vectors: `vibration_g`, `motor_current_a`, `intake_pressure_psi`, `discharge_pressure_psi`, `motor_temperature_c`, `frequency_hz`, `flow_rate_bpd`.
  - Calculate rate of change across the 15-minute window for accurate pre-trip degradation trends.

### Task 2: Multi-Event Disambiguation Engine
- Implement `check_well_trip_events(well_id: str)`:
  - Query PostgreSQL `events` table for all recorded trips for the well.
  - If $>1$ events exist and user query does NOT specify `event_id`, return `HybridRouteResult(intent=ESPIntentEnum.EVENT_DIAGNOSE, needs_clarification=True)` with:
    - `clarification_question`: *"Well {well_id} has {count} trip incidents recorded. Which event would you like to diagnose?"*
    - `suggested_options`:
      - `[Diagnose Latest Trip: {latest_id} ({latest_ts})]`
      - `[Diagnose Prior Trip: {prior_id} ({prior_ts})]`
      - `[View Reliability History for {well_id}]`

### Task 3: Forensic Payload Alignment for Dashboard Binding
- In `synthesize_xai_report`:
  - Populate exact timestamps:
    - `trip_timestamp`: ISO 8601 string of `event_data["timestamp"]`
    - `pre_trip_window_start`: ISO 8601 string of `event_data["timestamp"] - timedelta(minutes=15)`
    - `post_trip_window_end`: ISO 8601 string of `event_data["timestamp"] + timedelta(minutes=5)`
  - Populate navigation:
    - `resolved_path`: `f"/events/{event_id}"`
    - `route_title`: `f"Event Investigation Workspace ({event_id})"`
  - Populate deviations table with baseline vs 15-min pre-trip values and threshold violation flags.

### Task 4: Dual-Service Parity Sync
- Mirror all enhancements between `agent_service_v2` and `apps/api`:
  - `agent_service_v2/app/services/esp_diagnosis_service.py`
  - `apps/api/app/services/esp_diagnosis_service.py`

### Task 5: Empirical Verification & Regression Testing
- Write test runner `test_domain3_forensics.py`:
  - Test 1: Explicit Event ID diagnosis (`EV-20261012-103435-FNW-001-878`) -> Immediate 7-pillar report.
  - Test 2: Single-event well diagnosis -> Immediate report.
  - Test 3: Multi-event well without event ID -> Disambiguation prompt with interactive chips.
  - Test 4: Selection of chip -> Successful diagnosis.
  - Test 5: Verify structured payload timestamps (`trip_timestamp`, `pre_trip_window_start`, `post_trip_window_end`) and `resolved_path`.
- Run all 60 existing domain regression tests to guarantee zero regressions.

---

## 3. Verification Criteria
- [ ] 100% of Domain 3 queries return structured data containing `pre_trip_window_start`, `trip_timestamp`, and `resolved_path: "/events/{event_id}"`.
- [ ] Multi-event queries trigger clean HITL disambiguation chips without hardcoded assumptions.
- [ ] Existing 60-query benchmark maintains 100% pass rate.
