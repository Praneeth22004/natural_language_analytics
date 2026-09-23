import re
from typing import Dict, Any, Optional, Tuple

class CategoryClassifier:
    """Intelligently analyzes incident short_description and description
    to map them to the 5 standard ServiceNow categories:
    - Database ('database' -> 'Database')
    - Hardware ('hardware' -> 'Hardware')
    - Inquiry / Help ('inquiry' -> 'Inquiry / Help')
    - Network ('network' -> 'Network')
    - Software ('software' -> 'Software')
    """

    CATEGORIES = {
        "database": "Database",
        "hardware": "Hardware",
        "inquiry": "Inquiry / Help",
        "network": "Network",
        "software": "Software",
    }

    # High-confidence phrase / regex patterns with weights
    _PATTERNS = {
        "database": [
            (re.compile(r"\b(?:oracle|exadata|postgres|postgresql|mysql|mssql|mongodb|redis|cassandra|dynamodb|mariadb|sqlite)\b", re.I), 5),
            (re.compile(r"\b(?:hikaricp|hikari|connection pool|connection timeout|pool exhausted)\b", re.I), 5),
            (re.compile(r"\b(?:tablespace|table space|deadlock|sql\s*syntax|slow query|database backup|db\s*dump|query performance)\b", re.I), 5),
            (re.compile(r"\b(?:unclosed hibernate|unclosed session|transaction log|database cluster|missing index|staging db)\b", re.I), 5),
            (re.compile(r"\b(?:database|db|sql|queries|query|schema|stored procedure|etl|replication lag|replica sync)\b", re.I), 3),
        ],
        "network": [
            (re.compile(r"\b(?:vpn|wi-?fi|firewall|router|edge router|border gateway|default gateway|switch)\b", re.I), 5),
            (re.compile(r"\b(?:packet loss|latency|jitter|ip conflict|ip address conflict|split tunneling)\b", re.I), 5),
            (re.compile(r"\b(?:route table|bgp|dns|dhcp|subnet|vlan|ethernet|directconnect|direct connect)\b", re.I), 5),
            (re.compile(r"\b(?:cannot ping|ping failed|unreachable host|network drop|circuit down|cannot access shared drive)\b", re.I), 5),
            (re.compile(r"\b(?:network|bandwidth|connectivity|cisco|proxy|lan|wan|internet down|interface flapping)\b", re.I), 3),
        ],
        "hardware": [
            (re.compile(r"\b(?:laptop|workstation|pc|monitor|screen flickering|trackpad|keyboard|mouse)\b", re.I), 5),
            (re.compile(r"\bdesktop\b(?!\s+(?:client|app|application|software|edition))\b", re.I), 5),
            (re.compile(r"\b(?:docking station|charger|power cord|power supply|battery not charging)\b", re.I), 5),
            (re.compile(r"\b(?:printer|toner|cartridge|paper jam|print spooler|scanner|headset|webcam)\b", re.I), 5),
            (re.compile(r"\b(?:hard drive|hdd|ssd|disk failure|disk clicking|clicking noise|beeping sound|server beeping)\b", re.I), 5),
            (re.compile(r"\b(?:motherboard|cpu fan|fan noise|overheating|ram stick|memory stick|raid controller)\b", re.I), 5),
            (re.compile(r"\b(?:hardware|peripheral|display|broken screen|physical damage|not responding)\b", re.I), 3),
        ],
        "software": [
            (re.compile(r"\b(?:desktop client|web client|email client|email not syncing|not syncing|syncing|email)\b", re.I), 5),
            (re.compile(r"\b(?:application crashing|app crash|crashed|crashing|freeze|freezing|frozen)\b", re.I), 5),
            (re.compile(r"\b(?:nullpointer|500 internal server error|500 error|502 bad gateway|504 gateway timeout|http 500)\b", re.I), 5),
            (re.compile(r"\b(?:sap|erp|salesforce|crm|office 365|o365|outlook|teams|slack|excel|visio|sharepoint)\b", re.I), 5),
            (re.compile(r"\b(?:license expired|licensing error|antivirus scan|software update|patch failure)\b", re.I), 5),
            (re.compile(r"\b(?:okta|sso login|login loop|jwt|oauth token|token refresh|webhook|microservice)\b", re.I), 5),
            (re.compile(r"\b(?:kubernetes|k8s|pod crashloop|docker container|build failed|deployment failed)\b", re.I), 5),
            (re.compile(r"\b(?:software|application|app|bug|defect|exception|portal|customer portal|employee hub)\b", re.I), 3),
            (re.compile(r"\b(?:sync stalled|sync failure|session timeout|login failing|runtime error)\b", re.I), 3),
        ],
        "inquiry": [
            (re.compile(r"\b(?:how to|how do i|how can i|where can i|when is|what is the policy)\b", re.I), 6),
            (re.compile(r"\b(?:password reset|reset password|forgot password|unlock account|account locked)\b", re.I), 6),
            (re.compile(r"\b(?:request access|access request|need access to|grant access|how to request)\b", re.I), 6),
            (re.compile(r"\b(?:benefits enrollment|company holiday|next holiday|paystub|paystubs|payroll|salary question)\b", re.I), 6),
            (re.compile(r"\b(?:inquiry|question|help|guidance|training|tutorial|documentation|information)\b", re.I), 3),
        ]
    }

    @classmethod
    def normalize(cls, category: Optional[str]) -> Optional[str]:
        """Normalizes user/system provided category strings to canonical ServiceNow values."""
        if not category:
            return None
        cleaned = str(category).strip().lower()
        if cleaned in ["inquiry", "inquiry / help", "inquiry/help", "help", "password_reset", "inquiry_help"]:
            return "inquiry"
        if cleaned in ["database", "db", "database infrastructure"]:
            return "database"
        if cleaned in ["hardware", "hw", "hardware infrastructure"]:
            return "hardware"
        if cleaned in ["network", "net", "network infrastructure"]:
            return "network"
        if cleaned in ["software", "sw", "application", "software infrastructure"]:
            return "software"
        return None

    @classmethod
    def get_display_label(cls, category: str) -> str:
        """Returns the ServiceNow UI display label for a category."""
        return cls.CATEGORIES.get(category.lower(), category.title())

    @classmethod
    def classify(cls, short_description: str = "", description: str = "") -> str:
        """Analyzes incident text and scores against all 5 categories.
        Returns the best matching category: database, hardware, network, software, or inquiry.
        """
        short_desc = (short_description or "").strip()
        desc = (description or "").strip()
        
        if not short_desc and not desc:
            return "inquiry"

        scores: Dict[str, float] = {cat: 0.0 for cat in cls.CATEGORIES}

        # Weight short_description higher (1.5x) as it contains the core summary
        text_parts = [
            (short_desc, 1.5),
            (desc, 1.0)
        ]

        for text, weight_multiplier in text_parts:
            if not text:
                continue
            for cat, pattern_list in cls._PATTERNS.items():
                for regex, weight in pattern_list:
                    matches = regex.findall(text)
                    if matches:
                        scores[cat] += len(matches) * weight * weight_multiplier

        # Detect strong inquiry signals: questions, password reset, or "how to"
        combined_lower = f"{short_desc} {desc}".lower()
        has_error_or_outage = any(w in combined_lower for w in [
            "error", "fail", "timeout", "down", "outage", "crashed", "broken",
            "deadlock", "flickering", "dropped", "dropping", "slow", "freeze", "500", "504"
        ])

        # If it's a request/question with no active system error, boost inquiry
        if not has_error_or_outage:
            if any(w in combined_lower for w in ["how to", "how do i", "when is", "request access", "password reset", "benefits", "paystub"]):
                scores["inquiry"] += 10.0

        # Sort by highest score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_cat, top_score = ranked[0]

        # If no positive matches, default to inquiry
        if top_score <= 0.0:
            return "inquiry"

        return top_cat
