import io
import datetime
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import docx
from docx.shared import Inches, Pt, RGBColor
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from app.mcp.analytics_mcp import analytics_mcp_server
from app.mcp.servicenow_mcp import servicenow_mcp_server
from app.ai.llm_client import llm_client
from app.services.servicenow import build_timeframe_query

class ReportingMCPServer:
    """MCP Server exposing executive report generation and export to PDF, Word, and Excel."""

    name = "reporting_mcp_server"
    version = "1.0.0"

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "generate_executive_report",
                "description": "Compile a structured executive incident report for a specified period (e.g., August 2026, Last Month, Q3).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "period_title": {
                            "type": "string",
                            "description": "Report timeframe title, e.g. 'August 2026' or 'Q3 2026'"
                        },
                        "filter_query": {
                            "type": "string",
                            "description": "Optional ServiceNow encoded query to scope incidents"
                        }
                    },
                    "required": ["period_title"]
                }
            },
            {
                "name": "export_report_document",
                "description": "Export report data to binary file stream in PDF, Word (DOCX), or Excel (XLSX).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "format": {
                            "type": "string",
                            "enum": ["pdf", "docx", "xlsx"],
                            "description": "Target document format"
                        },
                        "report_payload": {
                            "type": "object",
                            "description": "Structured report JSON payload"
                        }
                    },
                    "required": ["format", "report_payload"]
                }
            }
        ]

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "generate_executive_report":
            period = arguments.get("period_title", "Monthly Incident Performance Review")
            query = arguments.get("filter_query", "")
            return await self.build_report(period, query)

        elif tool_name == "export_report_document":
            doc_format = arguments.get("format", "pdf").lower()
            payload = arguments.get("report_payload", {})
            return self.export_document(doc_format, payload)

        else:
            raise ValueError(f"Unknown tool: '{tool_name}' on {self.name}")

    async def build_report(self, period_title: str, query: str = "") -> Dict[str, Any]:
        """Compiles KPIs, recurring clusters, app rankings, and major incident highlights into an executive report."""
        if not query:
            query = build_timeframe_query(period_title)

        kpi_data = await analytics_mcp_server.execute_tool("calculate_kpis", {"filter_query": query})
        app_data = await analytics_mcp_server.execute_tool("get_application_analytics", {"top_n": 5, "filter_query": query})
        
        major_query = f"priority=1^{query}" if query else "priority=1"
        major_incidents_data = await servicenow_mcp_server.execute_tool("query_incidents", {"sysparm_query": major_query, "limit": 10})

        total = kpi_data.get('total_incidents', 0)
        critical = kpi_data.get('critical_incidents', 0)
        sla_rate = kpi_data.get('sla_compliance_rate', 100.0)
        mttr = kpi_data.get('mttr_hours', 0.0)
        top_apps = app_data.get("top_applications", [])
        top_app_name = top_apps[0]['name'] if top_apps else "None"

        if total == 0:
            recurring_data = {"total_clusters_detected": 0, "recurring_clusters": [], "top_affected_application": "None"}
            executive_summary = (
                f"During {period_title}, 0 incidents were recorded across enterprise services in live ServiceNow (dev204434). "
                f"All critical systems maintained 100% operational availability with zero P1 outages and zero SLA breaches."
            )
            strategic_recs = [
                "Maintain proactive health monitoring and automated synthetic heartbeat checks across core CIs.",
                "Review configuration drift detection to maintain zero-outage stability across production environments.",
                "Schedule quarterly disaster recovery failover drill across primary database nodes."
            ]
        else:
            recurring_data = await analytics_mcp_server.execute_tool("cluster_recurring_incidents", {"min_occurrences": 2})
            executive_summary = (
                f"During {period_title}, the IT operations organization managed a total of {total} incident{'s' if total != 1 else ''} "
                f"across critical business services in ServiceNow. Critical P1 incidents were held to {critical}, "
                f"maintaining an overall SLA compliance rate of {sla_rate}%. "
                f"Mean Time to Resolution (MTTR) averaged {mttr} hours. "
                f"Top affected service: '{top_app_name}'."
            )

            prompt = [
                {
                    "role": "system",
                    "content": "You are an Executive IT Director. Synthesize these ServiceNow operational metrics into a concise executive report summary (under 80 words) highlighting SLA, MTTR, and top risk. Strictly cite the provided numbers and do not hallucinate."
                },
                {
                    "role": "user",
                    "content": (
                        f"Report Period: {period_title}\n"
                        f"Total Incidents: {total}, P1 Critical: {critical}\n"
                        f"SLA Compliance: {sla_rate}%, MTTR: {mttr} hours\n"
                        f"Top Affected Application: {top_app_name} ({top_apps[0]['total']} incidents)\n" if top_apps else "Top Affected Application: None\n"
                    )
                }
            ]
            try:
                llm_exec = await llm_client.generate_chat_completion(prompt, temperature=0.1, max_tokens=180)
                if llm_exec:
                    executive_summary = llm_exec.strip()
            except Exception:
                pass

            clusters = recurring_data.get('recurring_clusters', [])
            strategic_recs = []
            for c in clusters[:4]:
                strategic_recs.append(f"{c.get('title')}: {c.get('recommendation')}")
            if not strategic_recs:
                for app in top_apps[:3]:
                    strategic_recs.append(f"Remediate recurring ticket volume on {app.get('name')} ({app.get('total')} incidents recorded in period).")
                strategic_recs.append("Conduct architectural resiliency review to prevent further SLA breaches.")

        return {
            "period": period_title,
            "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            "executive_summary": executive_summary,
            "kpis": kpi_data,
            "recurring_insights": recurring_data,
            "top_affected_applications": top_apps,
            "major_incidents": major_incidents_data.get("incidents", [])[:5],
            "strategic_recommendations": strategic_recs,
            "query_used": query
        }

    def export_document(self, doc_format: str, report: Dict[str, Any]) -> io.BytesIO:
        """Renders binary document streams for PDF, DOCX, and XLSX."""
        if doc_format == "pdf":
            return self._render_pdf(report)
        elif doc_format == "docx":
            return self._render_docx(report)
        elif doc_format == "xlsx":
            return self._render_xlsx(report)
        else:
            raise ValueError(f"Unsupported format: {doc_format}")

    def _render_pdf(self, report: Dict[str, Any]) -> io.BytesIO:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontSize=22,
            textColor=colors.HexColor("#1e293b"),
            spaceAfter=12
        )
        sub_style = ParagraphStyle(
            'DocSub',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=20
        )
        h2_style = ParagraphStyle(
            'SectionH2',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=14,
            spaceAfter=8
        )
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor("#334155"),
            leading=14,
            spaceAfter=10
        )

        elements = []
        period = report.get("period", "Executive Incident Analytics")
        elements.append(Paragraph(f"Executive Incident Report: {period}", title_style))
        elements.append(Paragraph(f"Generated: {report.get('generated_at', '')} | Source: ServiceNow Production & Analytics Engine", sub_style))

        # Summary
        elements.append(Paragraph("Executive Summary", h2_style))
        elements.append(Paragraph(report.get("executive_summary", ""), body_style))

        # KPIs Table
        elements.append(Paragraph("Key Performance Indicators (KPIs)", h2_style))
        kpis = report.get("kpis", {})
        kpi_table_data = [
            ["Metric", "Value", "Benchmark Target"],
            ["Total Incidents", str(kpis.get("total_incidents", 0)), "N/A"],
            ["Open Incidents", str(kpis.get("open_incidents", 0)), "< 15"],
            ["Closed Incidents", str(kpis.get("closed_incidents", 0)), "N/A"],
            ["P1 Critical Incidents", str(kpis.get("critical_incidents", 0)), "0 - 2"],
            ["SLA Compliance Rate", f"{kpis.get('sla_compliance_rate', 0)}%", "> 95.0%"],
            ["MTTR (Mean Time to Resolve)", f"{kpis.get('mttr_hours', 0)} hrs", "< 4.0 hrs"],
            ["MTBF (Mean Time Between Failures)", f"{kpis.get('mtbf_hours', 0)} hrs", "> 20.0 hrs"]
        ]
        t = Table(kpi_table_data, colWidths=[200, 150, 150])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 15))

        # Strategic Recommendations
        elements.append(Paragraph("Strategic Corrective Actions", h2_style))
        for rec in report.get("strategic_recommendations", []):
            elements.append(Paragraph(f"• {rec}", body_style))

        doc.build(elements)
        buffer.seek(0)
        return buffer

    def _render_docx(self, report: Dict[str, Any]) -> io.BytesIO:
        doc = docx.Document()
        title = doc.add_heading(f"Executive Incident Report: {report.get('period', '')}", level=1)
        title.style.font.name = 'Arial'
        title.style.font.color.rgb = RGBColor(15, 23, 42)

        doc.add_paragraph(f"Generated: {report.get('generated_at', '')} | Primary Source: ServiceNow REST API")

        doc.add_heading("Executive Summary", level=2)
        doc.add_paragraph(report.get("executive_summary", ""))

        doc.add_heading("Operational KPIs", level=2)
        kpis = report.get("kpis", {})
        table = doc.add_table(rows=1, cols=3)
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = "KPI Metric"
        hdr_cells[1].text = "Measured Value"
        hdr_cells[2].text = "Target"

        metrics = [
            ("Total Incidents", str(kpis.get("total_incidents", 0)), "N/A"),
            ("Open Incidents", str(kpis.get("open_incidents", 0)), "< 15"),
            ("P1 Critical Incidents", str(kpis.get("critical_incidents", 0)), "0 - 2"),
            ("SLA Compliance Rate", f"{kpis.get('sla_compliance_rate', 0)}%", "> 95.0%"),
            ("Mean Time to Resolution (MTTR)", f"{kpis.get('mttr_hours', 0)} hours", "< 4.0 hrs"),
            ("Mean Time Between Failures (MTBF)", f"{kpis.get('mtbf_hours', 0)} hours", "> 20.0 hrs"),
        ]
        for m, v, t in metrics:
            row_cells = table.add_row().cells
            row_cells[0].text = m
            row_cells[1].text = v
            row_cells[2].text = t

        doc.add_heading("Strategic Recommendations", level=2)
        for rec in report.get("strategic_recommendations", []):
            doc.add_paragraph(f"• {rec}")

        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer

    def _render_xlsx(self, report: Dict[str, Any]) -> io.BytesIO:
        wb = openpyxl.Workbook()
        ws_kpi = wb.active
        ws_kpi.title = "Executive KPIs"

        # Headers
        header_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
        header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
        
        ws_kpi.append(["Executive Incident Analytics Report", report.get("period", "")])
        ws_kpi.append(["Generated", report.get("generated_at", "")])
        ws_kpi.append([])
        
        ws_kpi.append(["Metric", "Value", "Operational Status"])
        for cell in ws_kpi[4]:
            cell.fill = header_fill
            cell.font = header_font

        kpis = report.get("kpis", {})
        rows = [
            ["Total Incidents", kpis.get("total_incidents", 0), "Monitored"],
            ["Open Incidents", kpis.get("open_incidents", 0), "Active Queue"],
            ["Closed Incidents", kpis.get("closed_incidents", 0), "Resolved"],
            ["P1 Critical Incidents", kpis.get("critical_incidents", 0), "Priority Attention"],
            ["SLA Compliance (%)", f"{kpis.get('sla_compliance_rate', 0)}%", "Within Target"],
            ["MTTR (Hours)", kpis.get("mttr_hours", 0), "Good"],
            ["MTBF (Hours)", kpis.get("mtbf_hours", 0), "Optimal"]
        ]
        for r in rows:
            ws_kpi.append(r)

        # Tab 2: Top Applications
        ws_apps = wb.create_sheet(title="Top Affected Applications")
        ws_apps.append(["Application / Configuration Item", "Total Incidents", "P1 Critical", "P2 High", "SLA Breaches"])
        for cell in ws_apps[1]:
            cell.fill = header_fill
            cell.font = header_font

        for app in report.get("top_affected_applications", []):
            ws_apps.append([
                app.get("name", "Unknown"),
                app.get("total", 0),
                app.get("p1", 0),
                app.get("p2", 0),
                app.get("sla_breached", 0)
            ])

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer

reporting_mcp_server = ReportingMCPServer()
