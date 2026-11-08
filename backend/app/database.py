import sqlite3
import os
from contextlib import contextmanager
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'storage', 'appraisals.db')

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
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('PRAGMA journal_mode=WAL;')
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
                docx_filename TEXT NOT NULL,
                source_pdf TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_appraisals_customer_name ON appraisals(customer_name);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_appraisals_created_at ON appraisals(created_at DESC);')
        conn.commit()

def get_appraisals_count() -> int:
    with get_db() as conn:
        cursor = conn.cursor()
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
    source_pdf: Optional[str] = None
) -> int:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appraisals (
                customer_name, crif_credit_limit, credit_days, salesperson,
                type_of_company, risk_grade, docx_filename, source_pdf
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            customer_name, crif_credit_limit, credit_days, salesperson,
            type_of_company, risk_grade, docx_filename, source_pdf
        ))
        conn.commit()
        return cursor.lastrowid

def get_all_appraisals(limit: int = 200, offset: int = 0) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, customer_name, crif_credit_limit, credit_days, salesperson,
                   type_of_company, risk_grade, docx_filename, source_pdf, created_at
            FROM appraisals
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_appraisal_by_id(appraisal_id: int) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM appraisals WHERE id = ?', (appraisal_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
