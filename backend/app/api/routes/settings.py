from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.config import settings
from app.services.servicenow import default_sn_client
from app.ai.llm_client import llm_client
from app.db.session import get_db
from app.db.models import AuditLog

router = APIRouter(prefix="/api/settings", tags=["Settings"])

class SettingsUpdateRequest(BaseModel):
    instance_url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    use_mock_fallback: Optional[bool] = None
    llm_provider: Optional[str] = None
    openai_api_key: Optional[str] = None
    nvidia_api_key: Optional[str] = None
    nvidia_model: Optional[str] = None
    nvidia_base_url: Optional[str] = None

class TestLlmRequest(BaseModel):
    provider: Optional[str] = None

@router.get("")
async def get_current_settings():
    """Returns current environment and connection state (with password masked)."""
    return {
        "instance_url": default_sn_client.instance_url,
        "username": default_sn_client.username,
        "has_password": bool(default_sn_client.password),
        "use_mock_fallback": default_sn_client.use_mock_fallback,
        "llm_provider": settings.LLM_PROVIDER,
        "has_openai_key": bool(settings.OPENAI_API_KEY),
        "has_nvidia_key": bool(settings.NVIDIA_API_KEY),
        "nvidia_model": settings.NVIDIA_MODEL,
        "nvidia_base_url": settings.NVIDIA_BASE_URL,
        "mode": "Enterprise Simulation (Mock Mode)" if default_sn_client.use_mock_fallback else "Live ServiceNow PDI"
    }

@router.post("/update")
async def update_settings(req: SettingsUpdateRequest):
    """Updates runtime configuration settings."""
    if req.instance_url is not None:
        default_sn_client.instance_url = req.instance_url.rstrip("/")
        settings.SERVICENOW_INSTANCE_URL = req.instance_url.rstrip("/")
    if req.username is not None:
        default_sn_client.username = req.username
        settings.SERVICENOW_USERNAME = req.username
    if req.password is not None and req.password != "":
        default_sn_client.password = req.password
        settings.SERVICENOW_PASSWORD = req.password
    if req.use_mock_fallback is not None:
        default_sn_client.use_mock_fallback = req.use_mock_fallback
        settings.SERVICENOW_USE_MOCK_FALLBACK = req.use_mock_fallback
    if req.llm_provider is not None:
        settings.LLM_PROVIDER = req.llm_provider
    if req.openai_api_key is not None and req.openai_api_key != "":
        settings.OPENAI_API_KEY = req.openai_api_key
    if req.nvidia_api_key is not None and req.nvidia_api_key != "":
        settings.NVIDIA_API_KEY = req.nvidia_api_key
    if req.nvidia_model is not None and req.nvidia_model != "":
        settings.NVIDIA_MODEL = req.nvidia_model
    if req.nvidia_base_url is not None and req.nvidia_base_url != "":
        settings.NVIDIA_BASE_URL = req.nvidia_base_url.rstrip("/")

    return {
        "success": True,
        "message": "Configuration updated successfully",
        "current_settings": {
            "instance_url": default_sn_client.instance_url,
            "username": default_sn_client.username,
            "use_mock_fallback": default_sn_client.use_mock_fallback,
            "llm_provider": settings.LLM_PROVIDER,
            "has_nvidia_key": bool(settings.NVIDIA_API_KEY),
            "nvidia_model": settings.NVIDIA_MODEL,
            "nvidia_base_url": settings.NVIDIA_BASE_URL
        }
    }

@router.post("/test-connection")
async def test_servicenow_connection():
    """Executes live handshake and table query to test ServiceNow credentials."""
    return await default_sn_client.test_connection()

@router.post("/test-llm")
async def test_llm_connection(req: Optional[TestLlmRequest] = None):
    """Executes ping test against configured or specified LLM provider."""
    provider_name = req.provider if req else None
    return await llm_client.test_provider(provider_name)

@router.get("/audit-logs")
async def get_audit_logs(db: AsyncSession = Depends(get_db)):
    """Retrieves recent audit entries."""
    try:
        query = select(AuditLog).order_by(desc(AuditLog.timestamp)).limit(20)
        result = await db.execute(query)
        logs = result.scalars().all()
        return [
            {
                "id": log.id,
                "user_id": log.user_id,
                "natural_query": log.natural_query,
                "generated_query": log.generated_query,
                "status": log.status,
                "execution_time_ms": log.execution_time_ms,
                "records_returned": log.records_returned,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None
            }
            for log in logs
        ]
    except Exception:
        return []
