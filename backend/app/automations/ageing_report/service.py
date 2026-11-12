"""
Service Layer for Ageing Report Automation.
Orchestrates ingestion, persistence in SQLite WAL database, filtering, updates, and Excel export.
"""
import uuid
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import io

from backend.app.core.database import get_db, DB_PATH
from backend.app.core.s3_storage import sync_db_to_s3, is_s3_enabled
from backend.app.core.parsers.common import clean_customer_name
from backend.app.automations.ageing_report.models import (
    CustomerAgeingSummary,
    AgeingBatchSummary
)
from backend.app.automations.ageing_report.parser import parse_master_ar_file
from backend.app.automations.ageing_report.engine import (
    aggregate_customer_ageing,
    calculate_batch_summary
)
from backend.app.automations.ageing_report.generator import generate_ageing_report_excel

logger = logging.getLogger("ageing_report.service")

def process_ageing_upload(file_bytes: bytes, filename: str) -> Tuple[str, AgeingBatchSummary]:
    """
    Ingests an Accounts Receivable Excel ledger, parses vouchers, aggregates debtor balances,
    computes 8-bucket tenors and IATA terms, carries forward follow-up notes from the previous batch,
    and persists batch, customer summaries, and raw vouchers in SQLite.
    """
    batch_uuid = str(uuid.uuid4())

    # Parse transactions
    transactions, meta = parse_master_ar_file(file_bytes)
    cutoff_date = meta.get("posting_cutoff_date", "")

    # Carry forward previous follow-up notes, received amounts, and FU assignments from most recent previous batch
    previous_followups: Dict[str, Dict[str, Any]] = {}
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT customer_name, fu_person, remark, received
                FROM ageing_customer_summaries
                WHERE batch_uuid = (
                    SELECT batch_uuid FROM ageing_batches ORDER BY created_at DESC LIMIT 1
                )
                """
            )
            for r in cursor.fetchall():
                c_name = clean_customer_name(r["customer_name"])
                previous_followups[c_name] = {
                    "fu_person": r["fu_person"],
                    "remark": r["remark"] or "",
                    "received": float(r["received"] or 0.0)
                }
    except Exception as e:
        logger.warning(f"Could not load previous batch followups: {e}")

    # Aggregate by customer with carry-forward
    customers = aggregate_customer_ageing(
        transactions,
        batch_uuid=batch_uuid,
        carry_forward=previous_followups
    )

    # Compute batch executive summary
    summary = calculate_batch_summary(
        customers=customers,
        batch_uuid=batch_uuid,
        filename=filename,
        posting_cutoff_date=cutoff_date,
        invoice_count=len(transactions)
    )

    # Persist in SQLite
    with get_db() as conn:
        cursor = conn.cursor()

        # Insert batch header
        cursor.execute(
            """
            INSERT INTO ageing_batches (
                batch_uuid, filename, posting_cutoff_date, total_receivable,
                total_overdue, customer_count, invoice_count, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                batch_uuid,
                filename,
                cutoff_date,
                summary.total_receivable,
                summary.total_overdue,
                summary.customer_count,
                summary.invoice_count,
                "processed"
            )
        )

        # Bulk insert customer rows
        rows_to_insert = [
            (
                c.batch_uuid,
                c.fu_person,
                c.sales_person,
                c.branch,
                c.customer_name,
                c.payment_terms,
                c.outstanding,
                c.received,
                c.balance,
                c.advance,
                c.remark,
                c.bucket_0_30,
                c.bucket_31_45,
                c.bucket_46_60,
                c.bucket_61_90,
                c.bucket_91_180,
                c.bucket_181_240,
                c.bucket_241_365,
                c.bucket_above_365,
                c.grand_total,
                c.this_iata,
                c.last_iata,
                c.on_ac
            )
            for c in customers
        ]

        cursor.executemany(
            """
            INSERT INTO ageing_customer_summaries (
                batch_uuid, fu_person, sales_person, branch, customer_name,
                payment_terms, outstanding, received, balance, advance, remark,
                bucket_0_30, bucket_31_45, bucket_46_60, bucket_61_90,
                bucket_91_180, bucket_181_240, bucket_241_365, bucket_above_365,
                grand_total, this_iata, last_iata, on_ac
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows_to_insert
        )

        # Bulk insert raw vouchers for drill-down drawer
        voucher_rows = [
            (
                batch_uuid,
                clean_customer_name(tx.customer),
                tx.voucher_no,
                tx.voucher_type,
                tx.posting_date,
                tx.due_date,
                tx.invoice_amount,
                tx.allocated_amount,
                tx.credit_note,
                tx.outstanding_amount,
                tx.on_account_amount,
                tx.net_outstanding_inr,
                tx.age_days,
                tx.payment_terms,
                tx.sales_person,
                tx.branch,
                tx.remarks
            )
            for tx in transactions
            if tx.customer
        ]

        cursor.executemany(
            """
            INSERT INTO ageing_vouchers (
                batch_uuid, customer_name, voucher_no, voucher_type,
                posting_date, due_date, invoice_amount, allocated_amount,
                credit_note, outstanding_amount, on_account_amount,
                net_outstanding_inr, age_days, payment_terms,
                sales_person, branch, remarks
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            voucher_rows
        )

        conn.commit()

    if is_s3_enabled():
        sync_db_to_s3(DB_PATH)

    logger.info(f"Processed and saved ageing batch {batch_uuid}: {len(customers)} customers, {len(transactions)} vouchers.")
    return batch_uuid, summary

def get_all_batches() -> List[Dict[str, Any]]:
    """Returns all historical ageing batch runs ordered by newest first."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, batch_uuid, filename, posting_cutoff_date, total_receivable,
                   total_overdue, customer_count, invoice_count, status, created_at
            FROM ageing_batches
            ORDER BY created_at DESC
            """
        )
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_batch_summary(batch_uuid: str) -> Optional[AgeingBatchSummary]:
    """Retrieves executive metrics and distribution for a specific batch UUID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT batch_uuid, filename, posting_cutoff_date, customer_count, invoice_count
            FROM ageing_batches
            WHERE batch_uuid = ?
            """,
            (batch_uuid,)
        )
        batch_row = cursor.fetchone()
        if not batch_row:
            return None

        # Fetch customer lines
        cursor.execute(
            """
            SELECT id, batch_uuid, fu_person, sales_person, branch, customer_name,
                   payment_terms, outstanding, received, balance, advance, remark,
                   bucket_0_30, bucket_31_45, bucket_46_60, bucket_61_90,
                   bucket_91_180, bucket_181_240, bucket_241_365, bucket_above_365,
                   grand_total, this_iata, last_iata, on_ac
            FROM ageing_customer_summaries
            WHERE batch_uuid = ?
            ORDER BY outstanding DESC
            """,
            (batch_uuid,)
        )
        cust_rows = cursor.fetchall()
        customers = [CustomerAgeingSummary(**dict(r)) for r in cust_rows]

        return calculate_batch_summary(
            customers=customers,
            batch_uuid=batch_uuid,
            filename=batch_row["filename"],
            posting_cutoff_date=batch_row["posting_cutoff_date"] or "",
            invoice_count=batch_row["invoice_count"]
        )

def get_batch_customers(
    batch_uuid: str,
    branch: Optional[str] = None,
    fu_person: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "outstanding",
    sort_dir: str = "desc",
    limit: int = 100,
    offset: int = 0
) -> Tuple[List[CustomerAgeingSummary], int]:
    """
    Queries paginated customer debtor summaries with optional search and filter facets.
    Supports dynamic sorting validated against an allowlist.
    Returns (customers_page, total_filtered_count).
    """
    ALLOWED_SORT_COLS = {
        "customer_name": "customer_name",
        "branch": "branch",
        "fu_person": "fu_person",
        "sales_person": "sales_person",
        "payment_terms": "payment_terms",
        "outstanding": "outstanding",
        "received": "received",
        "balance": "balance",
        "advance": "advance",
        "grand_total": "grand_total",
        "this_iata": "this_iata",
        "last_iata": "last_iata",
        "bucket_0_30": "bucket_0_30",
        "bucket_31_45": "bucket_31_45",
        "bucket_46_60": "bucket_46_60",
        "bucket_61_90": "bucket_61_90",
        "bucket_91_180": "bucket_91_180",
        "bucket_181_240": "bucket_181_240",
        "bucket_241_365": "bucket_241_365",
        "bucket_above_365": "bucket_above_365"
    }
    order_col = ALLOWED_SORT_COLS.get(sort_by, "outstanding")
    direction = "ASC" if sort_dir and sort_dir.lower() == "asc" else "DESC"

    conditions = ["batch_uuid = ?"]
    params: List[Any] = [batch_uuid]

    if branch and branch != "all":
        conditions.append("branch = ?")
        params.append(branch)

    if fu_person and fu_person != "all":
        conditions.append("fu_person = ?")
        params.append(fu_person)

    if search and search.strip():
        term = f"%{search.strip()}%"
        conditions.append("(customer_name LIKE ? OR sales_person LIKE ? OR remark LIKE ?)")
        params.extend([term, term, term])

    where_clause = " AND ".join(conditions)

    with get_db() as conn:
        cursor = conn.cursor()

        # Count total matching
        cursor.execute(f"SELECT COUNT(*) FROM ageing_customer_summaries WHERE {where_clause}", params)
        total_count = cursor.fetchone()[0]

        # Fetch page records with dynamic sorting
        query = f"""
            SELECT id, batch_uuid, fu_person, sales_person, branch, customer_name,
                   payment_terms, outstanding, received, balance, advance, remark,
                   bucket_0_30, bucket_31_45, bucket_46_60, bucket_61_90,
                   bucket_91_180, bucket_181_240, bucket_241_365, bucket_above_365,
                   grand_total, this_iata, last_iata, on_ac
            FROM ageing_customer_summaries
            WHERE {where_clause}
            ORDER BY {order_col} {direction}
            LIMIT ? OFFSET ?
        """
        page_params = params + [limit, offset]
        cursor.execute(query, page_params)
        rows = cursor.fetchall()

        customers = [CustomerAgeingSummary(**dict(r)) for r in rows]
        return customers, total_count

def get_customer_vouchers(batch_uuid: str, customer_name: str) -> List[Dict[str, Any]]:
    """Retrieves all invoice vouchers for a specific debtor and batch."""
    cleaned_name = clean_customer_name(customer_name)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, batch_uuid, customer_name, voucher_no, voucher_type,
                   posting_date, due_date, invoice_amount, allocated_amount,
                   credit_note, outstanding_amount, on_account_amount,
                   net_outstanding_inr, age_days, payment_terms,
                   sales_person, branch, remarks
            FROM ageing_vouchers
            WHERE batch_uuid = ? AND (customer_name = ? OR customer_name = ?)
            ORDER BY age_days DESC, posting_date DESC
            """,
            (batch_uuid, customer_name, cleaned_name)
        )
        return [dict(r) for r in cursor.fetchall()]

def update_customer_followup(
    customer_id: int,
    fu_person: Optional[str] = None,
    remark: Optional[str] = None,
    received: Optional[float] = None
) -> bool:
    """Updates follow-up assignment, remark, or collected payment for a debtor line."""
    updates = []
    params: List[Any] = []

    if fu_person is not None:
        updates.append("fu_person = ?")
        params.append(fu_person)

    if remark is not None:
        updates.append("remark = ?")
        params.append(remark)

    if received is not None:
        updates.append("received = ?")
        updates.append("balance = outstanding - ?")
        params.append(received)
        params.append(received)

    if not updates:
        return False

    params.append(customer_id)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE ageing_customer_summaries SET {', '.join(updates)} WHERE id = ?",
            params
        )
        conn.commit()
        updated = cursor.rowcount > 0

    if updated and is_s3_enabled():
        sync_db_to_s3(DB_PATH)

    return updated

def export_batch_excel(
    batch_uuid: str,
    branch: Optional[str] = None,
    fu_person: Optional[str] = None,
    search: Optional[str] = None
) -> Optional[io.BytesIO]:
    """
    Generates and returns the active Excel spreadsheet for the specified batch UUID.
    Supports exporting filtered subsets (by branch, FU owner, search) for branch managers.
    """
    conditions = ["batch_uuid = ?"]
    params: List[Any] = [batch_uuid]

    if branch and branch != "all":
        conditions.append("branch = ?")
        params.append(branch)

    if fu_person and fu_person != "all":
        conditions.append("fu_person = ?")
        params.append(fu_person)

    if search and search.strip():
        term = f"%{search.strip()}%"
        conditions.append("(customer_name LIKE ? OR sales_person LIKE ? OR remark LIKE ?)")
        params.extend([term, term, term])

    where_clause = " AND ".join(conditions)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT id, batch_uuid, fu_person, sales_person, branch, customer_name,
                   payment_terms, outstanding, received, balance, advance, remark,
                   bucket_0_30, bucket_31_45, bucket_46_60, bucket_61_90,
                   bucket_91_180, bucket_181_240, bucket_241_365, bucket_above_365,
                   grand_total, this_iata, last_iata, on_ac
            FROM ageing_customer_summaries
            WHERE {where_clause}
            ORDER BY outstanding DESC
            """,
            params
        )
        rows = cursor.fetchall()
        if not rows:
            return None

        customers = [CustomerAgeingSummary(**dict(r)) for r in rows]
        return generate_ageing_report_excel(customers)
