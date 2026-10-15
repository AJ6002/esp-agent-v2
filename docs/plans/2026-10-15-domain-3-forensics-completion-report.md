# Domain 3 Completion & Verification Report: Trip Root-Cause Diagnostics & Forensics

**Execution Timestamp**: 2026-10-15 22:05:00 UTC  
**Active Branch**: `dev-domain`  
**Database**: PostgreSQL Server 184 (`esp_apm_db`)  
**LLM Gateway**: Server 188 (`Qwen2.5-Coder-3B-Instruct-Q4_K_M`)  
**Target Services**: `agent_service_v2` & `apps/api` (100% Dual Parity)  

---

## 1. Executive Summary

Domain 3 (Trip Root-Cause Diagnostics & Physics Classification) has been upgraded and certified to full alignment with the Dashboard Team's integration specifications:
- **15-Min Pre-Trip / 5-Min Post-Trip Forensics Window**: Telemetry retrieval around trip events in `opg_well_telemetry` now spans a $T_{-900s}$ to $T_{+300s}$ window, ensuring rate-of-change and physical deviation math match the visual chart window in `<EventInvestigationWorkspace />`.
- **Multi-Event HITL Disambiguation**: When an operator queries why a well stopped/tripped without an explicit event ID, and the well has multiple historical trip incidents recorded in PostgreSQL, the Copilot surfaces an interactive disambiguation prompt displaying the recent event timestamps (with the latest marked `(Recommended)`).
- **Dashboard-Ready Structured Payload**: Emits `trip_timestamp`, `pre_trip_window_start`, `post_trip_window_end`, `resolved_path: "/events/" + event_id`, and full physical deviations array for instant component binding.
- **7-Pillar Markdown Forensic Report**: Renders Executive Summary, Baseline Deviation Table, Inflection Window, Ranked Hypotheses, Field Confirmation Tests, Deep-Link to `/events/$eventId`, and Safety Next Steps.

---

## 2. Technical Modifications

| File | Changes Made |
|:---|:---|
| [`agent_service_v2/app/services/esp_diagnosis_service.py`](file:///a:/TAS-AI/industrial-maintenance-copilot-master/agent_service_v2/app/services/esp_diagnosis_service.py) | • Added `get_well_recent_events` for querying recent trips from `events` table.<br>• Updated `get_telemetry_window` to default to 900s pre-trip and 300s post-trip.<br>• Added `trip_timestamp`, `pre_trip_window_start`, `post_trip_window_end`, `resolved_path`, and deep link to `synthesize_xai_report`. |
| [`agent_service_v2/app/ai/router.py`](file:///a:/TAS-AI/industrial-maintenance-copilot-master/agent_service_v2/app/ai/router.py) | • Added multi-event disambiguation check for `EVENT_DIAGNOSE` when $>1$ events exist and user did not specify event ID or "latest".<br>• Staged session memory tracking during disambiguation. |
| [`apps/api/app/services/esp_diagnosis_service.py`](file:///a:/TAS-AI/industrial-maintenance-copilot-master/apps/api/app/services/esp_diagnosis_service.py) | • Mirrored 15-min window expansion and forensic payload enhancements for API parity. |
| [`apps/api/app/ai/router.py`](file:///a:/TAS-AI/industrial-maintenance-copilot-master/apps/api/app/ai/router.py) | • Mirrored multi-event disambiguation and session tracking. |
| [`agent_service_v2/test_domain3_forensics.py`](file:///a:/TAS-AI/industrial-maintenance-copilot-master/agent_service_v2/test_domain3_forensics.py) | • Added dedicated automated test suite testing explicit event ID, multi-event clarification, latest bypass, and 15-min window parameters. |

---

## 3. Verification & Empirical Results

### 3.1 Domain 3 Dedicated Test Suite (`test_domain3_forensics.py`)
```text
Ran 5 tests in 6.442s
OK (100% Pass)
```
- `test_explicit_event_id_diagnosis`: PASS (Returns full 7-pillar report, `/events/$eventId` deep link, and ISO timestamps).
- `test_multi_event_clarification_on_ambiguous_well`: PASS (Triggers HITL clarification chips on wells with multiple trips).
- `test_explicit_latest_event_bypass`: PASS (Diagnoses latest event directly when user says "latest").
- `test_15min_pre_5min_post_telemetry_window`: PASS (Validates 900s pre / 300s post window spans).
- `test_recent_events_lookup`: PASS (Validates PostgreSQL query for recent events).

### 3.2 Full 60-Query 12-Domain Regression Benchmark
```text
=====================================================================================
BENCHMARK COMPLETE: 60/60 Queries Passed (100.0%) | Avg Latency: 1871.05ms
=====================================================================================
```
- Zero regressions across all 12 domains.
- Domain 3 queries executed in average $1,033.0\text{ ms}$.
