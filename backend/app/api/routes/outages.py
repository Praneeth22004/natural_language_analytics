from fastapi import APIRouter
from typing import Dict, Any
from app.services.servicenow import default_sn_client
from app.ai.insights_engine import InsightsEngine

router = APIRouter(prefix="/api/outages", tags=["Outages"])

@router.get("/investigate")
async def investigate_outage(service: str = "Email") -> Dict[str, Any]:
    """Investigate service outages and generate timeline from live ServiceNow P1 incidents."""
    clean_srv = service.split()[0].replace("(", "").replace(")", "").strip()
    query = f"short_descriptionLIKE{clean_srv}^ORcmdb_ciLIKE{clean_srv}^priority=1"
    incidents = await default_sn_client.query_table("incident", sysparm_query=query, limit=5)
    
    if not incidents:
        # Fetch top real P1 critical incident from ServiceNow
        incidents = await default_sn_client.query_table("incident", sysparm_query="priority=1", limit=5)

    return await InsightsEngine.synthesize_outage_investigation(incidents, service)
