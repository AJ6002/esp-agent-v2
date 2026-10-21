# Industrial Maintenance Copilot & ESP APM Platform

**Enterprise AI-Assisted Industrial Maintenance Platform with Simulated OPC UA Integration, Predictive Machine Learning, Evidence-Bound Diagnosis, Human-in-the-Loop Workflows, and End-to-End Traceability.**

[![Python](https://img.shields.io/badge/Python-3.11-3776AB)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-14.x-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-009688)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## Overview

The **Industrial Maintenance Copilot** bridges real-time SCADA telemetry, physical equipment baselines, vibration diagnostics, API RP 11S petroleum engineering standards, and Explainable AI (XAI) into an audited industrial maintenance loop.

The system supports two complementary backends:
1. **Enterprise Monorepo API (`apps/api`)**: Complete maintenance platform managing assets, work orders, LOTO safety checklists, technician dispatch, approval gates, and simulated OPC UA gateways.
2. **Decoupled Agent Microservice (`agent_service_v2`)**: Standalone, lightweight diagnostic service running on port `8092`, offering low-latency streaming NDJSON diagnostics for `<AgentDock />` and dashboard UI panels.

```mermaid
flowchart TB
    subgraph DataLayer["Data & Telemetry Layer"]
        SCADA["SCADA / Telemetry DB\n(Server 184 PostgreSQL)"]
        Simulator["Software Equipment Simulator\n(OPC UA Read-Only)"]
        Registry["Asset Registry & Baselines\n(40+ Monitored Wells)"]
    end

    subgraph ServiceLayer["Diagnostic & Service Layer"]
        API["Enterprise API (Port 8000)\napps/api"]
        Agent["Diagnostic Agent V2 (Port 8092)\nagent_service_v2"]
        LLM["Local Inference Server\n(Server 188 Qwen 2.5 3B)"]
    end

    subgraph UILayer["Operator Interface"]
        Web["Next.js Web Application (Port 3000)\napps/web"]
        Dock["AgentDock / Streaming Copilot"]
        Dashboard["Field Overview & Well Views"]
    end

    SCADA --> Agent
    SCADA --> API
    Simulator --> API
    Registry --> Agent
    Agent <--> LLM
    API <--> LLM
    Agent --> Dock
    API --> Web
    Dock --> Web
    Dashboard --> Web
```

---

## What Must Be in the `.env` Files to Run the Project

The repository uses two `.env` files depending on which services you run.

### 1. Root `.env` (Required for `apps/api` and `apps/web`)

Create `.env` in the repository root:
```bash
cp .env.example .env
```

#### Required Environment Variables Breakdown

| Variable | Required | Default / Recommended | Purpose |
|---|:---:|---|---|
| `APP_NAME` | No | `AI-Powered Industrial Maintenance Platform` | Application display name |
| `APP_ENV` | Yes | `development` | Environment mode (`development` or `production`) |
| `API_HOST` | Yes | `0.0.0.0` | API bind address |
| `API_PORT` | Yes | `8000` | API port |
| `FRONTEND_URL` | Yes | `http://localhost:3000` | Allowed CORS origin for Next.js frontend |
| `DATABASE_URL` | No | *(empty)* | PostgreSQL URI. Leave empty to use local SQLite automatically |
| `AUTO_MIGRATE_ON_STARTUP` | Yes | `true` | Automatically runs Alembic migrations on startup |
| `SECRET_KEY` | Yes | `change-this-to-a-random-secret-key-in-production` | Secret key for JWT session tokens |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Yes | `1440` | JWT token validity duration (24 hours) |
| `AI_ENABLED` | Yes | `true` | Set `true` to use LLM, or `false` for deterministic fallback |
| `LLM_API_BASE` | Yes | `http://192.168.1.188:8080/v1` | URL of the local OpenAI-compatible LLM gateway |
| `LLM_MODEL` | Yes | `Qwen2.5-Coder-3B-Instruct-Q4_K_M` | Active model identifier on the LLM server |
| `LLM_API_KEY` | No | `not-needed` | API key (not required for local vLLM instances) |
| `AI_REQUEST_TIMEOUT_SECONDS`| Yes | `60` | Maximum wait time for LLM generation responses |
| `SEED_ON_STARTUP` | Yes | `true` | Automatically seeds demo assets and initial users on startup |
| `STORAGE_TYPE` | Yes | `local` | Upload storage backend (`local` or `s3`) |
| `STORAGE_LOCAL_DIR` | Yes | `./uploads` | Local upload directory path |
| `GATEWAY_ENABLED` | Yes | `false` | Master switch for OPC UA protocol gateway |
| `GATEWAY_MODE` | No | `mock` | `mock` for built-in simulator, or `opcua` for network server |

#### Root `.env` Quickstart Template

```ini
APP_NAME=AI-Powered Industrial Maintenance Platform
APP_ENV=development
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_URL=http://localhost:3000

# Database: Leave empty for local SQLite (zero-config startup)
DATABASE_URL=
AUTO_MIGRATE_ON_STARTUP=true

# Authentication
SECRET_KEY=change-this-to-a-random-secret-key-in-production-at-least-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# AI Configuration (Local Qwen 2.5 3B on Server 188)
AI_ENABLED=true
LLM_API_BASE=http://192.168.1.188:8080/v1
LLM_API_KEY=not-needed
LLM_MODEL=Qwen2.5-Coder-3B-Instruct-Q4_K_M
AI_REQUEST_TIMEOUT_SECONDS=60
EQUIPMENT_COMMAND_TIMEOUT_SECONDS=300

# File Storage & Demo Seed
STORAGE_TYPE=local
STORAGE_LOCAL_DIR=./uploads
SEED_ON_STARTUP=true

# Industrial Protocol Gateway (OPC UA)
GATEWAY_ENABLED=false
GATEWAY_MODE=mock
GATEWAY_ENDPOINT=mock://opcua-simulator
GATEWAY_POLL_INTERVAL_SECONDS=5
GATEWAY_AUTO_INGEST=true
```

---

### 2. `agent_service_v2/.env` (Required for the Standalone Agent)

Create `.env` in `agent_service_v2/`:
```bash
cd agent_service_v2
cp .env.example .env
```

#### Required Variables for `agent_service_v2`

| Variable | Required | Recommended Value | Purpose |
|---|:---:|---|---|
| `HOST` | Yes | `0.0.0.0` | Bind host for the agent microservice |
| `PORT` | Yes | `8092` | Listening port for streaming NDJSON |
| `ESP_APM_DB_URL` | Yes | `postgresql://esp_admin:EspApm2026!@192.168.1.184:5433/esp_apm_db` | Read-only connection to Server 184 SCADA database |
| `AI_ENABLED` | Yes | `true` | Enables AI synthesis |
| `LLM_API_BASE` | Yes | `http://192.168.1.188:8080/v1` | URL for local LLM inference server |
| `LLM_MODEL` | Yes | `Qwen2.5-Coder-3B-Instruct-Q4_K_M` | Model identifier |
| `LLM_TIMEOUT` | Yes | `60` | Request timeout in seconds |

#### `agent_service_v2/.env` Template

```ini
HOST=0.0.0.0
PORT=8092
ESP_APM_DB_URL=postgresql://esp_admin:EspApm2026!@192.168.1.184:5433/esp_apm_db
AI_ENABLED=true
LLM_API_BASE=http://192.168.1.188:8080/v1
LLM_MODEL=Qwen2.5-Coder-3B-Instruct-Q4_K_M
LLM_TIMEOUT=60
```

---

## 12 Operational Query Domains

The diagnostic copilot is partitioned into 12 distinct operational domains:

1. **Domain 1 — Fleet Analysis**: Fleet inventory, triage ranking, gross liquid production, oil deferment, and alarm clustering.
2. **Domain 2 — Fleet Comparison**: Well-to-well side-by-side analysis, cluster vs cluster benchmarking, and nominal baseline deviations.
3. **Domain 3 — Trip Forensics**: High-density 15-minute pre-trip and 5-minute post-trip SCADA telemetry windows with multi-event disambiguation.
4. **Domain 4 — Well-Level Diagnosis (Flagship Engine)**: Dual-mode RCA engine covering post-trip forensics (Mode A) and live running well degradation (Mode B) with 7-section XAI reports and sensor-vs-physics reconciliation.
5. **Domain 5 — Well-Level Status**: Live telemetry snapshots, pump curve placement, and operational state.
6. **Domain 6 — Well-Level History & Work Orders**: Historical telemetry windows, failure event logs, and emergency LOTO dispatch.
7. **Domain 7 — Well-Level Health & Reliability**: Composite health score trajectories, Remaining Useful Life (RUL) bounds, and degradation rates.
8. **Domain 8 — Petroleum Engineering Knowledge Base**: 7,800+ chunk RAG search across API RP 11S guidelines and approved Standard Operating Procedures (SOPs).
9. **Domain 9 — UI Navigation & Copilot Explainer**: Direct routing and explanatory deep-links for dashboard views (Working Status, Subsystem Equalizer, Reliability).
10. **Domain 10 — Self-Knowledge & Identity**: System capabilities, fleet asset boundaries, and monitored well lists.
11. **Domain 11 — Conversational Session Layer**: Multi-turn dialogue, pronoun resolution (`it` $\rightarrow$ active well), and metric reframing.
12. **Domain 12 — Safety & Refusal Engine**: Intercepts false-premise queries on healthy assets, blocks physical SCADA actuation, and enforces Data Readiness Gates.

---

## Quick Start Guide

### Option 1: Docker Compose (All Services)

```bash
# Clone the repository
git clone https://github.com/AJ6002/esp-agent-v2.git
cd esp-agent-v2

# Configure environment
cp .env.example .env

# Start all services
docker compose up --build
```

Access services:
- **Web Application**: [http://localhost:3000](http://localhost:3000)
- **Monorepo API**: [http://localhost:8000](http://localhost:8000)
- **API Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Readiness Probe**: [http://localhost:8000/ready](http://localhost:8000/ready)

---

### Option 2: Manual Local Development

#### 1. Start the Enterprise Backend (`apps/api`)
```bash
cd apps/api
py -3.11 -m pip install -r requirements.txt
py -3.11 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Start the Standalone Agent Service (`agent_service_v2`)
```bash
cd agent_service_v2
py -3.11 -m pip install -r requirements.txt
py -3.11 -m uvicorn main:app --host 0.0.0.0 --port 8092 --reload
```

#### 3. Start the Web Frontend (`apps/web`)
```bash
cd apps/web
npm install
npm run dev
```

---

## Running Automated Tests

```bash
# Monorepo Backend API Tests
py -3.11 -m pytest apps/api/tests/test_esp_diagnosis.py -v

# Standalone Agent Diagnostic Suites
cd agent_service_v2
py -3.11 -m pytest test_domain3_forensics.py test_domain4_diagnosis.py test_domain11_conversational.py test_domain12_safety.py -v

# Full 60-Query Benchmark (100% Pass)
py -3.11 run_60_all_domains_benchmark.py
```

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
