import re
import datetime
import httpx
import base64
from typing import Dict, List, Any, Optional
from app.core.config import settings
from app.services.enterprise_seed_data import (
    ENTERPRISE_INCIDENTS,
    PROBLEMS,
    CHANGES,
    APPLICATIONS,
    USERS,
    TODAY,
    YESTERDAY
)

class ServiceNowClient:
    """Enterprise ServiceNow REST API Client connecting to live PDI instance with Basic Auth and Session Auth fallback."""

    def __init__(self,
                 instance_url: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 use_mock_fallback: Optional[bool] = None):
        self.instance_url = (instance_url or settings.SERVICENOW_INSTANCE_URL).rstrip("/")
        self.username = username or settings.SERVICENOW_USERNAME
        raw_pw = password or settings.SERVICENOW_PASSWORD
        # Strip outer quotes if passed from dotenv
        if (raw_pw.startswith("'") and raw_pw.endswith("'")) or (raw_pw.startswith('"') and raw_pw.endswith('"')):
            raw_pw = raw_pw[1:-1]
        self.password = raw_pw
        self.use_mock_fallback = use_mock_fallback if use_mock_fallback is not None else settings.SERVICENOW_USE_MOCK_FALLBACK
        self.timeout = settings.SERVICENOW_TIMEOUT
        
        # Cached auth headers and session state
        self._session_cookies: Dict[str, str] = {}
        self._user_token: Optional[str] = None

    def _get_basic_auth_header(self) -> str:
        """Encodes username and password into standard HTTP Basic Authorization header."""
        auth_bytes = f"{self.username}:{self.password}".encode("utf-8")
        return f"Basic {base64.b64encode(auth_bytes).decode('utf-8')}"

    async def _authenticate_session_fallback(self) -> bool:
        """Establishes an interactive web session if Basic Auth is disabled."""
        if not self.instance_url or "dev00000" in self.instance_url:
            return False

        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False, follow_redirects=True) as client:
                login_url = f"{self.instance_url}/login.do"
                await client.get(login_url)

                login_payload = {
                    "user_name": self.username,
                    "user_password": self.password,
                    "sys_action": "sysverb_login"
                }
                resp = await client.post(login_url, data=login_payload)
                tokens = re.findall(r"g_ck\s*=\s*['\"]([^'\"]+)['\"]", resp.text)
                if not tokens:
                    nav_resp = await client.get(f"{self.instance_url}/navpage.do")
                    tokens = re.findall(r"g_ck\s*=\s*['\"]([^'\"]+)['\"]", nav_resp.text)

                if tokens:
                    self._user_token = tokens[0]
                    self._session_cookies = dict(client.cookies)
                    return True
        except Exception as e:
            print(f"[ServiceNow Session Auth Warning]: {e}")

        return False

    async def test_connection(self) -> Dict[str, Any]:
        """Tests live connectivity to the ServiceNow instance."""
        if not self.instance_url or "dev00000" in self.instance_url:
            return {
                "success": False,
                "mode": "Simulation (Mock Mode)",
                "status_code": None,
                "message": "Default placeholder instance configured. Using enterprise demo dataset.",
                "instance": self.instance_url
            }

        endpoint = f"{self.instance_url}/api/now/table/incident?sysparm_limit=5&sysparm_display_value=all"
        headers = {
            "Authorization": self._get_basic_auth_header(),
            "Accept": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                resp = await client.get(endpoint, headers=headers)
                
                # If basic auth succeeds
                if resp.status_code == 200:
                    data = resp.json()
                    count = len(data.get("result", []))
                    return {
                        "success": True,
                        "mode": f"Live ServiceNow PDI (User: {self.username})",
                        "status_code": 200,
                        "message": f"Successfully connected to {self.instance_url}. Retrieved {count} live incidents via REST API.",
                        "instance": self.instance_url,
                        "sample_count": count,
                        "table_urls": {
                            "incident": f"{self.instance_url}/api/now/table/incident",
                            "problem": f"{self.instance_url}/api/now/table/problem",
                            "change_request": f"{self.instance_url}/api/now/table/change_request",
                            "cmdb_ci": f"{self.instance_url}/api/now/table/cmdb_ci",
                            "sys_user": f"{self.instance_url}/api/now/table/sys_user"
                        }
                    }
                
                # If 401, try session auth fallback
                elif resp.status_code == 401:
                    auth_ok = await self._authenticate_session_fallback()
                    if auth_ok and self._user_token:
                        headers_session = {"Accept": "application/json", "X-UserToken": self._user_token}
                        resp2 = await client.get(endpoint, headers=headers_session, cookies=self._session_cookies)
                        if resp2.status_code == 200:
                            count = len(resp2.json().get("result", []))
                            return {
                                "success": True,
                                "mode": f"Live ServiceNow PDI (Session Auth - User: {self.username})",
                                "status_code": 200,
                                "message": f"Successfully connected to {self.instance_url} via session token.",
                                "instance": self.instance_url,
                                "sample_count": count
                            }

                    return {
                        "success": False,
                        "mode": "Authentication Failed",
                        "status_code": 401,
                        "message": f"Invalid credentials for user '{self.username}' on {self.instance_url}.",
                        "instance": self.instance_url
                    }
                else:
                    return {
                        "success": False,
                        "mode": "HTTP Error",
                        "status_code": resp.status_code,
                        "message": f"ServiceNow returned HTTP {resp.status_code}: {resp.text[:150]}",
                        "instance": self.instance_url
                    }
        except httpx.ConnectTimeout:
            return {
                "success": False,
                "mode": "Connection Timeout",
                "status_code": None,
                "message": "ServiceNow PDI connection timed out (instance may be hibernating).",
                "instance": self.instance_url
            }
        except Exception as ex:
            return {
                "success": False,
                "mode": "Network Error",
                "status_code": None,
                "message": f"Failed to reach instance: {str(ex)}",
                "instance": self.instance_url
            }

    async def query_table(self, table_name: str, sysparm_query: str = "", limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Queries a ServiceNow table with live call or fallback simulation."""
        if self.instance_url and "dev00000" not in self.instance_url:
            endpoint = f"{self.instance_url}/api/now/table/{table_name}"
            params = {
                "sysparm_query": sysparm_query,
                "sysparm_limit": limit,
                "sysparm_offset": offset,
                "sysparm_display_value": "all"
            }
            headers = {
                "Authorization": self._get_basic_auth_header(),
                "Accept": "application/json"
            }

            try:
                async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                    resp = await client.get(endpoint, params=params, headers=headers)
                    
                    # If Basic Auth fails with 401, try session token fallback
                    if resp.status_code == 401:
                        if not self._user_token:
                            await self._authenticate_session_fallback()
                        if self._user_token:
                            headers_session = {"Accept": "application/json", "X-UserToken": self._user_token}
                            resp = await client.get(endpoint, params=params, headers=headers_session, cookies=self._session_cookies)

                    if resp.status_code == 200:
                        data = resp.json()
                        raw_results = data.get("result", [])
                        normalized = []
                        for r in raw_results:
                            item = {}
                            for k, v in r.items():
                                if isinstance(v, dict) and "display_value" in v:
                                    item[k] = v.get("display_value")
                                else:
                                    item[k] = v
                            
                            # Attach direct ServiceNow browser URL
                            sys_id = item.get("sys_id")
                            number = item.get("number")
                            if table_name in ["incident", "problem", "change_request"]:
                                if sys_id:
                                    item["servicenow_url"] = f"{self.instance_url}/nav_to.do?uri={table_name}.do?sys_id={sys_id}"
                                elif number:
                                    item["servicenow_url"] = f"{self.instance_url}/{table_name}_list.do?sysparm_query=number={number}"
                                else:
                                    item["servicenow_url"] = f"{self.instance_url}/{table_name}_list.do"
                            else:
                                item["servicenow_url"] = f"{self.instance_url}/{table_name}_list.do"

                            normalized.append(item)
                        
                        # Return live ServiceNow data directly, even if empty list
                        return normalized
            except Exception as e:
                print(f"[ServiceNow Query Exception]: {e}")
                if not self.use_mock_fallback:
                    return []

        # Only use simulation fallback if explicitly enabled
        if self.use_mock_fallback:
            return self._query_mock_table(table_name, sysparm_query, limit, offset)
        return []

    async def create_record(self, table_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a record in a ServiceNow table via live REST API or mock dataset."""
        if self.instance_url and "dev00000" not in self.instance_url:
            endpoint = f"{self.instance_url}/api/now/table/{table_name}"
            headers = {
                "Authorization": self._get_basic_auth_header(),
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            try:
                async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                    resp = await client.post(endpoint, json=payload, headers=headers)

                    # If Basic Auth fails with 401, try session token fallback
                    if resp.status_code == 401:
                        if not self._user_token:
                            await self._authenticate_session_fallback()
                        if self._user_token:
                            headers_session = {
                                "Content-Type": "application/json",
                                "Accept": "application/json",
                                "X-UserToken": self._user_token
                            }
                            resp = await client.post(endpoint, json=payload, headers=headers_session, cookies=self._session_cookies)

                    if resp.status_code in [200, 201]:
                        data = resp.json()
                        raw_result = data.get("result", {})
                        item = {}
                        for k, v in raw_result.items():
                            if isinstance(v, dict) and "display_value" in v:
                                item[k] = v.get("display_value")
                            else:
                                item[k] = v

                        sys_id = item.get("sys_id")
                        number = item.get("number")
                        if sys_id:
                            item["servicenow_url"] = f"{self.instance_url}/nav_to.do?uri={table_name}.do?sys_id={sys_id}"
                        elif number:
                            item["servicenow_url"] = f"{self.instance_url}/{table_name}_list.do?sysparm_query=number={number}"
                        else:
                            item["servicenow_url"] = f"{self.instance_url}/{table_name}_list.do"

                        return item
                    else:
                        print(f"[ServiceNow Create Record Error]: HTTP {resp.status_code} - {resp.text}")
            except Exception as e:
                print(f"[ServiceNow Create Record Exception]: {e}")

        # Fallback simulation if mock enabled or connection fails
        now_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        import uuid
        mock_sys_id = uuid.uuid4().hex
        new_inc_num = f"INC00{len(ENTERPRISE_INCIDENTS) + 1000:05d}"
        created_item = {
            "sys_id": mock_sys_id,
            "number": new_inc_num,
            "short_description": payload.get("short_description", "New Incident"),
            "description": payload.get("description", ""),
            "priority": str(payload.get("priority", "3")),
            "state": "New",
            "category": payload.get("category", "inquiry"),
            "cmdb_ci": payload.get("cmdb_ci", "Service Desk / End-User Devices"),
            "assignment_group": payload.get("assignment_group", "Service Desk"),
            "opened_at": now_str,
            "made_sla": "true",
            "servicenow_url": f"{self.instance_url}/nav_to.do?uri={table_name}.do?sys_id={mock_sys_id}"
        }
        if table_name == "incident":
            ENTERPRISE_INCIDENTS.insert(0, created_item)
        return created_item

    async def update_record(self, table_name: str, sys_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Updates an existing record in a ServiceNow table via live REST API (PATCH) or mock dataset."""
        if self.instance_url and "dev00000" not in self.instance_url:
            endpoint = f"{self.instance_url}/api/now/table/{table_name}/{sys_id}"
            headers = {
                "Authorization": self._get_basic_auth_header(),
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            try:
                async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                    resp = await client.patch(endpoint, json=payload, headers=headers)

                    if resp.status_code == 401:
                        if not self._user_token:
                            await self._authenticate_session_fallback()
                        if self._user_token:
                            headers_session = {
                                "Content-Type": "application/json",
                                "Accept": "application/json",
                                "X-UserToken": self._user_token
                            }
                            resp = await client.patch(endpoint, json=payload, headers=headers_session, cookies=self._session_cookies)

                    if resp.status_code in [200, 201]:
                        data = resp.json()
                        raw_result = data.get("result", {})
                        item = {}
                        for k, v in raw_result.items():
                            if isinstance(v, dict) and "display_value" in v:
                                item[k] = v.get("display_value")
                            else:
                                item[k] = v
                        return item
                    else:
                        print(f"[ServiceNow Update Record Error]: HTTP {resp.status_code} - {resp.text}")
            except Exception as e:
                print(f"[ServiceNow Update Record Exception]: {e}")

        # Fallback simulation if mock enabled or connection fails
        now_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        for inc in ENTERPRISE_INCIDENTS:
            if inc.get("sys_id") == sys_id or inc.get("number") == sys_id:
                for k, v in payload.items():
                    if k == "work_notes":
                        existing_notes = inc.get("work_notes", "")
                        new_note_entry = f"{now_str} - System Administrator (Work notes)\n{v}"
                        inc["work_notes"] = f"{new_note_entry}\n\n{existing_notes}".strip() if existing_notes else new_note_entry
                    else:
                        inc[k] = v
                return inc
        return {"sys_id": sys_id, **payload}

    async def get_incident_work_notes(self, sys_id: str, incident_num: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves chronological journal entries (work_notes, comments) for an incident."""
        notes: List[Dict[str, Any]] = []
        if self.instance_url and "dev00000" not in self.instance_url:
            try:
                # Query sys_journal_field for entries linked to this sys_id
                journals = await self.query_table(
                    "sys_journal_field",
                    sysparm_query=f"element_id={sys_id}^ORDERBYDESCsys_created_on",
                    limit=50
                )
                if journals:
                    for j in journals:
                        notes.append({
                            "type": j.get("element", "work_notes"),
                            "value": j.get("value", ""),
                            "created_at": j.get("sys_created_on", ""),
                            "created_by": j.get("sys_created_by", "System User"),
                            "sys_id": j.get("sys_id", "")
                        })
                    return notes
            except Exception as e:
                print(f"[ServiceNow Get Work Notes Exception]: {e}")

        # Fallback: check incident detail or mock dataset
        target_inc = None
        for inc in ENTERPRISE_INCIDENTS:
            if inc.get("sys_id") == sys_id or inc.get("number") == (incident_num or sys_id):
                target_inc = inc
                break

        if target_inc:
            wn_raw = target_inc.get("work_notes", "")
            if wn_raw:
                blocks = wn_raw.split("\n\n")
                for b in blocks:
                    lines = b.strip().split("\n", 1)
                    header = lines[0] if lines else ""
                    body = lines[1] if len(lines) > 1 else header
                    created_at = header.split(" - ")[0] if " - " in header else ""
                    created_by = header.split(" - ")[1].split(" (")[0] if " - " in header and " (" in header else "Administrator"
                    notes.append({
                        "type": "work_notes",
                        "value": body,
                        "created_at": created_at,
                        "created_by": created_by,
                        "sys_id": ""
                    })
        return notes


    def _query_mock_table(self, table_name: str, query: str, limit: int, offset: int) -> List[Dict[str, Any]]:
        """Applies query filters against mock data mirroring ServiceNow sysparm_query semantics."""
        dataset = []
        if table_name == "incident":
            dataset = ENTERPRISE_INCIDENTS
        elif table_name == "problem":
            dataset = PROBLEMS
        elif table_name == "change_request":
            dataset = CHANGES
        elif table_name == "cmdb_ci":
            dataset = APPLICATIONS
        elif table_name == "sys_user":
            dataset = USERS
        else:
            return []

        if not query or not query.strip():
            return dataset[offset:offset + limit]

        filtered = []
        query_upper = query.upper()

        for item in dataset:
            if self._matches_query(item, query, query_upper):
                filtered.append(item)

        # Ensure servicenow_url is present on all returned items
        for it in filtered[offset:offset + limit]:
            if "servicenow_url" not in it:
                it["servicenow_url"] = f"{self.instance_url}/nav_to.do?uri={table_name}.do?sys_id={it.get('sys_id', '')}"

        return filtered[offset:offset + limit]

    def _matches_query(self, item: Dict[str, Any], raw_query: str, query_upper: str) -> bool:
        """Evaluates whether an item matches the ServiceNow encoded query string."""
        # Priority check
        if "PRIORITY=1" in query_upper and not str(item.get("priority")).startswith("1"):
            return False
        if "PRIORITY=2" in query_upper and not str(item.get("priority")).startswith("2"):
            return False
        if "PRIORITY=3" in query_upper and not str(item.get("priority")).startswith("3"):
            return False
        if "PRIORITY=4" in query_upper and not str(item.get("priority")).startswith("4"):
            return False
        if "PRIORITY=5" in query_upper and not str(item.get("priority")).startswith("5"):
            return False

        # State check (Open vs Closed)
        if "STATEIN1,2,3" in query_upper or "STATE!=CLOSED" in query_upper or "STATE=OPEN" in query_upper or "ACTIVE=TRUE" in query_upper:
            if item.get("state") in ["Closed", "Resolved"]:
                return False
        if "STATE=CLOSED" in query_upper:
            if item.get("state") != "Closed":
                return False

        # SLA Breached
        if "SLA_BREACHED=TRUE" in query_upper or "HAS_BREACHED=TRUE" in query_upper:
            if not item.get("sla_breached"):
                return False

        # Text search (short_description / description LIKE)
        desc_matches = re.findall(r"(?:SHORT_DESCRIPTION|DESCRIPTION)LIKE([^^\^]+)", query_upper)
        for keyword in desc_matches:
            kw = keyword.strip().lower()
            text_target = (item.get("short_description", "") + " " + item.get("description", "")).lower()
            if kw not in text_target:
                return False

        # Assignment group search
        grp_match = re.search(r"ASSIGNMENT_GROUP(?:LIKE|=)([^^\^]+)", raw_query, re.IGNORECASE)
        if grp_match:
            grp_val = grp_match.group(1).strip().lower()
            if grp_val not in str(item.get("assignment_group", "")).lower():
                return False

        # CMDB CI search
        ci_match = re.search(r"CMDB_CI(?:LIKE|=)([^^\^]+)", raw_query, re.IGNORECASE)
        if ci_match:
            ci_val = ci_match.group(1).strip().lower()
            if ci_val not in str(item.get("cmdb_ci", "")).lower():
                return False

        # Date range checks
        opened_at_str = item.get("opened_at")
        if opened_at_str and ("YESTERDAY" in query_upper or "LAST_WEEK" in query_upper or "LAST_MONTH" in query_upper or "OPENED_AT" in query_upper):
            try:
                opened_dt = datetime.datetime.fromisoformat(str(opened_at_str).replace("Z", ""))
                
                # Check for Yesterday filter
                if "YESTERDAY" in query_upper:
                    y_start = (TODAY - datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0)
                    y_end = y_start + datetime.timedelta(days=1)
                    if not (y_start <= opened_dt < y_end):
                        return False
                
                # Check for Last Week filter
                elif "LAST_WEEK" in query_upper:
                    w_start = (TODAY - datetime.timedelta(days=7)).replace(hour=0, minute=0, second=0)
                    w_end = TODAY.replace(hour=23, minute=59, second=59)
                    if not (w_start <= opened_dt <= w_end):
                        return False

                # Check for Last Month filter
                elif "LAST_MONTH" in query_upper:
                    m_start = (TODAY - datetime.timedelta(days=35)).replace(hour=0, minute=0, second=0)
                    m_end = TODAY
                    if not (m_start <= opened_dt <= m_end):
                        return False

                # Check for BETWEEN filter (e.g. opened_atBETWEEN2026-08-01 00:00:00@2026-08-31 23:59:59)
                between_match = re.search(r"OPENED_ATBETWEEN([^@]+)@([^^\^]+)", query_upper)
                if between_match:
                    dt_start = datetime.datetime.fromisoformat(between_match.group(1).strip())
                    dt_end = datetime.datetime.fromisoformat(between_match.group(2).strip())
                    if not (dt_start <= opened_dt <= dt_end):
                        return False

                # Check for >= date filter
                gte_match = re.search(r"OPENED_AT>=([^^\^]+)", query_upper)
                if gte_match and "DAYSAGO" not in gte_match.group(1) and "JAVASCRIPT" not in gte_match.group(1):
                    try:
                        dt_gte = datetime.datetime.fromisoformat(gte_match.group(1).strip())
                        if opened_dt < dt_gte:
                            return False
                    except Exception:
                        pass

                # Check for <= date filter
                lte_match = re.search(r"OPENED_AT<=([^^\^]+)", query_upper)
                if lte_match and "DAYSAGO" not in lte_match.group(1) and "JAVASCRIPT" not in lte_match.group(1):
                    try:
                        dt_lte = datetime.datetime.fromisoformat(lte_match.group(1).strip())
                        if opened_dt > dt_lte:
                            return False
                    except Exception:
                        pass
            except Exception:
                pass

        return True

# Singleton instance
default_sn_client = ServiceNowClient()

def build_timeframe_query(timeframe: Optional[str]) -> str:
    """Builds a ServiceNow sysparm_query fragment for a given named timeframe or report period title."""
    if not timeframe:
        return ""
    import calendar
    import re
    text = timeframe.lower().replace("_", " ").strip()

    # 1. 30 days / past 30 days / last 30 days
    if "30 day" in text:
        return "opened_at>=javascript:gs.daysAgoStart(30)"

    # 2. 6 months / past 6 months / last 6 months / 180 days
    if "6 month" in text or "past_6_months" in text or "last_6_months" in text:
        return "opened_at>=javascript:gs.daysAgoStart(180)"

    # 3. Quarters e.g. Q1 2026, Q2 2026, Q3 2026, Q4 2026
    q_match = re.search(r"\bq([1-4])\b\s*(20\d\d)?", text)
    if q_match:
        q_num = int(q_match.group(1))
        year = int(q_match.group(2)) if q_match.group(2) else 2026
        q_months = {
            1: (1, 3, 31),
            2: (4, 6, 30),
            3: (7, 9, 30),
            4: (10, 12, 31)
        }
        sm, em, ed = q_months[q_num]
        return f"opened_at>={year}-{sm:02d}-01 00:00:00^opened_at<={year}-{em:02d}-{ed:02d} 23:59:59"

    # 4. Named month e.g. August 2026, March 2026, September 2026
    month_names = {
        "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
        "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7,
        "august": 8, "aug": 8, "september": 9, "sep": 9, "sept": 9, "october": 10, "oct": 10,
        "november": 11, "nov": 11, "december": 12, "dec": 12
    }
    for m_name, m_num in month_names.items():
        pattern = rf"\b{m_name}\b\s*(20\d\d)?"
        m_match = re.search(pattern, text)
        if m_match:
            year = int(m_match.group(1)) if m_match.group(1) else 2026
            _, last_day = calendar.monthrange(year, m_num)
            return f"opened_at>={year}-{m_num:02d}-01 00:00:00^opened_at<={year}-{m_num:02d}-{last_day:02d} 23:59:59"

    # 5. Yesterday
    if "yesterday" in text:
        return "opened_atONYesterday@javascript:gs.beginningOfYesterday()@javascript:gs.endOfYesterday()"

    # 6. Today
    if "today" in text:
        return "opened_atONToday@javascript:gs.beginningOfToday()@javascript:gs.endOfToday()"

    # 7. Last week
    if "last week" in text or "last_week" in text:
        return "opened_atONLast week@javascript:gs.beginningOfLastWeek()@javascript:gs.endOfLastWeek()"

    # 8. This week
    if "this week" in text or "this_week" in text:
        return "opened_atONThis week@javascript:gs.beginningOfThisWeek()@javascript:gs.endOfThisWeek()"

    # 9. Last month (without a specific year)
    if "last month" in text or "last_month" in text:
        return "opened_atONLast month@javascript:gs.beginningOfLastMonth()@javascript:gs.endOfLastMonth()"

    # 10. This month (without a specific year)
    if "this month" in text or "this_month" in text:
        return "opened_atONThis month@javascript:gs.beginningOfThisMonth()@javascript:gs.endOfThisMonth()"

    # 11. All time
    if "all" in text or "all-time" in text or "all_time" in text:
        return ""

    return ""
