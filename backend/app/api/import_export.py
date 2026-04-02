"""
Import/Export API - Excel import/export endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.excel_service import ExcelService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/template", summary="Download Excel template")
async def download_template(current_user: User = Depends(get_current_user)):
    try:
        excel_service = ExcelService()
        output = excel_service.generate_template()
        filename = f"ipam_import_template_{datetime.now().strftime('%Y%m%d')}.xlsx"
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except Exception as e:
        logger.error(f"Failed to generate template: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate Excel template: {str(e)}")


@router.post("/import", summary="Import Excel data")
async def import_data(
    file: UploadFile = File(..., description="Excel file"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only .xlsx and .xls files are supported")

    try:
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    try:
        excel_service = ExcelService()
        result = excel_service.import_data(contents, db, current_user.id)

        success_count = result.get("success_count", 0)
        error_count = result.get("error_count", 0)
        errors = result.get("errors", [])

        if error_count > 0 and success_count == 0:
            return {
                "code": 400,
                "message": f"Import failed: {error_count} errors found",
                "data": {"success_count": 0, "error_count": error_count, "errors": errors}
            }

        return {
            "code": 200,
            "message": f"Import completed: {success_count} succeeded, {error_count} failed",
            "data": {"success_count": success_count, "error_count": error_count, "errors": errors}
        }
    except Exception as e:
        logger.error(f"Import failed: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.get("/export", summary="Export data to Excel")
async def export_data(
    export_type: str = "ip",
    segment_id: int = None,
    status_filter: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    valid_types = ["ip", "device", "segment"]
    if export_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid export type. Must be one of: {', '.join(valid_types)}")

    try:
        excel_service = ExcelService()
        output = excel_service.export_data(
            db=db,
            export_type=export_type,
            segment_id=segment_id,
            status_filter=status_filter
        )
        filename = f"ipam_export_{export_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
