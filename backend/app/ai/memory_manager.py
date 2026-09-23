from typing import Dict, Any, List, Optional
import datetime
import re

class SessionMemory:
    """Maintains conversational context, message trajectory, active filters, and entity tracking for a chat session."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.history: List[Dict[str, Any]] = []
        self.last_intent: Optional[str] = None
        self.active_filters: Dict[str, Any] = {}
        self.last_incident_number: Optional[str] = None
        self.last_ci: Optional[str] = None
        self.last_query_result: List[Dict[str, Any]] = []
        self.created_at = datetime.datetime.utcnow()
        self.updated_at = datetime.datetime.utcnow()

    def add_interaction(
        self,
        user_text: str,
        assistant_text: str,
        intent: str,
        filters: Optional[Dict[str, Any]] = None,
        results: Optional[List[Dict[str, Any]]] = None,
        incident_number: Optional[str] = None,
        ci: Optional[str] = None
    ):
        """Records a user/assistant turn exchange and extracts tracked entities."""
        now_iso = datetime.datetime.utcnow().isoformat()
        
        # Auto-detect incident numbers if not explicitly provided
        extracted_inc = incident_number
        if not extracted_inc:
            user_inc_match = re.search(r"\b(inc\d{5,8})\b", user_text, re.IGNORECASE)
            if user_inc_match:
                extracted_inc = user_inc_match.group(1).upper()
            else:
                asst_inc_match = re.search(r"\b(inc\d{5,8})\b", assistant_text, re.IGNORECASE)
                if asst_inc_match:
                    extracted_inc = asst_inc_match.group(1).upper()

        if extracted_inc:
            self.last_incident_number = extracted_inc

        # Track configuration item if supplied
        if ci:
            self.last_ci = ci

        # Record turns in history
        self.history.append({
            "role": "user",
            "content": user_text,
            "timestamp": now_iso
        })
        self.history.append({
            "role": "assistant",
            "content": assistant_text,
            "intent": intent,
            "incident_number": extracted_inc,
            "timestamp": now_iso
        })

        self.last_intent = intent
        if filters:
            self.active_filters.update(filters)
        if results is not None:
            self.last_query_result = results

        self.updated_at = datetime.datetime.utcnow()

    def get_chat_history(self, max_turns: int = 8) -> List[Dict[str, str]]:
        """Returns the recent turns formatted for OpenAI/NVIDIA LLM chat prompts."""
        # Each exchange is 2 entries (user + assistant)
        slice_count = max_turns * 2
        recent_entries = self.history[-slice_count:] if slice_count < len(self.history) else self.history
        return [
            {"role": entry["role"], "content": entry["content"]}
            for entry in recent_entries
        ]

    def reset(self):
        """Clears all conversation turns and cached contextual entities."""
        self.history = []
        self.last_intent = None
        self.active_filters = {}
        self.last_incident_number = None
        self.last_ci = None
        self.last_query_result = []
        self.updated_at = datetime.datetime.utcnow()

    def get_context(self) -> Dict[str, Any]:
        """Provides context summary for intent detection and prompt synthesis."""
        return {
            "session_id": self.session_id,
            "last_intent": self.last_intent,
            "previous_filters": self.active_filters,
            "last_incident_number": self.last_incident_number,
            "last_ci": self.last_ci,
            "history_length": len(self.history),
            "turn_count": len(self.history) // 2,
            "cached_record_count": len(self.last_query_result),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class MemoryManager:
    """Manages active chat sessions with memory persistence and lifecycle controls."""

    def __init__(self):
        self.sessions: Dict[str, SessionMemory] = {}

    def get_or_create_session(self, session_id: str) -> SessionMemory:
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionMemory(session_id)
        return self.sessions[session_id]

    def reset_session(self, session_id: str) -> SessionMemory:
        """Resets the specified session's conversational memory."""
        session = self.get_or_create_session(session_id)
        session.reset()
        return session

    def clear_session(self, session_id: str) -> bool:
        """Completely purges the session from memory."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        if session_id in self.sessions:
            return self.sessions[session_id].get_context()
        return None


memory_manager = MemoryManager()
