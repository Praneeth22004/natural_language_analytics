import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.ai.memory_manager import SessionMemory, MemoryManager, memory_manager
from app.ai.intent_detector import IntentDetector

def test_session_memory_entity_and_interaction_tracking():
    mem = SessionMemory("test_session_abc")
    assert mem.history == []
    assert mem.last_incident_number is None

    # Interaction 1: Mentions incident INC0000060
    mem.add_interaction(
        user_text="Show work notes for INC0000060",
        assistant_text="Found 2 journal entries for INC0000060",
        intent=IntentDetector.INTENT_WORKNOTES,
        filters={"priority": 1}
    )

    assert len(mem.history) == 2
    assert mem.last_incident_number == "INC0000060"
    assert mem.last_intent == IntentDetector.INTENT_WORKNOTES
    assert mem.active_filters.get("priority") == 1

    ctx = mem.get_context()
    assert ctx["turn_count"] == 1
    assert ctx["last_incident_number"] == "INC0000060"
    assert ctx["history_length"] == 2

def test_session_memory_llm_chat_history_format():
    mem = SessionMemory("test_session_history")
    for i in range(5):
        mem.add_interaction(
            user_text=f"Question {i}",
            assistant_text=f"Answer {i}",
            intent="DIRECT_LLM"
        )

    assert len(mem.history) == 10
    recent_history = mem.get_chat_history(max_turns=2)
    # 2 turns * 2 (user + assistant) = 4 items
    assert len(recent_history) == 4
    assert recent_history[0]["role"] == "user"
    assert recent_history[0]["content"] == "Question 3"
    assert recent_history[-1]["role"] == "assistant"
    assert recent_history[-1]["content"] == "Answer 4"

def test_session_memory_reset():
    mem = SessionMemory("test_session_reset")
    mem.add_interaction(
        user_text="Investigate outage for MailServerUS",
        assistant_text="Outage identified for INC0000001",
        intent=IntentDetector.INTENT_OUTAGE_INVESTIGATION,
        ci="MailServerUS"
    )

    assert len(mem.history) == 2
    assert mem.last_incident_number == "INC0000001"
    assert mem.last_ci == "MailServerUS"

    # Reset
    mem.reset()
    assert mem.history == []
    assert mem.last_incident_number is None
    assert mem.last_ci is None
    assert mem.active_filters == {}
    assert mem.get_context()["turn_count"] == 0

def test_memory_manager_session_isolation():
    manager = MemoryManager()
    session_1 = manager.get_or_create_session("sess_alpha")
    session_2 = manager.get_or_create_session("sess_beta")

    session_1.add_interaction("User query for INC0000060", "Response for INC0000060", "INTENT_WORKNOTES")
    session_2.add_interaction("User query for INC0000085", "Response for INC0000085", "INTENT_WORKNOTES")

    assert session_1.last_incident_number == "INC0000060"
    assert session_2.last_incident_number == "INC0000085"

    manager.reset_session("sess_alpha")
    assert session_1.last_incident_number is None
    assert session_2.last_incident_number == "INC0000085"

def test_intent_detection_session_reset():
    assert IntentDetector.detect_intent("end chat") == IntentDetector.INTENT_RESET_SESSION
    assert IntentDetector.detect_intent("restart conversation") == IntentDetector.INTENT_RESET_SESSION
    assert IntentDetector.detect_intent("reset session") == IntentDetector.INTENT_RESET_SESSION
    assert IntentDetector.detect_intent("start over") == IntentDetector.INTENT_RESET_SESSION
    assert IntentDetector.detect_intent("clear the chat") == IntentDetector.INTENT_RESET_SESSION

@pytest.mark.asyncio
async def test_api_reset_session_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Seed interaction into memory
        mem = memory_manager.get_or_create_session("api_test_sess")
        mem.add_interaction("User message", "Assistant reply", "DIRECT_LLM")
        assert len(mem.history) == 2

        # 2. Call reset endpoint
        res = await client.post("/api/chat/session/reset", json={"session_id": "api_test_sess"})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["session_id"] == "api_test_sess"

        # 3. Verify memory is reset
        mem_after = memory_manager.get_or_create_session("api_test_sess")
        assert mem_after.history == []
        assert mem_after.last_incident_number is None

@pytest.mark.asyncio
async def test_conversational_chat_intent_reset():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Prepopulate session
        sess_id = "test_nl_reset"
        mem = memory_manager.get_or_create_session(sess_id)
        mem.add_interaction("First turn", "First reply", "DIRECT_LLM")

        # Send 'end chat' natural language message
        res = await client.post("/api/chat", json={"message": "end chat", "session_id": sess_id})
        assert res.status_code == 200
        data = res.json()
        assert data["intent"] == IntentDetector.INTENT_RESET_SESSION
        assert "Reset" in data["response_text"] or "Restarted" in data["response_text"] or "Cleared" in data["response_text"]
        assert data["structured_data"]["session_reset"] is True

        # Verify session memory in manager was wiped
        mem_after = memory_manager.get_or_create_session(sess_id)
        assert mem_after.history == []
