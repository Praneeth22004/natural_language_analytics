# Natural Language Incident Analytics & Reporting - API Documentation

## Overview
This platform provides an enterprise REST API and Model Context Protocol (MCP) interface that translates natural language queries into ServiceNow encoded queries (`sysparm_query`), executes data retrieval against ServiceNow Table APIs, computes operational KPIs (MTTR, MTBF, SLA breach rate), clusters recurring incidents, and generates exportable executive reports.

---

## Interactive API Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **MCP RPC Tool Endpoint**: `POST http://localhost:8000/api/mcp/rpc`

---

## Core REST Endpoints

### 1. Conversational Chat
`POST /api/chat`
Process natural language queries with context preservation and ServiceNow query generation.

**Request Body:**
```json
{
  "message": "What incidents were reported yesterday?",
  "session_id": "default_session"
}
```

**Response:**
```json
{
  "session_id": "default_session",
  "intent": "QUERY_INCIDENTS",
  "sysparm_query": "opened_atONYesterday@javascript:gs.beginningOfYesterday()@javascript:gs.endOfYesterday()^ORDERBYDESCopened_at",
  "response_text": "**Summary:**\n15 incidents were reported yesterday.\n\n**Breakdown:**\n- Critical: 2\n- High: 5\n- Medium: 6\n- Low: 2\n\n**Top Applications:**\n- AWS US-East-1 Cluster\n- Customer Portal\n- Oracle Exadata DB\n\n**Key Insights:**\nCritical (P1) incidents accounted for 13% of reported volume.",
  "structured_data": {
    "summary": "15 incidents were reported yesterday.",
    "breakdown": { "Critical": 2, "High": 5, "Medium": 6, "Low": 2 },
    "top_applications": ["AWS US-East-1 Cluster", "Customer Portal", "Oracle Exadata DB"],
    "key_insights": "Critical (P1) incidents accounted for 13% of reported volume.",
    "raw_count": 15
  },
  "execution_time_ms": 18,
  "suggestions": [
    "Show all P1 incidents from last week",
    "Which application had the most?",
    "Identify recurring incidents and root causes"
  ]
}
```

---

### 2. Operational Metrics & KPIs
`GET /api/dashboard/metrics?timeframe=yesterday`
Returns calculated MTTR, MTBF, SLA breach rate, priority and team workload distributions.

**Response:**
```json
{
  "kpis": {
    "total_incidents": 85,
    "open_incidents": 14,
    "closed_incidents": 71,
    "critical_incidents": 5,
    "sla_breached_incidents": 6,
    "sla_compliance_rate": 92.9,
    "mttr_hours": 3.2,
    "mtbf_hours": 24.5,
    "priority_distribution": { "P1": 5, "P2": 32, "P3": 38, "P4": 10, "P5": 4 },
    "assignment_group_distribution": { "Database Administration": 27, "Cloud Operations": 15, "Network Engineering": 12 }
  }
}
```

---

### 3. Recurring Incident Detection
`GET /api/analytics/recurring?min_occurrences=3`
Clusters repeat incidents, extracts root causes, affected CIs, and recommendations.

**Response:**
```json
{
  "total_clusters_detected": 4,
  "recurring_clusters": [
    {
      "cluster_id": "clus_001",
      "title": "Database Connection Pool Exhaustion",
      "root_cause": "Database Connection Timeout due to leaked client sessions and undersized HikariCP pool",
      "affected_application": "Customer Portal",
      "occurrences": 25,
      "recommendation": "Database connection pool tuning: expand maxPoolSize to 500 and activate connection leak detection."
    }
  ]
}
```

---

### 4. Root Cause Leaderboard
`GET /api/analytics/root-causes`
Returns common root causes ranked by occurrence and affected applications.

---

### 5. Outage Investigation
`GET /api/outages/investigate?service=AWS`
Synthesizes chronological outage timeline, primary CI, impacted services, and resolution details.

---

### 6. Executive Report Generation & Export
- `POST /api/reports/generate` -> Generates report JSON payload.
- `POST /api/reports/export/{format}` -> Downloads binary document (`format`: `pdf`, `docx`, `xlsx`).

---

## Model Context Protocol (MCP) Specifications

### Registered Tools
1. `servicenow_mcp_server`:
   - `query_incidents(sysparm_query, limit, offset)`
   - `get_incident_detail(identifier)`
   - `create_incident(short_description, description, priority, category, cmdb_ci, assignment_group)`
   - `query_problems(sysparm_query)`
   - `query_cmdb_ci(sysparm_query)`

2. `analytics_mcp_server`:
   - `calculate_kpis(filter_query)`
   - `cluster_recurring_incidents(min_occurrences)`
   - `get_root_cause_leaderboard()`
   - `get_application_analytics(top_n)`

3. `reporting_mcp_server`:
   - `generate_executive_report(period_title, filter_query)`
   - `export_report_document(format, report_payload)`

### Standard JSON-RPC Invocation
Endpoint: `POST /api/mcp/rpc`
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "calculate_kpis",
    "arguments": { "filter_query": "priority=1" }
  }
}
```

---

## Sample ServiceNow Encoded Queries (sysparm_query)

| Natural Language Question | Generated `sysparm_query` |
| :--- | :--- |
| *"What incidents were reported yesterday?"* | `opened_atONYesterday@javascript:gs.beginningOfYesterday()@javascript:gs.endOfYesterday()^ORDERBYDESCopened_at` |
| *"Show all P1 incidents from last week"* | `priority=1^opened_atONLast week@javascript:gs.beginningOfLastWeek()@javascript:gs.endOfLastWeek()^ORDERBYDESCopened_at` |
| *"How many incidents are currently open?"* | `stateIN1,2,3^active=true^ORDERBYDESCopened_at` |
| *"List all incidents assigned to Network team"* | `assignment_groupLIKENetwork Engineering^ORDERBYDESCopened_at` |
| *"Show incidents related to AWS"* | `short_descriptionLIKEAWS^ORdescriptionLIKEAWS^ORcmdb_ciLIKEAWS^ORDERBYDESCopened_at` |
| *"Provide details of the outage reported last month"* | `priority=1^short_descriptionLIKEoutage^opened_atONLast month@javascript:gs.beginningOfLastMonth()@javascript:gs.endOfLastMonth()^ORDERBYDESCopened_at` |
