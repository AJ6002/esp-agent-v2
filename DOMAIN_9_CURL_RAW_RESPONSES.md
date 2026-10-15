# Domain 9: UI / Navigation / Route Awareness Raw cURL Audit Log

**Audit Execution Time**: 2026-10-14T19:41:34.740146Z  
**Target Environment**: FastAPI Backend (`:8000`), Qwen 2.5 Coder 3B (`Server 188`)  
**Total Queries Evaluated**: 33  

---

## Summary Matrix

| # | Category | Query | Intent | Route ID | Path / Status | End Tag Verified |
|:---:|---|---|:---:|:---:|:---:|:---:|
| **01** | 9.1 Route | *"what is the Working Status page?"* | `UI_NAVIGATION` | `route.working_status` | `/working-status` | `YES` |
| **02** | 9.1 Route | *"explain the Working Status screen"* | `UI_NAVIGATION` | `route.working_status` | `/working-status` | `YES` |
| **03** | 9.1 Route | *"what is the Fleet Cockpit page?"* | `UI_NAVIGATION` | `route.fleet_cockpit` | `/` | `YES` |
| **04** | 9.1 Route | *"where is the fleet cockpit?"* | `UI_NAVIGATION` | `route.fleet_cockpit` | `/` | `YES` |
| **05** | 9.1 Route | *"what is the Well Monitor screen?"* | `UI_NAVIGATION` | `route.well_detail` | `/wells/FS-017` | `YES` |
| **06** | 9.1 Route | *"explain the single well monitor screen"* | `UI_NAVIGATION` | `route.well_detail` | `/wells/FS-017` | `YES` |
| **07** | 9.1 Route | *"what is the Live Calculations page?"* | `UI_NAVIGATION` | `route.live_calculations` | `/live-calculations` | `YES` |
| **08** | 9.1 Route | *"how do I navigate to live calculations?"* | `UI_NAVIGATION` | `route.live_calculations` | `/live-calculations` | `YES` |
| **09** | 9.1 Route | *"what is the Event Intelligence page?"* | `UI_NAVIGATION` | `route.event_intelligence` | `/events` | `YES` |
| **10** | 9.1 Route | *"where do I find trip forensics?"* | `UI_NAVIGATION` | `route.event_intelligence` | `/events` | `YES` |
| **11** | 9.1 Route | *"what is the Reports Hub page?"* | `UI_NAVIGATION` | `route.reports_hub` | `/reports` | `YES` |
| **12** | 9.1 Route | *"where are operational reports?"* | `UI_NAVIGATION` | `route.reports_hub` | `/reports` | `YES` |
| **13** | 9.1 Route | *"what is the Scenario Simulator page?"* | `UI_NAVIGATION` | `route.scenario_simulator` | `/custom-testing` | `YES` |
| **14** | 9.1 Route | *"how do I get to custom testing bench?"* | `UI_NAVIGATION` | `route.scenario_simulator` | `/custom-testing` | `YES` |
| **15** | 9.1 Navigation | *"show all screens in operations workspace"* | `UI_NAVIGATION` | `navigation.operations_workspace` | `/` | `YES` |
| **16** | 9.1 Navigation | *"list all available routes"* | `UI_NAVIGATION` | `navigation.operations_workspace` | `/` | `YES` |
| **17** | 9.2 Component | *"where can I find the 2D ESP string visualizer?"* | `UI_NAVIGATION` | `route.well_detail` | `/wells/FS-017` | `YES` |
| **18** | 9.2 Component | *"what does the 4-subsystem equalizer display?"* | `UI_NAVIGATION` | `route.well_detail` | `/wells/FS-017` | `YES` |
| **19** | 9.2 Component | *"where are live pump performance curves?"* | `UI_NAVIGATION` | `route.well_detail` | `/wells/FS-017` | `YES` |
| **20** | 9.2 Component | *"what does the FleetTable display?"* | `UI_NAVIGATION` | `route.fleet_cockpit` | `/` | `YES` |
| **21** | 9.2 Component | *"where is the Top KPI strip located?"* | `UI_NAVIGATION` | `route.fleet_cockpit` | `/` | `YES` |
| **22** | 9.2 Component | *"what displays in the Working Status diagnostic queue?"* | `UI_NAVIGATION` | `route.working_status` | `/working-status` | `YES` |
| **23** | 9.2 Component | *"what is the Fleet KPI Formulas Editor?"* | `UI_NAVIGATION` | `route.live_calculations` | `/live-calculations` | `YES` |
| **24** | 9.2 Component | *"where can I find the Scenario Configuration Bench?"* | `UI_NAVIGATION` | `route.scenario_simulator` | `/custom-testing` | `YES` |
| **25** | 9.3 Concept | *"what is the 14-fault classifier spectrum?"* | `UI_NAVIGATION` | `route.working_status` | `/working-status` | `YES` |
| **26** | 9.3 Concept | *"what is virtual flow metering (VFM)?"* | `UI_NAVIGATION` | `route.live_calculations` | `/live-calculations` | `YES` |
| **27** | 9.3 Concept | *"what are affinity laws in the platform?"* | `UI_NAVIGATION` | `route.well_detail` | `/wells/FS-017` | `YES` |
| **28** | 9.3 Concept | *"what is the zero fabrication data readiness gate?"* | `UI_NAVIGATION` | `route.reports_hub` | `/reports` | `YES` |
| **29** | 9.3 Concept | *"what is the recommended operating range (ROR)?"* | `UI_NAVIGATION` | `route.well_detail` | `/wells/FS-017` | `YES` |
| **30** | 9.4 Parametric Binding | *"where can I find pump curves for FS-017?"* | `UI_NAVIGATION` | `route.well_detail` | `/wells/FS-017` | `YES` |
| **31** | 9.4 Parametric Binding | *"show well detail for FNW-001"* | `UI_NAVIGATION` | `route.well_detail` | `/wells/FNW-001` | `YES` |
| **32** | 9.5 Out of Scope | *"where is the pizza ordering screen?"* | `UI_NAVIGATION` | `route.unknown` | `-` | `YES` |
| **33** | 9.5 Out of Scope | *"what is the 3D seismic voxel viewer page?"* | `UI_NAVIGATION` | `route.unknown` | `-` | `YES` |

---

## Detailed Raw API Requests & Responses

### Query #01: what is the Working Status page?
**Category**: `9.1 Route` | **Latency**: `2807ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "what is the Working Status page?"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] Well Working Status & Fault Spectrum\n\n**Route Path**: `/working-status` | **Type**: `Route` | **Source**: `[route.working_status]`\n\nThe Working Status page is a real-time dashboard that provides detailed information about the operational status of wells and the likelihood of faults. It includes a 14-fault machine learning classifier probability spectrum, deterministic SCADA operating envelopes, and a master-detail exception queue. This page is accessible through the `/working-status` path in the ESP Insight Suite application, which is part of the Advait ESP-PMM platform. The page is implemented in TypeScript and JavaScript, with helper logic and backend API specifications provided in the specified files. The live streaming protocol used is WebSocket, which allows for real-time updates to the dashboard.\n\n[route.working_status]\n\n---\n### Quick Navigation Actions:\n- [Open /working-status]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: Well Working Status & Fault Spectrum",
      "excerpt": "Real-time 14-fault ML classifier probability spectrum, deterministic SCADA operating envelopes, and master-detail exception queue.",
      "relevance_score": 1.0,
      "url": "/working-status"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /working-status",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.working_status",
    "entry_type": "route",
    "title": "Well Working Status & Fault Spectrum",
    "path": "/working-status",
    "resolved_path": "/working-status",
    "summary": "Real-time 14-fault ML classifier probability spectrum, deterministic SCADA operating envelopes, and master-detail exception queue.",
    "narrative": "The Working Status page is a real-time dashboard that provides detailed information about the operational status of wells and the likelihood of faults. It includes a 14-fault machine learning classifier probability spectrum, deterministic SCADA operating envelopes, and a master-detail exception queue. This page is accessible through the `/working-status` path in the ESP Insight Suite application, which is part of the Advait ESP-PMM platform. The page is implemented in TypeScript and JavaScript, with helper logic and backend API specifications provided in the specified files. The live streaming protocol used is WebSocket, which allows for real-time updates to the dashboard.\n\n[route.working_status]",
    "related_routes": [
      "route.fleet_cockpit",
      "route.well_detail",
      "route.event_intelligence"
    ],
    "suggested_options": [
      "Open /working-status",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] Well Working Status & Fault Spectrum\n\n**Route Path**: `/working-status` | **Type**: `Route` | **Source**: `[route.working_status]`\n\nThe Working Status page is a real-time dashboard that provides detailed information about the operational status of wells and the likelihood of faults. It includes a 14-fault machine learning classifier probability spectrum, deterministic SCADA operating envelopes, and a master-detail exception queue. This page is accessible through the `/working-status` path in the ESP Insight Suite application, which is part of the Advait ESP-PMM platform. The page is implemented in TypeScript and JavaScript, with helper logic and backend API specifications provided in the specified files. The live streaming protocol used is WebSocket, which allows for real-time updates to the dashboard.\n\n[route.working_status]\n\n---\n### Quick Navigation Actions:\n- [Open /working-status]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] Well Working Status & Fault Spectrum
> 
> **Route Path**: `/working-status` | **Type**: `Route` | **Source**: `[route.working_status]`
> 
> The Working Status page is a real-time dashboard that provides detailed information about the operational status of wells and the likelihood of faults. It includes a 14-fault machine learning classifier probability spectrum, deterministic SCADA operating envelopes, and a master-detail exception queue. This page is accessible through the `/working-status` path in the ESP Insight Suite application, which is part of the Advait ESP-PMM platform. The page is implemented in TypeScript and JavaScript, with helper logic and backend API specifications provided in the specified files. The live streaming protocol used is WebSocket, which allows for real-time updates to the dashboard.
> 
> [route.working_status]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /working-status]
> - [Where are Live Calculations?]
> - [Go to Fleet Cockpit]
> 

---

### Query #02: explain the Working Status screen
**Category**: `9.1 Route` | **Latency**: `1715ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "explain the Working Status screen"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] Well Working Status & Fault Spectrum\n\n**Route Path**: `/working-status` | **Type**: `Route` | **Source**: `[route.working_status]`\n\nThe Working Status screen in the ESP Insight Suite provides real-time information about the operational status of wells and the likelihood of faults. It includes a 14-fault machine learning classifier probability spectrum, deterministic SCADA operating envelopes, and a master-detail exception queue. This comprehensive view helps engineers monitor the health and potential issues of their wells in real-time, enabling proactive maintenance and optimization.\n\n[route.working_status]\n\n---\n### Quick Navigation Actions:\n- [Open /working-status]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: Well Working Status & Fault Spectrum",
      "excerpt": "Real-time 14-fault ML classifier probability spectrum, deterministic SCADA operating envelopes, and master-detail exception queue.",
      "relevance_score": 1.0,
      "url": "/working-status"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /working-status",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.working_status",
    "entry_type": "route",
    "title": "Well Working Status & Fault Spectrum",
    "path": "/working-status",
    "resolved_path": "/working-status",
    "summary": "Real-time 14-fault ML classifier probability spectrum, deterministic SCADA operating envelopes, and master-detail exception queue.",
    "narrative": "The Working Status screen in the ESP Insight Suite provides real-time information about the operational status of wells and the likelihood of faults. It includes a 14-fault machine learning classifier probability spectrum, deterministic SCADA operating envelopes, and a master-detail exception queue. This comprehensive view helps engineers monitor the health and potential issues of their wells in real-time, enabling proactive maintenance and optimization.\n\n[route.working_status]",
    "related_routes": [
      "route.fleet_cockpit",
      "route.well_detail",
      "route.event_intelligence"
    ],
    "suggested_options": [
      "Open /working-status",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] Well Working Status & Fault Spectrum\n\n**Route Path**: `/working-status` | **Type**: `Route` | **Source**: `[route.working_status]`\n\nThe Working Status screen in the ESP Insight Suite provides real-time information about the operational status of wells and the likelihood of faults. It includes a 14-fault machine learning classifier probability spectrum, deterministic SCADA operating envelopes, and a master-detail exception queue. This comprehensive view helps engineers monitor the health and potential issues of their wells in real-time, enabling proactive maintenance and optimization.\n\n[route.working_status]\n\n---\n### Quick Navigation Actions:\n- [Open /working-status]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] Well Working Status & Fault Spectrum
> 
> **Route Path**: `/working-status` | **Type**: `Route` | **Source**: `[route.working_status]`
> 
> The Working Status screen in the ESP Insight Suite provides real-time information about the operational status of wells and the likelihood of faults. It includes a 14-fault machine learning classifier probability spectrum, deterministic SCADA operating envelopes, and a master-detail exception queue. This comprehensive view helps engineers monitor the health and potential issues of their wells in real-time, enabling proactive maintenance and optimization.
> 
> [route.working_status]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /working-status]
> - [Where are Live Calculations?]
> - [Go to Fleet Cockpit]
> 

---

### Query #03: what is the Fleet Cockpit page?
**Category**: `9.1 Route` | **Latency**: `3918ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "what is the Fleet Cockpit page?"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] ESP Fleet Cockpit\n\n**Route Path**: `/` | **Type**: `Route` | **Source**: `[route.fleet_cockpit]`\n\nThe Fleet Cockpit page is a centralized dashboard that provides real-time Key Performance Indicators (KPIs) for the entire fleet. It includes a multi-discipline asset table view and a top-10 attention queue, allowing for efficient monitoring and management of assets across various departments.\n\nThe Fleet Cockpit page is accessible via the root URL (`/`) and is part of the ESP Insight Suite application. It is built using the `ESP Insight Suite` application workspace and is located in the `src/routes/index.tsx` file. The page is composed of several sub-components, including the `FleetTable` and `EspWellVisual`, which display asset data and visualizations, respectively. The `ui.tsx` file contains the UI components, and the `useEspFleet.ts` hook provides the core data for the page.\n\nThis page is crucial for fleet managers to quickly assess the overall health and performance of their assets, identify areas for improvement, and make informed decisions to optimize operations.\n\n[route.fleet_cockpit]\n\n---\n### Quick Navigation Actions:\n- [Open /]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: ESP Fleet Cockpit",
      "excerpt": "Centralized fleet-wide surveillance cockpit providing real-time KPI metrics, multi-discipline asset table views, and a top-10 attention queue.",
      "relevance_score": 1.0,
      "url": "/"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.fleet_cockpit",
    "entry_type": "route",
    "title": "ESP Fleet Cockpit",
    "path": "/",
    "resolved_path": "/",
    "summary": "Centralized fleet-wide surveillance cockpit providing real-time KPI metrics, multi-discipline asset table views, and a top-10 attention queue.",
    "narrative": "The Fleet Cockpit page is a centralized dashboard that provides real-time Key Performance Indicators (KPIs) for the entire fleet. It includes a multi-discipline asset table view and a top-10 attention queue, allowing for efficient monitoring and management of assets across various departments.\n\nThe Fleet Cockpit page is accessible via the root URL (`/`) and is part of the ESP Insight Suite application. It is built using the `ESP Insight Suite` application workspace and is located in the `src/routes/index.tsx` file. The page is composed of several sub-components, including the `FleetTable` and `EspWellVisual`, which display asset data and visualizations, respectively. The `ui.tsx` file contains the UI components, and the `useEspFleet.ts` hook provides the core data for the page.\n\nThis page is crucial for fleet managers to quickly assess the overall health and performance of their assets, identify areas for improvement, and make informed decisions to optimize operations.\n\n[route.fleet_cockpit]",
    "related_routes": [
      "route.working_status",
      "route.well_detail",
      "route.live_calculations"
    ],
    "suggested_options": [
      "Open /",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] ESP Fleet Cockpit\n\n**Route Path**: `/` | **Type**: `Route` | **Source**: `[route.fleet_cockpit]`\n\nThe Fleet Cockpit page is a centralized dashboard that provides real-time Key Performance Indicators (KPIs) for the entire fleet. It includes a multi-discipline asset table view and a top-10 attention queue, allowing for efficient monitoring and management of assets across various departments.\n\nThe Fleet Cockpit page is accessible via the root URL (`/`) and is part of the ESP Insight Suite application. It is built using the `ESP Insight Suite` application workspace and is located in the `src/routes/index.tsx` file. The page is composed of several sub-components, including the `FleetTable` and `EspWellVisual`, which display asset data and visualizations, respectively. The `ui.tsx` file contains the UI components, and the `useEspFleet.ts` hook provides the core data for the page.\n\nThis page is crucial for fleet managers to quickly assess the overall health and performance of their assets, identify areas for improvement, and make informed decisions to optimize operations.\n\n[route.fleet_cockpit]\n\n---\n### Quick Navigation Actions:\n- [Open /]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] ESP Fleet Cockpit
> 
> **Route Path**: `/` | **Type**: `Route` | **Source**: `[route.fleet_cockpit]`
> 
> The Fleet Cockpit page is a centralized dashboard that provides real-time Key Performance Indicators (KPIs) for the entire fleet. It includes a multi-discipline asset table view and a top-10 attention queue, allowing for efficient monitoring and management of assets across various departments.
> 
> The Fleet Cockpit page is accessible via the root URL (`/`) and is part of the ESP Insight Suite application. It is built using the `ESP Insight Suite` application workspace and is located in the `src/routes/index.tsx` file. The page is composed of several sub-components, including the `FleetTable` and `EspWellVisual`, which display asset data and visualizations, respectively. The `ui.tsx` file contains the UI components, and the `useEspFleet.ts` hook provides the core data for the page.
> 
> This page is crucial for fleet managers to quickly assess the overall health and performance of their assets, identify areas for improvement, and make informed decisions to optimize operations.
> 
> [route.fleet_cockpit]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /]
> - [What is Working Status?]
> - [Where are Live Calculations?]
> 

---

### Query #04: where is the fleet cockpit?
**Category**: `9.1 Route` | **Latency**: `1605ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "where is the fleet cockpit?"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] ESP Fleet Cockpit\n\n**Route Path**: `/` | **Type**: `Route` | **Source**: `[route.fleet_cockpit]`\n\nThe fleet cockpit is located at the root path `/` of the ESP Insight Suite. It serves as the central hub for real-time KPI metrics, multi-discipline asset table views, and a top-10 attention queue. The fleet cockpit is accessed via the ESP Insight Suite application workspace, which is the primary interface for users to interact with the platform.\n\n[route.fleet_cockpit]\n\n---\n### Quick Navigation Actions:\n- [Open /]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: ESP Fleet Cockpit",
      "excerpt": "Centralized fleet-wide surveillance cockpit providing real-time KPI metrics, multi-discipline asset table views, and a top-10 attention queue.",
      "relevance_score": 1.0,
      "url": "/"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.fleet_cockpit",
    "entry_type": "route",
    "title": "ESP Fleet Cockpit",
    "path": "/",
    "resolved_path": "/",
    "summary": "Centralized fleet-wide surveillance cockpit providing real-time KPI metrics, multi-discipline asset table views, and a top-10 attention queue.",
    "narrative": "The fleet cockpit is located at the root path `/` of the ESP Insight Suite. It serves as the central hub for real-time KPI metrics, multi-discipline asset table views, and a top-10 attention queue. The fleet cockpit is accessed via the ESP Insight Suite application workspace, which is the primary interface for users to interact with the platform.\n\n[route.fleet_cockpit]",
    "related_routes": [
      "route.working_status",
      "route.well_detail",
      "route.live_calculations"
    ],
    "suggested_options": [
      "Open /",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] ESP Fleet Cockpit\n\n**Route Path**: `/` | **Type**: `Route` | **Source**: `[route.fleet_cockpit]`\n\nThe fleet cockpit is located at the root path `/` of the ESP Insight Suite. It serves as the central hub for real-time KPI metrics, multi-discipline asset table views, and a top-10 attention queue. The fleet cockpit is accessed via the ESP Insight Suite application workspace, which is the primary interface for users to interact with the platform.\n\n[route.fleet_cockpit]\n\n---\n### Quick Navigation Actions:\n- [Open /]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] ESP Fleet Cockpit
> 
> **Route Path**: `/` | **Type**: `Route` | **Source**: `[route.fleet_cockpit]`
> 
> The fleet cockpit is located at the root path `/` of the ESP Insight Suite. It serves as the central hub for real-time KPI metrics, multi-discipline asset table views, and a top-10 attention queue. The fleet cockpit is accessed via the ESP Insight Suite application workspace, which is the primary interface for users to interact with the platform.
> 
> [route.fleet_cockpit]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /]
> - [What is Working Status?]
> - [Where are Live Calculations?]
> 

---

### Query #05: what is the Well Monitor screen?
**Category**: `9.1 Route` | **Latency**: `2233ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "what is the Well Monitor screen?"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] Well Monitor & Downhole Detail\n\n**Route Path**: `/wells/FS-017` | **Type**: `Route` | **Source**: `[route.well_detail]`\n\nThe Well Monitor screen is a single-well surveillance console that provides detailed information about the well. It includes a 2D downhole schematic visualizer, live H-Q pump performance curve, 4-subsystem equalizer, and wellbore depth pressure profile. This comprehensive view helps engineers monitor the well's performance and identify any issues or anomalies in real-time. The screen is accessible via the path `/wells/FS-017` and is part of the ESP Insight Suite application workspace.\n\n[route.well_detail]\n\n---\n### Quick Navigation Actions:\n- [Open /wells/FS-017]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: Well Monitor & Downhole Detail",
      "excerpt": "Single-well surveillance console featuring 2D downhole schematic visualizer, live H-Q pump performance curve, 4-subsystem equalizer, and wellbore depth pressure profile.",
      "relevance_score": 1.0,
      "url": "/wells/FS-017"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /wells/FS-017",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.well_detail",
    "entry_type": "route",
    "title": "Well Monitor & Downhole Detail",
    "path": "/wells/$wellId",
    "resolved_path": "/wells/FS-017",
    "summary": "Single-well surveillance console featuring 2D downhole schematic visualizer, live H-Q pump performance curve, 4-subsystem equalizer, and wellbore depth pressure profile.",
    "narrative": "The Well Monitor screen is a single-well surveillance console that provides detailed information about the well. It includes a 2D downhole schematic visualizer, live H-Q pump performance curve, 4-subsystem equalizer, and wellbore depth pressure profile. This comprehensive view helps engineers monitor the well's performance and identify any issues or anomalies in real-time. The screen is accessible via the path `/wells/FS-017` and is part of the ESP Insight Suite application workspace.\n\n[route.well_detail]",
    "related_routes": [
      "route.fleet_cockpit",
      "route.working_status",
      "route.live_calculations"
    ],
    "suggested_options": [
      "Open /wells/FS-017",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] Well Monitor & Downhole Detail\n\n**Route Path**: `/wells/FS-017` | **Type**: `Route` | **Source**: `[route.well_detail]`\n\nThe Well Monitor screen is a single-well surveillance console that provides detailed information about the well. It includes a 2D downhole schematic visualizer, live H-Q pump performance curve, 4-subsystem equalizer, and wellbore depth pressure profile. This comprehensive view helps engineers monitor the well's performance and identify any issues or anomalies in real-time. The screen is accessible via the path `/wells/FS-017` and is part of the ESP Insight Suite application workspace.\n\n[route.well_detail]\n\n---\n### Quick Navigation Actions:\n- [Open /wells/FS-017]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] Well Monitor & Downhole Detail
> 
> **Route Path**: `/wells/FS-017` | **Type**: `Route` | **Source**: `[route.well_detail]`
> 
> The Well Monitor screen is a single-well surveillance console that provides detailed information about the well. It includes a 2D downhole schematic visualizer, live H-Q pump performance curve, 4-subsystem equalizer, and wellbore depth pressure profile. This comprehensive view helps engineers monitor the well's performance and identify any issues or anomalies in real-time. The screen is accessible via the path `/wells/FS-017` and is part of the ESP Insight Suite application workspace.
> 
> [route.well_detail]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /wells/FS-017]
> - [What is Working Status?]
> - [Where are Live Calculations?]
> - [Go to Fleet Cockpit]
> 

---

### Query #06: explain the single well monitor screen
**Category**: `9.1 Route` | **Latency**: `3193ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "explain the single well monitor screen"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] Well Monitor & Downhole Detail\n\n**Route Path**: `/wells/FS-017` | **Type**: `Route` | **Source**: `[route.well_detail]`\n\nThe Single Well Monitor & Downhole Detail screen is a comprehensive surveillance console designed to provide real-time insights into a single well. It features a 2D downhole schematic visualizer, which allows users to visualize the wellbore and downhole components in a detailed manner. Additionally, the screen includes a live H-Q pump performance curve, which displays the pump's efficiency and performance over time. The 4-subsystem equalizer provides a visual representation of the well's subsystems, helping users monitor and adjust them as needed. The wellbore depth pressure profile offers a graphical representation of the well's pressure and depth, allowing users to track changes over time and make informed decisions. This screen is part of the ESP Insight Suite application workspace and is accessible via the `/wells/FS-017` path.\n\n[route.well_detail]\n\n---\n### Quick Navigation Actions:\n- [Open /wells/FS-017]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: Well Monitor & Downhole Detail",
      "excerpt": "Single-well surveillance console featuring 2D downhole schematic visualizer, live H-Q pump performance curve, 4-subsystem equalizer, and wellbore depth pressure profile.",
      "relevance_score": 1.0,
      "url": "/wells/FS-017"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /wells/FS-017",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.well_detail",
    "entry_type": "route",
    "title": "Well Monitor & Downhole Detail",
    "path": "/wells/$wellId",
    "resolved_path": "/wells/FS-017",
    "summary": "Single-well surveillance console featuring 2D downhole schematic visualizer, live H-Q pump performance curve, 4-subsystem equalizer, and wellbore depth pressure profile.",
    "narrative": "The Single Well Monitor & Downhole Detail screen is a comprehensive surveillance console designed to provide real-time insights into a single well. It features a 2D downhole schematic visualizer, which allows users to visualize the wellbore and downhole components in a detailed manner. Additionally, the screen includes a live H-Q pump performance curve, which displays the pump's efficiency and performance over time. The 4-subsystem equalizer provides a visual representation of the well's subsystems, helping users monitor and adjust them as needed. The wellbore depth pressure profile offers a graphical representation of the well's pressure and depth, allowing users to track changes over time and make informed decisions. This screen is part of the ESP Insight Suite application workspace and is accessible via the `/wells/FS-017` path.\n\n[route.well_detail]",
    "related_routes": [
      "route.fleet_cockpit",
      "route.working_status",
      "route.live_calculations"
    ],
    "suggested_options": [
      "Open /wells/FS-017",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] Well Monitor & Downhole Detail\n\n**Route Path**: `/wells/FS-017` | **Type**: `Route` | **Source**: `[route.well_detail]`\n\nThe Single Well Monitor & Downhole Detail screen is a comprehensive surveillance console designed to provide real-time insights into a single well. It features a 2D downhole schematic visualizer, which allows users to visualize the wellbore and downhole components in a detailed manner. Additionally, the screen includes a live H-Q pump performance curve, which displays the pump's efficiency and performance over time. The 4-subsystem equalizer provides a visual representation of the well's subsystems, helping users monitor and adjust them as needed. The wellbore depth pressure profile offers a graphical representation of the well's pressure and depth, allowing users to track changes over time and make informed decisions. This screen is part of the ESP Insight Suite application workspace and is accessible via the `/wells/FS-017` path.\n\n[route.well_detail]\n\n---\n### Quick Navigation Actions:\n- [Open /wells/FS-017]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] Well Monitor & Downhole Detail
> 
> **Route Path**: `/wells/FS-017` | **Type**: `Route` | **Source**: `[route.well_detail]`
> 
> The Single Well Monitor & Downhole Detail screen is a comprehensive surveillance console designed to provide real-time insights into a single well. It features a 2D downhole schematic visualizer, which allows users to visualize the wellbore and downhole components in a detailed manner. Additionally, the screen includes a live H-Q pump performance curve, which displays the pump's efficiency and performance over time. The 4-subsystem equalizer provides a visual representation of the well's subsystems, helping users monitor and adjust them as needed. The wellbore depth pressure profile offers a graphical representation of the well's pressure and depth, allowing users to track changes over time and make informed decisions. This screen is part of the ESP Insight Suite application workspace and is accessible via the `/wells/FS-017` path.
> 
> [route.well_detail]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /wells/FS-017]
> - [What is Working Status?]
> - [Where are Live Calculations?]
> - [Go to Fleet Cockpit]
> 

---

### Query #07: what is the Live Calculations page?
**Category**: `9.1 Route` | **Latency**: `3059ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "what is the Live Calculations page?"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] Live Telemetry & Derived Physics Engine\n\n**Route Path**: `/live-calculations` | **Type**: `Route` | **Source**: `[route.live_calculations]`\n\nThe Live Calculations page is a real-time dashboard that provides edge telemetry and derived physics calculations. It includes features such as Virtual Flow Metering (VFM), higher-order physics inspection, and a fleet KPI formula editor. This page is accessible through the `/live-calculations` path and is part of the Operations workspace. The page is supported by the FleetKpiFormulasEditor component and utilizes hooks like useFleetFormulae and useEspFleet for data retrieval and manipulation. The backend API for this page includes endpoints for fetching live calculations (`GET /api/esp/live-calculations`) and saving formulae to disk (`POST /api/esp/formulae/save-to-disk`). The page also uses a WebSocket (`LIV`) for real-time updates.\n\n[route.live_calculations]\n\n---\n### Quick Navigation Actions:\n- [Open /live-calculations]\n- [What is Working Status?]\n- [Go to Fleet Cockpit]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: Live Telemetry & Derived Physics Engine",
      "excerpt": "Real-time 1-second edge telemetry calculation bench, Virtual Flow Metering (VFM), higher-order physics inspection, and fleet KPI formula editor.",
      "relevance_score": 1.0,
      "url": "/live-calculations"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /live-calculations",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.live_calculations",
    "entry_type": "route",
    "title": "Live Telemetry & Derived Physics Engine",
    "path": "/live-calculations",
    "resolved_path": "/live-calculations",
    "summary": "Real-time 1-second edge telemetry calculation bench, Virtual Flow Metering (VFM), higher-order physics inspection, and fleet KPI formula editor.",
    "narrative": "The Live Calculations page is a real-time dashboard that provides edge telemetry and derived physics calculations. It includes features such as Virtual Flow Metering (VFM), higher-order physics inspection, and a fleet KPI formula editor. This page is accessible through the `/live-calculations` path and is part of the Operations workspace. The page is supported by the FleetKpiFormulasEditor component and utilizes hooks like useFleetFormulae and useEspFleet for data retrieval and manipulation. The backend API for this page includes endpoints for fetching live calculations (`GET /api/esp/live-calculations`) and saving formulae to disk (`POST /api/esp/formulae/save-to-disk`). The page also uses a WebSocket (`LIV`) for real-time updates.\n\n[route.live_calculations]",
    "related_routes": [
      "route.fleet_cockpit",
      "route.well_detail",
      "route.scenario_simulator"
    ],
    "suggested_options": [
      "Open /live-calculations",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] Live Telemetry & Derived Physics Engine\n\n**Route Path**: `/live-calculations` | **Type**: `Route` | **Source**: `[route.live_calculations]`\n\nThe Live Calculations page is a real-time dashboard that provides edge telemetry and derived physics calculations. It includes features such as Virtual Flow Metering (VFM), higher-order physics inspection, and a fleet KPI formula editor. This page is accessible through the `/live-calculations` path and is part of the Operations workspace. The page is supported by the FleetKpiFormulasEditor component and utilizes hooks like useFleetFormulae and useEspFleet for data retrieval and manipulation. The backend API for this page includes endpoints for fetching live calculations (`GET /api/esp/live-calculations`) and saving formulae to disk (`POST /api/esp/formulae/save-to-disk`). The page also uses a WebSocket (`LIV`) for real-time updates.\n\n[route.live_calculations]\n\n---\n### Quick Navigation Actions:\n- [Open /live-calculations]\n- [What is Working Status?]\n- [Go to Fleet Cockpit]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] Live Telemetry & Derived Physics Engine
> 
> **Route Path**: `/live-calculations` | **Type**: `Route` | **Source**: `[route.live_calculations]`
> 
> The Live Calculations page is a real-time dashboard that provides edge telemetry and derived physics calculations. It includes features such as Virtual Flow Metering (VFM), higher-order physics inspection, and a fleet KPI formula editor. This page is accessible through the `/live-calculations` path and is part of the Operations workspace. The page is supported by the FleetKpiFormulasEditor component and utilizes hooks like useFleetFormulae and useEspFleet for data retrieval and manipulation. The backend API for this page includes endpoints for fetching live calculations (`GET /api/esp/live-calculations`) and saving formulae to disk (`POST /api/esp/formulae/save-to-disk`). The page also uses a WebSocket (`LIV`) for real-time updates.
> 
> [route.live_calculations]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /live-calculations]
> - [What is Working Status?]
> - [Go to Fleet Cockpit]
> 

---

### Query #08: how do I navigate to live calculations?
**Category**: `9.1 Route` | **Latency**: `3691ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "how do I navigate to live calculations?"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] Live Telemetry & Derived Physics Engine\n\n**Route Path**: `/live-calculations` | **Type**: `Route` | **Source**: `[route.live_calculations]`\n\nTo navigate to the Live Calculations screen, you can access it by visiting the following URL:\n\n```\n/live-calculations\n```\n\nThis route is part of the Operations workspace and is located at the path `/live-calculations`. The screen provides real-time 1-second edge telemetry calculation bench, Virtual Flow Metering (VFM), higher-order physics inspection, and a fleet KPI formula editor. The Live Calculations screen is supported by the `FleetKpiFormulasEditor` component, which is located at `src/components/esp/FleetKpiFormulasEditor.tsx`. The necessary hooks for this functionality are `useFleetFormulae.ts` and `useEspFleet.ts`, and the backend API endpoints for this route are `GET /api/esp/live-calculations` and `POST /api/esp/formulae/save-to-disk`. Additionally, the screen uses a WebSocket (`LIV`) for streaming protocol.\n\n[route.live_calculations]\n\n---\n### Quick Navigation Actions:\n- [Open /live-calculations]\n- [What is Working Status?]\n- [Go to Fleet Cockpit]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: Live Telemetry & Derived Physics Engine",
      "excerpt": "Real-time 1-second edge telemetry calculation bench, Virtual Flow Metering (VFM), higher-order physics inspection, and fleet KPI formula editor.",
      "relevance_score": 1.0,
      "url": "/live-calculations"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /live-calculations",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.live_calculations",
    "entry_type": "route",
    "title": "Live Telemetry & Derived Physics Engine",
    "path": "/live-calculations",
    "resolved_path": "/live-calculations",
    "summary": "Real-time 1-second edge telemetry calculation bench, Virtual Flow Metering (VFM), higher-order physics inspection, and fleet KPI formula editor.",
    "narrative": "To navigate to the Live Calculations screen, you can access it by visiting the following URL:\n\n```\n/live-calculations\n```\n\nThis route is part of the Operations workspace and is located at the path `/live-calculations`. The screen provides real-time 1-second edge telemetry calculation bench, Virtual Flow Metering (VFM), higher-order physics inspection, and a fleet KPI formula editor. The Live Calculations screen is supported by the `FleetKpiFormulasEditor` component, which is located at `src/components/esp/FleetKpiFormulasEditor.tsx`. The necessary hooks for this functionality are `useFleetFormulae.ts` and `useEspFleet.ts`, and the backend API endpoints for this route are `GET /api/esp/live-calculations` and `POST /api/esp/formulae/save-to-disk`. Additionally, the screen uses a WebSocket (`LIV`) for streaming protocol.\n\n[route.live_calculations]",
    "related_routes": [
      "route.fleet_cockpit",
      "route.well_detail",
      "route.scenario_simulator"
    ],
    "suggested_options": [
      "Open /live-calculations",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] Live Telemetry & Derived Physics Engine\n\n**Route Path**: `/live-calculations` | **Type**: `Route` | **Source**: `[route.live_calculations]`\n\nTo navigate to the Live Calculations screen, you can access it by visiting the following URL:\n\n```\n/live-calculations\n```\n\nThis route is part of the Operations workspace and is located at the path `/live-calculations`. The screen provides real-time 1-second edge telemetry calculation bench, Virtual Flow Metering (VFM), higher-order physics inspection, and a fleet KPI formula editor. The Live Calculations screen is supported by the `FleetKpiFormulasEditor` component, which is located at `src/components/esp/FleetKpiFormulasEditor.tsx`. The necessary hooks for this functionality are `useFleetFormulae.ts` and `useEspFleet.ts`, and the backend API endpoints for this route are `GET /api/esp/live-calculations` and `POST /api/esp/formulae/save-to-disk`. Additionally, the screen uses a WebSocket (`LIV`) for streaming protocol.\n\n[route.live_calculations]\n\n---\n### Quick Navigation Actions:\n- [Open /live-calculations]\n- [What is Working Status?]\n- [Go to Fleet Cockpit]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] Live Telemetry & Derived Physics Engine
> 
> **Route Path**: `/live-calculations` | **Type**: `Route` | **Source**: `[route.live_calculations]`
> 
> To navigate to the Live Calculations screen, you can access it by visiting the following URL:
> 
> ```
> /live-calculations
> ```
> 
> This route is part of the Operations workspace and is located at the path `/live-calculations`. The screen provides real-time 1-second edge telemetry calculation bench, Virtual Flow Metering (VFM), higher-order physics inspection, and a fleet KPI formula editor. The Live Calculations screen is supported by the `FleetKpiFormulasEditor` component, which is located at `src/components/esp/FleetKpiFormulasEditor.tsx`. The necessary hooks for this functionality are `useFleetFormulae.ts` and `useEspFleet.ts`, and the backend API endpoints for this route are `GET /api/esp/live-calculations` and `POST /api/esp/formulae/save-to-disk`. Additionally, the screen uses a WebSocket (`LIV`) for streaming protocol.
> 
> [route.live_calculations]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /live-calculations]
> - [What is Working Status?]
> - [Go to Fleet Cockpit]
> 

---

### Query #09: what is the Event Intelligence page?
**Category**: `9.1 Route` | **Latency**: `2498ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "what is the Event Intelligence page?"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] Event & Incident Intelligence Forensics\n\n**Route Path**: `/events` | **Type**: `Route` | **Source**: `[route.event_intelligence]`\n\nThe Event Intelligence page is a comprehensive dashboard designed to provide real-time surveillance of SCADA incident lifecycles. It includes features such as live duration counters, chronological raw event audit logs, and a dedicated 7-pillar trip forensics workspace. This page is accessible via the `/events` path and offers a unified view of incident management, allowing engineers to quickly identify and analyze events in a structured manner. The page is integrated into the Operations workspace and is accessible through the primary Forensics Component, `EventInvestigationWorkspace`, and the Live Rollup Component, `LiveStateStrip`.\n\n[route.event_intelligence]\n\n---\n### Quick Navigation Actions:\n- [Open /events]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: Event & Incident Intelligence Forensics",
      "excerpt": "Unified SCADA incident lifecycle surveillance with live duration counters, chronological raw event audit logs, and a dedicated 7-pillar trip forensics workspace.",
      "relevance_score": 1.0,
      "url": "/events"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /events",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.event_intelligence",
    "entry_type": "route",
    "title": "Event & Incident Intelligence Forensics",
    "path": "/events",
    "resolved_path": "/events",
    "summary": "Unified SCADA incident lifecycle surveillance with live duration counters, chronological raw event audit logs, and a dedicated 7-pillar trip forensics workspace.",
    "narrative": "The Event Intelligence page is a comprehensive dashboard designed to provide real-time surveillance of SCADA incident lifecycles. It includes features such as live duration counters, chronological raw event audit logs, and a dedicated 7-pillar trip forensics workspace. This page is accessible via the `/events` path and offers a unified view of incident management, allowing engineers to quickly identify and analyze events in a structured manner. The page is integrated into the Operations workspace and is accessible through the primary Forensics Component, `EventInvestigationWorkspace`, and the Live Rollup Component, `LiveStateStrip`.\n\n[route.event_intelligence]",
    "related_routes": [
      "route.fleet_cockpit",
      "route.working_status",
      "route.reports_hub"
    ],
    "suggested_options": [
      "Open /events",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] Event & Incident Intelligence Forensics\n\n**Route Path**: `/events` | **Type**: `Route` | **Source**: `[route.event_intelligence]`\n\nThe Event Intelligence page is a comprehensive dashboard designed to provide real-time surveillance of SCADA incident lifecycles. It includes features such as live duration counters, chronological raw event audit logs, and a dedicated 7-pillar trip forensics workspace. This page is accessible via the `/events` path and offers a unified view of incident management, allowing engineers to quickly identify and analyze events in a structured manner. The page is integrated into the Operations workspace and is accessible through the primary Forensics Component, `EventInvestigationWorkspace`, and the Live Rollup Component, `LiveStateStrip`.\n\n[route.event_intelligence]\n\n---\n### Quick Navigation Actions:\n- [Open /events]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] Event & Incident Intelligence Forensics
> 
> **Route Path**: `/events` | **Type**: `Route` | **Source**: `[route.event_intelligence]`
> 
> The Event Intelligence page is a comprehensive dashboard designed to provide real-time surveillance of SCADA incident lifecycles. It includes features such as live duration counters, chronological raw event audit logs, and a dedicated 7-pillar trip forensics workspace. This page is accessible via the `/events` path and offers a unified view of incident management, allowing engineers to quickly identify and analyze events in a structured manner. The page is integrated into the Operations workspace and is accessible through the primary Forensics Component, `EventInvestigationWorkspace`, and the Live Rollup Component, `LiveStateStrip`.
> 
> [route.event_intelligence]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /events]
> - [What is Working Status?]
> - [Where are Live Calculations?]
> - [Go to Fleet Cockpit]
> 

---

### Query #10: where do I find trip forensics?
**Category**: `9.1 Route` | **Latency**: `1457ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "where do I find trip forensics?"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] Trip Forensics Workspace\n\n**Route Path**: `/events` | **Type**: `Concept` | **Source**: `[route.event_intelligence]`\n\nThe trip forensics workspace is located at the path `/events` within the Event Intelligence & Forensics section of the platform. This workspace allows surveillance engineers and electrical technicians to analyze high-frequency telemetry preceding ESP trips, isolating electrical, mechanical, and process sensor trends to establish unambiguous root cause before restarting.\n\n[route.event_intelligence]\n\n---\n### Quick Navigation Actions:\n- [Open /events]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: Trip Forensics Workspace",
      "excerpt": "Forensic environment capturing high-frequency telemetry preceding trips for root-cause isolation.",
      "relevance_score": 1.0,
      "url": "/events"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /events",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.event_intelligence",
    "entry_type": "concept",
    "title": "Trip Forensics Workspace",
    "path": "/events",
    "resolved_path": "/events",
    "summary": "Forensic environment capturing high-frequency telemetry preceding trips for root-cause isolation.",
    "narrative": "The trip forensics workspace is located at the path `/events` within the Event Intelligence & Forensics section of the platform. This workspace allows surveillance engineers and electrical technicians to analyze high-frequency telemetry preceding ESP trips, isolating electrical, mechanical, and process sensor trends to establish unambiguous root cause before restarting.\n\n[route.event_intelligence]",
    "related_routes": [],
    "suggested_options": [
      "Open /events",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] Trip Forensics Workspace\n\n**Route Path**: `/events` | **Type**: `Concept` | **Source**: `[route.event_intelligence]`\n\nThe trip forensics workspace is located at the path `/events` within the Event Intelligence & Forensics section of the platform. This workspace allows surveillance engineers and electrical technicians to analyze high-frequency telemetry preceding ESP trips, isolating electrical, mechanical, and process sensor trends to establish unambiguous root cause before restarting.\n\n[route.event_intelligence]\n\n---\n### Quick Navigation Actions:\n- [Open /events]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] Trip Forensics Workspace
> 
> **Route Path**: `/events` | **Type**: `Concept` | **Source**: `[route.event_intelligence]`
> 
> The trip forensics workspace is located at the path `/events` within the Event Intelligence & Forensics section of the platform. This workspace allows surveillance engineers and electrical technicians to analyze high-frequency telemetry preceding ESP trips, isolating electrical, mechanical, and process sensor trends to establish unambiguous root cause before restarting.
> 
> [route.event_intelligence]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /events]
> - [What is Working Status?]
> - [Where are Live Calculations?]
> - [Go to Fleet Cockpit]
> 

---

### Query #11: what is the Reports Hub page?
**Category**: `9.1 Route` | **Latency**: `2540ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "what is the Reports Hub page?"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] Operational Reports & Governance Hub\n\n**Route Path**: `/reports` | **Type**: `Route` | **Source**: `[route.reports_hub]`\n\nThe Reports Hub page is a governed operational reporting hub that enforces zero-fabrication data gates, allows for custom reporting intervals, provides Advait-styled Excel/CSV exports, and tracks historical archive data. It is accessible via the path `/reports` and is part of the Operations workspace. The page is supported by various components such as `ReportBuilder.tsx`, `ReportPreview.tsx`, `InsufficientDataView.tsx`, and `ReportArchive.tsx`, which are located in the `src/components/esp/reports` directory. The governance and engine modules are handled by `src/lib/esp/historia`.\n\n[route.reports_hub]\n\n---\n### Quick Navigation Actions:\n- [Open /reports]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: Operational Reports & Governance Hub",
      "excerpt": "Governed operational reporting hub enforcing zero-fabrication data gates, custom reporting intervals, Advait-styled Excel/CSV exports, and historical archive tracking.",
      "relevance_score": 1.0,
      "url": "/reports"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /reports",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.reports_hub",
    "entry_type": "route",
    "title": "Operational Reports & Governance Hub",
    "path": "/reports",
    "resolved_path": "/reports",
    "summary": "Governed operational reporting hub enforcing zero-fabrication data gates, custom reporting intervals, Advait-styled Excel/CSV exports, and historical archive tracking.",
    "narrative": "The Reports Hub page is a governed operational reporting hub that enforces zero-fabrication data gates, allows for custom reporting intervals, provides Advait-styled Excel/CSV exports, and tracks historical archive data. It is accessible via the path `/reports` and is part of the Operations workspace. The page is supported by various components such as `ReportBuilder.tsx`, `ReportPreview.tsx`, `InsufficientDataView.tsx`, and `ReportArchive.tsx`, which are located in the `src/components/esp/reports` directory. The governance and engine modules are handled by `src/lib/esp/historia`.\n\n[route.reports_hub]",
    "related_routes": [
      "route.fleet_cockpit",
      "route.event_intelligence"
    ],
    "suggested_options": [
      "Open /reports",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] Operational Reports & Governance Hub\n\n**Route Path**: `/reports` | **Type**: `Route` | **Source**: `[route.reports_hub]`\n\nThe Reports Hub page is a governed operational reporting hub that enforces zero-fabrication data gates, allows for custom reporting intervals, provides Advait-styled Excel/CSV exports, and tracks historical archive data. It is accessible via the path `/reports` and is part of the Operations workspace. The page is supported by various components such as `ReportBuilder.tsx`, `ReportPreview.tsx`, `InsufficientDataView.tsx`, and `ReportArchive.tsx`, which are located in the `src/components/esp/reports` directory. The governance and engine modules are handled by `src/lib/esp/historia`.\n\n[route.reports_hub]\n\n---\n### Quick Navigation Actions:\n- [Open /reports]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] Operational Reports & Governance Hub
> 
> **Route Path**: `/reports` | **Type**: `Route` | **Source**: `[route.reports_hub]`
> 
> The Reports Hub page is a governed operational reporting hub that enforces zero-fabrication data gates, allows for custom reporting intervals, provides Advait-styled Excel/CSV exports, and tracks historical archive data. It is accessible via the path `/reports` and is part of the Operations workspace. The page is supported by various components such as `ReportBuilder.tsx`, `ReportPreview.tsx`, `InsufficientDataView.tsx`, and `ReportArchive.tsx`, which are located in the `src/components/esp/reports` directory. The governance and engine modules are handled by `src/lib/esp/historia`.
> 
> [route.reports_hub]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /reports]
> - [What is Working Status?]
> - [Where are Live Calculations?]
> - [Go to Fleet Cockpit]
> 

---

### Query #12: where are operational reports?
**Category**: `9.1 Route` | **Latency**: `2209ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "where are operational reports?"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] Operational Reports & Governance Hub\n\n**Route Path**: `/reports` | **Type**: `Route` | **Source**: `[route.reports_hub]`\n\nOperational reports are found in the **Operational Reports & Governance Hub**. You can access this hub by navigating to the path `/reports`. This hub is designed to enforce zero-fabrication data gates, allow for custom reporting intervals, and provides Advait-styled Excel/CSV exports. It also includes a historical archive tracking feature. The hub is part of the Operations workspace and is supported by various components such as `ReportBuilder.tsx`, `ReportPreview.tsx`, `InsufficientDataView.tsx`, and `ReportArchive.tsx`.\n\n[route.reports_hub]\n\n---\n### Quick Navigation Actions:\n- [Open /reports]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: Operational Reports & Governance Hub",
      "excerpt": "Governed operational reporting hub enforcing zero-fabrication data gates, custom reporting intervals, Advait-styled Excel/CSV exports, and historical archive tracking.",
      "relevance_score": 1.0,
      "url": "/reports"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /reports",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.reports_hub",
    "entry_type": "route",
    "title": "Operational Reports & Governance Hub",
    "path": "/reports",
    "resolved_path": "/reports",
    "summary": "Governed operational reporting hub enforcing zero-fabrication data gates, custom reporting intervals, Advait-styled Excel/CSV exports, and historical archive tracking.",
    "narrative": "Operational reports are found in the **Operational Reports & Governance Hub**. You can access this hub by navigating to the path `/reports`. This hub is designed to enforce zero-fabrication data gates, allow for custom reporting intervals, and provides Advait-styled Excel/CSV exports. It also includes a historical archive tracking feature. The hub is part of the Operations workspace and is supported by various components such as `ReportBuilder.tsx`, `ReportPreview.tsx`, `InsufficientDataView.tsx`, and `ReportArchive.tsx`.\n\n[route.reports_hub]",
    "related_routes": [
      "route.fleet_cockpit",
      "route.event_intelligence"
    ],
    "suggested_options": [
      "Open /reports",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] Operational Reports & Governance Hub\n\n**Route Path**: `/reports` | **Type**: `Route` | **Source**: `[route.reports_hub]`\n\nOperational reports are found in the **Operational Reports & Governance Hub**. You can access this hub by navigating to the path `/reports`. This hub is designed to enforce zero-fabrication data gates, allow for custom reporting intervals, and provides Advait-styled Excel/CSV exports. It also includes a historical archive tracking feature. The hub is part of the Operations workspace and is supported by various components such as `ReportBuilder.tsx`, `ReportPreview.tsx`, `InsufficientDataView.tsx`, and `ReportArchive.tsx`.\n\n[route.reports_hub]\n\n---\n### Quick Navigation Actions:\n- [Open /reports]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] Operational Reports & Governance Hub
> 
> **Route Path**: `/reports` | **Type**: `Route` | **Source**: `[route.reports_hub]`
> 
> Operational reports are found in the **Operational Reports & Governance Hub**. You can access this hub by navigating to the path `/reports`. This hub is designed to enforce zero-fabrication data gates, allow for custom reporting intervals, and provides Advait-styled Excel/CSV exports. It also includes a historical archive tracking feature. The hub is part of the Operations workspace and is supported by various components such as `ReportBuilder.tsx`, `ReportPreview.tsx`, `InsufficientDataView.tsx`, and `ReportArchive.tsx`.
> 
> [route.reports_hub]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /reports]
> - [What is Working Status?]
> - [Where are Live Calculations?]
> - [Go to Fleet Cockpit]
> 

---

### Query #13: what is the Scenario Simulator page?
**Category**: `9.1 Route` | **Latency**: `1317ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "what is the Scenario Simulator page?"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] What-If Scenario Simulator\n\n**Route Path**: `/custom-testing` | **Type**: `Route` | **Source**: `[route.scenario_simulator]`\n\nThe Scenario Simulator page is a bench designed for what-if operational scenario simulations. It includes 14-channel telemetry controls, calibrated fault presets, dynamic pump curve feedback, and thermal reliability margins. This page is accessible via the `/custom-testing` path and is part of the Operations workspace.\n\n[route.scenario_simulator]\n\n---\n### Quick Navigation Actions:\n- [Open /custom-testing]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: What-If Scenario Simulator",
      "excerpt": "What-if operational scenario simulation bench with 14-channel telemetry controls, calibrated fault presets, dynamic pump curve feedback, and thermal reliability margins.",
      "relevance_score": 1.0,
      "url": "/custom-testing"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /custom-testing",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.scenario_simulator",
    "entry_type": "route",
    "title": "What-If Scenario Simulator",
    "path": "/custom-testing",
    "resolved_path": "/custom-testing",
    "summary": "What-if operational scenario simulation bench with 14-channel telemetry controls, calibrated fault presets, dynamic pump curve feedback, and thermal reliability margins.",
    "narrative": "The Scenario Simulator page is a bench designed for what-if operational scenario simulations. It includes 14-channel telemetry controls, calibrated fault presets, dynamic pump curve feedback, and thermal reliability margins. This page is accessible via the `/custom-testing` path and is part of the Operations workspace.\n\n[route.scenario_simulator]",
    "related_routes": [
      "route.well_detail",
      "route.live_calculations"
    ],
    "suggested_options": [
      "Open /custom-testing",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] What-If Scenario Simulator\n\n**Route Path**: `/custom-testing` | **Type**: `Route` | **Source**: `[route.scenario_simulator]`\n\nThe Scenario Simulator page is a bench designed for what-if operational scenario simulations. It includes 14-channel telemetry controls, calibrated fault presets, dynamic pump curve feedback, and thermal reliability margins. This page is accessible via the `/custom-testing` path and is part of the Operations workspace.\n\n[route.scenario_simulator]\n\n---\n### Quick Navigation Actions:\n- [Open /custom-testing]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] What-If Scenario Simulator
> 
> **Route Path**: `/custom-testing` | **Type**: `Route` | **Source**: `[route.scenario_simulator]`
> 
> The Scenario Simulator page is a bench designed for what-if operational scenario simulations. It includes 14-channel telemetry controls, calibrated fault presets, dynamic pump curve feedback, and thermal reliability margins. This page is accessible via the `/custom-testing` path and is part of the Operations workspace.
> 
> [route.scenario_simulator]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /custom-testing]
> - [What is Working Status?]
> - [Where are Live Calculations?]
> - [Go to Fleet Cockpit]
> 

---

### Query #14: how do I get to custom testing bench?
**Category**: `9.1 Route` | **Latency**: `4392ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "how do I get to custom testing bench?"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] What-If Scenario Simulator\n\n**Route Path**: `/custom-testing` | **Type**: `Route` | **Source**: `[route.scenario_simulator]`\n\nTo access the What-If Scenario Simulator bench, you need to navigate to the `/custom-testing` path. This route is located in the `/custom-testing` directory of the platform, which is accessible from the Operations workspace.\n\n### Route Components\n\nThe What-If Scenario Simulator bench includes the following components:\n\n- **PumpCurveChart.tsx**: This component displays the pump curve feedback, which is crucial for understanding the performance of the pump under different conditions.\n- **calc.ts**: This file contains mathematical functions used to calculate various parameters, such as friction head and pressure-to-foot conversion.\n- **fleet.ts**: This file contains the FLEET dataset, which provides data on the fleet of pumps and their performance characteristics.\n\n### Backend Mathematical Provenance\n\nThe What-If Scenario Simulator bench is supported by mathematical functions implemented in the `calc.ts` file, which are referenced in the `esp_routes.py` file at lines 572, 575, 608, 675, and 2491. This ensures that the calculations are mathematically sound and reliable.\n\n[route.scenario_simulator]\n\n---\n### Quick Navigation Actions:\n- [Open /custom-testing]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: What-If Scenario Simulator",
      "excerpt": "What-if operational scenario simulation bench with 14-channel telemetry controls, calibrated fault presets, dynamic pump curve feedback, and thermal reliability margins.",
      "relevance_score": 1.0,
      "url": "/custom-testing"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /custom-testing",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.scenario_simulator",
    "entry_type": "route",
    "title": "What-If Scenario Simulator",
    "path": "/custom-testing",
    "resolved_path": "/custom-testing",
    "summary": "What-if operational scenario simulation bench with 14-channel telemetry controls, calibrated fault presets, dynamic pump curve feedback, and thermal reliability margins.",
    "narrative": "To access the What-If Scenario Simulator bench, you need to navigate to the `/custom-testing` path. This route is located in the `/custom-testing` directory of the platform, which is accessible from the Operations workspace.\n\n### Route Components\n\nThe What-If Scenario Simulator bench includes the following components:\n\n- **PumpCurveChart.tsx**: This component displays the pump curve feedback, which is crucial for understanding the performance of the pump under different conditions.\n- **calc.ts**: This file contains mathematical functions used to calculate various parameters, such as friction head and pressure-to-foot conversion.\n- **fleet.ts**: This file contains the FLEET dataset, which provides data on the fleet of pumps and their performance characteristics.\n\n### Backend Mathematical Provenance\n\nThe What-If Scenario Simulator bench is supported by mathematical functions implemented in the `calc.ts` file, which are referenced in the `esp_routes.py` file at lines 572, 575, 608, 675, and 2491. This ensures that the calculations are mathematically sound and reliable.\n\n[route.scenario_simulator]",
    "related_routes": [
      "route.well_detail",
      "route.live_calculations"
    ],
    "suggested_options": [
      "Open /custom-testing",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] What-If Scenario Simulator\n\n**Route Path**: `/custom-testing` | **Type**: `Route` | **Source**: `[route.scenario_simulator]`\n\nTo access the What-If Scenario Simulator bench, you need to navigate to the `/custom-testing` path. This route is located in the `/custom-testing` directory of the platform, which is accessible from the Operations workspace.\n\n### Route Components\n\nThe What-If Scenario Simulator bench includes the following components:\n\n- **PumpCurveChart.tsx**: This component displays the pump curve feedback, which is crucial for understanding the performance of the pump under different conditions.\n- **calc.ts**: This file contains mathematical functions used to calculate various parameters, such as friction head and pressure-to-foot conversion.\n- **fleet.ts**: This file contains the FLEET dataset, which provides data on the fleet of pumps and their performance characteristics.\n\n### Backend Mathematical Provenance\n\nThe What-If Scenario Simulator bench is supported by mathematical functions implemented in the `calc.ts` file, which are referenced in the `esp_routes.py` file at lines 572, 575, 608, 675, and 2491. This ensures that the calculations are mathematically sound and reliable.\n\n[route.scenario_simulator]\n\n---\n### Quick Navigation Actions:\n- [Open /custom-testing]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] What-If Scenario Simulator
> 
> **Route Path**: `/custom-testing` | **Type**: `Route` | **Source**: `[route.scenario_simulator]`
> 
> To access the What-If Scenario Simulator bench, you need to navigate to the `/custom-testing` path. This route is located in the `/custom-testing` directory of the platform, which is accessible from the Operations workspace.
> 
> ### Route Components
> 
> The What-If Scenario Simulator bench includes the following components:
> 
> - **PumpCurveChart.tsx**: This component displays the pump curve feedback, which is crucial for understanding the performance of the pump under different conditions.
> - **calc.ts**: This file contains mathematical functions used to calculate various parameters, such as friction head and pressure-to-foot conversion.
> - **fleet.ts**: This file contains the FLEET dataset, which provides data on the fleet of pumps and their performance characteristics.
> 
> ### Backend Mathematical Provenance
> 
> The What-If Scenario Simulator bench is supported by mathematical functions implemented in the `calc.ts` file, which are referenced in the `esp_routes.py` file at lines 572, 575, 608, 675, and 2491. This ensures that the calculations are mathematically sound and reliable.
> 
> [route.scenario_simulator]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /custom-testing]
> - [What is Working Status?]
> - [Where are Live Calculations?]
> - [Go to Fleet Cockpit]
> 

---

### Query #15: show all screens in operations workspace
**Category**: `9.1 Navigation` | **Latency**: `5607ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "show all screens in operations workspace"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] Operations Workspace Navigation Index\n\n**Route Path**: `/` | **Type**: `Navigation` | **Source**: `[navigation.operations_workspace]`\n\nThe Operations Workspace in the ADVAIT ESP-PMM platform provides a comprehensive real-time operational command center for surveillance engineers, production technologists, and control room operators. It includes the following screens:\n\n1. **Dashboard**: Offers a high-level overview of the operational status of the 10 active ESP assets across the Gathering Centers `GCS-03`, `GCS-04`, and `GCS-15`. Key performance indicators (KPIs) such as pump efficiency, pump pressure, and pump current are displayed to provide a quick snapshot of the system's performance.\n\n2. **Asset Overview**: Provides detailed information about each ESP asset, including its location, operational status, and key performance metrics. This screen allows users to quickly identify any issues or anomalies.\n\n3. **Event Log**: Displays a log of all events and faults that have occurred on the ESP assets. This includes both historical and real-time events, allowing users to track the progression of issues and take corrective action.\n\n4. **Alarm Management**: Alerts users to any alarms or warnings that have been triggered on the ESP assets. Users can view the details of each alarm, including the cause, severity, and any corrective actions that have been taken.\n\n5. **Historical Data**: Provides access to historical data for the ESP assets, allowing users to analyze trends and patterns over time. This includes data on pump performance, pressure, and current, as well as any other relevant metrics.\n\n6. **Configuration Management**:\n\n[navigation.operations_workspace]\n\n---\n### Quick Navigation Actions:\n- [Open /]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: Operations Workspace Navigation Index",
      "excerpt": "Operational command center for surveillance engineers, production technologists, and control room operators monitoring the 10 active Farha South ESP assets.",
      "relevance_score": 1.0,
      "url": "/"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "navigation.operations_workspace",
    "entry_type": "navigation",
    "title": "Operations Workspace Navigation Index",
    "path": null,
    "resolved_path": "/",
    "summary": "Operational command center for surveillance engineers, production technologists, and control room operators monitoring the 10 active Farha South ESP assets.",
    "narrative": "The Operations Workspace in the ADVAIT ESP-PMM platform provides a comprehensive real-time operational command center for surveillance engineers, production technologists, and control room operators. It includes the following screens:\n\n1. **Dashboard**: Offers a high-level overview of the operational status of the 10 active ESP assets across the Gathering Centers `GCS-03`, `GCS-04`, and `GCS-15`. Key performance indicators (KPIs) such as pump efficiency, pump pressure, and pump current are displayed to provide a quick snapshot of the system's performance.\n\n2. **Asset Overview**: Provides detailed information about each ESP asset, including its location, operational status, and key performance metrics. This screen allows users to quickly identify any issues or anomalies.\n\n3. **Event Log**: Displays a log of all events and faults that have occurred on the ESP assets. This includes both historical and real-time events, allowing users to track the progression of issues and take corrective action.\n\n4. **Alarm Management**: Alerts users to any alarms or warnings that have been triggered on the ESP assets. Users can view the details of each alarm, including the cause, severity, and any corrective actions that have been taken.\n\n5. **Historical Data**: Provides access to historical data for the ESP assets, allowing users to analyze trends and patterns over time. This includes data on pump performance, pressure, and current, as well as any other relevant metrics.\n\n6. **Configuration Management**:\n\n[navigation.operations_workspace]",
    "related_routes": [
      "route.fleet_cockpit",
      "route.working_status",
      "route.well_detail",
      "route.live_calculations",
      "route.event_intelligence",
      "route.reports_hub",
      "route.scenario_simulator"
    ],
    "suggested_options": [
      "Open /",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] Operations Workspace Navigation Index\n\n**Route Path**: `/` | **Type**: `Navigation` | **Source**: `[navigation.operations_workspace]`\n\nThe Operations Workspace in the ADVAIT ESP-PMM platform provides a comprehensive real-time operational command center for surveillance engineers, production technologists, and control room operators. It includes the following screens:\n\n1. **Dashboard**: Offers a high-level overview of the operational status of the 10 active ESP assets across the Gathering Centers `GCS-03`, `GCS-04`, and `GCS-15`. Key performance indicators (KPIs) such as pump efficiency, pump pressure, and pump current are displayed to provide a quick snapshot of the system's performance.\n\n2. **Asset Overview**: Provides detailed information about each ESP asset, including its location, operational status, and key performance metrics. This screen allows users to quickly identify any issues or anomalies.\n\n3. **Event Log**: Displays a log of all events and faults that have occurred on the ESP assets. This includes both historical and real-time events, allowing users to track the progression of issues and take corrective action.\n\n4. **Alarm Management**: Alerts users to any alarms or warnings that have been triggered on the ESP assets. Users can view the details of each alarm, including the cause, severity, and any corrective actions that have been taken.\n\n5. **Historical Data**: Provides access to historical data for the ESP assets, allowing users to analyze trends and patterns over time. This includes data on pump performance, pressure, and current, as well as any other relevant metrics.\n\n6. **Configuration Management**:\n\n[navigation.operations_workspace]\n\n---\n### Quick Navigation Actions:\n- [Open /]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] Operations Workspace Navigation Index
> 
> **Route Path**: `/` | **Type**: `Navigation` | **Source**: `[navigation.operations_workspace]`
> 
> The Operations Workspace in the ADVAIT ESP-PMM platform provides a comprehensive real-time operational command center for surveillance engineers, production technologists, and control room operators. It includes the following screens:
> 
> 1. **Dashboard**: Offers a high-level overview of the operational status of the 10 active ESP assets across the Gathering Centers `GCS-03`, `GCS-04`, and `GCS-15`. Key performance indicators (KPIs) such as pump efficiency, pump pressure, and pump current are displayed to provide a quick snapshot of the system's performance.
> 
> 2. **Asset Overview**: Provides detailed information about each ESP asset, including its location, operational status, and key performance metrics. This screen allows users to quickly identify any issues or anomalies.
> 
> 3. **Event Log**: Displays a log of all events and faults that have occurred on the ESP assets. This includes both historical and real-time events, allowing users to track the progression of issues and take corrective action.
> 
> 4. **Alarm Management**: Alerts users to any alarms or warnings that have been triggered on the ESP assets. Users can view the details of each alarm, including the cause, severity, and any corrective actions that have been taken.
> 
> 5. **Historical Data**: Provides access to historical data for the ESP assets, allowing users to analyze trends and patterns over time. This includes data on pump performance, pressure, and current, as well as any other relevant metrics.
> 
> 6. **Configuration Management**:
> 
> [navigation.operations_workspace]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /]
> - [What is Working Status?]
> - [Where are Live Calculations?]
> - [Go to Fleet Cockpit]
> 

---

### Query #16: list all available routes
**Category**: `9.1 Navigation` | **Latency**: `490ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "list all available routes"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] Operations Workspace Navigation Index\n\n**Route Path**: `/` | **Type**: `Navigation` | **Source**: `[navigation.operations_workspace]`\n\nThat's not documented in the platform guide yet.\n\n[navigation.operations_workspace]\n\n---\n### Quick Navigation Actions:\n- [Open /]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: Operations Workspace Navigation Index",
      "excerpt": "Operational command center for surveillance engineers, production technologists, and control room operators monitoring the 10 active Farha South ESP assets.",
      "relevance_score": 1.0,
      "url": "/"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "navigation.operations_workspace",
    "entry_type": "navigation",
    "title": "Operations Workspace Navigation Index",
    "path": null,
    "resolved_path": "/",
    "summary": "Operational command center for surveillance engineers, production technologists, and control room operators monitoring the 10 active Farha South ESP assets.",
    "narrative": "That's not documented in the platform guide yet.\n\n[navigation.operations_workspace]",
    "related_routes": [
      "route.fleet_cockpit",
      "route.working_status",
      "route.well_detail",
      "route.live_calculations",
      "route.event_intelligence",
      "route.reports_hub",
      "route.scenario_simulator"
    ],
    "suggested_options": [
      "Open /",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] Operations Workspace Navigation Index\n\n**Route Path**: `/` | **Type**: `Navigation` | **Source**: `[navigation.operations_workspace]`\n\nThat's not documented in the platform guide yet.\n\n[navigation.operations_workspace]\n\n---\n### Quick Navigation Actions:\n- [Open /]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] Operations Workspace Navigation Index
> 
> **Route Path**: `/` | **Type**: `Navigation` | **Source**: `[navigation.operations_workspace]`
> 
> That's not documented in the platform guide yet.
> 
> [navigation.operations_workspace]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /]
> - [What is Working Status?]
> - [Where are Live Calculations?]
> - [Go to Fleet Cockpit]
> 

---

### Query #17: where can I find the 2D ESP string visualizer?
**Category**: `9.2 Component` | **Latency**: `1272ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "where can I find the 2D ESP string visualizer?"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] ESP 2D String Visualizer\n\n**Route Path**: `/wells/FS-017` | **Type**: `Component` | **Source**: `[route.well_detail]`\n\nThe 2D ESP string visualizer can be found on the Well Monitor & Downhole Detail screen at the path `/wells/FS-017`. Additionally, it is available in preview mode on the ESP Fleet Cockpit at `/`.\n\n[route.well_detail]\n\n---\n### Quick Navigation Actions:\n- [Open /wells/FS-017]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: ESP 2D String Visualizer",
      "excerpt": "2D downhole schematic of pump, motor, seal, and sensor with mechanical and thermal stress indicators.",
      "relevance_score": 1.0,
      "url": "/wells/FS-017"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /wells/FS-017",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.well_detail",
    "entry_type": "component",
    "title": "ESP 2D String Visualizer",
    "path": "/wells/$wellId",
    "resolved_path": "/wells/FS-017",
    "summary": "2D downhole schematic of pump, motor, seal, and sensor with mechanical and thermal stress indicators.",
    "narrative": "The 2D ESP string visualizer can be found on the Well Monitor & Downhole Detail screen at the path `/wells/FS-017`. Additionally, it is available in preview mode on the ESP Fleet Cockpit at `/`.\n\n[route.well_detail]",
    "related_routes": [],
    "suggested_options": [
      "Open /wells/FS-017",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] ESP 2D String Visualizer\n\n**Route Path**: `/wells/FS-017` | **Type**: `Component` | **Source**: `[route.well_detail]`\n\nThe 2D ESP string visualizer can be found on the Well Monitor & Downhole Detail screen at the path `/wells/FS-017`. Additionally, it is available in preview mode on the ESP Fleet Cockpit at `/`.\n\n[route.well_detail]\n\n---\n### Quick Navigation Actions:\n- [Open /wells/FS-017]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] ESP 2D String Visualizer
> 
> **Route Path**: `/wells/FS-017` | **Type**: `Component` | **Source**: `[route.well_detail]`
> 
> The 2D ESP string visualizer can be found on the Well Monitor & Downhole Detail screen at the path `/wells/FS-017`. Additionally, it is available in preview mode on the ESP Fleet Cockpit at `/`.
> 
> [route.well_detail]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /wells/FS-017]
> - [What is Working Status?]
> - [Where are Live Calculations?]
> - [Go to Fleet Cockpit]
> 

---

### Query #18: what does the 4-subsystem equalizer display?
**Category**: `9.2 Component` | **Latency**: `3017ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "what does the 4-subsystem equalizer display?"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] 4-Subsystem Equalizer\n\n**Route Path**: `/wells/FS-017` | **Type**: `Component` | **Source**: `[route.well_detail]`\n\nThe 4-Subsystem Equalizer displays multi-band health meters and alarm thresholds across four core ESP subsystems: Hydraulic, Electrical, Thermal, and Mechanical. These meters provide real-time monitoring of various parameters within each subsystem, helping engineers to assess the health and performance of the well. The display includes:\n- Hydraulic subsystem: Head, flow, intake/discharge pressure\n- Electrical subsystem: Motor current, voltage, frequency, load\n- Thermal subsystem: Motor winding temperature, intake temperature\n- Mechanical subsystem: Axial/radial vibration\nThis information is crucial for maintaining the well's performance and ensuring safe operations. The Equalizer is located on the Well Monitor & Downhole Detail screen, accessible via the path /wells/$wellId.\n\n[route.well_detail]\n\n---\n### Quick Navigation Actions:\n- [Open /wells/FS-017]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: 4-Subsystem Equalizer",
      "excerpt": "Multi-band health meters across Hydraulic, Electrical, Thermal, and Mechanical subsystems.",
      "relevance_score": 1.0,
      "url": "/wells/FS-017"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /wells/FS-017",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.well_detail",
    "entry_type": "component",
    "title": "4-Subsystem Equalizer",
    "path": "/wells/$wellId",
    "resolved_path": "/wells/FS-017",
    "summary": "Multi-band health meters across Hydraulic, Electrical, Thermal, and Mechanical subsystems.",
    "narrative": "The 4-Subsystem Equalizer displays multi-band health meters and alarm thresholds across four core ESP subsystems: Hydraulic, Electrical, Thermal, and Mechanical. These meters provide real-time monitoring of various parameters within each subsystem, helping engineers to assess the health and performance of the well. The display includes:\n- Hydraulic subsystem: Head, flow, intake/discharge pressure\n- Electrical subsystem: Motor current, voltage, frequency, load\n- Thermal subsystem: Motor winding temperature, intake temperature\n- Mechanical subsystem: Axial/radial vibration\nThis information is crucial for maintaining the well's performance and ensuring safe operations. The Equalizer is located on the Well Monitor & Downhole Detail screen, accessible via the path /wells/$wellId.\n\n[route.well_detail]",
    "related_routes": [],
    "suggested_options": [
      "Open /wells/FS-017",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] 4-Subsystem Equalizer\n\n**Route Path**: `/wells/FS-017` | **Type**: `Component` | **Source**: `[route.well_detail]`\n\nThe 4-Subsystem Equalizer displays multi-band health meters and alarm thresholds across four core ESP subsystems: Hydraulic, Electrical, Thermal, and Mechanical. These meters provide real-time monitoring of various parameters within each subsystem, helping engineers to assess the health and performance of the well. The display includes:\n- Hydraulic subsystem: Head, flow, intake/discharge pressure\n- Electrical subsystem: Motor current, voltage, frequency, load\n- Thermal subsystem: Motor winding temperature, intake temperature\n- Mechanical subsystem: Axial/radial vibration\nThis information is crucial for maintaining the well's performance and ensuring safe operations. The Equalizer is located on the Well Monitor & Downhole Detail screen, accessible via the path /wells/$wellId.\n\n[route.well_detail]\n\n---\n### Quick Navigation Actions:\n- [Open /wells/FS-017]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] 4-Subsystem Equalizer
> 
> **Route Path**: `/wells/FS-017` | **Type**: `Component` | **Source**: `[route.well_detail]`
> 
> The 4-Subsystem Equalizer displays multi-band health meters and alarm thresholds across four core ESP subsystems: Hydraulic, Electrical, Thermal, and Mechanical. These meters provide real-time monitoring of various parameters within each subsystem, helping engineers to assess the health and performance of the well. The display includes:
> - Hydraulic subsystem: Head, flow, intake/discharge pressure
> - Electrical subsystem: Motor current, voltage, frequency, load
> - Thermal subsystem: Motor winding temperature, intake temperature
> - Mechanical subsystem: Axial/radial vibration
> This information is crucial for maintaining the well's performance and ensuring safe operations. The Equalizer is located on the Well Monitor & Downhole Detail screen, accessible via the path /wells/$wellId.
> 
> [route.well_detail]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /wells/FS-017]
> - [What is Working Status?]
> - [Where are Live Calculations?]
> - [Go to Fleet Cockpit]
> 

---

### Query #19: where are live pump performance curves?
**Category**: `9.2 Component` | **Latency**: `1494ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "where are live pump performance curves?"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] Live Pump Performance Curve\n\n**Route Path**: `/wells/FS-017` | **Type**: `Component` | **Source**: `[route.well_detail]`\n\nThe Live Pump Performance Curve is a component that appears on the Well Monitor & Downhole Detail screen at the path `/wells/$wellId`. It displays dynamic H-Q pump performance curves with affinity law speed scaling, recommended operating range (ROR) bounds, continuous operating point coordinates, and upthrust/downthrust limit envelopes.\n\n[route.well_detail]\n\n---\n### Quick Navigation Actions:\n- [Open /wells/FS-017]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: Live Pump Performance Curve",
      "excerpt": "Dynamic H-Q pump curve with affinity law scaling, operating point, and upthrust/downthrust limits.",
      "relevance_score": 1.0,
      "url": "/wells/FS-017"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /wells/FS-017",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.well_detail",
    "entry_type": "component",
    "title": "Live Pump Performance Curve",
    "path": "/wells/$wellId",
    "resolved_path": "/wells/FS-017",
    "summary": "Dynamic H-Q pump curve with affinity law scaling, operating point, and upthrust/downthrust limits.",
    "narrative": "The Live Pump Performance Curve is a component that appears on the Well Monitor & Downhole Detail screen at the path `/wells/$wellId`. It displays dynamic H-Q pump performance curves with affinity law speed scaling, recommended operating range (ROR) bounds, continuous operating point coordinates, and upthrust/downthrust limit envelopes.\n\n[route.well_detail]",
    "related_routes": [],
    "suggested_options": [
      "Open /wells/FS-017",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] Live Pump Performance Curve\n\n**Route Path**: `/wells/FS-017` | **Type**: `Component` | **Source**: `[route.well_detail]`\n\nThe Live Pump Performance Curve is a component that appears on the Well Monitor & Downhole Detail screen at the path `/wells/$wellId`. It displays dynamic H-Q pump performance curves with affinity law speed scaling, recommended operating range (ROR) bounds, continuous operating point coordinates, and upthrust/downthrust limit envelopes.\n\n[route.well_detail]\n\n---\n### Quick Navigation Actions:\n- [Open /wells/FS-017]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] Live Pump Performance Curve
> 
> **Route Path**: `/wells/FS-017` | **Type**: `Component` | **Source**: `[route.well_detail]`
> 
> The Live Pump Performance Curve is a component that appears on the Well Monitor & Downhole Detail screen at the path `/wells/$wellId`. It displays dynamic H-Q pump performance curves with affinity law speed scaling, recommended operating range (ROR) bounds, continuous operating point coordinates, and upthrust/downthrust limit envelopes.
> 
> [route.well_detail]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /wells/FS-017]
> - [What is Working Status?]
> - [Where are Live Calculations?]
> - [Go to Fleet Cockpit]
> 

---

### Query #20: what does the FleetTable display?
**Category**: `9.2 Component` | **Latency**: `1511ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "what does the FleetTable display?"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] Fleet Surveillance Table\n\n**Route Path**: `/` | **Type**: `Component` | **Source**: `[route.fleet_cockpit]`\n\nThe FleetTable displays a comprehensive grid of all 10 monitored wells, showing real-time operational status pills (Running, Tripped, Outside ROR), frequency (Hz), motor current (A), intake/discharge pressures, production flow rates (BPD), and quick-action navigation buttons.\n\n[route.fleet_cockpit]\n\n---\n### Quick Navigation Actions:\n- [Open /]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: Fleet Surveillance Table",
      "excerpt": "Comprehensive 10-well asset grid with live telemetry, operating states, and direct navigation links.",
      "relevance_score": 1.0,
      "url": "/"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.fleet_cockpit",
    "entry_type": "component",
    "title": "Fleet Surveillance Table",
    "path": "/",
    "resolved_path": "/",
    "summary": "Comprehensive 10-well asset grid with live telemetry, operating states, and direct navigation links.",
    "narrative": "The FleetTable displays a comprehensive grid of all 10 monitored wells, showing real-time operational status pills (Running, Tripped, Outside ROR), frequency (Hz), motor current (A), intake/discharge pressures, production flow rates (BPD), and quick-action navigation buttons.\n\n[route.fleet_cockpit]",
    "related_routes": [],
    "suggested_options": [
      "Open /",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] Fleet Surveillance Table\n\n**Route Path**: `/` | **Type**: `Component` | **Source**: `[route.fleet_cockpit]`\n\nThe FleetTable displays a comprehensive grid of all 10 monitored wells, showing real-time operational status pills (Running, Tripped, Outside ROR), frequency (Hz), motor current (A), intake/discharge pressures, production flow rates (BPD), and quick-action navigation buttons.\n\n[route.fleet_cockpit]\n\n---\n### Quick Navigation Actions:\n- [Open /]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] Fleet Surveillance Table
> 
> **Route Path**: `/` | **Type**: `Component` | **Source**: `[route.fleet_cockpit]`
> 
> The FleetTable displays a comprehensive grid of all 10 monitored wells, showing real-time operational status pills (Running, Tripped, Outside ROR), frequency (Hz), motor current (A), intake/discharge pressures, production flow rates (BPD), and quick-action navigation buttons.
> 
> [route.fleet_cockpit]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /]
> - [What is Working Status?]
> - [Where are Live Calculations?]
> 

---

### Query #21: where is the Top KPI strip located?
**Category**: `9.2 Component` | **Latency**: `1792ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "where is the Top KPI strip located?"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] Top KPI Strip\n\n**Route Path**: `/` | **Type**: `Component` | **Source**: `[route.fleet_cockpit]`\n\nThe Top KPI Strip is located across the top header of the ESP Fleet Cockpit, Well Working Status, and Well Monitor. It displays 6 fleet-wide composite operational metrics: Active Monitored Assets, Fleet Availability, Total Gross Liquid, Total Oil Deferment, Dominant Trip Cause, and Fleet Mean Run Life (MTBF).\n\n[route.fleet_cockpit]\n\n---\n### Quick Navigation Actions:\n- [Open /]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: Top KPI Strip",
      "excerpt": "6 fleet composite metrics: Active Assets, Availability, Gross Liquid, Deferment, Dominant Trip, and MTBF.",
      "relevance_score": 1.0,
      "url": "/"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.fleet_cockpit",
    "entry_type": "component",
    "title": "Top KPI Strip",
    "path": "/",
    "resolved_path": "/",
    "summary": "6 fleet composite metrics: Active Assets, Availability, Gross Liquid, Deferment, Dominant Trip, and MTBF.",
    "narrative": "The Top KPI Strip is located across the top header of the ESP Fleet Cockpit, Well Working Status, and Well Monitor. It displays 6 fleet-wide composite operational metrics: Active Monitored Assets, Fleet Availability, Total Gross Liquid, Total Oil Deferment, Dominant Trip Cause, and Fleet Mean Run Life (MTBF).\n\n[route.fleet_cockpit]",
    "related_routes": [],
    "suggested_options": [
      "Open /",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] Top KPI Strip\n\n**Route Path**: `/` | **Type**: `Component` | **Source**: `[route.fleet_cockpit]`\n\nThe Top KPI Strip is located across the top header of the ESP Fleet Cockpit, Well Working Status, and Well Monitor. It displays 6 fleet-wide composite operational metrics: Active Monitored Assets, Fleet Availability, Total Gross Liquid, Total Oil Deferment, Dominant Trip Cause, and Fleet Mean Run Life (MTBF).\n\n[route.fleet_cockpit]\n\n---\n### Quick Navigation Actions:\n- [Open /]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] Top KPI Strip
> 
> **Route Path**: `/` | **Type**: `Component` | **Source**: `[route.fleet_cockpit]`
> 
> The Top KPI Strip is located across the top header of the ESP Fleet Cockpit, Well Working Status, and Well Monitor. It displays 6 fleet-wide composite operational metrics: Active Monitored Assets, Fleet Availability, Total Gross Liquid, Total Oil Deferment, Dominant Trip Cause, and Fleet Mean Run Life (MTBF).
> 
> [route.fleet_cockpit]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /]
> - [What is Working Status?]
> - [Where are Live Calculations?]
> 

---

### Query #22: what displays in the Working Status diagnostic queue?
**Category**: `9.2 Component` | **Latency**: `1214ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "what displays in the Working Status diagnostic queue?"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] Working Status Diagnostic Queue\n\n**Route Path**: `/working-status` | **Type**: `Component` | **Source**: `[route.working_status]`\n\nThe Working Status diagnostic queue displays the master surveillance queue of assets ranked by composite anomaly score. It includes 14-fault classifier spectrum probabilities, SCADA safety envelope violations, and thermodynamic physics alarms. This component appears on the Well Working Status screen.\n\n[route.working_status]\n\n---\n### Quick Navigation Actions:\n- [Open /working-status]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: Working Status Diagnostic Queue",
      "excerpt": "Surveillance queue ranked by anomaly score with 14-fault classifier spectrum probabilities.",
      "relevance_score": 1.0,
      "url": "/working-status"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /working-status",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.working_status",
    "entry_type": "component",
    "title": "Working Status Diagnostic Queue",
    "path": "/working-status",
    "resolved_path": "/working-status",
    "summary": "Surveillance queue ranked by anomaly score with 14-fault classifier spectrum probabilities.",
    "narrative": "The Working Status diagnostic queue displays the master surveillance queue of assets ranked by composite anomaly score. It includes 14-fault classifier spectrum probabilities, SCADA safety envelope violations, and thermodynamic physics alarms. This component appears on the Well Working Status screen.\n\n[route.working_status]",
    "related_routes": [],
    "suggested_options": [
      "Open /working-status",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] Working Status Diagnostic Queue\n\n**Route Path**: `/working-status` | **Type**: `Component` | **Source**: `[route.working_status]`\n\nThe Working Status diagnostic queue displays the master surveillance queue of assets ranked by composite anomaly score. It includes 14-fault classifier spectrum probabilities, SCADA safety envelope violations, and thermodynamic physics alarms. This component appears on the Well Working Status screen.\n\n[route.working_status]\n\n---\n### Quick Navigation Actions:\n- [Open /working-status]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] Working Status Diagnostic Queue
> 
> **Route Path**: `/working-status` | **Type**: `Component` | **Source**: `[route.working_status]`
> 
> The Working Status diagnostic queue displays the master surveillance queue of assets ranked by composite anomaly score. It includes 14-fault classifier spectrum probabilities, SCADA safety envelope violations, and thermodynamic physics alarms. This component appears on the Well Working Status screen.
> 
> [route.working_status]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /working-status]
> - [Where are Live Calculations?]
> - [Go to Fleet Cockpit]
> 

---

### Query #23: what is the Fleet KPI Formulas Editor?
**Category**: `9.2 Component` | **Latency**: `1860ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "what is the Fleet KPI Formulas Editor?"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] Fleet KPI Formulas Editor\n\n**Route Path**: `/live-calculations` | **Type**: `Component` | **Source**: `[route.live_calculations]`\n\nThe Fleet KPI Formulas Editor is a component located under the Live Calculations tab on the platform. It is a mathematical formula editor and execution registry that governs and manages VFM (Virtual Flow Metering) and fleet KPI (Key Performance Indicators) equations. This tool allows users to create, edit, and execute mathematical formulas related to these critical metrics, ensuring accuracy and consistency in fleet performance analysis.\n\n[route.live_calculations]\n\n---\n### Quick Navigation Actions:\n- [Open /live-calculations]\n- [What is Working Status?]\n- [Go to Fleet Cockpit]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: Fleet KPI Formulas Editor",
      "excerpt": "Governed mathematical formula editor and execution registry for VFM and fleet KPI equations.",
      "relevance_score": 1.0,
      "url": "/live-calculations"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /live-calculations",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.live_calculations",
    "entry_type": "component",
    "title": "Fleet KPI Formulas Editor",
    "path": "/live-calculations",
    "resolved_path": "/live-calculations",
    "summary": "Governed mathematical formula editor and execution registry for VFM and fleet KPI equations.",
    "narrative": "The Fleet KPI Formulas Editor is a component located under the Live Calculations tab on the platform. It is a mathematical formula editor and execution registry that governs and manages VFM (Virtual Flow Metering) and fleet KPI (Key Performance Indicators) equations. This tool allows users to create, edit, and execute mathematical formulas related to these critical metrics, ensuring accuracy and consistency in fleet performance analysis.\n\n[route.live_calculations]",
    "related_routes": [],
    "suggested_options": [
      "Open /live-calculations",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] Fleet KPI Formulas Editor\n\n**Route Path**: `/live-calculations` | **Type**: `Component` | **Source**: `[route.live_calculations]`\n\nThe Fleet KPI Formulas Editor is a component located under the Live Calculations tab on the platform. It is a mathematical formula editor and execution registry that governs and manages VFM (Virtual Flow Metering) and fleet KPI (Key Performance Indicators) equations. This tool allows users to create, edit, and execute mathematical formulas related to these critical metrics, ensuring accuracy and consistency in fleet performance analysis.\n\n[route.live_calculations]\n\n---\n### Quick Navigation Actions:\n- [Open /live-calculations]\n- [What is Working Status?]\n- [Go to Fleet Cockpit]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] Fleet KPI Formulas Editor
> 
> **Route Path**: `/live-calculations` | **Type**: `Component` | **Source**: `[route.live_calculations]`
> 
> The Fleet KPI Formulas Editor is a component located under the Live Calculations tab on the platform. It is a mathematical formula editor and execution registry that governs and manages VFM (Virtual Flow Metering) and fleet KPI (Key Performance Indicators) equations. This tool allows users to create, edit, and execute mathematical formulas related to these critical metrics, ensuring accuracy and consistency in fleet performance analysis.
> 
> [route.live_calculations]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /live-calculations]
> - [What is Working Status?]
> - [Go to Fleet Cockpit]
> 

---

### Query #24: where can I find the Scenario Configuration Bench?
**Category**: `9.2 Component` | **Latency**: `814ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "where can I find the Scenario Configuration Bench?"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] Scenario Configuration Bench\n\n**Route Path**: `/custom-testing` | **Type**: `Component` | **Source**: `[route.scenario_simulator]`\n\nThe Scenario Configuration Bench can be found on the What-If Scenario Simulator screen at the path `/custom-testing`.\n\n[route.scenario_simulator]\n\n---\n### Quick Navigation Actions:\n- [Open /custom-testing]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: Scenario Configuration Bench",
      "excerpt": "Interactive 14-channel parameter sliders, baseline cloning, and fault injection presets.",
      "relevance_score": 1.0,
      "url": "/custom-testing"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /custom-testing",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.scenario_simulator",
    "entry_type": "component",
    "title": "Scenario Configuration Bench",
    "path": "/custom-testing",
    "resolved_path": "/custom-testing",
    "summary": "Interactive 14-channel parameter sliders, baseline cloning, and fault injection presets.",
    "narrative": "The Scenario Configuration Bench can be found on the What-If Scenario Simulator screen at the path `/custom-testing`.\n\n[route.scenario_simulator]",
    "related_routes": [],
    "suggested_options": [
      "Open /custom-testing",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] Scenario Configuration Bench\n\n**Route Path**: `/custom-testing` | **Type**: `Component` | **Source**: `[route.scenario_simulator]`\n\nThe Scenario Configuration Bench can be found on the What-If Scenario Simulator screen at the path `/custom-testing`.\n\n[route.scenario_simulator]\n\n---\n### Quick Navigation Actions:\n- [Open /custom-testing]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] Scenario Configuration Bench
> 
> **Route Path**: `/custom-testing` | **Type**: `Component` | **Source**: `[route.scenario_simulator]`
> 
> The Scenario Configuration Bench can be found on the What-If Scenario Simulator screen at the path `/custom-testing`.
> 
> [route.scenario_simulator]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /custom-testing]
> - [What is Working Status?]
> - [Where are Live Calculations?]
> - [Go to Fleet Cockpit]
> 

---

### Query #25: what is the 14-fault classifier spectrum?
**Category**: `9.3 Concept` | **Latency**: `1887ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "what is the 14-fault classifier spectrum?"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] 14-Fault Classifier Spectrum\n\n**Route Path**: `/working-status` | **Type**: `Concept` | **Source**: `[route.working_status]`\n\nThe 14-Fault Classifier Spectrum is a multi-class machine learning classification engine that continuously scores SCADA telemetry against 14 recognized ESP failure modes. It is a critical feature of the Well Working Status screen, which provides real-time insights into the health of the well. The engine helps engineers detect developing downhole abnormalities hours or days before an electrical or mechanical trip occurs, preventing deferred production and premature equipment teardown.\n\n[route.working_status]\n\n---\n### Quick Navigation Actions:\n- [Open /working-status]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: 14-Fault Classifier Spectrum",
      "excerpt": "Multi-class ML classification engine continuously scoring telemetry against 14 recognized ESP failure modes.",
      "relevance_score": 1.0,
      "url": "/working-status"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /working-status",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.working_status",
    "entry_type": "concept",
    "title": "14-Fault Classifier Spectrum",
    "path": "/working-status",
    "resolved_path": "/working-status",
    "summary": "Multi-class ML classification engine continuously scoring telemetry against 14 recognized ESP failure modes.",
    "narrative": "The 14-Fault Classifier Spectrum is a multi-class machine learning classification engine that continuously scores SCADA telemetry against 14 recognized ESP failure modes. It is a critical feature of the Well Working Status screen, which provides real-time insights into the health of the well. The engine helps engineers detect developing downhole abnormalities hours or days before an electrical or mechanical trip occurs, preventing deferred production and premature equipment teardown.\n\n[route.working_status]",
    "related_routes": [],
    "suggested_options": [
      "Open /working-status",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] 14-Fault Classifier Spectrum\n\n**Route Path**: `/working-status` | **Type**: `Concept` | **Source**: `[route.working_status]`\n\nThe 14-Fault Classifier Spectrum is a multi-class machine learning classification engine that continuously scores SCADA telemetry against 14 recognized ESP failure modes. It is a critical feature of the Well Working Status screen, which provides real-time insights into the health of the well. The engine helps engineers detect developing downhole abnormalities hours or days before an electrical or mechanical trip occurs, preventing deferred production and premature equipment teardown.\n\n[route.working_status]\n\n---\n### Quick Navigation Actions:\n- [Open /working-status]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] 14-Fault Classifier Spectrum
> 
> **Route Path**: `/working-status` | **Type**: `Concept` | **Source**: `[route.working_status]`
> 
> The 14-Fault Classifier Spectrum is a multi-class machine learning classification engine that continuously scores SCADA telemetry against 14 recognized ESP failure modes. It is a critical feature of the Well Working Status screen, which provides real-time insights into the health of the well. The engine helps engineers detect developing downhole abnormalities hours or days before an electrical or mechanical trip occurs, preventing deferred production and premature equipment teardown.
> 
> [route.working_status]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /working-status]
> - [Where are Live Calculations?]
> - [Go to Fleet Cockpit]
> 

---

### Query #26: what is virtual flow metering (VFM)?
**Category**: `9.3 Concept` | **Latency**: `1745ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "what is virtual flow metering (VFM)?"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] Virtual Flow Metering (VFM)\n\n**Route Path**: `/live-calculations` | **Type**: `Concept` | **Source**: `[route.live_calculations]`\n\nVirtual Flow Metering (VFM) is a thermodynamic and hydrodynamic mathematical framework that calculates real-time gross liquid flow rate (BPD) and water cut from pump intake/discharge differential pressures, fluid specific gravity, and motor brake horsepower. It provides continuous, well-by-well production monitoring without requiring expensive physical test separators or frequent surface well tests.\n\n[route.live_calculations]\n\n---\n### Quick Navigation Actions:\n- [Open /live-calculations]\n- [What is Working Status?]\n- [Go to Fleet Cockpit]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: Virtual Flow Metering (VFM)",
      "excerpt": "Thermodynamic and hydrodynamic mathematical framework calculating real-time gross liquid flow rate and water cut.",
      "relevance_score": 1.0,
      "url": "/live-calculations"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /live-calculations",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.live_calculations",
    "entry_type": "concept",
    "title": "Virtual Flow Metering (VFM)",
    "path": "/live-calculations",
    "resolved_path": "/live-calculations",
    "summary": "Thermodynamic and hydrodynamic mathematical framework calculating real-time gross liquid flow rate and water cut.",
    "narrative": "Virtual Flow Metering (VFM) is a thermodynamic and hydrodynamic mathematical framework that calculates real-time gross liquid flow rate (BPD) and water cut from pump intake/discharge differential pressures, fluid specific gravity, and motor brake horsepower. It provides continuous, well-by-well production monitoring without requiring expensive physical test separators or frequent surface well tests.\n\n[route.live_calculations]",
    "related_routes": [],
    "suggested_options": [
      "Open /live-calculations",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] Virtual Flow Metering (VFM)\n\n**Route Path**: `/live-calculations` | **Type**: `Concept` | **Source**: `[route.live_calculations]`\n\nVirtual Flow Metering (VFM) is a thermodynamic and hydrodynamic mathematical framework that calculates real-time gross liquid flow rate (BPD) and water cut from pump intake/discharge differential pressures, fluid specific gravity, and motor brake horsepower. It provides continuous, well-by-well production monitoring without requiring expensive physical test separators or frequent surface well tests.\n\n[route.live_calculations]\n\n---\n### Quick Navigation Actions:\n- [Open /live-calculations]\n- [What is Working Status?]\n- [Go to Fleet Cockpit]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] Virtual Flow Metering (VFM)
> 
> **Route Path**: `/live-calculations` | **Type**: `Concept` | **Source**: `[route.live_calculations]`
> 
> Virtual Flow Metering (VFM) is a thermodynamic and hydrodynamic mathematical framework that calculates real-time gross liquid flow rate (BPD) and water cut from pump intake/discharge differential pressures, fluid specific gravity, and motor brake horsepower. It provides continuous, well-by-well production monitoring without requiring expensive physical test separators or frequent surface well tests.
> 
> [route.live_calculations]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /live-calculations]
> - [What is Working Status?]
> - [Go to Fleet Cockpit]
> 

---

### Query #27: what are affinity laws in the platform?
**Category**: `9.3 Concept` | **Latency**: `2549ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "what are affinity laws in the platform?"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] Affinity Laws\n\n**Route Path**: `/wells/FS-017` | **Type**: `Concept` | **Source**: `[route.well_detail]`\n\nAffinity laws in the platform are mathematical scaling relationships for centrifugal pumps that describe how flow rate, head, and hydraulic power vary with rotational speed. These laws are crucial for accurately modeling the performance of centrifugal pumps as the variable speed drive (VSD) frequency changes. They allow the platform to dynamically scale manufacturer baseline pump curves between 30 Hz and 65 Hz, ensuring that the operating envelope is accurately represented. This feature is part of the Well Monitor & Downhole Detail section on the platform, accessible via the path /wells/FS-017.\n\n[route.well_detail]\n\n---\n### Quick Navigation Actions:\n- [Open /wells/FS-017]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: Affinity Laws",
      "excerpt": "Centrifugal pump scaling laws dynamically scaling H-Q pump curves with VSD frequency changes.",
      "relevance_score": 1.0,
      "url": "/wells/FS-017"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /wells/FS-017",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.well_detail",
    "entry_type": "concept",
    "title": "Affinity Laws",
    "path": "/wells/$wellId",
    "resolved_path": "/wells/FS-017",
    "summary": "Centrifugal pump scaling laws dynamically scaling H-Q pump curves with VSD frequency changes.",
    "narrative": "Affinity laws in the platform are mathematical scaling relationships for centrifugal pumps that describe how flow rate, head, and hydraulic power vary with rotational speed. These laws are crucial for accurately modeling the performance of centrifugal pumps as the variable speed drive (VSD) frequency changes. They allow the platform to dynamically scale manufacturer baseline pump curves between 30 Hz and 65 Hz, ensuring that the operating envelope is accurately represented. This feature is part of the Well Monitor & Downhole Detail section on the platform, accessible via the path /wells/FS-017.\n\n[route.well_detail]",
    "related_routes": [],
    "suggested_options": [
      "Open /wells/FS-017",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] Affinity Laws\n\n**Route Path**: `/wells/FS-017` | **Type**: `Concept` | **Source**: `[route.well_detail]`\n\nAffinity laws in the platform are mathematical scaling relationships for centrifugal pumps that describe how flow rate, head, and hydraulic power vary with rotational speed. These laws are crucial for accurately modeling the performance of centrifugal pumps as the variable speed drive (VSD) frequency changes. They allow the platform to dynamically scale manufacturer baseline pump curves between 30 Hz and 65 Hz, ensuring that the operating envelope is accurately represented. This feature is part of the Well Monitor & Downhole Detail section on the platform, accessible via the path /wells/FS-017.\n\n[route.well_detail]\n\n---\n### Quick Navigation Actions:\n- [Open /wells/FS-017]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] Affinity Laws
> 
> **Route Path**: `/wells/FS-017` | **Type**: `Concept` | **Source**: `[route.well_detail]`
> 
> Affinity laws in the platform are mathematical scaling relationships for centrifugal pumps that describe how flow rate, head, and hydraulic power vary with rotational speed. These laws are crucial for accurately modeling the performance of centrifugal pumps as the variable speed drive (VSD) frequency changes. They allow the platform to dynamically scale manufacturer baseline pump curves between 30 Hz and 65 Hz, ensuring that the operating envelope is accurately represented. This feature is part of the Well Monitor & Downhole Detail section on the platform, accessible via the path /wells/FS-017.
> 
> [route.well_detail]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /wells/FS-017]
> - [What is Working Status?]
> - [Where are Live Calculations?]
> - [Go to Fleet Cockpit]
> 

---

### Query #28: what is the zero fabrication data readiness gate?
**Category**: `9.3 Concept` | **Latency**: `1769ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "what is the zero fabrication data readiness gate?"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] Zero Fabrication Data Readiness Gate\n\n**Route Path**: `/reports` | **Type**: `Concept` | **Source**: `[route.reports_hub]`\n\nThe Zero Fabrication Data Readiness Gate is a platform governance policy that enforces strict audit integrity by refusing to interpolate, fabricate, or render synthetic numbers when raw SCADA telemetry is stale, missing, or below readiness thresholds. This policy ensures that official operational and compliance reports exported to operators and regulatory partners represent empirical, verifiable ground truth rather than hallucinated or estimated figures.\n\n[route.reports_hub]\n\n---\n### Quick Navigation Actions:\n- [Open /reports]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: Zero Fabrication Data Readiness Gate",
      "excerpt": "Governance policy enforcing audit integrity by refusing to fabricate numbers when telemetry is missing or stale.",
      "relevance_score": 1.0,
      "url": "/reports"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /reports",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.reports_hub",
    "entry_type": "concept",
    "title": "Zero Fabrication Data Readiness Gate",
    "path": "/reports",
    "resolved_path": "/reports",
    "summary": "Governance policy enforcing audit integrity by refusing to fabricate numbers when telemetry is missing or stale.",
    "narrative": "The Zero Fabrication Data Readiness Gate is a platform governance policy that enforces strict audit integrity by refusing to interpolate, fabricate, or render synthetic numbers when raw SCADA telemetry is stale, missing, or below readiness thresholds. This policy ensures that official operational and compliance reports exported to operators and regulatory partners represent empirical, verifiable ground truth rather than hallucinated or estimated figures.\n\n[route.reports_hub]",
    "related_routes": [],
    "suggested_options": [
      "Open /reports",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] Zero Fabrication Data Readiness Gate\n\n**Route Path**: `/reports` | **Type**: `Concept` | **Source**: `[route.reports_hub]`\n\nThe Zero Fabrication Data Readiness Gate is a platform governance policy that enforces strict audit integrity by refusing to interpolate, fabricate, or render synthetic numbers when raw SCADA telemetry is stale, missing, or below readiness thresholds. This policy ensures that official operational and compliance reports exported to operators and regulatory partners represent empirical, verifiable ground truth rather than hallucinated or estimated figures.\n\n[route.reports_hub]\n\n---\n### Quick Navigation Actions:\n- [Open /reports]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] Zero Fabrication Data Readiness Gate
> 
> **Route Path**: `/reports` | **Type**: `Concept` | **Source**: `[route.reports_hub]`
> 
> The Zero Fabrication Data Readiness Gate is a platform governance policy that enforces strict audit integrity by refusing to interpolate, fabricate, or render synthetic numbers when raw SCADA telemetry is stale, missing, or below readiness thresholds. This policy ensures that official operational and compliance reports exported to operators and regulatory partners represent empirical, verifiable ground truth rather than hallucinated or estimated figures.
> 
> [route.reports_hub]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /reports]
> - [What is Working Status?]
> - [Where are Live Calculations?]
> - [Go to Fleet Cockpit]
> 

---

### Query #29: what is the recommended operating range (ROR)?
**Category**: `9.3 Concept` | **Latency**: `1516ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "what is the recommended operating range (ROR)?"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] Recommended Operating Range (ROR)\n\n**Route Path**: `/wells/FS-017` | **Type**: `Concept` | **Source**: `[route.well_detail]`\n\nThe Recommended Operating Range (ROR) is the optimal flow capacity corridor between the downthrust limit and upthrust limit on the pump curve. This range ensures that the pump operates efficiently and safely, minimizing excessive axial thrust and mechanical vibration, which can lead to reduced run life and premature pump failure.\n\n[route.well_detail]\n\n---\n### Quick Navigation Actions:\n- [Open /wells/FS-017]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: Recommended Operating Range (ROR)",
      "excerpt": "Optimal flow capacity corridor between downthrust and upthrust limits on the pump curve.",
      "relevance_score": 1.0,
      "url": "/wells/FS-017"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /wells/FS-017",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.well_detail",
    "entry_type": "concept",
    "title": "Recommended Operating Range (ROR)",
    "path": "/wells/$wellId",
    "resolved_path": "/wells/FS-017",
    "summary": "Optimal flow capacity corridor between downthrust and upthrust limits on the pump curve.",
    "narrative": "The Recommended Operating Range (ROR) is the optimal flow capacity corridor between the downthrust limit and upthrust limit on the pump curve. This range ensures that the pump operates efficiently and safely, minimizing excessive axial thrust and mechanical vibration, which can lead to reduced run life and premature pump failure.\n\n[route.well_detail]",
    "related_routes": [],
    "suggested_options": [
      "Open /wells/FS-017",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] Recommended Operating Range (ROR)\n\n**Route Path**: `/wells/FS-017` | **Type**: `Concept` | **Source**: `[route.well_detail]`\n\nThe Recommended Operating Range (ROR) is the optimal flow capacity corridor between the downthrust limit and upthrust limit on the pump curve. This range ensures that the pump operates efficiently and safely, minimizing excessive axial thrust and mechanical vibration, which can lead to reduced run life and premature pump failure.\n\n[route.well_detail]\n\n---\n### Quick Navigation Actions:\n- [Open /wells/FS-017]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] Recommended Operating Range (ROR)
> 
> **Route Path**: `/wells/FS-017` | **Type**: `Concept` | **Source**: `[route.well_detail]`
> 
> The Recommended Operating Range (ROR) is the optimal flow capacity corridor between the downthrust limit and upthrust limit on the pump curve. This range ensures that the pump operates efficiently and safely, minimizing excessive axial thrust and mechanical vibration, which can lead to reduced run life and premature pump failure.
> 
> [route.well_detail]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /wells/FS-017]
> - [What is Working Status?]
> - [Where are Live Calculations?]
> - [Go to Fleet Cockpit]
> 

---

### Query #30: where can I find pump curves for FS-017?
**Category**: `9.4 Parametric Binding` | **Latency**: `1641ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": "FS-017",
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "where can I find pump curves for FS-017?"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] Live Pump Performance Curve\n\n**Route Path**: `/wells/FS-017` | **Type**: `Component` | **Source**: `[route.well_detail]`\n\nThe pump curves for FS-017 can be found on the Well Monitor & Downhole Detail screen at the path `/wells/FS-017`. This screen displays dynamic H-Q pump performance curves with affinity law speed scaling, recommended operating range (ROR) bounds, continuous operating point coordinates, and upthrust/downthrust limit envelopes.\n\n[route.well_detail]\n\n---\n### Quick Navigation Actions:\n- [Open /wells/FS-017]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: Live Pump Performance Curve",
      "excerpt": "Dynamic H-Q pump curve with affinity law scaling, operating point, and upthrust/downthrust limits.",
      "relevance_score": 1.0,
      "url": "/wells/FS-017"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /wells/FS-017",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.well_detail",
    "entry_type": "component",
    "title": "Live Pump Performance Curve",
    "path": "/wells/$wellId",
    "resolved_path": "/wells/FS-017",
    "summary": "Dynamic H-Q pump curve with affinity law scaling, operating point, and upthrust/downthrust limits.",
    "narrative": "The pump curves for FS-017 can be found on the Well Monitor & Downhole Detail screen at the path `/wells/FS-017`. This screen displays dynamic H-Q pump performance curves with affinity law speed scaling, recommended operating range (ROR) bounds, continuous operating point coordinates, and upthrust/downthrust limit envelopes.\n\n[route.well_detail]",
    "related_routes": [],
    "suggested_options": [
      "Open /wells/FS-017",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] Live Pump Performance Curve\n\n**Route Path**: `/wells/FS-017` | **Type**: `Component` | **Source**: `[route.well_detail]`\n\nThe pump curves for FS-017 can be found on the Well Monitor & Downhole Detail screen at the path `/wells/FS-017`. This screen displays dynamic H-Q pump performance curves with affinity law speed scaling, recommended operating range (ROR) bounds, continuous operating point coordinates, and upthrust/downthrust limit envelopes.\n\n[route.well_detail]\n\n---\n### Quick Navigation Actions:\n- [Open /wells/FS-017]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] Live Pump Performance Curve
> 
> **Route Path**: `/wells/FS-017` | **Type**: `Component` | **Source**: `[route.well_detail]`
> 
> The pump curves for FS-017 can be found on the Well Monitor & Downhole Detail screen at the path `/wells/FS-017`. This screen displays dynamic H-Q pump performance curves with affinity law speed scaling, recommended operating range (ROR) bounds, continuous operating point coordinates, and upthrust/downthrust limit envelopes.
> 
> [route.well_detail]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /wells/FS-017]
> - [What is Working Status?]
> - [Where are Live Calculations?]
> - [Go to Fleet Cockpit]
> 

---

### Query #31: show well detail for FNW-001
**Category**: `9.4 Parametric Binding` | **Latency**: `2484ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": "FNW-001",
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "show well detail for FNW-001"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "# [ESP APM Navigation] Well Monitor & Downhole Detail\n\n**Route Path**: `/wells/FNW-001` | **Type**: `Route` | **Source**: `[route.well_detail]`\n\nTo view the well detail for FNW-001, navigate to the following path:\n\nPath: /wells/FNW-001\n\nThis route will display a single-well surveillance console featuring a 2D downhole schematic visualizer, live H-Q pump performance curve, 4-subsystem equalizer, and wellbore depth pressure profile. The well detail is accessible through the ESP Insight Suite application workspace, which can be found at `src/routes/wells.$wellId.tsx` in the ESP Insight Suite source code.\n\n[route.well_detail]\n\n---\n### Quick Navigation Actions:\n- [Open /wells/FNW-001]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: Well Monitor & Downhole Detail",
      "excerpt": "Single-well surveillance console featuring 2D downhole schematic visualizer, live H-Q pump performance curve, 4-subsystem equalizer, and wellbore depth pressure profile.",
      "relevance_score": 1.0,
      "url": "/wells/FNW-001"
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Open /wells/FNW-001",
    "Well Working Status",
    "Operations Workspace Index"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.well_detail",
    "entry_type": "route",
    "title": "Well Monitor & Downhole Detail",
    "path": "/wells/$wellId",
    "resolved_path": "/wells/FNW-001",
    "summary": "Single-well surveillance console featuring 2D downhole schematic visualizer, live H-Q pump performance curve, 4-subsystem equalizer, and wellbore depth pressure profile.",
    "narrative": "To view the well detail for FNW-001, navigate to the following path:\n\nPath: /wells/FNW-001\n\nThis route will display a single-well surveillance console featuring a 2D downhole schematic visualizer, live H-Q pump performance curve, 4-subsystem equalizer, and wellbore depth pressure profile. The well detail is accessible through the ESP Insight Suite application workspace, which can be found at `src/routes/wells.$wellId.tsx` in the ESP Insight Suite source code.\n\n[route.well_detail]",
    "related_routes": [
      "route.fleet_cockpit",
      "route.working_status",
      "route.live_calculations"
    ],
    "suggested_options": [
      "Open /wells/FNW-001",
      "Well Working Status",
      "Operations Workspace Index"
    ],
    "markdown_report": "# [ESP APM Navigation] Well Monitor & Downhole Detail\n\n**Route Path**: `/wells/FNW-001` | **Type**: `Route` | **Source**: `[route.well_detail]`\n\nTo view the well detail for FNW-001, navigate to the following path:\n\nPath: /wells/FNW-001\n\nThis route will display a single-well surveillance console featuring a 2D downhole schematic visualizer, live H-Q pump performance curve, 4-subsystem equalizer, and wellbore depth pressure profile. The well detail is accessible through the ESP Insight Suite application workspace, which can be found at `src/routes/wells.$wellId.tsx` in the ESP Insight Suite source code.\n\n[route.well_detail]\n\n---\n### Quick Navigation Actions:\n- [Open /wells/FNW-001]\n- [What is Working Status?]\n- [Where are Live Calculations?]\n- [Go to Fleet Cockpit]\n"
  }
}
```

#### 4. Rendered Markdown Narrative
> # [ESP APM Navigation] Well Monitor & Downhole Detail
> 
> **Route Path**: `/wells/FNW-001` | **Type**: `Route` | **Source**: `[route.well_detail]`
> 
> To view the well detail for FNW-001, navigate to the following path:
> 
> Path: /wells/FNW-001
> 
> This route will display a single-well surveillance console featuring a 2D downhole schematic visualizer, live H-Q pump performance curve, 4-subsystem equalizer, and wellbore depth pressure profile. The well detail is accessible through the ESP Insight Suite application workspace, which can be found at `src/routes/wells.$wellId.tsx` in the ESP Insight Suite source code.
> 
> [route.well_detail]
> 
> ---
> ### Quick Navigation Actions:
> - [Open /wells/FNW-001]
> - [What is Working Status?]
> - [Where are Live Calculations?]
> - [Go to Fleet Cockpit]
> 

---

### Query #32: where is the pizza ordering screen?
**Category**: `9.5 Out of Scope` | **Latency**: `89ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "where is the pizza ordering screen?"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "That's not documented in the platform guide yet.",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: Undocumented Route",
      "excerpt": "Feature not present in platform guide.",
      "relevance_score": 1.0,
      "url": null
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Operations Workspace",
    "Working Status",
    "Fleet Cockpit"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.unknown",
    "entry_type": "route",
    "title": "Undocumented Route",
    "path": null,
    "resolved_path": null,
    "summary": "Feature not present in platform guide.",
    "narrative": "That's not documented in the platform guide yet.",
    "related_routes": [],
    "suggested_options": [
      "Operations Workspace",
      "Working Status",
      "Fleet Cockpit"
    ],
    "markdown_report": "That's not documented in the platform guide yet."
  }
}
```

#### 4. Rendered Markdown Narrative
> That's not documented in the platform guide yet.

---

### Query #33: what is the 3D seismic voxel viewer page?
**Category**: `9.5 Out of Scope` | **Latency**: `23ms`

#### 1. Route Intent Preview (`GET /api/esp/route-intent`)
```json
{
  "intent": "UI_NAVIGATION",
  "entity": null,
  "entities": [],
  "time_filter_label": null,
  "confidence": 0.99,
  "routing_tier": "TIER_0_UI_NAVIGATION",
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": []
}
```

#### 2. Copilot Ask Request (`POST /api/esp/ask`)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/esp/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "what is the 3D seismic voxel viewer page?"}'
```

#### 3. Raw Response Payload
```json
{
  "answer": "That's not documented in the platform guide yet.",
  "confidence": 0.99,
  "citations": [
    {
      "source_type": "platform_ui_map_guide",
      "source_id": 1,
      "title": "Platform Navigation Guide: Undocumented Route",
      "excerpt": "Feature not present in platform guide.",
      "relevance_score": 1.0,
      "url": null
    }
  ],
  "warnings": [],
  "needs_clarification": false,
  "clarification_question": null,
  "suggested_options": [
    "Operations Workspace",
    "Working Status",
    "Fleet Cockpit"
  ],
  "is_mock": false,
  "disclaimer": "Content generated from knowledge base retrieval and AI assistance. For reference only, not a mandatory maintenance order.",
  "structured_data": {
    "intent": "UI_NAVIGATION",
    "route_id": "route.unknown",
    "entry_type": "route",
    "title": "Undocumented Route",
    "path": null,
    "resolved_path": null,
    "summary": "Feature not present in platform guide.",
    "narrative": "That's not documented in the platform guide yet.",
    "related_routes": [],
    "suggested_options": [
      "Operations Workspace",
      "Working Status",
      "Fleet Cockpit"
    ],
    "markdown_report": "That's not documented in the platform guide yet."
  }
}
```

#### 4. Rendered Markdown Narrative
> That's not documented in the platform guide yet.

---
