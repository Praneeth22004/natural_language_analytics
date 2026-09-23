import re
import html
from typing import Tuple

class SecurityValidator:
    """Enterprise security validator for natural language and ServiceNow queries."""

    # Disallowed patterns to prevent query injection or malicious payload execution
    DANGEROUS_PATTERNS = [
        r"(DROP\s+TABLE|DELETE\s+FROM|UPDATE\s+.*SET|INSERT\s+INTO)",
        r"(<script.*?>.*?</script>)",
        r"(javascript\s*:\s*(?!gs\.)\w+)", # Allow valid ServiceNow gs.* calls, reject raw JS injection
        r"(\.\./\.\./)",
    ]

    @classmethod
    def sanitize_user_input(cls, query: str) -> str:
        """Sanitizes user input string."""
        if not query:
            return ""
        # Strip excessive whitespace
        cleaned = query.strip()
        # Escape raw HTML
        cleaned = html.escape(cleaned)
        return cleaned

    @classmethod
    def validate_query_safety(cls, query: str) -> Tuple[bool, str]:
        """Validates query against malicious injection attempts."""
        if not query:
            return True, ""
        
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                return False, f"Potentially malicious pattern detected in query: {pattern}"
        
        return True, ""

    @classmethod
    def sanitize_servicenow_query(cls, sysparm_query: str) -> str:
        """Ensures ServiceNow encoded query does not contain illegal characters."""
        if not sysparm_query:
            return ""
        # Remove any null bytes or script tags
        sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", sysparm_query)
        return sanitized
