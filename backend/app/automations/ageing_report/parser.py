"""
Parser for ERP Accounts Receivable Transaction Ledgers (Master File).
Leverages centralized parsers from backend.app.core.parsers.
Optimized for high throughput via openpyxl iter_rows.
"""
import re
import datetime
from typing import List, Tuple, Dict, Any, Union, Optional
import openpyxl

from backend.app.core.parsers.excel import load_workbook_safe, detect_header_row
from backend.app.core.parsers.common import (
    clean_text,
    clean_customer_name,
    parse_currency_amount,
    normalize_date
)
from backend.app.automations.ageing_report.models import RawTransaction

# Canonical branch normalization mapping
BRANCH_MAP = {
    "bom": "Mumbai",
    "mumbai": "Mumbai",
    "amd": "Ahmedabad",
    "ahmedabad": "Ahmedabad",
    "del": "Delhi",
    "delhi": "Delhi",
    "ggn": "Delhi",
    "gurgaon": "Delhi",
    "haryana": "Delhi",
    "blr": "Banglore",
    "bangalore": "Banglore",
    "banglore": "Banglore",
    "ixe": "Banglore",
    "mangalore": "Banglore",
    "cok": "Kerala",
    "cochin": "Kerala",
    "ccj": "Kerala",
    "calicut": "Kerala",
    "trv": "Kerala",
    "trivandrum": "Kerala",
    "knn": "Kerala",
    "kannur": "Kerala",
    "kerala": "Kerala",
    "maa": "Chennai",
    "chennai": "Chennai",
    "hyd": "Hyderabad",
    "hyderabad": "Hyderabad",
    "ccu": "Kolkata",
    "kolkata": "Kolkata",
    "domestic": "Domestic"
}

def normalize_branch_name(raw_branch: Any) -> str:
    """
    Normalizes complex branch codes (e.g., 'BOM - Mumbai - JFL', 'COK - Cochin - JFL')
    into standardized corporate branch names ('Mumbai', 'Kerala', etc.).
    """
    text = clean_text(raw_branch).lower()
    if not text:
        return "Mumbai"

    for token, canonical in BRANCH_MAP.items():
        if re.search(rf"\b{re.escape(token)}\b", text):
            return canonical

    parts = text.split("-")
    if len(parts) >= 2:
        mid = parts[1].strip()
        for token, canonical in BRANCH_MAP.items():
            if token in mid:
                return canonical
        return mid.title()

    return "Mumbai"

def parse_master_ar_file(
    file_source: Union[str, bytes]
) -> Tuple[List[RawTransaction], Dict[str, Any]]:
    """
    Parses an ERP Accounts Receivable Excel file (e.g. MASTER FILE - Copy.xlsx).
    Scans for the header row dynamically, reads all transaction vouchers via fast row iterator,
    normalizes data fields, and returns (transactions, metadata).
    """
    wb = load_workbook_safe(file_source, data_only=True, read_only=True)
    
    # Priority sheet: 'DATA', fallback to first sheet
    ws = wb['DATA'] if 'DATA' in wb.sheetnames else wb.active

    # Detect header row dynamically
    header_row_idx, headers = detect_header_row(
        ws,
        search_rows=30,
        expected_keywords=['Customer', 'Voucher No', 'Invoice Amount']
    )

    # Normalize header lookup map (lowercase clean string -> 0-based tuple index)
    col_map: Dict[str, int] = {}
    for c_idx, h in enumerate(headers):
        clean_h = clean_text(h).lower()
        if clean_h:
            col_map[clean_h] = c_idx

    def find_idx(*candidates: str) -> Optional[int]:
        for cand in candidates:
            c_low = cand.lower()
            for h_text, idx in col_map.items():
                if c_low == h_text or c_low in h_text:
                    return idx
        return None

    i_customer = find_idx("customer") or 1
    i_voucher_no = find_idx("voucher no", "voucher") or 2
    i_voucher_type = find_idx("voucher type") or 3
    i_posting_date = find_idx("posting date") or 4
    i_currency = find_idx("currency") or 5
    i_ex_rate = find_idx("ex. rate", "rate") or 7
    i_inv_amt = find_idx("invoice amount", "invoice amt") or 8
    i_alloc_amt = find_idx("allocated amt", "allocated") or 9
    i_credit_note = find_idx("credit note") or 10
    i_out_amt = find_idx("outstanding amt") or 11
    i_overdue = find_idx("overdue") or 12
    i_on_account = find_idx("on account amt", "on account") or 13
    i_net_outstanding = find_idx("net outstanding amt (inr)", "net outstanding amt", "net outstanding") or 15
    i_due_date = find_idx("due date") or 16
    i_age_days = find_idx("age (days)", "age") or 17
    i_payment_terms = find_idx("payment terms", "terms") or 30
    i_sales_person = find_idx("sales person", "sales") or 31
    i_branch = find_idx("branch") or 32
    i_remarks = find_idx("remarks", "remark") or 33

    transactions: List[RawTransaction] = []
    max_posting_date: Optional[datetime.date] = None

    row_idx = header_row_idx
    for row in ws.iter_rows(min_row=header_row_idx + 1, values_only=True):
        row_idx += 1
        if not row:
            continue

        row_len = len(row)
        if i_customer >= row_len:
            continue

        cust_raw = row[i_customer]
        if not cust_raw:
            continue
        cust_name = clean_text(cust_raw)
        if not cust_name:
            continue

        voucher_no = clean_text(row[i_voucher_no]) if i_voucher_no < row_len else ""
        voucher_type = clean_text(row[i_voucher_type]) if i_voucher_type < row_len else ""

        # Posting date
        p_date_cell = row[i_posting_date] if i_posting_date < row_len else None
        p_date_str = normalize_date(p_date_cell)
        if isinstance(p_date_cell, datetime.datetime):
            if not max_posting_date or p_date_cell.date() > max_posting_date:
                max_posting_date = p_date_cell.date()
        elif isinstance(p_date_cell, datetime.date):
            if not max_posting_date or p_date_cell > max_posting_date:
                max_posting_date = p_date_cell

        # Due date
        due_date_cell = row[i_due_date] if i_due_date < row_len else None
        due_date_str = normalize_date(due_date_cell)

        # Amounts
        inv_amt = parse_currency_amount(row[i_inv_amt]) if i_inv_amt < row_len else 0.0
        alloc_amt = parse_currency_amount(row[i_alloc_amt]) if i_alloc_amt < row_len else 0.0
        credit_note = parse_currency_amount(row[i_credit_note]) if i_credit_note < row_len else 0.0
        out_amt = parse_currency_amount(row[i_out_amt]) if i_out_amt < row_len else 0.0
        overdue = parse_currency_amount(row[i_overdue]) if i_overdue < row_len else 0.0
        on_account = parse_currency_amount(row[i_on_account]) if i_on_account < row_len else 0.0
        net_outstanding = parse_currency_amount(row[i_net_outstanding]) if i_net_outstanding < row_len else 0.0

        # Age
        age_raw = row[i_age_days] if i_age_days < row_len else 0
        try:
            age_days = int(float(age_raw or 0))
        except (ValueError, TypeError):
            age_days = 0

        # Metadata
        terms = clean_text(row[i_payment_terms]) if i_payment_terms < row_len else ""
        sales = clean_text(row[i_sales_person]) if i_sales_person < row_len else ""
        raw_branch = row[i_branch] if i_branch < row_len else ""
        branch = normalize_branch_name(raw_branch)
        remarks = clean_text(row[i_remarks]) if i_remarks < row_len else ""

        tx = RawTransaction(
            row_num=row_idx,
            customer=cust_name,
            voucher_no=voucher_no,
            voucher_type=voucher_type,
            posting_date=p_date_str,
            currency=clean_text(row[i_currency] or "INR") if i_currency < row_len else "INR",
            ex_rate=float(row[i_ex_rate] or 1.0) if i_ex_rate < row_len and row[i_ex_rate] else 1.0,
            invoice_amount=inv_amt,
            allocated_amount=alloc_amt,
            credit_note=credit_note,
            outstanding_amount=out_amt,
            overdue=overdue,
            on_account_amount=on_account,
            net_outstanding_inr=net_outstanding,
            due_date=due_date_str,
            age_days=age_days,
            payment_terms=terms,
            sales_person=sales,
            branch=branch,
            remarks=remarks
        )
        transactions.append(tx)

    wb.close()

    metadata = {
        "sheet_name": ws.title,
        "header_row": header_row_idx,
        "total_rows_parsed": len(transactions),
        "posting_cutoff_date": max_posting_date.strftime("%d/%m/%Y") if max_posting_date else datetime.date.today().strftime("%d/%m/%Y")
    }

    return transactions, metadata
