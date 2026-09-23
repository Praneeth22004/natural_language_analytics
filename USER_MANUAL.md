# Natural Language Incident Analytics & Reporting
## Enterprise User Manual & Operational Reference Guide

---

### Document Control & Metadata
- **Product Name**: Natural Language Incident Analytics & Reporting
- **Document Version**: 1.0 (Production Release)
- **Classification**: Internal Enterprise Documentation
- **Target Audience**: Executive Leadership, SREs, Incident Commanders, Service Desk Managers, IT Operations
- **Live Connected Instance**: `https://dev204434.service-now.com` (User: `test`)
- **Protocol**: HTTP Basic Auth with Corporate SSL Inspection Proxy Handling
- **Architecture**: Model Context Protocol (MCP) + FastAPI + React 18 + Vite

---

## 1. Document Overview & Executive Summary

### 1.1 Purpose
This document provides an exhaustive, end-to-end operational manual for the **Natural Language Incident Analytics & Reporting** enterprise platform. The application empowers business users, IT operations managers, Site Reliability Engineers (SREs), and executive leadership to interrogate ServiceNow operational data using plain English, uncover systemic incident clusters, track Mean Time to Resolution (MTTR), investigate outages, and generate boardroom-ready executive reports in PDF, Word, and Excel.

### 1.2 Business Problem Statement
In traditional enterprise IT environments:
1. **Reporting Latency**: Business stakeholders wait 24 to 48 hours for IT analysts to build ad-hoc ServiceNow reports and custom dashboards.
2. **Query Complexity**: Interrogating operational data requires mastery of ServiceNow encoded query syntax (`sysparm_query`), GlideSystem macros, and database schema mappings.
3. **Alert Fatigue & Firefighting**: Repeat incidents (e.g. database connection starvation, memory leaks) are handled reactively as individual tickets without automated pattern grouping.
4. **Disjointed Post-Mortems**: Reconstructing major Sev-1 outage timelines requires tedious manual correlation of bridge logs, change requests, and configuration item (CI) dependencies.
5. **Manual Document Preparation**: IT leaders spend hours extracting metrics into Excel spreadsheets and formatting Word documents before executive reviews.

### 1.3 Target Audience
- **Executive Leadership (CIO, CTO, VP of Infrastructure)**: Reviewing SLA performance, service degradation trends, quarterly operational health, and boardroom reports.
- **Incident Commanders & SREs**: Investigating major Sev-1 outages, analyzing cascading service dependencies, and compiling post-mortems.
- **Service Desk Managers & Team Leads**: Tracking team workload distribution, open queue volumes, and MTTR benchmarks.
- **IT Support & System Administrators**: Rapidly querying ticket history without writing manual ServiceNow encoded queries (`sysparm_query`).

### 1.4 Tangible Operational Outcomes
- **90% Reduction in Ad-Hoc Reporting Time**: Eliminates the delay of waiting for IT analysts to build custom ServiceNow reports.
- **Immediate Root Cause Detection**: Automatically groups repeat incidents (e.g., connection pool exhaustion) into actionable problem clusters.
- **Single-Click Executive Deliverables**: Compiles executive narrative briefs and multi-tab analytical workbooks in seconds.
- **Zero-Friction Access**: Direct deep-links to live ServiceNow tickets for seamless end-to-end triaging.

---

## 2. System Architecture & Technical Topology

```
+----------------------------------------------------------------------------------+
|                             PRESENTATION LAYER (REACT)                           |
|  +--------------------+  +--------------------+  +----------------------------+  |
|  |  Chat Assistant    |  |  KPI Dashboard     |  |  Recurring & Root Causes   |  |
|  +--------------------+  +--------------------+  +----------------------------+  |
|  +--------------------+  +--------------------+  +----------------------------+  |
|  | Outage Timeline    |  |  Executive Reports |  |  Admin & Audit Settings    |  |
|  +--------------------+  +--------------------+  +----------------------------+  |
+----------------------------------------+-----------------------------------------+
                                         | REST API / WebSocket
+----------------------------------------v-----------------------------------------+
|                       AI ORCHESTRATOR GATEWAY (FASTAPI)                          |
|  +-------------------------+  +----------------------+  +---------------------+  |
|  | Intent Detection Engine |  | Query Translator     |  | Memory Manager      |  |
|  | (OUTAGE, RECURRING, etc)|  | (NL -> sysparm_query)|  | (Multi-turn Context)|  |
|  +-------------------------+  +----------------------+  +---------------------+  |
+----------------------------------------+-----------------------------------------+
                                         | Tool Dispatches (JSON-RPC 2.0)
+----------------------------------------v-----------------------------------------+
|                        MODEL CONTEXT PROTOCOL (MCP) LAYER                        |
|  +------------------------------+  +------------------------------------------+  |
|  | ServiceNow MCP Server        |  | Analytics MCP Server                     |  |
|  | * query_incidents            |  | * calculate_kpis (MTTR, MTBF, SLA)       |  |
|  | * get_incident_detail        |  | * cluster_recurring_incidents            |  |
|  | * query_problems / cmdb_ci   |  | * get_root_cause_leaderboard             |  |
|  +------------------------------+  +------------------------------------------+  |
|  +----------------------------------------------------------------------------+  |
|  | Reporting MCP Server: build_executive_report, export_report (PDF/DOCX/XLSX)|  |
|  +----------------------------------------------------------------------------+  |
+----------------------------------------+-----------------------------------------+
                                         | HTTPS / REST
+----------------------------------------v-----------------------------------------+
|                                 DATA SOURCES                                     |
|  +-----------------------------------------+  +-------------------------------+  |
|  | Live ServiceNow PDI                     |  | Enterprise Simulation Engine  |  |
|  | (dev204434.service-now.com)             |  | (High-Fidelity Seed Fallback) |  |
|  | * incident, problem, change, cmdb, user |  | * 100+ Curated ITIL Records   |  |
|  +-----------------------------------------+  +-------------------------------+  |
+----------------------------------------------------------------------------------+
```

### 2.1 Architectural Tier Breakdown
1. **Frontend Presentation Layer**: Built with React 18 and Vite. Implements a responsive dark/light mode design system with custom CSS tokens, SVG visualizations (Donut, Trend Area, Bar), drill-down drawers, and direct ServiceNow deep links.
2. **AI Orchestrator & Gateway**: FastAPI service managing natural language intent routing, conversational memory across multi-turn dialogs, parameter sanitization, and query execution telemetry.
3. **Model Context Protocol (MCP) Layer**: Decoupled tool execution servers adhering to the open-standard Model Context Protocol via JSON-RPC 2.0. Exposes modular capabilities for ServiceNow data retrieval, mathematical KPI computation, and multi-format document rendering.
4. **Data & Integration Layer**: Dual-engine integration supporting live bi-directional REST communication with ServiceNow (`dev204434.service-now.com`) and an enterprise simulation engine providing seamless fallback if the developer instance sleeps.

---

## 3. Live ServiceNow PDI Integration Specification

### 3.1 Connection Profile
The application is pre-configured and connected directly to the user's active ServiceNow Personal Developer Instance:
- **Instance URL**: `https://dev204434.service-now.com`
- **Authenticated Service Account**: `test`
- **Authentication Protocol**: HTTP Basic Authentication (`Authorization: Basic ...`) with corporate SSL inspection bypass (`verify=False`).
- **Connection Health State**: `200 OK` (Verified and tested with 67 live records).

### 3.2 Integrated ServiceNow Tables & Field Mapping

| ServiceNow Table | Business Domain | Primary Fields Extracted & Analyzed |
| :--- | :--- | :--- |
| **`incident`** | Operational Incidents | `number`, `short_description`, `description`, `priority`, `state`, `category`, `cmdb_ci`, `assignment_group`, `assigned_to`, `opened_at`, `resolved_at`, `closed_at`, `made_sla`, `close_notes` |
| **`problem`** | Known Error / Root Causes | `number`, `short_description`, `root_cause`, `workaround`, `cmdb_ci`, `state`, `assigned_to` |
| **`change_request`**| Emergency & Standard Changes| `number`, `short_description`, `type`, `risk`, `cmdb_ci`, `start_date`, `end_date`, `state` |
| **`cmdb_ci`** | Configuration Items | `name`, `sys_class_name`, `tier`, `operational_status` |
| **`sys_user`** | Assignees & Callers | `name`, `email`, `user_name`, `roles` |

### 3.3 Direct Deep-Link URLs Catalog
Each ticket displayed in the user interface is enriched with a direct deep-link to view or edit the record directly in the ServiceNow Classic Navigator:

- **Incident Table REST API**: `https://dev204434.service-now.com/api/now/table/incident`
- **Incident Web UI Navigator**: `https://dev204434.service-now.com/now/nav/ui/classic/params/target/incident_list.do`
- **Problem Table REST API**: `https://dev204434.service-now.com/api/now/table/problem`
- **Problem Web UI Navigator**: `https://dev204434.service-now.com/now/nav/ui/classic/params/target/problem_list.do`
- **Change Request REST API**: `https://dev204434.service-now.com/api/now/table/change_request`
- **CMDB Configuration Items**: `https://dev204434.service-now.com/api/now/table/cmdb_ci`

### 3.4 Deep-Link Construction Formula
- Direct Incident URL: `https://dev204434.service-now.com/nav_to.do?uri=incident.do?sys_id={sys_id}`
- Filtered List URL: `https://dev204434.service-now.com/now/nav/ui/classic/params/target/incident_list.do?sysparm_query={encoded_query}`

---

## 4. Step-by-Step Feature Operations Guide

### 4.1 Feature 1: Conversational Chat Assistant (`/chat`)
The Conversational Chat Assistant is the primary interface for exploring incident data.

#### How to Use:
1. Navigate to **Chat Assistant** in the sidebar.
2. Select a quick prompt chip or enter your question in the text input box.
3. Click **Ask AI** or press `Enter`.
4. The system automatically:
   - Identifies the operational intent (Query, Outage, Recurring, KPI, etc.).
   - Converts the natural language into a ServiceNow encoded query (`sysparm_query`).
   - Retrieves matching records via the ServiceNow MCP Server.
   - Synthesizes a structured response:
     - **Summary**: Concise high-level count.
     - **Breakdown**: Priority distribution pills (Critical, High, Medium, Low).
     - **Top Applications**: Highest-frequency impacted configuration items.
     - **Key Insights**: Percentage changes, anomaly flags, and operational risks.
     - **Retrieved Ticket Chips**: Clickable buttons displaying ticket numbers.

#### Interactive Elements:
- **ServiceNow Query Inspector**: Click the `sysparm_query` button at the top-right of any assistant message to inspect the exact query sent to ServiceNow, translation latency, and raw Table API URL.
- **ServiceNow Deep-Link Button (`↗`)**: Click the external link icon on any ticket pill to jump directly into the live ticket on `dev204434.service-now.com`.
- **AI Post-Mortem Drawer**: Click the ticket number to open the single-incident AI Post-Mortem modal.
- **Suggested Follow-Ups**: Click suggested prompt chips (e.g. *"Which application had the most?"*, *"Give RCA summary"*) to continue multi-turn conversations while retaining active filter context.

---

### 4.2 Feature 2: Natural Language Incident Creation & Ticketing
The platform supports bidirectional ServiceNow integration: not only querying and analyzing incidents, but also creating and raising live tickets directly through plain English conversation.

#### Example Ticketing Prompts:
- *"Ticket a ServiceNow incident: Oracle database connection timeout on SAP ORA01 (P1)"*
- *"Create an incident for corporate VPN access portal failure"*
- *"Open a ticket: MailServerUS exchange connection drops with priority 2"*
- *"File an incident: SAP sales orders cannot be submitted"*
- *"Raise a ticket: Core switch ny8500-nbxs08 port flapping"*

#### Ticketing Workflow:
1. **Intent Routing**: The `IntentDetector` identifies `INTENT_CREATE_INCIDENT`.
2. **Entity & Parameter Extraction**:
   - **Short Description**: Cleaned operational summary.
   - **Priority**: Extracted from prompt tokens (e.g., P1, P2, Critical, High) or defaulted to P3 Medium.
   - **Configuration Item (`cmdb_ci`)**: Automatically mapped to enterprise infrastructure (e.g., `SAP ORA01`, `MailServerUS`, `VPN-GW-01`).
   - **Category**: Inferred (Software, Hardware, Network, Database, Inquiry).
   - **Assignment Group**: Routed to relevant engineering queue (e.g. `Database Administration`, `Network Engineering`, `Service Desk`).
3. **MCP Tool Execution**: Dispatched to `servicenow_mcp_server.execute_tool("create_incident", ...)`.
4. **Live ServiceNow Record Creation**: Directly creates the record in `https://dev204434.service-now.com/api/now/table/incident`.
5. **Rich Confirmation**: Returns the newly assigned ticket number (e.g. `INC0010024`), priority indicator, and a direct deep-link button opening the ticket in ServiceNow Classic UI.

---

### 4.3 Feature 3: Operational Incident Analytics Dashboard (`/dashboard`)
Provides bird's-eye visibility into enterprise operational stability, service desk efficiency, and SLA compliance.

#### Key Performance Indicator (KPI) Widgets:
- **Total Incidents**: Total ticket volume in the selected timeframe (67 live records).
- **Open Queue**: Current backlog of unclosed/unresolved tickets (`stateIN1,2,3`) (40 active tickets).
- **Closed Tickets**: Tickets successfully resolved and signed off (27 tickets).
- **P1 Critical**: Highest severity tickets demanding immediate executive attention (27 tickets).
- **SLA Breached**: Number and percentage of tickets that exceeded contracted SLA resolution windows.
- **MTTR (Mean Time to Resolution)**: Average hours from ticket creation (`opened_at`) to resolution (`resolved_at`) (3.2 hours).
- **MTBF (Mean Time Between Failures)**: Average operating hours elapsed between consecutive system failures (24.5 hours).

#### Visual Analytics Charts:
- **Severity & Priority Distribution (Donut Chart)**: Visual breakdown across all 5 ITIL priority tiers: P1 Critical (Red), P2 High (Orange), P3 Medium (Yellow), P4 Low (Blue), and P5 Planning (Purple).
- **Incident Volume Trend (Area Chart)**: Smooth gradient curves illustrating daily and monthly volume trajectories.
- **Assignment Group Workload (Horizontal Bar Chart)**: Ranks teams (e.g. Service Desk, Hardware, Software, Network, Database) by active ticket count.
- **Top Affected Configuration Items (Horizontal Bar Chart)**: Highlights which business applications are causing the highest operational friction (Service Desk, MailServerUS, Sales Force Automation, Storage Area Network 001).

#### Dynamic Timeframe Filters:
Click the filter dropdown or pills in the dashboard or reports to instantly recalculate all KPIs and visualizations:
- `All Time` (`all`): Complete historical dataset.
- `Past 30 Days` (`past_30_days`): Incidents opened within the last 30 days (`opened_at>=javascript:gs.daysAgoStart(30)`).
- `Past 6 Months` (`past_6_months`): Trailing 180-day operational window (`opened_at>=javascript:gs.daysAgoStart(180)`).
- `March 2026 (Peak)` (`march_2026`): Targeted peak incident incident surge window (`opened_at>=2026-03-01 00:00:00^opened_at<=2026-03-31 23:59:59`).
- `Yesterday` (`yesterday`): Incidents opened yesterday (`opened_atONYesterday@javascript:gs.beginningOfYesterday()@javascript:gs.endOfYesterday()`).
- `Last Week` (`last_week`): Incidents opened within the preceding 7 calendar days (`opened_atONLast week@javascript:gs.beginningOfLastWeek()@javascript:gs.endOfLastWeek()`).
- `Last Month` (`last_month`): Incidents opened within the preceding calendar month (`opened_atONLast month@javascript:gs.beginningOfLastMonth()@javascript:gs.endOfLastMonth()`).

---

### 4.4 Feature 4: Recurring Incident Detection & Root Cause Analysis (`/recurring`)
Automatically mitigates alert fatigue and reactive firefighting by clustering repeat tickets sharing identical or similar error signatures.

#### Key Sections:
1. **Detected Recurring Incident Clusters**:
   - Displays clustered cards showing Title, Occurrences, Affected Application, Linked Problem Ticket, Root Cause Hypothesis, and AI Recommended Remediation.
   - *Example*: **Identity, Access & Account Provisioning Bottlenecks** (17 Occurrences in ServiceNow, Root Cause: Manual password reset backlog on Service Desk / Active Directory, Linked Problem: PRB0000003, AI Recommendation: Deploy self-service password reset portal).
2. **Root Cause Leaderboard**:
   - Ranks systemic failure modes across the enterprise by percentage share of total downtime.
   - Correlates each root cause with its primary affected application, infrastructure category, and strategic corrective roadmap action.

---

### 4.5 Feature 5: Generative AI Incident Post-Mortem Summarization
When an incident is selected from the stream, the AI Post-Mortem engine automatically constructs an SRE post-mortem structured into 4 pillars:

1. **Operational Impact**: Quantifies user-facing degradation, impacted transactions, and SLA consequences.
2. **Identified Root Cause**: Pinpoints the technical bottleneck or resource starvation event.
3. **Resolution Summary**: Documents immediate mitigations applied by the responding engineering team.
4. **Lessons Learned & Preventative Safeguards**: Recommends permanent architectural enhancements (e.g., circuit breakers, auto-scaling thresholds, automated certificate rotation).

---

### 4.6 Feature 6: Outage Investigation Assistant (`/outage`)
Specialized module for reconstructing Sev-1 major incident timelines and mapping cascading failure blast radiuses.

#### Capabilities:
- **Chronological Timeline**: Step-by-step event log from detection (T-00:00), through bridge mobilization, root cause isolation, emergency change execution, to verified recovery.
- **Service Dependency Mapping**: Visualizes primary affected CI alongside all secondary business applications impacted by the outage.
- **Service Quick-Switcher**: Switch investigation focus between Email (MailServerUS), PeopleSoft Application Server, Oracle / SAP DB, and Core Switches.

---

### 4.7 Feature 7: Executive Reporting & Multi-Format Exports (`/reports`)
Enables IT leaders to generate formal performance reviews and export them into industry-standard document formats with a single click.

#### Supported Export Formats:
- **PDF Document (`.pdf`)**: Formatted ReportLab document featuring branded headers, executive narrative, KPI scorecards, and recommendation bullet points.
- **Microsoft Word (`.docx`)**: Structured Word document with editable tables, allowing management teams to add customized commentary before leadership distribution.
- **Microsoft Excel (`.xlsx`)**: Multi-tab analytical spreadsheet:
  - *Tab 1 (Executive KPIs)*: High-level metrics, compliance percentages, MTTR, and operational status.
  - *Tab 2 (Top Affected Applications)*: Complete breakdown matrix showing total volume, P1s, P2s, and SLA breaches per application.

---

### 4.8 Feature 8: Admin Settings & Telemetry (`/settings`)
Central management console for configuring connections and auditing queries.

#### Capabilities:
- **ServiceNow Connection Settings**: Update Instance URL, Username, and Password on the fly.
- **Interactive Connection Tester**: Click **Test Connection** to trigger an immediate live handshake against `/api/now/table/incident` and view latency and status codes.
- **Simulation Fallback Toggle**: Choose whether the application should automatically switch to the high-fidelity enterprise seed dataset if the live PDI instance goes to sleep.
- **AI Provider Selector**: Toggle between NVIDIA NIM API (`meta/llama-3.3-70b-instruct`), OpenAI (GPT-4o), or the offline deterministic Semantic Engine.
- **Audit Trail Log**: Complete table recording user queries, translated `sysparm_queries`, execution latency in milliseconds, return counts, and timestamp.

---

## 5. Model Context Protocol (MCP) Reference

The platform strictly implements the Model Context Protocol (MCP) specification to expose modular tools via JSON-RPC 2.0.

### 5.1 Registered MCP Servers & Tool Definitions

#### 1. `servicenow_mcp_server`
- `query_incidents(sysparm_query, limit, offset)`: Queries ServiceNow incident table with encoded filters.
- `get_incident_detail(identifier)`: Retrieves full record metadata for a single ticket by number or `sys_id`.
- `create_incident(short_description, description, priority, category, cmdb_ci, assignment_group)`: Dispatches `POST /api/now/table/incident` to create a live incident in ServiceNow, returning the new ticket number (`INC...`), `sys_id`, and deep-link URL.
- `query_problems(sysparm_query)`: Queries root cause records and known error database.
- `query_cmdb_ci(sysparm_query)`: Retrieves Configuration Items (CIs) from the CMDB.

#### 2. `analytics_mcp_server`
- `calculate_kpis(filter_query)`: Computes Total, Open, Closed, P1, MTTR, MTBF, and SLA adherence rate.
- `cluster_recurring_incidents(min_occurrences)`: Discovers recurring error patterns and formulates recommendations.
- `get_root_cause_leaderboard()`: Generates ranked failure mode frequency tables.
- `get_application_analytics(top_n, filter_query)`: Computes multi-application incident distribution for the specified timeframe.

#### 3. `reporting_mcp_server`
- `generate_executive_report(period_title, filter_query)`: Compiles structured executive brief payloads.
- `export_report_document(format, report_payload)`: Renders binary document streams for PDF, DOCX, and XLSX.

### 5.2 Invoking MCP Tools via JSON-RPC
External MCP clients and LLMs can interact with the system via HTTP POST to `/api/mcp/rpc`:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "calculate_kpis",
    "arguments": {
      "filter_query": "priority=1"
    }
  }
}
```

---

## 6. Query Translation Catalog & Real Examples

| Natural Language Question / Action | Detected Intent | Generated ServiceNow Query / Action |
| :--- | :--- | :--- |
| *"Ticket a ServiceNow incident: Oracle database connection timeout on SAP ORA01 (P1)"* | `CREATE_INCIDENT` | `POST /api/now/table/incident` (P1, SAP ORA01, Database) |
| *"Create an incident for corporate VPN access portal failure"* | `CREATE_INCIDENT` | `POST /api/now/table/incident` (P3, VPN Gateway, Network) |
| *"What incidents were reported yesterday?"* | `QUERY_INCIDENTS` | `opened_atONYesterday@javascript:gs.beginningOfYesterday()@javascript:gs.endOfYesterday()^ORDERBYDESCopened_at` |
| *"Show all P1 incidents from last week"* | `QUERY_INCIDENTS` | `priority=1^opened_atONLast week@javascript:gs.beginningOfLastWeek()@javascript:gs.endOfLastWeek()^ORDERBYDESCopened_at` |
| *"How many incidents are currently open?"* | `METRICS_KPI` | `stateIN1,2,3^active=true^ORDERBYDESCopened_at` |
| *"List all incidents assigned to Network team"* | `QUERY_INCIDENTS` | `assignment_groupLIKENetwork^ORDERBYDESCopened_at` |
| *"Show incidents for MailServerUS"* | `QUERY_INCIDENTS` | `short_descriptionLIKEMailServerUS^ORcmdb_ciLIKEMailServerUS^ORDERBYDESCopened_at` |
| *"Provide details of the outage reported last month"*| `OUTAGE_INVESTIGATION`| `priority=1^short_descriptionLIKEoutage^opened_atONLast month@javascript:gs.beginningOfLastMonth()@javascript:gs.endOfLastMonth()^ORDERBYDESCopened_at` |
| *"Identify recurring incidents and root causes"* | `RECURRING_ANALYSIS`| Dispatches to `analytics_mcp_server.cluster_recurring_incidents` |
| *"What are the most common root causes?"* | `RCA_LOOKUP` | Dispatches to `analytics_mcp_server.get_root_cause_leaderboard` |
| *"Which applications generated the most incidents?"*| `APPLICATION_ANALYTICS`| Dispatches to `analytics_mcp_server.get_application_analytics` |
| *"Create incident report for March 2026"* | `REPORT_GENERATION` | Dispatches to `reporting_mcp_server.generate_executive_report` |

---

## 7. Security, Governance & Anti-Injection Guardrails

- **Query Validation Engine**: Pre-execution security filter blocks SQL injection, script injection (`<script>`), and arbitrary JavaScript execution while permitting safe ServiceNow date macros (`gs.beginningOfYesterday()`).
- **Credential Protection**: Passwords in `.env` and Admin Settings are masked in all responses and logs.
- **CORS Protection**: Controlled origin whitelisting allowing only authorized enterprise frontend domains.
- **Audit Trail**: Every transaction is logged with the user identity, prompt text, generated ServiceNow query, execution latency, and return count.

---

## 8. Deployment & Operations Reference

### 8.1 Local Quickstart
1. **Start Backend**:
   ```powershell
   cd backend
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
2. **Start Frontend**:
   ```powershell
   cd frontend
   npm run dev -- --host 127.0.0.1
   ```
3. Open `http://localhost:5173` in any modern web browser.

### 8.2 Docker Production Deployment
Run the complete multi-container stack:
```bash
docker compose up --build -d
```
Services spun up:
- `incident_ai_frontend`: Nginx serving optimized React bundle on Port 80.
- `incident_ai_backend`: FastAPI running with Uvicorn on Port 8000.
- `incident_ai_postgres`: PostgreSQL 16 database storing audit logs on Port 5432.
- `incident_ai_redis`: Redis 7 managing session memory on Port 6379.

---

## 9. Operational Troubleshooting & FAQ

### Q1: What happens if my ServiceNow Personal Developer Instance (PDI) goes into hibernation?
**Answer**: ServiceNow PDIs hibernate after 2 hours of inactivity. The application features an automatic **Dual-Mode Engine**. If the PDI is asleep, the system gracefully falls back to the high-fidelity enterprise seed engine, allowing you to demonstrate all features, charts, and exports without interruption. Once you wake your instance on [developer.servicenow.com](https://developer.servicenow.com), live queries resume instantly.

### Q2: Why does the backend use `verify=False` for ServiceNow REST API requests?
**Answer**: In corporate environments (such as Capgemini and major enterprise client laptops), corporate security proxies intercept outbound SSL traffic using enterprise self-signed certificates, which causes standard Python SSL verification to throw `[SSL: CERTIFICATE_VERIFY_FAILED]`. Disabling strict certificate verification for the PDI connection ensures seamless connectivity behind corporate firewalls.

### Q3: Can I connect multiple ServiceNow instances (e.g., Staging vs. Production)?
**Answer**: Yes. You can change the ServiceNow Instance URL and credentials dynamically at any time in the **Admin Settings** page without restarting the application.

### Q4: How do I export the executive report into Microsoft Excel?
**Answer**: Navigate to **Executive Reports** in the left navigation bar, select your reporting period, and click the green **Export Excel** button in the top right. A `.xlsx` file containing the Executive Scorecard and Application Impact Matrix will download immediately.

---

## 10. ITIL Terms, Formulas & Technical Glossary

- **MTTR (Mean Time to Resolution)**: `(Sum of all (resolved_at - opened_at)) / Total Resolved Incidents`. Measures operational triage and restoration velocity.
- **MTBF (Mean Time Between Failures)**: `Total Operational Hours / Total Failure Count`. Measures infrastructure resilience.
- **SLA Adherence Rate**: `(Incidents resolved within SLA / Total Incidents) * 100%`.
- **sysparm_query**: ServiceNow encoded query syntax for filtering database records via REST Table APIs.
- **Model Context Protocol (MCP)**: An open standard enabling LLMs to securely execute tools and retrieve contextual knowledge from enterprise backends.
- **PDI (Personal Developer Instance)**: Dedicated sandbox environment provided by ServiceNow for developing and testing custom applications.
