from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from app.mcp.servicenow_mcp import servicenow_mcp_server
from app.ai.insights_engine import InsightsEngine

from app.services.servicenow import build_timeframe_query

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])

@router.get("")
async def list_incidents(
    priority: Optional[int] = None,
    state: Optional[str] = None,
    ci: Optional[str] = None,
    search: Optional[str] = None,
    timeframe: Optional[str] = None,
    sysparm_query: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """List incidents with optional filters, including timeframe support."""
    clauses = []
    if timeframe:
        tf_query = build_timeframe_query(timeframe)
        if tf_query:
            clauses.append(tf_query)
    if priority:
        clauses.append(f"priority={priority}")
    if state:
        clauses.append(f"state={state}")
    if ci:
        clauses.append(f"cmdb_ciLIKE{ci}")
    if search:
        clauses.append(f"short_descriptionLIKE{search}^ORdescriptionLIKE{search}")
    if sysparm_query:
        clauses.append(sysparm_query)

    query = "^".join(clauses)
    result = await servicenow_mcp_server.execute_tool("query_incidents", {
        "sysparm_query": query,
        "limit": limit,
        "offset": offset
    })
    return result

@router.get("/{identifier}")
async def get_incident(identifier: str) -> Dict[str, Any]:
    """Retrieve details of a single incident."""
    result = await servicenow_mcp_server.execute_tool("get_incident_detail", {"identifier": identifier})
    if not result.get("found"):
        raise HTTPException(status_code=404, detail=f"Incident {identifier} not found")
    return result

@router.post("/{identifier}/summarize")
async def summarize_incident(identifier: str) -> Dict[str, Any]:
    """Generates AI Post-Mortem & Summarization for an incident."""
    detail_result = await servicenow_mcp_server.execute_tool("get_incident_detail", {"identifier": identifier})
    if not detail_result.get("found"):
        raise HTTPException(status_code=404, detail=f"Incident {identifier} not found")

    incident = detail_result["incident"]
    post_mortem = await InsightsEngine.summarize_single_incident(incident)
    return {
        "incident": incident,
        "post_mortem": post_mortem
    }
