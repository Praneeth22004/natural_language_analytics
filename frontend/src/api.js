const API_BASE = "http://localhost:8000/api";

export async function sendChatMessage(message, sessionId = "default_session") {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId })
  });
  if (!res.ok) throw new Error(`Chat API error: ${res.statusText}`);
  return res.json();
}

export async function fetchDashboardMetrics(timeframe = null) {
  const url = timeframe ? `${API_BASE}/dashboard/metrics?timeframe=${timeframe}` : `${API_BASE}/dashboard/metrics`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Dashboard API error: ${res.statusText}`);
  return res.json();
}

export async function fetchIncidents(params = {}) {
  const query = new URLSearchParams(params).toString();
  const res = await fetch(`${API_BASE}/incidents?${query}`);
  if (!res.ok) throw new Error(`Incidents API error: ${res.statusText}`);
  return res.json();
}

export async function fetchIncidentDetail(identifier) {
  const res = await fetch(`${API_BASE}/incidents/${identifier}`);
  if (!res.ok) throw new Error(`Incident detail error: ${res.statusText}`);
  return res.json();
}

export async function summarizeIncident(identifier) {
  const res = await fetch(`${API_BASE}/incidents/${identifier}/summarize`, {
    method: "POST"
  });
  if (!res.ok) throw new Error(`Summarize API error: ${res.statusText}`);
  return res.json();
}

export async function fetchRecurringClusters() {
  const res = await fetch(`${API_BASE}/analytics/recurring`);
  if (!res.ok) throw new Error(`Recurring API error: ${res.statusText}`);
  return res.json();
}

export async function fetchRcaLeaderboard() {
  const res = await fetch(`${API_BASE}/analytics/root-causes`);
  if (!res.ok) throw new Error(`RCA API error: ${res.statusText}`);
  return res.json();
}

export async function fetchApplicationAnalytics() {
  const res = await fetch(`${API_BASE}/analytics/applications`);
  if (!res.ok) throw new Error(`Application analytics error: ${res.statusText}`);
  return res.json();
}

export async function investigateOutage(service = "AWS") {
  const res = await fetch(`${API_BASE}/outages/investigate?service=${encodeURIComponent(service)}`);
  if (!res.ok) throw new Error(`Outage investigation error: ${res.statusText}`);
  return res.json();
}

export async function generateExecutiveReport(periodTitle) {
  const res = await fetch(`${API_BASE}/reports/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ period_title: periodTitle })
  });
  if (!res.ok) throw new Error(`Report generation error: ${res.statusText}`);
  return res.json();
}

export function getExportReportUrl(format, reportPayload) {
  return `${API_BASE}/reports/export/${format}`;
}

export async function fetchSettings() {
  const res = await fetch(`${API_BASE}/settings`);
  if (!res.ok) throw new Error(`Settings API error: ${res.statusText}`);
  return res.json();
}

export async function updateSettings(settingsData) {
  const res = await fetch(`${API_BASE}/settings/update`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settingsData)
  });
  if (!res.ok) throw new Error(`Settings update error: ${res.statusText}`);
  return res.json();
}

export async function testServiceNowConnection() {
  const res = await fetch(`${API_BASE}/settings/test-connection`, {
    method: "POST"
  });
  if (!res.ok) throw new Error(`Connection test error: ${res.statusText}`);
  return res.json();
}

export async function testLlmConnection(provider = null) {
  const res = await fetch(`${API_BASE}/settings/test-llm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(provider ? { provider } : {})
  });
  if (!res.ok) throw new Error(`LLM test error: ${res.statusText}`);
  return res.json();
}

export async function fetchAuditLogs() {
  const res = await fetch(`${API_BASE}/settings/audit-logs`);
  if (!res.ok) throw new Error(`Audit logs API error: ${res.statusText}`);
  return res.json();
}
