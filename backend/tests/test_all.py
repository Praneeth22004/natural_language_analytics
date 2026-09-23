import pytest
from app.ai.intent_detector import IntentDetector
from app.ai.query_translator import QueryTranslator
from app.services.servicenow import default_sn_client
from app.mcp.servicenow_mcp import servicenow_mcp_server
from app.mcp.analytics_mcp import analytics_mcp_server
from app.mcp.reporting_mcp import reporting_mcp_server
from app.mcp.mcp_protocol import mcp_registry

def test_intent_detection():
    # Outage
    assert IntentDetector.detect_intent("Provide details of the outage reported last month") == IntentDetector.INTENT_OUTAGE_INVESTIGATION
    # Recurring
    assert IntentDetector.detect_intent("Identify recurring incidents and root causes") == IntentDetector.INTENT_RECURRING_ANALYSIS
    # RCA
    assert IntentDetector.detect_intent("What are the most common root causes?") == IntentDetector.INTENT_RCA_LOOKUP
    # Report
    assert IntentDetector.detect_intent("Create incident report for August 2026") == IntentDetector.INTENT_REPORT_GENERATION
    # Apps
    assert IntentDetector.detect_intent("Which applications generated the most incidents this quarter?") == IntentDetector.INTENT_APPLICATION_ANALYTICS
    # KPIs
    assert IntentDetector.detect_intent("How many incidents are currently open?") == IntentDetector.INTENT_METRICS_KPI
    # Queries
    assert IntentDetector.detect_intent("What incidents were reported yesterday?") == IntentDetector.INTENT_QUERY_INCIDENTS
    assert IntentDetector.detect_intent("Show all P1 incidents from last week") == IntentDetector.INTENT_QUERY_INCIDENTS

def test_query_translation_yesterday():
    res = QueryTranslator.translate("What incidents were reported yesterday?")
    assert "YESTERDAY" in res["sysparm_query"].upper()
    assert res["applied_filters"]["timeframe"] == "yesterday"

def test_query_translation_p1_last_week():
    res = QueryTranslator.translate("Show all P1 incidents from last week")
    assert "priority=1" in res["sysparm_query"]
    assert res["applied_filters"]["timeframe"] == "last_week"

def test_query_translation_aws():
    res = QueryTranslator.translate("Show incidents related to AWS")
    query = res["sysparm_query"].lower()
    assert "short_descriptionlikeaws" in query or "cmdb_cilikeaws" in query

def test_query_translation_network_team():
    res = QueryTranslator.translate("List all incidents assigned to Network team")
    assert "assignment_groupLIKENetwork" in res["sysparm_query"]
    assert "Network" in res["applied_filters"]["assignment_group"]

def test_query_translation_p5_planning():
    res = QueryTranslator.translate("Show all P5 planning tickets")
    assert "priority=5" in res["sysparm_query"]
    assert res["applied_filters"]["priority"] == 5

@pytest.mark.asyncio
async def test_servicenow_mcp_query():
    result = await servicenow_mcp_server.execute_tool("query_incidents", {"sysparm_query": "priority=1", "limit": 10})
    assert result["count"] > 0
    for inc in result["incidents"]:
        assert str(inc["priority"]).startswith("1")

@pytest.mark.asyncio
async def test_analytics_kpi_computation():
    kpis = await analytics_mcp_server.execute_tool("calculate_kpis", {})
    assert kpis["total_incidents"] > 0
    assert kpis["open_incidents"] >= 0
    assert kpis["closed_incidents"] > 0
    assert kpis["mttr_hours"] > 0
    assert kpis["mtbf_hours"] > 0
    assert "P1" in kpis["priority_distribution"]

@pytest.mark.asyncio
async def test_analytics_recurring_clusters():
    res = await analytics_mcp_server.execute_tool("cluster_recurring_incidents", {"min_occurrences": 1})
    assert res["total_clusters_detected"] >= 1
    clusters = res["recurring_clusters"]
    assert len(clusters) > 0
    assert clusters[0]["occurrences"] > 0

@pytest.mark.asyncio
async def test_analytics_rca_leaderboard():
    res = await analytics_mcp_server.execute_tool("get_root_cause_leaderboard", {})
    assert len(res["leaderboard"]) >= 1
    assert "root_cause" in res["leaderboard"][0]
    assert res["leaderboard"][0]["occurrences"] > 0

@pytest.mark.asyncio
async def test_reporting_mcp_report_and_export():
    report = await reporting_mcp_server.build_report("August 2026")
    assert report["period"] == "August 2026"
    assert "kpis" in report
    assert len(report["strategic_recommendations"]) > 0

    # Test PDF generation
    pdf_buf = reporting_mcp_server.export_document("pdf", report)
    assert len(pdf_buf.getvalue()) > 100

    # Test DOCX generation
    docx_buf = reporting_mcp_server.export_document("docx", report)
    assert len(docx_buf.getvalue()) > 100

    # Test XLSX generation
    xlsx_buf = reporting_mcp_server.export_document("xlsx", report)
    assert len(xlsx_buf.getvalue()) > 100

def test_mcp_registry():
    tools = mcp_registry.list_all_tools()
    tool_names = [t["name"] for t in tools]
    assert "query_incidents" in tool_names
    assert "calculate_kpis" in tool_names
    assert "cluster_recurring_incidents" in tool_names
    assert "generate_executive_report" in tool_names
    assert "export_report_document" in tool_names

from unittest.mock import patch, AsyncMock, MagicMock
from app.ai.llm_client import llm_client
from app.core.config import settings

@pytest.mark.asyncio
async def test_nvidia_provider_missing_key():
    with patch.object(settings, "LLM_PROVIDER", "nvidia"):
        with patch.object(settings, "NVIDIA_API_KEY", None):
            res = await llm_client.generate_chat_completion([{"role": "user", "content": "hello"}])
            assert res is None

@pytest.mark.asyncio
async def test_nvidia_provider_success():
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "id": "chatcmpl-test",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "NVIDIA NIM response text"},
                "finish_reason": "stop"
            }
        ]
    }

    mock_client = AsyncMock()
    mock_client.post.return_value = fake_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch.object(settings, "LLM_PROVIDER", "nvidia"):
        with patch.object(settings, "NVIDIA_API_KEY", "nvapi-mock-test-key"):
            with patch.object(settings, "NVIDIA_MODEL", "meta/llama-3.3-70b-instruct"):
                with patch("httpx.AsyncClient", return_value=mock_client):
                    res = await llm_client.generate_chat_completion([{"role": "user", "content": "ping"}])
                    assert res == "NVIDIA NIM response text"
                    mock_client.post.assert_called_once()
                    call_args = mock_client.post.call_args
                    assert "meta/llama-3.3-70b-instruct" in str(call_args)
                    assert "Bearer nvapi-mock-test-key" in str(call_args)

@pytest.mark.asyncio
async def test_nvidia_test_provider_diagnostic():
    # Test when API key is missing
    with patch.object(settings, "NVIDIA_API_KEY", None):
        res = await llm_client.test_provider("nvidia")
        assert res["success"] is False
        assert "API Key is missing" in res["message"]

    # Test when API responds successfully
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "choices": [{"message": {"content": "OK"}}]
    }
    mock_client = AsyncMock()
    mock_client.post.return_value = fake_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch.object(settings, "NVIDIA_API_KEY", "nvapi-mock-key"):
        with patch("httpx.AsyncClient", return_value=mock_client):
            res = await llm_client.test_provider("nvidia")
            assert res["success"] is True
            assert res["model"] == settings.NVIDIA_MODEL
            assert res["sample_output"] == "OK"

