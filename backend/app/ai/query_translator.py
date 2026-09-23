import re
import datetime
from typing import Dict, Any, Tuple, List

class QueryTranslator:
    """Translates natural language questions into ServiceNow encoded queries (sysparm_query)."""

    # Real ServiceNow assignment groups
    TEAM_MAPPINGS = {
        "network": "Network",
        "network team": "Network",
        "database": "Database",
        "dba": "Database",
        "hardware": "Hardware",
        "hardware team": "Hardware",
        "software": "Software",
        "software team": "Software",
        "service desk": "Service Desk",
        "help desk": "Service Desk",
        "openspace": "Openspace",
        "capacity management": "Capacity Management",
        "procurement": "Procurement",
    }

    # Real ServiceNow applications / CIs / Services
    CI_KEYWORDS = [
        "mailserverus",
        "storage area network",
        "sales force",
        "salesforce",
        "peoplesoft",
        "databaseserver",
        "databaseserver2",
        "oracle",
        "sap",
        "sap sales",
        "sap hr",
        "sap financial",
        "sap controlling",
        "exchange",
        "exch-sd-05",
        "nyc rac nas200",
        "beth-ibm",
        "email",
        "switch",
        "router",
        "printer",
        "efax",
        "lawson",
        "headphone",
        "usb",
        "vpn",
        "wifi",
        "active directory",
        "outlook",
        "sfa software",
    ]

    @classmethod
    def translate(cls, user_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Translates English question to ServiceNow sysparm_query and extracted filter metadata."""
        text = user_text.lower().strip()
        context = context or {}
        
        query_clauses: List[str] = []
        applied_filters: Dict[str, Any] = {}

        # 1. Priority Detection
        if any(w in text for w in ["p1", "critical", "sev-1", "severity 1"]):
            query_clauses.append("priority=1")
            applied_filters["priority"] = 1
        elif any(w in text for w in ["p2", "high priority", "sev-2", "severity 2"]):
            query_clauses.append("priority=2")
            applied_filters["priority"] = 2
        elif any(w in text for w in ["p3", "medium", "moderate", "sev-3"]):
            query_clauses.append("priority=3")
            applied_filters["priority"] = 3
        elif any(w in text for w in ["p4", "low", "sev-4"]):
            query_clauses.append("priority=4")
            applied_filters["priority"] = 4
        elif any(w in text for w in ["p5", "planning"]):
            query_clauses.append("priority=5")
            applied_filters["priority"] = 5

        # 2. Dynamic Relative & Named Date/Time Filter Detection
        num_pattern = r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|a|an)"
        NUM_WORDS = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "a": 1, "an": 1
        }
        def extract_num(val: str) -> int:
            val = val.strip().lower()
            if val in NUM_WORDS:
                return NUM_WORDS[val]
            return int(val)

        # Match patterns like: "2 days back", "2 days ago", "in past 60 days", "last 2 days", "within 2 days"
        days_match = (
            re.search(rf"({num_pattern})\s*(?:days?|d)\s*(?:back|ago|prior|earlier|before)\b", text) or
            re.search(rf"(?:in\s+)?(?:the\s+)?(?:past|last)\s*({num_pattern})\s*(?:days?|d)\b", text) or
            re.search(rf"(?:within|since|from)\s*(?:the\s+)?(?:past|last)?\s*({num_pattern})\s*(?:days?|d)\b", text)
        )
        weeks_match = (
            re.search(rf"({num_pattern})\s*(?:weeks?|w)\s*(?:back|ago|prior|earlier|before)\b", text) or
            re.search(rf"(?:in\s+)?(?:the\s+)?(?:past|last)\s*({num_pattern})\s*(?:weeks?|w)\b", text) or
            re.search(rf"(?:within|since|from)\s*(?:the\s+)?(?:past|last)?\s*({num_pattern})\s*(?:weeks?|w)\b", text)
        )
        months_match = (
            re.search(rf"({num_pattern})\s*(?:months?|m)\s*(?:back|ago|prior|earlier|before)\b", text) or
            re.search(rf"(?:in\s+)?(?:the\s+)?(?:past|last)\s*({num_pattern})\s*(?:months?|m)\b", text) or
            re.search(rf"(?:within|since|from)\s*(?:the\s+)?(?:past|last)?\s*({num_pattern})\s*(?:months?|m)\b", text)
        )
        hours_match = (
            re.search(rf"({num_pattern})\s*(?:hours?|hrs?|h)\s*(?:back|ago|prior|earlier|before)\b", text) or
            re.search(rf"(?:in\s+)?(?:the\s+)?(?:past|last)\s*({num_pattern})\s*(?:hours?|hrs?|h)\b", text)
        )
        years_match = re.search(r"(?:in\s+)?(?:the\s+)?(?:past|last)\s+(\d+)\s*(?:years?|y)\b", text)

        month_names = {
            "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
            "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12
        }
        named_month_match = re.search(r"\b(january|february|march|april|may|june|july|august|september|october|november|december)(?:\s+(\d{4}))?\b", text)

        if days_match:
            n_days = extract_num(days_match.group(1))
            query_clauses.append(f"opened_at>=javascript:gs.daysAgoStart({n_days})")
            applied_filters["timeframe"] = f"past_{n_days}_days"
        elif weeks_match:
            n_weeks = extract_num(weeks_match.group(1))
            query_clauses.append(f"opened_at>=javascript:gs.daysAgoStart({n_weeks * 7})")
            applied_filters["timeframe"] = f"past_{n_weeks}_weeks"
        elif months_match:
            n_months = extract_num(months_match.group(1))
            query_clauses.append(f"opened_at>=javascript:gs.monthsAgoStart({n_months})")
            applied_filters["timeframe"] = f"past_{n_months}_months"
        elif hours_match:
            n_hours = extract_num(hours_match.group(1))
            query_clauses.append(f"opened_at>=javascript:gs.hoursAgo({n_hours})")
            applied_filters["timeframe"] = f"past_{n_hours}_hours"
        elif years_match:
            n_years = int(years_match.group(1))
            query_clauses.append(f"opened_at>=javascript:gs.monthsAgoStart({n_years * 12})")
            applied_filters["timeframe"] = f"past_{n_years}_years"
        elif named_month_match:
            m_name = named_month_match.group(1)
            m_num = month_names[m_name]
            y_val = int(named_month_match.group(2)) if named_month_match.group(2) else 2026
            import calendar
            _, last_day = calendar.monthrange(y_val, m_num)
            start_str = f"{y_val}-{m_num:02d}-01 00:00:00"
            end_str = f"{y_val}-{m_num:02d}-{last_day:02d} 23:59:59"
            query_clauses.append(f"opened_at>={start_str}^opened_at<={end_str}")
            applied_filters["timeframe"] = f"{m_name.capitalize()} {y_val}"
        elif "yesterday" in text:
            query_clauses.append("opened_atONYesterday@javascript:gs.beginningOfYesterday()@javascript:gs.endOfYesterday()")
            applied_filters["timeframe"] = "yesterday"
        elif "today" in text:
            query_clauses.append("opened_atONToday@javascript:gs.beginningOfToday()@javascript:gs.endOfToday()")
            applied_filters["timeframe"] = "today"
        elif "last week" in text:
            query_clauses.append("opened_atONLast week@javascript:gs.beginningOfLastWeek()@javascript:gs.endOfLastWeek()")
            applied_filters["timeframe"] = "last_week"
        elif "this week" in text:
            query_clauses.append("opened_atONThis week@javascript:gs.beginningOfThisWeek()@javascript:gs.endOfThisWeek()")
            applied_filters["timeframe"] = "this_week"
        elif "last month" in text:
            query_clauses.append("opened_atONLast month@javascript:gs.beginningOfLastMonth()@javascript:gs.endOfLastMonth()")
            applied_filters["timeframe"] = "last_month"
        elif "this month" in text:
            query_clauses.append("opened_atONThis month@javascript:gs.beginningOfThisMonth()@javascript:gs.endOfThisMonth()")
            applied_filters["timeframe"] = "this_month"
        elif "this year" in text or "in 2026" in text or "2026" in text:
            query_clauses.append("opened_atONThis year@javascript:gs.beginningOfThisYear()@javascript:gs.endOfThisYear()")
            applied_filters["timeframe"] = "this_year"
        elif any(w in text for w in ["all incidents", "show all", "list all", "all time", "everything", "all tickets"]):
            applied_filters["timeframe"] = "all_time"

        # 3. State Detection
        if any(w in text for w in ["currently open", "open incidents", "active", "in progress", "unresolved", "new incidents", "open tickets"]):
            query_clauses.append("stateIN1,2,3^active=true")
            applied_filters["state"] = "Open"
        elif any(w in text for w in ["closed", "resolved", "completed"]):
            query_clauses.append("stateIN6,7")
            applied_filters["state"] = "Closed/Resolved"
        elif "on hold" in text:
            query_clauses.append("state=3")
            applied_filters["state"] = "On Hold"

        # 4. SLA Breached Detection
        if any(w in text for w in ["sla breach", "breached", "sla missed", "missed sla"]):
            query_clauses.append("sla_breached=true")
            applied_filters["sla_breached"] = True

        # 5. Assignment Group Detection
        found_group = False
        for key, group_name in cls.TEAM_MAPPINGS.items():
            if f"assigned to {key}" in text or f"{key} team" in text or f"assignment group {key}" in text or f"assigned to the {key}" in text:
                query_clauses.append(f"assignment_groupLIKE{group_name}")
                applied_filters["assignment_group"] = group_name
                found_group = True
                break

        # Dynamic regex for assigned to group
        if not found_group:
            assigned_match = re.search(r"assigned\s+to\s+(?:the\s+)?([a-zA-Z0-9_\-\s]+?)(?:\s+team|\s+group|\?|$)", text)
            if assigned_match:
                extracted_grp = assigned_match.group(1).strip()
                if extracted_grp and extracted_grp not in ["me", "user", "someone", "anyone"]:
                    query_clauses.append(f"assignment_groupLIKE{extracted_grp}")
                    applied_filters["assignment_group"] = extracted_grp.title()

        # 6. CI / Keyword Detection
        found_ci = None
        for ci in cls.CI_KEYWORDS:
            if ci in text:
                found_ci = ci
                ci_upper = ci.upper()
                query_clauses.append(f"short_descriptionLIKE{ci_upper}^ORdescriptionLIKE{ci_upper}^ORcmdb_ciLIKE{ci_upper}")
                applied_filters["entity"] = ci.title()
                break

        # Dynamic entity detection: "related to X", "for X", "regarding X"
        if not found_ci:
            entity_match = re.search(r"(?:related\s+to|regarding|incidents\s+for)\s+([a-zA-Z0-9_\-\s]+?)(?:\s+in|\s+during|\s+assigned|\?|$)", text)
            if entity_match:
                extracted_entity = entity_match.group(1).strip()
                # Exclude generic words
                if extracted_entity and extracted_entity not in ["the", "all", "yesterday", "today", "past", "last", "service desk", "network"]:
                    query_clauses.append(f"short_descriptionLIKE{extracted_entity}^ORdescriptionLIKE{extracted_entity}^ORcmdb_ciLIKE{extracted_entity}")
                    applied_filters["entity"] = extracted_entity.title()

        # 7. Outage keyword
        if "outage" in text and not found_ci:
            query_clauses.append("short_descriptionLIKEoutage^ORdescriptionLIKEoutage")
            applied_filters["outage"] = True

        # 8. Conversational memory inheritance:
        # ONLY inherit previous filters if this is an explicit follow-up question
        # (e.g. "how many of those were P1?", "which ones were open?", "what about SAP?")
        # NEVER inherit if this is a fresh search query or if user specified any timeframe/criteria.
        is_explicit_followup = any(text.startswith(p) for p in [
            "which of those", "which of them", "how many of those", "how many of them",
            "who was assigned", "what about", "and for", "which one", "why did"
        ])
        
        has_time_words = any(w in text for w in [
            "yesterday", "today", "week", "month", "year", "past", "last", "days", "hours", "all", "recent", "latest"
        ])

        if is_explicit_followup and not applied_filters.get("timeframe") and not has_time_words:
            prev_tf = context.get("previous_filters", {}).get("timeframe")
            if prev_tf == "yesterday":
                query_clauses.append("opened_atONYesterday@javascript:gs.beginningOfYesterday()@javascript:gs.endOfYesterday()")
                applied_filters["timeframe"] = "yesterday"
            elif prev_tf == "last_week":
                query_clauses.append("opened_atONLast week@javascript:gs.beginningOfLastWeek()@javascript:gs.endOfLastWeek()")
                applied_filters["timeframe"] = "last_week"
            elif prev_tf == "last_month":
                query_clauses.append("opened_atONLast month@javascript:gs.beginningOfLastMonth()@javascript:gs.endOfLastMonth()")
                applied_filters["timeframe"] = "last_month"
            elif prev_tf and prev_tf.startswith("past_") and prev_tf.endswith("_days"):
                days_num = prev_tf.split("_")[1]
                query_clauses.append(f"opened_at>=javascript:gs.daysAgoStart({days_num})")
                applied_filters["timeframe"] = prev_tf

        # If no specific clauses, order by newest
        if not query_clauses:
            final_query = "ORDERBYDESCopened_at"
        else:
            final_query = "^".join(query_clauses) + "^ORDERBYDESCopened_at"

        return {
            "sysparm_query": final_query,
            "applied_filters": applied_filters,
            "explanation": cls._generate_explanation(applied_filters, user_text)
        }

    @classmethod
    def _generate_explanation(cls, filters: Dict[str, Any], raw_text: str) -> str:
        parts = []
        if "priority" in filters:
            parts.append(f"Priority = P{filters['priority']}")
        if "timeframe" in filters:
            parts.append(f"Timeframe = {filters['timeframe'].replace('_', ' ').title()}")
        if "state" in filters:
            parts.append(f"State = {filters['state']}")
        if "assignment_group" in filters:
            parts.append(f"Assigned to {filters['assignment_group']}")
        if "entity" in filters:
            parts.append(f"Matching entity '{filters['entity']}'")
        if "sla_breached" in filters:
            parts.append("SLA Breached = True")

        if parts:
            return f"Translated query with filters: {', '.join(parts)}"
        return f"Querying latest ServiceNow operational records matching '{raw_text}'"
