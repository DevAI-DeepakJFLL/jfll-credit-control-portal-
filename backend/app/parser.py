import re
import pypdf
from datetime import date
from typing import Dict, Any, List

def clean_text(text: str) -> str:
    if not text:
        return ""
    # Normalize unicode non-breaking spaces and hyphen variants
    text = text.replace('\xa0', ' ').replace('\u2010', '-').replace('\u2013', '-').replace('\u2014', '-').replace('‐', '-')
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

_MONTHS = {'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
           'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'}

def _normalize_date(raw_date: str) -> str:
    """Converts DD-Mon-YYYY (e.g. 01-Jan-2019) to DD-MM-YYYY (01-01-2019)."""
    raw_date = raw_date.replace('\u2010', '-').replace('‐', '-')
    parts = raw_date.strip().split('-')
    if len(parts) == 3 and parts[1].lower() in _MONTHS:
        return f"{parts[0]}-{_MONTHS[parts[1].lower()]}-{parts[2]}"
    return raw_date.strip()

def _format_inr(amount: int) -> str:
    """Formats an integer rupee amount into the Indian numbering system (e.g. ₹ 10,00,000)."""
    s = str(amount)
    if len(s) <= 3:
        return f"₹ {s}"
    head, tail = s[:-3], s[-3:]
    head = re.sub(r'(\d)(?=(\d{2})+$)', r'\1,', head)
    return f"₹ {head},{tail}"

def _generate_kyc_checklist(type_of_company: str, gst_delay_days: int = 0, bureau: str = "Rubix") -> List[Dict[str, str]]:
    is_pvt_ltd = 'private limited' in type_of_company.lower()
    is_partnership = 'partnership' in type_of_company.lower()

    kyc_docs = [
        {"document": "Permanent Account Number (PAN)", "status": "Available", "source": f"Income Tax / {bureau}", "remarks": "Active & Linked"},
        {"document": "GST Registration Certificate", "status": "Available", "source": f"GSTN Portal / {bureau}", "remarks": f"Active ({gst_delay_days} Days Delay)"}
    ]

    if is_pvt_ltd:
        kyc_docs.append({"document": "Tax Deduction Account (TAN)", "status": "Available", "source": "Income Tax Records", "remarks": "Active"})
        kyc_docs.append({"document": "Certificate of Incorporation (COI)", "status": "Available", "source": "MCA Master Data", "remarks": "Active Compliant"})
    elif is_partnership:
        kyc_docs.append({"document": "Tax Deduction Account (TAN)", "status": "Available", "source": "Statutory Records", "remarks": "Active"})
        kyc_docs.append({"document": "Certificate of Incorporation / Deed", "status": "Available", "source": "Registrar of Firms", "remarks": "Verified"})
    else:
        # Proprietorship
        kyc_docs.append({"document": "Aadhaar Card", "status": "Available", "source": "UIDAI / Master Record", "remarks": "Proprietor Verified"})
        kyc_docs.append({"document": "Import Export Code (IEC) / Trade License", "status": "Available", "source": "DGFT / Trade Registry", "remarks": "Active on Portal"})

    return kyc_docs

def _calculate_epfo_delay(epfo_text: str) -> int:
    """Computes delay in days for the latest EPFO contribution (due 15th of next month)."""
    m = re.search(r'\d{10,15}\s+(\d{1,2}-[A-Za-z]{3}-\d{2,4})\s+[\d\.]+\s+([A-Za-z]{3}-\d{2,4})', epfo_text)
    if not m:
        return 0
    credit_date_str = m.group(1)
    wage_month_str = m.group(2)
    w_parts = wage_month_str.split('-')
    if len(w_parts) != 2:
        return 0
    w_mon = w_parts[0].lower()
    w_year = int(w_parts[1])
    if w_year < 100:
        w_year += 2000
    month_num = int(_MONTHS.get(w_mon, '0'))
    if month_num == 0:
        return 0
    if month_num == 12:
        due_month = 1
        due_year = w_year + 1
    else:
        due_month = month_num + 1
        due_year = w_year
    due_date = date(due_year, due_month, 15)

    c_parts = credit_date_str.split('-')
    if len(c_parts) != 3:
        return 0
    c_day = int(c_parts[0])
    c_mon = int(_MONTHS.get(c_parts[1].lower(), '0'))
    c_year = int(c_parts[2])
    if c_year < 100:
        c_year += 2000
    if c_mon == 0:
        return 0
    credit_date = date(c_year, c_mon, c_day)
    return max(0, (credit_date - due_date).days)

def _extract_birl_court_cases(text: str) -> int:
    """Extracts active or pending court cases from CRIF BIRL Legal History section."""
    m_lh = re.search(r'LEGAL HISTORY\s*(.*?)(?:ANNEXURE|END OF REPORT|\Z)', text, re.DOTALL)
    if not m_lh:
        return 0
    lh_text = m_lh.group(1)
    if 'no results found' in lh_text.lower() or 'no match found' in lh_text.lower():
        return 0
    case_matches = re.findall(r'vs\s*\.\s*([A-Z0-9\s,\.\(\)&-]+?)\s+(?:Pending|Active)', lh_text, re.IGNORECASE)
    if case_matches:
        unique_defendants = set(" ".join(m.split()) for m in case_matches)
        return len(unique_defendants)
    pending_matches = re.findall(r'\b(?:Pending|Active)\b', lh_text, re.IGNORECASE)
    return len(pending_matches)

def detect_bureau_format(pdf_path: str) -> str:
    """
    Detects whether the uploaded PDF is a Rubix report, CRIF BIR report, or CRIF BIRL report.
    Returns: 'RUBIX', 'CRIF_BIR', 'CRIF_BIRL'
    """
    reader = pypdf.PdfReader(pdf_path)
    text = ""
    for page in reader.pages[:min(3, len(reader.pages))]:
        text += (page.extract_text() or "") + "\n"

    # 1. Rubix Data Sciences
    if 'Business Check' in text and ('Rubix' in text or 'RUBIX' in text or 'rubix' in text.lower()):
        return 'RUBIX'
    if 'Business Check' in text:
        return 'RUBIX'

    # 2. CRIF BIRL (Limited / Corporate comprehensive report)
    if 'ABOUT COMPANY' in text and any(k in text for k in ['BIR Report', 'CS/BIL', 'Unable\nTo\nRate', 'Credit Limit (INR Cr)']):
        return 'CRIF_BIRL'

    # 3. CRIF BIR (Standard Business Information Report)
    if 'Business Information Report' in text and ('CRIF SOLUTIONS' in text or 'CRIF Solutions' in text):
        return 'CRIF_BIR'

    # 4. Default fallback if CRIF is anywhere in text
    if 'CRIF' in text.upper():
        return 'CRIF_BIR'

    return 'RUBIX'

def parse_rubix_pdf(pdf_path: str) -> Dict[str, Any]:
    reader = pypdf.PdfReader(pdf_path)
    
    pages_text = []
    for i, page in enumerate(reader.pages):
        t = page.extract_text() or ""
        pages_text.append(clean_text(t))
        
    full_text = "\n".join(pages_text)
    
    # 1. Customer Name
    customer_name = ""
    # Header format: "Business Check | <CUSTOMER NAME> <DATE>"
    for p in pages_text[:3]:
        m = re.search(r'Business Check\s*\|\s*([A-Z0-9\s,\.\(\)-]+?)\s+\d{2}-[A-Za-z]{3}-\d{4}', p)
        if m:
            customer_name = m.group(1).strip()
            break
            
    if not customer_name and pages_text:
        # Fallback to Cover Page line 2
        p1_lines = [l.strip() for l in pages_text[0].split('\n') if l.strip()]
        if len(p1_lines) >= 2 and p1_lines[0].lower() == 'business check':
            customer_name = p1_lines[1]
            
    # Fallback to Business Facts
    if not customer_name:
        m = re.search(r'Company Name\s+([A-Z0-9\s,\.\(\)-]+?)(?:Company Address|\n)', full_text, re.IGNORECASE)
        if m:
            customer_name = m.group(1).strip()

    customer_name = customer_name.upper()

    # 2. Nature of Business
    # Found under "About [Customer Name]" on Page 3
    nature_of_business = ""
    for p in pages_text[1:5]:
        m = re.search(r'About\s+[^\n]+\n(.*?)(?:Above Average Counterparty Risk|Average Counterparty Risk|High Counterparty Risk|Low Counterparty Risk|Risk metrics|\Z)', p, re.DOTALL | re.IGNORECASE)
        if m:
            nob = m.group(1).strip()
            # Clean trailing risk header if caught
            nob = re.sub(r'\s*(?:Above Average|Average|High|Low|Very High)\s+Counterparty\s+Risk.*', '', nob, flags=re.DOTALL | re.IGNORECASE).strip()
            nob = re.sub(r'\s*Risk metrics.*', '', nob, flags=re.DOTALL | re.IGNORECASE).strip()
            nob = " ".join(nob.split())
            if len(nob) > 20:
                nature_of_business = nob
                break

    # 3. Class of Company (Type of Company)
    type_of_company = "Proprietorship"
    m_class = re.search(r'Class of Company\s+([A-Za-z\s]+?)(?:Company Activity|NIC Code|\n)', full_text, re.IGNORECASE)
    if m_class:
        type_of_company = m_class.group(1).strip()
        if 'private limited' in type_of_company.lower():
            type_of_company = 'PRIVATE LIMITED'
        elif 'partnership' in type_of_company.lower():
            type_of_company = 'Partnership'
        elif 'proprietorship' in type_of_company.lower():
            type_of_company = 'Proprietorship'

    # 4. Date of Incorporation / Registration
    date_of_incorporation = ""
    m_date = re.search(r'Date of (?:Incorporation|Registration)\s+([0-9]{2}-[A-Za-z]{3}-[0-9]{4})', full_text, re.IGNORECASE)
    if m_date:
        date_of_incorporation = _normalize_date(m_date.group(1))

    # 5. Registered Address
    registered_address = ""
    m_addr = re.search(r'Company Address\s+(.*?)(?:Company City|Company State|Company Pincode)', full_text, re.DOTALL | re.IGNORECASE)
    if m_addr:
        addr = m_addr.group(1).strip()
        registered_address = " ".join(addr.split())
    else:
        # Fallback to MCA or GST address
        m_gst_addr = re.search(r'GST.*?Address\s+(.*?)(?:Taxpayer Type|Status Active)', full_text, re.DOTALL | re.IGNORECASE)
        if m_gst_addr:
            registered_address = " ".join(m_gst_addr.group(1).strip().split())

    # 6. Credit Limit Recommendation & Tenor
    rubix_credit_limit_lakhs = 0.0
    crif_credit_limit_formatted = "₹ 0.00"
    recommended_credit_days = 30
    
    m_limit = re.search(r'\(in lakhs\)\s*₹?\s*([\d\.]+)', full_text)
    if m_limit:
        try:
            rubix_credit_limit_lakhs = float(m_limit.group(1))
            val_rupees = int(round(rubix_credit_limit_lakhs * 100000))
            crif_credit_limit_formatted = _format_inr(val_rupees)
        except (ValueError, TypeError):
            rubix_credit_limit_lakhs = 0.0

    m_days = re.search(r'Period \(in days\)\s*(\d+)', full_text)
    if m_days:
        try:
            recommended_credit_days = int(m_days.group(1))
        except (ValueError, TypeError):
            recommended_credit_days = 30

    # 7. Risk Score & Grade
    risk_score = 0
    risk_grade = "Rx5"
    risk_description = "Above Average Counterparty Risk"
    
    m_score = re.search(r'Risk score\s+(\d+)', full_text, re.IGNORECASE)
    if m_score:
        risk_score = int(m_score.group(1))
        
    m_grade = re.search(r'Risk grade\s+(Rx\d)', full_text, re.IGNORECASE)
    if m_grade:
        risk_grade = m_grade.group(1)
        
    m_desc = re.search(r'Description\s+([A-Za-z\s]+?Counterparty Risk)', full_text, re.IGNORECASE)
    if m_desc:
        risk_description = m_desc.group(1).strip()

    # 8. Compliance Checks
    gst_delay_days = 0
    m_gst_d = re.search(r'GST.*?Current delay\s*(?:days|\(In Days\))\s*(\d+)', full_text, re.IGNORECASE | re.DOTALL)
    if not m_gst_d:
        m_gst_d = re.search(r'GST Current Delay\s*\(In Days\)\s*(\d+)', full_text, re.IGNORECASE)
    if m_gst_d:
        gst_delay_days = int(m_gst_d.group(1))
        
    pf_delay_days = 0
    m_pf_d = re.search(r'PF compliance.*?Current delay days\s*(\d+)', full_text, re.IGNORECASE | re.DOTALL)
    if not m_pf_d:
        m_pf_d = re.search(r'PF Current Delay\s*\(In Days\)\s*(\d+)', full_text, re.IGNORECASE)
    if m_pf_d:
        pf_delay_days = int(m_pf_d.group(1))
        
    court_cases_count = 0
    m_court = re.search(r'High Court\s+(\d+)', full_text)
    if m_court:
        court_cases_count = int(m_court.group(1))

    external_rating = "Not Found"
    m_ext = re.search(r'CRISIL\s+([A-Za-z0-9+-]+)', full_text)
    if m_ext and m_ext.group(1).lower() != 'not':
        external_rating = f"CRISIL {m_ext.group(1)}"

    # Dynamic KYC Checklist based on constitution
    kyc_docs = _generate_kyc_checklist(type_of_company, gst_delay_days, bureau="Rubix")

    return {
        "customer_name": customer_name,
        "nature_of_business": nature_of_business,
        "type_of_company": type_of_company,
        "date_of_incorporation": date_of_incorporation,
        "registered_address": registered_address,
        "other_address": "N/A",
        "rubix_credit_limit_lakhs": rubix_credit_limit_lakhs,
        "crif_credit_limit": crif_credit_limit_formatted,
        "recommended_credit_days": recommended_credit_days,
        "approved_credit_days": "30 Days",
        "risk_score": risk_score,
        "risk_grade": risk_grade,
        "risk_description": risk_description,
        "gst_delay_days": gst_delay_days,
        "pf_delay_days": pf_delay_days,
        "court_cases_count": court_cases_count,
        "external_rating": external_rating,
        "bureau_source": "Rubix Data Sciences",
        "salesperson": "",
        "branch": "Mumbai Air Cargo",
        "iata_credit_days": "21 Days",
        "ocean_credit_days": "30 Days",
        "customs_duty_terms": "0 Days (Advance COD)",
        "sec_138_cheque": True,
        "caf_signed": True,
        "kyc_documents": kyc_docs,
        "created_by": "Credit Analyst",
        "checked_by": "Manager - Credit Control",
        "approved_by": "Head of Credit / Director",
        "appraisal_date": ""
    }

def parse_crif_bir_pdf(pdf_path: str) -> Dict[str, Any]:
    """Parses standard CRIF Business Information Report (BIR) PDFs."""
    reader = pypdf.PdfReader(pdf_path)
    pages_text = [clean_text(p.extract_text() or "") for p in reader.pages]
    full_text = "\n".join(pages_text)

    # 1. Customer Name
    customer_name = ""
    if pages_text:
        m_name = re.search(r'Business Information Report\s*\n\s*([A-Z0-9\s,\.\(\)&-]+?)\s*\n', pages_text[0])
        if m_name:
            customer_name = m_name.group(1).strip()
    if not customer_name:
        m_name = re.search(r'Company\s*name\s+([A-Z0-9\s,\.\(\)&-]+?)(?:Address|GSTIN|\n)', full_text, re.IGNORECASE)
        if m_name:
            customer_name = m_name.group(1).strip()
    customer_name = customer_name.upper()

    # 2. Type of Company
    type_of_company = "Proprietorship"
    m_form = re.search(r'Legal Form\s+([A-Za-z\s]+?)(?:GST Status|IEC Code|\n)', full_text, re.IGNORECASE)
    if m_form:
        form_raw = m_form.group(1).strip().lower()
        if 'private limited' in form_raw:
            type_of_company = 'PRIVATE LIMITED'
        elif 'partnership' in form_raw:
            type_of_company = 'Partnership'
        elif 'proprietorship' in form_raw:
            type_of_company = 'Proprietorship'
        else:
            type_of_company = m_form.group(1).strip()

    # 3. Date of Incorporation / Year of Establishment
    date_of_incorporation = ""
    m_year = re.search(r'Year of Establishment\s+(\d{4})', full_text, re.IGNORECASE)
    if m_year:
        date_of_incorporation = m_year.group(1).strip()
    else:
        m_date = re.search(r'Date of (?:Incorporation|Registration)\s+([0-9]{2}-[A-Za-z]{3}-[0-9]{4})', full_text, re.IGNORECASE)
        if m_date:
            date_of_incorporation = _normalize_date(m_date.group(1))

    # 4. Registered Address
    registered_address = ""
    if len(pages_text) > 1:
        m_addr = re.search(r'Registered Address\s+(.*?)(?:Operating Address|\n\s*Operating|Website|\n\s*Website)', pages_text[1], re.DOTALL | re.IGNORECASE)
        if m_addr:
            registered_address = " ".join(m_addr.group(1).split())
    if not registered_address:
        m_addr = re.search(r'Registered Address\s+(.*?)(?:Operating Address|Website|\n)', full_text, re.DOTALL | re.IGNORECASE)
        if m_addr:
            registered_address = " ".join(m_addr.group(1).split())

    # 5. Nature of Business
    nature_of_business = ""
    if len(pages_text) > 1:
        p2 = pages_text[1]
        m_nob = re.search(r'Fax\s+(?:N/A|[^\n]+)\s*\n\s*(.*?)\s*\n\s*(?:GOOGLE MAP|GLOBAL DUE DILIGENCE|\Z)', p2, re.DOTALL | re.IGNORECASE)
        if m_nob:
            nature_of_business = " ".join(m_nob.group(1).split())
    if not nature_of_business:
        m_nob_gen = re.search(r'([A-Z][a-zA-Z0-9\s,\.\(\)&-]+?(?:is a partnership firm|is a private limited company|engaged as|operates as)[^\n]+)', full_text)
        if m_nob_gen:
            nature_of_business = " ".join(m_nob_gen.group(1).split())

    # 6. Bureau Source
    bureau_source = "CRIF Solutions (BIR)"

    # 7. Risk Score, Grade, Description
    risk_score = 0
    risk_grade = "Normal"
    m_score = re.search(r'Score\s+(\d+)\s*/\s*(\d+)', full_text)
    if m_score:
        risk_score = int(m_score.group(1))
    m_grade = re.search(r'Score index\s+([A-Za-z]+)', full_text, re.IGNORECASE)
    if m_grade:
        risk_grade = m_grade.group(1).strip()

    risk_description = f"Score: {risk_score}/99 ({risk_grade} Index)"

    # 8. Credit limit & days
    rubix_credit_limit_lakhs = 0.0
    crif_credit_limit = "₹ 0.00"
    recommended_credit_days = 30

    # 9. Compliance
    gst_delay_days = 0
    pf_delay_days = 0
    court_cases_count = 0
    external_rating = "Not Found"

    kyc_docs = _generate_kyc_checklist(type_of_company, gst_delay_days, bureau="CRIF")

    return {
        "customer_name": customer_name,
        "nature_of_business": nature_of_business,
        "type_of_company": type_of_company,
        "date_of_incorporation": date_of_incorporation,
        "registered_address": registered_address,
        "other_address": "N/A",
        "rubix_credit_limit_lakhs": rubix_credit_limit_lakhs,
        "crif_credit_limit": crif_credit_limit,
        "recommended_credit_days": recommended_credit_days,
        "approved_credit_days": "30 Days",
        "risk_score": risk_score,
        "risk_grade": risk_grade,
        "risk_description": risk_description,
        "gst_delay_days": gst_delay_days,
        "pf_delay_days": pf_delay_days,
        "court_cases_count": court_cases_count,
        "external_rating": external_rating,
        "bureau_source": bureau_source,
        "salesperson": "",
        "branch": "Mumbai Air Cargo",
        "iata_credit_days": "21 Days",
        "ocean_credit_days": "30 Days",
        "customs_duty_terms": "0 Days (Advance COD)",
        "sec_138_cheque": True,
        "caf_signed": True,
        "kyc_documents": kyc_docs,
        "created_by": "Credit Analyst",
        "checked_by": "Manager - Credit Control",
        "approved_by": "Head of Credit / Director",
        "appraisal_date": ""
    }

def parse_crif_birl_pdf(pdf_path: str) -> Dict[str, Any]:
    """Parses comprehensive CRIF Business Information Report Limited (BIRL) PDFs."""
    reader = pypdf.PdfReader(pdf_path)
    pages_text = [clean_text(p.extract_text() or "") for p in reader.pages]
    full_text = "\n".join(pages_text)

    # 1. Customer Name
    customer_name = ""
    if pages_text:
        m_name = re.search(r'KEY OBSERVATIONS\s*\n\s*([A-Z0-9\s,\.\(\)&-]+?)\s*\n\s*Report Type', pages_text[0])
        if m_name:
            customer_name = m_name.group(1).strip()
    if not customer_name:
        m_name = re.search(r'BIR Report\s*\n\s*([A-Z0-9\s,\.\(\)&-]+?)\s*\n\s*Requested on:', full_text)
        if m_name:
            customer_name = m_name.group(1).strip()
    customer_name = customer_name.upper()

    # 2. Type of Company
    type_of_company = "PRIVATE LIMITED"
    m_form = re.search(r'Legal Form\(s\)\s+([A-Za-z\s\-]+?)(?:Registration|\n)', full_text)
    if m_form:
        form_raw = m_form.group(1).strip().lower()
        if 'private limited' in form_raw:
            type_of_company = 'PRIVATE LIMITED'
        elif 'partnership' in form_raw:
            type_of_company = 'Partnership'
        elif 'proprietorship' in form_raw:
            type_of_company = 'Proprietorship'
        else:
            type_of_company = m_form.group(1).strip()

    # 3. Date of Incorporation
    date_of_incorporation = ""
    m_date = re.search(r'Incorporation Date\s+([0-9]{2}-[A-Za-z]{3}-[0-9]{4})', full_text)
    if m_date:
        date_of_incorporation = _normalize_date(m_date.group(1))

    # 4. Registered Address
    registered_address = ""
    if len(pages_text) > 1:
        p2 = pages_text[1]
        m_addr = re.search(r'Registered Address\s+(.*?)(?:Operating Address|\n\s*Operating)', p2, re.DOTALL)
        if m_addr:
            registered_address = " ".join(m_addr.group(1).split())
    if not registered_address:
        m_addr = re.search(r'Registered Address\s+(.*?)(?:Operating Address|\n\s*Operating)', full_text, re.DOTALL)
        if m_addr:
            registered_address = " ".join(m_addr.group(1).split())

    # 5. Nature of Business (First paragraph under INDUSTRY AND SEGMENT(S) on Page 2)
    nature_of_business = ""
    if len(pages_text) > 1:
        p2 = pages_text[1]
        m_nob = re.search(r'INDUSTRY AND SEGMENT\(S\)\s*(.*?)\s*Registered Address', p2, re.DOTALL)
        if m_nob:
            nob = " ".join(m_nob.group(1).split())
            nob = re.sub(r'\binterna\s*onal\b', 'international', nob)
            nob = re.sub(r'\blogis\s*cs\b', 'logistics', nob)
            nature_of_business = nob
    if not nature_of_business:
        m_nob = re.search(r'INDUSTRY AND SEGMENT\(S\)\s*(.*?)\s*Registered Address', full_text, re.DOTALL)
        if m_nob:
            nob = " ".join(m_nob.group(1).split())
            nob = re.sub(r'\binterna\s*onal\b', 'international', nob)
            nob = re.sub(r'\blogis\s*cs\b', 'logistics', nob)
            nature_of_business = nob

    # 6. Bureau Source
    bureau_source = "CRIF Solutions (BIRL)"

    # 7. Risk Score & Grade & Description
    risk_score = 80
    risk_grade = "Rating 4/5"
    m_rat = re.search(r'Rating\s*(\d+)\s*/\s*(\d+)', full_text)
    if m_rat:
        num = int(m_rat.group(1))
        den = int(m_rat.group(2))
        risk_score = int(round((num / den) * 100))
        risk_grade = f"Rating {num}/{den}"

    risk_index = "Low Risk"
    m_idx = re.search(r'Risk Index\s+([A-Za-z\s]+?)(?:Credit Limit|\n)', full_text)
    if m_idx:
        risk_index = m_idx.group(1).strip()

    trend_summary = "activity increase"
    m_trend = re.search(r'Business Trend\s+(.*?)(?:Please refer|\n\s*\*)', full_text, re.DOTALL)
    if m_trend:
        tr_text = m_trend.group(1).lower()
        if 'increase in activities' in tr_text or 'activity increase' in tr_text:
            trend_summary = "activity increase"
        elif 'decrease in activities' in tr_text or 'activity decrease' in tr_text:
            trend_summary = "activity decrease"
        elif 'stable' in tr_text:
            trend_summary = "stable"

    risk_description = f"{risk_grade}, {risk_index} (Business trend: {trend_summary})"

    # 8. Credit Limit
    crif_credit_limit = "₹ 0.00"
    rubix_credit_limit_lakhs = 0.0
    m_lim = re.search(r'Credit Limit \(INR Cr\)\s*([\d\.]+)', full_text)
    if m_lim:
        try:
            cr_val = float(m_lim.group(1))
            val_rupees = int(round(cr_val * 10000000))
            crif_credit_limit = _format_inr(val_rupees)
            rubix_credit_limit_lakhs = round(cr_val * 100, 2)
        except (ValueError, TypeError):
            pass

    recommended_credit_days = 30

    # 9. Court Cases Count
    court_cases_count = _extract_birl_court_cases(full_text)

    # 10. PF Delay Days (Page 21 EPFO table)
    pf_delay_days = 0
    epfo_idx = full_text.find('ANNEXURE - ESTABLISHMENTS REGISTERED UNDER EPFO')
    if epfo_idx != -1:
        epfo_section = full_text[epfo_idx:epfo_idx + 3000]
        pf_delay_days = _calculate_epfo_delay(epfo_section)

    gst_delay_days = 0
    external_rating = "Not Found"

    kyc_docs = _generate_kyc_checklist(type_of_company, gst_delay_days, bureau="CRIF")

    return {
        "customer_name": customer_name,
        "nature_of_business": nature_of_business,
        "type_of_company": type_of_company,
        "date_of_incorporation": date_of_incorporation,
        "registered_address": registered_address,
        "other_address": "N/A",
        "rubix_credit_limit_lakhs": rubix_credit_limit_lakhs,
        "crif_credit_limit": crif_credit_limit,
        "recommended_credit_days": recommended_credit_days,
        "approved_credit_days": "30 Days",
        "risk_score": risk_score,
        "risk_grade": risk_grade,
        "risk_description": risk_description,
        "gst_delay_days": gst_delay_days,
        "pf_delay_days": pf_delay_days,
        "court_cases_count": court_cases_count,
        "external_rating": external_rating,
        "bureau_source": bureau_source,
        "salesperson": "",
        "branch": "Mumbai Air Cargo",
        "iata_credit_days": "21 Days",
        "ocean_credit_days": "30 Days",
        "customs_duty_terms": "0 Days (Advance COD)",
        "sec_138_cheque": True,
        "caf_signed": True,
        "kyc_documents": kyc_docs,
        "created_by": "Credit Analyst",
        "checked_by": "Manager - Credit Control",
        "approved_by": "Head of Credit / Director",
        "appraisal_date": ""
    }

def extract_bureau_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Detects the bureau format and dispatches to the appropriate parser.
    Supports Rubix, CRIF BIR, and CRIF BIRL.
    """
    bureau_format = detect_bureau_format(pdf_path)
    if bureau_format == 'CRIF_BIR':
        return parse_crif_bir_pdf(pdf_path)
    elif bureau_format == 'CRIF_BIRL':
        return parse_crif_birl_pdf(pdf_path)
    else:
        data = parse_rubix_pdf(pdf_path)
        data['bureau_source'] = "Rubix Data Sciences"
        return data
