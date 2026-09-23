import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    APP_NAME: str = "Natural Language Incident Analytics & Reporting"
    APP_PORT: int = 8000
    DEBUG: bool = True
    SECRET_KEY: str = "enterprise-secret-key-change-in-production"
    
    # ServiceNow Settings
    SERVICENOW_INSTANCE_URL: str = Field(default="https://dev00000.service-now.com")
    SERVICENOW_USERNAME: str = Field(default="admin")
    SERVICENOW_PASSWORD: str = Field(default="password")
    SERVICENOW_USE_MOCK_FALLBACK: bool = Field(default=True)
    SERVICENOW_TIMEOUT: int = 15
    
    # LLM Settings
    LLM_PROVIDER: str = Field(default="semantic_engine")  # "semantic_engine", "openai", "azure", "anthropic", "gemini", "nvidia"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT_NAME: Optional[str] = "gpt-4o"
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    NVIDIA_API_KEY: Optional[str] = None
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_MODEL: str = "meta/llama-3.2-11b-vision-instruct"
    
    # Database and Caching
    DATABASE_URL: str = "sqlite+aiosqlite:///./incident_analytics.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security & CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
