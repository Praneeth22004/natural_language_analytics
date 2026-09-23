from fastapi import APIRouter
from typing import Dict, Any
from app.mcp.analytics_mcp import analytics_mcp_server

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/recurring")
async def get_recurring_clusters(min_occurrences: int = 3) -> Dict[str, Any]:
    """Identify recurring incidents, clusters, affected applications, and recommendations."""
    return await analytics_mcp_server.execute_tool("cluster_recurring_incidents", {"min_occurrences": min_occurrences})

@router.get("/root-causes")
async def get_root_cause_leaderboard() -> Dict[str, Any]:
    """Retrieve root cause analysis leaderboard."""
    return await analytics_mcp_server.execute_tool("get_root_cause_leaderboard", {})

@router.get("/applications")
async def get_application_analytics(top_n: int = 10) -> Dict[str, Any]:
    """Retrieve application incident rankings and impact distribution."""
    return await analytics_mcp_server.execute_tool("get_application_analytics", {"top_n": top_n})
