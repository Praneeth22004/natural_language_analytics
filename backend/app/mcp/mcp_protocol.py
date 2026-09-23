from typing import Dict, Any, List
from app.mcp.servicenow_mcp import servicenow_mcp_server
from app.mcp.analytics_mcp import analytics_mcp_server
from app.mcp.reporting_mcp import reporting_mcp_server

class MCPRegistry:
    """Unified Model Context Protocol (MCP) tool registry and JSON-RPC router."""

    def __init__(self):
        self.servers = {
            "servicenow": servicenow_mcp_server,
            "analytics": analytics_mcp_server,
            "reporting": reporting_mcp_server
        }

    def list_all_tools(self) -> List[Dict[str, Any]]:
        """Returns metadata and parameter schemas for all registered MCP tools."""
        all_tools = []
        for server_name, server in self.servers.items():
            for tool in server.get_tool_definitions():
                tool_copy = dict(tool)
                tool_copy["server"] = server_name
                all_tools.append(tool_copy)
        return all_tools

    async def dispatch_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches tool execution to the appropriate MCP server."""
        for server in self.servers.values():
            tools = [t["name"] for t in server.get_tool_definitions()]
            if tool_name in tools:
                return await server.execute_tool(tool_name, arguments)

        raise ValueError(f"Tool '{tool_name}' not found across registered MCP servers.")

    async def handle_json_rpc(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handles standard JSON-RPC 2.0 MCP requests."""
        req_id = request.get("id", 1)
        method = request.get("method", "")
        params = request.get("params", {})

        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": self.list_all_tools()}
            }
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            try:
                result = await self.dispatch_tool_call(tool_name, arguments)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"content": [{"type": "text", "text": str(result)}], "raw": result}
                }
            except Exception as ex:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32603, "message": str(ex)}
                }
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method '{method}' not found."}
            }

mcp_registry = MCPRegistry()
