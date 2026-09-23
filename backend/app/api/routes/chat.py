import re
import time
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import AuditLog, ChatMessage
from app.core.security import SecurityValidator
from app.ai.intent_detector import IntentDetector
from app.ai.query_translator import QueryTranslator
from app.ai.insights_engine import InsightsEngine
from app.ai.memory_manager import memory_manager
from app.ai.llm_client import llm_client
from app.ai.category_classifier import CategoryClassifier
from app.mcp.servicenow_mcp import servicenow_mcp_server
from app.mcp.analytics_mcp import analytics_mcp_server
from app.mcp.reporting_mcp import reporting_mcp_server

router = APIRouter(prefix="/api/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default_session"

class ChatResponse(BaseModel):
    session_id: str
    intent: str
    sysparm_query: Optional[str] = None
    response_text: str
    structured_data: Optional[Dict[str, Any]] = None
    execution_time_ms: int
    suggestions: List[str] = []

class ResetSessionRequest(BaseModel):
    session_id: str

class ResetSessionResponse(BaseModel):
    status: str
    session_id: str
    message: str

@router.post("/session/reset", response_model=ResetSessionResponse)
async def reset_chat_session(req: ResetSessionRequest):
    """Explicitly resets and clears conversational memory for the given session ID."""
    memory_manager.reset_session(req.session_id)
    return ResetSessionResponse(
        status="success",
        session_id=req.session_id,
        message="Chat session memory has been cleared and reset successfully."
    )

@router.post("", response_model=ChatResponse)
async def process_chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    start_time = time.time()
    raw_query = req.message.strip()
    session_id = req.session_id or "default_session"

    # Security validation
    is_safe, error_msg = SecurityValidator.validate_query_safety(raw_query)
    if not is_safe:
        return ChatResponse(
            session_id=session_id,
            intent="SECURITY_BLOCKED",
            response_text=f"Security alert: {error_msg}",
            execution_time_ms=int((time.time() - start_time) * 1000)
        )

    # Fetch session context
    session = memory_manager.get_or_create_session(session_id)
    context = session.get_context()

    # Detect Intent
    intent = IntentDetector.detect_intent(raw_query, context)

    # Route based on detected intent
    sysparm_query = None
    response_text = ""
    structured_data = None
    records_count = 0
    suggestions = []
    applied_filters = {}
    retrieved_incidents = None

    # -1. RESET / END CHAT SESSION INTENT
    if intent == IntentDetector.INTENT_RESET_SESSION:
        memory_manager.reset_session(session_id)
        response_text = (
            "🔄 **Chat Context Cleared & Session Restarted**\n\n"
            "All prior conversational memory, cached query filters, and tracked incident references have been reset.\n\n"
            "I am ready for a fresh inquiry! How can I assist you with ServiceNow IT operations, outages, or incident diagnostics today?"
        )
        structured_data = {
            "session_reset": True,
            "session_id": session_id
        }
        suggestions = [
            "Show all P1 critical incidents",
            "Ticket a ServiceNow incident: Oracle database connection timeout",
            "Show open problem tickets",
            "What are our operational KPIs?"
        ]

    # 0. DIRECT LLM ASSISTANCE (General Knowledge, Conversational, Technical, or Analytical Questions)
    elif intent == IntentDetector.INTENT_DIRECT_LLM:
        history = session.get_chat_history(max_turns=6)
        system_instruction = (
            "You are a helpful, highly knowledgeable AI assistant with deep expertise in technology, "
            "systems engineering, ITIL operations, and ServiceNow. "
            "Answer the user's question accurately, directly, and concisely (under 90 words). "
            "Maintain continuity with previous turns in this conversation if the user refers to past context."
        )
        prompt = [{"role": "system", "content": system_instruction}]
        if history:
            prompt.extend(history)
        prompt.append({"role": "user", "content": raw_query})

        llm_reply = None
        try:
            llm_reply = await llm_client.generate_chat_completion(prompt, temperature=0.3, max_tokens=220)
        except Exception:
            pass

        if llm_reply:
            response_text = llm_reply.strip()
        else:
            response_text = (
                "I am your AI Incident & Operational Assistant. "
                "I specialize in analyzing ServiceNow incidents, outages, problems, CMDB items, and MTTR telemetry. "
                "How can I assist your IT operations today?"
            )

        structured_data = None
        suggestions = [
            "Show all P1 critical incidents",
            "Identify recurring incidents and root causes",
            "Show open problem tickets",
            "What are our operational KPIs?"
        ]

    # 0.5 TICKET A SERVICENOW INCIDENT (Natural Language Creation via NVIDIA LLM)
    elif intent == IntentDetector.INTENT_CREATE_INCIDENT:
        # Step 1: Use NVIDIA LLM to parse and extract incident attributes
        extraction_prompt = [
            {
                "role": "system",
                "content": (
                    "You are a ServiceNow IT Service Management dispatcher. "
                    "Extract incident details from the user's message into JSON with keys: "
                    "'short_description' (concise title under 15 words), "
                    "'description' (detailed explanation of the problem), "
                    "'priority' (integer 1 to 5, default 3; set 1 for critical/outage/sev-1/down, 2 for high/urgent, 3 for moderate, 4 for low), "
                    "'category' (one of: database, network, software, hardware, inquiry), "
                    "'cmdb_ci' (affected application, server, or database name, e.g. MailServerUS, Oracle, SAP, or empty string if unspecified), "
                    "'assignment_group' (one of: Database, Network, Software, Hardware, Service Desk). "
                    "Output ONLY the JSON object. Do not include markdown codeblocks or extra text."
                )
            },
            {
                "role": "user",
                "content": raw_query
            }
        ]

        extracted_data = {}
        try:
            llm_json_text = await llm_client.generate_chat_completion(extraction_prompt, temperature=0.1, max_tokens=180)
            if llm_json_text:
                cleaned = re.sub(r"^```(?:json)?", "", llm_json_text.strip(), flags=re.MULTILINE)
                cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE)
                import json
                extracted_data = json.loads(cleaned)
        except Exception as e:
            print(f"[Incident Extraction Error]: {e}")

        # Fallback extraction if LLM JSON parsing fails
        if not extracted_data.get("short_description"):
            clean_title = re.sub(
                r"^(ticket\s+(a\s+)?(service\s*now\s+)?incident|create\s+(an\s+)?incident|open\s+(a\s+)?ticket|file\s+(an\s+)?incident|raise\s+(a\s+)?ticket)\s*[:\-\s]*",
                "", raw_query, flags=re.IGNORECASE
            ).strip()
            if not clean_title:
                clean_title = raw_query
            prio = 3
            if any(w in raw_query.lower() for w in ["p1", "critical", "sev-1", "severity 1", "down", "outage"]):
                prio = 1
            elif any(w in raw_query.lower() for w in ["p2", "high", "sev-2", "severity 2", "urgent"]):
                prio = 2

            extracted_data = {
                "short_description": clean_title[:100],
                "description": raw_query,
                "priority": prio,
                "category": CategoryClassifier.classify(clean_title, raw_query),
                "cmdb_ci": "Oracle Database (SAP ORA01)" if "oracle" in raw_query.lower() else ("MailServerUS" if any(w in raw_query.lower() for w in ["mail", "email"]) else "Service Desk / End-User Devices"),
                "assignment_group": "Database" if any(w in raw_query.lower() for w in ["oracle", "sql"]) else ("Network" if any(w in raw_query.lower() for w in ["vpn", "switch"]) else "Service Desk")
            }
        else:
            # If LLM didn't produce a valid category or used default inquiry, analyze text
            curr_cat = extracted_data.get("category")
            if not curr_cat or CategoryClassifier.normalize(curr_cat) in [None, "inquiry"]:
                extracted_data["category"] = CategoryClassifier.classify(
                    extracted_data.get("short_description", ""),
                    extracted_data.get("description", raw_query)
                )

        # Step 2: Create ticket in ServiceNow via MCP tool
        create_result = await servicenow_mcp_server.execute_tool("create_incident", extracted_data)
        created_inc = create_result.get("incident", {})
        inc_num = created_inc.get("number", "INC0010001")
        inc_prio = created_inc.get("priority", extracted_data.get("priority", 3))

        # Safely resolve cmdb_ci and assignment_group display names
        raw_ci = created_inc.get("cmdb_ci")
        if isinstance(raw_ci, dict) and raw_ci.get("display_value"):
            inc_ci = raw_ci["display_value"]
        elif isinstance(raw_ci, str) and raw_ci.strip():
            inc_ci = raw_ci
        else:
            inc_ci = extracted_data.get("cmdb_ci") or "Service Desk / End-User Devices"

        raw_group = created_inc.get("assignment_group")
        if isinstance(raw_group, dict) and raw_group.get("display_value"):
            inc_group = raw_group["display_value"]
        elif isinstance(raw_group, str) and raw_group.strip():
            inc_group = raw_group
        else:
            inc_group = extracted_data.get("assignment_group") or "Service Desk"

        inc_url = created_inc.get("servicenow_url", f"https://dev204434.service-now.com/nav_to.do?uri=incident.do?sys_id={created_inc.get('sys_id', '')}")
        inc_title = created_inc.get("short_description") or extracted_data.get("short_description", "Incident")

        prio_map = {"1": "P1 - Critical", "2": "P2 - High", "3": "P3 - Moderate", "4": "P4 - Low", "5": "P5 - Planning"}
        prio_label = prio_map.get(str(inc_prio), f"P{inc_prio}")

        # Step 3: Use NVIDIA LLM for immediate initial SRE triage recommendations
        triage_prompt = [
            {
                "role": "system",
                "content": (
                    "You are a Lead Site Reliability Engineer (SRE). "
                    "An incident has just been created in ServiceNow. Provide a brief initial operational triage brief (under 80 words) "
                    "outlining 2-3 immediate technical diagnostic and remediation steps for the assigned team."
                )
            },
            {
                "role": "user",
                "content": f"Incident: {inc_num}\nTitle: {inc_title}\nPriority: {prio_label}\nCI: {inc_ci}\nGroup: {inc_group}"
            }
        ]
        llm_triage = None
        try:
            llm_triage = await llm_client.generate_chat_completion(triage_prompt, temperature=0.2, max_tokens=180)
        except Exception:
            pass

        triage_text = llm_triage.strip() if llm_triage else (
            f"1. Acknowledge ticket and notify {inc_group} on-call engineer.\n"
            f"2. Inspect real-time telemetry and error logs for {inc_ci}.\n"
            f"3. Check for recent infrastructure changes or deployments."
        )

        raw_cat_val = created_inc.get("category") or extracted_data.get("category", "inquiry")
        cat_display = CategoryClassifier.get_display_label(str(raw_cat_val))

        response_text = (
            f"### 🎫 Incident Created in ServiceNow: **{inc_num}**\n\n"
            f"Your incident has been submitted to **ServiceNow (dev204434)**.\n\n"
            f"| Attribute | Value |\n"
            f"| :--- | :--- |\n"
            f"| **Ticket Number** | `{inc_num}` |\n"
            f"| **Category** | **{cat_display}** |\n"
            f"| **Priority** | **{prio_label}** |\n"
            f"| **State** | **New / Unassigned** |\n"
            f"| **Short Description** | {inc_title} |\n"
            f"| **Configuration Item** | {inc_ci} |\n"
            f"| **Assignment Group** | {inc_group} |\n\n"
            f"🔗 **[Open {inc_num} in ServiceNow PDI]({inc_url})**\n\n"
            f"#### 🛠️ AI Initial SRE Triage & Immediate Actions\n"
            f"{triage_text}"
        )

        structured_data = {
            "created": True,
            "incident": created_inc,
            "ticket_number": inc_num,
            "servicenow_url": inc_url
        }

        suggestions = [
            f"Summarize {inc_num}",
            f"Show work notes for {inc_num}",
            "Show all P1 critical incidents",
            "What are our operational KPIs?"
        ]

    # 1.1 WORK NOTES MANAGEMENT (View & Add Work Notes)
    elif intent == IntentDetector.INTENT_WORKNOTES:
        inc_match = re.search(r"\b(inc\d{5,8})\b", raw_query, re.IGNORECASE)
        target_num = inc_match.group(1).upper() if inc_match else context.get("last_incident_number")

        if not target_num:
            response_text = (
                "### 📝 ServiceNow Incident Work Notes\n\n"
                "Please specify an incident number to view or add work notes.\n\n"
                "**Examples:**\n"
                "- `Show work notes for INC0000060`\n"
                "- `Add work note to INC0000060: Primary database failover verified and operational.`"
            )
            suggestions = ["Show work notes for INC0000060", "Show all P1 critical incidents"]
        else:
            context["last_incident_number"] = target_num
            # Detect if user wants to ADD a work note
            is_adding = any(w in raw_query.lower() for w in ["add", "append", "log", "update", "write", "record"]) or ":" in raw_query
            
            note_content = ""
            if ":" in raw_query:
                note_content = raw_query.split(":", 1)[1].strip()
            elif is_adding:
                # Try to extract after target_num
                parts = re.split(re.escape(target_num), raw_query, flags=re.IGNORECASE)
                if len(parts) > 1 and parts[1].strip():
                    cleaned = re.sub(r"^(?:with|saying|that|note|work\s*note|worknotes|to|is|as)?\s*[:\-\s]*", "", parts[1].strip(), flags=re.IGNORECASE)
                    if len(cleaned) > 5:
                        note_content = cleaned

            if is_adding and note_content:
                add_res = await servicenow_mcp_server.execute_tool("add_work_note", {
                    "identifier": target_num,
                    "work_notes": note_content
                })
                if add_res.get("success"):
                    response_text = (
                        f"### ✅ Work Note Added to **{target_num}**\n\n"
                        f"The internal work note has been updated in live **ServiceNow (dev204434)**:\n\n"
                        f"> 💬 *\"{note_content}\"*\n\n"
                        f"- **Ticket:** `{target_num}`\n"
                        f"- **State:** {add_res.get('state', 'Active')}\n"
                        f"- **Total Journal Entries:** {len(add_res.get('updated_notes', []))}\n\n"
                        f"🔗 **[Open {target_num} in ServiceNow](https://dev204434.service-now.com/incident_list.do?sysparm_query=number={target_num})**"
                    )
                    structured_data = {
                        "work_note_added": True,
                        "incident_number": target_num,
                        "note": note_content,
                        "work_notes": add_res.get("updated_notes", [])
                    }
                else:
                    response_text = f"❌ Failed to add work note to {target_num}: {add_res.get('message', 'Unknown error')}"
            else:
                # Fetch work notes
                notes_res = await servicenow_mcp_server.execute_tool("get_incident_work_notes", {"identifier": target_num})
                notes = notes_res.get("work_notes", [])
                if notes:
                    note_lines = []
                    for idx, n in enumerate(notes[:8], 1):
                        author = n.get("created_by") or "System"
                        ts = n.get("created_at") or ""
                        val = n.get("value", "").replace("\n", " ")
                        note_lines.append(f"**{idx}. {author}** *({ts})*\n> {val}\n")
                    response_text = (
                        f"### 📋 Work Notes & Activity History for **{target_num}**\n\n"
                        f"Found **{len(notes)}** journal entr{'y' if len(notes)==1 else 'ies'} in ServiceNow:\n\n"
                        + "\n".join(note_lines) +
                        f"\n🔗 **[Open {target_num} in ServiceNow](https://dev204434.service-now.com/incident_list.do?sysparm_query=number={target_num})**"
                    )
                else:
                    response_text = (
                        f"### 📋 Work Notes for **{target_num}**\n\n"
                        f"No prior work notes or journal entries recorded yet on `{target_num}`.\n\n"
                        f"You can add one by replying: `Add work note to {target_num}: Your diagnostic findings...`"
                    )
                structured_data = {
                    "incident_number": target_num,
                    "count": len(notes),
                    "work_notes": notes
                }

            suggestions = [
                f"Add work note to {target_num}: Verified telemetry normal.",
                f"Summarize {target_num}",
                "Show all P1 critical incidents"
            ]

    # 1. OUTAGE INVESTIGATION
    elif intent == IntentDetector.INTENT_OUTAGE_INVESTIGATION:
        query_info = QueryTranslator.translate(raw_query, context)
        sysparm_query = query_info["sysparm_query"]
        incidents = await servicenow_mcp_server.client.query_table("incident", sysparm_query=sysparm_query, limit=5)
        if not incidents:
            incidents = await servicenow_mcp_server.client.query_table("incident", sysparm_query="priority=1", limit=5)

        outage_data = await InsightsEngine.synthesize_outage_investigation(incidents, raw_query)
        structured_data = outage_data

        # LLM SRE outage synthesis
        llm_outage = None
        if outage_data.get("found"):
            prompt = [
                {
                    "role": "system",
                    "content": "You are a Principal SRE analyzing a major outage from ServiceNow. Provide a concise technical executive summary and key remediation steps (under 90 words)."
                },
                {
                    "role": "user",
                    "content": f"Incident: {outage_data.get('incident_number')}\nTitle: {outage_data.get('title')}\nCI: {outage_data.get('primary_ci')}\nDuration: {outage_data.get('duration')}\nResolution: {outage_data.get('resolution_summary')}\nImpacted: {', '.join(outage_data.get('impacted_applications', []))}"
                }
            ]
            try:
                llm_outage = await llm_client.generate_chat_completion(prompt, temperature=0.1, max_tokens=180)
            except Exception:
                pass

        if llm_outage:
            response_text = (
                f"**Major Outage Analysis ({outage_data.get('incident_number', 'INC0000001')}):**\n"
                f"{llm_outage.strip()}\n\n"
                f"- **Primary CI:** {outage_data.get('primary_ci')} | **Duration:** {outage_data.get('duration')}\n"
                f"- **Impacted Services:** " + ", ".join(outage_data.get("impacted_applications", []))
            )
        else:
            response_text = (
                f"**Major Outage Report (ServiceNow dev204434):**\n"
                f"- **Incident:** {outage_data.get('incident_number', 'INC0000001')} — {outage_data.get('title', 'Service Outage')}\n"
                f"- **Primary Impacted CI:** {outage_data.get('primary_ci', 'MailServerUS')}\n"
                f"- **Duration:** {outage_data.get('duration', '2 hours 15 minutes')}\n"
                f"- **Resolution:** {outage_data.get('resolution_summary', 'Remediated')}\n"
                f"- **Impacted Services:** " + ", ".join(outage_data.get("impacted_applications", []))
            )
        suggestions = ["Show root cause analysis", "Show all P1 critical incidents", "How many incidents are currently open?"]

    # 2. RECURRING INCIDENTS
    elif intent == IntentDetector.INTENT_RECURRING_ANALYSIS:
        recurring_data = await analytics_mcp_server.execute_tool("cluster_recurring_incidents", {"min_occurrences": 2})
        structured_data = recurring_data
        clusters = recurring_data.get("recurring_clusters", [])
        top_cluster = clusters[0] if clusters else {}
        sample_tickets = ", ".join(top_cluster.get("matching_tickets", [])[:4]) or "INC0000009, INC0000014"

        llm_recurring = None
        if clusters:
            c_summaries = [
                f"- {c['title']} ({c['occurrences']}x, CI: {c['affected_application']}): Root Cause: {c['root_cause']}"
                for c in clusters[:3]
            ]
            prompt = [
                {
                    "role": "system",
                    "content": "You are a Principal SRE. Synthesize these ServiceNow recurring incident clusters into a concise operational diagnosis and preventative roadmap (under 90 words)."
                },
                {
                    "role": "user",
                    "content": f"User query: {raw_query}\nTop Clusters:\n" + "\n".join(c_summaries)
                }
            ]
            try:
                llm_recurring = await llm_client.generate_chat_completion(prompt, temperature=0.1, max_tokens=180)
            except Exception:
                pass

        if llm_recurring:
            response_text = (
                f"**AI Recurring Incident Intelligence:**\n"
                f"{llm_recurring.strip()}\n\n"
                f"- **Detected Patterns:** {recurring_data.get('total_clusters_detected', 0)} distinct clusters ({recurring_data.get('total_clustered_incidents', 0)} tickets)\n"
                f"- **Highest Repeat Culprit:** {top_cluster.get('title')} ({top_cluster.get('occurrences')}x on {top_cluster.get('affected_application')})\n"
                f"- **Linked Problem Record:** {top_cluster.get('linked_problem', 'PRB0000003')}"
            )
        else:
            response_text = (
                f"**Recurring Incident Analysis (Live ServiceNow Data):**\n"
                f"Identified **{recurring_data.get('total_clusters_detected', 0)} recurring clusters** across your ServiceNow operational tickets ({recurring_data.get('total_clustered_incidents', 0)} clustered incidents).\n\n"
                f"- **Top Cluster:** {top_cluster.get('title', 'Service Desk Access Bottlenecks')}\n"
                f"- **Root Cause:** {top_cluster.get('root_cause', 'Unknown')}\n"
                f"- **Volume:** {top_cluster.get('occurrences', 0)} live incidents ({sample_tickets})\n"
                f"- **Primary Application / CI:** {top_cluster.get('affected_application', 'Service Desk')}\n"
                f"- **Linked Problem Record:** {top_cluster.get('linked_problem', 'PRB0000003')}\n"
                f"- **Prescriptive Recommendation:** {top_cluster.get('recommendation', 'N/A')}"
            )
        suggestions = ["Show root causes by application", "Show all P1 critical incidents", "Which applications generated the most incidents?"]

    # 3. ROOT CAUSE ANALYSIS (RCA) LOOKUP
    elif intent == IntentDetector.INTENT_RCA_LOOKUP:
        rca_data = await analytics_mcp_server.execute_tool("get_root_cause_leaderboard", {})
        structured_data = rca_data
        leaderboard = rca_data.get("leaderboard", [])

        llm_rca = None
        if leaderboard:
            rca_lines = [
                f"#{item['rank']} {item['root_cause']} ({item['occurrences']} incidents, {item['percentage']}) on {item['primary_application']}"
                for item in leaderboard[:4]
            ]
            prompt = [
                {
                    "role": "system",
                    "content": "You are a Principal SRE. Provide a concise strategic assessment (under 90 words) of these top systemic causes and prioritize corrective actions."
                },
                {
                    "role": "user",
                    "content": f"User asked: {raw_query}\nTop ServiceNow Root Causes:\n" + "\n".join(rca_lines)
                }
            ]
            try:
                llm_rca = await llm_client.generate_chat_completion(prompt, temperature=0.1, max_tokens=180)
            except Exception:
                pass

        leaderboard_summary = "\n".join([
            f"- **#{item['rank']} {item['root_cause']}** ({item['occurrences']} incidents, {item['percentage']}) — App: *{item['primary_application']}*"
            for item in leaderboard[:5]
        ])

        if llm_rca:
            response_text = (
                f"**AI Root Cause Analysis & Prevention Strategy:**\n"
                f"{llm_rca.strip()}\n\n"
                f"**Leaderboard:**\n"
                f"{leaderboard_summary}"
            )
        else:
            response_text = f"**Most Common Root Causes Leaderboard (Live ServiceNow Data):**\n{leaderboard_summary}"
        suggestions = ["Identify recurring incidents and root causes", "Which applications generated the most incidents?", "Show incidents for MailServerUS", "Show all P1 critical incidents"]

    # 4. SINGLE INCIDENT SUMMARIZATION / DEEP DIVE
    elif intent == IntentDetector.INTENT_INCIDENT_SUMMARIZATION:
        match = re.search(r"(inc\d{5,8})", raw_query, re.IGNORECASE)
        target_num = match.group(1).upper() if match else context.get("last_incident_number")
        
        inc_detail = None
        if target_num:
            res = await servicenow_mcp_server.execute_tool("get_incident_detail", {"identifier": target_num})
            if res.get("found"):
                inc_detail = res.get("incident")
        
        if not inc_detail:
            recent = await servicenow_mcp_server.client.query_table("incident", limit=1)
            inc_detail = recent[0] if recent else None

        if inc_detail:
            summary_info = await InsightsEngine.summarize_single_incident(inc_detail)
            num = inc_detail.get("number", "Ticket")
            ci = inc_detail.get("cmdb_ci", "General System")
            prio = inc_detail.get("priority", 3)
            summary_content = summary_info.get("summary_text") or summary_info.get("summary", "")

            response_text = (
                f"**AI Incident Post-Mortem: {num}**\n"
                f"*{inc_detail.get('short_description', '')}*\n"
                f"- **Affected CI:** {ci} | **Priority:** P{prio} | **Engine:** {summary_info.get('source', 'LLM')}\n\n"
                f"{summary_content}"
            )
            structured_data = {
                "incident": inc_detail,
                "analysis": summary_info
            }
            suggestions = [f"Show incidents related to {ci}", "Show root causes", "Show all P1 critical incidents"]
        else:
            response_text = f"No incident records found matching '{raw_query}' in ServiceNow dev204434."
            suggestions = ["Show all P1 critical incidents", "How many incidents are currently open?"]

    # 5. SRE ADVISORY & TROUBLESHOOTING
    elif intent == IntentDetector.INTENT_SRE_ADVISORY:
        kpi_data = await analytics_mcp_server.execute_tool("calculate_kpis", {})
        recent_p1 = await servicenow_mcp_server.client.query_table("incident", sysparm_query="priority=1", limit=3)
        p1_summary = ", ".join([f"{i.get('number')}: {i.get('short_description')}" for i in recent_p1]) or "None"

        prompt = [
            {
                "role": "system",
                "content": (
                    "You are a Principal Site Reliability Engineer and ServiceNow Architect. "
                    "Provide an authoritative, direct, and actionable technical recommendation (under 110 words) "
                    "answering the user's inquiry based on the ServiceNow environment context."
                )
            },
            {
                "role": "user",
                "content": (
                    f"User Query: {raw_query}\n"
                    f"Live ServiceNow Context:\n"
                    f"- Total Incidents: {kpi_data.get('total_incidents')}, Open: {kpi_data.get('open_incidents')}, MTTR: {kpi_data.get('mttr_hours')}h\n"
                    f"- SLA Adherence: {kpi_data.get('sla_compliance_rate')}%\n"
                    f"- Recent Critical Incidents: {p1_summary}"
                )
            }
        ]
        llm_advice = None
        try:
            llm_advice = await llm_client.generate_chat_completion(prompt, temperature=0.1, max_tokens=220)
        except Exception:
            pass

        if llm_advice:
            response_text = f"**SRE Operational Advisory (AI Analysis):**\n\n{llm_advice.strip()}"
        else:
            response_text = (
                f"**ServiceNow ITIL Best Practices Advisory:**\n"
                f"Based on current metrics ({kpi_data.get('open_incidents', 0)} open incidents, MTTR {kpi_data.get('mttr_hours', 0)}h):\n"
                f"1. Implement proactive automated alert thresholds on impacted services.\n"
                f"2. Link repeat incidents to parent Problem records for root-cause tracking.\n"
                f"3. Establish automated routing to specialized assignment groups to minimize MTTR."
            )
        structured_data = {"kpis": kpi_data}
        suggestions = ["Identify recurring incidents and root causes", "Show all P1 critical incidents", "How many incidents are currently open?"]

    # 6. PROBLEM MANAGEMENT LOOKUP & ANALYSIS (SERVICENOW TOOL: query_problems)
    elif intent == IntentDetector.INTENT_PROBLEM_LOOKUP:
        prb_match = re.search(r"(prb\d{5,8})", raw_query, re.IGNORECASE)
        prb_filter = f"number={prb_match.group(1).upper()}" if prb_match else ""
        problem_data = await servicenow_mcp_server.execute_tool("query_problems", {"sysparm_query": prb_filter})
        problems = problem_data.get("problems", [])
        structured_data = problem_data
        records_count = len(problems)

        prb_lines = [
            f"- **{p.get('number', 'PRB')}**: {p.get('short_description', 'N/A')} (State: {p.get('state', 'Open')}, CI: {p.get('cmdb_ci', 'General')})"
            for p in problems[:5]
        ]

        llm_prb = None
        if problems:
            prompt = [
                {
                    "role": "system",
                    "content": "You are a Principal Problem Manager. Provide a concise technical assessment (under 85 words) of these ServiceNow problem records and permanent resolution roadmap."
                },
                {
                    "role": "user",
                    "content": f"User Query: {raw_query}\nProblems:\n" + "\n".join(prb_lines)
                }
            ]
            try:
                llm_prb = await llm_client.generate_chat_completion(prompt, temperature=0.1, max_tokens=180)
            except Exception:
                pass

        if llm_prb:
            response_text = (
                f"**ServiceNow Problem Management Intelligence:**\n"
                f"{llm_prb.strip()}\n\n"
                f"**Tracked Problem Records ({len(problems)} found in dev204434):**\n" + "\n".join(prb_lines)
            )
        else:
            response_text = (
                f"**ServiceNow Problem Records ({len(problems)} found in dev204434):**\n" + "\n".join(prb_lines)
            )
        suggestions = ["Show all P1 critical incidents", "Identify recurring incidents and root causes", "Give RCA summary"]

    # 7. CMDB CONFIGURATION ITEMS LOOKUP & ANALYSIS (SERVICENOW TOOL: query_cmdb_ci)
    elif intent == IntentDetector.INTENT_CMDB_LOOKUP:
        ci_keyword = None
        for kw in QueryTranslator.CI_KEYWORDS:
            if kw in raw_query.lower():
                ci_keyword = kw
                break

        cmdb_filter = f"nameLIKE{ci_keyword}" if ci_keyword else ""
        cmdb_data = await servicenow_mcp_server.execute_tool("query_cmdb_ci", {"sysparm_query": cmdb_filter})
        cis = cmdb_data.get("configuration_items", [])
        structured_data = cmdb_data
        records_count = len(cis)

        ci_lines = [
            f"- **{c.get('name', 'CI')}** ({c.get('sys_class_name', 'cmdb_ci')}) - Operational: {c.get('operational_status', 'Operational')}"
            for c in cis[:6]
        ]

        llm_cmdb = None
        if cis:
            prompt = [
                {
                    "role": "system",
                    "content": "You are an Enterprise Infrastructure Architect. Analyze these ServiceNow CMDB Configuration Items (under 80 words) and highlight infrastructure criticality and dependencies."
                },
                {
                    "role": "user",
                    "content": f"User Query: {raw_query}\nCIs:\n" + "\n".join(ci_lines)
                }
            ]
            try:
                llm_cmdb = await llm_client.generate_chat_completion(prompt, temperature=0.1, max_tokens=170)
            except Exception:
                pass

        if llm_cmdb:
            response_text = (
                f"**CMDB Infrastructure Intelligence:**\n"
                f"{llm_cmdb.strip()}\n\n"
                f"**Live Configuration Items ({len(cis)} items found in dev204434):**\n" + "\n".join(ci_lines)
            )
        else:
            response_text = (
                f"**Live Configuration Items ({len(cis)} items found in dev204434):**\n" + "\n".join(ci_lines)
            )
        suggestions = ["Show incidents for MailServerUS", "Which applications generated the most incidents?", "Show all P1 critical incidents"]

    # 8. GENERAL GREETING / CAPABILITIES GUIDE
    elif intent == IntentDetector.INTENT_GENERAL:
        provider_name = llm_client.active_provider.upper() if llm_client.is_available() else "DETERMINISTIC SRE"
        model_name = llm_client.active_model
        response_text = (
            f"👋 **Hello! I am your AI SRE Assistant for ServiceNow.**\n\n"
            f"Powered by **{provider_name}** (`{model_name}`) and live ServiceNow MCP tools connected to **dev204434**.\n\n"
            f"**Here is what I can analyze and execute for you:**\n"
            f"1. 🔍 **Live Incident Queries:** *'Show all P1 critical incidents'* or *'Incidents for MailServerUS'*.\n"
            f"2. ⚡ **Major Outage Post-Mortems:** *'Investigate latest outage'* or *'Summarize INC0000001'* for instant AI post-mortems.\n"
            f"3. 🔄 **Recurring Incident Clustering:** *'Identify recurring incidents and root causes'*.\n"
            f"4. 📊 **Root Cause Analysis (RCA):** *'Give RCA leaderboard'* or *'Top systemic causes'*.\n"
            f"5. 🛠️ **Problem & CMDB Tracking:** *'Show open problem tickets'* or *'Show CMDB configuration items'*.\n"
            f"6. 📈 **SRE Advisory & KPIs:** *'How can we improve MTTR?'* or *'What are our operational KPIs?'*."
        )
        suggestions = [
            "Show all P1 critical incidents",
            "Identify recurring incidents and root causes",
            "Summarize INC0000001",
            "Show open problem tickets"
        ]

    # 9. APPLICATION ANALYTICS (SERVICENOW & MCP ANALYTICS)
    elif intent == IntentDetector.INTENT_APPLICATION_ANALYTICS:
        app_data = await analytics_mcp_server.execute_tool("get_application_analytics", {"top_n": 6})
        structured_data = app_data
        apps = app_data.get("top_applications", [])
        app_summary = "\n".join([f"{idx}. **{a['name']}** — {a['total']} incidents (P1: {a['p1']}, P2: {a['p2']})" for idx, a in enumerate(apps, 1)])

        llm_app = None
        if apps:
            prompt = [
                {
                    "role": "system",
                    "content": "You are a Principal SRE. Synthesize these application incident volumes into a concise operational risk evaluation (under 75 words) and recommend 1 preventive action."
                },
                {
                    "role": "user",
                    "content": f"User Query: {raw_query}\nApplications:\n" + app_summary
                }
            ]
            try:
                llm_app = await llm_client.generate_chat_completion(prompt, temperature=0.1, max_tokens=160)
            except Exception:
                pass

        if llm_app:
            response_text = (
                f"**Top Affected Applications / CIs (Live ServiceNow Data):**\n"
                f"{app_summary}\n\n"
                f"**AI Risk Evaluation:**\n{llm_app.strip()}"
            )
        else:
            response_text = f"**Top Affected Applications / CIs (Live ServiceNow Data):**\n{app_summary}"
        suggestions = ["Give RCA summary", "Show all P1 critical incidents", "How many incidents are currently open?"]

    # 10. METRICS & KPI QUERY (SERVICENOW & MCP ANALYTICS)
    elif intent == IntentDetector.INTENT_METRICS_KPI:
        kpi_data = await analytics_mcp_server.execute_tool("calculate_kpis", {})
        structured_data = kpi_data
        base_kpi = (
            f"**Incident Operational Metrics (Live ServiceNow dev204434):**\n"
            f"- **Currently Open:** {kpi_data.get('open_incidents', 0)}\n"
            f"- **Closed/Resolved:** {kpi_data.get('closed_incidents', 0)}\n"
            f"- **Total Monitored:** {kpi_data.get('total_incidents', 0)}\n"
            f"- **P1 Critical:** {kpi_data.get('critical_incidents', 0)}\n"
            f"- **SLA Compliance:** {kpi_data.get('sla_compliance_rate', 0)}%\n"
            f"- **MTTR:** {kpi_data.get('mttr_hours', 0)} hours | **MTBF:** {kpi_data.get('mtbf_hours', 0)} hours"
        )

        llm_kpi = None
        prompt = [
            {
                "role": "system",
                "content": "You are an IT Operations Director. Provide a concise operational posture assessment (under 70 words) evaluating SLA compliance and MTTR health based on these ServiceNow metrics."
            },
            {
                "role": "user",
                "content": f"KPIs: Open={kpi_data.get('open_incidents')}, P1={kpi_data.get('critical_incidents')}, SLA={kpi_data.get('sla_compliance_rate')}%, MTTR={kpi_data.get('mttr_hours')}h, MTBF={kpi_data.get('mtbf_hours')}h"
            }
        ]
        try:
            llm_kpi = await llm_client.generate_chat_completion(prompt, temperature=0.1, max_tokens=150)
        except Exception:
            pass

        if llm_kpi:
            response_text = f"{base_kpi}\n\n**AI Executive Assessment:**\n{llm_kpi.strip()}"
        else:
            response_text = base_kpi
        suggestions = ["Show all P1 critical incidents", "List all incidents assigned to Service Desk", "Identify recurring incidents and root causes"]

    # 11. REPORT GENERATION
    elif intent == IntentDetector.INTENT_REPORT_GENERATION:
        report_data = await reporting_mcp_server.execute_tool("generate_executive_report", {"period_title": "Executive Performance Review"})
        structured_data = report_data
        response_text = (
            f"**Executive Report Generated (ServiceNow dev204434):**\n"
            f"{report_data.get('executive_summary', '')}\n\n"
            f"You can download the full formatted report using the Export buttons below (PDF, Word, Excel)."
        )
        suggestions = ["Export to PDF", "Show top affected applications", "Show root causes by application"]

    # 7. DEFAULT: QUERY INCIDENTS WITH NATURAL LANGUAGE TO SERVICENOW TRANSLATION
    else:
        query_info = QueryTranslator.translate(raw_query, context)
        sysparm_query = query_info["sysparm_query"]
        filters = query_info["applied_filters"]
        
        # Execute via ServiceNow MCP tool
        result = await servicenow_mcp_server.execute_tool("query_incidents", {"sysparm_query": sysparm_query, "limit": 50})
        incidents = result.get("incidents", [])
        records_count = len(incidents)

        # Synthesize structured format
        insights = await InsightsEngine.synthesize_incident_query_response(raw_query, incidents, filters)
        response_text = insights["text"]
        applied_filters = filters
        retrieved_incidents = incidents
        structured_data = {
            **insights["structured"],
            "generated_query": sysparm_query,
            "applied_filters": filters,
            "explanation": query_info.get("explanation")
        }

        # Context-relevant suggestions
        if records_count == 0:
            suggestions = ["Show all P1 critical incidents", "How many incidents are currently open?", "List all incidents assigned to Service Desk", "Show incidents for MailServerUS"]
        elif "p1" in raw_query.lower() or "critical" in raw_query.lower():
            suggestions = ["Which applications generated the most incidents?", "Give RCA summary", "List all incidents assigned to Service Desk"]
        else:
            suggestions = ["Show all P1 critical incidents", "How many incidents are currently open?", "Identify recurring incidents and root causes"]

    # UNIFIED SESSION MEMORY POST-PROCESSING:
    # Record conversational turn across ALL intents (unless this turn was an explicit session reset)
    if intent != IntentDetector.INTENT_RESET_SESSION:
        target_inc = None
        target_ci = None
        if structured_data and isinstance(structured_data, dict):
            target_inc = structured_data.get("ticket_number") or structured_data.get("incident_number")
            if isinstance(structured_data.get("incident"), dict):
                target_inc = target_inc or structured_data["incident"].get("number")
                target_ci = target_ci or structured_data["incident"].get("cmdb_ci")

        session.add_interaction(
            user_text=raw_query,
            assistant_text=response_text,
            intent=intent,
            filters=applied_filters,
            results=retrieved_incidents,
            incident_number=target_inc,
            ci=target_ci
        )

    exec_time = int((time.time() - start_time) * 1000)

    # Log to audit table
    try:
        audit_entry = AuditLog(
            natural_query=raw_query,
            generated_query=sysparm_query,
            status="SUCCESS",
            execution_time_ms=exec_time,
            records_returned=records_count
        )
        db.add(audit_entry)
        await db.commit()
    except Exception:
        pass

    return ChatResponse(
        session_id=session_id,
        intent=intent,
        sysparm_query=sysparm_query,
        response_text=response_text,
        structured_data=structured_data,
        execution_time_ms=exec_time,
        suggestions=suggestions
    )
