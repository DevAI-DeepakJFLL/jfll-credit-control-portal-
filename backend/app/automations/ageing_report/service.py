"""
Service Layer for Ageing Report Automation.
Orchestrates ingestion, persistence in SQLite WAL database, filtering, updates, and Excel export.
"""
import uuid
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import io

from backend.app.core.database import get_db
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
    computes 8-bucket tenors and IATA terms, and persists the batch in SQLite.
    """
    batch_uuid = str(uuid.uuid4())

    # Parse transactions
    transactions, meta = parse_master_ar_file(file_bytes)
    cutoff_date = meta.get("posting_cutoff_date", "")

    # Aggregate by customer
    customers = aggregate_customer_ageing(transactions, batch_uuid=batch_uuid)

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
        conn.commit()

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
    limit: int = 100,
    offset: int = 0
) -> Tuple[List[CustomerAgeingSummary], int]:
    """
    Queries paginated customer debtor summaries with optional search and filter facets.
    Returns (customers_page, total_filtered_count).
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

        # Count total matching
        cursor.execute(f"SELECT COUNT(*) FROM ageing_customer_summaries WHERE {where_clause}", params)
        total_count = cursor.fetchone()[0]

        # Fetch page records
        query = f"""
            SELECT id, batch_uuid, fu_person, sales_person, branch, customer_name,
                   payment_terms, outstanding, received, balance, advance, remark,
                   bucket_0_30, bucket_31_45, bucket_46_60, bucket_61_90,
                   bucket_91_180, bucket_181_240, bucket_241_365, bucket_above_365,
                   grand_total, this_iata, last_iata, on_ac
            FROM ageing_customer_summaries
            WHERE {where_clause}
            ORDER BY outstanding DESC
            LIMIT ? OFFSET ?
        """
        page_params = params + [limit, offset]
        cursor.execute(query, page_params)
        rows = cursor.fetchall()

        customers = [CustomerAgeingSummary(**dict(r)) for r in rows]
        return customers, total_count

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
        return cursor.rowcount > 0

def export_batch_excel(batch_uuid: str) -> Optional[io.BytesIO]:
    """Generates and returns the active Excel spreadsheet for the specified batch UUID."""
    with get_db() as conn:
        cursor = conn.cursor()
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
        rows = cursor.fetchall()
        if not rows:
            return None

        customers = [CustomerAgeingSummary(**dict(r)) for r in rows]
        return generate_ageing_report_excel(customers)
