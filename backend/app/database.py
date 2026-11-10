import sqlite3
import os
import secrets
import logging
from datetime import datetime
from contextlib import contextmanager
from typing import List, Dict, Any, Optional

from backend.app.s3_storage import (
    sync_db_from_s3,
    sync_db_to_s3,
    is_s3_enabled,
    save_appraisal_record_to_s3,
    reconcile_records_from_s3
)

logger = logging.getLogger("database")

# Support configurable paths for AWS Lambda (/tmp only), Docker volumes, and local development
is_lambda = bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME") or os.getenv("LAMBDA_TASK_ROOT"))
DEFAULT_STORAGE_DIR = "/tmp/credit_crm/storage" if is_lambda else os.path.join(os.path.dirname(os.path.dirname(__file__)), 'storage')
STORAGE_DIR = os.getenv("STORAGE_DIR", DEFAULT_STORAGE_DIR)
DB_PATH = os.getenv("DATABASE_PATH", os.path.join(STORAGE_DIR, 'appraisals.db'))

_db_initialized = False

@contextmanager
def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    global _db_initialized
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Restore database from S3 if running in serverless and DB doesn't exist yet
    if not os.path.exists(DB_PATH) and is_s3_enabled():
        sync_db_from_s3(DB_PATH)

    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('PRAGMA journal_mode=WAL;')
        except sqlite3.OperationalError:
            pass
        cursor.execute('PRAGMA busy_timeout=5000;')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appraisals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                crif_credit_limit TEXT NOT NULL,
                credit_days TEXT NOT NULL,
                salesperson TEXT NOT NULL,
                type_of_company TEXT,
                risk_grade TEXT,
                docx_filename TEXT NOT NULL UNIQUE,
                source_pdf TEXT,
                access_token TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute("PRAGMA table_info(appraisals)")
        columns = [row[1] for row in cursor.fetchall()]
        if "access_token" not in columns:
            try:
                cursor.execute("ALTER TABLE appraisals ADD COLUMN access_token TEXT;")
            except Exception:
                pass
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_appraisals_customer_name ON appraisals(customer_name);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_appraisals_salesperson ON appraisals(salesperson);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_appraisals_created_at ON appraisals(created_at DESC);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_appraisals_docx_filename ON appraisals(docx_filename);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_appraisals_access_token ON appraisals(access_token);')
        conn.commit()

        # Reconcile any individual remote records written by concurrent serverless containers
        if is_s3_enabled():
            reconcile_records_from_s3(conn)
    
    _db_initialized = True

def get_appraisals_count(search: Optional[str] = None) -> int:
    with get_db() as conn:
        cursor = conn.cursor()
        if search and search.strip():
            query_param = f"%{search.strip()}%"
            cursor.execute(
                'SELECT COUNT(*) FROM appraisals WHERE customer_name LIKE ? OR salesperson LIKE ?',
                (query_param, query_param)
            )
        else:
            cursor.execute('SELECT COUNT(*) FROM appraisals')
        row = cursor.fetchone()
        return row[0] if row else 0

def save_appraisal(
    customer_name: str,
    crif_credit_limit: str,
    credit_days: str,
    salesperson: str,
    type_of_company: str,
    risk_grade: str,
    docx_filename: str,
    source_pdf: Optional[str] = None,
    access_token: Optional[str] = None
) -> int:
    created_at = datetime.now().isoformat()
    if not access_token:
        access_token = secrets.token_urlsafe(16)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appraisals (
                customer_name, crif_credit_limit, credit_days, salesperson,
                type_of_company, risk_grade, docx_filename, source_pdf, access_token, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            customer_name, crif_credit_limit, credit_days, salesperson,
            type_of_company, risk_grade, docx_filename, source_pdf, access_token, created_at
        ))
        conn.commit()
        last_id = cursor.lastrowid or 0
    
    # Save atomic record to S3 to guarantee multi-instance concurrency safety, then snapshot DB
    if is_s3_enabled():
        try:
            record_dict = {
                "id": last_id,
                "customer_name": customer_name,
                "crif_credit_limit": crif_credit_limit,
                "credit_days": credit_days,
                "salesperson": salesperson,
                "type_of_company": type_of_company,
                "risk_grade": risk_grade,
                "docx_filename": docx_filename,
                "source_pdf": source_pdf,
                "access_token": access_token,
                "created_at": created_at
            }
            save_appraisal_record_to_s3(record_dict)
            sync_db_to_s3(DB_PATH)
        except Exception as e:
            logger.warning(f"Non-critical: S3 database sync deferred: {e}")
            
    return last_id

def get_all_appraisals(limit: int = 200, offset: int = 0, search: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        if search and search.strip():
            query_param = f"%{search.strip()}%"
            cursor.execute('''
                SELECT id, customer_name, crif_credit_limit, credit_days, salesperson,
                       type_of_company, risk_grade, docx_filename, source_pdf, access_token, created_at
                FROM appraisals
                WHERE customer_name LIKE ? OR salesperson LIKE ?
                ORDER BY id DESC
                LIMIT ? OFFSET ?
            ''', (query_param, query_param, limit, offset))
        else:
            cursor.execute('''
                SELECT id, customer_name, crif_credit_limit, credit_days, salesperson,
                       type_of_company, risk_grade, docx_filename, source_pdf, access_token, created_at
                FROM appraisals
                ORDER BY id DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_appraisal_by_id(appraisal_id: int) -> Optional[Dict[str, Any]]:
    return get_appraisal_by_token_or_id(str(appraisal_id))

def get_appraisal_by_token_or_id(identifier: str) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        # Look up by unguessable access_token first
        cursor.execute('SELECT * FROM appraisals WHERE access_token = ?', (identifier,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        # Fallback to numeric id for backward compatibility
        if str(identifier).isdigit():
            cursor.execute('SELECT * FROM appraisals WHERE id = ?', (int(identifier),))
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None
