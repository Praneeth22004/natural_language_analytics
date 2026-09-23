import datetime
from datetime import timedelta
import random

# Base timestamp anchor (realistic dynamic dates relative to current execution)
NOW = datetime.datetime.utcnow()
TODAY = NOW.replace(hour=10, minute=0, second=0, microsecond=0)
YESTERDAY = TODAY - timedelta(days=1)
LAST_WEEK = TODAY - timedelta(days=7)
LAST_MONTH = TODAY - timedelta(days=30)

APPLICATIONS = [
    {"name": "AWS US-East-1 Cluster", "ci_class": "cmdb_ci_cloud_service", "tier": "Tier 1"},
    {"name": "Customer Portal", "ci_class": "cmdb_ci_web_app", "tier": "Tier 1"},
    {"name": "Employee Hub", "ci_class": "cmdb_ci_web_app", "tier": "Tier 2"},
    {"name": "Oracle Exadata DB", "ci_class": "cmdb_ci_database", "tier": "Tier 1"},
    {"name": "Payment Gateway V2", "ci_class": "cmdb_ci_service", "tier": "Tier 1"},
    {"name": "SAP Core ERP", "ci_class": "cmdb_ci_appl", "tier": "Tier 1"},
    {"name": "Okta SSO Gateway", "ci_class": "cmdb_ci_identity", "tier": "Tier 1"},
    {"name": "Corporate VPN NY", "ci_class": "cmdb_ci_network", "tier": "Tier 2"},
    {"name": "Salesforce CRM Sync", "ci_class": "cmdb_ci_cloud_app", "tier": "Tier 2"},
]

ASSIGNMENT_GROUPS = [
    "Cloud Operations",
    "Database Administration",
    "Network Engineering",
    "Security Operations",
    "Service Desk",
    "Application Support",
]

USERS = [
    {"sys_id": "usr_001", "name": "Sarah Jenkins", "email": "s.jenkins@enterprise.com", "role": "Incident Commander"},
    {"sys_id": "usr_002", "name": "David Chen", "email": "d.chen@enterprise.com", "role": "DBA Lead"},
    {"sys_id": "usr_003", "name": "Maria Rodriguez", "email": "m.rodriguez@enterprise.com", "role": "Cloud Architect"},
    {"sys_id": "usr_004", "name": "Alex Murphy", "email": "a.murphy@enterprise.com", "role": "Network Specialist"},
    {"sys_id": "usr_005", "name": "Elena Rostova", "email": "e.rostova@enterprise.com", "role": "DevOps Engineer"},
]

PROBLEMS = [
    {
        "sys_id": "prb_001",
        "number": "PRB0001042",
        "short_description": "PostgreSQL & Oracle connection pool exhaustion under sudden traffic spikes",
        "state": "Work in Progress",
        "priority": "1 - Critical",
        "root_cause": "Database Connection Timeout due to unclosed connection pool leaks in microservice backend",
        "workaround": "Temporarily restart pool workers and increase max_connections from 200 to 500",
        "cmdb_ci": "Oracle Exadata DB",
        "assigned_to": "David Chen",
    },
    {
        "sys_id": "prb_002",
        "number": "PRB0001089",
        "short_description": "AWS US-East-1 VPC peering packet drop causing intermittent 504 gateway timeouts",
        "state": "Known Error",
        "priority": "1 - Critical",
        "root_cause": "AWS DirectConnect route table flap combined with MTU mismatch",
        "workaround": "Reroute ingress traffic via secondary AWS US-West-2 cluster",
        "cmdb_ci": "AWS US-East-1 Cluster",
        "assigned_to": "Maria Rodriguez",
    },
    {
        "sys_id": "prb_003",
        "number": "PRB0001150",
        "short_description": "Corporate VPN gateway SSL certificate expiration handshake failures",
        "state": "Closed",
        "priority": "2 - High",
        "root_cause": "Automated Let's Encrypt renewal script permission error on bastion host",
        "workaround": "Manual certbot deployment with 4096-bit RSA certificate",
        "cmdb_ci": "Corporate VPN NY",
        "assigned_to": "Alex Murphy",
    }
]

CHANGES = [
    {
        "sys_id": "chg_001",
        "number": "CHG0008912",
        "short_description": "Emergency patch: Expand Oracle HikariCP database connection pool size",
        "type": "Emergency",
        "state": "Implemented",
        "risk": "Moderate",
        "cmdb_ci": "Oracle Exadata DB",
        "requested_by": "David Chen",
        "start_date": (TODAY - timedelta(days=2)).isoformat(),
        "end_date": (TODAY - timedelta(days=2, hours=-2)).isoformat(),
    },
    {
        "sys_id": "chg_002",
        "number": "CHG0008890",
        "short_description": "AWS VPC routing update and MTU alignment for US-East-1",
        "type": "Normal",
        "state": "Review",
        "risk": "High",
        "cmdb_ci": "AWS US-East-1 Cluster",
        "requested_by": "Maria Rodriguez",
        "start_date": (TODAY - timedelta(days=5)).isoformat(),
        "end_date": (TODAY - timedelta(days=5, hours=-4)).isoformat(),
    }
]

def generate_enterprise_incidents():
    incidents = []
    
    # Specific Curated Incidents to fulfill all test questions reliably:
    # 1. Critical incidents yesterday
    # 2. Critical incidents last week
    # 3. Recurring cluster 1: Database connection timeout (25 occurrences)
    # 4. Outage incident: AWS US-East-1 Outage last month
    # 5. Outage incident: Customer Portal 500 error
    # 6. Network team incidents
    # 7. Open vs Closed incidents
    
    # --- YESTERDAY INCIDENTS (15 total: 2 Critical, 5 High, 6 Medium, 2 Low) ---
    yesterday_configs = [
        # Critical (2)
        {"p": 1, "state": "In Progress", "ci": "AWS US-East-1 Cluster", "grp": "Cloud Operations", "desc": "AWS US-East-1 EC2 node pool degraded causing 504 errors on API Gateway", "sla": True},
        {"p": 1, "state": "Resolved", "ci": "Customer Portal", "grp": "Application Support", "desc": "Customer Portal checkout workflow throwing HTTP 500 Internal Server Error", "sla": False},
        # High (5)
        {"p": 2, "state": "In Progress", "ci": "Oracle Exadata DB", "grp": "Database Administration", "desc": "Database Connection Timeout: HikariCP pool maxed at 200 connections", "sla": False},
        {"p": 2, "state": "In Progress", "ci": "Employee Hub", "grp": "Application Support", "desc": "Employee Hub SSO login loop preventing staff authentication", "sla": True},
        {"p": 2, "state": "Resolved", "ci": "Payment Gateway V2", "grp": "Application Support", "desc": "Stripe webhook retry queue backing up over 10,000 requests", "sla": False},
        {"p": 2, "state": "Resolved", "ci": "Salesforce CRM Sync", "grp": "Application Support", "desc": "Salesforce OAuth token refresh failure halting order push", "sla": False},
        {"p": 2, "state": "New", "ci": "Corporate VPN NY", "grp": "Network Engineering", "desc": "Network team alert: High packet loss on primary edge router interface", "sla": False},
        # Medium (6)
        {"p": 3, "state": "In Progress", "ci": "SAP Core ERP", "grp": "Application Support", "desc": "SAP monthly ledger reconciliation job running 4x slower than baseline", "sla": False},
        {"p": 3, "state": "Resolved", "ci": "Customer Portal", "grp": "Application Support", "desc": "Product search cache invalidation delay on catalog items", "sla": False},
        {"p": 3, "state": "Resolved", "ci": "Oracle Exadata DB", "grp": "Database Administration", "desc": "Database temp tablespace utilization reached 88%", "sla": False},
        {"p": 3, "state": "Closed", "ci": "Corporate VPN NY", "grp": "Network Engineering", "desc": "VPN split tunneling policy mismatch on Windows 11 clients", "sla": False},
        {"p": 3, "state": "Closed", "ci": "Employee Hub", "grp": "Service Desk", "desc": "Expense report receipt attachment upload failing for PDF format", "sla": False},
        {"p": 3, "state": "Closed", "ci": "Salesforce CRM Sync", "grp": "Service Desk", "desc": "Sales lead assignment rules not triggering for APAC region", "sla": False},
        # Low (2)
        {"p": 4, "state": "Resolved", "ci": "Employee Hub", "grp": "Service Desk", "desc": "Intranet footer link typography alignment issue", "sla": False},
        {"p": 4, "state": "Closed", "ci": "General IT", "grp": "Service Desk", "desc": "Floor 4 printer spooler queue cleared", "sla": False},
        # Planning (2)
        {"p": 5, "state": "New", "ci": "Cloud Operations", "grp": "Cloud Operations", "desc": "Planning capacity upgrade for Kubernetes cluster nodes", "sla": False},
        {"p": 5, "state": "In Progress", "ci": "Oracle Exadata DB", "grp": "Database Administration", "desc": "Quarterly index optimization maintenance planning", "sla": False},
    ]

    for idx, conf in enumerate(yesterday_configs, start=1):
        num = f"INC00{10100 + idx}"
        opened = YESTERDAY + timedelta(hours=idx % 12, minutes=idx * 3)
        resolved = opened + timedelta(hours=2, minutes=30) if conf["state"] in ["Resolved", "Closed"] else None
        closed = resolved + timedelta(hours=4) if conf["state"] == "Closed" else None
        
        incidents.append({
            "sys_id": f"sys_inc_{10100 + idx}",
            "number": num,
            "short_description": conf["desc"],
            "description": f"Incident report logged for {conf['ci']}. Automated telemetry reported anomaly. Action taken by {conf['grp']}.",
            "priority": conf["p"],
            "state": conf["state"],
            "category": "Software" if "DB" in conf["ci"] or "Portal" in conf["ci"] else ("Cloud" if "AWS" in conf["ci"] else "Network"),
            "assignment_group": conf["grp"],
            "assigned_to": random.choice(USERS)["name"],
            "cmdb_ci": conf["ci"],
            "opened_at": opened.isoformat(),
            "resolved_at": resolved.isoformat() if resolved else None,
            "closed_at": closed.isoformat() if closed else None,
            "sla_breached": conf["sla"],
            "close_notes": "Issue investigated, patched and verified with monitoring telemetry." if resolved else None,
            "problem_id": "PRB0001042" if "Database Connection Timeout" in conf["desc"] else ("PRB0001089" if "AWS" in conf["ci"] else None)
        })

    # --- RECURRING CLUSTER: Database Connection Timeout (25 occurrences on Customer Portal / Oracle DB) ---
    for i in range(1, 26):
        num = f"INC00{10200 + i}"
        days_ago = (i % 20) + 2
        opened = TODAY - timedelta(days=days_ago, hours=i % 8)
        resolved = opened + timedelta(hours=1, minutes=45)
        incidents.append({
            "sys_id": f"sys_inc_rc_{i}",
            "number": num,
            "short_description": f"Database Connection Timeout: Unable to acquire connection from pool for Customer Portal [occurrence #{i}]",
            "description": "Customer Portal frontend reported java.sql.SQLTransientConnectionException: HikariPool-1 - Connection is not available, request timed out after 30005ms.",
            "priority": 1 if i <= 4 else 2,
            "state": "Closed",
            "category": "Database",
            "assignment_group": "Database Administration",
            "assigned_to": "David Chen",
            "cmdb_ci": "Customer Portal",
            "opened_at": opened.isoformat(),
            "resolved_at": resolved.isoformat(),
            "closed_at": (resolved + timedelta(hours=2)).isoformat(),
            "sla_breached": i % 4 == 0,
            "close_notes": "Root Cause: Database Connection Timeout due to unclosed hibernate sessions in checkout microservice. Workaround: Cleared leaked sockets and recycled HikariCP connection pool.",
            "problem_id": "PRB0001042"
        })

    # --- MAJOR OUTAGE INCIDENT: AWS US-East-1 Outage reported last month ---
    aws_outage_time = LAST_MONTH + timedelta(days=5, hours=14, minutes=15)
    incidents.append({
        "sys_id": "sys_inc_aws_major",
        "number": "INC0009999",
        "short_description": "AWS US-East-1 Regional Outage: Network border gateway drop causing severe latency and 504 errors across Tier 1 services",
        "description": "AWS US-East-1 experienced major route table flapping. Customer Portal, Payment Gateway V2, and SAP integration endpoints unreachable. Impacted 42,000 active sessions.",
        "priority": 1,
        "state": "Closed",
        "category": "Cloud Infrastructure",
        "assignment_group": "Cloud Operations",
        "assigned_to": "Sarah Jenkins",
        "cmdb_ci": "AWS US-East-1 Cluster",
        "opened_at": aws_outage_time.isoformat(),
        "resolved_at": (aws_outage_time + timedelta(hours=3, minutes=42)).isoformat(),
        "closed_at": (aws_outage_time + timedelta(hours=8)).isoformat(),
        "sla_breached": True,
        "close_notes": "AWS DirectConnect failover completed. Rerouted ingress traffic to US-West-2 cluster. MTU parameters reconfigured. Post-mortem RCA completed under PRB0001089.",
        "problem_id": "PRB0001089"
    })

    # --- ADDITIONAL ENTERPRISE INCIDENTS (Past 45 days background incidents) ---
    topics = [
        ("Corporate VPN NY", "Network Engineering", "VPN Gateway session limit exceeded for remote employees", "Network", 2),
        ("Okta SSO Gateway", "Security Operations", "SAML token signing certificate mismatch during federation", "Security", 1),
        ("Payment Gateway V2", "Application Support", "Payment processing latency exceeding 8000ms SLA target", "Software", 2),
        ("SAP Core ERP", "Application Support", "SAP batch posting deadlock on inventory ledger", "Software", 3),
        ("AWS US-East-1 Cluster", "Cloud Operations", "Kubernetes ingress controller CPU throttling on worker nodes", "Cloud", 2),
        ("Oracle Exadata DB", "Database Administration", "Tablespace autoextend failed due to underlying SAN mount volume full", "Database", 2),
        ("Employee Hub", "Service Desk", "Workday integration sync stalled on user provisioning", "Software", 3),
        ("Customer Portal", "Application Support", "Redis cluster replica sync failure causing cache misses", "Software", 2),
    ]

    for idx in range(1, 45):
        ci, grp, desc, cat, prio = topics[idx % len(topics)]
        days_back = (idx % 35) + 1
        opened = TODAY - timedelta(days=days_back, hours=(idx * 3) % 24)
        is_open = (idx % 5 == 0)
        state = "In Progress" if is_open else ("Resolved" if idx % 2 == 0 else "Closed")
        resolved = (opened + timedelta(hours=(idx % 6) + 1)) if not is_open else None
        
        incidents.append({
            "sys_id": f"sys_inc_bg_{idx}",
            "number": f"INC00{10300 + idx}",
            "short_description": desc,
            "description": f"Automated monitoring alert triggered on {ci}. Incident assigned to {grp} for remediation.",
            "priority": prio,
            "state": state,
            "category": cat,
            "assignment_group": grp,
            "assigned_to": random.choice(USERS)["name"],
            "cmdb_ci": ci,
            "opened_at": opened.isoformat(),
            "resolved_at": resolved.isoformat() if resolved else None,
            "closed_at": (resolved + timedelta(hours=2)).isoformat() if resolved and state == "Closed" else None,
            "sla_breached": (idx % 6 == 0),
            "close_notes": f"Remediated issue on {ci}. Diagnostics confirmed normal telemetry.",
            "problem_id": None
        })

    return incidents

# Cached instances
ENTERPRISE_INCIDENTS = generate_enterprise_incidents()
