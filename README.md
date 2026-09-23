# Natural Language Incident Analytics & Reporting

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React 18](https://img.shields.io/badge/React-18.2.0-61DAFB?style=flat&logo=react)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5.0.0-646CFF?style=flat&logo=vite)](https://vitejs.dev)
[![ServiceNow PDI](https://img.shields.io/badge/ServiceNow-dev204434-81B5A1?style=flat&logo=servicenow)](https://dev204434.service-now.com)
[![Model Context Protocol](https://img.shields.io/badge/MCP-JSON--RPC%202.0-blueviolet?style=flat)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Compose%20Ready-2496ED?style=flat&logo=docker)](https://docker.com)

> **Enterprise AI Platform for ServiceNow ITSM, SRE Incident Operations & Boardroom-Ready Reporting**

The **Natural Language Incident Analytics & Reporting** platform empowers business leaders, Site Reliability Engineers (SREs), Incident Commanders, and IT operations teams to interrogate, analyze, and manage ServiceNow operational data in plain English.

Eliminating the traditional 24-48 hour wait time for custom ServiceNow reports, the application automatically translates natural language questions into native ServiceNow encoded queries (`sysparm_query`), executes live ticket queries or raises new incidents directly into ServiceNow, calculates key ITIL metrics (MTTR, MTBF, SLA adherence), clusters repeat root cause patterns, and compiles boardroom-ready executive briefs in PDF, Word, and Excel.

---

## Key Highlights

- **Natural Language Incident Ticketing**: Create and file live incidents directly into ServiceNow by describing problems in plain English (e.g., *"Ticket a ServiceNow incident: Oracle database connection timeout on SAP ORA01 (P1)"*).
- **Zero SQL / Zero GlideSystem Coding**: Plain natural language automatically translated into native ServiceNow `sysparm_query` filters.
- **Model Context Protocol (MCP) Standard**: Modular tool execution layer powered by decoupled JSON-RPC 2.0 servers (`servicenow_mcp_server`, `analytics_mcp_server`, `reporting_mcp_server`).
- **Live Connected ServiceNow PDI**: Pre-connected to active Personal Developer Instance `https://dev204434.service-now.com` with direct deep-links to Classic ServiceNow Navigator.
- **Dual-Mode High-Resilience Architecture**: Automatic, seamless failover to an enterprise simulation seed engine (100+ realistic ITIL records) if the ServiceNow PDI hibernates, guaranteeing 100% demo availability.
- **Dynamic Timeframe Analytics**: Instant filtering across `All Time`, `Past 30 Days`, `Past 6 Months`, `March 2026 Peak`, `Yesterday`, `Last Week`, and `Last Month` using live GlideSystem macros.
- **Multi-Format Boardroom Exports**: Single-click generation of executive briefs in formatted **PDF** (vector graphics), editable **Microsoft Word (`.docx`)**, and multi-tab **Microsoft Excel (`.xlsx`)**.
- **Enterprise AI Flexibility**: Seamless support for **NVIDIA NIM API** (`meta/llama-3.3-70b-instruct`), **OpenAI** (`gpt-4o`), and an offline deterministic **Semantic Engine** for zero-cost sub-50ms execution.

---

## System Architecture

```
+----------------------------------------------------------------------------------+
|                            PRESENTATION LAYER (REACT 18)                         |
|  +--------------------+  +--------------------+  +----------------------------+  |
|  |  Chat Assistant    |  |  KPI Dashboard     |  |  Recurring & Root Causes   |  |
|  +--------------------+  +--------------------+  +----------------------------+  |
|  +--------------------+  +--------------------+  +----------------------------+  |
|  | Outage Timeline    |  |  Executive Reports |  |  Admin & Audit Settings    |  |
|  +--------------------+  +--------------------+  +----------------------------+  |
+----------------------------------------+-----------------------------------------+
                                         | REST API / WebSocket
+----------------------------------------v-----------------------------------------+
|                      AI ORCHESTRATION GATEWAY (FASTAPI)                          |
|  +-------------------------+  +----------------------+  +---------------------+  |
|  | Intent Detection Engine |  | Query Translator     |  | Memory Manager      |  |
|  | (TICKET, OUTAGE, etc.)  |  | (NL -> sysparm_query)|  | (Multi-turn Context)|  |
|  +-------------------------+  +----------------------+  +---------------------+  |
+----------------------------------------+-----------------------------------------+
                                         | JSON-RPC 2.0 Tool Dispatches
+----------------------------------------v-----------------------------------------+
|                       MODEL CONTEXT PROTOCOL (MCP) LAYER                         |
|  +------------------------------+  +------------------------------------------+  |
|  | ServiceNow MCP Server        |  | Analytics MCP Server                     |  |
|  | * query_incidents            |  | * calculate_kpis (MTTR, MTBF, SLA)       |  |
|  | * get_incident_detail        |  | * cluster_recurring_incidents            |  |
|  | * create_incident (POST)     |  | * get_root_cause_leaderboard             |  |
|  | * query_problems / cmdb_ci   |  | * get_application_analytics              |  |
|  +------------------------------+  +------------------------------------------+  |
|  +----------------------------------------------------------------------------+  |
|  | Reporting MCP Server: generate_executive_report, export_report (PDF/DOCX/XLSX)|
|  +----------------------------------------------------------------------------+  |
+----------------------------------------+-----------------------------------------+
                                         | HTTPS / REST (SSL Proxy Safe)
+----------------------------------------v-----------------------------------------+
|                                DATA SOURCES                                      |
|  +-----------------------------------------+  +-------------------------------+  |
|  | Live ServiceNow PDI                     |  | Enterprise Simulation Engine  |  |
|  | (https://dev204434.service-now.com)     |  | (High-Fidelity Seed Fallback) |  |
|  | * incident, problem, change, cmdb, user |  | * 100+ Curated ITIL Records   |  |
|  +-----------------------------------------+  +-------------------------------+  |
+----------------------------------------------------------------------------------+
```

---

## Core Capabilities & Modules

### 1. Conversational Chat & Automated Incident Ticketing (`/chat`)
- **Querying**: Ask complex questions in plain English (*"Show all P1 critical incidents"*, *"Summarize INC0000001"*, *"What incidents occurred yesterday?"*).
- **Incident Ticketing**: Raise tickets directly into ServiceNow with plain English prompts:
  - *"Ticket a ServiceNow incident: Oracle database connection timeout on SAP ORA01 (P1)"*
  - *"Create an incident for corporate VPN access portal failure"*
  - *"Open a ticket: MailServerUS exchange connection drops with priority 2"*
- **Parameter Extraction**: Automatically extracts short description, priority (P1-P4), target CI (`cmdb_ci`), category (software, hardware, network, database), and assignment group.
- **Direct Deep-Links**: Immediate response provides the assigned ticket number (`INC...`) and a direct link to the ticket in ServiceNow Classic UI.
- **Transparency**: Inspect the exact `sysparm_query` or Table API payload, translation latency, and raw REST URL at any time.

### 2. Operational Incident Analytics Dashboard (`/dashboard`)
- **Executive KPIs**: Real-time cards for Total Incidents, Open Backlog, Closed Tickets, P1 Criticals, SLA Breaches, MTTR (Mean Time to Resolution), and MTBF (Mean Time Between Failures).
- **Visual Analytics**:
  - Severity Breakdown (Donut Chart: P1 Red, P2 Orange, P3 Yellow, P4 Blue).
  - Monthly & Daily Incident Volume (Smooth Gradient Trend Area Chart).
  - Assignment Group Workload (Ranked Horizontal Bar Chart).
  - Top Impacted Configuration Items (Application Impact Bar Chart).
- **Dynamic Timeframe Filters**: Filter instantly across `All Time`, `Past 30 Days`, `Past 6 Months`, `March 2026 (Peak)`, `Yesterday`, `Last Week`, and `Last Month`.

### 3. Recurring Incident Detection & Root Cause Analysis
- Automatically groups incidents sharing identical or similar error signatures.
- Maps clusters to affected Configuration Items (CIs), linked ServiceNow Problems (`PRB...`), root cause hypotheses, and actionable AI recommendations.
- Ranks systemic failure modes in the **Root Cause Leaderboard** by downtime percentage share.

### 4. Generative AI Incident Post-Mortem Summarization
- Click any incident number to open an SRE incident review structured into 4 pillars:
  1. **Operational Impact**: User-facing degradation, affected transactions, SLA status.
  2. **Identified Root Cause**: Technical bottleneck, resource exhaustion, or misconfiguration.
  3. **Resolution Summary**: Mitigations applied by the responding team.
  4. **Lessons Learned & Preventative Safeguards**: Permanent architectural fixes (circuit breakers, auto-scaling, certificate automation).

### 5. Outage Investigation Assistant
- Chronological Sev-1 major incident timeline reconstruction from detection (T-00:00) to recovery.
- Service dependency mapping visualizing blast radius across upstream and downstream configuration items.

### 6. Executive Reporting & Multi-Format Exports (`/reports`)
- Single-click compilation of period review deliverables.
- **PDF Export**: Branded ReportLab document with executive narrative, KPI scorecards, and recommendation tables.
- **Microsoft Word (`.docx`)**: Clean, formatted Word document with editable tables for executive leadership customization.
- **Microsoft Excel (`.xlsx`)**: Multi-tab analytical workbook (Tab 1: Executive Scorecard; Tab 2: Application Breakdown Matrix).

### 7. Admin Settings & Audit Telemetry (`/settings`)
- Dynamically switch ServiceNow instance URL, username, and password with masked credentials.
- **Interactive Connection Tester**: Test live handshake against ServiceNow Table APIs and view latency and HTTP status code.
- **Simulation Toggle**: Manually toggle or auto-fallback to high-fidelity seed data if PDI sleeps.
- **AI Provider Switcher**: Toggle between NVIDIA NIM API, OpenAI, or the offline Semantic Engine.
- **Audit Log**: Full transaction history recording timestamps, natural language prompts, generated queries, latency, and returned row counts.

---

## Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend UI** | React 18, Vite, Lucide Icons, Pure Vanilla CSS tokens (Dark/Light mode) |
| **Backend API** | Python 3.10+, FastAPI, Uvicorn, Pydantic, HTTPX, SQLite/PostgreSQL |
| **Protocol** | Model Context Protocol (MCP) via JSON-RPC 2.0 |
| **Document Generation** | `python-docx` (Word), `python-pptx` (PowerPoint), `reportlab` (PDF), `openpyxl` (Excel) |
| **AI / LLM Clients** | NVIDIA NIM API (`meta/llama-3.3-70b-instruct`), OpenAI (`gpt-4o`), Rule-Based Semantic Engine |
| **Target System** | ServiceNow Utah / Vancouver / Washington PDI (`/api/now/table/*`) |
| **Containerization** | Docker, Docker Compose, Nginx Alpine |

---

## Live ServiceNow PDI Connection Profile

The application comes pre-configured to connect to the developer instance:

- **Instance URL**: `https://dev204434.service-now.com`
- **Username**: `test`
- **Auth Protocol**: HTTP Basic Authentication (`Authorization: Basic ...`)
- **SSL Verification**: Configured with corporate proxy bypass (`verify=False`) to avoid `[SSL: CERTIFICATE_VERIFY_FAILED]` on corporate-inspected laptops.
- **Tables Integrated**:
  - `incident`: Ticket history, severity, assignment groups, opened/resolved timestamps, SLA state.
  - `problem`: Known error database, root cause records, workarounds.
  - `change_request`: Emergency and standard RFCs for correlation during outages.
  - `cmdb_ci`: Configuration items, hardware, servers, databases, applications.
  - `sys_user`: Caller and assignee profiles.

---

## Quickstart & Setup Guide

### 1. Prerequisites
- **Python**: 3.10 or higher (Tested with Python 3.13)
- **Node.js**: 18+ or 20+ with `npm`
- **ServiceNow Instance**: Free PDI from [developer.servicenow.com](https://developer.servicenow.com) (or use the built-in enterprise simulation engine)

### 2. Backend Setup
```powershell
# Navigate to backend directory
cd backend

# (Optional) Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI development server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
The backend API is now running at `http://localhost:8000`.
- Interactive Swagger UI: `http://localhost:8000/docs`
- Interactive ReDoc: `http://localhost:8000/redoc`

### 3. Frontend Setup
In a new terminal window:
```powershell
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
Open `http://localhost:5173` in your web browser.

---

## Environment Configuration

Create or modify `backend/.env`:

```env
# --- SERVICENOW CONNECTION ---
SERVICENOW_INSTANCE_URL=https://dev204434.service-now.com
SERVICENOW_USERNAME=test
SERVICENOW_PASSWORD=your_instance_password
SERVICENOW_USE_MOCK_FALLBACK=true

# --- AI / LLM ENGINE SELECTION ---
# Options: "nvidia", "openai", "semantic_engine"
LLM_PROVIDER=nvidia

# --- NVIDIA NIM CONFIGURATION ---
NVIDIA_API_KEY=your_nvidia_api_key_here
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=meta/llama-3.3-70b-instruct

# --- OPENAI CONFIGURATION (Optional fallback) ---
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o

# --- SECURITY & APP CONFIG ---
SECRET_KEY=enterprise-secret-key-change-in-production
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173
```

---

## Model Context Protocol (MCP) Tool Reference

The platform adheres to the open [Model Context Protocol](https://modelcontextprotocol.io). External LLMs, agent frameworks, or scripts can invoke tools via JSON-RPC 2.0 at `POST /api/mcp/rpc`:

### 1. `servicenow_mcp_server`
- `query_incidents(sysparm_query, limit, offset)`: Queries ServiceNow incident table with encoded filters.
- `get_incident_detail(identifier)`: Retrieves complete ticket metadata, caller, CI, and deep links.
- `create_incident(short_description, description, priority, category, cmdb_ci, assignment_group)`: Dispatches `POST /api/now/table/incident` to create a live incident in ServiceNow.
- `query_problems(sysparm_query)`: Queries root causes, workarounds, and problem records.
- `query_cmdb_ci(sysparm_query)`: Queries Configuration Items (CIs) from the CMDB.

### 2. `analytics_mcp_server`
- `calculate_kpis(filter_query)`: Computes Total, Open, Closed, P1s, MTTR, MTBF, and SLA adherence rate.
- `cluster_recurring_incidents(min_occurrences)`: Discovers recurring failure patterns and formulates remediations.
- `get_root_cause_leaderboard()`: Computes ranked failure mode frequencies.
- `get_application_analytics(top_n, filter_query)`: Computes multi-application incident distribution for the specified timeframe.

### 3. `reporting_mcp_server`
- `generate_executive_report(period_title, filter_query)`: Compiles structured executive brief payloads.
- `export_report_document(format, report_payload)`: Renders binary document streams for PDF, DOCX, and XLSX.

#### Example JSON-RPC Tool Call:
```json
POST /api/mcp/rpc
{
  "jsonrpc": "2.0",
  "id": 101,
  "method": "tools/call",
  "params": {
    "name": "calculate_kpis",
    "arguments": {
      "filter_query": "priority=1^opened_atONLast month@javascript:gs.beginningOfLastMonth()@javascript:gs.endOfLastMonth()"
    }
  }
}
```

---

## Query Translation Catalog

| Natural Language Request | Detected Intent | Target Action / Generated Query |
| :--- | :--- | :--- |
| *"Ticket a ServiceNow incident: Oracle database connection timeout on SAP ORA01 (P1)"* | `CREATE_INCIDENT` | `POST /api/now/table/incident` (P1, SAP ORA01, Database) |
| *"Create an incident for corporate VPN access portal failure"* | `CREATE_INCIDENT` | `POST /api/now/table/incident` (P3, VPN Gateway, Network) |
| *"What incidents were reported yesterday?"* | `QUERY_INCIDENTS` | `opened_atONYesterday@javascript:gs.beginningOfYesterday()@javascript:gs.endOfYesterday()^ORDERBYDESCopened_at` |
| *"Show all P1 incidents from last week"* | `QUERY_INCIDENTS` | `priority=1^opened_atONLast week@javascript:gs.beginningOfLastWeek()@javascript:gs.endOfLastWeek()^ORDERBYDESCopened_at` |
| *"How many incidents are currently open?"* | `METRICS_KPI` | `stateIN1,2,3^active=true^ORDERBYDESCopened_at` |
| *"List all incidents assigned to Network team"* | `QUERY_INCIDENTS` | `assignment_groupLIKENetwork^ORDERBYDESCopened_at` |
| *"Show incidents for MailServerUS"* | `QUERY_INCIDENTS` | `short_descriptionLIKEMailServerUS^ORcmdb_ciLIKEMailServerUS^ORDERBYDESCopened_at` |
| *"Provide details of the outage reported last month"* | `OUTAGE_INVESTIGATION` | `priority=1^short_descriptionLIKEoutage^opened_atONLast month@javascript:gs.beginningOfLastMonth()@javascript:gs.endOfLastMonth()^ORDERBYDESCopened_at` |
| *"Identify recurring incidents and root causes"* | `RECURRING_ANALYSIS` | Dispatches to `analytics_mcp_server.cluster_recurring_incidents` |
| *"What are the most common root causes?"* | `RCA_LOOKUP` | Dispatches to `analytics_mcp_server.get_root_cause_leaderboard` |
| *"Which applications generated the most incidents?"* | `APPLICATION_ANALYTICS` | Dispatches to `analytics_mcp_server.get_application_analytics` |
| *"Create incident report for March 2026"* | `REPORT_GENERATION` | Dispatches to `reporting_mcp_server.generate_executive_report` |

---

## Docker Production Deployment

Run the complete multi-container stack with a single command:

```bash
docker compose up --build -d
```

Containers provisioned:
1. `incident_ai_frontend`: Nginx serving optimized React bundle on Port 80.
2. `incident_ai_backend`: FastAPI running with Uvicorn on Port 8000.
3. `incident_ai_postgres`: PostgreSQL 16 database storing audit logs and cache on Port 5432.
4. `incident_ai_redis`: Redis 7 managing session memory on Port 6379.

---

## Automated Test Suite

Run the full automated test suite using `pytest`:

```powershell
cd backend
pytest tests/ -v
```

### Key Test Suites:
- `tests/test_all.py`: End-to-end testing of chat routing, MCP tool execution, query translation, and export endpoints.
- `tests/test_incident_creation.py`: Unit and integration testing of natural language incident creation into ServiceNow Table API.
- `tests/test_dashboard_timeframes.py`: Verification of dynamic timeframe query building (`build_timeframe_query`) and zero-incident handling.

---

## Project Structure

```
Natural Language Analytics/
├── README.md                                # Master Project Documentation & Quickstart
├── USER_MANUAL.md                           # Enterprise User Manual & Operational Reference Guide
├── USER_MANUAL.docx                         # Formatted Word Document User Manual
├── USER_MANUAL_SERVICENOW.docx              # Mirrored Word Document User Manual
├── Natural_Language_Incident_Analytics.pptx # Executive 12-Slide Boardroom Presentation
├── DEPLOYMENT_GUIDE.md                      # Production Deployment & PDI Connectivity Guide
├── API_DOCUMENTATION.md                     # Comprehensive REST API & MCP RPC Documentation
├── build_complete_user_manual.py            # Automated User Manual & Word Docx Generator
├── generate_clean_ppt.py                    # Automated Clean & White PowerPoint Deck Generator
├── docker-compose.yml                       # Production Multi-Container Orchestration
├── Dockerfile.backend                       # Container image for FastAPI Backend
├── Dockerfile.frontend                      # Multi-stage Container image for React & Nginx
├── nginx.conf                               # Nginx reverse proxy configuration
│
├── backend/                                 # FastAPI Backend Service
│   ├── app/
│   │   ├── ai/                              # AI Orchestration, Intent Detection & LLMs
│   │   │   ├── intent_detector.py           # Multi-intent classifier (Create, Query, Outage, etc.)
│   │   │   ├── query_translator.py          # NL to ServiceNow sysparm_query generator
│   │   │   ├── llm_client.py                # NVIDIA NIM, OpenAI & Semantic fallback client
│   │   │   └── insights_engine.py           # Automated executive narrative synthesizer
│   │   ├── api/routes/                      # REST Endpoints
│   │   │   ├── chat.py                      # Conversational chat & ticketing endpoint (/api/chat)
│   │   │   ├── dashboard.py                 # KPI metrics & analytics endpoint (/api/dashboard)
│   │   │   ├── incidents.py                 # ServiceNow incident retrieval & filtering
│   │   │   ├── reports.py                   # Report generation & PDF/DOCX/XLSX export
│   │   │   ├── mcp_routes.py                # Model Context Protocol JSON-RPC handler
│   │   │   └── settings.py                  # PDI connection configuration & audit trail
│   │   ├── core/config.py                   # Application settings & environment variables
│   │   ├── mcp/                             # Model Context Protocol Servers
│   │   │   ├── servicenow_mcp.py            # ServiceNow Table API MCP tool server
│   │   │   ├── analytics_mcp.py             # KPI & clustering MCP tool server
│   │   │   └── reporting_mcp.py             # Executive reporting & document export server
│   │   ├── models/schemas.py                # Pydantic data schemas
│   │   └── services/servicenow.py           # ServiceNow HTTP client with simulation fallback
│   ├── requirements.txt                     # Backend Python dependencies
│   └── tests/                               # Pytest automated test suite
│
└── frontend/                                # React 18 + Vite Frontend Application
    ├── src/
    │   ├── api.js                           # Axios API client functions
    │   ├── index.css                        # Design system & dark/light theme CSS tokens
    │   ├── components/                      # Reusable UI Components
    │   │   ├── Sidebar.jsx                  # Primary navigation & ServiceNow status indicator
    │   │   ├── KpiCard.jsx                  # Visual stat card with icons & trends
    │   │   ├── Charts.jsx                   # SVG Charts (Donut, Area Trend, Horizontal Bar)
    │   │   └── MarkdownRenderer.jsx         # Code-highlighted rich text renderer
    │   └── pages/                           # Application Pages
    │       ├── ChatAssistantPage.jsx        # Conversational AI & incident ticketing page
    │       ├── IncidentAnalyticsDashboardPage.jsx # Operational KPI & metrics dashboard
    │       ├── ExecutiveReportsPage.jsx     # Period reports & PDF/DOCX/XLSX export page
    │       └── AdminSettingsPage.jsx        # ServiceNow credentials & audit telemetry page
    ├── package.json                         # Frontend dependencies
    └── vite.config.js                       # Vite build configuration
```

---

## Documentation & Deliverable Artifacts Index

- [USER_MANUAL.md](file:///c:/Users/lchintal/OneDrive%20-%20Capgemini/Desktop/Natural%20Language%20Analytics/USER_MANUAL.md): Complete operational user manual with step-by-step guides.
- [USER_MANUAL_SERVICENOW.docx](file:///c:/Users/lchintal/OneDrive%20-%20Capgemini/Desktop/Natural%20Language%20Analytics/USER_MANUAL_SERVICENOW.docx): Formatted Microsoft Word version of the complete user manual.
- [Natural_Language_Incident_Analytics.pptx](file:///c:/Users/lchintal/OneDrive%20-%20Capgemini/Desktop/Natural%20Language%20Analytics/Natural_Language_Incident_Analytics.pptx): Boardroom-ready 12-slide executive presentation in 16:9 widescreen format.
- [DEPLOYMENT_GUIDE.md](file:///c:/Users/lchintal/OneDrive%20-%20Capgemini/Desktop/Natural%20Language%20Analytics/DEPLOYMENT_GUIDE.md): Detailed installation, ServiceNow PDI setup, and Docker production runbook.
- [API_DOCUMENTATION.md](file:///c:/Users/lchintal/OneDrive%20-%20Capgemini/Desktop/Natural%20Language%20Analytics/API_DOCUMENTATION.md): Complete endpoint guide, JSON schemas, and Model Context Protocol RPC reference.
