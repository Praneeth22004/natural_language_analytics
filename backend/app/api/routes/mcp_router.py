from fastapi import APIRouter
from typing import Dict, Any
from app.mcp.mcp_protocol import mcp_registry

router = APIRouter(prefix="/api/mcp", tags=["MCP"])

@router.get("/tools")
async def list_mcp_tools():
    """Lists all available Model Context Protocol tools."""
    return {"tools": mcp_registry.list_all_tools()}

@router.post("/rpc")
async def handle_mcp_rpc(request: Dict[str, Any]):
    """Standard JSON-RPC 2.0 handler for MCP clients."""
    return await mcp_registry.handle_json_rpc(request)
