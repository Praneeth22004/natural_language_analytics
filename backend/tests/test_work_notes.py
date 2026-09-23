import pytest
from app.mcp.servicenow_mcp import servicenow_mcp_server
from app.ai.intent_detector import IntentDetector

def test_intent_detection_work_notes():
    assert IntentDetector.detect_intent("Show work notes for INC0000060") == IntentDetector.INTENT_WORKNOTES
    assert IntentDetector.detect_intent("Add work note to INC0000060: Tested backup power failover") == IntentDetector.INTENT_WORKNOTES
    assert IntentDetector.detect_intent("View previous work notes of INC0010101") == IntentDetector.INTENT_WORKNOTES

@pytest.mark.asyncio
async def test_get_incident_work_notes_mcp():
    res = await servicenow_mcp_server.execute_tool("get_incident_work_notes", {"identifier": "INC0000060"})
    assert res["found"] is True
    assert "work_notes" in res
    assert isinstance(res["work_notes"], list)

@pytest.mark.asyncio
async def test_add_work_note_mcp():
    res = await servicenow_mcp_server.execute_tool("add_work_note", {
        "identifier": "INC0000060",
        "work_notes": "Pytest automated verification work note."
    })
    assert res["success"] is True
    assert res["incident_number"] == "INC0000060"
    assert "updated_notes" in res
    assert len(res["updated_notes"]) > 0
