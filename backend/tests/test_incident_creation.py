import pytest
import httpx
from app.ai.intent_detector import IntentDetector
from app.mcp.servicenow_mcp import servicenow_mcp_server

from app.main import app

def test_intent_detection_create_incident():
    queries = [
        "ticket a service now incident: Oracle database connection timeout on SAP ORA01 (P1)",
        "i want to ticket a service now incident",
        "create an incident for corporate VPN access portal failure",
        "open a ticket: MailServerUS exchange connection drops",
        "file an incident: SAP sales orders cannot be submitted",
        "raise a ticket: core switch ny8500-nbxs08 port flapping"
    ]
    for q in queries:
        assert IntentDetector.detect_intent(q) == IntentDetector.INTENT_CREATE_INCIDENT, f"Failed for query: {q}"

@pytest.mark.asyncio
async def test_servicenow_mcp_create_incident():
    payload = {
        "short_description": "Pytest Verification Incident",
        "description": "Automated unit test ticket creation.",
        "priority": 3,
        "cmdb_ci": "MailServerUS",
        "category": "software",
        "assignment_group": "Service Desk"
    }
    result = await servicenow_mcp_server.execute_tool("create_incident", payload)
    assert result["success"] is True
    incident = result["incident"]
    assert "number" in incident
    assert "sys_id" in incident
    assert "servicenow_url" in incident
    assert incident["short_description"] == "Pytest Verification Incident"

@pytest.mark.asyncio
async def test_servicenow_mcp_create_incident_category_inference():
    # Database inference
    res_db = await servicenow_mcp_server.execute_tool("create_incident", {
        "short_description": "Oracle database deadlock on checkout",
        "description": "SQL timeout occurred on SAP ORA01"
    })
    assert res_db["category"] == "database"
    assert res_db["category_label"] == "Database"

    # Hardware inference
    res_hw = await servicenow_mcp_server.execute_tool("create_incident", {
        "short_description": "Laptop screen flickering and trackpad dead",
        "description": "Physical display issue with ThinkPad dock"
    })
    assert res_hw["category"] == "hardware"
    assert res_hw["category_label"] == "Hardware"

    # Network inference
    res_net = await servicenow_mcp_server.execute_tool("create_incident", {
        "short_description": "VPN gateway connection dropped",
        "description": "High packet loss on edge router interface"
    })
    assert res_net["category"] == "network"
    assert res_net["category_label"] == "Network"

    # Software inference
    res_sw = await servicenow_mcp_server.execute_tool("create_incident", {
        "short_description": "Customer Portal crashing with 500 error",
        "description": "Checkout service throwing uncaught nullpointer exception"
    })
    assert res_sw["category"] == "software"
    assert res_sw["category_label"] == "Software"

    # Inquiry / Help inference
    res_inq = await servicenow_mcp_server.execute_tool("create_incident", {
        "short_description": "How to request a new monitor?",
        "description": "Where can I submit hardware request form?"
    })
    assert res_inq["category"] == "inquiry"
    assert res_inq["category_label"] == "Inquiry / Help"

@pytest.mark.asyncio
async def test_chat_route_incident_ticketing():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=90.0) as client:
        res = await client.post("/api/chat", json={
            "message": "ticket a service now incident: Email server connection timeout on MailServerUS affecting executive users with priority 2"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["intent"] == IntentDetector.INTENT_CREATE_INCIDENT
        assert "Incident Created in ServiceNow" in data["response_text"]
        assert "INC" in data["response_text"]
        assert data["structured_data"] is not None
        assert data["structured_data"]["created"] is True
