"""
Centralized Excel & Tabular Parsing Library.
Shared across Credit Control CRM automations (Ageing Reports, Statement Reconciliation).
"""
import io
import openpyxl
from typing import List, Dict, Any, Tuple, Optional, Union
from backend.app.core.parsers.common import clean_text

def load_workbook_safe(
    source: Union[str, bytes, io.BytesIO], 
    data_only: bool = True,
    read_only: bool = True
) -> openpyxl.Workbook:
    """
    Safely loads an Excel workbook from disk path or in-memory byte buffer.
    """
    if isinstance(source, bytes):
        source = io.BytesIO(source)
    return openpyxl.load_workbook(source, data_only=data_only, read_only=read_only)

def detect_header_row(
    worksheet: openpyxl.worksheet.worksheet.Worksheet,
    min_non_empty_cols: Union[int, List[str]] = 4,
    search_rows: int = 30,
    expected_keywords: Optional[List[str]] = None
) -> Tuple[int, List[str]]:
    """
    Dynamically scans the first `search_rows` of an Excel worksheet to find the true table header row.
    Returns (header_row_number_1_based, list_of_clean_header_names).
    """
    if isinstance(min_non_empty_cols, (list, tuple, set)):
        expected_keywords = list(min_non_empty_cols)
        min_non_empty_cols = 4

    expected_lower = [k.lower().strip() for k in expected_keywords] if expected_keywords else []

    for r in range(1, search_rows + 1):
        row_vals = [cell.value for cell in worksheet[r]]
        non_empty = [clean_text(v) for v in row_vals if v is not None and clean_text(v) != '']
        if len(non_empty) >= min_non_empty_cols:
            if expected_lower:
                joined_row = " ".join(v.lower() for v in non_empty)
                # Check if at least half of the expected keywords are found
                matches = sum(1 for kw in expected_lower if kw in joined_row)
                if matches >= max(1, len(expected_lower) // 2):
                    headers = [clean_text(c) if c is not None else f"col_{idx}" for idx, c in enumerate(row_vals)]
                    return r, headers
            else:
                headers = [clean_text(c) if c is not None else f"col_{idx}" for idx, c in enumerate(row_vals)]
                return r, headers
    return 1, []

def extract_sheet_records(
    worksheet: openpyxl.worksheet.worksheet.Worksheet,
    start_row: Optional[int] = None,
    headers: Optional[List[str]] = None,
    max_rows: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Streams data rows below the header row as dictionaries keyed by header names.
    Ignores purely empty rows.
    """
    if start_row is None or headers is None:
        detected_row, detected_headers = detect_header_row(worksheet)
        start_row = start_row or (detected_row + 1)
        headers = headers or detected_headers

    records: List[Dict[str, Any]] = []
    current_row = start_row
    
    for row in worksheet.iter_rows(min_row=start_row, max_row=max_rows, values_only=True):
        if not any(c is not None and clean_text(c) != '' for c in row):
            continue  # skip empty lines
            
        record: Dict[str, Any] = {}
        for idx, val in enumerate(row):
            col_name = headers[idx] if idx < len(headers) else f"col_{idx}"
            record[col_name] = val
        records.append(record)
        current_row += 1

    return records
