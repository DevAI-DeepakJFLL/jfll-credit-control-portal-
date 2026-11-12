"""
Centralized Data Normalization & Formatting Utilities.
Shared across active Credit Control CRM automations (Credit Appraisal, Ageing Reports).
"""
import re
from datetime import datetime, date
from typing import Any, Union, Optional

RE_WHITESPACE = re.compile(r'[ \t]+')
RE_INR = re.compile(r'(\d)(?=(\d{2})+$)')
RE_NON_NUMERIC = re.compile(r'[^\d.-]')

_MONTHS = {
    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
    'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
}
MONTHS_MAP = _MONTHS

def clean_text(text: Any) -> str:
    """Normalizes unicode whitespace, hyphens, and non-breaking spaces."""
    if text is None:
        return ""
    text_str = str(text)
    text_str = text_str.replace('\xa0', ' ').replace('\u2010', '-').replace('\u2013', '-').replace('\u2014', '-').replace('‐', '-')
    text_str = RE_WHITESPACE.sub(' ', text_str)
    return text_str.strip()

def normalize_date(raw_date: Any) -> str:
    """
    Standardizes dates from various formats to DD-MM-YYYY.
    Supports:
      - datetime / date objects
      - DD-Mon-YYYY (e.g. 15-Aug-2018)
      - YYYY-MM-DD (e.g. 2018-08-15 00:00:00)
      - DD/MM/YYYY
    """
    if raw_date is None:
        return ""
    if isinstance(raw_date, (datetime, date)):
        return raw_date.strftime("%d-%m-%Y")
    
    text = clean_text(raw_date)
    if not text:
        return ""
        
    # Remove timestamp suffix if present (e.g., '2026-03-20 00:00:00')
    if ' ' in text:
        text = text.split(' ')[0]
        
    # Handle YYYY-MM-DD
    if len(text) == 10 and text[4] == '-' and text[7] == '-':
        parts = text.split('-')
        return f"{parts[2]}-{parts[1]}-{parts[0]}"
        
    # Handle DD-Mon-YYYY (e.g. 01-Jan-2019)
    parts = text.split('-')
    if len(parts) == 3 and parts[1].lower() in _MONTHS:
        return f"{parts[0]}-{_MONTHS[parts[1].lower()]}-{parts[2]}"
        
    # Handle DD/MM/YYYY
    if '/' in text:
        parts = text.split('/')
        if len(parts) == 3:
            return f"{parts[0].zfill(2)}-{parts[1].zfill(2)}-{parts[2]}"
            
    return text

def format_inr(amount: Union[int, float, str]) -> str:
    """
    Formats a numeric amount into standard Indian currency format (e.g. ₹ 10,00,000).
    """
    if amount is None or amount == "":
        return "₹ 0.00"
    try:
        if isinstance(amount, str):
            amt_clean = parse_currency_amount(amount)
        else:
            amt_clean = float(amount)
            
        is_negative = amt_clean < 0
        abs_amt = abs(amt_clean)
        int_part = int(abs_amt)
        dec_part = f"{abs_amt - int_part:.2f}"[2:]
        
        s = str(int_part)
        if len(s) <= 3:
            formatted = s
        else:
            head, tail = s[:-3], s[-3:]
            head = RE_INR.sub(r'\1,', head)
            formatted = f"{head},{tail}"
            
        sign = "-" if is_negative else ""
        return f"{sign}₹ {formatted}" if dec_part == "00" else f"{sign}₹ {formatted}.{dec_part}"
    except (ValueError, TypeError):
        return str(amount)

def parse_currency_amount(val: Any) -> float:
    """
    Safely converts strings with currency symbols, commas, or parentheses into a clean float.
    Handles '(1,500.00)' -> -1500.0, '₹ 25,00,000' -> 2500000.0.
    """
    if val is None or val == "":
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
        
    s = str(val).strip()
    if not s:
        return 0.0
        
    is_paren_negative = s.startswith('(') and s.endswith(')')
    if is_paren_negative:
        s = s[1:-1]
        
    # Remove currency symbols and formatting commas
    s = s.replace('₹', '').replace('Rs.', '').replace('INR', '').replace(',', '').strip()
    try:
        num = float(s)
        return -num if is_paren_negative else num
    except ValueError:
        return 0.0

def clean_customer_name(name: Any) -> str:
    """
    Normalizes company legal names for cross-ledger mapping.
    Strips trailing periods, quotes, multiple spaces, and capitalizes cleanly.
    """
    cleaned = clean_text(name).upper()
    cleaned = re.sub(r'[\s\.\,]+$', '', cleaned)
    return cleaned
