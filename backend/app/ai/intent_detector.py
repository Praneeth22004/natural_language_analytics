import re
from typing import Dict, Any

class IntentDetector:
    """Classifies user natural language input into operational analytics intents or direct LLM conversation."""

    # Operational ServiceNow & Analytics Intents
    INTENT_QUERY_INCIDENTS = "QUERY_INCIDENTS"
    INTENT_RECURRING_ANALYSIS = "RECURRING_ANALYSIS"
    INTENT_OUTAGE_INVESTIGATION = "OUTAGE_INVESTIGATION"
    INTENT_RCA_LOOKUP = "RCA_LOOKUP"
    INTENT_METRICS_KPI = "METRICS_KPI"
    INTENT_REPORT_GENERATION = "REPORT_GENERATION"
    INTENT_APPLICATION_ANALYTICS = "APPLICATION_ANALYTICS"
    INTENT_INCIDENT_SUMMARIZATION = "INCIDENT_SUMMARIZATION"
    INTENT_CREATE_INCIDENT = "CREATE_INCIDENT"
    INTENT_PROBLEM_LOOKUP = "PROBLEM_LOOKUP"
    INTENT_CMDB_LOOKUP = "CMDB_LOOKUP"
    INTENT_SRE_ADVISORY = "SRE_ADVISORY"
    INTENT_GENERAL = "GENERAL_HELP"
    INTENT_DIRECT_LLM = "DIRECT_LLM"

    @classmethod
    def detect_intent(cls, user_text: str, context: Dict[str, Any] = None) -> str:
        text = user_text.lower().strip()
        context = context or {}

        # 1. Greetings & System Capabilities
        if text in ["hi", "hello", "hey", "help", "help me", "who are you", "what can you do", "commands"]:
            return cls.INTENT_GENERAL
        if any(w in text for w in ["what can you do", "how do you work", "show capabilities", "help with commands"]):
            return cls.INTENT_GENERAL

        # 1.5 Incident Creation / Ticketing in ServiceNow
        if ("report" not in text and "brief" not in text) and (
            any(w in text for w in [
                "ticket a service now incident", "ticket a servicenow incident", "ticket an incident", "ticket incident",
                "create incident", "create an incident", "create a ticket", "create ticket",
                "open an incident", "open incident", "open a ticket", "open ticket",
                "file an incident", "file incident", "file a ticket", "file ticket",
                "log an incident", "log incident", "log a ticket", "log ticket",
                "raise an incident", "raise incident", "raise a ticket", "raise ticket",
                "new incident", "new ticket"
            ]) or (
                ("ticket" in text or "create" in text or "open" in text or "file" in text or "raise" in text or "log" in text)
                and ("incident" in text or "ticket" in text)
                and any(act in text for act in ["servicenow", "new", "priority", "for", "issue", "down", "error", "server", "database"])
                and not any(q in text for q in ["show", "list", "query", "summarize", "find", "search", "get", "how many", "count"])
            )
        ):
            return cls.INTENT_CREATE_INCIDENT

        # 2. Single Incident Summarization (e.g. INC0010101, "summarize INC...", "post-mortem for INC...")
        if re.search(r"inc\d{5,8}", text, re.IGNORECASE) or ("summarize" in text and ("incident" in text or "ticket" in text)):
            return cls.INTENT_INCIDENT_SUMMARIZATION

        # 3. Problem Records & Permanent Workarounds Lookup
        if re.search(r"prb\d{5,8}", text, re.IGNORECASE) or any(w in text for w in [
            "problem ticket", "problem record", "problem tickets", "problem records", 
            "open problems", "known error", "known errors", "workaround", "workarounds", 
            "show problems", "list problems"
        ]):
            return cls.INTENT_PROBLEM_LOOKUP

        # 4. CMDB / Configuration Item Lookup
        if any(w in text for w in [
            "cmdb", "configuration item", "configuration items", "cmdb_ci", 
            "list servers in cmdb", "cmdb assets", "inventory in cmdb", "items in cmdb"
        ]):
            return cls.INTENT_CMDB_LOOKUP

        # 5. Outage Investigation
        if any(w in text for w in ["outage", "major incident", "downtime", "sev-1 event", "service interruption"]):
            return cls.INTENT_OUTAGE_INVESTIGATION

        # 6. Recurring Incidents Analysis
        if any(w in text for w in ["recurring", "repeated incident", "repeat incident", "incident cluster", "frequency pattern", "repeat issues"]):
            return cls.INTENT_RECURRING_ANALYSIS

        # 7. Root Cause Analysis (RCA)
        if any(w in text for w in ["root cause", "rca", "common causes", "why did it fail", "cause leaderboard", "systemic causes"]):
            return cls.INTENT_RCA_LOOKUP

        # 8. Report Generation
        if any(w in text for w in ["create incident report", "generate report", "executive report", "monthly report", "export report"]):
            return cls.INTENT_REPORT_GENERATION

        # 9. Application Analytics
        if any(w in text for w in [
            "which application", "which applications", 
            "top applications", "top affected applications", "affected applications", 
            "application had the most", "applications had the most",
            "app rankings", "application ranking"
        ]):
            return cls.INTENT_APPLICATION_ANALYTICS

        # 10. Operational Metrics & KPIs
        if any(w in text for w in [
            "how many incidents", "incident count", "total incidents", "open incidents", "closed incidents",
            "what is our mttr", "what is our mtbf", "our mttr", "our sla", "sla compliance", "sla breach rate", 
            "operational kpis", "kpi metrics", "show kpis"
        ]):
            return cls.INTENT_METRICS_KPI

        # 11. SRE Advisory / Troubleshooting / ITIL Best Practice
        if any(w in text for w in [
            "how can we improve mttr", "how to improve mttr", "how to reduce outages", "how to prevent outages",
            "advice on mttr", "recommendation for outages", "sre advisory", "incident action plan", 
            "remediation roadmap", "how can we reduce mttr", "how can we improve and reduce outages"
        ]):
            return cls.INTENT_SRE_ADVISORY

        # 12. ServiceNow Incident Search Query
        # A query is ONLY an incident search if it explicitly references incidents, tickets, priorities, or ServiceNow filters:
        has_incident_noun = any(w in text for w in [
            "incident", "incidents", "ticket", "tickets", "p1", "p2", "p3", "p4", "p5", 
            "critical incident", "critical incidents", "sev-1", "severity 1", "assigned to"
        ])
        
        action_verbs = ["show", "find", "list", "get", "display", "check", "search"]
        has_action_verb = any(w in text.split() for w in action_verbs)
        
        ci_or_team_terms = [
            "mailserverus", "databaseserver", "sap", "oracle", "peoplesoft", "exchange", 
            "switch", "router", "service desk", "network team", "hardware team"
        ]
        has_ci_or_team = any(ci in text for ci in ci_or_team_terms)

        if has_incident_noun or (has_action_verb and has_ci_or_team):
            return cls.INTENT_QUERY_INCIDENTS

        # 13. Multi-turn Follow-ups in Conversation Context
        last_intent = context.get("last_intent")
        if last_intent in [cls.INTENT_QUERY_INCIDENTS, cls.INTENT_APPLICATION_ANALYTICS]:
            if "why" in text or "cause" in text:
                return cls.INTENT_RCA_LOOKUP
            if "which" in text or "most" in text or "application" in text:
                return cls.INTENT_APPLICATION_ANALYTICS

        # 14. Default to Direct LLM for General Knowledge, Conversational, or Technical Questions
        return cls.INTENT_DIRECT_LLM
