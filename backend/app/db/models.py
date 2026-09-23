import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from app.db.session import Base

class ConversationSession(Base):
    __tablename__ = "conversation_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(128), unique=True, index=True, nullable=False)
    title = Column(String(256), default="New Incident Conversation")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(128), index=True, nullable=False)
    role = Column(String(32), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    intent = Column(String(64), nullable=True)
    generated_query = Column(Text, nullable=True)
    structured_response = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class IncidentCache(Base):
    __tablename__ = "incident_cache"

    id = Column(Integer, primary_key=True, index=True)
    sys_id = Column(String(64), unique=True, index=True, nullable=False)
    number = Column(String(32), index=True, nullable=False)
    short_description = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Integer, index=True, default=3)  # 1=Critical, 2=High, 3=Moderate, 4=Low, 5=Planning
    state = Column(String(32), index=True, default="New")  # New, In Progress, On Hold, Resolved, Closed
    category = Column(String(64), default="Software")
    assignment_group = Column(String(128), index=True, default="Service Desk")
    assigned_to = Column(String(128), nullable=True)
    cmdb_ci = Column(String(128), index=True, default="General IT")
    opened_at = Column(DateTime, index=True, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    sla_breached = Column(Boolean, default=False)
    close_notes = Column(Text, nullable=True)
    raw_data = Column(JSON, nullable=True)
    synced_at = Column(DateTime, default=datetime.datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(64), default="analyst@enterprise.com")
    natural_query = Column(Text, nullable=False)
    generated_query = Column(Text, nullable=True)
    status = Column(String(32), default="SUCCESS")
    execution_time_ms = Column(Integer, default=0)
    records_returned = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class SavedReport(Base):
    __tablename__ = "saved_reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(256), nullable=False)
    period = Column(String(64), nullable=False)
    summary_text = Column(Text, nullable=True)
    report_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
