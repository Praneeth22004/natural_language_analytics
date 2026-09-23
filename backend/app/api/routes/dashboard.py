from fastapi import APIRouter
from typing import Dict, Any, Optional
from app.mcp.analytics_mcp import analytics_mcp_server
from app.services.servicenow import build_timeframe_query

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/metrics")
async def get_dashboard_metrics(timeframe: Optional[str] = None) -> Dict[str, Any]:
    """Retrieves operational KPIs, MTTR, MTBF, SLA breach rate, priority distribution, and trends."""
    query = build_timeframe_query(timeframe)

    kpis = await analytics_mcp_server.execute_tool("calculate_kpis", {"filter_query": query})
    app_stats = await analytics_mcp_server.execute_tool("get_application_analytics", {"top_n": 5, "filter_query": query})

    return {
        "kpis": kpis,
        "top_applications": app_stats.get("top_applications", []),
        "timeframe": timeframe or "all",
        "query_used": query
    }
