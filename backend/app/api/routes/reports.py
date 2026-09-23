from fastapi import APIRouter, Response, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.mcp.reporting_mcp import reporting_mcp_server

router = APIRouter(prefix="/api/reports", tags=["Reports"])

class GenerateReportRequest(BaseModel):
    period_title: str = "August 2026 Incident Performance Review"
    filter_query: Optional[str] = ""

@router.post("/generate")
async def generate_report(req: GenerateReportRequest) -> Dict[str, Any]:
    """Generates a structured executive report."""
    return await reporting_mcp_server.build_report(req.period_title, req.filter_query or "")

@router.post("/export/{doc_format}")
async def export_report(doc_format: str, report_payload: Dict[str, Any]):
    """Exports executive report data to PDF, DOCX, or XLSX binary download."""
    fmt = doc_format.lower()
    if fmt not in ["pdf", "docx", "xlsx"]:
        raise HTTPException(status_code=400, detail="Invalid format. Supported: pdf, docx, xlsx")

    try:
        stream = reporting_mcp_server.export_document(fmt, report_payload)
        content = stream.getvalue()

        media_types = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }

        period_slug = report_payload.get("period", "Executive_Report").replace(" ", "_")
        filename = f"Incident_Report_{period_slug}.{fmt}"

        return Response(
            content=content,
            media_type=media_types[fmt],
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(ex)}")
