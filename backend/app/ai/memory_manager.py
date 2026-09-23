from typing import Dict, Any, List, Optional
import datetime

class SessionMemory:
    """Maintains conversational context, message trajectory, and active query filters for a session."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.history: List[Dict[str, Any]] = []
        self.last_intent: Optional[str] = None
        self.active_filters: Dict[str, Any] = {}
        self.last_query_result: List[Dict[str, Any]] = []
        self.created_at = datetime.datetime.utcnow()
        self.updated_at = datetime.datetime.utcnow()

    def add_interaction(self, user_text: str, assistant_text: str, intent: str, filters: Dict[str, Any], results: List[Dict[str, Any]]):
        self.history.append({
            "role": "user",
            "content": user_text,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })
        self.history.append({
            "role": "assistant",
            "content": assistant_text,
            "intent": intent,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })
        self.last_intent = intent
        # Merge filters
        self.active_filters.update(filters)
        if results:
            self.last_query_result = results
        self.updated_at = datetime.datetime.utcnow()

    def get_context(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "last_intent": self.last_intent,
            "previous_filters": self.active_filters,
            "history_length": len(self.history),
            "cached_record_count": len(self.last_query_result)
        }

class MemoryManager:
    """In-memory session manager with Redis fallback capability."""

    def __init__(self):
        self.sessions: Dict[str, SessionMemory] = {}

    def get_or_create_session(self, session_id: str) -> SessionMemory:
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionMemory(session_id)
        return self.sessions[session_id]

    def clear_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]

memory_manager = MemoryManager()
