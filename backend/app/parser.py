import re
import pypdf
from typing import Dict, Any

def clean_text(text: str) -> str:
    if not text:
        return ""
    # Normalize unicode non-breaking spaces and whitespace
    text = text.replace('\xa0', ' ').replace('\u2010', '-').replace('\u2013', '-').replace('\u2014', '-')
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

_MONTHS = {'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
           'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'}

def _normalize_date(raw_date: str) -> str:
    """Converts DD-Mon-YYYY (e.g. 01-Jan-2019) to DD-MM-YYYY (01-01-2019)."""
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
    is_pvt_ltd = 'private limited' in type_of_company.lower()
    is_partnership = 'partnership' in type_of_company.lower()
    
    kyc_docs = [
        {"document": "Permanent Account Number (PAN)", "status": "Available", "source": "Income Tax / Rubix", "remarks": "Active & Linked"},
        {"document": "GST Registration Certificate", "status": "Available", "source": "GSTN Portal / Rubix", "remarks": f"Active ({gst_delay_days} Days Delay)"}
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
