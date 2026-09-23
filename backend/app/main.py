from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import init_db
from app.api.routes import (
    chat,
    dashboard,
    incidents,
    analytics,
    outages,
    reports,
    mcp_router,
    settings as settings_router
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database schema
    await init_db()
    yield
    # Teardown: close resources if needed

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Enterprise Natural Language Incident Analytics & Reporting Platform powered by ServiceNow and MCP",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for development & testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(chat.router)
app.include_router(dashboard.router)
app.include_router(incidents.router)
app.include_router(analytics.router)
app.include_router(outages.router)
app.include_router(reports.router)
app.include_router(mcp_router.router)
app.include_router(settings_router.router)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "mode": "Simulation Fallback" if settings.SERVICENOW_USE_MOCK_FALLBACK else "Live ServiceNow PDI",
        "llm_provider": settings.LLM_PROVIDER
    }

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API Gateway",
        "docs_url": "/docs",
        "health_check": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.APP_PORT, reload=settings.DEBUG)
