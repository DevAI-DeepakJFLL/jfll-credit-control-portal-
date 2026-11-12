"""
Centralized PDF Parsing Library.
Shared across all Credit Control CRM automations for fast, reliable document extraction.
"""
import io
import pypdf
from typing import List, Union
from backend.app.core.parsers.common import clean_text

def extract_pdf_pages_text(source: Union[str, bytes, io.BytesIO]) -> List[str]:
    """
    Extracts text page-by-page from a PDF file path or byte stream.
    Returns a list of cleaned strings, one per page.
    """
    reader = pypdf.PdfReader(source)
    pages_text = []
    for page in reader.pages:
        raw = page.extract_text() or ""
        pages_text.append(clean_text(raw))
    return pages_text

def extract_full_pdf_text(source: Union[str, bytes, io.BytesIO]) -> str:
    """
    Extracts and concatenates all text across all pages of a PDF document.
    """
    pages = extract_pdf_pages_text(source)
    return "\n\n".join(pages)
