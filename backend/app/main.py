import os
import time
import asyncio
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, Response

from backend.app.models import RubixExtractedData, GenerateDocxRequest
from backend.app.parser import parse_rubix_pdf
from backend.app.generator import build_crif_docx
from backend.app.database import init_db, save_appraisal, get_all_appraisals, get_appraisal_by_id, get_appraisals_count

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("credit_crm")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BACKEND_DIR)
STORAGE_DIR = os.path.join(BACKEND_DIR, 'storage')
UPLOADS_DIR = os.path.join(STORAGE_DIR, 'uploads')
MEMOS_DIR = os.path.join(STORAGE_DIR, 'memos')

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(MEMOS_DIR, exist_ok=True)

# Retention Policies:
# - Auto-delete PDFs from storage every 3 hours
# - Auto-delete saved DOCX files weekly (7 days)
PDF_RETENTION_SECONDS = 3 * 3600
DOCX_RETENTION_SECONDS = 7 * 24 * 3600
CLEANUP_CHECK_INTERVAL = 1800  # Check every 30 minutes

def prune_storage_files():
    """Removes temporary PDFs older than 3 hours and saved DOCX memos older than 7 days."""
    now = time.time()
    pruned_pdfs = 0
    pruned_docs = 0

    if os.path.exists(UPLOADS_DIR):
        for fname in os.listdir(UPLOADS_DIR):
            fpath = os.path.join(UPLOADS_DIR, fname)
            if os.path.isfile(fpath) and fname.lower().endswith('.pdf'):
                try:
                    if (now - os.path.getmtime(fpath)) > PDF_RETENTION_SECONDS:
                        os.remove(fpath)
                        pruned_pdfs += 1
                except OSError as e:
                    logger.warning(f"Failed to remove expired PDF {fname}: {e}")

    if os.path.exists(MEMOS_DIR):
        for fname in os.listdir(MEMOS_DIR):
            fpath = os.path.join(MEMOS_DIR, fname)
            if os.path.isfile(fpath) and fname.lower().endswith('.docx'):
                try:
                    if (now - os.path.getmtime(fpath)) > DOCX_RETENTION_SECONDS:
                        os.remove(fpath)
                        pruned_docs += 1
                except OSError as e:
                    logger.warning(f"Failed to remove expired DOCX memo {fname}: {e}")

    if pruned_pdfs > 0 or pruned_docs > 0:
        logger.info(f"Storage retention cleanup complete: pruned {pruned_pdfs} PDFs (3h+), {pruned_docs} DOCXs (7d+)")
    return {"pruned_pdfs": pruned_pdfs, "pruned_docs": pruned_docs}

async def storage_cleanup_worker():
    """Continuous background worker running periodic retention cleanup."""
    while True:
        try:
            prune_storage_files()
        except Exception as e:
            logger.error(f"Error in storage cleanup worker: {e}", exc_info=True)
        await asyncio.sleep(CLEANUP_CHECK_INTERVAL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Initial cleanup pass on server start
    prune_storage_files()
    # Start background cleanup worker
    cleanup_task = asyncio.create_task(storage_cleanup_worker())
    yield
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

app = FastAPI(title="Jet Freight Logistics - Credit Control CRM", version="1.0.0", lifespan=lifespan)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# CORS setup - stateless API without session cookies
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip Compression for payloads over 1KB
app.add_middleware(GZipMiddleware, minimum_size=1000)

MAX_UPLOAD_SIZE = 25 * 1024 * 1024  # 25 MB max
PDF_MAGIC_BYTES = b"%PDF-"

@app.get("/api/health")
def health():
    return {"status": "ok", "app": "Jet Freight Logistics Credit CRM", "timestamp": datetime.now().isoformat()}

@app.post("/api/extract", response_model=RubixExtractedData)
async def extract_pdf(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are supported.")
    
    # Verify PDF magic bytes (%PDF-)
    header_bytes = await file.read(5)
    await file.seek(0)
    if not header_bytes.startswith(PDF_MAGIC_BYTES):
        raise HTTPException(status_code=400, detail="Invalid PDF structure: Magic bytes '%PDF-' missing.")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = os.path.basename(file.filename or "upload.pdf")
    safe_filename = f"{timestamp}_{safe_name}"
    upload_path = os.path.join(UPLOADS_DIR, safe_filename)
    
    # Stream with size limit
    size = 0
    try:
        with open(upload_path, "wb") as buffer:
            while chunk := await file.read(1024 * 64): # 64KB chunks
                size += len(chunk)
                if size > MAX_UPLOAD_SIZE:
                    buffer.close()
                    if os.path.exists(upload_path):
                        os.remove(upload_path)
                    raise HTTPException(status_code=413, detail="File too large. Maximum upload size is 25MB.")
                buffer.write(chunk)
            
        try:
            extracted = parse_rubix_pdf(upload_path)
            extracted['appraisal_date'] = datetime.now().strftime("%d/%m/%Y")
            extracted['salesperson'] = extracted.get('salesperson') or "Snehal Birje"
            return extracted
        except Exception as e:
            logger.error(f"Error parsing PDF {upload_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to parse Rubix PDF. Ensure file is not corrupted or password-protected.")
    finally:
        # Cleanup temporary uploaded PDF to prevent unbounded disk growth
        if os.path.exists(upload_path):
            try:
                os.remove(upload_path)
            except OSError:
                pass

@app.post("/api/generate")
async def generate_docx(req: GenerateDocxRequest):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_name = "".join(c for c in req.customer_name if c.isalnum() or c in (' ', '_', '-')).strip() or "CUSTOMER"
        filename = f"CRIF_MEMO_{clean_name}_{timestamp}.docx"
        output_path = os.path.join(MEMOS_DIR, filename)
        
        # Prepare dict for generator
        payload = req.model_dump() if hasattr(req, "model_dump") else req.dict()
        build_crif_docx(payload, output_path)
        
        appraisal_id = save_appraisal(
            customer_name=req.customer_name,
            crif_credit_limit=req.crif_credit_limit,
            credit_days=req.credit_days,
            salesperson=req.salesperson,
            type_of_company=req.type_of_company,
            risk_grade=req.risk_grade_score,
            docx_filename=filename,
            source_pdf=req.source_pdf
        )
        
        return {
            "success": True,
            "appraisal_id": appraisal_id,
            "filename": filename,
            "download_url": f"/api/download/{appraisal_id}"
        }
    except Exception as e:
        logger.error(f"Failed to generate CRIF docx: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate CRIF memorandum document.")

@app.api_route("/api/download/{appraisal_id}", methods=["GET", "HEAD"])
def download_docx(appraisal_id: int):
    record = get_appraisal_by_id(appraisal_id)
    if not record:
        raise HTTPException(status_code=404, detail="Appraisal record not found")
        
    file_path = os.path.join(MEMOS_DIR, record['docx_filename'])
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail="Document has expired and been removed per the weekly retention policy."
        )
        
    return FileResponse(
        path=file_path,
        filename=record['docx_filename'],
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

@app.post("/api/maintenance/cleanup")
def trigger_maintenance_cleanup():
    stats = prune_storage_files()
    return {
        "status": "ok",
        "retention_policy": {
            "pdf": "Auto-deleted after 3 hours",
            "docx": "Auto-deleted weekly (7 days)"
        },
        "pruned": stats,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/appraisals")
def list_appraisals(response: Response, limit: int = 200, offset: int = 0):
    total = get_appraisals_count()
    response.headers["X-Total-Count"] = str(total)
    return get_all_appraisals(limit=min(limit, 500), offset=max(0, offset))

@app.api_route("/logo.jpeg", methods=["GET", "HEAD"], include_in_schema=False)
@app.api_route("/favicon.ico", methods=["GET", "HEAD"], include_in_schema=False)
def get_brand_logo():
    logo_path = os.path.join(ROOT_DIR, "jfll-logo.jpeg")
    if os.path.exists(logo_path):
        return FileResponse(
            logo_path,
            media_type="image/jpeg",
            headers={"Cache-Control": "public, max-age=86400, immutable"}
        )
    raise HTTPException(status_code=404, detail="Logo not found")
