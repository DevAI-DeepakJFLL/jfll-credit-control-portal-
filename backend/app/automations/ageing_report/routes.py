"""
FastAPI Routes for Accounts Receivable Ageing Report Automation.
Mounted under /api/ageing
"""
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Response
from fastapi.responses import StreamingResponse

from backend.app.automations.ageing_report.models import (
    AgeingBatchSummary,
    UpdateCustomerRequest
)
from backend.app.automations.ageing_report.service import (
    process_ageing_upload,
    get_all_batches,
    get_batch_summary,
    get_batch_customers,
    update_customer_followup,
    export_batch_excel
)

router = APIRouter()

@router.post("/upload")
async def upload_ageing_file(file: UploadFile = File(...)):
    """
    Ingests raw ERP Accounts Receivable ledger (.xlsx / .xlsm), parses voucher lines,
    computes aging brackets & freight IATA tenors, persists batch, and returns executive KPIs.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing")

    clean_name = file.filename.lower()
    if not (clean_name.endswith(".xlsx") or clean_name.endswith(".xlsm")):
        raise HTTPException(status_code=400, detail="Only Excel (.xlsx, .xlsm) files are supported for Ageing Report.")

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        batch_uuid, summary = process_ageing_upload(file_bytes, file.filename)
        return {
            "status": "success",
            "batch_uuid": batch_uuid,
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process Ageing file: {str(e)}")

@router.get("/batches")
def list_ageing_batches():
    """Lists historical ageing processing runs."""
    return get_all_batches()

@router.get("/summary/{batch_uuid}")
def retrieve_batch_summary(batch_uuid: str):
    """Retrieves executive metrics, bucket breakdown, and branch/FU distributions."""
    summary = get_batch_summary(batch_uuid)
    if not summary:
        raise HTTPException(status_code=404, detail="Ageing batch not found.")
    return summary

@router.get("/customers/{batch_uuid}")
def list_batch_customers(
    batch_uuid: str,
    response: Response,
    branch: Optional[str] = Query(None),
    fu_person: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500)
):
    """
    Returns paginated debtor records for a batch with branch, FU Person, and keyword filtering.
    """
    offset = (page - 1) * page_size
    customers, total_count = get_batch_customers(
        batch_uuid=batch_uuid,
        branch=branch,
        fu_person=fu_person,
        search=search,
        limit=page_size,
        offset=offset
    )
    response.headers["X-Total-Count"] = str(total_count)
    return {
        "customers": customers,
        "total": total_count,
        "page": page,
        "page_size": page_size
    }

@router.patch("/customer/{customer_id}")
def update_debtor_followup(customer_id: int, request: UpdateCustomerRequest):
    """Updates follow-up person assignment, remark, or collected payment amount."""
    success = update_customer_followup(
        customer_id=customer_id,
        fu_person=request.fu_person,
        remark=request.remark,
        received=request.received
    )
    if not success:
        raise HTTPException(status_code=404, detail="Customer record not found or no fields updated.")
    return {"status": "success", "customer_id": customer_id}

@router.get("/export/{batch_uuid}")
def export_ageing_excel(batch_uuid: str):
    """
    Generates and streams FINAL AGEING REPORT.xlsx with native Excel formulas and Sheet2 summary.
    """
    excel_stream = export_batch_excel(batch_uuid)
    if not excel_stream:
        raise HTTPException(status_code=404, detail="Batch records not found for export.")

    filename = f"FINAL_AGEING_REPORT_{batch_uuid[:8]}.xlsx"
    return StreamingResponse(
        excel_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
