---
title: "Domain 11: Conversational Intelligence & Server-Side Session Layer"
date: "2026-10-15"
type: "feat"
topic: "domain-11-conversational-session-layer"
artifact_contract: "ce-unified-plan/v1"
artifact_readiness: "requirements-only"
product_contract_source: "ce-brainstorm"
execution: "code"
---

# Domain 11: Conversational Intelligence & Server-Side Session Layer

## Goal Capsule

- Objective: Enable field operators and petroleum engineers to audit the exact live telemetry and physics baselines behind diagnostic answers, conduct follow-up inquiries, reframe metrics without restating wells, and queue compound requests within a continuous 24-hour operational session.
- Means: Implement an in-memory server-side session layer (`session_id -> SessionState`) in `agent_service_v2` that preserves structured telemetry snapshots, baseline envelope evaluations, active UI screen coordinates, and queued deferred intents across request boundaries.
- Product Authority: Covers Domain 11 (Conversational) capabilities for `agent_service_v2`. Surrounding domains (Domains 1–10, OPC UA physical write gateways) are established and out of active scope.
- Open Blockers: None.

## Product Contract

### Summary
A server-side conversational session layer for `agent_service_v2` that preserves structured execution state across turns (entities, telemetry snapshots, physics inputs, active route, and pending intents). This enables operators to audit the live evidence behind any copilot answer ("What data did you use?"), ask follow-up questions, pivot metrics ("What about temperature?"), and resolve compound multi-well requests.

### Problem Frame
The ESP APM copilot currently executes requests with high mathematical accuracy and sub-3ms routing speed, but treats each incoming HTTP call as an isolated event. Although `conversation_history` is passed as raw text in the request payload, the copilot lacks access to its own previous computational ground truth—it cannot cite the exact raw SCADA readings, limit envelopes, or diagnostic hypotheses that generated its last answer. When an operator asks *"What data did you use?"* or *"Why did you diagnose high vibration?"*, the copilot is forced to guess or re-query. Furthermore, compound queries (e.g. asking two questions in one prompt) drop the secondary request, and metric reframing requires repeating the well identifier every time.

### Key Decisions
- session-settled: In-memory session dictionary (`session_id -> SessionState`) over external Redis — provides zero-dependency container portability and instantaneous state lookups, with a 24-hour inactivity TTL and automatic LRU eviction.
- session-settled: Sub-capability 11.2 (Evidence Inquiry: *"What data did you use?"*) prioritized as the primary anchor — formats an explicit engineering audit table in Markdown with live telemetry, baselines, and deviations, plus a structured JSON dictionary.
- session-settled: Primary First + Interactive Follow-up for Compound Queries (11.7) — parses multiple intents, executes the primary intent immediately, preserves the secondary intent in the session queue, and suggests it as a prominent action chip: `[Continue: <Deferred Query>]`.
- session-settled: Interactive Disambiguation for Graph Explanation (11.3) — when an operator asks *"What does that chart mean?"* on a screen with multiple charts, prompts a clarification chip listing the charts present on that route from `ui_map.yaml`. If only one chart exists or the chart is explicitly named, explains it directly.
- session-settled: Standard SOP Template for Follow-up Justifications (11.1) — cites the diagnosed fault code from the petroleum engineering knowledge base coupled with the target well's recorded sensor evidence.
- session-settled: Session ID Lifecycle — auto-generates `sess_<uuid>` on the server when omitted, returning it in headers/payload, while binding headless command-line scripts to a persistent default session.
- session-settled: Session Memory Retention — 24-hour inactivity TTL retaining state across a full operational day before automated eviction.

### Requirements

#### Session State Management
- R1. The service shall maintain an in-memory session registry mapping `session_id` to `SessionState` records.
- R2. If a request arrives without a `session_id`, the service shall generate a unique `sess_<uuid>` identifier, bind the transaction to it, and return it in the response payload.
- R3. Inactive sessions shall automatically expire after 24 hours of inactivity.
- R4. After every successful query execution, `SessionState` shall record the resolved intent, target entity (well/cluster/event), full structured evidence snapshot (raw SCADA values, baseline limits, deviations), and active `page_route`.

#### Evidence Inquiry (Capability 11.2)
- R5. When a query matches evidence inquiry triggers (e.g., *"what data did you use"*, *"show the evidence"*, *"what numbers were behind that"*, *"data source"*), the router shall classify the intent as `EVIDENCE_INQUIRY`.
- R6. The response for `EVIDENCE_INQUIRY` shall present a Markdown audit table detailing: Telemetry Signal Name, Raw Value with Engineering Units, Baseline Reference Limit, % Deviation, Timestamp of SCADA Sample, and PostgreSQL Source Table (`opg_well_telemetry`, `events`, `asset_registry`).
- R7. The response for `EVIDENCE_INQUIRY` shall populate the `structured_data` field with an `evidence_audit` object containing machine-readable telemetry snapshots for frontend inspection.

#### Follow-up on Prior Answer (Capability 11.1)
- R8. When a query asks for justification of a prior claim (e.g., *"why did you say that"*, *"why vibration"*), the router shall classify the intent as `FOLLOW_UP_JUSTIFY`.
- R9. The response shall cite the diagnosed fault code from the local engineering knowledge base and explain how the prior recorded telemetry deviation triggered that rule.

#### Graph & Chart Explanation (Capability 11.3)
- R10. When a query asks about visual components (e.g., *"what does that chart mean"*, *"explain this graph"*), the router shall classify the intent as `GRAPH_EXPLAIN`.
- R11. If the current `page_route` contains multiple charts and the query does not name one, the copilot shall return an interactive clarification question listing the charts available on that screen as suggested options.
- R12. If a single chart matches the route or is named in the prompt, the copilot shall explain its engineering purpose, axes, and operational interpretation guidelines based on `ui_map.yaml`.

#### Clarification on Ambiguity (Capability 11.4)
- R13. When a query contains a diagnostic action without a resolvable well entity in the prompt or session state, the copilot shall emit `needs_clarification=True` with suggested options.

#### Multi-Turn Context & Pronoun Resolution (Capabilities 11.5 & 11.6)
- R14. Pronouns (*"it"*, *"its"*, *"that well"*, *"the pump"*) shall automatically bind to `SessionState.last_entity` before falling back to raw conversation history scanning.
- R15. Multi-turn context shall preserve the active well entity across at least 10 conversational turns within the same session.

#### Deferred Intent Handling & Compound Queries (Capability 11.7)
- R16. When a user prompt contains multiple discrete requests joined by conjunctions (*"and also"*, *"plus"*, *";"*), the router shall detect the compound structure.
- R17. The copilot shall execute the primary intent immediately, record the secondary intent in `SessionState.deferred_intents`, and output a suggested action chip `[Continue: <Secondary Query>]`.
- R18. If the operator selects the continuation chip or types *"continue"*, the queued secondary intent shall execute immediately without requiring the user to retype the query.

#### Reframing & Metric Pivoting (Capability 11.8)
- R19. When an operator queries a standalone metric (e.g., *"What about temperature?"*, *"Show vibration now"*) following an earlier well inquiry, the copilot shall bind the query to `SessionState.last_entity`.
- R20. The copilot shall return a focused subsystem telemetry report for the specified metric on that well.

### User Flows

#### Flow 1: Evidence Audit Flow (Capability 11.2)
1. Turn 1 (User): *"Why did well FNW-001 trip?"*
2. Turn 1 (Copilot): Diagnoses `HIGH_VIBRATION` with 2.45g peak, recommended LOTO checks, and saves evidence snapshot in session.
3. Turn 2 (User): *"What data did you use to make that diagnosis?"*
4. Turn 2 (Copilot): Emits formatted Markdown audit table displaying peak radial vibration (2.45g vs 2.0g limit, +22.5% deviation), PIP (397.2 PSI vs 350.0 baseline), and motor temperature from `opg_well_telemetry` at `2026-10-12 10:34:35`.

#### Flow 2: Compound Query & Deferred Continuation Flow (Capability 11.7)
1. Turn 1 (User): *"Diagnose FNW-001 and also compare FS-004 vs FS-006"*
2. Turn 1 (Copilot): Executes `EVENT_DIAGNOSE` for FNW-001, queues `MULTI_WELL_COMPARE` for FS-004 vs FS-006, and displays action chip `[Continue: Compare FS-004 vs FS-006]`.
3. Turn 2 (User): Clicks `[Continue: Compare FS-004 vs FS-006]` or types *"continue"*.
4. Turn 2 (Copilot): Pops the queued intent from session memory and returns the side-by-side comparison report immediately.

#### Flow 3: Metric Reframing Flow (Capability 11.8)
1. Turn 1 (User): *"What is the current status of FS-004?"*
2. Turn 1 (Copilot): Reports health status of well FS-004 (Running, 83.0 BPD, normal electrical current). Session binds `last_entity = 'FS-004'`.
3. Turn 2 (User): *"What about its temperature?"*
4. Turn 2 (Copilot): Resolves metric pivot to thermal subsystem for FS-004 and outputs motor temperature (84.5°C vs 110.0°C limit, normal thermal operating envelope).

### Acceptance Examples

- AE1. (Evidence Audit): Given a previous diagnosis of FNW-001, when the user queries *"What data did you use?"*, the response contains an audit table with the exact vibration, motor current, and intake pressure values from the previous diagnosis, matching live PostgreSQL ground truth.
- AE2. (Session Persistence): Given a `session_id = sess_test_01`, a well established in Turn 1 remains the active entity in Turn 5 without re-mentioning the well ID.
- AE3. (Compound Splitting): Given the prompt *"Check FS-017 health and triage offline wells"*, the copilot diagnoses FS-017 and queues the triage ranking as an action chip.
- AE4. (Interactive Chart Disambiguation): On route `/wells/FS-004`, when the user asks *"What does that chart mean?"*, the copilot asks whether they want the 4-Subsystem Equalizer or the 2D String Visualizer.
- AE5. (SOP Follow-up): When asking *"Why vibration?"* after an FNW-001 diagnosis, the copilot outputs the petroleum engineering definition of bearing wear / mechanical imbalance and cites the 2.45g vibration spike.

### Scope Boundaries

#### In-Scope
- Server-side in-memory session manager with 24-hour TTL and LRU cleanup.
- All 8 Domain 11 capabilities: 11.1 Follow-up, 11.2 Evidence Inquiry, 11.3 Graph Explanation, 11.4 Clarification, 11.5 Multi-turn Context, 11.6 Pronoun Resolution, 11.7 Deferred Compound Intent, 11.8 Reframing.
- Integration into `agent_service_v2/app/ai/router.py`, `esp_diagnosis_service.py`, and `main.py`.
- Automated regression suite validating all 8 conversational capabilities with session verification.

#### Out-of-Scope
- Redis or database persistence for sessions (strictly in-memory).
- Multi-user authentication or session token authorization.
- SCADA physical actuation or remote pump control (strict read-only safety boundary preserved).

### Success Criteria

- SC1. 100% of Domain 11 conversational regression tests pass green across all 8 capabilities.
- SC2. Evidence inquiries cite live SQL values with 0.0% discrepancy from PostgreSQL `esp_apm_db`.
- SC3. Compound queries cleanly split and offer one-click continuation without data loss.
- SC4. Session lookups execute with sub-1ms overhead in Python memory.
