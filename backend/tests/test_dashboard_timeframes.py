import pytest
from app.services.servicenow import build_timeframe_query, default_sn_client
from app.mcp.analytics_mcp import analytics_mcp_server

def test_build_timeframe_query():
    assert "beginningOfYesterday" in build_timeframe_query("yesterday")
    assert "beginningOfLastWeek" in build_timeframe_query("last_week")
    assert "beginningOfLastMonth" in build_timeframe_query("last_month")
    assert "daysAgoStart(30)" in build_timeframe_query("past_30_days")
    assert "daysAgoStart(180)" in build_timeframe_query("past_6_months")
    assert "2026-03-01" in build_timeframe_query("march_2026")
    assert build_timeframe_query("all") == ""

@pytest.mark.asyncio
async def test_kpi_computation_zero_incidents():
    kpis = analytics_mcp_server._compute_kpis([])
    assert kpis["total_incidents"] == 0
    assert kpis["open_incidents"] == 0
    assert kpis["closed_incidents"] == 0
    assert kpis["critical_incidents"] == 0
    assert kpis["sla_breached_incidents"] == 0
    assert kpis["mttr_hours"] == 0.0
    assert kpis["mtbf_hours"] == 0.0
    assert kpis["sla_compliance_rate"] == 100.0

@pytest.mark.asyncio
async def test_application_analytics_with_filter():
    # Empty query should return empty apps
    result_empty = analytics_mcp_server._compute_app_analytics([], top_n=5)
    assert result_empty["top_applications"] == []
    assert result_empty["total_applications_impacted"] == 0

    # Live query with future timeframe filter yields 0 incidents in dev204434
    future_q = build_timeframe_query("January 2030")
    app_stats_future = await analytics_mcp_server.execute_tool("get_application_analytics", {
        "top_n": 5,
        "filter_query": future_q
    })
    assert len(app_stats_future["top_applications"]) == 0

    # Live query with yesterday filter returns whatever is in ServiceNow
    yesterday_q = build_timeframe_query("yesterday")
    app_stats_y = await analytics_mcp_server.execute_tool("get_application_analytics", {
        "top_n": 5,
        "filter_query": yesterday_q
    })
    assert isinstance(app_stats_y["top_applications"], list)
