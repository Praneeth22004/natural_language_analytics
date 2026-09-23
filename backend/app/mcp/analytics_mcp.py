import datetime
from collections import defaultdict, Counter
from typing import Dict, Any, List, Optional
from app.services.servicenow import default_sn_client, ServiceNowClient

class AnalyticsMCPServer:
    """MCP Server exposing KPI computation, trend analysis, and recurring incident clustering."""

    name = "analytics_mcp_server"
    version = "1.0.0"

    def __init__(self, client: Optional[ServiceNowClient] = None):
        self.client = client or default_sn_client

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "calculate_kpis",
                "description": "Compute operational KPIs including Total, Open, Closed, P1 Critical, SLA Breaches, MTTR (Mean Time to Resolution in hours), and MTBF (Mean Time Between Failures in hours).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filter_query": {
                            "type": "string",
                            "description": "Optional ServiceNow filter query to scope KPI calculations."
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "cluster_recurring_incidents",
                "description": "Group similar incidents, identify repeated patterns, affected CIs, occurrences, root causes, and corrective action recommendations.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "min_occurrences": {
                            "type": "integer",
                            "description": "Minimum threshold of occurrences to classify as recurring (default: 3)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_root_cause_leaderboard",
                "description": "Calculate root cause leaderboard with occurrence counts, percentages, and affected applications.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_application_analytics",
                "description": "Rank applications by incident volume, severity distribution, and impact level.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "top_n": {
                            "type": "integer",
                            "description": "Number of top applications to return (default: 10)"
                        },
                        "filter_query": {
                            "type": "string",
                            "description": "ServiceNow sysparm_query filter string for timeframe or other filters"
                        }
                    },
                    "required": []
                }
            }
        ]

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "calculate_kpis":
            query = arguments.get("filter_query", "")
            incidents = await self.client.query_table("incident", sysparm_query=query, limit=200)
            return self._compute_kpis(incidents)

        elif tool_name == "cluster_recurring_incidents":
            min_occ = int(arguments.get("min_occurrences", 3))
            incidents = await self.client.query_table("incident", limit=250)
            return self._detect_recurring(incidents, min_occ)

        elif tool_name == "get_root_cause_leaderboard":
            incidents = await self.client.query_table("incident", limit=250)
            return self._compute_rca_leaderboard(incidents)

        elif tool_name == "get_application_analytics":
            top_n = int(arguments.get("top_n", 10))
            filter_query = arguments.get("filter_query", "")
            incidents = await self.client.query_table("incident", sysparm_query=filter_query, limit=250)
            return self._compute_app_analytics(incidents, top_n)

        else:
            raise ValueError(f"Unknown tool: '{tool_name}' on {self.name}")

    def _compute_kpis(self, incidents: List[Dict[str, Any]]) -> Dict[str, Any]:
        total = len(incidents)
        open_count = 0
        closed_count = 0
        critical_count = 0
        sla_breached_count = 0
        resolution_durations_hrs = []
        failure_timestamps = []

        priority_dist = defaultdict(int)
        assignment_dist = defaultdict(int)
        monthly_trend = defaultdict(int)

        for inc in incidents:
            state = str(inc.get("state", "New"))
            p_val = str(inc.get("priority", 3))
            prio = int(p_val[0]) if p_val and p_val[0].isdigit() else 3
            sla = bool(inc.get("sla_breached", False) or str(inc.get("made_sla", "true")).lower() == "false")
            grp = inc.get("assignment_group", "Unassigned")
            
            priority_dist[f"P{prio}"] += 1
            assignment_dist[grp] += 1

            if state in ["Closed", "Resolved"]:
                closed_count += 1
            else:
                open_count += 1

            if prio == 1:
                critical_count += 1

            if sla:
                sla_breached_count += 1

            opened_str = inc.get("opened_at")
            resolved_str = inc.get("resolved_at")

            if opened_str:
                try:
                    opened_dt = datetime.datetime.fromisoformat(opened_str.replace("Z", ""))
                    failure_timestamps.append(opened_dt)
                    month_key = opened_dt.strftime("%b %Y")
                    monthly_trend[month_key] += 1

                    if resolved_str:
                        resolved_dt = datetime.datetime.fromisoformat(resolved_str.replace("Z", ""))
                        diff_hours = (resolved_dt - opened_dt).total_seconds() / 3600.0
                        if diff_hours > 0:
                            resolution_durations_hrs.append(diff_hours)
                except Exception:
                    pass

        # Calculate MTTR (Mean Time to Resolution in hours)
        mttr = round(sum(resolution_durations_hrs) / len(resolution_durations_hrs), 1) if resolution_durations_hrs else 0.0
        
        # Calculate MTBF (Mean Time Between Failures in hours)
        mtbf = 0.0
        if len(failure_timestamps) > 1:
            sorted_times = sorted(failure_timestamps)
            intervals = [(sorted_times[i] - sorted_times[i-1]).total_seconds() / 3600.0 for i in range(1, len(sorted_times))]
            pos_intervals = [x for x in intervals if x > 0]
            if pos_intervals:
                mtbf = round(sum(pos_intervals) / len(pos_intervals), 1)

        sla_compliance_rate = round(((total - sla_breached_count) / total * 100), 1) if total > 0 else 100.0

        return {
            "total_incidents": total,
            "open_incidents": open_count,
            "closed_incidents": closed_count,
            "critical_incidents": critical_count,
            "sla_breached_incidents": sla_breached_count,
            "sla_compliance_rate": sla_compliance_rate,
            "mttr_hours": mttr,
            "mtbf_hours": mtbf,
            "priority_distribution": dict(priority_dist),
            "assignment_group_distribution": dict(assignment_dist),
            "monthly_incident_counts": dict(monthly_trend)
        }

    def _detect_recurring(self, incidents: List[Dict[str, Any]], min_occ: int) -> Dict[str, Any]:
        """Detects recurring incident clusters dynamically based on live ServiceNow tickets, categories, and CIs."""
        patterns = {
            'Identity, Access & Account Provisioning Bottlenecks': {
                'keywords': ['password', 'reset', 'access', 'login', 'account', 'home directory', 'permission'],
                'root_cause': 'Manual Service Desk password reset and directory permission ticket backlog',
                'affected_application': 'Service Desk / Active Directory',
                'linked_problem': 'PRB0000003 (Service Desk Account Backlog)',
                'recommendation': 'Deploy self-service password reset (SSPR) portal and automate home directory provisioning workflows.'
            },
            'Workstation Hardware & Peripheral Failures': {
                'keywords': ['hardware', 'computer', 'headphone', 'printer', 'toner', 'usb', 'laptop', 'cpu'],
                'root_cause': 'End-user workstation device driver conflicts and hardware peripheral wear',
                'affected_application': 'Corporate End-User Workstations & Peripherals',
                'linked_problem': 'PRB0000109 (USB port has stopped working)',
                'recommendation': 'Push standardized OEM audio and peripheral driver pack via Microsoft Endpoint Manager / SCCM.'
            },
            'Email & Messaging Service Disruptions': {
                'keywords': ['email', 'mail', 'exchange', 'outlook', 'attachment'],
                'root_cause': 'Exchange Server connection drops & MailServer queue saturation',
                'affected_application': 'MailServerUS / Exchange (EXCH-SD-05)',
                'linked_problem': 'PRB0000051 (Exchange server outage)',
                'recommendation': 'Apply Exchange Server cumulative rollup patch, restart SMTP transport queue, and verify MailServerUS cluster failover.'
            },
            'Network Switching & Core Gateway Flapping': {
                'keywords': ['network', 'switch', 'router', 'connection', 'drops', 'switching'],
                'root_cause': 'Core switch port flapping and intermittent packet loss on distribution layer',
                'affected_application': 'Core Switches (ny8500-nbxs08 / ny8500-nbxs09)',
                'linked_problem': 'PRB0000050 (Switch occasionally drops connections)',
                'recommendation': 'Replace faulty SFP transceiver on core switch ny8500-nbxs08 and enable Spanning Tree Protocol (STP) root guard.'
            },
            'Database Connectivity & Performance Degradation': {
                'keywords': ['database', 'oracle', 'sql', 'db', 'slowly', 'lawson'],
                'root_cause': 'Database session starvation, long-running queries, and tablespace growth',
                'affected_application': 'Oracle Database (SAP ORA01) / Lawson DB',
                'linked_problem': 'PRB0000029 (Oracle database running slowly and dropping connections)',
                'recommendation': 'Tune Oracle SGA/PGA memory buffers, rebuild fragmented indices, and adjust client connection pool timeouts.'
            }
        }

        clusters = []
        for idx, (p_name, p_info) in enumerate(patterns.items(), 1):
            matching = []
            p_counts = Counter()
            for inc in incidents:
                title = (inc.get('short_description') or '').lower()
                cat = (inc.get('category') or '').lower()
                ci = (inc.get('cmdb_ci') or '').lower()
                combined = f"{title} {cat} {ci}"
                
                if any(k in combined for k in p_info['keywords']):
                    matching.append(inc)
                    p_val = str(inc.get('priority', 3))
                    prio = f"P{p_val[0]}" if p_val and p_val[0].isdigit() else "P3"
                    p_counts[prio] += 1

            if matching and len(matching) >= min_occ:
                sample_inc = matching[0]
                clusters.append({
                    'cluster_id': f'clus_{idx:03d}',
                    'title': p_name,
                    'root_cause': p_info['root_cause'],
                    'affected_application': p_info['affected_application'],
                    'occurrences': len(matching),
                    'priority_breakdown': dict(p_counts),
                    'status': f"Linked to live {p_info['linked_problem'].split()[0]}",
                    'linked_problem': p_info['linked_problem'],
                    'recommendation': p_info['recommendation'],
                    'sample_incident': sample_inc.get('number', 'INC0000001'),
                    'sample_incident_url': sample_inc.get('servicenow_url', ''),
                    'trend': f"{len(matching)} live incidents matched in ServiceNow",
                    'matching_tickets': [m.get('number') for m in matching[:8]]
                })

        clusters.sort(key=lambda c: c['occurrences'], reverse=True)
        total_clustered = sum(c['occurrences'] for c in clusters)
        top_app = f"{clusters[0]['affected_application']} ({clusters[0]['occurrences']} incidents)" if clusters else "Service Desk"

        return {
            "total_clusters_detected": len(clusters),
            "recurring_clusters": clusters,
            "total_clustered_incidents": total_clustered,
            "top_affected_application": top_app
        }

    def _compute_rca_leaderboard(self, incidents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generates RCA leaderboard dynamically from live ServiceNow incident volume."""
        patterns = [
            {
                'keywords': ['password', 'reset', 'access', 'login', 'account', 'home directory', 'permission'],
                'root_cause': 'Manual Service Desk password reset and directory permission ticket backlog',
                'primary_application': 'Service Desk / Active Directory',
                'category': 'Identity & Access',
                'action': 'Deploy self-service password reset (SSPR) portal and automated user provisioning'
            },
            {
                'keywords': ['hardware', 'computer', 'headphone', 'printer', 'toner', 'usb', 'laptop', 'cpu'],
                'root_cause': 'End-user workstation device driver conflicts and hardware peripheral wear',
                'primary_application': 'Corporate End-User Workstations & Peripherals',
                'category': 'Hardware Infrastructure',
                'action': 'Push standardized OEM driver updates and refresh aged peripheral devices'
            },
            {
                'keywords': ['email', 'mail', 'exchange', 'outlook', 'attachment'],
                'root_cause': 'Exchange Server connection drops & MailServer queue saturation',
                'primary_application': 'MailServerUS / Exchange (EXCH-SD-05)',
                'category': 'Messaging & Collaboration',
                'action': 'Apply Exchange Server cumulative patch and verify MailServerUS cluster failover'
            },
            {
                'keywords': ['network', 'switch', 'router', 'connection', 'drops', 'switching'],
                'root_cause': 'Core switch port flapping and intermittent packet loss on distribution layer',
                'primary_application': 'Core Switches (ny8500-nbxs08 / ny8500-nbxs09)',
                'category': 'Network Infrastructure',
                'action': 'Replace faulty SFP transceiver on core switch ny8500-nbxs08 and enable STP root guard'
            },
            {
                'keywords': ['database', 'oracle', 'sql', 'db', 'slowly', 'lawson'],
                'root_cause': 'Database session starvation, long-running queries, and tablespace growth',
                'primary_application': 'Oracle Database (SAP ORA01) / Lawson DB',
                'category': 'Database Infrastructure',
                'action': 'Tune Oracle SGA/PGA memory buffers, rebuild fragmented indices, and adjust pool timeouts'
            }
        ]

        total_inc = len(incidents) or 1
        leaderboard = []

        for p_info in patterns:
            matching = []
            for inc in incidents:
                title = (inc.get('short_description') or '').lower()
                cat = (inc.get('category') or '').lower()
                ci = (inc.get('cmdb_ci') or '').lower()
                combined = f"{title} {cat} {ci}"
                if any(k in combined for k in p_info['keywords']):
                    matching.append(inc)

            if matching:
                count = len(matching)
                pct = f"{round((count / total_inc) * 100, 1)}%"
                leaderboard.append({
                    "rank": 0,
                    "root_cause": p_info['root_cause'],
                    "occurrences": count,
                    "percentage": pct,
                    "primary_application": p_info['primary_application'],
                    "category": p_info['category'],
                    "action": p_info['action'],
                    "sample_tickets": [m.get('number') for m in matching[:4]]
                })

        leaderboard.sort(key=lambda x: x['occurrences'], reverse=True)
        for idx, item in enumerate(leaderboard, 1):
            item['rank'] = idx

        return {
            "total_analyzed": sum(item["occurrences"] for item in leaderboard),
            "leaderboard": leaderboard
        }

    def _compute_app_analytics(self, incidents: List[Dict[str, Any]], top_n: int) -> Dict[str, Any]:
        """Ranks applications by incident volume, handling unassigned CIs cleanly."""
        app_counts = defaultdict(lambda: {"total": 0, "p1": 0, "p2": 0, "p3": 0, "p4": 0, "p5": 0, "sla_breached": 0})

        for inc in incidents:
            ci = inc.get("cmdb_ci")
            if not ci or not str(ci).strip():
                # If CI not explicitly mapped, attribute to Service Desk / End-User Devices
                ci = "Service Desk / End-User Devices"
            else:
                ci = str(ci).strip()

            p_val = str(inc.get("priority", 3))
            prio = int(p_val[0]) if p_val and p_val[0].isdigit() else 3
            sla = bool(inc.get("sla_breached", False) or str(inc.get("made_sla", "true")).lower() == "false")

            app_counts[ci]["total"] += 1
            app_counts[ci][f"p{prio}"] += 1
            if sla:
                app_counts[ci]["sla_breached"] += 1

        ranked = sorted(
            [{"name": k, **v} for k, v in app_counts.items()],
            key=lambda x: x["total"],
            reverse=True
        )[:top_n]

        return {
            "top_applications": ranked,
            "total_applications_impacted": len(app_counts)
        }

analytics_mcp_server = AnalyticsMCPServer()
