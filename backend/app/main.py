import os
import time
import secrets
import asyncio
import logging
import threading
from collections import defaultdict
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, Response

from backend.app.models import RubixExtractedData, GenerateDocxRequest
from backend.app.parser import extract_bureau_pdf
from backend.app.generator import build_crif_docx
from backend.app.database import (
    init_db,
    save_appraisal,
    get_all_appraisals,
    get_appraisal_by_token_or_id,
    get_appraisals_count
)
from backend.app.s3_storage import upload_memo_to_s3, download_memo_from_s3, is_s3_enabled
from backend.app.automations.ageing_report.routes import router as ageing_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("credit_crm")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BACKEND_DIR)

# Detect AWS Lambda environment where only /tmp is writable
is_lambda = bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME") or os.getenv("LAMBDA_TASK_ROOT"))
DEFAULT_STORAGE_DIR = "/tmp/credit_crm/storage" if is_lambda else os.path.join(BACKEND_DIR, 'storage')
STORAGE_DIR = os.getenv("STORAGE_DIR", DEFAULT_STORAGE_DIR)
UPLOADS_DIR = os.getenv("UPLOADS_DIR", os.path.join(STORAGE_DIR, 'uploads'))
MEMOS_DIR = os.getenv("MEMOS_DIR", os.path.join(STORAGE_DIR, 'memos'))

_initialized = False

def ensure_initialized():
    """Guarantees directories and database tables exist across both serverful and serverless runtimes."""
    global _initialized
    if not _initialized:
        os.makedirs(UPLOADS_DIR, exist_ok=True)
        os.makedirs(MEMOS_DIR, exist_ok=True)
        init_db()
        _initialized = True

# Immediate initialization pass
ensure_initialized()

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
        try:
            with os.scandir(UPLOADS_DIR) as entries:
                for entry in entries:
                    if entry.is_file() and entry.name.lower().endswith('.pdf'):
                        try:
                            if (now - entry.stat().st_mtime) > PDF_RETENTION_SECONDS:
                                os.remove(entry.path)
                                pruned_pdfs += 1
                        except OSError as e:
                            logger.warning(f"Failed to remove expired PDF {entry.name}: {e}")
        except OSError as e:
            logger.warning(f"Failed to scan directory {UPLOADS_DIR}: {e}")

    if os.path.exists(MEMOS_DIR):
        try:
            with os.scandir(MEMOS_DIR) as entries:
                for entry in entries:
                    if entry.is_file() and entry.name.lower().endswith('.docx'):
                        try:
                            if (now - entry.stat().st_mtime) > DOCX_RETENTION_SECONDS:
                                os.remove(entry.path)
                                pruned_docs += 1
                        except OSError as e:
                            logger.warning(f"Failed to remove expired DOCX memo {entry.name}: {e}")
        except OSError as e:
            logger.warning(f"Failed to scan directory {MEMOS_DIR}: {e}")

    if pruned_pdfs > 0 or pruned_docs > 0:
        logger.info(f"Storage retention cleanup complete: pruned {pruned_pdfs} PDFs (3h+), {pruned_docs} DOCXs (7d+)")
    return {"pruned_pdfs": pruned_pdfs, "pruned_docs": pruned_docs}

async def storage_cleanup_worker():
    """Continuous background worker running periodic retention cleanup (server mode)."""
    while True:
        try:
            prune_storage_files()
        except Exception as e:
            logger.error(f"Error in storage cleanup worker: {e}", exc_info=True)
        await asyncio.sleep(CLEANUP_CHECK_INTERVAL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_initialized()
    # Initial cleanup pass on server start
    prune_storage_files()
    # In long-running server environments (Docker / EC2), run periodic retention loop
    cleanup_task = None
    if not is_lambda:
        cleanup_task = asyncio.create_task(storage_cleanup_worker())
    yield
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass

app = FastAPI(title="Jet Freight Logistics - Credit Control CRM", version="1.0.0", lifespan=lifespan)

# In-Memory IP Rate Limiter
_rate_limit_lock = threading.Lock()
_ip_request_timestamps = defaultdict(list)
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"

def check_rate_limit(request: Request, limit: int = RATE_LIMIT_PER_MINUTE, window: int = 60):
    ip = get_client_ip(request)
    now = time.time()
    with _rate_limit_lock:
        timestamps = _ip_request_timestamps[ip]
        cutoff = now - window
        active_timestamps = [t for t in timestamps if t > cutoff]
        _ip_request_timestamps[ip] = active_timestamps
        if len(active_timestamps) >= limit:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Maximum 30 requests per minute allowed."
            )
        _ip_request_timestamps[ip].append(now)

        # Periodic memory cleanup if many distinct client IPs accumulate
        if len(_ip_request_timestamps) > 1000:
            dead_ips = [k for k, v in _ip_request_timestamps.items() if not v or v[-1] <= cutoff]
            for k in dead_ips:
                del _ip_request_timestamps[k]

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    ensure_initialized()
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; object-src 'none'; frame-ancestors 'none';"
    )
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
    return response

# CORS setup for local development and container deployments.
# When running on AWS Lambda, CORS is handled directly by the Function URL infrastructure
# to avoid duplicate "Access-Control-Allow-Origin: *, *" headers.
if not is_lambda:
    default_origins = "http://localhost:3000,http://127.0.0.1:3000"
    ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", default_origins).split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# GZip Compression for payloads over 1KB
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Register Automation Routers
app.include_router(ageing_router, prefix="/api/ageing", tags=["Ageing Report"])

MAX_UPLOAD_SIZE = 25 * 1024 * 1024  # 25 MB max
PDF_MAGIC_BYTES = b"%PDF-"

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "app": "Jet Freight Logistics Credit CRM",
        "timestamp": datetime.now().isoformat(),
        "runtime": "AWS Lambda" if is_lambda else "Standard Container/Server",
        "s3_persistence": is_s3_enabled()
    }

@app.post("/api/extract", response_model=RubixExtractedData)
async def extract_pdf(request: Request, file: UploadFile = File(...)):
    check_rate_limit(request)
    ensure_initialized()
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are supported.")
    
    # Verify PDF magic bytes (%PDF-)
    header_bytes = await file.read(5)
    await file.seek(0)
    if not header_bytes.startswith(PDF_MAGIC_BYTES):
        raise HTTPException(status_code=400, detail="Invalid PDF structure: Magic bytes '%PDF-' missing.")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    safe_name = os.path.basename(file.filename or "upload.pdf")
    unique_suffix = secrets.token_hex(4)
    safe_filename = f"{timestamp}_{unique_suffix}_{safe_name}"
    upload_path = os.path.join(UPLOADS_DIR, safe_filename)
    
    # Stream with size limit
    size = 0
    try:
        with open(upload_path, "wb") as buffer:
            while chunk := await file.read(1024 * 64): # 64KB chunks
                size += len(chunk)
                if size > MAX_UPLOAD_SIZE:
                    raise HTTPException(status_code=413, detail="File too large. Maximum upload size is 25MB.")
                buffer.write(chunk)
            
        try:
            extracted = extract_bureau_pdf(upload_path)
            extracted['appraisal_date'] = datetime.now().strftime("%d/%m/%Y")
            return extracted
        except Exception as e:
            logger.error(f"Error parsing PDF {upload_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to parse bureau PDF. Ensure file is not corrupted or password-protected.")
    finally:
        await file.close()
        # Cleanup temporary uploaded PDF to prevent unbounded disk growth
        if os.path.exists(upload_path):
            try:
                os.remove(upload_path)
            except OSError:
                pass

@app.post("/api/generate")
async def generate_docx(request: Request, req: GenerateDocxRequest):
    check_rate_limit(request)
    ensure_initialized()
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        unique_suffix = secrets.token_hex(4)
        clean_name = "".join(c for c in req.customer_name if c.isalnum() or c in (' ', '_', '-')).strip() or "CUSTOMER"
        filename = f"CRIF_MEMO_{clean_name}_{timestamp}_{unique_suffix}.docx"
        output_path = os.path.join(MEMOS_DIR, filename)
        
        # Prepare dict for generator
        payload = req.model_dump() if hasattr(req, "model_dump") else req.dict()
        build_crif_docx(payload, output_path)
        
        # Backup generated DOCX memo to S3 bucket if configured
        if is_s3_enabled():
            upload_memo_to_s3(filename, output_path)
        
        # Generate unguessable download access token to prevent sequential ID enumeration
        access_token = secrets.token_urlsafe(16)
        
        appraisal_id = save_appraisal(
            customer_name=req.customer_name,
            crif_credit_limit=req.crif_credit_limit,
            credit_days=req.credit_days,
            salesperson=req.salesperson,
            type_of_company=req.type_of_company,
            risk_grade=req.risk_grade_score,
            docx_filename=filename,
            source_pdf=req.source_pdf,
            access_token=access_token
        )
        
        return {
            "success": True,
            "appraisal_id": appraisal_id,
            "access_token": access_token,
            "filename": filename,
            "download_url": f"/api/download/{access_token}"
        }
    except Exception as e:
        logger.error(f"Failed to generate CRIF docx: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate CRIF memorandum document.")

@app.api_route("/api/download/{identifier}", methods=["GET", "HEAD"])
def download_docx(identifier: str):
    ensure_initialized()
    record = get_appraisal_by_token_or_id(identifier)
    if not record:
        raise HTTPException(status_code=404, detail="Appraisal record not found")
        
    file_path = os.path.join(MEMOS_DIR, record['docx_filename'])
    if not os.path.exists(file_path):
        # Attempt to pull from S3 if running in stateless container or after local purge
        if is_s3_enabled():
            download_memo_from_s3(record['docx_filename'], file_path)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail="Document has expired and been removed per retention policy."
        )
        
    return FileResponse(
        path=file_path,
        filename=record['docx_filename'],
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "").strip()

@app.post("/api/maintenance/cleanup")
def trigger_maintenance_cleanup(x_admin_key: Optional[str] = Header(None)):
    ensure_initialized()
    if not ADMIN_SECRET_KEY or not x_admin_key or not secrets.compare_digest(x_admin_key, ADMIN_SECRET_KEY):
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid or missing X-Admin-Key")
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

def is_sample_routes_enabled() -> bool:
    default_val = "false" if os.getenv("ENVIRONMENT", "").strip().lower() == "production" else "true"
    return os.getenv("ENABLE_SAMPLE_ROUTES", default_val).strip().lower() == "true"

@app.get("/api/sample/{filename}")
def load_sample_file(filename: str):
    ensure_initialized()
    if not is_sample_routes_enabled():
        raise HTTPException(status_code=403, detail="Sample routes are disabled in this environment.")
    clean_name = os.path.basename(filename)
    rubix_dir = os.path.join(BACKEND_DIR, 'tests', 'fixtures', 'rubix_samples')
    crif_dir = os.path.join(BACKEND_DIR, 'tests', 'fixtures', 'crif_samples')
    
    file_path = os.path.join(rubix_dir, clean_name)
    if not os.path.exists(file_path):
        file_path = os.path.join(crif_dir, clean_name)
        
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Sample fixture not found")
        
    try:
        extracted = extract_bureau_pdf(file_path)
        extracted['appraisal_date'] = datetime.now().strftime("%d/%m/%Y")
        return extracted
    except Exception as e:
        logger.error(f"Error extracting sample {filename}: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse sample PDF")

@app.get("/api/appraisals")
def list_appraisals(response: Response, limit: int = 200, offset: int = 0, search: Optional[str] = None):
    ensure_initialized()
    total = get_appraisals_count(search=search)
    response.headers["X-Total-Count"] = str(total)
    return get_all_appraisals(limit=min(limit, 500), offset=max(0, offset), search=search)

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
