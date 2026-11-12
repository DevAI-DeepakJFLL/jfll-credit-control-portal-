"""
Centralized Reusable Parser Library for Credit Control CRM.
Provides unified PDF, Excel, date, currency, and entity parsing for all department automations.
"""
from backend.app.core.parsers.common import (
    clean_text,
    normalize_date,
    format_inr,
    parse_currency_amount,
    clean_customer_name
)

from backend.app.core.parsers.pdf import (
    extract_pdf_pages_text,
    extract_full_pdf_text
)

from backend.app.core.parsers.excel import (
    load_workbook_safe,
    detect_header_row,
    extract_sheet_records
)

__all__ = [
    "clean_text",
    "normalize_date",
    "format_inr",
    "parse_currency_amount",
    "clean_customer_name",
    "extract_pdf_pages_text",
    "extract_full_pdf_text",
    "load_workbook_safe",
    "detect_header_row",
    "extract_sheet_records"
]
