import sqlite3
import os
import logging
from contextlib import contextmanager

from backend.app.core.s3_storage import (
    sync_db_from_s3,
    is_s3_enabled,
    reconcile_records_from_s3
)

logger = logging.getLogger("core.database")

# Support configurable paths for AWS Lambda (/tmp only), Docker volumes, and local development
is_lambda = bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME") or os.getenv("LAMBDA_TASK_ROOT"))
DEFAULT_STORAGE_DIR = "/tmp/credit_crm/storage" if is_lambda else os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'storage')
STORAGE_DIR = os.getenv("STORAGE_DIR", DEFAULT_STORAGE_DIR)
DB_PATH = os.getenv("DATABASE_PATH", os.path.join(STORAGE_DIR, 'appraisals.db'))

_db_initialized = False

@contextmanager
def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
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
        
        # 1. Automation: Credit Appraisal Tables
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

        # 2. Automation: Ageing Report Tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ageing_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_uuid TEXT NOT NULL UNIQUE,
                filename TEXT NOT NULL,
                posting_cutoff_date TEXT,
                total_receivable REAL DEFAULT 0.0,
                total_overdue REAL DEFAULT 0.0,
                customer_count INTEGER DEFAULT 0,
                invoice_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'processed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ageing_batches_uuid ON ageing_batches(batch_uuid);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ageing_batches_created ON ageing_batches(created_at DESC);')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ageing_customer_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_uuid TEXT NOT NULL,
                fu_person TEXT,
                sales_person TEXT,
                branch TEXT,
                customer_name TEXT NOT NULL,
                payment_terms TEXT,
                outstanding REAL DEFAULT 0.0,
                received REAL DEFAULT 0.0,
                balance REAL DEFAULT 0.0,
                advance REAL DEFAULT 0.0,
                remark TEXT,
                bucket_0_30 REAL DEFAULT 0.0,
                bucket_31_45 REAL DEFAULT 0.0,
                bucket_46_60 REAL DEFAULT 0.0,
                bucket_61_90 REAL DEFAULT 0.0,
                bucket_91_180 REAL DEFAULT 0.0,
                bucket_181_240 REAL DEFAULT 0.0,
                bucket_241_365 REAL DEFAULT 0.0,
                bucket_above_365 REAL DEFAULT 0.0,
                grand_total REAL DEFAULT 0.0,
                this_iata REAL DEFAULT 0.0,
                last_iata REAL DEFAULT 0.0,
                on_ac REAL DEFAULT 0.0,
                FOREIGN KEY (batch_uuid) REFERENCES ageing_batches(batch_uuid) ON DELETE CASCADE
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ageing_cust_batch ON ageing_customer_summaries(batch_uuid);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ageing_cust_branch ON ageing_customer_summaries(branch);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ageing_cust_name ON ageing_customer_summaries(customer_name);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ageing_cust_fu ON ageing_customer_summaries(batch_uuid, fu_person);')

        # 3. Automation: Ageing Drilldown Vouchers
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ageing_vouchers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_uuid TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                voucher_no TEXT,
                voucher_type TEXT,
                posting_date TEXT,
                due_date TEXT,
                invoice_amount REAL DEFAULT 0.0,
                allocated_amount REAL DEFAULT 0.0,
                credit_note REAL DEFAULT 0.0,
                outstanding_amount REAL DEFAULT 0.0,
                on_account_amount REAL DEFAULT 0.0,
                net_outstanding_inr REAL DEFAULT 0.0,
                age_days INTEGER DEFAULT 0,
                payment_terms TEXT,
                sales_person TEXT,
                branch TEXT,
                remarks TEXT,
                FOREIGN KEY (batch_uuid) REFERENCES ageing_batches(batch_uuid) ON DELETE CASCADE
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ageing_vouchers_lookup ON ageing_vouchers(batch_uuid, customer_name);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ageing_vouchers_batch ON ageing_vouchers(batch_uuid);')

        conn.commit()

        # Reconcile any individual remote records written by concurrent serverless containers
        if is_s3_enabled():
            reconcile_records_from_s3(conn)
    
    _db_initialized = True
