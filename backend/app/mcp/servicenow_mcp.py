from typing import Dict, Any, List, Optional
from app.services.servicenow import default_sn_client, ServiceNowClient

class ServiceNowMCPServer:
    """MCP Server exposing ServiceNow data retrieval tools."""

    name = "servicenow_mcp_server"
    version = "1.0.0"

    def __init__(self, client: Optional[ServiceNowClient] = None):
        self.client = client or default_sn_client

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Returns JSON schema definitions for tools exposed by this server."""
        return [
            {
                "name": "query_incidents",
                "description": "Retrieve incident records from ServiceNow using sysparm_query syntax.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sysparm_query": {
                            "type": "string",
                            "description": "ServiceNow encoded query string, e.g. 'priority=1^opened_at>=...'"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of records to return (default: 50)"
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Pagination offset"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_incident_detail",
                "description": "Fetch detailed information for a single incident by number or sys_id.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "identifier": {
                            "type": "string",
                            "description": "Incident number (e.g. INC0010101) or sys_id"
                        }
                    },
                    "required": ["identifier"]
                }
            },
            {
                "name": "query_problems",
                "description": "Retrieve problem records linked to recurring root causes and workarounds.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sysparm_query": {
                            "type": "string",
                            "description": "Encoded query for problems"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "query_cmdb_ci",
                "description": "Retrieve Configuration Items (CIs) such as applications, servers, databases.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sysparm_query": {
                            "type": "string",
                            "description": "Encoded query for CMDB CIs"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "create_incident",
                "description": "Create / ticket a new incident in ServiceNow with short description, description, priority, category, and affected CI.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "short_description": {
                            "type": "string",
                            "description": "Concise summary of the incident (required)"
                        },
                        "description": {
                            "type": "string",
                            "description": "Detailed explanation of the issue or error symptoms"
                        },
                        "priority": {
                            "type": "integer",
                            "description": "Priority (1=Critical, 2=High, 3=Moderate, 4=Low, 5=Planning)"
                        },
                        "urgency": {
                            "type": "integer",
                            "description": "Urgency (1=High, 2=Medium, 3=Low)"
                        },
                        "impact": {
                            "type": "integer",
                            "description": "Impact (1=High, 2=Medium, 3=Low)"
                        },
                        "cmdb_ci": {
                            "type": "string",
                            "description": "Configuration item or affected service (e.g. MailServerUS, Oracle, SAP)"
                        },
                        "category": {
                            "type": "string",
                            "description": "Incident category (software, hardware, network, database, inquiry)"
                        },
                        "assignment_group": {
                            "type": "string",
                            "description": "Assignment group (Service Desk, Network, Database, Software)"
                        }
                    },
                    "required": ["short_description"]
                }
            }
        ]

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches and executes the requested tool."""
        if tool_name == "create_incident":
            short_desc = arguments.get("short_description", "").strip()
            if not short_desc:
                raise ValueError("short_description is required to create an incident")

            prio = arguments.get("priority", 3)
            urgency = arguments.get("urgency", 2)
            impact = arguments.get("impact", 2)
            if prio == 1:
                urgency = 1
                impact = 1
            elif prio == 2:
                urgency = 2
                impact = 1

            payload = {
                "short_description": short_desc,
                "description": arguments.get("description", short_desc),
                "priority": str(prio),
                "urgency": str(urgency),
                "impact": str(impact),
                "category": arguments.get("category", "inquiry"),
                "cmdb_ci": arguments.get("cmdb_ci", "Service Desk / End-User Devices"),
                "assignment_group": arguments.get("assignment_group", "Service Desk"),
                "comments": "Created via AI Incident Assistant"
            }
            record = await self.client.create_record("incident", payload)
            return {
                "success": True,
                "incident": record,
                "message": f"Successfully created incident {record.get('number')} in ServiceNow."
            }

        elif tool_name == "query_incidents":
            query = arguments.get("sysparm_query", "")
            limit = int(arguments.get("limit", 50))
            offset = int(arguments.get("offset", 0))
            records = await self.client.query_table("incident", sysparm_query=query, limit=limit, offset=offset)
            return {
                "count": len(records),
                "query": query,
                "incidents": records
            }

        elif tool_name == "get_incident_detail":
            identifier = arguments.get("identifier", "").strip()
            query = f"number={identifier}^ORsys_id={identifier}"
            records = await self.client.query_table("incident", sysparm_query=query, limit=1)
            if records:
                return {"found": True, "incident": records[0]}
            return {"found": False, "message": f"Incident '{identifier}' not found."}

        elif tool_name == "query_problems":
            query = arguments.get("sysparm_query", "")
            records = await self.client.query_table("problem", sysparm_query=query)
            return {"count": len(records), "problems": records}

        elif tool_name == "query_cmdb_ci":
            query = arguments.get("sysparm_query", "")
            records = await self.client.query_table("cmdb_ci", sysparm_query=query)
            return {"count": len(records), "configuration_items": records}

        else:
            raise ValueError(f"Unknown tool: '{tool_name}' on {self.name}")

servicenow_mcp_server = ServiceNowMCPServer()
